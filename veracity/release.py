"""Release-readiness aggregation."""

from __future__ import annotations

from typing import Any

from .config import Config, load_config
from .evidence import make_evidence
from .detectors import (
    detect_dependency_impact,
    detect_security_files,
    file_paths,
    path_matches,
    possible_breaking_changes,
)
from .models import ReleaseReadinessReport
from .scanners import normalize_scanner_input


def analyze_release(release: dict[str, Any], *, config: Config | None = None) -> ReleaseReadinessReport:
    config = config or load_config()
    if not isinstance(release, dict):
        raise ValueError("Release input must be a JSON object")
    pull_requests = release.get("pull_requests", [])
    if not isinstance(pull_requests, list):
        raise ValueError("release.pull_requests must be a list")
    notable: list[str] = []
    security: list[str] = []
    dependencies: list[str] = []
    breaking: list[str] = []
    evidence = []
    docs_changed = False
    tests_changed = False
    for index, pr in enumerate(pull_requests):
        title = str(pr.get("title", f"Pull request {index + 1}"))
        files = pr.get("files", [])
        paths = file_paths(files)
        notable.append(title)
        ev = make_evidence(f"Merged change: {title}", "release_pr", str(pr.get("number", index + 1)), ", ".join(paths) or "No files supplied")
        evidence.append(ev)
        if detect_security_files(files, config):
            security.append(title)
        if detect_dependency_impact(files, config).level != "None":
            dependencies.append(title)
        breaking.extend(possible_breaking_changes(files))
        docs_changed = docs_changed or any(path_matches(path, config.paths.docs) for path in paths)
        tests_changed = tests_changed or any(path_matches(path, config.paths.tests) for path in paths)
    scanner_findings = []
    high_risk = []
    for scanner_input in release.get("scanner_inputs", []):
        for finding in normalize_scanner_input(scanner_input):
            scanner_findings.append(f"{finding.severity} - {finding.scanner}: {finding.title}")
            evidence.append(
                make_evidence(
                    f"{finding.scanner} reported {finding.id}",
                    "scanner_finding",
                    finding.id,
                    finding.explanation,
                )
            )
            if finding.severity in {"High", "Critical"}:
                high_risk.append(f"{finding.scanner}: {finding.title}")
    for issue in release.get("issues", []):
        if not isinstance(issue, dict):
            continue
        labels = {
            str(label.get("name", "")) if isinstance(label, dict) else str(label)
            for label in issue.get("labels", [])
        }
        if str(issue.get("state", "open")).lower() == "open" and labels & {
            "security",
            "blocker",
            "critical",
            "high-priority",
        }:
            issue_text = f"Issue #{issue.get('number', '?')}: {issue.get('title', 'Untitled issue')}"
            high_risk.append(issue_text)
            evidence.append(
                make_evidence(
                    issue_text,
                    "release_issue",
                    str(issue.get("number", "?")),
                    f"Open issue with labels: {', '.join(sorted(labels))}",
                )
            )
    risk = "High" if high_risk or security or breaking else "Medium" if dependencies else "Low"
    if high_risk:
        verdict = "Do not ship until high-risk items are resolved"
    elif breaking or security:
        verdict = "Review before release"
    elif dependencies:
        verdict = "Review dependency changes before release"
    else:
        verdict = "Looks ready for release review"
    version = str(release.get("version", "Unspecified"))
    summary = (
        f"Release {version} contains {len(pull_requests)} merged change(s), "
        f"{len(security)} security-sensitive change(s), and {len(dependencies)} dependency change(s)."
    )
    checklist = ["Confirm the full test suite passes.", "Review and finalize release notes."]
    if security:
        checklist.append("Confirm security-sensitive changes received maintainer review.")
    if breaking:
        checklist.append("Confirm migration guidance covers possible breaking changes.")
    if high_risk:
        checklist.append("Resolve or explicitly accept unresolved high-risk items.")
    if dependencies:
        checklist.append("Confirm dependency scanner results and upgrade rationale are documented.")
    if not docs_changed:
        checklist.append("Confirm documentation and changelog are current.")
    changelog = release.get("changelog", [])
    if isinstance(changelog, str):
        changelog = [line.strip() for line in changelog.splitlines() if line.strip()]
    release_notes = (
        "\n".join(f"- {item}" for item in changelog)
        if isinstance(changelog, list) and changelog
        else "\n".join(f"- {title}" for title in notable) or "- No notable changes supplied."
    )
    return ReleaseReadinessReport(
        version=version,
        verdict=verdict,
        risk_level=risk,
        executive_summary=summary,
        notable_changes=notable,
        breaking_changes=breaking,
        security_sensitive_changes=security,
        dependency_changes=dependencies,
        scanner_findings=scanner_findings,
        docs_status="Documentation changes detected." if docs_changed else "No documentation changes detected.",
        tests_status="Test changes detected." if tests_changed else "No test changes detected.",
        unresolved_high_risk_items=high_risk,
        release_notes=release_notes,
        release_checklist=checklist,
        evidence=evidence,
        limitations=[
            "Release readiness is based only on supplied merged changes, scanner summaries, and metadata.",
            "This report does not replace release-manager review.",
        ],
    )
