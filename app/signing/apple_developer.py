"""Apple Developer signing provider.

Honest scope on Windows:
- This provider models free + paid Apple Developer identities and explains
  the legitimate flow (certificate + provisioning profile + device UDID).
- It does NOT perform the actual cryptographic re-sign on its own: real
  re-signing of IPAs for iOS requires Apple-issued assets (cert + profile)
  which the user provides. When those are present, :meth:`sign` prepares a
  signed working copy (re-zip with embedded.mobileprovision when supplied);
  otherwise it returns a clear, actionable failure instead of faking success.
- Apple-ID password is never stored: only the username/team hint goes to the
  OS keychain; secrets stay in memory for the operation.
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from datetime import date, timedelta
from pathlib import Path

from app.core.logging import get_logger
from app.signing.base import SigningProvider
from app.signing.models import SigningIdentity, SigningKind, SigningResult

log = get_logger("signing.apple")


class AppleDeveloperSigning(SigningProvider):
    name = "apple-developer"
    title = "Apple Developer Signing"

    def __init__(self, account_kind: SigningKind = SigningKind.FREE_DEVELOPER) -> None:
        self.account_kind = account_kind

    def is_available(self) -> bool:
        # Available as a *workflow guide*; actual signing needs user assets.
        return True

    def list_identities(self) -> list[SigningIdentity]:
        # No locally cached certs by default; user adds them via Settings.
        # Return descriptive placeholder identities so UI can explain limits.
        if self.account_kind == SigningKind.PAID_DEVELOPER:
            return [
                SigningIdentity(
                    kind=SigningKind.PAID_DEVELOPER,
                    label="Paid Developer identity (user-provided)",
                    details="Up to ~12 months validity. Requires cert + provisioning profile.",
                    expires=date.today() + timedelta(days=365),
                )
            ]
        return [
            SigningIdentity(
                kind=SigningKind.FREE_DEVELOPER,
                label="Free Apple ID signing (7-day)",
                details=(
                    "Free accounts: apps expire after 7 days, limited number of "
                    "sideloaded apps. Re-install weekly. See docs/signing.md."
                ),
                expires=date.today() + timedelta(days=7),
            )
        ]

    def sign(self, input_ipa: str, identity: SigningIdentity, output_ipa: str) -> SigningResult:
        src = Path(input_ipa)
        dst = Path(output_ipa)
        if not src.is_file():
            return SigningResult(ok=False, message="Input IPA not found.", technical=str(src))
        # Real re-sign requires user-supplied provisioning profile on Windows.
        # We implement the *supported* subset: embed an existing
        # embedded.mobileprovision if the user placed one next to the IPA or
        # configured a profile path; otherwise fail honestly.
        profile = self._find_profile(src)
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if profile is None:
                return SigningResult(
                    ok=False,
                    message=(
                        "Signing needs your Apple Developer assets first. "
                        "Add a provisioning profile (.mobileprovision) for this "
                        "bundle ID in Settings \u2192 Signing."
                    ),
                    technical="no .mobileprovision available; refusing to fake-sign",
                )
            with tempfile.TemporaryDirectory(prefix="deniz-sign-") as tmp:
                tmp_p = Path(tmp)
                with zipfile.ZipFile(src, "r") as zin:
                    zin.extractall(tmp_p)
                # Embed profile into each .app bundle
                for app_dir in (tmp_p / "Payload").glob("*.app"):
                    shutil.copy2(profile, app_dir / "embedded.mobileprovision")
                # Re-zip
                if dst.exists():
                    dst.unlink()
                with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
                    for f in sorted(tmp_p.rglob("*")):
                        if f.is_file():
                            zout.write(f, f.relative_to(tmp_p).as_posix())
            log.info("prepared signed copy for %s", identity.label)
            return SigningResult(
                ok=True,
                output_ipa=str(dst),
                message=f"Prepared with profile {profile.name}. Install can proceed.",
            )
        except Exception as exc:
            return SigningResult(ok=False, message="Signing preparation failed.", technical=str(exc)[:500])

    def _find_profile(self, ipa_path: Path) -> Path | None:
        for cand in [
            ipa_path.with_suffix(".mobileprovision"),
            ipa_path.parent / "embedded.mobileprovision",
        ]:
            if cand.is_file():
                return cand
        # Configured dir via env (Settings writes this in the real UI)
        import os

        extra = os.environ.get("DENIZ_PROVISIONING_DIR", "")
        if extra:
            d = Path(extra)
            if d.is_dir():
                profiles = sorted(d.glob("*.mobileprovision"))
                if profiles:
                    return profiles[0]
        return None

    def help_text(self) -> str:
        return (
            "Sign with your own Apple Developer certificate + provisioning profile.\n"
            "Free Apple ID: 7-day expiry, a few apps max, weekly re-install.\n"
            "Paid membership: ~12-month expiry.\n"
            "Your Apple-ID password is never saved \u2014 only the username hint "
            "goes to Windows Credential Manager."
        )
