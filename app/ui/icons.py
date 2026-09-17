"""Consistent stroke icon set, drawn with QPainter.

2px strokes, round caps, 24x24 grid — no emojis, no external assets.
Usage: ``from app.ui.icons import icon; btn.setIcon(icon("home"))``.
"""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

NAMES = {
    "home",
    "apps",
    "file",
    "phone",
    "book",
    "download",
    "history",
    "gear",
    "search",
    "bell",
    "sun",
    "moon",
    "min",
    "max",
    "close",
    "chevR",
    "chevL",
    "chevD",
    "check",
    "warn",
    "x",
    "refresh",
    "folder",
    "plus",
    "trash",
    "pen",
    "dots",
    "bolt",
    "shield",
    "info",
    "pause",
    "play",
    "sidebar",
    "upload",
    "link",
    "clock",
    "cpu",
}


def _pen(color: QColor, w: float = 2.0) -> QPen:
    pen = QPen(color)
    pen.setWidthF(w)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _draw(name: str, p: QPainter) -> None:
    cx, cy = 12.0, 12.0
    if name == "home":
        path = QPainterPath(QPointF(4, 11))
        path.lineTo(QPointF(12, 4.5))
        path.lineTo(QPointF(20, 11))
        p.drawPath(path)
        p.drawRect(QRectF(7.5, 10.5, 9, 8))
    elif name == "apps":
        for x, y in ((5, 5), (13, 5), (5, 13), (13, 13)):
            p.drawRoundedRect(QRectF(x, y, 6, 6), 1.8, 1.8)
    elif name == "file":
        path = QPainterPath(QPointF(7, 3.5))
        path.lineTo(QPointF(14, 3.5))
        path.lineTo(QPointF(17.5, 7))
        path.lineTo(QPointF(17.5, 20.5))
        path.lineTo(QPointF(7, 20.5))
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(14, 3.5), QPointF(14, 7))
        p.drawLine(QPointF(14, 7), QPointF(17.5, 7))
    elif name == "phone":
        p.drawRoundedRect(QRectF(7.5, 3, 9, 18), 2.4, 2.4)
        p.drawLine(QPointF(10.8, 18.6), QPointF(13.2, 18.6))
    elif name == "book":
        p.drawRoundedRect(QRectF(5.5, 4, 13, 16), 1.6, 1.6)
        p.drawLine(QPointF(5.5, 8), QPointF(18.5, 8))
        p.drawLine(QPointF(9, 4), QPointF(9, 20))
    elif name == "download":
        p.drawLine(QPointF(12, 4), QPointF(12, 14.5))
        path = QPainterPath(QPointF(7.5, 10.5))
        path.lineTo(QPointF(12, 15))
        path.lineTo(QPointF(16.5, 10.5))
        p.drawPath(path)
        p.drawLine(QPointF(5, 19.5), QPointF(19, 19.5))
    elif name == "upload":
        p.drawLine(QPointF(12, 15), QPointF(12, 4.5))
        path = QPainterPath(QPointF(7.5, 8.5))
        path.lineTo(QPointF(12, 4))
        path.lineTo(QPointF(16.5, 8.5))
        p.drawPath(path)
        p.drawLine(QPointF(5, 19.5), QPointF(19, 19.5))
    elif name in ("history", "clock"):
        p.drawEllipse(QRectF(4.5, 4.5, 15, 15))
        p.drawLine(QPointF(12, 8), QPointF(12, 12.2))
        p.drawLine(QPointF(12, 12.2), QPointF(15, 14))
        if name == "history":
            p.drawLine(QPointF(3.5, 6.5), QPointF(6, 5))
            p.drawLine(QPointF(3.5, 6.5), QPointF(4.5, 9))
    elif name == "gear":
        p.drawEllipse(QRectF(8.6, 8.6, 6.8, 6.8))
        for a in range(0, 360, 45):
            import math

            rad = math.radians(a)
            x1, y1 = cx + 7.6 * math.cos(rad), cy + 7.6 * math.sin(rad)
            x2, y2 = cx + 9.6 * math.cos(rad), cy + 9.6 * math.sin(rad)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    elif name == "search":
        p.drawEllipse(QRectF(4.5, 4.5, 12, 12))
        p.drawLine(QPointF(13.8, 13.8), QPointF(19.5, 19.5))
    elif name == "bell":
        path = QPainterPath()
        path.addRoundedRect(QRectF(6.5, 9.5, 11, 8), 3, 3)
        p.drawPath(path)
        p.drawLine(QPointF(9, 9.5), QPointF(9, 7))
        path2 = QPainterPath(QPointF(9, 7))
        path2.quadTo(QPointF(12, 3.5), QPointF(15, 7))
        path2.lineTo(QPointF(15, 9.5))
        p.drawPath(path2)
        p.drawLine(QPointF(10.5, 20), QPointF(13.5, 20))
    elif name == "sun":
        p.drawEllipse(QRectF(8.5, 8.5, 7, 7))
        for x1, y1, x2, y2 in [
            (12, 3, 12, 5),
            (12, 19, 12, 21),
            (3, 12, 5, 12),
            (19, 12, 21, 12),
            (5.6, 5.6, 7, 7),
            (17, 17, 18.4, 18.4),
            (18.4, 5.6, 17, 7),
            (7, 17, 5.6, 18.4),
        ]:
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    elif name == "moon":
        path = QPainterPath(QPointF(16.5, 4.5))
        path.quadTo(QPointF(9, 7), QPointF(9, 13.5))
        path.quadTo(QPointF(9, 19.5), QPointF(16, 20))
        path.quadTo(QPointF(12.5, 17), QPointF(12.5, 12.5))
        path.quadTo(QPointF(12.5, 8), QPointF(16.5, 4.5))
        p.drawPath(path)
    elif name == "min":
        p.drawLine(QPointF(6, 12), QPointF(18, 12))
    elif name == "max":
        p.drawRoundedRect(QRectF(6, 6, 12, 12), 2, 2)
    elif name == "close":
        p.drawLine(QPointF(6.5, 6.5), QPointF(17.5, 17.5))
        p.drawLine(QPointF(17.5, 6.5), QPointF(6.5, 17.5))
    elif name == "x":
        p.drawLine(QPointF(7, 7), QPointF(17, 17))
        p.drawLine(QPointF(17, 7), QPointF(7, 17))
    elif name == "chevR":
        path = QPainterPath(QPointF(9.5, 6))
        path.lineTo(QPointF(15, 12))
        path.lineTo(QPointF(9.5, 18))
        p.drawPath(path)
    elif name == "chevL":
        path = QPainterPath(QPointF(14.5, 6))
        path.lineTo(QPointF(9, 12))
        path.lineTo(QPointF(14.5, 18))
        p.drawPath(path)
    elif name == "chevD":
        path = QPainterPath(QPointF(6, 9.5))
        path.lineTo(QPointF(12, 15))
        path.lineTo(QPointF(18, 9.5))
        p.drawPath(path)
    elif name == "check":
        path = QPainterPath(QPointF(5, 12.5))
        path.lineTo(QPointF(10.5, 18))
        path.lineTo(QPointF(19, 7))
        p.drawPath(path)
    elif name == "warn":
        path = QPainterPath(QPointF(12, 4))
        path.lineTo(QPointF(20, 19))
        path.lineTo(QPointF(4, 19))
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(12, 9.5), QPointF(12, 13.5))
        p.drawPoint(QPointF(12, 16.3))
    elif name == "refresh":
        p.drawArc(QRectF(4.5, 4.5, 15, 15), 40 * 16, 280 * 16)
        path = QPainterPath(QPointF(19.5, 4))
        path.lineTo(QPointF(19.5, 9))
        path.lineTo(QPointF(14.5, 9))
        p.drawPath(path)
    elif name == "folder":
        path = QPainterPath(QPointF(4, 7))
        path.lineTo(QPointF(4, 18.5))
        path.lineTo(QPointF(20, 18.5))
        path.lineTo(QPointF(20, 7))
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(4, 7), QPointF(10, 7))
        p.drawLine(QPointF(10, 7), QPointF(11.5, 5))
        p.drawLine(QPointF(11.5, 5), QPointF(20, 5))
        p.drawLine(QPointF(20, 5), QPointF(20, 7))
    elif name == "plus":
        p.drawLine(QPointF(12, 5), QPointF(12, 19))
        p.drawLine(QPointF(5, 12), QPointF(19, 12))
    elif name == "trash":
        p.drawLine(QPointF(9, 6.5), QPointF(15, 6.5))
        p.drawLine(QPointF(6.5, 6.5), QPointF(17.5, 6.5))
        path = QPainterPath(QPointF(8, 6.5))
        path.lineTo(QPointF(8, 19))
        path.lineTo(QPointF(16, 19))
        path.lineTo(QPointF(16, 6.5))
        p.drawPath(path)
        p.drawLine(QPointF(10.5, 10), QPointF(10.5, 16))
        p.drawLine(QPointF(13.5, 10), QPointF(13.5, 16))
    elif name == "pen":
        path = QPainterPath(QPointF(14.5, 4.5))
        path.lineTo(QPointF(19.5, 9.5))
        path.lineTo(QPointF(11, 18))
        path.lineTo(QPointF(5.5, 19.5))
        path.lineTo(QPointF(7, 14))
        path.closeSubpath()
        p.drawPath(path)
    elif name == "dots":
        for yy in (6.5, 12, 17.5):
            p.drawPoint(QPointF(12, yy))
    elif name == "bolt":
        path = QPainterPath(QPointF(13.5, 3.5))
        path.lineTo(QPointF(7, 13.5))
        path.lineTo(QPointF(11.5, 13.5))
        path.lineTo(QPointF(10.5, 20.5))
        path.lineTo(QPointF(17, 10.5))
        path.lineTo(QPointF(12.5, 10.5))
        path.closeSubpath()
        p.drawPath(path)
    elif name == "shield":
        path = QPainterPath(QPointF(12, 3.5))
        path.lineTo(QPointF(18, 6))
        path.lineTo(QPointF(18, 12))
        path.quadTo(QPointF(18, 17), QPointF(12, 20.5))
        path.quadTo(QPointF(6, 17), QPointF(6, 12))
        path.lineTo(QPointF(6, 6))
        path.closeSubpath()
        p.drawPath(path)
        path2 = QPainterPath(QPointF(9, 12))
        path2.lineTo(QPointF(11.2, 14.2))
        path2.lineTo(QPointF(15.2, 9.8))
        p.drawPath(path2)
    elif name == "info":
        p.drawEllipse(QRectF(4.5, 4.5, 15, 15))
        p.drawPoint(QPointF(12, 8))
        p.drawLine(QPointF(12, 11), QPointF(12, 16))
    elif name == "pause":
        p.drawLine(QPointF(9.5, 6), QPointF(9.5, 18))
        p.drawLine(QPointF(14.5, 6), QPointF(14.5, 18))
    elif name == "play":
        path = QPainterPath(QPointF(8.5, 5.5))
        path.lineTo(QPointF(17.5, 12))
        path.lineTo(QPointF(8.5, 18.5))
        path.closeSubpath()
        p.drawPath(path)
    elif name == "sidebar":
        p.drawRoundedRect(QRectF(4, 4.5, 16, 15), 2, 2)
        p.drawLine(QPointF(10, 4.5), QPointF(10, 19.5))
    elif name == "link":
        p.drawArc(QRectF(9.5, 9.5, 10, 10), 0, 5760 // 2)
        p.drawArc(QRectF(4.5, 4.5, 10, 10), 0, 5760 // 2)
    elif name == "cpu":
        p.drawRoundedRect(QRectF(7, 7, 10, 10), 2, 2)
        for x in (10, 14):
            p.drawLine(QPointF(x, 4.5), QPointF(x, 7))
            p.drawLine(QPointF(x, 17), QPointF(x, 19.5))
            p.drawLine(QPointF(4.5, x - 4 + 4), QPointF(7, x - 4 + 4))
        p.drawLine(QPointF(4.5, 10), QPointF(7, 10))
        p.drawLine(QPointF(4.5, 14), QPointF(7, 14))
        p.drawLine(QPointF(17, 10), QPointF(19.5, 10))
        p.drawLine(QPointF(17, 14), QPointF(19.5, 14))
    else:
        p.drawEllipse(QRectF(7, 7, 10, 10))


@lru_cache(maxsize=256)
def _render(name: str, size: int, color: str) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    scale = size / 24.0
    p.scale(scale, scale)
    p.setPen(_pen(QColor(color), 2.0))
    p.setBrush(Qt.BrushStyle.NoBrush)
    _draw(name if name in NAMES else "info", p)
    p.end()
    return pm


def icon(name: str, size: int = 20, color: str = "#c3cad9") -> QIcon:
    return QIcon(_render(name, size, color))
