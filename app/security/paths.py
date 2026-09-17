"""Secure temp-file helpers."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def secure_temp_dir(prefix: str = "deniz-") -> Iterator[Path]:
    """Yield a temp dir with restrictive permissions; always cleaned up."""
    tmp = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        try:
            os.chmod(tmp, 0o700)
        except Exception:
            pass
        yield tmp
    finally:
        import shutil

        shutil.rmtree(tmp, ignore_errors=True)


def secure_unlink(path: Path) -> None:
    try:
        if path.is_file():
            path.unlink()
    except Exception:
        pass
