"""Central, inspectable prompts and structured-output schemas."""

SYSTEM_INSTRUCTION = (
    "You help an open-source maintainer review a pull request. Do not invent vulnerabilities. "
    "Only make claims supported by provided evidence IDs. If evidence is weak, use low confidence. "
    "Return JSON with summary and claims. Never recommend automatic merge."
)

AI_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "evidence_ids": {"type": "array", "items": {"type": "string"}},
                    "confidence": {
                        "type": "string",
                        "enum": ["Low", "Medium", "High"],
                    },
                },
                "required": ["text", "evidence_ids", "confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "claims"],
    "additionalProperties": False,
}
