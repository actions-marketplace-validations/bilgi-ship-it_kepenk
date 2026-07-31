# Kepenk v0.x integration compatibility contract

**Contract version: 1 — applies to Kepenk releases from v0.2.0 until v1.0.0.**

Kepenk is still pre-1.0. This document defines the narrower machine-facing surfaces that integrations may rely on during the v0.x series. It does not promise that every Python function, message, file layout, or implementation detail will remain unchanged.

## Compatibility levels

### Stable within v0.x

A stable surface will not be removed or changed incompatibly in a patch release. An incompatible change requires one of:

1. a new explicit format or protocol version while the old version remains supported for a migration window;
2. a documented deprecation in release notes followed by removal in a later minor release;
3. an immediate security fix when preserving the old behavior would keep users exposed.

Additive changes are allowed when existing consumers continue to work. Examples include a new optional field, a new CLI subcommand, or a new policy matcher.

### Experimental

Experimental surfaces are usable and tested, but may change in a minor v0.x release. Changes must still be documented with migration guidance. Patch releases should remain backwards compatible unless a security or correctness issue requires otherwise.

### Internal

Anything not named in this document is internal. Internal Python modules, helper functions, dataclass implementation details, log wording, Markdown summaries, test fixtures, and repository layout may change without a deprecation period.

## Stable surfaces

### Policy format version 1

The following are stable:

- top-level `version: 1`;
- effects `allow`, `approval`, and `deny`;
- top-level fields `default`, `audit`, and `rules`;
- rule fields `id`, `effect`, `reason`, and `match`;
- match keys `action`, `command_regex`, `command_contains`, `path_glob`, `host_glob`, `repository_glob`, and `metadata`;
- first matching rule wins;
- the default effect is `approval` when omitted;
- malformed or unsupported policies fail closed.

`repository_glob` matches only the explicit caller-provided `repository` action field. Kepenk does not infer repository context from the filesystem, current directory, Git configuration, remotes, package metadata, or a hosting provider. Missing context does not match a repository matcher.

New optional keys or matchers may be added. A breaking policy-format change requires a new integer version and a migration document. The versioned JSON Schema remains at `schemas/kepenk-policy-v1.schema.json`.

### CLI commands and exit codes

The installed command remains `kepenk`. The following subcommands and machine-relevant options are stable:

- `init [--force]`;
- `validate [--json]`;
- `check --action TYPE [--command TEXT] [--path PATH] [--host HOST] [--repository VALUE] [--metadata KEY=VALUE] [--json]`;
- `run [--yes] [--repository VALUE] -- COMMAND ...`;
- `protocol`;
- `verify-audit [--audit PATH]`.

The documented exit codes are stable:

- `0`: success or allowed action;
- `64`: usage, configuration, validation, protocol, or startup error;
- `75`: explicit approval is required but was not granted;
- `77`: denied by policy;
- for `kepenk run`, another positive value may be the executed child process exit code.

For `check --json`, the stable decision keys are `effect`, `reason`, `rule_id`, and `action`. The action keys are `type`, `command`, `path`, `host`, `repository`, and `metadata`. Human-readable wording is not stable.

### JSONL protocol version 1

Each non-empty input line is one JSON object containing:

- `version`, currently integer `1`;
- optional `id`, which may be a string, integer, or null;
- `action`, with `type` plus optional `command`, `path`, `host`, `repository`, and `metadata`.

Successful output contains exactly the required envelope fields `version`, `id`, `ok`, and `decision`. The decision uses the stable CLI decision shape.

Error output contains `version`, `id`, `ok`, and `error`; `error` contains `code` and `message`. These error codes are stable:

- `invalid_json`;
- `invalid_request`;
- `evaluation_error`.

The protocol is newline-delimited, emits one response for each non-empty request line, flushes each response, and returns exit code `64` if any request failed. New optional fields may be added. A breaking envelope change requires a new protocol version.

### GitHub Action

The reusable action remains available through the repository root `action.yml`.

Stable inputs:

- `mode`;
- `policy`;
- `action_type`;
- `command`;
- `path`;
- `host`;
- `repository`;
- `metadata_json`.

Stable outputs:

- `valid`;
- `effect`;
- `rule_id`;
- `reason`;
- `rule_count`.

`mode` continues to accept `validate` and `check`. Decision exit codes remain `0`, `64`, `75`, and `77` with the same meanings as the CLI. Job-summary formatting and internal step names are internal.

### pre-commit hook

The published hook keeps:

- hook ID `kepenk-validate`;
- entry point `kepenk-pre-commit`;
- managed `language: python` execution;
- one or more filenames passed as positional arguments;
- exit code `0` only when every supplied policy is valid;
- non-zero failure when a policy is missing, malformed, or unsupported.

The default filename regular expression may be extended. Repositories using unusual names should continue to set their own `files` expression.

## Experimental surfaces

### Declarative policy test suites

The `kepenk test` command and policy test-suite format version `1` are experimental while the v0.3 line is developed.

The current interface is:

- `kepenk --policy POLICY test [--tests SUITE] [--json]`;
- default suite path `kepenk.tests.yaml`;
- top-level suite fields `version` and `cases`;
- case fields `id`, `action`, and `expect`;
- action fields `type`, `command`, `path`, `host`, `repository`, and `metadata`;
- expectation fields `effect` and `rule_id`, including explicit `null` for a default decision;
- exit code `0` when every case passes, `1` for expectation mismatches, and `64` for an invalid policy or suite;
- JSON result fields `version`, `ok`, `total`, `passed`, `failed`, and `cases`.

The command evaluates decisions only. It does not execute test actions and does not append test results to the policy audit chain. The format is protected against incompatible patch-release changes, but may receive documented changes in a later minor v0.x release before it is promoted to the stable section.

The versioned schema is `schemas/kepenk-tests-v1.schema.json`.

### MCP adapter

The local command `kepenk-mcp` and tool name `kepenk_check_action` are experimental during v0.2.x.

The adapter currently:

- runs over local MCP stdio;
- accepts `type`, `command`, `path`, `host`, `repository`, and `metadata`;
- returns the JSONL decision or structured error envelope;
- records valid decisions in the configured audit chain;
- never executes the proposed action.

The tool name, core input field names, and fail-closed meaning will not change in a patch release. MCP SDK-specific representation details may change in a minor release with migration notes. The calling MCP host remains responsible for enforcing `allow`, `approval`, `deny`, transport failures, and structured errors.

## Repository-context security boundary

The `repository` field is caller-provided policy context. It is not authentication, repository attestation, proof of checkout identity, or authorization by itself. Callers that can select the value can misrepresent it. High-risk integrations should supply it from a trusted wrapper or protected workflow and combine Kepenk with normal credential, branch, runner, and operating-system controls.

See `docs/repository-context.md` for examples and migration guidance.

## Deprecation and migration policy

For a normal incompatible change to a stable surface:

1. open a public issue describing the reason and proposed replacement;
2. document the deprecation in `CHANGELOG.md` and release notes;
3. keep the old surface working for at least one subsequent minor v0.x release when technically and securely practical;
4. provide a migration example;
5. protect both the old and replacement behavior with tests during the overlap.

A severe security problem may require immediate removal or stricter fail-closed behavior. Such a release must state the security reason, affected versions, and required user action.

## What is not guaranteed

This contract does not stabilize:

- direct imports of names beginning with `_`;
- undocumented Python APIs;
- exact exception text, human-readable console wording, or Markdown job summaries;
- ordering of JSON object keys;
- timestamps and hashes in audit entries;
- internal file locations outside documented integration files;
- third-party SDK APIs or runner behavior;
- v1.0 behavior beyond the explicit migration promises above.

## Regression protection

`tests/test_compatibility_contract.py` locks the declared machine-facing names, fields, versions, and exit codes. A contributor changing one of these assertions must also update this document, release notes, and migration guidance rather than silently weakening compatibility.
