# Architecture

MaintainerGuard is intentionally a small local-first Python CLI and library. It
does not require a backend, database, dashboard, or runtime dependency.

## Modules

- `config.py`: strict TOML loading, defaults, validation, policy config
- `models.py`: typed report, evidence, scanner, policy, and GitHub models
- `evidence.py`: stable evidence ID generation
- `detectors.py`: deterministic changed-file, security, docs, tests, release, and supply-chain detectors
- `scanners.py`: scanner adapters that normalize external scanner outputs
- `policies.py`: repository-specific policy checks
- `analysis.py`: merge-readiness orchestration, risk, verdict, decision guidance
- `reports.py`: Markdown and JSON rendering
- `github.py`: event parsing, bounded GitHub API access, one-comment strategy
- `issue.py`: issue triage heuristics
- `release.py`: release-readiness aggregation
- `privacy.py`: redaction helpers used before optional AI calls
- `ai.py` and `prompts.py`: optional OpenAI enrichment and structured validation
- `cli.py`: local runner, GitHub event runner, and Action entrypoint

## Data flow

1. CLI or Action input loads config and sample/GitHub/scanner data.
2. Scanner inputs are normalized into `ScannerFinding`.
3. Changed files become evidence records.
4. Detectors produce security, dependency, test, docs, and release impacts.
5. Policies evaluate against changed paths and impact results.
6. The analysis engine selects risk, verdict, checklist, and decision guidance.
7. Optional AI may add wording only after evidence validation.
8. Reports render as Markdown or JSON.
9. GitHub publishing, if enabled, updates one marked comment.

## Adding scanner adapters

Add parsing logic in `scanners.py` and normalize to `ScannerFinding`. Preserve
these fields when possible:

- tool name;
- category;
- severity;
- title and description;
- affected files or dependency;
- advisory ID;
- recommendation;
- blocking flag.

Adapters should summarize supplied scanner output. They must not claim a
scanner warning is a confirmed vulnerability.

## Adding policy rules

Use config-only policy rules first. Supported requirements are `tests`, `docs`,
`scanner`, and `manual_review`. Keep path globs narrow and messages actionable.

If a new policy requirement is needed, add it in `policies.py`, validate it in
`config.py`, document it in `docs/maintainer-policies.md`, and add tests.

## Adding report sections

Report sections should come from deterministic model fields or evidence-backed
derived values. Avoid adding prose that makes unsupported claims. If a section
introduces a new major claim, ensure the model or evidence table can explain it.
