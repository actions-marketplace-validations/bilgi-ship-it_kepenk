from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WRAPPER = Path(__file__).parents[1] / "examples" / "codex" / "kepenk_codex.py"


def _policy(tmp_path: Path) -> Path:
    policy = tmp_path / "kepenk.yaml"
    policy.write_text(
        f"""
version: 1
default: approval
audit:
  path: {tmp_path / 'audit.jsonl'}
rules:
  - id: deny-marker
    effect: deny
    reason: denied for test
    match:
      action: shell
      command_contains: --denied-marker
  - id: approve-marker
    effect: approval
    reason: approval required for test
    match:
      action: shell
      command_contains: --approval-marker
  - id: allow-marker
    effect: allow
    reason: allowed for test
    match:
      action: shell
      command_contains: --allowed-marker
""",
        encoding="utf-8",
    )
    return policy


def _write_command(marker: Path, token: str) -> list[str]:
    code = "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ran')"
    return [sys.executable, "-c", code, str(marker), token]


def _run(policy: Path, mode: str, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(WRAPPER), "--policy", str(policy), mode, "--", *command],
        check=False,
        capture_output=True,
        text=True,
    )


def test_codex_wrapper_runs_allowed_command(tmp_path: Path) -> None:
    marker = tmp_path / "allowed.txt"
    result = _run(_policy(tmp_path), "run", _write_command(marker, "--allowed-marker"))

    assert result.returncode == 0
    assert marker.read_text(encoding="utf-8") == "ran"


def test_codex_wrapper_does_not_run_denied_command(tmp_path: Path) -> None:
    marker = tmp_path / "denied.txt"
    result = _run(_policy(tmp_path), "run", _write_command(marker, "--denied-marker"))

    assert result.returncode == 77
    assert not marker.exists()


def test_codex_wrapper_requires_then_accepts_explicit_approval(tmp_path: Path) -> None:
    marker = tmp_path / "approved.txt"
    command = _write_command(marker, "--approval-marker")
    policy = _policy(tmp_path)

    blocked = _run(policy, "run", command)
    assert blocked.returncode == 75
    assert not marker.exists()

    approved = _run(policy, "approve", command)
    assert approved.returncode == 0
    assert marker.read_text(encoding="utf-8") == "ran"
