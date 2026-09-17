"""App details dialog: icon, facts, actions (DE)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.ipa.library import CATEGORIES
from app.ipa.models import IpaInfo
from app.ui import design as D


class AppDetailsDialog(QDialog):
    install_ipa = Signal(object)
    remove_ipa = Signal(object)
    category_changed = Signal(object, str)

    def __init__(self, payload: dict | IpaInfo, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Details")
        self.setMinimumWidth(480)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        if isinstance(payload, IpaInfo):
            self._ipa: IpaInfo | None = payload
            self._app: dict | None = None
        else:
            self._ipa = payload.get("ipa") if isinstance(payload, dict) else None
            self._app = None if self._ipa else (payload if isinstance(payload, dict) else None)

        # header
        head = QHBoxLayout()
        head.setSpacing(14)
        badge = QLabel(self._title()[:1].upper() or "?")
        badge.setFixedSize(64, 64)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0a54d6, stop:1 #3fd2ff);"
            "border-radius: 16px; font-size: 30px; font-weight: 800; color: white;"
        )
        texts = QVBoxLayout()
        texts.setSpacing(2)
        t = QLabel(self._title())
        t.setObjectName("cardTitle")
        t.setStyleSheet("font-size: 19px;")
        texts.addWidget(t)
        texts.addWidget(self._status_chip())
        head.addWidget(badge)
        head.addLayout(texts, 1)
        lay.addLayout(head)

        for label, value in self._facts():
            row = QHBoxLayout()
            k = QLabel(label)
            k.setObjectName("muted")
            v = QLabel(value)
            v.setWordWrap(True)
            v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(k, 1)
            row.addWidget(v, 2)
            lay.addLayout(row)

        if self._ipa is not None:
            row = QHBoxLayout()
            row.addWidget(_muted("Kategorie"))
            self.combo = QComboBox()
            self.combo.addItems(CATEGORIES)
            self.combo.setCurrentText(self._ipa.category if self._ipa.category in CATEGORIES else "Alle")
            self.combo.currentTextChanged.connect(lambda c: self.category_changed.emit(self._ipa, c))
            row.addWidget(self.combo, 2)
            lay.addLayout(row)

        btns = QHBoxLayout()
        if self._ipa is not None:
            b1 = QPushButton("Installieren")
            b1.setObjectName("primary")
            b1.clicked.connect(self._install_and_close)
            btns.addWidget(b1)
        b2 = QPushButton("Schließen")
        b2.setObjectName("ghost")
        b2.clicked.connect(self.accept)
        btns.addWidget(b2)
        btns.addStretch(1)
        lay.addLayout(btns)

    def _install_and_close(self) -> None:
        self.install_ipa.emit(self._ipa)
        self.accept()

    def _title(self) -> str:
        if self._ipa is not None:
            return self._ipa.display_title
        if self._app is not None:
            return str(self._app.get("name", "?"))
        return "?"

    def _status_chip(self) -> QLabel:
        if self._ipa is not None:
            return D.chip("In Bibliothek", "blue")
        return D.chip("Installiert", "green")

    def _facts(self) -> list[tuple[str, str]]:
        if self._ipa is not None:
            i = self._ipa
            return [
                ("Version", i.version),
                ("Bundle-ID", i.bundle_id),
                ("Größe", i.size_human),
                ("Datei", i.file_name),
                ("Hinzugefügt", i.added_ts[:10] if i.added_ts else "–"),
            ]
        if self._app is not None:
            a = self._app
            return [
                ("Version", str(a.get("version", "?"))),
                ("Bundle-ID", str(a.get("bundle_id", "?"))),
            ]
        return []

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


def _muted(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("muted")
    return label
