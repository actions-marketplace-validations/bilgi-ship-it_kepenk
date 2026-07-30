#!/usr/bin/env bash
set -euo pipefail
python -m compileall -q src tests
pytest
if command -v ruff >/dev/null 2>&1; then ruff check .; fi
if command -v mypy >/dev/null 2>&1; then mypy src/kepenk; fi
