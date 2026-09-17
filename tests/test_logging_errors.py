"""Logging redaction + error-model tests."""

from __future__ import annotations

from app.core.errors import DeviceNotFoundError
from app.core.logging import redact_message, sanitize_for_log


def test_redacts_password() -> None:
    assert "secret123" not in redact_message("password: secret123 login")
    assert "***REDACTED***" in redact_message("password: secret123 login")


def test_redacts_bearer() -> None:
    assert "abcDEF123" not in redact_message("Authorization: Bearer abcDEF123")


def test_redacts_private_key() -> None:
    assert "BEGIN" not in redact_message("-----BEGIN PRIVATE KEY----- xyz")
    assert "BEGIN" not in redact_message("-----BEGIN RSA PRIVATE KEY----- xyz")


def test_sanitize_dict() -> None:
    out = sanitize_for_log({"username": "deniz", "password": "hunter2", "token": "abc"})
    assert out["username"] == "deniz"
    assert out["password"] == "***REDACTED***"
    assert out["token"] == "***REDACTED***"


def test_device_error_user_text() -> None:
    err = DeviceNotFoundError()
    text = err.user_text()
    assert "locked" in text
    assert "Trust" in text
    assert "0x800" not in text
