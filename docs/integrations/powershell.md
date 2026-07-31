# Windows and PowerShell integration

Kepenk evaluates the command string it receives; it does not invoke a shell parser and does not use `shell=True`. The provided PowerShell policy is therefore an explicit set of conservative string and regular-expression checks, not a complete PowerShell parser.

## Start with the example policy

Copy [`examples/powershell/kepenk.yaml`](../../examples/powershell/kepenk.yaml) into a project:

```powershell
Copy-Item examples/powershell/kepenk.yaml .\kepenk.yaml
kepenk --policy .\kepenk.yaml validate
```

Route a command through Kepenk by passing the executable and every argument separately:

```powershell
kepenk --policy .\kepenk.yaml run -- pwsh -NoProfile -Command "Invoke-Pester"
```

Kepenk ultimately calls `subprocess.run([...], shell=False)`. This avoids an additional command-shell expansion layer and preserves the caller's argument boundaries.

## Expected decisions

### Allowed

```powershell
kepenk check --action shell --command 'pwsh -NoProfile -Command "Invoke-Pester"'
kepenk check --action shell --command 'pwsh -NoProfile -Command "Get-ChildItem src"'
kepenk check --action shell --command 'git status --short'
```

### Requires approval

```powershell
kepenk check --action shell --command 'git push origin main'
kepenk check --action shell --command 'pwsh -NoProfile -Command "Publish-Module -Path .\dist"'
kepenk check --action shell --command 'dotnet nuget push package.nupkg'
```

### Denied

```powershell
kepenk check --action shell --command 'pwsh -NoProfile -Command "Remove-Item C:\work -Recurse -Force"'
kepenk check --action shell --command 'cmd /c rd C:\work /s /q'
```

## Quoting and normalization limitations

- `kepenk check --command` receives a display string. Quoting has already been interpreted by the calling terminal before Kepenk sees it.
- `kepenk run -- ...` is safer for execution because arguments remain a list and Kepenk launches them with `shell=False`.
- PowerShell aliases and user-defined functions can obscure intent. The example policy covers common built-ins such as `Remove-Item`, `ri`, `Invoke-Pester`, and publishing commands, but cannot identify every alias or dynamically constructed command.
- Encoded commands, `Invoke-Expression`, string concatenation, downloaded scripts, and nested shells require stricter organization-specific deny rules or an external sandbox.
- Windows paths are not normalized by the policy engine. Regexes evaluate the command exactly as received.
- Rule order matters. Deny rules must remain before approval and allow rules.

Kepenk is an approval boundary, not a complete PowerShell security sandbox. Use constrained credentials, isolated runners, and operating-system controls for untrusted execution.
