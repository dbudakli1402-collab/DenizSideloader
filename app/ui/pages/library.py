"""Bibliothek: IPA-Dateien und Downloads in Tabs (Mockup-Navigation)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget

from app.downloads.manager import DownloadItem
from app.ipa.models import IpaInfo
from app.ui.pages.downloads import DownloadsPage
from app.ui.pages.files import FilesPage


class LibraryPage(QWidget):
    install_ipa = Signal(IpaInfo)
    import_requested = Signal()
    files_dropped = Signal(list)
    open_details = Signal(dict)
    set_category = Signal(object, str)
    rename_requested = Signal(IpaInfo)
    reveal_requested = Signal(IpaInfo)
    remove_requested = Signal(IpaInfo)
    start_download = Signal(str)
    cancel_download = Signal(object)
    pause_download = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(12)
        head = QLabel("Bibliothek")
        head.setObjectName("pageTitle")
        root.addWidget(head)
        sub = QLabel("IPA-Dateien verwalten und neue laden.")
        sub.setObjectName("muted")
        root.addWidget(sub)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self.files = FilesPage()
        self.files.setObjectName("tabpage")
        self.dl = DownloadsPage()
        self.tabs.addTab(self.files, "IPA-Dateien")
        self.tabs.addTab(self.dl, "Downloads")

        self.files.install_ipa.connect(self.install_ipa.emit)
        self.files.import_requested.connect(self.import_requested.emit)
        self.files.files_dropped.connect(self.files_dropped.emit)
        self.files.open_details.connect(self.open_details.emit)
        self.files.set_category.connect(self.set_category.emit)
        self.files.rename_requested.connect(self.rename_requested.emit)
        self.files.reveal_requested.connect(self.reveal_requested.emit)
        self.files.remove_requested.connect(self.remove_requested.emit)
        self.dl.start_download.connect(self.start_download.emit)
        self.dl.cancel_download.connect(self.cancel_download.emit)
        self.dl.pause_download.connect(self.pause_download.emit)

    # pass-through API used by the shell
    def set_items(self, items: list[IpaInfo]) -> None:
        self.files.set_items(items)

    def set_downloads(self, items: list[DownloadItem]) -> None:
        self.dl.set_items(items)

    def show_error(self, msg: str) -> None:
        self.tabs.setCurrentWidget(self.dl)
        self.dl.show_error(msg)

    def pick_file(self) -> str:
        return self.files.pick_file()

    def ask_name(self, current: str) -> str:
        return self.files.ask_name(current)
