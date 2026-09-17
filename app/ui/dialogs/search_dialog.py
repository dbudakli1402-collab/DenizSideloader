"""Global search dialog (Ctrl+K): apps, IPA files, devices."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

from app.device.models import DeviceInfo
from app.ipa.models import IpaInfo


class SearchDialog(QDialog):
    picked_ipa = Signal(object)
    picked_device = Signal(object)
    picked_app = Signal(dict)
    goto = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Suchen")
        self.setMinimumWidth(540)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        self.input = QLineEdit()
        self.input.setObjectName("search")
        self.input.setPlaceholderText("Apps, IPA-Dateien oder Geräte suchen …")
        self.input.textChanged.connect(lambda: self._render())
        self.input.returnPressed.connect(self._activate_first)
        lay.addWidget(self.input)
        self.list = QListWidget()
        self.list.itemActivated.connect(lambda it: self._activate(it))
        lay.addWidget(self.list)
        self._ipas: list[IpaInfo] = []
        self._devices: list[DeviceInfo] = []
        self._apps: list[dict] = []

    def set_data(self, ipas: list[IpaInfo], devices: list[DeviceInfo], apps: list[dict]) -> None:
        self._ipas = ipas
        self._devices = devices
        self._apps = apps
        self._render()

    def _render(self) -> None:
        self.list.clear()
        q = self.input.text().strip().lower()

        def _add(section: str, title: str, sub: str, payload: tuple) -> None:
            item = QListWidgetItem(f"{section}   ·   {title}   —   {sub}")
            item.setData(32, payload)
            self.list.addItem(item)

        for info in self._ipas:
            if q and q not in info.app_name.lower() and q not in info.bundle_id.lower():
                continue
            _add("IPA", info.display_title, f"v{info.version}", ("ipa", info))
        for a in self._apps:
            title = str(a.get("name", "?"))
            if q and q not in title.lower():
                continue
            _add("App", title, "Installiert", ("app", a))
        for d in self._devices:
            if q and q not in d.display_name.lower():
                continue
            _add("Gerät", d.display_name, f"iOS {d.ios_version}", ("dev", d))
        if self.list.count() == 0:
            QListWidgetItem("Keine Treffer.", self.list)

    def _activate_first(self) -> None:
        if self.list.count():
            item = self.list.item(0)
            if item is not None:
                self._activate(item)

    def _activate(self, item: QListWidgetItem) -> None:
        data = item.data(32)
        if not isinstance(data, tuple):
            return
        kind, payload = data
        self.accept()
        if kind == "ipa":
            self.picked_ipa.emit(payload)
        elif kind == "app":
            self.picked_app.emit(payload)
        elif kind == "dev":
            self.picked_device.emit(payload)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
