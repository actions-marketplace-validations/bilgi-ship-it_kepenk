# Kepenk

**A deterministic approval and audit gate for AI coding agents.**

Kepenk evaluates structured actions against a local policy and returns `allow`, `approval`, or `deny`. It is provider-neutral, local-first, and intended for coding agents, command-line automation, continuous integration, and open-source maintainer workflows.

The current verified public release is [v0.2.1](https://github.com/bilgi-ship-it/kepenk/releases/tag/v0.2.1). Kepenk remains early alpha and pre-1.0. See the [v0.x compatibility contract](docs/compatibility-v0.md) for the machine-facing surfaces covered during this period.

Verified source archive: https://github.com/bilgi-ship-it/kepenk/archive/refs/tags/v0.2.1.zip

Kepenk is a policy and approval layer rather than a sandbox. Use it with suitable operating-system isolation, limited credentials, protected branches, and normal software supply-chain controls.

## Start and adopt

The [adoption guide](docs/adoption.md) reaches a first policy decision in five steps and explains local, pre-commit, GitHub Actions, JSONL, and MCP integration paths.

Public integrations may be submitted to the consent-based [adopter registry](ADOPTERS.md). Independent adopters and founding-team pilots are recorded separately. Every listed project needs a public repository and a public integration permalink.

A reusable [case-study outline](docs/case-study-template.md) and [adopter pull-request template](.github/PULL_REQUEST_TEMPLATE/adopter.md) are available for maintainers who choose to share their integration.

## Current main

The v0.3 development line includes declarative policy regression tests and explicit repository-scoped policy context.

A versioned suite records representative actions together with the expected effect and rule identifier. Test evaluation does not launch the proposed action and does not add test results to the production audit chain.

The optional `repository` action field and `repository_glob` matcher let callers distinguish repositories without Kepenk probing the current directory or Git remotes. Repository context is caller-provided policy data, not authentication.

See the [policy-testing guide](docs/policy-testing.md), [repository-context guide](docs/repository-context.md), [example suite](examples/tests/python-development.tests.yaml), and [versioned schema](schemas/kepenk-tests-v1.schema.json).

## Integration guides

- [Codex integration](docs/integrations/codex.md)
- [Policy testing](docs/policy-testing.md)
- [Repository-scoped policy context](docs/repository-context.md)
- [JSONL protocol](docs/integrations/jsonl-protocol.md)
- [GitHub Action](docs/integrations/github-action.md)
- [pre-commit integration](docs/integrations/pre-commit.md)
- [MCP integration](docs/integrations/mcp.md)
- [PowerShell guidance](docs/powershell.md)

Ten reviewed starting policies are available in the [policy-pack guide](examples/policies/README.md). Three reproducible demonstrations are indexed in the [demo guide](docs/demos/README.md).

## Quality and releases

Continuous integration covers Ubuntu and Windows with Python 3.11 and 3.13. It runs linting, strict type checks, the complete test suite, the example policy regression suite, demonstrations, pre-commit checks, policy validation, and clean package-install verification.

The project follows a GitHub-first release process. Verified wheel and source distributions are attached to each completed GitHub release. Public package-index publication is a separate maintainer action.

## Project links

- [Adoption guide](docs/adoption.md)
- [Adopter registry](ADOPTERS.md)
- [Roadmap](ROADMAP.md)
- [Contributing](CONTRIBUTING.md)
- [Compatibility contract](docs/compatibility-v0.md)
- [Release process](docs/releasing.md)
- [Security policy](SECURITY.md)
- [Open issues](https://github.com/bilgi-ship-it/kepenk/issues)

Apache License 2.0. See [LICENSE](LICENSE).
