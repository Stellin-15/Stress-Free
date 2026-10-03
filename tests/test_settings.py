import json

import pytest

import settings


@pytest.fixture
def store(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "_PATH", str(path))
    return path


def test_missing_file_gives_defaults(store):
    assert settings.load() == settings.DEFAULTS


def test_round_trip(store):
    data = dict(settings.DEFAULTS, pattern="STEALTH", radius=220, auto_pause=False)
    settings.save(data)
    assert settings.load() == data


def test_corrupt_file_gives_defaults(store):
    store.write_text("{not json", encoding="utf-8")
    assert settings.load() == settings.DEFAULTS


def test_wrong_types_and_unknown_keys_are_ignored(store):
    store.write_text(json.dumps({"radius": "huge", "speed": 7, "evil": 1}),
                     encoding="utf-8")
    loaded = settings.load()
    assert loaded["radius"] == settings.DEFAULTS["radius"]
    assert loaded["speed"] == 7
    assert "evil" not in loaded


def test_load_does_not_mutate_defaults(store):
    settings.load()["radius"] = 999
    assert settings.DEFAULTS["radius"] != 999
