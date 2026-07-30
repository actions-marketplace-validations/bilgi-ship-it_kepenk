# Agent policy

Before any side-effecting shell command, evaluate it with Kepenk:

```bash
kepenk check --action shell --command "<exact command>"
```

For commands that should be run through the policy gate:

```bash
kepenk run -- <command and arguments>
```

Never bypass a `deny` decision. Stop and ask the maintainer when the decision is `approval`.
