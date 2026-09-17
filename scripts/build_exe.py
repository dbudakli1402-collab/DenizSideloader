"""Build a windowed Windows .exe with PyInstaller (no console)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "DenizSideloader",
        "--distpath",
        str(ROOT / "release"),
        "--workpath",
        str(ROOT / "build"),
        "--paths",
        str(ROOT),
        "--collect-all",
        "PySide6",
        "app/__main__.py",
    ]
    print("+", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)  # noqa: S603 - fixed argv, no user input, no shell


if __name__ == "__main__":
    raise SystemExit(main())
