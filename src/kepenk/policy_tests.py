from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

from .engine import PolicyEngine
from .errors import KepenkError
from .models import Action, Decision, Effect

_VALID_EFFECTS: set[str] = {"allow", "approval", "deny"}
_ROOT_KEYS = {"version", "cases"}
_CASE_KEYS = {"id", "action", "expect"}
_ACTION_KEYS = {"type", "command", "path", "host", "metadata"}
_EXPECTATION_KEYS = {"effect", "rule_id"}


class PolicyTestError(KepenkError):
    """Raised when a policy test suite is missing, malformed, or unsupported."""


@dataclass(frozen=True, slots=True)
class ExpectedDecision:
    effect: Effect
    rule_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {"effect": self.effect, "rule_id": self.rule_id}


@dataclass(frozen=True, slots=True)
class PolicyTestCase:
    id: str
    action: Action
    expected: ExpectedDecision


@dataclass(frozen=True, slots=True)
class PolicyTestSuite:
    version: int
    cases: tuple[PolicyTestCase, ...]


@dataclass(frozen=True, slots=True)
class PolicyTestResult:
    case: PolicyTestCase
    decision: Decision
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.case.id,
            "passed": self.passed,
            "action": self.case.action.to_dict(),
            "expected": self.case.expected.to_dict(),
            "actual": {
                "effect": self.decision.effect,
                "rule_id": self.decision.rule_id,
                "reason": self.decision.reason,
            },
        }


def _mapping(value: Any, field_name: str) -> dict[Any, Any]:
    if not isinstance(value, dict):
        raise PolicyTestError(f"{field_name} must be a mapping")
    return value


def _reject_unknown_fields(
    value: dict[Any, Any], allowed: set[str], field_name: str
) -> None:
    unknown = {str(key) for key in value if key not in allowed}
    if unknown:
        names = ", ".join(sorted(unknown))
        raise PolicyTestError(f"{field_name} has unsupported fields: {names}")


def _non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PolicyTestError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise PolicyTestError(f"{field_name} must be a string or null")
    return value


def _effect(value: Any, field_name: str) -> Effect:
    if not isinstance(value, str) or value not in _VALID_EFFECTS:
        raise PolicyTestError(f"{field_name} must be one of: allow, approval, deny")
    return cast(Effect, value)


def _json_value(value: Any, field_name: str) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [
            _json_value(item, f"{field_name}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise PolicyTestError(f"{field_name} keys must be non-empty strings")
            result[key] = _json_value(item, f"{field_name}.{key}")
        return result
    raise PolicyTestError(f"{field_name} must contain only JSON-compatible values")


def _load_action(value: Any, case_id: str) -> Action:
    field_name = f"case {case_id!r} action"
    raw = _mapping(value, field_name)
    _reject_unknown_fields(raw, _ACTION_KEYS, field_name)
    action_type = _non_empty_string(raw.get("type"), f"{field_name}.type")

    raw_metadata = raw.get("metadata", {})
    if not isinstance(raw_metadata, dict):
        raise PolicyTestError(f"{field_name}.metadata must be a mapping")
    metadata = _json_value(raw_metadata, f"{field_name}.metadata")
    if not isinstance(metadata, dict):
        raise AssertionError("metadata validation must return a mapping")

    return Action(
        type=action_type,
        command=_optional_string(raw.get("command"), f"{field_name}.command"),
        path=_optional_string(raw.get("path"), f"{field_name}.path"),
        host=_optional_string(raw.get("host"), f"{field_name}.host"),
        metadata=metadata,
    )


def _load_expectation(value: Any, case_id: str) -> ExpectedDecision:
    field_name = f"case {case_id!r} expect"
    raw = _mapping(value, field_name)
    _reject_unknown_fields(raw, _EXPECTATION_KEYS, field_name)
    for required in ("effect", "rule_id"):
        if required not in raw:
            raise PolicyTestError(f"{field_name}.{required} is required")

    raw_rule_id = raw["rule_id"]
    rule_id = None if raw_rule_id is None else _non_empty_string(
        raw_rule_id, f"{field_name}.rule_id"
    )
    return ExpectedDecision(
        effect=_effect(raw["effect"], f"{field_name}.effect"),
        rule_id=rule_id,
    )


def load_policy_test_suite(path: str | Path) -> PolicyTestSuite:
    suite_path = Path(path)
    try:
        raw_value = yaml.safe_load(suite_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PolicyTestError(f"policy test suite not found: {suite_path}") from exc
    except yaml.YAMLError as exc:
        raise PolicyTestError(f"invalid YAML in {suite_path}: {exc}") from exc

    raw = _mapping(raw_value, "policy test suite root")
    _reject_unknown_fields(raw, _ROOT_KEYS, "policy test suite root")
    if raw.get("version") != 1:
        raise PolicyTestError("only policy test suite version 1 is supported")

    raw_cases = raw.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise PolicyTestError("cases must be a non-empty list")

    seen_ids: set[str] = set()
    cases: list[PolicyTestCase] = []
    for index, raw_case_value in enumerate(raw_cases):
        raw_case = _mapping(raw_case_value, f"case at index {index}")
        _reject_unknown_fields(raw_case, _CASE_KEYS, f"case at index {index}")
        case_id = _non_empty_string(raw_case.get("id"), f"cases[{index}].id")
        if case_id in seen_ids:
            raise PolicyTestError(f"duplicate policy test case id: {case_id}")
        seen_ids.add(case_id)
        if "action" not in raw_case:
            raise PolicyTestError(f"case {case_id!r} action is required")
        if "expect" not in raw_case:
            raise PolicyTestError(f"case {case_id!r} expect is required")
        cases.append(
            PolicyTestCase(
                id=case_id,
                action=_load_action(raw_case["action"], case_id),
                expected=_load_expectation(raw_case["expect"], case_id),
            )
        )

    return PolicyTestSuite(version=1, cases=tuple(cases))


def evaluate_policy_test_suite(
    engine: PolicyEngine, suite: PolicyTestSuite
) -> tuple[PolicyTestResult, ...]:
    results: list[PolicyTestResult] = []
    for case in suite.cases:
        decision = engine.evaluate(case.action)
        passed = (
            decision.effect == case.expected.effect
            and decision.rule_id == case.expected.rule_id
        )
        results.append(PolicyTestResult(case=case, decision=decision, passed=passed))
    return tuple(results)
