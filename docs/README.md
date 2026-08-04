# Veracity Documentation

Use this page as a map for Veracity's user and contributor docs.

## Start here

- [Getting started](getting-started.md) - quickest path from install to useful reports.
- [CLI guide](cli.md) - `vera demo`, `vera init`, `vera doctor`, `vera verify`, and analysis commands.
- [GitHub automation](github-automation.md) - safe GitHub Action usage and comment publishing.
- [Configuration](configuration.md) - `.veracity.toml` options and validation.

## Reports and evidence

- [Report format](report-format.md) - report sections, evidence tables, and limitations.
- [Maintainer policies](maintainer-policies.md) - repository-specific review rules.
- [Scanner inputs](scanner-inputs.md) - which scanner output is verified against which binary version, and what SARIF fields change the outcome.
- [Privacy and security](privacy-and-security.md) - safety model, AI boundaries, and redaction.
- [Upgrading to v0.4](upgrading-to-v0.4.md) - the rename, and the behaviour changes that can move a verdict.
- [Upgrading to v0.3.0](upgrading-to-v0.3.md) - scanner-focused upgrade notes from `v0.2.x`.

## Project internals

- [Architecture](architecture.md) - module boundaries and extension points.
- [Development](development.md) - local checks and contribution workflow.
- [Roadmap](roadmap.md) - what shipped, the known defects that are next, and what is deliberately not planned.

## Release and launch checklists

- [Public release checklist](public-release-checklist.md)
- [Public launch checklist](public-launch-checklist.md)
- [Launch materials](launch.md)

Veracity is evidence-first and human-in-the-loop. It does not guarantee
secure code, find every vulnerability, or replace maintainer review.
