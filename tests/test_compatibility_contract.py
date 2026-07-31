from __future__ import annotations

import asyncio
import io
import json
from pathlib import Path

import yaml
from mcp import Client

from kepenk.cli import (
    EXIT_APPROVAL_NOT_GRANTED,
    EXIT_DENIED,
    EXIT_USAGE,
    _parser,
)
from kepenk.engine import PolicyEngine
from kepenk.github_action import (
    EXIT_APPROVAL_NOT_GRANTED as ACTION_EXIT_APPROVAL,
)
from kepenk.github_action import EXIT_DENIED as ACTION_EXIT_DENIED
from kepenk.github_action import EXIT_USAGE as ACTION_EXIT_USAGE
from kepenk.mcp_server import create_mcp_server
from kepenk.models import Action, Decision
from kepenk.policy import load_policy
from kepenk.protocol import (
    EXIT_PROTOCOL_ERROR,
    PROTOCOL_VERSION,
    evaluate_request,
    run_protocol,
)

ROOT = Path(__file__).resolve().parents[1]
STABLE_ACTION_KEYS = {"type", "command", "path", "host", "repository", "metadata"}
STABLE_DECISION_KEYS = {"effect", "reason", "rule_id", "action"}


def _write_policy(tmp_path: Path, *, audit_path: Path | None = None) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    selected_audit = audit_path or (tmp_path / "audit.jsonl")
    policy_path = tmp_path / "kepenk.yaml"
    policy_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "default": "approval",
                "audit": {"path": str(selected_audit)},
                "rules": [
                    {
                        "id": "allow-status",
                        "effect": "allow",
                        "reason": "read only",
                        "match": {
                            "action": "shell",
                            "command_regex": r"^git status$",
                        },
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return policy_path


def test_policy_v1_schema_contract() -> None:
    schema = json.loads(
        (ROOT / "schemas/kepenk-policy-v1.schema.json").read_text(encoding="utf-8")
    )

    assert schema["properties"]["version"]["const"] == 1
    assert set(schema["$defs"]["effect"]["enum"]) == {"allow", "approval", "deny"}
    assert {"version"}.issubset(schema["required"])
    assert {"default", "audit", "rules"}.issubset(schema["properties"])
    assert {"id", "effect", "reason", "match"}.issubset(
        schema["$defs"]["rule"]["properties"]
    )
    assert {
        "action",
        "command_regex",
        "command_contains",
        "path_glob",
        "host_glob",
        "repository_glob",
        "metadata",
    }.issubset(schema["$defs"]["match"]["properties"])


def test_cli_commands_json_shape_and_exit_code_contract() -> None:
    parser = _parser()
    samples = {
        "init": ["init"],
        "validate": ["validate", "--json"],
        "check": [
            "check",
            "--action",
            "shell",
            "--command",
            "git status",
            "--repository",
            "example/project",
            "--json",
        ],
        "run": ["run", "--repository", "example/project", "--", "python", "-V"],
        "protocol": ["protocol"],
        "verify-audit": ["verify-audit", "--audit", "audit.jsonl"],
    }

    for expected, argv in samples.items():
        assert parser.parse_args(argv).subcommand == expected

    assert (EXIT_USAGE, EXIT_APPROVAL_NOT_GRANTED, EXIT_DENIED) == (64, 75, 77)

    payload = Decision(
        effect="allow",
        reason="read only",
        rule_id="allow-status",
        action=Action(
            type="shell",
            command="git status",
            repository="example/project",
        ),
    ).to_dict()
    assert STABLE_DECISION_KEYS.issubset(payload)
    assert STABLE_ACTION_KEYS.issubset(payload["action"])
    assert payload["action"]["repository"] == "example/project"


def test_jsonl_protocol_success_and_error_contract(tmp_path: Path) -> None:
    policy = load_policy(_write_policy(tmp_path))
    engine = PolicyEngine(policy)

    response = evaluate_request(
        engine,
        policy.audit_path,
        {
            "version": 1,
            "id": 7,
            "action": {
                "type": "shell",
                "command": "git status",
                "repository": "example/project",
                "metadata": {},
            },
        },
    )
    assert PROTOCOL_VERSION == 1
    assert {"version", "id", "ok", "decision"}.issubset(response)
    assert response["id"] == 7
    assert response["ok"] is True
    assert STABLE_DECISION_KEYS.issubset(response["decision"])
    assert STABLE_ACTION_KEYS.issubset(response["decision"]["action"])
    assert response["decision"]["action"]["repository"] == "example/project"

    output = io.StringIO()
    code = run_protocol(
        engine,
        policy.audit_path,
        io.StringIO('{bad json}\n{"version":2,"id":"x","action":{}}\n'),
        output,
    )
    errors = [json.loads(line)["error"]["code"] for line in output.getvalue().splitlines()]
    assert code == EXIT_PROTOCOL_ERROR == 64
    assert errors == ["invalid_json", "invalid_request"]

    failing_policy = load_policy(_write_policy(tmp_path / "failing", audit_path=tmp_path))
    failure_output = io.StringIO()
    failure_code = run_protocol(
        PolicyEngine(failing_policy),
        failing_policy.audit_path,
        io.StringIO(
            '{"version":1,"id":9,"action":{"type":"shell","command":"git status"}}\n'
        ),
        failure_output,
    )
    failure = json.loads(failure_output.getvalue())
    assert failure_code == 64
    assert failure["error"]["code"] == "evaluation_error"


def test_github_action_input_output_and_exit_code_contract() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))

    assert {
        "mode",
        "policy",
        "action_type",
        "command",
        "path",
        "host",
        "repository",
        "metadata_json",
    }.issubset(action["inputs"])
    assert {"valid", "effect", "rule_id", "reason", "rule_count"}.issubset(
        action["outputs"]
    )
    assert action["inputs"]["mode"]["default"] == "validate"
    assert action["inputs"]["policy"]["default"] == "kepenk.yaml"
    assert action["inputs"]["repository"]["default"] == ""
    assert (ACTION_EXIT_USAGE, ACTION_EXIT_APPROVAL, ACTION_EXIT_DENIED) == (64, 75, 77)


def test_pre_commit_hook_contract() -> None:
    hooks = yaml.safe_load((ROOT / ".pre-commit-hooks.yaml").read_text(encoding="utf-8"))
    hook = next(item for item in hooks if item["id"] == "kepenk-validate")

    assert hook["entry"] == "kepenk-pre-commit"
    assert hook["language"] == "python"
    assert hook["require_serial"] is True


def test_mcp_tool_name_input_and_result_contract(tmp_path: Path) -> None:
    server = create_mcp_server(_write_policy(tmp_path))

    async def exercise() -> None:
        async with Client(server) as client:
            tools = await client.list_tools()
            tool = next(item for item in tools.tools if item.name == "kepenk_check_action")
            assert tool.name == "kepenk_check_action"

            result = await client.call_tool(
                "kepenk_check_action",
                {
                    "type": "shell",
                    "command": "git status",
                    "path": None,
                    "host": None,
                    "repository": "example/project",
                    "metadata": {},
                },
            )
            assert result.structured_content is not None
            payload = result.structured_content
            assert {"version", "id", "ok", "decision"}.issubset(payload)
            assert payload["ok"] is True
            assert STABLE_DECISION_KEYS.issubset(payload["decision"])
            assert STABLE_ACTION_KEYS.issubset(payload["decision"]["action"])
            assert payload["decision"]["action"]["repository"] == "example/project"

    asyncio.run(exercise())
