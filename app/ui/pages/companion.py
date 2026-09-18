"""Companion-Seite (AltServer-Workflow, iloader-inspiriert, eigenes Branding).

Layout nach Vorlage: Kopf (Logo, Titel, Version, GitHub) + ACCOUNT +
MANAGEMENT links, DEVICES + INSTALLERS + SETTINGS rechts.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.companion.anisette import SERVERS
from app.companion.models import INSTALLERS, InstallerDef
from app.device.models import DeviceInfo
from app.ui import design as D
from app.ui.icons import icon as make_icon


class CompanionPage(QWidget):
    login_requested = Signal(str, str, bool)  # email, password, save_username
    logout_requested = Signal()
    refresh_devices = Signal()
    device_selected = Signal(str)
    open_pairing = Signal()
    open_certificates = Signal()
    open_app_ids = Signal()
    install_with = Signal(str)  # installer key
    import_ipa = Signal()
    anisette_changed = Signal(str, bool)  # server, custom
    reset_anisette = Signal()
    delete_pairing = Signal()
    view_logs = Signal()
    keyring_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        body = QVBoxLayout(content)
        body.setContentsMargins(26, 18, 26, 22)
        body.setSpacing(14)
        root.addWidget(scroll)
        scroll.setWidget(content)

        # header
        head = QHBoxLayout()
        head.setSpacing(10)
        head.addWidget(D.logo_badge(40))
        title = QLabel("DenizSideloader")
        title.setStyleSheet("font-size: 21px; font-weight: 800;")
        sub = QLabel("Sideloading Companion")
        sub.setObjectName("muted")
        tcol = QVBoxLayout()
        tcol.setSpacing(0)
        tcol.addWidget(title)
        tcol.addWidget(sub)
        head.addLayout(tcol)
        from app import __version__

        head.addWidget(D.chip(f"Version {__version__}", "blue"))
        head.addStretch(1)
        self.btn_github = QPushButton("GitHub")
        self.btn_github.setObjectName("ghost")
        self.btn_github.setIcon(make_icon("link", 15))
        head.addWidget(self.btn_github)
        body.addLayout(head)

        cols = QHBoxLayout()
        cols.setSpacing(16)
        body.addLayout(cols, 1)

        left = QVBoxLayout()
        left.setSpacing(14)
        cols.addLayout(left, 1)
        right = QVBoxLayout()
        right.setSpacing(14)
        cols.addLayout(right, 3)

        # ACCOUNT
        acc, al = D.card()
        al.addWidget(_cap("Account"))
        at = QLabel("Apple-ID")
        at.setObjectName("cardTitle")
        al.addWidget(at)
        self.edit_email = QLineEdit()
        self.edit_email.setPlaceholderText("Apple-ID E-Mail …")
        self.edit_pass = QLineEdit()
        self.edit_pass.setPlaceholderText("Apple-ID Passwort …")
        self.edit_pass.setEchoMode(QLineEdit.EchoMode.Password)
        al.addWidget(self.edit_email)
        al.addWidget(self.edit_pass)
        self.cb_save = QCheckBox("Benutzername speichern (nie das Passwort)")
        self.cb_save.setChecked(True)
        al.addWidget(self.cb_save)
        self.btn_login = QPushButton("Anmelden")
        self.btn_login.setObjectName("primary")
        self.btn_login.clicked.connect(self._do_login)
        al.addWidget(self.btn_login)
        self.login_state = QLabel("")
        self.login_state.setObjectName("muted")
        self.login_state.setWordWrap(True)
        al.addWidget(self.login_state)
        left.addWidget(acc)

        # MANAGEMENT
        mgmt, ml = D.card()
        ml.addWidget(_cap("Verwaltung"))
        self.mgmt = QListWidget()
        self.mgmt.setObjectName("nav")
        for label, shortcut in [
            ("Pairing-Datei", "Strg+P"),
            ("Geräte aktualisieren", "Strg+R"),
            ("Zertifikate", "Strg+Umschalt+C"),
            ("App-IDs", "Strg+Umschalt+A"),
        ]:
            item = QListWidgetItem(f"{label}   ·   {shortcut}")
            self.mgmt.addItem(item)
        self.mgmt.itemClicked.connect(self._mgmt_clicked)
        self.mgmt.setMaximumHeight(178)
        ml.addWidget(self.mgmt)
        left.addWidget(mgmt)
        left.addStretch(1)

        # DEVICES
        dev, dl = D.card()
        dh = QHBoxLayout()
        dh.addWidget(_cap("Geräte"))
        dh.addStretch(1)
        hint = QLabel("Gerät auswählen")
        hint.setObjectName("muted")
        dh.addWidget(hint)
        dl.addLayout(dh)
        dt = QLabel("iDevice")
        dt.setObjectName("cardTitle")
        dl.addWidget(dt)
        self.dev_list = QListWidget()
        self.dev_list.setObjectName("nav")
        self.dev_list.itemClicked.connect(self._dev_clicked)
        dl.addWidget(self.dev_list)
        self.btn_refresh = QPushButton("Aktualisieren")
        self.btn_refresh.setObjectName("ghost")
        self.btn_refresh.clicked.connect(self.refresh_devices.emit)
        dl.addWidget(self.btn_refresh)
        right.addWidget(dev)

        # INSTALLERS
        ins, il = D.card()
        ih = QHBoxLayout()
        ih.addWidget(_cap("Installer"))
        ih.addStretch(1)
        ch = QLabel("Build wählen")
        ch.setObjectName("muted")
        ih.addWidget(ch)
        il.addLayout(ih)
        grid = QHBoxLayout()
        grid.setSpacing(10)
        for inst in INSTALLERS:
            tile = D.TileButton()
            row = QVBoxLayout(tile)
            row.setContentsMargins(10, 12, 10, 12)
            row.setSpacing(2)
            t = QLabel(inst.title)
            t.setObjectName("cardTitle")
            t.setWordWrap(True)
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s = QLabel(inst.subtitle)
            s.setObjectName("muted")
            s.setWordWrap(True)
            s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(t)
            row.addWidget(s)
            tile.clicked.connect(lambda _=False, k=inst.key: self.install_with.emit(k))
            grid.addWidget(tile, 1)
        imp = QPushButton("IPA\nimportieren")
        imp.setObjectName("primary")
        imp.clicked.connect(self.import_ipa.emit)
        grid.addWidget(imp, 1)
        il.addLayout(grid)
        right.addWidget(ins)

        # SETTINGS
        st, sl = D.card()
        sl.addWidget(_cap("Einstellungen"))
        sl.addWidget(_lbl("Anisette-Server:"))
        self.combo_ani = QComboBox()
        for host, label in SERVERS:
            self.combo_ani.addItem(f"{label} ({host})", host)
        sl.addWidget(self.combo_ani)
        self.btn_custom = QPushButton("Eigenen Anisette-Server verwenden")
        self.btn_custom.setObjectName("ghost")
        self.btn_custom.clicked.connect(self._toggle_custom)
        sl.addWidget(self.btn_custom)
        self.edit_custom = QLineEdit()
        self.edit_custom.setPlaceholderText("ani.deinserver.de")
        self.edit_custom.setVisible(False)
        sl.addWidget(self.edit_custom)
        self.ani_state = QLabel("")
        self.ani_state.setObjectName("muted")
        sl.addWidget(self.ani_state)
        brow = QHBoxLayout()
        self.btn_reset_ani = QPushButton("Anisette-Status zurücksetzen")
        self.btn_reset_ani.setObjectName("danger")
        self.btn_reset_ani.clicked.connect(self.reset_anisette.emit)
        self.btn_del_pair = QPushButton("Gespeichertes Pairing löschen")
        self.btn_del_pair.setObjectName("danger")
        self.btn_del_pair.clicked.connect(self.delete_pairing.emit)
        self.btn_logs = QPushButton("Logs ansehen (Strg+L)")
        self.btn_logs.setObjectName("ghost")
        self.btn_logs.clicked.connect(self.view_logs.emit)
        brow.addWidget(self.btn_reset_ani, 1)
        brow.addWidget(self.btn_del_pair, 1)
        brow.addWidget(self.btn_logs, 1)
        sl.addLayout(brow)
        self.cb_keyring = QCheckBox("Schlüsselbund nicht verwenden")
        sl.addWidget(self.cb_keyring)
        self.cb_keyring.toggled.connect(self.keyring_toggled.emit)
        kh = QLabel(
            "Ohne Schlüsselbund liegt der Benutzername als Hinweis in den Einstellungen. "
            "Passwörter werden grundsätzlich nie gespeichert."
        )
        kh.setObjectName("muted")
        kh.setWordWrap(True)
        sl.addWidget(kh)
        right.addWidget(st)
        right.addStretch(1)

        self._devices: list[DeviceInfo] = []
        self._custom = False

    # -- actions ------------------------------------------------------------
    def _do_login(self) -> None:
        self.login_requested.emit(self.edit_email.text(), self.edit_pass.text(), self.cb_save.isChecked())
        self.edit_pass.clear()

    def _mgmt_clicked(self, item: QListWidgetItem) -> None:
        text = item.text()
        if text.startswith("Pairing"):
            self.open_pairing.emit()
        elif text.startswith("Geräte"):
            self.refresh_devices.emit()
        elif text.startswith("Zertifikate"):
            self.open_certificates.emit()
        elif text.startswith("App"):
            self.open_app_ids.emit()

    def _dev_clicked(self, item: QListWidgetItem) -> None:
        udid = item.data(32)
        if udid:
            self.device_selected.emit(str(udid))

    def _toggle_custom(self) -> None:
        self._custom = not self._custom
        self.edit_custom.setVisible(self._custom)
        self.btn_custom.setText("Standard-Server verwenden" if self._custom else "Eigenen Anisette-Server verwenden")
        self._emit_ani()

    def _emit_ani(self) -> None:
        if self._custom:
            self.anisette_changed.emit(self.edit_custom.text(), True)
        else:
            self.anisette_changed.emit(self.combo_ani.currentData() or "", False)

    def load_settings(self, server: str, custom: bool, use_keyring: bool, email: str) -> None:
        for i in range(self.combo_ani.count()):
            if self.combo_ani.itemData(i) == server:
                self.combo_ani.setCurrentIndex(i)
                break
        if custom:
            self._custom = True
            self.edit_custom.setVisible(True)
            self.edit_custom.setText(server)
        if email and not self.edit_email.text():
            self.edit_email.setText(email)
        self.cb_keyring.blockSignals(True)
        self.cb_keyring.setChecked(not use_keyring)
        self.cb_keyring.blockSignals(False)
        self.combo_ani.currentIndexChanged.connect(lambda: self._emit_ani())
        self.edit_custom.textChanged.connect(lambda: self._emit_ani())

    # -- data ------------------------------------------------------------------
    def set_devices(self, devices: list[DeviceInfo], selected: str | None = None) -> None:
        self._devices = devices
        self.dev_list.clear()
        if not devices:
            QListWidgetItem("Keine Geräte gefunden.", self.dev_list).setFlags(Qt.ItemFlag.NoItemFlags)
            return
        for d in devices:
            item = QListWidgetItem(f"{d.display_name}  ·  iOS {d.ios_version}  ·  USB")
            item.setData(32, d.udid)
            self.dev_list.addItem(item)
            if selected and d.udid == selected:
                self.dev_list.setCurrentItem(item)

    def set_login_state(self, text: str, ok: bool) -> None:
        self.login_state.setText(text)
        self.login_state.setStyleSheet(f"color: {D.GREEN if ok else D.AMBER};")

    def set_anisette_state(self, text: str) -> None:
        self.ani_state.setText(text)

    def installers(self) -> list[InstallerDef]:
        return INSTALLERS


def _cap(text: str) -> QLabel:
    label = QLabel(text.upper())
    label.setObjectName("section")
    return label


def _lbl(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("font-size: 13px; font-weight: 600;")
    return label
