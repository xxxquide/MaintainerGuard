# Upgrading to v0.3.0

MaintainerGuard v0.3.0 focuses on scanner trust and documentation clarity.
There are no breaking CLI or configuration changes from `v0.2.x`.

## Recommended Action version

Use the current published Action tag in public workflows:

```yaml
- uses: xxxquide/MaintainerGuard@v0.3.1
```

Local development can still use `uses: ./` when testing this repository before a
release.

## What changed

- SARIF results with the same tool, rule, title, severity, and category are
  grouped so reports are less noisy.
- SARIF `region.startLine` is preserved as `path:line`; path-only fallback is
  still used when no line is available.
- SARIF rule metadata can provide severity/category context when individual
  results are sparse.
- Scanner fixtures now cover CodeQL-like SARIF, Semgrep-like findings,
  Gitleaks-like results, Dependabot-like advisories, and Trivy variants.
- Scanner documentation now includes a coverage matrix that distinguishes
  native adapters from generic JSON mappings.

## What did not change

- Safe defaults are unchanged: dry-run enabled, AI disabled, comments disabled,
  and no auto-merge behavior.
- Existing `mg demo`, `mg init`, `mg doctor`, `mg verify`, `mg pr`, `mg issue`,
  and `mg release` commands remain compatible.
- Trivy vulnerability normalization remains supported and covered by tests.
- MaintainerGuard still explains supplied scanner output. It does not replace
  scanners, prove exploitability, or claim to find every vulnerability.

## Suggested verification

```bash
mg verify
mg pr examples/sample-data/prs/dependency-update.json \
  --scanner examples/sample-data/scanners/dependency-advisory.json
mg release examples/sample-data/releases/v0.3.0.json
```

For repository maintainers:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q maintainerguard
python3 -m pip wheel . --no-deps
```
