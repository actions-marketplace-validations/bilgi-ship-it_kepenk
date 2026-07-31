from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .audit import append_decision, verify_audit
from .engine import PolicyEngine
from .errors import KepenkError
from .models import Action, Decision
from .policy import load_policy
from .protocol import run_protocol
from .runner import display_command, run_command

EXIT_USAGE = 64
EXIT_APPROVAL_NOT_GRANTED = 75
EXIT_DENIED = 77


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kepenk",
        description="Deterministic approval and audit gate for AI agent actions.",
    )
    parser.add_argument(
        "--policy",
        default="kepenk.yaml",
        help="Policy path (default: kepenk.yaml)",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    init = sub.add_parser("init", help="Create a conservative starter policy")
    init.add_argument("--force", action="store_true", help="Overwrite an existing policy")

    validate = sub.add_parser("validate", help="Validate a policy file and exit")
    validate.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    check = sub.add_parser("check", help="Evaluate an action without executing it")
    _add_action_arguments(check)
    check.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    run = sub.add_parser("run", help="Evaluate and execute a command")
    run.add_argument("--yes", action="store_true", help="Grant required approval non-interactively")
    run.add_argument("command", nargs=argparse.REMAINDER, help="Command after --")

    sub.add_parser(
        "protocol",
        help="Read versioned JSONL action requests from stdin and write decisions to stdout",
    )

    verify = sub.add_parser("verify-audit", help="Verify the audit hash chain")
    verify.add_argument("--audit", help="Audit path; defaults to policy audit.path")
    return parser


def _add_action_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--action", required=True, help="Action type, e.g. shell")
    parser.add_argument("--command")
    parser.add_argument("--path")
    parser.add_argument("--host")
    parser.add_argument(
        "--metadata",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Metadata value; repeatable",
    )


def _metadata(items: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"metadata must be KEY=VALUE: {item}")
        key, value = item.split("=", 1)
        if not key:
            raise ValueError("metadata key must not be empty")
        result[key] = value
    return result


def _print_decision(decision: Decision, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(decision.to_dict(), ensure_ascii=False, sort_keys=True))
        return
    rule = decision.rule_id or "<default>"
    print(f"{decision.effect.upper()}: {decision.reason} [rule: {rule}]")


def _init_policy(policy_path: Path, force: bool) -> int:
    if policy_path.exists() and not force:
        print(f"policy already exists: {policy_path}", file=sys.stderr)
        return EXIT_USAGE
    source = Path(__file__).resolve().parents[2] / "kepenk.example.yaml"
    if source.exists():
        shutil.copyfile(source, policy_path)
    else:
        policy_path.write_text(
            "version: 1\ndefault: approval\naudit:\n  path: .kepenk/audit.jsonl\nrules: []\n",
            encoding="utf-8",
        )
    print(f"created {policy_path}")
    return 0


def _load_engine(policy_path: str) -> tuple[PolicyEngine, str]:
    policy = load_policy(policy_path)
    return PolicyEngine(policy), policy.audit_path


def _confirm(decision: Decision) -> bool:
    print(f"APPROVAL REQUIRED: {decision.reason}", file=sys.stderr)
    answer = input("Approve this action? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    policy_path = Path(args.policy)

    try:
        if args.subcommand == "init":
            return _init_policy(policy_path, args.force)

        engine, audit_path = _load_engine(str(policy_path))

        if args.subcommand == "validate":
            payload = {
                "valid": True,
                "version": engine.policy.version,
                "default": engine.policy.default,
                "rules": len(engine.policy.rules),
                "audit_path": audit_path,
            }
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            else:
                print(
                    f"valid policy: version {payload['version']}, "
                    f"{payload['rules']} rules, default={payload['default']}"
                )
            return 0

        if args.subcommand == "check":
            action = Action(
                type=args.action,
                command=args.command,
                path=args.path,
                host=args.host,
                metadata=_metadata(args.metadata),
            )
            decision = engine.evaluate(action)
            append_decision(audit_path, decision, outcome="checked")
            _print_decision(decision, args.json)
            if decision.denied:
                return EXIT_DENIED
            if decision.requires_approval:
                return EXIT_APPROVAL_NOT_GRANTED
            return 0

        if args.subcommand == "protocol":
            return run_protocol(engine, audit_path, sys.stdin, sys.stdout)

        if args.subcommand == "verify-audit":
            selected_path = args.audit or audit_path
            valid, count, error = verify_audit(selected_path)
            if valid:
                print(f"valid audit chain: {count} events")
                return 0
            print(f"invalid audit chain after {count} events: {error}", file=sys.stderr)
            return EXIT_USAGE

        if args.subcommand == "run":
            command = list(args.command)
            if command and command[0] == "--":
                command = command[1:]
            if not command:
                parser.error("kepenk run requires a command after --")
            action = Action(type="shell", command=display_command(command))
            decision = engine.evaluate(action)
            _print_decision(decision)
            if decision.denied:
                append_decision(audit_path, decision, outcome="denied")
                return EXIT_DENIED
            if decision.requires_approval and not (args.yes or _confirm(decision)):
                append_decision(audit_path, decision, outcome="approval_not_granted")
                return EXIT_APPROVAL_NOT_GRANTED
            append_decision(audit_path, decision, outcome="execution_started")
            child_code = run_command(command)
            append_decision(audit_path, decision, outcome=f"execution_finished:{child_code}")
            return child_code

        raise AssertionError("unreachable")
    except (KepenkError, ValueError) as exc:
        print(f"kepenk: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
