from __future__ import annotations

import ipaddress
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import urlparse

from .errors import KepenkError

Classification = Literal["independent_adopter", "founding_team_pilot"]
IntegrationType = Literal["github_action", "pre_commit", "cli", "jsonl", "mcp", "other"]

_VALID_CLASSIFICATIONS: set[str] = {"independent_adopter", "founding_team_pilot"}
_VALID_INTEGRATIONS: set[str] = {
    "github_action",
    "pre_commit",
    "cli",
    "jsonl",
    "mcp",
    "other",
}
_ROOT_KEYS = {
    "version",
    "classification",
    "repository",
    "repository_url",
    "maintainer",
    "maintainer_url",
    "maintainer_consent",
    "integration",
    "kepenk_version",
    "evidence_url",
    "verified_on",
}
_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+$")
_MAINTAINER_PATTERN = re.compile(r"^[A-Za-z0-9_.@/-]+$")
_VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
_MAX_FILE_BYTES = 64 * 1024


class AdoptionEvidenceError(KepenkError):
    """Raised when an adoption evidence manifest is malformed or unsupported."""


@dataclass(frozen=True, slots=True)
class AdoptionEvidence:
    version: int
    classification: Classification
    repository: str
    repository_url: str
    maintainer: str
    maintainer_url: str
    maintainer_consent: bool
    integration: IntegrationType
    kepenk_version: str
    evidence_url: str
    verified_on: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "classification": self.classification,
            "repository": self.repository,
            "repository_url": self.repository_url,
            "maintainer": self.maintainer,
            "maintainer_url": self.maintainer_url,
            "maintainer_consent": self.maintainer_consent,
            "integration": self.integration,
            "kepenk_version": self.kepenk_version,
            "evidence_url": self.evidence_url,
            "verified_on": self.verified_on,
        }


def _mapping(value: Any, field_name: str) -> dict[Any, Any]:
    if not isinstance(value, dict):
        raise AdoptionEvidenceError(f"{field_name} must be a JSON object")
    return value


def _reject_unknown_fields(value: dict[Any, Any], allowed: set[str], field_name: str) -> None:
    unknown = {str(key) for key in value if key not in allowed}
    if unknown:
        names = ", ".join(sorted(unknown))
        raise AdoptionEvidenceError(f"{field_name} has unsupported fields: {names}")


def _require_fields(value: dict[Any, Any], required: set[str], field_name: str) -> None:
    missing = sorted(required - {key for key in value if isinstance(key, str)})
    if missing:
        names = ", ".join(missing)
        raise AdoptionEvidenceError(f"{field_name} is missing required fields: {names}")


def _non_empty_string(value: Any, field_name: str, *, maximum: int = 300) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdoptionEvidenceError(f"{field_name} must be a non-empty string")
    rendered = value.strip()
    if len(rendered) > maximum:
        raise AdoptionEvidenceError(f"{field_name} must be at most {maximum} characters")
    if any(ord(character) < 32 for character in rendered):
        raise AdoptionEvidenceError(f"{field_name} must not contain control characters")
    return rendered


def _public_https_url(value: Any, field_name: str) -> str:
    rendered = _non_empty_string(value, field_name, maximum=2048)
    parsed = urlparse(rendered)
    if parsed.scheme != "https" or not parsed.netloc or parsed.hostname is None:
        raise AdoptionEvidenceError(f"{field_name} must be an absolute HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise AdoptionEvidenceError(f"{field_name} must not contain URL credentials")
    if parsed.query or parsed.fragment:
        raise AdoptionEvidenceError(f"{field_name} must not contain a query or fragment")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in {"localhost", "localhost.localdomain"}:
        raise AdoptionEvidenceError(f"{field_name} must use a public host")
    if hostname.endswith((".local", ".internal", ".localhost")):
        raise AdoptionEvidenceError(f"{field_name} must use a public host")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise AdoptionEvidenceError(f"{field_name} must use a public host")
    return rendered.rstrip("/")


def _classification(value: Any) -> Classification:
    if not isinstance(value, str) or value not in _VALID_CLASSIFICATIONS:
        allowed = ", ".join(sorted(_VALID_CLASSIFICATIONS))
        raise AdoptionEvidenceError(f"classification must be one of: {allowed}")
    return cast(Classification, value)


def _integration(value: Any) -> IntegrationType:
    if not isinstance(value, str) or value not in _VALID_INTEGRATIONS:
        allowed = ", ".join(sorted(_VALID_INTEGRATIONS))
        raise AdoptionEvidenceError(f"integration must be one of: {allowed}")
    return cast(IntegrationType, value)


def _repository(value: Any) -> str:
    rendered = _non_empty_string(value, "repository", maximum=300)
    if not _REPOSITORY_PATTERN.fullmatch(rendered):
        raise AdoptionEvidenceError("repository must be a public owner/name-style slug")
    return rendered


def _maintainer(value: Any) -> str:
    rendered = _non_empty_string(value, "maintainer", maximum=100)
    if not _MAINTAINER_PATTERN.fullmatch(rendered):
        raise AdoptionEvidenceError("maintainer contains unsupported characters")
    return rendered


def _kepenk_version(value: Any) -> str:
    rendered = _non_empty_string(value, "kepenk_version", maximum=100)
    if not _VERSION_PATTERN.fullmatch(rendered):
        raise AdoptionEvidenceError("kepenk_version must be a tagged semantic version such as v0.3.0")
    return rendered


def _verified_on(value: Any) -> str:
    rendered = _non_empty_string(value, "verified_on", maximum=10)
    try:
        parsed = date.fromisoformat(rendered)
    except ValueError as exc:
        raise AdoptionEvidenceError("verified_on must be a valid YYYY-MM-DD date") from exc
    if parsed.isoformat() != rendered:
        raise AdoptionEvidenceError("verified_on must be a valid YYYY-MM-DD date")
    return rendered


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AdoptionEvidenceError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def load_adoption_evidence(path: str | Path) -> AdoptionEvidence:
    evidence_path = Path(path)
    try:
        raw_bytes = evidence_path.read_bytes()
    except FileNotFoundError as exc:
        raise AdoptionEvidenceError(f"adoption evidence not found: {evidence_path}") from exc
    if len(raw_bytes) > _MAX_FILE_BYTES:
        raise AdoptionEvidenceError(
            f"adoption evidence exceeds the {_MAX_FILE_BYTES}-byte limit"
        )
    try:
        rendered = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdoptionEvidenceError("adoption evidence must be UTF-8 JSON") from exc
    try:
        raw_value = json.loads(rendered, object_pairs_hook=_object_without_duplicates)
    except json.JSONDecodeError as exc:
        raise AdoptionEvidenceError(f"invalid JSON in {evidence_path}: {exc.msg}") from exc

    raw = _mapping(raw_value, "adoption evidence root")
    _reject_unknown_fields(raw, _ROOT_KEYS, "adoption evidence root")
    _require_fields(raw, _ROOT_KEYS, "adoption evidence root")
    if raw["version"] != 1:
        raise AdoptionEvidenceError("only adoption evidence version 1 is supported")

    repository = _repository(raw["repository"])
    repository_url = _public_https_url(raw["repository_url"], "repository_url")
    repository_path = urlparse(repository_url).path.strip("/")
    if not repository_path.endswith(repository):
        raise AdoptionEvidenceError("repository_url path must end with the repository slug")

    maintainer_consent = raw["maintainer_consent"]
    if maintainer_consent is not True:
        raise AdoptionEvidenceError("maintainer_consent must be true")

    evidence_url = _public_https_url(raw["evidence_url"], "evidence_url")
    if evidence_url != repository_url and not evidence_url.startswith(f"{repository_url}/"):
        raise AdoptionEvidenceError("evidence_url must point inside the declared repository URL")

    return AdoptionEvidence(
        version=1,
        classification=_classification(raw["classification"]),
        repository=repository,
        repository_url=repository_url,
        maintainer=_maintainer(raw["maintainer"]),
        maintainer_url=_public_https_url(raw["maintainer_url"], "maintainer_url"),
        maintainer_consent=True,
        integration=_integration(raw["integration"]),
        kepenk_version=_kepenk_version(raw["kepenk_version"]),
        evidence_url=evidence_url,
        verified_on=_verified_on(raw["verified_on"]),
    )
