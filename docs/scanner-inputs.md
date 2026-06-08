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
