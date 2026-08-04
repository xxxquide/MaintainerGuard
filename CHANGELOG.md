# Changelog

All notable changes to Veracity are documented here.

## [Unreleased]

## [0.4.0] - 2026-08-05

### Renamed

The project was renamed from MaintainerGuard to Veracity. This is a breaking
change: the distribution, the commands and the configuration file all change name.
See [docs/upgrading-to-v0.4.md](docs/upgrading-to-v0.4.md) for the migration.

The old identity described things the software did not do. "Guard" promised
protection that the tool's own disclaimer denies — it does not find vulnerabilities
and does not prove code is secure. And the headline read "Evidence-first AI
maintainer assistant" while the language model was off by default and could not
affect any verdict.

- Distribution and import package: `maintainerguard` becomes `veracity`.
- Commands: `maintainerguard` becomes `veracity`, and `mg` becomes `vera`.
- Configuration file: `.maintainerguard.toml` becomes `.veracity.toml`. If the old
  file is present and the new one is not, loading now fails with an error naming
  both, rather than silently using defaults.
- Pull-request comment marker: `<!-- veracity:merge-readiness -->`. The first run
  after upgrading will not recognise a comment left by an older version.
- Skip label `skip-maintainerguard` becomes `skip-veracity`.
- Environment variable `MG_REPORT_LENGTH` becomes `VERACITY_REPORT_LENGTH`.
- Workflow files under `.github/workflows/` are renamed accordingly.
- GitHub Action `branding.icon` changes from `shield` to `filter`.
- Description everywhere becomes "Evidence-backed review verdicts from
  multi-scanner output, scoped to the change under review."
- README rewritten: verified-scanner table with the exact binary versions, the
  attribution rule stated explicitly, and a comparison section naming what
  reviewdog, GitHub code scanning, sarif-tools, DefectDojo and LLM reviewers do
  better.
- `docs/roadmap.md` replaced. The previous version planned nine releases through
  v2.0 on top of a core that had never been checked against real scanner output.
- New hero asset as SVG (8 KB). `assets/demo.gif` and the old PNG banner were
  removed: they carried the old name and stale command output, and together weighed
  about 16 MB. The repository now has no binary assets.
- `tests/test_branding.py` fails if the old brand or the old command name reappears
  outside the changelog, the upgrade guide and the configuration migration error.

### Fixed

Verified against real scanner binaries (Trivy 0.73.0, Gitleaks 8.30.1,
osv-scanner 2.4.0, Semgrep OSS) rather than hand-written fixtures.

- Trivy native JSON now reads `Secrets`, `Misconfigurations`, and `Licenses` in
  addition to `Vulnerabilities`. A real `trivy fs` report of 65 findings
  normalized to 61; the four dropped findings included a CRITICAL leaked GitHub
  Personal Access Token and a HIGH Dockerfile misconfiguration.
- `gitleaks --report-format json` writes a top-level JSON array and previously
  raised `ValueError: Scanner input must be a JSON object`. Arrays are now a
  first-class scanner input, in the normalizer and in the CLI.
- Real `semgrep --json` output was routed to the secret-scanner adapter, because
  that branch matched any `{"results": [...]}` payload. Every SAST finding became
  a High, blocking "Possible secret reported by scanner" and the report verdict
  became `Blocked by scanner finding`. Semgrep native output now has its own
  adapter that preserves `check_id`, severity, CWE metadata, and autofix hints.
- Scanner findings are no longer marked blocking unless the input says so. The
  secret-result adapter defaulted `blocking` to `True`.
- Format detection is now explicit and positive. An unrecognised payload raises
  `UnsupportedScannerInput` instead of normalizing to an empty list, which was
  indistinguishable from a clean scan.
- SARIF results carrying an accepted `suppressions` entry or a
  `baselineState` of `unchanged`/`absent` are excluded. Maintainer-dismissed and
  pre-existing findings previously reappeared as active evidence.
- SARIF severity now honours CodeQL's `security-severity` score using GitHub's
  documented bands (>= 9.0 Critical, >= 7.0 High, >= 4.0 Medium). A 9.8 finding
  was reported as High. The flat `problem.severity` key that real CodeQL emits is
  also read, alongside the previously supported nested form.
- `partialFingerprints` and CWE tags are preserved on normalized findings.

Second pass over the defects recorded during the scanner-fidelity audit. Each
one has a regression test in `tests/test_audit_followups.py` that fails without
the fix.

- A security-sensitive file dropped by `privacy.max_files_analyzed` left the
  report claiming `confidence: High` with verdict `Ready for maintainer review`.
  Confidence is now capped at Medium when the cap drops files, and the executive
  summary states how many files went unanalyzed instead of leaving it to a
  limitations footnote. Paths excluded by `paths.ignore` are a deliberate choice
  and do not lower confidence.
- The optional AI `summary` and claim texts were stored verbatim. A crafted or
  prompt-injected response could embed the published-comment marker
  (`<!-- veracity:merge-readiness -->`), which is how comments are
  deduplicated, and could open a second `## Evidence` heading beside the
  deterministic one. AI text is now sanitized in `safe_enrich_report` as well as
  in `validate_ai_enrichment`: HTML comments and comment fragments are removed,
  Markdown headings are flattened, control characters are stripped, and the
  summary and each claim are length-bounded. The rendered block is quoted so
  model output is visually attributable.
- The system instruction now states that the pull-request title, body, and patch
  are untrusted contributor-controlled data to be described rather than obeyed,
  and asks for plain prose with no markup.
- Security categorization matched keywords as substrings. `terraform/main.tf` was
  reported as a rendering change because `orm` occurs inside `terraform`,
  `src/formatters.py` for the same reason, and `src/authors.py` as an
  authentication change because `auth` occurs inside `author`. Keywords are now
  matched as whole words against separator-normalized text, with plural forms
  allowed. Keywords that are themselves path fragments (`.github/workflows`,
  `package.json`, `api_key`) keep substring semantics. The same fix applies to
  `changed_areas`, the documentation-impact terms, and the behavior hints.
- Test and documentation paths are no longer reported as security-sensitive
  changes. `tests/fixtures/auth_token.json` was categorized as authentication and
  `docs/security/threat-model.md` matched the default `**/security/**` pattern.
  Documentation and test classification now takes precedence over
  `paths.security_sensitive`; a maintainer who wants otherwise removes the path
  from `paths.docs` or `paths.tests`.
- Breaking-change detection searched whole patches for words like `remove` and
  `deprecated`, so a diff whose only content was `# remove trailing whitespace`
  was reported as a breaking change and escalated release impact to High. It now
  requires a structural signal: a removed declaration, a deleted or renamed file,
  or an explicit breaking-change marker. Findings say which signal fired.
- File `status` was never read. A change that only deleted `src/auth/session.py`
  demanded new tests for code that no longer exists, and a pure rename with no
  diff content was treated as a behavior change. Deletions and content-free
  renames no longer count as behavior needing test coverage.
- `[[policy]]` validated only that `name`, `paths`, and `require` were present.
  `blocking = "yes"` is truthy, so a soft policy silently became one that
  escalates risk to Critical. `blocking` must now be a boolean, and `name`,
  `require`, and `message` must be strings.

### Added

- Scanner findings are attributed to the change under review. `ScannerFinding`
  gains `in_changed_scope` and `scope_reason`, and only in-scope findings affect
  the verdict, risk level, reasons, and checklist. A finding with no reported
  path stays in scope, so nothing is silently dismissed.
- A `Pre-existing repository findings` report section lists findings that point
  at untouched files, with the reason they were separated.
- `tests/test_real_scanner_fidelity.py` plus byte-for-byte real scanner output
  under `tests/fixtures/real-scanners/` and a `regenerate.sh` to refresh them.

### Changed

- Report section order now puts decision guidance, the maintainer checklist, the
  evidence table, and limitations first. A published comment truncated at
  `github.max_comment_characters` dropped 41% of a real report, and the
  `## Evidence` section was the first thing lost because it rendered last.
- Truncated comments end with an explicit notice instead of stopping mid-word.
- Optional AI enrichment renders after the deterministic sections.
- Concise mode previews the first 10 pre-existing findings; set
  `report_mode = "detailed"` for the full list.

- The build backend is now hatchling instead of the hand-written standard-library
  PEP 517 backend, which generated `METADATA` by hand and had drifted from
  `[project]`: keywords and classifiers disagreed, `Author` was never emitted,
  and `readme` was dropped, leaving an empty long description on PyPI. Metadata
  now comes from `[project]`. hatchling is a build-time dependency only;
  Veracity still has no third-party runtime dependencies.
- `veracity/__init__.py` is the single source for the version.
  `[project]` declares `dynamic = ["version"]`, so the duplicate that caused the
  drift is gone.
- `assets/` is excluded from the sdist, which drops it from 15.9 MB to about
  150 KB. The demo GIF and banner are not needed to install or run the package.
  A stray `.coverage` file is no longer packaged.
- `[project.urls]` now publishes homepage, source, changelog, and issue links.

### Behaviour change

A repository-wide scanner report no longer inflates an unrelated change. A
documentation-only pull request supplied with a real `trivy fs` report of the
whole repository previously produced `Review required`, risk `High`, a 61-item
checklist, and a 50,639-character report. It now produces `Ready for maintainer
review`, risk `Low`, no scanner checklist items, and lists the 65 findings as
pre-existing. Findings inside changed files, and findings without a reported
path, keep their previous weight.

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
