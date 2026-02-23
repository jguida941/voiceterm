# Installation

This doc covers install options and model setup.
Recommended: Homebrew on macOS/Linux for a global `voiceterm` command.
Current stable release: `v1.0.89` (2026-02-23). Full release notes: [../dev/CHANGELOG.md](../dev/CHANGELOG.md).

Related docs:
[Quick Start](../QUICK_START.md) |
[Usage](USAGE.md) |
[Troubleshooting](TROUBLESHOOTING.md) |
[CLI Flags](CLI_FLAGS.md)

## Platform Support

| Platform | Status | Install Method |
|----------|--------|----------------|
| **macOS** (Intel/Apple Silicon) | ✅ Supported | Homebrew (recommended), App, Source |
| **Linux** (x86_64/arm64) | ✅ Supported | Homebrew (recommended), Source |
| **Windows** | ⚠️ WSL2 only | Use Linux instructions in WSL2 |

## Contents

- [Prerequisites](#prerequisites)
- [Choose an Install Path](#choose-an-install-path)
- [Option A: Homebrew (recommended)](#option-a-homebrew-recommended)
- [Option B: PyPI](#option-b-pypi)
- [Option C: Install from source](#option-c-install-from-source)
- [Option D: macOS App (folder picker)](#option-d-macos-app-folder-picker)
- [Option E: Manual run (no install)](#option-e-manual-run-no-install)
- [Option F: Windows (WSL2 only)](#option-f-windows-wsl2-only)
- [After install: run in your project](#after-install-run-in-your-project)
- [Optional: Macro Wizard](#optional-macro-wizard)
- [See Also](#see-also)

## Prerequisites

**AI CLI (choose one):**

| CLI | Install Command |
|-----|-----------------|
| Codex (default) | `npm install -g @openai/codex` |
| Claude Code | `bash -c "$(curl -fsSL https://claude.ai/install.sh)"` |

Authenticate once after installing your CLI:

```bash
voiceterm --login --codex
voiceterm --login --claude
```

**Other requirements:**

- Microphone access
- Whisper model file downloaded on first run
- Disk space for models: `tiny.en` ~75 MB, `base.en` ~142 MB, `small.en` ~466 MB, `medium.en` ~1.5 GB, `large` ~3.1 GB
- Rust toolchain (stable) only if you build from source: <https://rustup.rs>
- Optional: `python3`, `ffmpeg`, and `whisper` CLI on PATH (used as backup if native engine is unavailable; disable with `--no-python-fallback`)

Input-device note:

- If you copy/paste a device name from wrapped terminal output, `--input-device` now normalizes embedded whitespace/newlines before runtime lookup.

## Choose an Install Path

| If you want... | Choose | Why |
|----------------|--------|-----|
| Easiest global install and upgrades | **Homebrew** | Best default on macOS/Linux with `brew upgrade` updates |
| Python-managed CLI install | **PyPI (`pipx`)** | Isolated Python tool install, then bootstrap native binary on first run |
| Full local control / development workflow | **From source** | Build and modify directly from this repository |
| Finder-based launch on macOS | **macOS App** | Folder picker launches VoiceTerm without terminal setup steps |
| No install, one-off run | **Manual run** | Use the repo scripts directly from any directory |

## Option A: Homebrew (recommended)

<details open>
<summary><strong>Show Homebrew steps</strong></summary>

Install Homebrew (if needed):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Tap and install:

```bash
brew tap jguida941/voiceterm
brew install voiceterm
```

Run from any project (first run downloads the model if missing):

```bash
cd ~/my-project
voiceterm
```

Model storage defaults to `~/.local/share/voiceterm/models` for Homebrew installs
(or when the repo directory is not writable). The install/start scripts honor
`VOICETERM_MODEL_DIR` for a custom path.
Homebrew upgrades should reuse this directory, so the Whisper model is not
redownloaded on each version bump unless the file is missing.

Optional pre-download:

```bash
$(brew --prefix)/opt/voiceterm/libexec/scripts/setup.sh models --base
```

### Homebrew update

```bash
brew update
brew upgrade voiceterm
```

If Homebrew still shows an older version or `voiceterm` runs an older binary, see
[Troubleshooting: Wrong version after update](TROUBLESHOOTING.md#wrong-version-after-update).

After upgrading, run `voiceterm --version` to confirm.

Detailed runtime behavior is documented in [USAGE.md](USAGE.md). Runtime issues
and terminal-specific edge cases are documented in
[TROUBLESHOOTING.md](TROUBLESHOOTING.md).

</details>

## Option B: PyPI

<details>
<summary><strong>Show PyPI steps</strong></summary>

Install with pipx (recommended for isolated CLI tools):

```bash
pipx install voiceterm
```

Or with pip:

```bash
python3 -m pip install --user voiceterm
```

Then run:

```bash
voiceterm --version
```

PyPI project page:

- <https://pypi.org/project/voiceterm/>

PyPI launcher note:

- The package installs a Python launcher named `voiceterm`.
- On first run it bootstraps the native Rust binary into
  `~/.local/share/voiceterm/native/bin/voiceterm`.
- Bootstrap requires `git` and `cargo` on PATH.
- If you already have a native binary installed, set:
  `VOICETERM_NATIVE_BIN=/absolute/path/to/voiceterm`.

</details>

## Option C: Install from source

<details>
<summary><strong>Show source install steps</strong></summary>

Recommended if you want a local build or plan to hack on VoiceTerm.

```bash
git clone https://github.com/jguida941/voiceterm.git
cd voiceterm
./scripts/install.sh
```

The installer builds the overlay, installs the `voiceterm` wrapper, and downloads
a Whisper model to the correct path for the CLI.

For startup splash options, see [USAGE.md - Startup splash behavior](USAGE.md#startup-splash-behavior).

Example output:

![Installer Output](../img/install.png)

To choose a model size during install:

```bash
./scripts/install.sh --tiny
./scripts/install.sh --small
./scripts/install.sh --medium
```

To launch macro setup from install:

```bash
./scripts/install.sh --with-macros-wizard
./scripts/install.sh --with-macros-wizard --macros-pack full-dev
```

### PATH notes

If `voiceterm` is not found, the installer used the first writable directory in
this order: `/opt/homebrew/bin`, `/usr/local/bin`, `~/.local/bin`, or
`/path/to/voiceterm/bin`.

Add that directory to PATH or set `VOICETERM_INSTALL_DIR` before running
`./scripts/install.sh`.

If a `voiceterm` command already exists in `/opt/homebrew/bin` or
`/usr/local/bin`, the installer skips that location to avoid clobbering
system/Homebrew installs. In `~/.local/bin` or the repo `bin/` directory it
will overwrite. Remove the conflicting binary or set `VOICETERM_INSTALL_DIR`
to override.

</details>

## Option D: macOS App (folder picker)

<details>
<summary><strong>Show macOS app steps</strong></summary>

1. Double-click **app/macos/VoiceTerm.app**.
2. Pick your project folder.
3. A Terminal window opens and runs the overlay inside that folder.

![Folder Picker](../img/folder-picker.png)

</details>

## Option E: Manual run (no install)

<details>
<summary><strong>Show manual run steps</strong></summary>

Run from any project folder:

```bash
VOICETERM_CWD="$(pwd)" /path/to/voiceterm/scripts/start.sh
```

`scripts/start.sh` handles model download and setup when needed.

</details>

## Option F: Windows (WSL2 only)

<details>
<summary><strong>Show Windows (WSL2) steps</strong></summary>

Windows native is not supported (VoiceTerm requires a Unix terminal).
Use a Linux environment in WSL2:

1. Install WSL2 + Ubuntu.
2. Open a WSL terminal.
3. Follow one Linux install path in this doc (Homebrew, PyPI, source, or manual run).
4. Run VoiceTerm inside WSL:

   ```bash
   cd ~/my-project
   voiceterm
   ```

</details>

## After install: run in your project

VoiceTerm works with any codebase. Run from your project directory or set
`VOICETERM_CWD` to force the working directory.

```bash
cd ~/my-project
voiceterm
```

To target Claude instead of Codex:

```bash
voiceterm --claude
```

## Optional: Macro Wizard

Use the macro wizard if you want project-local voice command packs:

```bash
./scripts/macros.sh wizard
```

Run wizard during source install:

```bash
./scripts/install.sh --with-macros-wizard
./scripts/install.sh --with-macros-wizard --macros-pack full-dev
```

Canonical macro docs and pack details:

- [USAGE.md - Project Voice Macros](USAGE.md#project-voice-macros)
- [scripts/README.md - macros.sh](../scripts/README.md#macrossh)

Common next steps:

- Voice controls and behavior: [USAGE.md](USAGE.md)
- Voice macros setup and packs: [USAGE.md#project-voice-macros](USAGE.md#project-voice-macros)
- Built-in voice navigation commands: [USAGE.md#built-in-voice-navigation-commands](USAGE.md#built-in-voice-navigation-commands)
- Runtime troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Uninstall

**Homebrew:**

```bash
brew uninstall voiceterm
```

**PyPI:**

```bash
pipx uninstall voiceterm
```

**From source:** Remove the `voiceterm` binary from your PATH (check `which voiceterm` for the location).

## See Also

| Topic | Link |
|-------|------|
| Quick Start | [QUICK_START.md](../QUICK_START.md) |
| Usage | [USAGE.md](USAGE.md) |
| CLI Flags | [CLI_FLAGS.md](CLI_FLAGS.md) |
| Troubleshooting hub | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Install/update troubleshooting | [TROUBLESHOOTING.md#install-and-update-issues](TROUBLESHOOTING.md#install-and-update-issues) |
