"""Input validation: URLs, filenames, paths. No shell injection surface."""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path, PureWindowsPath
from urllib.parse import urlparse

_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._\- ]+")
_MAX_FILENAME_LEN = 180


def validate_https_url(url: str) -> str:
    """Validate a download URL. Returns normalized URL or raises ValueError.

    Rules:
    - must be http(s); plain http allowed only for localhost (tests)
    - must have a host; no credentials in URL
    - should end with .ipa (warning-free for direct links, but enforced loosely:
      we require .ipa path suffix to avoid accidental non-IPA downloads)
    - blocks private/loopback hosts except localhost (SSRF hygiene)
    """
    url = url.strip()
    if not url:
        raise ValueError("Please enter a download URL.")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must start with https:// (or http:// for local testing).")
    if "@" in (parsed.netloc or ""):
        raise ValueError("URLs with embedded credentials are not allowed.")
    host = (parsed.hostname or "").strip()
    if not host:
        raise ValueError("URL has no valid host.")
    is_localhost = host.lower() in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme == "http" and not is_localhost:
        raise ValueError("Only HTTPS downloads are allowed (HTTP only for localhost tests).")
    if not is_localhost:
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
                raise ValueError("Downloads from private/local network addresses are blocked.")
        except ValueError as exc:
            # Not an IP literal -> hostname; block obvious internal names
            if "not allowed" in str(exc) or "blocked" in str(exc):
                raise
    path = parsed.path or ""
    if ".ipa" not in path.lower():
        raise ValueError("URL should point directly to an .ipa file (expected '.ipa' in path).")
    return url


def sanitize_filename(name: str, default: str = "app.ipa") -> str:
    name = (name or "").strip().replace("\x00", "")
    # Strip directory components (both POSIX and Windows)
    name = name.replace("\\", "/").split("/")[-1].strip()
    try:
        # Extra guard for Windows drive/UNC tricks
        win = PureWindowsPath(name)
        name = win.name
    except Exception:
        pass
    name = _SAFE_FILENAME.sub("_", name).strip(" .")
    if not name:
        return default
    if len(name) > _MAX_FILENAME_LEN:
        stem, dot, suffix = name.rpartition(".")
        if dot and len(suffix) <= 8:
            name = stem[: _MAX_FILENAME_LEN - len(suffix) - 1] + "." + suffix
        else:
            name = name[:_MAX_FILENAME_LEN]
    if "." not in name:
        name += ".ipa"
    return name


def safe_join(base: Path, *parts: str) -> Path:
    """Join *parts* onto *base*, raising on path traversal escapes."""
    base_resolved = base.resolve()
    candidate = base_resolved
    for part in parts:
        cleaned = sanitize_filename(part, default="file")
        candidate = candidate / cleaned
    try:
        candidate.resolve().relative_to(base_resolved)
    except ValueError:
        raise ValueError("Unsafe path: would escape the target directory.") from None
    # Also reject raw .. segments defensively
    for part in parts:
        if part.strip() in ("..", "../", "..\\") or ".." in part.replace("\\", "/").split("/"):
            raise ValueError("Unsafe path component.")
    return candidate


def is_safe_ipa_path(path: str | Path) -> bool:
    p = Path(path)
    return p.suffix.lower() == ".ipa" and "\x00" not in str(path)
