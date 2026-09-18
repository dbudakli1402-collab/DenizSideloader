"""Companion tests: session, anisette, installers, pairing."""

from __future__ import annotations

from pathlib import Path

from app.companion.anisette import SERVERS, AnisetteState, normalize_server
from app.companion.models import INSTALLERS, AppleSession


def test_session_never_persists_password() -> None:
    s = AppleSession()
    s.begin("User@Example.com", "secret123")
    assert s.email == "user@example.com"
    assert s.has_password()
    assert "secret123" not in repr(s)
    pwd = s.take_password()
    assert pwd == "secret123"
    assert not s.has_password()  # wiped after one take
    s.begin("a@b.c", "x")
    s.mark_ready()
    assert s.ready and not s.has_password()
    s.invalidate()
    assert s.email == "" and not s.ready


def test_normalize_server() -> None:
    assert normalize_server("ani.sidestore.io") == "https://ani.sidestore.io"
    assert normalize_server("https://ani.sidestore.io/") == "https://ani.sidestore.io"
    assert normalize_server("http://localhost:8080") == "http://localhost:8080"
    import pytest

    for bad in ["", "http://ani.sidestore.io", "user@host", "has space"]:
        with pytest.raises(ValueError):
            normalize_server(bad)


def test_server_list_matches_iloader_defaults() -> None:
    hosts = [h for h, _ in SERVERS]
    assert "ani.sidestore.io" in hosts
    assert len(hosts) >= 8


def test_anisette_state_reset(tmp_path: Path) -> None:
    st = AnisetteState(tmp_path / "ani")
    assert not st.has_state()
    (tmp_path / "ani" / "machine.dat").write_bytes(b"machine-data")
    assert st.has_state()
    assert st.reset() is True
    assert not st.has_state()
    assert st.reset() is False


def test_installer_defs_official_urls() -> None:
    by_key = {d.key: d for d in INSTALLERS}
    assert set(by_key) == {
        "sidestore-stable",
        "sidestore-nightly",
        "livecontainer-stable",
        "livecontainer-nightly",
    }
    assert "github.com/SideStore/SideStore" in by_key["sidestore-stable"].url
    assert "github.com/LiveContainer/LiveContainer" in by_key["livecontainer-stable"].url
    for d in INSTALLERS:
        assert d.url.startswith("https://github.com/")
        assert d.filename.endswith(".ipa")
        assert d.bundle_id


def test_pairing_delete_empty(tmp_path: Path, monkeypatch) -> None:
    from app.device import pairing as P

    d = tmp_path / "empty"
    d.mkdir()
    (d / "ABC123.plist").write_text("dummy-record")
    monkeypatch.setattr(P, "_candidate_dirs", lambda: [d])

    class _FakeOS:
        pair_record_path = tmp_path / "nocache"

    import pymobiledevice3.pair_records as _pr

    monkeypatch.setattr(_pr, "OSUTILS", _FakeOS())
    searched, names = P.list_pair_records()
    assert searched == [d]
    assert names == ["ABC123.plist"]
    assert P.delete_stored() == 1
    assert P.list_pair_records()[1] == []


def test_installer_fail_closed_without_device(tmp_path: Path) -> None:
    """CompanionInstaller with unreachable backend must fail honestly."""
    from app.companion.installers import place_pairing_record

    ok, msg = place_pairing_record("NOPE-UDID", "com.SideStore.SideStore", "pairing.mobiledevicepairing")
    assert ok is False
    assert msg
