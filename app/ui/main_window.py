"""App shell v2: frameless window, sidebar, topbar, toasts, history wiring."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
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
from app.core.config import AppConfig
from app.core.logging import get_logger
from app.device.interface import DeviceService
from app.downloads.manager import DownloadItem, DownloadManager, DownloadState
from app.installation.models import InstallationJob
from app.installation.service import InstallationService
from app.ipa.library import CATEGORIES, IpaLibrary
from app.ipa.models import IpaInfo
from app.security import credentials as creds
from app.storage.autostart import set_start_with_windows
from app.storage.history import HistoryStore
from app.storage.settings import SettingsStore
from app.ui import design as D
from app.ui.dialogs.app_details import AppDetailsDialog
from app.ui.dialogs.install_dialog import InstallDialog
from app.ui.dialogs.search_dialog import SearchDialog
from app.ui.dialogs.wizard import FirstLaunchWizard
from app.ui.icons import icon as make_icon
from app.ui.pages.apps import AppsPage
from app.ui.pages.catalog import CatalogPage
from app.ui.pages.devices import DevicesPage
from app.ui.pages.downloads import DownloadsPage
from app.ui.pages.files import FilesPage
from app.ui.pages.history import HistoryPage
from app.ui.pages.home import HomePage
from app.ui.pages.settings import SettingsPage
from app.ui.widgets.toasts import ToastManager

log = get_logger("ui")

NAV = [
    ("Home", "home"),
    ("Apps", "apps"),
    ("IPA-Dateien", "file"),
    ("Geräte", "phone"),
    ("App-Bibliothek", "book"),
    ("Downloads", "download"),
    ("Verlauf", "history"),
    ("Einstellungen", "gear"),
]

CAT_ICONS = {
    "Alle": "apps",
    "Spiele": "play",
    "Social": "bell",
    "Tools": "gear",
    "Entertainment": "play",
    "Produktivität": "bolt",
    "Bildung": "book",
}


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
        self._known_devices: set[str] = set()
        self._dl_states: dict[int, DownloadState] = {}
        self._details_cache: dict[str, dict] = {}
        self._installed_cache: list[dict] = []

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
        self.statusBar().showMessage("Bereit")
        wrap = QWidget()
        wrap.setLayout(main_col)
        root.addWidget(wrap, 1)

        self.home = HomePage()
        self.apps = AppsPage()
        self.files = FilesPage()
        self.devices_page = DevicesPage()
        self.catalog = CatalogPage()
        self.dl_page = DownloadsPage()
        self.history_page = HistoryPage()
        self.settings_page = SettingsPage()
        self._pages = [
            self.home,
            self.apps,
            self.files,
            self.devices_page,
            self.catalog,
            self.dl_page,
            self.history_page,
            self.settings_page,
        ]
        for p in self._pages:
            self.stack.addWidget(p)

        self.toasts = ToastManager(central)
        self._wire()
        self._shortcuts()
        self._tray()
        self.refresh_all(reason="start")

    # -- shell construction ------------------------------------------------
    def _build_sidebar(self, root: QHBoxLayout) -> None:
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(232)
        self.sidebar = side
        lay = QVBoxLayout(side)
        lay.setContentsMargins(14, 16, 14, 14)
        lay.setSpacing(8)

        brand_row = QHBoxLayout()
        bolt = QLabel()
        bolt.setPixmap(make_icon("bolt", 24, D.CYAN).pixmap(30, 30))
        bcol = QVBoxLayout()
        bcol.setSpacing(0)
        b = QLabel("Deniz Sideloader")
        b.setObjectName("brand")
        v = QLabel(f"Version {__version__}")
        v.setObjectName("brandSub")
        bcol.addWidget(b)
        bcol.addWidget(v)
        brand_row.addWidget(bolt)
        brand_row.addLayout(bcol, 1)
        self.btn_collapse = QPushButton()
        self.btn_collapse.setObjectName("iconbtn")
        self.btn_collapse.setIcon(make_icon("sidebar", 18))
        self.btn_collapse.setToolTip("Sidebar ein-/ausklappen")
        self.btn_collapse.clicked.connect(self._toggle_sidebar)
        brand_row.addWidget(self.btn_collapse)
        lay.addLayout(brand_row)

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        for name, glyph in NAV:
            item = QListWidgetItem(make_icon(glyph, 18), name)
            item.setData(32, glyph)
            self.nav.addItem(item)
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(self._switch)
        self.nav.setMouseTracking(True)
        lay.addWidget(self.nav)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {D.BORDER_SOFT};")
        lay.addWidget(sep)
        cat_h = QLabel("KATEGORIEN")
        cat_h.setObjectName("section")
        lay.addWidget(cat_h)
        self.cats = QListWidget()
        self.cats.setObjectName("nav")
        self.cat_items: list[QListWidgetItem] = []
        for c in CATEGORIES:
            item = QListWidgetItem(make_icon(CAT_ICONS.get(c, "apps"), 17), c)
            self.cats.addItem(item)
            self.cat_items.append(item)
        self.cats.setCurrentRow(0)
        self.cats.itemClicked.connect(self._pick_category)
        self.cats.setMaximumHeight(240)
        lay.addWidget(self.cats)
        lay.addStretch(1)

        # device mini card
        self.mini, mini_lay = D.card(obj="card2")
        mini_lay.setContentsMargins(12, 10, 12, 10)
        self.mini_name = QLabel("Kein iPhone")
        self.mini_name.setStyleSheet("font-size: 13px; font-weight: 700;")
        self.mini_sub = QLabel("Nicht verbunden")
        self.mini_sub.setObjectName("muted")
        mini_lay.addWidget(self.mini_name)
        mini_lay.addWidget(self.mini_sub)
        self.mini.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mini.installEventFilter(self)
        lay.addWidget(self.mini)
        root.addWidget(side)

    def _build_topbar(self, col: QVBoxLayout) -> None:
        bar = QWidget()
        bar.setObjectName("topbar")
        bar.setFixedHeight(60)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 10, 16, 10)
        lay.setSpacing(10)
        self.crumb = QLabel("Home")
        self.crumb.setObjectName("cardTitle")
        lay.addWidget(self.crumb)
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
        b_set.clicked.connect(lambda: self._switch(7))
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
        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)

    # -- wiring ------------------------------------------------------------
    def _wire(self) -> None:
        self.home.choose_ipa.connect(self.choose_and_install)
        self.home.files_dropped.connect(self._import_many)
        self.home.goto.connect(self._switch)
        self.apps.install_ipa.connect(lambda info: self._install_path(info.path))
        self.apps.import_requested.connect(self.import_ipa)
        self.apps.open_details.connect(self._show_details)
        self.files.install_ipa.connect(lambda info: self._install_path(info.path))
        self.files.import_requested.connect(self.import_ipa)
        self.files.files_dropped.connect(self._import_many)
        self.files.open_details.connect(self._show_details)
        self.files.set_category.connect(self._set_category)
        self.files.rename_requested.connect(self._rename_ipa)
        self.files.reveal_requested.connect(self._reveal_ipa)
        self.files.remove_requested.connect(self._remove_ipa)
        self.catalog.install_ipa.connect(lambda info: self._install_path(info.path))
        self.catalog.open_details.connect(self._show_details)
        self.catalog.category_selected.connect(self._pick_category_name)
        self.devices_page.refresh_requested.connect(lambda: self.refresh_devices(True))
        self.devices_page.show_apps.connect(lambda: self._switch(1))
        self.dl_page.start_download.connect(self._start_download)
        self.dl_page.cancel_download.connect(self._cancel_download)
        self.dl_page.pause_download.connect(self._pause_download)
        self.settings_page.save_requested.connect(self._save_settings)
        self.settings_page.clear_credentials.connect(self._clear_creds)
        self.settings_page.clear_logs.connect(self._clear_logs)
        self.settings_page.clear_cache.connect(self._clear_cache)
        self.settings_page.browse_downloads.connect(self._browse_downloads)
        self.settings_page.browse_provisioning.connect(self._browse_prov)
        self.settings_page.open_github.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/dbudakli1402-collab/DenizSideloader"))
        )

    def _shortcuts(self) -> None:
        sc = QShortcut(QKeySequence("Ctrl+K"), self)
        sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc.activated.connect(self._open_search)
        for i in range(8):
            s = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            s.setContext(Qt.ShortcutContext.ApplicationShortcut)
            s.activated.connect(lambda _=False, n=i: self._switch(n))

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

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if watched is self.mini and event.type() == QEvent.Type.MouseButtonPress:
            self._switch(3)
            return True
        return super().eventFilter(watched, event)

    # -- navigation --------------------------------------------------------
    def _switch(self, row: int) -> None:
        self.nav.blockSignals(True)
        self.nav.setCurrentRow(row)
        self.nav.blockSignals(False)
        self.crumb.setText(NAV[row][0])
        if self.settings.settings.general.animations:
            self._fade_to(row)
        else:
            self.stack.setCurrentIndex(row)
        if row in (0, 3):
            self.refresh_devices()
        if row == 1:
            self.refresh_apps()
        if row == 6:
            self.history_page.set_events(self.history.list(self._history_filter))
        if row == 4:
            self.catalog.set_items(self.library.list())

    def _fade_to(self, row: int) -> None:
        self.stack.setCurrentIndex(row)
        eff = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(160)
        anim.setStartValue(0.35)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        anim.finished.connect(lambda: self.stack.setGraphicsEffect(None))  # type: ignore[arg-type]

    def _toggle_sidebar(self) -> None:
        narrow = self.sidebar.width() > 120
        self._anim_width(self.sidebar, 64 if narrow else 232)

    def _anim_width(self, widget: QWidget, target: int) -> None:
        anim = QPropertyAnimation(widget, b"minimumWidth", self)
        anim.setDuration(200)
        anim.setStartValue(widget.width())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.start()
        anim2 = QPropertyAnimation(widget, b"maximumWidth", self)
        anim2.setDuration(200)
        anim2.setStartValue(widget.width())
        anim2.setEndValue(target)
        anim2.start()

    def _pick_category(self, item: QListWidgetItem) -> None:
        self._pick_category_name(item.text())

    def _pick_category_name(self, name: str) -> None:
        for i, it in enumerate(self.cat_items):
            if it.text() == name:
                self.cats.setCurrentRow(i)
                break
        self.catalog.set_category(name)
        self._switch(4)

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

    # frameless dragging
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

    # -- search ------------------------------------------------------------
    def _open_search(self) -> None:
        dlg = SearchDialog(self)
        dlg.set_data(self.library.list(), self.devices.cached, self._installed_cache)
        dlg.picked_ipa.connect(lambda info: self._show_details({"ipa": info}))
        dlg.picked_app.connect(self._show_details)
        dlg.picked_device.connect(lambda _d: self._switch(3))
        dlg.exec()

    # -- data refresh ------------------------------------------------------
    def refresh_all(self, reason: str = "") -> None:
        self.refresh_devices()
        self.refresh_library()
        self.refresh_downloads()
        self.refresh_apps()
        self.settings_page.load(self.settings.settings)
        self.history_page.set_events(self.history.list("all"))
        self.home.set_activity(self.history.list("all"))
        _ = reason

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
        details: dict = {}
        if dev is not None:
            details = self._device_details(dev.udid)
        self.home.set_device(dev, details.get(dev.udid, {}) if dev else {})
        self.home.set_status_chip(dev is not None)
        self.home.set_activity(self.history.list("all"))
        self.devices_page.set_devices(found, details, self.devices.backend_help() if not found else "")
        if dev is not None:
            self.mini_name.setText(dev.display_name)
            self.mini_sub.setText(f"iOS {dev.ios_version} · Verbunden")
        else:
            self.mini_name.setText("Kein iPhone")
            self.mini_sub.setText("Nicht verbunden")
        self._set_conn(dev is not None)
        self._update_badges()
        if manual:
            self.statusBar().showMessage(f"{len(found)} Gerät(e) verbunden" if found else "Kein iPhone verbunden")
            if self.stack.currentIndex() == 6:
                self.history_page.set_events(self.history.list(self._history_filter))

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
        parent = self.conn.parent()
        lay = parent.layout() if parent is not None else None
        if lay is not None:
            old = self.conn
            idx = lay.indexOf(old)
            lay.removeWidget(old)
            old.deleteLater()
            self.conn = D.chip("Verbunden" if connected else "Getrennt", "green" if connected else "gray")
            lay.insertWidget(idx if idx >= 0 else lay.count(), self.conn)

    def refresh_library(self) -> None:
        items = self.library.list()
        self.files.set_items(items)
        self.catalog.set_items(items)
        counts = self.library.counts_by_category()
        for i, c in enumerate(CATEGORIES):
            self.cat_items[i].setText(f"{c}  ·  {counts.get(c, 0)}")
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
                elif it.state == DownloadState.CANCELLED and prev not in (None,):
                    self.history.record("download", f"Download abgebrochen: {it.dest.name}", status="info")
            self._dl_states[id(it)] = it.state
        self.dl_page.set_items(items)
        self._update_badges()

    def _update_badges(self) -> None:
        lib_n = len(self.library.list())
        dev_n = len(self.devices.cached)
        active_dl = sum(1 for i in self.downloads.items if i.state in (DownloadState.ACTIVE, DownloadState.QUEUED))
        counts = {
            "Apps": len(self._installed_cache),
            "IPA-Dateien": lib_n,
            "Geräte": dev_n,
            "Downloads": active_dl,
            "App-Bibliothek": lib_n,
        }
        for i in range(self.nav.count()):
            item = self.nav.item(i)
            name = NAV[i][0]
            glyph = item.data(32)
            n = counts.get(name, 0)
            item.setText(f"{name}   ·   {n}" if n else name)
            item.setIcon(make_icon(glyph, 18))

    @property
    def _history_filter(self) -> str:
        from app.ui.pages.history import KIND_MAP

        return KIND_MAP.get(self.history_page.filter.currentText(), "all")

    # -- IPA flows ---------------------------------------------------------
    def choose_and_install(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "IPA-Datei auswählen", "", "iOS-App (*.ipa)")
        if path:
            self._install_path(path)

    def import_ipa(self) -> None:
        path = self.files.pick_file()
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
        self.toasts.success(f"{ok} IPA(s) importiert") if ok else None
        if fail:
            self.toasts.error("Import fehlgeschlagen", f"{fail} Datei(en) ungültig.")
        self.statusBar().showMessage(f"{ok} importiert" + (f", {fail} fehlerhaft" if fail else ""))

    def _set_category(self, info: object, cat: str) -> None:
        assert isinstance(info, IpaInfo)
        self.library.set_category(info, cat)
        self.refresh_library()

    def _rename_ipa(self, info: IpaInfo) -> None:
        name = self.files.ask_name(info.file_name)
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
            self._switch(3)
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
        # signed work copy always cleaned
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
        self.home.set_activity(self.history.list("all"))
        if self.stack.currentIndex() == 6:
            self.history_page.set_events(self.history.list(self._history_filter))

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

    # -- downloads ---------------------------------------------------------
    def _start_download(self, url: str) -> None:
        try:
            item = self.downloads.enqueue(url)
        except ValueError as exc:
            self.dl_page.show_error(str(exc))
            return
        self.dl_page.show_error("")
        self._dl_states[id(item)] = DownloadState.QUEUED
        self.history.record("download", f"Download gestartet: {item.dest.name}", url[:120])
        self.downloads.start(item, on_progress=lambda it: self.refresh_downloads())
        self.refresh_downloads()
        self.statusBar().showMessage(f"Lade {item.dest.name} …")

    def _cancel_download(self, item: DownloadItem) -> None:
        self.downloads.cancel(item)
        self.refresh_downloads()

    def _pause_download(self, item: DownloadItem) -> None:
        if item.state == DownloadState.PAUSED:
            self.downloads.resume(item, on_progress=lambda it: self.refresh_downloads())
        else:
            self.downloads.pause(item)
        self.refresh_downloads()

    # -- settings ----------------------------------------------------------
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
        self.toasts.success("Einstellungen gespeichert")
        self.statusBar().showMessage("Einstellungen gespeichert")

    def _clear_creds(self) -> None:
        creds.clear_cached_credentials()
        self.toasts.success("Zugangsdaten gelöscht")

    def _clear_logs(self) -> None:
        try:
            for f in self.config.log_dir.glob("*.log"):
                f.write_text("", encoding="utf-8")
        except Exception:
            pass
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

    # -- misc --------------------------------------------------------------
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
