# Development guide

Veracity uses Python 3.11+ and the standard library. The package is split
by responsibility: configuration, typed models, evidence, detectors, scanners,
policies, risk analysis, noise filtering, reports, privacy, AI, GitHub,
issue/release analysis, and CLI.

## Checks

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q veracity
python3 -m veracity validate-config
python3 -m veracity demo --scenario high-risk-auth
./mg verify
python3 -m pip wheel . --no-deps
```

Tests use sample data and mocks; they must not require network access, API keys,
or a real GitHub repository.

After `python3 -m pip install -e .`, both `veracity` and `vera` point to
the same CLI entrypoint. The local `./mg` wrapper is available for source-tree
smoke checks before installation.

## Design rules

- Deterministic analysis remains useful when AI is off.
- Every important claim references known evidence.
- Absence-based findings use cautious language and no more than Medium confidence.
- Critical risk requires explicit critical scanner evidence or blocking policy.
- External services remain isolated and mockable.
- Documentation and examples must match executable behavior.

Add new scanner formats by normalizing them into `ScannerFinding`. Include
category, description, affected dependency or files, advisory ID, recommendation,
and blocking behavior when available. Add fixtures under
`examples/sample-data/scanners/` and tests in `tests/test_scanners.py`.

Add new detectors as pure functions before connecting them to the analysis
engine. New report sections should be backed by model fields or evidence-backed
derived values.

## Action development

`action.yml` delegates to `python3 -m veracity action-run`. Keep Action
inputs mapped through environment variables in one place and preserve safe
defaults: dry-run on, no comment publishing, update existing comments, no AI
unless explicitly enabled, and no secrets required for local demos.

The Action must remain portable when used as `uses: xxxquide/veracity@tag`.
Keep `$GITHUB_ACTION_PATH` on `PYTHONPATH` and do not `cd` into the Action
directory; config, scanner, and event paths should resolve from the caller
workspace.

## Packaging

The package is built with [hatchling](https://hatch.pypa.io/latest/), declared in
`[build-system]`. It is a build-time dependency only: Veracity still has
no third-party runtime dependencies.

Earlier versions used a hand-written standard-library PEP 517 backend. It
generated `METADATA` by hand and had already drifted from `[project]`: keywords
and classifiers disagreed, `Author` was never emitted, and `readme` was dropped
entirely, which left an empty long description on PyPI.

Two things to know when changing packaging:

- **Version.** `veracity/__init__.py` is the single source. `[project]`
  declares `dynamic = ["version"]` and `[tool.hatch.version]` reads it from
  there, so the two cannot drift.
- **Bundled data.** The CLI resolves `examples/sample-data`, `schemas`,
  `action.yml`, and `.veracity.toml` relative to the directory containing
  the installed package, so the wheel keeps them at the top level via
  `[tool.hatch.build.targets.wheel.force-include]`. If you move them, update
  `_package_root()` in `veracity/cli.py` in the same change.

`assets/` is excluded from the sdist: the demo GIF and banner total about 16 MB,
are not needed to install or run the package, and PyPI renders the readme from
metadata rather than from the archive.

Verify a build locally with:

```bash
python3 -m pip wheel . --no-deps
python3 -m unittest tests.test_packaging -v
```
