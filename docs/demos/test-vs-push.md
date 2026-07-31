# Demo 1: allow tests, pause Git push

This demo proves that Kepenk can execute a reviewed local test command while stopping before a remote Git write.

## Setup

From a clean checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp kepenk.example.yaml kepenk.yaml
```

On Windows PowerShell, activate with `.\.venv\Scripts\Activate.ps1` and use `Copy-Item` instead of `cp`.

## Execute a safe test command

```bash
kepenk run -- python -m pytest --version
```

Expected decision:

```text
ALLOW: Local test commands are low risk. [rule: allow-local-tests]
```

The child command runs only because the policy returned `allow`.

## Check a proposed push

```bash
kepenk check --action shell --command "git push origin main" --json
```

Expected properties:

```json
{"effect":"approval","rule_id":"require-approval-for-push"}
```

The command exits with code `75`. `check` evaluates and audits the proposed action; it never executes `git push`.

## Automated proof

```bash
python scripts/run_safety_demos.py
```

The script asserts the exit codes, matched rules, and audit chain instead of relying on screenshots.
