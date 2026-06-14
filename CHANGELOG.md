# Changelog

All notable changes to MaintainerGuard are documented here.

## [Unreleased]

## [0.3.1] - 2026-06-14

### Added

- Added `mg scanners` to list scanner input families covered by bundled fixtures.
- Added scanner fixture normalization to `mg verify` so local smoke checks cover the documented scanner matrix.

### Changed

- Synced generated GitHub Action workflow examples and public Action references to `v0.3.1`.
- Clarified CLI and scanner docs around fixture-backed scanner support without expanding security claims.

## [0.3.0] - 2026-06-13

### Added

- Added a scanner fixture coverage matrix documenting supported scanner shapes and support levels.
- Added sanitized CodeQL-like, Semgrep-like, Gitleaks-like, Dependabot-like, and Trivy configuration scanner fixtures.
- Added v0.2.x to v0.3.0 upgrade notes.

### Changed

- Grouped duplicate SARIF findings with the same scanner, rule, title, severity, and category while preserving unique affected locations.
- Expanded SARIF severity/category normalization using rule metadata when result-level fields are sparse.
- Synced package metadata, GitHub Action examples, workflows, CLI defaults, and release samples to `v0.3.0`.
- Kept Trivy vulnerability support covered while adding scanner-depth fixtures and tests.

## [0.2.0] - 2026-06-10

### Added

- Added policy presets for `minimal`, `security`, `strict`, and `docs` repository profiles.
- Added `mg presets` and `mg init --preset minimal|security|strict|docs`.
- Added SARIF line evidence by preserving `startLine` as `path:line` while keeping path-only fallback.
- Added SARIF rule metadata fallback for sparse results, including rule default severity and description text.

### Changed

- Kept Trivy vulnerability normalization from v0.1.4 while integrating SARIF scanner improvements.
- Documented policy preset behavior and custom `[[policy]]` override semantics.
- Expanded scanner, CLI, config, and smoke-test coverage for the v0.2.0 integration.

## [0.1.4] - 2026-06-09

### Changed

- Synced public GitHub Action examples, generated workflow templates, and package metadata to `v0.1.4`.
- Updated repository workflow examples to current official `actions/checkout@v6` and `actions/setup-python@v6` major versions.
- Expanded CI smoke checks with `./mg verify`, secret-finding demo, JSON demo output, and PR analysis with scanner input.
- Added documentation and examples indexes for easier project navigation.

## [0.1.3] - 2026-06-09

### Changed

- Synced public GitHub Action examples, generated workflow templates, and package metadata to `v0.1.3`.
- Kept local `uses: ./` examples limited to clearly labeled local-development notes.

## [0.1.2] - 2026-06-08

### Changed

- Cleaned up README presentation for Marketplace rendering.
- Moved the README hero image to `assets/maintainerguard-hero.png`.
- Published a documentation-only Marketplace polish release without behavior changes.

## [0.1.1] - 2026-06-08

### Fixed

- Added top-level GitHub Action `branding` metadata for Marketplace readiness.
- Updated reusable Action snippets to reference `xxxquide/MaintainerGuard@v0.1.1`.

## [0.1.0] - 2026-06-08

### Added

- Composite GitHub Action metadata and Action entrypoint with safe dry-run defaults
- Decision guidance in merge-readiness reports and release verdicts in release reports
- Richer scanner normalization fields: category, recommendation, advisory ID, and affected dependency
- Supply-chain-sensitive detection for workflows, Dockerfiles, release/build scripts, provenance, and SBOM files
- Safer issue triage categories for security, regression, and dependency reports
- Public release checklist, architecture docs, issue templates, and PR template
- Bundled sample data and schemas in built wheels so installed demos work
- Deterministic evidence-first PR analysis and Markdown/JSON reports
- Security-sensitive, dependency, test, documentation, and release detectors
- Scanner normalization for generic JSON, SARIF, OSV-style, and secret outputs
- Configurable policies, noise filtering, and risk/verdict rules
- Optional validated AI enrichment with deterministic fallback
- Guarded GitHub one-comment automation helpers
- Issue triage, release readiness, schemas, samples, workflows, and documentation
