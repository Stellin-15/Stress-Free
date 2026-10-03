"""Movement worker (OrbitApp.move_logic) driven against a fake input layer.

No real cursor movement and no window: the worker only touches `winapi`
and plain attributes, so we swap `winapi` for FakeWin and build the app
object without calling Tk's __init__.
"""
import queue
import threading
import time

import pytest

import mouse_circle as mc


class FakeWin:
    """Simulates the Windows input state the worker reads and writes."""

    def __init__(self):
        self.pos = (500, 500)
        self.last_input = time.monotonic()
        self.keys = set()
        self.moves = 0
        self.nudges = 0

    # what the worker calls
    def get_cursor_pos(self):
        return self.pos

    def move_to(self, x, y):
        self.pos = (round(x), round(y))
        self.last_input = time.monotonic()
        self.moves += 1
        return True

    def nudge(self):
        self.last_input = time.monotonic()
        self.nudges += 1
        return True

    def idle_seconds(self):
        return time.monotonic() - self.last_input

    def keys_down(self):
        return frozenset(self.keys)

    def user_input_detected(self, expected, baseline, tolerance=2):
        moved = (abs(self.pos[0] - expected[0]) > tolerance
                 or abs(self.pos[1] - expected[1]) > tolerance)
        return moved or bool(self.keys_down() - baseline)

    # what the "user" does
    def user_moves(self, pos):
        self.pos = pos
        self.last_input = time.monotonic()

    def user_key(self, vk, down=True):
        (self.keys.add if down else self.keys.discard)(vk)
        self.last_input = time.monotonic()


def user_grabs_mouse(fw, app, pos, timeout=2.0):
    """Keep moving the cursor like a real hand until the worker pauses.

    A single teleport can land between the worker's check and its next
    move and be overwritten. Real mouse use is a stream of movements, and
    the next step catches it, so the test models that."""
    end = time.monotonic() + timeout
    x, y = pos
    while time.monotonic() < end:
        fw.user_moves((x, y))
        if app._paused:
            return True
        x += 1
        time.sleep(0.005)
    return False


def wait_until(cond, timeout=2.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.01)
    return False


@pytest.fixture
def engine(monkeypatch):
    fw = FakeWin()
    monkeypatch.setattr(mc, "winapi", fw)
    monkeypatch.setattr(mc, "RESUME_AFTER_SECS", 0.4)
    monkeypatch.setattr(mc, "STEALTH_IDLE_SECS", 0.3)
    monkeypatch.setattr(mc, "AUTO_PAUSE_GRACE", 0.1)

    app = mc.OrbitApp.__new__(mc.OrbitApp)   # skip Tk entirely
    app._radius, app._speed = 100.0, 10.0
    app._pattern, app._auto_pause = "CIRCLE", True
    app._paused = False
    app._events = queue.Queue()

    stop = threading.Event()
    started = []

    def start(pattern="CIRCLE"):
        app._pattern = pattern
        th = threading.Thread(target=app.move_logic, args=(stop,), daemon=True)
        th.start()
        started.append(th)
        return th

    yield app, fw, start
    stop.set()
    for th in started:
        th.join(1)
        assert not th.is_alive(), "worker did not stop"


# ── patterns ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("pattern,box", [
    ("CIRCLE",   (300, 500, 400, 600)),   # centre sits radius left of start
    ("FIGURE-8", (400, 600, 450, 550)),
    ("JITTER",   (400, 600, 400, 600)),
])
def test_patterns_stay_anchored(engine, pattern, box):
    app, fw, start = engine
    app._auto_pause = False
    seen = []
    orig = fw.move_to
    fw.move_to = lambda x, y: (seen.append((x, y)), orig(x, y))[1]
    start(pattern)
    # > 2 full 80-step loops; Windows sleeps tick at ~15 ms, so allow time
    assert wait_until(lambda: len(seen) > 170, timeout=6)
    xmin, xmax, ymin, ymax = box
    assert all(xmin - 1 <= x <= xmax + 1 and ymin - 1 <= y <= ymax + 1
               for x, y in seen), "path drifted outside its anchor box"


def test_circle_starts_at_cursor(engine):
    app, fw, start = engine
    first = []
    orig = fw.move_to
    fw.move_to = lambda x, y: (first.append((x, y)) if not first else None,
                               orig(x, y))[1]
    start("CIRCLE")
    assert wait_until(lambda: first)
    assert first[0] == pytest.approx((500, 500), abs=1)


# ── auto-pause ────────────────────────────────────────────────────────────────

def test_pauses_on_mouse_and_resumes_when_idle(engine):
    app, fw, start = engine
    start()
    assert wait_until(lambda: fw.moves > 10)
    assert user_grabs_mouse(fw, app, (900, 300))

    moves = fw.moves
    time.sleep(0.2)
    assert fw.moves == moves, "moved the cursor while paused"

    assert wait_until(lambda: not app._paused, timeout=2)
    assert wait_until(lambda: fw.moves > moves + 5)
    # re-anchored where the user left the cursor (x drifted a little while
    # "moving"; circle centre sits one radius left of the anchor)
    x, y = fw.pos
    assert 690 <= x <= 1300 and 198 <= y <= 402


def test_keeps_paused_while_user_stays_active(engine):
    app, fw, start = engine
    start()
    assert wait_until(lambda: fw.moves > 10)
    assert user_grabs_mouse(fw, app, (900, 300))
    for i in range(6):                     # user keeps working for ~0.6 s
        fw.user_moves((900 + i, 300))
        time.sleep(0.1)
        assert app._paused


def test_pauses_on_new_key(engine):
    app, fw, start = engine
    start()
    assert wait_until(lambda: fw.moves > 10)
    fw.user_key(0x41)
    assert wait_until(lambda: app._paused)
    fw.user_key(0x41, down=False)
    assert wait_until(lambda: not app._paused, timeout=2)


def test_stale_held_key_does_not_pause(engine):
    # Windows can report a key as held long after release; it must be
    # treated as baseline, not as the user being back.
    app, fw, start = engine
    fw.keys.add(0x56)
    start()
    assert wait_until(lambda: fw.moves > 30)
    assert not app._paused


def test_auto_pause_off_ignores_user(engine):
    app, fw, start = engine
    app._auto_pause = False
    start()
    assert wait_until(lambda: fw.moves > 10)
    fw.user_moves((100, 100))
    time.sleep(0.2)
    assert not app._paused


# ── stealth ───────────────────────────────────────────────────────────────────

def test_stealth_never_moves_cursor_and_nudges_when_idle(engine):
    app, fw, start = engine
    start("STEALTH")
    assert wait_until(lambda: fw.nudges >= 2, timeout=3.5)
    assert fw.moves == 0
    assert fw.pos == (500, 500)


def test_stealth_quiet_while_user_busy(engine):
    app, fw, start = engine
    start("STEALTH")
    time.sleep(0.1)
    nudges = fw.nudges
    for _ in range(12):                    # user active for ~1.2 s
        fw.user_moves((300, 300))
        time.sleep(0.1)
    assert fw.nudges == nudges


def test_leaving_stealth_reanchors_at_cursor(engine):
    app, fw, start = engine
    start("STEALTH")
    time.sleep(0.1)
    fw.user_moves((300, 300))
    app._pattern = "FIGURE-8"
    assert wait_until(lambda: fw.moves > 5)
    x, y = fw.pos
    assert abs(x - 300) <= 101 and abs(y - 300) <= 51


def test_stops_promptly(engine):
    app, fw, start = engine
    app._speed = 1.0                       # slowest = longest sleep per step
    stop = threading.Event()
    th = threading.Thread(target=app.move_logic, args=(stop,), daemon=True)
    th.start()
    assert wait_until(lambda: fw.moves > 2)
    t0 = time.monotonic()
    stop.set()
    th.join(1)
    assert not th.is_alive()
    assert time.monotonic() - t0 < 0.1
