# Scanner input formats

MaintainerGuard consumes scanner output; it does not replace scanners or
independently confirm their findings.

## Supported MVP formats

- MaintainerGuard generic JSON from `schemas/scanner.schema.json`
- SARIF result files with tool name, rule ID, level, message, and locations
- OSV-style results containing packages and vulnerabilities
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
