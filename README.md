# Orbit Mouse Pro

[![CI](https://github.com/Stellin-15/Stress-Free/actions/workflows/ci.yml/badge.svg)](https://github.com/Stellin-15/Stress-Free/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/Stellin-15/Stress-Free)](https://github.com/Stellin-15/Stress-Free/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/Stellin-15/Stress-Free/total)](https://github.com/Stellin-15/Stress-Free/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

> Ensures you are working even when you are not 😉

A cyberpunk-themed mouse automation tool that keeps your status active by moving your mouse in continuous patterns. Features a slick dark UI with neon animations, real-time controls, and a system tray.

---

## Features

- **Actually keeps you active** — moves are sent as real input (`SendInput`), so Teams, Slack and the screensaver see activity; sleep and screen-off are blocked while running
- **Stealth mode** — keeps you active with *zero* visible cursor movement (an invisible nudge only after 30 s idle)
- **Auto-pause** — touch the mouse or keyboard and it backs off; resumes after 15 s of you being idle
- **Movement patterns** — Circle, Figure-8, Jitter, or Stealth
- **Radius & speed sliders** — adjust live while running
- **Running timer + live idle readout** — proof that Windows sees you as active
- **Productivity Score** — a fake % that climbs to 99% and never hits 100
- **Funny idle messages** — rotates motivational nonsense while stopped
- **Global hotkeys** — `Ctrl+Alt+H` hides/shows, `Ctrl+Alt+O` starts/stops, from any app
- **System tray** — closing the window keeps it running in the tray (Show/Hide, Start/Stop, Quit)
- **Remembers your settings** — pattern, radius, speed and auto-pause persist between launches
- **Auto-updater** — notifies you when a new version is available
- **Cyberpunk UI** — neon yellow animated orbit ring, glitch effects, CRT scanline

---

## Download

Head to the [website](https://stellin-15.github.io/Stress-Free/) or grab the latest installer from [Releases](https://github.com/Stellin-15/Stress-Free/releases).

---

## Running from source

```bash
# 1. Clone
git clone https://github.com/Stellin-15/Stress-Free.git
cd Stress-Free

# 2. Create & activate venv
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r "Python Version/requirements.txt"

# 4. Run
python "Python Version/mouse_circle.py"
```

**Requirements:** Python 3.9+, Windows 10/11

---

## Controls

| Action | How |
|---|---|
| Start / Stop | Click **▶ ENGAGE ORBIT** / **■ ABORT**, or `Ctrl+Alt+O` from anywhere |
| Stop (window focused) | `ESC` |
| Hide / show window | `Ctrl+Alt+H` from anywhere, or click the tray icon |
| Close window | Hides to the tray — keeps running |
| Quit | Tray menu → Quit |

---

## Contributing

PRs welcome. [CONTRIBUTING.md](CONTRIBUTING.md) covers dev setup, running the tests (`pytest`, `ruff check .`) and the branch/PR flow. Changes are tracked in [CHANGELOG.md](CHANGELOG.md).

Releases are automated: push a version tag and GitHub Actions builds and publishes the installer. See [RELEASING.md](RELEASING.md).

---

## Tech stack

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — modern dark GUI
- Win32 `SendInput` / `SetThreadExecutionState` via ctypes — real input & sleep prevention
- [pystray](https://github.com/moses-palmer/pystray) — system tray
- [Pillow](https://pillow.readthedocs.io/) — icon & logo generation
- [PyInstaller](https://pyinstaller.org/) — exe packaging
- [Inno Setup](https://jrsoftware.org/isinfo.php) — Windows installer

---

## License

[MIT](LICENSE) © Stellin
