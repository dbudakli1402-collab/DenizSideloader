"""Secure credential storage via OS keychain (Windows Credential Manager).

- Never stores Apple passwords in JSON / .env / logs / git.
- ``keyring`` picks the Windows Credential Manager backend on Windows.
- Only *tokens/session hints* and usernames are stored; passwords are
  kept in-memory only for the duration of an operation and wiped after.
"""

from __future__ import annotations

SERVICE_NAME = "DenizSideloader"


def store_secret(account: str, secret: str) -> None:
    import keyring

    keyring.set_password(SERVICE_NAME, account, secret)


def load_secret(account: str) -> str | None:
    import keyring

    try:
        return keyring.get_password(SERVICE_NAME, account)
    except Exception:
        return None


def delete_secret(account: str) -> None:
    import keyring

    try:
        keyring.delete_password(SERVICE_NAME, account)
    except Exception:
        pass


def clear_cached_credentials(accounts: list[str] | None = None) -> None:
    """Delete known cached non-password artifacts (usernames, team ids)."""
    for account in accounts or ["apple-id-username", "apple-team-id", "signing-hint"]:
        delete_secret(account)
