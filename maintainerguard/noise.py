"""Evidence-required duplicate and noise filtering."""

from __future__ import annotations

from .models import Evidence, Reason, ScannerFinding


def filter_reasons(reasons: list[Reason], evidence: list[Evidence]) -> list[Reason]:
    known = {item.id for item in evidence}
    seen: set[tuple[str, tuple[str, ...]]] = set()
    output = []
    for reason in reasons:
        refs = tuple(sorted(set(reason.evidence_ids)))
        key = (reason.text.strip().lower(), refs)
        if not reason.text.strip() or not refs or not set(refs).issubset(known) or key in seen:
            continue
        seen.add(key)
        output.append(reason)
    return output


def filter_scanner_findings(findings: list[ScannerFinding]) -> list[ScannerFinding]:
    seen: set[tuple[str, str]] = set()
    output = []
    for finding in findings:
        key = (finding.scanner.lower(), finding.id.lower())
        if key in seen or not finding.title.strip():
            continue
        seen.add(key)
        output.append(finding)
    return output
