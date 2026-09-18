"""Logs-Seite: App-Logs + Verlauf in Tabs."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.storage.history import HistoryEvent
from app.ui.pages.history import HistoryPage


class LogsPage(QWidget):
    clear_logs = Signal()
    open_folder = Signal()

    def __init__(self, log_file: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.log_file = log_file
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(12)
        head = QLabel("Logs")
        head.setObjectName("pageTitle")
        root.addWidget(head)
        sub = QLabel("Sideloading-Logs, Fehler und Verlauf.")
        sub.setObjectName("muted")
        root.addWidget(sub)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        logtab = QWidget()
        ll = QVBoxLayout(logtab)
        ll.setContentsMargins(4, 8, 4, 4)
        bar = QHBoxLayout()
        self.level = QComboBox()
        self.level.addItems(["Alle", "INFO", "WARNING", "ERROR"])
        self.level.currentTextChanged.connect(lambda: self.reload())
        b_ref = QPushButton("Aktualisieren")
        b_ref.setObjectName("ghost")
        b_ref.clicked.connect(self.reload)
        b_open = QPushButton("Ordner öffnen")
        b_open.setObjectName("ghost")
        b_open.clicked.connect(self.open_folder.emit)
        b_clear = QPushButton("Logs löschen")
        b_clear.setObjectName("danger")
        b_clear.clicked.connect(self.clear_logs.emit)
        bar.addWidget(QLabel("Level:"))
        bar.addWidget(self.level)
        bar.addStretch(1)
        bar.addWidget(b_ref)
        bar.addWidget(b_open)
        bar.addWidget(b_clear)
        ll.addLayout(bar)
        self.view = QTextEdit()
        self.view.setReadOnly(True)
        self.view.setFontFamily("Consolas")
        self.view.setFontPointSize(10)
        ll.addWidget(self.view, 1)
        self.tabs.addTab(logtab, "App-Logs")

        self.history = HistoryPage()
        self.tabs.addTab(self.history, "Verlauf")

    def set_log_file(self, path: Path) -> None:
        self.log_file = path
        self.reload()

    def reload(self) -> None:
        level = self.level.currentText()
        try:
            lines = self.log_file.read_text(encoding="utf-8", errors="replace").splitlines()[-800:]
        except Exception:
            lines = []
        if level != "Alle":
            lines = [ln for ln in lines if f"| {level}" in ln or ln.startswith(level)]
        self.view.setPlainText("\n".join(lines) if lines else "Keine Log-Einträge.")
        bar = self.view.verticalScrollBar()
        if bar is not None:
            bar.setValue(bar.maximum())

    def set_events(self, events: list[HistoryEvent]) -> None:
        self.history.set_events(events)
