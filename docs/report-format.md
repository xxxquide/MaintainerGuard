# Report format reference

MaintainerGuard emits Markdown by default because the primary output is intended
for maintainer review and GitHub comments. Pass `--format json` for structured
output.

## Merge-readiness report

The report contains verdict, risk, confidence, executive summary, changed areas,
review reasons, security-sensitive areas, scanner findings, dependency impact,
test impact, documentation impact, release impact, policy checks, decision
guidance, checklist, evidence, and limitations.

Verdict priority is:

1. Not enough information
2. Blocked by scanner finding
3. Changes requested by blocking policy
4. Tests required
5. Security review recommended
6. Documentation update recommended
7. Review required
8. Ready for maintainer review

Important deterministic reasons and checklist items reference evidence IDs.
Optional AI claims appear separately and are retained only when all referenced
evidence IDs exist.

## Issue and release reports

Issue reports include classification, labels, missing information, next action,
and a response draft. Possible private security reports are routed toward
responsible disclosure handling instead of public technical expansion.

Release reports include a release verdict, risk, executive summary, notable
changes, breaking changes, security-sensitive changes, dependency changes, docs
readiness, tests readiness, scanner findings, unresolved high-risk items,
release notes draft, release checklist, evidence, and limitations.

The versioned output shape is summarized by `schemas/report.schema.json`.

## Section order and truncation

Decision guidance, the maintainer checklist, the evidence table, and limitations
render before the detail sections. A published GitHub comment is capped at
`github.max_comment_characters` (30000 by default), and these are the parts a
maintainer cannot afford to lose to truncation. A truncated comment ends with an
explicit notice rather than stopping mid-sentence.

Optional AI enrichment renders last, after the deterministic sections it is meant
to be checked against.

## Pre-existing repository findings

Scanner findings that point at files the change does not touch appear under
`Pre-existing repository findings` with the reason they were separated. They do
not affect the verdict, risk level, reasons, or checklist. Concise mode previews
the first 10; set `report_mode = "detailed"` for the full list.

Each finding in the JSON output carries `in_changed_scope` and `scope_reason`.
