"""Apple-inspired dark theme (QSS) + light variant."""

from __future__ import annotations

DARK_QSS = """
* { font-family: 'Segoe UI', 'Inter', sans-serif; }
QMainWindow, QWidget#central { background: #0e0f13; color: #f2f3f5; }
QWidget#sidebar { background: #15171d; border-right: 1px solid #23262e; }
QPushButton#navBtn {
  background: transparent; color: #b9bec7; border: none; border-radius: 10px;
  padding: 10px 14px; text-align: left; font-size: 14px;
}
QPushButton#navBtn:hover { background: #1e2129; color: #ffffff; }
QPushButton#navBtn:checked { background: #2a2f3a; color: #ffffff; font-weight: 600; }
QFrame#card {
  background: #171a21; border: 1px solid #242832; border-radius: 16px;
}
QLabel#title { font-size: 26px; font-weight: 700; }
QLabel#subtitle { font-size: 13px; color: #9aa1ad; }
QLabel#cardTitle { font-size: 15px; font-weight: 600; }
QLabel#muted { color: #9aa1ad; font-size: 12px; }
QPushButton#primary {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a84ff, stop:1 #5e5ce6);
  color: white; border: none; border-radius: 12px; padding: 12px 22px;
  font-size: 14px; font-weight: 600;
}
QPushButton#primary:hover { background: #0a84ff; }
QPushButton#primary:disabled { background: #2a2e37; color: #7c828d; }
QPushButton#secondary {
  background: #22262f; color: #f2f3f5; border: 1px solid #31363f;
  border-radius: 12px; padding: 10px 18px; font-size: 13px;
}
QPushButton#secondary:hover { background: #2a2f3a; }
QPushButton#danger {
  background: #3a1d20; color: #ff9d9d; border: 1px solid #5a2b30;
  border-radius: 10px; padding: 8px 14px;
}
QLineEdit, QComboBox, QSpinBox {
  background: #101319; border: 1px solid #2b303b; border-radius: 10px;
  padding: 9px 12px; color: #f2f3f5; font-size: 13px; selection-background-color: #0a84ff;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #0a84ff; }
QProgressBar {
  background: #22262f; border: none; border-radius: 8px; height: 14px;
  text-align: center; color: #cfd4dc; font-size: 11px;
}
QProgressBar::chunk {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0a84ff, stop:1 #5e5ce6);
  border-radius: 8px;
}
QListWidget { background: transparent; border: none; outline: none; }
QListWidget::item { background: transparent; border: none; padding: 2px; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #2c313b; border-radius: 5px; min-height: 30px; }
QCheckBox { color: #dfe3e9; font-size: 13px; spacing: 8px; }
QCheckBox::indicator {
  width: 16px; height: 16px; border-radius: 6px;
  border: 1px solid #3a404b; background: #1b1f27;
}
QCheckBox::indicator:checked { background: #0a84ff; border: 1px solid #0a84ff; }
QTabWidget::pane { border: none; }
QToolTip { background: #1e222b; color: #f2f3f5; border: 1px solid #333945; padding: 6px; }
QStatusBar { background: #0e0f13; color: #8b919c; font-size: 12px; }
"""

LIGHT_QSS = (
    DARK_QSS.replace("#0e0f13", "#f5f6f8")
    .replace("#15171d", "#ffffff")
    .replace("#171a21", "#ffffff")
    .replace("#f2f3f5", "#14161a")
)


def apply_theme(app: object, theme: str = "dark") -> None:
    from PySide6.QtWidgets import QApplication

    assert isinstance(app, QApplication)
    app.setStyle("Fusion")
    app.setStyleSheet(LIGHT_QSS if theme == "light" else DARK_QSS)
