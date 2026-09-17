"""URL validation, filename + path security tests."""

from __future__ import annotations

import pytest

from app.security.validation import (
    is_safe_ipa_path,
    safe_join,
    sanitize_filename,
    validate_https_url,
)


def test_valid_https_url() -> None:
    assert validate_https_url("https://example.com/app.ipa").endswith(".ipa")


def test_rejects_non_ipa_path() -> None:
    with pytest.raises(ValueError):
        validate_https_url("https://example.com/index.html")


def test_rejects_plain_http_remote() -> None:
    with pytest.raises(ValueError):
        validate_https_url("http://example.com/app.ipa")


def test_allows_localhost_http() -> None:
    assert validate_https_url("http://localhost:8000/app.ipa")


def test_rejects_credentials_in_url() -> None:
    with pytest.raises(ValueError):
        validate_https_url("https://user:pass@example.com/app.ipa")


def test_rejects_private_ip() -> None:
    with pytest.raises(ValueError):
        validate_https_url("https://192.168.1.10/app.ipa")


def test_rejects_missing_scheme() -> None:
    with pytest.raises(ValueError):
        validate_https_url("example.com/app.ipa")


def test_sanitize_strips_dirs() -> None:
    assert sanitize_filename("../../etc/passwd") == "passwd.ipa"
    assert sanitize_filename("C:\\Windows\\evil.exe") == "evil.exe"


def test_sanitize_empty_default() -> None:
    assert sanitize_filename("") == "app.ipa"


def test_safe_join_ok(tmp_path) -> None:
    p = safe_join(tmp_path, "app.ipa")
    assert str(p).startswith(str(tmp_path.resolve()))


def test_safe_join_blocks_traversal(tmp_path) -> None:
    with pytest.raises(ValueError):
        safe_join(tmp_path, "..")


def test_is_safe_ipa_path() -> None:
    assert is_safe_ipa_path("app.ipa")
    assert not is_safe_ipa_path("app.exe")
    assert not is_safe_ipa_path("app.ipa\x00.exe")
