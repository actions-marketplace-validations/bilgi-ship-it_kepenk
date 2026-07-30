# Kepenk policy for coding agents

Use Kepenk before every shell action that can modify files, dependencies, Git state, remote systems, or published artifacts.

## Required workflow

Run an action through the non-interactive gate:

```bash
python examples/codex/kepenk_codex.py run -- <command> [arguments...]
```

Interpret the exit code strictly:

- `0`: the command was allowed and completed.
- `75`: approval is required. Stop and ask the maintainer. Do not execute the command directly.
- `77`: the policy denied the command. Never bypass the decision.
- `64`: the policy or invocation is invalid. Stop and report the error.

After the maintainer explicitly approves the exact command, execute it with:

```bash
python examples/codex/kepenk_codex.py approve -- <same command> [same arguments...]
```

Use `check` when only a decision is needed and the command must not run:

```bash
python examples/codex/kepenk_codex.py check -- <command> [arguments...]
```

## Non-bypass rule

Do not replace the wrapper with direct shell execution after an `approval` or `deny` result. If the command changes, evaluate the new exact command again.
