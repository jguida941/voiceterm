# VoiceTerm Quick Start

Get voice input for your AI CLI in under 2 minutes.
Works on macOS and Linux (Windows needs WSL2).
Current stable release: `v1.0.89` (2026-02-23). Full release notes: [dev/CHANGELOG.md](dev/CHANGELOG.md).
See [README](README.md) for the current release.

## 1) Install Codex CLI (default backend)

```bash
npm install -g @openai/codex
```

Or use another AI CLI: `voiceterm --claude`.

## 2) Install VoiceTerm

**Homebrew (recommended):**

```bash
brew tap jguida941/voiceterm
brew install voiceterm
```

**PyPI (pipx):**

```bash
pipx install voiceterm
```

**From source:**

```bash
git clone https://github.com/jguida941/voiceterm.git
cd voiceterm
./scripts/install.sh
```

**macOS App:** Double-click **app/macos/VoiceTerm.app** and choose your project folder.

If `voiceterm` is not found after install, see [guides/INSTALL.md](guides/INSTALL.md) for PATH notes.

## 3) Run from any project

```bash
cd ~/my-project
voiceterm
```

If you haven't authenticated with your backend CLI yet:

```bash
voiceterm --login --codex
voiceterm --login --claude
```

First run downloads a Whisper model if missing.
To pick a size, use `./scripts/install.sh --small` or
`./scripts/setup.sh models --medium`.

Codex is the default backend; `voiceterm --codex` is optional if you want to be explicit.

To target Claude instead of Codex:

```bash
voiceterm --claude
```

## 4) Core controls

- `Ctrl+R` - toggle voice capture (start recording / stop early)
- `Ctrl+E` - finalize active recording early (stages text only, does not send)
- `Ctrl+T` - toggle send mode (auto vs insert)
- `Ctrl+V` - toggle auto-voice (disabling cancels any running capture)
- `Ctrl+O` - open settings menu
- `Ctrl+H` - open transcript history (search and replay)
- `Ctrl+N` - open notification history
- `Ctrl+Q` - exit overlay

Full controls reference:

- [guides/USAGE.md#core-controls](guides/USAGE.md#core-controls)
- [guides/USAGE.md#settings-menu](guides/USAGE.md#settings-menu)
- [guides/USAGE.md#voice-modes](guides/USAGE.md#voice-modes)

Theme Studio tip:

- Press `Ctrl+Y` and use `Undo edit`, `Redo edit`, and `Rollback edits` to recover live visual override changes for the current session.

Wake-word tip:

- If wake listener startup fails, Full HUD now shows `Wake: ERR`; run with `--logs` and check [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md).
- `Wake: ON` is now a steady badge and wake-listener capture windows are longer to reduce macOS microphone-indicator flicker.
- Pausing auto-voice rearm does not disable wake-word triggers; saying a wake phrase still starts capture when wake mode is ON.

In `auto` mode, text is typed and submitted. In `insert` mode, text is typed
and you press Enter (or say `send`). See [Usage Guide](guides/USAGE.md) for full details.

Deep-dive guides:

- Macros: [guides/USAGE.md#project-voice-macros](guides/USAGE.md#project-voice-macros)
- HUD and themes: [guides/USAGE.md#customization](guides/USAGE.md#customization)
- Backend support status: [guides/USAGE.md#backend-support](guides/USAGE.md#backend-support)
- Runtime troubleshooting hub: [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)

Optional macro setup (project-local):

```bash
./scripts/macros.sh wizard
```

If you install from source, `./scripts/install.sh` now prompts to run the macro
wizard at the end of install.

- Startup and IDE behavior: [guides/TROUBLESHOOTING.md#terminal-and-ide-issues](guides/TROUBLESHOOTING.md#terminal-and-ide-issues)

## 5) Common flags

```bash
voiceterm --auto-voice
voiceterm --voice-send-mode insert
voiceterm --voice-vad-threshold-db -50
voiceterm --mic-meter
voiceterm --logs
```

See [CLI_FLAGS.md](guides/CLI_FLAGS.md) for all options including wake-word,
session memory, theme, and capture tuning flags.

## 6) Need help?

- Full user docs map: [guides/README.md](guides/README.md)
- Install options: [guides/INSTALL.md](guides/INSTALL.md)
- Troubleshooting hub: [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)
