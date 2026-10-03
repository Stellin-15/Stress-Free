"""Persist user preferences to %APPDATA%\\OrbitMousePro\\settings.json."""
import json
import os

DEFAULTS = {
    "pattern":         "CIRCLE",
    "radius":          150,
    "speed":           5,
    "auto_pause":      True,
    "tray_hint_shown": False,
}

_DIR  = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"),
                     "OrbitMousePro")
_PATH = os.path.join(_DIR, "settings.json")


def load():
    """Defaults merged with whatever valid keys are on disk."""
    data = dict(DEFAULTS)
    try:
        with open(_PATH, encoding="utf-8") as f:
            saved = json.load(f)
        for key, default in DEFAULTS.items():
            if isinstance(saved.get(key), type(default)):
                data[key] = saved[key]
    except (OSError, ValueError, AttributeError):
        pass  # missing or corrupt file — fall back to defaults
    return data


def save(data):
    try:
        os.makedirs(_DIR, exist_ok=True)
        tmp = _PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, _PATH)  # atomic — no half-written file on crash
    except OSError:
        pass
