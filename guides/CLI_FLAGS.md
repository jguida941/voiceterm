# CLI Flags

All `voiceterm` flags in one place.
If you are new, start with [Quick Reference](#quick-reference).

Docs map:

- Quick start path: [../QUICK_START.md](../QUICK_START.md)
- Voice lifecycle and controls: [USAGE.md](USAGE.md)
- Whisper model guidance: [WHISPER.md](WHISPER.md)

## Contents

- [Quick Reference](#quick-reference)
- [Voice Behavior](#voice-behavior)
- [Developer Guard](#developer-guard)
- [Backend Selection](#backend-selection)
- [Microphone & Audio](#microphone--audio)
- [Whisper STT](#whisper-stt)
- [Capture Tuning](#capture-tuning)
- [Themes & Display](#themes--display)
- [Logging](#logging)
- [IPC / Integration](#ipc--integration)
- [Sounds](#sounds)
- [Environment Variables](#environment-variables)
- [See Also](#see-also)

---

## Quick Reference

Most common flags:

```bash
voiceterm --codex                       # Use Codex (default)
voiceterm --claude                      # Use Claude Code
voiceterm --login --codex               # Run Codex login before starting
voiceterm --login --claude              # Run Claude login before starting
voiceterm --auto-voice                  # Hands-free mode
voiceterm --auto-voice --wake-word --voice-send-mode insert  # Wake + voice submit
voiceterm --image-mode                  # Persistent image mode for HUD [rec] (Ctrl+R stays voice)
voiceterm --dev                         # Enable guarded deferred dev features (`DEV` badge)
voiceterm --dev --dev-log              # Also persist dev events to JSONL files
voiceterm --theme dracula               # Change theme
voiceterm --voice-vad-threshold-db -50  # Adjust mic sensitivity
voiceterm --mic-meter                   # Calibrate mic threshold
voiceterm --logs                        # Enable debug logging
voiceterm --session-memory              # Write user/backend chat memory to markdown
```

---

## Voice Behavior

| Flag | Purpose | Default |
|------|---------|---------|
| `--auto-voice` | Start in auto-voice mode (hands-free) | off |
| `--auto-voice-idle-ms <MS>` | Idle time before auto-voice triggers when prompt not detected | 1200 |
| `--transcript-idle-ms <MS>` | Idle time before queued transcripts are injected into the terminal | 250 |
| `--voice-send-mode <auto\|insert>` | `auto` types text and presses Enter; `insert` types text and waits for Enter (or voice `send`) | auto |
| `--wake-word` | Enable local wake-word listening (off by default) | off |
| `--wake-word-sensitivity <0.0-1.0>` | Wake detector sensitivity | 0.55 |
| `--wake-word-cooldown-ms <MS>` | Cooldown between wake triggers (500-10000) | 2000 |
| `--image-mode` | Enable persistent image mode for HUD `[rec]`; `Ctrl+R` still triggers voice capture | off |
| `--image-capture-command <CMD>` | Custom capture command. Output path is provided via `VOICETERM_IMAGE_PATH` | auto on macOS (`screencapture`) |
| `--seconds <N>` | Recording duration for the Python fallback pipeline (1-60) | 5 |

For runtime controls and keyboard shortcuts, see [USAGE.md](USAGE.md).

Wake labels in Full HUD:

- `Wake: ON` - listener is active
- `Wake: PAUSED` - listener paused during capture/transcription
- `Wake: ERR` - listener startup failed
- Mouse is on by default for clickable HUD controls.
- In Cursor terminal, wheel/touchpad scrolling may not move chat history while
  mouse mode is on (the scrollbar can still be dragged).
- Wake phrases still work even if auto-voice is paused.
- Built-in phrases `send`, `send message`, and `submit` send staged text in `insert` mode.
- In `auto` mode, wake-triggered `send`/`submit` still sends Enter even without staged `insert` text.
- Latency badges hide during active recording/processing and return after
  transcription with the latest reliable STT sample.
- `Ctrl+X` triggers one-shot screenshot capture prompts.
- Image mode adds an `IMG` HUD badge when persistent mode is enabled.

---

## Developer Guard

| Flag | Purpose | Default |
|------|---------|---------|
| `--dev` (`--dev-mode`, `-D`) | Enables guarded deferred developer-mode features for this launch only (includes `Ctrl+D` Dev panel with `Dev Tools` commands: `status`, `report`, `triage`, `security`, `sync`) | off |
| `--dev-log` | Persist guarded dev events to session JSONL logs (requires `--dev`) | off |
| `--dev-path <DIR>` | Root directory for `--dev-log` session files (requires `--dev --dev-log`) | `$HOME/.voiceterm/dev` (fallback: `<cwd>/.voiceterm/dev`) |

When enabled, Full HUD shows a `DEV` badge.
`Ctrl+D` toggles the in-session Dev panel.
Without `--dev`, `Ctrl+D` is forwarded as EOF (`0x04`) to the backend CLI.
With `--dev-log`, VoiceTerm writes JSONL session files under `<dev-path>/sessions/`.
For command-by-command Dev panel behavior, see [DEV_MODE.md](DEV_MODE.md).

---

## Backend Selection

| Flag | Purpose | Default |
|------|---------|---------|
| `--codex` | Use Codex CLI (shorthand) | - |
| `--claude` | Use Claude Code (shorthand) | - |
| `--gemini` | Use Gemini CLI (experimental; currently not working) | - |
| `--backend <NAME\|CMD>` | Backend preset: `codex`, `claude`, `gemini` (not working), `aider` (untested), `opencode` (untested), or a custom command string | codex |
| `--login` | Run backend login before starting the overlay | off |
| `--prompt-regex <REGEX>` | Override prompt detection pattern | auto-learned |
| `--prompt-log <PATH>` | Log detected prompts to file (debugging) | disabled |
| `--codex-cmd <PATH>` | Path to Codex binary | codex |
| `--claude-cmd <PATH>` | Path to Claude binary (IPC + overlay) | claude |
| `--codex-arg <ARG>` | Extra args passed to Codex (repeatable) | - |
| `--persistent-codex` | Keep a persistent Codex PTY session (advanced) | off |

**Examples:**

```bash
voiceterm --codex               # Use Codex (default)
voiceterm --claude              # Use Claude Code
voiceterm --login --codex       # Login to Codex CLI
voiceterm --login --claude      # Login to Claude CLI
```

**Notes:**

- `--backend` accepts a custom command string, for example: `voiceterm --backend "my-custom-cli --flag"`.
- Gemini is currently nonfunctional. Aider/OpenCode presets are untested. Only Codex and Claude are fully supported.

---

## Microphone & Audio

| Flag | Purpose | Default |
|------|---------|---------|
| `--input-device <NAME>` | Use a specific microphone | system default |
| `--list-input-devices` | Print available audio devices and exit | - |
| `--mic-meter` | Calibration tool: measures ambient noise and speech | - |
| `--mic-meter-ambient-ms <MS>` | Ambient sample duration for calibration | 3000 |
| `--mic-meter-speech-ms <MS>` | Speech sample duration for calibration | 3000 |
| `--doctor` | Print environment diagnostics and exit | - |
| `--ffmpeg-cmd <PATH>` | FFmpeg binary path (python fallback) | ffmpeg |
| `--ffmpeg-device <NAME>` | FFmpeg audio device override (python fallback) | - |

`--input-device` values are normalized before lookup (extra whitespace/newlines collapsed), so pasted multi-line names resolve correctly.

---

## Whisper STT

| Flag | Purpose | Default |
|------|---------|---------|
| `--whisper-model <NAME>` | Model size: `tiny`, `base`, `small`, `medium`, `large` | small |
| `--whisper-model-path <PATH>` | Path to Whisper model file | auto-detected |
| `--lang <LANG>` | Language code (`en`, `es`, `auto`, etc.) | en |
| `--whisper-cmd <PATH>` | Whisper CLI path (python fallback) | whisper |
| `--whisper-beam-size <N>` | Beam search size (0 = greedy) | 0 |
| `--whisper-temperature <T>` | Sampling temperature | 0.0 |
| `--no-python-fallback` | Fail instead of falling back to Python Whisper | off |
| `--voice-stt-timeout-ms <MS>` | Timeout before triggering fallback | 60000 |
| `--python-cmd <PATH>` | Python interpreter for fallback scripts | python3 |
| `--pipeline-script <PATH>` | Python fallback pipeline script (bundled in the install by default) | built-in |

For model-size tradeoffs and troubleshooting details, see [WHISPER.md](WHISPER.md).

---

## Capture Tuning

VAD (voice activity detection) flags control when VoiceTerm starts and stops recording.

| Flag | Purpose | Default |
|------|---------|---------|
| `--voice-vad-threshold-db <DB>` | Mic sensitivity (-120 = very sensitive, 0 = less; hotkeys clamp -80..-10) | -55.0 |
| `--voice-max-capture-ms <MS>` | Max recording duration (max 60000) | 30000 |
| `--voice-silence-tail-ms <MS>` | Silence duration to stop recording | 1000 |
| `--voice-min-speech-ms-before-stt <MS>` | Minimum speech before STT starts | 300 |
| `--voice-lookback-ms <MS>` | Audio kept before silence stop | 200 |
| `--voice-buffer-ms <MS>` | Total audio buffer (max 120000) | 30000 |
| `--voice-sample-rate <HZ>` | Audio sample rate | 16000 |
| `--voice-vad-frame-ms <MS>` | VAD frame size | 20 |
| `--voice-vad-smoothing-frames <N>` | VAD smoothing window | 3 |
| `--voice-vad-engine <earshot\|simple>` | VAD implementation — earshot is the built-in advanced engine | earshot (when built with `vad_earshot`), otherwise `simple` |
| `--voice-channel-capacity <N>` | Internal frame channel capacity | 100 |

---

## Themes & Display

| Flag | Purpose | Default |
|------|---------|---------|
| `--theme <NAME>` | Theme name | backend default |
| `--theme-file <PATH>` | Load theme from a specific TOML file path | unset |
| `--export-theme <NAME>` | Export a built-in theme as TOML to stdout and exit | unset |
| `--no-color` | Disable all colors | off |
| `--hud-style <MODE>` | HUD display style: `full`, `minimal`, `hidden` | full |
| `--minimal-hud` | Shorthand for `--hud-style minimal` | off |
| `--hud-right-panel <MODE>` | Right-side HUD panel: `off`, `ribbon`, `dots`, `heartbeat` | ribbon |
| `--hud-border-style <STYLE>` | Full HUD border style: `theme`, `single`, `rounded`, `double`, `heavy`, `none` | theme |
| `--hud-right-panel-recording-only` | Only animate right panel while recording | on |
| `--latency-display <off\|short\|label>` | Shortcuts-row latency badge style (`off`, `Nms`, or `Latency: Nms`) for completed turns | short |
| `--term <TERM>` | TERM value for the CLI | inherited |

Set `--hud-right-panel-recording-only=false` to keep right-panel animation active while idle.
`--theme-file` uses the same path source as `VOICETERM_THEME_FILE`.
When set, VoiceTerm polls the file (~500ms) and applies valid edits live.

**Themes:** `chatgpt`, `claude`, `codex`, `coral`, `catppuccin`, `dracula`,
`nord`, `tokyonight`, `gruvbox`, `ansi`, `none`.

For HUD runtime behavior and theme details, see [USAGE.md](USAGE.md#hud-styles).

---

## Logging

| Flag | Purpose | Default |
|------|---------|---------|
| `--logs` | Enable debug logging to file | off |
| `--no-logs` | Force disable logging | off |
| `--log-content` | Include transcript snippets in logs | off |
| `--log-timings` | Verbose timing information | off |
| `--session-memory` | Enable markdown session-memory logging (`user` + `assistant` lines) | off |
| `--session-memory-path <PATH>` | Override markdown session-memory log path | `<cwd>/.voiceterm/session-memory.md` |

**Log location:** `$TMPDIR/voiceterm_tui.log` (macOS) or
`/tmp/voiceterm_tui.log` (Linux)

**Session-memory location:** `<cwd>/.voiceterm/session-memory.md` by default,
or `--session-memory-path`.

**Dev-event location (`--dev --dev-log`):** `<dev-path>/sessions/session-*.jsonl`
where `dev-path` defaults to `$HOME/.voiceterm/dev` (or `<cwd>/.voiceterm/dev`
if `HOME` is unavailable).

**Trace log (JSON):** `$TMPDIR/voiceterm_trace.jsonl` (macOS) or
`/tmp/voiceterm_trace.jsonl` (Linux). Override with `VOICETERM_TRACE_LOG`.

---

## IPC / Integration

| Flag | Purpose | Default |
|------|---------|---------|
| `--json-ipc` | Run in JSON IPC mode (external UI integration) | off |
| `--claude-skip-permissions` | Skip Claude permission prompts (IPC only; high-risk) | off |

`--claude-skip-permissions` forwards Claude's
`--dangerously-skip-permissions` behavior. Keep this off unless you are in a
trusted, isolated environment and accept that tool actions may run without
interactive approval prompts.

---

## Sounds

| Flag | Purpose | Default |
|------|---------|---------|
| `--sounds` | Enable all notification sounds | off |
| `--sound-on-complete` | Beep when transcript completes | off |
| `--sound-on-error` | Beep on voice capture error | off |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VOICETERM_CWD` | Run CLI in this directory | current directory |
| `VOICETERM_MODEL_DIR` | Whisper model storage path (used by install/start scripts) | `whisper_models/` or `~/.local/share/voiceterm/models` |
| `VOICETERM_INSTALL_DIR` | Override install location | unset |
| `VOICETERM_NO_STARTUP_BANNER` | Skip the startup splash screen | unset |
| `VOICETERM_STARTUP_SPLASH_MS` | Splash dwell time in milliseconds (0 = immediate, max 30000) | 1500 |
| `VOICETERM_PROMPT_REGEX` | Override prompt detection | unset |
| `VOICETERM_CONFIG_DIR` | Override persistent config directory (`config.toml`) | unset |
| `VOICETERM_ONBOARDING_STATE` | Override first-run onboarding state file path | unset |
| `VOICETERM_PROMPT_LOG` | Prompt detection log path | unset |
| `VOICETERM_IMAGE_CAPTURE_COMMAND` | Default value for `--image-capture-command` | unset |
| `VOICETERM_THEME_FILE` | Same as `--theme-file <PATH>`; load and watch a TOML theme file | unset |
| `VOICETERM_STYLE_PACK_JSON` | Runtime Theme Studio preview payload (`base_theme` lock + supported overrides, including `components.overlay_border` and `components.hud_border`) | unset |
| `VOICETERM_LOGS` | Enable logging (same as `--logs`) | unset |
| `VOICETERM_NO_LOGS` | Disable logging | unset |
| `VOICETERM_LOG_CONTENT` | Allow content in logs | unset |
| `VOICETERM_TRACE_LOG` | Structured trace log path | unset |
| `VOICETERM_DEBUG_INPUT` | Log raw input bytes/events (for terminal compatibility debugging) | unset |
| `VOICETERM_SESSION_MEMORY_PATH` | Default path for `--session-memory-path` | unset |
| `CLAUDE_CMD` | Override Claude CLI path | unset |
| `VOICETERM_PROVIDER` | IPC default provider (`codex` or `claude`) | unset |
| `NO_COLOR` | Disable colors (standard) | unset |

---

## See Also

| Topic | Link |
|-------|------|
| Quick Start | [QUICK_START.md](../QUICK_START.md) |
| Install | [INSTALL.md](INSTALL.md) |
| Usage | [USAGE.md](USAGE.md) |
| Troubleshooting | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
