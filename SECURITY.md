# Security Policy

## Supported versions

Kepenk is currently alpha software. Only the latest release receives fixes.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could enable policy bypass, command injection, audit forgery, or unsafe execution.

Report privately through GitHub Security Advisories. Include:

- affected version or commit
- reproduction steps
- expected and actual behavior
- security impact
- suggested mitigation, if available

## Security boundaries

Kepenk is a policy and approval layer, not a sandbox. It cannot contain a compromised process or prevent direct execution that bypasses the Kepenk wrapper. Deploy it together with least privilege, isolated environments, protected secrets, and operating-system controls.
