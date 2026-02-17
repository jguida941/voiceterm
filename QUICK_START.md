# VoiceTerm Quick Start

Get voice input for your AI CLI in under 2 minutes.
Works on macOS and Linux (Windows needs WSL2).

Docs map:

- User docs entrypoint: [guides/README.md](guides/README.md)
- Install details: [guides/INSTALL.md](guides/INSTALL.md)
- Usage and controls: [guides/USAGE.md](guides/USAGE.md)
- Troubleshooting hub: [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)
- Engineering history: [dev/history/ENGINEERING_EVOLUTION.md](dev/history/ENGINEERING_EVOLUTION.md)

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

## 4) Essential controls

- `Ctrl+R` - start voice capture
- `Ctrl+V` - toggle auto-voice (disabling cancels any running capture)
- `Ctrl+T` - toggle send mode (auto vs insert)
- `Ctrl+G` - quick cycle theme
- `Ctrl+Y` - open theme picker
- `Ctrl+O` - open settings menu (use ↑↓←→ + Enter)
- `Ctrl+U` - cycle HUD style (full/minimal/hidden)
- `Ctrl+]` - increase mic threshold by 5 dB (less sensitive)
- `Ctrl+\` - decrease mic threshold by 5 dB (more sensitive; `Ctrl+/` also works)
- `?` - show shortcut help
- `Ctrl+Q` - exit overlay
- `Ctrl+C` - forwarded to the CLI
- `Enter` - in insert mode, stop capture early and transcribe what was captured

Full behavior notes and screenshots are in [guides/USAGE.md](guides/USAGE.md).

Send mode note: "auto" types your words and presses Enter. "Insert" types your words
but lets you press `Enter` yourself. VoiceTerm only writes to the terminal (PTY) and
does not call Codex/Claude directly.

Built-in voice navigation phrases include `scroll up`, `scroll down`,
`show last error`, `copy last error`, and `explain last error`.
If you also use matching macros, macros run first. Use `voice scroll up` /
`voice scroll down` to force built-in navigation phrases.

More detailed topics:

- Macros: [guides/USAGE.md#project-voice-macros](guides/USAGE.md#project-voice-macros)
- HUD and themes: [guides/USAGE.md#customization](guides/USAGE.md#customization)
- Backend support status: [guides/USAGE.md#backend-support](guides/USAGE.md#backend-support)

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
voiceterm --latency-display label
voiceterm --voice-max-capture-ms 60000 --voice-buffer-ms 60000
voiceterm --transcript-idle-ms 250
voiceterm --prompt-regex '^codex> $'
```

See [guides/CLI_FLAGS.md](guides/CLI_FLAGS.md) for the full CLI flag and env var list.

## 6) Need help?

- Full user docs map: [guides/README.md](guides/README.md)
- Install options: [guides/INSTALL.md](guides/INSTALL.md)
- Troubleshooting hub: [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)
