"""Repackage (bundle ID) + profiles/pairing helper tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ipa.parser import parse_ipa
from app.ipa.repackage import set_bundle_id, validate_bundle_id
from app.signing.local_provisioning import list_profiles
from tests.conftest import make_ipa


def test_validate_ok() -> None:
    assert validate_bundle_id("com.example.app") == "com.example.app"


def test_validate_rejects() -> None:
    for bad in ["", "no-dots", "1com.app", "com.app!", "a" * 200]:
        with pytest.raises(ValueError):
            validate_bundle_id(bad)


def test_repackage_changes_bundle(tmp_path: Path) -> None:
    src = make_ipa(tmp_path / "a.ipa", bundle_id="com.example.old")
    out = set_bundle_id(src, "com.example.new")
    assert out.is_file()
    info = parse_ipa(out)
    assert info.bundle_id == "com.example.new"
    assert info.app_name == "DemoApp"
    # original untouched
    assert parse_ipa(src).bundle_id == "com.example.old"


def test_repackage_invalid_ipa(tmp_path: Path) -> None:
    from app.core.errors import IpaInvalidError

    bad = tmp_path / "bad.ipa"
    bad.write_bytes(b"junk")
    with pytest.raises(IpaInvalidError):
        set_bundle_id(bad, "com.example.new")


def test_list_profiles_empty(tmp_path: Path) -> None:
    assert list_profiles([tmp_path / "none"]) == []


def test_list_profiles_found(tmp_path: Path) -> None:
    d = tmp_path / "prov"
    d.mkdir()
    (d / "a.mobileprovision").write_bytes(b"x")
    found = list_profiles([d])
    assert len(found) == 1
    assert found[0].name == "a.mobileprovision"


def test_pairing_lists_without_secrets(tmp_path: Path, monkeypatch) -> None:
    from app.device import pairing as P

    d = tmp_path / "pm"
    d.mkdir()
    (d / "ABC123.plist").write_text("secret-stuff-must-not-leak")
    monkeypatch.setattr(P, "_candidate_dirs", lambda: [d])
    searched, names = P.list_pair_records()
    assert searched == [d]
    assert names == ["ABC123.plist"]
