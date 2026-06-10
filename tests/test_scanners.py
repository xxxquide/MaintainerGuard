import unittest

from maintainerguard.scanners import normalize_scanner_input


class ScannerTests(unittest.TestCase):
    def test_normalizes_sarif(self):
        findings = normalize_scanner_input(
            {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {"driver": {"name": "CodeQL"}},
                        "results": [
                            {
                                "ruleId": "js/xss",
                                "level": "warning",
                                "message": {"text": "Potential unsafe rendering"},
                                "locations": [
                                    {
                                        "physicalLocation": {
                                            "artifactLocation": {"uri": "src/view.js"}
                                        }
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )
        self.assertEqual("CodeQL", findings[0].scanner)
        self.assertEqual("Medium", findings[0].severity)
        self.assertEqual("src/view.js", findings[0].affected[0])

    def test_normalizes_osv_and_generic(self):
        osv = normalize_scanner_input(
            {
                "results": [
                    {
                        "packages": [
                            {
                                "package": {"name": "lib", "version": "1.0"},
                                "vulnerabilities": [{"id": "OSV-1", "summary": "Advisory"}],
                            }
                        ]
                    }
                ]
            }
        )
        generic = normalize_scanner_input(
            {
                "scanner": "secret-scan",
                "findings": [{"id": "S1", "severity": "high", "title": "Possible secret"}],
            }
        )
        self.assertEqual("OSV", osv[0].scanner)
        self.assertEqual("dependency", osv[0].category)
        self.assertEqual("OSV-1", osv[0].advisory_id)
        self.assertEqual("lib@1.0", osv[0].affected_dependency)
        self.assertIn("patched", osv[0].recommendation)
        self.assertEqual("secret-scan", generic[0].scanner)
        self.assertEqual("secret", generic[0].category)

    def test_normalizes_semgrep_like_and_supply_chain_findings(self):
        semgrep = normalize_scanner_input(
            {
                "scanner": "Semgrep",
                "findings": [
                    {
                        "id": "python.lang.security.audit.subprocess-shell-true",
                        "category": "static-analysis",
                        "severity": "medium",
                        "title": "subprocess shell=True",
                        "description": "subprocess uses shell=True",
                        "affected_files": ["src/runner.py"],
                        "recommendation": "Confirm command arguments are trusted and sanitized.",
                    }
                ],
            }
        )
        self.assertEqual("static-analysis", semgrep[0].category)
        self.assertEqual("Confirm command arguments are trusted and sanitized.", semgrep[0].recommendation)

        supply_chain = normalize_scanner_input(
            {
                "scanner": "workflow-policy",
                "findings": [
                    {
                        "id": "WF-1",
                        "category": "supply-chain",
                        "severity": "high",
                        "title": "Workflow gained write permissions",
                        "affected_files": [".github/workflows/release.yml"],
                    }
                ],
            }
        )
        self.assertEqual("supply-chain", supply_chain[0].category)
        self.assertIn("workflow", supply_chain[0].recommendation.lower())

    def test_osv_severity_arrays_do_not_break_normalization(self):
        findings = normalize_scanner_input(
            {
                "results": [
                    {
                        "packages": [
                            {
                                "package": {"name": "lib", "version": "1.0"},
                                "vulnerabilities": [
                                    {
                                        "id": "OSV-2",
                                        "summary": "Advisory",
                                        "database_specific": {"severity": "HIGH"},
                                        "severity": [{"type": "CVSS_V3", "score": "9.8"}],
                                    }
                                ],
                            }
                        ]
                    }
                ]
            }
        )
        self.assertEqual("High", findings[0].severity)

    def test_normalizes_trivy_vulnerability_results(self):
        findings = normalize_scanner_input(
            {
                "SchemaVersion": 2,
                "ArtifactName": "example-app:ci",
                "Results": [
                    {
                        "Target": "example-app:ci (debian 12.5)",
                        "Type": "debian",
                        "Vulnerabilities": [
                            {
                                "VulnerabilityID": "CVE-2026-0001",
                                "PkgName": "openssl",
                                "InstalledVersion": "3.0.0",
                                "FixedVersion": "3.0.8",
                                "Severity": "HIGH",
                                "Title": "openssl contains a sanitized advisory",
                                "Description": "Example Trivy output only.",
                            }
                        ],
                    }
                ],
            }
        )
        self.assertEqual(1, len(findings))
        self.assertEqual("Trivy", findings[0].scanner)
        self.assertEqual("High", findings[0].severity)
        self.assertEqual("dependency", findings[0].category)
        self.assertEqual("CVE-2026-0001", findings[0].advisory_id)
        self.assertEqual("openssl@3.0.0", findings[0].affected_dependency)
        self.assertIn("example-app:ci", findings[0].affected[0])
        self.assertIn("3.0.8", findings[0].recommendation)

    def test_duplicate_generic_findings_are_removed_by_analysis(self):
        from maintainerguard.analysis import analyze_pull_request
        from maintainerguard.config import load_config

        scanner = {
            "scanner": "tool",
            "findings": [
                {"id": "same", "title": "One", "severity": "medium"},
                {"id": "same", "title": "Duplicate", "severity": "medium"},
            ],
        }
        report = analyze_pull_request(
            {"title": "Change", "files": [{"path": "src/main.py"}]},
            scanner_inputs=[scanner],
            config=load_config(),
        )
        self.assertEqual(1, len(report.scanner_findings))


if __name__ == "__main__":
    unittest.main()
