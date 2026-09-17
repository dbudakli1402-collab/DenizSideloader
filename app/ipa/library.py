"""Local IPA library: import / list / remove with JSON persistence."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path

from app.core.logging import get_logger
from app.ipa.models import IpaInfo
from app.ipa.parser import parse_ipa
from app.security.validation import is_safe_ipa_path, sanitize_filename

log = get_logger("ipa.library")


class IpaLibrary:
    def __init__(self, library_dir: Path, index_file: Path | None = None) -> None:
        self.library_dir = library_dir
        self.library_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = index_file or (library_dir / "library.json")
        self._items: dict[str, IpaInfo] = {}
        self.load()

    # -- persistence -----------------------------------------------------
    def load(self) -> None:
        self._items = {}
        if not self.index_file.is_file():
            # Re-scan directory for IPAs without index
            for p in sorted(self.library_dir.glob("*.ipa")):
                try:
                    info = parse_ipa(p)
                    self._items[info.bundle_id + "|" + p.name] = info
                except Exception:
                    continue
            return
        try:
            data = json.loads(self.index_file.read_text(encoding="utf-8"))
            for entry in data.get("items", []):
                try:
                    info = IpaInfo(**{k: entry[k] for k in IpaInfo.__dataclass_fields__ if k in entry})
                    if Path(info.path).is_file():
                        self._items[info.bundle_id + "|" + Path(info.path).name] = info
                except Exception:
                    continue
        except Exception as exc:
            log.warning("library index unreadable, rescanning: %s", exc)

    def save(self) -> None:
        payload = {"version": 1, "items": [asdict(i) for i in self._items.values()]}
        tmp = self.index_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self.index_file)

    # -- operations ------------------------------------------------------
    def list(self) -> list[IpaInfo]:
        return sorted(self._items.values(), key=lambda i: i.app_name.lower())

    def import_file(self, src: str | Path, copy: bool = True) -> IpaInfo:
        src_p = Path(src)
        if not is_safe_ipa_path(src_p):
            from app.core.errors import IpaInvalidError

            raise IpaInvalidError("Only .ipa files can be imported.")
        info = parse_ipa(src_p)  # validates before copying
        dest_name = sanitize_filename(src_p.name)
        dest = self.library_dir / dest_name
        # Deduplicate filename
        counter = 1
        while dest.exists() and dest.resolve() != src_p.resolve():
            stem = Path(dest_name).stem
            dest = self.library_dir / f"{stem} ({counter}).ipa"
            counter += 1
        if copy and dest.resolve() != src_p.resolve():
            shutil.copy2(src_p, dest)
            info.path = str(dest)
            info.file_name = dest.name
            info.file_size = dest.stat().st_size
        key = info.bundle_id + "|" + Path(info.path).name
        self._items[key] = info
        self.save()
        log.info("imported IPA: %s (%s)", info.app_name, info.bundle_id)
        return info

    def remove(self, info: IpaInfo, delete_file: bool = True) -> None:
        key = info.bundle_id + "|" + Path(info.path).name
        self._items.pop(key, None)
        if delete_file:
            try:
                Path(info.path).unlink(missing_ok=True)
            except Exception:
                pass
        self.save()

    def find_by_bundle(self, bundle_id: str) -> IpaInfo | None:
        for item in self._items.values():
            if item.bundle_id == bundle_id:
                return item
        return None
