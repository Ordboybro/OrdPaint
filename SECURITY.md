# Security Policy

OrdPaint is a local desktop application that reads, writes and exports user-controlled image/project files. File integrity, parser safety and resource limits are therefore treated as security-relevant concerns.

## Reporting a vulnerability

Please report security-sensitive issues privately through GitHub rather than publishing exploit details in a public issue. Include the affected commit/version, operating system, reproduction steps, expected and actual behavior, and security or data-integrity impact.

Do not include private project files, credentials or other secrets in a report.

## Security boundaries

- Project files must be validated before use.
- Resource limits should prevent pathological project data from exhausting memory or CPU.
- Project saves should remain atomic so failed writes do not silently destroy the previous file.
- Imported images and project data should not be treated as trusted input.
- Crash diagnostics should avoid recording secrets or unrelated private data.

Changes to project parsing, persistence, clipboard handling, image import/export, resource limits or filesystem operations should include regression coverage where practical.

OrdPaint is not a security-audited application. This policy describes engineering expectations; it is not a security guarantee.
