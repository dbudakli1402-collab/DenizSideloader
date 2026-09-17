"""Shared fixtures: builds a minimal valid .ipa in tmp_path."""

from __future__ import annotations

import plistlib
import zipfile
from pathlib import Path

import pytest


def make_ipa(
    path: Path,
    bundle_id: str = "com.example.demo",
    app_name: str = "DemoApp",
    version: str = "1.2.3",
) -> Path:
    info = {
        "CFBundleIdentifier": bundle_id,
        "CFBundleDisplayName": app_name,
        "CFBundleName": app_name,
        "CFBundleShortVersionString": version,
        "CFBundleVersion": "42",
        "MinimumOSVersion": "17.0",
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"Payload/{app_name}.app/Info.plist", plistlib.dumps(info))
        zf.writestr(f"Payload/{app_name}.app/{app_name}", b"fake-binary")
        zf.writestr(f"Payload/{app_name}.app/AppIcon60x60.png", b"\x89PNG-fake")
    return path


@pytest.fixture
def sample_ipa(tmp_path: Path) -> Path:
    return make_ipa(tmp_path / "demo.ipa")
