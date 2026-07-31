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

- [x] structured stdin/stdout protocol ([#18](https://github.com/bilgi-ship-it/kepenk/issues/18))
- [x] at least 10 real-world policy packs ([#19](https://github.com/bilgi-ship-it/kepenk/issues/19))
- [x] three reproducible agent-safety demos ([#20](https://github.com/bilgi-ship-it/kepenk/issues/20))
- [x] pre-commit integration ([#21](https://github.com/bilgi-ship-it/kepenk/issues/21))
- [x] MCP policy-gate adapter ([#29](https://github.com/bilgi-ship-it/kepenk/issues/29))
- [x] documented compatibility contract for integrations ([#30](https://github.com/bilgi-ship-it/kepenk/issues/30))
- [x] tagged `v0.2.0` GitHub Release with verified wheel and source distribution ([#33](https://github.com/bilgi-ship-it/kepenk/issues/33))
- [x] tagged `v0.2.1` portability patch for non-Python consumer repositories ([#48](https://github.com/bilgi-ship-it/kepenk/issues/48))

## v0.3 — Maintainer workflows

- [x] policy packs for release and package publishing
- [x] declarative policy test suites for expected decisions ([#37](https://github.com/bilgi-ship-it/kepenk/issues/37))
- [x] repository-scoped approval contexts ([#39](https://github.com/bilgi-ship-it/kepenk/issues/39))
- [x] signed approval receipts ([#40](https://github.com/bilgi-ship-it/kepenk/issues/40))
- [x] audit export in SARIF format ([#41](https://github.com/bilgi-ship-it/kepenk/issues/41))
- [x] tagged `v0.3.0` GitHub Release with verified wheel and source distribution ([#60](https://github.com/bilgi-ship-it/kepenk/issues/60))

## v0.4 — Adoption and ecosystem evidence

- [x] adopter onboarding kit and public evidence registry ([#38](https://github.com/bilgi-ship-it/kepenk/issues/38))
- [x] first reproducible founding-team pilot case study ([#63](https://github.com/bilgi-ship-it/kepenk/issues/63))
- [ ] at least three independent repositories using Kepenk
- [ ] at least two contributors outside the founding team
- [x] documented maintainer response and release cadence ([#55](https://github.com/bilgi-ship-it/kepenk/issues/55))
- [ ] anonymized adoption and usage evidence
- [ ] public case studies from independent adopters
- [ ] OpenTelemetry-compatible redacted audit export ([#59](https://github.com/bilgi-ship-it/kepenk/issues/59))
- [ ] additional CI-provider integration guides ([#57](https://github.com/bilgi-ship-it/kepenk/issues/57), [#58](https://github.com/bilgi-ship-it/kepenk/issues/58))

## v1.0 — Stable policy contract

- [ ] compatibility guarantees for the policy schema
- [ ] migration guidance between schema versions
- [ ] third-party security review
- [ ] stable extension protocol
- [ ] long-term support and disclosure policy
