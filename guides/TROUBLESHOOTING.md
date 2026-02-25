# Troubleshooting
<!-- markdownlint-disable MD033 -->

Single troubleshooting reference for VoiceTerm.
Start with the quick-fix table, then jump to the matching section.

Fast first checks:

1. Run `voiceterm --version` to confirm you are on the build you expect.
2. Run with logs: `voiceterm --logs`.
3. If wake mode is involved, check the HUD wake label (`Wake: ON`, `Wake: PAUSED`, `Wake: ERR`).

## Quick Fixes

| Problem | First action | Section |
|---------|--------------|---------|
| No speech detected | Lower mic threshold (`Ctrl+\\`) | [Status Messages](#status-messages) |
| Voice not recording | Check microphone permissions | [Audio Setup](#audio-setup) |
| Voice macro not expanding | Validate macros file + toggle state | [Status Messages](#status-messages) |
| Codex/Claude not responding | Verify install + login | [Backend Issues](#backend-issues) |
| Claude executes actions without confirmation | Disable permission-skip mode | [Backend Issues](#backend-issues) |
| Full HUD shows `Wake: ERR` | Verify wake listener startup/log path details | [Status Messages](#status-messages) |
| Wake phrase does not trigger capture | Verify wake mode and phrase match | [Wake-word enabled but no wake triggers yet](#wake-word-enabled-but-no-wake-triggers-yet) |
| Auto-voice not triggering | Check prompt detection | [Backend Issues](#backend-issues) |
| Dev panel not opening | Verify `--dev` flag at launch | [Backend Issues](#backend-issues) |
| Transcript queued while backend is busy | Wait for prompt or tune regex | [Backend Issues](#backend-issues) |
| Wrong version after update | Check PATH + reinstall flow | [Install and Update Issues](#install-and-update-issues) |
| Settings/HUD lags while backend is busy | Reduce output load and capture logs | [Terminal and IDE Issues](#terminal-and-ide-issues) |
| Meter looks too loud at normal speech | Validate meter behavior and sensitivity | [Terminal and IDE Issues](#terminal-and-ide-issues) |
| Startup splash behaves oddly | Tune splash env vars | [Terminal and IDE Issues](#terminal-and-ide-issues) |
| Theme colors look muted | Verify truecolor env | [Terminal and IDE Issues](#terminal-and-ide-issues) |
| Theme file edits do not apply | Verify `--theme-file` / `VOICETERM_THEME_FILE` and check logs | [Terminal and IDE Issues](#terminal-and-ide-issues) |

## Status Messages

### No speech detected

The mic recorded but no voice crossed the current threshold.

1. Speak louder or closer to the mic.
2. Lower threshold with `Ctrl+\\` (or `Ctrl+/`).
3. Run `voiceterm --mic-meter` to calibrate.

### Voice macro not expanding

Macros load from `<project>/.voiceterm/macros.yaml` and apply only when
`Settings -> Macros` is ON.

1. Confirm file path and YAML structure.
2. Check `Macros` toggle state in Settings (`Ctrl+O`) since startup default is `OFF`.
3. Check trigger text match (case/whitespace-insensitive).
4. Run `./scripts/macros.sh validate --output ./.voiceterm/macros.yaml`.
5. Restart VoiceTerm after editing macros.

<details>
<summary>More status message issues</summary>

### Wake: ERR

Wake listener startup failed. Voice capture can still be started manually, but
always-listening wake triggers are unavailable until startup succeeds.

1. Run with logs: `voiceterm --logs`.
2. Check the status line message for the wake-listener log path.
3. Re-check microphone access and selected input device (`voiceterm --list-input-devices`).
4. If using `--input-device`, copy the exact name from `--list-input-devices` output and retry.

### Voice capture failed (see log)

Capture could not start.

1. Check mic permissions for your terminal app.
2. Run `voiceterm --list-input-devices`.
3. Try a specific device: `voiceterm --input-device "Your Mic Name"`.
4. Re-run with logs: `voiceterm --logs`.

### Voice capture error (see log)

Recording or transcription failed at runtime.

1. Run with logs: `voiceterm --logs`.
2. Check `${TMPDIR:-/tmp}/voiceterm_tui.log` (macOS resolves from `TMPDIR`;
   Linux is usually `/tmp`).
3. Restart `voiceterm`.

### Processing... (stuck)

Transcription is taking longer than expected.

1. Wait up to 60 seconds for longer captures.
2. If still stuck, press `Ctrl+C` and restart.
3. Try a smaller model (`--whisper-model base`).

### Latency badge seems wrong in auto mode

The HUD latency badge shows transcript processing delay, not backend response time.
In auto mode, the last good sample stays visible between captures.

1. Re-run with logs: `voiceterm --logs`
2. Look for `latency_audit` lines in the log.
3. If `stt_ms` rises on longer utterances, that is expected for non-streaming transcription.
4. Compare `rtf` (real-time factor). Lower is faster.

### Transcript includes ambient-sound tags

If Whisper emits ambient placeholders such as `(siren wailing)` or
`(water splashing)`, update to the latest build. Current sanitizer rules strip
known non-speech tags.

If artifacts persist:

1. Run with logs: `voiceterm --logs`
2. Capture the exact emitted token from `${TMPDIR:-/tmp}/voiceterm_tui.log`
3. Report the phrase so the non-speech filter list can be extended.

### Transcript history has no entries

`Ctrl+H` only shows completed transcript captures.

1. Run one successful capture first (`Ctrl+R`, speak, wait for transcript).
2. Reopen transcript history (`Ctrl+H`) and verify entries appear newest-first.
3. If entries still do not appear, run with logs: `voiceterm --logs`

### Notification history has no entries

`Ctrl+N` shows runtime status notifications (for example mode toggles, warnings,
and errors), not transcript rows.

1. Trigger a status event first (for example `Ctrl+V` to toggle auto-voice).
2. Reopen notification history (`Ctrl+N`) and verify entries appear.
3. If entries still do not appear, run with logs: `voiceterm --logs`

### Notification history rows look misaligned

If borders or row widths look uneven in `Ctrl+N`, update to the latest release.
Recent builds fixed toast-history row width accounting for mixed glyph/color themes.

### Style-pack HUD border override does not apply

`components.hud_border` from `VOICETERM_STYLE_PACK_JSON` only applies when HUD border mode is `theme`.

1. Check current HUD border mode (`Ctrl+Y` -> `HUD borders`) or launch flag (`--hud-border-style`).
2. Set HUD borders to `theme` if you want style-pack `components.hud_border` to drive the Full HUD border set.
3. If you need fixed borders regardless of style-pack, keep `single`/`rounded`/`double`/`heavy`/`none`.

### Session memory file is missing

The markdown session-memory log is opt-in.

1. Start VoiceTerm with `--session-memory`.
2. If needed, set an explicit path: `--session-memory-path <PATH>`.
3. Speak once, then close VoiceTerm to flush pending lines.
4. Confirm the file exists (default: `<cwd>/.voiceterm/session-memory.md`).

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
interrupting, those are mouse event codes. They should be handled by the HUD
parser, not forwarded to the backend.

1. Confirm version: `voiceterm --version`
2. Re-run with logs: `voiceterm --logs`
3. If needed as a temporary workaround, set `Settings -> Mouse` to `OFF`
4. Report terminal/IDE + version if raw fragments still appear on latest build

Note for Cursor terminal:

- With `Mouse` ON, wheel/touchpad scrolling may not move chat history.
- The scrollbar can still be dragged to move up/down.
- If you want touchpad/wheel scrolling, set `Settings -> Mouse` to `OFF`.
  You can still operate HUD controls with keyboard focus and `Enter`.

</details>

## Audio Setup

### Voice not recording

Check microphone permissions:

- macOS: System Settings -> Privacy & Security -> Microphone
- Linux: verify PulseAudio/PipeWire access (`pactl list sources`)

<details>
<summary>More audio setup help</summary>

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

### Codex or Claude not responding

1. Verify backend CLI exists:

   ```bash
   which codex
   which claude
   ```

2. Verify authentication:

   ```bash
   voiceterm --login --codex
   voiceterm --login --claude
   ```

3. If login fails with `failed to spawn ... login`, your backend CLI binary is missing or not on `PATH`; reinstall the backend CLI and rerun step 1.

4. Restart `voiceterm` if the session is stuck.

<details>
<summary>More backend issues</summary>

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

### Codex or Claude reply rows are occluded

VoiceTerm suppresses HUD rows when Codex/Claude interactive prompts are
detected (approval walls plus reply/composer prompt markers), so your active
reply area stays visible. For reply/composer prompts, suppression stays active
while you type and clears when the prompt is submitted or canceled.

If reply rows still look clipped or overlapped:

1. Confirm version:

   ```bash
   voiceterm --version
   ```

2. Retry with a taller terminal first (long wrapped command paths can consume rows quickly).
3. Re-run with logs and capture a screenshot while the overlap is visible:

   ```bash
   voiceterm --logs --codex
   voiceterm --logs --claude
   ```

4. Include terminal name/version + screenshot + relevant
   `${TMPDIR:-/tmp}/voiceterm_tui.log` lines when reporting the issue.

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
   - relevant `${TMPDIR:-/tmp}/voiceterm_tui.log` lines

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

Wake-word listening is local. It depends on mic capture + local Whisper
transcription, so setup issues can block detections.

1. In Full HUD, confirm wake privacy status:
   - `Wake: ON` means always-listening is active.
   - `Wake: PAUSED` means wake listening is temporarily paused while capture/transcription is active.
   - `Wake: ON` is now a steady badge (no pulse blink), so visual state matches runtime state.
   - On macOS, the mic indicator (`orange dot`) can blink during internal wake-listener cycles. That does not mean wake mode turned off.
2. Confirm expected values in Settings (`Ctrl+O`) or via
   `--wake-word-sensitivity` / `--wake-word-cooldown-ms`.
3. Confirm a local Whisper model path is configured and usable in your install.
4. Try moderate sensitivity first (for example `0.55` to `0.70`), then retest.
5. Use expected wake phrases (`hey codex`, `ok codex`, `hey claude`, or
   `voiceterm`) and speak clearly near the mic.
   Common transcript variants like `code x` and `voice term` are accepted, and leading command tails (`hey codex ...`) are supported.
6. If this persists, keep using `Ctrl+R` / `Ctrl+E` controls and share logs
   (`voiceterm --logs`).

### Voice `send` does nothing / `Nothing to send`

The built-in `send` / `send message` / `submit` phrases only submit staged text
in `insert` send mode.

1. Confirm send mode is `insert` (`Ctrl+T`).
2. Dictate text first so staged input exists, then say `send`.
3. Wake-tail submit also works: `hey codex send` / `hey claude send`.
   It submits staged text in `insert` mode.
4. If no staged text exists in `insert` mode, `send` will show `Nothing to send`.

### Ctrl+E behavior feels inconsistent

`Ctrl+E` is finalize-only in `insert` mode.

1. While recording, `Ctrl+E` requests early finalize so transcript text lands in the input box sooner.
2. It does not send Enter to the backend.
3. When ready to submit, press Enter (or use `hey codex send`).

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
- [Theme Studio fallback line](#theme-studio-shows-fallback-line)
- [Startup banner lingers](#startup-banner-lingers-in-ide-terminal)
- [Theme colors look muted](#theme-colors-look-muted-in-ide-terminal)
- [Theme file edits do not apply](#theme-file-edits-do-not-apply)
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

3. Reproduce once and inspect `${TMPDIR:-/tmp}/voiceterm_tui.log` for `input bytes`
and `input events` lines.

### Ctrl+G quick theme cycle does not work

1. Verify terminal key handling with `Ctrl+Y` first (Theme Studio should open).
2. If `Ctrl+Y` works but `Ctrl+G` does not, check for shell/terminal keybinding
   overrides and disable that binding.
3. Use `VOICETERM_DEBUG_INPUT=1 voiceterm --logs` and inspect
   `${TMPDIR:-/tmp}/voiceterm_tui.log` for `Ctrl+G` input events.

### Theme Studio shows fallback line

If Theme Studio shows `(theme studio fallback; press Esc and reopen)`, VoiceTerm
detected a rare page-state mismatch and switched to a safe fallback instead of
crashing.

1. Press `Esc` to close Theme Studio.
2. Reopen Theme Studio with `Ctrl+Y`.
3. If it repeats, run with logs and capture one screenshot:

   ```bash
   voiceterm --logs
   ```

4. Include terminal/IDE details and relevant `${TMPDIR:-/tmp}/voiceterm_tui.log`
   lines when reporting.

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
2. Confirm terminal width is large enough for Full HUD (`>= 60` columns is a practical minimum).
3. If visualizer placement still looks wrong, run once with logs:

   ```bash
   voiceterm --logs
   ```

4. Share `${TMPDIR:-/tmp}/voiceterm_tui.log` with terminal/IDE details.

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
   include logs from `${TMPDIR:-/tmp}/voiceterm_tui.log`.

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

3. Share `${TMPDIR:-/tmp}/voiceterm_tui.log` if still reproducible.

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

This is usually a harmless shutdown race where the PTY session was already closing.

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

### Theme file edits do not apply

If you expect live updates from a TOML theme file:

1. Confirm the path is set with `--theme-file <PATH>` or `VOICETERM_THEME_FILE=<PATH>`.
2. Re-run once with logs:

   ```bash
   voiceterm --theme-file ~/.config/voiceterm/themes/my-theme.toml --logs
   ```

3. Save a valid TOML file and wait for the watcher poll cycle (~500ms).
4. If `VOICETERM_STYLE_PACK_JSON` is set, clear it while testing (`unset VOICETERM_STYLE_PACK_JSON`) because style-pack payloads take precedence over theme files.
5. Check `${TMPDIR:-/tmp}/voiceterm_tui.log` for theme-file parse/load warnings.

### Style-pack preview payload not applying

If `VOICETERM_STYLE_PACK_JSON` is set but your theme looks wrong:

1. Check that the JSON is valid. Invalid payloads fall back to the built-in theme.
2. If the payload sets `base_theme`, theme switching is locked to that theme for the session.
3. Clear the variable to reset: `unset VOICETERM_STYLE_PACK_JSON`
4. See [USAGE.md - Themes](USAGE.md#themes) for full style-pack details.

</details>

## Install and Update Issues

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
$(brew --prefix)/opt/voiceterm/libexec/rust/target/release/voiceterm --version
```

<details>
<summary>More install issues</summary>

### Homebrew link conflict

If `brew install voiceterm` fails because the command already exists:

```bash
brew link --overwrite voiceterm
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

- Debug log: `${TMPDIR:-/tmp}/voiceterm_tui.log`
- Trace log: `${TMPDIR:-/tmp}/voiceterm_trace.jsonl`

</details>

## FAQ

### How do I reset settings to defaults?

Delete the config file and restart VoiceTerm:

```bash
rm ~/.config/voiceterm/config.toml
```

### How do I uninstall VoiceTerm?

See [INSTALL.md - Uninstall](INSTALL.md#uninstall).

### What languages does Whisper support?

Whisper supports many languages. Start with `--lang en` (tested) or use
`--lang auto`.
Reference:
[Whisper supported languages](https://github.com/openai/whisper#available-models-and-languages)

### Which AI CLI backends work?

See [USAGE.md -> Backend Support](USAGE.md#backend-support).

### Which Whisper model should I use?

Start with `base` for speed, `small` for balance, `medium` for higher accuracy.
See [WHISPER.md](WHISPER.md) for full guidance.

### Can I use VoiceTerm without Codex?

Yes. Use Claude: `voiceterm --claude`

### Does VoiceTerm send voice audio to the cloud?

No. Whisper runs locally.

## Getting Help

<details>
<summary>Expand Getting Help</summary>

When reporting an issue, include:

1. `voiceterm --version`
2. Backend (`codex` or `claude`) and launch command
3. Terminal/IDE name and version
4. Relevant log excerpt from `${TMPDIR:-/tmp}/voiceterm_tui.log`

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
