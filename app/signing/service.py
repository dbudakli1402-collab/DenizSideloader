"""Signing service facade (mockable)."""

from __future__ import annotations

from app.signing.apple_developer import AppleDeveloperSigning
from app.signing.base import SigningProvider
from app.signing.local_provisioning import LocalProvisioning
from app.signing.models import SigningIdentity, SigningResult


class SigningService:
    def __init__(self, providers: list[SigningProvider] | None = None) -> None:
        self._providers = providers or [AppleDeveloperSigning(), LocalProvisioning()]

    @property
    def providers(self) -> list[SigningProvider]:
        return list(self._providers)

    def all_identities(self) -> list[tuple[SigningProvider, SigningIdentity]]:
        out: list[tuple[SigningProvider, SigningIdentity]] = []
        for p in self._providers:
            try:
                if p.is_available():
                    for ident in p.list_identities():
                        out.append((p, ident))
            except Exception:
                continue
        return out

    def sign(
        self, provider: SigningProvider, input_ipa: str, identity: SigningIdentity, output_ipa: str
    ) -> SigningResult:
        return provider.sign(input_ipa, identity, output_ipa)
