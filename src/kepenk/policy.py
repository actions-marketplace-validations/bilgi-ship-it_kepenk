from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import PolicyError
from .models import Effect, Policy, Rule

VALID_EFFECTS: set[str] = {"allow", "approval", "deny"}
VALID_MATCH_KEYS: set[str] = {
    "action",
    "command_regex",
    "command_contains",
    "path_glob",
    "host_glob",
    "repository_glob",
    "metadata",
}


def _effect(value: Any, field_name: str) -> Effect:
    if not isinstance(value, str) or value not in VALID_EFFECTS:
        raise PolicyError(f"{field_name} must be one of: allow, approval, deny")
    return value  # type: ignore[return-value]


def _non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PolicyError(f"{field_name} must be a non-empty string")
    return value.strip()


def _validate_match(value: Any, rule_id: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        raise PolicyError(f"rule {rule_id!r}: match must be a non-empty mapping")
    unknown = set(value) - VALID_MATCH_KEYS
    if unknown:
        names = ", ".join(sorted(unknown))
        raise PolicyError(f"rule {rule_id!r}: unsupported match keys: {names}")
    return value


def load_policy(path: str | Path) -> Policy:
    policy_path = Path(path)
    try:
        raw = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PolicyError(f"policy file not found: {policy_path}") from exc
    except yaml.YAMLError as exc:
        raise PolicyError(f"invalid YAML in {policy_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise PolicyError("policy root must be a mapping")
    if raw.get("version") != 1:
        raise PolicyError("only policy version 1 is supported")

    default = _effect(raw.get("default", "approval"), "default")
    raw_rules = raw.get("rules", [])
    if not isinstance(raw_rules, list):
        raise PolicyError("rules must be a list")

    seen_ids: set[str] = set()
    rules: list[Rule] = []
    for index, raw_rule in enumerate(raw_rules):
        if not isinstance(raw_rule, dict):
            raise PolicyError(f"rule at index {index} must be a mapping")
        rule_id = _non_empty_string(raw_rule.get("id"), f"rules[{index}].id")
        if rule_id in seen_ids:
            raise PolicyError(f"duplicate rule id: {rule_id}")
        seen_ids.add(rule_id)
        effect = _effect(raw_rule.get("effect"), f"rule {rule_id!r} effect")
        reason = _non_empty_string(
            raw_rule.get("reason", f"Matched policy rule {rule_id}"),
            f"rule {rule_id!r} reason",
        )
        match = _validate_match(raw_rule.get("match"), rule_id)
        rules.append(Rule(id=rule_id, effect=effect, reason=reason, match=match))

    audit = raw.get("audit", {})
    if audit is None:
        audit = {}
    if not isinstance(audit, dict):
        raise PolicyError("audit must be a mapping")
    audit_path = audit.get("path", ".kepenk/audit.jsonl")
    audit_path = _non_empty_string(audit_path, "audit.path")

    return Policy(version=1, default=default, rules=tuple(rules), audit_path=audit_path)
