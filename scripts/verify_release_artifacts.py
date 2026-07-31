from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import venv
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DISTRIBUTION_NAME = "kepenk-gate"


def _run(
    command: Sequence[str | Path],
    cwd: Path = ROOT,
    expected_codes: tuple[int, ...] = (0,),
) -> None:
    printable = [str(item) for item in command]
    print("+", " ".join(printable), flush=True)
    result = subprocess.run(printable, cwd=cwd, check=False)
    if result.returncode not in expected_codes:
        raise subprocess.CalledProcessError(result.returncode, printable)


def _environment_python(environment: Path) -> Path:
    if os.name == "nt":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def _environment_command(environment: Path, name: str) -> Path:
    if os.name == "nt":
        return environment / "Scripts" / f"{name}.exe"
    return environment / "bin" / name


def _expected_version() -> str:
    payload = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = payload.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise RuntimeError("pyproject.toml must define a non-empty project.version")
    return version


def _artifacts() -> tuple[Path, Path]:
    wheels = sorted(DIST.glob("*.whl"))
    source_distributions = sorted(DIST.glob("*.tar.gz"))
    if len(wheels) != 1 or len(source_distributions) != 1:
        raise RuntimeError(
            "expected exactly one wheel and one source distribution; "
            f"found {len(wheels)} wheels and {len(source_distributions)} source distributions"
        )
    return wheels[0], source_distributions[0]


def _write_adoption_evidence(workspace: Path, expected_version: str) -> Path:
    evidence = workspace / "adoption.json"
    evidence.write_text(
        json.dumps(
            {
                "version": 1,
                "classification": "founding_team_pilot",
                "repository": "bilgi-ship-it/ustaca-ai",
                "repository_url": "https://github.com/bilgi-ship-it/ustaca-ai",
                "maintainer": "bilgi-ship-it",
                "maintainer_url": "https://github.com/bilgi-ship-it",
                "maintainer_consent": True,
                "integration": "github_action",
                "kepenk_version": f"v{expected_version}",
                "evidence_url": (
                    "https://github.com/bilgi-ship-it/ustaca-ai/tree/main/.kepenk"
                ),
                "verified_on": "2026-07-31",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return evidence


def _verify_install(artifact: Path, expected_version: str) -> None:
    with tempfile.TemporaryDirectory(prefix="kepenk-release-") as temporary:
        temporary_path = Path(temporary)
        environment = temporary_path / "venv"
        workspace = temporary_path / "workspace"
        workspace.mkdir()
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python = _environment_python(environment)
        kepenk = _environment_command(environment, "kepenk")
        pre_commit = _environment_command(environment, "kepenk-pre-commit")
        mcp = _environment_command(environment, "kepenk-mcp")

        _run(
            [
                python,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                artifact,
            ]
        )
        _run(
            [
                python,
                "-c",
                (
                    "from importlib.metadata import version; "
                    f"assert version({DISTRIBUTION_NAME!r}) == {expected_version!r}"
                ),
            ]
        )
        _run([kepenk, "--help"])
        _run([kepenk, "validate-adoption", "--help"])
        _run([pre_commit, "--help"])
        _run([mcp, "--help"])
        evidence = _write_adoption_evidence(workspace, expected_version)
        _run(
            [kepenk, "validate-adoption", "--evidence", evidence, "--json"],
            cwd=workspace,
        )
        _run([kepenk, "--policy", "kepenk.yaml", "init"], cwd=workspace)
        _run(
            [
                kepenk,
                "--policy",
                "kepenk.yaml",
                "check",
                "--action",
                "shell",
                "--command",
                "git status --short",
            ],
            cwd=workspace,
            expected_codes=(75,),
        )


def main() -> int:
    expected_version = _expected_version()
    shutil.rmtree(DIST, ignore_errors=True)
    _run([sys.executable, "-m", "build"])
    wheel, source_distribution = _artifacts()
    _run([sys.executable, "-m", "twine", "check", wheel, source_distribution])
    _verify_install(wheel, expected_version)
    _verify_install(source_distribution, expected_version)
    print(
        f"verified release artifacts for {DISTRIBUTION_NAME}=={expected_version}: "
        f"{wheel.name}, {source_distribution.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
