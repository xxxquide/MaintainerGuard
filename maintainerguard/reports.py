"""Markdown-first and JSON report rendering."""

from __future__ import annotations

import json
from typing import Any

from .models import IssueTriageReport, MergeReadinessReport, ReleaseReadinessReport


def render_report(report: Any, *, output_format: str = "markdown", mode: str = "concise") -> str:
    if output_format == "json":
        return json.dumps(report.to_dict(), indent=2, sort_keys=True)
    if output_format != "markdown":
        raise ValueError("output_format must be markdown or json")
    if isinstance(report, MergeReadinessReport):
        return _render_merge(report, mode)
    if isinstance(report, IssueTriageReport):
        return _render_issue(report)
    if isinstance(report, ReleaseReadinessReport):
        return _render_release(report)
    raise TypeError(f"Unsupported report type: {type(report).__name__}")


def _render_merge(report: MergeReadinessReport, mode: str) -> str:
    lines = [
        "# MaintainerGuard Merge Readiness Report",
        "",
        f"**Verdict:** {report.verdict}",
        "",
        f"**Overall risk:** {report.risk_level}",
        "",
        f"**Confidence:** {report.confidence}",
        "",
        "## Executive summary",
        "",
        report.executive_summary,
    ]
    if report.skipped:
        lines.extend(["", "## Limitations", "", *[f"- {item}" for item in report.limitations]])
        return "\n".join(lines) + "\n"
    lines.extend(["", "## Key changes", "", *(_bullets(report.changed_areas) or ["- No changed areas identified."])])
    if report.ai_summary:
        lines.extend(["", "## Optional AI enrichment", "", report.ai_summary])
        lines.extend(_bullets([item.text for item in report.ai_claims]))
    lines.extend(["", "## Why this requires review", "", *(_bullets([item.text for item in report.reasons]) or ["- No elevated review signals detected."])])
    lines.extend(
        [
            "",
            "## Decision guidance",
            "",
            f"**Recommended maintainer action:** {report.decision_guidance}",
            "",
            f"**Reason:** {report.decision_reason}",
        ]
    )
    lines.extend(["", "## Security-sensitive areas", ""])
    lines.extend(
        _bullets(
            [
                f"{item.category}: {', '.join(item.affected_files)}. {item.review_guidance}"
                for item in report.security_sensitive_areas
            ]
        )
        or ["- None detected."]
    )
    lines.extend(["", "## Scanner findings", ""])
    lines.extend(
        _bullets(
            [
                (
                    f"{item.severity} - {item.scanner} ({item.category}) - {item.title}: "
                    f"{item.explanation} Recommendation: {item.recommendation or 'Review the supplied scanner evidence before merge.'}"
                )
                for item in report.scanner_findings
            ]
        )
        or ["- No supplied scanner findings."]
    )
    for title, impact in (
        ("Dependency and supply-chain impact", report.dependency_impact),
        ("Test impact", report.test_impact),
        ("Documentation impact", report.documentation_impact),
        ("Release impact", report.release_impact),
    ):
        lines.extend(["", f"## {title}", "", f"**{impact.level}:** {impact.summary}"])
        if impact.signals:
            lines.extend(["", *_bullets(impact.signals)])
        if mode == "detailed" and impact.suggested_actions:
            lines.extend(["", *_bullets(impact.suggested_actions)])
    lines.extend(["", "## Possible breaking changes", ""])
    lines.extend(_bullets(report.possible_breaking_changes) or ["- None detected."])
    lines.extend(["", "## Policy checks", ""])
    lines.extend(
        _bullets(
            [
                f"{'Passed' if item.passed else 'Attention required'} - {item.name}: {item.message}"
                for item in report.policy_results
            ]
        )
        or ["- No configured policy matched the changed files."]
    )
    lines.extend(["", "## Maintainer checklist", "", *(_bullets([item.text for item in report.checklist]) or ["- Complete normal maintainer review."])])
    lines.extend(["", "## Evidence", "", "| ID | Claim | Evidence | Confidence |", "|---|---|---|---|"])
    for item in report.evidence:
        lines.append(f"| `{item.id}` | {_cell(item.claim)} | {_cell(f'{item.source_type}: {item.source}; {item.detail}')} | {item.confidence} |")
    lines.extend(["", "## Limitations", "", *_bullets(report.limitations)])
    return "\n".join(lines) + "\n"


def _render_issue(report: IssueTriageReport) -> str:
    lines = [
        "# MaintainerGuard Issue Triage Report",
        "",
        f"**Issue type:** {report.issue_type}  ",
        f"**Confidence:** {report.confidence}  ",
        f"**Suggested priority:** {report.priority}",
        "",
        "## Suggested labels",
        "",
        *(_bullets(report.suggested_labels) or ["- None"]),
        "",
        "## Missing information",
        "",
        *(_bullets(report.missing_information) or ["- None detected."]),
        "",
        "## Possible duplicates",
        "",
        *(_bullets(report.possible_duplicates) or ["- None suggested from supplied candidates."]),
        "",
        "## Next action",
        "",
        report.next_action,
        "",
        "## Suggested response",
        "",
        report.suggested_response,
        "",
        "## Evidence",
        "",
        "| ID | Claim | Evidence | Confidence |",
        "|---|---|---|---|",
        *[
            f"| `{item.id}` | {_cell(item.claim)} | {_cell(f'{item.source_type}: {item.source}; {item.detail}')} | {item.confidence} |"
            for item in report.evidence
        ],
        "",
        "## Limitations",
        "",
        *_bullets(report.limitations),
    ]
    return "\n".join(lines) + "\n"


def _render_release(report: ReleaseReadinessReport) -> str:
    lines = [
        "# MaintainerGuard Release Readiness Report",
        "",
        f"**Version:** {report.version}  ",
        f"**Release verdict:** {report.verdict}  ",
        f"**Overall risk:** {report.risk_level}",
        "",
        "## Executive summary",
        "",
        report.executive_summary,
        "",
        "## Notable changes",
        "",
        *(_bullets(report.notable_changes) or ["- None supplied."]),
        "",
        "## Breaking changes",
        "",
        *(_bullets(report.breaking_changes) or ["- None detected."]),
        "",
        "## Security-sensitive changes",
        "",
        *(_bullets(report.security_sensitive_changes) or ["- None detected."]),
        "",
        "## Dependency changes",
        "",
        *(_bullets(report.dependency_changes) or ["- None detected."]),
        "",
        "## Scanner findings",
        "",
        *(_bullets(report.scanner_findings) or ["- No supplied scanner findings."]),
        "",
        "## Documentation status",
        "",
        report.docs_status,
        "",
        "## Test status",
        "",
        report.tests_status,
        "",
        "## Unresolved high-risk items",
        "",
        *(_bullets(report.unresolved_high_risk_items) or ["- None supplied or detected."]),
        "",
        "## Suggested release checklist",
        "",
        *_bullets(report.release_checklist),
        "",
        "## Generated release notes draft",
        "",
        report.release_notes,
        "",
        "## Evidence",
        "",
        "| ID | Claim | Evidence | Confidence |",
        "|---|---|---|---|",
        *[
            f"| `{item.id}` | {_cell(item.claim)} | {_cell(f'{item.source_type}: {item.source}; {item.detail}')} | {item.confidence} |"
            for item in report.evidence
        ],
        "",
        "## Limitations",
        "",
        *_bullets(report.limitations),
    ]
    return "\n".join(lines) + "\n"


def _bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items if item]


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
