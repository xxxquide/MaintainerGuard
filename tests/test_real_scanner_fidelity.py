"""Fidelity tests against REAL scanner output, not hand-written '-like' fixtures.

Why this file exists
--------------------
Every scanner fixture under examples/sample-data/scanners/ is named "*-like"
and was written by hand. The test suite therefore validates the project's own
assumptions about scanner formats rather than the formats real scanners emit.

Running the real binaries (Trivy 0.73.0, Gitleaks 8.30.1, osv-scanner 2.4.0,
Semgrep OSS) against a deliberately vulnerable fixture project produced these
results on 2026-08-04:

    real output                        findings in file   normalize_scanner_input()
    trivy fs --format json                    65                 61   <- 4 LOST
    trivy fs --format sarif                   65                 65
    gitleaks --report-format json              1              CRASH   <- ValueError
    gitleaks --report-format sarif             1                  1
    osv-scanner --format json                117                117
    osv-scanner --format sarif      117 / 61 uniq            61       (correct grouping)
    semgrep --json                             4                  4   <- MISROUTED
    semgrep --sarif                            4                  4

Specifically lost by the Trivy native-JSON path:

    [Secrets]           src/app.py  CRITICAL  github-pat  GitHub Personal Access Token
    [Misconfigurations] Dockerfile  HIGH      DS-0002     Image user should not be 'root'
    [Misconfigurations] Dockerfile  LOW       DS-0005     ADD instead of COPY
    [Misconfigurations] Dockerfile  LOW       DS-0026     No HEALTHCHECK defined

The Semgrep native JSON path misroutes every finding to the secret scanner
adapter with blocking=True, which makes the end-to-end verdict
"Blocked by scanner finding" for ordinary SAST results.

Each test below is written to FAIL on today's code and pass once the
corresponding defect is fixed. Fixtures live in
tests/fixtures/real-scanners/ and are byte-for-byte scanner output; regenerate
them with tests/fixtures/real-scanners/regenerate.sh.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from veracity.scanners import normalize_scanner_input

FIXTURES = Path(__file__).parent / "fixtures" / "real-scanners"


def load(name: str):
    path = FIXTURES / name
    if not path.exists():  # pragma: no cover - fixtures are optional in CI
        raise unittest.SkipTest(f"missing real-scanner fixture: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def count_trivy_findings(data: dict) -> int:
    total = 0
    for result in data.get("Results", []):
        for key in ("Vulnerabilities", "Misconfigurations", "Secrets", "Licenses"):
            total += len(result.get(key) or [])
    return total


class RealTrivyOutput(unittest.TestCase):
    """Trivy emits four finding classes; only Vulnerabilities is read today."""

    def test_no_finding_class_is_silently_dropped(self):
        data = load("trivy-fs.json")
        expected = count_trivy_findings(data)
        actual = len(normalize_scanner_input(data))
        self.assertEqual(
            actual,
            expected,
            f"Trivy native JSON: {expected} findings present, {actual} normalized. "
            "Secrets/Misconfigurations/Licenses are dropped without a warning.",
        )

    def test_critical_secret_is_not_lost(self):
        data = load("trivy-fs.json")
        findings = normalize_scanner_input(data)
        self.assertTrue(
            any(f.category == "secret" for f in findings),
            "Trivy reported a CRITICAL github-pat under Results[].Secrets; "
            "no secret finding survived normalization.",
        )

    def test_dockerfile_misconfiguration_is_not_lost(self):
        data = load("trivy-fs.json")
        findings = normalize_scanner_input(data)
        self.assertTrue(
            any("Dockerfile" in " ".join(f.affected) for f in findings),
            "Trivy reported HIGH DS-0002 on Dockerfile; it is absent after normalization.",
        )


class RealGitleaksOutput(unittest.TestCase):
    """gitleaks --report-format json emits a top-level JSON array."""

    def test_top_level_array_is_accepted(self):
        data = load("gitleaks.json")
        self.assertIsInstance(data, list, "fixture is not the real gitleaks shape")
        try:
            findings = normalize_scanner_input(data)
        except ValueError as exc:
            self.fail(
                "gitleaks native JSON raises instead of parsing: "
                f"{exc}. Real gitleaks 8.x writes a JSON array, not an object."
            )
        self.assertEqual(len(findings), len(data))
        self.assertTrue(all(f.category == "secret" for f in findings))


class RealSemgrepOutput(unittest.TestCase):
    """Semgrep native JSON uses {"results": [...]} and must not hit the secret adapter."""

    def test_not_misrouted_to_secret_scanner(self):
        data = load("semgrep.json")
        findings = normalize_scanner_input(data)
        self.assertTrue(findings, "no findings parsed from real semgrep output")
        misrouted = [f for f in findings if f.scanner == "secret-scanner"]
        self.assertEqual(
            misrouted,
            [],
            "Real semgrep --json is routed to _from_secret_results because that "
            "branch matches any {'results': [...]} payload. Every SAST finding "
            "becomes a 'Possible secret reported by scanner'.",
        )

    def test_does_not_fabricate_blocking_findings(self):
        data = load("semgrep.json")
        findings = normalize_scanner_input(data)
        self.assertEqual(
            [f.id for f in findings if f.blocking],
            [],
            "Semgrep findings are marked blocking=True, which makes the end-to-end "
            "verdict 'Blocked by scanner finding' for ordinary SAST results.",
        )

    def test_rule_id_is_preserved(self):
        data = load("semgrep.json")
        findings = normalize_scanner_input(data)
        expected = {r["check_id"] for r in data["results"]}
        self.assertTrue(
            expected & {f.id for f in findings},
            "semgrep check_id is discarded; findings are labelled secret-1..secret-N.",
        )


class UnknownFormatsMustNotBeSilent(unittest.TestCase):
    """An unclassifiable payload must not be indistinguishable from a clean scan."""

    def test_unrecognised_payload_raises(self):
        # Grype's native shape: recognised by no adapter here.
        payload = {"matches": [{"vulnerability": {"id": "CVE-2026-1", "severity": "Critical"}}]}
        with self.assertRaises(ValueError) as caught:
            normalize_scanner_input(payload)
        self.assertIn("recognise", str(caught.exception).lower())

    def test_unrecognised_array_raises(self):
        with self.assertRaises(ValueError):
            normalize_scanner_input([{"totally": "unknown"}])

    def test_recognised_but_empty_payload_returns_empty(self):
        # A clean scan legitimately has no findings and must not raise.
        self.assertEqual(normalize_scanner_input({"scanner": "x", "findings": []}), [])
        self.assertEqual(normalize_scanner_input([]), [])
        self.assertEqual(
            normalize_scanner_input({"version": "2.1.0", "runs": []}),
            [],
        )


class SarifSuppressionsAndBaseline(unittest.TestCase):
    """SARIF suppressions/baselineState carry maintainer decisions and must be honoured."""

    SARIF = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "CodeQL",
                        "rules": [
                            {
                                "id": "py/sql-injection",
                                "defaultConfiguration": {"level": "error"},
                                "properties": {
                                    "tags": ["security", "external/cwe/cwe-089"],
                                    "problem.severity": "error",
                                    "security-severity": "9.8",
                                },
                            }
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": "py/sql-injection",
                        "message": {"text": "Suppressed as a false positive."},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "app/a.py"},
                                    "region": {"startLine": 1},
                                }
                            }
                        ],
                        "suppressions": [
                            {"kind": "external", "status": "accepted",
                             "justification": "reviewed, not exploitable"}
                        ],
                    },
                    {
                        "ruleId": "py/sql-injection",
                        "message": {"text": "Pre-existing finding."},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "app/b.py"},
                                    "region": {"startLine": 2},
                                }
                            }
                        ],
                        "baselineState": "unchanged",
                    },
                    {
                        "ruleId": "py/sql-injection",
                        "message": {"text": "Newly introduced finding."},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "app/c.py"},
                                    "region": {"startLine": 3},
                                }
                            }
                        ],
                        "baselineState": "new",
                    },
                ],
            }
        ],
    }

    def test_accepted_suppression_is_excluded(self):
        findings = normalize_scanner_input(self.SARIF)
        self.assertEqual(
            [f for f in findings if "Suppressed" in f.title],
            [],
            "A finding with suppressions[].status == 'accepted' is reported as active. "
            "Maintainer-dismissed findings return on every run.",
        )

    def test_unchanged_baseline_state_is_distinguishable(self):
        findings = normalize_scanner_input(self.SARIF)
        self.assertEqual(
            [f for f in findings if "Pre-existing" in f.title],
            [],
            "baselineState == 'unchanged' means the finding predates this change; "
            "it is presented as evidence for the current pull request.",
        )

    def test_security_severity_maps_critical(self):
        findings = normalize_scanner_input(self.SARIF)
        severities = {f.severity for f in findings}
        self.assertIn(
            "Critical",
            severities,
            "CodeQL security-severity 9.8 must map to Critical per GitHub's documented "
            f"scale (>=9.0 critical). Got {severities or 'no findings'}.",
        )


class DiffScoping(unittest.TestCase):
    """Findings must be attributable to the files a change actually touches."""

    @staticmethod
    def analyze(changed_path: str):
        from veracity.analysis import analyze_pull_request
        from veracity.config import load_config

        return analyze_pull_request(
            {
                "title": "Unrelated one-file change",
                "files": [{"path": changed_path, "status": "modified"}],
            },
            scanner_inputs=[load("trivy-fs.json")],
            config=load_config(),
        )

    def test_repo_wide_findings_do_not_inflate_an_unrelated_change(self):
        # docs/guide.md carries no scanner finding of its own. Every finding in
        # the fixture belongs to requirements.txt, Dockerfile, or src/app.py.
        report = self.analyze("docs/guide.md")
        pre_existing = [f for f in report.scanner_findings if not f.in_changed_scope]
        self.assertTrue(
            pre_existing,
            "The fixture reports findings in files this change does not touch; "
            "none were separated out.",
        )
        self.assertEqual(
            report.risk_level,
            "Low",
            "A documentation-only change is rated "
            f"{report.risk_level} because of pre-existing findings in files it never "
            f"modified. Verdict was {report.verdict!r}.",
        )
        self.assertLess(
            len(report.checklist),
            5,
            f"The maintainer checklist has {len(report.checklist)} items for a "
            "documentation-only change; pre-existing repository findings are being "
            "turned into review tasks.",
        )

    def test_findings_inside_the_change_still_count(self):
        # The fixture's CRITICAL Trivy secret finding is located in src/app.py,
        # so changing that file must still produce an elevated verdict.
        report = self.analyze("src/app.py")
        in_scope = [f for f in report.scanner_findings if f.in_changed_scope]
        self.assertTrue(
            any(f.category == "secret" for f in in_scope),
            "The secret Trivy reported in src/app.py must stay in scope when that file changes.",
        )
        self.assertEqual(
            "High",
            report.risk_level,
            "A CRITICAL leaked credential inside the changed file must not be demoted.",
        )

    def test_dependency_findings_count_when_the_manifest_changes(self):
        report = self.analyze("requirements.txt")
        in_scope = [f for f in report.scanner_findings if f.in_changed_scope]
        self.assertTrue(
            any(f.category == "dependency" for f in in_scope),
            "Dependency advisories must be in scope when the manifest they describe changes.",
        )

    def test_scope_decision_is_explained(self):
        report = self.analyze("src/app.py")
        for finding in report.scanner_findings:
            self.assertTrue(
                finding.scope_reason,
                f"{finding.id} carries no explanation for its scope decision.",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
