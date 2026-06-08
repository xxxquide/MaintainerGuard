import unittest
from pathlib import Path

from maintainerguard.config import load_config
from maintainerguard.github import (
    COMMENT_MARKER,
    GitHubClient,
    analysis_hash,
    choose_comment_action,
    parse_github_event,
    publication_allowed,
)


class GitHubTests(unittest.TestCase):
    def test_action_metadata_has_safe_defaults_and_expected_inputs(self):
        root = Path(__file__).resolve().parents[1]
        action = (root / "action.yml").read_text(encoding="utf-8")
        for expected in (
            "mode:",
            "config-path:",
            "output-format:",
            "dry-run:",
            "post-comment:",
            "update-existing-comment:",
            "fail-on-risk:",
            "scanner-result-paths:",
            "report-length:",
            "ai-enabled:",
        ):
            self.assertIn(expected, action)
        self.assertIn("default: \"true\"", action)
        self.assertIn("post-comment:\n    description:", action)
        self.assertIn("default: \"false\"", action)
        self.assertIn("ai-enabled:\n    description:", action)
        self.assertIn("GITHUB_ACTION_PATH", action)
        self.assertIn("PYTHONPATH", action)
        self.assertIn("python3 -m maintainerguard action-run", action)
        self.assertNotIn("cd \"$GITHUB_ACTION_PATH\"", action)

    def test_publication_requires_all_safety_gates(self):
        config = load_config()
        self.assertFalse(publication_allowed(config, explicit_post=True))
        self.assertFalse(publication_allowed(config, explicit_post=False))

        config.dry_run = False
        config.github.post_comments = True
        self.assertFalse(
            publication_allowed(
                config,
                explicit_post=True,
                pull_request={"author": {"type": "Bot"}, "draft": False, "labels": []},
            )
        )
        self.assertFalse(
            publication_allowed(
                config,
                explicit_post=True,
                pull_request={"author": {"type": "User"}, "draft": True, "labels": []},
            )
        )
        self.assertTrue(
            publication_allowed(
                config,
                explicit_post=True,
                pull_request={"author": {"type": "User"}, "draft": False, "labels": []},
            )
        )

    def test_comment_strategy_updates_one_and_skips_identical(self):
        body = "# report"
        digest = analysis_hash(body)
        existing = [{"id": 4, "body": f"{COMMENT_MARKER}\n<!-- hash:{digest} -->\nold"}]
        self.assertEqual("skip", choose_comment_action(existing, body).action)

        changed = choose_comment_action(existing, "# changed")
        self.assertEqual("update", changed.action)
        self.assertEqual(4, changed.comment_id)

        self.assertEqual("create", choose_comment_action([], body).action)

    def test_comment_strategy_respects_update_policy_and_total_length(self):
        existing = [{"id": 9, "body": f"{COMMENT_MARKER}\nold"}]
        action = choose_comment_action(existing, "changed", update_previous=False)
        self.assertEqual("skip", action.action)

        limited = choose_comment_action([], "x" * 5000, max_characters=1000)
        self.assertEqual(1000, len(limited.body))
        self.assertTrue(limited.body.startswith(COMMENT_MARKER))
        self.assertEqual(1, limited.body.count(COMMENT_MARKER))

    def test_parses_pull_request_event_without_trusting_file_contents(self):
        event_type, payload = parse_github_event(
            {
                "number": 8,
                "repository": {"full_name": "owner/repo"},
                "pull_request": {
                    "number": 8,
                    "title": "Change auth",
                    "body": "Details",
                    "draft": False,
                    "user": {"login": "alice", "type": "User"},
                    "labels": [{"name": "review"}],
                    "files": [{"filename": "untrusted"}],
                },
            }
        )
        self.assertEqual("pull_request", event_type)
        self.assertEqual("owner/repo", payload["repository"])
        self.assertNotIn("files", payload)

    def test_github_client_paginates_pr_files_up_to_configured_limit(self):
        class FakeClient(GitHubClient):
            def __init__(self):
                self.calls = []

            def _request(self, method, path, payload=None):
                self.calls.append(path)
                if path.endswith("page=1"):
                    return [{"filename": f"src/{index}.py"} for index in range(100)]
                return [{"filename": f"src/{index}.py"} for index in range(100, 180)]

        client = FakeClient()
        files = client.get_pull_files("owner/repo", 12, 150)
        self.assertEqual(150, len(files))
        self.assertEqual(2, len(client.calls))

    def test_github_client_paginates_comments_to_find_existing_marker(self):
        class FakeClient(GitHubClient):
            def __init__(self):
                self.calls = []

            def _request(self, method, path, payload=None):
                self.calls.append(path)
                if path.endswith("page=1"):
                    return [{"id": index, "body": "other"} for index in range(100)]
                return [{"id": 101, "body": COMMENT_MARKER}]

        client = FakeClient()
        comments = client.get_issue_comments("owner/repo", 12)
        self.assertEqual(101, len(comments))
        self.assertEqual(2, len(client.calls))


if __name__ == "__main__":
    unittest.main()
