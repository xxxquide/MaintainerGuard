# Contributing to MaintainerGuard

MaintainerGuard welcomes focused contributions that improve evidence quality,
maintainer usefulness, safety, documentation, or test coverage.

## Before opening a pull request

1. Read `README.md`, `docs/architecture.md`, and `docs/privacy-and-security.md`.
2. Keep deterministic analysis useful when AI is disabled.
3. Link every important recommendation to evidence.
4. Do not add vulnerability claims that exceed supplied scanner evidence.
5. Do not introduce automatic merge behavior, comment spam, or secrets.
6. Add focused tests and update documentation for behavior changes.

## Development checks

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q maintainerguard
python3 -m pip wheel . --no-deps
python3 -m maintainerguard validate-config
python3 -m maintainerguard demo --scenario high-risk-auth
```

Third-party dependencies require an explicit design discussion because the MVP
is intentionally standard-library-only.

## Pull request guidance

Explain the behavior changed, evidence model impact, safety/privacy impact,
tests run, and any intentional limitations. Keep changes narrow and avoid
unrelated refactoring.

## Extension points

- Scanner adapters: update `maintainerguard/scanners.py`, add sample input, add normalization tests, and document the format.
- Policy rules: update config validation, policy evaluation, docs, and tests.
- Report sections: add model fields or evidence-backed derived output, then update snapshots and docs.
- GitHub Action behavior: preserve dry-run defaults and one-comment behavior.
