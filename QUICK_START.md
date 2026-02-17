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

- `Ctrl+R` - toggle voice capture (start recording / stop early)
- `Ctrl+E` - in insert mode: send staged text now; if recording with no staged text, finalize and submit current capture; if idle with no staged text, no-op
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
- `Enter` - send staged prompt text in insert mode

Full behavior notes and screenshots are in [guides/USAGE.md](guides/USAGE.md).

Send mode note: "auto" types your words and presses Enter. "Insert" types your words
but lets you press `Enter` yourself. VoiceTerm only writes to the terminal (PTY) and
does not call Codex/Claude directly.
In insert mode, pressing `Ctrl+E` while idle with no staged text now shows
`Nothing to send` (instead of silently doing nothing).
When help/settings/theme overlays are open, unmatched input now closes the
overlay and replays the action instead of dropping it.
Status text is pipeline-neutral (`Listening Manual Mode`, `No speech detected`);
use Settings (`Ctrl+O`) to view the current `Voice pipeline`.
Latency badge reflects direct STT delay (`stt_ms`) only, hides for
no-speech/error captures, and auto-clears stale idle values after a short
window.
Hidden HUD launcher text/buttons and recording indicator are intentionally
muted gray so hidden mode stays unobtrusive. Idle hidden mode shows
`? help`, `^O settings`, and `[open] [hide]`; selecting `hide` collapses the
launcher to only `[open]`.
In collapsed mode, the first `open` restores the hidden launcher, and the next
`open` switches HUD style.
Help overlay includes clickable Docs/Troubleshooting links (OSC-8 capable
terminals).
On first run, VoiceTerm shows a persistent `Getting started` hint
(`Ctrl+R` / `?` / `Ctrl+O`) until your first successful transcript capture.

Built-in voice navigation phrases include `scroll up`, `scroll down`,
`show last error`, `copy last error`, and `explain last error`.
If you also use matching macros, macros run first. Use `voice scroll up` /
`voice scroll down` to force built-in navigation phrases.

More detailed topics:

- Macros: [guides/USAGE.md#project-voice-macros](guides/USAGE.md#project-voice-macros)
- HUD and themes: [guides/USAGE.md#customization](guides/USAGE.md#customization)
- Backend support status: [guides/USAGE.md#backend-support](guides/USAGE.md#backend-support)
- Full HUD note: right-panel visualizer (`ribbon`, `dots`, `heartbeat`)
  appears on the main status row (top-right lane).
- Theme note: on `xterm-256color`, selected themes are preserved; ANSI fallback
  applies only on ANSI16 terminals.

Optional macro setup (project-local):

```bash
./scripts/macros.sh wizard
```

If you install from source, `./scripts/install.sh` now prompts to run the macro
wizard at the end of install.

- Pre-release test builds from a branch:

```bash
git clone --branch <branch-name> https://github.com/jguida941/voiceterm.git
cd voiceterm
./scripts/install.sh
```

After installing a test branch build, run the release verification commands in
`dev/DEVELOPMENT.md` (`Testing` and `Manual QA checklist`) before promoting to
a tagged release.

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
voiceterm --wake-word --wake-word-sensitivity 0.65 --wake-word-cooldown-ms 3000
```

Wake-word remains OFF by default; use the flag above or Settings (`Ctrl+O`) to
enable and tune sensitivity/cooldown.

See [guides/CLI_FLAGS.md](guides/CLI_FLAGS.md) for the full CLI flag and env var list.

## 6) Need help?

- Full user docs map: [guides/README.md](guides/README.md)
- Install options: [guides/INSTALL.md](guides/INSTALL.md)
- Troubleshooting hub: [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)
