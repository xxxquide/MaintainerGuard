import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SampleTests(unittest.TestCase):
    def test_required_repository_and_documentation_files_exist(self):
        required = [
            "README.md",
            "LICENSE",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CHANGELOG.md",
            "CODE_OF_CONDUCT.md",
            ".maintainerguard.toml",
            ".github/workflows/ci.yml",
            ".github/workflows/maintainerguard-pr.yml",
            ".github/workflows/maintainerguard-issue.yml",
            ".github/workflows/maintainerguard-release.yml",
            ".github/ISSUE_TEMPLATE/bug_report.md",
            ".github/ISSUE_TEMPLATE/feature_request.md",
            ".github/ISSUE_TEMPLATE/scanner_adapter_request.md",
            ".github/ISSUE_TEMPLATE/policy_rule_request.md",
            ".github/pull_request_template.md",
            "action.yml",
            "docs/README.md",
            "docs/getting-started.md",
            "docs/configuration.md",
            "docs/report-format.md",
            "docs/github-automation.md",
            "docs/scanner-inputs.md",
            "docs/privacy-and-security.md",
            "docs/maintainer-policies.md",
            "docs/development.md",
            "docs/architecture.md",
            "docs/public-release-checklist.md",
            "docs/roadmap.md",
            "examples/README.md",
            "examples/reports/docs-only.md",
            "examples/reports/docs-only-low-risk.md",
            "examples/reports/high-risk-auth.md",
            "examples/reports/dependency-advisory.md",
            "examples/reports/ci-workflow-risk.md",
            "examples/reports/secret-finding.md",
            "examples/reports/issue-triage.md",
            "examples/reports/release-readiness.md",
            "examples/reports/release-v0.2.0.md",
        ]
        for relative in required:
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertGreater(path.stat().st_size, 0, relative)

    def test_required_sample_sets_exist_and_parse(self):
        expected_counts = {
            "examples/sample-data/prs": 7,
            "examples/sample-data/issues": 6,
            "examples/sample-data/scanners": 7,
            "examples/sample-data/releases": 1,
            "schemas": 5,
        }
        for relative, minimum in expected_counts.items():
            files = sorted((ROOT / relative).glob("*.json"))
            self.assertGreaterEqual(len(files), minimum, relative)
            for path in files:
                self.assertIsInstance(json.loads(path.read_text()), dict, path)

    def test_advertised_cli_sample_commands_run(self):
        commands = [
            ["analyze-pr", "examples/sample-data/prs/high-risk-auth.json"],
            ["demo", "--scenario", "dependency-advisory"],
            ["demo", "--scenario", "ci-workflow-risk"],
            ["demo", "--scenario", "secret-finding"],
            ["analyze-issue", "examples/sample-data/issues/bug-missing-reproduction.json"],
            ["analyze-release", "examples/sample-data/releases/v0.2.0.json"],
            ["parse-scanner", "examples/sample-data/scanners/mixed-severity.json"],
            ["parse-scanner", "examples/sample-data/scanners/container-trivy-warning.json"],
            ["validate-config"],
            ["github-run", "examples/sample-data/github/pull-request-event.json"],
        ]
        for command in commands:
            result = subprocess.run(
                [sys.executable, "-m", "maintainerguard", *command],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, f"{command}: {result.stderr}")

    def test_checked_in_report_snapshots_match_current_renderer(self):
        snapshots = [
            (
                ["analyze-pr", "examples/sample-data/prs/docs-only.json"],
                "examples/reports/docs-only.md",
            ),
            (
                ["analyze-pr", "examples/sample-data/prs/high-risk-auth.json"],
                "examples/reports/high-risk-auth.md",
            ),
            (
                ["analyze-release", "examples/sample-data/releases/v0.2.0.json"],
                "examples/reports/release-v0.2.0.md",
            ),
            (
                ["analyze-pr", "examples/sample-data/prs/dependency-update.json", "--scanner", "examples/sample-data/scanners/dependency-advisory.json"],
                "examples/reports/dependency-advisory.md",
            ),
            (
                ["analyze-issue", "examples/sample-data/issues/bug-missing-reproduction.json"],
                "examples/reports/issue-triage.md",
            ),
        ]
        for command, snapshot in snapshots:
            result = subprocess.run(
                [sys.executable, "-m", "maintainerguard", *command],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual((ROOT / snapshot).read_text(), result.stdout, snapshot)


if __name__ == "__main__":
    unittest.main()
