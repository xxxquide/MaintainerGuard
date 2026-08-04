"""Guards against the previous brand name reappearing in the tree.

The rename in v0.4 touched 380 occurrences across 76 files. A partial rename is
worse than none: a stale command name in the docs, or a stale marker in the
publishing code, fails at the moment someone first tries to use it.

Three places may still name the old project, and only these three:

- ``CHANGELOG.md`` records what shipped under the old name.
- ``docs/upgrading-to-v0.4.md`` tells people what to rename.
- ``veracity/config.py`` recognises the old configuration filename in order to
  raise a helpful error instead of silently using defaults.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OLD_BRAND = re.compile(r"maintainerguard", re.IGNORECASE)
# The bare short command that was replaced by `vera`.
# A leading "/" must NOT be excluded, or "./mg" slips through — it did.
OLD_COMMAND = re.compile(r"(?<![A-Za-z0-9_.\-])mg(?![A-Za-z0-9_\-])")

ALLOWED_BRAND_FILES = {
    "CHANGELOG.md",
    "docs/upgrading-to-v0.4.md",
    "veracity/config.py",
    "tests/test_branding.py",
}

SKIP_DIRS = {".git", "__pycache__", "assets", "dist", "build", ".venv"}
# Byte-for-byte scanner output; never edit it for cosmetic reasons.
SKIP_PREFIXES = ("tests/fixtures/real-scanners/",)
TEXT_SUFFIXES = {
    ".py", ".md", ".toml", ".yml", ".yaml", ".json", ".cff", ".txt", ".sh", ".cfg", ""
}


def tracked_text_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(SKIP_PREFIXES):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            yield rel, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue


class NoStaleBrandTests(unittest.TestCase):
    def test_old_brand_name_only_appears_where_it_must(self):
        offenders = {
            rel: len(OLD_BRAND.findall(text))
            for rel, text in tracked_text_files()
            if rel not in ALLOWED_BRAND_FILES and OLD_BRAND.search(text)
        }
        self.assertEqual(
            {},
            offenders,
            "The previous brand name survives in files that should not mention it: "
            f"{offenders}",
        )

    def test_old_short_command_is_gone(self):
        offenders = {
            rel: OLD_COMMAND.findall(text)
            for rel, text in tracked_text_files()
            if rel not in ALLOWED_BRAND_FILES and OLD_COMMAND.search(text)
        }
        self.assertEqual({}, offenders, f"`mg` should now be `vera`: {offenders}")

    def test_the_allowlist_itself_stays_honest(self):
        # An allowlisted file that no longer mentions the old name should be
        # removed from the allowlist, so the exception list cannot rot into a
        # blanket exemption.
        texts = dict(tracked_text_files())
        stale = [
            rel
            for rel in sorted(ALLOWED_BRAND_FILES - {"tests/test_branding.py"})
            if rel in texts and not OLD_BRAND.search(texts[rel])
        ]
        self.assertEqual(
            [],
            stale,
            f"These files no longer need a branding exception: {stale}",
        )


class BrandIsConsistentTests(unittest.TestCase):
    def test_package_command_and_config_names_agree(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('name = "veracity"', pyproject)
        self.assertIn('veracity = "veracity.cli:main"', pyproject)
        self.assertIn('vera = "veracity.cli:main"', pyproject)
        self.assertTrue((ROOT / "veracity" / "cli.py").is_file())
        self.assertTrue((ROOT / ".veracity.toml").is_file())
        self.assertTrue((ROOT / "vera").is_file())

    def test_shim_invokes_the_renamed_package(self):
        self.assertIn("python3 -m veracity", (ROOT / "vera").read_text(encoding="utf-8"))

    def test_comment_marker_carries_the_new_brand(self):
        from veracity.github import COMMENT_MARKER

        self.assertEqual("<!-- veracity:merge-readiness -->", COMMENT_MARKER)

    def test_workflows_are_renamed(self):
        workflows = {p.name for p in (ROOT / ".github" / "workflows").glob("*.yml")}
        for expected in ("veracity-pr.yml", "veracity-issue.yml", "veracity-release.yml"):
            self.assertIn(expected, workflows)

    def test_action_metadata_makes_no_protection_claim(self):
        action = (ROOT / "action.yml").read_text(encoding="utf-8")
        self.assertIn("name: Veracity", action)
        self.assertNotIn("icon: shield", action)

    def test_no_headline_claims_an_llm_the_tool_does_not_need(self):
        for rel in ("README.md", "pyproject.toml", "CITATION.cff", "action.yml"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn("AI maintainer assistant", text, rel)


class MigrationGuidanceTests(unittest.TestCase):
    def test_legacy_config_file_raises_instead_of_silently_using_defaults(self):
        import os
        import tempfile

        from veracity.config import ConfigError, load_config

        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                Path(".maintainerguard.toml").write_text("[core]\n", encoding="utf-8")
                with self.assertRaises(ConfigError) as caught:
                    load_config()
            finally:
                os.chdir(cwd)
        message = str(caught.exception)
        self.assertIn(".veracity.toml", message)
        self.assertIn("upgrading-to-v0.4", message)

    def test_upgrade_guide_exists_and_covers_the_breaking_changes(self):
        guide = (ROOT / "docs" / "upgrading-to-v0.4.md").read_text(encoding="utf-8")
        for topic in (
            ".veracity.toml",
            "skip-veracity",
            "VERACITY_REPORT_LENGTH",
            "vera",
            "veracity:merge-readiness",
        ):
            self.assertIn(topic, guide, topic)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
