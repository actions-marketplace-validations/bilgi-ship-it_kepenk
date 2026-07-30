# Codex integration

Kepenk does not depend on Codex, and Codex is not part of the core policy engine. This integration is a small, auditable adapter that turns a shell command into a structured Kepenk action before execution.

## Files

- [`examples/codex/kepenk_codex.py`](../../examples/codex/kepenk_codex.py): non-interactive wrapper
- [`examples/codex/kepenk.yaml`](../../examples/codex/kepenk.yaml): conservative example policy
- [`examples/codex/AGENTS.md`](../../examples/codex/AGENTS.md): instructions for a coding agent

## Setup

Install Kepenk in the repository environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Copy or adapt the example policy and agent instructions. The wrapper uses the adjacent `kepenk.yaml` by default. Override it with `--policy` or the `KEPENK_POLICY` environment variable.

## Decision-only check

```bash
python examples/codex/kepenk_codex.py check -- git push origin main
```

The command is evaluated but never executed.

## Run an allowed command

```bash
python examples/codex/kepenk_codex.py run -- python -m pytest
```

`run` is deliberately non-interactive. An `approval` decision exits with code `75` instead of prompting inside an unattended agent session.

## Human-approved command

After a maintainer approves the exact command:

```bash
python examples/codex/kepenk_codex.py approve -- git push origin main
```

The policy is evaluated again. A `deny` decision remains non-bypassable even in `approve` mode.

## Exit codes

| Code | Meaning | Agent behavior |
|---:|---|---|
| `0` | Allowed and completed, or check allowed | Continue |
| `64` | Invalid policy or invocation | Stop and report |
| `75` | Human approval required | Ask the maintainer |
| `77` | Denied by policy | Never bypass |
| other | Child process exit code | Report command failure |

## Trust boundary

The wrapper is an enforcement point only when the agent is required to use it. Direct shell execution outside Kepenk remains outside the security boundary. Combine this workflow with sandboxing, least-privilege credentials, branch protection, and code review.
