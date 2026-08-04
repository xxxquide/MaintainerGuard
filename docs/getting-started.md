# Getting started

Veracity runs locally with Python 3.11 or newer and no third-party
runtime packages.

## See value immediately

```bash
vera demo
vera demo --scenario docs-only
vera demo --scenario dependency-advisory
vera demo --scenario ci-workflow-risk
vera pr examples/sample-data/prs/dependency-update.json \
  --scanner examples/sample-data/scanners/dependency-advisory.json
```

The default authentication example should request tests and security review.
The docs-only scenario should be low risk. The dependency example with the
supplied critical scanner finding should be blocked.

## Configure a repository

Copy or edit `.veracity.toml`, then validate it:

```bash
vera init
vera doctor
vera validate-config
```

Keep `dry_run = true`, AI disabled, and comment posting disabled until local
reports match maintainer expectations.

## Run tests and package

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q veracity
python3 -m pip wheel . --no-deps
vera verify
```

The wheel includes the bundled sample data used by `vera demo`, so the demo
command works after installation. `veracity` and
`python3 -m veracity ...` remain available for debugging.

Continue with the configuration, policy, GitHub automation, and privacy guides
before enabling integrations.
