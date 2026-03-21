# Orbit Mouse Pro

> Ensures you are working even when you are not 😉

A cyberpunk-themed mouse automation tool that keeps your status active by moving your mouse in continuous patterns. Features a slick dark UI with neon animations, real-time controls, and a system tray.

---

## Features

- **Movement patterns** — Circle, Figure-8, or Jitter (looks human)
- **Radius & speed sliders** — adjust live while running
- **Running timer** — shows how long you've been "productive"
- **Productivity Score** — a fake % that climbs to 99% and never hits 100
- **Funny idle messages** — rotates motivational nonsense while stopped
- **Boss Key** — `Ctrl+H` hides the window instantly; mouse keeps moving
- **System tray** — runs silently in the background with Show / Stop / Quit
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
| Start | Click **▶ ENGAGE ORBIT** |
| Stop | Click **■ ABORT** or press `ESC` |
| Hide window | `Ctrl+H` (mouse keeps running) |
| Restore window | Click the tray icon |
| Quit | Tray menu → Quit |

---

## Releasing a new version

See [RELEASING.md](RELEASING.md) for the full step-by-step guide.

---

## Tech stack

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — modern dark GUI
- [pyautogui](https://pyautogui.readthedocs.io/) — mouse control
- [pystray](https://github.com/moses-palmer/pystray) — system tray
- [Pillow](https://pillow.readthedocs.io/) — icon & logo generation
- [PyInstaller](https://pyinstaller.org/) — exe packaging
- [Inno Setup](https://jrsoftware.org/isinfo.php) — Windows installer
