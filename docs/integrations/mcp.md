# MCP policy-gate adapter

Kepenk can run as a local Model Context Protocol server over `stdio`. It exposes one tool, `kepenk_check_action`, that evaluates a proposed structured action against a local policy and appends the decision to the configured audit chain.

The adapter never executes the proposed command, file operation, deployment, API request, or tool call.

## Install

```bash
python -m pip install "kepenk-gate[mcp]"
```

For a source checkout:

```bash
python -m pip install -e ".[mcp]"
```

## Run over stdio

```bash
kepenk-mcp --policy /absolute/path/to/kepenk.yaml
```

`KEPENK_POLICY` may be used instead of `--policy`.

The process reserves standard output for MCP protocol messages. Startup and policy errors are written to standard error and return exit code `64`.

## Host configuration

A typical local MCP host configuration is:

```json
{
  "mcpServers": {
    "kepenk": {
      "command": "kepenk-mcp",
      "args": [
        "--policy",
        "/absolute/path/to/kepenk.yaml"
      ]
    }
  }
}
```

Use an absolute policy path because MCP hosts may launch the server from a different working directory.

## Tool input

`kepenk_check_action` accepts the same structured fields as Kepenk's JSONL protocol:

```json
{
  "type": "shell",
  "command": "git push origin main",
  "path": null,
  "host": null,
  "repository": "example/project",
  "metadata": {}
}
```

Only `type` is required. `command`, `path`, `host`, and `repository` may be strings or null. `metadata` must be an object.

Use the dedicated `repository` field with policy `repository_glob` matchers. Kepenk does not inspect the MCP host's working directory or Git configuration to populate it. The field is caller-provided policy context, not authentication.

## Tool result

A valid request returns the full deterministic decision envelope:

```json
{
  "version": 1,
  "id": null,
  "ok": true,
  "decision": {
    "effect": "approval",
    "reason": "Publishing code requires human approval.",
    "rule_id": "require-approval-for-push",
    "action": {
      "type": "shell",
      "command": "git push origin main",
      "path": null,
      "host": null,
      "repository": "example/project",
      "metadata": {}
    }
  }
}
```

Malformed requests fail closed with a structured error:

```json
{
  "version": 1,
  "id": null,
  "ok": false,
  "error": {
    "code": "invalid_request",
    "message": "action.type must be a non-empty string"
  }
}
```

Audit write failures return `evaluation_error`; they must not be treated as approval to continue.

## Enforcement boundary

The MCP server is a decision service, not a sandbox or command proxy. The MCP host or calling agent must enforce the result:

- continue only when `ok` is true and `decision.effect` is `allow`;
- pause for an explicit human decision when the effect is `approval`;
- stop when the effect is `deny`;
- stop on every structured error, transport failure, timeout, or malformed response.

Do not grant the MCP server credentials or filesystem access that it does not need. Keep the policy and audit path repository-scoped, supply repository context only from a trusted caller, and combine Kepenk with least-privilege credentials, protected branches, isolated runners, and operating-system controls.

See the [repository-context guide](../repository-context.md) for examples and trust boundaries.

## Development verification

```bash
pytest tests/test_mcp_server.py
kepenk-mcp --help
```

The test suite exercises allow, approval, deny, invalid input, audit logging, tool discovery, repository context, and an in-memory MCP tool call.
