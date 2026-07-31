# Changelog

All notable changes will be documented here.

## [Unreleased]

### Changed

- refreshed the Ustaca AI founding-team case study, adopter registry, example manifest, and public evidence snapshot after the pilot moved to `v0.4.0` and began validating `.kepenk/adoption.json` in CI

### Security

- the refreshed evidence continues to classify Ustaca AI as founding-team usage and does not change verified independent adopters or recorded outside contributors from zero

## [0.4.0] - 2026-07-31

### Added

- versioned offline adoption-evidence manifest, local `kepenk validate-adoption` command, JSON Schema, public example, and fail-closed validation tests
- reproducible Ustaca AI founding-team case study linked to public policy, regression-suite, workflow, pull-request, and successful CI evidence
- ten-minute external contributor quickstart and visible `good first issue`, `help wanted`, and independent-adopter entry points
- dated public project-evidence snapshot that keeps founding-team pilots, independent adopters, and outside contributors as separate counts
- form-ready Codex for Open Source application package with regression-tested 500-character answers and private-field boundaries

### Changed

- README and adoption guidance now use the verified `v0.4.0` release and document the offline evidence workflow
- roadmap records the completed evidence-manifest work while leaving independent-adoption, outside-contributor, CI-provider, and OpenTelemetry targets open

### Security

- adoption evidence validation performs no network requests or telemetry, rejects unknown and duplicate fields, requires explicit maintainer consent, and rejects credential-bearing, local, private-network, query-bearing, fragment-bearing, and inconsistent evidence URLs
- structural validation does not claim repository ownership, maintainer identity, URL availability, production security, or independent adoption; registry inclusion remains subject to human review
- application and project-evidence documents keep applicant email, OpenAI Organization ID, credentials, billing data, and other private account details out of the public repository
- founding-team usage remains explicitly separated from independent adoption and outside contribution

## [0.3.0] - 2026-07-31

### Added

- declarative version-1 policy test suites and the `kepenk test` command
- public adopter onboarding, evidence registry, case-study outline, and submission template
- first disclosed founding-team pilot in the public Ustaca AI repository
- explicit caller-provided `repository` action context and the additive policy v1 `repository_glob` matcher across CLI, JSONL, GitHub Action, MCP, and policy test suites
- deterministic `kepenk export-sarif` conversion from verified audit chains, with optional approval warnings and stdout or selected-file output
- Ed25519 key generation plus version-1 signed approval receipt creation and local verification
- versioned JSON Schema and documented threat model for portable approval receipts
- public maintainer response targets, issue-triage practice, review expectations, release cadence, and measurement rules

### Changed

- the runtime now includes the `cryptography` dependency for Ed25519 receipt signing and verification
- README and adoption guidance now use the verified `v0.3.0` release
- roadmap and compatibility documentation describe the completed v0.3 maintainer workflow surfaces

### Security

- repository context is never inferred from the filesystem or Git configuration and is documented as caller-provided policy data rather than authentication
- missing repository context does not match `repository_glob` and therefore falls through to later rules or the policy default
- SARIF export refuses invalid or malformed audit events and omits command text, host, repository context, metadata, timestamps, hashes, and unsafe paths
- approval receipts bind the exact structured action, current approval decision, semantic policy digest, Ed25519 key ID, nonce, issuance time, and expiry
- receipt generation refuses `allow` and `deny`; receipt verification reevaluates the current policy and cannot override a current deny decision
- private keys are accepted only from explicit unencrypted PKCS8 PEM files and are never embedded in receipts, audit logs, policies, metadata, or CLI output
- receipt creation and verification never execute the proposed action or append signing material to the audit chain

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
