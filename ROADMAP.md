# Roadmap

Kepenk follows a GitHub-first release strategy. Public PyPI publication is useful but optional; it does not block development, adoption, or open-source program applications.

## v0.1 — Deterministic local gate

- [x] YAML policies
- [x] allow / approval / deny decisions
- [x] safe command execution without `shell=True`
- [x] hash-chained JSONL audit log
- [x] fail-closed policy validation
- [x] machine-readable JSON decision output
- [x] versioned JSON Schema
- [x] Codex wrapper and documented `AGENTS.md` pattern
- [x] reusable GitHub Action
- [x] Windows and PowerShell policy examples
- [x] reproducible wheel and source-distribution verification
- [x] tagged `v0.1.0` GitHub Release with verified artifacts
- [ ] optional public PyPI publication

## v0.2 — Usable agent integrations

The immediate goal is to make Kepenk easy to adopt, demonstrate, and integrate from other tools.

- [x] structured stdin/stdout protocol ([#18](https://github.com/bilgi-ship-it/kepenk/issues/18))
- [ ] at least 10 real-world policy packs ([#19](https://github.com/bilgi-ship-it/kepenk/issues/19))
- [ ] three reproducible agent-safety demos ([#20](https://github.com/bilgi-ship-it/kepenk/issues/20))
- [ ] pre-commit integration ([#21](https://github.com/bilgi-ship-it/kepenk/issues/21))
- [ ] MCP proxy adapter
- [ ] documented compatibility contract for integrations

## v0.3 — Maintainer workflows

- [ ] policy packs for release and package publishing
- [ ] repository-scoped approvals
- [ ] signed approval receipts
- [ ] audit export in SARIF format
- [ ] OpenTelemetry-compatible audit export
- [ ] policy test command for expected allow / approval / deny cases

## v0.4 — Adoption and ecosystem evidence

- [ ] at least three independent repositories using Kepenk
- [ ] at least two contributors outside the founding team
- [ ] documented maintainer response and release cadence
- [ ] anonymized adoption and usage evidence
- [ ] public case studies with reproducible configuration

## v1.0 — Stable policy contract

- [ ] compatibility guarantees for the policy schema
- [ ] migration guidance between schema versions
- [ ] third-party security review
- [ ] stable extension protocol
- [ ] long-term support and disclosure policy
