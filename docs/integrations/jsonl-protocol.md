# JSONL agent protocol

Kepenk can evaluate multiple agent actions through a long-running, line-oriented process:

```bash
kepenk --policy kepenk.yaml protocol
```

The command reads one JSON object per line from standard input and writes one JSON response per line to standard output. Valid decisions are appended to the configured audit log.

## Request

```json
{"version":1,"id":"req-1","action":{"type":"shell","command":"python -m pytest","metadata":{"agent":"codex"}}}
```

Required fields:

- `version`: currently `1`
- `action`: an object containing a non-empty `type`

Optional fields:

- `id`: a string, integer, or null copied to the response
- `action.command`, `action.path`, `action.host`: string or null
- `action.metadata`: JSON object

Unknown action fields are rejected so callers cannot assume that an unenforced field affected the decision.

## Successful response

```json
{"decision":{"action":{"command":"python -m pytest","host":null,"metadata":{"agent":"codex"},"path":null,"type":"shell"},"effect":"allow","reason":"Local tests are low risk.","rule_id":"allow-tests"},"id":"req-1","ok":true,"version":1}
```

## Error response

```json
{"error":{"code":"invalid_request","message":"line 1: action.type must be a non-empty string"},"id":"req-1","ok":false,"version":1}
```

Callers must treat every response with `ok: false` as denied. Kepenk continues processing later lines, but exits with code `64` after EOF if any line was invalid. Valid allow, approval, and deny decisions do not make the protocol process exit early.

## Security boundary

This protocol evaluates policy decisions; it does not execute commands. The caller remains responsible for enforcing `allow`, pausing on `approval`, stopping on `deny`, protecting the policy file, and isolating credentials and operating-system permissions.
