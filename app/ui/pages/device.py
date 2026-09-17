"""My iPhone page: device list, status, trust hints."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.device.models import DeviceInfo, TrustState
from app.ui.widgets import Card, secondary_button


class DevicePage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        head = QLabel("My iPhone")
        head.setObjectName("title")
        layout.addWidget(head)

        self.cards_box = QVBoxLayout()
        self.cards_box.setSpacing(12)
        layout.addLayout(self.cards_box, 1)

        self.btn_refresh: QPushButton = secondary_button("Refresh")
        layout.addWidget(self.btn_refresh)
        layout.addStretch(1)

    def set_devices(self, devices: list[DeviceInfo], help_text: str = "") -> None:
        # Clear
        while self.cards_box.count():
            item = self.cards_box.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        if not devices:
            card = Card()
            t = QLabel("Kein iPhone verbunden")
            t.setObjectName("cardTitle")
            d = QLabel("Connect your iPhone via USB and unlock it.")
            d.setWordWrap(True)
            d.setObjectName("subtitle")
            card.add(t)
            card.add(d)
            if help_text:
                h = QLabel(help_text)
                h.setObjectName("muted")
                h.setWordWrap(True)
                card.add(h)
            self.cards_box.addWidget(card)
            return
        for dev in devices:
            card = Card()
            t = QLabel(dev.display_name)
            t.setObjectName("cardTitle")
            sub = QLabel(f"iOS {dev.ios_version} \u2022 Connected via USB")
            sub.setObjectName("subtitle")
            card.add(t)
            card.add(sub)
            if dev.trusted == TrustState.UNTRUSTED:
                warn = QLabel("Please unlock your iPhone and select \u201cTrust\u201d when prompted.")
                warn.setWordWrap(True)
                warn.setStyleSheet("color: #ff9f0a;")
                card.add(warn)
            self.cards_box.addWidget(card)
