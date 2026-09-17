"""Home page: status card, Choose/Download IPA, recent list."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QVBoxLayout, QWidget

from app.ui.widgets import Card, primary_button, secondary_button, status_pill


class HomePage(QWidget):
    choose_ipa = Signal()
    download_ipa = Signal()
    open_recent = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Deniz Sideloader")
        title.setObjectName("title")
        layout.addWidget(title)

        self.status_card = Card()
        self.status_label = status_pill(False)
        self.status_detail = QLabel("Connect your iPhone via USB and unlock it.")
        self.status_detail.setObjectName("subtitle")
        self.status_detail.setWordWrap(True)
        self.status_card.add(self.status_label)
        self.status_card.add(self.status_detail)
        layout.addWidget(self.status_card)

        install_card = Card()
        t = QLabel("IPA installieren")
        t.setObjectName("cardTitle")
        install_card.add(t)
        row = QHBoxLayout()
        row.setSpacing(12)
        self.btn_choose = primary_button("Choose IPA")
        self.btn_choose.clicked.connect(self.choose_ipa.emit)
        self.btn_download = secondary_button("Download IPA")
        self.btn_download.clicked.connect(self.download_ipa.emit)
        row.addWidget(self.btn_choose)
        row.addWidget(self.btn_download)
        row.addStretch(1)
        install_card.add_layout(row)
        layout.addWidget(install_card)

        recent_card = Card()
        rt = QLabel("Zuletzt verwendet")
        rt.setObjectName("cardTitle")
        recent_card.add(rt)
        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(lambda item: self.open_recent.emit(item.data(32)))
        recent_card.add(self.recent_list)
        layout.addWidget(recent_card)
        layout.addStretch(1)

    def set_device_status(self, connected: bool, detail: str) -> None:
        # Rebuild pill
        self.status_label.setText("\u25cf iPhone verbunden" if connected else "\u25cb Kein iPhone verbunden")
        self.status_label.setStyleSheet(
            "color: #30d158; font-size: 14px; font-weight: 600;"
            if connected
            else "color: #ff9f0a; font-size: 14px; font-weight: 600;"
        )
        self.status_detail.setText(detail)

    def set_recent(self, paths: list[str]) -> None:
        self.recent_list.clear()
        from PySide6.QtWidgets import QListWidgetItem

        if not paths:
            item = QListWidgetItem("Noch keine IPAs verwendet.")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.recent_list.addItem(item)
            return
        for p in paths:
            item = QListWidgetItem(p)
            item.setData(32, p)
            self.recent_list.addItem(item)
