# Getting started

MaintainerGuard runs locally with Python 3.11 or newer and no third-party
runtime packages.

## See value immediately

```bash
mg demo
mg demo --scenario docs-only
mg demo --scenario dependency-advisory
mg demo --scenario ci-workflow-risk
mg pr examples/sample-data/prs/dependency-update.json \
  --scanner examples/sample-data/scanners/dependency-advisory.json
```

The default authentication example should request tests and security review.
The docs-only scenario should be low risk. The dependency example with the
supplied critical scanner finding should be blocked.

## Configure a repository

Copy or edit `.maintainerguard.toml`, then validate it:

```bash
mg init
mg doctor
mg validate-config
```

Keep `dry_run = true`, AI disabled, and comment posting disabled until local
reports match maintainer expectations.

## Run tests and package

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q maintainerguard
python3 -m pip wheel . --no-deps
mg verify
```

The wheel includes the bundled sample data used by `mg demo`, so the demo
command works after installation. `maintainerguard` and
`python3 -m maintainerguard ...` remain available for debugging.

Continue with the configuration, policy, GitHub automation, and privacy guides
before enabling integrations.
