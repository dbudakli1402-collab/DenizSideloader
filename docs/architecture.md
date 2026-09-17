# Architecture

```
DenizSideloader/
  app/
    main.py          # entry: builds services, applies theme, runs Qt loop
    core/            # config, logging (redacting), errors, events, app state
    device/          # DeviceProvider interface + pymobiledevice3 + mock
    ipa/             # parser (zip+plist, no code exec) + library (JSON index)
    signing/         # SigningProvider interface + Apple/Local providers
    installation/    # state-machine orchestrator (Select→…→Verify→Done)
    downloads/       # HTTPS streaming manager (progress/speed/ETA/SHA-256)
    security/        # keyring credentials, URL/path/filename validation
    storage/         # JSON settings, autostart
    ui/              # PySide6: theme, MainWindow, 7 pages, dialogs, widgets
  tests/             # 52 tests, all hardware-mocked
  docs/ assets/ scripts/ .github/
```

## Technology decision

**Python 3.10+ + PySide6 (Qt6, native).** Why:

1. **Windows-first native desktop** — real windows, tray, file dialogs, no
   browser/localhost workaround.
2. **No Chromium overhead** — Qt renders natively; satisfies the
   "no unnecessary Electron/Chromium processes" requirement. (Rust/Tauri was
   considered but needs a Rust toolchain + MSVC; Python+Qt builds and tests
   with just `pip`.)
3. **Maintainable for open source** — small dependency set
   (`PySide6`, `requests`, `keyring`), strict layering, everything mockable.
4. **Testable without hardware** — providers behind interfaces; CI runs the
   full suite with mocks.

## Key flows

**Install:** `MainWindow._install_path` → `InstallationJob` →
`InstallationService.run` on a `QThread` (UI never blocks) →
steps emitted back to `InstallDialog`. Signing without valid assets and
install without the device backend **fail honestly** with guidance.

**Downloads:** `URL → Validate → Download (streamed, cert-verified) →
Verify (SHA-256) → Store (traversal-safe) → auto-import`.

**Secrets:** `keyring` (Windows Credential Manager) for username/team hints
only. Passwords live in memory for one operation, never touch disk/logs/git.
