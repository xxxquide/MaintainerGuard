"""Optional, bounded AI enrichment with deterministic validation."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .config import AIConfig, Config
from .models import MergeReadinessReport, Reason
from .privacy import redact_value
from .prompts import AI_OUTPUT_SCHEMA, SYSTEM_INSTRUCTION


class AIError(RuntimeError):
    pass


def validate_ai_enrichment(payload: Any, valid_evidence_ids: set[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"summary": "", "claims": []}
    summary = payload.get("summary", "")
    if not isinstance(summary, str):
        summary = ""
    claims = []
    for item in payload.get("claims", []):
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        refs = item.get("evidence_ids")
        confidence = item.get("confidence", "Low")
        if (
            isinstance(text, str)
            and text.strip()
            and isinstance(refs, list)
            and refs
            and all(isinstance(ref, str) and ref in valid_evidence_ids for ref in refs)
            and confidence in {"Low", "Medium", "High"}
        ):
            claims.append({"text": text.strip(), "evidence_ids": refs, "confidence": confidence})
    return {"summary": summary.strip(), "claims": claims}


def enrich_with_openai(
    report_data: dict[str, Any],
    config: AIConfig,
    valid_evidence_ids: set[str],
) -> dict[str, Any]:
    if not config.enabled:
        return {"summary": "", "claims": []}
    if config.provider != "openai":
        raise AIError(f"Unsupported AI provider: {config.provider}")
    if not config.model:
        raise AIError("AI model must be configured when AI is enabled")
    api_key = os.environ.get(config.api_key_env)
    if not api_key:
        raise AIError(f"AI is enabled but {config.api_key_env} is not set")
    bounded = json.dumps(redact_value(report_data), separators=(",", ":"))[:30000]
    payload = {
        "model": config.model,
        "store": False,
        "instructions": SYSTEM_INSTRUCTION,
        "input": bounded,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "maintainerguard_enrichment",
                "strict": True,
                "schema": AI_OUTPUT_SCHEMA,
            }
        },
    }
    request = urllib.request.Request(
        config.endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise AIError(f"AI enrichment failed: {exc}") from exc
    output_text = result.get("output_text")
    if not output_text:
        output_text = _extract_output_text(result)
    try:
        parsed = json.loads(output_text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise AIError("AI response did not contain valid JSON") from exc
    return validate_ai_enrichment(parsed, valid_evidence_ids)


def safe_enrich_report(report: MergeReadinessReport, config: Config) -> MergeReadinessReport:
    """Apply optional AI text without allowing it to change deterministic decisions."""
    if not config.ai.enabled:
        return report
    valid_ids = {item.id for item in report.evidence}
    try:
        enrichment = enrich_with_openai(report.to_dict(), config.ai, valid_ids)
    except AIError as exc:
        report.limitations.append(f"AI enrichment was unavailable: {exc}")
        return report
    report.ai_summary = enrichment["summary"]
    report.ai_claims = [
        Reason(
            text=item["text"],
            evidence_ids=item["evidence_ids"],
            confidence=item["confidence"],
            severity="Low",
            category="ai_enrichment",
        )
        for item in enrichment["claims"]
    ]
    return report


def _extract_output_text(result: dict[str, Any]) -> str:
    for output in result.get("output", []):
        for content in output.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                return content["text"]
    return ""
