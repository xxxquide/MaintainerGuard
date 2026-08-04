# Public release checklist

Run this checklist before publishing Veracity publicly or cutting a
release.

## Verification

- Run `python3 -m unittest discover -s tests -v`.
- Run `python3 -m compileall -q veracity`.
- Run `python3 -m pip wheel . --no-deps`.
- Run `python3 -m veracity validate-config`.
- Run `python3 -m veracity demo --scenario high-risk-auth`.
- Run a scanner-backed PR report.
- Run issue and release sample reports.
- Run `python3 -m unittest tests.test_real_scanner_fidelity` and confirm every
  scanner named in the README still parses without loss.
- Run `python3 -m unittest tests.test_branding` and confirm no stale brand or
  command name reappeared.
- Confirm every scanner version claimed in the README matches the fixtures in
  `tests/fixtures/real-scanners/`; regenerate them if a scanner released a new
  major version.
- Confirm no public claim exceeds what a test asserts.

## Repository hygiene

- Confirm there are no `__pycache__` directories.
- Confirm there are no `*.pyc` files.
- Confirm there is no `.DS_Store`.
- Confirm there is no `__MACOSX`, `node_modules`, `dist`, `build`, coverage, or cache output.
- Confirm `.env` is absent and `.env.example` contains no real values.

## Safety and claims

- Search docs and code for fake adoption, fake stars, fake sponsors, testimonials, or benchmarks.
- Search docs and code for security overclaims such as guaranteed security or finding every vulnerability.
- Confirm README says Veracity does not replace human review.
- Confirm scanner docs explain that Veracity summarizes supplied scanner output.
- Confirm GitHub workflows use least-privilege permissions.
- Confirm comment publishing requires explicit dry-run and post-comment changes.

## Examples and docs

- Regenerate sample reports after report renderer changes.
- Verify README commands match actual CLI commands.
- Validate `.veracity.toml`.
- Confirm Action examples use safe defaults.
- Confirm public release notes describe real implemented behavior only.
