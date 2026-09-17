"""Settings store tests: defaults, validation, no secrets."""

from __future__ import annotations

from pathlib import Path

from app.storage.settings import AppSettings, SettingsStore


def test_defaults_valid() -> None:
    s = AppSettings()
    s.validate()
    assert s.general.theme == "dark"
    assert s.downloads.concurrent == 3


def test_invalid_values_repaired() -> None:
    s = AppSettings()
    s.general.theme = "neon"  # type: ignore[assignment]
    s.downloads.concurrent = 99
    s.validate()
    assert s.general.theme == "dark"
    assert s.downloads.concurrent == 8


def test_roundtrip(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    store.settings.general.language = "de"
    store.settings.signing.apple_id_username = "user@example.com"
    store.save()
    store2 = SettingsStore(tmp_path / "settings.json")
    assert store2.settings.general.language == "de"
    assert store2.settings.signing.apple_id_username == "user@example.com"


def test_no_password_field() -> None:
    fields = set(AppSettings.__dataclass_fields__)
    assert not ({"password", "passwd", "token", "secret"} & fields)
    raw = SettingsStore.__new__(SettingsStore)
    _ = raw  # silence linters about unused


def test_recent_limit(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path / "s.json")
    store.settings.recent_ipas = [f"C:/a{i}.ipa" for i in range(30)]
    store.save()
    reloaded = SettingsStore(tmp_path / "s.json")
    assert len(reloaded.settings.recent_ipas) <= 16
