# GitHub Action integration

The repository includes a composite GitHub Action that can validate a policy or evaluate one explicit structured action. It runs locally inside the GitHub runner and sends no telemetry to a hosted Kepenk service.

## Validate a policy

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
  - name: Validate policy
    uses: bilgi-ship-it/kepenk@<commit-or-release-tag>
    with:
      mode: validate
      policy: kepenk.yaml
```

Pin Kepenk to a reviewed commit SHA or immutable release tag in production workflows.

## Check an explicit action

```yaml
- name: Check a proposed publish command
  id: policy
  uses: bilgi-ship-it/kepenk@<commit-or-release-tag>
  with:
    mode: check
    policy: kepenk.yaml
    action_type: shell
    command: twine upload dist/*
```

The step exits with Kepenk's documented codes:

- `0`: policy is valid, or the checked action is allowed
- `64`: invalid policy or action input
- `75`: explicit human approval is required
- `77`: action is denied

## Outputs

The action exposes `valid`, `effect`, `rule_id`, `reason`, and `rule_count`. A Markdown result is also written to the GitHub job summary.

## Metadata

Pass structured metadata as a JSON object:

```yaml
with:
  mode: check
  action_type: deployment
  host: api.example.com
  metadata_json: '{"environment":"production","region":"eu"}'
```

## Scope

This action validates and checks decisions. It does not execute the proposed command. Execution remains a separate workflow step and should only occur when the Kepenk step succeeds with the expected output.
