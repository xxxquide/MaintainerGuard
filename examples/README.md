# MaintainerGuard Examples

The examples directory contains sample input data and rendered reports that can
be used without API keys or network access.

## Best first demo

Run the high-risk authentication scenario first:

```bash
mg demo --scenario high-risk-auth
```

It demonstrates the main MaintainerGuard value: changed files, policy signals,
test impact, scanner evidence, decision guidance, a maintainer checklist, and
explicit limitations in one report.

## Other useful demos

```bash
mg demo --scenario dependency-advisory
mg demo --scenario ci-workflow-risk
mg demo --scenario secret-finding
mg demo --scenario docs-only
mg demo --scenario test-only
mg demo --scenario high-risk-auth --format json
```

## Sample data

- `configs/` - safe example `.maintainerguard.toml` files for the built-in
  `minimal`, `security`, `strict`, and `docs` policy presets.
- `sample-data/prs/` - pull-request fixtures for merge readiness analysis.
- `sample-data/issues/` - issue fixtures for triage reports.
- `sample-data/releases/` - release-readiness fixture data.
- `sample-data/scanners/` - normalized scanner inputs and SARIF-like examples.
- `sample-data/github/` - small GitHub event fixtures for local automation tests.

## Rendered reports

- [High-risk auth](reports/high-risk-auth.md)
- [Dependency advisory](reports/dependency-advisory.md)
- [CI workflow risk](reports/ci-workflow-risk.md)
- [Secret finding](reports/secret-finding.md)
- [Docs-only low risk](reports/docs-only-low-risk.md)
- [Test-only low risk](reports/test-only-low-risk.md)
- [Issue triage](reports/issue-triage.md)
- [Release readiness](reports/release-readiness.md)

The rendered reports are snapshots of deterministic sample output. If report
rendering changes intentionally, regenerate the relevant report and update tests.
