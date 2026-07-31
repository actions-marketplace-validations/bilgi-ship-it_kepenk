from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "examples" / "policies"


def main() -> int:
    policies = sorted(POLICY_DIR.glob("*.yaml"))
    if not policies:
        print(f"no policy examples found in {POLICY_DIR}", file=sys.stderr)
        return 1

    for policy in policies:
        print(f"validating {policy.relative_to(ROOT)}")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "kepenk.cli",
                "--policy",
                str(policy),
                "validate",
            ],
            cwd=ROOT,
            check=False,
        )
        if result.returncode != 0:
            return result.returncode

    print(f"validated {len(policies)} policy examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
