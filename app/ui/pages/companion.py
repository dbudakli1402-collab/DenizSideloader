"""Companion-Seite (AltServer-Workflow, iloader-inspiriert, eigenes Branding).

DE/EN umschaltbar (eigene String-Tabelle, ehrlich implementiert).
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
from app.companion.strings import text as T
from app.device.models import DeviceInfo
from app.ui import design as D
from app.ui.icons import icon as make_icon


class CompanionPage(QWidget):
    login_requested = Signal(str, str, bool)
    logout_requested = Signal()
    refresh_devices = Signal()
    device_selected = Signal(str)
    open_pairing = Signal()
    open_certificates = Signal()
    open_app_ids = Signal()
    install_with = Signal(str)
    import_ipa = Signal()
    anisette_changed = Signal(str, bool)
    reset_anisette = Signal()
    delete_pairing = Signal()
    view_logs = Signal()
    keyring_toggled = Signal(bool)
    language_changed = Signal(str)
    open_translations = Signal()

    MGMT_KEYS = ["mgmt_pairing", "mgmt_refresh", "mgmt_certs", "mgmt_appids"]
    MGMT_SHORTCUTS = ["Strg+P", "Strg+R", "Strg+Umschalt+C", "Strg+Umschalt+A"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._lang = "de"
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

        head = QHBoxLayout()
        head.setSpacing(10)
        head.addWidget(D.logo_badge(40, glow=True))
        title = QLabel("DenizSigner")
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
        self.acc_cap = _cap("account")
        al.addWidget(self.acc_cap)
        self.apple_title = QLabel()
        self.apple_title.setObjectName("cardTitle")
        al.addWidget(self.apple_title)
        self.edit_email = QLineEdit()
        self.edit_pass = QLineEdit()
        self.edit_pass.setEchoMode(QLineEdit.EchoMode.Password)
        al.addWidget(self.edit_email)
        al.addWidget(self.edit_pass)
        self.cb_save = QCheckBox()
        self.cb_save.setChecked(True)
        al.addWidget(self.cb_save)
        self.btn_login = QPushButton()
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
        self.mgmt_cap = _cap("management")
        ml.addWidget(self.mgmt_cap)
        self.mgmt = QListWidget()
        self.mgmt.setObjectName("nav")
        self.mgmt.itemClicked.connect(self._mgmt_clicked)
        self.mgmt.setMaximumHeight(178)
        ml.addWidget(self.mgmt)
        left.addWidget(mgmt)
        left.addStretch(1)

        # DEVICES
        dev, dl = D.card()
        dh = QHBoxLayout()
        self.dev_cap = _cap("devices")
        dh.addWidget(self.dev_cap)
        dh.addStretch(1)
        self.dev_hint = QLabel()
        self.dev_hint.setObjectName("muted")
        dh.addWidget(self.dev_hint)
        dl.addLayout(dh)
        self.dev_title = QLabel("iDevice")
        self.dev_title.setObjectName("cardTitle")
        dl.addWidget(self.dev_title)
        self.dev_list = QListWidget()
        self.dev_list.setObjectName("nav")
        self.dev_list.itemClicked.connect(self._dev_clicked)
        dl.addWidget(self.dev_list)
        self.btn_refresh = QPushButton()
        self.btn_refresh.setObjectName("ghost")
        self.btn_refresh.clicked.connect(self.refresh_devices.emit)
        dl.addWidget(self.btn_refresh)
        right.addWidget(dev)

        # INSTALLERS
        ins, il = D.card()
        ih = QHBoxLayout()
        self.ins_cap = _cap("installers")
        ih.addWidget(self.ins_cap)
        ih.addStretch(1)
        self.ins_hint = QLabel()
        self.ins_hint.setObjectName("muted")
        ih.addWidget(self.ins_hint)
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
        self.btn_import = QPushButton()
        self.btn_import.setObjectName("primary")
        self.btn_import.clicked.connect(self.import_ipa.emit)
        grid.addWidget(self.btn_import, 1)
        il.addLayout(grid)
        right.addWidget(ins)

        # SETTINGS
        st, sl = D.card()
        self.set_cap = _cap("settings")
        sl.addWidget(self.set_cap)
        self.ani_label = QLabel()
        self.ani_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        sl.addWidget(self.ani_label)
        self.combo_ani = QComboBox()
        for host, label in SERVERS:
            self.combo_ani.addItem(f"{label} ({host})", host)
        sl.addWidget(self.combo_ani)
        self.btn_custom = QPushButton()
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
        self.lang_label = QLabel()
        self.lang_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        sl.addWidget(self.lang_label)
        langrow = QHBoxLayout()
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("Deutsch", "de")
        self.combo_lang.addItem("English", "en")
        self.combo_lang.currentIndexChanged.connect(self._lang_changed)
        langrow.addWidget(self.combo_lang, 1)
        sl.addLayout(langrow)
        self.btn_trans = QPushButton()
        self.btn_trans.setObjectName("ghost")
        self.btn_trans.clicked.connect(self.open_translations.emit)
        sl.addWidget(self.btn_trans)
        brow = QHBoxLayout()
        self.btn_reset_ani = QPushButton()
        self.btn_reset_ani.setObjectName("danger")
        self.btn_reset_ani.clicked.connect(self.reset_anisette.emit)
        self.btn_del_pair = QPushButton()
        self.btn_del_pair.setObjectName("danger")
        self.btn_del_pair.clicked.connect(self.delete_pairing.emit)
        self.btn_logs = QPushButton()
        self.btn_logs.setObjectName("ghost")
        self.btn_logs.clicked.connect(self.view_logs.emit)
        brow.addWidget(self.btn_reset_ani, 1)
        brow.addWidget(self.btn_del_pair, 1)
        brow.addWidget(self.btn_logs, 1)
        sl.addLayout(brow)
        self.cb_keyring = QCheckBox()
        sl.addWidget(self.cb_keyring)
        self.cb_keyring.toggled.connect(self.keyring_toggled.emit)
        kh = QLabel()
        kh.setObjectName("muted")
        kh.setWordWrap(True)
        self.keyring_hint = kh
        sl.addWidget(kh)
        right.addWidget(st)
        right.addStretch(1)

        self._devices: list[DeviceInfo] = []
        self._custom = False
        self.apply_language("de")

    # -- language -------------------------------------------------------------
    def _t(self, key: str) -> str:
        return T(self._lang, key)

    def apply_language(self, lang: str) -> None:
        self._lang = lang if lang in ("de", "en") else "de"
        self.acc_cap.setText(self._t("account").upper())
        self.apple_title.setText(self._t("apple_id"))
        self.edit_email.setPlaceholderText(self._t("email_ph"))
        self.edit_pass.setPlaceholderText(self._t("pass_ph"))
        self.cb_save.setText(self._t("save_user"))
        self.btn_login.setText(self._t("login"))
        self.mgmt_cap.setText(self._t("management").upper())
        self.mgmt.clear()
        for key, sc in zip(self.MGMT_KEYS, self.MGMT_SHORTCUTS, strict=True):
            QListWidgetItem(f"{self._t(key)}   ·   {sc}", self.mgmt)
        self.dev_cap.setText(self._t("devices").upper())
        self.dev_hint.setText(self._t("pick_device"))
        self.btn_refresh.setText(self._t("refresh"))
        self.ins_cap.setText(self._t("installers").upper())
        self.ins_hint.setText(self._t("pick_build"))
        self.btn_import.setText(self._t("import_ipa"))
        self.set_cap.setText(self._t("settings").upper())
        self.ani_label.setText(self._t("anisette"))
        self.btn_custom.setText(self._t("standard") if self._custom else self._t("custom"))
        self.lang_label.setText(self._t("language"))
        self.btn_trans.setText("Bei Übersetzungen helfen" if self._lang == "de" else "Help translate")
        self.btn_reset_ani.setText(self._t("reset_ani"))
        self.btn_del_pair.setText(self._t("del_pair"))
        self.btn_logs.setText(self._t("view_logs"))
        self.cb_keyring.setText(self._t("no_keyring"))
        self.keyring_hint.setText(
            "Ohne Schlüsselbund liegt der Benutzername als Hinweis in den Einstellungen. "
            "Passwörter werden grundsätzlich nie gespeichert."
            if self._lang == "de"
            else "Without keyring, the username hint lives in settings. Passwords are never stored."
        )
        self.combo_lang.blockSignals(True)
        self.combo_lang.setCurrentIndex(0 if self._lang == "de" else 1)
        self.combo_lang.blockSignals(False)
        self.set_devices(self._devices)

    def _lang_changed(self) -> None:
        lang = self.combo_lang.currentData() or "de"
        self.apply_language(str(lang))
        self.language_changed.emit(str(lang))

    # -- actions ---------------------------------------------------------------
    def _do_login(self) -> None:
        self.login_requested.emit(self.edit_email.text(), self.edit_pass.text(), self.cb_save.isChecked())
        self.edit_pass.clear()

    def _mgmt_clicked(self, item: QListWidgetItem) -> None:
        idx = self.mgmt.row(item)
        [self.open_pairing.emit, self.refresh_devices.emit, self.open_certificates.emit, self.open_app_ids.emit][idx]()

    def _dev_clicked(self, item: QListWidgetItem) -> None:
        udid = item.data(32)
        if udid:
            self.device_selected.emit(str(udid))

    def _toggle_custom(self) -> None:
        self._custom = not self._custom
        self.edit_custom.setVisible(self._custom)
        self.btn_custom.setText(self._t("standard") if self._custom else self._t("custom"))
        self._emit_ani()

    def _emit_ani(self) -> None:
        if self._custom:
            self.anisette_changed.emit(self.edit_custom.text(), True)
        else:
            self.anisette_changed.emit(self.combo_ani.currentData() or "", False)

    def load_settings(self, server: str, custom: bool, use_keyring: bool, email: str, lang: str) -> None:
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
        self.apply_language(lang)
        self.combo_ani.currentIndexChanged.connect(lambda: self._emit_ani())
        self.edit_custom.textChanged.connect(lambda: self._emit_ani())

    # -- data ---------------------------------------------------------------------
    def set_devices(self, devices: list[DeviceInfo], selected: str | None = None) -> None:
        self._devices = devices
        self.dev_list.clear()
        if not devices:
            row = QListWidgetItem(self._t("no_devices"))
            row.setFlags(Qt.ItemFlag.NoItemFlags)
            self.dev_list.addItem(row)
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
