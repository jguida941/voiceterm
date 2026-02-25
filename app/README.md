# App Launchers

Platform-specific application launchers for VoiceTerm.

## macOS

`macos/VoiceTerm.app` - Double-click app that opens a folder picker and launches VoiceTerm in Terminal.

**Usage:**

1. Double-click `VoiceTerm.app`
2. Select your project folder
3. Terminal opens with VoiceTerm running in that folder

**Building:** The app is a simple AppleScript wrapper. No build step required.

## Windows

`windows/` - Windows launcher (coming soon)

**Planned features:**

- Windows Terminal integration
- PowerShell launcher
- WSL2 support

## PySide6 Command Center

`pyside6/` - Optional desktop control-plane command center.

This app is designed as an operator console over existing repository controls.
It does not replace the Rust runtime overlay.

Primary use cases:

- run `devctl` and governance checks from a tabbed UI
- view recent GitHub Actions runs
- run git and ad-hoc terminal commands from one place

Run:

```bash
python3 -m pip install PySide6
python3 app/pyside6/run.py
```
