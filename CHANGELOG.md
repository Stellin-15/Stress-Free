# Changelog

All notable changes to Orbit Mouse Pro are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

The release workflow publishes the section matching the tag as the GitHub Release notes, so write entries for users.

## [Unreleased]

## [1.2.0] - 2026-10-03

### Added
- **Stealth mode**: keeps you active with zero visible cursor movement. It sends an invisible input event only after 30 seconds of idle.
- **Auto-pause**: moving the mouse or pressing a key pauses Orbit. It resumes after 15 seconds of you being idle.
- **Global hotkeys**: `Ctrl+Alt+H` shows/hides the window and `Ctrl+Alt+O` starts/stops, from any app.
- Live **SYS IDLE** readout, so you can see that Windows registers the activity.
- Settings (pattern, radius, speed, auto-pause) are remembered between launches.
- The tray menu has Start/Stop and uses the Orbit emblem.

### Changed
- Mouse movement is now sent as real input. The previous method moved the cursor without resetting the Windows idle timer, so Teams/Slack could still mark you as away.
- Sleep and screen-off are blocked while Orbit is running.
- Closing the window now hides Orbit to the tray. Quit from the tray menu.
- Update notices appear in the footer instead of below the window.

### Fixed
- Circle and Jitter patterns drifted across the screen over time.
- Pressing Stop then Start quickly could run two movement loops at once.
- The Abort button and footer were cut off at the bottom of the window.
- Pressing ESC while idle showed "ABORTED".
- Possible random crash from reading UI controls on a background thread.
- The exe now has the Orbit icon.

## [1.1.0] - 2026-03-21

### Added
- Cyberpunk redesign: neon orbit ring, glitch title, CRT scanline, custom logo.
- Movement patterns: Circle, Figure-8, Jitter.
- Live radius and speed sliders.
- Running timer, fake Productivity Score and rotating idle messages.
- Boss key (`Ctrl+H`) and system tray with Show / Stop / Quit.
- Auto-update check with a download banner.

### Fixed
- The auto-updater only accepts github.com download URLs.
- Closing the window while movement was active crashed the app.
- ESC reliably stops movement.

[Unreleased]: https://github.com/Stellin-15/Stress-Free/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/Stellin-15/Stress-Free/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/Stellin-15/Stress-Free/releases/tag/v1.1.0
