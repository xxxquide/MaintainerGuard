"""Optional, bounded AI enrichment with deterministic validation."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from .config import AIConfig, Config
from .models import MergeReadinessReport, Reason
from .privacy import redact_value
from .prompts import AI_OUTPUT_SCHEMA, SYSTEM_INSTRUCTION


class AIError(RuntimeError):
    pass


# The AI summary is free text. Everything else in the report is bounded by the
# evidence model, so this is the only field an adversary can steer, and the
# pull-request title, body, and patch all reach the prompt.
AI_SUMMARY_LIMIT = 1500
AI_CLAIM_LIMIT = 300

_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_COMMENT_FRAGMENT = re.compile(r"<!--|-->")
_ATX_HEADING = re.compile(r"(?m)^[ \t]*#{1,6}[ \t]*")
_SETEXT_UNDERLINE = re.compile(r"(?m)^[ \t]*(?:=|-){3,}[ \t]*$")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_BLANK_RUN = re.compile(r"\n{3,}")


def sanitize_ai_text(value: Any, limit: int) -> str:
    """Strip anything that lets model output impersonate the report itself.

    HTML comments are removed because the published-comment marker is an HTML
    comment: injecting it can orphan or hijack the maintainer's existing comment.
    Markdown headings are flattened so AI text cannot fabricate a section such as
    `## Evidence` next to the deterministic one.
    """
    if not isinstance(value, str):
        return ""
    cleaned = _HTML_COMMENT.sub(" ", value)
    cleaned = _COMMENT_FRAGMENT.sub(" ", cleaned)
    cleaned = _ATX_HEADING.sub("", cleaned)
    cleaned = _SETEXT_UNDERLINE.sub("", cleaned)
    cleaned = _CONTROL.sub("", cleaned)
    cleaned = _BLANK_RUN.sub("\n\n", cleaned).strip()
    if len(cleaned) > limit:
        cleaned = cleaned[:limit].rstrip() + " [truncated by MaintainerGuard]"
    return cleaned


def validate_ai_enrichment(payload: Any, valid_evidence_ids: set[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"summary": "", "claims": []}
    summary = sanitize_ai_text(payload.get("summary", ""), AI_SUMMARY_LIMIT)
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
            claims.append(
                {
                    "text": sanitize_ai_text(text, AI_CLAIM_LIMIT),
                    "evidence_ids": refs,
                    "confidence": confidence,
                }
            )
    return {"summary": summary, "claims": [item for item in claims if item["text"]]}


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
    # Sanitized again here on purpose: safe_enrich_report is the boundary that
    # writes into the report, and it must not depend on its caller having done it.
    report.ai_summary = sanitize_ai_text(enrichment.get("summary", ""), AI_SUMMARY_LIMIT)
    report.ai_claims = [
        Reason(
            text=sanitize_ai_text(item["text"], AI_CLAIM_LIMIT),
            evidence_ids=item["evidence_ids"],
            confidence=item["confidence"],
            severity="Low",
            category="ai_enrichment",
        )
        for item in enrichment.get("claims", [])
        if sanitize_ai_text(item.get("text", ""), AI_CLAIM_LIMIT)
    ]
    return report


def _extract_output_text(result: dict[str, Any]) -> str:
    for output in result.get("output", []):
        for content in output.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                return content["text"]
    return ""
