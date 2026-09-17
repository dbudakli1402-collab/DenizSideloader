"""Geräte: device management with real facts only."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.device.models import DeviceInfo, TrustState
from app.ui import design as D
from app.ui.icons import icon as make_icon


def _gb(num_bytes: int) -> str:
    return f"{num_bytes / 1e9:.0f} GB"


class DevicesPage(QWidget):
    refresh_requested = Signal()
    show_apps = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(14)
        head = QLabel("Geräte")
        head.setObjectName("pageTitle")
        root.addWidget(head)
        self.box = QVBoxLayout()
        self.box.setSpacing(14)
        root.addLayout(self.box, 1)
        self.set_devices([], {}, "")

    def set_devices(self, devices: list[DeviceInfo], details: dict, help_text: str) -> None:
        while self.box.count():
            item = self.box.takeAt(0)
            old = item.widget() if item is not None else None
            if old is not None:
                old.deleteLater()
        if not devices:
            card, lay = D.card()
            row = QHBoxLayout()
            pic = QLabel()
            pic.setPixmap(make_icon("phone", 34, D.MUTED).pixmap(44, 44))
            t = QLabel("Kein iPhone verbunden")
            t.setObjectName("cardTitle")
            row.addWidget(pic)
            row.addWidget(t, 1)
            lay.addLayout(row)
            hint = QLabel("Verbinde dein iPhone per USB und entsperre es.")
            hint.setObjectName("muted")
            hint.setWordWrap(True)
            lay.addWidget(hint)
            if help_text:
                h = QLabel(help_text)
                h.setObjectName("muted")
                h.setWordWrap(True)
                lay.addWidget(h)
            btn = QPushButton("Aktualisieren")
            btn.setObjectName("primary")
            btn.clicked.connect(self.refresh_requested.emit)
            lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)
            self.box.addWidget(card)
            self.box.addStretch(1)
            return
        for dev in devices:
            card, lay = D.card()
            top = QHBoxLayout()
            pic = QLabel()
            pic.setPixmap(make_icon("phone", 30, D.CYAN).pixmap(40, 40))
            texts = QVBoxLayout()
            texts.setSpacing(1)
            texts.addWidget(_title(dev.display_name))
            texts.addWidget(_muted(f"iOS {dev.ios_version}  ·  {dev.model}" if dev.model else f"iOS {dev.ios_version}"))
            top.addWidget(pic)
            top.addLayout(texts, 1)
            if dev.trusted == TrustState.TRUSTED:
                top.addWidget(D.chip("Verbunden", "green"))
            elif dev.trusted == TrustState.UNTRUSTED:
                top.addWidget(D.chip("Trust erforderlich", "amber"))
            else:
                top.addWidget(D.chip("Unbekannt", "gray"))
            lay.addLayout(top)
            if dev.trusted == TrustState.UNTRUSTED:
                w = QLabel("Bitte entsperre dein iPhone und tippe auf „Vertrauen“.")
                w.setWordWrap(True)
                w.setStyleSheet(f"color: {D.AMBER};")
                lay.addWidget(w)
            det = details.get(dev.udid, {}) if isinstance(details, dict) else {}
            total = det.get("storage_total")
            avail = det.get("storage_available")
            if isinstance(total, int) and isinstance(avail, int) and total > 0:
                used = total - avail
                lay.addWidget(_muted(f"Speicher  {_gb(used)} / {_gb(total)}"))
                bar = D.progress(used / total)
                lay.addWidget(bar)
            batt = det.get("battery_pct")
            if isinstance(batt, int):
                extra = " · lädt" if det.get("charging") else ""
                lay.addWidget(_muted(f"Akku  {batt}%{extra}"))
                lay.addWidget(D.progress(batt / 100, green=True))
            facts = []
            if det.get("serial"):
                facts.append(f"Seriennummer: {det['serial']}")
            if det.get("product_type"):
                facts.append(f"Modellcode: {det['product_type']}")
            facts.append(f"Kennung: {dev.short_udid}")
            f = QLabel("   ·   ".join(facts))
            f.setObjectName("muted")
            f.setWordWrap(True)
            lay.addWidget(f)
            row = QHBoxLayout()
            b_apps = QPushButton("Apps anzeigen")
            b_apps.setObjectName("primary")
            b_apps.clicked.connect(self.show_apps.emit)
            b_ref = QPushButton("Aktualisieren")
            b_ref.setObjectName("ghost")
            b_ref.clicked.connect(self.refresh_requested.emit)
            row.addWidget(b_apps)
            row.addWidget(b_ref)
            row.addStretch(1)
            lay.addLayout(row)
            self.box.addWidget(card)
        self.box.addStretch(1)


def _title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("cardTitle")
    return label


def _muted(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("muted")
    return label
