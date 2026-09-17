# Contributing to Deniz Sideloader

Thanks for helping! This guide keeps contributions fast and safe.

## Local development

Requirements: Windows 10/11, Python 3.10+.

```powershell
cd DenizSideloader
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt

# run
python -m app

# simulate a connected iPhone (no hardware needed)
$env:DENIZ_MOCK_DEVICES = "1"; python -m app
```

## Checks (must pass before a PR)

```powershell
python -m pytest tests
python -m ruff check app tests
python -m ruff format --check app tests
python -m mypy app
```

CI (`.github/workflows/ci.yml`) runs all of the above on Windows plus a
packaging smoke test.

## Branching & pull requests

- Branch from `main`: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`.
- One topic per PR; describe what actually works vs. what is a documented
  limitation (see "Honesty rule" below).
- PR template checklist must be filled out.

## Honesty rule (important)

Never add a button that reports success without doing the work. If Apple or
Windows blocks a step:

1. Find the real limitation,
2. build a clean interface abstraction,
3. implement the supported subset,
4. mark the unsupported path clearly in UI + docs.

## Code style

- `ruff` (line length 120) + `ruff format`; `mypy` clean.
- No `print()` in app code — use `app.core.logging.get_logger`.
- Never log secrets; never `shell=True`; validate all paths/URLs.
- Qt code stays in `app/ui/`; logic stays mockable in core services.

## Tests

- New logic needs tests; Apple/iPhone backends must be mocked so CI works
  without hardware (see `tests/test_installation.py`).
- Fixtures: build minimal `.ipa` files on the fly (`tests/conftest.py`) —
  never commit real IPAs or profiles.
