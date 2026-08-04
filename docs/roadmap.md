# Roadmap

This file lists what shipped and what is next. It is short on purpose.

An earlier version of this roadmap planned nine releases through v2.0, with
acceptance criteria and out-of-scope sections for each. It was replaced because it
planned surface area on top of a core that had never been checked against real
scanner output. Running the actual binaries found nine defects in an evening,
including a silently dropped CRITICAL leaked credential. Documentation, presets and
contributor onboarding were being planned for behaviour that did not work.

The rule that replaced it: **nothing is planned that cannot be stated as a test
which currently fails.**

## Shipped

### v0.4 — verified scanner fidelity, and a rename

- Real-binary fidelity suite: Trivy 0.73.0, Gitleaks 8.30.1, osv-scanner 2.4.0 and
  Semgrep OSS, with fixtures checked in and a regeneration script.
- Explicit scanner-format detection. An unrecognised payload raises instead of
  normalizing to an empty list.
- Trivy `Secrets`, `Misconfigurations` and `Licenses`, not only `Vulnerabilities`.
- gitleaks native JSON, which is a top-level array.
- Semgrep native JSON as its own adapter instead of falling through to the
  secret-scanner branch.
- SARIF `suppressions`, `baselineState`, `security-severity` bands, flat
  `problem.severity`, `partialFingerprints` and CWE tags.
- Findings attributed to the change under review via `in_changed_scope` and
  `scope_reason`.
- Report order that survives comment truncation, plus an explicit truncation
  notice.
- Sanitized optional model output, and untrusted-input framing in the prompt.
- Whole-word rather than substring detector matching, file `status` honoured,
  policy field types validated, confidence capped when input bounds drop files.
- hatchling instead of a hand-written build backend, and one source for the
  version.
- Renamed the project. See [upgrading to v0.4](upgrading-to-v0.4.md).

### v0.1 – v0.3

Baseline runner, evidence model, detectors, policy presets, SARIF and Trivy
normalization, issue triage, release readiness, GitHub Action metadata, guarded
one-comment publishing, optional validated model enrichment. Those releases shipped
under the previous name.

## Next

Each item is a defect with a known reproduction, recorded during the audit that
produced v0.4. They are ordered by how much they can mislead a maintainer.

1. **Comment deduplication cannot self-heal.** With two marked comments only the
   first is updated and the rest are orphaned; a marked comment edited by a human
   is overwritten.
2. **HTTP errors are indistinguishable.** `HTTPError` subclasses `URLError`, so
   403, 404 and rate limiting collapse into one generic `RuntimeError` with no
   status and no backoff.
3. **`fail-on-risk` is not applied in `github-run`.** It works in `action-run`; the
   other path always returns 0, so advertised gating silently does nothing.
4. **`ai.endpoint` is unvalidated.** It accepts any scheme and host, including
   `file://` and link-local addresses. `timeout_seconds` accepts negatives.
5. **Risk ignores magnitude.** Risk is the maximum per-reason severity with no
   volume term, so a 300-file untested refactor scores Medium.
6. **CI pins actions by mutable tag** rather than by commit SHA — the exact
   practice this tool flags in other repositories — and tests only one Python
   version.

## Not planned

Recorded so the question is not reopened without new evidence.

- **A hosted service, dashboard or account system.** The tool works locally; a
  backend would add operational cost and remove the main reason to trust it.
- **Automatic merging.** Ever.
- **Inline per-finding review comments.** reviewdog already does this well, in any
  CI and for several forges. Duplicating it would be worse than linking to it.
- **Being a language-model code reviewer.** That market is served, free, by tools
  built for it. The optional model here improves wording and nothing else, and it
  stays optional.
- **Breadth of scanner support as a headline.** A new adapter is worth adding only
  with real output from the real binary and a test. Claimed support without a
  fixture is how an earlier release ended up dropping a critical finding.

## Feedback

The most useful contribution is a real scanner report that Veracity handles
incorrectly. Add the output to `tests/fixtures/real-scanners/` with a failing test
and the case makes itself.

- Discussions: https://github.com/xxxquide/veracity/discussions
- Good first issues:
  https://github.com/xxxquide/veracity/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22good%20first%20issue%22

Items under "Next" are intentions, not commitments, and not descriptions of current
behaviour.
