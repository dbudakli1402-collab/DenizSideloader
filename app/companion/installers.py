"""Official companion installer flow (iloader operation ported, rewritten).

Steps per installer, mirroring iloader's download → install → pairing:
1. Download the official IPA from the project's GitHub releases.
2. Install it through our regular (signed) installation pipeline.
3. Place this PC's pairing record into the installed app container so the
   companion app (SideStore) can refresh apps itself.

Step 3 uses the existing pymobiledevice3 house_arrest backend and only ever
touches the user's own trusted device. Anything missing fails honestly.
"""

from __future__ import annotations

from collections.abc import Callable

from app.companion.models import InstallerDef
from app.core.logging import get_logger
from app.device.pairing import load_usbmux_record
from app.downloads.manager import DownloadItem, DownloadManager
from app.installation.models import InstallationJob
from app.installation.service import InstallationService

log = get_logger("companion.install")

StepCb = Callable[[str, float, str], None]  # (step, progress01, message)


class CompanionInstaller:
    def __init__(self, downloads: DownloadManager, installer: InstallationService) -> None:
        self.downloads = downloads
        self.installer = installer

    def run(self, definition: InstallerDef, udid: str, on_step: StepCb | None = None) -> InstallationJob:
        def emit(step: str, frac: float, msg: str = "") -> None:
            if on_step:
                try:
                    on_step(step, frac, msg)
                except Exception:
                    pass

        job = InstallationJob(ipa_path="", udid=udid, app_name=definition.title)
        # 1. download official IPA into the download folder
        emit("download", 0.02, f"Lade {definition.filename} …")
        try:
            item = self.downloads.enqueue(definition.url, filename=definition.filename)
        except ValueError as exc:
            job.fail("Download abgelehnt", str(exc))
            emit("download", 0.0, str(exc))
            return job
        done: list[str] = []
        failed: list[str] = []

        def _cb(it: DownloadItem) -> None:
            emit("download", 0.02 + it.progress * 0.30, f"Lade … {int(it.progress * 100)} %")

        thread = self.downloads.start(item, on_progress=_cb)
        thread.join(timeout=1800)
        if item.state.value != "done":
            job.fail("Download fehlgeschlagen", item.error or "Unbekannter Download-Fehler.")
            emit("download", 0.0, job.error_detail)
            return job
        ipa_path = str(item.dest)
        job.ipa_path = ipa_path
        emit("download", 0.34, "Download fertig.")
        # 2. install through the regular pipeline (signing requirements apply)
        emit("install", 0.36, "Installiere …")

        def _forward(inner: InstallationJob) -> None:
            emit("install", 0.36 + inner.progress * 0.50, inner.message)

        self.installer.run(job, on_step=_forward)
        if job.step.value != "done":
            emit("install", 0.36, job.error_detail)
            return job
        # 3. place pairing record into the companion app container
        emit("pairing", 0.88, "Lege Pairing-Datei ab …")
        ok, note = place_pairing_record(udid, definition.bundle_id, definition.pairing_file)
        if not ok:
            job.fail("Pairing fehlgeschlagen", note)
            emit("pairing", 0.88, note)
            return job
        emit("pairing", 1.0, "Fertig.")
        _ = done, failed
        return job


def place_pairing_record(udid: str, bundle_id: str, filename: str) -> tuple[bool, str]:
    """Push this PC's pairing record into the app container. Honest result."""
    data = load_usbmux_record(udid)
    if not data:
        return False, (
            "Kein lokaler Pairing-Eintrag für dieses Gerät gefunden. "
            "Verbinde das iPhone per USB, tippe auf „Vertrauen“ und versuche es erneut."
        )

    async def _push() -> None:
        from pymobiledevice3.lockdown import create_using_usbmux
        from pymobiledevice3.services.house_arrest import HouseArrestService

        lockdown = await create_using_usbmux(udid)
        async with HouseArrestService(lockdown=lockdown) as ha:
            await ha.send_command(bundle_id, "VendDocuments")
            ha.set_file_contents(filename, data)  # sync helper on the service

    try:
        from app.device.pymobiledevice_provider import _run

        _run(_push())
    except Exception as exc:
        msg = str(exc)
        if "trust" in msg.lower() or "pair" in msg.lower():
            return False, "iPhone vertraut diesem Computer nicht. Entsperren, „Vertrauen“, erneut versuchen."
        return False, f"Pairing-Ablage fehlgeschlagen: {msg[:300]}"
    log.info("pairing record placed for %s", bundle_id)
    return True, "Pairing-Datei abgelegt."
