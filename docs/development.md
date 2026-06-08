# Development guide

MaintainerGuard uses Python 3.11+ and the standard library. The package is split
by responsibility: configuration, typed models, evidence, detectors, scanners,
policies, risk analysis, noise filtering, reports, privacy, AI, GitHub,
issue/release analysis, and CLI.

## Checks

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q maintainerguard
python3 -m maintainerguard validate-config
python3 -m maintainerguard demo --scenario high-risk-auth
./mg verify
python3 -m pip wheel . --no-deps
```

Tests use sample data and mocks; they must not require network access, API keys,
or a real GitHub repository.

After `python3 -m pip install -e .`, both `maintainerguard` and `mg` point to
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

`action.yml` delegates to `python3 -m maintainerguard action-run`. Keep Action
inputs mapped through environment variables in one place and preserve safe
defaults: dry-run on, no comment publishing, update existing comments, no AI
unless explicitly enabled, and no secrets required for local demos.

The Action must remain portable when used as `uses: xxxquide/MaintainerGuard@tag`.
Keep `$GITHUB_ACTION_PATH` on `PYTHONPATH` and do not `cd` into the Action
directory; config, scanner, and event paths should resolve from the caller
workspace.
