"""Apps-Seite v3: Karten mit Status-Chip und Drei-Punkte-Menü (Mockup)."""

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
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.ipa.models import IpaInfo
from app.ui import design as D


class AppsPage(QWidget):
    install_ipa = Signal(IpaInfo)
    import_requested = Signal()
    open_details = Signal(dict)
    uninstall_app = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(14)
        head = QLabel("Apps")
        head.setObjectName("pageTitle")
        root.addWidget(head)
        sub = QLabel("Installierte Apps und Bibliothek im Überblick.")
        sub.setObjectName("muted")
        root.addWidget(sub)

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
        self.grid.setRowStretch(99, 1)  # spacer row absorbs vertical slack
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

    def _render(self) -> None:
        is_grid = self.view.currentText() == "Grid"
        self.grid_wrap.setVisible(is_grid)
        self.list.setVisible(not is_grid)
        q = self.search.text().strip().lower()
        rows: list[tuple[str, str, str, str, Any]] = []
        for a in self._installed:
            title = str(a.get("name", "?"))
            if q and q not in title.lower() and q not in str(a.get("bundle_id", "")).lower():
                continue
            rows.append((title, f"v{str(a.get('version', '?'))}", "Aktiv", "dev", a))
        for info in self._library:
            if info.bundle_id in {str(a.get("bundle_id")) for a in self._installed}:
                continue
            if q and q not in info.app_name.lower() and q not in info.bundle_id.lower():
                continue
            rows.append((info.display_title, f"v{info.version}", "Bibliothek", "ipa", info))
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
                "Verbinde dein Gerät oder importiere eine IPA-Datei.",
                "IPA importieren",
            )
            self.grid.addWidget(empty, 0, 0)
            if btn is not None:
                btn.clicked.connect(self.import_requested.emit)
            return
        for n, (title, sub, status, kind, payload) in enumerate(rows):
            if is_grid:
                self.grid.addWidget(self._card(title, sub, status, kind, payload), n // 4, n % 4)
            else:
                li = QListWidgetItem()
                card = self._card(title, sub, status, kind, payload)
                li.setSizeHint(card.sizeHint())
                li.setData(32, (kind, payload))
                self.list.addItem(li)
                self.list.setItemWidget(li, card)

    def _open_list_item(self, item: QListWidgetItem) -> None:
        data = item.data(32)
        if isinstance(data, tuple) and len(data) == 2:
            self._open(data[0], data[1])

    def _card(self, title: str, sub: str, status: str, kind: str, payload: Any) -> QFrame:
        frame, lay = D.card(obj="card2")
        frame.setMaximumWidth(360)
        lay.setContentsMargins(14, 12, 14, 12)
        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(D.app_badge(title[:1], "#2b6cb0" if kind == "dev" else "#3a4763", 46))
        tx = QVBoxLayout()
        tx.setSpacing(1)
        t = QLabel(title)
        t.setObjectName("cardTitle")
        t.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        s = QLabel(sub)
        s.setObjectName("muted")
        s.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        tx.addWidget(t)
        tx.addWidget(s)
        top.addLayout(tx, 1)
        dots = QPushButton("···")
        dots.setObjectName("iconbtn")
        dots.setToolTip("Menü")
        dots.clicked.connect(lambda _=False, k=kind, p=payload: self._menu(k, p, dots))
        top.addWidget(dots, alignment=Qt.AlignmentFlag.AlignTop)
        lay.addLayout(top)
        chip = D.chip(status, "green" if status == "Aktiv" else "blue")
        chip.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        lay.addWidget(chip)
        lay.addStretch(1)
        return frame

    def _menu(self, kind: str, payload: Any, anchor: QWidget) -> None:
        menu = QMenu(self)
        a_det = menu.addAction("Details")
        a_inst = menu.addAction("Installieren") if kind == "ipa" else None
        a_un = menu.addAction("Deinstallieren") if kind == "dev" else None
        chosen = menu.exec(anchor.mapToGlobal(anchor.rect().bottomLeft()))
        if chosen == a_det:
            self._open(kind, payload)
        elif a_inst is not None and chosen == a_inst:
            self.install_ipa.emit(payload)
        elif a_un is not None and chosen == a_un:
            self.uninstall_app.emit(payload)

    def _open(self, kind: str, payload: Any) -> None:
        if kind == "ipa":
            self.open_details.emit({"ipa": payload})
        else:
            self.open_details.emit(payload)
