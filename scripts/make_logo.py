"""Generate the Deniz Sideloader app logo (D badge, blue glow).

Outputs: assets/logo-256/128/64/48/32/16.png + assets/logo.ico + assets/logo.svg
No third-party artwork: gradient rounded square + bold D, drawn in code.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, ".")

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPixmap,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


def draw(size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHints(
        QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing,
        True,
    )
    m = size / 256.0
    # glow: layered translucent rounded rects behind the badge
    for i, alpha in ((26, 18), (20, 26), (14, 36)):
        r = i * m
        path = QPainterPath()
        path.addRoundedRect(QRectF(r, r, size - 2 * r, size - 2 * r), 52 * m, 52 * m)
        p.fillPath(path, QColor(22, 131, 255, alpha))
    # badge body
    body = QPainterPath()
    body.addRoundedRect(QRectF(30 * m, 30 * m, 196 * m, 196 * m), 46 * m, 46 * m)
    grad = QLinearGradient(30 * m, 30 * m, 226 * m, 226 * m)
    grad.setColorAt(0.0, QColor("#0a54d6"))
    grad.setColorAt(0.55, QColor("#1683ff"))
    grad.setColorAt(1.0, QColor("#3fd2ff"))
    p.fillPath(body, grad)
    # subtle top highlight
    hi = QPainterPath()
    hi.addRoundedRect(QRectF(30 * m, 30 * m, 196 * m, 98 * m), 46 * m, 46 * m)
    p.fillPath(hi, QColor(255, 255, 255, 22))
    # letter D as vector shapes (no font dependency, always crisp)
    white = QColor("#ffffff")
    p.fillRect(QRectF(78 * m, 68 * m, 34 * m, 120 * m), white)
    bowl = QPainterPath()
    bowl.setFillRule(Qt.FillRule.OddEvenFill)
    bowl.moveTo(112 * m, 68 * m)
    bowl.arcTo(QRectF(52 * m, 68 * m, 120 * m, 120 * m), -90.0, 180.0)
    bowl.closeSubpath()
    bowl.moveTo(112 * m, 102 * m)
    bowl.arcTo(QRectF(86 * m, 102 * m, 52 * m, 52 * m), -90.0, 180.0)
    bowl.closeSubpath()
    p.fillPath(bowl, white)
    p.end()
    return pm


def main() -> int:
    from PySide6.QtWidgets import QApplication

    _app = QApplication([])
    os.makedirs(ASSETS, exist_ok=True)
    for px in (256, 128, 64, 48, 32, 16):
        pm = draw(256).scaled(px, px, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        out = os.path.join(ASSETS, f"logo-{px}.png")
        pm.save(out, "PNG")
        print("wrote", out)
    # multi-size ICO for Windows (exe + installer + taskbar)
    try:
        from PIL import Image

        imgs = [Image.open(os.path.join(ASSETS, f"logo-{px}.png")) for px in (256, 48, 32, 16)]
        imgs[0].save(os.path.join(ASSETS, "logo.ico"), sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
        print("wrote", os.path.join(ASSETS, "logo.ico"))
    except Exception as exc:
        print("ICO skipped:", exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
