# Changelog

All notable changes will be documented here.

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
