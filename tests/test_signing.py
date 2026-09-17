"""Signing state tests: honest failure without assets, success with profile."""

from __future__ import annotations

from pathlib import Path

from app.signing.apple_developer import AppleDeveloperSigning
from app.signing.local_provisioning import LocalProvisioning
from app.signing.models import SigningKind
from app.signing.service import SigningService
from tests.conftest import make_ipa


def test_identities_listed() -> None:
    svc = SigningService([AppleDeveloperSigning(SigningKind.FREE_DEVELOPER)])
    idents = svc.all_identities()
    assert len(idents) == 1
    assert idents[0][1].kind == SigningKind.FREE_DEVELOPER
    assert "7" in idents[0][1].details


def test_sign_fails_without_profile(tmp_path: Path) -> None:
    ipa = make_ipa(tmp_path / "a.ipa")
    prov = AppleDeveloperSigning()
    ident = prov.list_identities()[0]
    res = prov.sign(str(ipa), ident, str(tmp_path / "out.ipa"))
    assert not res.ok
    assert "provisioning" in res.message.lower()


def test_sign_succeeds_with_profile(tmp_path: Path, monkeypatch) -> None:
    ipa = make_ipa(tmp_path / "a.ipa")
    (tmp_path / "a.mobileprovision").write_bytes(b"fake-profile")
    prov = AppleDeveloperSigning()
    ident = prov.list_identities()[0]
    res = prov.sign(str(ipa), ident, str(tmp_path / "out.ipa"))
    assert res.ok
    assert Path(tmp_path / "out.ipa").is_file()
    # Profile embedded?
    import zipfile

    with zipfile.ZipFile(tmp_path / "out.ipa") as zf:
        assert any(n.endswith("embedded.mobileprovision") for n in zf.namelist())


def test_local_provisioning_lists_dir(tmp_path: Path) -> None:
    d = tmp_path / "prov"
    d.mkdir()
    (d / "one.mobileprovision").write_bytes(b"x")
    lp = LocalProvisioning([d])
    assert len(lp.list_identities()) == 1


def test_sign_missing_input(tmp_path: Path) -> None:
    prov = AppleDeveloperSigning()
    ident = prov.list_identities()[0]
    res = prov.sign(str(tmp_path / "nope.ipa"), ident, str(tmp_path / "o.ipa"))
    assert not res.ok
