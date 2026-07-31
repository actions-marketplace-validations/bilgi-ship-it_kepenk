from __future__ import annotations

import argparse
import json
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
REPOSITORIES = {
    "pypi": "https://pypi.org/pypi",
    "testpypi": "https://test.pypi.org/pypi",
}

Opener = Callable[..., Any]


def project_identity(pyproject_path: Path = ROOT / "pyproject.toml") -> tuple[str, str]:
    with pyproject_path.open("rb") as handle:
        data = tomllib.load(handle)
    project = data.get("project", {})
    name = project.get("name")
    version = project.get("version")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("pyproject.toml must define a non-empty project.name")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("pyproject.toml must define a non-empty project.version")
    return name, version


def inspect_project(
    name: str,
    version: str,
    repository: str = "pypi",
    opener: Opener = urlopen,
) -> dict[str, object]:
    base_url = REPOSITORIES[repository]
    url = f"{base_url}/{quote(name, safe='')}/json"
    try:
        response = opener(url, timeout=10)
    except HTTPError as exc:
        if exc.code == 404:
            return {
                "repository": repository,
                "project": name,
                "version": version,
                "status": "not_found",
                "version_published": False,
                "message": (
                    "No public project listing was found. This does not prove that the "
                    "name is reservable or that publishing permission exists."
                ),
            }
        raise RuntimeError(f"{repository} returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"could not reach {repository}: {exc.reason}") from exc

    with response:
        payload = json.load(response)
    releases = payload.get("releases", {})
    if not isinstance(releases, dict):
        raise RuntimeError(f"{repository} returned an unexpected project response")
    version_published = version in releases
    return {
        "repository": repository,
        "project": name,
        "version": version,
        "status": "exists",
        "version_published": version_published,
        "message": (
            "The requested version already exists and must not be overwritten."
            if version_published
            else "The project exists; confirm publishing ownership before uploading."
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect public PyPI state before publishing a Kepenk release."
    )
    parser.add_argument(
        "--repository",
        choices=sorted(REPOSITORIES),
        default="pypi",
        help="Package index to inspect (default: pypi)",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        name, version = project_identity()
        result = inspect_project(name, version, repository=args.repository)
    except (OSError, ValueError, RuntimeError, tomllib.TOMLDecodeError) as exc:
        print(f"PyPI preflight failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"{result['repository']}: {result['project']} {result['version']} — "
            f"{result['status']}"
        )
        print(result["message"])

    return 1 if result["version_published"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
