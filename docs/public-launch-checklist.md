# Public launch checklist

Use this checklist before public promotion, launch posts, or outreach to
maintainer communities.

## Repository metadata

- Confirm the repository description is specific and honest.
- Confirm the website points to the GitHub Marketplace Action.
- Confirm repository topics are relevant.
- Confirm the repository is public.

Recommended About settings:

- Description: `Evidence-first AI maintainer assistant for merge, security, issue, and release readiness.`
- Website: `https://github.com/marketplace/actions/maintainerguard`
- Topics: `github-actions`, `maintainers`, `code-review`, `security`, `supply-chain-security`, `open-source`, `developer-tools`, `release-automation`

## README quality

- Confirm the first screen explains what MaintainerGuard is.
- Confirm badges render and link to real project resources.
- Confirm the recommended Action usage is `xxxquide/MaintainerGuard@v0.1.3`.
- Confirm Quick Start commands work.
- Confirm README links to sample reports, Marketplace, Security policy, and contributing docs.
- Confirm limitations are visible and honest.

## Marketplace listing

- Confirm the Marketplace page renders the Action name, icon, color, and description.
- Confirm the latest version is `v0.1.3`.
- Confirm the usage snippet points to the expected version.
- Confirm README rendering looks clean on Marketplace.

## Release and tag

- Confirm `v0.1.3` exists and points to the intended Action metadata release.
- Do not move public tags unless there is an explicit, documented reason.
- Use patch releases for public tag corrections.

## External Action test

- Run or review an external repository workflow using:

  ```yaml
  uses: xxxquide/MaintainerGuard@v0.1.3
  ```

- Confirm dry-run output works without comments.
- Confirm optional comment publishing updates one marked comment only when explicitly enabled.

## Roadmap and issues

- Create roadmap issues for future policy presets, scanner adapters, SARIF improvements, and sample reports.
- Create feedback issues asking maintainers what checks and scanner integrations matter.
- Avoid duplicate issues.

## Security settings

Review these repository settings manually when available:

- Enable Dependabot alerts.
- Enable secret scanning if available.
- Enable push protection if available.
- Enable private vulnerability reporting if available.
- Review branch protection rules.
- Keep `SECURITY.md` up to date.

Do not claim these settings are enabled unless verified in GitHub.

## No fake claims

- Do not claim fake users, sponsors, testimonials, stars, benchmarks, or adoption.
- Do not claim MaintainerGuard guarantees secure code.
- Do not claim MaintainerGuard finds every vulnerability.
- Do not claim MaintainerGuard replaces human review.

## Repository hygiene

- Confirm no `__pycache__`, `*.pyc`, `.DS_Store`, `__MACOSX`, build output, wheels, archives, or local virtual environments are tracked.
- Confirm no `.env` or real secrets are committed.
- Confirm sample data uses fake placeholder values only.

## Promotion assets

- Confirm launch copy is ready in `docs/launch.md`.
- Confirm screenshots or images are committed intentionally.
- Confirm no generated junk is included with image assets.

## Post-launch monitoring

- Watch GitHub Actions for failures.
- Watch issues for maintainer feedback.
- Fix documentation confusion quickly.
- Track noisy report patterns as policy/scanner roadmap issues.
- Keep launch claims modest and evidence-based.
