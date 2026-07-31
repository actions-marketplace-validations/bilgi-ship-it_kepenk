from __future__ import annotations

import io
import json
from pathlib import Path

from kepenk.engine import PolicyEngine
from kepenk.policy import load_policy
from kepenk.protocol import EXIT_PROTOCOL_ERROR, evaluate_request, parse_request, run_protocol


def _write_policy(tmp_path: Path) -> tuple[PolicyEngine, str]:
    audit_path = tmp_path / "audit.jsonl"
    policy_path = tmp_path / "kepenk.yaml"
    policy_path.write_text(
        f"""
version: 1
default: approval
audit:
  path: {audit_path}
rules:
  - id: deny-rm
    effect: deny
    reason: destructive
    match:
      action: shell
      command_regex: 'rm\\s+-rf'
  - id: allow-python
    effect: allow
    reason: allowed
    match:
      action: shell
      command_regex: '^python'
""",
        encoding="utf-8",
    )
    policy = load_policy(policy_path)
    return PolicyEngine(policy), policy.audit_path


def _request(request_id: str, command: str) -> str:
    return json.dumps(
        {
            "version": 1,
            "id": request_id,
            "action": {"type": "shell", "command": command},
        }
    )


def test_parse_request_rejects_unknown_action_fields() -> None:
    payload = {
        "version": 1,
        "id": "x",
        "action": {"type": "shell", "command": "echo ok", "assume_safe": True},
    }

    try:
        parse_request(payload)
    except ValueError as exc:
        assert "unsupported action fields" in str(exc)
    else:
        raise AssertionError("expected invalid request")


def test_evaluate_request_returns_versioned_decision(tmp_path: Path) -> None:
    engine, audit_path = _write_policy(tmp_path)

    response = evaluate_request(
        engine,
        audit_path,
        {
            "version": 1,
            "id": "req-1",
            "action": {"type": "shell", "command": "python -V"},
        },
    )

    assert response["version"] == 1
    assert response["id"] == "req-1"
    assert response["ok"] is True
    assert response["decision"]["effect"] == "allow"


def test_protocol_processes_multiple_requests(tmp_path: Path) -> None:
    engine, audit_path = _write_policy(tmp_path)
    source = io.StringIO(
        "\n".join(
            [
                _request("allow", "python -V"),
                _request("approval", "echo hi"),
                _request("deny", "rm -rf build"),
            ]
        )
        + "\n"
    )
    output = io.StringIO()

    assert run_protocol(engine, audit_path, source, output) == 0

    responses = [json.loads(line) for line in output.getvalue().splitlines()]
    assert [item["id"] for item in responses] == ["allow", "approval", "deny"]
    assert [item["decision"]["effect"] for item in responses] == [
        "allow",
        "approval",
        "deny",
    ]
    assert len(Path(audit_path).read_text(encoding="utf-8").splitlines()) == 3


def test_protocol_fails_closed_and_continues_after_invalid_input(tmp_path: Path) -> None:
    engine, audit_path = _write_policy(tmp_path)
    source = io.StringIO(
        "{not-json}\n"
        + json.dumps(
            {
                "version": 1,
                "id": "bad-action",
                "action": {"type": "", "command": "echo hi"},
            }
        )
        + "\n"
        + _request("valid", "python -V")
        + "\n"
    )
    output = io.StringIO()

    assert run_protocol(engine, audit_path, source, output) == EXIT_PROTOCOL_ERROR

    responses = [json.loads(line) for line in output.getvalue().splitlines()]
    assert responses[0]["ok"] is False
    assert responses[0]["error"]["code"] == "invalid_json"
    assert responses[1]["id"] == "bad-action"
    assert responses[1]["ok"] is False
    assert responses[1]["error"]["code"] == "invalid_request"
    assert responses[2]["id"] == "valid"
    assert responses[2]["decision"]["effect"] == "allow"
    assert len(Path(audit_path).read_text(encoding="utf-8").splitlines()) == 1


def test_protocol_cli_reads_jsonl(tmp_path: Path, monkeypatch, capsys) -> None:
    from kepenk.cli import main

    engine, audit_path = _write_policy(tmp_path)
    del engine
    policy_path = tmp_path / "kepenk.yaml"
    monkeypatch.setattr("sys.stdin", io.StringIO(_request("cli", "python -V") + "\n"))

    assert main(["--policy", str(policy_path), "protocol"]) == 0

    response = json.loads(capsys.readouterr().out)
    assert response["id"] == "cli"
    assert response["decision"]["effect"] == "allow"
    assert len(Path(audit_path).read_text(encoding="utf-8").splitlines()) == 1
