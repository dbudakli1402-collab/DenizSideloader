"""History store + library categories/rename tests."""

from __future__ import annotations

from pathlib import Path

from app.ipa.library import CATEGORIES, IpaLibrary
from app.storage.history import HistoryEvent, HistoryStore
from tests.conftest import make_ipa


def test_history_record_and_filter(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "h.jsonl")
    store.record("install", "Installiert: Demo", "com.example.demo")
    store.record("download", "Download fertig: demo.ipa")
    store.record("install", "Fehler", status="fail")
    assert len(store.list("all")) == 3
    assert len(store.list("install")) == 2
    assert len(store.list("errors")) == 1
    assert len(store.list("device")) == 0
    # newest first
    assert store.list("all")[0].ts >= store.list("all")[-1].ts


def test_history_persists(tmp_path: Path) -> None:
    p = tmp_path / "h.jsonl"
    HistoryStore(p).record("device", "Gerät verbunden: iPhone")
    assert len(HistoryStore(p).list("all")) == 1


def test_history_unknown_kind_becomes_error(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "h.jsonl")
    ev = HistoryEvent.now("nonsense", "x")
    assert ev.kind == "error"
    store.add(ev)
    assert store.list("all")[0].kind == "error"


def test_history_limit(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "h.jsonl", limit=5)
    for i in range(9):
        store.record("install", f"job {i}")
    assert len(store.list("all")) == 5


def test_default_category(tmp_path: Path) -> None:
    lib = IpaLibrary(tmp_path / "lib")
    info = lib.import_file(make_ipa(tmp_path / "a.ipa"))
    assert info.category == "Alle"
    assert lib.counts_by_category()["Alle"] == 1


def test_set_category(tmp_path: Path) -> None:
    lib = IpaLibrary(tmp_path / "lib")
    info = lib.import_file(make_ipa(tmp_path / "a.ipa"))
    lib.set_category(info, "Spiele")
    counts = lib.counts_by_category()
    assert counts["Spiele"] == 1
    assert counts["Alle"] == 1  # Alle always shows the total
    assert set(counts) == set(CATEGORIES)


def test_set_category_invalid_falls_back(tmp_path: Path) -> None:
    lib = IpaLibrary(tmp_path / "lib")
    info = lib.import_file(make_ipa(tmp_path / "a.ipa"))
    updated = lib.set_category(info, "Cheats")
    assert updated.category == "Alle"


def test_rename(tmp_path: Path) -> None:
    lib = IpaLibrary(tmp_path / "lib")
    info = lib.import_file(make_ipa(tmp_path / "a.ipa"))
    updated = lib.rename(info, "Mein Spiel")
    assert updated.file_name == "Mein Spiel.ipa"
    assert Path(updated.path).is_file()
    assert len(lib.list()) == 1
    # reload keeps rename + category
    lib.set_category(updated, "Tools")
    assert IpaLibrary(tmp_path / "lib").list()[0].file_name == "Mein Spiel.ipa"
