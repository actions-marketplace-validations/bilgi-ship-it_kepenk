from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, TextIO

from .audit import append_decision
from .engine import PolicyEngine
from .errors import KepenkError
from .models import Action

PROTOCOL_VERSION = 1
EXIT_PROTOCOL_ERROR = 64
_ALLOWED_ACTION_FIELDS = {"type", "command", "path", "host", "repository", "metadata"}


class ProtocolError(ValueError):
    """Raised when a protocol request cannot be evaluated safely."""


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProtocolError(f"action.{field} must be a string or null")
    return value


def _request_id(payload: Any) -> str | int | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get("id")
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def parse_request(payload: Any) -> tuple[str | int | None, Action]:
    if not isinstance(payload, dict):
        raise ProtocolError("request must be a JSON object")

    version = payload.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version != PROTOCOL_VERSION:
        raise ProtocolError(f"version must be {PROTOCOL_VERSION}")

    request_id = payload.get("id")
    if request_id is not None and not isinstance(request_id, str):
        if not isinstance(request_id, int) or isinstance(request_id, bool):
            raise ProtocolError("id must be a string, integer, or null")

    raw_action = payload.get("action")
    if not isinstance(raw_action, dict):
        raise ProtocolError("action must be a JSON object")

    action_fields: set[str] = set()
    for key in raw_action:
        if not isinstance(key, str):
            raise ProtocolError("action field names must be strings")
        action_fields.add(key)

    unknown = sorted(action_fields - _ALLOWED_ACTION_FIELDS)
    if unknown:
        names = ", ".join(unknown)
        raise ProtocolError(f"unsupported action fields: {names}")

    action_type = raw_action.get("type")
    if not isinstance(action_type, str) or not action_type.strip():
        raise ProtocolError("action.type must be a non-empty string")

    raw_metadata = raw_action.get("metadata", {})
    if raw_metadata is None:
        raw_metadata = {}
    if not isinstance(raw_metadata, Mapping):
        raise ProtocolError("action.metadata must be a JSON object")

    metadata: dict[str, Any] = {}
    for key, value in raw_metadata.items():
        if not isinstance(key, str):
            raise ProtocolError("action.metadata keys must be strings")
        metadata[key] = value

    return request_id, Action(
        type=action_type.strip(),
        command=_optional_string(raw_action.get("command"), "command"),
        path=_optional_string(raw_action.get("path"), "path"),
        host=_optional_string(raw_action.get("host"), "host"),
        repository=_optional_string(raw_action.get("repository"), "repository"),
        metadata=metadata,
    )


def _error_response(
    request_id: str | int | None,
    *,
    code: str,
    message: str,
) -> dict[str, Any]:
    return {
        "version": PROTOCOL_VERSION,
        "id": request_id,
        "ok": False,
        "error": {"code": code, "message": message},
    }


def evaluate_request(
    engine: PolicyEngine,
    audit_path: str,
    payload: Any,
) -> dict[str, Any]:
    request_id, action = parse_request(payload)
    decision = engine.evaluate(action)
    append_decision(audit_path, decision, outcome="protocol_checked")
    return {
        "version": PROTOCOL_VERSION,
        "id": request_id,
        "ok": True,
        "decision": decision.to_dict(),
    }


def run_protocol(
    engine: PolicyEngine,
    audit_path: str,
    input_stream: TextIO,
    output_stream: TextIO,
) -> int:
    had_error = False
    for line_number, line in enumerate(input_stream, start=1):
        if not line.strip():
            continue
        payload: Any = None
        try:
            payload = json.loads(line)
            response = evaluate_request(engine, audit_path, payload)
        except json.JSONDecodeError as exc:
            had_error = True
            response = _error_response(
                None,
                code="invalid_json",
                message=f"line {line_number}: {exc.msg}",
            )
        except ProtocolError as exc:
            had_error = True
            response = _error_response(
                _request_id(payload),
                code="invalid_request",
                message=f"line {line_number}: {exc}",
            )
        except KepenkError as exc:
            had_error = True
            response = _error_response(
                _request_id(payload),
                code="evaluation_error",
                message=f"line {line_number}: {exc}",
            )
        output_stream.write(json.dumps(response, ensure_ascii=False, sort_keys=True) + "\n")
        output_stream.flush()
    return EXIT_PROTOCOL_ERROR if had_error else 0
