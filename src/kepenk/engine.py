from __future__ import annotations

import fnmatch
import re
from collections.abc import Iterable, Mapping
from typing import Any

from .errors import PolicyError
from .models import Action, Decision, Policy, Rule


class PolicyEngine:
    def __init__(self, policy: Policy):
        self.policy = policy

    def evaluate(self, action: Action) -> Decision:
        for rule in self.policy.rules:
            if self._matches(rule, action):
                return Decision(
                    effect=rule.effect,
                    reason=rule.reason,
                    rule_id=rule.id,
                    action=action,
                )
        return Decision(
            effect=self.policy.default,
            reason="No rule matched; policy default applied.",
            rule_id=None,
            action=action,
        )

    def _matches(self, rule: Rule, action: Action) -> bool:
        for key, expected in rule.match.items():
            if key == "action" and not self._value_matches(action.type, expected):
                return False
            if key == "command_regex" and not self._regex_matches(action.command, expected, rule.id):
                return False
            if key == "command_contains" and not self._contains_matches(action.command, expected):
                return False
            if key == "path_glob" and not self._glob_matches(action.path, expected):
                return False
            if key == "host_glob" and not self._glob_matches(action.host, expected):
                return False
            if key == "metadata" and not self._metadata_matches(action.metadata, expected):
                return False
        return True

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        if isinstance(value, list):
            return value
        return [value]

    def _value_matches(self, actual: str | None, expected: Any) -> bool:
        if actual is None:
            return False
        return any(actual == item for item in self._as_list(expected) if isinstance(item, str))

    def _regex_matches(self, actual: str | None, expected: Any, rule_id: str) -> bool:
        if actual is None:
            return False
        patterns = self._as_list(expected)
        for pattern in patterns:
            if not isinstance(pattern, str):
                raise PolicyError(f"rule {rule_id!r}: command_regex values must be strings")
            try:
                if re.search(pattern, actual):
                    return True
            except re.error as exc:
                raise PolicyError(f"rule {rule_id!r}: invalid command_regex: {exc}") from exc
        return False

    def _contains_matches(self, actual: str | None, expected: Any) -> bool:
        if actual is None:
            return False
        needles = [item for item in self._as_list(expected) if isinstance(item, str)]
        return bool(needles) and all(item in actual for item in needles)

    def _glob_matches(self, actual: str | None, expected: Any) -> bool:
        if actual is None:
            return False
        patterns: Iterable[Any] = self._as_list(expected)
        return any(fnmatch.fnmatch(actual, pattern) for pattern in patterns if isinstance(pattern, str))

    def _metadata_matches(self, actual: Mapping[str, Any], expected: Any) -> bool:
        if not isinstance(expected, dict):
            return False
        for key, expected_value in expected.items():
            if key not in actual:
                return False
            candidates = self._as_list(expected_value)
            if actual[key] not in candidates:
                return False
        return True
