# Orbit Mouse Pro — Gaps & Upgrade Plan

Audit of the repo as of v1.1.0 (commit `0e2426d`). Each gap lists the location, what goes wrong, and the fix.

Severity: 🔴 broken / misleading · 🟠 real UX or reliability problem · 🟡 polish / hygiene

## Progress

| Item | Status |
|---|---|
| 1.1 Real input + sleep prevention | ✅ v1.2: `SendInput` + `SetThreadExecutionState` + live idle readout. Verified: `SetCursorPos` does **not** reset the idle timer, `SendInput` does |
| 1.2 Drift · 1.3 Double-run · 1.4 Thread safety | ✅ v1.1.1 |
| 1.5 Auto-pause on user input | ✅ v1.2 (mouse displacement + held keys; resumes after 15 s idle) |
| 1.6 Global hotkeys | ✅ v1.2 (`Ctrl+Alt+H` hide/show, `Ctrl+Alt+O` start/stop) |
| 1.7 ESC while idle · X → tray · update banner clipping · settings persistence | ✅ (`_is_newer` pre-release tags and topmost toggle still open) |
| 2.1 Missing dep · 2.2 exe icon · 2.3 UPX off · 2.4 runtime logo write | ✅ v1.1.1 (signing still open) |
| 3. RELEASING.md un-ignored | ✅ v1.1.1 (LICENSE still open) |
| 5.3 Stealth mode · 5.5 Settings saved · 5.17 Real tray emblem | ✅ v1.2 |
| Website copy for v1.2 features | ⏳ update at release time |

---

## 1. Core functionality gaps

### 🔴 1.1 It may not actually keep you "Active"
`pyautogui.moveTo` on Windows calls `SetCursorPos` (`venv/.../_pyautogui_win.py:369`). `SetCursorPos` moves the cursor but does not inject a real input event. Windows' idle timer (`GetLastInputInfo`) is what Teams, Slack, the screensaver and sleep all read, and `SetCursorPos` often doesn't reset it. That means the app can look busy while the PC still goes idle. This is the product's whole promise, so it's the first thing to verify.

**Fix:**
- Send moves through `SendInput` with `MOUSEEVENTF_MOVE` (ctypes, or `pynput`). These are real input events and they reset the idle timer.
- Also call `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)` while running. This is the official way to block sleep and screen-off, and it needs no mouse movement at all.
- Add a "status: idle for Xs" readout from `GetLastInputInfo` in the UI so users can see that it works.

### 🔴 1.2 Circle and Jitter drift across the screen
`mouse_circle.py:543` re-reads `pyautogui.position()` as the center at the start of every 80-step loop.
- **Circle:** the path starts at `cx + radius` and ends near there, so each loop's new center is about `radius` px to the right. The cursor walks right until it hits the screen edge.
- **Jitter:** each loop re-centers on the last random point, so it turns into a random walk that ends up stuck in a corner.

**Fix:** capture the anchor point once in `start_movement` and orbit around it. For Circle, start at the cursor by offsetting the center (`anchor - (radius, 0)`) so there's no jump on the first frame.

### 🔴 1.3 Stop→Start quickly runs two copies of everything
`start_movement` (`:573`) starts a new worker thread plus new `after()` loops for the dot, timer and productivity. `stop_movement` only flips `is_running`. If you press Start again before the old loops wake up (within 25 ms to 4 s), the old loops see `is_running == True` and keep going. The result is two threads fighting over the mouse, the dot spinning at double speed, and the timer ticking twice.

**Fix:** use a run generation counter (`self._run_id += 1`) and have each loop exit when its captured id is stale. Or keep the `after` ids and `after_cancel` them, and use a `threading.Event` for the worker.

### 🟠 1.4 Tkinter is accessed from a background thread
`move_logic` (`:544–546`) calls `radius_slider.get()`, `speed_slider.get()` and `pattern_var.get()` from the worker thread. Tkinter isn't thread-safe, so this can crash rarely and randomly, especially in the frozen exe.

**Fix:** mirror the values into plain attributes (`self._radius`, etc.) from the slider `command` callbacks, and have the worker read only those.

### 🟠 1.5 It hijacks your mouse, and there's no "user is back" detection
While running you can't use the mouse at all. The only way out is ESC, which needs window focus, or the tray. `FAILSAFE = False` (`:14`) also removes the corner escape hatch.

**Fix:** auto-pause when real user input is detected. Compare the cursor position you set with the actual position, or watch `GetLastInputInfo` for input you didn't generate. Resume after N seconds idle. This one feature changes the app from a toy into something people keep running all day.

### 🟠 1.6 The Boss Key isn't global
`self.bind('<Control-h>')` (`:83`) only fires when the Orbit window has focus. Once the window is hidden it can't get focus, so the same key can't bring it back, and the README/site claim "toggle" behaviour.

**Fix:** register a system-wide hotkey (`RegisterHotKey` via ctypes, or `keyboard`/`pynput`). Do the same for a global Stop hotkey.

### 🟡 1.7 Smaller logic issues
- ESC while idle still flashes "ABORTED" (`stop_movement` has no `if not self.is_running: return`).
- The window is forced `-topmost` (`:661`) with no toggle.
- Closing with **X** quits the app (`:84`). For a tray app, users expect X to minimize to the tray.
- The update banner is `pack()`ed at the bottom of a fixed, non-resizable 440×690 window (`:645`), so it can be clipped and never seen.
- `_is_newer` (`updater.py:37`) returns False for tags like `1.2.0-beta` or `v1.2.0`.
- No settings persistence. Pattern, radius and speed reset on every launch.

---

## 2. Packaging & release gaps

### 🔴 2.1 Missing dependency
`pywinstyles` is imported (`mouse_circle.py:12`) but isn't in `requirements.txt`, so a fresh clone that follows the README crashes on launch.

### 🟠 2.2 The exe has no icon
`OrbitMousePro.spec` has no `icon='orbit.ico'` in `EXE(...)`. The installer has the icon but the exe itself (taskbar, Explorer) shows the default Python icon.

### 🟠 2.3 Antivirus false positives are very likely
UPX compression (`upx=True`), an unsigned binary, PyInstaller onefile and an app that moves the mouse together look a lot like malware to Defender and other AV heuristics.

**Fix:** set `upx=False`, consider `--onedir` (faster startup, fewer flags), submit builds to Microsoft's false-positive portal, and look into free signing (SignPath.io offers free code signing for OSS) to stop SmartScreen warnings.

### 🟠 2.4 The app writes into its own source tree on every launch
`_apply_icon` (`:108–113`) saves `docs/logo.png` on every start. That belongs in a build script, not at runtime. In the frozen exe it writes into the temp `_MEIPASS` folder, and from source it silently changes git-tracked files.

### 🟡 2.5 The version is hardcoded in 7 places
`version.py`, `setup.iss` (×2), `version.json`, and `index.html` (×4: download URL, badge, mockup, footer). That makes a bad release easy.

**Fix:** keep `version.py` as the single source of truth and have a script/CI step stamp the rest. The website can `fetch('version.json')` and fill in the version and download link at runtime.

### 🟡 2.6 No CI / automated release
Builds are manual on your machine.

**Fix:** a GitHub Actions workflow on tag `v*` that runs `pip install` → PyInstaller → Inno Setup (`choco install innosetup`) → uploads to a GitHub Release → updates `docs/version.json`. Add a SHA-256 to `version.json` and have the updater show or verify it.

### 🟡 2.7 Installer
- `PrivilegesRequired=admin` with the comment "so the app can move the mouse globally" (`setup.iss:20–21`) is wrong. Mouse movement needs no admin, and the installer's elevation doesn't carry over to the app anyway. Use `PrivilegesRequired=lowest` plus `PrivilegesRequiredOverridesAllowed=dialog`, which installs per-user with no UAC prompt and is one less scary step.
- No `AppId` GUID, which upgrades and uninstall tracking need to work reliably.

---

## 3. Repo hygiene gaps

- 🔴 `README.md` and `RELEASING.md` are listed in `.gitignore` (`:14–15`). README is tracked anyway because it was committed earlier, but **RELEASING.md isn't in the repo**, so the README's link to it is a 404.
- 🟡 Naming is inconsistent: repo "Stress-Free", app "Orbit Mouse Pro", entry file `mouse_circle.py`, folder `Python Version/` (the space breaks a lot of tooling). Suggested: `src/orbit/` with `main.py`.
- 🟡 Everything lives in one 660-line class. Split it into `engine.py` (movement + idle detection, no UI), `ui/`, `tray.py`, `settings.py`. The engine then becomes unit-testable.
- 🟡 No tests, no linter, no `LICENSE` file (the site says "Open Source" but there's no license, which legally means all rights reserved), no `CHANGELOG.md`, no screenshot in the README.
- 🟡 `docs/assets/` exists locally but is empty and untracked.

---

## 4. Website gaps (`docs/`)

- 🟠 **No real screenshot or GIF of the app.** The CSS mockup is nice, but a 5-second looping GIF/WebM of the real app with the cursor moving converts far better.
- 🟠 **No Open Graph / Twitter card tags.** Shared links on Discord, Slack, X or LinkedIn show up as plain text. Add `og:title`, `og:description`, `og:image` (1200×630 banner) and `twitter:card`.
- 🟠 **No `@media` queries in `style.css` at all.** The grids use `auto-fit` so they wrap, but the nav, hero `h1` (Orbitron) and footer aren't tuned for phones. Test at 375px.
- 🟡 Constant animations (scanline, glitch, pulse, spin, flicker) with no `prefers-reduced-motion` handling. That's an accessibility issue, and the glitch/flicker effects can bother photosensitive users.
- 🟡 Fonts load through CSS `@import`, which blocks rendering. Use `<link rel="preconnect">` + `<link>` in `<head>`.
- 🟡 The external `target="_blank"` links are missing `rel="noopener"`.
- 🟡 Pitch mismatch: the README sells a "fake productivity" joke, the site sells "keep your PC awake". Pick one voice, or use both on purpose ("serious tool, unserious attitude").
- 🟡 No analytics or download counter, so you can't tell whether anyone uses it. The GitHub Releases API gives download counts for free and you can show them on the site.

---

## 5. Making it *crazy* good

Ordered roughly by impact ÷ effort.

### Tier 1: Make the core bulletproof (the "it just works" tier)
1. **Real input + sleep prevention** (1.1). Make the promise true.
2. **Smart auto-pause**: stop when you touch the mouse or keyboard, resume after X seconds of idle. Show a "🟢 You're back — paused" toast.
3. **Stealth / Zen mode**: a 1-pixel nudge every 30–60 s, or an invisible F15 keypress (the classic Caffeine trick). It stays active with **zero visible cursor movement**, so you can keep it running while you watch something. This will be the most-used mode.
4. **Global hotkeys** for show/hide and start/stop.
5. **Settings saved** to `%APPDATA%\OrbitMousePro\settings.json`.

### Tier 2: Features people would actually brag about
6. **Schedules**: "Run Mon–Fri 9:00–17:30", "Stop at 18:00", "Run for 45 min". Add a lunch-break exception.
7. **Human-like movement engine**: replace the perfect circles with Bézier curves, ease-in/out, random pauses, micro-overshoot, and occasional scroll/Shift taps. Call it the **"Humanize" slider**. Perfect circles are the most obviously fake pattern possible.
8. **More patterns**: Lissajous, spiral, "reading" (slow down-scroll + small horizontal sweeps), "Doodle" (draws a random shape), "Draw your own" (record a path and replay it).
9. **Presence presets**: "Teams", "Slack", "Just stay awake", "Presentation mode", each with the right combination of nudge interval, mode and sleep blocking.
10. **App-aware rules**: auto-start when a Zoom/Teams meeting app isn't focused, or auto-stop when a fullscreen game or video is running.
11. **Start minimized to tray** plus a **"launch on Windows startup"** toggle inside the app, not just in the installer.

### Tier 3: Lean into the personality (this is your differentiator)
12. **Fake-productivity theatre, done properly**: a stats screen showing "Meetings survived", "Emails 'read'", "Synergies leveraged", a lifetime "hours of productivity generated" counter, and a weekly "Performance Review" with a fake manager quote.
13. **Achievements**: "Iron Butt (8h session)", "Ghost (24h)", "Night Shift", "Didn't touch it once". Unlocked with a glitchy neon toast.
14. **Fake work screen (Panic Button 2.0)**: the boss key opens a fullscreen fake VS Code, Excel or terminal scrolling plausible output, instead of just hiding the window.
15. **Sound design**: optional synthwave UI blips on engage/abort, CRT power-on on launch.
16. **Themes**: Cyberpunk (current), Matrix green, Vaporwave pink, plus a "Corporate Beige" stealth theme that looks like a boring IT utility.
17. **Mini mode**: a tiny always-on-top 80×80 orbit widget, or just the tray icon with an animated spinning dot while running. The tray icon is currently a flat yellow circle (`:617`), so use the real emblem and animate it.
18. **Windows toast notifications** for start/stop/schedule events instead of in-window only.

### Tier 4: Distribution & growth
19. `winget install OrbitMousePro`, a Scoop bucket, and a Chocolatey package. Developers trust these more than a raw .exe.
20. A portable build (zip, no installer) for locked-down work laptops.
21. A real demo GIF at the top of the README plus a launch post (r/sideproject, Product Hunt, Hacker News "Show HN"). The joke angle travels well.
22. A **CLI**: `orbit start --mode stealth --for 2h`, which is good for power users and scripting.
23. **Cross-platform**: macOS uses `IOPMAssertionCreateWithName` for sleep prevention and `CGEventPost` for input. Optional, but it doubles the audience.

---

## 6. Suggested roadmap

| Release | Scope |
|---|---|
| **v1.1.1 (hotfix)** | 1.2 drift, 1.3 double-run, 1.4 thread safety, 2.1 missing dep, 2.2 exe icon, `upx=False`, un-ignore RELEASING.md, add LICENSE |
| **v1.2 "Actually Works"** | SendInput + `SetThreadExecutionState`, idle readout, auto-pause on user input, Stealth mode, global hotkeys, settings persistence, X → tray |
| **v1.3 "Pipeline"** | Restructure into `src/orbit/`, engine unit tests, GitHub Actions release, single-source version, site reads `version.json`, OG tags + demo GIF |
| **v2.0 "Crazy Good"** | Humanize engine + new patterns, schedules, presets, stats/achievements, fake work screen, themes, mini mode, winget |

**If you only do three things:** fix the drift bug (1.2), switch to real input + `SetThreadExecutionState` (1.1), and add Stealth mode + auto-pause. Those three turn it from a fun demo into something people keep installed.
