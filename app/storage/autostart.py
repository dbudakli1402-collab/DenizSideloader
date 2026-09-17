"""Startup/autostart helpers (Windows registry) + tray note."""

from __future__ import annotations

import sys


def set_start_with_windows(enable: bool, app_name: str = "DenizSideloader") -> bool:
    """Enable/disable autostart on Windows. Returns success. No-op elsewhere."""
    if sys.platform != "win32":
        return False
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
        )
        if enable:
            exe = sys.executable
            # Quote properly; no shell injection: single value, no shell.
            cmd = f'"{exe}" -m app.main'
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False
