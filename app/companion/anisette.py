"""Anisette configuration + local state (iloader-inspired, rewritten).

Anisette data lets Apple tell real Apple devices apart from scripts. iloader
fetches it from community servers (remote v3) and caches machine state in
secure storage. We mirror that structure: server selection (same public
server list), custom URL, HTTPS reachability check, and a local state
directory whose reset is a real operation. The machine-data provisioning
used during full Apple authentication lands here once implemented.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import requests

from app.core.logging import get_logger

log = get_logger("companion.anisette")

# Public community servers (same list iloader offers; plain data, no code).
SERVERS: list[tuple[str, str]] = [
    ("ani.sidestore.io", "SideStore (.io)"),
    ("ani.stikstore.app", "StikStore"),
    ("ani.sidestore.app", "SideStore (.app)"),
    ("ani.sidestore.zip", "SideStore (.zip)"),
    ("ani.846969.xyz", "SideStore (.xyz)"),
    ("ani.neoarz.xyz", "neoarz"),
    ("ani.xu30.top", "SteX"),
    ("anisette.wedotstud.io", "WE. Studio"),
]

DEFAULT_SERVER = "ani.sidestore.io"


def normalize_server(value: str) -> str:
    """Accept host or URL, return https URL without trailing slash."""
    v = (value or "").strip().rstrip("/")
    if not v:
        raise ValueError("Bitte einen Anisette-Server angeben.")
    if "@" in v or " " in v:
        raise ValueError("Ungültiger Servername.")
    if not v.startswith("http://") and not v.startswith("https://"):
        v = "https://" + v
    if v.startswith("http://") and "localhost" not in v and "127.0.0.1" not in v:
        raise ValueError("Nur HTTPS-Server sind erlaubt (außer localhost).")
    return v


def check_reachable(server_url: str, timeout: int = 10) -> tuple[bool, str]:
    """HTTPS reachability probe. Returns (ok, detail). No data is exchanged
    beyond a plain GET; never sends credentials or device data."""
    url = normalize_server(server_url)
    try:
        resp = requests.get(url, timeout=timeout, verify=True)
        return True, f"Erreichbar (HTTP {resp.status_code})."
    except requests.exceptions.SSLError:
        return False, "TLS-Zertifikat ungültig — abgebrochen."
    except requests.exceptions.ConnectionError:
        return False, "Keine Verbindung zum Server."
    except requests.exceptions.Timeout:
        return False, "Zeitüberschreitung."
    except ValueError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"Fehler: {exc}"[:200]


@dataclass
class AnisetteState:
    """Local anisette machine state directory."""

    directory: Path

    def __post_init__(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)

    def has_state(self) -> bool:
        try:
            return any(self.directory.iterdir())
        except Exception:
            return False

    def reset(self) -> bool:
        """Delete cached machine state. Returns True if anything was removed."""
        removed = False
        try:
            for child in list(self.directory.iterdir()):
                if child.is_file() or child.is_symlink():
                    child.unlink()
                    removed = True
                elif child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                    removed = True
        except Exception as exc:
            log.warning("anisette reset failed: %s", exc)
        return removed
