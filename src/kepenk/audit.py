from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .errors import AuditError
from .models import Decision

GENESIS_HASH = "0" * 64


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _hash_event(payload: dict[str, Any], previous_hash: str) -> str:
    digest = hashlib.sha256()
    digest.update(previous_hash.encode("ascii"))
    digest.update(b"\n")
    digest.update(_canonical(payload))
    return digest.hexdigest()


def _last_hash(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return GENESIS_HASH
    try:
        last_non_empty = ""
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last_non_empty = line.strip()
        if not last_non_empty:
            return GENESIS_HASH
        event = json.loads(last_non_empty)
        value = event.get("event_hash")
        if not isinstance(value, str) or len(value) != 64:
            raise AuditError("last audit entry has no valid event_hash")
        return value
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read audit log {path}: {exc}") from exc


def append_decision(path: str | Path, decision: Decision, *, outcome: str) -> dict[str, Any]:
    audit_path = Path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = _last_hash(audit_path)
    payload: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "decision": decision.to_dict(),
        "outcome": outcome,
        "previous_hash": previous_hash,
    }
    payload["event_hash"] = _hash_event(payload, previous_hash)
    try:
        with audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError as exc:
        raise AuditError(f"cannot append audit log {audit_path}: {exc}") from exc
    return payload


def read_verified_audit(path: str | Path) -> tuple[dict[str, Any], ...]:
    """Read an audit log while verifying every hash link and event hash."""
    audit_path = Path(path)
    if not audit_path.exists():
        raise AuditError("audit file does not exist")

    previous_hash = GENESIS_HASH
    events: list[dict[str, Any]] = []
    try:
        with audit_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                raw_event = json.loads(line)
                if not isinstance(raw_event, dict):
                    raise AuditError(f"audit event at line {line_number} must be an object")

                event: dict[str, Any] = dict(raw_event)
                stored_hash = event.pop("event_hash", None)
                linked_hash = event.get("previous_hash")
                if linked_hash != previous_hash:
                    raise AuditError(f"broken previous_hash at line {line_number}")
                expected_hash = _hash_event(event, previous_hash)
                if stored_hash != expected_hash:
                    raise AuditError(f"invalid event_hash at line {line_number}")

                raw_event["event_hash"] = stored_hash
                events.append(raw_event)
                previous_hash = expected_hash
    except AuditError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read audit log {audit_path}: {exc}") from exc

    return tuple(events)


def verify_audit(path: str | Path) -> tuple[bool, int, str | None]:
    audit_path = Path(path)
    if not audit_path.exists():
        return False, 0, "audit file does not exist"
    previous_hash = GENESIS_HASH
    count = 0
    try:
        with audit_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                event = json.loads(line)
                if not isinstance(event, dict):
                    return False, count, f"audit event at line {line_number} must be an object"
                stored_hash = event.pop("event_hash", None)
                linked_hash = event.get("previous_hash")
                if linked_hash != previous_hash:
                    return False, count, f"broken previous_hash at line {line_number}"
                expected_hash = _hash_event(event, previous_hash)
                if stored_hash != expected_hash:
                    return False, count, f"invalid event_hash at line {line_number}"
                previous_hash = expected_hash
                count += 1
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, count, str(exc)
    return True, count, None
