# Scanner input formats

MaintainerGuard consumes scanner output; it does not replace scanners or
independently confirm their findings.

## Supported formats and fixtures

MaintainerGuard supports a small set of normalized scanner shapes. The table
below is intentionally conservative: it describes what is covered by fixtures
and tests, not a promise that every vendor-specific variant is fully supported.

| Fixture | Tool family | Support level | Preserved evidence |
|---|---|---|---|
| `static-analysis.sarif.json` | SARIF/code scanning | Native SARIF adapter | tool name, rule ID, severity, message, `path:line` |
| `codeql-like.sarif.json` | CodeQL-like SARIF | Native SARIF adapter | rule default severity, security tags, `path:line` |
| `dependency-advisory.json` | Generic dependency advisory | Generic JSON | advisory ID, dependency, affected files, blocking flag |
| `dependabot-advisory.json` | Dependabot-like advisory | Generic JSON | GHSA-style ID, dependency, lockfile evidence |
| `trivy-vulnerability.json` | Trivy vulnerability output | Native Trivy vulnerability adapter | target, package version, advisory ID, fixed version |
| `trivy-misconfiguration.json` | Trivy config-style warning | Generic JSON | workflow path, category, maintainer recommendation |
| `secret-scan.json` | Generic secret scanner | Simple result-array adapter | affected file, severity, blocking flag |
| `gitleaks-like.json` | Gitleaks-like result | Simple result-array adapter | affected file, secret category, blocking flag |
| `semgrep-like.json` | Semgrep-like static analysis | Generic JSON | rule ID, affected path, static-analysis category |
| `supply-chain-workflow.json` | Workflow/supply-chain policy | Generic JSON | workflow path, supply-chain category |
| `mixed-severity.json` | Mixed generic findings | Generic JSON | normalized severities and categories |
| `container-trivy-warning.json` | Container/supply-chain warning | Generic JSON | image/build target and recommendation |

Supported input families:

- MaintainerGuard generic JSON from `schemas/scanner.schema.json`
- SARIF result files with tool name, rule ID, level, message, rule metadata,
  and locations
- OSV-style results containing packages and vulnerabilities
- Trivy vulnerability results with targets, package versions, advisory IDs, and
  fixed versions
- Simple secret-scanner result arrays
- Semgrep-like static-analysis findings through generic JSON
- Workflow or supply-chain policy warnings through generic JSON

Normalized findings include tool name, category, severity, title, description,
affected files, affected dependency, advisory ID, recommendation, blocking flag,
and evidence references after PR analysis attaches them.

Normalize a sample:

```bash
python3 -m maintainerguard parse-scanner examples/sample-data/scanners/static-analysis.sarif.json
```

List the fixture-backed scanner families:

```bash
mg scanners
```

Run a local smoke check across every bundled scanner fixture:

```bash
mg verify
```

Normalize a sanitized Trivy vulnerability result:

```bash
python3 -m maintainerguard parse-scanner examples/sample-data/scanners/trivy-vulnerability.json
```

Attach scanner evidence to PR analysis:

```bash
python3 -m maintainerguard analyze-pr examples/sample-data/prs/dependency-update.json \
  --scanner examples/sample-data/scanners/dependency-advisory.json
```

Try a sanitized Trivy-like container warning:

```bash
python3 -m maintainerguard parse-scanner examples/sample-data/scanners/container-trivy-warning.json
```

The explainer groups duplicate scanner IDs, normalizes severity, identifies
affected files or dependencies, and suggests maintainer review. It never turns a
scanner warning into a confirmed vulnerability claim.

For SARIF input, duplicate results with the same tool, rule, title, severity,
and category are grouped into one MaintainerGuard finding with unique affected
locations. This keeps reports readable while preserving `path:line` evidence
when SARIF supplies `region.startLine`; path-only evidence is kept when no line
is present.

## Generic JSON example

```json
{
  "scanner": "workflow-policy",
  "findings": [
    {
      "id": "WF-1",
      "category": "supply-chain",
      "severity": "high",
      "title": "Release workflow gained write permissions",
      "affected_files": [".github/workflows/release.yml"],
      "recommendation": "Confirm the permissions are necessary and scoped."
    }
  ]
}
```

## Mapping scanner output into generic JSON

Use the generic format when MaintainerGuard does not yet have a dedicated
adapter for a scanner. Keep examples sanitized: use placeholder image names,
repository paths, package versions, and advisory IDs instead of real private
scanner output.

For a Trivy-like container or supply-chain warning, map scanner fields like this:

- Scanner name -> `scanner`, for example `trivy-container`.
- Vulnerability or rule ID -> finding `id`.
- Scanner severity -> finding `severity`; MaintainerGuard normalizes common
  values such as `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL`.
- Target image, manifest, lockfile, or Dockerfile -> `affected_files`.
- Package name and installed version -> `dependency`.
- CVE or vendor advisory -> `advisory_id`.
- Fixed version or remediation note -> `recommendation`.

MaintainerGuard explains and groups the supplied scanner evidence for maintainer
review. It does not replace the scanner, rescan the image, or confirm that a
reported vulnerability is exploitable.
