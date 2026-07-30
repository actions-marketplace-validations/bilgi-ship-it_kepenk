#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from kepenk.audit import append_decision
from kepenk.engine import PolicyEngine
from kepenk.errors import KepenkError
from kepenk.models import Action, Decision
from kepenk.policy import load_policy
from kepenk.runner import display_command, run_command

EXIT_USAGE = 64
EXIT_APPROVAL_NOT_GRANTED = 75
EXIT_DENIED = 77


def _parser() -> argparse.ArgumentParser:
    default_policy = os.environ.get(
        "KEPENK_POLICY",
        str(Path(__file__).with_name("kepenk.yaml")),
    )
    parser = argparse.ArgumentParser(
        description="Route Codex shell actions through a Kepenk policy.",
    )
    parser.add_argument("--policy", default=default_policy)
    parser.add_argument("mode", choices=("check", "run", "approve"))
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def _decision_line(decision: Decision) -> str:
    rule = decision.rule_id or "<default>"
    return f"{decision.effect.upper()}: {decision.reason} [rule: {rule}]"


def _command(arguments: list[str]) -> list[str]:
    command = list(arguments)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ValueError("a command is required after --")
    return command


def _execute(policy_path: str, mode: str, command: list[str]) -> int:
    policy = load_policy(policy_path)
    action = Action(type="shell", command=display_command(command))
    decision = PolicyEngine(policy).evaluate(action)
    print(_decision_line(decision))

    if mode == "check":
        append_decision(policy.audit_path, decision, outcome="codex_checked")
        if decision.denied:
            return EXIT_DENIED
        if decision.requires_approval:
            return EXIT_APPROVAL_NOT_GRANTED
        return 0

    if decision.denied:
        append_decision(policy.audit_path, decision, outcome="codex_denied")
        return EXIT_DENIED

    if decision.requires_approval and mode != "approve":
        append_decision(policy.audit_path, decision, outcome="codex_approval_required")
        print(
            "Stop and ask the maintainer. Re-run with mode 'approve' only after explicit approval.",
            file=sys.stderr,
        )
        return EXIT_APPROVAL_NOT_GRANTED

    if decision.requires_approval:
        append_decision(policy.audit_path, decision, outcome="codex_approval_granted")

    append_decision(policy.audit_path, decision, outcome="codex_execution_started")
    child_code = run_command(command)
    append_decision(
        policy.audit_path,
        decision,
        outcome=f"codex_execution_finished:{child_code}",
    )
    return child_code


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        return _execute(args.policy, args.mode, _command(args.command))
    except (KepenkError, ValueError) as exc:
        print(f"kepenk-codex: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
