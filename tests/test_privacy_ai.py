import unittest
import json
from unittest.mock import patch

from maintainerguard.ai import enrich_with_openai, safe_enrich_report, validate_ai_enrichment
from maintainerguard.analysis import analyze_pull_request
from maintainerguard.config import AIConfig, load_config
from maintainerguard.privacy import redact_text


class PrivacyAndAITests(unittest.TestCase):
    def test_redacts_common_secret_patterns(self):
        text = "token=example-token-value and password=hunter2"
        redacted = redact_text(text)
        self.assertNotIn("hunter2", redacted)
        self.assertNotIn("example-token-value", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_ai_claims_without_valid_evidence_are_discarded(self):
        payload = {
            "summary": "Review auth changes.",
            "claims": [
                {"text": "Auth changed", "evidence_ids": ["ev-auth"], "confidence": "High"},
                {"text": "Invented issue", "evidence_ids": ["missing"], "confidence": "High"},
            ],
        }
        validated = validate_ai_enrichment(payload, {"ev-auth"})
        self.assertEqual(1, len(validated["claims"]))
        self.assertEqual("Auth changed", validated["claims"][0]["text"])

    def test_ai_failure_keeps_deterministic_report_and_adds_limitation(self):
        config = load_config()
        config.ai.enabled = True
        config.ai.model = "example-model"
        report = analyze_pull_request(
            {"title": "Docs", "files": [{"path": "README.md", "status": "modified"}]},
            config=config,
        )
        original_verdict = report.verdict
        with patch.dict("os.environ", {}, clear=True):
            enriched = safe_enrich_report(report, config)
        self.assertEqual(original_verdict, enriched.verdict)
        self.assertEqual("", enriched.ai_summary)
        self.assertTrue(any("AI enrichment was unavailable" in item for item in enriched.limitations))

    def test_valid_ai_enrichment_cannot_change_verdict(self):
        config = load_config()
        config.ai.enabled = True
        config.ai.model = "example-model"
        report = analyze_pull_request(
            {"title": "Docs", "files": [{"path": "README.md", "status": "modified"}]},
            config=config,
        )
        evidence_id = report.evidence[0].id
        with patch(
            "maintainerguard.ai.enrich_with_openai",
            return_value={
                "summary": "The documentation change is low risk.",
                "claims": [{"text": "README changed.", "evidence_ids": [evidence_id], "confidence": "High"}],
            },
        ):
            enriched = safe_enrich_report(report, config)
        self.assertEqual("Ready for maintainer review", enriched.verdict)
        self.assertEqual("The documentation change is low risk.", enriched.ai_summary)
        self.assertEqual(1, len(enriched.ai_claims))

    def test_openai_request_is_non_storing_and_redacted(self):
        captured = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"output_text":"{\\"summary\\":\\"ok\\",\\"claims\\":[]}"}'

        def fake_urlopen(request, timeout):
            captured["payload"] = json.loads(request.data)
            return Response()

        config = AIConfig(enabled=True, model="example-model")
        with patch.dict("os.environ", {"OPENAI_API_KEY": "not-sent-to-model"}, clear=True):
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                enrich_with_openai(
                    {"summary": "token=secret-value", "api_key": "private-value"},
                    config,
                    set(),
                )
        serialized = json.dumps(captured["payload"])
        self.assertFalse(captured["payload"]["store"])
        self.assertNotIn("secret-value", serialized)
        self.assertNotIn("private-value", serialized)
        self.assertNotIn("not-sent-to-model", serialized)


if __name__ == "__main__":
    unittest.main()
