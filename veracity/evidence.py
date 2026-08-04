"""Evidence creation and validation helpers."""

from __future__ import annotations

import hashlib

from .models import Evidence


def evidence_id(source_type: str, source: str, claim: str) -> str:
    value = f"{source_type}\0{source}\0{claim}".encode("utf-8")
    return f"ev-{hashlib.sha256(value).hexdigest()[:12]}"


def make_evidence(
    claim: str,
    source_type: str,
    source: str,
    detail: str,
    confidence: str = "High",
) -> Evidence:
    return Evidence(
        id=evidence_id(source_type, source, claim),
        claim=claim,
        source_type=source_type,
        source=source,
        detail=detail,
        confidence=confidence,
    )


def valid_evidence_references(evidence_ids: list[str], evidence: list[Evidence]) -> bool:
    known = {item.id for item in evidence}
    return bool(evidence_ids) and set(evidence_ids).issubset(known)
