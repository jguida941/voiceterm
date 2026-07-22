# VoiceTerm Quick Start

Get voice input for your AI CLI in under 2 minutes.
Works on macOS and Linux (Windows needs WSL2).
If you want hands-free mode, start with `--auto-voice` + `--wake-word`, then
use `insert` send mode so you can say `send` / `submit`.

Need the full docs instead of the shortest path?
[Install Guide](guides/INSTALL.md) |
[Usage Guide](guides/USAGE.md) |
[CLI Flags](guides/CLI_FLAGS.md) |
[Troubleshooting](guides/TROUBLESHOOTING.md)

## 1) Install Codex CLI (default backend)

```bash
npm install -g @openai/codex
```

If you use Claude instead, install Claude Code:

```bash
npm install -g @anthropic-ai/claude-code
```

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

**macOS App:** Double-click `app/macos/VoiceTerm.app` and choose your project folder.

If `voiceterm` is not found after install, see
[guides/INSTALL.md](guides/INSTALL.md) for PATH notes.

## 3) Run from any project

```bash
cd ~/my-project
voiceterm
```

If you have not authenticated your backend CLI yet:

```bash
voiceterm --login --codex
voiceterm --login --claude
```

First run through an installed wrapper downloads a Whisper model if missing.
To choose a specific model, download it and pass its exact path:

```bash
./scripts/setup.sh models --base
voiceterm --whisper-model-path ./whisper_models/ggml-base.en.bin
```

For a source checkout, build and launch through the model-aware start script:

```bash
make build
./scripts/start.sh
```

The raw `rust/target/release/voiceterm` binary needs
`--whisper-model-path <FILE>` unless a matching model is already under the
repository's `whisper_models/` directory.

Codex is default; `voiceterm --codex` is optional.
Use `voiceterm --claude` to target Claude.
Need backend details, IDE compatibility, or experimental-backend status?
Start here:

- [Backend support](guides/USAGE.md#backend-support)
- [IDE compatibility](guides/USAGE.md#ide-compatibility)
- [Troubleshooting](guides/TROUBLESHOOTING.md)

## 4) Core controls

- `Ctrl+R` - trigger voice capture
- `Ctrl+X` - one-shot screenshot prompt capture
- `Ctrl+E` - in `insert` mode, finalize early, transcribe, and place the text in the chat composer without sending
- `Ctrl+T` - toggle send mode (auto vs insert)
- `Ctrl+V` - toggle auto-voice (disabling cancels running capture)
- `Ctrl+D` - send EOF to the backend CLI
- `Ctrl+Q` - quit VoiceTerm

In `auto` mode, text is typed and submitted.
In `insert` mode, text is typed and waits for Enter (or spoken `send`).
Latency badges are based on completed STT turns and hide while VoiceTerm is
actively recording or processing.
Pressing `Ctrl+R` again during an active capture cancels and discards it.
When a high-confidence Codex/Claude approval card appears, VoiceTerm can hide
HUD rows so the interactive choices stay readable; ordinary composer and hint
text does not trigger suppression.

Full controls reference:

- [guides/USAGE.md#core-controls](guides/USAGE.md#core-controls)
- [guides/USAGE.md#settings-menu](guides/USAGE.md#settings-menu)
- [guides/USAGE.md#voice-modes](guides/USAGE.md#voice-modes)

Mouse note:

- `Mouse` is ON by default for clickable HUD controls.
- In Cursor terminal, wheel/touchpad scrolling may not move chat history while
  `Mouse` stays ON, but the scrollbar can still be dragged.
- If you want touchpad/wheel scrolling, set `Mouse` to `OFF` and use keyboard
  HUD navigation (`Left`/`Right` + `Enter`) for controls.
- `Ctrl+Y` opens Theme Studio; use `Tab` / `Shift+Tab` to move across pages
  (`Home`, `Colors`, `Borders`, `Components`, `Preview`, `Export`).
- The live HUD preview beneath Theme Studio updates immediately as you change
  HUD style, borders, right panel, colors, or glyphs. The conversation remains
  untouched behind the isolated editor.

## 5) Hands-free starter (optional)

Settings path:

1. Press `Ctrl+O` and set `Wake word` to `ON`.
2. Press `Ctrl+T` until send mode is `insert`.
3. Press `Ctrl+V` to turn auto-voice on.
4. Say your wake phrase (`hey codex` / `hey claude`), speak your prompt, then
   say `send`.

Example flow:

1. `hey codex`
2. "summarize the last 3 commits"
3. `send`

Quick examples:

- `hey codex send`
- `hey claude send`

Optional startup command:

```bash
voiceterm --auto-voice --wake-word --voice-send-mode insert
```

If wake startup fails, Full HUD shows `Wake: ERR`. Run with `--logs` and check
[guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md).

## 6) Common flags

```bash
voiceterm --auto-voice
voiceterm --wake-word
voiceterm --voice-send-mode insert
voiceterm --image-mode    # persistent image capture for HUD [rec]
voiceterm --theme-file ~/.config/voiceterm/themes/my-theme.toml
voiceterm --voice-vad-threshold-db -50
voiceterm --mic-meter
voiceterm --logs
```

`Ctrl+D` forwards EOF (`0x04`) to the wrapped CLI, so that session may close.

See [guides/CLI_FLAGS.md](guides/CLI_FLAGS.md) for the full option reference.

## 7) Need help?

- Full user docs map: [guides/README.md](guides/README.md)
- Install options: [guides/INSTALL.md](guides/INSTALL.md)
- Daily usage and controls: [guides/USAGE.md](guides/USAGE.md)
- Full flag list: [guides/CLI_FLAGS.md](guides/CLI_FLAGS.md)
- Troubleshooting hub: [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)
