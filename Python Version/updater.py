import urllib.request
import json
import threading
from version import APP_VERSION

UPDATE_URL = "https://stellin-15.github.io/Stress-Free/version.json"
TRUSTED_URL_PREFIX = "https://github.com/"


def check_for_updates(callback):
    """Check for a newer version in the background.

    Calls callback(latest_version: str, download_url: str) on the calling
    thread via tkinter's after() if a newer version is found.
    Fails silently on any network or parse error.
    """
    def _check():
        try:
            with urllib.request.urlopen(UPDATE_URL, timeout=5) as resp:
                data = json.loads(resp.read())

            latest = data.get("version")
            download_url = data.get("download_url", "")

            # Security: reject any download URL not from github.com
            if not latest or not download_url.startswith(TRUSTED_URL_PREFIX):
                return

            if _is_newer(latest, APP_VERSION):
                callback(latest, download_url)
        except Exception:
            pass  # Never block the app for a network check

    threading.Thread(target=_check, daemon=True).start()


def _is_newer(latest: str, current: str) -> bool:
    try:
        return (
            tuple(int(x) for x in latest.split("."))
            > tuple(int(x) for x in current.split("."))
        )
    except ValueError:
        return False
