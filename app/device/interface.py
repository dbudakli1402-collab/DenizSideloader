"""Device provider interface + service (mockable for CI without iPhone)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.device.models import DeviceInfo


class DeviceProvider(ABC):
    """Abstract source of connected iOS devices."""

    name: str = "base"

    @abstractmethod
    def list_devices(self) -> list[DeviceInfo]:
        """Return currently connected devices. Must not raise on empty."""

    @abstractmethod
    def is_available(self) -> bool:
        """False when the underlying backend can't run on this machine."""

    @abstractmethod
    def help_text(self) -> str:
        """Human-readable explanation of requirements/limitations."""


class DeviceService:
    """Facade used by UI + installation workflow."""

    def __init__(self, providers: list[DeviceProvider] | None = None) -> None:
        from app.device.mock_provider import MockDeviceProvider

        self._providers: list[DeviceProvider] = providers or [MockDeviceProvider()]
        self._cached: list[DeviceInfo] = []

    @property
    def providers(self) -> list[DeviceProvider]:
        return list(self._providers)

    def refresh(self) -> list[DeviceInfo]:
        found: list[DeviceInfo] = []
        for provider in self._providers:
            try:
                if provider.is_available():
                    found.extend(provider.list_devices())
            except Exception:
                # A broken provider must never crash detection; UI shows hint.
                continue
        # Deduplicate by UDID, keep first
        seen: set[str] = set()
        deduped: list[DeviceInfo] = []
        for d in found:
            if d.udid not in seen:
                seen.add(d.udid)
                deduped.append(d)
        self._cached = deduped
        return list(self._cached)

    @property
    def cached(self) -> list[DeviceInfo]:
        return list(self._cached)

    def backend_help(self) -> str:
        return "\n\n".join(p.help_text() for p in self._providers)
