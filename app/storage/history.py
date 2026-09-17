"""Activity history: append-only JSONL event log for the Verlauf timeline."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

KINDS = {"install", "download", "device", "error"}


@dataclass
class HistoryEvent:
    ts: str  # ISO timestamp
    kind: str  # install | download | device | error
    title: str
    detail: str = ""
    status: str = "ok"  # ok | fail | info

    @staticmethod
    def now(kind: str, title: str, detail: str = "", status: str = "ok") -> HistoryEvent:
        return HistoryEvent(
            ts=datetime.now().isoformat(timespec="seconds"),
            kind=kind if kind in KINDS else "error",
            title=title,
            detail=detail,
            status=status,
        )


class HistoryStore:
    def __init__(self, path: Path, limit: int = 300) -> None:
        self.path = path
        self.limit = limit
        self._events: list[HistoryEvent] = []
        self.load()

    def load(self) -> list[HistoryEvent]:
        self._events = []
        if self.path.is_file():
            try:
                for line in self.path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    raw = json.loads(line)
                    self._events.append(
                        HistoryEvent(
                            ts=str(raw.get("ts", "")),
                            kind=str(raw.get("kind", "error")),
                            title=str(raw.get("title", "")),
                            detail=str(raw.get("detail", "")),
                            status=str(raw.get("status", "ok")),
                        )
                    )
            except Exception:
                self._events = []
        return list(self._events)

    def add(self, event: HistoryEvent) -> None:
        self._events.append(event)
        del self._events[: max(0, len(self._events) - self.limit)]
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
        except Exception:
            pass

    def record(self, kind: str, title: str, detail: str = "", status: str = "ok") -> HistoryEvent:
        event = HistoryEvent.now(kind, title, detail, status)
        self.add(event)
        return event

    def list(self, kind: str = "all") -> list[HistoryEvent]:
        if kind == "all":
            items = list(self._events)
        elif kind == "errors":
            items = [e for e in self._events if e.status == "fail"]
        else:
            items = [e for e in self._events if e.kind == kind]
        return sorted(items, key=lambda e: e.ts, reverse=True)

    def clear(self) -> None:
        self._events = []
        try:
            if self.path.is_file():
                self.path.unlink()
        except Exception:
            pass
