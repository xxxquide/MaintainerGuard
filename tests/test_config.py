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
            self.assertTrue(load_config(path).dry_run)

    def test_rejects_invalid_types_and_threshold_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".maintainerguard.toml"
            path.write_text("[core]\ndry_run = \"yes\"\n")
            with self.assertRaises(ConfigError):
                load_config(path)

            path.write_text("[risk_thresholds]\nmedium = 7\nhigh = 3\ncritical = 12\n")
            with self.assertRaises(ConfigError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
