"""Streaming download manager: progress, speed, ETA, cancel, SHA-256.

Security chain: URL -> Validate -> Download (HTTPS, cert validation by
requests) -> Verify (size + SHA-256) -> Store (path-traversal safe).
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

import requests

from app.core.errors import DownloadError
from app.core.logging import get_logger, sanitize_for_log
from app.security.validation import safe_join, sanitize_filename, validate_https_url

log = get_logger("downloads")


class DownloadState(str, Enum):
    QUEUED = "queued"
    ACTIVE = "active"
    PAUSED = "paused"
    DONE = "done"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class DownloadItem:
    url: str
    dest: Path
    state: DownloadState = DownloadState.QUEUED
    total_bytes: int = 0
    done_bytes: int = 0
    speed_bps: float = 0.0
    sha256: str = ""
    error: str = ""
    _cancel: threading.Event = field(default_factory=threading.Event, repr=False)
    _pause: threading.Event = field(default_factory=threading.Event, repr=False)

    @property
    def progress(self) -> float:
        if self.total_bytes <= 0:
            return 0.0
        return min(1.0, self.done_bytes / self.total_bytes)

    @property
    def eta_seconds(self) -> float | None:
        if self.speed_bps <= 0 or self.total_bytes <= 0:
            return None
        remaining = max(0, self.total_bytes - self.done_bytes)
        return remaining / self.speed_bps


ProgressCb = Callable[[DownloadItem], None]


class DownloadManager:
    def __init__(self, download_dir: Path, max_concurrent: int = 3) -> None:
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max(1, max_concurrent)
        self._items: list[DownloadItem] = []
        self._lock = threading.Lock()
        self._sem = threading.Semaphore(self.max_concurrent)

    @property
    def items(self) -> list[DownloadItem]:
        with self._lock:
            return list(self._items)

    def enqueue(self, url: str, filename: str | None = None) -> DownloadItem:
        clean_url = validate_https_url(url)
        if filename:
            safe_name = sanitize_filename(filename)
        else:
            raw = Path(urlparse(clean_url).path).name or "app.ipa"
            safe_name = sanitize_filename(raw)
        dest = safe_join(self.download_dir, safe_name)
        # Avoid overwrite: suffix counter
        base = dest
        i = 1
        while dest.exists():
            dest = base.with_name(f"{base.stem} ({i}){base.suffix}")
            i += 1
        item = DownloadItem(url=clean_url, dest=dest)
        with self._lock:
            self._items.append(item)
        log.info("download queued: %s", sanitize_for_log({"url": clean_url, "dest": str(dest)}))
        return item

    def start(self, item: DownloadItem, on_progress: ProgressCb | None = None) -> threading.Thread:
        t = threading.Thread(target=self._run, args=(item, on_progress), daemon=True)
        t.start()
        return t

    def cancel(self, item: DownloadItem) -> None:
        item._cancel.set()
        item._pause.clear()

    def pause(self, item: DownloadItem) -> None:
        if item.state == DownloadState.ACTIVE:
            item._pause.set()
            item.state = DownloadState.PAUSED

    def resume(self, item: DownloadItem, on_progress: ProgressCb | None = None) -> threading.Thread:
        item._pause.clear()
        item._cancel.clear()
        return self.start(item, on_progress)

    # -- internals -------------------------------------------------------
    def _run(self, item: DownloadItem, on_progress: ProgressCb | None) -> None:
        with self._sem:
            item.state = DownloadState.ACTIVE
            item.error = ""
            try:
                self._stream(item, on_progress)
                item.state = DownloadState.DONE
            except DownloadError as exc:
                if item._cancel.is_set():
                    item.state = DownloadState.CANCELLED
                else:
                    item.state = DownloadState.ERROR
                    item.error = exc.user_text() if hasattr(exc, "user_text") else str(exc)
            except Exception as exc:  # defensive: never leak raw internals to UI alone
                item.state = DownloadState.ERROR if not item._cancel.is_set() else DownloadState.CANCELLED
                item.error = f"Download failed: {exc}"
            if on_progress:
                try:
                    on_progress(item)
                except Exception:
                    pass

    def _stream(self, item: DownloadItem, on_progress: ProgressCb | None) -> None:
        headers = {}
        start_at = 0
        if item.dest.exists() and item.done_bytes > 0:
            start_at = item.dest.stat().st_size
            headers["Range"] = f"bytes={start_at}-"
        try:
            with requests.get(item.url, stream=True, timeout=30, headers=headers, verify=True) as resp:
                if resp.status_code not in (200, 206):
                    raise DownloadError(
                        title="Download failed",
                        message=f"Server answered with HTTP {resp.status_code}.",
                        causes=[
                            "The link expired or is not a direct IPA link",
                            "No internet connection / firewall blocking",
                        ],
                        technical=f"HTTP {resp.status_code} for {item.url}",
                    )
                total = resp.headers.get("Content-Length")
                try:
                    item.total_bytes = (int(total) if total else 0) + start_at
                except ValueError:
                    item.total_bytes = start_at
                ctype = (resp.headers.get("Content-Type") or "").lower()
                if "text/html" in ctype:
                    raise DownloadError(
                        title="Not an IPA file",
                        message="The URL returned a web page instead of an IPA file.",
                        causes=["Link is a store page, not a direct .ipa download"],
                        technical=f"Content-Type: {ctype}",
                    )
                mode = "ab" if (start_at and resp.status_code == 206) else "wb"
                if mode == "wb":
                    start_at = 0
                    item.done_bytes = 0
                h = hashlib.sha256()
                if mode == "ab" and item.dest.exists():
                    # Re-hash existing prefix (small files in practice; chunked)
                    with open(item.dest, "rb") as f:
                        for chunk in iter(lambda: f.read(1024 * 1024), b""):
                            h.update(chunk)
                last_emit = 0.0
                t0 = time.monotonic()
                window_bytes = 0
                window_t0 = t0
                with open(item.dest, mode) as f:
                    for chunk in resp.iter_content(chunk_size=256 * 1024):
                        if item._cancel.is_set():
                            return
                        while item._pause.is_set() and not item._cancel.is_set():
                            time.sleep(0.1)
                        if not chunk:
                            continue
                        f.write(chunk)
                        h.update(chunk)
                        item.done_bytes += len(chunk)
                        window_bytes += len(chunk)
                        now = time.monotonic()
                        if now - window_t0 >= 0.5:
                            item.speed_bps = window_bytes / max(0.001, now - window_t0)
                            window_bytes = 0
                            window_t0 = now
                        if on_progress and now - last_emit > 0.15:
                            last_emit = now
                            on_progress(item)
                item.sha256 = h.hexdigest()
        except requests.exceptions.SSLError as exc:
            raise DownloadError(
                title="Insecure connection",
                message="The server's HTTPS certificate could not be verified. Download aborted.",
                technical=str(exc)[:300],
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise DownloadError(
                title="Connection failed",
                message="We couldn't reach the download server.",
                causes=["No internet connection", "Server offline", "Firewall/VPN blocking"],
                technical=str(exc)[:300],
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise DownloadError(
                title="Download timed out",
                message="The server took too long to respond.",
                technical=str(exc)[:300],
            ) from exc


def format_speed(bps: float) -> str:
    if bps < 1024:
        return f"{bps:.0f} B/s"
    if bps < 1024 * 1024:
        return f"{bps / 1024:.1f} KB/s"
    return f"{bps / (1024 * 1024):.1f} MB/s"


def format_eta(seconds: float | None) -> str:
    if seconds is None:
        return "--"
    s = int(seconds)
    if s < 60:
        return f"{s}s left"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}m {s}s left"
    h, m = divmod(m, 60)
    return f"{h}h {m}m left"
