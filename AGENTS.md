# AGENTS.md

## Mission

Build Kepenk as a small, deterministic, provider-neutral safety gate for AI agent actions.

## Non-negotiable rules

- Never add model-dependent policy decisions to the core engine.
- Never execute a command with `shell=True`.
- Malformed policy must fail closed.
- Preserve stable exit-code semantics.
- Add or update tests for every behavior change.
- Avoid telemetry and network calls in the core package.
- Do not weaken default deny/approval examples for convenience.

## Development commands

```bash
pip install -e ".[dev]"
ruff check .
mypy src/kepenk
pytest
```

## Architecture

- `models.py`: immutable data contracts
- `policy.py`: YAML loading and validation
- `engine.py`: deterministic matching and decisions
- `audit.py`: append-only hash-chained JSONL audit
- `runner.py`: safe subprocess wrapper
- `cli.py`: user-facing CLI and exit codes

## Pull requests

Keep changes focused. Explain threat-model impact, compatibility impact, and tests run.
