"""About page."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app import __app_name__, __version__
from app.ui.widgets import Card


class AboutPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        head = QLabel("About")
        head.setObjectName("title")
        layout.addWidget(head)
        card = Card()
        t = QLabel(f"{__app_name__} \u2022 v{__version__}")
        t.setObjectName("cardTitle")
        card.add(t)
        body = QLabel(
            "A modern open-source desktop application for managing and legitimately "
            "sideloading IPA applications to your own iPhone.\n\n"
            "Tech: Python + PySide6 (Qt, native \u2014 no Chromium/Electron overhead).\n"
            "License: MIT. No telemetry. Passwords are never stored."
        )
        body.setWordWrap(True)
        body.setObjectName("subtitle")
        card.add(body)
        layout.addWidget(card)
        layout.addStretch(1)
