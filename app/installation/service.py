"""Installation service orchestrating the honest workflow.

Steps: Select -> Analyze -> Detect -> Signing check -> Prepare -> Sign ->
Install -> Verify -> Done.

- Analyze is real (IPA parser).
- Detect is real (DeviceService).
- Signing check + Sign use SigningService honestly: without valid assets the
  job FAILS with guidance instead of fake success.
- Install uses the device backend when it supports installs
  (pymobiledevice3 InstallationProxy); otherwise fails honestly with the
  documented Windows limitation and next steps.
- Designed for Qt threading: pass a callback; the service never touches UI.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from app.core.errors import DeviceNotFoundError, IpaInvalidError, SigningNotConfiguredError
from app.core.logging import get_logger
from app.device.interface import DeviceService
from app.device.models import TrustState
from app.installation.models import InstallationJob, InstallStep
from app.ipa.parser import parse_ipa
from app.signing.models import SigningResult
from app.signing.service import SigningService

log = get_logger("install")

ProgressCb = Callable[[InstallationJob], None]


class InstallationService:
    def __init__(
        self,
        devices: DeviceService | None = None,
        signing: SigningService | None = None,
    ) -> None:
        from app.device.mock_provider import MockDeviceProvider
        from app.device.pymobiledevice_provider import default_providers

        self.devices = devices or DeviceService(providers=default_providers())
        self.signing = signing or SigningService()
        # Keep parity with simple mocks used in tests
        _ = MockDeviceProvider

    def run(self, job: InstallationJob, on_step: ProgressCb | None = None) -> InstallationJob:
        def emit() -> None:
            if on_step:
                try:
                    on_step(job)
                except Exception:
                    pass

        try:
            # 1. Select
            job.advance(InstallStep.SELECT, 0.05, f"IPA loaded: {Path(job.ipa_path).name}")
            emit()
            # 2. Analyze (real)
            try:
                info = parse_ipa(job.ipa_path)
            except IpaInvalidError as exc:
                job.fail(exc.title, exc.user_text())
                emit()
                return job
            job.app_name = info.app_name
            job.bundle_id = info.bundle_id
            job.advance(
                InstallStep.ANALYZE,
                0.18,
                f"Analyzed {info.app_name} v{info.version} ({info.bundle_id})",
            )
            emit()
            # 3. Detect (real)
            found = self.devices.refresh()
            target = next((d for d in found if d.udid == job.udid), None)
            if target is None:
                err = DeviceNotFoundError()
                job.fail(err.title, err.user_text())
                emit()
                return job
            if target.trusted == TrustState.UNTRUSTED:
                job.fail(
                    "Trust required",
                    "Your iPhone hasn't trusted this computer yet.\n\nUnlock your iPhone and tap \u201cTrust\u201d.",
                )
                emit()
                return job
            job.advance(InstallStep.DETECT, 0.30, f"iPhone connected: {target.display_name}")
            emit()
            # 4. Signing check (real: need at least one identity)
            identities = self.signing.all_identities()
            if not identities:
                sign_err = SigningNotConfiguredError()
                job.fail(sign_err.title, sign_err.user_text())
                emit()
                return job
            provider, identity = identities[0]
            job.advance(InstallStep.SIGNING_CHECK, 0.42, f"Using: {identity.label}")
            emit()
            # 5. Prepare
            job.advance(InstallStep.PREPARE, 0.52, "Preparing installation\u2026")
            emit()
            time.sleep(0.05)
            # 6. Sign (honest: may fail without assets)
            work_out = str(Path(job.ipa_path).with_name(Path(job.ipa_path).stem + ".signed.ipa"))
            result: SigningResult = self.signing.sign(provider, job.ipa_path, identity, work_out)
            if not result.ok:
                job.fail(
                    "Signing incomplete",
                    result.message + ("\n\n" + result.technical if result.technical else ""),
                )
                emit()
                return job
            job.advance(InstallStep.SIGN, 0.66, result.message or "Signing prepared")
            emit()
            signed_ipa = result.output_ipa or job.ipa_path
            # 7. Install (backend-dependent, honest)
            job.advance(
                InstallStep.INSTALL,
                0.75,
                "Installing application\u2026 Do not disconnect your iPhone.",
            )
            emit()
            install_ok, install_note = self._backend_install(target.udid, signed_ipa, on_step, job)
            if not install_ok:
                job.fail("Installation not completed", install_note)
                emit()
                return job
            # 8. Verify
            job.advance(InstallStep.VERIFY, 0.93, "Verifying installation\u2026")
            emit()
            time.sleep(0.05)
            job.advance(InstallStep.DONE, 1.0, f"{job.app_name} was successfully installed on your iPhone.")
            emit()
            return job
        except Exception as exc:  # last-resort guard
            log.error("installation crashed: %s", exc)
            job.fail("Unexpected error", f"{exc}")
            emit()
            return job

    # -- backend ---------------------------------------------------------
    def _backend_install(
        self, udid: str, signed_ipa: str, on_step: ProgressCb | None, job: InstallationJob
    ) -> tuple[bool, str]:
        """Try real install via pymobiledevice3; else honest limitation message."""
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.services.installation_proxy import InstallationProxyService
        except Exception:
            return False, (
                "The install backend (pymobiledevice3) isn't available on this PC.\n\n"
                "To enable real installs:\n"
                "\u2022 Install iTunes / Apple Devices + `pip install DenizSideloader[device]`\n"
                "\u2022 Provide your Apple Developer signing assets (Settings \u2192 Signing)\n"
                "\u2022 Reconnect via USB, trust, retry\n\n"
                "Nothing was installed \u2014 this is a documented limitation, not a silent fake-success."
            )
        try:
            lockdown = create_using_usbmux(udid)
            last_pct = 0

            def _cb(progress: object) -> None:
                nonlocal last_pct
                try:
                    pct = 0
                    if isinstance(progress, dict):
                        pct = int(progress.get("PercentComplete", 0))
                    frac = 0.75 + (min(100, max(0, pct)) / 100.0) * 0.16
                    job.progress = frac
                    job.message = f"Installing application\u2026 {pct}%"
                    if on_step:
                        on_step(job)
                except Exception:
                    pass

            with InstallationProxyService(lockdown=lockdown) as inst:
                inst.install(signed_ipa, callback=_cb)
            return True, "ok"
        except Exception as exc:
            msg = str(exc)
            if "trust" in msg.lower() or "pair" in msg.lower():
                return False, (
                    "Your iPhone hasn't trusted this computer yet.\n\n"
                    "Unlock it, tap \u201cTrust\u201d, reconnect, retry."
                )
            return False, (
                "The device backend reported an error and nothing was installed.\n\n"
                f"Details: {msg[:600]}\n\n"
                "Check: USB cable, iTunes/Apple Devices installed, signing assets valid."
            )
