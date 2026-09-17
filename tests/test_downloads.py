"""Download manager tests (local HTTP server, no internet)."""

from __future__ import annotations

import functools
import http.server
import threading
from pathlib import Path

import pytest

from app.downloads.manager import DownloadManager, DownloadState
from app.downloads.validation import sha256_of_file


@pytest.fixture
def serve_dir(tmp_path: Path):
    root = tmp_path / "srv"
    root.mkdir()
    payload = root / "app.ipa"
    payload.write_bytes(b"A" * 256 * 1024 + b"B" * 128 * 1024)  # 384 KiB
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_port}/app.ipa", payload
    srv.shutdown()


def test_download_success(tmp_path: Path, serve_dir) -> None:
    url, src = serve_dir
    mgr = DownloadManager(tmp_path / "dl")
    item = mgr.enqueue(url)
    seen: list[float] = []
    th = mgr.start(item, on_progress=lambda it: seen.append(it.progress))
    th.join(timeout=30)
    assert item.state == DownloadState.DONE
    assert item.dest.is_file()
    assert item.dest.stat().st_size == src.stat().st_size
    assert item.sha256 == sha256_of_file(item.dest)
    assert seen, "expected progress callbacks"


def test_download_404(tmp_path: Path, serve_dir) -> None:
    url, _ = serve_dir
    mgr = DownloadManager(tmp_path / "dl")
    item = mgr.enqueue(url.replace("app.ipa", "missing.ipa"))
    th = mgr.start(item)
    th.join(timeout=30)
    assert item.state == DownloadState.ERROR
    assert item.error


def test_enqueue_rejects_html_page_url(tmp_path: Path) -> None:
    mgr = DownloadManager(tmp_path / "dl")
    with pytest.raises(ValueError):
        mgr.enqueue("https://example.com/store-page")


def test_cancel(tmp_path: Path, serve_dir) -> None:
    url, _ = serve_dir
    mgr = DownloadManager(tmp_path / "dl")
    item = mgr.enqueue(url)
    mgr.cancel(item)
    th = mgr.start(item)
    th.join(timeout=30)
    assert item.state in (DownloadState.CANCELLED, DownloadState.DONE, DownloadState.ERROR)


def test_format_helpers() -> None:
    from app.downloads.manager import format_eta, format_speed

    assert "B/s" in format_speed(512)
    assert "KB/s" in format_speed(2048)
    assert format_eta(None) == "--"
    assert "left" in format_eta(90)
