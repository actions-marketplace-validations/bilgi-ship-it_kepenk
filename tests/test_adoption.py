from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from kepenk.adoption import AdoptionEvidenceError, load_adoption_evidence
from kepenk.cli import EXIT_USAGE, main


def _manifest() -> dict[str, Any]:
    return {
        "version": 1,
        "classification": "founding_team_pilot",
        "repository": "bilgi-ship-it/ustaca-ai",
        "repository_url": "https://github.com/bilgi-ship-it/ustaca-ai",
        "maintainer": "bilgi-ship-it",
        "maintainer_url": "https://github.com/bilgi-ship-it",
        "maintainer_consent": True,
        "integration": "github_action",
        "kepenk_version": "v0.3.0",
        "evidence_url": "https://github.com/bilgi-ship-it/ustaca-ai/tree/main/.kepenk",
        "verified_on": "2026-07-31",
    }


def _write_manifest(tmp_path: Path, manifest: dict[str, Any] | None = None) -> Path:
    path = tmp_path / "adoption.json"
    path.write_text(
        json.dumps(_manifest() if manifest is None else manifest),
        encoding="utf-8",
    )
    return path


def test_load_valid_adoption_evidence(tmp_path: Path) -> None:
    evidence = load_adoption_evidence(_write_manifest(tmp_path))

    assert evidence.version == 1
    assert evidence.classification == "founding_team_pilot"
    assert evidence.repository == "bilgi-ship-it/ustaca-ai"
    assert evidence.maintainer_consent is True
    assert evidence.integration == "github_action"
    assert evidence.kepenk_version == "v0.3.0"
    assert evidence.to_dict() == _manifest()


def test_provider_neutral_subgroup_repository_is_supported(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest.update(
        {
            "classification": "independent_adopter",
            "repository": "group/subgroup/project",
            "repository_url": "https://gitlab.example.org/group/subgroup/project",
            "maintainer": "group-maintainer",
            "maintainer_url": "https://gitlab.example.org/group-maintainer",
            "integration": "cli",
            "evidence_url": (
                "https://gitlab.example.org/group/subgroup/project/-/blob/main/.kepenk/adoption.json"
            ),
        }
    )

    evidence = load_adoption_evidence(_write_manifest(tmp_path, manifest))

    assert evidence.classification == "independent_adopter"
    assert evidence.repository == "group/subgroup/project"
    assert evidence.integration == "cli"


def test_validate_adoption_cli_does_not_load_policy(tmp_path: Path, capsys) -> None:
    evidence_path = _write_manifest(tmp_path)
    missing_policy = tmp_path / "missing-policy.yaml"

    assert (
        main(
            [
                "--policy",
                str(missing_policy),
                "validate-adoption",
                "--evidence",
                str(evidence_path),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "valid adoption evidence" in output
    assert "repository=bilgi-ship-it/ustaca-ai" in output
    assert "integration=github_action" in output


def test_validate_adoption_cli_json(tmp_path: Path, capsys) -> None:
    evidence_path = _write_manifest(tmp_path)

    assert main(["validate-adoption", "--evidence", str(evidence_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["classification"] == "founding_team_pilot"
    assert payload["repository"] == "bilgi-ship-it/ustaca-ai"
    assert payload["maintainer_consent"] is True


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("version", 2, "only adoption evidence version 1 is supported"),
        ("classification", "partner", "classification must be one of"),
        ("repository", "single-name", "owner/name-style slug"),
        ("repository_url", "http://github.com/bilgi-ship-it/ustaca-ai", "absolute HTTPS"),
        ("repository_url", "https://127.0.0.1/bilgi-ship-it/ustaca-ai", "public host"),
        ("maintainer", "bad handle!", "unsupported characters"),
        ("maintainer_url", "https://localhost/maintainer", "public host"),
        ("maintainer_consent", False, "maintainer_consent must be true"),
        ("integration", "hosted_magic", "integration must be one of"),
        ("kepenk_version", "main", "tagged semantic version"),
        ("evidence_url", "https://example.org/unrelated", "declared repository URL"),
        ("verified_on", "2026-02-30", "valid YYYY-MM-DD"),
    ],
)
def test_invalid_manifest_fields_fail_closed(
    tmp_path: Path,
    field: str,
    value: Any,
    message: str,
) -> None:
    manifest = _manifest()
    manifest[field] = value

    with pytest.raises(AdoptionEvidenceError, match=message):
        load_adoption_evidence(_write_manifest(tmp_path, manifest))


def test_repository_url_must_end_with_repository_slug(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest["repository_url"] = "https://github.com/another-owner/another-project"
    manifest["evidence_url"] = "https://github.com/another-owner/another-project/actions"

    with pytest.raises(AdoptionEvidenceError, match="path must end with the repository slug"):
        load_adoption_evidence(_write_manifest(tmp_path, manifest))


def test_unknown_missing_and_duplicate_fields_are_rejected(tmp_path: Path) -> None:
    unknown = _manifest()
    unknown["downloads"] = 100
    with pytest.raises(AdoptionEvidenceError, match="unsupported fields: downloads"):
        load_adoption_evidence(_write_manifest(tmp_path, unknown))

    missing = _manifest()
    del missing["evidence_url"]
    with pytest.raises(AdoptionEvidenceError, match="missing required fields: evidence_url"):
        load_adoption_evidence(_write_manifest(tmp_path, missing))

    duplicate_path = tmp_path / "duplicate.json"
    duplicate_path.write_text(
        '{"version":1,"version":1}',
        encoding="utf-8",
    )
    with pytest.raises(AdoptionEvidenceError, match="duplicate JSON field: version"):
        load_adoption_evidence(duplicate_path)


def test_url_credentials_queries_and_fragments_are_rejected(tmp_path: Path) -> None:
    for repository_url, message in (
        ("https://user:secret@github.com/bilgi-ship-it/ustaca-ai", "URL credentials"),
        ("https://github.com/bilgi-ship-it/ustaca-ai?private=true", "query or fragment"),
        ("https://github.com/bilgi-ship-it/ustaca-ai#secret", "query or fragment"),
    ):
        manifest = _manifest()
        manifest["repository_url"] = repository_url
        with pytest.raises(AdoptionEvidenceError, match=message):
            load_adoption_evidence(_write_manifest(tmp_path, manifest))


def test_oversized_and_non_utf8_files_are_rejected(tmp_path: Path) -> None:
    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b" " * (64 * 1024 + 1))
    with pytest.raises(AdoptionEvidenceError, match="65536-byte limit"):
        load_adoption_evidence(oversized)

    non_utf8 = tmp_path / "non-utf8.json"
    non_utf8.write_bytes(b"\xff\xfe")
    with pytest.raises(AdoptionEvidenceError, match="UTF-8 JSON"):
        load_adoption_evidence(non_utf8)


def test_cli_returns_usage_for_invalid_manifest(tmp_path: Path, capsys) -> None:
    manifest = _manifest()
    manifest["maintainer_consent"] = False
    evidence_path = _write_manifest(tmp_path, manifest)

    assert main(["validate-adoption", "--evidence", str(evidence_path)]) == EXIT_USAGE
    assert "maintainer_consent must be true" in capsys.readouterr().err
