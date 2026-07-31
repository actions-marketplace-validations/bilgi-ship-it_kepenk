# Policy packs

These examples are conservative starting points for common coding-agent and maintainer workflows. Copy one into your repository, review every rule, and adapt it to your commands and security model.

| Pack | Safe by default | Requires approval | Denied |
|---|---|---|---|
| [`python-development.yaml`](python-development.yaml) | tests, lint, type checks, local builds | dependency installation, package upload | recursive deletion of root-like paths |
| [`git-maintenance.yaml`](git-maintenance.yaml) | status, diff, log, show and other read-only inspection | push and history-changing operations | force-push, hard reset, aggressive clean |
| [`docker-maintenance.yaml`](docker-maintenance.yaml) | version, state and configuration inspection | builds, runs, registry operations | system prune, volume deletion, forced removal |

## Use a pack

```bash
cp examples/policies/python-development.yaml kepenk.yaml
kepenk validate
kepenk check --action shell --command "python -m pytest"
kepenk check --action shell --command "python -m pip install requests"
```

Kepenk uses the first matching rule. Put narrow deny rules before broader approval or allow rules. Unmatched actions use the policy's `default`, which is `approval` in these packs.

## Security boundary

Policy packs are examples, not universal security policies. Command strings can vary across shells, wrappers, aliases and operating systems. Kepenk is not a sandbox and does not inspect what a script eventually executes. Combine it with least-privilege credentials, protected branches, isolated runners and operating-system controls.

## Validate all examples

```bash
python scripts/validate_policy_examples.py
pytest tests/test_policy_packs.py
```

CI runs both structural validation and representative decision tests for every committed pack.
