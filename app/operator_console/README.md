# VoiceTerm Operator Console

Optional desktop Operator Console for the current Codex/Claude review-channel
flow.

This app is intentionally a thin wrapper:

- Rust still owns PTY/runtime/session behavior.
- `devctl review-channel` still owns launch/rollover commands.
- The desktop app reads repo-visible state and writes repo-visible operator
  decision artifacts.
- The desktop app now prefers the merged mobile relay read path when it can:
  it first reads the emitted `dev/reports/mobile/latest/full.json` projection
  bundle from `devctl mobile-status`, then falls back to rebuilding the merged
  review-channel + controller `phone-status` snapshot when that bundle has not
  been emitted yet.

## Current Scope

Phase-1 behavior:

- guided `Home` start screen that summarizes current state before you dive into
  raw panes
- `Mobile Relay` summaries on Home and Analytics that prefer the emitted
  `devctl mobile-status` bundle, with honest fallback to rebuilt merged
  control + review state and then raw controller `phone-status`
- side-by-side bridge-derived Codex, Claude, and Operator panes (parsed from `code_audit.md`)
- explicit `Codex Session` and `Claude Session` monitor panes backed by the
  review-channel full projection's agent registry plus current bridge state,
  so the app shows what each side is working on even before live PTY traces
  are projected into the desktop
- Activity tab with card-based agent summaries plus a selectable
  human-readable report reader (`Overview`, `Blockers`, `Codex`, `Claude`,
  `Operator`, `Approvals`)
- simple/technical read mode switch for report wording and footer status text
- one-click `Start Swarm` flow that runs dry-run preflight first, then the
  live Terminal.app launch on macOS when preflight is green, with visible
  green/yellow/red status on both Home and Activity surfaces
- typed Activity-tab quick actions for `review-channel --dry-run`,
  `status --ci`, `triage --ci`, and `process-audit --strict`
- staged Codex/Claude summary drafts derived from the selected report, with
  explicit provenance text copied from the current snapshot
- raw `code_audit.md` view
- `Launch Dry-Run`, `Launch Live`, and `Rollover` buttons, with live controls
  explicitly gated to the macOS Terminal.app path
- selectable desktop themes matching the overlay ids
  (`coral`, `claude`, `codex`, `chatgpt`, `catppuccin`, `dracula`, `nord`,
  `tokyonight`, `gruvbox`, `ansi`, `none`) plus a desktop `minimal` preset
- visible diagnostics pane for snapshot, approval, and launcher events
- optional persisted dev-log mode for startup, refresh, warnings, and command
  activity
- refresh-safe text panes that preserve your place unless you are already
  tailing the bottom of a log/output pane
- default `Workbench` startup with a top-row `Codex Session | Operator Spine |
  Claude Session` split and a dense lower utility row for launcher output,
  bridge, diagnostics, reports, and snapshot context
- visible splitter handles so panes can be resized horizontally and vertically
- `Workbench` layout mode with snap presets so Home, Activity, Monitor, and
  lane surfaces can stay visible together while you resize around them
- configurable rollover threshold and ACK wait time
- optional operator `approve` / `deny` artifacts when structured
  `review_state` approval packets exist

Not in scope yet:

- embedded interactive terminal emulation
- replacing the Rust overlay
- bypassing `devctl` or policy gates

The current session panes are honest about their source: they are repo-visible
review-channel registry/bridge surfaces, not embedded PTY terminals.

## Run

Preferred launcher from the repo root:

```bash
./scripts/operator_console.sh
```

The script auto-installs `PyQt6` for the current Python interpreter when it is
missing, then launches the desktop app. Manual fallback:

```bash
python3 -m pip install PyQt6
python3 -m app.operator_console.run
```

Pick a desktop theme explicitly when you want a different look:

```bash
./scripts/operator_console.sh --theme coral
./scripts/operator_console.sh --theme claude
./scripts/operator_console.sh --theme tokyonight
./scripts/operator_console.sh --theme minimal
```

If you omit `--theme`, startup now restores the last saved active desktop
theme from the theme engine and otherwise falls back to `codex`.

Persist repo-visible diagnostics when you are debugging launcher or bridge
issues:

```bash
./scripts/operator_console.sh --dev-log
```

Use a different repo-visible diagnostics root when needed:

```bash
./scripts/operator_console.sh --dev-log --log-dir dev/reports/review_channel/custom_operator_console
```

## Recommended Live Swarm Test

The desktop app can now run the guarded `Start Swarm` path itself, but the
canonical backend still remains `devctl review-channel`. Live launch and
rollover are still Terminal.app-backed on macOS only; other platforms should
use `Dry Run` and the repo-visible bridge artifacts.

`Start Swarm`, `Launch Live`, and `Rollover` are Terminal.app-backed live
controls. They stay enabled on macOS and are visibly gated off-platform; `Dry
Run` remains the honest preflight path everywhere.

1. Start the Operator Console with persisted logs:

   ```bash
   ./scripts/operator_console.sh --dev-log
   ```

2. On the `Home` or `Activity` surface, press `Start Swarm` and watch the
   visible preflight/live status row. The app will run the dry-run preflight
   first and only launch live sessions when the JSON preflight stays green.

3. If you want to inspect the canonical CLI path directly in parallel, verify
   the shared launcher is healthy without opening new sessions yet:

   ```bash
   python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format md
   ```

4. If the dry run reports `ok: True`, `bridge_active: True`, and the expected
   Codex/Claude lane counts, the app's `Start Swarm` row should transition from
   `Swarm Preflight` to `Swarm Launching` and then to `Swarm Running` on
   macOS. The equivalent manual CLI live-launch path is:

   ```bash
   python3 dev/scripts/devctl.py review-channel --action launch --format md
   ```

5. Watch the Operator Console plus `code_audit.md`. A healthy run should show:
   - bridge-derived Codex and Claude panes refreshing from parsed `code_audit.md` sections
   - diagnostics entries for launcher activity and bridge refreshes
   - `code_audit.md` heartbeat fields changing instead of staying static
   - `markdown bridge only; live terminal telemetry unavailable` when `review_state.json` is absent

## Analytics Mode

The `Analytics` layout is currently a repo-visible review-signal dashboard, not
a live CI/deploy control tower. It shows bridge-derived warnings, approvals,
lane health, and worktree identity, and it marks unwired CI/test telemetry as
`n/a` instead of implying those feeds are already live.

6. When you want to test the handoff path, trigger a controlled rollover:

   ```bash
   python3 dev/scripts/devctl.py review-channel --action rollover --rollover-threshold-pct 50 --await-ack-seconds 180 --format md
   ```

## Dev Logs

When `--dev-log` is enabled, the Operator Console writes repo-visible log
artifacts under:

- `dev/reports/review_channel/operator_console/latest.operator_console.log`
- `dev/reports/review_channel/operator_console/latest.events.ndjson`
- `dev/reports/review_channel/operator_console/latest.command_output.log`
- `dev/reports/review_channel/operator_console/sessions/<timestamp>/`

Logged events include:

- snapshot changes from the bridge/review-state surface
- wrapped command starts and exits
- raw launcher / rollover stdout and stderr
- staged AI draft text when `--dev-log` is enabled
- operator approve/deny actions

Use the files like this:

- `latest.operator_console.log`: operator-readable event stream
- `latest.events.ndjson`: structured diagnostics for tooling
- `latest.command_output.log`: raw subprocess output for triage

If `--dev-log` is not enabled, the diagnostics pane is still visible in the
window, but it stays memory-only for that run.

## Flow

```text
+-------------------- VoiceTerm Operator Console --------------------+
| Codex Bridge | Claude Bridge | Operator State | Raw bridge | Launcher | Diag |
+---------------------------+----------------------------------------+
                            |
                            v
                 repo-visible bridge, state, and commands
                            |
      +---------------------+---------------------+------------------+
      |                                           |                  |
      v                                           v                  v
 code_audit.md / review_state.json   devctl review-channel launch   dev-log artifacts
      |                                           |                  |
      +---------------------+---------------------+------------------+
                            |
                            v
                Rust runtime / provider CLI sessions
```

## Operator Decisions

When structured approval packets are present, the `Approve` and `Deny` buttons
write artifacts under:

- `dev/reports/review_channel/operator_decisions/*.json`
- `dev/reports/review_channel/operator_decisions/*.md`
- `dev/reports/review_channel/operator_decisions/latest.{json,md}`

This is a prototype bridge until the richer `review-channel` packet action
surface lands.
