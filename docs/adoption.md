# Adopt Kepenk in a repository

This guide reaches a first deterministic decision in five shell commands and then shows how to turn that experiment into verifiable repository adoption.

## First decision in five commands

From the repository you want to protect:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install "https://github.com/bilgi-ship-it/kepenk/archive/refs/tags/v0.4.0.zip"
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

Use the repository action to validate a policy or evaluate an explicit action in CI. Pin the verified `v0.4.0` tag or an exact reviewed commit. See [the GitHub Action guide](integrations/github-action.md).

### JSONL or MCP

Use the JSONL protocol for a long-running local process. Use the MCP adapter for an MCP-capable host. In both cases, the caller must enforce the returned decision. See the [JSONL](integrations/jsonl-protocol.md) and [MCP](integrations/mcp.md) guides.

## Add policy regression tests

Kepenk v0.4.0 includes `kepenk test`, which compares representative actions with expected effects and rule IDs:

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

## Create an offline evidence manifest

Kepenk v0.4.0 includes an optional version-1 adoption-evidence manifest. It standardizes public integration facts without telemetry or network access.

Copy the [checked-in example](../examples/adoption/ustaca-ai.json) to `.kepenk/adoption.json`, change every field to the adopting repository, and validate it with the verified `v0.4.0` release:

```bash
kepenk validate-adoption --evidence .kepenk/adoption.json
```

Machine-readable validation:

```bash
kepenk validate-adoption \
  --evidence .kepenk/adoption.json \
  --json
```

The manifest records classification, repository, maintainer consent, integration type, Kepenk version, evidence URL, and verification date. See [the adoption-evidence guide](adoption-evidence.md) and [versioned JSON Schema](../schemas/kepenk-adoption-evidence-v1.schema.json).

A structurally valid manifest does not prove ownership, identity, URL availability, production security, or independent adoption. Registry review remains human and consent based.

## Submit adoption evidence

1. Fork or branch this repository.
2. Add one row to the correct table in [`ADOPTERS.md`](../ADOPTERS.md).
3. Use a permalink to the policy, workflow, hook, adapter, integration documentation, or adoption manifest.
4. Complete [the adopter pull-request template](../.github/PULL_REQUEST_TEMPLATE/adopter.md).
5. Include the locally validated `.kepenk/adoption.json` permalink when one is available.
6. Optionally add a case study based on [the case-study template](case-study-template.md).

Founding-team pilots and independent adopters are kept in separate sections. A founding-team repository must never be presented as independent adoption.

## Evidence review

A registry pull request is checked for:

- repository ownership or maintainer authorization;
- a working public evidence link;
- clear integration type;
- honest classification as independent or founding-team;
- agreement between any manifest and the linked public repository;
- absence of unsupported user, download, security, or production claims.

Acceptance into the registry is not a security certification or endorsement. It records only that the linked public repository shows a Kepenk integration at the verification date.

## Remove an entry

A listed maintainer may request removal through an issue or pull request. The project may also remove an entry when its evidence link disappears or no longer shows Kepenk use. No explanation beyond the removal request is required from the listed maintainer.
