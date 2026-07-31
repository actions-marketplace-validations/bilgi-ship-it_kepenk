from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from kepenk.audit import GENESIS_HASH, _hash_event, append_decision
from kepenk.cli import EXIT_USAGE
from kepenk.cli import main as cli_main
from kepenk.errors import AuditError
from kepenk.models import Action, Decision
from kepenk.sarif import SARIF_SCHEMA, SARIF_VERSION, SarifError, build_sarif

SARIF_SHAPE = {
    "type": "object",
    "additionalProperties": True,
    "required": ["$schema", "version", "runs"],
    "properties": {
        "$schema": {"const": SARIF_SCHEMA},
        "version": {"const": "2.1.0"},
        "runs": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["tool", "results"],
                "properties": {
                    "tool": {
                        "type": "object",
                        "required": ["driver"],
                        "properties": {
                            "driver": {
                                "type": "object",
                                "required": ["name", "rules"],
                                "properties": {
                                    "name": {"const": "Kepenk"},
                                    "rules": {"type": "array"},
                                },
                            }
                        },
                    },
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["ruleId", "level", "message", "properties"],
                            "properties": {
                                "level": {"enum": ["warning", "error"]},
                                "message": {
                                    "type": "object",
                                    "required": ["text"],
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


def _decision(
    effect: str,
    *,
    rule_id: str | None,
    reason: str,
    path: str | None = None,
    command: str = "python -m pytest",
) -> Decision:
    return Decision(
        effect=effect,  # type: ignore[arg-type]
        reason=reason,
        rule_id=rule_id,
        action=Action(
            type="shell",
            command=command,
            path=path,
            host="secret.internal.example",
            repository="private/project",
            metadata={"token": "top-secret-value", "customer": "hidden"},
        ),
    )


def _write_policy(tmp_path: Path, audit_path: Path) -> Path:
    policy_path = tmp_path / "kepenk.yaml"
    policy_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "default": "approval",
                "audit": {"path": str(audit_path)},
                "rules": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return policy_path


def test_allow_only_audit_produces_valid_empty_sarif(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    append_decision(
        audit_path,
        _decision("allow", rule_id="allow-tests", reason="Tests are allowed."),
        outcome="checked",
    )

    first = build_sarif(audit_path)
    second = build_sarif(audit_path)

    Draft202012Validator(SARIF_SHAPE).validate(first)
    assert first == second
    assert first["version"] == SARIF_VERSION
    assert first["runs"][0]["tool"]["driver"]["rules"] == []
    assert first["runs"][0]["results"] == []


def test_deny_is_error_with_safe_location_and_private_fields_redacted(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    append_decision(
        audit_path,
        _decision(
            "deny",
            rule_id="deny-publish",
            reason="Package publication is blocked.",
            path="src/package.py",
            command="publish --token top-secret-value",
        ),
        outcome="denied",
    )

    document = build_sarif(audit_path)
    result = document["runs"][0]["results"][0]
    rendered = json.dumps(document, sort_keys=True)

    Draft202012Validator(SARIF_SHAPE).validate(document)
    assert result["ruleId"] == "deny-publish"
    assert result["level"] == "error"
    assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == (
        "src/package.py"
    )
    assert result["properties"] == {
        "effect": "deny",
        "actionType": "shell",
        "outcome": "denied",
        "auditEventIndex": 1,
    }
    for private_value in (
        "top-secret-value",
        "secret.internal.example",
        "private/project",
        "customer",
        "metadata",
        "command",
    ):
        assert private_value not in rendered


def test_approval_is_optional_and_exported_as_warning(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    append_decision(
        audit_path,
        _decision(
            "approval",
            rule_id=None,
            reason="Human approval is required.",
        ),
        outcome="approval_not_granted",
    )

    assert build_sarif(audit_path)["runs"][0]["results"] == []

    included = build_sarif(audit_path, include_approval=True)
    result = included["runs"][0]["results"][0]
    assert result["ruleId"] == "kepenk/default-approval"
    assert result["level"] == "warning"
    assert result["properties"]["effect"] == "approval"


def test_unsafe_paths_are_not_exported_as_locations(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    for unsafe_path in ("/etc/passwd", "../secret.txt", "C:\\secret.txt", "https://x/y"):
        append_decision(
            audit_path,
            _decision(
                "deny",
                rule_id="deny-unsafe",
                reason="Unsafe action is blocked.",
                path=unsafe_path,
            ),
            outcome="denied",
        )

    document = build_sarif(audit_path)
    assert len(document["runs"][0]["results"]) == 4
    assert all("locations" not in result for result in document["runs"][0]["results"])


def test_tampered_audit_is_refused(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    append_decision(
        audit_path,
        _decision("deny", rule_id="deny-x", reason="Blocked."),
        outcome="denied",
    )
    audit_path.write_text(
        audit_path.read_text(encoding="utf-8").replace("Blocked.", "Changed."),
        encoding="utf-8",
    )

    with pytest.raises(AuditError, match="invalid event_hash"):
        build_sarif(audit_path)


def test_hash_valid_but_malformed_event_is_refused(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    payload = {
        "timestamp": "2026-07-31T00:00:00+00:00",
        "decision": {"effect": "deny"},
        "outcome": "denied",
        "previous_hash": GENESIS_HASH,
    }
    event = dict(payload)
    event["event_hash"] = _hash_event(payload, GENESIS_HASH)
    audit_path.write_text(json.dumps(event) + "\n", encoding="utf-8")

    with pytest.raises(SarifError, match="decision.reason"):
        build_sarif(audit_path)


def test_cli_writes_stdout_or_selected_file_and_fails_closed(tmp_path: Path, capsys) -> None:
    audit_path = tmp_path / "audit.jsonl"
    policy_path = _write_policy(tmp_path, audit_path)
    append_decision(
        audit_path,
        _decision("deny", rule_id="deny-x", reason="Blocked."),
        outcome="denied",
    )

    stdout_code = cli_main(
        ["--policy", str(policy_path), "export-sarif", "--audit", str(audit_path)]
    )
    stdout_payload = json.loads(capsys.readouterr().out)
    assert stdout_code == 0
    assert stdout_payload["version"] == "2.1.0"

    output_path = tmp_path / "reports" / "kepenk.sarif"
    file_code = cli_main(
        [
            "--policy",
            str(policy_path),
            "export-sarif",
            "--audit",
            str(audit_path),
            "--output",
            str(output_path),
        ]
    )
    assert file_code == 0
    assert capsys.readouterr().out == ""
    assert json.loads(output_path.read_text(encoding="utf-8"))["version"] == "2.1.0"

    audit_path.write_text("not json\n", encoding="utf-8")
    failed_code = cli_main(
        ["--policy", str(policy_path), "export-sarif", "--audit", str(audit_path)]
    )
    captured = capsys.readouterr()
    assert failed_code == EXIT_USAGE
    assert captured.out == ""
    assert "cannot read audit log" in captured.err
