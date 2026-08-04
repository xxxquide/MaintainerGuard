"""Input minimization and secret redaction."""

from __future__ import annotations

import re
from typing import Any


_PATTERNS = [
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
]


def redact_text(text: str) -> str:
    output = text
    for pattern in _PATTERNS:
        output = pattern.sub("[REDACTED]", output)
    return output


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if _sensitive_key(str(key)) else redact_value(item)
            for key, item in value.items()
        }
    return value


def _sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(term in lowered for term in ("password", "secret", "token", "api_key", "private_key"))
