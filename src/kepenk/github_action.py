from __future__ import annotations

import argparse
import html
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

from .engine import PolicyEngine
from .errors import KepenkError
from .models import Action, Decision, Policy
from .policy import load_policy

EXIT_USAGE = 64
EXIT_APPROVAL_NOT_GRANTED = 75
EXIT_DENIED = 77


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kepenk GitHub Action runtime")
    parser.add_argument(
        "--mode",
        choices=("validate", "check"),
        default=os.environ.get("KEPENK_ACTION_MODE", "validate"),
    )
    parser.add_argument(
        "--policy",
        default=os.environ.get("KEPENK_ACTION_POLICY", "kepenk.yaml"),
    )
    parser.add_argument(
        "--action",
        default=os.environ.get("KEPENK_ACTION_TYPE", "shell"),
    )
    parser.add_argument(
        "--command",
        default=os.environ.get("KEPENK_ACTION_COMMAND", ""),
    )
    parser.add_argument(
        "--path",
        default=os.environ.get("KEPENK_ACTION_PATH_VALUE", ""),
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("KEPENK_ACTION_HOST", ""),
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("KEPENK_ACTION_REPOSITORY", ""),
    )
    parser.add_argument(
        "--metadata-json",
        default=os.environ.get("KEPENK_ACTION_METADATA_JSON", "{}"),
    )
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT", ""))
    parser.add_argument(
        "--github-step-summary",
        default=os.environ.get("GITHUB_STEP_SUMMARY", ""),
    )
    return parser


def _metadata(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"metadata_json must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("metadata_json must decode to an object")
    return parsed


def _write_output(path: str, name: str, value: object) -> None:
    if not path:
        return
    delimiter = f"KEPENK_{uuid.uuid4().hex}"
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def _write_outputs(path: str, values: dict[str, object]) -> None:
    for name, value in values.items():
        _write_output(path, name, value)


def _append_summary(path: str, markdown: str) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(markdown.rstrip() + "\n")


def _code(value: object) -> str:
    return f"<code>{html.escape(str(value))}</code>"


def _policy_summary(policy_path: str, policy: Policy) -> str:
    return "\n".join(
        [
            "## Kepenk policy validation",
            "",
            "| Field | Value |",
            "|---|---|",
            "| Status | **VALID** |",
            f"| Policy | {_code(policy_path)} |",
            f"| Version | {_code(policy.version)} |",
            f"| Default | {_code(policy.default)} |",
            f"| Rules | {_code(len(policy.rules))} |",
        ]
    )


def _decision_summary(policy_path: str, decision: Decision) -> str:
    action = decision.action
    return "\n".join(
        [
            "## Kepenk policy check",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Decision | **{html.escape(decision.effect.upper())}** |",
            f"| Policy | {_code(policy_path)} |",
            f"| Rule | {_code(decision.rule_id or '<default>')} |",
            f"| Reason | {html.escape(decision.reason)} |",
            f"| Action | {_code(action.type)} |",
            f"| Command | {_code(action.command or '')} |",
            f"| Path | {_code(action.path or '')} |",
            f"| Host | {_code(action.host or '')} |",
            f"| Repository | {_code(action.repository or '')} |",
        ]
    )


def _error_summary(policy_path: str, error: Exception) -> str:
    return "\n".join(
        [
            "## Kepenk policy result",
            "",
            "| Field | Value |",
            "|---|---|",
            "| Status | **INVALID** |",
            f"| Policy | {_code(policy_path)} |",
            f"| Error | {html.escape(str(error))} |",
        ]
    )


def _check_exit_code(decision: Decision) -> int:
    if decision.denied:
        return EXIT_DENIED
    if decision.requires_approval:
        return EXIT_APPROVAL_NOT_GRANTED
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        policy = load_policy(args.policy)
        if args.mode == "validate":
            _write_outputs(
                args.github_output,
                {
                    "valid": "true",
                    "effect": "",
                    "rule_id": "",
                    "reason": "",
                    "rule_count": len(policy.rules),
                },
            )
            _append_summary(args.github_step_summary, _policy_summary(args.policy, policy))
            print(f"VALID: {args.policy} ({len(policy.rules)} rules)")
            return 0

        action = Action(
            type=args.action,
            command=args.command or None,
            path=args.path or None,
            host=args.host or None,
            repository=args.repository or None,
            metadata=_metadata(args.metadata_json),
        )
        decision = PolicyEngine(policy).evaluate(action)
        _write_outputs(
            args.github_output,
            {
                "valid": "true",
                "effect": decision.effect,
                "rule_id": decision.rule_id or "",
                "reason": decision.reason,
                "rule_count": len(policy.rules),
            },
        )
        _append_summary(args.github_step_summary, _decision_summary(args.policy, decision))
        print(f"{decision.effect.upper()}: {decision.reason}")
        return _check_exit_code(decision)
    except (KepenkError, ValueError) as exc:
        _write_outputs(
            args.github_output,
            {
                "valid": "false",
                "effect": "",
                "rule_id": "",
                "reason": str(exc),
                "rule_count": 0,
            },
        )
        _append_summary(args.github_step_summary, _error_summary(args.policy, exc))
        print(f"kepenk-action: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
