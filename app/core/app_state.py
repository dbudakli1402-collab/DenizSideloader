"""Central app state container (non-Qt, easily mockable in tests)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.device.models import DeviceInfo
from app.installation.models import InstallationJob
from app.ipa.models import IpaInfo


@dataclass
class AppState:
    devices: list[DeviceInfo] = field(default_factory=list)
    selected_device_udid: str | None = None
    library: list[IpaInfo] = field(default_factory=list)
    recent_ipas: list[str] = field(default_factory=list)
    active_job: InstallationJob | None = None
    first_launch_done: bool = False

    @property
    def selected_device(self) -> DeviceInfo | None:
        for d in self.devices:
            if d.udid == self.selected_device_udid:
                return d
        return self.devices[0] if self.devices else None

    def push_recent(self, path: str, limit: int = 8) -> None:
        if path in self.recent_ipas:
            self.recent_ipas.remove(path)
        self.recent_ipas.insert(0, path)
        del self.recent_ipas[limit:]
