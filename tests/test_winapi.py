"""Smoke tests for the ctypes layer. They only read state and never move the
cursor or send input, so they're safe on CI runners and developer machines."""
import ctypes
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows only")

import winapi  # noqa: E402


def test_input_struct_matches_win32_size():
    # SendInput rejects the call if cbSize is wrong: 40 bytes on 64-bit,
    # 28 on 32-bit
    expected = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28
    assert ctypes.sizeof(winapi.INPUT) == expected


def test_idle_seconds_is_non_negative():
    assert winapi.idle_seconds() >= 0


def test_keys_down_returns_frozenset():
    assert isinstance(winapi.keys_down(), frozenset)


def test_cursor_pos_is_int_pair():
    x, y = winapi.get_cursor_pos()
    assert isinstance(x, int) and isinstance(y, int)
