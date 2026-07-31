# Kepenk

**A deterministic approval and audit gate for AI coding agents.**

Kepenk evaluates structured actions against a local policy and returns `allow`, `approval`, or `deny`. It is provider-neutral, local-first, and intended for coding agents, command-line automation, continuous integration, and open-source maintainer workflows.

The current verified public release is [v0.4.0](https://github.com/bilgi-ship-it/kepenk/releases/tag/v0.4.0). Kepenk remains early alpha and pre-1.0. See the [v0.x compatibility contract](docs/compatibility-v0.md) for the machine-facing surfaces covered during this period.

Verified source archive: https://github.com/bilgi-ship-it/kepenk/archive/refs/tags/v0.4.0.zip

Kepenk is a policy and approval layer rather than a sandbox. Use it with suitable operating-system isolation, limited credentials, protected branches, and normal software supply-chain controls.

## Start and adopt

The [adoption guide](docs/adoption.md) reaches a first policy decision in five steps and explains local, pre-commit, GitHub Actions, JSONL, and MCP integration paths.

Public integrations may be submitted to the consent-based [adopter registry](ADOPTERS.md). Independent adopters and founding-team pilots are recorded separately. Every listed project needs a public repository and a public integration permalink.

Kepenk v0.4.0 adds an experimental, telemetry-free [offline adoption-evidence manifest](docs/adoption-evidence.md). `kepenk validate-adoption` checks the local JSON structure without fetching URLs or proving ownership. The [versioned schema](schemas/kepenk-adoption-evidence-v1.schema.json) and [Ustaca AI example](examples/adoption/ustaca-ai.json) are public; registry inclusion still requires human review and maintainer consent.

A reusable [case-study outline](docs/case-study-template.md), [adopter pull-request template](.github/PULL_REQUEST_TEMPLATE/adopter.md), and [reproducible Ustaca AI founding-team case study](docs/case-studies/ustaca-ai.md) are available. The founding-team case study is public integration evidence, not independent adoption.

## Contribute or become the first independent adopter

The [ten-minute contributor quickstart](docs/contributor-quickstart.md) covers fork, environment, checks, a focused first change, and a draft pull request.

Current unassigned community work:

- [#57 — GitLab CI policy-check guide](https://github.com/bilgi-ship-it/kepenk/issues/57): documentation-focused `good first issue`;
- [#58 — Azure Pipelines policy-check guide](https://github.com/bilgi-ship-it/kepenk/issues/58): documentation-focused `good first issue`;
- [#59 — OpenTelemetry-compatible redacted audit export](https://github.com/bilgi-ship-it/kepenk/issues/59): larger privacy-first design and implementation task;
- [#65 — adopt Kepenk in an independent public repository](https://github.com/bilgi-ship-it/kepenk/issues/65): consent-based public integration evidence.

The current public record has one founding-team pilot, no verified independent adopter, and no recorded outside contributor. These counts are kept deliberately separate. See the [public project-evidence snapshot](docs/project-evidence.md).

## v0.4 release highlights

Kepenk v0.4.0 standardizes public adoption evidence without adding telemetry or a hosted service. The local manifest validator rejects unsupported fields, duplicate JSON keys, missing consent, malformed versions and dates, private or credential-bearing URLs, and repository/evidence mismatches.

The release also publishes a reproducible founding-team case study, a ten-minute contributor path, public evidence accounting, and a form-ready open-source program application package. None of these documents convert founding-team use into independent adoption or claim an outside contributor that does not exist.

The v0.3 maintainer-workflow foundation remains available: declarative policy regression tests, explicit repository-scoped policy context, privacy-safe SARIF reporting, and Ed25519-signed approval receipts.

A versioned suite records representative actions together with the expected effect and rule identifier. Test evaluation does not launch the proposed action and does not add test results to the production audit chain.

The optional `repository` action field and `repository_glob` matcher let callers distinguish repositories without Kepenk probing the current directory or Git remotes. Repository context is caller-provided policy data, not authentication.

`kepenk export-sarif` converts denied audit decisions to SARIF 2.1.0 after verifying every hash link. Approval-required decisions are optional warnings. Command text, host, repository context, metadata, timestamps, and hashes are omitted from the report.

Signed approval receipts bind one `approval` decision to the exact structured action, semantic policy digest, Ed25519 key, nonce, and expiry. Key generation, receipt creation, and receipt verification are separate from execution. A valid receipt does not prove human identity or one-time consumption and never overrides a current `deny` decision.

See the [policy-testing guide](docs/policy-testing.md), [repository-context guide](docs/repository-context.md), [SARIF guide](docs/sarif.md), [approval-receipt threat model and format](docs/approval-receipts.md), [example suite](examples/tests/python-development.tests.yaml), and [versioned schemas](schemas/).

## Integration guides

- [Codex integration](docs/integrations/codex.md)
- [Policy testing](docs/policy-testing.md)
- [Repository-scoped policy context](docs/repository-context.md)
- [SARIF audit export](docs/sarif.md)
- [Signed approval receipts](docs/approval-receipts.md)
- [Offline adoption evidence](docs/adoption-evidence.md)
- [JSONL protocol](docs/integrations/jsonl-protocol.md)
- [GitHub Action](docs/integrations/github-action.md)
- [pre-commit integration](docs/integrations/pre-commit.md)
- [MCP integration](docs/integrations/mcp.md)
- [PowerShell guidance](docs/powershell.md)

Ten reviewed starting policies are available in the [policy-pack guide](examples/policies/README.md). Three reproducible demonstrations are indexed in the [demo guide](docs/demos/README.md).

## Quality and releases

Continuous integration covers Ubuntu and Windows with Python 3.11 and 3.13. It runs linting, strict type checks, the complete test suite, the example policy regression suite, demonstrations, pre-commit checks, policy validation, and clean package-install verification.

The project follows a GitHub-first release process. Verified wheel and source distributions are attached to each completed GitHub release. Public package-index publication is a separate maintainer action.

Current maintainer ownership, response targets, review practice, release cadence, and public measurement rules are documented in [`MAINTAINERS.md`](MAINTAINERS.md). These are transparent working targets, not guaranteed service levels.

## Project links

- [Contributor quickstart](docs/contributor-quickstart.md)
- [Public project evidence](docs/project-evidence.md)
- [Adoption guide](docs/adoption.md)
- [Offline adoption evidence](docs/adoption-evidence.md)
- [Adopter registry](ADOPTERS.md)
- [Ustaca AI case study](docs/case-studies/ustaca-ai.md)
- [Maintainer policy](MAINTAINERS.md)
- [Roadmap](ROADMAP.md)
- [Contributing](CONTRIBUTING.md)
- [Compatibility contract](docs/compatibility-v0.md)
- [Release process](docs/releasing.md)
- [Security policy](SECURITY.md)
- [Open issues](https://github.com/bilgi-ship-it/kepenk/issues)

Apache License 2.0. See [LICENSE](LICENSE).
