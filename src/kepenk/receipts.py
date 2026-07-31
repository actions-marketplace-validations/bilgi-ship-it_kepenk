from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .engine import PolicyEngine
from .errors import KepenkError
from .models import Action, Policy

RECEIPT_VERSION = 1
RECEIPT_ALGORITHM = "Ed25519"
DEFAULT_RECEIPT_LIFETIME_SECONDS = 600
MAX_RECEIPT_LIFETIME_SECONDS = 86_400
MAX_FUTURE_CLOCK_SKEW_SECONDS = 60
MAX_RECEIPT_FILE_BYTES = 1_048_576

_RECEIPT_FIELDS = {"version", "algorithm", "key_id", "payload", "signature"}
_PAYLOAD_FIELDS = {
    "issued_at",
    "expires_at",
    "nonce",
    "policy_sha256",
    "decision",
    "action",
}
_DECISION_FIELDS = {"effect", "reason", "rule_id"}
_ACTION_FIELDS = {"type", "command", "path", "host", "repository", "metadata"}
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_KEY_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_BASE64URL = re.compile(r"^[A-Za-z0-9_-]+$")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class ReceiptError(KepenkError):
    """Raised when an approval receipt or signing key fails closed."""


def _canonical_bytes(value: Any, field: str) -> bytes:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ReceiptError(f"{field} must be canonical JSON-compatible data: {exc}") from exc
    return rendered.encode("utf-8")


def _exact_fields(value: dict[str, Any], expected: set[str], field: str) -> None:
    missing = expected - set(value)
    unknown = set(value) - expected
    if missing:
        raise ReceiptError(f"{field} is missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ReceiptError(f"{field} has unsupported fields: {', '.join(sorted(unknown))}")


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReceiptError(f"{field} must be an object")
    for key in value:
        if not isinstance(key, str):
            raise ReceiptError(f"{field} field names must be strings")
    return value


def _required_string(value: Any, field: str, *, maximum: int | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReceiptError(f"{field} must be a non-empty string")
    if maximum is not None and len(value) > maximum:
        raise ReceiptError(f"{field} must be at most {maximum} characters")
    return value


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ReceiptError(f"{field} must be a string or null")
    return value


def _utc_now(value: datetime | None = None) -> datetime:
    selected = value or datetime.now(UTC)
    if selected.tzinfo is None or selected.utcoffset() is None:
        raise ReceiptError("time value must be timezone-aware")
    return selected.astimezone(UTC).replace(microsecond=0)


def _format_timestamp(value: datetime) -> str:
    return _utc_now(value).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any, field: str) -> datetime:
    text = _required_string(value, field)
    if not _TIMESTAMP.fullmatch(text):
        raise ReceiptError(f"{field} must be UTC in YYYY-MM-DDTHH:MM:SSZ format")
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise ReceiptError(f"{field} is not a valid UTC timestamp") from exc


def canonical_policy(policy: Policy) -> dict[str, Any]:
    value = {
        "version": policy.version,
        "default": policy.default,
        "audit_path": policy.audit_path,
        "rules": [
            {
                "id": rule.id,
                "effect": rule.effect,
                "reason": rule.reason,
                "match": dict(rule.match),
            }
            for rule in policy.rules
        ],
    }
    _canonical_bytes(value, "policy")
    return value


def policy_sha256(policy: Policy) -> str:
    return hashlib.sha256(_canonical_bytes(canonical_policy(policy), "policy")).hexdigest()


def public_key_id(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def load_receipt_private_key(path: str | Path) -> Ed25519PrivateKey:
    selected = Path(path)
    try:
        data = selected.read_bytes()
        key = serialization.load_pem_private_key(data, password=None)
    except FileNotFoundError as exc:
        raise ReceiptError(f"private key file not found: {selected}") from exc
    except (OSError, ValueError, TypeError, UnsupportedAlgorithm) as exc:
        raise ReceiptError(f"cannot load unencrypted PEM private key {selected}: {exc}") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise ReceiptError(f"private key is not Ed25519: {selected}")
    return key


def load_receipt_public_key(path: str | Path) -> Ed25519PublicKey:
    selected = Path(path)
    try:
        data = selected.read_bytes()
        key = serialization.load_pem_public_key(data)
    except FileNotFoundError as exc:
        raise ReceiptError(f"public key file not found: {selected}") from exc
    except (OSError, ValueError, TypeError, UnsupportedAlgorithm) as exc:
        raise ReceiptError(f"cannot load PEM public key {selected}: {exc}") from exc
    if not isinstance(key, Ed25519PublicKey):
        raise ReceiptError(f"public key is not Ed25519: {selected}")
    return key


def _write_bytes(path: Path, data: bytes, *, mode: int, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT
    flags |= os.O_TRUNC if force else os.O_EXCL
    try:
        descriptor = os.open(path, flags, mode)
    except FileExistsError as exc:
        raise ReceiptError(f"file already exists: {path}") from exc
    except OSError as exc:
        raise ReceiptError(f"cannot create file {path}: {exc}") from exc

    try:
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
    except OSError as exc:
        raise ReceiptError(f"cannot write file {path}: {exc}") from exc


def generate_receipt_key_pair(
    private_key_path: str | Path,
    public_key_path: str | Path,
    *,
    force: bool = False,
) -> str:
    private_path = Path(private_key_path)
    public_path = Path(public_key_path)
    if private_path.resolve() == public_path.resolve():
        raise ReceiptError("private and public key paths must be different")
    if not force:
        for selected in (private_path, public_path):
            if selected.exists():
                raise ReceiptError(f"file already exists: {selected}")

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    private_created = False
    try:
        _write_bytes(private_path, private_bytes, mode=0o600, force=force)
        private_created = True
        _write_bytes(public_path, public_bytes, mode=0o644, force=force)
    except ReceiptError:
        if private_created and not force:
            try:
                private_path.unlink()
            except OSError:
                pass
        raise
    return public_key_id(public_key)


def _signature_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _signature_decode(value: Any) -> bytes:
    text = _required_string(value, "receipt.signature")
    if "=" in text or not _BASE64URL.fullmatch(text):
        raise ReceiptError("receipt.signature must be unpadded base64url")
    padding = "=" * (-len(text) % 4)
    try:
        decoded = base64.b64decode(text + padding, altchars=b"-_", validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ReceiptError("receipt.signature is not valid base64url") from exc
    if len(decoded) != 64:
        raise ReceiptError("receipt.signature must decode to 64 bytes")
    return decoded


def _receipt_action(value: Any) -> dict[str, Any]:
    action = _mapping(value, "receipt.payload.action")
    _exact_fields(action, _ACTION_FIELDS, "receipt.payload.action")
    _required_string(action.get("type"), "receipt.payload.action.type")
    for field in ("command", "path", "host", "repository"):
        _optional_string(action.get(field), f"receipt.payload.action.{field}")
    metadata = _mapping(action.get("metadata"), "receipt.payload.action.metadata")
    _canonical_bytes(metadata, "receipt.payload.action.metadata")
    return action


def _receipt_decision(value: Any) -> dict[str, Any]:
    decision = _mapping(value, "receipt.payload.decision")
    _exact_fields(decision, _DECISION_FIELDS, "receipt.payload.decision")
    if decision.get("effect") != "approval":
        raise ReceiptError("receipt.payload.decision.effect must be approval")
    _required_string(decision.get("reason"), "receipt.payload.decision.reason")
    _optional_string(decision.get("rule_id"), "receipt.payload.decision.rule_id")
    return decision


def _parse_receipt(value: Any) -> dict[str, Any]:
    receipt = _mapping(value, "receipt")
    _exact_fields(receipt, _RECEIPT_FIELDS, "receipt")
    if receipt.get("version") != RECEIPT_VERSION or isinstance(receipt.get("version"), bool):
        raise ReceiptError(f"receipt.version must be {RECEIPT_VERSION}")
    if receipt.get("algorithm") != RECEIPT_ALGORITHM:
        raise ReceiptError(f"receipt.algorithm must be {RECEIPT_ALGORITHM}")

    key_id = _required_string(receipt.get("key_id"), "receipt.key_id")
    if not _KEY_ID.fullmatch(key_id):
        raise ReceiptError("receipt.key_id must be sha256 followed by 64 lowercase hex characters")

    payload = _mapping(receipt.get("payload"), "receipt.payload")
    _exact_fields(payload, _PAYLOAD_FIELDS, "receipt.payload")
    _parse_timestamp(payload.get("issued_at"), "receipt.payload.issued_at")
    _parse_timestamp(payload.get("expires_at"), "receipt.payload.expires_at")
    _required_string(payload.get("nonce"), "receipt.payload.nonce", maximum=512)
    digest = _required_string(payload.get("policy_sha256"), "receipt.payload.policy_sha256")
    if not _HEX_64.fullmatch(digest):
        raise ReceiptError("receipt.payload.policy_sha256 must be 64 lowercase hex characters")
    _receipt_decision(payload.get("decision"))
    _receipt_action(payload.get("action"))
    _signature_decode(receipt.get("signature"))
    _canonical_bytes(
        {
            "version": receipt["version"],
            "algorithm": receipt["algorithm"],
            "key_id": receipt["key_id"],
            "payload": receipt["payload"],
        },
        "receipt signed envelope",
    )
    return receipt


def create_approval_receipt(
    policy: Policy,
    action: Action,
    private_key: Ed25519PrivateKey,
    *,
    nonce: str,
    expires_in: int = DEFAULT_RECEIPT_LIFETIME_SECONDS,
    now: datetime | None = None,
) -> dict[str, Any]:
    selected_nonce = _required_string(nonce, "nonce", maximum=512)
    if isinstance(expires_in, bool) or not isinstance(expires_in, int):
        raise ReceiptError("expires_in must be an integer number of seconds")
    if expires_in <= 0 or expires_in > MAX_RECEIPT_LIFETIME_SECONDS:
        raise ReceiptError(
            f"expires_in must be between 1 and {MAX_RECEIPT_LIFETIME_SECONDS} seconds"
        )

    decision = PolicyEngine(policy).evaluate(action)
    if decision.effect != "approval":
        raise ReceiptError(
            f"approval receipts require an approval decision; got {decision.effect}"
        )

    issued_at = _utc_now(now)
    expires_at = issued_at + timedelta(seconds=expires_in)
    key_id = public_key_id(private_key.public_key())
    payload = {
        "issued_at": _format_timestamp(issued_at),
        "expires_at": _format_timestamp(expires_at),
        "nonce": selected_nonce,
        "policy_sha256": policy_sha256(policy),
        "decision": {
            "effect": decision.effect,
            "reason": decision.reason,
            "rule_id": decision.rule_id,
        },
        "action": action.to_dict(),
    }
    envelope = {
        "version": RECEIPT_VERSION,
        "algorithm": RECEIPT_ALGORITHM,
        "key_id": key_id,
        "payload": payload,
    }
    signature = private_key.sign(_canonical_bytes(envelope, "receipt signed envelope"))
    receipt = {**envelope, "signature": _signature_encode(signature)}
    return _parse_receipt(receipt)


def receipt_sha256(receipt: dict[str, Any]) -> str:
    parsed = _parse_receipt(receipt)
    return hashlib.sha256(_canonical_bytes(parsed, "receipt")).hexdigest()


def verify_approval_receipt(
    receipt: dict[str, Any],
    policy: Policy,
    action: Action,
    public_key: Ed25519PublicKey,
    *,
    nonce: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    parsed = _parse_receipt(receipt)
    expected_nonce = _required_string(nonce, "nonce", maximum=512)
    payload = _mapping(parsed["payload"], "receipt.payload")

    expected_key_id = public_key_id(public_key)
    if parsed["key_id"] != expected_key_id:
        raise ReceiptError("receipt key ID does not match the expected public key")

    envelope = {
        "version": parsed["version"],
        "algorithm": parsed["algorithm"],
        "key_id": parsed["key_id"],
        "payload": parsed["payload"],
    }
    signature = _signature_decode(parsed["signature"])
    try:
        public_key.verify(signature, _canonical_bytes(envelope, "receipt signed envelope"))
    except InvalidSignature as exc:
        raise ReceiptError("receipt signature is invalid") from exc

    issued_at = _parse_timestamp(payload["issued_at"], "receipt.payload.issued_at")
    expires_at = _parse_timestamp(payload["expires_at"], "receipt.payload.expires_at")
    selected_now = _utc_now(now)
    if expires_at <= issued_at:
        raise ReceiptError("receipt expiry must be later than issuance")
    if (expires_at - issued_at).total_seconds() > MAX_RECEIPT_LIFETIME_SECONDS:
        raise ReceiptError("receipt lifetime exceeds the supported maximum")
    if issued_at > selected_now + timedelta(seconds=MAX_FUTURE_CLOCK_SKEW_SECONDS):
        raise ReceiptError("receipt was issued too far in the future")
    if selected_now >= expires_at:
        raise ReceiptError("receipt has expired")

    if payload["nonce"] != expected_nonce:
        raise ReceiptError("receipt nonce does not match the expected replay context")
    if payload["policy_sha256"] != policy_sha256(policy):
        raise ReceiptError("receipt policy digest does not match the current policy")

    expected_action = action.to_dict()
    _canonical_bytes(expected_action, "expected action")
    if payload["action"] != expected_action:
        raise ReceiptError("receipt action does not match the expected structured action")

    decision = PolicyEngine(policy).evaluate(action)
    if decision.effect != "approval":
        raise ReceiptError(
            f"current policy decision must be approval; got {decision.effect}"
        )
    expected_decision = {
        "effect": decision.effect,
        "reason": decision.reason,
        "rule_id": decision.rule_id,
    }
    if payload["decision"] != expected_decision:
        raise ReceiptError("receipt decision does not match the current policy decision")

    return {
        "valid": True,
        "version": parsed["version"],
        "algorithm": parsed["algorithm"],
        "key_id": parsed["key_id"],
        "issued_at": payload["issued_at"],
        "expires_at": payload["expires_at"],
        "nonce": payload["nonce"],
        "policy_sha256": payload["policy_sha256"],
        "receipt_sha256": receipt_sha256(parsed),
        "decision": payload["decision"],
        "action": payload["action"],
    }


def load_receipt(path: str | Path) -> dict[str, Any]:
    selected = Path(path)
    try:
        if selected.stat().st_size > MAX_RECEIPT_FILE_BYTES:
            raise ReceiptError(
                f"receipt file exceeds {MAX_RECEIPT_FILE_BYTES} bytes: {selected}"
            )
        raw = json.loads(selected.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReceiptError(f"receipt file not found: {selected}") from exc
    except ReceiptError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReceiptError(f"cannot read receipt {selected}: {exc}") from exc
    return _parse_receipt(raw)


def render_receipt(receipt: dict[str, Any]) -> str:
    parsed = _parse_receipt(receipt)
    return json.dumps(parsed, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_receipt(
    receipt: dict[str, Any],
    path: str | Path,
    *,
    force: bool = False,
) -> None:
    _write_bytes(
        Path(path),
        render_receipt(receipt).encode("utf-8"),
        mode=0o600,
        force=force,
    )
