# Repository-scoped policy context

Kepenk can evaluate the same proposed action differently for different repositories or workspaces by using one explicit action field:

- action field: `repository`
- policy matcher: `repository_glob`

The value is always supplied by the caller. Kepenk does not inspect the current directory, Git remotes, package metadata, environment variables, or a hosting provider to discover it automatically.

## Policy example

```yaml
version: 1
default: approval

rules:
  - id: allow-tests-in-example-project
    effect: allow
    reason: Tests are allowed in the reviewed project.
    match:
      action: shell
      repository_glob: example/project
      command_regex: '(^|\s)(pytest|python\s+-m\s+pytest)(\s|$)'

  - id: deny-publish-in-production-projects
    effect: deny
    reason: Public package publication is blocked in production repositories.
    match:
      action: shell
      repository_glob: 'company/production-*'
      command_contains: publish
```

Rules still use first-match-wins behavior. When a rule includes `repository_glob` and the action omits `repository`, that rule does not match. Evaluation then continues to later rules or the policy default.

## CLI

```bash
kepenk check \
  --action shell \
  --repository example/project \
  --command "python -m pytest"

kepenk run \
  --repository example/project \
  -- python -m pytest
```

## JSONL protocol

```json
{"version":1,"id":"check-1","action":{"type":"shell","repository":"example/project","command":"python -m pytest"}}
```

## GitHub Action

```yaml
- name: Check a proposed command
  uses: bilgi-ship-it/kepenk@<reviewed-commit-or-tag>
  with:
    mode: check
    policy: kepenk.yaml
    action_type: shell
    repository: example/project
    command: python -m pytest
```

A workflow may explicitly pass `${{ github.repository }}`. Kepenk itself does not read that value unless it is supplied through the `repository` input.

## MCP

The experimental `kepenk_check_action` tool accepts an optional `repository` string together with `type`, `command`, `path`, `host`, and `metadata`.

## Policy tests

```yaml
version: 1
cases:
  - id: allow-project-tests
    action:
      type: shell
      repository: example/project
      command: python -m pytest
    expect:
      effect: allow
      rule_id: allow-tests-in-example-project

  - id: missing-context-falls-back
    action:
      type: shell
      command: python -m pytest
    expect:
      effect: approval
      rule_id: null
```

## Security boundary

Repository context is not authentication and is not cryptographically bound to a checkout. A caller that can choose the value can also lie about it. Use trusted wrappers, protected workflow definitions, limited credentials, and operating-system isolation when the value affects a high-risk decision.

Kepenk intentionally avoids implicit probing because filesystem paths and Git remotes can be ambiguous, unavailable, attacker-controlled, or privacy-sensitive. Callers should provide a canonical value they understand, such as `owner/name`, and document who is allowed to set it.
