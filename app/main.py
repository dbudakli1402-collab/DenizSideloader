"""Application entry point: builds services, applies theme, runs Qt loop.

No console window in normal use: shipped via pythonw / windowed PyInstaller build.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from app import __app_name__, __version__
    from app.core.config import DEFAULT_CONFIG, AppConfig
    from app.core.logging import setup_logging
    from app.device.interface import DeviceService
    from app.device.pymobiledevice_provider import default_providers
    from app.downloads.manager import DownloadManager
    from app.installation.service import InstallationService
    from app.ipa.library import IpaLibrary
    from app.signing.apple_developer import AppleDeveloperSigning
    from app.signing.local_provisioning import LocalProvisioning
    from app.signing.models import SigningKind
    from app.signing.service import SigningService
    from app.storage.settings import SettingsStore
    from app.ui.design import apply_theme
    from app.ui.main_window import MainWindow

    config = AppConfig(
        app_data_dir=DEFAULT_CONFIG.app_data_dir,
        cache_dir=DEFAULT_CONFIG.cache_dir,
        log_dir=DEFAULT_CONFIG.log_dir,
        download_dir=DEFAULT_CONFIG.download_dir,
        library_dir=DEFAULT_CONFIG.library_dir,
    )
    config.ensure_dirs()
    store = SettingsStore(config.app_data_dir / "settings.json")
    import logging as _logging

    level = _logging.DEBUG if store.settings.advanced.debug_mode else _logging.INFO
    logger = setup_logging(config.log_dir, level=level)
    logger.info("starting %s v%s", __app_name__, __version__)
    s = store.settings
    if s.downloads.folder:
        config.download_dir = Path(s.downloads.folder)
        config.download_dir.mkdir(parents=True, exist_ok=True)
    if s.signing.provisioning_dir:
        os.environ.setdefault("DENIZ_PROVISIONING_DIR", s.signing.provisioning_dir)

    kind = SigningKind.PAID_DEVELOPER if s.signing.account_type == "paid" else SigningKind.FREE_DEVELOPER
    prov_dirs = [Path(s.signing.provisioning_dir)] if s.signing.provisioning_dir else []

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("DenizSideloader")
    from app.ui.branding import window_icon

    app.setWindowIcon(window_icon())
    apply_theme(app, s.general.theme if s.general.theme in ("dark", "light") else "dark")

    window = MainWindow(
        config=config,
        settings=store,
        devices=DeviceService(providers=default_providers()),
        library=IpaLibrary(config.library_dir),
        downloads=DownloadManager(config.download_dir, max_concurrent=s.downloads.concurrent),
        installer=InstallationService(
            devices=DeviceService(providers=default_providers()),
            signing=SigningService([AppleDeveloperSigning(kind), LocalProvisioning(prov_dirs)]),
        ),
    )
    window.show()
    window.maybe_first_launch()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
