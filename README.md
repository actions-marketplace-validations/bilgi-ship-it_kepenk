# Kepenk

**A deterministic approval and audit gate for AI coding agents.**

Kepenk sits between an agent and a side-effecting action. It evaluates a local YAML policy and returns one of three decisions:

- `allow` — continue automatically
- `approval` — require an explicit human confirmation
- `deny` — stop the action

The project is provider-neutral, local-first, and designed for coding agents, CLI automations, CI jobs, and maintainer workflows.

> Status: early alpha. The current public release is [`v0.1.0`](https://github.com/bilgi-ship-it/kepenk/releases/tag/v0.1.0). The policy format may evolve before v1.0.

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
    reason: Local test commands are low risk.
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
```

Exit codes:

- `0`: allowed, approved, or command completed successfully
- `64`: invalid configuration, CLI input, or JSONL protocol request
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
- [PowerShell examples](docs/powershell.md): Windows-specific quoting, command matching, and policy limitations.

## Current v0.2 priorities

- [Structured stdin/stdout protocol](https://github.com/bilgi-ship-it/kepenk/issues/18)
- [Real-world policy packs](https://github.com/bilgi-ship-it/kepenk/issues/19)
- [Reproducible agent-safety demos](https://github.com/bilgi-ship-it/kepenk/issues/20)
- [Pre-commit integration](https://github.com/bilgi-ship-it/kepenk/issues/21)

See [ROADMAP.md](ROADMAP.md) for the full plan.

## Releasing

The verified wheel and source distribution are attached to the [`v0.1.0` GitHub Release](https://github.com/bilgi-ship-it/kepenk/releases/tag/v0.1.0). See [docs/releasing.md](docs/releasing.md) for the reproducible build and clean-install process. Public PyPI publication is optional and currently deferred.

## Security

Read [SECURITY.md](SECURITY.md) before production use. Report vulnerabilities privately.

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the issues labeled [`good first issue`](https://github.com/bilgi-ship-it/kepenk/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

## License

Apache License 2.0. See [LICENSE](LICENSE).
