# Contributing

Thanks for helping out! Orbit Mouse Pro is a small Windows-only Python app. This page covers what you need to get changes merged.

## Dev setup

```bash
git clone https://github.com/Stellin-15/Stress-Free.git
cd Stress-Free
python -m venv venv
venv\Scripts\activate
pip install -r "Python Version/requirements.txt" -r requirements-dev.txt
python "Python Version/mouse_circle.py"
```

## Before opening a PR

```bash
ruff check .
pytest
```

CI runs both on every pull request, and `main` only accepts changes that pass.

## Workflow

1. Branch off `main` with a descriptive name, such as `fix/tray-crash`, `feat/schedules` or `chore/deps`.
2. Keep each PR to one concern. Explain what changed, why, and how you tested it (the PR template prompts for this).
3. Add a line under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md) for anything users will notice.
4. A real Windows API call can't run in CI, so put the logic behind `winapi` and test it with a fake. See `tests/test_engine.py`.

## Code layout

| File | Role |
|---|---|
| `Python Version/mouse_circle.py` | UI and movement worker |
| `Python Version/winapi.py` | ctypes wrappers: `SendInput`, idle time, sleep blocking, global hotkeys |
| `Python Version/settings.py` | Saved preferences in `%APPDATA%\OrbitMousePro` |
| `Python Version/updater.py` | Update check against `docs/version.json` |
| `docs/` | GitHub Pages website |
| `installer/setup.iss` | Inno Setup installer script |

Releases are covered in [RELEASING.md](RELEASING.md).
