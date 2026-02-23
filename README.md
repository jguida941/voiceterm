<p align="center">
  <img src="img/logo-hero-transparent.png" alt="VoiceTerm" width="740">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Rust-stable?style=flat&logo=rust&logoColor=white&labelColor=7C422B&color=2D2F34&logoSize=auto" alt="Rust">
  <img src="https://img.shields.io/badge/macOS-supported?style=flat&logo=apple&logoColor=white&labelColor=7C422B&color=2D2F34&logoSize=auto" alt="macOS">
  <img src="https://img.shields.io/badge/Linux-supported?style=flat&logo=linux&logoColor=white&labelColor=7C422B&color=2D2F34&logoSize=auto" alt="Linux">
  <img src="https://img.shields.io/badge/Whisper-local?style=flat&logo=openai&logoColor=white&labelColor=7C422B&color=2D2F34&logoSize=auto" alt="Whisper">
  <a href="https://ratatui.rs"><img src="https://img.shields.io/badge/Ratatui-native?style=flat&logo=ratatui&logoColor=white&labelColor=7C422B&color=2D2F34&logoSize=auto" alt="Ratatui"></a>
</p>

<p align="center">
  <a href="https://github.com/jguida941/voiceterm/releases"><img src="https://img.shields.io/github/v/tag/jguida941/voiceterm?sort=semver&style=flat&label=release&labelColor=7C422B&color=2D2F34" alt="VoiceTerm Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT?style=flat&labelColor=7C422B&color=2D2F34" alt="MIT License"></a>
  <a href="https://github.com/jguida941/voiceterm/actions/workflows/rust_ci.yml"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/jguida941/voiceterm/master/.github/badges/ci-status.json&style=flat&label=ci&labelColor=7C422B&color=2D2F34&logo=github&logoColor=white&logoSize=auto" alt="CI"></a>
  <a href="https://github.com/jguida941/voiceterm/actions/workflows/mutation-testing.yml"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/jguida941/voiceterm/master/.github/badges/mutation-score.json&style=flat&label=mutation&labelColor=7C422B&color=2D2F34&logo=github&logoColor=white&logoSize=auto" alt="Mutation Score"></a>
  <a href="https://codecov.io/gh/jguida941/voiceterm"><img src="https://img.shields.io/codecov/c/github/jguida941/voiceterm?style=flat&label=coverage&labelColor=7C422B&color=2D2F34&logo=codecov&logoColor=white&logoSize=auto" alt="Coverage"></a>
</p>

Voice input for AI CLIs. Talk instead of type.
Runs Whisper locally with ~250ms latency. No cloud, no API keys.
Current stable release: `v1.0.89` (2026-02-23). Full release notes: [dev/CHANGELOG.md](dev/CHANGELOG.md).

Recent runtime updates:

- Theme Studio now supports in-session style-pack override recovery via `Undo edit`, `Redo edit`, and `Rollback edits`.
- Wake listener startup failures now show explicit HUD/state feedback (`Wake: ERR`) instead of a false-ready wake badge.
- Full HUD `Wake: ON` now renders as a steady status badge and wake listener capture windows are longer to reduce mic indicator flapping on macOS.
- `--input-device` values are normalized before lookup, so wrapped copy/paste device names are handled reliably.

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

Requires Rust toolchain. See [Install Guide](guides/INSTALL.md) for details.

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
    A["Microphone"] --> B["Whisper Speech-to-Text"]
    B --> C["Transcript"]
    C --> D["Terminal Session"]
    D --> E["AI CLI"]
    E --> F["Terminal Output"]
```

VoiceTerm wraps your AI CLI in a virtual terminal session and adds voice input.
You talk → Whisper transcribes locally → text gets typed into the CLI.
All CLI output passes through unchanged.

![Recording](img/recording.png)

## Requirements

- macOS or Linux (Windows needs WSL2)
- Microphone access
- ~0.5 GB disk for the default small model (base is ~142 MB, medium is ~1.5 GB)

## Features

### Main features

| Feature | What it does |
|---------|---------------|
| **Local speech-to-text** | Whisper runs on your machine (no cloud calls) |
| **Fast voice-to-text** | A local Whisper engine turns speech into text quickly |
| **Terminal passthrough** | Your CLI layout and behavior stay the same |
| **Auto-voice** | You can talk hands-free instead of typing |
| **Transcript queue** | If the CLI is busy, VoiceTerm waits and sends text when ready |
| **Codex + Claude support** | Primary support for Codex and Claude Code |

### Everyday tools

- **Voice macros**: expand phrases from `.voiceterm/macros.yaml` and toggle them on/off in Settings
- **Voice navigation**: spoken `scroll`, `show last error`, `copy last error`, and `explain last error`
- **Transcript history**: use `Ctrl+H` to search and replay past text into the active CLI
- **Notification history**: use `Ctrl+N` to review recent status notifications
- **Saved settings**: keeps runtime settings in `~/.config/voiceterm/config.toml` (CLI flags still override per run)
- **Claude prompt safety**: hides the HUD during Claude approval/permission prompts so prompt lines stay readable
- **HUD telemetry**: mic/latency chips for recording, busy, and idle states
- **Built-in themes**: 11 themes including ChatGPT, Catppuccin, Dracula, Nord, Tokyo Night, and Gruvbox

For full behavior details and controls, see [guides/USAGE.md](guides/USAGE.md).

## Supported AI CLIs

VoiceTerm is optimized for Codex and Claude Code.
For canonical backend support status and experimental backend notes, see
[Usage Guide -> Backend Support](guides/USAGE.md#backend-support).
For backend configuration details, see the [Usage Guide](guides/USAGE.md).

### Codex

![Codex Backend](img/codex-backend.png)

### Claude Code

![Claude Backend](img/claude-backend.png)

## UI Tour

### Theme Picker

![Theme Picker](img/theme-picker.png)
Use `Ctrl+Y` to open Theme Studio, then choose `Theme picker`
(or use `Ctrl+G` to quick-cycle themes). In the picker, use
↑/↓ to move and Enter to select, or type the theme number.

### Settings Menu

![Settings](img/settings.png)

Mouse control is enabled by default. Open Settings with `Ctrl+O`.
For full behavior and configuration details, use:

- [Settings Menu](guides/USAGE.md#settings-menu)
- [Themes](guides/USAGE.md#themes)
- [HUD styles](guides/USAGE.md#hud-styles)

### Transcript History

Use `Ctrl+H` to open transcript history, type to filter, and press `Enter` to
replay into the active CLI input. Mouse click selection is also supported.
History rows are labeled by source (`mic`, `you`, `ai`); only `mic` and `you`
rows are replayable, and `ai` rows are output-only.
Use `--session-memory` (optionally `--session-memory-path`) for a persistent
markdown session log alongside the in-app history overlay.
Detailed behavior: [Transcript History](guides/USAGE.md#transcript-history).

### Help Overlay

Press `?` to open grouped shortcuts (`Recording`, `Mode`, `Appearance`,
`Sensitivity`, `Navigation`) with clickable Docs/Troubleshooting links on
terminals that support clickable links. Details: [Core Controls](guides/USAGE.md#core-controls).

## Controls

For keybindings and runtime behavior, see:

- [Core Controls](guides/USAGE.md#core-controls)
- [Settings Menu](guides/USAGE.md#settings-menu)
- [Voice Modes](guides/USAGE.md#voice-modes)

For CLI flags and command-line options:

- `voiceterm --help` (or `voiceterm -h`)
- [CLI Flags](guides/CLI_FLAGS.md)

Related docs:

- [Usage Guide](guides/USAGE.md)
- [Changelog](dev/CHANGELOG.md)
- [Development](dev/DEVELOPMENT.md)

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

<details>
<summary><strong>More macro details (packs, examples, and rules)</strong></summary>

Packs:

- `safe-core`: low-risk git/GitHub inspection commands
- `power-git`: write actions (commit/push/PR/issue) in `insert` mode by default
- `full-dev`: safe-core + power-git + project checks and release helpers

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

</details>

This repository includes a starter macro pack at `.voiceterm/macros.yaml` with
expanded git/GitHub voice workflows plus codex-voice check/release commands.

## Engineering History

Want the design and process timeline?

- [Engineering Evolution and SDLC Timeline](dev/history/ENGINEERING_EVOLUTION.md)
- [Developer Index](dev/README.md)

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
