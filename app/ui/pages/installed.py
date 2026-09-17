"""Installed Apps page: lists apps reported by the device backend."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.ui.widgets import Card


class InstalledPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        head = QLabel("Installed Apps")
        head.setObjectName("title")
        layout.addWidget(head)
        self.box = QVBoxLayout()
        self.box.setSpacing(10)
        layout.addLayout(self.box, 1)
        layout.addStretch(1)
        self.set_apps([], "")

    def set_apps(self, apps: list[dict[str, str]], note: str = "") -> None:
        while self.box.count():
            item = self.box.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        if not apps:
            card = Card()
            card.add(_label("No app data available", "cardTitle"))
            msg = note or (
                "Installed-app listing needs the device backend (pymobiledevice3) "
                "plus a connected, trusted iPhone. Update/Remove from here is only "
                "shown when the backend reliably supports it."
            )
            w = _label(msg, "subtitle")
            w.setWordWrap(True)
            card.add(w)
            self.box.addWidget(card)
            return
        for app in apps:
            card = Card()
            card.add(_label(str(app.get("name", "?")), "cardTitle"))
            sub = _label(f"Version {app.get('version', '?')}\n{app.get('bundle_id', '')}", "muted")
            sub.setWordWrap(True)
            card.add(sub)
            note_l = _label(
                "Update/Remove via backend is not reliably supported \u2014 use the device.",
                "muted",
            )
            note_l.setWordWrap(True)
            card.add(note_l)
            self.box.addWidget(card)


def _label(text: str, obj: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName(obj)
    return label
