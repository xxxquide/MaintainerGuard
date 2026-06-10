# Maintainer policies

Policies connect repository-specific path patterns to review requirements.
Use `core.policy_preset` for common profiles:

- `minimal`: disables repository policy checks;
- `security`: default checks for auth, workflows, dependency manifests, and public interfaces;
- `strict`: blocking auth, workflow, and dependency checks for repositories that want merge gates;
- `docs`: documentation-focused checks for README, docs, examples, and changelog paths.

Custom `[[policy]]` entries replace the selected preset.

```toml
[[policy]]
name = "Authentication changes require tests"
paths = ["**/auth/**", "**/session*"]
require = "tests"
blocking = false
message = "Add or confirm tests for changed authentication behavior."
```

Supported requirements are:

- `tests`: passes when related test files changed
- `docs`: passes when related documentation files changed
- `scanner`: passes when at least one scanner input was supplied
- `manual_review`: intentionally remains unmet to surface maintainer review

Set `blocking = true` only for a repository rule that must prevent a ready
verdict. Failed blocking policies produce Critical risk and a
`Changes requested` verdict. Keep policies narrow and explain the expected
maintainer action in `message`.

Common policy patterns:

- auth/session paths require tests;
- public CLI or configuration changes require docs;
- dependency manifests require scanner results;
- release workflows require manual review;
- high-risk release paths can be blocking in mature repositories;
- docs-only changes usually stay low risk because no elevated detector fires;
- skip labels such as `skip-maintainerguard` disable analysis.

Policies should not accuse contributors of intent. Use messages that describe
what maintainers should verify.
