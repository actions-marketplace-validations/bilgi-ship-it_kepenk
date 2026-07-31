from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from kepenk.cli import main as cli_main
from kepenk.engine import PolicyEngine
from kepenk.github_action import main as action_main
from kepenk.mcp_server import evaluate_mcp_action
from kepenk.models import Action
from kepenk.policy import load_policy
from kepenk.policy_tests import evaluate_policy_test_suite, load_policy_test_suite
from kepenk.protocol import ProtocolError, evaluate_request, parse_request

ROOT = Path(__file__).resolve().parents[1]


def _write_policy(tmp_path: Path) -> Path:
    policy_path = tmp_path / "kepenk.yaml"
    policy_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "default": "approval",
                "audit": {"path": str(tmp_path / "audit.jsonl")},
                "rules": [
                    {
                        "id": "deny-publish-in-production",
                        "effect": "deny",
                        "reason": "publishing is blocked in production repositories",
                        "match": {
                            "action": "shell",
                            "repository_glob": "company/production-*",
                            "command_contains": "publish",
                        },
                    },
                    {
                        "id": "allow-project-tests",
                        "effect": "allow",
                        "reason": "tests are allowed in reviewed projects",
                        "match": {
                            "action": "shell",
                            "repository_glob": ["company/app", "company/library-*"],
                            "command_regex": r"^python -m pytest$",
                        },
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return policy_path


def test_repository_glob_matches_exact_and_pattern_and_missing_context_falls_back(
    tmp_path: Path,
) -> None:
    engine = PolicyEngine(load_policy(_write_policy(tmp_path)))

    exact = engine.evaluate(
        Action(
            type="shell",
            command="python -m pytest",
            repository="company/app",
        )
    )
    pattern = engine.evaluate(
        Action(
            type="shell",
            command="python -m pytest",
            repository="company/library-core",
        )
    )
    missing = engine.evaluate(Action(type="shell", command="python -m pytest"))
    other = engine.evaluate(
        Action(
            type="shell",
            command="python -m pytest",
            repository="outside/project",
        )
    )

    assert (exact.effect, exact.rule_id) == ("allow", "allow-project-tests")
    assert (pattern.effect, pattern.rule_id) == ("allow", "allow-project-tests")
    assert (missing.effect, missing.rule_id) == ("approval", None)
    assert (other.effect, other.rule_id) == ("approval", None)


def test_repository_context_is_serialized_and_used_by_cli(tmp_path: Path, capsys) -> None:
    policy_path = _write_policy(tmp_path)

    code = cli_main(
        [
            "--policy",
            str(policy_path),
            "check",
            "--action",
            "shell",
            "--command",
            "python -m pytest",
            "--repository",
            "company/app",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["effect"] == "allow"
    assert payload["rule_id"] == "allow-project-tests"
    assert payload["action"]["repository"] == "company/app"


def test_protocol_accepts_repository_and_rejects_non_string(tmp_path: Path) -> None:
    policy = load_policy(_write_policy(tmp_path))
    engine = PolicyEngine(policy)

    response = evaluate_request(
        engine,
        policy.audit_path,
        {
            "version": 1,
            "id": "repository",
            "action": {
                "type": "shell",
                "command": "python -m pytest",
                "repository": "company/app",
            },
        },
    )

    assert response["decision"]["effect"] == "allow"
    assert response["decision"]["action"]["repository"] == "company/app"

    with pytest.raises(ProtocolError, match="action.repository must be a string or null"):
        parse_request(
            {
                "version": 1,
                "action": {"type": "shell", "repository": ["company/app"]},
            }
        )


def test_policy_suite_carries_repository_context(tmp_path: Path) -> None:
    policy = load_policy(_write_policy(tmp_path))
    suite_path = tmp_path / "kepenk.tests.yaml"
    suite_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "cases": [
                    {
                        "id": "allow-tests",
                        "action": {
                            "type": "shell",
                            "command": "python -m pytest",
                            "repository": "company/app",
                        },
                        "expect": {
                            "effect": "allow",
                            "rule_id": "allow-project-tests",
                        },
                    },
                    {
                        "id": "missing-context",
                        "action": {
                            "type": "shell",
                            "command": "python -m pytest",
                        },
                        "expect": {"effect": "approval", "rule_id": None},
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    suite = load_policy_test_suite(suite_path)
    results = evaluate_policy_test_suite(PolicyEngine(policy), suite)

    assert suite.cases[0].action.repository == "company/app"
    assert all(result.passed for result in results)


def test_github_action_and_mcp_carry_repository_context(tmp_path: Path) -> None:
    policy_path = _write_policy(tmp_path)
    output = tmp_path / "github-output.txt"
    summary = tmp_path / "summary.md"

    action_code = action_main(
        [
            "--mode",
            "check",
            "--policy",
            str(policy_path),
            "--action",
            "shell",
            "--command",
            "python -m pytest",
            "--repository",
            "company/app",
            "--github-output",
            str(output),
            "--github-step-summary",
            str(summary),
        ]
    )

    assert action_code == 0
    assert "Repository" in summary.read_text(encoding="utf-8")
    assert "company/app" in summary.read_text(encoding="utf-8")

    policy = load_policy(policy_path)
    response = evaluate_mcp_action(
        PolicyEngine(policy),
        policy.audit_path,
        action_type="shell",
        command="python -m pytest",
        repository="company/app",
    )
    assert response["ok"] is True
    assert response["decision"]["effect"] == "allow"
    assert response["decision"]["action"]["repository"] == "company/app"


def test_repository_context_validates_against_versioned_schemas() -> None:
    policy_schema = json.loads(
        (ROOT / "schemas/kepenk-policy-v1.schema.json").read_text(encoding="utf-8")
    )
    suite_schema = json.loads(
        (ROOT / "schemas/kepenk-tests-v1.schema.json").read_text(encoding="utf-8")
    )

    policy = {
        "version": 1,
        "default": "approval",
        "rules": [
            {
                "id": "allow-project-tests",
                "effect": "allow",
                "match": {
                    "action": "shell",
                    "repository_glob": "company/*",
                    "command_contains": "pytest",
                },
            }
        ],
    }
    suite = {
        "version": 1,
        "cases": [
            {
                "id": "project-tests",
                "action": {
                    "type": "shell",
                    "repository": "company/app",
                    "command": "pytest",
                },
                "expect": {"effect": "allow", "rule_id": "allow-project-tests"},
            }
        ],
    }

    Draft202012Validator(policy_schema).validate(policy)
    Draft202012Validator(suite_schema).validate(suite)
