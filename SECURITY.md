# Security Policy

## Supported versions

MaintainerGuard is currently an MVP. Security fixes are applied to the latest
version on the primary development branch.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability that could put users at
risk. Contact the repository maintainers privately through the security
reporting mechanism configured by the hosting repository. Include affected
version, impact, reproduction details, and suggested mitigation when possible.

Do not include real credentials, private repository contents, or unrelated
personal data in a report.

## Security model

MaintainerGuard is a defensive review-assistance tool. It does not claim to find
all vulnerabilities or prove that a change is safe. It does not execute
untrusted repository code. Scanner findings are treated as supplied evidence,
not independently confirmed facts.

Safe defaults keep AI and comment publishing disabled, bound input sizes, redact
common secret patterns, and require explicit publication gates. See
`docs/privacy-and-security.md` for the complete model and limitations.
