"""Repository-specific policy evaluation."""

from __future__ import annotations

from .config import Config
from .detectors import file_paths, path_matches
from .models import Impact, PolicyResult


def evaluate_policies(
    files: list[dict],
    config: Config,
    test_impact: Impact,
    documentation_impact: Impact,
    scanner_count: int,
    evidence_for_path: dict[str, str],
) -> list[PolicyResult]:
    paths = file_paths(files)
    results = []
    for policy in config.policies:
        matched = [path for path in paths if path_matches(path, policy.paths)]
        if not matched:
            continue
        passed = {
            "tests": test_impact.level == "Low",
            "docs": documentation_impact.level == "Low",
            "scanner": scanner_count > 0,
            "manual_review": False,
        }[policy.require]
        evidence_ids = [evidence_for_path[path] for path in matched if path in evidence_for_path]
        message = policy.message or (
            f"Policy '{policy.name}' passed." if passed else f"Policy '{policy.name}' requires attention."
        )
        results.append(PolicyResult(policy.name, passed, policy.blocking, message, evidence_ids))
    return results
