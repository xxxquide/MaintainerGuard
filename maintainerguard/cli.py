"""MaintainerGuard command-line interface."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .ai import safe_enrich_report
from .analysis import analyze_pull_request
from .config import ConfigError, default_config_toml, load_config
from .github import (
    GitHubClient,
    choose_comment_action,
    parse_github_event,
    publication_allowed,
)
from .issue import triage_issue
from .release import analyze_release
from .reports import render_report
from .scanners import normalize_scanner_input


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_program_name(),
        description="MaintainerGuard - evidence-first merge, security, and release readiness for open-source maintainers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Common commands:
  mg demo
  mg init
  mg doctor
  mg verify
  mg pr <file>
  mg issue <file>
  mg release <file>

Long-form commands such as analyze-pr, analyze-issue, and analyze-release remain supported.""",
    )
    parser.add_argument("--config", type=Path, help="Path to .maintainerguard.toml")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="Run the default demo or a named bundled scenario")
    demo.add_argument("--scenario", default="high-risk-auth")
    demo.add_argument("--format", choices=["markdown", "json"])
    analyze_pr = subparsers.add_parser("analyze-pr", help="Analyze PR JSON")
    analyze_pr.add_argument("input", type=Path)
    analyze_pr.add_argument("--scanner", action="append", type=Path, default=[])
    analyze_pr.add_argument("--format", choices=["markdown", "json"])
    pr = subparsers.add_parser("pr", help="Analyze PR JSON")
    pr.add_argument("input", type=Path)
    pr.add_argument("--scanner", action="append", type=Path, default=[])
    pr.add_argument("--format", choices=["markdown", "json"])
    analyze_issue = subparsers.add_parser("analyze-issue", help="Analyze issue JSON")
    analyze_issue.add_argument("input", type=Path)
    analyze_issue.add_argument("--format", choices=["markdown", "json"])
    issue = subparsers.add_parser("issue", help="Analyze issue JSON")
    issue.add_argument("input", type=Path)
    issue.add_argument("--format", choices=["markdown", "json"])
    analyze_release_parser = subparsers.add_parser("analyze-release", help="Analyze release JSON")
    analyze_release_parser.add_argument("input", type=Path)
    analyze_release_parser.add_argument("--format", choices=["markdown", "json"])
    release_parser = subparsers.add_parser("release", help="Analyze release JSON")
    release_parser.add_argument("input", type=Path)
    release_parser.add_argument("--format", choices=["markdown", "json"])
    parse_scanner = subparsers.add_parser("parse-scanner", help="Normalize scanner JSON")
    parse_scanner.add_argument("input", type=Path)
    subparsers.add_parser("validate-config", help="Validate configuration")
    subparsers.add_parser("print-config", help="Print a documented example configuration")
    subparsers.add_parser("config", help="Print a documented example configuration")
    init = subparsers.add_parser("init", help="Create a safe local MaintainerGuard configuration")
    init.add_argument("--github-action", action="store_true", help="Also create a safe dry-run GitHub Actions workflow")
    init.add_argument("--force", action="store_true", help="Overwrite files that already exist")
    subparsers.add_parser("doctor", help="Check local MaintainerGuard setup")
    subparsers.add_parser("verify", help="Run deterministic sample smoke checks")
    subparsers.add_parser("version", help="Print MaintainerGuard version")
    github_run = subparsers.add_parser("github-run", help="Analyze a GitHub event")
    github_run.add_argument("event", type=Path)
    github_run.add_argument("--post", action="store_true", help="Explicitly allow publishing if configuration also permits it")
    github_run.add_argument("--format", choices=["markdown", "json"])
    subparsers.add_parser("action-run", help="Run from the MaintainerGuard GitHub Action")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "version":
            print(__version__)
            return 0
        if args.command == "init":
            return _init(args)
        if args.command == "doctor":
            return _doctor(args.config)
        if args.command == "verify":
            return _verify(args.config)
        config = load_config(args.config) if args.config else load_config()
        if args.command in {"print-config", "config"}:
            print(default_config_toml(), end="")
            return 0
        if args.command == "validate-config":
            print("Configuration is valid.")
            return 0
        if args.command == "parse-scanner":
            print(json.dumps([item.to_dict() for item in normalize_scanner_input(_read_json(args.input))], indent=2, sort_keys=True))
            return 0
        if args.command == "demo":
            pr, scanners = _demo(args.scenario)
            report = safe_enrich_report(
                analyze_pull_request(pr, scanner_inputs=scanners, config=config), config
            )
            print(render_report(report, output_format=args.format or config.output_format, mode=config.report_mode), end="")
            return 0
        if args.command in {"analyze-pr", "pr"}:
            scanners = _load_scanners([*args.scanner, *map(Path, config.paths.scanner_inputs)])
            report = safe_enrich_report(
                analyze_pull_request(_read_json(args.input), scanner_inputs=scanners, config=config),
                config,
            )
            print(render_report(report, output_format=args.format or config.output_format, mode=config.report_mode), end="")
            return 0
        if args.command in {"analyze-issue", "issue"}:
            report = triage_issue(_read_json(args.input))
            print(render_report(report, output_format=args.format or config.output_format), end="")
            return 0
        if args.command in {"analyze-release", "release"}:
            report = analyze_release(_read_json(args.input), config=config)
            print(render_report(report, output_format=args.format or config.output_format), end="")
            return 0
        if args.command == "github-run":
            return _github_run(args, config)
        if args.command == "action-run":
            return _action_run(config)
    except (ConfigError, ValueError, OSError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"maintainerguard: {exc}", file=sys.stderr)
        return 2
    parser.error("Unknown command")
    return 2


def _program_name() -> str:
    name = Path(sys.argv[0]).name
    return name if name in {"mg", "maintainerguard"} else "mg"


def _init(args: argparse.Namespace) -> int:
    config_path = args.config or Path(".maintainerguard.toml")
    created: list[Path] = []
    skipped: list[Path] = []
    _write_setup_file(config_path, default_config_toml(), args.force, created, skipped)
    if args.github_action:
        workflow = Path(".github") / "workflows" / "maintainerguard.yml"
        _write_setup_file(workflow, _safe_workflow_template(), args.force, created, skipped)

    print("MaintainerGuard initialized.\n")
    if created:
        print("Created:")
        for path in created:
            print(f"* {path.as_posix()}")
        print()
    if skipped:
        print("Already present:")
        for path in skipped:
            print(f"* {path.as_posix()} already exists; use --force to overwrite")
        print()
    if not created and skipped:
        print("No files changed.\n")
    print("Next steps:")
    print(f"1. Review {config_path.as_posix()}")
    print("2. Run: mg doctor")
    print("3. Run: mg demo")
    print("4. Commit the config file")
    return 0


def _write_setup_file(path: Path, content: str, force: bool, created: list[Path], skipped: list[Path]) -> None:
    if path.exists() and not force:
        skipped.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path)


def _safe_workflow_template() -> str:
    return """name: MaintainerGuard

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

permissions:
  contents: read
  pull-requests: read

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: xxxquide/MaintainerGuard@v0.1.0
        with:
          mode: analyze-pr
          dry-run: "true"
          post-comment: "false"
          fail-on-risk: none
"""


def _doctor(config_path: Path | None) -> int:
    print("MaintainerGuard Doctor\n")
    problems = 0
    _status("OK", "CLI available")
    if sys.version_info >= (3, 11):
        _status("OK", f"Python {sys.version_info.major}.{sys.version_info.minor}+")
    else:
        _status("FAIL", "Python 3.11 or newer is required")
        problems += 1

    candidate = config_path or Path(".maintainerguard.toml")
    config_exists = candidate.exists()
    if config_exists:
        _status("OK", f"Config found: {candidate.as_posix()}")
    else:
        _status("INFO", f"Config not found: {candidate.as_posix()}")
        _status("INFO", "Run: mg init")

    try:
        config = load_config(candidate) if config_exists or config_path else load_config()
    except ConfigError as exc:
        _status("FAIL", f"Config is invalid: {exc}")
        print("\nMaintainerGuard setup needs attention.")
        return 2
    if config_exists:
        _status("OK", "Config is valid")
    else:
        _status("OK", "Built-in safe defaults available")

    root = _package_root()
    _status("OK" if (root / "examples/sample-data/prs/high-risk-auth.json").exists() else "FAIL", "Sample data available")
    if not (root / "examples/sample-data/prs/high-risk-auth.json").exists():
        problems += 1
    action_status = "OK" if (root / "action.yml").exists() else "INFO"
    _status(action_status, "GitHub Action metadata available" if action_status == "OK" else "GitHub Action metadata not bundled")
    _status("OK" if not config.ai.enabled else "INFO", "AI disabled by default" if not config.ai.enabled else "AI enabled by configuration")
    _status("OK" if config.dry_run else "WARN", "Dry-run enabled by default" if config.dry_run else "Dry-run disabled by configuration")

    if problems:
        print("\nMaintainerGuard setup needs attention.")
        return 2
    print("\nMaintainerGuard is ready.")
    return 0


def _verify(config_path: Path | None) -> int:
    print("MaintainerGuard Verify\n")
    config = load_config(config_path) if config_path else load_config()
    checks = [
        ("config validation", lambda: load_config(config_path) if config_path else load_config()),
        ("demo: high-risk-auth", lambda: _verify_demo("high-risk-auth", config)),
        ("demo: dependency-advisory", lambda: _verify_demo("dependency-advisory", config)),
        ("demo: ci-workflow-risk", lambda: _verify_demo("ci-workflow-risk", config)),
        ("demo: secret-finding", lambda: _verify_demo("secret-finding", config)),
        ("sample PR analysis", lambda: _verify_pr(config)),
        ("sample issue analysis", _verify_issue),
        ("sample release analysis", lambda: _verify_release(config)),
        ("JSON output", lambda: _verify_json(config)),
    ]
    failures = 0
    for name, check in checks:
        try:
            check()
        except Exception as exc:
            failures += 1
            _status("FAIL", f"{name}: {exc}")
        else:
            _status("OK", name)
    if failures:
        print(f"\n{failures} check(s) failed.")
        return 2
    print("\nAll checks passed.")
    return 0


def _status(status: str, message: str) -> None:
    print(f"{status:<4}{message}")


def _verify_demo(scenario: str, config) -> None:
    pr, scanners = _demo(scenario)
    report = safe_enrich_report(analyze_pull_request(pr, scanner_inputs=scanners, config=config), config)
    if not render_report(report, output_format="markdown", mode=config.report_mode).strip():
        raise RuntimeError("empty report")


def _verify_pr(config) -> None:
    root = _package_root()
    report = safe_enrich_report(
        analyze_pull_request(
            _read_json(root / "examples/sample-data/prs/dependency-update.json"),
            scanner_inputs=_load_scanners([root / "examples/sample-data/scanners/dependency-advisory.json"]),
            config=config,
        ),
        config,
    )
    if getattr(report, "verdict", "") != "Blocked by scanner finding":
        raise RuntimeError("unexpected PR verdict")


def _verify_issue() -> None:
    report = triage_issue(_read_json(_package_root() / "examples/sample-data/issues/bug-missing-reproduction.json"))
    if getattr(report, "issue_type", "") != "Bug report":
        raise RuntimeError("unexpected issue classification")


def _verify_release(config) -> None:
    report = analyze_release(_read_json(_package_root() / "examples/sample-data/releases/v0.2.0.json"), config=config)
    if not getattr(report, "version", ""):
        raise RuntimeError("missing release version")


def _verify_json(config) -> None:
    pr, scanners = _demo("high-risk-auth")
    report = safe_enrich_report(analyze_pull_request(pr, scanner_inputs=scanners, config=config), config)
    data = json.loads(render_report(report, output_format="json", mode=config.report_mode))
    if data.get("report_type") != "merge_readiness_report":
        raise RuntimeError("unexpected JSON report type")


def _package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _github_run(args: argparse.Namespace, config) -> int:
    event = _read_json(args.event)
    event_type, normalized = parse_github_event(event)
    if event_type == "issue":
        report = triage_issue(normalized)
    else:
        repository = normalized.pop("repository", "")
        number = int(normalized.get("number", 0))
        token = os.environ.get("GITHUB_TOKEN", "")
        if token and repository:
            client = GitHubClient(token)
            normalized["files"] = client.get_pull_files(repository, number, config.privacy.max_files_analyzed)
        elif "files" in event:
            normalized["files"] = event["files"]
        else:
            normalized["files"] = []
        report = safe_enrich_report(
            analyze_pull_request(
                normalized,
                scanner_inputs=_load_scanners([Path(path) for path in config.paths.scanner_inputs]),
                config=config,
            ),
            config,
        )
    body = render_report(report, output_format=args.format or config.output_format, mode=config.report_mode)
    print(body, end="")
    if event_type == "pull_request" and publication_allowed(config, args.post, normalized):
        repository = event.get("repository", {}).get("full_name", "")
        token = os.environ.get("GITHUB_TOKEN", "")
        if not repository or not token:
            raise RuntimeError("Publishing requires repository metadata and GITHUB_TOKEN")
        client = GitHubClient(token)
        comments = client.get_issue_comments(repository, int(event.get("number", 0)))
        action = choose_comment_action(
            comments,
            body,
            update_previous=config.github.update_previous_comment,
            max_characters=config.github.max_comment_characters,
        )
        if action.action == "create":
            client.create_comment(repository, int(event.get("number", 0)), action.body)
        elif action.action == "update" and action.comment_id:
            client.update_comment(repository, action.comment_id, action.body)
    return 0


def _action_run(config) -> int:
    mode = os.environ.get("MG_MODE", "analyze-pr").strip() or "analyze-pr"
    output_format = os.environ.get("MG_OUTPUT_FORMAT", config.output_format).strip() or config.output_format
    report_mode = os.environ.get("MG_REPORT_LENGTH", config.report_mode).strip() or config.report_mode
    config.output_format = output_format
    config.report_mode = report_mode
    config.dry_run = _truthy(os.environ.get("MG_DRY_RUN", str(config.dry_run)))
    config.github.post_comments = _truthy(os.environ.get("MG_POST_COMMENT", str(config.github.post_comments)))
    config.github.update_previous_comment = _truthy(
        os.environ.get("MG_UPDATE_EXISTING_COMMENT", str(config.github.update_previous_comment))
    )
    config.ai.enabled = _truthy(os.environ.get("MG_AI_ENABLED", str(config.ai.enabled)))
    scanner_paths = _split_paths(os.environ.get("MG_SCANNER_RESULT_PATHS", ""))
    input_path = os.environ.get("MG_INPUT_PATH", "").strip()
    event_path = os.environ.get("GITHUB_EVENT_PATH", "").strip()
    report = None
    body = ""

    if mode == "validate-config":
        print("Configuration is valid.")
        return 0
    if mode == "demo":
        scenario = input_path or "high-risk-auth"
        pr, scanners = _demo(scenario)
        report = safe_enrich_report(analyze_pull_request(pr, scanner_inputs=scanners, config=config), config)
    elif mode == "analyze-pr":
        if input_path:
            report = safe_enrich_report(
                analyze_pull_request(_read_json(Path(input_path)), scanner_inputs=_load_scanners(scanner_paths), config=config),
                config,
            )
        elif event_path:
            event = _read_json(Path(event_path))
            event_type, normalized = parse_github_event(event)
            if event_type != "pull_request":
                raise ValueError("analyze-pr mode requires a pull_request event")
            repository = normalized.pop("repository", "")
            number = int(normalized.get("number", 0))
            token = os.environ.get("GITHUB_TOKEN", "")
            if token and repository:
                client = GitHubClient(token)
                normalized["files"] = client.get_pull_files(repository, number, config.privacy.max_files_analyzed)
            elif "files" in event:
                normalized["files"] = event["files"]
            else:
                normalized["files"] = []
            report = safe_enrich_report(
                analyze_pull_request(normalized, scanner_inputs=_load_scanners(scanner_paths), config=config),
                config,
            )
            body = render_report(report, output_format=output_format, mode=report_mode)
            print(body, end="")
            if publication_allowed(config, config.github.post_comments, normalized):
                if not repository or not token:
                    raise RuntimeError("Publishing requires repository metadata and GITHUB_TOKEN")
                client = GitHubClient(token)
                comments = client.get_issue_comments(repository, int(event.get("number", 0)))
                action = choose_comment_action(
                    comments,
                    body,
                    update_previous=config.github.update_previous_comment,
                    max_characters=config.github.max_comment_characters,
                )
                if action.action == "create":
                    client.create_comment(repository, int(event.get("number", 0)), action.body)
                elif action.action == "update" and action.comment_id:
                    client.update_comment(repository, action.comment_id, action.body)
            return _fail_on_risk(report, os.environ.get("MG_FAIL_ON_RISK", "none"))
        else:
            raise ValueError("analyze-pr mode requires a sample input path or GITHUB_EVENT_PATH")
    elif mode == "analyze-issue":
        if input_path:
            report = triage_issue(_read_json(Path(input_path)))
        elif event_path:
            event_type, normalized = parse_github_event(_read_json(Path(event_path)))
            if event_type != "issue":
                raise ValueError("analyze-issue mode requires an issue event")
            report = triage_issue(normalized)
        else:
            raise ValueError("analyze-issue mode requires a sample input path or GITHUB_EVENT_PATH")
    elif mode == "analyze-release":
        path = Path(input_path or "examples/sample-data/releases/v0.2.0.json")
        report = analyze_release(_read_json(path), config=config)
    else:
        raise ValueError(f"Unsupported action mode: {mode}")

    body = render_report(report, output_format=output_format, mode=report_mode)
    print(body, end="")
    return _fail_on_risk(report, os.environ.get("MG_FAIL_ON_RISK", "none"))


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_scanners(paths: list[Path]) -> list[dict[str, Any]]:
    return [_read_json(path) for path in paths]


def _split_paths(raw: str) -> list[Path]:
    output: list[Path] = []
    for chunk in raw.replace(",", "\n").splitlines():
        value = chunk.strip()
        if value:
            output.append(Path(value))
    return output


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _fail_on_risk(report, threshold: str) -> int:
    threshold = (threshold or "none").strip().lower()
    if threshold == "none":
        return 0
    order = {"Unknown": 0, "Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    required = {"critical": 4, "high": 3}.get(threshold)
    if required is None:
        raise ValueError("fail-on-risk must be none, critical, or high")
    return 1 if order.get(getattr(report, "risk_level", "Unknown"), 0) >= required else 0


def _demo(scenario: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = Path(__file__).resolve().parents[1]
    aliases = {
        "dependency-advisory": (
            root / "examples" / "sample-data" / "prs" / "dependency-update.json",
            [root / "examples" / "sample-data" / "scanners" / "dependency-advisory.json"],
        ),
        "ci-workflow-risk": (
            root / "examples" / "sample-data" / "prs" / "ci-workflow.json",
            [root / "examples" / "sample-data" / "scanners" / "supply-chain-workflow.json"],
        ),
        "secret-finding": (
            root / "examples" / "sample-data" / "prs" / "secret-finding.json",
            [root / "examples" / "sample-data" / "scanners" / "secret-scan.json"],
        ),
    }
    if scenario in aliases:
        pr_path, scanner_paths = aliases[scenario]
        return _read_json(pr_path), _load_scanners(scanner_paths)
    sample_path = (
        root
        / "examples"
        / "sample-data"
        / "prs"
        / f"{scenario}.json"
    )
    if sample_path.exists():
        return _read_json(sample_path), []
    samples = {
        "docs-only": {
            "title": "Clarify getting started instructions",
            "files": [{"path": "docs/getting-started.md", "status": "modified", "patch": "+Clarify setup."}],
        },
        "medium-risk-config": {
            "title": "Change configuration validation",
            "files": [{"path": "src/config.py", "status": "modified", "patch": "+require value"}],
        },
        "high-risk-auth": {
            "title": "Change session validation",
            "files": [{"path": "src/auth/session.py", "status": "modified", "patch": "+validate_session(token)"}],
        },
        "dependency-update": {
            "title": "Update dependency",
            "files": [{"path": "requirements.txt", "status": "modified", "patch": "+example-lib==1.2.3"}],
        },
        "ci-workflow": {
            "title": "Update release workflow",
            "files": [{"path": ".github/workflows/release.yml", "status": "modified", "patch": "+permissions: write-all"}],
        },
        "release-impact": {
            "title": "Breaking CLI change",
            "files": [{"path": "src/cli.py", "status": "modified", "patch": "+BREAKING: remove old flag"}],
        },
    }
    if scenario not in samples:
        raise ValueError(f"Unknown demo scenario: {scenario}")
    return {"schema_version": "1.0", **samples[scenario]}, []
