from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import KepenkError
from .policy import load_policy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kepenk-pre-commit",
        description="Validate one or more Kepenk policy files.",
    )
    parser.add_argument("filenames", nargs="*", help="Policy files passed by pre-commit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    failed = False

    for filename in args.filenames:
        policy_path = Path(filename)
        try:
            policy = load_policy(policy_path)
        except (KepenkError, OSError) as exc:
            failed = True
            print(f"INVALID {policy_path}: {exc}", file=sys.stderr)
            continue

        print(
            f"VALID {policy_path}: version={policy.version} "
            f"default={policy.default} rules={len(policy.rules)}"
        )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
