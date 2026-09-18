"""IPA repackaging for developers: change the bundle ID of your own IPA.

Legitimate use: you own the source (or a re-signable build) and need a
different bundle ID to match your provisioning profile. The function only
rewrites the ``CFBundleIdentifier`` in ``Payload/*.app/Info.plist`` and
re-zips — no code is touched, nothing decrypted, nothing bypassed.
"""

from __future__ import annotations

import plistlib
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from app.core.errors import IpaInvalidError
from app.ipa.parser import _find_info_plist  # noqa: SLF001 - internal reuse

_BUNDLE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9\-]*(\.[A-Za-z][A-Za-z0-9\-]*)+$")


def validate_bundle_id(bundle_id: str) -> str:
    cleaned = (bundle_id or "").strip()
    if not _BUNDLE_RE.match(cleaned):
        raise ValueError(
            "Ungültige Bundle-ID. Format: com.deinname.appname (Buchstaben, Ziffern, Bindestrich, Punkte)."
        )
    if len(cleaned) > 155:
        raise ValueError("Bundle-ID ist zu lang (max. 155 Zeichen).")
    return cleaned


def set_bundle_id(src: str | Path, new_bundle_id: str, dest: str | Path | None = None) -> Path:
    """Return path of the repackaged IPA with the new bundle ID."""
    bundle_id = validate_bundle_id(new_bundle_id)
    src_p = Path(src)
    if not src_p.is_file() or src_p.suffix.lower() != ".ipa":
        raise IpaInvalidError("Keine gültige IPA-Datei.", technical=str(src_p))
    if dest is None:
        dest_p = src_p.with_name(f"{src_p.stem}-repackaged.ipa")
    else:
        dest_p = Path(dest)
    try:
        with zipfile.ZipFile(src_p, "r") as zin:
            names = zin.namelist()
            info_name = _find_info_plist(names)
            if not info_name:
                raise IpaInvalidError("Kein Payload/*.app/Info.plist im Archiv.")
            tmpdir = Path(tempfile.mkdtemp(prefix="deniz-repack-"))
            try:
                zin.extractall(tmpdir)
                plist_path = tmpdir.joinpath(*info_name.split("/"))
                plist = plistlib.loads(plist_path.read_bytes())
                if not isinstance(plist, dict) or not plist.get("CFBundleIdentifier"):
                    raise IpaInvalidError("Info.plist ohne CFBundleIdentifier.")
                plist["CFBundleIdentifier"] = bundle_id
                plist_path.write_bytes(plistlib.dumps(plist))
                if dest_p.exists():
                    dest_p.unlink()
                with zipfile.ZipFile(dest_p, "w", zipfile.ZIP_DEFLATED) as zout:
                    for f in sorted(tmpdir.rglob("*")):
                        if f.is_file():
                            zout.write(f, f.relative_to(tmpdir).as_posix())
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)
    except zipfile.BadZipFile as exc:
        raise IpaInvalidError("Datei ist kein gültiges ZIP/IPA-Archiv.", technical=str(exc)) from exc
    return dest_p.resolve()
