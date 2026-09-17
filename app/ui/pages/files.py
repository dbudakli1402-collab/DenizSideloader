"""IPA-Dateien: file-manager view (search, filter, sort, context menu)."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ipa.library import CATEGORIES
from app.ipa.models import IpaInfo
from app.ui import design as D


class FilesPage(QWidget):
    install_ipa = Signal(IpaInfo)
    import_requested = Signal()
    files_dropped = Signal(list)
    open_details = Signal(dict)
    set_category = Signal(object, str)
    rename_requested = Signal(IpaInfo)
    reveal_requested = Signal(IpaInfo)
    remove_requested = Signal(IpaInfo)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(14)
        head = QLabel("IPA-Dateien")
        head.setObjectName("pageTitle")
        root.addWidget(head)

        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("Dateien suchen …")
        self.search.textChanged.connect(lambda: self._render())
        self.f_cat = QComboBox()
        self.f_cat.addItems(["Alle Kategorien"] + CATEGORIES[1:])
        self.f_cat.currentTextChanged.connect(lambda: self._render())
        self.f_sort = QComboBox()
        self.f_sort.addItems(["Name", "Größe", "Version", "Datum"])
        self.f_sort.currentTextChanged.connect(lambda: self._render())
        self.btn_import = QPushButton("Importieren")
        self.btn_import.setObjectName("primary")
        self.btn_import.clicked.connect(self.import_requested.emit)
        bar.addWidget(self.search, 1)
        bar.addWidget(self.f_cat)
        bar.addWidget(self.f_sort)
        bar.addWidget(self.btn_import)
        root.addLayout(bar)

        self.list = QListWidget()
        self.list.setSpacing(8)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._menu)
        self.list.itemDoubleClicked.connect(lambda it: self.open_details.emit({"ipa": it.data(32)}))
        root.addWidget(self.list, 1)
        self._items: list[IpaInfo] = []

    def set_items(self, items: list[IpaInfo]) -> None:
        self._items = items
        cats = ["Alle Kategorien"] + CATEGORIES[1:]
        cur = self.f_cat.currentText()
        self.f_cat.blockSignals(True)
        self.f_cat.clear()
        self.f_cat.addItems(cats)
        if cur in cats:
            self.f_cat.setCurrentText(cur)
        self.f_cat.blockSignals(False)
        self._render()

    def _filtered(self) -> list[IpaInfo]:
        q = self.search.text().strip().lower()
        cat = self.f_cat.currentText()
        out = [
            i
            for i in self._items
            if (not q or q in i.app_name.lower() or q in i.bundle_id.lower() or q in i.file_name.lower())
            and (cat == "Alle Kategorien" or i.category == cat)
        ]
        key = {
            "Name": lambda i: i.app_name.lower(),
            "Größe": lambda i: i.file_size,
            "Version": lambda i: i.version,
            "Datum": lambda i: i.added_ts,
        }[self.f_sort.currentText()]
        return sorted(out, key=key, reverse=self.f_sort.currentText() in ("Größe", "Datum"))

    def _render(self) -> None:
        self.list.clear()
        items = self._filtered()
        if not items:
            li = QListWidgetItem()
            empty, btn = D.empty_state(
                "file",
                "Keine IPA-Dateien",
                "Noch keine IPA-Dateien vorhanden." if not self._items else "Keine Treffer für diese Suche.",
                "IPA importieren",
            )
            li.setSizeHint(empty.sizeHint() + QSize(0, 40))
            self.list.addItem(li)
            self.list.setItemWidget(li, empty)
            if btn is not None:
                btn.clicked.connect(self.import_requested.emit)
            return
        for info in items:
            card, _ = D.card(obj="card2")
            lay = card.layout()
            assert isinstance(lay, QVBoxLayout)
            lay.setContentsMargins(16, 12, 16, 12)
            top = QHBoxLayout()
            t = QLabel(info.display_title)
            t.setObjectName("cardTitle")
            top.addWidget(t, 1)
            top.addWidget(D.chip(info.category, "blue"))
            lay.addLayout(top)
            meta = QLabel(f"{info.bundle_id}  ·  Version {info.version}  ·  {info.size_human}  ·  {info.added_ts[:10]}")
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

    def _menu(self, pos: QPoint) -> None:
        item = self.list.itemAt(pos)
        if item is None or not isinstance(item.data(32), IpaInfo):
            return
        info: IpaInfo = item.data(32)
        menu = QMenu(self)
        a_install = menu.addAction("Installieren")
        a_rename = menu.addAction("Umbenennen")
        a_folder = menu.addAction("Ordner öffnen")
        cat_menu = menu.addMenu("Kategorie")
        for c in CATEGORIES:
            act = cat_menu.addAction(c)
            act.setCheckable(True)
            act.setChecked(info.category == c)
            act.triggered.connect(lambda _=False, cc=c, p=info: self.set_category.emit(p, cc))
        a_details = menu.addAction("Details")
        menu.addSeparator()
        a_delete = menu.addAction("Löschen")
        chosen = menu.exec(self.list.mapToGlobal(pos))
        if chosen == a_install:
            self.install_ipa.emit(info)
        elif chosen == a_rename:
            self.rename_requested.emit(info)
        elif chosen == a_folder:
            self.reveal_requested.emit(info)
        elif chosen == a_details:
            self.open_details.emit({"ipa": info})
        elif chosen == a_delete:
            self.remove_requested.emit(info)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()

    def pick_file(self) -> str:
        path, _ = QFileDialog.getOpenFileName(self, "IPA-Datei auswählen", "", "iOS-App (*.ipa)")
        return path

    def ask_name(self, current: str) -> str:
        name, ok = QInputDialog.getText(self, "Umbenennen", "Neuer Dateiname:", text=current)
        return name if ok else ""
