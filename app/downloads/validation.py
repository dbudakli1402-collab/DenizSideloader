"""Download validation + hashing re-exports (single import surface for tests)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.security.validation import sanitize_filename, validate_https_url

__all__ = ["validate_https_url", "sanitize_filename", "sha256_of_file"]


def sha256_of_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
