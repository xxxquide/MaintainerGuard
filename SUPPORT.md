# Support

Veracity is a small open-source project. The best support path depends
on what you need.

## Questions and usage help

For general setup questions, workflow examples, scanner formats, or policy
ideas, use GitHub Discussions:

https://github.com/xxxquide/veracity/discussions

## Bugs

Open a bug report when Veracity behaves incorrectly, crashes, or produces
misleading output:

https://github.com/xxxquide/veracity/issues/new/choose

Before opening an issue, run:

```bash
vera doctor
vera verify
```

Please include:

- the command you ran;
- Veracity version or commit;
- Python version and operating system;
- a small sanitized sample input when possible;
- the expected output and the actual output.

Do not include real secrets, private repository contents, or active credentials.

## Security reports

Do not open a public issue for a suspected vulnerability that could put users at
risk. Follow the private reporting guidance in `SECURITY.md`.

## Scope

Veracity is an evidence-first review assistant. It does not guarantee
secure code, replace human review, or act as an autonomous maintainer.
