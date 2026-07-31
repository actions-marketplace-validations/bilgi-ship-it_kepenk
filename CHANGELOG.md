# Changelog

All notable changes will be documented here.

## [Unreleased]

### Added

- declarative version-1 policy test suites and the `kepenk test` command
- public adopter onboarding, evidence registry, case-study outline, and submission template
- first disclosed founding-team pilot in the public Ustaca AI repository
- explicit caller-provided `repository` action context and the additive policy v1 `repository_glob` matcher across CLI, JSONL, GitHub Action, MCP, and policy test suites
- deterministic `kepenk export-sarif` conversion from verified audit chains, with optional approval warnings and stdout or selected-file output

### Security

- repository context is never inferred from the filesystem or Git configuration and is documented as caller-provided policy data rather than authentication
- missing repository context does not match `repository_glob` and therefore falls through to later rules or the policy default
- SARIF export refuses invalid or malformed audit events and omits command text, host, repository context, metadata, timestamps, hashes, and unsafe paths

## [0.2.1] - 2026-07-31

### Fixed

- the composite GitHub Action no longer enables consumer-repository pip caching, so it works in repositories without Python dependency files

### Compatibility

- Action inputs, outputs, exit codes, and the pinned setup-python revision remain compatible with v0.2.0
- the public npm/Turborepo founding-team pilot passes when pinned to `v0.2.1`

## [0.2.0] - 2026-07-31

### Added

- versioned JSONL stdin/stdout protocol for long-running agent integrations
- ten reviewed policy packs covering Python, Git, Docker, npm, PyPI, Terraform, database migrations, filesystem cleanup, read-only repository inspection, and CI/CD releases
- representative allow, approval, and deny tests for every policy pack
- three reproducible safety demonstrations for test execution, Git push approval, destructive deletion, audit verification, and CI publishing gates
- managed pre-commit hook with multi-file validation and fail-closed diagnostics
- optional local MCP stdio adapter with the `kepenk_check_action` tool
- MCP client integration tests covering tool discovery, decisions, invalid input, and audit logging
- v0.x compatibility contract for policy, CLI, JSONL, GitHub Action, pre-commit, and MCP integration surfaces
- compatibility regression tests for every declared stable machine-facing surface

### Changed

- CI now validates policy examples and runs safety demos, pre-commit checks, MCP smoke tests, and compatibility tests on Ubuntu and Windows with Python 3.11 and 3.13
- release verification now covers all public command entry points and installed package metadata
- README, roadmap, and release instructions now describe integration stability and deprecation rules

### Security

- all protocol, MCP, policy-validation, and audit failures remain fail closed
- MCP integration is decision-only and never executes the proposed action
- CI demonstration proves an approval decision prevents the simulated package-publishing step
- compatibility rules prevent silent removal or incompatible mutation of stable security-relevant fields and exit codes

## [0.1.0] - 2026-07-31

### Added

- deterministic YAML policy engine
- allow, approval, and deny effects
- safe subprocess runner using argument lists and `shell=False`
- hash-chained JSONL audit log
- CLI commands for init, validate, check, run, approval, and audit verification
- machine-readable JSON output for policy validation and action decisions
- versioned JSON Schema with editor integration
- non-interactive Codex wrapper and documented `AGENTS.md` workflow
- reusable composite GitHub Action with validation, decision outputs, and job summaries
- Windows and PowerShell policy examples for deletion, publishing, testing, and read-only inspection
- documented PowerShell quoting, alias, encoded-command, and normalization limitations
- clean wheel and source-distribution verification process
- lint, strict type checking, tests, and package verification in CI
- test matrix covering Ubuntu and Windows on Python 3.11 and 3.13

### Security

- destructive recursive deletion examples are denied before lower-risk allow rules
- remote Git changes and package publication require explicit approval
- invalid or unsupported policy configurations fail closed
