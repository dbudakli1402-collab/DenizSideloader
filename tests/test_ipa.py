"""IPA detection + metadata tests."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from app.core.errors import IpaInvalidError
from app.ipa.library import IpaLibrary
from app.ipa.parser import hash_file_sha256, parse_ipa


def test_parse_valid_ipa(sample_ipa: Path) -> None:
    info = parse_ipa(sample_ipa)
    assert info.bundle_id == "com.example.demo"
    assert info.app_name == "DemoApp"
    assert info.version == "1.2.3"
    assert info.file_size > 0


def test_parse_missing_plist(tmp_path: Path) -> None:
    bad = tmp_path / "bad.ipa"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("Payload/Empty.txt", b"no app here")
    with pytest.raises(IpaInvalidError):
        parse_ipa(bad)


def test_parse_not_a_zip(tmp_path: Path) -> None:
    bad = tmp_path / "bad.ipa"
    bad.write_bytes(b"definitely not a zip")
    with pytest.raises(IpaInvalidError):
        parse_ipa(bad)


def test_parse_missing_bundle_id(tmp_path: Path) -> None:
    import plistlib

    bad = tmp_path / "noid.ipa"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("Payload/App.app/Info.plist", plistlib.dumps({"CFBundleName": "X"}))
    with pytest.raises(IpaInvalidError):
        parse_ipa(bad)


def test_hash_is_sha256(sample_ipa: Path) -> None:
    h = hash_file_sha256(sample_ipa)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_library_import_list_remove(tmp_path: Path, sample_ipa: Path) -> None:
    lib = IpaLibrary(tmp_path / "lib")
    info = lib.import_file(sample_ipa)
    assert info.bundle_id == "com.example.demo"
    assert len(lib.list()) == 1
    # Persistence round-trip
    lib2 = IpaLibrary(tmp_path / "lib")
    assert len(lib2.list()) == 1
    lib2.remove(lib2.list()[0])
    assert lib2.list() == []


def test_library_rejects_non_ipa(tmp_path: Path) -> None:
    lib = IpaLibrary(tmp_path / "lib")
    txt = tmp_path / "note.txt"
    txt.write_text("hello")
    with pytest.raises(IpaInvalidError):
        lib.import_file(txt)


def test_size_human(sample_ipa: Path) -> None:
    info = parse_ipa(sample_ipa)
    assert "B" in info.size_human or "KB" in info.size_human
