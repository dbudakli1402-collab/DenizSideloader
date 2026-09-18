"""Update check + companion strings tests."""

from __future__ import annotations

from app.companion.strings import STRINGS, text
from app.core.update import _nums, check_for_update


def test_nums() -> None:
    assert _nums("v1.1.0") == (1, 1, 0)
    assert _nums("v1.10.2") > _nums("v1.2.0")


def test_update_newer(monkeypatch) -> None:
    import requests

    class FakeResp:
        status_code = 200

        def json(self):
            return {"tag_name": "v9.9.9", "html_url": "https://example.com", "body": "x"}

    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResp())
    newer, tag, url, _ = check_for_update("v1.0.0")
    assert newer and tag == "v9.9.9" and url == "https://example.com"


def test_update_current(monkeypatch) -> None:
    import requests

    class FakeResp:
        status_code = 200

        def json(self):
            return {"tag_name": "v1.0.0", "html_url": "u", "body": ""}

    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResp())
    newer, _, _, _ = check_for_update("v1.0.0")
    assert not newer


def test_update_offline(monkeypatch) -> None:
    import requests

    def _boom(*a, **k):
        raise requests.exceptions.ConnectionError("nope")

    monkeypatch.setattr(requests, "get", _boom)
    newer, _, _, detail = check_for_update("v1.0.0")
    assert not newer and detail


def test_strings_complete() -> None:
    assert set(STRINGS["en"]) == set(STRINGS["de"])
    assert text("en", "login") == "Login"
    assert text("de", "login") == "Anmelden"
    assert text("xx", "login") == "Anmelden"  # fallback
