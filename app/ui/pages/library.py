"""IPA Library page: import / drag&drop / install / delete."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ipa.models import IpaInfo
from app.ui.widgets import Card, primary_button, secondary_button


class IpaCard(Card):
    install_clicked = Signal(IpaInfo)
    remove_clicked = Signal(IpaInfo)

    def __init__(self, info: IpaInfo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.info = info
        title = QLabel(info.display_title)
        title.setObjectName("cardTitle")
        meta = QLabel(f"{info.bundle_id}\nVersion {info.version} \u2022 IPA \u2022 {info.size_human}")
        meta.setObjectName("muted")
        self.add(title)
        self.add(meta)
        row = QHBoxLayout()
        btn_install = primary_button("Install")
        btn_install.clicked.connect(lambda: self.install_clicked.emit(self.info))
        btn_remove = secondary_button("Delete")
        btn_remove.clicked.connect(lambda: self.remove_clicked.emit(self.info))
        row.addWidget(btn_install)
        row.addWidget(btn_remove)
        row.addStretch(1)
        self.add_layout(row)


class LibraryPage(QWidget):
    import_requested = Signal()
    install_ipa = Signal(IpaInfo)
    remove_ipa = Signal(IpaInfo)
    files_dropped = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        head = QLabel("IPA Library")
        head.setObjectName("title")
        layout.addWidget(head)

        hint = QLabel("Import .ipa files or drop them anywhere on this page.")
        hint.setObjectName("subtitle")
        layout.addWidget(hint)

        self.list = QListWidget()
        self.list.setSpacing(8)
        layout.addWidget(self.list, 1)

        row = QHBoxLayout()
        self.btn_import = primary_button("Import IPA")
        self.btn_import.clicked.connect(self.import_requested.emit)
        row.addWidget(self.btn_import)
        row.addStretch(1)
        layout.addLayout(row)

    def set_items(self, items: list[IpaInfo]) -> None:
        self.list.clear()
        for info in items:
            card = IpaCard(info)
            card.install_clicked.connect(self.install_ipa.emit)
            card.remove_clicked.connect(self.remove_ipa.emit)
            item = QListWidgetItem()
            item.setSizeHint(card.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, card)
        self.list.setStyleSheet("QListWidget::item { background: transparent; }")

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()

    def pick_file(self) -> str:
        path, _ = QFileDialog.getOpenFileName(self, "Choose IPA", "", "iOS App (*.ipa)")
        return path
