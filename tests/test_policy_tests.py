from __future__ import annotations

import json
from pathlib import Path

import pytest

from kepenk.cli import EXIT_TEST_FAILED, EXIT_USAGE, main
from kepenk.engine import PolicyEngine
from kepenk.policy import load_policy
from kepenk.policy_tests import (
    PolicyTestError,
    evaluate_policy_test_suite,
    load_policy_test_suite,
)


def _write_policy(tmp_path: Path) -> Path:
    path = tmp_path / "kepenk.yaml"
    path.write_text(
        f"""
version: 1
default: approval
audit:
  path: {tmp_path / 'audit.jsonl'}
rules:
  - id: deny-delete
    effect: deny
    reason: destructive
    match:
      action: shell
      command_regex: '^rm -rf'
  - id: allow-tests
    effect: allow
    reason: tests are safe
    match:
      action: shell
      command_regex: '^python -m pytest'
  - id: approve-upload
    effect: approval
    reason: publishing needs approval
    match:
      action: shell
      command_regex: '^python -m twine upload'
""",
        encoding="utf-8",
    )
    return path


def _write_suite(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "kepenk.tests.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def _complete_suite(tmp_path: Path) -> Path:
    marker = tmp_path / "must-not-exist"
    return _write_suite(
        tmp_path,
        f"""
version: 1
cases:
  - id: allow-local-tests
    action:
      type: shell
      command: python -m pytest
      metadata:
        environment: test
        labels: [local, safe]
    expect:
      effect: allow
      rule_id: allow-tests
  - id: require-upload-approval
    action:
      type: shell
      command: python -m twine upload dist/*
    expect:
      effect: approval
      rule_id: approve-upload
  - id: deny-recursive-delete
    action:
      type: shell
      command: rm -rf /
    expect:
      effect: deny
      rule_id: deny-delete
  - id: use-default-for-unmatched
    action:
      type: shell
      command: touch {marker}
    expect:
      effect: approval
      rule_id: null
""",
    )


def test_suite_evaluates_all_effects_without_execution_or_audit(tmp_path: Path) -> None:
    policy_path = _write_policy(tmp_path)
    suite_path = _complete_suite(tmp_path)
    engine = PolicyEngine(load_policy(policy_path))

    suite = load_policy_test_suite(suite_path)
    results = evaluate_policy_test_suite(engine, suite)

    assert suite.version == 1
    assert [result.decision.effect for result in results] == [
        "allow",
        "approval",
        "deny",
        "approval",
    ]
    assert all(result.passed for result in results)
    assert results[-1].decision.rule_id is None
    assert not (tmp_path / "must-not-exist").exists()
    assert not (tmp_path / "audit.jsonl").exists()


def test_cli_policy_test_human_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    policy_path = _write_policy(tmp_path)
    suite_path = _complete_suite(tmp_path)

    assert main(["--policy", str(policy_path), "test", "--tests", str(suite_path)]) == 0

    output = capsys.readouterr().out
    assert "PASS allow-local-tests" in output
    assert "PASS use-default-for-unmatched" in output
    assert "policy tests: 4 passed, 0 failed, 4 total" in output


def test_cli_policy_test_json_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    policy_path = _write_policy(tmp_path)
    suite_path = _complete_suite(tmp_path)

    assert (
        main(
            [
                "--policy",
                str(policy_path),
                "test",
                "--tests",
                str(suite_path),
                "--json",
            ]
        )
        == 0
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["version"] == 1
    assert payload["ok"] is True
    assert payload["passed"] == 4
    assert payload["failed"] == 0
    assert payload["cases"][0]["expected"] == {
        "effect": "allow",
        "rule_id": "allow-tests",
    }
    assert payload["cases"][-1]["actual"]["rule_id"] is None


def test_cli_policy_test_returns_one_for_expectation_mismatch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    policy_path = _write_policy(tmp_path)
    suite_path = _write_suite(
        tmp_path,
        """
version: 1
cases:
  - id: wrong-expectation
    action:
      type: shell
      command: python -m pytest
    expect:
      effect: deny
      rule_id: deny-delete
""",
    )

    assert (
        main(["--policy", str(policy_path), "test", "--tests", str(suite_path)])
        == EXIT_TEST_FAILED
    )
    output = capsys.readouterr().out
    assert "FAIL wrong-expectation" in output
    assert "expected deny via deny-delete; got allow via allow-tests" in output
    assert "policy tests: 0 passed, 1 failed, 1 total" in output


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (
            """
version: 1
cases:
  - id: duplicate
    action: {type: shell}
    expect: {effect: allow, rule_id: null}
  - id: duplicate
    action: {type: shell}
    expect: {effect: allow, rule_id: null}
""",
            "duplicate policy test case id",
        ),
        (
            """
version: 1
unknown: true
cases:
  - id: case
    action: {type: shell}
    expect: {effect: allow, rule_id: null}
""",
            "unsupported fields: unknown",
        ),
        (
            """
version: 1
cases:
  - id: missing-rule-id
    action: {type: shell}
    expect: {effect: allow}
""",
            "expect.rule_id is required",
        ),
        (
            """
version: 1
cases:
  - id: invalid-metadata
    action:
      type: shell
      metadata:
        released: 2026-07-31
    expect: {effect: approval, rule_id: null}
""",
            "must contain only JSON-compatible values",
        ),
    ],
)
def test_suite_loader_rejects_invalid_input(
    tmp_path: Path, body: str, message: str
) -> None:
    suite_path = _write_suite(tmp_path, body)

    with pytest.raises(PolicyTestError, match=message):
        load_policy_test_suite(suite_path)


def test_cli_invalid_suite_returns_usage_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    policy_path = _write_policy(tmp_path)
    suite_path = _write_suite(tmp_path, "version: 2\ncases: []\n")

    assert (
        main(["--policy", str(policy_path), "test", "--tests", str(suite_path)])
        == EXIT_USAGE
    )
    assert "only policy test suite version 1 is supported" in capsys.readouterr().err
