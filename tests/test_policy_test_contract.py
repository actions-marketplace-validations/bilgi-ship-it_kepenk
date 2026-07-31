from __future__ import annotations

import json
from pathlib import Path

from kepenk.cli import EXIT_TEST_FAILED, EXIT_USAGE, _parser

ROOT = Path(__file__).resolve().parents[1]


def test_policy_test_schema_contract() -> None:
    schema = json.loads(
        (ROOT / "schemas/kepenk-tests-v1.schema.json").read_text(encoding="utf-8")
    )

    assert schema["properties"]["version"]["const"] == 1
    assert schema["required"] == ["version", "cases"]
    assert schema["properties"]["cases"]["minItems"] == 1
    assert set(schema["$defs"]["case"]["required"]) == {"id", "action", "expect"}
    assert set(schema["$defs"]["action"]["properties"]) == {
        "type",
        "command",
        "path",
        "host",
        "metadata",
    }
    assert set(schema["$defs"]["expectation"]["required"]) == {"effect", "rule_id"}
    assert set(schema["$defs"]["expectation"]["properties"]["effect"]["enum"]) == {
        "allow",
        "approval",
        "deny",
    }


def test_policy_test_cli_contract() -> None:
    args = _parser().parse_args(
        ["--policy", "policy.yaml", "test", "--tests", "suite.yaml", "--json"]
    )

    assert args.subcommand == "test"
    assert args.policy == "policy.yaml"
    assert args.tests == "suite.yaml"
    assert args.json is True
    assert EXIT_TEST_FAILED == 1
    assert EXIT_USAGE == 64
