# Installation

This doc covers install options and model setup.
Recommended: Homebrew on macOS/Linux for a global `voiceterm` command.

Docs map:

- User guides index: [README.md](README.md)
- Engineering history: [../dev/history/ENGINEERING_EVOLUTION.md](../dev/history/ENGINEERING_EVOLUTION.md)

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
- [Using with your own projects](#using-with-your-own-projects)
- [Windows](#windows)
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
- Whisper model (GGML) downloaded on first run
- Disk space for models: `tiny.en` ~75 MB, `base.en` ~142 MB, `small.en` ~466 MB, `medium.en` ~1.5 GB, `large` ~3.1 GB
- Rust toolchain (stable) only if you build from source: <https://rustup.rs>
- Optional (Python fallback): `python3`, `ffmpeg`, and the `whisper` CLI on PATH
  (disable with `--no-python-fallback`)

## Choose an Install Path

| If you want... | Choose | Why |
|----------------|--------|-----|
| Easiest global install and upgrades | **Homebrew** | Best default on macOS/Linux with `brew upgrade` updates |
| Python-managed CLI install | **PyPI (`pipx`)** | Isolated Python tool install, then bootstrap native binary on first run |
| Full local control / development workflow | **From source** | Build and modify directly from this repository |
| Finder-based launch on macOS | **macOS App** | Folder picker launches VoiceTerm without terminal setup steps |
| No install, one-off run | **Manual run** | Use the repo scripts directly from any directory |

## Option A: Homebrew (recommended)

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

After upgrading, run `voiceterm --version` and open Settings (`Ctrl+O`) once to
confirm your expected defaults (for example `Send mode`, `Macros`, and
`Latency display`) are available. Wake-word controls are also present there,
but default to `OFF` unless explicitly enabled.
Quick post-upgrade smoke check:

- `Ctrl+R` record toggle
- `Ctrl+E` insert-mode send/finalize behavior
- `Ctrl+H` transcript history overlay (source labels + replayable-row behavior)
- `Ctrl+O` settings overlay opens and persists changes
- Optional: `voiceterm --session-memory` writes markdown memory logs at the expected path

Detailed runtime behavior is documented in [USAGE.md](USAGE.md). Runtime issues
and terminal-specific edge cases are documented in
[TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Option B: PyPI

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

## Option C: Install from source

Recommended if you want a local build or plan to hack on VoiceTerm.

```bash
git clone https://github.com/jguida941/voiceterm.git
cd voiceterm
./scripts/install.sh
```

The installer builds the overlay, installs the `voiceterm` wrapper, and downloads
a Whisper model to the correct path for the CLI.

To suppress the startup splash screen, set `VOICETERM_NO_STARTUP_BANNER=1`.
To keep it but shorten/disable dwell time, set `VOICETERM_STARTUP_SPLASH_MS`
(`0` = immediate clear, default `1500`).

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

## Option D: macOS App (folder picker)

1. Double-click **app/macos/VoiceTerm.app**.
2. Pick your project folder.
3. A Terminal window opens and runs the overlay inside that folder.

![Folder Picker](../img/folder-picker.png)

## Option E: Manual run (no install)

Run from any project folder:

```bash
VOICETERM_CWD="$(pwd)" /path/to/voiceterm/scripts/start.sh
```

`scripts/start.sh` handles model download and setup when needed.

## Integration/Test Branch Installs

If you need to validate a pre-release integration build before final tagging:

```bash
git clone --branch <branch-name> https://github.com/jguida941/voiceterm.git
cd voiceterm
./scripts/install.sh
voiceterm --version
```

After install, run the release verification commands in `dev/DEVELOPMENT.md`
(`Testing` and `Manual QA checklist`) for process teardown, CPU leak detection,
and high-load UI responsiveness.

## Using with your own projects

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

Built-in voice navigation phrases are available after install:
`scroll up`, `scroll down`, `show last error`, `copy last error`, and
`explain last error`.

Linux clipboard note: `copy last error` uses `wl-copy`, `xclip`, or `xsel`
when available.

Optional macro wizard (project-local smart command pack):

```bash
./scripts/macros.sh wizard
```

Available packs:

- `safe-core`: low-risk git/GitHub inspection commands
- `power-git`: write actions (commit/push/PR/issue) in insert mode
- `full-dev`: safe-core + power-git + codex-voice maintainer checks/release helpers

For GitHub macros, wizard validation expects `gh` to be authenticated
(`gh auth login`).

## Windows

Windows native is not supported yet (the overlay uses a Unix PTY). Use WSL2 or
a macOS/Linux machine.

## See Also

| Topic | Link |
|-------|------|
| Quick Start | [QUICK_START.md](../QUICK_START.md) |
| Usage | [USAGE.md](USAGE.md) |
| CLI Flags | [CLI_FLAGS.md](CLI_FLAGS.md) |
| Troubleshooting hub | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Install/update troubleshooting | [TROUBLESHOOTING.md#install-and-update-issues](TROUBLESHOOTING.md#install-and-update-issues) |
