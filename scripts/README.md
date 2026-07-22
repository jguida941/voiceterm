# User Scripts

Scripts for installing and running VoiceTerm.

| Script | Purpose | Usage |
|--------|---------|-------|
| `install.sh` | One-time installer | `./scripts/install.sh` |
| `start.sh` | Launch VoiceTerm | `./scripts/start.sh` |
| `setup.sh` | Download Whisper models | `./scripts/setup.sh models --base` |
| `macros.sh` | Macro pack wizard/installer | `./scripts/macros.sh wizard` |
| `python_fallback.py` | Fallback STT pipeline | Used automatically |
| `release/` | Version, notes, checksum, and Homebrew helpers | `make release-check V=X.Y.Z` |
| `tests/` | Integration, latency, wake-word, and benchmark checks | `make integration` |

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
./scripts/install.sh --with-macros-wizard --macros-pack power-git
```

## start.sh

Same as running `voiceterm` directly, but handles model download and setup
automatically. Useful when running from the source repo without installing.

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
./scripts/macros.sh install --pack power-git --overwrite

# Validate an existing file
./scripts/macros.sh validate --output ./.voiceterm/macros.yaml
```

Pack summary:

- `safe-core`: low-risk git/GitHub inspection commands
- `power-git`: write actions (commit/push/PR/issue) defaulting to `insert` mode

Wizard personalization:

- Auto-detects and templates values from your repo where possible:
  - `__GITHUB_REPO__` (owner/name)
  - `__GITHUB_OWNER__`
  - `__DEFAULT_BRANCH__`
  - `__GITHUB_USER__`
  - `__CURRENT_BRANCH__`
- Validates GitHub CLI readiness for GitHub macros (`gh` install/auth/repo access).

## python_fallback.py

Python fallback pipeline for speech-to-text. VoiceTerm uses this automatically
when the native Whisper engine cannot run — for example, if the model file is
missing or the audio device is not accessible to the native pipeline.

Requires: `python3`, `ffmpeg`, `whisper` CLI on PATH.
You can disable this fallback with `--no-python-fallback`.

## Development and release helpers

The repository-level `Makefile` is the supported entry point:

```bash
make check
make ci
make integration
make release-check V=X.Y.Z
```

The scripts in `release/` are dependency-free Python helpers used by those
targets and the GitHub release workflows. The scripts in `tests/` can also be
run directly when diagnosing a specific runtime path.
