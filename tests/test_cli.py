import subprocess
import sys
import tempfile
import unittest
import json
import os
from pathlib import Path

from maintainerguard.cli import _split_paths


ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def run_cli(self, args, cwd=None):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "maintainerguard", *args],
            cwd=cwd or ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_print_config_and_demo_work_without_installation(self):
        config = subprocess.run(
            [sys.executable, "-m", "maintainerguard", "print-config"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("dry_run = true", config.stdout)

        demo = subprocess.run(
            [sys.executable, "-m", "maintainerguard", "demo", "--scenario", "docs-only"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("MaintainerGuard Merge Readiness Report", demo.stdout)

    def test_analyze_pr_loads_configured_scanner_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pr = root / "pr.json"
            scanner = root / "scanner.json"
            config = root / "config.toml"
            pr.write_text('{"title":"Deps","files":[{"path":"requirements.txt"}]}')
            scanner.write_text(
                '{"scanner":"tool","findings":[{"id":"X","severity":"critical","title":"Critical","blocking":true}]}'
            )
            config.write_text(
                '[paths]\nscanner_inputs = ["' + str(scanner).replace("\\", "\\\\") + '"]\n'
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "maintainerguard",
                    "--config",
                    str(config),
                    "analyze-pr",
                    str(pr),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("Blocked by scanner finding", result.stdout)

    def test_split_paths_accepts_commas_and_newlines_without_duplicates_from_parser(self):
        self.assertEqual(
            [Path("a.json"), Path("b.json"), Path("c.json")],
            _split_paths("a.json,b.json\nc.json"),
        )

    def test_action_run_scanner_env_does_not_duplicate_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pr = root / "pr.json"
            scanner = root / "scanner.json"
            pr.write_text('{"title":"Deps","files":[{"path":"requirements.txt"}]}')
            scanner.write_text(
                '{"scanner":"tool","findings":[{"id":"SCAN-1","severity":"high","title":"Scanner signal"}]}'
            )
            result = subprocess.run(
                [sys.executable, "-m", "maintainerguard", "action-run"],
                env={
                    "MG_MODE": "analyze-pr",
                    "MG_INPUT_PATH": str(pr),
                    "MG_SCANNER_RESULT_PATHS": str(scanner),
                    "MG_DRY_RUN": "true",
                    "MG_OUTPUT_FORMAT": "json",
                },
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(["SCAN-1"], [item["id"] for item in report["scanner_findings"]])

    def test_friendly_aliases_match_existing_analysis_commands(self):
        pr = self.run_cli(
            [
                "pr",
                str(ROOT / "examples/sample-data/prs/dependency-update.json"),
                "--scanner",
                str(ROOT / "examples/sample-data/scanners/dependency-advisory.json"),
            ]
        )
        self.assertEqual(0, pr.returncode, pr.stderr)
        self.assertIn("Blocked by scanner finding", pr.stdout)

        issue = self.run_cli(["issue", str(ROOT / "examples/sample-data/issues/bug-missing-reproduction.json")])
        self.assertEqual(0, issue.returncode, issue.stderr)
        self.assertIn("MaintainerGuard Issue Triage Report", issue.stdout)

        release = self.run_cli(["release", str(ROOT / "examples/sample-data/releases/v0.3.0.json")])
        self.assertEqual(0, release.returncode, release.stderr)
        self.assertIn("MaintainerGuard Release Readiness Report", release.stdout)

    def test_existing_long_commands_still_work(self):
        result = self.run_cli(
            [
                "analyze-pr",
                str(ROOT / "examples/sample-data/prs/dependency-update.json"),
                "--scanner",
                str(ROOT / "examples/sample-data/scanners/dependency-advisory.json"),
            ]
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Blocked by scanner finding", result.stdout)

    def test_init_creates_config_safely_and_requires_force_to_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self.run_cli(["init"], cwd=root)
            self.assertEqual(0, first.returncode, first.stderr)
            config = root / ".maintainerguard.toml"
            self.assertTrue(config.exists())
            self.assertIn("dry_run = true", config.read_text(encoding="utf-8"))
            self.assertIn('policy_preset = "security"', config.read_text(encoding="utf-8"))
            self.assertIn("MaintainerGuard initialized.", first.stdout)

            config.write_text("custom = true\n", encoding="utf-8")
            second = self.run_cli(["init"], cwd=root)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual("custom = true\n", config.read_text(encoding="utf-8"))
            self.assertIn("already exists", second.stdout)

            forced = self.run_cli(["init", "--force"], cwd=root)
            self.assertEqual(0, forced.returncode, forced.stderr)
            forced_text = config.read_text(encoding="utf-8")
            self.assertIn("dry_run = true", forced_text)
            self.assertIn('policy_preset = "security"', forced_text)

    def test_init_accepts_each_policy_preset(self):
        for preset in ("minimal", "security", "strict", "docs"):
            with self.subTest(preset=preset):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    result = self.run_cli(["init", "--preset", preset], cwd=root)
                    self.assertEqual(0, result.returncode, result.stderr)
                    config = root / ".maintainerguard.toml"
                    self.assertIn(
                        f'policy_preset = "{preset}"',
                        config.read_text(encoding="utf-8"),
                    )

    def test_presets_lists_builtin_policy_presets(self):
        result = self.run_cli(["presets"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("minimal", result.stdout)
        self.assertIn("security", result.stdout)
        self.assertIn("strict", result.stdout)
        self.assertIn("docs", result.stdout)

    def test_scanners_lists_fixture_backed_support(self):
        result = self.run_cli(["scanners"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Scanner input families covered by bundled fixtures", result.stdout)
        self.assertIn("codeql-like.sarif.json", result.stdout)
        self.assertIn("trivy-vulnerability.json", result.stdout)
        self.assertIn("does not replace scanners", result.stdout)

    def test_init_can_create_safe_github_action_workflow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.run_cli(["init", "--github-action"], cwd=root)
            self.assertEqual(0, result.returncode, result.stderr)
            workflow = root / ".github/workflows/maintainerguard.yml"
            self.assertTrue(workflow.exists())
            text = workflow.read_text(encoding="utf-8")
            self.assertIn("permissions:", text)
            self.assertIn("contents: read", text)
            self.assertIn("pull-requests: read", text)
            self.assertIn("uses: xxxquide/MaintainerGuard@v0.3.1", text)
            self.assertIn("mode: analyze-pr", text)
            self.assertIn('dry-run: "true"', text)
            self.assertIn('post-comment: "false"', text)
            self.assertNotIn("ai-enabled", text)
            self.assertNotIn('dry-run: "false"', text)
            self.assertNotIn('post-comment: "true"', text)
            self.assertNotIn("issues: write", text)

    def test_doctor_passes_with_valid_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.run_cli(["init"], cwd=root)
            result = self.run_cli(["doctor"], cwd=root)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("MaintainerGuard Doctor", result.stdout)
            self.assertRegex(result.stdout, r"OK\s+Config found: \.maintainerguard\.toml")
            self.assertIn("MaintainerGuard is ready.", result.stdout)

    def test_doctor_suggests_init_when_config_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli(["doctor"], cwd=Path(directory))
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("Config not found", result.stdout)
            self.assertIn("Run: mg init", result.stdout)

    def test_verify_runs_smoke_checks(self):
        result = self.run_cli(["verify"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("MaintainerGuard Verify", result.stdout)
        self.assertRegex(result.stdout, r"OK\s+demo: high-risk-auth")
        self.assertRegex(result.stdout, r"OK\s+sample release analysis")
        self.assertRegex(result.stdout, r"OK\s+scanner fixture normalization")
        self.assertIn("All checks passed.", result.stdout)


if __name__ == "__main__":
    unittest.main()
