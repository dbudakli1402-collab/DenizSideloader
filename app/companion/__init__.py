"""Companion workflows (AltServer-style, iloader-inspired, MIT-attributed).

Covers: Apple-ID session preparation (password in-memory only, never stored),
Anisette server configuration + local state, official installer definitions
(SideStore / LiveContainer from their GitHub releases), and pairing-file
placement into installed companion apps.

Flows adapted from iloader (MIT, see docs/attribution.md). Rewritten in
Python for this codebase; branding/names are our own.
"""

from __future__ import annotations
