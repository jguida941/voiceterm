# VoiceTerm Quick Start

Get voice input for your AI CLI in under 2 minutes.
Works on macOS and Linux (Windows needs WSL2).
For an always-listening flow, combine `--auto-voice` + `--wake-word`, then say
`send` / `submit` in `insert` mode for hands-free delivery.

## 1) Install Codex CLI (default backend)

```bash
npm install -g @openai/codex
```

If you use Claude instead, install Claude Code:

```bash
curl -fsSL https://claude.ai/install.sh | bash
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

First run downloads a Whisper model if missing.
To choose a model at launch, use `--whisper-model`:

```bash
voiceterm --whisper-model base
voiceterm --whisper-model medium
```

If you installed from source and want to pre-download a model:

```bash
./scripts/setup.sh models --small
```

Codex is default; `voiceterm --codex` is optional.
Use `voiceterm --claude` to target Claude.

## 4) Core controls

- `Ctrl+R` - trigger voice capture
- `Ctrl+X` - one-shot screenshot prompt capture
- `Ctrl+E` - finalize active recording early (stages text only, does not send)
- `Ctrl+T` - toggle send mode (auto vs insert)
- `Ctrl+V` - toggle auto-voice (disabling cancels running capture)
- `Ctrl+D` - toggle Dev panel (`--dev` launches only)
- `Ctrl+Q` - quit VoiceTerm

In `auto` mode, text is typed and submitted.
In `insert` mode, text is typed and waits for Enter (or spoken `send`).
When Codex/Claude approval or reply/composer prompts appear, VoiceTerm
suppresses HUD rows until you submit/cancel so the prompt stays readable.

Full controls reference:

- [guides/USAGE.md#core-controls](guides/USAGE.md#core-controls)
- [guides/USAGE.md#settings-menu](guides/USAGE.md#settings-menu)
- [guides/USAGE.md#voice-modes](guides/USAGE.md#voice-modes)

## 5) Hands-free starter (optional)

GUI setup:

1. Press `Ctrl+O` and set `Wake word` to `ON`.
2. Press `Ctrl+T` until send mode is `insert`.
3. Press `Ctrl+V` to turn auto-voice on.
4. Say your wake phrase (`hey codex` / `hey claude`), speak your prompt, then
   say `send`.

Example flow:

1. `hey codex`
2. "summarize the last 3 commits"
3. `send`

One-shot examples:

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
voiceterm --dev
voiceterm --dev --dev-log
voiceterm --voice-vad-threshold-db -50
voiceterm --mic-meter
voiceterm --logs
```

Style-pack note:

- `VOICETERM_STYLE_PACK_JSON` can set `components.overlay_border` for overlays and `components.hud_border` for Full HUD when border style is `theme`.

See [guides/CLI_FLAGS.md](guides/CLI_FLAGS.md) for the full option reference.

## 7) Need help?

- Full user docs map: [guides/README.md](guides/README.md)
- Install options: [guides/INSTALL.md](guides/INSTALL.md)
- Troubleshooting hub: [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)
