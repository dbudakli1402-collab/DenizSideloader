"""Tiny typed event bus (Qt signals are used in UI; this is for core logic)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> Callable[[], None]:
        self._subs[topic].append(handler)

        def _unsub() -> None:
            try:
                self._subs[topic].remove(handler)
            except ValueError:
                pass

        return _unsub

    def emit(self, topic: str, payload: Any = None) -> None:
        for handler in list(self._subs.get(topic, [])):
            handler(payload)


bus = EventBus()
