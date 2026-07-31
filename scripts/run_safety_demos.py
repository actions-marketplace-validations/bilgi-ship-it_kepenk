from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_POLICY = ROOT / "kepenk.example.yaml"


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "kepenk.cli", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def _json_output(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise AssertionError(f"missing JSON output; stderr={result.stderr!r}")
    payload = json.loads(lines[-1])
    if not isinstance(payload, dict):
        raise AssertionError("expected a JSON object")
    return payload


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="kepenk-demos-") as temporary:
        workdir = Path(temporary)
        policy_path = workdir / "kepenk.yaml"
        audit_path = workdir / "audit.jsonl"
        policy_text = SOURCE_POLICY.read_text(encoding="utf-8").replace(
            ".kepenk/audit.jsonl",
            audit_path.as_posix(),
        )
        policy_path.write_text(policy_text, encoding="utf-8")
        prefix = ("--policy", str(policy_path))

        safe_test = _run(
            *prefix,
            "run",
            "--",
            "python",
            "-m",
            "pytest",
            "--version",
            cwd=workdir,
        )
        assert safe_test.returncode == 0, safe_test.stderr
        assert "ALLOW:" in safe_test.stdout

        push = _run(
            *prefix,
            "check",
            "--action",
            "shell",
            "--command",
            "git push origin main",
            "--json",
            cwd=workdir,
        )
        push_payload = _json_output(push)
        assert push.returncode == 75
        assert push_payload["effect"] == "approval"
        assert push_payload["rule_id"] == "require-approval-for-push"

        destructive_delete = _run(
            *prefix,
            "check",
            "--action",
            "shell",
            "--command",
            "sudo rm -rf /",
            "--json",
            cwd=workdir,
        )
        delete_payload = _json_output(destructive_delete)
        assert destructive_delete.returncode == 77
        assert delete_payload["effect"] == "deny"
        assert delete_payload["rule_id"] == "deny-destructive-root-delete"

        audit = _run(
            *prefix,
            "verify-audit",
            "--audit",
            str(audit_path),
            cwd=workdir,
        )
        assert audit.returncode == 0, audit.stderr
        assert "valid audit chain: 4 events" in audit.stdout

        print("demo 1: safe test command executed and returned allow")
        print("demo 1: git push returned approval and was not executed")
        print("demo 2: destructive delete returned deny and was not executed")
        print("demo 2: audit hash chain verified with 4 events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
