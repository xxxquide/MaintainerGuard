import unittest

from maintainerguard.issue import triage_issue
from maintainerguard.release import analyze_release


class IssueAndReleaseTests(unittest.TestCase):
    def test_issue_triage_detects_missing_bug_details(self):
        report = triage_issue(
            {
                "schema_version": "1.0",
                "title": "It crashes",
                "body": "The command throws an error.",
                "labels": [],
            }
        )
        self.assertEqual("Bug report", report.issue_type)
        self.assertIn("reproduction steps", report.missing_information)
        self.assertTrue(report.evidence)

    def test_issue_triage_distinguishes_support_requests(self):
        report = triage_issue(
            {
                "schema_version": "1.0",
                "title": "Support needed for private configuration",
                "body": "Please help with setup.",
                "labels": [],
            }
        )
        self.assertEqual("Support request", report.issue_type)

    def test_issue_triage_handles_security_reports_safely(self):
        report = triage_issue(
            {
                "schema_version": "1.0",
                "title": "Possible security issue in webhook handling",
                "body": "I found a possible token exposure and can share details privately.",
                "labels": [],
            }
        )
        self.assertEqual("Security report", report.issue_type)
        self.assertIn("security", report.suggested_labels)
        self.assertIn("responsible disclosure", report.next_action.lower())
        self.assertNotIn("exploit", report.suggested_response.lower())

    def test_issue_triage_detects_regression_and_dependency_issues(self):
        regression = triage_issue(
            {
                "title": "Regression: analyze-pr fails after 0.2.0",
                "body": "This worked in 0.1.0 and now fails on Linux.",
            }
        )
        self.assertEqual("Regression report", regression.issue_type)
        self.assertEqual("High", regression.priority)

        dependency = triage_issue(
            {
                "title": "Dependency advisory for example-http",
                "body": "OSV reports an advisory for example-http.",
            }
        )
        self.assertEqual("Dependency issue", dependency.issue_type)
        self.assertIn("dependencies", dependency.suggested_labels)

    def test_release_report_aggregates_risk(self):
        report = analyze_release(
            {
                "schema_version": "1.0",
                "version": "0.2.0",
                "pull_requests": [
                    {
                        "title": "Change auth",
                        "files": [{"path": "src/auth/session.py", "status": "modified"}],
                    },
                    {
                        "title": "Update docs",
                        "files": [{"path": "docs/auth.md", "status": "modified"}],
                    },
                ],
            }
        )
        self.assertIn("Change auth", report.notable_changes)
        self.assertEqual("Review before release", report.verdict)
        self.assertTrue(report.security_sensitive_changes)
        self.assertTrue(report.release_checklist)

    def test_release_report_keeps_all_supplied_scanner_summaries(self):
        report = analyze_release(
            {
                "schema_version": "1.0",
                "version": "1.0.0",
                "pull_requests": [],
                "scanner_inputs": [
                    {
                        "scanner": "tool",
                        "findings": [
                            {"id": "LOW-1", "severity": "low", "title": "Informational signal"}
                        ],
                    }
                ],
            }
        )
        self.assertEqual(["Low - tool: Informational signal"], report.scanner_findings)

    def test_release_changelog_counts_as_documentation(self):
        report = analyze_release(
            {
                "schema_version": "1.0",
                "version": "1.0.0",
                "pull_requests": [
                    {"title": "Release notes", "files": [{"path": "CHANGELOG.md"}]}
                ],
            }
        )
        self.assertEqual("Documentation changes detected.", report.docs_status)

    def test_release_uses_changelog_and_open_high_priority_issues(self):
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
                        "labels": ["security", "blocker"],
                    }
                ],
                "changelog": ["Added evidence export.", "Fixed report rendering."],
            }
        )
        self.assertIn("Issue #9: Security regression", report.unresolved_high_risk_items)
        self.assertEqual("Do not ship until high-risk items are resolved", report.verdict)
        self.assertIn("Added evidence export.", report.release_notes)
        self.assertTrue(any(item.source_type == "release_issue" for item in report.evidence))


if __name__ == "__main__":
    unittest.main()
