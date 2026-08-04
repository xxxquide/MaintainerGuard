# CLI guide

Veracity is easiest to use through the short `vera` command.

```bash
vera demo
vera init
vera presets
vera scanners
vera doctor
vera verify
vera pr <file>
vera issue <file>
vera release <file>
```

The longer `veracity` command and `python3 -m veracity ...`
module form remain supported for automation and debugging.

## Installation

After the repository is published, install with `pipx`:

```bash
pipx install git+https://github.com/xxxquide/veracity.git
vera demo
```

From a local checkout:

```bash
git clone https://github.com/xxxquide/veracity.git
cd Veracity
python3 -m pip install -e .
vera verify
```

You can also run from source without installing:

```bash
./mg demo
./mg doctor
./mg verify
```

## Quick start

```bash
vera demo
vera init
vera doctor
vera verify
```

`vera demo` runs the high-risk authentication sample by default. It does not
require API keys, a GitHub token, or network access.

## Command reference

### `vera demo`

Run a bundled sample pull request scenario.

```bash
vera demo
vera demo --scenario dependency-advisory
vera demo --scenario ci-workflow-risk
vera demo --scenario secret-finding
vera demo --scenario high-risk-auth --format json
```

### `vera init`

Create a safe repository configuration.

```bash
vera init
vera init --preset minimal
vera init --preset security
vera init --preset strict
vera init --preset docs
vera init --github-action
vera init --force
```

`vera init` creates `.veracity.toml` if it does not already exist. It does
not overwrite files unless `--force` is supplied. `--preset` selects the
built-in policy profile written to `core.policy_preset`; the default is
`security`.

`vera init --github-action` also creates
`.github/workflows/veracity.yml` with safe defaults:

- dry-run enabled;
- comment posting disabled;
- AI disabled by configuration;
- read-only workflow permissions;
- no auto-merge behavior.

The generated workflow is copy-ready for pull-request analysis:

```yaml
name: Veracity

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
      - uses: xxxquide/veracity@v0.4.0
        with:
          mode: analyze-pr
          dry-run: "true"
          post-comment: "false"
          fail-on-risk: none
```

The workflow uses the published Action reference, leaves comment publishing
off, and does not enable AI. `vera init --github-action` will not overwrite an
existing `.veracity.toml` or workflow file unless `--force` is also
supplied:

```bash
vera init --github-action --force
```

### `vera presets`

List built-in policy presets.

```bash
vera presets
```

### `vera scanners`

List scanner input families covered by bundled fixtures.

```bash
vera scanners
```

This is a quick way to see which scanner shapes Veracity currently
normalizes with checked-in sample data. It is not a claim that every
vendor-specific scanner output variant is fully supported.

### `vera doctor`

Check whether Veracity is ready to use in the current directory.

```bash
vera doctor
vera --config path/to/.veracity.toml doctor
```

Missing config is not a hard failure. The command suggests `vera init` and still
checks built-in defaults and bundled sample data.

### `vera verify`

Run deterministic smoke checks without API keys.

```bash
vera verify
```

The command checks configuration loading, bundled demo scenarios, sample PR
analysis, sample issue analysis, sample release analysis, JSON report rendering,
and scanner fixture normalization.

### `vera pr`

Analyze pull-request JSON.

```bash
vera pr examples/sample-data/prs/dependency-update.json \
  --scanner examples/sample-data/scanners/dependency-advisory.json
```

Equivalent long command:

```bash
veracity analyze-pr examples/sample-data/prs/dependency-update.json \
  --scanner examples/sample-data/scanners/dependency-advisory.json
```

### `vera issue`

Analyze issue JSON.

```bash
vera issue examples/sample-data/issues/bug-missing-reproduction.json
```

### `vera release`

Analyze release-readiness JSON.

```bash
vera release examples/sample-data/releases/v0.3.0.json
```

### `vera config`

Print the documented example configuration.

```bash
vera config
vera validate-config
```

### `vera version`

Print the installed Veracity version.

```bash
vera version
```

## JSON output

Most report commands accept `--format json`.

```bash
vera demo --scenario high-risk-auth --format json
vera pr examples/sample-data/prs/dependency-update.json --format json
```

JSON is intended for automation. Markdown remains the default for terminals and
GitHub comments.

## Troubleshooting

### `vera` command not found

Confirm the package is installed in the active environment:

```bash
python3 -m pip install -e .
python3 -m veracity demo --scenario high-risk-auth
```

The module form is useful when a shell cannot find the short console script yet.

### Config file missing

Run `vera init` from the repository root to create `.veracity.toml` with
safe defaults:

```bash
vera init
vera doctor
```

`vera doctor` can still inspect built-in defaults when the config file is missing,
but repository-specific policy checks need a config file.

### Invalid `.veracity.toml`

Print a clean example, compare it with your file, then validate again:

```bash
vera config
vera validate-config
```

### GitHub Action dry-run logs but no PR comment

This is expected when `post-comment: "false"` is configured. Dry-run mode is the
safe default for checking the report in workflow logs without writing to the PR.

If GitHub Action behavior differs from local CLI behavior, keep dry-run mode on
while comparing inputs and read [GitHub automation](github-automation.md).
Comment publishing requires explicit `dry-run: "false"`,
`post-comment: "true"`, `pull-requests: write`, and `issues: write`
permissions. Do not enable comments by default for every repository; turn them
on only after the dry-run report is useful.

Veracity does not prove code is secure, find every vulnerability, or
replace maintainer review. It produces evidence-backed readiness reports and
checklists for human maintainers.
