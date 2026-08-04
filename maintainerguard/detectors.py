"""Deterministic change-impact detectors."""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Iterable

from .config import Config
from .models import Impact


SECURITY_CATEGORIES: dict[str, tuple[tuple[str, ...], str, str]] = {
    "Authentication and sessions": (
        ("auth", "login", "session", "token", "password", "middleware"),
        "Authentication or session behavior commonly controls access to protected resources.",
        "Verify authentication success and rejection paths, token/session handling, and protected routes.",
    ),
    "Authorization and permissions": (
        ("permission", "authorize", "authorization", "role", "admin", "access"),
        "Authorization and permission changes may alter who can perform protected actions.",
        "Verify least privilege, role boundaries, and denied-access behavior.",
    ),
    "Secrets and cryptography": (
        ("secret", "apikey", "api_key", "crypto", "encrypt", "hash", "certificate", "private_key"),
        "Secret handling and cryptographic code require careful review for accidental exposure or misuse.",
        "Verify secret handling, key material boundaries, and cryptographic assumptions.",
    ),
    "Command, file, and network boundaries": (
        ("shell", "exec", "spawn", "upload", "path", "webhook", "request", "redirect", "deserialize"),
        "Code at command, file, or network boundaries may process untrusted input.",
        "Verify input validation, path handling, command arguments, and network trust boundaries.",
    ),
    "Web rendering and data access": (
        ("sql", "query", "orm", "html", "template", "xss", "cors"),
        "Rendering and data-access changes may affect injection or browser security boundaries.",
        "Verify parameterization, escaping, origin rules, and output encoding.",
    ),
    "CI, release, and supply chain": (
        (".github/workflows", "release", "deploy", "dockerfile", "package.json", "pyproject.toml"),
        "Build, workflow, and dependency changes affect the software supply chain.",
        "Review permissions, pinned actions, scripts, publishing behavior, and dependency provenance.",
    ),
}

BEHAVIOR_HINTS = (
    "src/",
    "lib/",
    "app/",
    "api/",
    "cli",
    "config",
    "auth",
    "route",
    "handler",
    "service",
)


_WORD_SPLIT = re.compile(r"[^a-z0-9]+")

# Statuses that carry no new behavior to review.
_REMOVED_STATUSES = {"removed", "deleted"}
_RENAMED_STATUSES = {"renamed", "moved"}

# A removed line that looks like a declaration, not prose. Used instead of
# searching whole patches for words like "remove", which fire on comments and
# documentation text.
_DECLARATION = re.compile(
    r"""^\s*
    (?:@\w+|export|public|private|protected|static|async|pub|final|abstract)?\s*
    (?:
        (?:def|class|func|fn|function|interface|type|struct|enum|impl|trait|module|namespace)\b
        | [A-Za-z_][\w.]*\s*[:=]\s*(?:function\b|async\b|lambda\b|\()
        | [A-Z][A-Z0-9_]{2,}\s*[:=]
    )
    """,
    re.VERBOSE,
)
_EXPLICIT_BREAKING = re.compile(r"breaking[ _-]?change|^\s*[-+]?\s*breaking\s*:", re.IGNORECASE)


def _terms(text: str) -> str:
    """Lowercase text with separators collapsed, space-padded for word tests."""
    return f" {_WORD_SPLIT.sub(' ', text.lower()).strip()} "


def keyword_matches(keyword: str, *texts: str) -> bool:
    """Match a keyword as a whole word, not as a substring.

    Substring matching reported `terraform/main.tf` as a rendering change because
    `orm` occurs inside `terraform`, and `src/authors.py` as authentication
    because `auth` occurs inside `author`. Keywords that are themselves path or
    file fragments (`.github/workflows`, `package.json`, `api_key`) keep
    substring semantics, because word splitting would destroy them.
    """
    lowered = keyword.lower()
    if not lowered.isalnum():
        return any(lowered in text.lower() for text in texts)
    variants = (f" {lowered} ", f" {lowered}s ", f" {lowered}es ")
    return any(variant in _terms(text) for text in texts for variant in variants)


def _is_generated_or_supporting(path: str, config: Config) -> bool:
    """Tests and documentation are not security-sensitive behavior changes."""
    return path_matches(path, config.paths.tests) or path_matches(path, config.paths.docs)


def _carries_behavior(item: dict) -> bool:
    """False for deletions and for pure renames with no diff content."""
    status = str(item.get("status", "modified")).strip().lower()
    if status in _REMOVED_STATUSES:
        return False
    if status in _RENAMED_STATUSES and not str(item.get("patch", "")).strip():
        return False
    return True


def path_matches(path: str, patterns: Iterable[str]) -> bool:
    lowered = path.lower()
    return any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(lowered, pattern.lower()) for pattern in patterns)


def file_paths(files: list[dict]) -> list[str]:
    return [str(item.get("path", "")) for item in files if item.get("path")]


def changed_areas(files: list[dict]) -> list[str]:
    areas: set[str] = set()
    for path in file_paths(files):
        lower = path.lower()
        if lower.startswith("docs/") or lower.startswith("readme"):
            areas.add("Documentation")
        elif lower.startswith("tests/") or keyword_matches("test", path) or ".spec." in lower:
            areas.add("Tests")
        elif lower.startswith(".github/workflows/"):
            areas.add("CI/CD")
        elif any(
            keyword_matches(term, path)
            for term in ("auth", "session", "permission", "security")
        ):
            areas.add("Security-sensitive code")
        elif any(
            keyword_matches(term, path)
            for term in ("requirements", "package.json", "lock", "pyproject.toml", "go.mod", "cargo.")
        ):
            areas.add("Dependencies")
        elif any(keyword_matches(term, path) for term in ("config", ".env", "settings")):
            areas.add("Configuration")
        else:
            root = path.split("/", 1)[0]
            areas.add(root if root else "Repository")
    return sorted(areas)


def detect_security_files(files: list[dict], config: Config) -> list[tuple[str, list[str], str, str]]:
    matches: list[tuple[str, list[str], str, str]] = []
    paths = file_paths(files)
    categorized: set[str] = set()
    for category, (keywords, explanation, guidance) in SECURITY_CATEGORIES.items():
        affected = [
            path
            for path, item in zip(paths, files)
            if (
                category == "CI, release, and supply chain"
                or not _is_supply_chain_review_path(path, config)
            )
            if not _is_generated_or_supporting(path, config)
            if any(
                keyword_matches(keyword, path, str(item.get("patch", "")))
                for keyword in keywords
            )
        ]
        if affected:
            categorized.update(affected)
            matches.append((category, sorted(set(affected)), explanation, guidance))
    # Documentation and test classification takes precedence over the
    # security-sensitive path list, so the default `**/security/**` pattern does
    # not report `docs/security/threat-model.md` as a security-sensitive code
    # change. A maintainer who wants otherwise removes the path from
    # `paths.docs` or `paths.tests`.
    configured = [
        path
        for path in paths
        if path_matches(path, config.paths.security_sensitive)
        and path not in categorized
        and not _is_generated_or_supporting(path, config)
    ]
    if configured:
        matches.append(
            (
                "Configured security-sensitive path",
                sorted(set(configured)),
                "Repository configuration marks this path as requiring additional security attention.",
                "Review the changed behavior and confirm repository-specific security expectations.",
            )
        )
    return matches


def detect_test_impact(files: list[dict], config: Config, security_touched: bool) -> Impact:
    paths = file_paths(files)
    tests = [path for path in paths if path_matches(path, config.paths.tests)]
    behavior = [
        str(item["path"])
        for item in files
        if item.get("path")
        and not path_matches(str(item["path"]), config.paths.docs)
        and not path_matches(str(item["path"]), config.paths.tests)
        and _carries_behavior(item)
        and _matches_behavior_hint(str(item["path"]))
    ]
    if tests:
        return Impact("Low", "Related test files changed in this pull request.", tests, confidence="High")
    if security_touched and behavior:
        return Impact(
            "High",
            "Security-sensitive behavior changed, but no related test files changed.",
            behavior,
            [
                "Add rejection-path and success-path tests for the changed security-sensitive behavior.",
                "Test invalid, expired, and missing credentials or tokens where applicable.",
                "Test unauthenticated access and the valid-session success path where applicable.",
                "Confirm existing regression tests cover the affected paths.",
            ],
            confidence="Medium",
        )
    if behavior:
        return Impact(
            "Medium",
            "Behavior-related files changed, but no related test files changed.",
            behavior,
            ["Confirm existing tests cover the changed behavior or add focused tests."],
            confidence="Medium",
        )
    return Impact("None", "No behavior change requiring additional test review was detected.", confidence="High")


def _matches_behavior_hint(path: str) -> bool:
    lowered = path.lower()
    for hint in BEHAVIOR_HINTS:
        if hint.endswith("/"):
            if lowered.startswith(hint) or f"/{hint}" in lowered:
                return True
        elif keyword_matches(hint, path):
            return True
    return False


def _is_supply_chain_review_path(path: str, config: Config) -> bool:
    lower = path.lower()
    return (
        lower.startswith(".github/workflows/")
        or path_matches(path, config.paths.dependency)
        or path_matches(path, config.paths.release)
    )


def detect_documentation_impact(files: list[dict], config: Config, security_touched: bool) -> Impact:
    paths = file_paths(files)
    docs = [path for path in paths if path_matches(path, config.paths.docs)]
    behavior = [
        path
        for path in paths
        if not path_matches(path, config.paths.docs)
        and any(
            keyword_matches(term, path)
            for term in ("api", "cli", "config", "auth", "permission", "public", "feature")
        )
    ]
    breaking = bool(breaking_change_signals(files))
    if docs:
        return Impact("Low", "Documentation or examples changed with the pull request.", docs, confidence="High")
    if behavior or security_touched or breaking:
        return Impact(
            "Medium",
            "The change may affect user-visible or security-related behavior, but documentation files did not change.",
            behavior,
            ["Review README, docs, examples, changelog, and migration guidance for required updates."],
            confidence="Medium",
        )
    return Impact("None", "No documentation drift signal was detected.", confidence="High")


def detect_dependency_impact(files: list[dict], config: Config) -> Impact:
    affected = [path for path in file_paths(files) if path_matches(path, config.paths.dependency)]
    if not affected:
        return Impact("None", "No dependency or package-manager files changed.", confidence="High")
    patch = "\n".join(str(item.get("patch", "")) for item in files if item.get("path") in affected).lower()
    actions = ["Review dependency provenance, version changes, and scanner findings."]
    signals = _dependency_signals(files, affected)
    level = "Medium"
    if "postinstall" in patch or "preinstall" in patch:
        level = "High"
        signals.append("Install-time package script signal detected.")
        actions.append("Review newly introduced install-time scripts before merge.")
    if "curl " in patch or "wget " in patch or " | sh" in patch:
        level = "High"
        signals.append("Install-time or remote-download script signal detected.")
        actions.append("Review remote-download build or install script changes before merge.")
    if any(path.startswith(".github/workflows/") for path in affected):
        signals.append("CI workflow changed.")
        actions.append("Confirm CI workflow permission changes are intentional.")
    if any(path.lower().startswith(("dockerfile", "containerfile")) for path in affected):
        signals.append("Container build definition changed.")
        actions.append("Review container base image, package installation, and network fetches.")
    if any("release" in path.lower() for path in affected):
        signals.append("Release or publishing path changed.")
        actions.append("Check release workflow changes carefully before shipping.")
    if any("sbom" in path.lower() or "provenance" in path.lower() or "attestation" in path.lower() for path in affected):
        signals.append("SBOM, provenance, or attestation metadata changed.")
        actions.append("Verify supply-chain metadata matches the intended release inputs.")
    return Impact(
        level,
        "Dependency or supply-chain-sensitive files changed.",
        affected,
        actions,
        confidence="High",
        signals=signals,
    )


def detect_release_impact(files: list[dict], config: Config) -> Impact:
    affected = [path for path in file_paths(files) if path_matches(path, config.paths.release)]
    patch = "\n".join(str(item.get("patch", "")) for item in files).lower()
    breaking = bool(breaking_change_signals(files))
    if affected or breaking:
        actions = ["Confirm changelog and release notes describe the change."]
        if any(path.startswith(".github/workflows/") for path in affected):
            actions.append("Review workflow permissions, actions, and publishing behavior.")
        signals = []
        if any(path.startswith(".github/workflows/") for path in affected):
            signals.append("CI or GitHub workflow changed.")
        if "permissions:" in patch:
            signals.append("Workflow permission configuration changed.")
        if breaking:
            signals.append("Possible breaking-change language detected.")
        return Impact(
            "High" if breaking else "Medium",
            "Release-sensitive files or breaking-change signals were detected.",
            affected,
            actions,
            confidence="Medium",
            signals=signals,
        )
    return Impact("None", "No release-impact signal was detected.", confidence="High")


def breaking_change_signals(files: list[dict]) -> list[tuple[str, str]]:
    """Structural breaking-change signals.

    Searching a whole patch for words like `remove` or `deprecated` fired on
    comments and prose: a diff whose only content was `# remove trailing
    whitespace` was reported as a breaking change and escalated release impact to
    High. Only removed declarations, deleted files, and explicit markers count.
    """
    signals: list[tuple[str, str]] = []
    for item in files:
        path = str(item.get("path", "unknown file"))
        status = str(item.get("status", "modified")).strip().lower()
        if status in _REMOVED_STATUSES:
            signals.append((path, "the file was deleted"))
            continue
        if status in _RENAMED_STATUSES:
            signals.append((path, "the file was renamed"))
            continue
        for line in str(item.get("patch", "")).splitlines():
            if _EXPLICIT_BREAKING.search(line):
                signals.append((path, "the diff declares a breaking change"))
                break
            if line.startswith("-") and not line.startswith("---") and _DECLARATION.search(line[1:]):
                signals.append((path, "a declaration was removed or changed"))
                break
    return signals


def possible_breaking_changes(files: list[dict]) -> list[str]:
    return [
        f"Review possible behavior or interface change in {path}: {reason}."
        for path, reason in breaking_change_signals(files)
    ]


def _dependency_signals(files: list[dict], affected: list[str]) -> list[str]:
    signals: list[str] = []
    if affected and all(_is_lockfile(path) for path in affected):
        signals.append("Lockfile-only dependency change detected.")
    removed: dict[str, str] = {}
    added: dict[str, str] = {}
    for item in files:
        if item.get("path") not in affected:
            continue
        for line in str(item.get("patch", "")).splitlines():
            if not line or line.startswith(("+++", "---")):
                continue
            parsed = _dependency_declaration(line[1:].strip())
            if not parsed:
                continue
            name, version = parsed
            if line.startswith("-"):
                removed[name] = version
            elif line.startswith("+"):
                added[name] = version
    for name in sorted(set(removed) | set(added)):
        if name in removed and name in added and removed[name] != added[name]:
            direction = _version_direction(removed[name], added[name])
            signals.append(f"{direction} {name} from {removed[name]} to {added[name]}.")
        elif name in added and name not in removed:
            signals.append(f"Added dependency {name} {added[name]}.")
        elif name in removed and name not in added:
            signals.append(f"Removed dependency {name} {removed[name]}.")
    return signals[:20]


def _dependency_declaration(line: str) -> tuple[str, str] | None:
    match = re.match(r'["\']?([A-Za-z0-9_.-]+)["\']?\s*(?:==|:|@)\s*["\']?([^"\',\s]+)', line)
    if not match:
        return None
    return match.group(1), match.group(2)


def _is_lockfile(path: str) -> bool:
    lower = path.lower()
    return lower.endswith((".lock", ".lock.json")) or lower in {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "cargo.lock",
        "go.sum",
    }


def _version_direction(old: str, new: str) -> str:
    old_parts = tuple(int(part) for part in re.findall(r"\d+", old))
    new_parts = tuple(int(part) for part in re.findall(r"\d+", new))
    if old_parts and new_parts:
        if new_parts > old_parts:
            return "Upgraded"
        if new_parts < old_parts:
            return "Downgraded"
    return "Updated"
