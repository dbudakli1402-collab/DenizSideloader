"""Deniz Sideloader Design System v2.

Premium dark navy theme, electric-blue accent, rounded cards, micro-spacing.
Single source of truth for colors, radii, typography and shared widgets.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

# -- palette ---------------------------------------------------------------
BG_APP = "#05070d"
BG_SIDE = "#080d18"
BG_TOP = "#080d18"
CARD = "#0d1424"
CARD_2 = "#111a2e"
BORDER = "#1d2942"
BORDER_SOFT = "#16203a"
TEXT = "#f2f5fa"
MUTED = "#8b94a9"
FAINT = "#5d6680"
ACCENT = "#2f7bff"
ACCENT_DEEP = "#0a54d6"
CYAN = "#3fd2ff"
GREEN = "#35d399"
GREEN_BG = "rgba(53,211,153,0.12)"
RED = "#ff6b6b"
RED_BG = "rgba(255,107,107,0.12)"
AMBER = "#ffb020"
AMBER_BG = "rgba(255,176,32,0.12)"
BLUE_BG = "rgba(47,123,255,0.14)"

RADIUS_SM = 10
RADIUS_MD = 14
RADIUS_LG = 18
RADIUS_XL = 22

FONT = "'Segoe UI', 'Inter', sans-serif"

QSS_DARK = f"""
* {{ font-family: {FONT}; }}
QMainWindow, QWidget#shell, QWidget#pageRoot {{ background: {BG_APP}; color: {TEXT}; }}
QWidget#sidebar {{ background: {BG_SIDE}; border-right: 1px solid {BORDER_SOFT}; }}
QWidget#topbar {{ background: {BG_TOP}; border-bottom: 1px solid {BORDER_SOFT}; }}
QLabel#brand {{ font-size: 15px; font-weight: 800; letter-spacing: 0.2px; }}
QLabel#brandSub {{ font-size: 11px; color: {MUTED}; }}
QLabel#heroKicker {{ font-size: 22px; font-weight: 600; color: {TEXT}; }}
QLabel#heroTitle {{ font-size: 40px; font-weight: 800; }}
QLabel#heroSub {{ font-size: 14px; color: {MUTED}; }}
QLabel#pageTitle {{ font-size: 24px; font-weight: 800; }}
QLabel#section {{ font-size: 12px; font-weight: 700; color: {MUTED}; letter-spacing: 1.2px; }}
QLabel#cardTitle {{ font-size: 15px; font-weight: 700; }}
QLabel#muted {{ color: {MUTED}; font-size: 12.5px; }}
QLabel#big {{ font-size: 26px; font-weight: 800; }}
QFrame#card {{ background: {CARD}; border: 1px solid {BORDER_SOFT}; border-radius: {RADIUS_LG}px; }}
QFrame#card2 {{ background: {CARD_2}; border: 1px solid {BORDER_SOFT}; border-radius: {RADIUS_MD}px; }}
QFrame#hero {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0b1e4b, stop:0.55 #0a1430, stop:1 #070b16);
  border: 1px solid #22345f; border-radius: {RADIUS_XL}px; }}
QFrame#dropzone {{ background: rgba(47,123,255,0.05); border: 2px dashed #2c4a85; border-radius: {RADIUS_LG}px; }}
QFrame#dropzone[active="true"] {{ background: rgba(47,123,255,0.12); border: 2px dashed {CYAN}; }}
QListWidget {{ background: transparent; border: none; outline: none; }}
QListWidget::item {{ background: transparent; border: none; }}
QListWidget#nav {{ background: transparent; border: none; outline: none; font-size: 13.5px; }}
QListWidget#nav::item {{ color: #c3cad9; border-radius: {RADIUS_SM}px; padding: 9px 12px; margin: 1px 0px; }}
QListWidget#nav::item:hover {{ background: #101a30; color: #ffffff; }}
QListWidget#nav::item:selected {{
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_DEEP}, stop:1 {ACCENT});
  color: #ffffff; font-weight: 700; }}
QPushButton#primary {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_DEEP}, stop:1 {ACCENT});
  color: white; border: none; border-radius: 12px; padding: 11px 20px; font-size: 13.5px; font-weight: 700; }}
QPushButton#primary:hover {{ background: {ACCENT}; }}
QPushButton#primary:disabled {{ background: #1a2440; color: {FAINT}; }}
QPushButton#ghost {{ background: #131c33; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 12px;
  padding: 10px 16px; font-size: 13px; font-weight: 600; }}
QPushButton#ghost:hover {{ background: #1a2542; border: 1px solid #2c3f6b; }}
QPushButton#iconbtn {{ background: transparent; border: none; border-radius: 9px; padding: 7px; }}
QPushButton#iconbtn:hover {{ background: #16203a; }}
QPushButton#danger {{ background: {RED_BG}; color: {RED}; border: 1px solid rgba(255,107,107,0.35);
  border-radius: 10px; padding: 8px 14px; font-weight: 600; }}
QFrame#tile {{ background: #131c33; border: 1px solid {BORDER}; border-radius: 12px; }}
QFrame#tile:hover {{ background: #1a2542; border: 1px solid #2c3f6b; }}
QLineEdit#search {{ background: #0b1224; border: 1px solid {BORDER}; border-radius: 11px;
  padding: 9px 12px 9px 38px; color: {TEXT}; font-size: 13px; selection-background-color: {ACCENT}; }}
QLineEdit#search:focus {{ border: 1px solid {ACCENT}; }}
QLineEdit, QComboBox, QSpinBox {{ background: #0b1224; border: 1px solid {BORDER}; border-radius: 10px;
  padding: 8px 11px; color: {TEXT}; font-size: 13px; selection-background-color: {ACCENT}; }}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QProgressBar#bar {{ background: #16203a; border: none; border-radius: 7px; height: 12px;
  text-align: center; color: {MUTED}; font-size: 10px; }}
QProgressBar#bar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_DEEP}, stop:1 {CYAN});
  border-radius: 7px; }}
QProgressBar#barGreen::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f9d6c, stop:1 {GREEN}); }}
QLabel#chip {{ border-radius: 9px; padding: 3px 10px; font-size: 11.5px; font-weight: 700; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: #22304f; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #2e4066; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; }}
QScrollBar::handle:horizontal {{ background: #22304f; border-radius: 5px; min-width: 30px; }}
QCheckBox {{ color: {TEXT}; font-size: 13px; spacing: 9px; }}
QCheckBox::indicator {{
  width: 17px; height: 17px; border-radius: 6px;
  border: 1px solid #33436b; background: #0e1730; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border: 1px solid {ACCENT}; }}
QToolTip {{ background: #141d36; color: {TEXT}; border: 1px solid {BORDER}; padding: 6px 9px; border-radius: 8px; }}
QStatusBar {{ background: {BG_APP}; color: {FAINT}; font-size: 12px; }}
QMenu {{ background: #0e1730; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px; }}
QMenu::item {{ border-radius: 7px; padding: 8px 14px; font-size: 13px; }}
QMenu::item:selected {{ background: #1b2a4d; }}
QDialog {{ background: {BG_SIDE}; }}
QLabel#toastTitle {{ font-size: 13.5px; font-weight: 700; }}
QLabel#toastBody {{ font-size: 12.5px; color: {MUTED}; }}
QFrame#toast {{ background: #101a33; border: 1px solid #2a3d68; border-radius: 14px; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; padding: 8px 16px; font-size: 13px; font-weight: 600; }}
QTabBar::tab:selected {{ color: {TEXT}; border-bottom: 2px solid {ACCENT}; }}
"""

QSS_LIGHT = QSS_DARK  # light theme follows the same system with brighter surfaces
for _old, _new in [
    (BG_APP, "#eef1f7"),
    (BG_SIDE, "#ffffff"),
    (BG_TOP, "#ffffff"),
    (CARD, "#ffffff"),
    (CARD_2, "#f2f5fb"),
    (TEXT, "#101828"),
    (MUTED, "#5b6577"),
    ("#0b1224", "#ffffff"),
    ("#131c33", "#eef2fa"),
    ("#101a33", "#ffffff"),
    ("#0e1730", "#f4f6fb"),
    ("#16203a", "#e3e9f4"),
]:
    QSS_LIGHT = QSS_LIGHT.replace(_old, _new)


def apply_theme(app: object, theme: str = "dark") -> None:
    from PySide6.QtWidgets import QApplication

    assert isinstance(app, QApplication)
    app.setStyle("Fusion")
    app.setStyleSheet(QSS_LIGHT if theme == "light" else QSS_DARK)


# -- shared widget factories -------------------------------------------------
class TileButton(QFrame):
    """Clickable card tile (QPushButton must not contain child layouts)."""

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("tile")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
            return
        super().keyPressEvent(event)


def _mk(parent: QWidget | None = None, obj: str = "card") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(parent)
    frame.setObjectName(obj)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(10)
    return frame, lay


def card(parent: QWidget | None = None, obj: str = "card") -> tuple[QFrame, QVBoxLayout]:
    frame, lay = _mk(parent, obj)
    return frame, lay


def chip(text: str, kind: str = "blue"):
    """Small status pill. kind: blue|green|red|amber|gray."""
    from PySide6.QtWidgets import QLabel

    colors = {
        "blue": (BLUE_BG, "#7aa8ff"),
        "green": (GREEN_BG, GREEN),
        "red": (RED_BG, RED),
        "amber": (AMBER_BG, AMBER),
        "gray": ("#16203a", MUTED),
    }
    bg, fg = colors.get(kind, colors["blue"])
    label = QLabel(text)
    label.setObjectName("chip")
    label.setStyleSheet(f"QLabel#chip {{ background: {bg}; color: {fg}; }}")
    return label


def progress(value01: float, green: bool = False):
    from PySide6.QtWidgets import QProgressBar

    bar = QProgressBar()
    bar.setObjectName("barGreen" if green else "bar")
    bar.setRange(0, 100)
    bar.setValue(int(max(0.0, min(1.0, value01)) * 100))
    bar.setTextVisible(False)
    return bar


def empty_state(icon: str, title: str, subtitle: str, button_text: str = ""):
    """Centered empty-state block. Returns (frame, button|None)."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

    from app.ui.icons import icon as make_icon

    frame = QFrame()
    lay = QVBoxLayout(frame)
    lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.setSpacing(8)
    pic = QLabel()
    pic.setPixmap(make_icon(icon, 44, MUTED).pixmap(52, 52))
    pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
    t = QLabel(title)
    t.setObjectName("cardTitle")
    t.setAlignment(Qt.AlignmentFlag.AlignCenter)
    s = QLabel(subtitle)
    s.setObjectName("muted")
    s.setWordWrap(True)
    s.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(pic)
    lay.addWidget(t)
    lay.addWidget(s)
    btn = None
    if button_text:
        btn = QPushButton(button_text)
        btn.setObjectName("primary")
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
    return frame, btn
