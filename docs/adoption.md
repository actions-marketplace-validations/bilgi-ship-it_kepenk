# Adopt Kepenk in a repository

This guide reaches a first deterministic decision in five shell commands and then shows how to turn that experiment into verifiable repository adoption.

## First decision in five commands

From the repository you want to protect:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install "https://github.com/bilgi-ship-it/kepenk/archive/refs/tags/v0.3.0.zip"
kepenk init
kepenk check --action shell --command "python -m pytest"
```

On Windows PowerShell, replace the activation command with:

```powershell
.\.venv\Scripts\Activate.ps1
```

The starter policy is conservative. Review `kepenk.yaml` before treating any result as suitable for your repository.

## Choose an integration

### Local CLI

Use `kepenk check` to inspect a proposed action without running it. Use `kepenk run` only when you intentionally want Kepenk to launch an allowed or approved command.

### pre-commit

Use the managed hook when policy files should be validated before they reach CI. See [the pre-commit guide](integrations/pre-commit.md).

### GitHub Actions

Use the repository action to validate a policy or evaluate an explicit action in CI. Pin the verified `v0.3.0` tag or an exact reviewed commit. See [the GitHub Action guide](integrations/github-action.md).

### JSONL or MCP

Use the JSONL protocol for a long-running local process. Use the MCP adapter for an MCP-capable host. In both cases, the caller must enforce the returned decision. See the [JSONL](integrations/jsonl-protocol.md) and [MCP](integrations/mcp.md) guides.

## Add policy regression tests

Kepenk v0.3.0 includes `kepenk test`, which compares representative actions with expected effects and rule IDs:

```bash
kepenk --policy kepenk.yaml test --tests kepenk.tests.yaml
```

Keep the policy and test suite together so a pull request shows both the rule change and its intended security effect. See [the policy-testing guide](policy-testing.md).

## Verification checklist

Before requesting a registry entry, confirm that:

- the repository is public;
- the Kepenk integration is visible at a stable public URL;
- the policy validates successfully;
- representative allow, approval, deny, and default behavior are checked;
- no credentials, private logs, private keys, signed production receipts, or proprietary source are included;
- the repository documentation states that Kepenk is a policy layer rather than a sandbox;
- the maintainer agrees to be listed in `ADOPTERS.md`.

An integration can be real without being listed. The registry exists only for public, consent-based evidence.

## Submit adoption evidence

1. Fork or branch this repository.
2. Add one row to the correct table in [`ADOPTERS.md`](../ADOPTERS.md).
3. Use a permalink to the policy, workflow, hook, adapter, or integration documentation.
4. Complete [the adopter pull-request template](../.github/PULL_REQUEST_TEMPLATE/adopter.md).
5. Optionally add a case study based on [the case-study template](case-study-template.md).

Founding-team pilots and independent adopters are kept in separate sections. A founding-team repository must never be presented as independent adoption.

## Evidence review

A registry pull request is checked for:

- repository ownership or maintainer authorization;
- a working public evidence link;
- clear integration type;
- honest classification as independent or founding-team;
- absence of unsupported user, download, security, or production claims.

Acceptance into the registry is not a security certification or endorsement. It records only that the linked public repository shows a Kepenk integration at the verification date.

## Remove an entry

A listed maintainer may request removal through an issue or pull request. The project may also remove an entry when its evidence link disappears or no longer shows Kepenk use. No explanation beyond the removal request is required from the listed maintainer.
