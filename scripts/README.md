# User Scripts

Scripts for installing and running VoiceTerm.

| Script | Purpose | Usage |
|--------|---------|-------|
| `install.sh` | One-time installer | `./scripts/install.sh` |
| `start.sh` | Launch VoiceTerm | `./scripts/start.sh` |
| `setup.sh` | Download Whisper models | `./scripts/setup.sh models --base` |
| `macros.sh` | Macro pack wizard/installer | `./scripts/macros.sh wizard` |
| `python_fallback.py` | Fallback STT pipeline | Used automatically |

## install.sh

Builds VoiceTerm and installs the `voiceterm` command.

```bash
./scripts/install.sh
```

Pick a model size during install:

```bash
./scripts/install.sh --small
```

Launch the macro wizard at the end of install:

```bash
./scripts/install.sh --with-macros-wizard
./scripts/install.sh --with-macros-wizard --macros-pack full-dev
```

## start.sh

Launches VoiceTerm directly (downloads model if needed).

```bash
./scripts/start.sh
```

## setup.sh

Downloads Whisper models and performs initial setup.

```bash
# Download base English model (recommended)
./scripts/setup.sh models --base

# Download small model (larger, more accurate)
./scripts/setup.sh models --small

# Show help
./scripts/setup.sh --help
```

## macros.sh

Interactive wizard to generate project-local macro files.

```bash
# Wizard (recommended)
./scripts/macros.sh wizard

# Non-interactive install
./scripts/macros.sh install --pack safe-core
./scripts/macros.sh install --pack full-dev --overwrite

# Validate an existing file
./scripts/macros.sh validate --output ./.voiceterm/macros.yaml
```

Pack summary:

- `safe-core`: low-risk git/GitHub inspection commands
- `power-git`: write actions (commit/push/PR/issue) defaulting to `insert` mode
- `full-dev`: safe-core + power-git + codex-voice maintainer checks/release helpers

Wizard personalization:

- Auto-detects and templates values from your repo where possible:
  - `__GITHUB_REPO__` (owner/name)
  - `__GITHUB_OWNER__`
  - `__DEFAULT_BRANCH__`
  - `__GITHUB_USER__`
  - `__CURRENT_BRANCH__`
- Validates GitHub CLI readiness for GitHub macros (`gh` install/auth/repo access).

## python_fallback.py

Python fallback pipeline for speech-to-text. Used automatically when:

- Native Whisper model is not available
- Audio device issues occur

Requires: `python3`, `ffmpeg`, `whisper` CLI on PATH.

---

For developer scripts, see [dev/scripts/](../dev/scripts/).
