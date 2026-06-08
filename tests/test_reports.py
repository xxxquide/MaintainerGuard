import json
import unittest

from maintainerguard.analysis import analyze_pull_request
from maintainerguard.config import load_config
from maintainerguard.reports import render_report
from maintainerguard.release import analyze_release


class ReportTests(unittest.TestCase):
    def test_markdown_contains_required_sections_and_evidence(self):
        report = analyze_pull_request(
            {
                "schema_version": "1.0",
                "title": "Auth update",
                "files": [{"path": "src/auth/session.py", "status": "modified"}],
            },
            config=load_config(),
        )
        output = render_report(report, output_format="markdown", mode="detailed")
        self.assertIn("# MaintainerGuard Merge Readiness Report", output)
        self.assertIn("## Evidence", output)
        self.assertIn("## Limitations", output)
        self.assertIn("## Decision guidance", output)
        self.assertIn("Recommended maintainer action:", output)
        self.assertNotIn("vulnerability found", output.lower())

    def test_json_is_structured(self):
        report = analyze_pull_request(
            {"schema_version": "1.0", "title": "Docs", "files": [{"path": "README.md"}]},
            config=load_config(),
        )
        output = json.loads(render_report(report, output_format="json"))
        self.assertEqual("merge_readiness_report", output["report_type"])
        self.assertTrue(output["evidence"])
        self.assertIn("decision_guidance", output)
        self.assertIn("decision_reason", output)

    def test_merge_markdown_renders_breaking_changes_and_policy_checks(self):
        report = analyze_pull_request(
            {
                "title": "Breaking auth change",
                "files": [
                    {
                        "path": "src/auth/session.py",
                        "patch": "+BREAKING: remove old session behavior",
                    }
                ],
            },
            config=load_config(),
        )
        output = render_report(report, output_format="markdown")
        self.assertIn("## Possible breaking changes", output)
        self.assertIn("## Policy checks", output)

    def test_release_markdown_renders_status_and_unresolved_items(self):
        report = analyze_release(
            {
                "schema_version": "1.0",
                "version": "1.0.0",
                "pull_requests": [],
                "issues": [
                    {
                        "number": 9,
                        "title": "Security regression",
                        "state": "open",
                        "labels": ["blocker"],
                    }
                ],
            }
        )
        output = render_report(report, output_format="markdown")
        self.assertIn("## Documentation status", output)
        self.assertIn("## Test status", output)
        self.assertIn("## Scanner findings", output)
        self.assertIn("## Unresolved high-risk items", output)
        self.assertIn("**Release verdict:**", output)


if __name__ == "__main__":
    unittest.main()
