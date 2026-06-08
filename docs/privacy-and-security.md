# Privacy and security

MaintainerGuard is designed for authorized defensive review assistance.

## Data processed locally

Local analysis can process supplied PR metadata, changed-file paths, bounded
patch text, issue/release feeds, scanner results, and repository policy
configuration. It does not require a backend or database.

## Optional AI data

AI is disabled by default. When explicitly enabled, MaintainerGuard sends a
bounded, redacted structured representation of the deterministic report to the
configured OpenAI Responses API endpoint. It does not enumerate or send
environment variables, it requests `store: false`, and it does not send entire
repository contents.

Common token, password, API-key, GitHub-token, OpenAI-key, and private-key
patterns are redacted. Redaction is best effort, not a guarantee. Do not enable
AI for data you are not authorized to share, and review provider data-handling
terms before use.

## Operational safety

- Dry-run is enabled by default.
- GitHub comment posting is disabled and requires three explicit gates.
- MaintainerGuard never automatically merges changes.
- Input file count and diff size are bounded.
- API keys are read from named environment variables and never logged.
- AI output cannot change deterministic risk or verdict.
- Unsupported AI claims are discarded.

## Limitations

MaintainerGuard does not prove code is secure, find every bug, confirm every
scanner result, or replace human review. It does not execute untrusted code or
perform offensive security actions. Only analyze repositories and data you are
authorized to review.
