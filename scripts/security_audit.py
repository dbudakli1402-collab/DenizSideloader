"""Repo security audit: blocked files + password assignments + shell=True."""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

blocked_ext = {".pem", ".key", ".p12", ".pfx", ".mobileprovision"}
blocked_names = {".env", "credentials.json", "secrets.json"}
failures: list[str] = []

EXCLUDED_DIRS = {".git", "__pycache__", "build", "release", "dist", ".venv", "venv"}

for p in ROOT.rglob("*"):
    if not p.is_file() or EXCLUDED_DIRS & set(p.parts):
        continue
    if p.suffix.lower() in blocked_ext or p.name in blocked_names:
        failures.append(f"blocked file present: {p.relative_to(ROOT)}")

pat = re.compile(r'password\s*=\s*["\'][^"\']+["\']')
shell_pat = re.compile(r"shell\s*=\s*True")
for p in list((ROOT / "app").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py")):
    if p.name == "security_audit.py":
        continue  # self-scan would match its own patterns
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if pat.search(line) and "REDACTED" not in line:
            failures.append(f"password assignment: {p.relative_to(ROOT)}:{i}")
        if shell_pat.search(line):
            failures.append(f"shell=True: {p.relative_to(ROOT)}:{i}")

if failures:
    print("AUDIT FAILURES:")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("security audit clean: no blocked files, no password assignments, no shell=True")
