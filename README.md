# Kepenk

**A deterministic approval and audit gate for AI coding agents.**

Kepenk sits between an agent and a side-effecting action. It evaluates a local YAML policy and returns one of three decisions:

- `allow` — continue automatically;
- `approval` — require explicit human confirmation;
- `deny` — stop the action.

The project is provider-neutral, local-first, and designed for coding agents, CLI automation, CI jobs, and open-source maintainer workflows.

> **Status:** early alpha. The current verified public release is [`v0.2.0`](https://github.com/bilgi-ship-it/kepenk/releases/tag/v0.2.0). Features described as “current main” are under development for the next minor release.

## Why Kepenk?

Coding agents can modify files, run commands, call APIs, publish packages, and change infrastructure. Prompt instructions are useful, but they are not an enforcement boundary. Kepenk provides a deterministic policy decision outside the model and can record decisions in a tamper-evident audit chain.

Kepenk is **not a sandbox**. Use it with operating-system isolation, least-privilege credentials, protected branches, and normal software supply-chain controls.

## Install the current release

PyPI is not required. Install the verified GitHub release tag:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install "https://github.com/bilgi-ship-it/kepenk/archive/refs/tags/v0.2.0.zip"

kepenk --help
kepenk init
kepenk validate
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Basic decision workflow

```bash
kepenk init
kepenk validate
kepenk check --action shell --command "python -m pytest"
kepenk check --action shell --command "git push origin main"
kepenk run -- python -m pytest
```

The generated starter policy uses conservative defaults. Rules are evaluated in order; the first matching rule wins. When no rule matches, the policy default applies.

## Declarative policy tests — current main

The v0.3 development line adds regression tests for policy decisions. A suite declares the exact `effect` and `rule_id` expected for representative actions:

```bash
kepenk --policy examples/policies/python-development.yaml test \
  --tests examples/tests/python-development.tests.yaml
```

Policy tests:

- evaluate decisions without executing the proposed action;
- do not append test results to the production audit chain;
- return `0` when every case passes;
- return `1` for expectation mismatches;
- return `64` for malformed policy or suite configuration;
- support structured JSON output with `--json`.

See [declarative policy testing](docs/policy-testing.md) and the versioned [`kepenk-tests-v1` schema](schemas/kepenk-tests-v1.schema.json).

## Policy packs

Ten reviewed starting policies cover:

- Python and Git development;
- Docker and filesystem maintenance;
- npm and PyPI package work;
- Terraform and database migrations;
- read-only repository inspection;
- CI/CD releases.

Every committed policy pack is validated in CI and tested with representative decisions. Treat examples as starting points, not universal security policies. See [the policy-pack guide](examples/policies/README.md).

## Reproducible safety demos

Three documented demonstrations show the enforcement boundary without performing publication, deployment, or destructive operations:

1. [Allow tests and pause a Git push](docs/demos/test-vs-push.md)
2. [Deny a destructive request and verify the audit chain](docs/demos/destructive-delete-audit.md)
3. [Block a publishing step in GitHub Actions](docs/demos/ci-publish-gate.md)

Run the local demos:

```bash
python -m pip install -e ".[dev]"
python scripts/run_safety_demos.py
```

## Integrations

- [Codex](docs/integrations/codex.md): non-interactive `check` and `run` workflows with a sample `AGENTS.md`.
- [Policy testing](docs/policy-testing.md): regression-test expected decisions locally and in CI.
- [JSONL protocol](docs/integrations/jsonl-protocol.md): a versioned stdin/stdout interface for agents and automation.
- [GitHub Action](docs/integrations/github-action.md): validate policies and expose reusable decision outputs.
- [pre-commit](docs/integrations/pre-commit.md): reject invalid policy files before CI.
- [MCP](docs/integrations/mcp.md): expose one local read-only decision tool over `stdio`.
- [PowerShell](docs/powershell.md): Windows-specific command matching and limitations.

## MCP policy gate

Install the optional integration from the verified release:

```bash
python -m pip install \
  "kepenk-gate[mcp] @ https://github.com/bilgi-ship-it/kepenk/archive/refs/tags/v0.2.0.zip"
kepenk-mcp --policy /absolute/path/to/kepenk.yaml
```

The MCP server evaluates and audits a proposed action. It never executes that action. The calling host must enforce `allow`, `approval`, `deny`, and transport or structured-error failures.

## CLI

```text
kepenk init [--force]
kepenk validate [--json]
kepenk test [--tests PATH] [--json]              # current main
kepenk check --action TYPE [--command TEXT] [--path PATH] [--host HOST] [--json]
kepenk run [--yes] -- COMMAND [ARG ...]
kepenk protocol
kepenk verify-audit [--audit PATH]
kepenk-mcp [--policy PATH]
```

Documented exit codes:

- `0`: success, allowed action, completed command, or all policy tests passed;
- `1`: one or more valid policy-test expectations failed;
- `64`: invalid configuration, input, protocol request, or startup state;
- `75`: human approval was required but not granted;
- `77`: denied by policy;
- another positive value from `kepenk run`: executed child-process exit code.

## Compatibility

The [v0.x compatibility contract](docs/compatibility-v0.md) separates stable, experimental, and internal surfaces. Policy v1, the documented CLI and JSONL contracts, the GitHub Action, and the pre-commit hook receive explicit regression protection. MCP and declarative policy testing remain experimental during their current v0.x development lines.

## Development

```bash
git clone https://github.com/bilgi-ship-it/kepenk.git
cd kepenk
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
mypy src/kepenk
pytest
```

CI tests Ubuntu and Windows on Python 3.11 and 3.13. It also validates policy packs, runs safety demos, executes the example policy regression suite, checks pre-commit integration, and verifies clean wheel and source-distribution installs.

## Roadmap

- `v0.2.0`: JSONL protocol, policy packs, demos, pre-commit, MCP, and compatibility contract — released.
- `v0.3`: declarative policy tests, repository-scoped contexts, signed approval receipts, and audit exports.
- `v0.4`: independent adopters, external contributors, public case studies, and verifiable ecosystem evidence.

See [ROADMAP.md](ROADMAP.md) and the current [open issues](https://github.com/bilgi-ship-it/kepenk/issues).

## Releasing

Verified wheel and source distributions are attached to the [`v0.2.0` GitHub Release](https://github.com/bilgi-ship-it/kepenk/releases/tag/v0.2.0). See [docs/releasing.md](docs/releasing.md). Public PyPI publication remains a separate explicit maintainer action.

## Security

Read [SECURITY.md](SECURITY.md) before production use. Report vulnerabilities privately.

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and issues labeled [`good first issue`](https://github.com/bilgi-ship-it/kepenk/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

## License

Apache License 2.0. See [LICENSE](LICENSE).
