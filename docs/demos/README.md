# Reproducible safety demos

These demos provide copy-paste commands and executable assertions for Kepenk's core safety behavior.

1. [Allow tests, pause Git push](test-vs-push.md)
2. [Deny destructive deletion and verify the audit chain](destructive-delete-audit.md)
3. [Block a publishing step in GitHub Actions](ci-publish-gate.md)

Run the local demonstrations from a development checkout:

```bash
python -m pip install -e ".[dev]"
python scripts/run_safety_demos.py
```

Expected final summary:

```text
demo 1: safe test command executed and returned allow
demo 1: git push returned approval and was not executed
demo 2: destructive delete returned deny and was not executed
demo 2: audit hash chain verified with 4 events
```

The CI publishing demo runs separately through `.github/workflows/demo-publish-gate.yml`. None of the demos executes a push, deletion, deployment, or package upload.
