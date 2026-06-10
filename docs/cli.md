# CLI guide

MaintainerGuard is easiest to use through the short `mg` command.

```bash
mg demo
mg init
mg doctor
mg verify
mg pr <file>
mg issue <file>
mg release <file>
```

The longer `maintainerguard` command and `python3 -m maintainerguard ...`
module form remain supported for automation and debugging.

## Installation

After the repository is published, install with `pipx`:

```bash
pipx install git+https://github.com/xxxquide/MaintainerGuard.git
mg demo
```

From a local checkout:

```bash
git clone https://github.com/xxxquide/MaintainerGuard.git
cd MaintainerGuard
python3 -m pip install -e .
mg verify
```

You can also run from source without installing:

```bash
./mg demo
./mg doctor
./mg verify
```

## Quick start

```bash
mg demo
mg init
mg doctor
mg verify
```

`mg demo` runs the high-risk authentication sample by default. It does not
require API keys, a GitHub token, or network access.

## Command reference

### `mg demo`

Run a bundled sample pull request scenario.

```bash
mg demo
mg demo --scenario dependency-advisory
mg demo --scenario ci-workflow-risk
mg demo --scenario secret-finding
mg demo --scenario high-risk-auth --format json
```

### `mg init`

Create a safe repository configuration.

```bash
mg init
mg init --github-action
mg init --force
```

`mg init` creates `.maintainerguard.toml` if it does not already exist. It does
not overwrite files unless `--force` is supplied.

`mg init --github-action` also creates
`.github/workflows/maintainerguard.yml` with safe defaults:

- dry-run enabled;
- comment posting disabled;
- AI disabled by configuration;
- read-only workflow permissions;
- no auto-merge behavior.

The generated workflow is copy-ready for pull-request analysis:

```yaml
name: MaintainerGuard

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

permissions:
  contents: read
  pull-requests: read

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
      - uses: xxxquide/MaintainerGuard@v0.1.4
        with:
          mode: analyze-pr
          dry-run: "true"
          post-comment: "false"
          fail-on-risk: none
```

The workflow uses the published Action reference, leaves comment publishing
off, and does not enable AI. `mg init --github-action` will not overwrite an
existing `.maintainerguard.toml` or workflow file unless `--force` is also
supplied:

```bash
mg init --github-action --force
```

### `mg doctor`

Check whether MaintainerGuard is ready to use in the current directory.

```bash
mg doctor
mg --config path/to/.maintainerguard.toml doctor
```

Missing config is not a hard failure. The command suggests `mg init` and still
checks built-in defaults and bundled sample data.

### `mg verify`

Run deterministic smoke checks without API keys.

```bash
mg verify
```

The command checks configuration loading, bundled demo scenarios, sample PR
analysis, sample issue analysis, sample release analysis, and JSON report
rendering.

### `mg pr`

Analyze pull-request JSON.

```bash
mg pr examples/sample-data/prs/dependency-update.json \
  --scanner examples/sample-data/scanners/dependency-advisory.json
```

Equivalent long command:

```bash
maintainerguard analyze-pr examples/sample-data/prs/dependency-update.json \
  --scanner examples/sample-data/scanners/dependency-advisory.json
```

### `mg issue`

Analyze issue JSON.

```bash
mg issue examples/sample-data/issues/bug-missing-reproduction.json
```

### `mg release`

Analyze release-readiness JSON.

```bash
mg release examples/sample-data/releases/v0.2.0.json
```

### `mg config`

Print the documented example configuration.

```bash
mg config
mg validate-config
```

### `mg version`

Print the installed MaintainerGuard version.

```bash
mg version
```

## JSON output

Most report commands accept `--format json`.

```bash
mg demo --scenario high-risk-auth --format json
mg pr examples/sample-data/prs/dependency-update.json --format json
```

JSON is intended for automation. Markdown remains the default for terminals and
GitHub comments.

## Troubleshooting

If `mg` is not found, confirm the package is installed in the active
environment:

```bash
python3 -m pip install -e .
python3 -m maintainerguard demo --scenario high-risk-auth
```

If configuration fails, print a clean example and compare it with your file:

```bash
mg config
mg validate-config
```

If GitHub Action behavior differs from local CLI behavior, start with dry-run
mode and read [GitHub automation](github-automation.md). Comment publishing
requires explicit `dry-run: "false"`, `post-comment: "true"`,
`pull-requests: write`, and `issues: write` permissions.

MaintainerGuard does not prove code is secure, find every vulnerability, or
replace maintainer review. It produces evidence-backed readiness reports and
checklists for human maintainers.
