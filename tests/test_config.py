import tempfile
import unittest
from pathlib import Path

from maintainerguard.config import ConfigError, default_config_toml, load_config


class ConfigTests(unittest.TestCase):
    def test_defaults_are_safe(self):
        config = load_config()

        self.assertTrue(config.dry_run)
        self.assertFalse(config.ai.enabled)
        self.assertFalse(config.github.post_comments)
        self.assertTrue(config.github.update_previous_comment)
        self.assertGreater(config.privacy.max_diff_characters, 0)
        self.assertEqual("security", config.policy_preset)
        self.assertTrue(config.policies)

    def test_loads_valid_toml_and_rejects_unknown_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".maintainerguard.toml"
            path.write_text("[core]\ndry_run = false\nreport_mode = \"detailed\"\n")
            config = load_config(path)
            self.assertFalse(config.dry_run)
            self.assertEqual("detailed", config.report_mode)

            path.write_text("[core]\nunknown = true\n")
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_example_config_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".maintainerguard.toml"
            path.write_text(default_config_toml())
            config = load_config(path)
            self.assertTrue(config.dry_run)
            self.assertEqual("security", config.policy_preset)

            path.write_text(default_config_toml("minimal"))
            minimal = load_config(path)
            self.assertEqual("minimal", minimal.policy_preset)
            self.assertEqual([], minimal.policies)

    def test_policy_presets_expand_when_no_custom_policies_are_set(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".maintainerguard.toml"

            path.write_text("[core]\npolicy_preset = \"minimal\"\n")
            self.assertEqual([], load_config(path).policies)

            path.write_text("[core]\npolicy_preset = \"security\"\n")
            security = load_config(path)
            self.assertTrue(any(policy.require == "tests" for policy in security.policies))
            self.assertFalse(any(policy.blocking for policy in security.policies))

            path.write_text("[core]\npolicy_preset = \"strict\"\n")
            strict = load_config(path)
            self.assertTrue(any(policy.blocking for policy in strict.policies))
            self.assertTrue(any(policy.require == "manual_review" for policy in strict.policies))

            path.write_text("[core]\npolicy_preset = \"docs\"\n")
            docs = load_config(path)
            self.assertEqual(1, len(docs.policies))
            self.assertEqual("docs", docs.policies[0].require)

    def test_custom_policies_override_policy_preset(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".maintainerguard.toml"
            path.write_text(
                "\n".join(
                    [
                        "[core]",
                        'policy_preset = "strict"',
                        "",
                        "[[policy]]",
                        'name = "Docs only"',
                        'paths = ["docs/**"]',
                        'require = "docs"',
                    ]
                )
            )

            config = load_config(path)
            self.assertEqual(1, len(config.policies))
            self.assertEqual("Docs only", config.policies[0].name)

    def test_rejects_invalid_types_and_threshold_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".maintainerguard.toml"
            path.write_text("[core]\ndry_run = \"yes\"\n")
            with self.assertRaises(ConfigError):
                load_config(path)

            path.write_text("[risk_thresholds]\nmedium = 7\nhigh = 3\ncritical = 12\n")
            with self.assertRaises(ConfigError):
                load_config(path)

            path.write_text("[core]\npolicy_preset = \"maximum\"\n")
            with self.assertRaises(ConfigError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
