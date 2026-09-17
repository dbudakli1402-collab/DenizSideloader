# Deniz Sideloader

> A modern open-source desktop application for managing and legitimately sideloading IPA applications to your own iPhone.

[![CI](https://github.com/dbudakli1402-collab/DenizSideloader/actions/workflows/ci.yml/badge.svg)](https://github.com/dbudakli1402-collab/DenizSideloader/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/dbudakli1402-collab/DenizSideloader)](https://github.com/dbudakli1402-collab/DenizSideloader/releases)

![App screenshot](assets/screenshot-home.png)
![Library screenshot](assets/screenshot-library.png)

## Features

- **Home** — connection status card, big **Choose IPA** / **Download IPA** actions, recent IPAs
- **IPA Library** — import, drag & drop, metadata (name, bundle ID, version, size, icon), install, delete
- **My iPhone** — USB detection, device name, iOS version, Trust guidance
- **Installed Apps** — backend-backed listing (honest "unavailable" state otherwise)
- **Downloads** — direct IPA URLs with progress, speed, ETA, pause/cancel, SHA-256, auto-import
- **Installation workflow** — Select → Analyze → Detect → Signing check → Prepare → Sign → Install → Verify → Done, with live progress dialog
- **Modular signing** — free (7-day) / paid Apple Developer + local provisioning files; passwords never stored
- **Settings** — General, iPhone, Downloads, Security, Signing; OS-keychain credentials; autostart; tray
- **Security** — HTTPS-only, cert validation, path-traversal protection, redacted logs, no telemetry
- Dark, Apple-inspired native UI (Qt, no Chromium/Electron overhead), first-launch wizard

## Requirements

- Windows 10/11, Python 3.10+
- iPhone with USB data cable
- Apple Mobile Device support: iTunes (apple.com) or Apple Devices app
- For real installs: `pip install DenizSideloader[device]` (pymobiledevice3) + your own signing assets

## Installation

```powershell
cd DenizSideloader
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app
```

Build a console-free exe:

```powershell
pip install -r requirements-dev.txt
python scripts/build_exe.py   # -> release/DenizSideloader.exe
```

## iPhone setup

1. Connect via USB, unlock the iPhone.
2. Tap **Trust**, enter passcode.
3. Keep connected during installs. See `docs/windows-setup.md`.

## Apple Developer requirements

Free Apple ID: apps expire after ~7 days, few apps max, weekly re-install.
Paid membership: ~12-month validity. Details: `docs/signing.md`.
Your password is **never stored** — only a username hint goes to Windows
Credential Manager.

## Sideloading guide

1. Import an `.ipa` (Library → Import / drag & drop) or paste a direct URL (Downloads).
2. Go Home → **Choose IPA** (or Install in the Library).
3. Confirm the target iPhone → watch the progress dialog.
4. "Installation complete" → Done. Do not disconnect mid-install.

## What actually works today

| Area | Status |
| ---- | ------ |
| IPA parsing/metadata/library | ✅ real |
| Download manager + SHA-256 | ✅ real |
| Device detection (with backend + drivers + trust) | ✅ real |
| Signing-assets workflow | ✅ real (needs your profile) |
| On-device install | ✅ real when backend + assets present; otherwise **honest failure with steps** |
| Installed-apps listing | ✅ when backend supports it; otherwise labeled unavailable |

No fake-success buttons anywhere — see `docs/limitations.md`.

## Troubleshooting

| Symptom | Fix |
| ------- | --- |
| No iPhone found | unlock, Trust, cable/port, iTunes/Apple Devices |
| Trust required loop | reconnect, unlock first, then Trust |
| Signing incomplete | add `.mobileprovision` in Settings → Signing |
| 7-day expiry | free-account Apple policy, re-install |
| Download fails | must be a direct `https://…*.ipa` link |

Errors always show causes + Retry/Help; technical details under "Show details".

## Security

HTTPS-only downloads, cert validation, SHA-256, traversal/shell-injection
protections, redacted structured logs, OS-keychain-only hints, no telemetry.
Report issues privately per SECURITY.md. **Never paste passwords/tokens/keys
into issues.**

## FAQ

**Is this a jailbreak?** No. Only Apple's legitimate signing mechanism.
**Does it store my Apple password?** Never.
**Does it work without an iPhone?** Library/downloads/settings do; installs need hardware.
**Why "failed" instead of installing?** Missing backend/drivers/assets — the message tells you exactly what to add.

## Development

```powershell
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests
python -m ruff check app tests
python -m ruff format --check app tests
python -m mypy app
$env:DENIZ_MOCK_DEVICES = "1"; python -m app   # simulated iPhone
```

Tech choice: **Python + PySide6 (Qt, native)** — no Chromium overhead, no
browser/localhost hack, builds with just pip. See `docs/architecture.md`.

## Build & Release

- CI (Windows): lint → format-check → typecheck → tests → secret scan → packaging smoke test.
- Tag `v*` triggers the exe build (`scripts/build_exe.py`) + artifact upload.
- Versioning: `app/__init__.py::__version__` (+ git tags for releases).

## Contributing / License

See CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md. License: MIT (LICENSE).
