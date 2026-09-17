"""IPA parser: reads metadata + icon from an .ipa (zip) without executing anything.

An IPA must contain ``Payload/<App>.app/Info.plist``. We parse it with
plistlib (XML + binary both supported) and extract a small, well-defined
subset of keys. No code is executed, no DRM touched.
"""

from __future__ import annotations

import hashlib
import plistlib
import zipfile
from pathlib import Path

from app.core.errors import IpaInvalidError
from app.core.logging import get_logger
from app.ipa.models import IpaInfo

log = get_logger("ipa")

INFO_KEYS = {
    "CFBundleIdentifier": "bundle_id",
    "CFBundleDisplayName": "display",
    "CFBundleName": "name",
    "CFBundleShortVersionString": "version",
    "CFBundleVersion": "build",
    "MinimumOSVersion": "minimum_os",
    "LSMinimumSystemVersion": "minimum_os_alt",
}


def _find_info_plist(names: list[str]) -> str | None:
    candidates = [
        n for n in names if n.startswith("Payload/") and n.endswith(".app/Info.plist") and "__MACOSX" not in n
    ]
    if not candidates:
        return None
    # Prefer shortest (top-level app, not nested)
    candidates.sort(key=len)
    return candidates[0]


def _find_icon(zip_file: zipfile.ZipFile, app_prefix: str, plist: dict) -> str:
    """Best-effort icon lookup; returns archive member name or ''."""
    candidates: list[str] = []
    icons = plist.get("CFBundleIcons") or {}
    if isinstance(icons, dict):
        primary = icons.get("CFBundlePrimaryIcon") or {}
        if isinstance(primary, dict):
            for f in primary.get("CFBundleIconFiles") or []:
                if isinstance(f, str):
                    candidates.append(f)
    for key in ("CFBundleIconFile", "CFBundleIconFiles"):
        v = plist.get(key)
        if isinstance(v, str):
            candidates.append(v)
        elif isinstance(v, list):
            candidates.extend(x for x in v if isinstance(x, str))
    candidates.extend(["AppIcon60x60", "Icon", "icon", "AppIcon"])
    names = set(zip_file.namelist())
    for c in candidates:
        base = c[:-4] if c.lower().endswith(".png") else c
        for trial in (
            f"{app_prefix}{base}.png",
            f"{app_prefix}{base}@2x.png",
            f"{app_prefix}{base}@3x.png",
            f"{app_prefix}{c}",
        ):
            if trial in names:
                return trial
    # Fallback: any png directly under .app/
    for n in zip_file.namelist():
        if n.startswith(app_prefix) and n.lower().endswith(".png") and n.count("/") == 2:
            return n
    return ""


def parse_ipa(path: str | Path, compute_hash: bool = False) -> IpaInfo:
    p = Path(path)
    if not p.is_file():
        raise IpaInvalidError("File not found.", technical=str(p))
    if p.suffix.lower() != ".ipa":
        raise IpaInvalidError("File must have an .ipa extension.", technical=str(p))
    try:
        with zipfile.ZipFile(p, "r") as zf:
            names = zf.namelist()
            info_name = _find_info_plist(names)
            if not info_name:
                raise IpaInvalidError(
                    "No Payload/*.app/Info.plist found in archive.",
                    technical=f"{p.name}: {len(names)} entries",
                )
            app_prefix = info_name[: -len("Info.plist")]
            try:
                raw = zf.read(info_name)
            except KeyError as exc:
                raise IpaInvalidError("Info.plist could not be read.", technical=str(exc)) from exc
            try:
                plist = plistlib.loads(raw)
            except Exception as exc:
                raise IpaInvalidError("Info.plist is not a valid plist.", technical=str(exc)) from exc
            if not isinstance(plist, dict):
                raise IpaInvalidError("Info.plist has an unexpected format.")
            bundle_id = str(plist.get("CFBundleIdentifier") or "").strip()
            if not bundle_id:
                raise IpaInvalidError("Info.plist misses CFBundleIdentifier.")
            app_name = str(plist.get("CFBundleDisplayName") or plist.get("CFBundleName") or "").strip() or p.stem
            version = str(plist.get("CFBundleShortVersionString") or "").strip() or "Unknown"
            build = str(plist.get("CFBundleVersion") or "").strip()
            minimum_os = str(plist.get("MinimumOSVersion") or plist.get("LSMinimumSystemVersion") or "").strip()
            icon_member = _find_icon(zf, app_prefix, plist)
    except zipfile.BadZipFile as exc:
        raise IpaInvalidError("File is not a valid ZIP/IPA archive.", technical=str(exc)) from exc

    sha = ""
    if compute_hash:
        sha = hash_file_sha256(p)

    size = p.stat().st_size
    return IpaInfo(
        path=str(p),
        file_name=p.name,
        file_size=size,
        bundle_id=bundle_id,
        app_name=app_name,
        version=version,
        build=build,
        minimum_os=minimum_os,
        icon_path=icon_member,
        sha256=sha,
    )


def hash_file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_icon(path: str | Path, dest: Path) -> Path | None:
    """Extract the IPA icon to *dest* (PNG). Returns dest or None."""
    try:
        info = parse_ipa(path)
    except IpaInvalidError:
        return None
    if not info.icon_path:
        return None
    try:
        with zipfile.ZipFile(path, "r") as zf:
            data = zf.read(info.icon_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest
    except Exception as exc:
        log.warning("icon extract failed: %s", exc)
        return None
