"""Device state tests with mock providers (no iPhone needed)."""

from __future__ import annotations

from app.device.interface import DeviceService
from app.device.mock_provider import MockDeviceProvider
from app.device.models import ConnectionType, DeviceInfo, TrustState


def _dev(name="iPhone 15 Pro", trusted=TrustState.TRUSTED) -> DeviceInfo:
    return DeviceInfo(
        udid="UDID-123",
        name=name,
        ios_version="18.1",
        connection=ConnectionType.USB,
        trusted=trusted,
    )


def test_empty_without_env(monkeypatch) -> None:
    monkeypatch.delenv("DENIZ_MOCK_DEVICES", raising=False)
    svc = DeviceService([MockDeviceProvider(simulated=[])])
    assert svc.refresh() == []


def test_simulated_device(monkeypatch) -> None:
    monkeypatch.setenv("DENIZ_MOCK_DEVICES", "1")
    svc = DeviceService([MockDeviceProvider()])
    found = svc.refresh()
    assert len(found) == 1
    assert found[0].trusted == TrustState.TRUSTED


def test_dedup_by_udid() -> None:
    svc = DeviceService([MockDeviceProvider(simulated=[_dev(), _dev()])])
    assert len(svc.refresh()) == 1


def test_untrusted_hint() -> None:
    d = _dev(trusted=TrustState.UNTRUSTED)
    assert "Trust" in d.status_hint()


def test_broken_provider_does_not_crash() -> None:
    class Broken(MockDeviceProvider):
        def list_devices(self):  # type: ignore[override]
            raise RuntimeError("usb exploded")

    svc = DeviceService([Broken(simulated=[]), MockDeviceProvider(simulated=[_dev()])])
    assert len(svc.refresh()) == 1


def test_short_udid() -> None:
    d = _dev()
    d.udid = "00008110-001A2B3C4D5E6F78"
    assert "\u2026" in d.short_udid
    assert d.short_udid.endswith("6F78")
    tiny = _dev()
    assert tiny.short_udid == "UDID-123"  # short UDIDs pass through
