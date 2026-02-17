<p align="center">
  <img src="img/logo.svg" alt="VoiceTerm" width="900">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Rust-000000?style=for-the-badge&logo=rust&logoColor=white" alt="Rust">
  <img src="https://img.shields.io/badge/Whisper-Voice_Input-8B5CF6?style=for-the-badge&logo=audacity&logoColor=white" alt="Whisper">
  <img src="https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white" alt="macOS">
  <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux">
  <a href="https://github.com/jguida941/voiceterm/releases"><img src="https://img.shields.io/github/v/release/jguida941/voiceterm?display_name=tag&style=for-the-badge&label=VoiceTerm&color=2EA043&labelColor=0D1117" alt="VoiceTerm Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="MIT License"></a>
</p>

<p align="center">
  <a href="https://github.com/jguida941/voiceterm/actions/workflows/rust_ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/jguida941/voiceterm/rust_ci.yml?branch=master&style=for-the-badge&label=CI&logo=github" alt="CI"></a>
  <a href="https://github.com/jguida941/voiceterm/actions/workflows/mutation-testing.yml"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/jguida941/voiceterm/master/.github/badges/mutation-score.json&style=for-the-badge&logo=github" alt="Mutation Score"></a>
</p>

Voice input for AI CLIs. Talk instead of type.
Runs Whisper locally with ~250ms latency. No cloud, no API keys.

## Quick Nav

- [Install and Start](#install-and-start)
- [How It Works](#how-it-works)
- [Requirements](#requirements)
- [Supported AI CLIs](#supported-ai-clis)
- [UI Tour](#ui-tour)
- [Controls](#controls)
- [Guides Index](guides/README.md)
- [Engineering History](dev/history/ENGINEERING_EVOLUTION.md)
- [Developer Index](dev/README.md)
- [Documentation](#documentation)
- [Support](#support)

## Install and Start

Install one supported AI CLI first:

**Codex:**

```bash
npm install -g @openai/codex
```

**Claude Code:**

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Then choose one VoiceTerm setup path:

<details open>
<summary><strong>Homebrew (recommended)</strong></summary>

```bash
brew tap jguida941/voiceterm
brew install voiceterm
cd ~/your-project
voiceterm
```

If needed, authenticate once:

```bash
voiceterm --login --codex
voiceterm --login --claude
```

</details>

<details>
<summary><strong>PyPI (pipx / pip)</strong></summary>

```bash
pipx install voiceterm
# or: python3 -m pip install --user voiceterm

cd ~/your-project
voiceterm
```

If needed, authenticate once:

```bash
voiceterm --login --codex
voiceterm --login --claude
```

</details>

<details>
<summary><strong>From source</strong></summary>

```bash
git clone https://github.com/jguida941/voiceterm.git
cd voiceterm
./scripts/install.sh
```

</details>

<details>
<summary><strong>macOS App</strong></summary>

Double-click `app/macos/VoiceTerm.app`, pick a folder, and it opens Terminal
with VoiceTerm running.
</details>

For model options and startup/IDE tuning:

- [Install Guide](guides/INSTALL.md)
- [Whisper docs](guides/WHISPER.md)
- [Troubleshooting](guides/TROUBLESHOOTING.md)

## How It Works

```mermaid
graph TD
    A["Microphone"] --> B["Whisper STT"]
    B --> C["Transcript"]
    C --> D["PTY"]
    D --> E["AI CLI"]
    E --> F["Terminal Output"]
```

VoiceTerm wraps your AI CLI in a PTY and adds voice input.
You talk → Whisper transcribes locally → text gets typed into the CLI.
All CLI output passes through unchanged.

## Requirements

- macOS or Linux (Windows needs WSL2)
- Microphone access
- ~0.5 GB disk for the default small model (base is ~142 MB, medium is ~1.5 GB)

## Features

| Feature | Description |
|---------|-------------|
| **Local STT** | Whisper runs on your machine - no cloud calls |
| **~250ms latency** | Fast transcription through whisper.cpp |
| **PTY passthrough** | CLI UI stays unchanged |
| **Auto-voice** | Hands-free mode - no typing needed |
| **Transcript queue** | Speak while CLI is busy, types when ready |
| **Project voice macros** | Expand trigger phrases from `.voiceterm/macros.yaml` before typing |
| **Macros toggle** | Runtime ON/OFF control for macro expansion from Settings |
| **Built-in voice navigation** | Spoken actions for scroll up/down, show/copy last error, and explain last error |
| **Adaptive HUD telemetry** | Compact meter/latency trend chips that adapt to recording, busy, and idle states |
| **Backends** | Primary support for Codex and Claude Code |
| **Themes** | 11 built-in themes including ChatGPT, Catppuccin, Dracula, Nord, Tokyo Night, Gruvbox |

## Voice Recording

![Recording](img/recording.png)

## Supported AI CLIs

VoiceTerm is optimized for Codex and Claude Code.
For canonical backend support status and experimental backend notes, see
[Usage Guide -> Backend Support](guides/USAGE.md#backend-support).
For backend configuration details, see the [Usage Guide](guides/USAGE.md).

### Codex

```bash
npm install -g @openai/codex
voiceterm
voiceterm --codex   # explicit (optional)
voiceterm --login --codex
```

![Codex Backend](img/codex-backend.png)

### Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
voiceterm --claude
voiceterm --login --claude
```

![Claude Backend](img/claude-backend.png)

## UI Tour

### Theme Picker

![Theme Picker](img/theme-picker.png)
Use `Ctrl+Y` to open the picker (or `Ctrl+G` to quick-cycle themes), then use
↑/↓ to move and Enter to select, or type the theme number.

### Settings Menu

![Settings](img/settings.png)

Mouse control is enabled by default, and Settings (`Ctrl+O`) covers the main
runtime toggles: send mode, auto-voice, macros, HUD style/border, right-panel
telemetry, latency display, and wake-word controls (wake toggle,
sensitivity, cooldown; default OFF).
In Full HUD mode, the right-panel visualizer (`Ribbon`, `Dots`, `Heartbeat`)
is shown on the main status row (top-right lane).
On `xterm-256color` terminals, VoiceTerm now keeps your selected theme
instead of forcing ANSI fallback (ANSI fallback remains for ANSI16 terminals).
See the [Usage Guide](guides/USAGE.md) for full behavior and configuration details.

## Controls

For complete keybindings and behavior details, see:

- [Core Controls](guides/USAGE.md#core-controls)
- [Settings Menu](guides/USAGE.md#settings-menu)
- [Voice Modes](guides/USAGE.md#voice-modes)

Short version: `Ctrl+G` quick-cycles theme, and built-in voice commands support
`scroll up`, `scroll down`, `show last error`, `copy last error`, and
`explain last error`.
Recording/send controls: `Ctrl+R` toggles recording start/stop, and in insert
mode `Ctrl+E` sends staged text immediately; if recording with no staged text,
it stops early and submits when transcription completes; if idle with no staged
text, it is consumed as a no-op. `Enter` remains submit-only for staged text.
Latency badge shows direct STT delay (`stt_ms`) when available, hides on
no-speech/error captures, and auto-expires stale idle values after a short
window; severity color uses speech-relative speed (`rtf`) when speech metrics
exist.
Hidden HUD launcher text, `[open]`, and recording indicator use intentionally
muted/dull gray so hidden mode stays out of the way.
If a macro and built-in phrase overlap, macros run first; use explicit
`voice scroll up` / `voice scroll down` to force built-in navigation.
Status text is pipeline-neutral (for example `Listening Manual Mode` and
`No speech detected`); check Settings (`Ctrl+O`) for `Voice pipeline`.
If you are validating pre-release builds, use `Testing_Guide.md` sections `3`,
`3A`, and `4A` to verify process cleanup, CPU stability, and high-load UI
responsiveness.

## Engineering History

Want the design and process timeline?

- [Engineering Evolution and SDLC Timeline](dev/history/ENGINEERING_EVOLUTION.md)
- [Developer Index](dev/README.md)

## Voice Macros

Voice macros are project-local voice shortcuts defined in
`.voiceterm/macros.yaml`.

Startup default: `Settings -> Macros` starts as `OFF` (safe mode). Turn it on
when you want macro expansion.

Quick setup:

```bash
# Interactive wizard (recommended)
./scripts/macros.sh wizard

# or generate a pack directly
./scripts/macros.sh install --pack safe-core
```

Packs:

- `safe-core`: low-risk git/GitHub inspection commands
- `power-git`: write actions (commit/push/PR/issue) in `insert` mode by default
- `full-dev`: safe-core + power-git + codex-voice maintainer checks/release helpers

If you use GitHub macros, the wizard checks `gh` availability/auth and can
prompt for `gh auth login`.

Example:

- You say: `run tests`
- VoiceTerm types: `cargo test --all-features`

When it runs:

- `Settings -> Macros = ON`: if a spoken trigger matches, VoiceTerm expands it
  before typing into the CLI.
- `Settings -> Macros = OFF`: VoiceTerm skips expansion and types your
  transcript exactly as spoken.

See [Project Voice Macros](guides/USAGE.md#project-voice-macros) for the file
format, templates, and matching rules.

This repository includes a starter macro pack at `.voiceterm/macros.yaml` with
expanded git/GitHub voice workflows plus codex-voice check/release commands.

## Documentation

Use this order if you're new:

1. Start with [Quick Start](QUICK_START.md).
2. Use the [Guides Index](guides/README.md) for task-based navigation.
3. Use [Troubleshooting](guides/TROUBLESHOOTING.md) as the single issue hub.

| Users | Developers |
|-------|------------|
| [Guides Index](guides/README.md) | [Developer Index](dev/README.md) |
| [Quick Start](QUICK_START.md) | [Engineering History](dev/history/ENGINEERING_EVOLUTION.md) |
| [Install Guide](guides/INSTALL.md) | [Master Plan](dev/active/MASTER_PLAN.md) |
| [Usage Guide](guides/USAGE.md) | [Development](dev/DEVELOPMENT.md) |
| [CLI Flags](guides/CLI_FLAGS.md) | [Architecture](dev/ARCHITECTURE.md) |
| [Whisper & Languages](guides/WHISPER.md) | [ADRs](dev/adr/README.md) |
| [Troubleshooting Hub](guides/TROUBLESHOOTING.md) | [Changelog](dev/CHANGELOG.md) |
| [User Scripts](scripts/README.md) | [Dev Scripts](dev/scripts/README.md) |
| [Contributing](.github/CONTRIBUTING.md) | [History Index](dev/history/README.md) |

## Support

- Troubleshooting: [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)
- Bug reports and feature requests: [GitHub Issues](https://github.com/jguida941/voiceterm/issues)
- Security concerns: [.github/SECURITY.md](.github/SECURITY.md)

## Contributing

PRs welcome. See [CONTRIBUTING.md](.github/CONTRIBUTING.md).
Before opening a PR, run `python3 dev/scripts/devctl.py check --profile prepush`.
For governance/docs consistency, also run `python3 dev/scripts/devctl.py hygiene`.

## License

MIT - [LICENSE](LICENSE)
