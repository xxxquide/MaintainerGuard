# Upgrading to v0.4

v0.4 renames the project from MaintainerGuard to Veracity and changes scanner
behaviour. The rename is breaking: the package, the commands and the configuration
file all change name.

## Why the rename

Two reasons, both about accuracy rather than taste.

"Guard" promised protection that the tool's own disclaimer denies — it does not
find vulnerabilities and does not prove code is secure; it explains the output of
scanners you run. And the previous headline read "Evidence-first **AI** maintainer
assistant" while the language model was disabled by default and could not affect
any verdict. Both parts of the old identity described something the software did
not do.

## What to change

### 1. Reinstall

```bash
pipx uninstall maintainerguard
pipx install git+https://github.com/xxxquide/veracity.git
```

The distribution name is now `veracity`. Nothing was ever published to PyPI under
the old name.

### 2. Commands

| Before | Now |
|---|---|
| `maintainerguard` | `veracity` |
| `mg` | `vera` |
| `python3 -m maintainerguard` | `python3 -m veracity` |
| `./mg` (from a checkout) | `./vera` |

Subcommands, flags and output formats are unchanged.

### 3. Configuration file

```bash
git mv .maintainerguard.toml .veracity.toml
```

Contents are unchanged. If Veracity finds `.maintainerguard.toml` and no
`.veracity.toml`, it stops with an error naming both files. It deliberately does
not fall back to defaults: a run that silently ignores your configuration looks
like a clean run, which is the failure mode this release exists to remove.

### 4. Skip label

The pull-request label `skip-maintainerguard` is now `skip-veracity`. The
`no-ai` and `skip-ai` labels are unchanged. If you use a custom set, check
`github.skip_labels` in your configuration.

### 5. Environment variable

`MG_REPORT_LENGTH` is now `VERACITY_REPORT_LENGTH`.

### 6. GitHub Action reference

```yaml
# before
- uses: xxxquide/MaintainerGuard@v0.3.1
# now
- uses: xxxquide/veracity@v0.4.0
```

GitHub redirects the old repository path, so an un-updated workflow keeps
resolving, but update it: redirects are not a contract.

The Action's inputs are unchanged. Its `branding.icon` changed from `shield` to
`filter`, for the same reason the name did.

### 7. Existing PR comments

The hidden marker changed from `<!-- maintainerguard:merge-readiness -->` to
`<!-- veracity:merge-readiness -->`. The first run after upgrading will not
recognise a comment written by an older version and will create a new one. Delete
the old comment once, and the one-comment behaviour resumes.

## Behaviour changes worth knowing

These are not cosmetic and they can change a verdict.

- **Findings are attributed to the change.** Only findings in scope for the change
  under review affect the verdict, risk level and checklist. Others are listed under
  `Pre-existing repository findings`. If you supply repository-wide scanner reports,
  expect risk levels to drop — that is the point. See the README for the rule.
- **Trivy native JSON now reads `Secrets`, `Misconfigurations` and `Licenses`.** If
  you supply `trivy fs` output, expect more findings than before, including ones
  that were previously dropped without a warning.
- **gitleaks native JSON works.** It is a top-level array; older versions raised
  `ValueError`.
- **Semgrep native JSON is no longer treated as secret-scanner output.** Older
  versions marked every Semgrep finding as a blocking secret, which produced
  `Blocked by scanner finding` for ordinary static-analysis results. If your
  pipeline depended on that verdict, it depended on a bug.
- **Unrecognised scanner payloads now raise `UnsupportedScannerInput`** instead of
  returning no findings. If a previously "clean" report goes red, that report was
  never being parsed.
- **SARIF suppressions and baseline state are honoured.** Findings you dismissed,
  and findings marked `unchanged`/`absent`, are excluded.
- **CodeQL `security-severity` drives severity.** A 9.8 finding is now Critical
  where it was previously High.
- **Report section order changed.** Decision guidance, checklist, evidence and
  limitations come first, so a truncated GitHub comment keeps them.
- **Detectors match whole words.** `terraform/main.tf` is no longer classified as a
  rendering change, and test and documentation paths are no longer reported as
  security-sensitive changes.
- **`[[policy]]` field types are validated.** `blocking = "yes"` was previously
  truthy and silently escalated risk to Critical; it is now a configuration error.

## Nothing to do

- Report JSON keeps `schema_version` `1.0`; `ScannerFinding` gained fields
  (`in_changed_scope`, `scope_reason`, `cwe`, `fingerprint`) but removed none.
- Policy presets, thresholds and module toggles are unchanged.
- No runtime dependencies were added. hatchling is a build-time dependency only.
