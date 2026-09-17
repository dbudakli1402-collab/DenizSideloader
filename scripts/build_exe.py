"""Build a windowed Windows .exe with PyInstaller (no console).

Size diet: no --collect-all for PySide6 (it drags QtWebEngine ~200MB, QML,
Designer, Pdf ...). PyInstaller's Qt hooks auto-include what the imports need
(Core/Gui/Widgets + platform/style/imageformat plugins). Unused bindings and
REPL-only stacks are excluded explicitly.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Python modules never needed at runtime (QML/WebEngine UI, REPL/debug tools).
EXCLUDES = [
    # Qt modules we don't use (no QML/WebEngine/Pdf/Designer anywhere)
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.QtQml",
    "PySide6.QtQmlModels",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtQuick3DAssetImport",
    "PySide6.QtQuick3DHelpers",
    "PySide6.QtQuick3DRuntimeRender",
    "PySide6.QtQuick3DUtils",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtTest",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtGraphs",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "PySide6.QtSql",
    "PySide6.QtNfc",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSerialBus",
    "PySide6.QtPositioning",
    "PySide6.QtBluetooth",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtTextToSpeech",
    "PySide6.QtHttpServer",
    "PySide6.QtGraphsWidgets",
    # REPL/debug-only stacks (pymobiledevice3 CLI extras; app never imports them)
    "IPython",
    "ipykernel",
    "jedi",
    "parso",
    "prompt_toolkit",
    "pygments",
    "tornado",
    "zmq",
    "debugpy",
    "pytest",
    "_pytest",
]


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
    ]
    for mod in EXCLUDES:
        cmd += ["--exclude-module", mod]
    cmd.append("app/__main__.py")
    print("+", " ".join(cmd[:12]), f"... (+{len(EXCLUDES)} excludes)")
    return subprocess.call(cmd, cwd=ROOT)  # noqa: S603 - fixed argv, no user input, no shell


if __name__ == "__main__":
    raise SystemExit(main())
