# Troubleshooting

Single troubleshooting reference for VoiceTerm.
Use the quick-fix table first, then jump to the detailed section.

Docs map:

- User guides index: [README.md](README.md)
- Engineering history: [../dev/history/ENGINEERING_EVOLUTION.md](../dev/history/ENGINEERING_EVOLUTION.md)

## Quick Fixes

| Problem | First action | Section |
|---------|--------------|---------|
| No speech detected | Lower mic threshold (`Ctrl+\\`) | [No speech detected](#no-speech-detected) |
| Voice not recording | Check microphone permissions | [Voice capture failed (see log)](#voice-capture-failed-see-log) |
| Codex/Claude not responding | Verify install + login | [Codex or Claude not responding](#codex-or-claude-not-responding) |
| Claude executes actions without confirmation | Disable permission-skip mode | [Claude running without permission prompts](#claude-running-without-permission-prompts) |
| Auto-voice not triggering | Check prompt detection | [Auto-voice not triggering](#auto-voice-not-triggering) |
| Transcript queued while backend is busy | Wait for prompt or tune regex | [Transcript queued (N)](#transcript-queued-n) |
| No error captured yet | Run one backend command first | [No error captured yet / to copy / to explain](#no-error-captured-yet--to-copy--to-explain) |
| Wrong version after update | Check PATH + reinstall flow | [Wrong version after update](#wrong-version-after-update) |
| Settings/HUD lags while backend is busy | Run high-load responsiveness checks | [Settings or HUD lags during heavy backend output](#settings-or-hud-lags-during-heavy-backend-output) |
| Meter looks too loud at normal speech | Validate meter behavior and sensitivity | [Meter looks too loud for normal speech](#meter-looks-too-loud-for-normal-speech) |
| HUD duplicates/flickers in JetBrains | Verify version and collect logs | [HUD duplicates in JetBrains terminals](#hud-duplicates-in-jetbrains-terminals) |
| JetBrains cursor briefly flashes `|`/block over HUD | Verify version and collect logs | [Overlay flickers in JetBrains terminals](#overlay-flickers-in-jetbrains-terminals) |
| Startup splash behaves oddly | Tune splash env vars | [Startup banner lingers in IDE terminal](#startup-banner-lingers-in-ide-terminal) |
| Theme colors look muted | Verify truecolor env | [Theme colors look muted in IDE terminal](#theme-colors-look-muted-in-ide-terminal) |
| `PTY write failed: Input/output error` on exit | Usually benign shutdown race | [PTY exit write error in logs](#pty-exit-write-error-in-logs) |

## Contents

- [Status Messages](#status-messages)
- [Audio Setup](#audio-setup)
- [Mic Sensitivity](#mic-sensitivity)
- [Backend Issues](#backend-issues)
- [Terminal and IDE Issues](#terminal-and-ide-issues)
- [Install and Update Issues](#install-and-update-issues)
- [Enabling Logs](#enabling-logs)
- [FAQ](#faq)
- [Getting Help](#getting-help)
- [See Also](#see-also)

## Status Messages

### No speech detected

The mic recorded but no voice crossed the current threshold.

1. Speak louder or closer to the mic.
2. Lower threshold with `Ctrl+\\` (or `Ctrl+/`).
3. Run `voiceterm --mic-meter` to calibrate.

Status text is pipeline-neutral; check Settings (`Ctrl+O`) -> `Voice pipeline`
if you need to confirm native Rust vs fallback capture.

### Voice capture failed (see log)

Capture could not start.

1. Check mic permissions for your terminal app.
2. Run `voiceterm --list-input-devices`.
3. Try a specific device: `voiceterm --input-device "Your Mic Name"`.
4. Re-run with logs: `voiceterm --logs`.

### Voice capture error (see log)

Recording or transcription failed at runtime.

1. Run with logs: `voiceterm --logs`.
2. Check `${TMPDIR}/voiceterm_tui.log` (macOS) or `/tmp/voiceterm_tui.log` (Linux).
3. Restart `voiceterm`.

### Processing... (stuck)

Transcription is taking longer than expected.

1. Wait up to 60 seconds for longer captures.
2. If still stuck, press `Ctrl+C` and restart.
3. Try a smaller model (`--whisper-model base`).

### Voice macro not expanding

Macros load from `<project>/.voiceterm/macros.yaml` and apply only when
`Settings -> Macros` is ON.

1. Confirm file path and YAML structure.
2. Check `Macros` toggle state in Settings (`Ctrl+O`) since startup default is `OFF`.
3. Check trigger text match (case/whitespace-insensitive).
4. Run `./scripts/macros.sh validate --output ./.voiceterm/macros.yaml`.
   If it warns about unresolved placeholders (for example `__GITHUB_REPO__`),
   rerun `./scripts/macros.sh wizard` and provide repo details.
   If it warns about GitHub auth, run `gh auth login`.
5. Restart VoiceTerm after editing macros.

### Voice macro expanded unexpectedly

Macro expansion runs only when `Settings -> Macros` is ON.

1. Open Settings (`Ctrl+O`).
2. Set `Macros` to OFF for raw transcript injection.

### Python pipeline

Native STT was unavailable, so Python fallback was used.

1. Check models: `ls whisper_models/ggml-*.bin`
2. Download model: `./scripts/setup.sh models --base`
3. Ensure fallback dependencies exist (`python3`, `ffmpeg`, `whisper`) or use
   `--no-python-fallback`.

## Audio Setup

### Check microphone permissions

- macOS: System Settings -> Privacy & Security -> Microphone
- Linux: verify PulseAudio/PipeWire access (`pactl list sources`)

### Verify Whisper model exists

```bash
ls whisper_models/ggml-*.bin
```

If missing:

```bash
./scripts/setup.sh models --base
```

### List/select devices

```bash
voiceterm --list-input-devices
voiceterm --input-device "MacBook Pro Microphone"
```

### Microphone changed or unplugged

Restart VoiceTerm after plugging in a new input device.

## Mic Sensitivity

### Too sensitive (background noise triggers capture)

- Press `Ctrl+]` to raise threshold (less sensitive)
- Or set startup threshold:

```bash
voiceterm --voice-vad-threshold-db -30
```

### Not sensitive enough (misses your voice)

- Press `Ctrl+\\` (or `Ctrl+/`) to lower threshold (more sensitive)
- Or set startup threshold:

```bash
voiceterm --voice-vad-threshold-db -50
```

### Find the right threshold

```bash
voiceterm --mic-meter
```

Hotkey range: `-80 dB` to `-10 dB`, default `-55 dB`.
CLI flag range: `-120 dB` to `0 dB`.

## Backend Issues

### Codex or Claude not responding

1. Verify backend CLI exists:

   ```bash
   which codex
   which claude
   ```

2. Verify authentication:

   ```bash
   codex login
   # or
   claude login
   ```

   Or from VoiceTerm:

   ```bash
   voiceterm --login --codex
   voiceterm --login --claude
   ```

3. Restart `voiceterm` if the session is stuck.

### Claude running without permission prompts

If Claude tool actions run without approval prompts, check whether
`--claude-skip-permissions` was enabled.

1. Restart VoiceTerm without that flag:

   ```bash
   voiceterm --json-ipc
   ```

2. If you need skip-permissions for automation, run only in isolated/trusted
   environments (for example sandboxed or disposable workspaces).
3. Avoid using skip-permissions mode with untrusted repositories or with
   credentials/secrets available in your shell environment.

### Many codex or claude processes remain after quitting

Recent builds terminate backend process groups and reap child processes on exit.
If you still observe leftovers:

1. Confirm version:

   ```bash
   voiceterm --version
   ```

2. Check for orphaned backend processes:

   ```bash
   ps -axo ppid,pid,command | egrep '(^ *1 .*\\b(codex|claude)\\b)'
   ```

3. If orphans remain, report with:

   - `voiceterm --version`
   - terminal/IDE name + version
   - launch command
   - relevant `${TMPDIR}/voiceterm_tui.log` lines

For full manual release validation, run `Testing_Guide.md` sections `3` and
`3A` (normal exit, abrupt kill, multi-session isolation, and churn checks).

### Auto-voice not triggering

Auto-voice waits for prompt readiness before listening again.

1. Override prompt detection for your shell/backend prompt:

   ```bash
   voiceterm --prompt-regex '^codex> $'
   ```

2. Enable prompt logging:

   ```bash
   voiceterm --prompt-log /tmp/voiceterm_prompt.log
   ```

3. Inspect the prompt log and adjust regex.

### Transcript queued (N)

Backend output is still streaming, so transcript injection is deferred.

1. Wait for prompt return.
2. If urgent, stop current generation (`Ctrl+C`) and retry.
3. If this happens often, tune prompt detection (`--prompt-regex`) and
   transcript timeout (`--transcript-idle-ms`).

### Transcript queue full (oldest dropped)

You recorded more items than queue capacity while backend was busy.

1. Pause speaking until prompt returns.
2. Use shorter chunks.
3. Prefer `insert` mode if you need manual pacing.

### No error captured yet / to copy / to explain

Voice actions such as `show last error`, `copy last error`, and
`explain last error` need at least one recent terminal output line that looks
like an error.

1. Run or repeat the failing command once so the error appears in terminal output.
2. Retry the voice command phrase after the output is visible.
3. On Linux, install one clipboard helper (`wl-copy`, `xclip`, or `xsel`) if
   `copy last error` fails.
4. If clipboard helpers are unavailable, copy manually from terminal output.

## Terminal and IDE Issues

### IDE terminal controls not working (JetBrains/Cursor)

If HUD button clicks or arrow navigation fail in one terminal app but not
another:

1. Verify core shortcuts still work (`Ctrl+U`, `Ctrl+O`).
2. Capture input diagnostics:

   ```bash
   voiceterm --logs
   VOICETERM_DEBUG_INPUT=1 voiceterm --logs
   ```

3. Reproduce once and inspect `${TMPDIR}/voiceterm_tui.log` for `input bytes`
and `input events` lines.

### Ctrl+G quick theme cycle does not work

1. Verify terminal key handling with `Ctrl+Y` first (theme picker should open).
2. If `Ctrl+Y` works but `Ctrl+G` does not, check for shell/terminal keybinding
   overrides and disable that binding.
3. Use `VOICETERM_DEBUG_INPUT=1 voiceterm --logs` and inspect
   `${TMPDIR}/voiceterm_tui.log` for `Ctrl+G` input events.

### Settings or HUD lags during heavy backend output

If arrow keys/settings updates feel delayed while backend output is streaming:

1. Confirm version:

   ```bash
   voiceterm --version
   ```

2. Run the high-load checks in `Testing_Guide.md` section `4A`:

   ```bash
   yes "voiceterm-load-line" | head -n 50000
   ```

3. While output is active, open Settings (`Ctrl+O`) and hold arrow navigation
   for several seconds.
4. In current builds, high-output redraw pacing and queue handling were tuned
   to keep HUD/settings more reactive; if you still see lag, capture logs.
5. If lag persists, collect logs with `voiceterm --logs` and include:
   - terminal/IDE name + version
   - backend (`--codex` or `--claude`)
   - whether recording was active

### Meter looks too loud for normal speech

If meter bars/dots frequently appear at warning/error levels during normal
speech:

1. Run calibration once:

   ```bash
   voiceterm --mic-meter
   ```

2. Check threshold in Settings (`Ctrl+O`) and adjust sensitivity with `Ctrl+]`
   or `Ctrl+\\` as needed.
3. Validate expected behavior from `Testing_Guide.md` section `4A`:
   - silence near floor
   - normal speech mostly green
   - loud transients may briefly hit yellow/red
4. If behavior is still clearly incorrect, capture a short screen recording and
   include logs from `${TMPDIR}/voiceterm_tui.log`.

### HUD duplicates in JetBrains terminals

If Full HUD appears stacked/repeated:

1. Verify version:

   ```bash
   voiceterm --version
   ```

2. Re-run once with logs:

   ```bash
   voiceterm --logs
   ```

3. Share `${TMPDIR}/voiceterm_tui.log` if still reproducible.

### Overlay flickers in JetBrains terminals

If HUD rapidly flashes in JetBrains but not Cursor/VS Code:

1. Verify version.
2. Current builds hide/show the cursor around JetBrains redraw sequences to
   reduce random `|`/block cursor artifact flashes over HUD rows.
3. Reproduce with `voiceterm --logs`.
4. Share logs + terminal app/version if it persists.

Implementation details on redraw/resize behavior are in
`dev/ARCHITECTURE.md`.

### PTY exit write error in logs

If you see:

```text
failed to send PTY exit command: PTY write failed: Input/output error (os error 5)
```

This is usually a benign shutdown race where the PTY was already closing.

### Startup banner missing

Splash is shown by default in non-JetBrains terminals. JetBrains terminals may
skip splash intentionally.

Check if banner is explicitly disabled:

```bash
env | rg VOICETERM_NO_STARTUP_BANNER
```

Disable explicitly (all terminals):

```bash
VOICETERM_NO_STARTUP_BANNER=1 voiceterm
```

### Startup banner lingers in IDE terminal

1. Check version:

   ```bash
   voiceterm --version
   ```

2. Test immediate splash clear:

   ```bash
   VOICETERM_STARTUP_SPLASH_MS=0 voiceterm
   ```

3. Disable splash globally if preferred:

   ```bash
   VOICETERM_NO_STARTUP_BANNER=1 voiceterm
   ```

### Theme colors look muted in IDE terminal

Some IDE profiles do not expose truecolor env vars.

1. Inspect env:

   ```bash
   env | rg 'COLORTERM|TERM|TERM_PROGRAM|TERMINAL_EMULATOR|NO_COLOR'
   ```

2. Ensure `NO_COLOR` is not set.
3. A/B test truecolor:

   ```bash
   COLORTERM=truecolor voiceterm --theme catppuccin
   ```

## Install and Update Issues

### Homebrew link conflict

If `brew install voiceterm` fails because the command already exists:

```bash
brew link --overwrite voiceterm
```

### Wrong version after update

Start with a normal update:

```bash
brew update
brew upgrade voiceterm
```

If Homebrew still shows an older version, refresh taps:

```bash
brew untap jguida941/voiceterm 2>/dev/null || true
brew untap jguida941/homebrew-voiceterm 2>/dev/null || true
brew tap jguida941/voiceterm
brew update
brew info voiceterm
```

If still stale, clear cache and reinstall:

```bash
rm -f "$(brew --cache)"/voiceterm--*
brew reinstall voiceterm
```

If `voiceterm --version` is still old, check PATH shadowing:

```bash
which -a voiceterm
```

Common shadow path from local install:

```bash
mv ~/.local/bin/voiceterm ~/.local/bin/voiceterm.bak
hash -r
```

Check for repo-local wrapper too:

```bash
ls -l ~/voiceterm/bin/voiceterm 2>/dev/null
```

Relink Homebrew and clear shell cache:

```bash
brew unlink voiceterm && brew link --overwrite voiceterm
hash -r
```

Verify Homebrew binary directly:

```bash
$(brew --prefix)/opt/voiceterm/libexec/src/target/release/voiceterm --version
```

## Enabling Logs

```bash
voiceterm --logs
```

Include transcript snippets (optional):

```bash
voiceterm --logs --log-content
```

Disable all logs:

```bash
voiceterm --no-logs
```

Log paths:

- Debug log: `${TMPDIR}/voiceterm_tui.log` (macOS) or `/tmp/voiceterm_tui.log` (Linux)
- Trace log: `${TMPDIR}/voiceterm_trace.jsonl` or `/tmp/voiceterm_trace.jsonl`

## FAQ

### What languages does Whisper support?

Whisper supports many languages. Start with `--lang en` (tested) or use
`--lang auto`.

Reference:
[Whisper supported languages](https://github.com/openai/whisper#available-models-and-languages)

### Which AI CLI backends work?

Canonical backend support matrix lives in:
[USAGE.md -> Backend Support](USAGE.md#backend-support)

### Which Whisper model should I use?

Start with `base` for speed, `small` for balance, `medium` for higher accuracy.
See [WHISPER.md](WHISPER.md) for full guidance.

### Can I use VoiceTerm without Codex?

Yes. Use Claude:

```bash
voiceterm --claude
```

### Does VoiceTerm send voice audio to the cloud?

No. Whisper runs locally.

## Getting Help

When reporting an issue, include:

1. `voiceterm --version`
2. Backend (`codex` or `claude`) and launch command
3. Terminal/IDE name and version
4. Relevant log excerpt from `${TMPDIR}/voiceterm_tui.log`

## See Also

| Topic | Link |
|-------|------|
| Install guide | [INSTALL.md](INSTALL.md) |
| Usage guide | [USAGE.md](USAGE.md) |
| CLI flags | [CLI_FLAGS.md](CLI_FLAGS.md) |
| Whisper guide | [WHISPER.md](WHISPER.md) |
| Developer architecture | [../dev/ARCHITECTURE.md](../dev/ARCHITECTURE.md) |
