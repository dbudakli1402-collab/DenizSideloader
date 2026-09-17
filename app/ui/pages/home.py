"""Home dashboard: hero, features, device card, installer dropzone, activity."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.device.models import DeviceInfo
from app.storage.history import HistoryEvent
from app.ui import design as D
from app.ui.icons import icon as make_icon


def _feature(glyph: str, title: str, sub: str) -> QFrame:
    frame, lay = D.card(obj="card2")
    row = QHBoxLayout()
    row.setSpacing(12)
    pic = QLabel()
    pic.setPixmap(make_icon(glyph, 22, D.CYAN).pixmap(30, 30))
    texts = QVBoxLayout()
    texts.setSpacing(1)
    t = QLabel(title)
    t.setObjectName("cardTitle")
    s = QLabel(sub)
    s.setObjectName("muted")
    texts.addWidget(t)
    texts.addWidget(s)
    row.addWidget(pic)
    row.addLayout(texts, 1)
    lay.addLayout(row)
    return frame


def _quick(glyph: str, title: str, sub: str) -> D.TileButton:
    btn = D.TileButton()
    inner = QHBoxLayout(btn)
    inner.setContentsMargins(12, 10, 12, 10)
    inner.setSpacing(12)
    pic = QLabel()
    pic.setPixmap(make_icon(glyph, 22, "#7aa8ff").pixmap(30, 30))
    texts = QVBoxLayout()
    texts.setSpacing(1)
    t = QLabel(title)
    t.setObjectName("cardTitle")
    s = QLabel(sub)
    s.setObjectName("muted")
    texts.addWidget(t)
    texts.addWidget(s)
    inner.addWidget(pic)
    inner.addLayout(texts, 1)
    return btn


class DropZone(QFrame):
    clicked = Signal()
    dropped = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dropzone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(6)
        lay.setContentsMargins(20, 26, 20, 26)
        pic = QLabel()
        pic.setPixmap(make_icon("download", 34, "#7aa8ff").pixmap(44, 44))
        pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t = QLabel("IPA-Datei hierhin ziehen")
        t.setObjectName("cardTitle")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s = QLabel("oder klicken, um eine Datei auszuwählen")
        s.setObjectName("muted")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn = QPushButton("IPA auswählen")
        self.btn.setObjectName("primary")
        self.btn.clicked.connect(self.clicked.emit)
        lay.addWidget(pic)
        lay.addWidget(t)
        lay.addWidget(s)
        lay.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit()

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            self.setProperty("active", True)
            self.style().unpolish(self)
            self.style().polish(self)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event) -> None:  # noqa: N802
        self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.dropped.emit(paths)
            event.acceptProposedAction()


class HomePage(QWidget):
    choose_ipa = Signal()
    files_dropped = Signal(list)
    goto = Signal(int)  # nav index

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(16)

        # -- hero ---------------------------------------------------------
        hero = QFrame()
        hero.setObjectName("hero")
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(28, 26, 28, 26)
        hl.setSpacing(24)
        left = QVBoxLayout()
        left.setSpacing(10)
        kicker = QLabel("Willkommen bei")
        kicker.setObjectName("heroKicker")
        title = QLabel('<span style="color:#ffffff">Deniz</span> <span style="color:#3fd2ff">Sideloader</span>')
        title.setObjectName("heroTitle")
        title.setTextFormat(Qt.TextFormat.RichText)
        sub = QLabel("Sideloading war noch nie so einfach.")
        sub.setObjectName("heroSub")
        feats = QHBoxLayout()
        feats.setSpacing(10)
        feats.addWidget(_feature("bolt", "Schnell", "In Sekunden installiert"))
        feats.addWidget(_feature("shield", "Sicher", "Daten bleiben bei dir"))
        feats.addWidget(_feature("check", "Kostenlos", "Keine versteckten Kosten"))
        left.addWidget(kicker)
        left.addWidget(title)
        left.addWidget(sub)
        left.addLayout(feats)
        hl.addLayout(left, 3)

        # device card (right)
        self.dev_card, dev_lay = D.card(obj="card2")
        dev_lay.setContentsMargins(20, 18, 20, 18)
        self.dev_name = QLabel("Kein iPhone verbunden")
        self.dev_name.setObjectName("cardTitle")
        self.dev_sub = QLabel("Verbinde dein iPhone per USB.")
        self.dev_sub.setObjectName("muted")
        self.dev_sub.setWordWrap(True)
        self.dev_status = D.chip("Getrennt", "gray")
        head = QHBoxLayout()
        head.addWidget(self.dev_name, 1)
        head.addWidget(self.dev_status)
        self.dev_head = head
        self._chip: QLabel = self.dev_status
        self.store_bar = D.progress(0.0)
        self.store_lbl = QLabel("")
        self.store_lbl.setObjectName("muted")
        self.batt_bar = D.progress(0.0, green=True)
        self.batt_lbl = QLabel("")
        self.batt_lbl.setObjectName("muted")
        self.btn_manage = QPushButton("Gerät verwalten")
        self.btn_manage.setObjectName("primary")
        self.btn_manage.clicked.connect(lambda: self.goto.emit(3))
        dev_lay.addLayout(head)
        dev_lay.addWidget(self.dev_sub)
        dev_lay.addWidget(self.store_lbl)
        dev_lay.addWidget(self.store_bar)
        dev_lay.addWidget(self.batt_lbl)
        dev_lay.addWidget(self.batt_bar)
        dev_lay.addWidget(self.btn_manage)
        self.dev_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        hl.addWidget(self.dev_card, 2)
        root.addWidget(hero)

        # -- lower row ----------------------------------------------------
        row = QGridLayout()
        row.setSpacing(16)
        row.setColumnStretch(0, 3)
        row.setColumnStretch(1, 3)
        row.setColumnStretch(2, 4)

        inst_card, inst_lay = D.card()
        h = QHBoxLayout()
        t = QLabel("App installieren")
        t.setObjectName("cardTitle")
        h.addWidget(t, 1)
        inst_lay.addLayout(h)
        self.drop = DropZone()
        self.drop.clicked.connect(self.choose_ipa.emit)
        self.drop.dropped.connect(self.files_dropped.emit)
        inst_lay.addWidget(self.drop)
        row.addWidget(inst_card, 0, 0)

        quick_card, quick_lay = D.card()
        tq = QLabel("Schnellzugriff")
        tq.setObjectName("cardTitle")
        quick_lay.addWidget(tq)
        grid = QGridLayout()
        grid.setSpacing(10)
        targets = [
            ("book", "App-Bibliothek", "Beliebte Apps entdecken", 4),
            ("history", "Verlauf", "Zuletzt installierte Apps", 6),
            ("file", "Dateien durchsuchen", "IPA-Dateien finden", 2),
            ("gear", "Einstellungen", "Konfiguration & Hilfe", 7),
        ]
        for i, (glyph, name, desc, idx) in enumerate(targets):
            btn = _quick(glyph, name, desc)
            btn.clicked.connect(lambda _=False, n=idx: self.goto.emit(n))
            grid.addWidget(btn, i // 2, i % 2)
        quick_lay.addLayout(grid)
        row.addWidget(quick_card, 0, 1)

        act_card, act_lay = D.card()
        ah = QHBoxLayout()
        ta = QLabel("Aktivitäten")
        ta.setObjectName("cardTitle")
        more = QPushButton("Alle anzeigen ›")
        more.setObjectName("iconbtn")
        more.clicked.connect(lambda: self.goto.emit(6))
        ah.addWidget(ta, 1)
        ah.addWidget(more)
        act_lay.addLayout(ah)
        self.act_box = QVBoxLayout()
        self.act_box.setSpacing(8)
        act_lay.addLayout(self.act_box)
        act_lay.addStretch(1)
        row.addWidget(act_card, 0, 2)
        root.addLayout(row, 1)

    # -- data -------------------------------------------------------------
    def set_device(self, dev: DeviceInfo | None, details: dict | None = None) -> None:
        details = details or {}
        if dev is None:
            self.dev_name.setText("Kein iPhone verbunden")
            self.dev_sub.setText("Verbinde dein iPhone per USB.")
            self.store_lbl.setText("")
            self.store_bar.setValue(0)
            self.batt_lbl.setText("")
            self.batt_bar.setValue(0)
            return
        self.dev_name.setText(dev.display_name)
        self.dev_sub.setText(f"iOS {dev.ios_version}")
        total = details.get("storage_total")
        avail = details.get("storage_available")
        if isinstance(total, int) and isinstance(avail, int) and total > 0:
            used = total - avail

            def _gb(num_bytes: int) -> str:
                return f"{num_bytes / 1e9:.0f} GB"

            self.store_lbl.setText(f"Speicher  {_gb(used)} / {_gb(total)}")
            self.store_bar.setValue(int(used / total * 100))
        else:
            self.store_lbl.setText("")
            self.store_bar.setValue(0)
        batt = details.get("battery_pct")
        if isinstance(batt, int):
            extra = " · lädt" if details.get("charging") else ""
            self.batt_lbl.setText(f"Akku  {batt}%{extra}")
            self.batt_bar.setValue(batt)
        else:
            self.batt_lbl.setText("")
            self.batt_bar.setValue(0)

    def set_status_chip(self, connected: bool) -> None:
        self.dev_head.removeWidget(self._chip)
        self._chip.deleteLater()
        self._chip = D.chip("Verbunden", "green") if connected else D.chip("Getrennt", "gray")
        self.dev_head.addWidget(self._chip)

    def set_activity(self, events: list[HistoryEvent]) -> None:
        while self.act_box.count():
            item = self.act_box.takeAt(0)
            w = item.widget() if item is not None else None
            if w is not None:
                w.deleteLater()
        if not events:
            lbl = QLabel("Noch keine Aktivitäten.")
            lbl.setObjectName("muted")
            self.act_box.addWidget(lbl)
            return
        glyph = {"install": "bolt", "download": "download", "device": "phone", "error": "warn"}
        for ev in events[:5]:
            row = QHBoxLayout()
            row.setSpacing(10)
            pic = QLabel()
            pic.setPixmap(
                make_icon(glyph.get(ev.kind, "info"), 18, D.GREEN if ev.status == "ok" else D.RED).pixmap(22, 22)
            )
            texts = QVBoxLayout()
            texts.setSpacing(0)
            texts.addWidget(_bold(ev.title))
            sub = QLabel(ev.ts.replace("T", " "))
            sub.setObjectName("muted")
            texts.addWidget(sub)
            row.addWidget(pic)
            row.addLayout(texts, 1)
            wrap = QWidget()
            wrap.setLayout(row)
            self.act_box.addWidget(wrap)


def _bold(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("font-size: 13px; font-weight: 600;")
    return label
