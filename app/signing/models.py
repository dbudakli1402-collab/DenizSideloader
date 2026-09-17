"""Signing data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class SigningKind(str, Enum):
    FREE_DEVELOPER = "free-developer"
    PAID_DEVELOPER = "paid-developer"
    LOCAL_PROVISIONING = "local-provisioning"
    UNSUPPORTED = "unsupported"


@dataclass
class SigningIdentity:
    kind: SigningKind
    label: str
    team_id: str = ""
    expires: date | None = None
    details: str = ""

    @property
    def expiry_text(self) -> str:
        if not self.expires:
            return "expiry unknown"
        delta = (self.expires - date.today()).days
        if delta < 0:
            return f"expired on {self.expires.isoformat()}"
        if delta == 0:
            return "expires today"
        return f"expires in {delta} days ({self.expires.isoformat()})"


@dataclass
class SigningResult:
    ok: bool
    output_ipa: str = ""
    message: str = ""
    technical: str = ""
