"""Application configuration: paths, constants, version."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

APP_NAME = "Deniz Sideloader"
APP_ID = "org.denizsideloader.app"
APP_VERSION = "0.1.0"
ORG_NAME = "DenizSideloader"

# Apple limits (documented, see docs/signing.md)
FREE_DEV_CERT_EXPIRY_DAYS = 7
PAID_DEV_CERT_EXPIRY_DAYS = 365
FREE_DEV_MAX_APPS = 3  # commonly cited limit for free provisioning (may vary)
FREE_DEV_MAX_DEVICES = 100


def _app_data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "DenizSideloader"
    # Fallback for dev on other OSes (CI runs Windows, but keep portable)
    xdg = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(xdg) / "DenizSideloader"


def _cache_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "DenizSideloader" / "Cache"
    return _app_data_dir() / "cache"


APP_DATA_DIR: Path = _app_data_dir()
CACHE_DIR: Path = _cache_dir()
LOG_DIR: Path = APP_DATA_DIR / "logs"
DEFAULT_DOWNLOAD_DIR: Path = Path.home() / "Downloads" / "DenizSideloader"
DEFAULT_LIBRARY_DIR: Path = APP_DATA_DIR / "library"


@dataclass
class AppConfig:
    """Resolved runtime directories. Created on demand."""

    app_data_dir: Path = field(default_factory=lambda: APP_DATA_DIR)
    cache_dir: Path = field(default_factory=lambda: CACHE_DIR)
    log_dir: Path = field(default_factory=lambda: LOG_DIR)
    download_dir: Path = field(default_factory=lambda: DEFAULT_DOWNLOAD_DIR)
    library_dir: Path = field(default_factory=lambda: DEFAULT_LIBRARY_DIR)

    def ensure_dirs(self) -> None:
        for p in (
            self.app_data_dir,
            self.cache_dir,
            self.log_dir,
            self.download_dir,
            self.library_dir,
        ):
            p.mkdir(parents=True, exist_ok=True)


DEFAULT_CONFIG = AppConfig()
