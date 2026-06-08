# GitHub automation

The included workflows and `action.yml` run MaintainerGuard in dry-run mode by
default. They intentionally use read-only permissions unless you explicitly
choose comment publishing.

## First-class Action inputs

The composite Action supports:

- `mode`: `analyze-pr`, `analyze-issue`, `analyze-release`, `validate-config`, or `demo`
- `config-path`
- `output-format`: `markdown` or `json`
- `dry-run`
- `post-comment`
- `update-existing-comment`
- `fail-on-risk`: `none`, `critical`, or `high`
- `scanner-result-paths`
- `scenario-or-sample-input-path`
- `ai-enabled`
- `report-length`: `concise` or `detailed`

Safe default:

```yaml
permissions:
  contents: read
  pull-requests: read

steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with:
      python-version: "3.11"
  - uses: ./
    with:
      mode: analyze-pr
      dry-run: "true"
      fail-on-risk: none
```

## Pull requests

`.github/workflows/maintainerguard-pr.yml` uses the composite Action. The
Action entrypoint is `action-run`; it reads `GITHUB_EVENT_PATH` from the caller
workspace and, with a read token, retrieves a bounded list of PR files through
the GitHub REST API.

`github-run` remains available as a direct CLI helper for manually running
MaintainerGuard against a GitHub event JSON file:

```bash
python3 -m maintainerguard github-run "$GITHUB_EVENT_PATH"
```

Use `action-run` through `action.yml` for GitHub Actions. Use `github-run` when
you intentionally want the lower-level CLI helper.

## Local and published Action usage

For local repository testing, use:

```yaml
- uses: ./
```

After publishing a release tag, users can reference the reusable Action from
another repository:

```yaml
- uses: xxxquide/MaintainerGuard@v0.1.1
```

The Action prepends `$GITHUB_ACTION_PATH` to `PYTHONPATH` so Python imports the
MaintainerGuard package from the published Action checkout. It keeps the working
directory as the caller repository, so `.maintainerguard.toml`, scanner paths,
sample input paths, and `GITHUB_EVENT_PATH` still resolve relative to the caller
workspace.

## Safe comment publishing

Before enabling comments:

1. Confirm local reports and policies.
2. Set `core.dry_run = false`.
3. Set `github.post_comments = true`.
4. Add `pull-requests: write` and `issues: write` permissions to the specific workflow job.
5. Set the Action input `post-comment: "true"` or add `--post` to `github-run`.

All gates are required. MaintainerGuard uses one hidden marker, updates the
existing marked comment, and skips publication when the analysis hash is
unchanged. It respects configured skip labels and draft/bot settings.

Comment publishing requires intentionally broader permissions:

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
```

Do not enable `pull-requests: write`, `issues: write`, `dry-run: "false"`,
and `post-comment: "true"` until dry-run reports are acceptable for the
repository.

## Issues and scheduled releases

The issue workflow produces a local triage report without posting. The scheduled
release workflow demonstrates a prepared local feed. A production release feed
can be assembled from authorized GitHub API data, then passed to
`analyze-release`.

Never use untrusted secrets on `pull_request_target` events. Keep permissions
minimal and review workflow changes manually.
