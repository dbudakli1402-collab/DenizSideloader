"""Downloads page: modern download cards (DE)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.downloads.manager import DownloadItem, DownloadState, format_eta, format_speed
from app.ui import design as D


class DownloadRow(QWidget):
    cancel_clicked = Signal(object)
    pause_clicked = Signal(object)

    def __init__(self, item: DownloadItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.item: DownloadItem = item
        frame, lay = D.card(obj="card2")
        lay.setContentsMargins(16, 14, 16, 14)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)
        self.title = QLabel(item.dest.name)
        self.title.setObjectName("cardTitle")
        lay.addWidget(self.title)
        from app.ui.design import progress as _bar

        self.bar = _bar(0.0)
        lay.addWidget(self.bar)
        self.info = QLabel("")
        self.info.setObjectName("muted")
        lay.addWidget(self.info)
        row = QHBoxLayout()
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setObjectName("ghost")
        self.btn_pause.clicked.connect(lambda: self.pause_clicked.emit(self.item))
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_cancel.setObjectName("danger")
        self.btn_cancel.clicked.connect(lambda: self.cancel_clicked.emit(self.item))
        row.addWidget(self.btn_pause)
        row.addWidget(self.btn_cancel)
        row.addStretch(1)
        lay.addLayout(row)
        self.refresh(item)

    def refresh(self, item: DownloadItem) -> None:
        self.item = item
        self.bar.setValue(int(item.progress * 100))
        if item.state == DownloadState.DONE:
            self.info.setText(f"Fertig · SHA-256: {item.sha256[:16]}…")
            self.btn_pause.setEnabled(False)
            self.btn_cancel.setEnabled(False)
        elif item.state == DownloadState.ERROR:
            self.info.setText(f"Fehler: {item.error[:200]}")
        elif item.state == DownloadState.CANCELLED:
            self.info.setText("Abgebrochen")
        elif item.state == DownloadState.PAUSED:
            self.info.setText("Pausiert")
            self.btn_pause.setText("Fortsetzen")
        else:
            self.info.setText(f"{format_speed(item.speed_bps)} · {format_eta(item.eta_seconds)}")


STATUS_DE = {
    DownloadState.QUEUED: "Warteschlange",
    DownloadState.ACTIVE: "Lädt",
    DownloadState.PAUSED: "Pausiert",
    DownloadState.DONE: "Fertig",
    DownloadState.CANCELLED: "Abgebrochen",
    DownloadState.ERROR: "Fehler",
}


class DownloadsPage(QWidget):
    start_download = Signal(str)
    cancel_download = Signal(object)
    pause_download = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(14)
        head = QLabel("Downloads")
        head.setObjectName("pageTitle")
        root.addWidget(head)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://beispiel.de/app.ipa")
        self.url_input.returnPressed.connect(lambda: self.start_download.emit(self.url_input.text()))
        self.btn_go = QPushButton("Herunterladen")
        self.btn_go.setObjectName("primary")
        self.btn_go.clicked.connect(lambda: self.start_download.emit(self.url_input.text()))
        row.addWidget(self.url_input, 1)
        row.addWidget(self.btn_go)
        root.addLayout(row)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {D.RED};")
        self.error_label.setWordWrap(True)
        root.addWidget(self.error_label)

        self.list = QListWidget()
        self.list.setSpacing(8)
        root.addWidget(self.list, 1)

    def show_error(self, msg: str) -> None:
        self.error_label.setText(msg)

    def set_items(self, items: list[DownloadItem]) -> None:
        self.list.clear()
        if not items:
            li = QListWidgetItem()
            empty, _ = D.empty_state("download", "Keine Downloads", "Füge oben eine direkte IPA-URL ein.")
            li.setSizeHint(empty.sizeHint())
            self.list.addItem(li)
            self.list.setItemWidget(li, empty)
            return
        for item in items:
            row = DownloadRow(item)
            row.cancel_clicked.connect(self.cancel_download.emit)
            row.pause_clicked.connect(self.pause_download.emit)
            head = QHBoxLayout()
            chip = D.chip(
                STATUS_DE.get(item.state, item.state.value),
                "green"
                if item.state == DownloadState.DONE
                else ("red" if item.state == DownloadState.ERROR else "blue"),
            )
            head.addWidget(chip)
            head.addStretch(1)
            wrap = QWidget()
            lay = QVBoxLayout(wrap)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(6)
            lay.addLayout(head)
            lay.addWidget(row)
            li = QListWidgetItem()
            li.setSizeHint(wrap.sizeHint())
            self.list.addItem(li)
            self.list.setItemWidget(li, wrap)
