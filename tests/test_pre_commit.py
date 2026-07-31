from __future__ import annotations

from pathlib import Path

import yaml

from kepenk.pre_commit import main


def _write_valid_policy(path: Path) -> None:
    path.write_text(
        """
version: 1
default: approval
audit:
  path: .kepenk/audit.jsonl
rules:
  - id: allow-status
    effect: allow
    reason: read only
    match:
      action: shell
      command_regex: '^git status$'
""",
        encoding="utf-8",
    )


def test_valid_policy_returns_zero(tmp_path: Path, capsys) -> None:
    policy = tmp_path / "kepenk.yaml"
    _write_valid_policy(policy)

    assert main([str(policy)]) == 0
    output = capsys.readouterr()
    assert f"VALID {policy}" in output.out
    assert output.err == ""


def test_invalid_policy_fails_closed_but_checks_remaining_files(
    tmp_path: Path,
    capsys,
) -> None:
    invalid = tmp_path / "broken.kepenk.yaml"
    invalid.write_text("version: 2\nrules: []\n", encoding="utf-8")
    valid = tmp_path / "kepenk.yaml"
    _write_valid_policy(valid)

    assert main([str(invalid), str(valid)]) == 1
    output = capsys.readouterr()
    assert f"INVALID {invalid}" in output.err
    assert "only policy version 1 is supported" in output.err
    assert f"VALID {valid}" in output.out


def test_missing_policy_fails_closed(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "missing.kepenk.yaml"

    assert main([str(missing)]) == 1
    assert "policy file not found" in capsys.readouterr().err


def test_no_filenames_is_a_no_op() -> None:
    assert main([]) == 0


def test_hook_manifest_declares_managed_python_hook() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = yaml.safe_load((root / ".pre-commit-hooks.yaml").read_text(encoding="utf-8"))

    assert isinstance(manifest, list)
    assert manifest[0]["id"] == "kepenk-validate"
    assert manifest[0]["entry"] == "kepenk-pre-commit"
    assert manifest[0]["language"] == "python"
    assert manifest[0]["require_serial"] is True
