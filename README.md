# Kepenk

**A deterministic approval and audit gate for AI coding agents.**

Kepenk sits between an agent and a side-effecting action. It evaluates a local YAML policy and returns one of three decisions:

- `allow` — continue automatically
- `approval` — require an explicit human confirmation
- `deny` — stop the action

The project is provider-neutral, local-first, and designed for coding agents, CLI automations, CI jobs, and maintainer workflows.

> Status: early alpha. The policy format is intentionally small and may evolve before v1.0.

## Why Kepenk?

AI coding agents can modify files, run shell commands, call APIs, publish packages, and change production systems. A prompt-level instruction is useful, but it is not an enforcement boundary. Kepenk provides a deterministic policy check outside the model and writes a tamper-evident audit chain.

Kepenk does **not** claim to be a sandbox. It is an approval and policy layer that should be combined with operating-system isolation, least-privilege credentials, and normal security controls.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

kepenk init
kepenk check --action shell --command "git push origin main"
kepenk run -- python -m pytest
```

The generated `kepenk.yaml` starts with conservative defaults.

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
      command_regex: '(^|\\s)(rm|sudo\\s+rm)\\s+-[^\\n]*r[^\\n]*\\s+(/|/\\*|~)(\\s|$)'

  - id: require-approval-for-push
    effect: approval
    reason: Publishing code requires human approval.
    match:
      action: shell
      command_regex: '(^|\\s)git\\s+push(\\s|$)'

  - id: allow-tests
    effect: allow
    reason: Local test commands are low risk.
    match:
      action: shell
      command_regex: '(^|\\s)(pytest|python\\s+-m\\s+pytest)(\\s|$)'
```

Rules are evaluated in order; the first matching rule wins. When no rule matches, `default` is used.

## CLI

```text
kepenk init [--force]
kepenk check --action TYPE [--command TEXT] [--path PATH] [--host HOST] [--json]
kepenk run [--yes] -- COMMAND [ARG ...]
kepenk verify-audit [--audit PATH]
```

Exit codes:

- `0`: allowed, approved, or command completed successfully
- `64`: invalid configuration or CLI input
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

## Scope for v0.1

- YAML policy loader and validation
- ordered rule evaluation
- shell, filesystem, network, git, and generic action types
- interactive approval flow
- hash-chained JSONL audit log
- CLI suitable for wrappers and hooks

See [ROADMAP.md](ROADMAP.md) for planned adapters and integrations.

## Security

Read [SECURITY.md](SECURITY.md) before production use. Report vulnerabilities privately.

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and issues labeled `good first issue`.

## License

Apache License 2.0. See [LICENSE](LICENSE).
