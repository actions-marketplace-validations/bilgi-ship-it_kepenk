from __future__ import annotations

import asyncio
from pathlib import Path

import yaml
from mcp import Client

from kepenk.audit import verify_audit
from kepenk.engine import PolicyEngine
from kepenk.mcp_server import create_mcp_server, evaluate_mcp_action
from kepenk.policy import load_policy


def _write_policy(tmp_path: Path) -> Path:
    audit_path = tmp_path / "audit.jsonl"
    policy_path = tmp_path / "kepenk.yaml"
    policy_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "default": "approval",
                "audit": {"path": str(audit_path)},
                "rules": [
                    {
                        "id": "deny-root-delete",
                        "effect": "deny",
                        "reason": "destructive deletion is denied",
                        "match": {
                            "action": "shell",
                            "command_regex": r"^rm -rf /$",
                        },
                    },
                    {
                        "id": "require-push-approval",
                        "effect": "approval",
                        "reason": "push requires approval",
                        "match": {
                            "action": "shell",
                            "command_regex": r"^git push(?:\s|$)",
                        },
                    },
                    {
                        "id": "allow-status",
                        "effect": "allow",
                        "reason": "status is read only",
                        "match": {
                            "action": "shell",
                            "command_regex": r"^git status$",
                        },
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return policy_path


def test_mcp_evaluator_covers_allow_approval_deny_and_audit(tmp_path: Path) -> None:
    policy_path = _write_policy(tmp_path)
    policy = load_policy(policy_path)
    engine = PolicyEngine(policy)

    allowed = evaluate_mcp_action(
        engine,
        policy.audit_path,
        action_type="shell",
        command="git status",
    )
    approval = evaluate_mcp_action(
        engine,
        policy.audit_path,
        action_type="shell",
        command="git push origin main",
    )
    denied = evaluate_mcp_action(
        engine,
        policy.audit_path,
        action_type="shell",
        command="rm -rf /",
    )

    assert allowed["ok"] is True
    assert allowed["decision"]["effect"] == "allow"
    assert approval["decision"]["effect"] == "approval"
    assert denied["decision"]["effect"] == "deny"

    valid, count, error = verify_audit(policy.audit_path)
    assert valid is True
    assert count == 3
    assert error is None


def test_mcp_evaluator_fails_closed_for_invalid_input(tmp_path: Path) -> None:
    policy_path = _write_policy(tmp_path)
    policy = load_policy(policy_path)

    response = evaluate_mcp_action(
        PolicyEngine(policy),
        policy.audit_path,
        action_type="",
        command="git status",
    )

    assert response == {
        "version": 1,
        "id": None,
        "ok": False,
        "error": {
            "code": "invalid_request",
            "message": "action.type must be a non-empty string",
        },
    }
    assert not Path(policy.audit_path).exists()


def test_mcp_server_exposes_one_policy_check_tool(tmp_path: Path) -> None:
    policy_path = _write_policy(tmp_path)
    server = create_mcp_server(policy_path)

    async def exercise() -> None:
        async with Client(server) as client:
            tools = await client.list_tools()
            assert [tool.name for tool in tools.tools] == ["kepenk_check_action"]

            result = await client.call_tool(
                "kepenk_check_action",
                {"type": "shell", "command": "git status"},
            )
            assert result.structured_content is not None
            assert result.structured_content["ok"] is True
            assert result.structured_content["decision"]["effect"] == "allow"

    asyncio.run(exercise())
