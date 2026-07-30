from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

Effect = Literal["allow", "approval", "deny"]


@dataclass(frozen=True, slots=True)
class Action:
    type: str
    command: str | None = None
    path: str | None = None
    host: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "command": self.command,
            "path": self.path,
            "host": self.host,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class Rule:
    id: str
    effect: Effect
    reason: str
    match: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class Policy:
    version: int
    default: Effect
    rules: tuple[Rule, ...]
    audit_path: str


@dataclass(frozen=True, slots=True)
class Decision:
    effect: Effect
    reason: str
    rule_id: str | None
    action: Action

    @property
    def allowed(self) -> bool:
        return self.effect == "allow"

    @property
    def requires_approval(self) -> bool:
        return self.effect == "approval"

    @property
    def denied(self) -> bool:
        return self.effect == "deny"

    def to_dict(self) -> dict[str, Any]:
        return {
            "effect": self.effect,
            "reason": self.reason,
            "rule_id": self.rule_id,
            "action": self.action.to_dict(),
        }
