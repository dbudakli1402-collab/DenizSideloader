"""IPA data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class IpaInfo:
    path: str
    file_name: str
    file_size: int
    bundle_id: str
    app_name: str
    version: str
    build: str = ""
    minimum_os: str = ""
    icon_path: str = ""
    sha256: str = ""
    status: str = "ready"  # ready | installing | installed | error
    category: str = "Alle"
    added_ts: str = ""
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def size_human(self) -> str:
        size = float(self.file_size)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
            size /= 1024
        return f"{size:.1f} GB"

    @property
    def display_title(self) -> str:
        return self.app_name or Path(self.path).stem
