# Changelog

All notable changes to MaintainerGuard are documented here.

## [Unreleased]

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

## [0.1.0] - 2026-06-04

- Initial open-source MVP implementation.
