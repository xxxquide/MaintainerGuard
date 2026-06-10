# Configuration reference

MaintainerGuard reads `.maintainerguard.toml` from the current directory or an
explicit path passed through `--config`. Unknown sections, unknown keys,
incorrect types, unsupported policy requirements, and invalid thresholds fail
validation.

## Core

- `dry_run`: disables publication unless explicitly set to `false`
- `report_mode`: `concise` or `detailed`
- `output_format`: `markdown` or `json`
- `policy_preset`: built-in policy set, one of `minimal`, `security`, `strict`, or `docs`
- `language`: metadata for future language support; current output is English
- `log_level`: reserved for operational logging policy

## AI

AI is optional and disabled by default. Configure `enabled`, `provider`,
`model`, `api_key_env`, `endpoint`, and `timeout_seconds`. The current provider
adapter supports the OpenAI Responses API. A missing key or API failure leaves
the deterministic report intact.

## GitHub

`post_comments`, `update_previous_comment`, `comment_on_drafts`,
`comment_on_bots`, `max_comment_characters`, and `skip_labels` control
publication. Publishing still requires explicit Action or CLI publication
enablement. The Action defaults to `dry-run: "true"` and `post-comment:
"false"`.

## Privacy

`max_diff_characters` and `max_files_analyzed` define data boundaries. Common
secret patterns are always redacted before optional AI requests. The MVP never
reads environment variables except the configured AI key and `GITHUB_TOKEN`.

## Modules, paths, and thresholds

Module toggles control deterministic detectors. Path lists use shell-style glob
patterns. `paths.scanner_inputs` can provide scanner JSON files that
`analyze-pr` loads when no workflow-specific list is sufficient. Risk thresholds
must be increasing positive integers. Critical risk is reserved for explicit
critical blocking scanner findings or failed blocking policies.

Use `.maintainerguard.toml` and `mg config` as the complete executable
reference. `python3 -m maintainerguard print-config` remains available for
debugging and automation.

## Policy examples

Use `policy_preset` when a repository only needs a standard profile:

```toml
[core]
policy_preset = "strict"
```

Available presets:

- `minimal`: no repository policy checks
- `security`: default auth, workflow, dependency, and public-interface checks
- `strict`: security-style checks with blocking rules for auth, workflow, and dependency changes
- `docs`: documentation-focused checks for README, docs, examples, and changelog paths

Custom `[[policy]]` entries replace the selected preset. This keeps repository
specific policies explicit and avoids silently combining preset checks with
custom rules.

```toml
[[policy]]
name = "Dependency changes should include scanner results"
paths = ["requirements*.txt", "package.json", "go.mod"]
require = "scanner"
blocking = false
message = "Run or attach dependency scanner results for changed package inputs."

[[policy]]
name = "Release workflow requires maintainer approval"
paths = [".github/workflows/release.yml"]
require = "manual_review"
blocking = true
message = "A maintainer must review release workflow permission changes."
```

Supported `require` values are `tests`, `docs`, `scanner`, and
`manual_review`.
