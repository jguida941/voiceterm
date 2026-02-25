# VoiceTerm

Voice-first terminal overlay for Codex and Claude.
Local Whisper speech-to-text runs on your machine by default, with PTY passthrough and a customizable HUD.

Primary support: Codex and Claude Code.

## Install

```bash
pipx install voiceterm
# or
python3 -m pip install --user voiceterm
```

Then run:

```bash
voiceterm
```

Authenticate your backend once if needed:

```bash
voiceterm --login --codex
voiceterm --login --claude
```

## What This Package Does

The PyPI package installs the `voiceterm` launcher.

On first run, it bootstraps the native VoiceTerm binary into:

- `~/.local/share/voiceterm/native/bin/voiceterm` (default)

By default it downloads a prebuilt release binary from the matching GitHub
release tag (`v<package-version>`), verifies the SHA256 checksum, and installs
it locally.

Default mode: `VOICETERM_BOOTSTRAP_MODE=binary-only`

## Runtime Requirements

- Internet access to GitHub Releases (or a configured mirror)
- macOS or Linux (Windows via WSL2)

Source-build fallback requirements (only when enabled):

- `git`
- Rust toolchain (`cargo`, `rustc`)

## Optional Environment Overrides

- `VOICETERM_NATIVE_BIN=/absolute/path/to/voiceterm`
  - Use an already-installed native binary and skip bootstrap.
- `VOICETERM_PY_NATIVE_ROOT=/custom/root`
  - Change where the bootstrap binary is installed.
- `VOICETERM_BOOTSTRAP_MODE=binary-only|binary-then-source|source-only`
  - Choose bootstrap strategy.
- `VOICETERM_RELEASE_OWNER_REPO=jguida941/voiceterm`
  - Override GitHub owner/repo used for release binary downloads.
- `VOICETERM_RELEASE_BASE_URL=https://github.com/jguida941/voiceterm/releases/download`
  - Override release download base URL (for mirror/proxy setups).
- `VOICETERM_REPO_URL=https://github.com/jguida941/voiceterm`
  - Use a different source repository URL (source-bootstrap modes only).
- `VOICETERM_REPO_REF=v1.0.69`
  - Override release tag for binary mode or git ref for source-bootstrap modes.

## Documentation

- Main repository: <https://github.com/jguida941/voiceterm>
- Install guide: <https://github.com/jguida941/voiceterm/blob/master/guides/INSTALL.md>
- Usage guide: <https://github.com/jguida941/voiceterm/blob/master/guides/USAGE.md>
- CLI flags: <https://github.com/jguida941/voiceterm/blob/master/guides/CLI_FLAGS.md>
- Troubleshooting: <https://github.com/jguida941/voiceterm/blob/master/guides/TROUBLESHOOTING.md>
