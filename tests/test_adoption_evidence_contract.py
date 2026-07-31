from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from kepenk.adoption import load_adoption_evidence

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/kepenk-adoption-evidence-v1.schema.json"
EXAMPLE_PATH = ROOT / "examples/adoption/ustaca-ai.json"

EXPECTED_FIELDS = {
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


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_checked_in_example_matches_schema_and_runtime() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    assert list(validator.iter_errors(example)) == []
    evidence = load_adoption_evidence(EXAMPLE_PATH)
    assert evidence.to_dict() == example
    assert set(schema["required"]) == EXPECTED_FIELDS
    assert set(schema["properties"]) == EXPECTED_FIELDS
    assert schema["additionalProperties"] is False


def test_schema_rejects_unknown_fields_and_missing_consent() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    with_unknown = {**example, "downloads": 10}
    assert list(validator.iter_errors(with_unknown))

    without_consent = dict(example)
    without_consent["maintainer_consent"] = False
    assert list(validator.iter_errors(without_consent))


def test_adoption_evidence_docs_state_offline_and_human_review_boundaries() -> None:
    guide = _read("docs/adoption-evidence.md")
    readme = _read("README.md")
    adoption = _read("docs/adoption.md")
    roadmap = _read("ROADMAP.md")
    changelog = _read("CHANGELOG.md")

    for target in (
        "docs/adoption-evidence.md",
        "schemas/kepenk-adoption-evidence-v1.schema.json",
        "examples/adoption/ustaca-ai.json",
    ):
        assert target in readme

    assert "validate-adoption" in guide
    assert "does not replace a registry pull request" in guide
    assert "does not" in guide
    assert "fetch any URL" in guide
    assert "count users" in guide
    assert "prove repository ownership" in guide
    assert "Human registry review" in guide
    assert "validate-adoption" in adoption
    assert "manifest" in adoption.lower()
    assert "[#70]" in roadmap
    assert "offline adoption-evidence manifest" in changelog


def test_contract_marks_version_one_as_experimental() -> None:
    guide = _read("docs/adoption-evidence.md")

    assert "Version 1 is experimental during the v0.4 line" in guide
    assert "breaking field or classification change requires a new integer manifest version" in guide
