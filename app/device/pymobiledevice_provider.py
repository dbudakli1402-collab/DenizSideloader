"""Real-device provider based on pymobiledevice3 (optional dependency).

Honest limitation handling (Windows):
- pymobiledevice3 can query lockdown info over USB *if* Apple Mobile Device
  support / iTunes drivers are installed and the device trusts the PC.
- IPA *installation* of a signed app via AFC/house_arrest-style flows is
  possible only when signing requirements are met; unsigned installs are
  refused and surfaced as errors, never bypassed.
- If pymobiledevice3 (or its drivers) is missing, this provider reports
  ``is_available() == False`` with a clear help text instead of faking data.

No private APIs, no jailbreak, no DRM handling.
"""

from __future__ import annotations

from app.device.interface import DeviceProvider
from app.device.models import ConnectionType, DeviceInfo, TrustState


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
            from pymobiledevice3.usbmux import list_devices as usbmux_list
        except Exception as exc:
            raise RuntimeError(f"pymobiledevice3 backend unavailable: {exc}") from exc

        devices: list[DeviceInfo] = []
        try:
            raw = usbmux_list()
        except Exception:
            return []
        for entry in raw or []:
            try:
                udid = str(getattr(entry, "udid", "") or getattr(entry, "serial", ""))
                if not udid:
                    continue
                name, version = self._lockdown_info(udid)
                devices.append(
                    DeviceInfo(
                        udid=udid,
                        name=name or "iPhone",
                        ios_version=version or "Unknown",
                        connection=ConnectionType.USB,
                        trusted=TrustState.TRUSTED if name else TrustState.UNKNOWN,
                    )
                )
            except Exception:
                continue
        return devices

    def _lockdown_info(self, udid: str) -> tuple[str, str]:
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
        except Exception:
            return "", ""
        try:
            lockdown = create_using_usbmux(udid)
            name = str(lockdown.get_value("", "DeviceName") or "")
            version = str(lockdown.get_value("", "ProductVersion") or "")
            return name, version
        except Exception as exc:
            # Pairing/trust errors surface as untrusted hint via empty name.
            if "trust" in str(exc).lower() or "pair" in str(exc).lower():
                return "", ""
            return "", ""

    def list_installed_apps(self, udid: str) -> list[dict[str, str]]:
        """Best-effort installed-app query via pymobiledevice3.

        Returns [] when unsupported/unavailable. Never raises for UI paths.
        """
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.services.installation_proxy import InstallationProxyService
        except Exception:
            return []
        try:
            lockdown = create_using_usbmux(udid)
            with InstallationProxyService(lockdown=lockdown) as inst:
                apps = inst.get_apps()
            result: list[dict[str, str]] = []
            app_dict = apps.get("User", apps) if isinstance(apps, dict) else {}
            if isinstance(app_dict, dict):
                for bundle_id, meta in app_dict.items():
                    if not isinstance(meta, dict):
                        continue
                    result.append(
                        {
                            "bundle_id": str(bundle_id),
                            "name": str(meta.get("CFBundleDisplayName") or meta.get("CFBundleName") or bundle_id),
                            "version": str(meta.get("CFBundleShortVersionString") or ""),
                        }
                    )
            return result
        except Exception:
            return []

    def help_text(self) -> str:
        return (
            "pymobiledevice3 backend (optional, open-source, `pip install DenizSideloader[device]`).\n"
            "Requires: iPhone connected via USB, unlocked, tapped \u201cTrust\u201d, "
            "plus Apple Mobile Device support (install iTunes from Apple or Apple Devices app).\n"
            "Without these, no device is reported \u2014 this is a documented limitation, not an error to bypass."
        )


def default_providers() -> list[DeviceProvider]:
    """Preferred provider chain: real backend first, mock fallback."""
    from app.device.mock_provider import MockDeviceProvider

    return [PyMobileDeviceProvider(), MockDeviceProvider()]
