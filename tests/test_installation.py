"""Installation state-machine tests with mocked services (no iPhone)."""

from __future__ import annotations

from pathlib import Path

from app.device.interface import DeviceService
from app.device.mock_provider import MockDeviceProvider
from app.device.models import ConnectionType, DeviceInfo, TrustState
from app.installation.models import InstallationJob, InstallStep
from app.installation.service import InstallationService
from app.signing.apple_developer import AppleDeveloperSigning
from app.signing.models import SigningKind
from app.signing.service import SigningService
from tests.conftest import make_ipa


def _device_svc() -> DeviceService:
    dev = DeviceInfo(
        udid="UDID-1",
        name="iPhone",
        ios_version="18.0",
        connection=ConnectionType.USB,
        trusted=TrustState.TRUSTED,
    )
    return DeviceService([MockDeviceProvider(simulated=[dev])])


class _NoBackendInstall(InstallationService):
    def _backend_install(self, udid, signed_ipa, on_step, job):  # type: ignore[override]
        return True, "ok"


def test_full_success_with_profile(tmp_path: Path, monkeypatch) -> None:
    ipa = make_ipa(tmp_path / "a.ipa")
    (tmp_path / "a.mobileprovision").write_bytes(b"p")
    svc = _NoBackendInstall(
        devices=_device_svc(),
        signing=SigningService([AppleDeveloperSigning(SigningKind.FREE_DEVELOPER)]),
    )
    steps: list[InstallStep] = []
    job = InstallationJob(ipa_path=str(ipa), udid="UDID-1")
    svc.run(job, on_step=lambda j: steps.append(j.step))
    assert job.step == InstallStep.DONE
    assert job.progress == 1.0
    assert InstallStep.ANALYZE in steps and InstallStep.SIGN in steps


def test_fails_without_device(tmp_path: Path) -> None:
    ipa = make_ipa(tmp_path / "a.ipa")
    svc = _NoBackendInstall(
        devices=DeviceService([MockDeviceProvider(simulated=[])]),
        signing=SigningService([AppleDeveloperSigning()]),
    )
    job = InstallationJob(ipa_path=str(ipa), udid="NOPE")
    svc.run(job)
    assert job.step == InstallStep.FAILED
    assert "iPhone" in job.error_title


def test_fails_with_invalid_ipa(tmp_path: Path) -> None:
    bad = tmp_path / "bad.ipa"
    bad.write_bytes(b"junk")
    svc = _NoBackendInstall(devices=_device_svc(), signing=SigningService([AppleDeveloperSigning()]))
    job = InstallationJob(ipa_path=str(bad), udid="UDID-1")
    svc.run(job)
    assert job.step == InstallStep.FAILED


def test_fails_without_signing_assets(tmp_path: Path) -> None:
    ipa = make_ipa(tmp_path / "a.ipa")  # no .mobileprovision next to it
    svc = _NoBackendInstall(devices=_device_svc(), signing=SigningService([AppleDeveloperSigning()]))
    job = InstallationJob(ipa_path=str(ipa), udid="UDID-1")
    svc.run(job)
    assert job.step == InstallStep.FAILED
    assert "Signing" in job.error_title


def test_honest_backend_limitation(tmp_path: Path) -> None:
    """Real service without pymobiledevice3 must fail honestly, never fake success."""
    ipa = make_ipa(tmp_path / "a.ipa")
    (tmp_path / "a.mobileprovision").write_bytes(b"p")
    svc = InstallationService(devices=_device_svc(), signing=SigningService([AppleDeveloperSigning()]))
    job = InstallationJob(ipa_path=str(ipa), udid="UDID-1")
    try:
        import pymobiledevice3  # noqa: F401

        pytest = None
    except ImportError:
        pytest = True
    svc.run(job)
    if pytest:
        assert job.step == InstallStep.FAILED
        assert "backend" in job.error_detail.lower() or "install" in job.error_title.lower()


def test_untrusted_device_blocked(tmp_path: Path) -> None:
    from app.device.mock_provider import MockDeviceProvider

    ipa = make_ipa(tmp_path / "a.ipa")
    dev = DeviceInfo(
        udid="U2",
        name="iPhone",
        ios_version="18.0",
        connection=ConnectionType.USB,
        trusted=TrustState.UNTRUSTED,
    )
    svc = _NoBackendInstall(
        devices=DeviceService([MockDeviceProvider(simulated=[dev])]),
        signing=SigningService([AppleDeveloperSigning()]),
    )
    job = InstallationJob(ipa_path=str(ipa), udid="U2")
    svc.run(job)
    assert job.step == InstallStep.FAILED
    assert "Trust" in job.error_title
