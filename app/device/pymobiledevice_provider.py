"""Real-device provider based on pymobiledevice3 (optional dependency).

Honest limitation handling (Windows):
- pymobiledevice3 can query lockdown info over USB *if* Apple Mobile Device
  support / iTunes drivers are installed and the device trusts the PC.
- IPA *installation* of a signed app via the installation proxy is possible
  only when signing requirements are met; unsigned installs are refused and
  surfaced as errors, never bypassed.
- If pymobiledevice3 (or its drivers) is missing, this provider reports
  ``is_available() == False`` with a clear help text instead of faking data.

No private APIs, no jailbreak, no DRM handling.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

from app.core.logging import get_logger
from app.device.interface import DeviceProvider
from app.device.models import ConnectionType, DeviceInfo, TrustState

log = get_logger("device.pymobile")

T = TypeVar("T")


def _run(coro: Coroutine[Any, Any, T]) -> T:
    """Run *coro* to completion from sync code (provider interface is sync)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # Already inside a loop (unexpected in our threads): isolate in new thread.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


class PyMobileDeviceProvider(DeviceProvider):
    name = "pymobiledevice3"

    def is_available(self) -> bool:
        try:
            import pymobiledevice3  # noqa: F401
        except ImportError:
            return False
        return True

    def list_devices(self) -> list[DeviceInfo]:
        try:
            from pymobiledevice3 import usbmux
        except Exception as exc:
            raise RuntimeError(f"pymobiledevice3 backend unavailable: {exc}") from exc

        try:
            raw = _run(usbmux.list_devices())
        except Exception as exc:
            log.warning("usbmux list failed: %s", exc)
            return []
        devices: list[DeviceInfo] = []
        for entry in raw or []:
            try:
                udid = self._entry_udid(entry)
                if not udid:
                    continue
                name, version, trusted = self._lockdown_info(udid)
                devices.append(
                    DeviceInfo(
                        udid=udid,
                        name=name or "iPhone",
                        ios_version=version or "Unknown",
                        connection=ConnectionType.USB,
                        trusted=trusted,
                    )
                )
            except Exception as exc:
                log.warning("device entry skipped: %s", exc)
                continue
        return devices

    @staticmethod
    def _entry_udid(entry: Any) -> str:
        if isinstance(entry, dict):
            for key in ("UniqueDeviceID", "Identifier", "SerialNumber", "udid", "serial"):
                value = entry.get(key)
                if value:
                    return str(value)
            return ""
        for attr in ("serial", "udid", "identifier", "ecid"):
            value = getattr(entry, attr, None)
            if value:
                return str(value)
        return ""

    def _lockdown_info(self, udid: str) -> tuple[str, str, TrustState]:
        async def _query() -> tuple[str, str, TrustState]:
            from pymobiledevice3.lockdown import create_using_usbmux

            try:
                lockdown = await create_using_usbmux(udid)
            except Exception as exc:
                if "trust" in str(exc).lower() or "pair" in str(exc).lower():
                    return "", "", TrustState.UNTRUSTED
                return "", "", TrustState.UNKNOWN
            try:
                name = str(await lockdown.get_value("", "DeviceName") or "")
                version = str(await lockdown.get_value("", "ProductVersion") or "")
            except Exception as exc:
                if "trust" in str(exc).lower() or "pair" in str(exc).lower():
                    return "", "", TrustState.UNTRUSTED
                return "", "", TrustState.UNKNOWN
            return name, version, TrustState.TRUSTED if name else TrustState.UNKNOWN

        try:
            return _run(_query())
        except Exception:
            return "", "", TrustState.UNKNOWN

    def list_installed_apps(self, udid: str) -> list[dict[str, str]]:
        """Best-effort installed-app query via pymobiledevice3.

        Returns [] when unsupported/unavailable. Never raises for UI paths.
        """

        async def _query() -> list[dict[str, str]]:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.services.installation_proxy import InstallationProxyService

            lockdown = await create_using_usbmux(udid)
            async with InstallationProxyService(lockdown=lockdown) as inst:
                # Note: the 'User' filter returns {} on recent iOS versions,
                # so query 'Any' and keep third-party apps (never com.apple.*).
                apps = await inst.get_apps("Any")
            result: list[dict[str, str]] = []
            if isinstance(apps, dict):
                for bundle_id, meta in apps.items():
                    if not isinstance(meta, dict):
                        continue
                    if str(bundle_id).startswith("com.apple."):
                        continue
                    result.append(
                        {
                            "bundle_id": str(bundle_id),
                            "name": str(meta.get("CFBundleDisplayName") or meta.get("CFBundleName") or bundle_id),
                            "version": str(meta.get("CFBundleShortVersionString") or ""),
                        }
                    )
            return result

        try:
            return _run(_query())
        except Exception as exc:
            log.warning("installed-apps query failed: %s", exc)
            return []

    def get_device_details(self, udid: str) -> dict[str, Any]:
        """Extra device facts (storage, battery, serial). Only real values.

        Returns a dict with whichever keys the backend could actually read —
        the UI shows a fact only when its key is present.
        """

        async def _query() -> dict[str, Any]:
            from pymobiledevice3.lockdown import create_using_usbmux

            out: dict[str, Any] = {}
            lockdown = await create_using_usbmux(udid)
            total = await lockdown.get_value("com.apple.disk_usage", "TotalDiskCapacity")
            avail = await lockdown.get_value("com.apple.disk_usage", "AmountDataAvailable")
            if isinstance(total, int) and total > 0:
                out["storage_total"] = total
            if isinstance(avail, int) and avail >= 0:
                out["storage_available"] = avail
            batt = await lockdown.get_value("com.apple.mobile.battery", "BatteryCurrentCapacity")
            if isinstance(batt, int) and 0 <= batt <= 100:
                out["battery_pct"] = batt
            charging = await lockdown.get_value("com.apple.mobile.battery", "BatteryIsCharging")
            if isinstance(charging, bool):
                out["charging"] = charging
            serial = await lockdown.get_value("", "SerialNumber")
            if serial:
                out["serial"] = str(serial)
            ptype = await lockdown.get_value("", "ProductType")
            if ptype:
                out["product_type"] = str(ptype)
            return out

        try:
            result = _run(_query())
            return result if isinstance(result, dict) else {}
        except Exception as exc:
            log.warning("device details unavailable: %s", exc)
            return {}

    def help_text(self) -> str:
        return (
            "pymobiledevice3 backend (open-source, bundled in the release build).\n"
            "Requires: iPhone connected via USB, unlocked, tapped \u201cTrust\u201d, "
            "plus Apple Mobile Device support (install iTunes from Apple or Apple Devices app).\n"
            "Without these, no device is reported \u2014 this is a documented limitation, not an error to bypass."
        )


def default_providers() -> list[DeviceProvider]:
    """Preferred provider chain: real backend first, mock fallback."""
    from app.device.mock_provider import MockDeviceProvider

    return [PyMobileDeviceProvider(), MockDeviceProvider()]
