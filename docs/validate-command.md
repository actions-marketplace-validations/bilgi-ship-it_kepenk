# Policy validation command

Use `kepenk validate` to load and validate a policy without evaluating or executing an action.

```bash
kepenk --policy kepenk.yaml validate
```

Successful output:

```text
valid policy: version 1, 3 rules, default=approval
```

For CI and editor integrations, request JSON output:

```bash
kepenk --policy kepenk.yaml validate --json
```

```json
{"audit_path":".kepenk/audit.jsonl","default":"approval","rules":3,"valid":true,"version":1}
```

Invalid YAML, unsupported versions, duplicate rule IDs, unsupported match keys, and malformed fields fail closed with exit code `64`.
