<p align="center">
  <img src="img/logo-hero-transparent.png" alt="VoiceTerm" width="740">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Rust-stable?style=flat&logo=rust&logoColor=white&labelColor=7C422B&color=2D2F34&logoSize=auto" alt="Rust">
  <img src="https://img.shields.io/badge/macOS-supported?style=flat&logo=apple&logoColor=white&labelColor=7C422B&color=2D2F34&logoSize=auto" alt="macOS">
  <img src="https://img.shields.io/badge/Linux-supported?style=flat&logo=linux&logoColor=white&labelColor=7C422B&color=2D2F34&logoSize=auto" alt="Linux">
  <img src="https://img.shields.io/static/v1?label=Whisper&message=local&style=flat&labelColor=7C422B&color=2D2F34" alt="Whisper">
  <a href="https://ratatui.rs"><img src="https://img.shields.io/badge/Ratatui-native?style=flat&logo=ratatui&logoColor=white&labelColor=7C422B&color=2D2F34&logoSize=auto" alt="Ratatui"></a>
</p>

<p align="center">
  <a href="https://github.com/jguida941/voiceterm/releases"><img src="https://img.shields.io/github/v/tag/jguida941/voiceterm?sort=semver&style=flat&label=release&labelColor=7C422B&color=2D2F34" alt="VoiceTerm Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/static/v1?label=license&message=MIT&style=flat&labelColor=7C422B&color=2D2F34" alt="MIT License"></a>
  <a href="https://github.com/jguida941/voiceterm/actions/workflows/rust_ci.yml"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/jguida941/voiceterm/master/.github/badges/ci-status.json&style=flat&label=ci&labelColor=7C422B&color=2D2F34&logo=github&logoColor=white&logoSize=auto" alt="CI"></a>
  <a href="https://github.com/jguida941/voiceterm/actions/workflows/rust_ci.yml"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/jguida941/voiceterm/master/.github/badges/clippy-warnings.json&style=flat&label=clippy&labelColor=7C422B&color=2D2F34&logo=rust&logoColor=white&logoSize=auto" alt="Clippy Warnings"></a>
  <a href="https://github.com/jguida941/voiceterm/actions/workflows/mutation-testing.yml"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/jguida941/voiceterm/master/.github/badges/mutation-score.json&style=flat&label=mutation&labelColor=7C422B&color=2D2F34&logo=github&logoColor=white&logoSize=auto" alt="Mutation Score"></a>
  <a href="https://codecov.io/gh/jguida941/voiceterm"><img src="https://img.shields.io/codecov/c/github/jguida941/voiceterm?style=flat&label=coverage&labelColor=7C422B&color=2D2F34&logo=codecov&logoColor=white&logoSize=auto" alt="Coverage"></a>
</p>

Low-latency Rust terminal overlay for Codex and Claude Code with local Whisper
STT, PTY passthrough, wake words, macros, and a customizable HUD.

Whisper runs locally by default — no cloud API keys required.
Release history: [CHANGELOG](dev/CHANGELOG.md).

If you are new, use this path:

1. [Quick Start](QUICK_START.md)
2. [Install Guide](guides/INSTALL.md)
3. [Usage Guide](guides/USAGE.md)
4. [Troubleshooting](guides/TROUBLESHOOTING.md)

## Quick Nav

- [Install and Start](#install-and-start)
- [How It Works](#how-it-works)
- [Hands-Free Quick Start](#hands-free-quick-start)
- [Features](#features)
- [Supported Backends](#supported-ai-clis)
- [IDE Support](#ide-support)
- [UI Overview](#ui-overview)
- [Controls](#controls)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [For Developers](#for-developers)
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

If you are running from source while developing, run:

```bash
python3 dev/scripts/devctl.py check --profile ci
```

Optional advanced tools from the same checkout:

- [Operator Console README](app/operator_console/README.md)
- [iOS README](app/ios/README.md)
- [Install Guide: optional source-only tools](guides/INSTALL.md#optional-operator-console-source-checkout)

</details>

<details>
<summary><strong>macOS App</strong></summary>

Double-click `app/macos/VoiceTerm.app`, pick a folder, and it opens Terminal
with VoiceTerm running.
</details>

For model options and startup tuning:

- [Install Guide](guides/INSTALL.md)
- [Whisper docs](guides/WHISPER.md)
- [Troubleshooting](guides/TROUBLESHOOTING.md)

## How It Works

VoiceTerm listens to your mic, converts speech to text on your machine, and
types the result into your AI CLI input.

![Recording](img/auto-record.png)

## Requirements

- macOS or Linux (Windows needs WSL2)
- Microphone access
- ~0.5 GB disk for the default small model (base is ~142 MB, medium is ~1.5 GB)

## Hands-Free Quick Start

VoiceTerm supports a fully hands-free workflow — no typing needed at all.

```bash
voiceterm --auto-voice --wake-word --voice-send-mode insert
```

1. Say the wake phrase (`hey codex` or `hey claude`)
2. Speak your prompt
3. Say `send` or `submit` to deliver it

## Features

### Main features

| Feature | What it does |
|---------|---------------|
| **Local speech-to-text** | Whisper runs on your machine — no cloud calls needed |
| **Fast voice-to-text** | Local Whisper turns speech into text quickly |
| **Keep your CLI as-is** | Your backend CLI layout and behavior stay the same |
| **Auto voice mode** | Keep listening on so you can talk instead of typing |
| **Wake mode + voice send** | Say `hey codex`/`hey claude`, then say `send`/`submit` |
| **Image prompts** | Use `Ctrl+X` for screenshot prompts, or enable persistent image mode |
| **Transcript queue** | If the CLI is busy, VoiceTerm waits and sends text when ready |
| **Codex + Claude support** | Primary support for Codex and Claude Code |

### Everyday tools

| Tool | What it does |
|------|--------------|
| **Voice navigation** | Spoken `scroll`, `send`, `show last error`, `copy last error`, `explain last error` |
| **Voice macros** | Expand phrases from `.voiceterm/macros.yaml` — see [Voice Macros](#voice-macros) |
| **Built-in themes** | 11 themes including ChatGPT, Catppuccin, Dracula, Nord, Tokyo Night, and Gruvbox |
| **Transcript history** | `Ctrl+H` to search and replay past text |
| **Notification history** | `Ctrl+N` to review recent status messages |
| **Saved settings** | Stored in `~/.config/voiceterm/config.toml` |
| **HUD controls** | Mouse and keyboard both work by default |

For full details: [Usage Guide](guides/USAGE.md).

## Supported AI CLIs

VoiceTerm is optimized for Codex and Claude Code.
For full backend status and setup details, see
[Usage Guide — Backend Support](guides/USAGE.md#backend-support).

| Backend | Status | Notes |
|---|---|---|
| Codex | Supported | Default backend |
| Claude Code | Supported | Full support on current releases |
| Gemini CLI | Experimental | Not working in current releases |
| Other/custom backends | Experimental | See the usage guide for current limits |

![Claude Backend](img/claude-backend.png)

## IDE Support

| IDE host | Codex | Claude Code | Notes |
|---|---|---|---|
| Cursor terminal | Fully supported | Fully supported | Recommended host |
| JetBrains terminals (IntelliJ, PyCharm, WebStorm, CLion) | Fully supported | Fully supported | Claude may need a one-time terminal resize after long outputs — see [Troubleshooting](guides/TROUBLESHOOTING.md#jetbrains--claude-overlay-overlap-after-long-parallel-output) |
| AntiGravity | Not yet supported | Not yet supported | Not available in current releases |
| Other IDE terminals | Unverified | Unverified | Treat as experimental |

For more IDE details: [Usage Guide — IDE Compatibility](guides/USAGE.md#ide-compatibility).

## UI Overview

### Theme Picker

![Theme Picker](img/theme-picker.png)

For details: [Themes](guides/USAGE.md#themes) ·
[CLI Flags](guides/CLI_FLAGS.md#themes--display).

### Settings Menu

![Settings](img/settings.png)

For details: [Settings Menu](guides/USAGE.md#settings-menu) ·
[Themes](guides/USAGE.md#themes) ·
[HUD styles](guides/USAGE.md#hud-styles).

### Transcript History

`Ctrl+H` opens transcript history where you can search and replay past inputs.

![Transcript History](img/transcript-history.png)

For details: [Transcript History](guides/USAGE.md#transcript-history).

### Shortcuts Overlay

Press `Shift+?` to open the shortcuts overlay with grouped hotkeys and
clickable links to Docs and Troubleshooting.

![Shortcuts Overlay](img/shortcuts.png)

For details: [Core Controls](guides/USAGE.md#core-controls).

## Controls

For shortcuts and behavior, see:

- [Core Controls](guides/USAGE.md#core-controls)
- [Settings Menu](guides/USAGE.md#settings-menu)
- [Voice Modes](guides/USAGE.md#voice-modes)

For CLI flags and command-line options:

- `voiceterm --help` (or `voiceterm -h`)
- [CLI Flags](guides/CLI_FLAGS.md)

## Voice Macros

***Note: Voice macros are still in development and may have rough edges.***

Voice macros are project-local shortcuts in `.voiceterm/macros.yaml`.
Turn macros on in Settings when you want phrase expansion.
Setup and examples: [Project Voice Macros](guides/USAGE.md#project-voice-macros).

<!-- TODO: add screenshot of voice macros in action -->

## Documentation

Start with the shortest useful doc for your goal:

| Audience | Document |
|---|---|
| User | [Quick Start](QUICK_START.md) |
| User | [Guides Index](guides/README.md) |
| User | [Install Guide](guides/INSTALL.md) |
| User | [Usage Guide](guides/USAGE.md) |
| User | [CLI Flags](guides/CLI_FLAGS.md) |
| User | [Troubleshooting](guides/TROUBLESHOOTING.md) |
| Advanced | [Operator Console (optional PyQt6 app)](app/operator_console/README.md) |

## Contributing

PRs welcome. See [CONTRIBUTING.md](.github/CONTRIBUTING.md).
Before opening a PR, run:

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py docs-check --user-facing`
- `python3 dev/scripts/devctl.py hygiene`

## For Developers

Looking to contribute or dig into the codebase?

- [Developer Index](dev/README.md) — tooling, architecture, and dev guides
- [Development Guide](dev/guides/DEVELOPMENT.md) — build, test, and CI instructions
- [Operator Console README](app/operator_console/README.md) — optional PyQt6 shared-screen app and launcher usage

**When do I run what?**

| When | Command |
|------|---------|
| Quick sanity check while coding | `python3 dev/scripts/devctl.py check --profile quick` |
| Before pushing to GitHub | `python3 dev/scripts/devctl.py check --profile prepush` |
| Full CI-equivalent check locally | `python3 dev/scripts/devctl.py check --profile ci` |
| Rust tests only | `cd rust && cargo test --bin voiceterm` |
| Python tests only | `python3 -m pytest dev/scripts/devctl/tests/ -q` |
| Check docs are up to date | `python3 dev/scripts/devctl.py docs-check --strict-tooling` |
| Governance / archive hygiene | `python3 dev/scripts/devctl.py hygiene` |
| See project status | `python3 dev/scripts/devctl.py status` |
| List all devctl commands | `python3 dev/scripts/devctl.py list` |

For all available commands, what they do, and when to use them: [devctl guide](dev/scripts/README.md).

## Support

- Troubleshooting:
  [guides/TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md)
- Bug reports and feature requests:
  [GitHub Issues](https://github.com/jguida941/voiceterm/issues)
- Security concerns:
  [.github/SECURITY.md](.github/SECURITY.md)

## License

MIT - [LICENSE](LICENSE)
