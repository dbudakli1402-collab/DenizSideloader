"""App-Bibliothek: library grouped by category, opens details."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ipa.library import CATEGORIES
from app.ipa.models import IpaInfo
from app.ui import design as D


class CatalogPage(QWidget):
    install_ipa = Signal(IpaInfo)
    open_details = Signal(dict)
    category_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(14)
        head = QLabel("App-Bibliothek")
        head.setObjectName("pageTitle")
        root.addWidget(head)
        sub = QLabel("Deine IPA-Sammlung nach Kategorien.")
        sub.setObjectName("muted")
        root.addWidget(sub)
        self.list = QListWidget()
        self.list.setSpacing(10)
        self.list.itemDoubleClicked.connect(
            lambda it: self.open_details.emit({"ipa": it.data(32)}) if isinstance(it.data(32), IpaInfo) else None
        )
        root.addWidget(self.list, 1)
        self._items: list[IpaInfo] = []
        self._cat = "Alle"

    def set_category(self, cat: str) -> None:
        self._cat = cat if cat in CATEGORIES else "Alle"
        self._render()

    def set_items(self, items: list[IpaInfo]) -> None:
        self._items = items
        self._render()

    def _render(self) -> None:
        self.list.clear()
        items = [i for i in self._items if self._cat == "Alle" or i.category == self._cat]
        if not items:
            li = QListWidgetItem()
            empty, _ = D.empty_state(
                "book",
                "Keine Apps in dieser Kategorie",
                "Weise IPA-Dateien über das Kontextmenü eine Kategorie zu.",
            )
            li.setSizeHint(empty.sizeHint())
            self.list.addItem(li)
            self.list.setItemWidget(li, empty)
            return
        for info in sorted(items, key=lambda i: i.app_name.lower()):
            card, lay = D.card(obj="card2")
            lay.setContentsMargins(16, 12, 16, 12)
            top = QHBoxLayout()
            t = QLabel(info.display_title)
            t.setObjectName("cardTitle")
            top.addWidget(t, 1)
            top.addWidget(D.chip(info.category, "blue"))
            lay.addLayout(top)
            meta = QLabel(f"Version {info.version}  ·  {info.size_human}  ·  {info.bundle_id}")
            meta.setObjectName("muted")
            lay.addWidget(meta)
            row = QHBoxLayout()
            b1 = QPushButton("Installieren")
            b1.setObjectName("primary")
            b1.clicked.connect(lambda _=False, p=info: self.install_ipa.emit(p))
            b2 = QPushButton("Details")
            b2.setObjectName("ghost")
            b2.clicked.connect(lambda _=False, p=info: self.open_details.emit({"ipa": p}))
            row.addWidget(b1)
            row.addWidget(b2)
            row.addStretch(1)
            lay.addLayout(row)
            li = QListWidgetItem()
            li.setSizeHint(card.sizeHint())
            li.setData(32, info)
            self.list.addItem(li)
            self.list.setItemWidget(li, card)
