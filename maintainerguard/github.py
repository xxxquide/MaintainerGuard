"""Safe GitHub event and one-comment automation helpers."""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from typing import Any

from .config import Config
from .models import CommentAction


COMMENT_MARKER = "<!-- maintainerguard:merge-readiness -->"


def analysis_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def choose_comment_action(
    existing_comments: list[dict[str, Any]],
    body: str,
    *,
    update_previous: bool = True,
    max_characters: int | None = None,
) -> CommentAction:
    digest = analysis_hash(body)
    complete_body = f"{COMMENT_MARKER}\n<!-- hash:{digest} -->\n{body}"
    if max_characters is not None:
        complete_body = complete_body[:max_characters]
    for comment in existing_comments:
        existing_body = str(comment.get("body", ""))
        if COMMENT_MARKER not in existing_body:
            continue
        if f"<!-- hash:{digest} -->" in existing_body:
            return CommentAction("skip", int(comment.get("id", 0)) or None, complete_body)
        if not update_previous:
            return CommentAction("skip", int(comment.get("id", 0)) or None, complete_body)
        return CommentAction("update", int(comment.get("id", 0)) or None, complete_body)
    return CommentAction("create", None, complete_body)


def publication_allowed(
    config: Config,
    explicit_post: bool,
    pull_request: dict[str, Any] | None = None,
) -> bool:
    if not (explicit_post and not config.dry_run and config.github.post_comments):
        return False
    if pull_request is None:
        return True
    if pull_request.get("draft") and not config.github.comment_on_drafts:
        return False
    author = pull_request.get("author", {})
    if (
        isinstance(author, dict)
        and str(author.get("type", "")).lower() == "bot"
        and not config.github.comment_on_bots
    ):
        return False
    labels = [
        str(label.get("name", "")) if isinstance(label, dict) else str(label)
        for label in pull_request.get("labels", [])
    ]
    return not bool(set(labels) & set(config.github.skip_labels))


def parse_github_event(event: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if "pull_request" in event:
        pr = event["pull_request"]
        return "pull_request", {
            "schema_version": "1.0",
            "number": pr.get("number", event.get("number")),
            "title": pr.get("title", ""),
            "body": pr.get("body", ""),
            "draft": pr.get("draft", False),
            "author": pr.get("user", {}),
            "labels": pr.get("labels", []),
            "repository": event.get("repository", {}).get("full_name", ""),
        }
    if "issue" in event:
        issue = event["issue"]
        return "issue", {
            "schema_version": "1.0",
            "number": issue.get("number", event.get("number")),
            "title": issue.get("title", ""),
            "body": issue.get("body", ""),
            "labels": issue.get("labels", []),
            "repository": event.get("repository", {}).get("full_name", ""),
        }
    raise ValueError("Unsupported GitHub event")


class GitHubClient:
    def __init__(self, token: str, api_url: str = "https://api.github.com") -> None:
        if not token:
            raise ValueError("GitHub token is required")
        self._token = token
        self._api_url = api_url.rstrip("/")

    def get_pull_files(self, repository: str, number: int, max_files: int) -> list[dict[str, Any]]:
        data = []
        page = 1
        while len(data) < max_files:
            batch = self._request(
                "GET",
                f"/repos/{repository}/pulls/{number}/files?per_page=100&page={page}",
            )
            if not isinstance(batch, list):
                raise RuntimeError("GitHub pull-files response was not a list")
            data.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return [
            {
                "path": item.get("filename", ""),
                "status": item.get("status", "modified"),
                "patch": item.get("patch", ""),
            }
            for item in data[:max_files]
        ]

    def get_issue_comments(
        self, repository: str, number: int, max_comments: int = 500
    ) -> list[dict[str, Any]]:
        comments = []
        page = 1
        while len(comments) < max_comments:
            batch = self._request(
                "GET",
                f"/repos/{repository}/issues/{number}/comments?per_page=100&page={page}",
            )
            if not isinstance(batch, list):
                raise RuntimeError("GitHub comments response was not a list")
            comments.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return comments[:max_comments]

    def create_comment(self, repository: str, number: int, body: str) -> dict[str, Any]:
        return self._request("POST", f"/repos/{repository}/issues/{number}/comments", {"body": body})

    def update_comment(self, repository: str, comment_id: int, body: str) -> dict[str, Any]:
        return self._request("PATCH", f"/repos/{repository}/issues/comments/{comment_id}", {"body": body})

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        request = urllib.request.Request(
            f"{self._api_url}{path}",
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "MaintainerGuard/0.1",
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"GitHub API request failed: {exc}") from exc
