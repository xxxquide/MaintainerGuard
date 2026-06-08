"""Typed models shared by MaintainerGuard modules."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


class Serializable:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Evidence(Serializable):
    id: str
    claim: str
    source_type: str
    source: str
    detail: str
    confidence: str = "High"


@dataclass(frozen=True)
class Reason(Serializable):
    text: str
    evidence_ids: list[str]
    confidence: str
    severity: str = "Medium"
    category: str = "review"


@dataclass(frozen=True)
class ChecklistItem(Serializable):
    text: str
    evidence_ids: list[str]
    priority: str = "Medium"


@dataclass(frozen=True)
class SecuritySensitiveArea(Serializable):
    category: str
    affected_files: list[str]
    explanation: str
    review_guidance: str
    confidence: str
    evidence_ids: list[str]


@dataclass(frozen=True)
class Impact(Serializable):
    level: str
    summary: str
    affected_files: list[str] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    confidence: str = "Medium"
    signals: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScannerFinding(Serializable):
    id: str
    scanner: str
    severity: str
    title: str
    explanation: str
    category: str = "generic"
    description: str = ""
    affected: list[str] = field(default_factory=list)
    affected_dependency: str = ""
    advisory_id: str = ""
    recommendation: str = ""
    blocking: bool = False
    evidence_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PolicyResult(Serializable):
    name: str
    passed: bool
    blocking: bool
    message: str
    evidence_ids: list[str]


@dataclass
class MergeReadinessReport(Serializable):
    report_type: str = "merge_readiness_report"
    schema_version: str = "1.0"
    verdict: str = "Not enough information"
    risk_level: str = "Unknown"
    confidence: str = "Low"
    executive_summary: str = ""
    decision_guidance: str = "Not enough information"
    decision_reason: str = ""
    ai_summary: str = ""
    ai_claims: list[Reason] = field(default_factory=list)
    changed_areas: list[str] = field(default_factory=list)
    reasons: list[Reason] = field(default_factory=list)
    security_sensitive_areas: list[SecuritySensitiveArea] = field(default_factory=list)
    scanner_findings: list[ScannerFinding] = field(default_factory=list)
    dependency_impact: Impact = field(
        default_factory=lambda: Impact("None", "No dependency impact detected.")
    )
    test_impact: Impact = field(
        default_factory=lambda: Impact("None", "No test impact detected.")
    )
    documentation_impact: Impact = field(
        default_factory=lambda: Impact("None", "No documentation impact detected.")
    )
    release_impact: Impact = field(
        default_factory=lambda: Impact("None", "No release impact detected.")
    )
    possible_breaking_changes: list[str] = field(default_factory=list)
    policy_results: list[PolicyResult] = field(default_factory=list)
    checklist: list[ChecklistItem] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


@dataclass
class IssueTriageReport(Serializable):
    report_type: str = "issue_triage_report"
    schema_version: str = "1.0"
    issue_type: str = "Unclear issue"
    confidence: str = "Low"
    suggested_labels: list[str] = field(default_factory=list)
    priority: str = "Normal"
    missing_information: list[str] = field(default_factory=list)
    possible_duplicates: list[str] = field(default_factory=list)
    next_action: str = ""
    suggested_response: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class ReleaseReadinessReport(Serializable):
    report_type: str = "release_readiness_report"
    schema_version: str = "1.0"
    version: str = "Unspecified"
    verdict: str = "Not enough information"
    risk_level: str = "Unknown"
    executive_summary: str = ""
    notable_changes: list[str] = field(default_factory=list)
    breaking_changes: list[str] = field(default_factory=list)
    security_sensitive_changes: list[str] = field(default_factory=list)
    dependency_changes: list[str] = field(default_factory=list)
    scanner_findings: list[str] = field(default_factory=list)
    docs_status: str = ""
    tests_status: str = ""
    unresolved_high_risk_items: list[str] = field(default_factory=list)
    release_notes: str = ""
    release_checklist: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CommentAction(Serializable):
    action: str
    comment_id: int | None = None
    body: str = ""
