"""Companion data models: session, anisette config, installer definitions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AppleSession:
    """In-memory Apple-ID session preparation.

    Holds the email (persistable as keychain hint) and keeps the password
    ONLY in RAM for the duration of one operation. There is intentionally
    no method to persist the password anywhere.
    """

    email: str = ""
    ready: bool = False
    detail: str = ""
    _password: str = field(default="", repr=False, compare=False)

    def begin(self, email: str, password: str) -> None:
        self.email = email.strip().lower()
        self._password = password
        self.ready = False
        self.detail = ""

    def take_password(self) -> str:
        """Consume the in-memory password once, then wipe it."""
        pwd, self._password = self._password, ""
        return pwd

    def has_password(self) -> bool:
        return bool(self._password)

    def mark_ready(self, detail: str = "") -> None:
        self.ready = True
        self.detail = detail
        self._password = ""

    def invalidate(self) -> None:
        self.email = ""
        self.ready = False
        self.detail = ""
        self._password = ""


@dataclass
class InstallerDef:
    key: str
    title: str
    subtitle: str
    filename: str
    url: str
    bundle_id: str  # expected bundle id for the pairing step
    pairing_file: str = "pairing.mobiledevicepairing"


INSTALLERS: list[InstallerDef] = [
    InstallerDef(
        key="sidestore-stable",
        title="SideStore (Stable)",
        subtitle="Stabile Version",
        filename="SideStore.ipa",
        url="https://github.com/SideStore/SideStore/releases/latest/download/SideStore.ipa",
        bundle_id="com.SideStore.SideStore",
    ),
    InstallerDef(
        key="sidestore-nightly",
        title="SideStore (Nightly)",
        subtitle="Entwicklungsstand",
        filename="SideStore-Nightly.ipa",
        url="https://github.com/SideStore/SideStore/releases/download/nightly/SideStore.ipa",
        bundle_id="com.SideStore.SideStore",
    ),
    InstallerDef(
        key="livecontainer-stable",
        title="LiveContainer + SideStore (Stable)",
        subtitle="Stabile Version",
        filename="LiveContainerSideStore.ipa",
        url="https://github.com/LiveContainer/LiveContainer/releases/latest/download/LiveContainer+SideStore.ipa",
        bundle_id="com.SideStore.SideStore",
    ),
    InstallerDef(
        key="livecontainer-nightly",
        title="LiveContainer + SideStore (Nightly)",
        subtitle="Entwicklungsstand",
        filename="LiveContainerSideStore-Nightly.ipa",
        url="https://github.com/LiveContainer/LiveContainer/releases/download/nightly/LiveContainer+SideStore.ipa",
        bundle_id="com.SideStore.SideStore",
    ),
]
