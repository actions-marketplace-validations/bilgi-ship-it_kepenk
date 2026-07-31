from __future__ import annotations

from pathlib import Path

from kepenk.github_action import main


def _policy(tmp_path: Path) -> Path:
    path = tmp_path / "kepenk.yaml"
    path.write_text(
        """
version: 1
default: approval
rules:
  - id: deny-publish
    effect: deny
    reason: publishing is blocked
    match:
      action: shell
      command_contains: publish
  - id: allow-status
    effect: allow
    reason: status is read only
    match:
      action: shell
      command_contains: status
""",
        encoding="utf-8",
    )
    return path


def _output_values(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    index = 0
    while index < len(lines):
        name, delimiter = lines[index].split("<<", 1)
        index += 1
        chunks: list[str] = []
        while lines[index] != delimiter:
            chunks.append(lines[index])
            index += 1
        values[name] = "\n".join(chunks)
        index += 1
    return values


def test_validate_mode_writes_outputs_and_summary(tmp_path: Path) -> None:
    output = tmp_path / "output.txt"
    summary = tmp_path / "summary.md"

    result = main(
        [
            "--mode",
            "validate",
            "--policy",
            str(_policy(tmp_path)),
            "--github-output",
            str(output),
            "--github-step-summary",
            str(summary),
        ]
    )

    values = _output_values(output)
    assert result == 0
    assert values["valid"] == "true"
    assert values["rule_count"] == "2"
    assert "VALID" in summary.read_text(encoding="utf-8")


def test_check_mode_reports_allow_decision(tmp_path: Path) -> None:
    output = tmp_path / "output.txt"

    result = main(
        [
            "--mode",
            "check",
            "--policy",
            str(_policy(tmp_path)),
            "--command",
            "git status --short",
            "--github-output",
            str(output),
        ]
    )

    values = _output_values(output)
    assert result == 0
    assert values["effect"] == "allow"
    assert values["rule_id"] == "allow-status"


def test_check_mode_uses_deny_exit_code(tmp_path: Path) -> None:
    result = main(
        [
            "--mode",
            "check",
            "--policy",
            str(_policy(tmp_path)),
            "--command",
            "npm publish",
        ]
    )

    assert result == 77


def test_check_mode_uses_approval_exit_code(tmp_path: Path) -> None:
    result = main(
        [
            "--mode",
            "check",
            "--policy",
            str(_policy(tmp_path)),
            "--command",
            "git commit -m change",
        ]
    )

    assert result == 75


def test_invalid_policy_is_reported_fail_closed(tmp_path: Path) -> None:
    policy = tmp_path / "invalid.yaml"
    policy.write_text("version: 2\n", encoding="utf-8")
    output = tmp_path / "output.txt"

    result = main(
        [
            "--mode",
            "validate",
            "--policy",
            str(policy),
            "--github-output",
            str(output),
        ]
    )

    values = _output_values(output)
    assert result == 64
    assert values["valid"] == "false"
