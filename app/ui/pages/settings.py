"""Settings page: General / iPhone / Downloads / Security / Signing."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.storage.settings import AppSettings
from app.ui.widgets import Card, secondary_button


class SettingsPage(QWidget):
    save_requested = Signal()
    clear_credentials = Signal()
    clear_logs = Signal()
    browse_downloads = Signal()
    browse_provisioning = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        head = QLabel("Settings")
        head.setObjectName("title")
        layout.addWidget(head)

        # General
        self.general_card = Card()
        self.general_card.add(_h("General"))
        form = QFormLayout()
        self.cb_autostart = QCheckBox("Start with Windows")
        self.cb_tray = QCheckBox("Minimize to tray")
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["dark", "light", "system"])
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["en", "de"])
        form.addRow(self.cb_autostart)
        form.addRow(self.cb_tray)
        form.addRow("Theme", self.combo_theme)
        form.addRow("Language", self.combo_lang)
        self.general_card.add_layout(form)
        layout.addWidget(self.general_card)

        # iPhone
        self.iphone_card = Card()
        self.iphone_card.add(_h("iPhone"))
        form2 = QFormLayout()
        self.cb_autodetect = QCheckBox("Auto-detect devices")
        self.cb_confirm = QCheckBox("Confirm before installation")
        form2.addRow(self.cb_autodetect)
        form2.addRow(self.cb_confirm)
        self.iphone_card.add_layout(form2)
        layout.addWidget(self.iphone_card)

        # Downloads
        self.dl_card = Card()
        self.dl_card.add(_h("Downloads"))
        form3 = QFormLayout()
        row_dl = QHBoxLayout()
        self.edit_folder = QLineEdit()
        self.btn_folder = secondary_button("Browse")
        self.btn_folder.clicked.connect(self.browse_downloads.emit)
        row_dl.addWidget(self.edit_folder, 1)
        row_dl.addWidget(self.btn_folder)
        self.spin_concurrent = QSpinBox()
        self.spin_concurrent.setRange(1, 8)
        self.cb_autoimport = QCheckBox("Automatically import downloaded IPAs")
        form3.addRow("Download folder", row_dl)
        form3.addRow("Concurrent downloads", self.spin_concurrent)
        form3.addRow(self.cb_autoimport)
        self.dl_card.add_layout(form3)
        layout.addWidget(self.dl_card)

        # Signing
        self.sign_card = Card()
        self.sign_card.add(_h("Signing"))
        form4 = QFormLayout()
        self.combo_account = QComboBox()
        self.combo_account.addItems(["free", "paid"])
        row_prov = QHBoxLayout()
        self.edit_prov = QLineEdit()
        self.edit_prov.setPlaceholderText("Folder with .mobileprovision files")
        self.btn_prov = secondary_button("Browse")
        self.btn_prov.clicked.connect(self.browse_provisioning.emit)
        row_prov.addWidget(self.edit_prov, 1)
        row_prov.addWidget(self.btn_prov)
        self.edit_appleid = QLineEdit()
        self.edit_appleid.setPlaceholderText("Apple ID email (username hint only, never the password)")
        form4.addRow("Account type", self.combo_account)
        form4.addRow("Provisioning folder", row_prov)
        form4.addRow("Apple ID", self.edit_appleid)
        expl = QLabel(
            "Why sign in? iOS only runs apps signed with your own Apple Developer "
            "certificate. Free accounts expire after 7 days. Your password is never "
            "stored \u2014 only the username hint goes to Windows Credential Manager."
        )
        expl.setWordWrap(True)
        expl.setObjectName("muted")
        self.sign_card.add_layout(form4)
        self.sign_card.add(expl)
        layout.addWidget(self.sign_card)

        # Security
        self.sec_card = Card()
        self.sec_card.add(_h("Security"))
        row_sec = QHBoxLayout()
        self.btn_clear_creds: QPushButton = secondary_button("Clear cached credentials")
        self.btn_clear_creds.clicked.connect(self.clear_credentials.emit)
        self.btn_clear_logs: QPushButton = secondary_button("Clear logs")
        self.btn_clear_logs.clicked.connect(self.clear_logs.emit)
        row_sec.addWidget(self.btn_clear_creds)
        row_sec.addWidget(self.btn_clear_logs)
        row_sec.addStretch(1)
        note = QLabel("Credential storage: OS keychain (Windows Credential Manager). No telemetry.")
        note.setObjectName("muted")
        self.sec_card.add(note)
        self.sec_card.add_layout(row_sec)
        layout.addWidget(self.sec_card)

        self.btn_save: QPushButton = QPushButton("Save")
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self.save_requested.emit)
        layout.addWidget(self.btn_save)
        layout.addStretch(1)

    def load(self, s: AppSettings) -> None:
        self.cb_autostart.setChecked(s.general.start_with_windows)
        self.cb_tray.setChecked(s.general.minimize_to_tray)
        self.combo_theme.setCurrentText(s.general.theme)
        self.combo_lang.setCurrentText(s.general.language)
        self.cb_autodetect.setChecked(s.iphone.auto_detect)
        self.cb_confirm.setChecked(s.iphone.confirm_before_install)
        self.edit_folder.setText(s.downloads.folder)
        self.spin_concurrent.setValue(s.downloads.concurrent)
        self.cb_autoimport.setChecked(s.downloads.auto_import)
        self.combo_account.setCurrentText(s.signing.account_type)
        self.edit_prov.setText(s.signing.provisioning_dir)
        self.edit_appleid.setText(s.signing.apple_id_username)

    def collect(self, s: AppSettings) -> None:
        s.general.start_with_windows = self.cb_autostart.isChecked()
        s.general.minimize_to_tray = self.cb_tray.isChecked()
        s.general.theme = self.combo_theme.currentText()
        s.general.language = self.combo_lang.currentText()
        s.iphone.auto_detect = self.cb_autodetect.isChecked()
        s.iphone.confirm_before_install = self.cb_confirm.isChecked()
        s.downloads.folder = self.edit_folder.text().strip()
        s.downloads.concurrent = self.spin_concurrent.value()
        s.downloads.auto_import = self.cb_autoimport.isChecked()
        s.signing.account_type = self.combo_account.currentText()
        s.signing.provisioning_dir = self.edit_prov.text().strip()
        s.signing.apple_id_username = self.edit_appleid.text().strip()


def _h(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("cardTitle")
    return label
