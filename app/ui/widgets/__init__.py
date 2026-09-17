"""Reusable widgets: cards, status pill, error box."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Card(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 18, 20, 18)
        self._layout.setSpacing(10)

    def add(self, w: QWidget) -> None:
        self._layout.addWidget(w)

    def add_layout(self, layout: QLayout) -> None:
        self._layout.addLayout(layout)


def status_pill(connected: bool) -> QLabel:
    label = QLabel("\u25cf iPhone verbunden" if connected else "\u25cb Kein iPhone verbunden")
    color = "#30d158" if connected else "#ff9f0a"
    label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 600;")
    return label


def error_box(title: str, body: str, technical: str = "") -> Card:
    card = Card()
    t = QLabel(title)
    t.setObjectName("cardTitle")
    t.setStyleSheet("color: #ff9d9d;")
    b = QLabel(body)
    b.setWordWrap(True)
    card.add(t)
    card.add(b)
    if technical:
        detail = QLabel(f"<small style='color:#8b919c'>{technical[:800]}</small>")
        detail.setTextFormat(Qt.TextFormat.RichText)
        detail.setWordWrap(True)
        card.add(detail)
    return card


def friendly_error_dialog(parent: QWidget, title: str, message: str, technical: str = "") -> None:
    from PySide6.QtWidgets import QMessageBox

    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    if technical:
        box.setDetailedText(technical[:4000])
    box.setIcon(QMessageBox.Icon.Warning)
    box.addButton("Retry", QMessageBox.ButtonRole.AcceptRole)
    box.addButton("Help", QMessageBox.ButtonRole.HelpRole)
    box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
    box.exec()


def primary_button(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("primary")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def secondary_button(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("secondary")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b
