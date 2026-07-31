from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

from .audit import read_verified_audit
from .errors import AuditError

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
_VALID_EFFECTS = {"allow", "approval", "deny"}


class SarifError(AuditError):
    """Raised when a verified audit event cannot be exported safely."""


def _required_mapping(value: Any, field: str, event_index: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SarifError(f"audit event {event_index}: {field} must be an object")
    return value


def _required_string(value: Any, field: str, event_index: int) -> str:
    if not isinstance(value, str) or not value:
        raise SarifError(f"audit event {event_index}: {field} must be a non-empty string")
    return value


def _optional_string(value: Any, field: str, event_index: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SarifError(f"audit event {event_index}: {field} must be a string or null")
    return value


def _safe_relative_uri(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.replace("\\", "/")
    if normalized.startswith(("/", "//")) or re.match(r"^[A-Za-z]:", normalized):
        return None
    if urlsplit(normalized).scheme:
        return None

    path = PurePosixPath(normalized)
    if any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def _validated_event(event: dict[str, Any], event_index: int) -> dict[str, Any]:
    decision = _required_mapping(event.get("decision"), "decision", event_index)
    effect = _required_string(decision.get("effect"), "decision.effect", event_index)
    if effect not in _VALID_EFFECTS:
        raise SarifError(
            f"audit event {event_index}: decision.effect must be allow, approval, or deny"
        )

    reason = _required_string(decision.get("reason"), "decision.reason", event_index)
    rule_id = _optional_string(decision.get("rule_id"), "decision.rule_id", event_index)
    action = _required_mapping(decision.get("action"), "decision.action", event_index)
    action_type = _required_string(
        action.get("type"), "decision.action.type", event_index
    )
    action_path = _optional_string(
        action.get("path"), "decision.action.path", event_index
    )
    outcome = _required_string(event.get("outcome"), "outcome", event_index)

    return {
        "effect": effect,
        "reason": reason,
        "rule_id": rule_id,
        "action_type": action_type,
        "safe_path": _safe_relative_uri(action_path),
        "outcome": outcome,
    }


def build_sarif(
    audit_path: str | Path,
    *,
    include_approval: bool = False,
) -> dict[str, Any]:
    events = read_verified_audit(audit_path)
    selected_effects = {"deny"}
    if include_approval:
        selected_effects.add("approval")

    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    for event_index, event in enumerate(events, start=1):
        validated = _validated_event(event, event_index)
        effect = validated["effect"]
        if effect not in selected_effects:
            continue

        rule_id = validated["rule_id"] or f"kepenk/default-{effect}"
        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {"text": validated["reason"]},
                "defaultConfiguration": {
                    "level": "error" if effect == "deny" else "warning"
                },
                "properties": {"tags": ["kepenk", effect]},
            }

        result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": "error" if effect == "deny" else "warning",
            "kind": "fail",
            "message": {"text": validated["reason"]},
            "properties": {
                "effect": effect,
                "actionType": validated["action_type"],
                "outcome": validated["outcome"],
                "auditEventIndex": event_index,
            },
        }
        if validated["safe_path"] is not None:
            result["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": validated["safe_path"]}
                    }
                }
            ]
        results.append(result)

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Kepenk",
                        "informationUri": "https://github.com/bilgi-ship-it/kepenk",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }


def write_sarif(
    audit_path: str | Path,
    output_path: str | Path | None = None,
    *,
    include_approval: bool = False,
) -> str:
    document = build_sarif(audit_path, include_approval=include_approval)
    rendered = json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output_path is not None:
        selected = Path(output_path)
        try:
            selected.parent.mkdir(parents=True, exist_ok=True)
            selected.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            raise SarifError(f"cannot write SARIF output {selected}: {exc}") from exc
    return rendered
