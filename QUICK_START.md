# VoiceTerm Quick Start

Get voice input for your AI CLI in under 2 minutes.
Works on macOS and Linux (Windows needs WSL2).
Current stable release: `v1.0.86` (2026-02-20). Full release notes: [dev/CHANGELOG.md](dev/CHANGELOG.md).

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

## 4) Core controls

- `Ctrl+R` - toggle voice capture (start recording / stop early)
- `Ctrl+E` - in insert mode: send staged text now; if recording with no staged text, finalize and submit current capture; if idle with no staged text, shows `Nothing to send`
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

Behavior highlights:

- Send mode: `auto` types and submits; `insert` types and waits for `Enter`.
- Overlays (`help` / `settings` / `theme studio` / `theme picker` / `history` / `notifications`): unmatched input closes the overlay and replays the action.
- History overlay rows are source-labeled (`mic`, `you`, `ai`); only `mic` and `you` rows are replayable.
- Runtime settings persist in `~/.config/voiceterm/config.toml`; explicit CLI flags override persisted values for that run.
- Hidden HUD keeps idle controls subtle: `? help`, `^O settings`, `[open] [hide]`.
- Claude approval/permission prompts temporarily suppress HUD rows to keep prompt actions visible.

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

- Pre-release/test branch install flow: [guides/INSTALL.md#integrationtest-branch-installs](guides/INSTALL.md#integrationtest-branch-installs)
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
voiceterm --session-memory --session-memory-path ./.voiceterm/session-memory.md
```

Wake-word remains OFF by default; use the flag above or Settings (`Ctrl+O`) to
enable and tune sensitivity/cooldown.

See [guides/CLI_FLAGS.md](guides/CLI_FLAGS.md) for the full CLI flag and env var list.

## 6) Need help?

- Full user docs map: [guides/README.md](guides/README.md)
- Install options: [guides/INSTALL.md](guides/INSTALL.md)
- Troubleshooting hub: [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)
