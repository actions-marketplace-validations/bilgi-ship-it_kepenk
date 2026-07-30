from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "kepenk-policy-v1.schema.json"


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_policy_schema_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(_schema())


def test_representative_policy_passes_schema_validation() -> None:
    policy = {
        "version": 1,
        "default": "approval",
        "audit": {"path": ".kepenk/audit.jsonl"},
        "rules": [
            {
                "id": "allow-read-only-checks",
                "effect": "allow",
                "reason": "Read-only inspection is safe.",
                "match": {
                    "action": ["shell", "filesystem"],
                    "command_contains": ["git", "status"],
                    "command_regex": r"(^|\s)git\s+status(\s|$)",
                    "path_glob": ["src/**", "tests/**"],
                    "host_glob": "*.example.com",
                    "metadata": {
                        "environment": ["development", "test"],
                        "read_only": True,
                    },
                },
            }
        ],
    }

    Draft202012Validator(_schema()).validate(policy)


@pytest.mark.parametrize(
    "policy",
    [
        {"version": 2},
        {"version": 1, "default": "maybe"},
        {"version": 1, "unknown": True},
        {
            "version": 1,
            "rules": [{"id": "empty-match", "effect": "allow", "match": {}}],
        },
        {
            "version": 1,
            "rules": [
                {
                    "id": "unsupported-key",
                    "effect": "deny",
                    "match": {"magic": True},
                }
            ],
        },
    ],
)
def test_invalid_policies_fail_schema_validation(policy: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema()).validate(policy)
