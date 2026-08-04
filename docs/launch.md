# Launch materials

Reusable copy for talking about Veracity in public. Every number here is
reproducible from the repository; if a claim cannot be reproduced, it does not
belong on this page.

## Positioning

Veracity reads the reports your scanners already produce, attributes each finding
to the change under review, and renders one Markdown report with a verdict, a
checklist and an evidence table. Deterministic, local, no language model required.

The differentiator is not breadth. It is that the scanner support is proven against
real binaries — Trivy 0.73.0, Gitleaks 8.30.1, osv-scanner 2.4.0, Semgrep OSS —
with their byte-for-byte output checked into the test suite, and that every finding
carries a stated reason for why it was or was not counted against this change.

## The concrete hook

The honest, checkable story is the failure this was built to fix:

> A pull request that changed one file was rated **High risk** and handed the
> maintainer a **61-item checklist**, because a repository-wide Trivy report listed
> 61 CVEs in `requirements.txt` — a file the change never touched. The same input
> now returns `Ready for maintainer review` at Low risk, and lists those 65
> findings separately as pre-existing, each with a reason.

Reproduce it from a checkout; the numbers are in `CHANGELOG.md`.

## What not to say

Do not claim that Veracity:

- finds vulnerabilities, or finds every vulnerability — it reads other tools' output;
- guarantees security, or replaces human review;
- acts as an autonomous maintainer, or merges anything;
- supports a scanner that has no fixture and no test in the repository;
- is used or trusted by anyone who has not said so publicly.

Do not compare against reviewdog, GitHub code scanning or sarif-tools without
saying what they do better. The README does; public copy should match it.

## Short post

```text
Veracity — an open-source CLI and GitHub Action that turns the scanner output you already
have into one evidence-backed review verdict, scoped to the change under review.

A one-file PR used to get High risk and a 61-item checklist because a repo-wide Trivy
report listed 61 CVEs in a file the PR never touched. Now it gets Low, and those findings
are listed separately as pre-existing.

Deterministic, no LLM required, no telemetry. Scanner support tested against real
binaries: Trivy 0.73, Gitleaks 8.30, osv-scanner 2.4, Semgrep OSS.

https://github.com/xxxquide/veracity
```

## Longer post

I built Veracity, an open-source CLI and GitHub Action for maintainers who already
run scanners.

Scanners are good at finding things and bad at answering the question a maintainer
actually has on a pull request: which of these does *this change* introduce, and
what should I check before merging? Veracity reads the reports your scanners
produce, attributes each finding to the change, and renders one report with a
verdict, a checklist and an evidence table.

Two things I would want to know if someone showed me this:

**It is tested against real scanner binaries, not hand-written fixtures.** An
earlier version claimed support for Semgrep, Gitleaks and Trivy based on fixtures
written by hand. Running the real tools showed that Semgrep's native JSON was
misrouted into the secret-scanner adapter, that Gitleaks' native output crashed the
parser, and that a leaked GitHub token with CRITICAL severity was being dropped
silently. Real output for four scanners is now checked into the test suite with a
regeneration script.

**It tells you why a finding counted.** Every finding carries whether it is in
scope for this change and the reason. When it cannot tell, it keeps the finding
rather than quietly dropping it.

It is dry-run by default, does not merge, has no telemetry and no hosted service,
and the optional language model can only affect wording — never the verdict.

reviewdog is better if you want inline per-finding comments; GitHub code scanning
is better if you live in the Security tab; sarif-tools is better for manipulating
SARIF as data. Veracity's bet is the consolidated maintainer verdict with stated
attribution.

Repository: https://github.com/xxxquide/veracity

## Questions worth asking maintainers

- Which scanner output does it get wrong? That is the most useful bug report here.
- Which report sections are noise for your project?
- Is attribution to the diff the behaviour you want, or do you want repository-wide
  findings surfaced too?
- What belongs in a policy preset that is not already there?

## Launch checklist

- README hero, badges and the verified-scanner table check out.
- Latest recommended Action version is `v0.4.0`, and that tag exists.
- Every scanner named in public copy has a fixture and a test.
- Every number in public copy is reproducible from a checkout.
- GitHub About description, website and topics updated.
- Security settings reviewed.
- No adoption, benchmark, star, sponsor or testimonial claims.
- Comparison section mentions what the alternatives do better.
