"""App shell v3 (Mockup): 6 Bereiche, Profil, Statusbar, Quick-Actions."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizeGrip,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from app import __app_name__, __version__
from app.companion.anisette import SERVERS as SERVERS_ANI
from app.companion.anisette import AnisetteState, check_reachable, normalize_server
from app.companion.installers import CompanionInstaller
from app.companion.models import INSTALLERS, AppleSession, InstallerDef
from app.core.config import AppConfig
from app.core.logging import get_logger
from app.device.interface import DeviceService
from app.device.models import DeviceInfo
from app.device.pairing import list_pair_records
from app.downloads.manager import DownloadItem, DownloadManager, DownloadState
from app.installation.models import InstallationJob
from app.installation.service import InstallationService
from app.ipa.library import IpaLibrary
from app.ipa.models import IpaInfo
from app.security import credentials as creds
from app.signing.base import SigningProvider
from app.signing.models import SigningIdentity
from app.storage.autostart import set_start_with_windows
from app.storage.history import HistoryStore
from app.storage.settings import SettingsStore
from app.ui import design as D
from app.ui.dialogs.app_details import AppDetailsDialog
from app.ui.dialogs.companion_dialogs import (
    AppIdsDialog,
    CertificatesDialog,
    CompanionProgressDialog,
    PairingDialog,
)
from app.ui.dialogs.install_dialog import InstallDialog
from app.ui.dialogs.quick_actions import BundleIdDialog, ProfilesDialog, QrDialog, SignDialog, UrlDownloadDialog
from app.ui.dialogs.search_dialog import SearchDialog
from app.ui.dialogs.wizard import FirstLaunchWizard
from app.ui.icons import icon as make_icon
from app.ui.pages.apps import AppsPage
from app.ui.pages.companion import CompanionPage
from app.ui.pages.devices import DevicesPage
from app.ui.pages.home import HomePage
from app.ui.pages.library import LibraryPage
from app.ui.pages.logs import LogsPage
from app.ui.pages.settings import SettingsPage
from app.ui.widgets.toasts import ToastManager

log = get_logger("ui")

NAV = [
    ("Home", "home"),
    ("Apps", "apps"),
    ("Geräte", "phone"),
    ("Companion", "link"),
    ("Bibliothek", "book"),
    ("Logs", "history"),
    ("Einstellungen", "gear"),
]


class CompanionWorker(QThread):
    stepped = Signal(str, float, str)
    finished_job = Signal(object)

    def __init__(self, runner: CompanionInstaller, definition, udid: str) -> None:
        super().__init__()
        self.runner = runner
        self.definition = definition
        self.udid = udid

    def run(self) -> None:
        job = self.runner.run(self.definition, self.udid, on_step=self.stepped.emit)
        self.finished_job.emit(job)


class InstallWorker(QThread):
    stepped = Signal(object)

    def __init__(self, service: InstallationService, job: InstallationJob) -> None:
        super().__init__()
        self.service = service
        self.job = job

    def run(self) -> None:
        self.service.run(self.job, on_step=self.stepped.emit)


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: AppConfig,
        settings: SettingsStore,
        devices: DeviceService,
        library: IpaLibrary,
        downloads: DownloadManager,
        installer: InstallationService,
    ) -> None:
        super().__init__()
        self.config = config
        self.settings = settings
        self.devices = devices
        self.library = library
        self.downloads = downloads
        self.installer = installer
        self.history = HistoryStore(config.app_data_dir / "history.jsonl")
        self._worker: InstallWorker | None = None
        self._dialog: InstallDialog | None = None
        self._fade_anim: QPropertyAnimation | None = None
        self._known_devices: set[str] = set()
        self._dl_states: dict[int, DownloadState] = {}
        self._details_cache: dict[str, dict] = {}
        self._installed_cache: list[dict] = []
        self._selected_udid: str | None = None
        self.session = AppleSession()
        self.anisette = AnisetteState(config.app_data_dir / "anisette")
        self.companion_runner = CompanionInstaller(downloads, installer)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.resize(1360, 820)
        self.setMinimumSize(1280, 720)
        self._drag_pos = None

        central = QWidget()
        central.setObjectName("shell")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._build_sidebar(root)
        main_col = QVBoxLayout()
        main_col.setContentsMargins(0, 0, 0, 0)
        main_col.setSpacing(0)
        self._build_topbar(main_col)
        self.stack = QStackedWidget()
        main_col.addWidget(self.stack, 1)
        self._build_statusbar(main_col)
        wrap = QWidget()
        wrap.setLayout(main_col)
        root.addWidget(wrap, 1)

        self.home = HomePage()
        self.apps = AppsPage()
        self.devices_page = DevicesPage()
        self.companion = CompanionPage()
        self.library_page = LibraryPage()
        self.logs_page = LogsPage(config.log_dir / "deniz-sideloader.log")
        self.settings_page = SettingsPage()
        self._pages = [
            self.home,
            self.apps,
            self.devices_page,
            self.companion,
            self.library_page,
            self.logs_page,
            self.settings_page,
        ]
        for p in self._pages:
            self.stack.addWidget(p)

        self.toasts = ToastManager(central)
        self._wire()
        self._shortcuts()
        self._tray()
        from PySide6.QtCore import QTimer as _QTimer

        self._log_timer = _QTimer(self)
        self._log_timer.setInterval(5000)
        self._log_timer.timeout.connect(self._maybe_refresh_logs)
        self._log_timer.start()
        self.refresh_all()

    # -- shell -------------------------------------------------------------
    def _build_sidebar(self, root: QHBoxLayout) -> None:
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(248)
        self.sidebar = side
        lay = QVBoxLayout(side)
        lay.setContentsMargins(14, 16, 14, 14)
        lay.setSpacing(8)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        brand.addWidget(D.logo_badge(40))
        bcol = QVBoxLayout()
        bcol.setSpacing(0)
        b = QLabel("Deniz Sideloader")
        b.setObjectName("brand")
        v = QLabel(f"Version {__version__}")
        v.setObjectName("brandSub")
        bcol.addWidget(b)
        bcol.addWidget(v)
        brand.addLayout(bcol, 1)
        self.btn_collapse = QPushButton()
        self.btn_collapse.setObjectName("iconbtn")
        self.btn_collapse.setIcon(make_icon("sidebar", 18))
        self.btn_collapse.setToolTip("Sidebar ein-/ausklappen")
        self.btn_collapse.clicked.connect(self._toggle_sidebar)
        brand.addWidget(self.btn_collapse)
        lay.addLayout(brand)

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        for name, glyph in NAV:
            item = QListWidgetItem(make_icon(glyph, 18), name)
            item.setData(32, glyph)
            self.nav.addItem(item)
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(self._switch)
        lay.addWidget(self.nav, 1)

        self.profile, play = D.card(obj="card2")
        play.setContentsMargins(12, 10, 12, 10)
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(D.logo_badge(36))
        tx = QVBoxLayout()
        tx.setSpacing(0)
        self.prof_name = QLabel("Deniz")
        self.prof_name.setStyleSheet("font-size: 13px; font-weight: 700;")
        self.prof_type = QLabel("Kostenlos")
        self.prof_type.setObjectName("muted")
        tx.addWidget(self.prof_name)
        tx.addWidget(self.prof_type)
        row.addLayout(tx, 1)
        play.addLayout(row)
        lay.addWidget(self.profile)
        root.addWidget(side)

    def _build_topbar(self, col: QVBoxLayout) -> None:
        bar = QWidget()
        bar.setObjectName("topbar")
        bar.setFixedHeight(60)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 10, 16, 10)
        lay.setSpacing(10)
        ver = D.chip(f"Version {__version__}", "blue")
        lay.addWidget(ver)
        lay.addStretch(1)
        self.search_btn = QPushButton("  Apps, IPA-Dateien oder Geräte suchen …      Strg + K")
        self.search_btn.setObjectName("ghost")
        self.search_btn.setMinimumWidth(380)
        self.search_btn.setIcon(make_icon("search", 16))
        self.search_btn.clicked.connect(self._open_search)
        lay.addWidget(self.search_btn)
        lay.addStretch(1)
        self.conn = D.chip("Getrennt", "gray")
        lay.addWidget(self.conn)
        self.btn_theme = QPushButton()
        self.btn_theme.setObjectName("iconbtn")
        self.btn_theme.setToolTip("Hell/Dunkel wechseln")
        self.btn_theme.clicked.connect(self._toggle_theme)
        lay.addWidget(self.btn_theme)
        b_set = QPushButton()
        b_set.setObjectName("iconbtn")
        b_set.setIcon(make_icon("gear", 18))
        b_set.setToolTip("Einstellungen")
        b_set.clicked.connect(lambda: self._switch(6))
        lay.addWidget(b_set)
        for glyph, tip, slot in (
            ("min", "Minimieren", self.showMinimized),
            ("max", "Maximieren", self._toggle_max),
            ("close", "Schließen", self.close),
        ):
            btn = QPushButton()
            btn.setObjectName("iconbtn")
            btn.setIcon(make_icon(glyph, 16))
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            lay.addWidget(btn)
        col.addWidget(bar)
        self.topbar = bar
        self._refresh_theme_icon()
        QSizeGrip(self).setFixedSize(16, 16)

    def _build_statusbar(self, col: QVBoxLayout) -> None:
        bar = self.statusBar()
        self.st_dot = QLabel("●")
        self.st_dot.setStyleSheet(f"color: {D.GREEN}; font-size: 11px;")
        self.st_text = QLabel("Bereit für Sideloading")
        self.st_text.setObjectName("statusOk")
        bar.addWidget(self.st_dot)
        bar.addWidget(self.st_text, 1)
        self.st_ios = QLabel("")
        self.st_ios.setObjectName("muted")
        self.st_conn = QLabel("")
        self.st_conn.setObjectName("muted")
        bar.addPermanentWidget(self.st_ios)
        bar.addPermanentWidget(self.st_conn)

    # -- wiring --------------------------------------------------------------
    def _wire(self) -> None:
        self.home.choose_ipa.connect(self.choose_and_install)
        self.home.files_dropped.connect(self._import_many)
        self.home.goto.connect(self._switch)
        self.home.quick_library.connect(self._goto_library_files)
        self.home.quick_url.connect(self._ask_url)
        self.home.quick_qr.connect(lambda: QrDialog(parent=self).exec())
        self.home.action_sign.connect(self._quick_sign)
        self.home.action_bundle.connect(self._quick_bundle)
        self.home.action_profiles.connect(self._show_profiles)
        self.home.action_logs.connect(lambda: self._switch(5))
        self.home.install_ipa.connect(lambda info: self._install_path(info.path))
        self.home.open_details.connect(self._show_details)
        self.home.uninstall_app.connect(self._uninstall_app)
        self.companion.login_requested.connect(self._companion_login)
        self.companion.logout_requested.connect(self._companion_logout)
        self.companion.refresh_devices.connect(lambda: self.refresh_devices(True))
        self.companion.device_selected.connect(self._select_device)
        self.companion.open_pairing.connect(self._open_pairing)
        self.companion.open_certificates.connect(self._open_certificates)
        self.companion.open_app_ids.connect(self._open_app_ids)
        self.companion.install_with.connect(self._install_with)
        self.companion.import_ipa.connect(self.import_ipa)
        self.companion.anisette_changed.connect(self._anisette_changed)
        self.companion.reset_anisette.connect(self._reset_anisette)
        self.companion.delete_pairing.connect(self._delete_pairing)
        self.companion.view_logs.connect(lambda: self._switch(5))
        self.companion.keyring_toggled.connect(self._keyring_toggled)
        self.companion.btn_github.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/dbudakli1402-collab/DenizSideloader"))
        )
        self.apps.install_ipa.connect(lambda info: self._install_path(info.path))
        self.apps.import_requested.connect(self.import_ipa)
        self.apps.open_details.connect(self._show_details)
        self.apps.uninstall_app.connect(self._uninstall_app)
        self.library_page.install_ipa.connect(lambda info: self._install_path(info.path))
        self.library_page.import_requested.connect(self.import_ipa)
        self.library_page.files_dropped.connect(self._import_many)
        self.library_page.open_details.connect(self._show_details)
        self.library_page.set_category.connect(self._set_category)
        self.library_page.rename_requested.connect(self._rename_ipa)
        self.library_page.reveal_requested.connect(self._reveal_ipa)
        self.library_page.remove_requested.connect(self._remove_ipa)
        self.library_page.start_download.connect(self._start_download)
        self.library_page.cancel_download.connect(self._cancel_download)
        self.library_page.pause_download.connect(self._pause_download)
        self.devices_page.refresh_requested.connect(lambda: self.refresh_devices(True))
        self.devices_page.show_apps.connect(lambda: self._switch(1))
        self.logs_page.clear_logs.connect(self._clear_logs)
        self.logs_page.open_folder.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.config.log_dir)))
        )
        self.settings_page.save_requested.connect(self._save_settings)
        self.settings_page.clear_credentials.connect(self._clear_creds)
        self.settings_page.clear_logs.connect(self._clear_logs)
        self.settings_page.clear_cache.connect(self._clear_cache)
        self.settings_page.show_pairing.connect(self.show_pairing)
        self.settings_page.browse_downloads.connect(self._browse_downloads)
        self.settings_page.browse_provisioning.connect(self._browse_prov)
        self.settings_page.open_github.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/dbudakli1402-collab/DenizSideloader"))
        )

    def _shortcuts(self) -> None:
        sc = QShortcut(QKeySequence("Ctrl+K"), self)
        sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc.activated.connect(self._open_search)
        for i in range(7):
            s = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            s.setContext(Qt.ShortcutContext.ApplicationShortcut)
            s.activated.connect(lambda _=False, n=i: self._switch(n))
        for seq, slot in [
            ("Ctrl+R", lambda: self.refresh_devices(True)),
            ("Ctrl+P", self._open_pairing),
            ("Ctrl+L", lambda: self._switch(5)),
        ]:
            sc = QShortcut(QKeySequence(seq), self)
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
            sc.activated.connect(slot)

    def _tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self)
        menu = QMenu()
        show_act = QAction("Anzeigen", self)
        show_act.triggered.connect(self.showNormal)
        quit_act = QAction("Beenden", self)
        quit_act.triggered.connect(self.close)
        menu.addAction(show_act)
        menu.addAction(quit_act)
        self.tray.setContextMenu(menu)
        self.tray.show()

    # -- navigation ------------------------------------------------------------
    def _switch(self, row: int) -> None:
        self.nav.blockSignals(True)
        self.nav.setCurrentRow(row)
        self.nav.blockSignals(False)
        if self.settings.settings.general.animations:
            self._fade_to(row)
        else:
            self.stack.setCurrentIndex(row)
        if row in (0, 2):
            self.refresh_devices()
        if row in (0, 1):
            self.refresh_apps()
        if row == 4:
            self.refresh_library()
            self.refresh_downloads()
        if row == 5:
            self.logs_page.reload()
            self.logs_page.set_events(self.history.list("all"))

    def _fade_to(self, row: int) -> None:
        self.stack.setCurrentIndex(row)
        if self._fade_anim is not None:
            try:
                self._fade_anim.stop()
            except Exception:
                pass
            self._fade_anim = None
        self.stack.setGraphicsEffect(None)  # type: ignore[arg-type]
        eff = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(180)
        anim.setStartValue(0.4)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(self._clear_fade)
        self._fade_anim = anim
        anim.start()

    def _clear_fade(self) -> None:
        self.stack.setGraphicsEffect(None)  # type: ignore[arg-type]
        self._fade_anim = None

    def _toggle_sidebar(self) -> None:
        narrow = self.sidebar.width() > 130
        for prop, target in (("minimumWidth", 64 if narrow else 248), ("maximumWidth", 64 if narrow else 248)):
            anim = QPropertyAnimation(self.sidebar, prop.encode(), self)
            anim.setDuration(200)
            anim.setStartValue(self.sidebar.width())
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim.start()

    def _toggle_max(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _toggle_theme(self) -> None:
        s = self.settings.settings
        s.general.theme = "light" if s.general.theme == "dark" else "dark"
        self.settings.save()
        from PySide6.QtWidgets import QApplication

        from app.ui.design import apply_theme

        apply_theme(QApplication.instance(), s.general.theme)
        self._refresh_theme_icon()

    def _refresh_theme_icon(self) -> None:
        dark = self.settings.settings.general.theme != "light"
        self.btn_theme.setIcon(make_icon("moon" if dark else "sun", 18))

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.topbar.underMouse():
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if self.topbar.underMouse():
            self._toggle_max()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "toasts"):
            self.toasts.resize_to_parent()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and hasattr(self, "toasts"):
            self.toasts.resize_to_parent()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        return super().eventFilter(watched, event)

    def _goto_library_files(self) -> None:
        self._switch(4)
        self.library_page.tabs.setCurrentIndex(0)

    def _maybe_refresh_logs(self) -> None:
        try:
            if self.stack.currentIndex() == 5:
                self.logs_page.reload()
        except Exception:
            pass

    # -- search ------------------------------------------------------------------
    def _open_search(self) -> None:
        dlg = SearchDialog(self)
        dlg.set_data(self.library.list(), self.devices.cached, self._installed_cache)
        dlg.picked_ipa.connect(lambda info: self._show_details({"ipa": info}))
        dlg.picked_app.connect(self._show_details)
        dlg.picked_device.connect(lambda _d: self._switch(2))
        dlg.exec()

    # -- refresh -------------------------------------------------------------------
    def refresh_all(self) -> None:
        self.refresh_devices()
        self.refresh_library()
        self.refresh_downloads()
        self.refresh_apps()
        self.settings_page.load(self.settings.settings)
        self.logs_page.set_events(self.history.list("all"))
        self.home.set_apps(self._installed_cache, self.library.list())
        self._update_profile()
        s = self.settings.settings
        email = ""
        if s.companion.use_keyring:
            try:
                email = creds.load_secret("apple-id-username") or s.signing.apple_id_username
            except Exception:
                email = s.signing.apple_id_username
        else:
            email = s.signing.apple_id_username
        self.companion.load_settings(
            s.companion.anisette_server, s.companion.anisette_custom, s.companion.use_keyring, email or ""
        )
        if self.session.email:
            self.companion.set_login_state(f"Sitzung vorbereitet ({self.session.email}).", True)

    def refresh_devices(self, manual: bool = False) -> None:
        found = self.devices.refresh()
        current = {d.udid for d in found}
        for d in found:
            if d.udid not in self._known_devices:
                self.history.record("device", f"Gerät verbunden: {d.display_name}", f"iOS {d.ios_version}")
                if self.settings.settings.notify.on_success:
                    self.toasts.info("iPhone verbunden", d.display_name)
        for _gone in self._known_devices - current:
            self.history.record("device", "Gerät getrennt", status="info")
        self._known_devices = current

        dev = found[0] if found else None
        if self._selected_udid and self._selected_udid not in current:
            self._selected_udid = None
        self.companion.set_devices(found, selected=self._selected_udid)
        details: dict = {}
        if dev is not None:
            details = self._device_details(dev.udid)
        self.home.set_device(dev, details.get(dev.udid, {}) if dev else {})
        self.home.set_apps(self._installed_cache, self.library.list())
        self.devices_page.set_devices(found, details, self.devices.backend_help() if not found else "")
        self._set_conn(dev is not None)
        self._update_statusbar(dev)
        self._update_badges()
        if manual:
            self.statusBar().showMessage("Bereit")
            self.toasts.info("Geräte aktualisiert", f"{len(found)} Gerät(e) gefunden.")

    def _device_details(self, udid: str) -> dict:
        if udid in self._details_cache:
            return self._details_cache
        for prov in self.devices.providers:
            fn = getattr(prov, "get_device_details", None)
            if callable(fn):
                try:
                    det = fn(udid)
                    if det:
                        self._details_cache = {udid: det}
                        return self._details_cache
                except Exception:
                    continue
        return {}

    def _set_conn(self, connected: bool) -> None:
        self.conn.setText("Verbunden" if connected else "Getrennt")
        if connected:
            self.conn.setStyleSheet(f"QLabel#chip {{ background: {D.GREEN_BG}; color: {D.GREEN}; }}")
        else:
            self.conn.setStyleSheet("QLabel#chip { background: #16203a; color: #8b94a9; }")

    def _update_statusbar(self, dev: DeviceInfo | None) -> None:
        if dev is None:
            self.st_dot.setStyleSheet(f"color: {D.FAINT}; font-size: 11px;")
            self.st_text.setText("Nicht verbunden")
            self.st_text.setObjectName("muted")
            self.st_ios.setText("")
            self.st_conn.setText("")
            return
        self.st_dot.setStyleSheet(f"color: {D.GREEN}; font-size: 11px;")
        self.st_text.setText("Bereit für Sideloading")
        self.st_text.setObjectName("statusOk")
        self.st_ios.setText(f"iOS {dev.ios_version}")
        self.st_conn.setText(f"{dev.connection.value.upper()} · Verbunden")

    def _update_profile(self) -> None:
        s = self.settings.settings
        self.prof_name.setText(s.signing.apple_id_username or "Deniz")
        self.prof_type.setText("Bezahlt" if s.signing.account_type == "paid" else "Kostenlos")

    def refresh_library(self) -> None:
        items = self.library.list()
        self.library_page.set_items(items)
        self._update_badges()

    def refresh_apps(self) -> None:
        found = self.devices.cached or self.devices.refresh()
        apps: list[dict] = []
        if found:
            for prov in self.devices.providers:
                fn = getattr(prov, "list_installed_apps", None)
                if callable(fn):
                    try:
                        apps = fn(found[0].udid)
                        if apps:
                            break
                    except Exception:
                        continue
        self._installed_cache = apps
        self.apps.set_data(apps, self.library.list())
        self.home.set_apps(apps, self.library.list())
        self._update_badges()

    def refresh_downloads(self) -> None:
        items = self.downloads.items
        for it in items:
            prev = self._dl_states.get(id(it))
            if prev != it.state:
                if it.state == DownloadState.DONE and prev not in (None, DownloadState.DONE):
                    self.history.record("download", f"Download fertig: {it.dest.name}", f"SHA-256: {it.sha256[:16]}…")
                    if self.settings.settings.notify.on_download:
                        self.toasts.success("Download abgeschlossen", it.dest.name)
                    if self.settings.settings.downloads.auto_import:
                        try:
                            self.library.import_file(it.dest)
                            self.refresh_library()
                        except Exception as exc:
                            log.warning("auto-import failed: %s", exc)
                elif it.state == DownloadState.ERROR:
                    self.history.record(
                        "download",
                        f"Download fehlgeschlagen: {it.dest.name}",
                        it.error[:200],
                        status="fail",
                    )
                    if self.settings.settings.notify.on_error:
                        self.toasts.error("Download fehlgeschlagen", it.dest.name)
                elif it.state == DownloadState.CANCELLED and prev is not None:
                    self.history.record("download", f"Download abgebrochen: {it.dest.name}", status="info")
            self._dl_states[id(it)] = it.state
        self.library_page.set_downloads(items)
        self._update_badges()

    def _update_badges(self) -> None:
        lib_n = len(self.library.list())
        counts = {"Apps": len(self._installed_cache), "Bibliothek": lib_n, "Geräte": len(self.devices.cached)}
        for i in range(self.nav.count()):
            item = self.nav.item(i)
            name = NAV[i][0]
            glyph = item.data(32)
            n = counts.get(name, 0)
            item.setText(f"{name}   ·   {n}" if n else name)
            item.setIcon(make_icon(glyph, 18))

    # -- IPA flows ---------------------------------------------------------------------
    def choose_and_install(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "IPA-Datei auswählen", "", "iOS-App (*.ipa)")
        if path:
            self._install_path(path)

    def import_ipa(self) -> None:
        path = self.library_page.pick_file()
        if path:
            self._import_many([path])

    def _import_many(self, paths: list[str]) -> None:
        ok, fail = 0, 0
        for p in paths:
            try:
                info = self.library.import_file(p)
                self.history.record("download", f"IPA importiert: {info.display_title}", info.bundle_id)
                ok += 1
            except Exception as exc:
                fail += 1
                log.warning("import failed %s: %s", p, exc)
        self.refresh_library()
        if ok:
            self.toasts.success(f"{ok} IPA(s) importiert")
        if fail:
            self.toasts.error("Import fehlgeschlagen", f"{fail} Datei(en) ungültig.")

    def _set_category(self, info: object, cat: str) -> None:
        assert isinstance(info, IpaInfo)
        self.library.set_category(info, cat)
        self.refresh_library()

    def _rename_ipa(self, info: IpaInfo) -> None:
        name = self.library_page.ask_name(info.file_name)
        if not name or name == info.file_name:
            return
        try:
            self.library.rename(info, name)
            self.refresh_library()
            self.toasts.success("Umbenannt", name)
        except Exception as exc:
            self.toasts.error("Umbenennen fehlgeschlagen", str(exc)[:200])

    def _reveal_ipa(self, info: IpaInfo) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(info.path).parent)))

    def _remove_ipa(self, info: IpaInfo) -> None:
        if (
            QMessageBox.question(self, "Löschen", f"{info.display_title} aus der Bibliothek löschen?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        self.library.remove(info)
        self.history.record("download", f"IPA gelöscht: {info.display_title}", status="info")
        self.refresh_library()

    def _show_details(self, payload: dict) -> None:
        dlg = AppDetailsDialog(payload, self)
        dlg.install_ipa.connect(lambda p: self._install_path(p.path) if isinstance(p, IpaInfo) else None)
        dlg.category_changed.connect(lambda p, c: self._set_category(p, c))
        dlg.exec()

    def _uninstall_app(self, payload: dict) -> None:
        bundle = str(payload.get("bundle_id", ""))
        name = str(payload.get("name", bundle))
        found = self.devices.cached or self.devices.refresh()
        if not found:
            self.toasts.error("Kein iPhone gefunden", "Verbinde dein iPhone per USB.")
            return
        if (
            QMessageBox.question(self, "Deinstallieren?", f"{name} vom iPhone entfernen?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        ok, msg = False, "Backend fehlt"
        for prov in self.devices.providers:
            fn = getattr(prov, "uninstall_app", None)
            if callable(fn):
                try:
                    ok, msg = fn(found[0].udid, bundle)
                    break
                except Exception as exc:
                    ok, msg = False, str(exc)[:300]
        if ok:
            self.history.record("install", f"Deinstalliert: {name}", bundle)
            self.toasts.success("Deinstalliert", name)
            self.refresh_apps()
        else:
            self.history.record("install", f"Deinstallieren fehlgeschlagen: {name}", msg[:200], status="fail")
            self.toasts.error("Deinstallieren fehlgeschlagen", msg[:200])

    def _install_path(self, path: str) -> None:
        s = self.settings.settings
        try:
            if Path(path).is_file() and Path(path).suffix.lower() == ".ipa":
                if not any(i.path == path for i in self.library.list()):
                    try:
                        info = self.library.import_file(path)
                        path = info.path
                        self.refresh_library()
                    except Exception:
                        pass
        except Exception:
            pass
        found = self.devices.cached or self.devices.refresh()
        if not found:
            self.toasts.error("Kein iPhone gefunden", "Verbinde dein iPhone per USB und entsperre es.")
            self._switch(2)
            return
        target = found[0]
        if s.iphone.confirm_before_install:
            if (
                QMessageBox.question(
                    self, "Installieren?", f"{Path(path).name} auf {target.display_name} installieren?"
                )
                != QMessageBox.StandardButton.Yes
            ):
                return
        job = InstallationJob(ipa_path=path, udid=target.udid)
        self.history.record("install", f"Installation gestartet: {Path(path).stem}", target.display_name)
        self._dialog = InstallDialog(job, self)
        self._dialog.show()
        self._worker = InstallWorker(self.installer, job)
        self._worker.stepped.connect(lambda j: self._dialog.update_job(j) if self._dialog else None)
        self._worker.finished.connect(lambda: self._install_finished(job))
        self._worker.start()

    def _install_finished(self, job: InstallationJob) -> None:
        if self._dialog:
            self._dialog.update_job(job)
        try:
            Path(job.ipa_path).with_name(Path(job.ipa_path).stem + ".signed.ipa").unlink(missing_ok=True)
        except Exception:
            pass
        if job.step.value == "done":
            self.history.record("install", f"Installiert: {job.app_name}", job.bundle_id)
            if self.settings.settings.notify.on_success:
                self.toasts.success("Installation abgeschlossen", f"{job.app_name} wurde installiert.")
            if self._dialog:
                self._dialog.accept()
            if not self.settings.settings.install.keep_ipa:
                try:
                    info = next((i for i in self.library.list() if i.path == job.ipa_path), None)
                    if info is not None:
                        self.library.remove(info)
                        self.refresh_library()
                except Exception:
                    pass
            self.refresh_apps()
        elif job.step.value == "failed":
            self.history.record(
                "install",
                f"Installation fehlgeschlagen: {job.app_name or Path(job.ipa_path).stem}",
                job.error_detail[:200],
                status="fail",
            )
            if self._dialog:
                self._dialog.reject()
            if self.settings.settings.notify.on_error:
                self.toasts.error(job.error_title or "Installation fehlgeschlagen", job.error_detail[:200])
            self._friendly_error(
                job.error_title or "Installation fehlgeschlagen",
                job.error_detail,
                "\n".join(job.log[-8:]),
            )

    def _friendly_error(self, title: str, message: str, technical: str = "") -> None:
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(message)
        if technical:
            box.setDetailedText(technical[:4000])
        box.setIcon(QMessageBox.Icon.Warning)
        box.addButton("Erneut versuchen", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Schließen", QMessageBox.ButtonRole.RejectRole)
        box.exec()

    # -- quick actions --------------------------------------------------------------------
    def _ask_url(self) -> None:
        dlg = UrlDownloadDialog(self)
        dlg.start.connect(self._start_download)
        dlg.exec()

    def _quick_sign(self) -> None:
        items = self.library.list()
        if not items:
            self.toasts.error("Keine IPA-Datei", "Importiere zuerst eine IPA in die Bibliothek.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "IPA zum Signieren wählen", "", "iOS-App (*.ipa)")
        target = next((i for i in items if i.path == path), items[0] if not path else None)
        if target is None:
            return
        idents = self.installer.signing.all_identities()
        dlg = SignDialog(target, idents, self)
        dlg.sign_now.connect(lambda prov, ident: self._do_standalone_sign(target, prov, ident))
        dlg.exec()

    def _do_standalone_sign(self, ipa: IpaInfo, provider: SigningProvider, identity: SigningIdentity) -> None:
        out = str(Path(ipa.path).with_name(Path(ipa.path).stem + "-signed.ipa"))
        res = self.installer.signing.sign(provider, ipa.path, identity, out)
        if res.ok and res.output_ipa:
            try:
                info = self.library.import_file(res.output_ipa)
                self.refresh_library()
                self.history.record("install", f"Signiert: {info.display_title}", identity.label)
                self.toasts.success("Signiert", info.display_title)
            except Exception as exc:
                self.toasts.error("Import fehlgeschlagen", str(exc)[:200])
        else:
            self.history.record(
                "install",
                f"Signieren fehlgeschlagen: {ipa.display_title}",
                res.message[:200],
                status="fail",
            )
            self.toasts.error("Signieren fehlgeschlagen", res.message[:300])

    def _quick_bundle(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "IPA wählen", "", "iOS-App (*.ipa)")
        if not path:
            items = self.library.list()
            if not items:
                self.toasts.error("Keine IPA-Datei", "Importiere zuerst eine IPA in die Bibliothek.")
                return
            info = items[0]
        else:
            try:
                info = self.library.import_file(path)
                self.refresh_library()
            except Exception as exc:
                self.toasts.error("Import fehlgeschlagen", str(exc)[:200])
                return
        dlg = BundleIdDialog(info.bundle_id, self)
        dlg.apply_now.connect(lambda bid: self._do_repackage(info, bid))
        dlg.exec()

    def _do_repackage(self, info: IpaInfo, bundle_id: str) -> None:
        from app.ipa.repackage import set_bundle_id

        try:
            out = set_bundle_id(info.path, bundle_id)
            new_info = self.library.import_file(out)
            self.refresh_library()
            self.history.record("install", f"Bundle-ID geändert: {new_info.display_title}", bundle_id)
            self.toasts.success("Bundle-ID geändert", bundle_id)
        except Exception as exc:
            msg = exc.user_text() if hasattr(exc, "user_text") else str(exc)
            self.history.record("install", "Bundle-ID fehlgeschlagen", msg[:200], status="fail")
            self.toasts.error("Bundle-ID fehlgeschlagen", msg[:300])

    def _show_profiles(self) -> None:
        s = self.settings.settings
        dirs = [Path(s.signing.provisioning_dir)] if s.signing.provisioning_dir else []
        from app.signing.local_provisioning import default_search_dirs

        dlg = ProfilesDialog(dirs + default_search_dirs(), self)
        dlg.use_folder.connect(self._set_prov_dir)
        dlg.exec()

    def _set_prov_dir(self, folder: str) -> None:
        s = self.settings.settings
        s.signing.provisioning_dir = folder
        self.settings.save()
        os.environ["DENIZ_PROVISIONING_DIR"] = folder
        self.settings_page.load(s)
        self.toasts.success("Profil-Ordner gesetzt", folder)

    # -- companion ----------------------------------------------------------------------------
    def _select_device(self, udid: str) -> None:
        self._selected_udid = udid
        self.companion.set_devices(self.devices.cached, selected=udid)

    def _companion_login(self, email: str, password: str, save_username: bool) -> None:
        email = (email or "").strip().lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            self.companion.set_login_state("Bitte eine gültige Apple-ID-E-Mail eingeben.", False)
            return
        if len(password) < 1:
            self.companion.set_login_state("Bitte das Apple-ID-Passwort eingeben.", False)
            return
        self.session.begin(email, password)
        server, _ = self._current_anisette()
        ok, detail = check_reachable(server)
        if not ok:
            self.session.invalidate()
            self.companion.set_login_state(f"Anisette-Server nicht erreichbar: {detail}", False)
            return
        pwd = self.session.take_password()  # consume + wipe immediately
        _ = pwd
        if save_username:
            self._store_username_hint(email)
        s = self.settings.settings
        s.signing.apple_id_username = email
        self.settings.save()
        self.session.mark_ready(f"Sitzung vorbereitet ({email}).")
        self._update_profile()
        self.history.record("device", f"Apple-Sitzung vorbereitet: {email}", detail)
        self.companion.set_login_state(
            "Sitzung vorbereitet. Hinweis: Die vollständige Apple-Anmeldung (GSA-Protokoll) "
            "folgt per Update — das Passwort wurde nirgendwo gespeichert.",
            True,
        )
        self.toasts.success("Sitzung vorbereitet", email)

    def _companion_logout(self) -> None:
        self.session.invalidate()
        self.companion.set_login_state("", True)
        self.toasts.info("Abgemeldet", "Sitzung wurde verworfen.")

    def _store_username_hint(self, email: str) -> None:
        s = self.settings.settings
        if s.companion.use_keyring:
            try:
                creds.store_secret("apple-id-username", email)
                return
            except Exception as exc:
                log.warning("keychain hint failed: %s", exc)
        s.signing.apple_id_username = email
        self.settings.save()

    def _current_anisette(self) -> tuple[str, bool]:
        s = self.settings.settings
        if s.companion.anisette_custom:
            return s.companion.anisette_server, True
        for host, _label in SERVERS_ANI:
            if host == s.companion.anisette_server:
                return host, False
        return s.companion.anisette_server, s.companion.anisette_custom

    def _anisette_changed(self, server: str, custom: bool) -> None:
        s = self.settings.settings
        try:
            clean = normalize_server(server) if custom else server
        except ValueError as exc:
            self.companion.set_anisette_state(str(exc))
            return
        s.companion.anisette_server = server.strip()
        s.companion.anisette_custom = custom
        self.settings.save()
        ok, detail = check_reachable(clean)
        has = self.anisette.has_state()
        self.companion.set_anisette_state(f"{detail} Lokaler Status: {'vorhanden' if has else 'leer'}.")
        self.history.record("device", f"Anisette-Server: {clean}", detail)

    def _reset_anisette(self) -> None:
        if (
            QMessageBox.question(self, "Zurücksetzen?", "Lokalen Anisette-Status wirklich löschen?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        removed = self.anisette.reset()
        try:
            creds.delete_secret("deniz-anisette-state")
        except Exception:
            pass
        self.companion.set_anisette_state("Status zurückgesetzt." if removed else "Kein Status vorhanden.")
        self.history.record("device", "Anisette-Status zurückgesetzt", status="info")
        self.toasts.success("Anisette zurückgesetzt")

    def _delete_pairing(self) -> None:
        if (
            QMessageBox.question(self, "Löschen?", "Gespeicherte Pairing-Einträge wirklich löschen?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        from app.device.pairing import delete_stored

        n = delete_stored()
        self._selected_udid = None
        self.refresh_devices()
        self.history.record("device", f"Pairing gelöscht ({n} Einträge)", status="info")
        self.toasts.success("Pairing gelöscht", f"{n} Einträge entfernt.")

    def _keyring_toggled(self, dont_use: bool) -> None:
        s = self.settings.settings
        s.companion.use_keyring = not dont_use
        self.settings.save()
        self.toasts.info(
            "Schlüsselbund " + ("deaktiviert" if dont_use else "aktiviert"),
            "Nur der Benutzername-Hinweis ist betroffen — Passwörter werden nie gespeichert.",
        )

    def _open_pairing(self) -> None:
        from app.device.pairing import list_pair_records

        _searched, names = list_pair_records()
        dlg = PairingDialog(names, self)
        dlg.export_requested.connect(self._export_pairing)
        dlg.delete_requested.connect(self._delete_pairing)
        dlg.open_folder.connect(self._open_pairing_folder)
        dlg.exec()

    def _export_pairing(self) -> None:
        from app.device.pairing import export_pairing

        found = self.devices.cached or self.devices.refresh()
        udid = self._selected_udid or (found[0].udid if found else "")
        if not udid:
            self.toasts.error("Kein Gerät", "Verbinde zuerst ein iPhone.")
            return
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Pairing-Datei exportieren",
            f"{udid}.mobiledevicepairing",
            "Pairing (*.mobiledevicepairing);;Alle (*)",
        )
        if not path:
            return
        try:
            out = export_pairing(udid, Path(path))
            self.history.record("device", f"Pairing exportiert: {out.name}", status="info")
            self.toasts.success("Exportiert", out.name)
        except Exception as exc:
            self.toasts.error("Export fehlgeschlagen", str(exc)[:250])

    def _open_pairing_folder(self) -> None:
        from app.device.pairing import pair_records_folder

        folder = pair_records_folder()
        if folder is None:
            self.toasts.info("Pairing", "Kein lokaler Ordner gefunden.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _open_certificates(self) -> None:
        s = self.settings.settings
        dirs = [Path(s.signing.provisioning_dir)] if s.signing.provisioning_dir else []
        from app.signing.local_provisioning import default_search_dirs, list_profiles

        dlg = CertificatesDialog(list_profiles(dirs + default_search_dirs()), portal_locked=True, parent=self)
        dlg.exec()

    def _open_app_ids(self) -> None:
        bids = [i.bundle_id for i in self.library.list()]
        dlg = AppIdsDialog(bids, portal_locked=True, parent=self)
        dlg.exec()

    def _install_with(self, key: str) -> None:
        definition = next((d for d in INSTALLERS if d.key == key), None)
        if definition is None:
            return
        found = self.devices.cached or self.devices.refresh()
        udid = self._selected_udid or (found[0].udid if found else "")
        if not udid:
            self.toasts.error("Kein iPhone gefunden", "Verbinde dein iPhone per USB und entsperre es.")
            self._switch(2)
            return
        if self.settings.settings.iphone.confirm_before_install:
            if (
                QMessageBox.question(self, "Installieren?", f"{definition.title} herunterladen und installieren?")
                != QMessageBox.StandardButton.Yes
            ):
                return
        dlg = CompanionProgressDialog(definition.title, self)
        dlg.show()
        self._companion_worker = CompanionWorker(self.companion_runner, definition, udid)
        self._companion_worker.stepped.connect(dlg.update_step)
        self._companion_worker.finished_job.connect(lambda job: self._companion_done(job, dlg, definition))
        self._companion_worker.start()

    def _companion_done(self, job: InstallationJob, dlg: CompanionProgressDialog, definition: InstallerDef) -> None:
        try:
            Path(job.ipa_path).with_name(Path(job.ipa_path).stem + ".signed.ipa").unlink(missing_ok=True)
        except Exception:
            pass
        if job.step.value == "done":
            try:
                self.library.import_file(job.ipa_path)
                self.refresh_library()
            except Exception:
                pass
            self.history.record("install", f"Installiert: {definition.title}", definition.bundle_id)
            if self.settings.settings.notify.on_success:
                self.toasts.success("Installation abgeschlossen", definition.title)
            dlg.accept()
            self.refresh_apps()
        else:
            self.history.record(
                "install",
                f"Installation fehlgeschlagen: {definition.title}",
                job.error_detail[:200],
                status="fail",
            )
            dlg.reject()
            if self.settings.settings.notify.on_error:
                self.toasts.error(job.error_title or "Installation fehlgeschlagen", job.error_detail[:250])
            self._friendly_error(
                job.error_title or "Installation fehlgeschlagen",
                job.error_detail,
                "\n".join(job.log[-8:]),
            )

    # -- downloads ---------------------------------------------------------------------------
    def _start_download(self, url: str) -> None:
        try:
            item = self.downloads.enqueue(url)
        except ValueError as exc:
            self.library_page.show_error(str(exc))
            return
        self._dl_states[id(item)] = DownloadState.QUEUED
        self.history.record("download", f"Download gestartet: {item.dest.name}", url[:120])
        self.downloads.start(item, on_progress=lambda it: self.refresh_downloads())
        self.refresh_downloads()
        self._switch(4)
        self.library_page.tabs.setCurrentIndex(1)

    def _cancel_download(self, item: DownloadItem) -> None:
        self.downloads.cancel(item)
        self.refresh_downloads()

    def _pause_download(self, item: DownloadItem) -> None:
        if item.state == DownloadState.PAUSED:
            self.downloads.resume(item, on_progress=lambda it: self.refresh_downloads())
        else:
            self.downloads.pause(item)
        self.refresh_downloads()

    # -- settings -------------------------------------------------------------------------------
    def _save_settings(self) -> None:
        s = self.settings.settings
        self.settings_page.collect(s)
        s.validate()
        self.settings.save()
        set_start_with_windows(s.general.start_with_windows)
        if s.downloads.folder:
            self.downloads.download_dir = Path(s.downloads.folder)
            self.downloads.download_dir.mkdir(parents=True, exist_ok=True)
        if s.signing.provisioning_dir:
            os.environ["DENIZ_PROVISIONING_DIR"] = s.signing.provisioning_dir
        if s.signing.apple_id_username:
            try:
                creds.store_secret("apple-id-username", s.signing.apple_id_username)
            except Exception:
                pass
        from PySide6.QtWidgets import QApplication

        from app.ui.design import apply_theme

        apply_theme(QApplication.instance(), s.general.theme)
        self._refresh_theme_icon()
        self._update_profile()
        self.toasts.success("Einstellungen gespeichert")

    def _clear_creds(self) -> None:
        creds.clear_cached_credentials()
        self.toasts.success("Zugangsdaten gelöscht")

    def _clear_logs(self) -> None:
        try:
            for f in self.config.log_dir.glob("*.log"):
                f.write_text("", encoding="utf-8")
        except Exception:
            pass
        self.logs_page.reload()
        self.toasts.success("Logs gelöscht")

    def _clear_cache(self) -> None:
        import shutil

        try:
            shutil.rmtree(self.config.cache_dir, ignore_errors=True)
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self._details_cache = {}
        self.toasts.success("Cache gelöscht")

    def _browse_downloads(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Download-Ordner")
        if d:
            self.settings_page.edit_folder.setText(d)

    def _browse_prov(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Provisioning-Ordner")
        if d:
            self.settings_page.edit_prov.setText(d)

    def maybe_first_launch(self) -> None:
        if not self.settings.settings.first_launch_done:
            wiz = FirstLaunchWizard(self)
            wiz.exec()
            self.settings.settings.first_launch_done = True
            self.settings.save()

    def show_pairing(self) -> None:
        searched, names = list_pair_records()
        if names:
            self.toasts.info("Pairing-Dateien", f"{len(names)} Einträge (Namen only): {', '.join(names[:5])}")
        else:
            self.toasts.info("Pairing-Dateien", "Keine lokalen Pairing-Einträge gefunden.")
        log.info("pairing search dirs: %s found: %s", [str(p) for p in searched], names[:10])

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.settings.settings.general.minimize_to_tray and hasattr(self, "tray"):
            event.ignore()
            self.hide()
            try:
                self.tray.showMessage("Deniz Sideloader", "In den Tray minimiert.")
            except Exception:
                pass
        else:
            event.accept()
