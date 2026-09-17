"""Structured logging with secret redaction.

Never log Apple passwords, tokens, private keys or session credentials.
Use :func:`redact` helpers and pass ``extra={"redacted": True}`` implicitly
by routing all messages through :class:`RedactingFilter`.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

REDACT_PATTERNS = [
    re.compile(r"(?i)(password\s*[:=]\s*)(['\"]?)([^\s'\",;]+)(\2)"),
    re.compile(r"(?i)(passwd\s*[:=]\s*)(\S+)"),
    re.compile(r"(?i)(token\s*[:=]\s*)(['\"]?)([^\s'\",;]+)(\2)"),
    re.compile(r"(?i)(bearer\s+)([A-Za-z0-9\-._~+/=]+)"),
    re.compile(r"(?i)(apple[-_ ]?id\s*[:=]\s*\S+\s+password\s*[:=]\s*)\S+"),
    re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"),
]

REDACT_REPLACEMENT = r"\1\2***REDACTED***\4"


def redact_message(message: str) -> str:
    redacted = message
    for i, pat in enumerate(REDACT_PATTERNS):
        if i == 4:
            redacted = pat.sub(r"\1***REDACTED***", redacted)
        elif i == 5:
            redacted = redacted.replace("-----BEGIN RSA PRIVATE KEY-----", "***REDACTED PRIVATE KEY***").replace(
                "-----BEGIN PRIVATE KEY-----", "***REDACTED PRIVATE KEY***"
            )
        else:
            try:
                redacted = pat.sub(REDACT_REPLACEMENT, redacted)
            except Exception:
                continue
    # Bearer special-case (2 groups)
    redacted = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9\-._~+/=]+", r"\1***REDACTED***", redacted)
    return redacted


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact_message(record.msg)
            if record.args:
                # Redact %s-style args conservatively: stringify check
                args = record.args
                if isinstance(args, dict):
                    record.args = {k: ("***REDACTED***" if _looks_secret_key(k) else v) for k, v in args.items()}
                elif isinstance(args, (tuple, list)):
                    record.args = tuple("***REDACTED***" if isinstance(a, str) and len(a) > 64 else a for a in args)
        except Exception:
            pass
        return True


def _looks_secret_key(key: str) -> bool:
    k = key.lower()
    return any(token in k for token in ("password", "passwd", "token", "secret", "private_key", "session"))


_CONFIGURED = False


def setup_logging(log_dir: Path, level: int = logging.INFO) -> logging.Logger:
    """Configure root-ish app logger writing to rotating file + stderr."""
    global _CONFIGURED
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("deniz")
    logger.setLevel(level)
    logger.propagate = False
    if not _CONFIGURED:
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh = logging.FileHandler(log_dir / "deniz-sideloader.log", encoding="utf-8")
        fh.setFormatter(fmt)
        fh.addFilter(RedactingFilter())
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        sh.addFilter(RedactingFilter())
        logger.addHandler(fh)
        logger.addHandler(sh)
        _CONFIGURED = True
    return logger


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"deniz.{name}")
    # Ensure redaction even if setup_logging wasn't called (e.g. tests)
    if not any(isinstance(f, RedactingFilter) for f in logger.filters):
        logger.addFilter(RedactingFilter())
    return logger


def sanitize_for_log(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *data* with secret values masked."""
    out: dict[str, Any] = {}
    for k, v in data.items():
        if _looks_secret_key(k):
            out[k] = "***REDACTED***"
        else:
            out[k] = v
    return out
