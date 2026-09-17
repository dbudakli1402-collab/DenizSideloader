# Windows setup

## PC

1. Windows 10/11, Python 3.10+.
2. Install Apple Mobile Device support: **iTunes (from apple.com)** or the
   **Apple Devices** app from the Microsoft Store.
3. `pip install DenizSideloader[device]` for the real device backend
   (optional but needed for actual installs).
4. Run `python -m app` from the `DenizSideloader` folder, or build
   `release/DenizSideloader.exe` via `python scripts/build_exe.py`
   (windowed — no console during normal use).

## iPhone

1. Connect via USB (use a data cable, not charge-only).
2. Unlock the iPhone.
3. Tap **Trust** when prompted, enter the device passcode.
4. Keep the phone unlocked and connected during installation.

## Troubleshooting

| Symptom | Fix |
| ------- | --- |
| No device found | Unlock, re-tap Trust, try another cable/port, install iTunes/Apple Devices |
| Trust prompt never appears | Reconnect USB; check for a charge-only cable |
| Signing incomplete | Add `.mobileprovision` under Settings → Signing |
| App expired after 7 days | Free-account limit — re-install (see `docs/signing.md`) |
