"""JSON settings store with validation + defaults. No secrets stored here."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class GeneralSettings:
    start_with_windows: bool = False
    minimize_to_tray: bool = True
    theme: str = "dark"  # dark | light | system
    language: str = "de"  # de | en
    animations: bool = True


@dataclass
class IphoneSettings:
    auto_detect: bool = True
    confirm_before_install: bool = True
    check_connection: bool = True


@dataclass
class DownloadSettings:
    folder: str = ""
    concurrent: int = 3
    auto_import: bool = True


@dataclass
class SecuritySettings:
    credential_storage: str = "os-keychain"  # os-keychain only supported value
    store_usernames_only: bool = True


@dataclass
class SigningSettings:
    account_type: str = "free"  # free | paid
    provisioning_dir: str = ""
    apple_id_username: str = ""  # username hint only, never password


@dataclass
class InstallSettings:
    keep_ipa: bool = True
    auto_update_check: bool = False


@dataclass
class NotifySettings:
    on_success: bool = True
    on_error: bool = True
    on_download: bool = True


@dataclass
class AdvancedSettings:
    debug_mode: bool = False


@dataclass
class AppSettings:
    general: GeneralSettings = field(default_factory=GeneralSettings)
    iphone: IphoneSettings = field(default_factory=IphoneSettings)
    downloads: DownloadSettings = field(default_factory=DownloadSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    signing: SigningSettings = field(default_factory=SigningSettings)
    install: InstallSettings = field(default_factory=InstallSettings)
    notify: NotifySettings = field(default_factory=NotifySettings)
    advanced: AdvancedSettings = field(default_factory=AdvancedSettings)
    first_launch_done: bool = False
    recent_ipas: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.general.theme not in ("dark", "light", "system"):
            self.general.theme = "dark"
        if self.general.language not in ("en", "de"):
            self.general.language = "de"
        self.downloads.concurrent = max(1, min(8, int(self.downloads.concurrent or 3)))
        if self.signing.account_type not in ("free", "paid"):
            self.signing.account_type = "free"
        # Never allow password-like keys
        for banned in ("password", "passwd", "token", "secret"):
            if banned in asdict(self).keys():
                raise ValueError("Secrets must never be stored in settings.")


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.settings = AppSettings()
        self.load()

    def load(self) -> AppSettings:
        if self.path.is_file():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self.settings = self._from_dict(raw)
            except Exception:
                self.settings = AppSettings()
        self.settings.validate()
        return self.settings

    def save(self) -> None:
        self.settings.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self.settings), indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def _from_dict(self, raw: dict) -> AppSettings:
        s = AppSettings()
        try:
            g = raw.get("general", {})
            s.general = GeneralSettings(**{k: g[k] for k in GeneralSettings.__dataclass_fields__ if k in g})
            ip = raw.get("iphone", {})
            s.iphone = IphoneSettings(**{k: ip[k] for k in IphoneSettings.__dataclass_fields__ if k in ip})
            dl = raw.get("downloads", {})
            s.downloads = DownloadSettings(**{k: dl[k] for k in DownloadSettings.__dataclass_fields__ if k in dl})
            sec = raw.get("security", {})
            s.security = SecuritySettings(**{k: sec[k] for k in SecuritySettings.__dataclass_fields__ if k in sec})
            sg = raw.get("signing", {})
            s.signing = SigningSettings(**{k: sg[k] for k in SigningSettings.__dataclass_fields__ if k in sg})
            ins = raw.get("install", {})
            s.install = InstallSettings(**{k: ins[k] for k in InstallSettings.__dataclass_fields__ if k in ins})
            nt = raw.get("notify", {})
            s.notify = NotifySettings(**{k: nt[k] for k in NotifySettings.__dataclass_fields__ if k in nt})
            ad = raw.get("advanced", {})
            s.advanced = AdvancedSettings(**{k: ad[k] for k in AdvancedSettings.__dataclass_fields__ if k in ad})
            s.first_launch_done = bool(raw.get("first_launch_done", False))
            rec = raw.get("recent_ipas", [])
            s.recent_ipas = [str(x) for x in rec if isinstance(x, str)][:16]
        except Exception:
            pass
        # Defensive: drop any secret-ish keys if hand-edited
        return s
