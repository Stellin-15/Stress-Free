import json
import re
from pathlib import Path

import pytest

from updater import TRUSTED_URL_PREFIX, _is_newer
from version import APP_VERSION

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("latest,current,expected", [
    ("1.2.0", "1.1.0", True),
    ("1.10.0", "1.9.0", True),    # numeric, not string, comparison
    ("2.0.0", "1.99.99", True),
    ("1.1.0", "1.1.0", False),
    ("1.0.9", "1.1.0", False),
    ("garbage", "1.1.0", False),
])
def test_is_newer(latest, current, expected):
    assert _is_newer(latest, current) is expected


def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", APP_VERSION)


def test_published_version_json_is_valid():
    """docs/version.json is what every installed copy polls for updates."""
    data = json.loads((ROOT / "docs" / "version.json").read_text(encoding="utf-8"))
    assert re.fullmatch(r"\d+\.\d+\.\d+", data["version"])
    assert data["download_url"].startswith(TRUSTED_URL_PREFIX)
    assert f"/v{data['version']}/" in data["download_url"]
    # Never advertise a version newer than the code in this commit
    assert not _is_newer(data["version"], APP_VERSION)
