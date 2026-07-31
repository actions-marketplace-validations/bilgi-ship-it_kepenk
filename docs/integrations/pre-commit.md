# pre-commit integration

Kepenk publishes a managed Python hook that validates changed policy files before a commit is created.

## Consumer configuration

Add this to the consuming repository's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/bilgi-ship-it/kepenk
    rev: <reviewed-commit-or-release-containing-the-hook>
    hooks:
      - id: kepenk-validate
        files: '^(kepenk\.yaml|config/agent-policy\.yaml)$'
```

Use an immutable reviewed commit SHA or a release tag that contains `.pre-commit-hooks.yaml`. The `files` expression can list one or more policy locations used by the repository.

Install and run:

```bash
python -m pip install pre-commit
pre-commit install
pre-commit run kepenk-validate --all-files
```

The same commands work on Linux, macOS, and Windows when Python and Git are available. pre-commit creates an isolated Python environment for the managed hook.

## Result format

A valid file prints a line such as:

```text
VALID kepenk.yaml: version=1 default=approval rules=4
```

An invalid or missing file prints a diagnostic to standard error and returns exit code `1`:

```text
INVALID config/agent-policy.yaml: only policy version 1 is supported
```

The hook continues through all filenames so a single run can report more than one policy error, but any error fails the commit.

## Default file matching

The published hook automatically considers common names such as:

- `kepenk.yaml`
- `kepenk.production.yml`
- `service.kepenk.yaml`
- `.kepenk/policy.yaml`

Override `files` in the consumer configuration for other names.

## Repository self-check

Kepenk itself uses a local pre-commit configuration to validate the starter policy, all policy packs, and demo policies:

```bash
pre-commit validate-manifest .pre-commit-hooks.yaml
pre-commit validate-config .pre-commit-config.yaml
pre-commit run kepenk-validate-local --all-files
```

These commands run in the Ubuntu and Windows CI matrix.
