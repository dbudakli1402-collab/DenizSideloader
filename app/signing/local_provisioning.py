"""Local provisioning provider: uses profiles/certs already on disk."""

from __future__ import annotations

import os
from pathlib import Path

from app.signing.apple_developer import AppleDeveloperSigning
from app.signing.base import SigningProvider
from app.signing.models import SigningIdentity, SigningKind, SigningResult


class LocalProvisioning(SigningProvider):
    """Reuses .mobileprovision / .p12 files the user already owns.

    Never generates or forges certificates. Lists what's found; signing
    delegates to the same honest embed flow as AppleDeveloperSigning.
    """

    name = "local-provisioning"
    title = "Local Provisioning Files"

    def __init__(self, search_dirs: list[Path] | None = None) -> None:
        self.search_dirs = search_dirs or []
        self._apple = AppleDeveloperSigning()

    def is_available(self) -> bool:
        return True

    def list_identities(self) -> list[SigningIdentity]:
        found: list[SigningIdentity] = []
        for d in self.search_dirs:
            if not d.is_dir():
                continue
            for prof in sorted(d.glob("*.mobileprovision")):
                found.append(
                    SigningIdentity(
                        kind=SigningKind.LOCAL_PROVISIONING,
                        label=f"Profile: {prof.name}",
                        details=f"Local file: {prof}",
                    )
                )
        return found

    def sign(self, input_ipa: str, identity: SigningIdentity, output_ipa: str) -> SigningResult:
        return self._apple.sign(input_ipa, identity, output_ipa)

    def help_text(self) -> str:
        return (
            "Uses provisioning profiles you already exported from Xcode / "
            "Apple Developer portal. Nothing is generated or bypassed."
        )


def default_search_dirs() -> list[Path]:
    """Candidate folders where users typically keep .mobileprovision files."""
    home = Path.home()
    candidates = [
        Path(os.environ.get("DENIZ_PROVISIONING_DIR", "")) if os.environ.get("DENIZ_PROVISIONING_DIR") else None,
        home / "Downloads" / "DenizSideloader",
        home / "Documents" / "Provisioning Profiles",
    ]
    return [d for d in candidates if d is not None]


def list_profiles(search_dirs: list[Path] | None = None) -> list[Path]:
    """List .mobileprovision files (names/paths only — never parsed for secrets)."""
    found: list[Path] = []
    for d in search_dirs if search_dirs is not None else default_search_dirs():
        try:
            if d.is_dir():
                found.extend(sorted(d.glob("*.mobileprovision")))
        except Exception:
            continue
    return found
