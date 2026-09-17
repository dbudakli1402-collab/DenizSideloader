"""Mock provider: used for CI/tests and when no backend is present.

Reads optional ``DENIZ_MOCK_DEVICES=1`` env var to simulate a connected iPhone
so the UI workflow can be exercised without hardware.
"""

from __future__ import annotations

import os

from app.device.interface import DeviceProvider
from app.device.models import ConnectionType, DeviceInfo, TrustState


class MockDeviceProvider(DeviceProvider):
    name = "mock"

    def __init__(self, simulated: list[DeviceInfo] | None = None) -> None:
        self._simulated = simulated

    def is_available(self) -> bool:
        return True

    def list_devices(self) -> list[DeviceInfo]:
        if self._simulated is not None:
            return list(self._simulated)
        if os.environ.get("DENIZ_MOCK_DEVICES") == "1":
            return [
                DeviceInfo(
                    udid="MOCK-UDID-0001-DEMO",
                    name="iPhone (Simulated)",
                    ios_version="18.0",
                    model="iPhone16,2",
                    connection=ConnectionType.USB,
                    trusted=TrustState.TRUSTED,
                )
            ]
        return []

    def help_text(self) -> str:
        return "Mock backend: reports no device unless DENIZ_MOCK_DEVICES=1. Used for tests and CI without an iPhone."
