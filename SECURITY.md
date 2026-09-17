# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Instead, open a private security advisory on GitHub
(Security tab → Advisories) or contact the maintainers privately.
Include:

- What you found and where (file, version/commit)
- Steps to reproduce (without real credentials)
- What you expected vs. what happened

We aim to acknowledge reports within 7 days.

## Credential Handling Rules

This project deals with Apple IDs and signing assets. The following rules
are enforced by design and by tests:

- **Never store Apple passwords.** Not in JSON, not in `.env`, not in logs,
  not in GitHub issues. Only a username *hint* may be kept in the OS keychain
  (Windows Credential Manager via `keyring`).
- **No secrets in the repository.** No API keys, certificates (`.p12`,
  `.pfx`, `.pem`, `.key`), provisioning profiles (`.mobileprovision`),
  tokens, or private keys. CI fails if such files are present.
- **No secrets in logs.** All log output passes through a redacting filter
  (`app/core/logging.py`); tests verify password/token/private-key redaction.
- **Downloads:** HTTPS only (HTTP only for `localhost` in tests),
  certificate validation enabled, SHA-256 recorded for every download.
- **No shell injection:** user input is never passed to a shell; file paths
  are validated against traversal (`safe_join`).

## What Counts as a Vulnerability Here

- Credential or token leakage (logs, files, UI)
- Path traversal / arbitrary file write via IPA import or downloads
- SSRF via the download manager (private-network bypass)
- Signature/state confusion that reports "installed" when nothing happened

Out of scope: jailbreak/DRM topics — this project will not implement those,
so please do not request them.
