"""App branding: logo paths (source tree and PyInstaller bundle)."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon


def assets_dir() -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        cand = Path(base) / "assets"
        if cand.is_dir():
            return cand
    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        cand = parent / "assets"
        if cand.is_dir():
            return cand
    return here.parent / "assets"


def logo_png(size: int = 64) -> Path:
    return assets_dir() / f"logo-{size}.png"


def logo_ico() -> Path:
    return assets_dir() / "logo.ico"


def window_icon() -> QIcon:
    ico = logo_ico()
    if ico.is_file():
        return QIcon(str(ico))
    png = logo_png(64)
    if png.is_file():
        return QIcon(str(png))
    return QIcon()
