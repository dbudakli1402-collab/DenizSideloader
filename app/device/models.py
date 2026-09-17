"""Device data models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ConnectionType(str, Enum):
    USB = "usb"
    WIFI = "wifi"
    UNKNOWN = "unknown"


class TrustState(str, Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    UNKNOWN = "unknown"


@dataclass
class DeviceInfo:
    udid: str
    name: str
    ios_version: str
    model: str = ""
    connection: ConnectionType = ConnectionType.USB
    trusted: TrustState = TrustState.UNKNOWN

    @property
    def short_udid(self) -> str:
        if len(self.udid) <= 12:
            return self.udid
        return f"{self.udid[:6]}\u2026{self.udid[-4:]}"

    @property
    def display_name(self) -> str:
        return self.name or "iPhone"

    def status_hint(self) -> str:
        if self.trusted == TrustState.UNTRUSTED:
            return "Please unlock your iPhone and select \u201cTrust\u201d when prompted."
        if self.trusted == TrustState.UNKNOWN:
            return "Connect your iPhone via USB and unlock it."
        return f"{self.display_name} \u2022 iOS {self.ios_version} \u2022 Connected via USB"
