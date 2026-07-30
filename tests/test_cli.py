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
      command_regex: 'rm\\s+-rf'
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
    assert main(["--policy", str(policy), "check", "--action", "shell", "--command", "rm -rf x"]) == EXIT_DENIED
    assert main(["--policy", str(policy), "check", "--action", "shell", "--command", "echo hi"]) == EXIT_APPROVAL_NOT_GRANTED
    assert main(["--policy", str(policy), "check", "--action", "shell", "--command", "python -V"]) == 0
