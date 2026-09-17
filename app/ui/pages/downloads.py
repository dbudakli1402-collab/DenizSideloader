"""Downloads page: URL input, progress list with speed/ETA, pause/cancel."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from app.downloads.manager import DownloadItem, DownloadState, format_eta, format_speed
from app.ui.widgets import Card, primary_button, secondary_button


class DownloadRow(Card):
    cancel_clicked = Signal(object)
    pause_clicked = Signal(object)

    def __init__(self, item: DownloadItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.item = item
        self.title = QLabel(item.dest.name)
        self.title.setObjectName("cardTitle")
        self.add(self.title)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.add(self.bar)
        self.info = QLabel("")
        self.info.setObjectName("muted")
        self.add(self.info)
        row = QHBoxLayout()
        self.btn_pause = secondary_button("Pause")
        self.btn_pause.clicked.connect(lambda: self.pause_clicked.emit(self.item))
        self.btn_cancel = secondary_button("Cancel")
        self.btn_cancel.clicked.connect(lambda: self.cancel_clicked.emit(self.item))
        row.addWidget(self.btn_pause)
        row.addWidget(self.btn_cancel)
        row.addStretch(1)
        self.add_layout(row)
        self.refresh(item)

    def refresh(self, item: DownloadItem) -> None:
        self.item = item
        self.bar.setValue(int(item.progress * 100))
        if item.state == DownloadState.DONE:
            self.info.setText(f"Done \u2022 SHA-256: {item.sha256[:16]}\u2026")
        elif item.state == DownloadState.ERROR:
            self.info.setText(f"Error: {item.error[:200]}")
        elif item.state == DownloadState.CANCELLED:
            self.info.setText("Cancelled")
        else:
            self.info.setText(f"{format_speed(item.speed_bps)} \u2022 {format_eta(item.eta_seconds)}")


class DownloadsPage(QWidget):
    start_download = Signal(str)
    cancel_download = Signal(object)
    pause_download = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        head = QLabel("Downloads")
        head.setObjectName("title")
        layout.addWidget(head)

        row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/app.ipa")
        self.btn_go = primary_button("Download")
        self.btn_go.clicked.connect(lambda: self.start_download.emit(self.url_input.text()))
        row.addWidget(self.url_input, 1)
        row.addWidget(self.btn_go)
        layout.addLayout(row)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff9d9d;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        self.list = QListWidget()
        self.list.setSpacing(8)
        layout.addWidget(self.list, 1)
        self._rows: dict[int, DownloadRow] = {}

    def show_error(self, msg: str) -> None:
        self.error_label.setText(msg)

    def set_items(self, items: list[DownloadItem]) -> None:
        self.list.clear()
        self._rows.clear()
        for item in items:
            row = DownloadRow(item)
            row.cancel_clicked.connect(self.cancel_download.emit)
            row.pause_clicked.connect(self.pause_download.emit)
            li = QListWidgetItem()
            li.setSizeHint(row.sizeHint())
            self.list.addItem(li)
            self.list.setItemWidget(li, row)
            self._rows[id(item)] = row
