# Contributing to Kepenk

Thank you for helping build a safer layer for agentic developer tooling.

## Before opening a pull request

1. Open or reference an issue for non-trivial changes.
2. Keep the core deterministic and provider-neutral.
3. Add tests for new behavior and edge cases.
4. Run:

```bash
ruff check .
mypy src/kepenk
pytest
```

## Commit and PR guidance

- Use focused commits.
- Describe the threat model or failure mode addressed.
- Call out policy-format changes explicitly.
- Do not include secrets, production logs, or proprietary Ustaca code.

## Good first contributions

- additional policy examples
- Windows/PowerShell command patterns
- documentation improvements
- clearer validation errors
- fuzz and property tests for rule matching
