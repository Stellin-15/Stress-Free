"""Thin ctypes wrappers over the Win32 calls Orbit needs.

Why not pyautogui: it moves the cursor with SetCursorPos, which does NOT
reset the Windows idle timer (GetLastInputInfo) — the thing Teams, Slack,
the screensaver and sleep all read. SendInput injects real input events,
so every move here counts as activity.
"""
import ctypes
import threading
from ctypes import wintypes as w

user32   = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# ── SendInput structures ──────────────────────────────────────────────────────

ULONG_PTR = ctypes.c_size_t

INPUT_MOUSE    = 0
MOUSEEVENTF_MOVE        = 0x0001
MOUSEEVENTF_VIRTUALDESK = 0x4000
MOUSEEVENTF_ABSOLUTE    = 0x8000


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", w.LONG), ("dy", w.LONG), ("mouseData", w.DWORD),
                ("dwFlags", w.DWORD), ("time", w.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", w.WORD), ("wScan", w.WORD), ("dwFlags", w.DWORD),
                ("time", w.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", w.DWORD), ("wParamL", w.WORD), ("wParamH", w.WORD)]


class _INPUTUNION(ctypes.Union):
    # All three members so sizeof(INPUT) matches what SendInput expects
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", w.DWORD), ("u", _INPUTUNION)]


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", w.UINT), ("dwTime", w.DWORD)]


user32.SendInput.argtypes = [w.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype  = w.UINT
user32.GetCursorPos.argtypes = [ctypes.POINTER(w.POINT)]
user32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype  = ctypes.c_short
user32.RegisterHotKey.argtypes   = [w.HWND, ctypes.c_int, w.UINT, w.UINT]
user32.UnregisterHotKey.argtypes = [w.HWND, ctypes.c_int]
user32.GetMessageW.argtypes = [ctypes.POINTER(w.MSG), w.HWND, w.UINT, w.UINT]
user32.PostThreadMessageW.argtypes = [w.DWORD, w.UINT, w.WPARAM, w.LPARAM]
kernel32.GetTickCount.restype = w.DWORD
kernel32.SetThreadExecutionState.argtypes = [w.DWORD]
kernel32.SetThreadExecutionState.restype  = w.DWORD

SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79


def _send_mouse(dx, dy, flags):
    inp = INPUT(type=INPUT_MOUSE)
    inp.u.mi = MOUSEINPUT(dx, dy, 0, flags, 0, 0)
    # Returns 0 when blocked, e.g. by UIPI while an elevated window is focused
    return user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT)) == 1


# ── Cursor & activity ─────────────────────────────────────────────────────────

def get_cursor_pos():
    pt = w.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def move_to(x, y):
    """Move the cursor to screen pixel (x, y) with a real input event."""
    vx = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    vy = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    vw = max(2, user32.GetSystemMetrics(SM_CXVIRTUALSCREEN))
    vh = max(2, user32.GetSystemMetrics(SM_CYVIRTUALSCREEN))
    # Absolute coords are normalised 0..65535 across the whole virtual desktop
    nx = round((x - vx) * 65535 / (vw - 1))
    ny = round((y - vy) * 65535 / (vh - 1))
    nx = min(65535, max(0, nx))
    ny = min(65535, max(0, ny))
    return _send_mouse(nx, ny, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
                       | MOUSEEVENTF_VIRTUALDESK)


def nudge():
    """Zero-distance mouse move: resets the idle timer, cursor stays put."""
    return _send_mouse(0, 0, MOUSEEVENTF_MOVE)


def idle_seconds():
    """Seconds since the last input event (ours or the user's)."""
    info = LASTINPUTINFO(cbSize=ctypes.sizeof(LASTINPUTINFO))
    if not user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0
    # DWORD subtraction wraps correctly after the 49.7-day tick rollover
    return ((kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000.0


def keys_down():
    """Virtual-key codes (incl. mouse buttons) Windows reports as held."""
    return frozenset(vk for vk in range(0x01, 0xFF)
                     if user32.GetAsyncKeyState(vk) & 0x8000)


def user_input_detected(expected_pos, baseline_keys, tolerance=2):
    """True if the user moved the cursor away from where we put it, or is
    holding a key / mouse button that wasn't already down in baseline_keys.

    The baseline matters: Windows can report a key as held long after it was
    released (a key-up lost to UAC or another app's hook), which would
    otherwise look like permanent user activity."""
    x, y = get_cursor_pos()
    if abs(x - expected_pos[0]) > tolerance or abs(y - expected_pos[1]) > tolerance:
        return True
    return bool(keys_down() - baseline_keys)


# ── Sleep prevention ──────────────────────────────────────────────────────────

ES_CONTINUOUS       = 0x80000000
ES_SYSTEM_REQUIRED  = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


def keep_awake(enabled):
    """Block system sleep and display-off. The flag is held by the calling
    thread, so call this from the main (UI) thread."""
    flags = ES_CONTINUOUS
    if enabled:
        flags |= ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    kernel32.SetThreadExecutionState(flags)


# ── Global hotkeys ────────────────────────────────────────────────────────────

MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x0001, 0x0002, 0x4000
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012


class HotkeyListener(threading.Thread):
    """Registers system-wide hotkeys and calls on_hotkey(id) from this
    background thread. RegisterHotKey binds to the registering thread's
    message queue, so registration and the message loop share a thread."""

    def __init__(self, bindings, on_hotkey):
        super().__init__(daemon=True)
        self._bindings  = bindings      # {id: (modifiers, virtual_key)}
        self._on_hotkey = on_hotkey
        self._tid       = None
        self.failed     = []            # ids another app already owns

    def run(self):
        self._tid = kernel32.GetCurrentThreadId()
        registered = []
        for hk_id, (mods, vk) in self._bindings.items():
            if user32.RegisterHotKey(None, hk_id, mods | MOD_NOREPEAT, vk):
                registered.append(hk_id)
            else:
                self.failed.append(hk_id)
        try:
            msg = w.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY:
                    self._on_hotkey(msg.wParam)
        finally:
            for hk_id in registered:
                user32.UnregisterHotKey(None, hk_id)

    def stop(self):
        if self._tid:
            user32.PostThreadMessageW(self._tid, WM_QUIT, 0, 0)
