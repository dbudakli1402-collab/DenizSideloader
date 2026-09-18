"""Pairing records: read-only listing of local lockdown pair records.

Shows WHICH devices paired (filenames only) so users can manage trust.
Never reads or exposes record contents (those contain secrets).
"""

from __future__ import annotations

import os
from pathlib import Path


def _candidate_dirs() -> list[Path]:
    home = Path.home()
    roots = [
        Path(os.environ.get("APPDATA", "")) / "pymobiledevice3",
        home / ".pymobiledevice3",
        Path("/var/lib/lockdown"),
    ]
    out: list[Path] = []
    for r in roots:
        try:
            if r.is_dir():
                out.append(r)
        except Exception:
            continue
    return out


def list_pair_records() -> tuple[list[Path], list[str]]:
    """Return (record dirs searched, record filenames found, no contents)."""
    names: list[str] = []
    searched: list[Path] = []
    for root in _candidate_dirs():
        searched.append(root)
        try:
            for f in sorted(root.rglob("*.plist")) + sorted(root.rglob("*.pem")):
                names.append(f.name)
        except Exception:
            continue
    # deduplicate, cap
    seen: list[str] = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return searched, seen[:50]


def pair_records_folder() -> Path | None:
    for root in _candidate_dirs():
        return root
    return None


def load_usbmux_record(udid: str) -> bytes | None:
    """Load this PC's usbmux pairing record for *udid* (memory only).

    Used to place the record into a companion app container on the same
    trusted device (iloader's pairing step). Returns None when absent.
    """
    try:
        from pymobiledevice3.pair_records import get_usbmux_pairing_record
    except Exception:
        return None
    try:
        record = get_usbmux_pairing_record(udid)
    except Exception:
        return None
    if record is None:
        return None
    try:
        import plistlib

        if isinstance(record, dict):
            return plistlib.dumps(record)
        if isinstance(record, (bytes, bytearray)):
            return bytes(record)
        path = Path(str(record))
        if path.is_file():
            return path.read_bytes()
    except Exception:
        return None
    return None


def export_pairing(udid: str, dest: Path) -> Path:
    """Copy the local pairing record to a user-chosen path (explicit action)."""
    data = load_usbmux_record(udid)
    if not data:
        raise FileNotFoundError("Kein lokaler Pairing-Eintrag für dieses Gerät gefunden.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest


def delete_stored() -> int:
    """Delete locally stored pairing records. Returns number removed."""
    removed = 0
    for root in _candidate_dirs():
        try:
            for f in list(root.rglob("*.plist")) + list(root.rglob("*.pem")):
                try:
                    f.unlink()
                    removed += 1
                except Exception:
                    continue
        except Exception:
            continue
    # pymobiledevice3 cache folder
    try:
        from pymobiledevice3.pair_records import OSUTILS

        cache = OSUTILS.pair_record_path
        if cache.is_dir():
            for f in list(cache.glob("*.plist")):
                try:
                    f.unlink()
                    removed += 1
                except Exception:
                    continue
    except Exception:
        pass
    return removed
