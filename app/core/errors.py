"""Typed application errors with user-friendly messages."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AppError(Exception):
    """Base error carrying a user message, causes and optional technical detail."""

    title: str
    message: str
    causes: list[str] = field(default_factory=list)
    technical: str = ""
    retryable: bool = True

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.title}: {self.message}"

    def user_text(self) -> str:
        lines = [self.message]
        if self.causes:
            lines.append("")
            lines.append("Possible causes:")
            lines.extend(f"\u2022 {c}" for c in self.causes)
        return "\n".join(lines)


class DeviceError(AppError):
    pass


class DeviceNotFoundError(DeviceError):
    def __init__(self, technical: str = "") -> None:
        super().__init__(
            title="No iPhone found",
            message="We couldn't find your iPhone.",
            causes=[
                "iPhone is locked",
                "The computer has not been trusted (tap \u201cTrust\u201d on the iPhone)",
                "USB cable is charge-only or disconnected",
                "Apple device services are unavailable (see Help)",
            ],
            technical=technical,
            retryable=True,
        )


class DeviceTrustError(DeviceError):
    def __init__(self, technical: str = "") -> None:
        super().__init__(
            title="Trust required",
            message="Your iPhone hasn't trusted this computer yet.",
            causes=[
                "Unlock your iPhone",
                "Tap \u201cTrust\u201d when prompted",
                "Reconnect the USB cable and try again",
            ],
            technical=technical,
            retryable=True,
        )


class IpaError(AppError):
    pass


class IpaInvalidError(IpaError):
    def __init__(self, reason: str, technical: str = "") -> None:
        super().__init__(
            title="Invalid IPA",
            message=f"This file doesn't look like a valid IPA. {reason}",
            causes=[
                "The file is damaged or incomplete",
                "It's not an iOS application archive (needs Payload/*.app/Info.plist)",
            ],
            technical=technical,
            retryable=False,
        )


class SigningError(AppError):
    pass


class SigningNotConfiguredError(SigningError):
    def __init__(self, technical: str = "") -> None:
        super().__init__(
            title="Signing not configured",
            message="No signing identity is available, so the app can't be installed yet.",
            causes=[
                "No Apple Developer certificate / provisioning profile found",
                "On Windows, free-developer signing needs a helper (see Help)",
            ],
            technical=technical,
            retryable=False,
        )


class DownloadError(AppError):
    pass


class InstallationError(AppError):
    pass
