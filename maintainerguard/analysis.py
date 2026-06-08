"""Evidence-first deterministic pull-request analysis."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .config import Config, load_config
from .detectors import (
    changed_areas,
    detect_dependency_impact,
    detect_documentation_impact,
    detect_release_impact,
    detect_security_files,
    detect_test_impact,
    path_matches,
    possible_breaking_changes,
)
from .evidence import make_evidence
from .models import (
    ChecklistItem,
    Evidence,
    MergeReadinessReport,
    Reason,
    ScannerFinding,
    SecuritySensitiveArea,
)
from .noise import filter_reasons, filter_scanner_findings
from .policies import evaluate_policies
from .scanners import normalize_scanner_input


def analyze_pull_request(
    pull_request: dict[str, Any],
    *,
    scanner_inputs: list[dict[str, Any]] | None = None,
    config: Config | None = None,
) -> MergeReadinessReport:
    config = config or load_config()
    if not isinstance(pull_request, dict):
        raise ValueError("Pull request input must be a JSON object")
    labels = _labels(pull_request.get("labels", []))
    skip_reason = _skip_reason(pull_request, labels, config)
    if skip_reason:
        return MergeReadinessReport(
            executive_summary=f"Analysis skipped: {skip_reason}",
            skipped=True,
            skip_reason=skip_reason,
            limitations=["No merge-readiness conclusion was produced because analysis was skipped."],
        )

    raw_files = pull_request.get("files", [])
    if not isinstance(raw_files, list) or not raw_files:
        return MergeReadinessReport(
            executive_summary="No changed-file information was supplied.",
            limitations=[
                "Changed files are required for deterministic pull-request analysis.",
                "This report does not replace human review.",
            ],
        )
    files, diff_truncated = _bounded_files(raw_files, config)
    evidence: list[Evidence] = []
    evidence_for_path: dict[str, str] = {}
    for item in files:
        path = str(item["path"])
        detail = f"{item.get('status', 'modified')} file"
        patch = str(item.get("patch", ""))
        if patch:
            detail += f"; supplied patch length {min(len(patch), config.privacy.max_diff_characters)} characters"
        item_evidence = make_evidence(f"{path} changed", "changed_file", path, detail)
        evidence.append(item_evidence)
        evidence_for_path[path] = item_evidence.id

    security_areas: list[SecuritySensitiveArea] = []
    if config.modules.security:
        for category, affected, explanation, guidance in detect_security_files(files, config):
            refs = [evidence_for_path[path] for path in affected]
            security_areas.append(
                SecuritySensitiveArea(category, affected, explanation, guidance, "High", refs)
            )
    test_impact = detect_test_impact(files, config, bool(security_areas)) if config.modules.tests else _disabled_impact("Test")
    docs_impact = detect_documentation_impact(files, config, bool(security_areas)) if config.modules.documentation else _disabled_impact("Documentation")
    dependency_impact = detect_dependency_impact(files, config) if config.modules.dependencies else _disabled_impact("Dependency")
    release_impact = detect_release_impact(files, config) if config.modules.release else _disabled_impact("Release")
    test_impact = _attach_path_evidence(test_impact, evidence_for_path)
    docs_impact = _attach_path_evidence(docs_impact, evidence_for_path)
    dependency_impact = _attach_path_evidence(dependency_impact, evidence_for_path)
    release_impact = _attach_path_evidence(release_impact, evidence_for_path)

    scanner_findings: list[ScannerFinding] = []
    if config.modules.scanners:
        for scanner_input in scanner_inputs or []:
            for finding in normalize_scanner_input(scanner_input):
                ev = make_evidence(
                    f"{finding.scanner} reported {finding.id}",
                    "scanner_finding",
                    finding.id,
                    finding.explanation,
                )
                evidence.append(ev)
                scanner_findings.append(replace(finding, evidence_ids=[ev.id]))
    scanner_findings = filter_scanner_findings(scanner_findings)

    policy_results = (
        evaluate_policies(files, config, test_impact, docs_impact, len(scanner_inputs or []), evidence_for_path)
        if config.modules.policies
        else []
    )
    reasons = _build_reasons(
        security_areas,
        scanner_findings,
        dependency_impact,
        test_impact,
        docs_impact,
        release_impact,
        policy_results,
    )
    reasons = filter_reasons(reasons, evidence)
    risk_level = _risk_level(reasons, scanner_findings, policy_results, config)
    verdict = _verdict(
        scanner_findings,
        policy_results,
        test_impact,
        security_areas,
        docs_impact,
        reasons,
    )
    checklist = _checklist(
        security_areas,
        scanner_findings,
        dependency_impact,
        test_impact,
        docs_impact,
        release_impact,
        policy_results,
    )
    title = str(pull_request.get("title", "Untitled pull request"))
    areas = changed_areas(files)
    summary = _summary(title, areas, risk_level, verdict, reasons)
    decision_guidance, decision_reason = _decision_guidance(
        verdict,
        risk_level,
        reasons,
        scanner_findings,
        security_areas,
        test_impact,
        docs_impact,
    )
    confidence = "High" if files and evidence else "Low"
    if any(item.confidence == "Medium" for item in reasons):
        confidence = "Medium"
    limitations = [
        "MaintainerGuard identifies review signals; it does not prove the presence or absence of vulnerabilities.",
        "Absence-based test and documentation signals are inferred from supplied changed-file data.",
        "This report supports, but does not replace, human maintainer review.",
    ]
    if len(raw_files) > config.privacy.max_files_analyzed:
        limitations.append(
            f"Only the first {config.privacy.max_files_analyzed} changed files were analyzed."
        )
    if diff_truncated:
        limitations.append(
            f"Supplied diff input was truncated to {config.privacy.max_diff_characters} characters before analysis."
        )
    return MergeReadinessReport(
        verdict=verdict,
        risk_level=risk_level,
        confidence=confidence,
        executive_summary=summary,
        decision_guidance=decision_guidance,
        decision_reason=decision_reason,
        changed_areas=areas,
        reasons=reasons,
        security_sensitive_areas=security_areas,
        scanner_findings=scanner_findings,
        dependency_impact=dependency_impact,
        test_impact=test_impact,
        documentation_impact=docs_impact,
        release_impact=release_impact,
        possible_breaking_changes=possible_breaking_changes(files),
        policy_results=policy_results,
        checklist=checklist,
        evidence=evidence,
        limitations=limitations,
    )


def _labels(raw: Any) -> list[str]:
    output = []
    for label in raw if isinstance(raw, list) else []:
        output.append(str(label.get("name", "")) if isinstance(label, dict) else str(label))
    return output


def _bounded_files(raw_files: list[Any], config: Config) -> tuple[list[dict[str, Any]], bool]:
    files: list[dict[str, Any]] = []
    remaining = config.privacy.max_diff_characters
    truncated = False
    for raw in raw_files[: config.privacy.max_files_analyzed]:
        if not isinstance(raw, dict) or not raw.get("path"):
            continue
        path = str(raw["path"])
        if path_matches(path, config.paths.ignore):
            continue
        item = dict(raw)
        patch = str(item.get("patch", ""))
        if len(patch) > remaining:
            patch = patch[:remaining]
            truncated = True
        item["patch"] = patch
        remaining -= len(patch)
        if remaining <= 0 and any(
            isinstance(other, dict) and str(other.get("patch", ""))
            for other in raw_files[len(files) + 1 :]
        ):
            truncated = True
        files.append(item)
    return files, truncated


def _skip_reason(pr: dict[str, Any], labels: list[str], config: Config) -> str:
    if set(labels) & set(config.github.skip_labels):
        return "a configured skip label is present"
    return ""


def _attach_path_evidence(impact, evidence_for_path: dict[str, str]):
    refs = [evidence_for_path[path] for path in impact.affected_files if path in evidence_for_path]
    return replace(impact, evidence_ids=refs)


def _disabled_impact(name: str):
    from .models import Impact

    return Impact("Disabled", f"{name} analysis is disabled by configuration.", confidence="High")


def _build_reasons(security, scanners, dependency, tests, docs, release, policies) -> list[Reason]:
    reasons: list[Reason] = []
    for area in security:
        reasons.append(Reason(f"Security-sensitive area touched: {area.category}.", area.evidence_ids, area.confidence, "High", "security"))
    for finding in scanners:
        reasons.append(Reason(f"{finding.scanner} reported {finding.title}.", finding.evidence_ids, "High", finding.severity, "scanner"))
    for impact, category in (
        (dependency, "dependency"),
        (tests, "tests"),
        (docs, "documentation"),
        (release, "release"),
    ):
        if impact.level not in {"None", "Low", "Disabled"} and impact.evidence_ids:
            reasons.append(Reason(impact.summary, impact.evidence_ids, impact.confidence, impact.level, category))
    for policy in policies:
        if not policy.passed:
            reasons.append(Reason(policy.message, policy.evidence_ids, "High", "High" if policy.blocking else "Medium", "policy"))
    return reasons


def _risk_level(reasons, scanners, policies, config: Config) -> str:
    if any(item.severity == "Critical" and item.blocking for item in scanners) or any(
        not item.passed and item.blocking for item in policies
    ):
        return "Critical"
    score = 0
    weights = {"Low": 1, "Medium": 3, "High": 7, "Critical": 12, "Unknown": 2}
    for reason in reasons:
        score = max(score, weights.get(reason.severity, 2))
    if score >= config.thresholds.high:
        return "High"
    if score >= config.thresholds.medium:
        return "Medium"
    return "Low"


def _verdict(scanners, policies, tests, security, docs, reasons) -> str:
    if any(item.blocking for item in scanners):
        return "Blocked by scanner finding"
    if any(not item.passed and item.blocking for item in policies):
        return "Changes requested"
    if tests.level == "High":
        return "Tests required"
    if security:
        return "Security review recommended"
    if docs.level == "Medium":
        return "Documentation update recommended"
    if reasons:
        return "Review required"
    return "Ready for maintainer review"


def _checklist(security, scanners, dependency, tests, docs, release, policies) -> list[ChecklistItem]:
    items: list[ChecklistItem] = []
    for area in security:
        items.append(ChecklistItem(area.review_guidance, area.evidence_ids, "High"))
    for finding in scanners:
        items.append(ChecklistItem(f"Review {finding.scanner} finding {finding.id} before merge.", finding.evidence_ids, finding.severity))
    for impact in (dependency, tests, docs, release):
        for action in impact.suggested_actions:
            if impact.evidence_ids:
                items.append(ChecklistItem(action, impact.evidence_ids, impact.level))
    for policy in policies:
        if not policy.passed:
            items.append(ChecklistItem(policy.message, policy.evidence_ids, "High" if policy.blocking else "Medium"))
    seen = set()
    return [item for item in items if not (item.text in seen or seen.add(item.text))]


def _summary(title: str, areas: list[str], risk: str, verdict: str, reasons: list[Reason]) -> str:
    area_text = ", ".join(areas) if areas else "unknown areas"
    reason_text = reasons[0].text if reasons else "No elevated deterministic review signals were detected."
    return f'"{title}" affects {area_text}. Verdict: {verdict}. Overall risk: {risk}. {reason_text}'


def _decision_guidance(
    verdict: str,
    risk_level: str,
    reasons: list[Reason],
    scanners: list[ScannerFinding],
    security: list[SecuritySensitiveArea],
    tests,
    docs,
) -> tuple[str, str]:
    guidance = {
        "Ready for maintainer review": "Looks safe for normal review",
        "Review required": "Review carefully",
        "Security review recommended": "Request security review",
        "Tests required": "Request tests",
        "Documentation update recommended": "Request documentation update",
        "Blocked by scanner finding": "Block until scanner finding is resolved",
        "Changes requested": "Review carefully",
        "Not enough information": "Not enough information",
    }.get(verdict, "Review carefully")
    if risk_level == "Critical" and scanners:
        guidance = "Block until scanner finding is resolved"
    reason_parts: list[str] = []
    if scanners:
        reason_parts.append(
            "scanner evidence includes "
            + ", ".join(f"{item.severity.lower()} {item.scanner} finding {item.id}" for item in scanners[:3])
        )
    if security:
        reason_parts.append(
            "security-sensitive areas were touched: "
            + ", ".join(item.category for item in security[:3])
        )
    if tests.level == "High":
        reason_parts.append("related tests were not supplied for behavior that may need coverage")
    if docs.level == "Medium":
        reason_parts.append("documentation may need review because no related docs changed")
    if not reason_parts and reasons:
        reason_parts.append(reasons[0].text)
    if not reason_parts:
        reason_parts.append("no elevated deterministic review signals were detected")
    return guidance, "A maintainer should act on this recommendation because " + "; ".join(reason_parts) + "."
