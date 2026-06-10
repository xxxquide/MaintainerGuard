# MaintainerGuard Merge Readiness Report

**Verdict:** Blocked by scanner finding

**Overall risk:** Critical

**Confidence:** High

## Executive summary

"Update HTTP dependency" affects Dependencies. Verdict: Blocked by scanner finding. Overall risk: Critical. dependency-check reported Critical advisory reported for example-http.

## Key changes

- Dependencies

## Why this requires review

- dependency-check reported Critical advisory reported for example-http.
- Dependency or supply-chain-sensitive files changed.

## Decision guidance

**Recommended maintainer action:** Block until scanner finding is resolved

**Reason:** A maintainer should act on this recommendation because scanner evidence includes critical dependency-check finding ADV-2026-001.

## Security-sensitive areas

- None detected.

## Scanner findings

- Critical - dependency-check (dependency) - Critical advisory reported for example-http: dependency-check reported a dependency finding: Critical advisory reported for example-http. Review the supplied scanner evidence before merge. Scanner detail: The supplied scanner associates example-http 1.2.3 with ADV-2026-001. Recommendation: Review reachability, available patched versions, and whether the dependency change is required.

## Dependency and supply-chain impact

**Medium:** Dependency or supply-chain-sensitive files changed.

- Upgraded example-http from 1.1.0 to 1.2.3.

## Test impact

**None:** No behavior change requiring additional test review was detected.

## Documentation impact

**None:** No documentation drift signal was detected.

## Release impact

**None:** No release-impact signal was detected.

## Possible breaking changes

- None detected.

## Policy checks

- Passed - Dependency changes should include scanner results: Run or attach dependency scanner results for changed package inputs.

## Maintainer checklist

- Review dependency-check finding ADV-2026-001 before merge.
- Review dependency provenance, version changes, and scanner findings.

## Evidence

| ID | Claim | Evidence | Confidence |
|---|---|---|---|
| `ev-4712b5996df1` | requirements.txt changed | changed_file: requirements.txt; modified file; supplied patch length 41 characters | High |
| `ev-8bb20639473e` | requirements.lock changed | changed_file: requirements.lock; modified file; supplied patch length 41 characters | High |
| `ev-adbaf6476e2d` | dependency-check reported ADV-2026-001 | scanner_finding: ADV-2026-001; dependency-check reported a dependency finding: Critical advisory reported for example-http. Review the supplied scanner evidence before merge. Scanner detail: The supplied scanner associates example-http 1.2.3 with ADV-2026-001. | High |

## Limitations

- MaintainerGuard identifies review signals; it does not prove the presence or absence of vulnerabilities.
- Absence-based test and documentation signals are inferred from supplied changed-file data.
- This report supports, but does not replace, human maintainer review.
