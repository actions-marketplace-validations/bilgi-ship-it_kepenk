from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_pypi_state.py"
SPEC = importlib.util.spec_from_file_location("kepenk_check_pypi_state", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

inspect_project = MODULE.inspect_project
project_identity = MODULE.project_identity


class FakeResponse(io.BytesIO):
    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def _response(payload: dict[str, object]) -> FakeResponse:
    return FakeResponse(json.dumps(payload).encode("utf-8"))


def test_project_identity_reads_name_and_version(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "example-gate"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )

    assert project_identity(pyproject) == ("example-gate", "1.2.3")


def test_missing_public_project_is_not_claimed_as_available() -> None:
    def missing(url: str, timeout: int) -> FakeResponse:
        raise HTTPError(url, 404, "Not Found", hdrs=None, fp=None)

    result = inspect_project("kepenk-gate", "0.1.0", opener=missing)

    assert result["status"] == "not_found"
    assert result["version_published"] is False
    assert "does not prove" in str(result["message"])


def test_existing_version_blocks_reuse() -> None:
    def existing(url: str, timeout: int) -> FakeResponse:
        return _response({"releases": {"0.1.0": [{}]}})

    result = inspect_project("kepenk-gate", "0.1.0", opener=existing)

    assert result["status"] == "exists"
    assert result["version_published"] is True


def test_existing_project_without_version_requires_ownership_check() -> None:
    def existing(url: str, timeout: int) -> FakeResponse:
        return _response({"releases": {"0.0.1": [{}]}})

    result = inspect_project("kepenk-gate", "0.1.0", opener=existing)

    assert result["version_published"] is False
    assert "ownership" in str(result["message"])


def test_network_failure_is_explicit() -> None:
    def unavailable(url: str, timeout: int) -> FakeResponse:
        raise URLError("offline")

    with pytest.raises(RuntimeError, match="could not reach pypi"):
        inspect_project("kepenk-gate", "0.1.0", opener=unavailable)
