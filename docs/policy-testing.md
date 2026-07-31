# Declarative policy testing

Kepenk policy tests prove that a policy produces the expected deterministic decision for representative actions. They are regression tests for safety rules: changing a rule, matcher, or rule order can be reviewed through an explicit pass or failure in local development and CI.

Policy tests **never execute an action**. They call the same policy engine used by `check`, compare the returned effect and rule ID with the declared expectation, and exit. They also do not append test decisions to the configured production audit chain.

## Run a suite

```bash
kepenk --policy examples/policies/python-development.yaml test \
  --tests examples/tests/python-development.tests.yaml
```

A successful run prints one line per case and a summary:

```text
PASS allow-pytest: expected allow via allow-python-tests; got allow via allow-python-tests
PASS require-package-upload-approval: expected approval via require-approval-for-package-upload; got approval via require-approval-for-package-upload
policy tests: 7 passed, 0 failed, 7 total
```

Use `--json` for CI or another program:

```bash
kepenk --policy kepenk.yaml test --tests kepenk.tests.yaml --json
```

The top-level JSON fields are:

- `version`: test-suite format version;
- `ok`: `true` only when every case passed;
- `total`, `passed`, and `failed`;
- `cases`: the structured action, expected decision, actual decision, and pass state for each named case.

## Test-suite format

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/bilgi-ship-it/kepenk/main/schemas/kepenk-tests-v1.schema.json
version: 1

cases:
  - id: allow-local-tests
    action:
      type: shell
      command: python -m pytest
      metadata:
        environment: local
    expect:
      effect: allow
      rule_id: allow-tests

  - id: default-is-approval
    action:
      type: shell
      command: echo unmatched
    expect:
      effect: approval
      rule_id: null
```

Every case requires:

- a unique, non-empty `id`;
- an `action` with a non-empty `type` and optional `command`, `path`, `host`, and JSON-compatible `metadata`;
- an `expect` mapping containing both `effect` and `rule_id`.

`effect` must be `allow`, `approval`, or `deny`. `rule_id` must contain the exact expected policy rule ID. Use `null` when no rule should match and the policy default should decide the action.

The loader rejects unknown fields, duplicate case IDs, missing expectations, unsupported versions, non-string action fields, and metadata values that cannot be represented safely in JSON. The JSON Schema provides editor validation; Kepenk still performs its own fail-closed runtime validation.

## Exit codes

- `0`: every test case passed;
- `1`: the suite was valid, but one or more expected decisions did not match;
- `64`: the policy or test suite was missing, malformed, or unsupported.

The action-decision exit codes `75` and `77` are intentionally not used by `kepenk test`. A declared approval or denial is a successful test when it matches the expectation.

## CI example

```yaml
- name: Install Kepenk
  run: python -m pip install "https://github.com/bilgi-ship-it/kepenk/archive/refs/tags/v0.2.0.zip"

- name: Test the agent policy
  run: >-
    kepenk --policy kepenk.yaml test
    --tests kepenk.tests.yaml
```

Pin a verified release tag or commit in real workflows. Keep the policy and its test suite in the same pull request so reviewers can see whether a rule change also changes the expected security behavior.

## What to test

A useful suite normally includes:

1. at least one expected `allow` for routine local work;
2. at least one `approval` for publication, deployment, credentialed access, or other reversible-but-sensitive work;
3. at least one `deny` for an action the repository never wants an agent to perform;
4. an unmatched action proving the intended default;
5. ordering cases when two rules could plausibly match the same action;
6. metadata, host, or path cases when those fields affect policy decisions.

Tests describe intended policy behavior; they do not make an unsafe policy safe. Review the policy, test cases, operating-system permissions, credentials, and surrounding sandbox or isolation controls together.
