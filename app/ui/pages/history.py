"""Verlauf: timeline of real activity events with filters."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from app.storage.history import HistoryEvent
from app.ui import design as D
from app.ui.icons import icon as make_icon

FILTERS = ["Alle", "Installationen", "Downloads", "Geräte", "Fehler"]
KIND_MAP = {"Alle": "all", "Installationen": "install", "Downloads": "download", "Geräte": "device", "Fehler": "errors"}


class HistoryPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(14)
        head = QLabel("Verlauf")
        head.setObjectName("pageTitle")
        root.addWidget(head)
        bar = QHBoxLayout()
        self.filter = QComboBox()
        self.filter.addItems(FILTERS)
        self.filter.currentTextChanged.connect(lambda: self._render())
        bar.addWidget(self.filter)
        bar.addStretch(1)
        root.addLayout(bar)
        self.list = QListWidget()
        self.list.setSpacing(8)
        root.addWidget(self.list, 1)
        self._events: list[HistoryEvent] = []

    def set_events(self, events: list[HistoryEvent]) -> None:
        self._events = events
        self._render()

    def _render(self) -> None:
        self.list.clear()
        kind = KIND_MAP.get(self.filter.currentText(), "all")
        if kind == "all":
            items = list(self._events)
        elif kind == "errors":
            items = [e for e in self._events if e.status == "fail"]
        else:
            items = [e for e in self._events if e.kind == kind]
        items = sorted(items, key=lambda e: e.ts, reverse=True)
        if not items:
            li = QListWidgetItem()
            empty, _ = D.empty_state(
                "history",
                "Kein Verlauf",
                "Hier erscheinen Installationen, Downloads und Geräteereignisse.",
            )
            li.setSizeHint(empty.sizeHint())
            self.list.addItem(li)
            self.list.setItemWidget(li, empty)
            return
        glyph = {"install": "bolt", "download": "download", "device": "phone", "error": "warn"}
        for ev in items:
            card, lay = D.card(obj="card2")
            lay.setContentsMargins(16, 12, 16, 12)
            row = QHBoxLayout()
            row.setSpacing(12)
            pic = QLabel()
            color = D.GREEN if ev.status == "ok" else (D.RED if ev.status == "fail" else D.CYAN)
            pic.setPixmap(make_icon(glyph.get(ev.kind, "info"), 20, color).pixmap(26, 26))
            texts = QVBoxLayout()
            texts.setSpacing(1)
            t = QLabel(ev.title)
            t.setObjectName("cardTitle")
            texts.addWidget(t)
            if ev.detail:
                d = QLabel(ev.detail[:220])
                d.setObjectName("muted")
                d.setWordWrap(True)
                texts.addWidget(d)
            row.addWidget(pic)
            row.addLayout(texts, 1)
            ts = QLabel(ev.ts.replace("T", " "))
            ts.setObjectName("muted")
            row.addWidget(ts)
            lay.addLayout(row)
            li = QListWidgetItem()
            li.setSizeHint(card.sizeHint())
            self.list.addItem(li)
            self.list.setItemWidget(li, card)
