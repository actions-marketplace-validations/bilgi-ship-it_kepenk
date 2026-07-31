# Demo 2: deny destructive deletion and verify the audit chain

This demo evaluates a destructive command without executing it, confirms a deny decision, and verifies that the decision was recorded in the tamper-evident JSONL audit log.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp kepenk.example.yaml kepenk.yaml
```

## Evaluate the command

```bash
kepenk check --action shell --command "sudo rm -rf /" --json
```

Expected properties:

```json
{"effect":"deny","rule_id":"deny-destructive-root-delete"}
```

The command exits with code `77`. Because this uses `check`, the deletion command is never sent to a shell.

## Verify the audit log

```bash
kepenk verify-audit
```

Expected form:

```text
valid audit chain: <event-count> events
```

The exact count depends on other checks already performed with the same policy. The verification fails if an event or hash link is modified.

## Reproducible isolated proof

```bash
python scripts/run_safety_demos.py
```

The script creates a temporary policy and audit path, records the test, push, and deletion decisions, and asserts a valid four-event hash chain.
