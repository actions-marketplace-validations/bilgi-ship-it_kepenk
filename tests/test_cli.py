from pathlib import Path

from kepenk.cli import EXIT_APPROVAL_NOT_GRANTED, EXIT_DENIED, main


def _write_policy(tmp_path: Path) -> Path:
    path = tmp_path / "kepenk.yaml"
    path.write_text(
        """
version: 1
default: approval
audit:
  path: AUDIT_PATH
rules:
  - id: deny-rm
    effect: deny
    reason: destructive
    match:
      action: shell
      command_regex: 'rm\s+-rf'
  - id: allow-python
    effect: allow
    reason: allowed
    match:
      action: shell
      command_regex: '^python'
""".replace("AUDIT_PATH", str(tmp_path / "audit.jsonl")),
        encoding="utf-8",
    )
    return path


def test_check_exit_codes(tmp_path: Path) -> None:
    policy = _write_policy(tmp_path)
    prefix = ["--policy", str(policy), "check", "--action", "shell", "--command"]

    assert main([*prefix, "rm -rf x"]) == EXIT_DENIED
    assert main([*prefix, "echo hi"]) == EXIT_APPROVAL_NOT_GRANTED
    assert main([*prefix, "python -V"]) == 0


def test_validate_policy(tmp_path: Path, capsys) -> None:
    policy = _write_policy(tmp_path)

    assert main(["--policy", str(policy), "validate"]) == 0
    assert "valid policy: version 1" in capsys.readouterr().out


def test_validate_policy_json(tmp_path: Path, capsys) -> None:
    policy = _write_policy(tmp_path)

    assert main(["--policy", str(policy), "validate", "--json"]) == 0
    output = capsys.readouterr().out
    assert '"valid": true' in output
    assert '"rules": 2' in output
