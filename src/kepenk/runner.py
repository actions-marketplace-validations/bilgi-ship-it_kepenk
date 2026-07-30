from __future__ import annotations

import shlex
import subprocess
from collections.abc import Sequence


def display_command(command: Sequence[str]) -> str:
    return shlex.join(command)


def run_command(command: Sequence[str]) -> int:
    if not command:
        raise ValueError("command must not be empty")
    completed = subprocess.run(list(command), check=False, shell=False)
    return completed.returncode
