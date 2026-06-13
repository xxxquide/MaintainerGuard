# Roadmap

## v0.1 - implemented baseline

- Local runner and sample scenarios
- Merge-readiness reports and evidence table
- Security-sensitive, dependency, docs, tests, and release detectors
- Generic JSON, SARIF, OSV-style, and secret-scanner normalization
- Configuration, repository policies, Markdown/JSON reports, and tests
- Optional validated AI enrichment
- Guarded GitHub pull-request comment strategy
- Issue triage and release-readiness local feeds
- Composite GitHub Action metadata with safe defaults
- Decision guidance and release verdicts
- Supply-chain workflow and build-script signals

## v0.2 - implemented policy presets and SARIF evidence

- Policy presets for `minimal`, `security`, `strict`, and `docs`
- `mg presets` and `mg init --preset ...`
- SARIF line evidence using `path:line` when `region.startLine` is present
- SARIF rule default severity and description fallback
- Preserved Trivy vulnerability normalization
- Updated policy preset examples and docs

## v0.3 - scanner trust and fixture depth

- Scanner fixture coverage matrix
- CodeQL-like, Semgrep-like, Gitleaks-like, Dependabot-like, and Trivy variant fixtures
- SARIF duplicate grouping for matching rule/title/severity/category results
- Better SARIF severity/category normalization from rule metadata
- v0.2.x to v0.3.0 upgrade notes
- Better examples navigation for scanner fixtures and release samples

## v0.4 - policy intelligence and repository fit

- Better policy diagnostics explaining which rule fired and why
- Stronger path-to-test and path-to-doc heuristics
- More mature preset examples and custom override guidance
- Optional policy debugging output if it stays concise

## Future research

- SBOM and provenance integrations
- Scanner adapter extension points when real contributor demand appears
- GitLab support if maintainers ask for it
- Local-model adapter if it can stay optional and safe
- Organization-level reports
- Maintainer analytics that preserve privacy

## Feedback

Roadmap priorities should come from real maintainer workflows. Useful feedback
includes noisy report sections, missing scanner formats, policy rules that would
save review time, and examples of decisions maintainers still want to make
manually.

- Share feedback in GitHub Discussions:
  https://github.com/xxxquide/MaintainerGuard/discussions
- Pick up small scoped work:
  https://github.com/xxxquide/MaintainerGuard/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22good%20first%20issue%22

Roadmap items are intentions, not commitments or claims of current behavior.
