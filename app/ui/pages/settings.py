"""Einstellungen: GENERAL / DEVICE / INSTALLATION / NOTIFICATIONS / ADVANCED / ABOUT."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app import __app_name__, __version__
from app.storage.settings import AppSettings
from app.ui import design as D


class SettingsPage(QWidget):
    save_requested = Signal()
    clear_credentials = Signal()
    clear_logs = Signal()
    clear_cache = Signal()
    show_pairing = Signal()
    browse_downloads = Signal()
    browse_provisioning = Signal()
    open_github = Signal()
    check_updates = Signal()

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
        body.setContentsMargins(26, 22, 26, 22)
        body.setSpacing(14)
        root.addWidget(scroll)
        scroll.setWidget(content)
        head = QLabel("Einstellungen")
        head.setObjectName("pageTitle")
        body.addWidget(head)

        # GENERAL
        c, lay = D.card()
        lay.addWidget(_section("Allgemein"))
        f = QFormLayout()
        self.cb_autostart = QCheckBox("Mit Windows starten")
        self.cb_tray = QCheckBox("In den Tray minimieren")
        self.cb_anim = QCheckBox("Animationen")
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["dark", "light"])
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["de", "en"])
        f.addRow(self.cb_autostart)
        f.addRow(self.cb_tray)
        f.addRow(self.cb_anim)
        f.addRow("Theme", self.combo_theme)
        f.addRow("Sprache", self.combo_lang)
        lay.addLayout(f)
        body.addWidget(c)

        # DEVICE
        c, lay = D.card()
        lay.addWidget(_section("Gerät"))
        f = QFormLayout()
        self.cb_autodetect = QCheckBox("Automatisch verbinden")
        self.cb_confirm = QCheckBox("Vor Installation bestätigen")
        self.cb_checkconn = QCheckBox("Verbindung prüfen")
        f.addRow(self.cb_autodetect)
        f.addRow(self.cb_confirm)
        f.addRow(self.cb_checkconn)
        lay.addLayout(f)
        body.addWidget(c)

        # INSTALLATION
        c, lay = D.card()
        lay.addWidget(_section("Installation"))
        f = QFormLayout()
        row_dl = QHBoxLayout()
        self.edit_folder = QLineEdit()
        self.btn_folder = QPushButton("Durchsuchen")
        self.btn_folder.setObjectName("ghost")
        self.btn_folder.clicked.connect(self.browse_downloads.emit)
        row_dl.addWidget(self.edit_folder, 1)
        row_dl.addWidget(self.btn_folder)
        self.spin_concurrent = QSpinBox()
        self.spin_concurrent.setRange(1, 8)
        self.cb_autoimport = QCheckBox("Heruntergeladene IPAs automatisch importieren")
        self.cb_keepipa = QCheckBox("IPA nach Installation behalten")
        f.addRow("Download-Ordner", row_dl)
        f.addRow("Gleichzeitige Downloads", self.spin_concurrent)
        f.addRow(self.cb_autoimport)
        f.addRow(self.cb_keepipa)
        lay.addLayout(f)
        # signing
        lay.addWidget(_section("Signierung"))
        f2 = QFormLayout()
        self.combo_account = QComboBox()
        self.combo_account.addItems(["free", "paid"])
        row_prov = QHBoxLayout()
        self.edit_prov = QLineEdit()
        self.edit_prov.setPlaceholderText("Ordner mit .mobileprovision-Dateien")
        self.btn_prov = QPushButton("Durchsuchen")
        self.btn_prov.setObjectName("ghost")
        self.btn_prov.clicked.connect(self.browse_provisioning.emit)
        row_prov.addWidget(self.edit_prov, 1)
        row_prov.addWidget(self.btn_prov)
        self.edit_appleid = QLineEdit()
        self.edit_appleid.setPlaceholderText("Apple-ID (nur Benutzername, nie das Passwort)")
        f2.addRow("Kontotyp", self.combo_account)
        f2.addRow("Provisioning-Ordner", row_prov)
        f2.addRow("Apple-ID", self.edit_appleid)
        lay.addLayout(f2)
        expl = QLabel(
            "Warum signieren? iOS startet nur Apps mit deinem eigenen Apple-Zertifikat. "
            "Kostenlose Accounts laufen nach 7 Tagen ab. Dein Passwort wird nirgends gespeichert."
        )
        expl.setWordWrap(True)
        expl.setObjectName("muted")
        lay.addWidget(expl)
        body.addWidget(c)

        # NOTIFICATIONS
        c, lay = D.card()
        lay.addWidget(_section("Mitteilungen"))
        self.cb_n_success = QCheckBox("Erfolgreiche Installation")
        self.cb_n_error = QCheckBox("Fehler")
        self.cb_n_download = QCheckBox("Downloads")
        for cb in (self.cb_n_success, self.cb_n_error, self.cb_n_download):
            lay.addWidget(cb)
        body.addWidget(c)

        # ADVANCED
        c, lay = D.card()
        lay.addWidget(_section("Erweitert"))
        self.cb_debug = QCheckBox("Debug-Modus (ausführliche Logs)")
        lay.addWidget(self.cb_debug)
        row = QHBoxLayout()
        self.btn_clear_creds = QPushButton("Gespeicherte Zugangsdaten löschen")
        self.btn_clear_creds.setObjectName("ghost")
        self.btn_clear_creds.clicked.connect(self.clear_credentials.emit)
        self.btn_clear_logs = QPushButton("Logs löschen")
        self.btn_clear_logs.setObjectName("ghost")
        self.btn_clear_logs.clicked.connect(self.clear_logs.emit)
        self.btn_clear_cache = QPushButton("Cache löschen")
        self.btn_clear_cache.setObjectName("ghost")
        self.btn_clear_cache.clicked.connect(self.clear_cache.emit)
        self.btn_pairing = QPushButton("Pairing-Dateien anzeigen")
        self.btn_pairing.setObjectName("ghost")
        self.btn_pairing.clicked.connect(self.show_pairing.emit)
        row.addWidget(self.btn_clear_creds)
        row.addWidget(self.btn_clear_logs)
        row.addWidget(self.btn_clear_cache)
        row.addWidget(self.btn_pairing)
        row.addStretch(1)
        lay.addLayout(row)
        note = QLabel("Zugangsdaten: OS-Schlüsselbund. Keine Telemetrie.")
        note.setObjectName("muted")
        lay.addWidget(note)
        body.addWidget(c)

        # ABOUT
        c, lay = D.card()
        lay.addWidget(_section("Über"))
        about = QLabel(f"{__app_name__} · v{__version__}\nOpen Source · MIT-Lizenz")
        about.setObjectName("muted")
        lay.addWidget(about)
        b_gh = QPushButton("GitHub öffnen")
        b_gh.setObjectName("ghost")
        b_gh.clicked.connect(self.open_github.emit)
        b_up = QPushButton("Auf Updates prüfen")
        b_up.setObjectName("ghost")
        b_up.clicked.connect(self.check_updates.emit)
        lay.addWidget(b_gh, alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(b_up, alignment=Qt.AlignmentFlag.AlignLeft)
        body.addWidget(c)

        self.btn_save = QPushButton("Speichern")
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self.save_requested.emit)
        body.addWidget(self.btn_save, alignment=Qt.AlignmentFlag.AlignLeft)
        body.addStretch(1)

    def load(self, s: AppSettings) -> None:
        self.cb_autostart.setChecked(s.general.start_with_windows)
        self.cb_tray.setChecked(s.general.minimize_to_tray)
        self.cb_anim.setChecked(s.general.animations)
        self.combo_theme.setCurrentText(s.general.theme if s.general.theme in ("dark", "light") else "dark")
        self.combo_lang.setCurrentText(s.general.language)
        self.cb_autodetect.setChecked(s.iphone.auto_detect)
        self.cb_confirm.setChecked(s.iphone.confirm_before_install)
        self.cb_checkconn.setChecked(s.iphone.check_connection)
        self.edit_folder.setText(s.downloads.folder)
        self.spin_concurrent.setValue(s.downloads.concurrent)
        self.cb_autoimport.setChecked(s.downloads.auto_import)
        self.cb_keepipa.setChecked(s.install.keep_ipa)
        self.combo_account.setCurrentText(s.signing.account_type)
        self.edit_prov.setText(s.signing.provisioning_dir)
        self.edit_appleid.setText(s.signing.apple_id_username)
        self.cb_n_success.setChecked(s.notify.on_success)
        self.cb_n_error.setChecked(s.notify.on_error)
        self.cb_n_download.setChecked(s.notify.on_download)
        self.cb_debug.setChecked(s.advanced.debug_mode)

    def collect(self, s: AppSettings) -> None:
        s.general.start_with_windows = self.cb_autostart.isChecked()
        s.general.minimize_to_tray = self.cb_tray.isChecked()
        s.general.animations = self.cb_anim.isChecked()
        s.general.theme = self.combo_theme.currentText()
        s.general.language = self.combo_lang.currentText()
        s.iphone.auto_detect = self.cb_autodetect.isChecked()
        s.iphone.confirm_before_install = self.cb_confirm.isChecked()
        s.iphone.check_connection = self.cb_checkconn.isChecked()
        s.downloads.folder = self.edit_folder.text().strip()
        s.downloads.concurrent = self.spin_concurrent.value()
        s.downloads.auto_import = self.cb_autoimport.isChecked()
        s.install.keep_ipa = self.cb_keepipa.isChecked()
        s.signing.account_type = self.combo_account.currentText()
        s.signing.provisioning_dir = self.edit_prov.text().strip()
        s.signing.apple_id_username = self.edit_appleid.text().strip()
        s.notify.on_success = self.cb_n_success.isChecked()
        s.notify.on_error = self.cb_n_error.isChecked()
        s.notify.on_download = self.cb_n_download.isChecked()
        s.advanced.debug_mode = self.cb_debug.isChecked()


def _section(text: str) -> QLabel:
    label = QLabel(text.upper())
    label.setObjectName("section")
    return label
