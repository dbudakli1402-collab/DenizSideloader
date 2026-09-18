"""GitHub release update check (iloader has an updater plugin; ours is manual).

Compares the local version against the latest public GitHub release.
Network failures are silent-ish: returns (False, current, '', detail).
"""

from __future__ import annotations

import re

import requests

from app.core.logging import get_logger

log = get_logger("core.update")

OWNER = "dbudakli1402-collab"
REPO = "DenizSideloader"


def _nums(tag: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", tag)[:3])


def check_for_update(current: str, timeout: int = 10) -> tuple[bool, str, str, str]:
    """Return (newer_available, latest_tag, url, notes)."""
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest",
            timeout=timeout,
            headers={"Accept": "application/vnd.github+json"},
        )
        if resp.status_code != 200:
            return False, current, "", f"HTTP {resp.status_code}"
        data = resp.json()
        tag = str(data.get("tag_name", "")).strip()
        url = str(data.get("html_url", ""))
        if not tag:
            return False, current, "", "Keine Versionsinfo."
        if _nums(tag) > _nums(current):
            return True, tag, url, str(data.get("body", ""))[:500]
        return False, tag, url, "Aktuell."
    except requests.exceptions.Timeout:
        return False, current, "", "Zeitüberschreitung."
    except requests.exceptions.ConnectionError:
        return False, current, "", "Keine Verbindung."
    except Exception as exc:
        log.warning("update check failed: %s", exc)
        return False, current, "", "Fehler."
