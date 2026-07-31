from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import venv
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


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


def _artifacts() -> tuple[Path, Path]:
    wheels = sorted(DIST.glob("*.whl"))
    source_distributions = sorted(DIST.glob("*.tar.gz"))
    if len(wheels) != 1 or len(source_distributions) != 1:
        raise RuntimeError(
            "expected exactly one wheel and one source distribution; "
            f"found {len(wheels)} wheels and {len(source_distributions)} source distributions"
        )
    return wheels[0], source_distributions[0]


def _verify_install(artifact: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="kepenk-release-") as temporary:
        temporary_path = Path(temporary)
        environment = temporary_path / "venv"
        workspace = temporary_path / "workspace"
        workspace.mkdir()
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python = _environment_python(environment)

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
        _run([python, "-m", "kepenk", "--help"])
        _run([python, "-m", "kepenk", "--policy", "kepenk.yaml", "init"], cwd=workspace)
        _run(
            [
                python,
                "-m",
                "kepenk",
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
    shutil.rmtree(DIST, ignore_errors=True)
    _run([sys.executable, "-m", "build"])
    wheel, source_distribution = _artifacts()
    _run([sys.executable, "-m", "twine", "check", wheel, source_distribution])
    _verify_install(wheel)
    _verify_install(source_distribution)
    print(f"verified release artifacts: {wheel.name}, {source_distribution.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
