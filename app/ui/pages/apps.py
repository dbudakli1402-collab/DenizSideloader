"""Apps page: installed device apps + library apps, grid/list, status."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ipa.models import IpaInfo
from app.ui import design as D


class AppsPage(QWidget):
    install_ipa = Signal(IpaInfo)
    import_requested = Signal()
    open_details = Signal(dict)  # device app dict or {"ipa": IpaInfo}

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(14)
        head = QLabel("Apps")
        head.setObjectName("pageTitle")
        root.addWidget(head)

        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("Apps suchen …")
        self.search.textChanged.connect(lambda: self._render())
        self.view = QComboBox()
        self.view.addItems(["Grid", "Liste"])
        self.view.currentTextChanged.connect(lambda: self._render())
        bar.addWidget(self.search, 1)
        bar.addWidget(self.view)
        root.addLayout(bar)

        self.grid_wrap = QFrame()
        self.grid = QGridLayout(self.grid_wrap)
        self.grid.setSpacing(12)
        root.addWidget(self.grid_wrap, 1)
        self.list = QListWidget()
        self.list.setSpacing(6)
        self.list.itemDoubleClicked.connect(self._open_list_item)
        root.addWidget(self.list, 1)

        self._installed: list[dict] = []
        self._library: list[IpaInfo] = []

    def set_data(self, installed: list[dict], library: list[IpaInfo]) -> None:
        self._installed = installed
        self._library = library
        self._render()

    def _query(self) -> str:
        return self.search.text().strip().lower()

    def _render(self) -> None:
        is_grid = self.view.currentText() == "Grid"
        self.grid_wrap.setVisible(is_grid)
        self.list.setVisible(not is_grid)
        q = self._query()
        lib_by_bundle = {i.bundle_id: i for i in self._library}
        rows: list[tuple[str, str, str, str, Any]] = []  # title, sub, status, kind, payload
        for a in self._installed:
            title = str(a.get("name", "?"))
            if q and q not in title.lower() and q not in str(a.get("bundle_id", "")).lower():
                continue
            in_lib = str(a.get("bundle_id", "")) in lib_by_bundle
            rows.append((title, f"Version {a.get('version', '?')}", "Installiert", "dev", a))
            _ = in_lib
        for info in self._library:
            if info.bundle_id in {str(a.get("bundle_id")) for a in self._installed}:
                continue
            if q and q not in info.app_name.lower() and q not in info.bundle_id.lower():
                continue
            rows.append(
                (info.display_title, f"Version {info.version} · {info.size_human}", "Nicht installiert", "ipa", info)
            )
        # clear grid
        while self.grid.count():
            taken = self.grid.takeAt(0)
            old = taken.widget() if taken is not None else None
            if old is not None:
                old.deleteLater()
        self.list.clear()
        if not rows:
            empty, btn = D.empty_state(
                "apps",
                "Keine Apps gefunden",
                "Passe die Suche an oder importiere eine IPA-Datei.",
                "IPA importieren",
            )
            self.grid.addWidget(empty, 0, 0)
            if btn is not None:
                btn.clicked.connect(self.import_requested.emit)
            return
        for n, (title, sub, status, kind, payload) in enumerate(rows):
            if is_grid:
                self.grid.addWidget(self._card(title, sub, status, kind, payload), n // 3, n % 3)
            else:
                li = QListWidgetItem()
                card = self._card(title, sub, status, kind, payload, compact=True)
                li.setSizeHint(card.sizeHint())
                li.setData(32, (kind, payload))
                self.list.addItem(li)
                self.list.setItemWidget(li, card)

    def _card(self, title: str, sub: str, status: str, kind: str, payload: Any, compact: bool = False) -> QFrame:
        frame, lay = D.card(obj="card2")
        lay.setContentsMargins(16, 14, 16, 14)
        top = QHBoxLayout()
        top.setSpacing(12)
        badge = QLabel(title[:1].upper() or "?")
        badge.setFixedSize(44, 44)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0a54d6, stop:1 #2f7bff);"
            "border-radius: 12px; font-size: 20px; font-weight: 800; color: white;"
        )
        texts = QVBoxLayout()
        texts.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("cardTitle")
        s = QLabel(sub)
        s.setObjectName("muted")
        texts.addWidget(t)
        texts.addWidget(s)
        top.addWidget(badge)
        top.addLayout(texts, 1)
        top.addWidget(D.chip(status, "green" if status == "Installiert" else "gray"))
        lay.addLayout(top)
        row = QHBoxLayout()
        row.setSpacing(8)
        if kind == "ipa":
            b1 = QPushButton("Installieren")
            b1.setObjectName("primary")
            b1.clicked.connect(lambda _=False, p=payload: self.install_ipa.emit(p))
            row.addWidget(b1)
        else:
            b0 = QPushButton("Details")
            b0.setObjectName("ghost")
            b0.clicked.connect(lambda _=False, p=payload: self.open_details.emit(p))
            row.addWidget(b0)
        if kind == "ipa":
            b2 = QPushButton("Details")
            b2.setObjectName("ghost")
            b2.clicked.connect(lambda _=False, p=payload: self.open_details.emit({"ipa": p}))
            row.addWidget(b2)
        row.addStretch(1)
        lay.addLayout(row)
        if compact:
            frame.setMaximumHeight(150)
        return frame

    def _open_list_item(self, item: QListWidgetItem) -> None:
        kind, payload = item.data(32)
        if kind == "ipa":
            self.open_details.emit({"ipa": payload})
        else:
            self.open_details.emit(payload)
