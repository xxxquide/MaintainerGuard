# MaintainerGuard — Full Professional Prompt for an AI Engineering Agent

Copy the full prompt below into your AI coding agent, such as Codex, Claude Code, Cursor Agent, OpenHands, or another autonomous software engineering agent.

---

You are an autonomous senior-level AI software engineering agent.

Your task is to design and implement a complete open-source MVP project from scratch.

The project name is:

**MaintainerGuard**

Project tagline:

**Evidence-first AI maintainer assistant for merge, security, and release readiness.**

High-level concept:

MaintainerGuard is an open-source AI-assisted merge, security, and release readiness layer for open-source maintainers.

It helps maintainers understand whether a pull request is safe and ready to merge by analyzing the PR changes, affected files, scanner results, dependency changes, documentation impact, test impact, repository policies, and release impact. It then produces a single clear evidence-backed report for the maintainer.

This project must not be a generic AI chatbot, not a toy demo, not a simple wrapper around an AI API, and not a fake “AI vulnerability scanner” that overpromises security. It must be a serious developer tool for real open-source maintainers.

The core idea is:

MaintainerGuard should not replace human maintainers.  
MaintainerGuard should help maintainers make better decisions faster.  
MaintainerGuard should reduce review noise, not create more AI-generated spam.  
MaintainerGuard should require evidence for every important recommendation.  
MaintainerGuard should make pull request and release review more transparent, safer, and easier.

Do not hardcode a technology stack. Choose the best technical approach yourself based on the product requirements. Select the programming language, framework, libraries, architecture, testing tools, and project structure that are most appropriate for an open-source developer tool that can run locally, in CI, and in repository automation workflows.

The final project should look like a real open-source repository that could be published on GitHub and shown to developers, maintainers, and grant reviewers.

## Main product positioning

MaintainerGuard is not an “AI security scanner”.  
MaintainerGuard is not an “AI PR reviewer” that blindly posts comments.  
MaintainerGuard is an evidence-first maintainer assistant that creates merge readiness and release readiness reports.

It should combine:

- pull request analysis;
- security-sensitive change detection;
- scanner result explanation;
- dependency risk summarization;
- documentation drift detection;
- test impact detection;
- release impact detection;
- maintainer policy checks;
- evidence-backed AI summaries;
- no-spam GitHub automation behavior.

The central question MaintainerGuard answers is:

> Can this PR be safely merged, and what exactly should the maintainer review before merging?

## Core philosophy

1. Humans stay in control.
2. AI must assist, not replace.
3. Every recommendation must be grounded in evidence.
4. Evidence can be a changed file, diff hunk, scanner finding, dependency change, missing test, missing documentation update, repository policy rule, or configuration rule.
5. The tool must never claim that a vulnerability is confirmed unless the evidence clearly supports that.
6. The tool must never promise to find all bugs or all vulnerabilities.
7. The tool must avoid spam.
8. The tool must be configurable.
9. The tool must be safe by default.
10. The tool must be useful even in dry-run mode.
11. The tool must be honest about uncertainty.
12. The project must be open-source friendly and developer-friendly.
13. The project must not fake adoption, stars, users, sponsors, companies, benchmarks, or testimonials.

## Target users

Primary users:

- open-source maintainers;
- solo maintainers;
- maintainers of small and medium repositories;
- teams that review many pull requests;
- maintainers who need help understanding risky changes;
- maintainers who want better release confidence;
- maintainers who already use scanners but struggle with noisy output.

Secondary users:

- contributors who want faster feedback;
- reviewers who want concise summaries;
- release managers who need release notes and risk summaries;
- security-minded maintainers who need a lightweight review assistant;
- projects that want human-in-the-loop AI review without relying on a closed SaaS.

## Main use case

A contributor opens a pull request.

MaintainerGuard analyzes the PR and produces one structured report:

**MaintainerGuard Merge Readiness Report**

The report explains:

- what changed;
- which areas are affected;
- whether security-sensitive areas are touched;
- whether dependencies changed;
- whether scanner findings exist;
- whether tests were added or missing;
- whether documentation may need updates;
- whether there may be breaking changes;
- what the release impact is;
- what the maintainer should check before merging;
- what evidence supports each claim.

The report should help the maintainer decide:

- merge;
- review required;
- request changes;
- require tests;
- require documentation update;
- require security review;
- block until dependency/security issue is resolved.

Important product principle:

The primary output should be one clean, useful maintainer report, not many noisy inline AI comments.

If GitHub automation is implemented, the tool should post or update one bot comment per PR, not spam multiple comments. It should support dry-run mode and should avoid duplicate comments.

## Core MVP modules

### 1. Merge Readiness Engine

This is the heart of the project.

It should analyze pull request information and produce a merge readiness verdict.

Possible verdicts:

- Ready for maintainer review
- Review required
- Changes requested
- Tests required
- Documentation update recommended
- Security review recommended
- Blocked by scanner finding
- Not enough information

Risk levels:

- Low
- Medium
- High
- Critical
- Unknown

The merge readiness report should include:

- Executive summary
- Overall verdict
- Overall risk level
- Main reasons for the verdict
- Changed areas
- Security-sensitive areas
- Scanner findings summary
- Dependency impact
- Test impact
- Documentation impact
- Release impact
- Possible breaking changes
- Maintainer checklist
- Evidence table
- Confidence level
- Limitations of the analysis

Example output style:

```md
# MaintainerGuard Merge Readiness Report

Verdict: Review Required  
Overall risk: High  
Confidence: Medium

## Executive summary

This pull request modifies authentication and session validation logic. The changed files affect protected route handling and token validation. No new tests were detected for invalid, expired, or missing tokens. Documentation was not updated.

## Why this requires careful review

- Authentication middleware was modified.
- Session validation behavior appears to have changed.
- No tests were added for the changed auth flow.
- No documentation update was detected.
- One dependency-related scanner warning was found.

## Security-sensitive areas

- src/auth/session.*
- src/middleware/auth.*
- src/routes/admin.*

## Scanner signals

- CodeQL: no new alerts detected
- OSV: one dependency advisory found
- Secret scan: no obvious leaked secrets detected
- Policy check: auth changes require tests

## Suggested maintainer checklist

- Verify expired tokens are rejected.
- Confirm protected routes still require authentication.
- Add tests for missing, invalid, and expired tokens.
- Review the dependency advisory before merge.
- Update documentation if session behavior changed.

## Evidence

| Claim | Evidence | Confidence |
|---|---|---|
| Auth behavior changed | Changed files under src/auth and middleware | High |
| Tests may be missing | No files changed under tests or spec folders | Medium |
| Docs may need update | README and docs folders unchanged | Medium |
| Dependency risk exists | Scanner result reports advisory in dependency file | High |

## Limitations

This report is AI-assisted and should not replace human review.
```

### 2. Security-Sensitive Change Detector

This module should not pretend to prove vulnerabilities.

Its job is to identify when a PR touches code areas that commonly require extra security attention.

It should detect or infer changes related to:

- authentication;
- authorization;
- permissions;
- sessions;
- tokens;
- passwords;
- API keys;
- secrets;
- cryptography;
- hashing;
- encryption;
- file uploads;
- file paths;
- path traversal risk areas;
- shell command execution;
- process spawning;
- SQL/database queries;
- ORM query construction;
- user input handling;
- HTML rendering;
- templating;
- XSS-sensitive areas;
- CORS;
- redirects;
- webhooks;
- network requests;
- deserialization;
- dependency files;
- package manager files;
- lockfiles;
- CI/CD workflow files;
- release scripts;
- deployment scripts.

For each security-sensitive area, the module should produce:

- category;
- affected files;
- why this area may be sensitive;
- what the maintainer should review;
- confidence level;
- evidence.

The output should avoid fearmongering. It should say “security-sensitive area touched” rather than “vulnerability found” unless a scanner finding or clear evidence supports it.

### 3. Scanner Result Explainer

MaintainerGuard should be able to consume scanner outputs or mock/sample scanner outputs.

It should support the concept of scanner result ingestion for tools such as:

- static analysis scanners;
- dependency vulnerability scanners;
- secret scanners;
- code scanning reports;
- supply-chain reports;
- SBOM/provenance tools in future versions.

The MVP can use simplified sample scanner outputs if full integrations are too large, but the architecture should clearly allow real scanner integrations later.

The scanner result explainer should:

- group related findings;
- summarize severity;
- identify affected files/dependencies;
- explain findings in maintainer-friendly language;
- separate blocking issues from informational warnings;
- avoid duplicating scanner output blindly;
- reduce noise;
- suggest next maintainer action;
- include evidence.

Example:

Scanner finding:

> Dependency X has known advisory Y.

MaintainerGuard explanation:

> This PR updates the dependency lockfile and introduces dependency X version 1.2.3, which is associated with advisory Y in the provided scanner output. Review whether the vulnerable code path is reachable and consider upgrading to a patched version before merge.

### 4. Evidence-First AI Layer

This is one of the most important parts of the project.

Any AI-generated recommendation must be connected to evidence.

The AI layer should never simply say:

> This PR is risky.

It should say:

> This PR is risky because it modifies authentication middleware and no tests were added for the changed auth flow.

The AI layer should support structured outputs where appropriate.

It should return objects or structured data such as:

- summary;
- verdict;
- risk level;
- reasons;
- evidence;
- confidence;
- limitations;
- checklist items.

The AI layer should be separated from the rest of the project.

Do not scatter prompts randomly throughout the codebase.

Prompts/templates should be centralized and easy to inspect.

The AI layer should:

- avoid sending secrets;
- mask sensitive values;
- limit input size;
- handle API failures;
- support dry-run/sample mode;
- support deterministic behavior where possible;
- validate AI output before using it;
- avoid hallucinated claims;
- avoid unsupported vulnerability claims;
- include uncertainty when needed.

If AI is not configured, the tool should still provide useful heuristic-based analysis where possible.

### 5. AI Noise Gate

This is a major differentiator.

MaintainerGuard should be designed to reduce AI-generated maintainer noise, not add to it.

The tool should include a “noise gate” concept.

Before publishing or displaying a finding, the tool should check:

- Is there evidence?
- Is this finding useful to a maintainer?
- Is this a duplicate?
- Is the confidence too low?
- Is this already covered by another finding?
- Is this actionable?
- Is this too vague?
- Is this likely to create unnecessary noise?
- Does it respect the user’s config?

The tool should prefer one concise report over many comments.

No-spam behavior:

- post one comment per PR if integrated with GitHub;
- update previous MaintainerGuard comment instead of creating new ones;
- avoid commenting on bot-generated PRs unless configured;
- support skip labels such as no-ai, skip-ai, skip-maintainerguard;
- support dry-run mode;
- support maximum comment length;
- support concise/detailed modes;
- avoid repeated comments for the same unchanged analysis.

### 6. Documentation Drift Detector

This module should detect when code changes may require documentation updates.

It should analyze:

- public API changes;
- configuration changes;
- CLI behavior changes;
- environment variable changes;
- authentication behavior changes;
- permission changes;
- dependency changes;
- new features;
- removed behavior;
- breaking changes;
- examples affected by code changes.

It should check whether related documentation files were updated:

- README;
- docs folder;
- examples folder;
- changelog;
- migration guide;
- API docs;
- configuration reference.

It should produce:

- whether documentation update is likely needed;
- affected docs;
- evidence;
- confidence;
- suggested action.

Example output:

```md
Documentation impact: Recommended

This PR changes configuration validation behavior, but no documentation files were updated.

Potential docs to review:
- README configuration section
- docs/configuration.md
- examples/maintainerguard.yml

Evidence:
- config-related source files changed
- no files changed under docs/
- example config unchanged
```

### 7. Test Impact Detector

This module should detect when tests may be missing.

It should analyze:

- changed files;
- risk areas;
- whether test files changed;
- whether behavior changed;
- whether security-sensitive code changed;
- whether dependency/config behavior changed.

It should not automatically accuse the contributor. It should say:

> Tests may be needed

or

> No related test changes detected.

It should produce:

- test impact level;
- suggested test focus;
- missing test categories;
- affected files;
- evidence.

Example:

```md
Test impact: High

This PR modifies authentication behavior, but no related test files were changed.

Suggested tests:
- expired token rejection;
- invalid token rejection;
- unauthenticated protected route access;
- valid session success path.
```

### 8. Dependency and Supply-Chain Change Analyzer

This module should detect when PRs change dependency or supply-chain relevant files.

Examples:

- package manifests;
- lockfiles;
- dependency config;
- build scripts;
- CI workflows;
- release scripts;
- container files;
- package publishing config;
- installation scripts.

It should identify:

- new dependencies;
- removed dependencies;
- version upgrades/downgrades;
- lockfile-only changes;
- package script changes;
- suspicious install/postinstall scripts;
- CI permission changes;
- release workflow changes.

The tool should not claim malicious behavior without evidence.

It should produce:

- supply-chain impact summary;
- affected files;
- scanner findings if available;
- maintainer checklist;
- confidence;
- evidence.

### 9. Release Readiness Module

This module helps maintainers before releases.

It should be able to generate a release readiness report from recent merged PRs, issues, scanner summaries, and changelog-like data.

The release readiness report should include:

- release summary;
- notable changes;
- breaking changes;
- security-sensitive changes;
- dependency changes;
- docs status;
- tests status;
- unresolved high-risk items;
- generated release notes draft;
- release checklist.

Example sections:

```md
# MaintainerGuard Release Readiness Report

## Executive summary

This release contains 12 merged pull requests, including 2 security-sensitive changes and 1 dependency update. One breaking change may require documentation.

## Breaking changes

- Configuration validation is now stricter.

## Security-sensitive changes

- Authentication middleware updated.
- Token validation behavior changed.

## Dependency changes

- Updated dependency X from 1.2.0 to 1.3.0.

## Suggested release checklist

- Confirm migration notes are included.
- Verify auth tests pass.
- Review dependency advisory status.
- Confirm changelog includes breaking changes.
```

### 10. Issue Triage Module

This is useful but secondary.

The tool should optionally analyze issues and help maintainers triage them.

It should detect:

- bug report;
- feature request;
- question;
- documentation issue;
- support request;
- unclear issue;
- possible duplicate;
- missing reproduction;
- missing environment details;
- missing version;
- missing logs;
- missing expected/actual behavior.

It should suggest:

- labels;
- priority;
- next action;
- polite response;
- possible duplicates if data is available.

Example:

```md
Issue type: Bug report  
Confidence: Medium  
Suggested labels: bug, needs reproduction, needs environment info

Missing information:
- package version;
- operating system;
- reproduction steps;
- full error log.

Suggested response:
“Thanks for the report. Could you please provide the package version, operating system, exact command, and a minimal reproduction? That will help us investigate faster.”
```

### 11. Maintainer Policy System

The project should support repository-specific policies.

Examples:

- auth changes require tests;
- public API changes require docs;
- dependency changes require scanner check;
- CI workflow changes require maintainer approval;
- high-risk files require manual review;
- no automatic comments on draft PRs;
- skip analysis for certain paths;
- skip analysis for certain labels;
- block merge report if critical scanner finding exists.

The policy system should be configurable.

Example policy ideas:

- highRiskPaths
- requiredDocsForPaths
- requiredTestsForPaths
- securitySensitivePaths
- dependencyFiles
- releaseSensitiveFiles
- skipLabels
- commentMode
- riskThresholds

### 12. Configuration System

The project must have a clear and beginner-friendly configuration system.

The user should be able to configure:

- enabled modules;
- AI usage;
- dry-run mode;
- comment mode;
- report length;
- risk thresholds;
- labels to skip;
- file paths to ignore;
- security-sensitive paths;
- dependency files;
- docs paths;
- test paths;
- release paths;
- scanner input paths;
- policy rules;
- output format;
- whether to post comments;
- whether to update previous comments;
- maximum diff size;
- maximum files analyzed;
- language/tone if appropriate;
- privacy settings;
- log level.

The project should include a fully documented example configuration file.

The default configuration should be safe:

- dry-run or non-destructive behavior by default;
- no secrets logged;
- no spammy comments;
- no destructive actions;
- no automatic merge decisions;
- human-in-the-loop by default.

### 13. CLI or Local Runner

The project should include a way to run MaintainerGuard locally.

A user should be able to run sample scenarios.

Possible commands or equivalent functionality:

- analyze PR from sample data;
- analyze issue from sample data;
- generate merge readiness report;
- generate release readiness report;
- validate config;
- print example config;
- run dry-run analysis;
- parse scanner result sample.

The exact CLI design is up to you. Choose the best design.

The local demo must work without requiring a real GitHub repository.

The user should be able to see the value immediately through sample data.

### 14. GitHub Automation Readiness

The project should be designed so it can run in GitHub automation workflows.

If full GitHub integration is feasible, implement it.

If not fully feasible for MVP, provide:

- architecture for integration;
- example workflow files;
- documented expected inputs;
- documented permissions;
- dry-run examples;
- comment posting strategy;
- secrets configuration;
- safe defaults.

The project should explain:

- how to run on pull_request;
- how to run on issue_opened;
- how to run on schedule for weekly/release reports;
- how to provide scanner outputs;
- how to avoid comment spam;
- how to configure permissions safely.

### 15. Report Format

Reports should be Markdown-first.

The main report should be readable directly in a GitHub PR comment.

The report should be structured, not chaotic.

Recommended Merge Readiness Report sections:

- Header
- Verdict
- Risk level
- Confidence
- Executive summary
- Key changes
- Risk reasons
- Security-sensitive areas
- Scanner findings
- Dependency impact
- Test impact
- Documentation impact
- Release impact
- Maintainer checklist
- Evidence table
- Limitations

The report should not be too long by default. Provide concise and detailed modes.

### 16. Evidence Table

The evidence table is a core product feature.

Every important claim should be backed by evidence.

Evidence can include:

- changed file path;
- diff summary;
- scanner finding;
- dependency file change;
- missing docs change;
- missing tests change;
- configured policy rule;
- issue/PR metadata;
- release data.

Example:

```md
| Claim | Evidence | Confidence |
|---|---|---|
| Authentication behavior changed | src/auth/session.ts and src/middleware/auth.ts modified | High |
| Tests may be missing | No test files changed in this PR | Medium |
| Documentation may need update | docs/ and README unchanged | Medium |
| Dependency risk exists | Scanner finding in dependency report | High |
```

### 17. Security and Privacy Requirements

The project must include strong security and privacy documentation.

It must explain:

- what data may be sent to AI providers;
- how secrets are protected;
- how to avoid sending private data;
- how to run in dry-run mode;
- how to disable AI;
- how to use the tool safely in public repositories;
- why AI output is not a substitute for human review;
- limitations of AI-assisted security review;
- responsible disclosure guidance if relevant.

The implementation should:

- never log API keys;
- mask secrets;
- avoid sending environment variables;
- avoid sending full repository contents unnecessarily;
- limit input size;
- avoid storing sensitive prompt data unless explicitly configured;
- keep all destructive actions disabled by default;
- avoid scanning repositories without authorization.

The project must not include offensive security functionality, exploit generation, malware, credential theft, or instructions for attacking systems.

This is a defensive maintainer-assistance tool.

### 18. Documentation Requirements

The README must be excellent.

It should include:

- project name;
- tagline;
- short explanation;
- why this exists;
- key features;
- how it works;
- example merge readiness report;
- quick start;
- local demo;
- configuration;
- sample GitHub workflow;
- scanner integration concept;
- safety and privacy notes;
- roadmap;
- contributing;
- license;
- disclaimer.

README tone:

- professional;
- clear;
- calm;
- developer-friendly;
- no hype;
- no fake claims;
- no fake adoption;
- no unrealistic security promises.

Recommended README positioning:

> MaintainerGuard helps open-source maintainers review pull requests with more confidence by producing evidence-backed merge readiness reports. It combines pull request analysis, security-sensitive change detection, scanner result summaries, documentation/test impact checks, and release readiness signals into one concise report.

Add docs folder with:

- getting-started guide;
- configuration reference;
- report format reference;
- GitHub workflow examples;
- scanner input examples;
- privacy and security guide;
- maintainer policies guide;
- development guide;
- contributing guide.

### 19. Repository Files

Create a professional repository structure.

Required files:

- README;
- LICENSE;
- CONTRIBUTING;
- SECURITY or SECURITY section;
- CHANGELOG;
- CODE_OF_CONDUCT if appropriate;
- example configuration file;
- example workflows;
- docs folder;
- examples folder;
- sample data folder;
- tests;
- project metadata;
- ignore file;
- environment example if needed;
- CI configuration if appropriate.

Do not create a messy one-file project.

Separate code by responsibility:

- config loading;
- PR analysis;
- issue analysis;
- scanner parsing;
- security-sensitive detection;
- docs/test impact detection;
- release readiness;
- AI provider layer;
- prompt templates;
- evidence model;
- report rendering;
- CLI/local runner;
- GitHub integration layer;
- utilities;
- tests.

### 20. Sample Data

Include realistic sample data so the project can demo itself.

Sample PRs:

- low-risk docs-only PR;
- medium-risk config change PR;
- high-risk auth/session PR;
- dependency update PR;
- CI workflow change PR;
- release-impact PR.

Sample scanner outputs:

- clean result;
- dependency advisory result;
- secret scanner result;
- static analysis warning;
- mixed severity report.

Sample issues:

- bug report missing reproduction;
- feature request;
- docs issue;
- support question;
- possible duplicate.

The local demo should use these samples and generate realistic reports.

### 21. Tests

Add tests for core logic.

Test areas:

- config loading and validation;
- risk classification;
- evidence creation;
- security-sensitive file detection;
- docs drift detection;
- test impact detection;
- scanner result parsing;
- report rendering;
- no-spam/no-duplicate logic if implemented;
- AI output validation if implemented.

Tests should not require real API keys.

Use mocks or sample data.

### 22. Quality Requirements

Code quality must be high.

Requirements:

- clean architecture;
- readable names;
- consistent formatting;
- good error handling;
- meaningful errors;
- no hardcoded secrets;
- no fake runtime behavior;
- no broken examples;
- no misleading placeholders;
- no unnecessary complexity;
- no giant unreadable functions;
- good separation of pure logic and external calls;
- external services should be mockable;
- project should run locally;
- tests should pass;
- docs should match behavior.

### 23. AI Prompt Requirements Inside the Project

If the project uses AI prompts internally, they should be:

- short;
- structured;
- deterministic-friendly;
- evidence-focused;
- maintainer-focused;
- non-hallucination oriented;
- safe;
- clear about uncertainty;
- designed to produce structured output.

Internal AI instruction style:

> You are helping an open-source maintainer review a pull request. Do not invent vulnerabilities. Only make claims supported by provided evidence. If evidence is weak, mark confidence as low. Produce actionable maintainer guidance.

### 24. Important Avoidances

Do not build:

- a generic chatbot;
- a closed SaaS;
- a dashboard-first startup prototype;
- a fake AI security scanner;
- a tool that claims to find all vulnerabilities;
- a tool that automatically merges PRs;
- a tool that spams inline comments;
- an offensive security tool;
- a credential extraction tool;
- a malware or exploit generator;
- a project with fake users/stars/testimonials;
- a project that requires a backend just to demo the MVP.

Avoid marketing phrases like:

- “guaranteed security”;
- “finds every vulnerability”;
- “replace human review”;
- “fully autonomous maintainer”;
- “trusted by thousands” unless true;
- “enterprise-grade” unless justified.

### 25. Product Roadmap

Add a realistic roadmap.

Suggested roadmap:

v0.1:

- local runner;
- sample PR analysis;
- merge readiness report;
- security-sensitive change detection;
- docs/test impact detection;
- sample scanner result parsing;
- evidence table;
- configuration file;
- markdown report rendering.

v0.2:

- GitHub Action integration;
- update-one-comment mode;
- richer scanner integrations;
- policy system;
- issue triage;
- release readiness report.

v0.3:

- more scanner formats;
- duplicate finding reduction;
- repository-specific risk profiles;
- multi-language output;
- plugin system;
- GitLab support.

Future:

- organization-level maintainer reports;
- SBOM/provenance integration;
- local model support;
- web report viewer;
- advanced policy engine;
- maintainer analytics.

### 26. MVP Acceptance Criteria

The project is acceptable only if:

1. It has a clear product vision.
2. It is a real working MVP, not only a README.
3. It can run locally on sample data.
4. It generates a real merge readiness report.
5. The report includes evidence-backed claims.
6. It includes security-sensitive change detection.
7. It includes docs/test impact detection.
8. It includes scanner result explanation using sample scanner data.
9. It includes configuration.
10. It includes tests for core logic.
11. It includes strong documentation.
12. It has safe defaults.
13. It does not overpromise security.
14. It avoids AI spam.
15. It does not fake adoption.
16. It is easy to understand.
17. It is easy to extend.
18. It looks like a professional open-source repository.
19. It can be presented to open-source maintainers.
20. It can later be used as the basis for a serious public OSS project.

### 27. Suggested Final User Experience

A new user should be able to:

1. Clone the repository.
2. Install or prepare the project using the chosen stack.
3. Run a local demo command.
4. See a MaintainerGuard report generated from sample PR data.
5. Open README and understand the tool within 2 minutes.
6. Copy an example config.
7. See how it would run in GitHub automation.
8. Understand privacy and safety limitations.
9. Understand what is implemented now and what is future work.

### 28. Final Output Expected From You

After implementing the project, provide a final summary containing:

- what was built;
- why the architecture was chosen;
- main files and folders;
- how to run the local demo;
- how to run tests;
- how to configure the tool;
- sample commands;
- what features work now;
- what is intentionally mocked or sample-based;
- what limitations exist;
- what should be improved next;
- how this project could be prepared for public GitHub release.

Do not ask unnecessary questions.

Make strong engineering decisions yourself.

If a detail is ambiguous, choose the option that makes the project:

- more useful for OSS maintainers;
- safer;
- more honest;
- easier to demo;
- easier to maintain;
- more credible as an open-source tool.

Build the project as if it will be published publicly and reviewed by serious developers.

The final result should feel like a polished open-source MVP for a real maintainer-focused AI developer tool.
