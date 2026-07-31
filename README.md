# Kepenk

**A deterministic approval and audit gate for AI coding agents.**

Kepenk sits between an agent and a side-effecting action. It evaluates a local YAML policy and returns one of three decisions:

- `allow` — continue automatically
- `approval` — require an explicit human confirmation
- `deny` — stop the action

The project is provider-neutral, local-first, and designed for coding agents, CLI automations, CI jobs, and maintainer workflows.

> Status: early alpha. The current public release is [`v0.1.0`](https://github.com/bilgi-ship-it/kepenk/releases/tag/v0.1.0). The project remains pre-1.0; machine-facing guarantees are limited to the documented [v0.x compatibility contract](docs/compatibility-v0.md).

## Why Kepenk?

AI coding agents can modify files, run shell commands, call APIs, publish packages, and change production systems. A prompt-level instruction is useful, but it is not an enforcement boundary. Kepenk provides a deterministic policy check outside the model and writes a tamper-evident audit chain.

Kepenk does **not** claim to be a sandbox. It is an approval and policy layer that should be combined with operating-system isolation, least-privilege credentials, protected branches, and normal security controls.

## Install the current release

Kepenk can be installed directly from the verified GitHub release tag; PyPI is not required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install "https://github.com/bilgi-ship-it/kepenk/archive/refs/tags/v0.1.0.zip"

kepenk --help
kepenk init
kepenk validate
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Five-minute example

```bash
kepenk init
kepenk validate
kepenk check --action shell --command "python -m pytest"
kepenk check --action shell --command "git push origin main"
kepenk run -- python -m pytest
```

The generated `kepenk.yaml` starts with conservative defaults. Safe local tests can be allowed, publishing actions can require approval, and destructive actions can be denied.

## Policy packs

Kepenk includes ten reviewed starting policies for Python, Git, Docker, npm, PyPI, Terraform, database migrations, filesystem cleanup, read-only repository inspection, and CI/CD releases.

```bash
cp examples/policies/python-development.yaml kepenk.yaml
kepenk validate
kepenk check --action shell --command "python -m pytest"
```

Every committed policy pack is validated in CI and covered by representative allow, approval and deny tests. Review and adapt a pack before use; these examples are not universal security policies. See [the policy-pack guide](examples/policies/README.md).

## Reproducible safety demos

Three executable demos show the core enforcement behavior without running a push, destructive delete, deployment, or package upload:

1. [Allow tests, pause Git push](docs/demos/test-vs-push.md)
2. [Deny destructive deletion and verify the audit chain](docs/demos/destructive-delete-audit.md)
3. [Block a publishing step in GitHub Actions](docs/demos/ci-publish-gate.md)

Run the two local demonstrations with:

```bash
python -m pip install -e ".[dev]"
python scripts/run_safety_demos.py
```

The script is part of the Ubuntu and Windows CI matrix. The publishing demo has its own executable workflow at `.github/workflows/demo-publish-gate.yml`.

## MCP policy gate

Install the optional MCP integration and run a local `stdio` server:

```bash
python -m pip install "kepenk-gate[mcp]"
kepenk-mcp --policy /absolute/path/to/kepenk.yaml
```

The server exposes one tool, `kepenk_check_action`. It accepts a structured action, returns the complete `allow`, `approval`, or `deny` decision envelope, and writes the decision to the configured audit chain. It never executes the proposed command or tool call.

See the [MCP integration guide](docs/integrations/mcp.md) for host configuration, result handling, and fail-closed enforcement requirements.

## v0.x compatibility

The [v0.x integration compatibility contract](docs/compatibility-v0.md) separates stable, experimental, and internal surfaces. Policy v1, documented CLI and JSONL contracts, the GitHub Action, and the pre-commit hook receive explicit regression protection. The MCP adapter is documented as experimental during v0.2.x rather than being presented as a v1.0-level guarantee.

Normal incompatible changes to a stable surface require public deprecation, release notes, migration guidance, and an overlap period when technically and securely practical. Security fixes may tighten behavior immediately and must explain the required user action.

## Development installation

```bash
git clone https://github.com/bilgi-ship-it/kepenk.git
cd kepenk
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

## Policy example

```yaml
version: 1
default: approval

audit:
  path: .kepenk/audit.jsonl

rules:
  - id: deny-destructive-root-delete
    effect: deny
    reason: Recursive deletion of a root-like path is never allowed.
    match:
      action: shell
      command_regex: '(^|\s)(rm|sudo\s+rm)\s+-[^\n]*r[^\n]*\s+(/|/\*|~)(\s|$)'

  - id: require-approval-for-push
    effect: approval
    reason: Publishing code requires human approval.
    match:
      action: shell
      command_regex: '(^|\s)git\s+push(\s|$)'

  - id: allow-tests
    effect: allow
    reason: Local tests are low risk.
    match:
      action: shell
      command_regex: '(^|\s)(pytest|python\s+-m\s+pytest)(\s|$)'
```

Rules are evaluated in order; the first matching rule wins. When no rule matches, `default` is used.

### Policy schema and editor support

The versioned JSON Schema is available at [`schemas/kepenk-policy-v1.schema.json`](schemas/kepenk-policy-v1.schema.json). Editors that support YAML language-server directives can enable validation and autocomplete with:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/bilgi-ship-it/kepenk/main/schemas/kepenk-policy-v1.schema.json
version: 1
```

The schema catches structural errors early. Kepenk still performs its own deterministic, fail-closed runtime validation before evaluating a policy.

## CLI

```text
kepenk init [--force]
kepenk validate [--json]
kepenk check --action TYPE [--command TEXT] [--path PATH] [--host HOST] [--json]
kepenk run [--yes] -- COMMAND [ARG ...]
kepenk protocol
kepenk verify-audit [--audit PATH]
kepenk-mcp [--policy PATH]
```

Exit codes:

- `0`: allowed, approved, or command completed successfully
- `64`: invalid configuration, CLI input, JSONL protocol request, or MCP startup input
- `75`: human approval was required but not granted
- `77`: denied by policy
- other: child process exit code

## Design principles

1. **Deterministic before intelligent** — security-critical decisions should be inspectable.
2. **Local first** — policy evaluation requires no network connection.
3. **Provider neutral** — usable with Codex, other agents, and plain automation.
4. **Fail closed** — malformed policy stops execution.
5. **Human control** — risky actions can pause for explicit approval.
6. **Auditable** — every decision can be written to a hash-chained JSONL log.

## Integrations

- [Codex integration](docs/integrations/codex.md): non-interactive `check` and `run` workflows with a sample policy and `AGENTS.md`.
- [JSONL agent protocol](docs/integrations/jsonl-protocol.md): a versioned, long-running stdin/stdout interface for agents and automation tools.
- [GitHub Action](docs/integrations/github-action.md): validate policies and check explicit actions with job summaries and reusable outputs.
- [pre-commit hook](docs/integrations/pre-commit.md): reject invalid policy files before a commit reaches CI.
- [MCP policy gate](docs/integrations/mcp.md): expose deterministic decisions through one local read-only MCP tool.
- [v0.x compatibility contract](docs/compatibility-v0.md): machine-facing stability, deprecation, and migration rules before v1.0.
- [PowerShell examples](docs/powershell.md): Windows-specific quoting, command matching, and policy limitations.

## Current v0.2 priorities

- [x] [Structured stdin/stdout protocol](https://github.com/bilgi-ship-it/kepenk/issues/18)
- [x] [Real-world policy packs](https://github.com/bilgi-ship-it/kepenk/issues/19)
- [x] [Reproducible agent-safety demos](https://github.com/bilgi-ship-it/kepenk/issues/20)
- [x] [Pre-commit integration](https://github.com/bilgi-ship-it/kepenk/issues/21)
- [x] [MCP policy-gate adapter](https://github.com/bilgi-ship-it/kepenk/issues/29)
- [x] [v0.x integration compatibility contract](https://github.com/bilgi-ship-it/kepenk/issues/30)

See [ROADMAP.md](ROADMAP.md) for the full plan.

## Releasing

The verified wheel and source distribution are attached to the [`v0.1.0` GitHub Release](https://github.com/bilgi-ship-it/kepenk/releases/tag/v0.1.0). See [docs/releasing.md](docs/releasing.md) for the reproducible build, compatibility review, and clean-install process. Public PyPI publication is optional and currently deferred.

## Security

Read [SECURITY.md](SECURITY.md) before production use. Report vulnerabilities privately.

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the issues labeled [`good first issue`](https://github.com/bilgi-ship-it/kepenk/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

## License

Apache License 2.0. See [LICENSE](LICENSE).
