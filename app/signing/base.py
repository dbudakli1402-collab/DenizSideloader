"""Signing provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.signing.models import SigningIdentity, SigningResult


class SigningProvider(ABC):
    name: str = "base"
    title: str = "Base"

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def list_identities(self) -> list[SigningIdentity]: ...

    @abstractmethod
    def sign(self, input_ipa: str, identity: SigningIdentity, output_ipa: str) -> SigningResult: ...

    @abstractmethod
    def help_text(self) -> str: ...
