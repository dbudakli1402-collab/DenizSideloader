"""Main window: sidebar + stacked pages, wiring all services."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from app import __app_name__, __version__
from app.core.config import AppConfig
from app.core.logging import get_logger
from app.device.interface import DeviceService
from app.device.models import DeviceInfo
from app.downloads.manager import DownloadItem, DownloadManager
from app.installation.models import InstallationJob
from app.installation.service import InstallationService
from app.ipa.library import IpaLibrary
from app.ipa.models import IpaInfo
from app.security import credentials as creds
from app.storage.autostart import set_start_with_windows
from app.storage.settings import SettingsStore
from app.ui.dialogs.install_dialog import InstallDialog
from app.ui.dialogs.wizard import FirstLaunchWizard
from app.ui.pages.about import AboutPage
from app.ui.pages.device import DevicePage
from app.ui.pages.downloads import DownloadsPage
from app.ui.pages.home import HomePage
from app.ui.pages.installed import InstalledPage
from app.ui.pages.library import LibraryPage
from app.ui.pages.settings import SettingsPage
from app.ui.widgets import friendly_error_dialog

log = get_logger("ui")

NAV = ["Home", "IPA Library", "My iPhone", "Installed Apps", "Downloads", "Settings", "About"]


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
        self._worker: InstallWorker | None = None
        self._dialog: InstallDialog | None = None

        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.resize(1180, 760)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(210)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(14, 18, 14, 18)
        side_layout.setSpacing(6)
        brand = QLabel("\u25c6 Deniz Sideloader")
        brand.setStyleSheet("font-size: 16px; font-weight: 700; padding: 6px 10px;")
        side_layout.addWidget(brand)
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav")
        for name in NAV:
            QListWidgetItem(name, self.nav_list)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._switch)
        # Style nav as buttons via delegate-less stylesheet on items
        self.nav_list.setStyleSheet(
            "QListWidget { background: transparent; border: none; font-size: 14px; }"
            "QListWidget::item { color: #b9bec7; border-radius: 10px; padding: 10px 14px; }"
            "QListWidget::item:hover { background: #1e2129; color: #fff; }"
            "QListWidget::item:selected { background: #2a2f3a; color: #fff; font-weight: 600; }"
        )
        side_layout.addWidget(self.nav_list, 1)
        root.addWidget(side)

        # Pages
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.home = HomePage()
        self.lib_page = LibraryPage()
        self.dev_page = DevicePage()
        self.installed_page = InstalledPage()
        self.dl_page = DownloadsPage()
        self.settings_page = SettingsPage()
        self.about_page = AboutPage()
        for p in (
            self.home,
            self.lib_page,
            self.dev_page,
            self.installed_page,
            self.dl_page,
            self.settings_page,
            self.about_page,
        ):
            self.stack.addWidget(p)

        self.statusBar().showMessage("Ready")
        self._wire()
        self._tray()
        self.refresh_all()

    # -- wiring ----------------------------------------------------------
    def _wire(self) -> None:
        self.home.choose_ipa.connect(self.choose_and_install)
        self.home.download_ipa.connect(lambda: self._switch(4))
        self.home.open_recent.connect(self._install_path)
        self.lib_page.import_requested.connect(self.import_ipa)
        self.lib_page.install_ipa.connect(lambda info: self._install_path(info.path))
        self.lib_page.remove_ipa.connect(self._remove_ipa)
        self.lib_page.files_dropped.connect(self._import_many)
        self.dev_page.btn_refresh.clicked.connect(lambda: self.refresh_devices())
        self.dl_page.start_download.connect(self._start_download)
        self.dl_page.cancel_download.connect(self._cancel_download)
        self.dl_page.pause_download.connect(self._pause_download)
        self.settings_page.save_requested.connect(self._save_settings)
        self.settings_page.clear_credentials.connect(self._clear_creds)
        self.settings_page.clear_logs.connect(self._clear_logs)
        self.settings_page.browse_downloads.connect(self._browse_downloads)
        self.settings_page.browse_provisioning.connect(self._browse_prov)

    def _tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self)
        menu = QMenu()
        show_act = QAction("Show", self)
        show_act.triggered.connect(self.showNormal)
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(self.close)
        menu.addAction(show_act)
        menu.addAction(quit_act)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def _switch(self, row: int) -> None:
        self.stack.setCurrentIndex(row)
        if row == 2:
            self.refresh_devices()
        if row == 3:
            self.refresh_installed()

    # -- data refresh ----------------------------------------------------
    def refresh_all(self) -> None:
        self.refresh_devices()
        self.refresh_library()
        self.refresh_downloads()
        self.settings_page.load(self.settings.settings)
        self.home.set_recent(self.settings.settings.recent_ipas)

    def refresh_devices(self) -> None:
        found = self.devices.refresh()
        if found:
            d = found[0]
            self.home.set_device_status(True, f"{d.display_name} \u2022 iOS {d.ios_version} \u2022 Connected via USB")
        else:
            self.home.set_device_status(False, "Connect your iPhone via USB and unlock it.")
        self.dev_page.set_devices(found, self.devices.backend_help())
        self.statusBar().showMessage(f"{len(found)} device(s) connected" if found else "No iPhone connected")

    def refresh_library(self) -> None:
        self.lib_page.set_items(self.library.list())

    def refresh_downloads(self) -> None:
        self.dl_page.set_items(self.downloads.items)

    def refresh_installed(self) -> None:
        found = self.devices.cached or self.devices.refresh()
        apps: list[dict[str, str]] = []
        note = ""
        if found:
            for prov in self.devices.providers:
                list_apps = getattr(prov, "list_installed_apps", None)
                if callable(list_apps):
                    try:
                        apps = list_apps(found[0].udid)
                        if apps:
                            break
                    except Exception:
                        continue
            if not apps:
                note = "Backend reachable but app listing unsupported/unavailable right now."
        self.installed_page.set_apps(apps, note)

    # -- IPA flows -------------------------------------------------------
    def choose_and_install(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose IPA", "", "iOS App (*.ipa)")
        if path:
            self._install_path(path)

    def import_ipa(self) -> None:
        path = self.lib_page.pick_file()
        if path:
            self._import_many([path])

    def _import_many(self, paths: list[str]) -> None:
        ok, fail = 0, 0
        for p in paths:
            try:
                self.library.import_file(p)
                ok += 1
            except Exception as exc:
                fail += 1
                log.warning("import failed %s: %s", p, exc)
        self.refresh_library()
        self.statusBar().showMessage(f"Imported {ok} IPA(s)" + (f", {fail} failed" if fail else ""))

    def _remove_ipa(self, info: IpaInfo) -> None:
        if (
            QMessageBox.question(self, "Delete IPA", f"Delete {info.display_title} from library?")
            == QMessageBox.StandardButton.Yes
        ):
            self.library.remove(info)
            self.refresh_library()

    def _install_path(self, path: str) -> None:
        s = self.settings.settings
        # Auto-import into library for consistency
        try:
            if Path(path).is_file() and Path(path).suffix.lower() == ".ipa":
                in_lib = any(i.path == path for i in self.library.list())
                if not in_lib:
                    try:
                        info = self.library.import_file(path)
                        path = info.path
                        self.refresh_library()
                    except Exception:
                        pass
        except Exception:
            pass
        s.recent_ipas = [p for p in s.recent_ipas if p != path]
        s.recent_ipas.insert(0, path)
        s.recent_ipas = s.recent_ipas[:8]
        self.settings.save()
        self.home.set_recent(s.recent_ipas)

        found = self.devices.cached or self.devices.refresh()
        if not found:
            friendly_error_dialog(
                self,
                "No iPhone found",
                "We couldn't find your iPhone.\n\nPossible causes:\n"
                "\u2022 iPhone is locked\n"
                "\u2022 The computer has not been trusted\n"
                "\u2022 Apple device services are unavailable",
                "",
            )
            self._switch(2)
            return
        target: DeviceInfo = found[0]
        if s.iphone.confirm_before_install:
            if (
                QMessageBox.question(self, "Install?", f"Install {Path(path).name} on {target.display_name}?")
                != QMessageBox.StandardButton.Yes
            ):
                return
        job = InstallationJob(ipa_path=path, udid=target.udid)
        self._dialog = InstallDialog(job, self)
        self._dialog.show()
        self._worker = InstallWorker(self.installer, job)
        self._worker.stepped.connect(lambda j: self._dialog.update_job(j) if self._dialog else None)
        self._worker.finished.connect(lambda: self._install_finished(job))
        self._worker.start()

    def _install_finished(self, job: InstallationJob) -> None:
        if self._dialog:
            self._dialog.update_job(job)
        if job.step.value == "done":
            QMessageBox.information(
                self,
                "Installation complete",
                f"{job.app_name} was successfully installed on your iPhone.",
            )
            if self._dialog:
                self._dialog.accept()
        elif job.step.value == "failed":
            if self._dialog:
                self._dialog.reject()
            friendly_error_dialog(
                self,
                job.error_title or "Installation failed",
                job.error_detail,
                "\n".join(job.log[-8:]),
            )

    # -- downloads -------------------------------------------------------
    def _start_download(self, url: str) -> None:
        try:
            item = self.downloads.enqueue(url)
        except ValueError as exc:
            self.dl_page.show_error(str(exc))
            return
        self.dl_page.show_error("")
        self.refresh_downloads()

        def _cb(it: DownloadItem) -> None:
            # thread-safe-ish refresh via queued call
            self.refresh_downloads()
            if it.state.value == "done" and self.settings.settings.downloads.auto_import:
                try:
                    self.library.import_file(it.dest)
                    self.refresh_library()
                except Exception as exc:
                    log.warning("auto-import failed: %s", exc)

        # Wrap callback to hop to GUI thread
        from PySide6.QtCore import QMetaObject

        def _safe_cb(it: DownloadItem) -> None:
            QMetaObject.invokeMethod(self, "_on_dl_progress", Qt.ConnectionType.QueuedConnection)

        _ = _safe_cb
        self.downloads.start(item, on_progress=lambda it: self._on_dl_item(it))
        self.statusBar().showMessage(f"Downloading {item.dest.name}\u2026")

    def _on_dl_item(self, item: DownloadItem) -> None:
        self.refresh_downloads()
        if item.state.value == "done":
            if self.settings.settings.downloads.auto_import:
                try:
                    self.library.import_file(item.dest)
                    self.refresh_library()
                except Exception as exc:
                    log.warning("auto-import failed: %s", exc)
            self.statusBar().showMessage(f"Downloaded {item.dest.name} \u2022 SHA-256 verified")

    def _on_dl_progress(self) -> None:
        self.refresh_downloads()

    def _cancel_download(self, item: DownloadItem) -> None:
        self.downloads.cancel(item)
        self.refresh_downloads()

    def _pause_download(self, item: DownloadItem) -> None:
        from app.downloads.manager import DownloadState

        if item.state == DownloadState.PAUSED:
            self.downloads.resume(item, on_progress=lambda it: self._on_dl_item(it))
        else:
            self.downloads.pause(item)
        self.refresh_downloads()

    # -- settings --------------------------------------------------------
    def _save_settings(self) -> None:
        s = self.settings.settings
        self.settings_page.collect(s)
        s.validate()
        self.settings.save()
        set_start_with_windows(s.general.start_with_windows)
        # Apply download dir live
        if s.downloads.folder:
            self.downloads.download_dir = Path(s.downloads.folder)
            self.downloads.download_dir.mkdir(parents=True, exist_ok=True)
        if s.signing.provisioning_dir:
            import os

            os.environ["DENIZ_PROVISIONING_DIR"] = s.signing.provisioning_dir
        if s.signing.apple_id_username:
            try:
                creds.store_secret("apple-id-username", s.signing.apple_id_username)
            except Exception:
                pass
        self.statusBar().showMessage("Settings saved")

    def _clear_creds(self) -> None:
        creds.clear_cached_credentials()
        QMessageBox.information(self, "Security", "Cached credentials cleared.")

    def _clear_logs(self) -> None:
        try:
            for f in self.config.log_dir.glob("*.log"):
                f.write_text("", encoding="utf-8")
        except Exception:
            pass
        QMessageBox.information(self, "Logs", "Logs cleared.")

    def _browse_downloads(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Download folder")
        if d:
            self.settings_page.edit_folder.setText(d)

    def _browse_prov(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Provisioning folder")
        if d:
            self.settings_page.edit_prov.setText(d)

    def maybe_first_launch(self) -> None:
        if not self.settings.settings.first_launch_done:
            wiz = FirstLaunchWizard(self)
            wiz.exec()
            self.settings.settings.first_launch_done = True
            self.settings.save()

    # -- misc ------------------------------------------------------------
    def closeEvent(self, event) -> None:  # noqa: N802
        if self.settings.settings.general.minimize_to_tray and hasattr(self, "tray"):
            event.ignore()
            self.hide()
            self.tray.showMessage("Deniz Sideloader", "Minimized to tray.")
        else:
            event.accept()
