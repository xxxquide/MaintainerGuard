# Public release checklist

Run this checklist before publishing MaintainerGuard publicly or cutting a
release.

## Verification

- Run `python3 -m unittest discover -s tests -v`.
- Run `python3 -m compileall -q maintainerguard`.
- Run `python3 -m pip wheel . --no-deps`.
- Run `python3 -m maintainerguard validate-config`.
- Run `python3 -m maintainerguard demo --scenario high-risk-auth`.
- Run a scanner-backed PR report.
- Run issue and release sample reports.

## Repository hygiene

- Confirm there are no `__pycache__` directories.
- Confirm there are no `*.pyc` files.
- Confirm there is no `.DS_Store`.
- Confirm there is no `__MACOSX`, `node_modules`, `dist`, `build`, coverage, or cache output.
- Confirm `.env` is absent and `.env.example` contains no real values.

## Safety and claims

- Search docs and code for fake adoption, fake stars, fake sponsors, testimonials, or benchmarks.
- Search docs and code for security overclaims such as guaranteed security or finding every vulnerability.
- Confirm README says MaintainerGuard does not replace human review.
- Confirm scanner docs explain that MaintainerGuard summarizes supplied scanner output.
- Confirm GitHub workflows use least-privilege permissions.
- Confirm comment publishing requires explicit dry-run and post-comment changes.

## Examples and docs

- Regenerate sample reports after report renderer changes.
- Verify README commands match actual CLI commands.
- Validate `.maintainerguard.toml`.
- Confirm Action examples use safe defaults.
- Confirm public release notes describe real implemented behavior only.
