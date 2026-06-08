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
