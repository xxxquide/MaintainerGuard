"""Evidence-backed issue triage."""

from __future__ import annotations

from typing import Any

from .evidence import make_evidence
from .models import IssueTriageReport


def triage_issue(issue: dict[str, Any]) -> IssueTriageReport:
    if not isinstance(issue, dict):
        raise ValueError("Issue input must be a JSON object")
    title = str(issue.get("title", "")).strip()
    body = str(issue.get("body", "")).strip()
    combined = f"{title}\n{body}".lower()
    evidence = [
        make_evidence("Issue title supplied", "issue_metadata", "title", title or "No title", "High"),
        make_evidence("Issue body supplied", "issue_metadata", "body", body or "No body", "High"),
    ]
    if any(term in combined for term in ("security", "vulnerability", "credential", "token exposure", "secret exposure")):
        issue_type, confidence, labels = "Security report", "Medium", ["security", "needs-maintainer-review"]
    elif "regression" in combined or "worked in" in combined:
        issue_type, confidence, labels = "Regression report", "Medium", ["bug", "regression"]
    elif any(term in combined for term in ("dependency", "dependencies", "advisory", "osv", "cve", "package update")):
        issue_type, confidence, labels = "Dependency issue", "Medium", ["dependencies"]
    elif any(term in combined for term in ("crash", "error", "bug", "fails", "broken", "exception")):
        issue_type, confidence, labels = "Bug report", "Medium", ["bug"]
    elif any(term in combined for term in ("feature", "request", "would like", "enhancement")):
        issue_type, confidence, labels = "Feature request", "Medium", ["enhancement"]
    elif any(term in combined for term in ("docs", "documentation", "readme", "typo")):
        issue_type, confidence, labels = "Documentation issue", "High", ["documentation"]
    elif "support" in combined:
        issue_type, confidence, labels = "Support request", "Medium", ["support"]
    elif "?" in combined or any(term in combined for term in ("how do", "help")):
        issue_type, confidence, labels = "Question", "Medium", ["question"]
    else:
        issue_type, confidence, labels = "Unclear issue", "Low", ["needs-triage"]
    missing: list[str] = []
    if issue_type in {"Bug report", "Regression report", "Dependency issue"}:
        checks = {
            "reproduction steps": ("steps", "reproduce", "reproduction", "minimal example"),
            "package version": ("version",),
            "operating system or environment": ("operating system", " os ", "linux", "macos", "windows", "environment"),
            "expected and actual behavior": ("expected", "actual"),
            "full error log": ("stack trace", "traceback", "full error", "log"),
        }
        for name, terms in checks.items():
            if not any(term in f" {combined} " for term in terms):
                missing.append(name)
        labels.extend(f"needs-{name.replace(' ', '-')}" for name in missing[:2])
    candidates = issue.get("duplicate_candidates", [])
    duplicates = [
        str(item.get("title", item))
        for item in candidates
        if isinstance(item, (str, dict))
        and _overlap(title, str(item.get("title", "")) if isinstance(item, dict) else item)
    ]
    if issue_type == "Security report":
        next_action = "Handle through the project's responsible disclosure process before public technical detail expansion."
        response = (
            "Thanks for flagging this. Please share sensitive details through the project's responsible "
            "disclosure channel rather than expanding them publicly here. A maintainer should review and "
            "coordinate next steps."
        )
    elif missing:
        next_action = "Request the missing information before investigation."
        requested = ", ".join(missing)
        response = f"Thanks for the report. Could you please provide {requested}? That will help maintainers investigate efficiently."
    else:
        next_action = "A maintainer can review and prioritize this issue."
        response = "Thanks for the clear report. A maintainer can now review and prioritize it."
    return IssueTriageReport(
        issue_type=issue_type,
        confidence=confidence,
        suggested_labels=sorted(set(labels)),
        priority="High" if any(term in combined for term in ("security", "data loss", "regression", "credential")) else "Normal",
        missing_information=missing,
        possible_duplicates=duplicates,
        next_action=next_action,
        suggested_response=response,
        evidence=evidence,
        limitations=[
            "Issue classification is heuristic and should be confirmed by a maintainer.",
            "Duplicate suggestions are limited to supplied candidate issues.",
        ],
    )


def _overlap(left: str, right: str) -> bool:
    left_words = {word for word in left.lower().split() if len(word) > 3}
    right_words = {word for word in right.lower().split() if len(word) > 3}
    return bool(left_words & right_words)
