from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from .engine import PolicyEngine
from .errors import KepenkError
from .policy import load_policy
from .protocol import PROTOCOL_VERSION, ProtocolError, evaluate_request

EXIT_USAGE = 64


def _error_response(code: str, message: str) -> dict[str, Any]:
    return {
        "version": PROTOCOL_VERSION,
        "id": None,
        "ok": False,
        "error": {"code": code, "message": message},
    }


def evaluate_mcp_action(
    engine: PolicyEngine,
    audit_path: str,
    *,
    action_type: str,
    command: str | None = None,
    path: str | None = None,
    host: str | None = None,
    repository: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate one structured MCP tool request without executing it."""
    payload = {
        "version": PROTOCOL_VERSION,
        "id": None,
        "action": {
            "type": action_type,
            "command": command,
            "path": path,
            "host": host,
            "repository": repository,
            "metadata": metadata or {},
        },
    }
    try:
        return evaluate_request(engine, audit_path, payload)
    except ProtocolError as exc:
        return _error_response("invalid_request", str(exc))
    except KepenkError as exc:
        return _error_response("evaluation_error", str(exc))


def create_mcp_server(policy_path: str | Path = "kepenk.yaml") -> Any:
    """Build a local stdio MCP server exposing one read-only decision tool."""
    try:
        from mcp.server import MCPServer
    except ImportError as exc:  # pragma: no cover - exercised by installation guidance
        raise RuntimeError(
            'MCP support is not installed. Install it with: pip install "kepenk-gate[mcp]"'
        ) from exc

    policy = load_policy(policy_path)
    engine = PolicyEngine(policy)
    server = MCPServer("Kepenk Policy Gate")

    @server.tool()
    def kepenk_check_action(
        type: str,
        command: str | None = None,
        path: str | None = None,
        host: str | None = None,
        repository: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Check a proposed agent action. This tool never executes the action."""
        return evaluate_mcp_action(
            engine,
            policy.audit_path,
            action_type=type,
            command=command,
            path=path,
            host=host,
            repository=repository,
            metadata=metadata,
        )

    return server


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kepenk-mcp",
        description="Run the Kepenk policy gate as a local MCP stdio server.",
    )
    parser.add_argument(
        "--policy",
        default=os.environ.get("KEPENK_POLICY", "kepenk.yaml"),
        help="Path to a Kepenk policy file (default: kepenk.yaml or KEPENK_POLICY)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        server = create_mcp_server(args.policy)
    except (KepenkError, OSError, RuntimeError) as exc:
        print(f"kepenk-mcp: {exc}", file=sys.stderr)
        return EXIT_USAGE

    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
