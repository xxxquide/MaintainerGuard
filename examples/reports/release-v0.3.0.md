# MaintainerGuard Release Readiness Report

**Version:** 0.3.0

**Release verdict:** Looks ready for release review

**Overall risk:** Low

## Executive summary

Release 0.3.0 contains 3 merged change(s), 0 security-sensitive change(s), and 0 dependency change(s).

## Notable changes

- Group duplicate SARIF scanner findings
- Add real-world scanner fixture coverage
- Document v0.2 upgrade notes and scanner matrix

## Breaking changes

- None detected.

## Security-sensitive changes

- None detected.

## Dependency changes

- None detected.

## Scanner findings

- Low - release-scan: Documentation-only release validation note

## Documentation status

Documentation changes detected.

## Test status

Test changes detected.

## Unresolved high-risk items

- None supplied or detected.

## Suggested release checklist

- Confirm the full test suite passes.
- Review and finalize release notes.

## Generated release notes draft

- Add scanner fixture coverage matrix and real-world scanner examples.
- Group duplicate SARIF findings while preserving path and line evidence.
- Use SARIF rule metadata as fallback for sparse scanner results.
- Keep Trivy vulnerability support covered by regression tests.
- Add v0.2.x to v0.3.0 upgrade notes.

## Evidence

| ID | Claim | Evidence | Confidence |
|---|---|---|---|
| `ev-66c40e63a757` | Merged change: Group duplicate SARIF scanner findings | release_pr: 201; maintainerguard/scanners.py, tests/test_scanners.py | High |
| `ev-37668917c7ce` | Merged change: Add real-world scanner fixture coverage | release_pr: 202; examples/sample-data/scanners/codeql-like.sarif.json, examples/sample-data/scanners/semgrep-like.json, docs/scanner-inputs.md | High |
| `ev-c58448de961a` | Merged change: Document v0.2 upgrade notes and scanner matrix | release_pr: 203; docs/upgrading-to-v0.3.md, examples/README.md, CHANGELOG.md | High |
| `ev-b68cd96cde18` | release-scan reported REL-030 | scanner_finding: REL-030; release-scan reported a generic finding: Documentation-only release validation note. Review the supplied scanner evidence before merge. Scanner detail: Review generated examples and upgrade notes before publishing. | High |

## Limitations

- Release readiness is based only on supplied merged changes, scanner summaries, and metadata.
- This report does not replace release-manager review.
