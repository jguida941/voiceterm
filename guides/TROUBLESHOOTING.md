# Troubleshooting
<!-- markdownlint-disable MD033 -->

Single troubleshooting reference for VoiceTerm.
Use the quick-fix table first, then jump into the matching section shortcuts.
Current stable release: `v1.0.85` (2026-02-20). Full release notes: [../dev/CHANGELOG.md](../dev/CHANGELOG.md).

## Quick Fixes

| Problem | First action | Section |
|---------|--------------|---------|
| No speech detected | Lower mic threshold (`Ctrl+\\`) | [Status Messages](#status-messages) |
| Voice not recording | Check microphone permissions | [Audio Setup](#audio-setup) |
| Voice macro not expanding | Validate macros file + toggle state | [Status Messages](#status-messages) |
| Codex/Claude not responding | Verify install + login | [Backend Issues](#backend-issues) |
| Claude executes actions without confirmation | Disable permission-skip mode | [Backend Issues](#backend-issues) |
| Claude approval prompt text is occluded by HUD rows | Update and verify prompt-safe HUD suppression | [Backend Issues](#backend-issues) |
| Auto-voice not triggering | Check prompt detection | [Backend Issues](#backend-issues) |
| Transcript queued while backend is busy | Wait for prompt or tune regex | [Backend Issues](#backend-issues) |
| Wrong version after update | Check PATH + reinstall flow | [Install and Update Issues](#install-and-update-issues) |
| Settings/HUD lags while backend is busy | Reduce output load and capture logs | [Terminal and IDE Issues](#terminal-and-ide-issues) |
| Meter looks too loud at normal speech | Validate meter behavior and sensitivity | [Terminal and IDE Issues](#terminal-and-ide-issues) |
| Transcript includes tags like `(siren wailing)` | Update VoiceTerm and capture a sample log | [Status Messages](#status-messages) |
| Startup splash behaves oddly | Tune splash env vars | [Terminal and IDE Issues](#terminal-and-ide-issues) |
| Theme colors look muted | Verify truecolor env | [Terminal and IDE Issues](#terminal-and-ide-issues) |
| `PTY write failed: Input/output error` on exit | Usually benign shutdown race | [Terminal and IDE Issues](#terminal-and-ide-issues) |

## Status Messages

Section shortcuts:

- [No speech detected](#no-speech-detected)
- [Voice capture failed (see log)](#voice-capture-failed-see-log)
- [Latency badge seems wrong](#latency-badge-seems-wrong-in-auto-mode)
- [Transcript includes ambient-sound tags](#transcript-includes-ambient-sound-tags)
- [Session memory file is missing](#session-memory-file-is-missing)
- [Voice macro not expanding](#voice-macro-not-expanding)

<details>
<summary>Expand Status Messages</summary>

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
4. In insert mode, use `Ctrl+R` to stop active recording without sending.
   `Ctrl+E` sends staged text immediately; with no staged text it only
   finalizes+submits during active recording (idle with no staged text shows
   `Nothing to send`). `Enter` is forwarded to wrapped CLI input (`insert`
   mode: submit staged text).

### Latency badge seems wrong in auto mode

The HUD latency badge is meant to reflect the latest completed transcript STT
processing delay (`stt_ms`), not backend response time.

1. Confirm version:

   ```bash
   voiceterm --version
   ```

2. Re-run with logs and inspect latency audit lines:

   ```bash
   voiceterm --logs
   ```

   Look for `latency_audit|display_ms=...|capture_ms=...|speech_ms=...|stt_ms=...|rtf=...`.
3. If `stt_ms` rises on longer utterances, that is usually expected. Final-result
   latency scales with audio length for non-streaming STT.
4. Compare `rtf` (real-time factor) for consistency across short and long clips:
   lower is faster (`0.20` means 1 second of speech took ~200ms to transcribe).
   If `rtf` stays roughly stable while `stt_ms` changes, the pipeline is
   behaving normally.
5. If no transcript was produced (`No speech detected` / capture errors), the
   badge should hide instead of showing a synthetic value.
6. Color severity follows speech-relative STT speed (`rtf`) when speech metrics
   are present, with absolute-ms thresholds only as fallback.
7. The badge is STT-only (no derived elapsed/capture fallback math) and stale
   idle values auto-expire after a short window.

### Transcript includes ambient-sound tags

If Whisper emits ambient placeholders such as `(siren wailing)` or
`(water splashing)`, update to the latest build. Current sanitizer rules strip
known non-speech tags in both `(...)` and `[...]` forms before delivery.

If artifacts persist:

1. Run with logs: `voiceterm --logs`
2. Capture the exact emitted token from `${TMPDIR}/voiceterm_tui.log`
3. Report the phrase so the non-speech filter list can be extended

### Transcript history has no entries

`Ctrl+H` only shows completed transcript captures.

1. Run one successful capture first (`Ctrl+R`, speak, wait for transcript).
2. Reopen transcript history (`Ctrl+H`) and verify entries appear newest-first.
3. If entries still do not appear, run with logs:

   ```bash
   voiceterm --logs
   ```

4. Include terminal/IDE details and relevant `${TMPDIR}/voiceterm_tui.log`
   lines when reporting.

### Notification history has no entries

`Ctrl+N` shows runtime status notifications (for example mode toggles, warnings,
and errors), not transcript rows.

1. Trigger a status event first (for example `Ctrl+V` to toggle auto-voice, or
   open/close Settings with `Ctrl+O`).
2. Reopen notification history (`Ctrl+N`) and verify entries appear.
3. If entries still do not appear, run with logs:

   ```bash
   voiceterm --logs
   ```

4. Include relevant `${TMPDIR}/voiceterm_tui.log` lines when reporting.

### Session memory file is missing

The markdown session-memory log is opt-in.

1. Start VoiceTerm with `--session-memory`.
2. If needed, set an explicit path: `--session-memory-path <PATH>`.
3. Speak once (or send one backend/output line), then close VoiceTerm to flush
   pending lines.
4. Confirm the file exists (default: `<cwd>/.voiceterm/session-memory.md`).
5. If still missing, rerun with logs (`voiceterm --logs`) and check
   `${TMPDIR}/voiceterm_tui.log` for session-memory initialization errors.

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

### Raw mouse escape text appears in terminal

If you see fragments like `[<0;35;25M` in the wrapped CLI while clicking or
interrupting, those are mouse-report escape sequences that should be handled by
the HUD parser, not forwarded to the backend.

1. Confirm version: `voiceterm --version`
2. Re-run with logs: `voiceterm --logs`
3. If needed as a temporary workaround, set `Settings -> Mouse` to `OFF`
4. Report terminal/IDE + version if raw fragments still appear on latest build

</details>

## Audio Setup

Section shortcuts:

- [Check microphone permissions](#check-microphone-permissions)
- [Verify Whisper model exists](#verify-whisper-model-exists)
- [Microphone changed or unplugged](#microphone-changed-or-unplugged)

<details>
<summary>Expand Audio Setup</summary>

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

</details>

## Mic Sensitivity

Section shortcuts:

- [Too sensitive](#too-sensitive-background-noise-triggers-capture)
- [Not sensitive enough](#not-sensitive-enough-misses-your-voice)
- [Find the right threshold](#find-the-right-threshold)

<details>
<summary>Expand Mic Sensitivity</summary>

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

</details>

## Backend Issues

Section shortcuts:

- [Codex or Claude not responding](#codex-or-claude-not-responding)
- [Claude running without permission prompts](#claude-running-without-permission-prompts)
- [Claude prompt rows are occluded](#claude-prompt-rows-are-occluded)
- [Auto-voice not triggering](#auto-voice-not-triggering)
- [Wake-word enabled but no wake triggers yet](#wake-word-enabled-but-no-wake-triggers-yet)
- [Transcript queued (N)](#transcript-queued-n)
- [Transcript queue full (oldest dropped)](#transcript-queue-full-oldest-dropped)
- [Status line clips oddly](#status-line-clips-oddly-with-cjk-or-emoji-text)

<details>
<summary>Expand Backend Issues</summary>

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

### Claude prompt rows are occluded

VoiceTerm now suppresses HUD rows when Claude interactive approval/permission
prompts are detected, so prompt text/actions stay visible.

If prompts still look clipped or overlapped:

1. Confirm version:

   ```bash
   voiceterm --version
   ```

2. Retry in a larger terminal row count first (wrapped absolute command paths
   can consume multiple rows quickly).
3. Re-run with logs and capture a screenshot:

   ```bash
   voiceterm --logs --claude
   ```

4. Include terminal name/version + screenshot + relevant
   `${TMPDIR}/voiceterm_tui.log` lines when reporting the issue.

### Many codex or claude processes remain after quitting

VoiceTerm should clean up backend processes on exit. If you still observe
leftover `codex`/`claude` processes:

1. Confirm version:

   ```bash
   voiceterm --version
   ```

2. Fully quit VoiceTerm and reopen it once.
3. Check for orphaned backend processes:

   ```bash
   ps -axo ppid,pid,command | egrep '(^ *1 .*\\b(codex|claude)\\b)'
   ```

4. If orphans remain, report with:

   - `voiceterm --version`
   - terminal/IDE name + version
   - launch command
   - relevant `${TMPDIR}/voiceterm_tui.log` lines

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

### Wake-word enabled but no wake triggers yet

Wake-word listening is local and depends on microphone capture + local Whisper
transcription, so setup issues can prevent detections.

1. In Full HUD, confirm wake privacy status:
   - `Wake: ON` means always-listening is active.
   - `Wake: PAUSED` means wake listening is temporarily suspended while capture/transcription is active.
2. Confirm expected values in Settings (`Ctrl+O`) or via
   `--wake-word-sensitivity` / `--wake-word-cooldown-ms`.
3. Confirm a local Whisper model path is configured and usable in your install.
4. Try moderate sensitivity first (for example `0.55` to `0.70`), then retest.
5. Use expected wake phrases (`hey codex`, `ok codex`, `hey claude`, or
   `voiceterm`) and speak clearly near the mic.
6. If this persists, keep using `Ctrl+R` / `Ctrl+E` controls and share logs
   (`voiceterm --logs`).

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

### Status line clips oddly with CJK or emoji text

Status-line width/truncation now uses display-width semantics, so wide glyphs
should clip cleanly without shifting HUD alignment.

1. Confirm version:

   ```bash
   voiceterm --version
   ```

2. If clipping still looks wrong, run with logs and share terminal/IDE details:

   ```bash
   voiceterm --logs
   ```

</details>

## Terminal and IDE Issues

Section shortcuts:

- [Settings or HUD lags](#settings-or-hud-lags-during-heavy-backend-output)
- [Meter looks too loud](#meter-looks-too-loud-for-normal-speech)
- [HUD duplicates in JetBrains terminals](#hud-duplicates-in-jetbrains-terminals)
- [Overlay flickers in JetBrains terminals](#overlay-flickers-in-jetbrains-terminals)
- [Startup banner lingers](#startup-banner-lingers-in-ide-terminal)
- [Theme colors look muted](#theme-colors-look-muted-in-ide-terminal)
- [Style-pack preview payload not applying](#style-pack-preview-payload-not-applying)
- [PTY exit write error in logs](#pty-exit-write-error-in-logs)

<details>
<summary>Expand Terminal and IDE Issues</summary>

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

1. Verify terminal key handling with `Ctrl+Y` first (Theme Studio should open).
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

2. While output is active, open Settings (`Ctrl+O`) and hold arrow navigation
   for several seconds.
3. Reduce competing terminal load (for example pause very noisy commands) and retry.
4. If lag persists, collect logs with `voiceterm --logs` and include:
   - terminal/IDE name + version
   - backend (`--codex` or `--claude`)
   - whether recording was active

### Full HUD right-panel visualizer missing or misplaced

In Full HUD mode, the right-panel visualizer (`ribbon`, `dots`, `heartbeat`)
renders on the **main status row** (top-right lane), not on the shortcuts row.
For `ribbon`, short sample history should render from a low baseline with peaks
above it, not as a full-height block across the entire lane.

1. Verify HUD panel mode is not `off` at launch (for example `--hud-right-panel ribbon`).
2. Confirm terminal width is large enough for Full HUD (`>= 60` columns is a
   practical minimum; very narrow widths may fall back to compact rendering).
3. If visualizer placement still looks wrong, run once with logs:

   ```bash
   voiceterm --logs
   ```

4. Share `${TMPDIR}/voiceterm_tui.log` with terminal/IDE details.

### Meter looks too loud for normal speech

If meter bars/dots frequently appear at warning/error levels during normal
speech:

1. Run calibration once:

   ```bash
   voiceterm --mic-meter
   ```

2. Check threshold in Settings (`Ctrl+O`) and adjust sensitivity with `Ctrl+]`
   or `Ctrl+\\` as needed.
3. Expected behavior after calibration:
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

### Style-pack preview payload not applying

If `VOICETERM_STYLE_PACK_JSON` is set, VoiceTerm loads that payload through the
style-schema parser and applies the resolved `base_theme` plus any supported
runtime visual overrides.

1. Validate payload shape:

   ```bash
   VOICETERM_STYLE_PACK_JSON='{"version":2,"profile":"ops","base_theme":"dracula","overrides":{"border_style":"rounded","indicators":"ascii","glyphs":"ascii"}}' voiceterm --version
   ```

   The `indicators` override is reflected in status-lane state glyphs (idle,
   auto/manual/recording, and processing/responding lanes). The `glyphs`
   override is reflected in HUD meter/icon families plus overlay chrome symbols
   (for example footer `[x] close` text and ASCII slider track/knob glyphs in
   Settings).

2. If payload is invalid/unsupported, VoiceTerm falls back to the selected
   built-in theme (startup should remain stable).
3. If payload is valid and includes `base_theme`, Theme Picker/quick-cycle
   switching is intentionally locked to that base theme during the session.
   You'll see a lock status message and dimmed picker rows for non-current
   themes.
4. Clear the override to confirm fallback path:

   ```bash
   unset VOICETERM_STYLE_PACK_JSON
   voiceterm --theme codex
   ```

</details>

## Install and Update Issues

Section shortcuts:

- [Homebrew link conflict](#homebrew-link-conflict)
- [Wrong version after update](#wrong-version-after-update)

<details>
<summary>Expand Install and Update Issues</summary>

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

</details>

## Enabling Logs

<details>
<summary>Expand Enabling Logs</summary>

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

</details>

## FAQ

Section shortcuts:

- [What languages does Whisper support?](#what-languages-does-whisper-support)
- [Which AI CLI backends work?](#which-ai-cli-backends-work)
- [Which Whisper model should I use?](#which-whisper-model-should-i-use)
- [Can I use VoiceTerm without Codex?](#can-i-use-voiceterm-without-codex)
- [Does VoiceTerm send voice audio to the cloud?](#does-voiceterm-send-voice-audio-to-the-cloud)

<details>
<summary>Expand FAQ</summary>

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

</details>

## Getting Help

<details>
<summary>Expand Getting Help</summary>

When reporting an issue, include:

1. `voiceterm --version`
2. Backend (`codex` or `claude`) and launch command
3. Terminal/IDE name and version
4. Relevant log excerpt from `${TMPDIR}/voiceterm_tui.log`

</details>

## See Also

<details>
<summary>Expand See Also</summary>

| Topic | Link |
|-------|------|
| Install guide | [INSTALL.md](INSTALL.md) |
| Usage guide | [USAGE.md](USAGE.md) |
| CLI flags | [CLI_FLAGS.md](CLI_FLAGS.md) |
| Whisper guide | [WHISPER.md](WHISPER.md) |

</details>
<!-- markdownlint-enable MD033 -->
