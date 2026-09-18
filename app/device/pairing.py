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
