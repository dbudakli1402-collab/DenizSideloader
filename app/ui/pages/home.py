"""Home dashboard v3 (Mockup): hero, sideloading, meine apps, schnellzugriff, news."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.device.models import DeviceInfo
from app.ipa.models import IpaInfo
from app.ui import design as D
from app.ui.design import DropZone
from app.ui.icons import icon as make_icon

# UI-Beispiele ( Platzhalter aus dem Mockup ): nur wenn KEINE echten Daten da sind,
# klar als Beispiel markiert, ohne Funktion dahinter.
EXAMPLE_APPS = [
    ("AltStore", "v1.6.1", "A", "#2fb380"),
    ("Spotify", "v8.9.76", "S", "#1db954"),
    ("YouTube", "v19.16.3", "Y", "#ff3b30"),
    ("Delta", "v1.6.3", "D", "#7c5cff"),
]

NEWS = [
    ("Deniz Sideloader v1.0.0", "Heute", "Neue Oberfläche mit vielen Verbesserungen!"),
    ("Unterstützung für iOS 17", "Gestern", "Vollständige Kompatibilität"),
    ("Neue Features", "12.09.2025", "Mehr Kontrolle, mehr Möglichkeiten."),
]


class HomePage(QWidget):
    choose_ipa = Signal()
    files_dropped = Signal(list)
    goto = Signal(int)
    quick_library = Signal()
    quick_url = Signal()
    quick_qr = Signal()
    action_sign = Signal()
    action_bundle = Signal()
    action_profiles = Signal()
    action_logs = Signal()
    install_ipa = Signal(IpaInfo)
    open_details = Signal(dict)
    uninstall_app = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        lay = QHBoxLayout(content)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)
        root.addWidget(scroll)
        scroll.setWidget(content)

        left = QVBoxLayout()
        left.setSpacing(16)
        lay.addLayout(left, 3)
        right = QVBoxLayout()
        right.setSpacing(16)
        lay.addLayout(right, 1)

        # -- hero ---------------------------------------------------------
        hero = QFrame()
        hero.setObjectName("hero")
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(26, 24, 26, 24)
        hl.setSpacing(20)
        logo = D.logo_badge(72, glow=True)
        hl.addWidget(logo)
        texts = QVBoxLayout()
        texts.setSpacing(6)
        t = QLabel("Deniz Sideloader")
        t.setStyleSheet("font-size: 27px; font-weight: 800;")
        s = QLabel("Sideloading Made Simple")
        s.setStyleSheet("font-size: 16px; color: #9db4d8;")
        d = QLabel(
            "Installiere und verwalte deine IPA-Dateien schnell,\n"
            "einfach und sicher – direkt auf deinem iPhone oder iPad."
        )
        d.setObjectName("muted")
        d.setStyleSheet("font-size: 13px;")
        texts.addWidget(t)
        texts.addWidget(s)
        texts.addWidget(d)
        hl.addLayout(texts, 1)

        self.hero_dev, hdl = D.card(obj="card2")
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        hero_pic = QLabel()
        hero_pic.setPixmap(make_icon("phone", 18, D.CYAN).pixmap(22, 22))
        hero_title = QLabel("iPhone")
        hero_title.setObjectName("cardTitle")
        title_row.addWidget(hero_pic)
        title_row.addWidget(hero_title, 1)
        hdl.addLayout(title_row)
        self.hero_ios = QLabel("iOS –")
        self.hero_ios.setObjectName("muted")
        hdl.addWidget(self.hero_ios)
        self.hero_chip = QLabel("Getrennt")
        self.hero_chip.setObjectName("chip")
        self._paint_chip(self.hero_chip, False)
        hdl.addWidget(self.hero_chip)
        self.btn_manage = QPushButton("Gerät verwalten  →")
        self.btn_manage.setObjectName("primary")
        self.btn_manage.clicked.connect(lambda: self.goto.emit(2))
        hdl.addWidget(self.btn_manage)
        hl.addWidget(self.hero_dev)
        left.addWidget(hero)

        # -- sideloading --------------------------------------------------
        sc, sl = D.card()
        head = QHBoxLayout()
        bic = QLabel()
        bic.setPixmap(make_icon("bolt", 18, D.CYAN).pixmap(22, 22))
        ht = QLabel("Sideloading")
        ht.setObjectName("cardTitle")
        head.addWidget(bic)
        head.addWidget(ht, 1)
        sl.addLayout(head)
        sub = QLabel("IPA-Datei auswählen und auf dein Gerät übertragen.")
        sub.setObjectName("muted")
        sl.addWidget(sub)
        cols = QHBoxLayout()
        cols.setSpacing(12)
        self.drop = DropZone()
        self.drop.clicked.connect(self.choose_ipa.emit)
        self.drop.dropped.connect(self.files_dropped.emit)
        cols.addWidget(self.drop, 3)
        qa = QVBoxLayout()
        qa.setSpacing(10)
        for glyph, title, subtitle, sig in [
            ("book", "Aus App Library", "Bereits geladene IPA-Dateien", "quick_library"),
            ("link", "Von URL", "IPA aus Link laden", "quick_url"),
            ("apps", "QR Code", "IPA über QR Code installieren", "quick_qr"),
        ]:
            tile = D.TileButton()
            row = QHBoxLayout(tile)
            row.setContentsMargins(12, 10, 12, 10)
            pic = QLabel()
            pic.setPixmap(make_icon(glyph, 20, "#7aa8ff").pixmap(26, 26))
            tx = QVBoxLayout()
            tx.setSpacing(1)
            a = QLabel(title)
            a.setObjectName("cardTitle")
            b = QLabel(subtitle)
            b.setObjectName("muted")
            tx.addWidget(a)
            tx.addWidget(b)
            row.addWidget(pic)
            row.addLayout(tx, 1)
            arrow = QLabel("›")
            arrow.setStyleSheet("color: #5d6680; font-size: 18px;")
            row.addWidget(arrow)
            tile.clicked.connect(getattr(self, sig).emit)
            qa.addWidget(tile)
        cols.addLayout(qa, 2)
        sl.addLayout(cols)
        left.addWidget(sc)

        # -- meine apps ---------------------------------------------------
        mc, ml = D.card()
        mh = QHBoxLayout()
        mic = QLabel()
        mic.setPixmap(make_icon("apps", 18, D.CYAN).pixmap(22, 22))
        mt = QLabel("Meine Apps")
        mt.setObjectName("cardTitle")
        mh.addWidget(mic)
        mh.addWidget(mt, 1)
        more = QPushButton("Alle anzeigen  →")
        more.setObjectName("iconbtn")
        more.clicked.connect(lambda: self.goto.emit(1))
        mh.addWidget(more)
        ml.addLayout(mh)
        msub = QLabel("Alle installierten und signierten Apps auf deinem Gerät.")
        msub.setObjectName("muted")
        ml.addWidget(msub)
        self.apps_grid = QGridLayout()
        self.apps_grid.setSpacing(12)
        self.apps_grid.setRowStretch(99, 1)  # spacer row absorbs vertical slack
        ml.addLayout(self.apps_grid)
        left.addWidget(mc)
        left.addStretch(1)

        # -- right rail ---------------------------------------------------
        qc, ql = D.card()
        ql.addWidget(_rail_title("Schnellzugriff", "bolt"))
        self.qa_box = QVBoxLayout()
        self.qa_box.setSpacing(10)
        for glyph, title, subtitle, sig in [
            ("pen", "IPA signieren", "Mit deinem Zertifikat signieren", "action_sign"),
            ("link", "Bundle ID ändern", "Für eigene Apps", "action_bundle"),
            ("file", "Provisioning Profile", "Profil verwalten", "action_profiles"),
            ("history", "Logs anzeigen", "Sideloading Logs & Fehler", "action_logs"),
        ]:
            tile = D.TileButton()
            row = QHBoxLayout(tile)
            row.setContentsMargins(12, 10, 12, 10)
            pic = QLabel()
            pic.setPixmap(make_icon(glyph, 20, "#7aa8ff").pixmap(26, 26))
            tx = QVBoxLayout()
            tx.setSpacing(1)
            a = QLabel(title)
            a.setObjectName("cardTitle")
            b = QLabel(subtitle)
            b.setObjectName("muted")
            tx.addWidget(a)
            tx.addWidget(b)
            row.addWidget(pic)
            row.addLayout(tx, 1)
            arrow = QLabel("›")
            arrow.setStyleSheet("color: #5d6680; font-size: 18px;")
            row.addWidget(arrow)
            tile.clicked.connect(getattr(self, sig).emit)
            self.qa_box.addWidget(tile)
        ql.addLayout(self.qa_box)
        right.addWidget(qc)

        nc, nl = D.card()
        nh = QHBoxLayout()
        nl.addLayout(nh)
        nh.addWidget(_rail_title("Neuigkeiten", "bell"))
        nh.addStretch(1)
        allb = QPushButton("Alle →")
        allb.setObjectName("iconbtn")
        allb.setToolTip("Alle Neuigkeiten")
        nh.addWidget(allb)
        for title, when, body in NEWS:
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {D.ACCENT};")
            tx = QVBoxLayout()
            tx.setSpacing(1)
            a = QLabel(title)
            a.setStyleSheet("font-size: 13px; font-weight: 700;")
            b = QLabel(body)
            b.setObjectName("muted")
            tx.addWidget(a)
            tx.addWidget(b)
            row.addWidget(dot, alignment=Qt.AlignmentFlag.AlignTop)
            row.addLayout(tx, 1)
            w = QLabel(when)
            w.setObjectName("muted")
            row.addWidget(w, alignment=Qt.AlignmentFlag.AlignTop)
            nl.addLayout(row)
        right.addWidget(nc)

        promo = QFrame()
        promo.setObjectName("hero")
        pl = QVBoxLayout(promo)
        pl.setContentsMargins(20, 18, 20, 18)
        pt = QLabel("Deniz Sideloader\nSideloading. Next Level.")
        pt.setStyleSheet("font-size: 17px; font-weight: 800;")
        pl.addWidget(pt, alignment=Qt.AlignmentFlag.AlignCenter)
        right.addWidget(promo)
        right.addStretch(1)

        self._installed: list[dict] = []
        self._library: list[IpaInfo] = []

    # -- data -------------------------------------------------------------
    @staticmethod
    def _paint_chip(label: QLabel, connected: bool) -> None:
        if connected:
            label.setText("Verbunden")
            label.setStyleSheet(f"QLabel#chip {{ background: {D.GREEN_BG}; color: {D.GREEN}; }}")
        else:
            label.setText("Getrennt")
            label.setStyleSheet("QLabel#chip { background: #16203a; color: #8b94a9; }")

    def set_device(self, dev: DeviceInfo | None, details: dict | None = None) -> None:
        _ = details
        if dev is None:
            self._paint_chip(self.hero_chip, False)
            self.hero_ios.setText("iOS –")
        else:
            self.hero_ios.setText(f"{dev.display_name} · iOS {dev.ios_version}")
            self._paint_chip(self.hero_chip, True)

    def set_apps(self, installed: list[dict], library: list[IpaInfo]) -> None:
        self._installed = installed
        self._library = library
        while self.apps_grid.count():
            item = self.apps_grid.takeAt(0)
            wd = item.widget() if item is not None else None
            if wd is not None:
                wd.deleteLater()
        rows: list[tuple] = []
        for a in installed[:4]:
            rows.append((str(a.get("name", "?")), str(a.get("version", "?")), False, a))
        if not rows:
            for name, ver, letter, color in EXAMPLE_APPS:
                rows.append(
                    (name, ver, True, {"name": name, "version": ver, "example": True, "letter": letter, "color": color})
                )
        for n, (name, ver, example, payload) in enumerate(rows):
            card, lay = D.card(obj="card2")
            lay.setContentsMargins(14, 12, 14, 12)
            top = QHBoxLayout()
            badge = (
                D.app_badge(name[:1], "#3a4763")
                if not example
                else D.app_badge(payload.get("letter", "?"), payload.get("color", "#3a4763"))
            )
            tx = QVBoxLayout()
            tx.setSpacing(1)
            t = QLabel(name)
            t.setObjectName("cardTitle")
            v = QLabel(ver)
            v.setObjectName("muted")
            tx.addWidget(t)
            tx.addWidget(v)
            top.addWidget(badge)
            top.addLayout(tx, 1)
            dots = QPushButton("···")
            dots.setObjectName("iconbtn")
            dots.clicked.connect(lambda _=False, p=payload, ex=example: self._menu(p, ex))
            top.addWidget(dots, alignment=Qt.AlignmentFlag.AlignTop)
            lay.addLayout(top)
            lay.addWidget(D.chip("Beispiel" if example else "Aktiv", "gray" if example else "green"))
            self.apps_grid.addWidget(card, 0, n)

    def _menu(self, payload: dict, example: bool) -> None:
        from PySide6.QtWidgets import QMenu

        from app.ui.dialogs.app_details import AppDetailsDialog

        if example:
            dlg = AppDetailsDialog(
                {
                    "name": payload.get("name"),
                    "version": payload.get("version"),
                    "bundle_id": "Beispiel-Eintrag (keine echte App)",
                },
                self,
            )
            dlg.exec()
            return
        menu = QMenu(self)
        a_det = menu.addAction("Details")
        a_un = menu.addAction("Deinstallieren")
        chosen = menu.exec(self.cursor().pos())
        if chosen == a_det:
            self.open_details.emit(payload)
        elif chosen == a_un:
            self.uninstall_app.emit(payload)


def _row_title(text: str, glyph: str) -> QWidget:
    wrap = QWidget()
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    pic = QLabel()
    pic.setPixmap(make_icon(glyph, 18, D.CYAN).pixmap(22, 22))
    t = QLabel(text)
    t.setObjectName("cardTitle")
    lay.addWidget(pic)
    lay.addWidget(t, 1)
    return wrap


def _rail_title(text: str, glyph: str) -> QWidget:
    return _row_title(text, glyph)
