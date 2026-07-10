# VoiceTerm Operator Console

Optional desktop Operator Console for the current Codex/Claude review-channel
flow.

Use this page in one of two ways:

- If you want to run the app, start at [Fast Start](#fast-start).
- If you want to extend the app, start at [Read This First](#read-this-first).

## Read This First

Use these docs in this order when you are extending the app:

- `app/operator_console/AGENTS.md`: local agent/developer rules for where code belongs
- `dev/active/operator_console.md`: active plan and scope
- `app/operator_console/views/README.md`: view package map
- `app/operator_console/theme/README.md`: theme package map
- `app/operator_console/state/README.md`: state package map
- `app/operator_console/tests/README.md`: test package map

## Plain-English Guide

This app is a desktop control room for the repo workflow.

- It shows repo state, review-channel state, and operator status in one place.
- It can launch the allowlisted `devctl` workflows the team already uses.
- It does not own the runtime, the PTY session logic, or the policy rules.
- It is a wrapper over repo-visible commands and artifacts, not a second
  backend.

If you only need one sentence: open the app, inspect the current repo/review
state, run `Dry Run` first, then use `Start Swarm` or `Launch Live` only after
the preflight is green.

## Quick Links

- Launch and first-run steps: [Fast Start](#fast-start)
- What the app is allowed to do: [What It Is](#what-it-is)
- Current supported feature set: [Current Scope](#current-scope)
- Developer/package layout: [Folder Map](#folder-map)
- Detailed plan and scope authority: [`dev/active/operator_console.md`](../../dev/active/operator_console.md)

## What It Is

This app is intentionally a thin wrapper:

- Rust still owns PTY/runtime/session behavior.
- `devctl review-channel` still owns launch/rollover commands.
- The desktop app reads repo-visible state and writes repo-visible operator
  decision artifacts.
- Typed `review_state` / `control_state` style artifacts are the intended
  primary contract. The markdown bridge and compatibility payload rebuilds are
  transitional fallback/debug inputs, not long-term backend authority.
- The desktop app now prefers the merged mobile relay read path when it can:
  it first reads the emitted `dev/reports/mobile/latest/full.json` projection
  bundle from `devctl mobile-status`, then falls back to rebuilding the merged
  review-channel + controller `phone-status` snapshot when that bundle has not
  been emitted yet.

## What It Is Not

- not an embedded terminal emulator
- not a replacement for the Rust overlay
- not a second command runner outside `devctl`
- not a hidden AI control plane

## Folder Map

The package is now being split by responsibility instead of letting `state/`
and `tests/` absorb everything.

- `app/operator_console/run.py`: app entrypoint
- `app/operator_console/views/`: Qt widgets and window surfaces
- `app/operator_console/views/README.md`: current view package map
- `app/operator_console/views/shared/`: shared widgets, text helpers, and small UI primitives
- `app/operator_console/views/workspaces/`: guided Home and Activity workspace surfaces
- `app/operator_console/views/actions/`: command, review, swarm, and process action mixins
- `app/operator_console/views/workflow/`: workflow-specific UI
- `app/operator_console/views/layout/`: layout and shell UI
- `app/operator_console/views/collaboration/`: conversation, task board, and timeline UI
- `app/operator_console/theme/`: theming, editor, import/export, preview
- `app/operator_console/theme/README.md`: theme-specific folder map
- `app/operator_console/theme/runtime/`: active theme state, persistence, gallery, and engine
- `app/operator_console/theme/editor/`: theme editor controls, preview, and motion playground
- `app/operator_console/theme/io/`: overlay import/export and file dialogs
- `app/operator_console/workflows/`: workflow launch commands, reports, presets
- `app/operator_console/collaboration/`: conversation, task board, timeline,
  context-pack helpers
- `app/operator_console/layout/`: persisted layout state
- `app/operator_console/state/`: shared models plus grouped snapshot, review,
  session, bridge, repo, activity, job, and presentation helpers
- `app/operator_console/tests/`: tests, now starting to mirror the same
  responsibility split

Root files that should stay at the package root:

- `app/operator_console/run.py`: app entrypoint
- `app/operator_console/help_render.py`: launcher/help text rendering
- `app/operator_console/launch_support.py`: launch/bootstrap helpers
- `app/operator_console/logging_support.py`: shared diagnostics/logging

For the messy subtrees:

- `app/operator_console/state/README.md` explains what still belongs in
  `state/` and what should move out.
- `app/operator_console/views/README.md` explains which UI files belong in
  `shared`, `workspaces`, `actions`, `workflow`, `layout`, or
  `collaboration`.
- `app/operator_console/theme/README.md` explains which theme files belong in
  `runtime`, `editor`, `io`, `config`, or `qss`.
- `app/operator_console/tests/README.md` explains how tests should mirror the
  runtime layout.

Rule of thumb:

- if it renders widgets, it belongs under `views/`
- if it shapes non-Qt data, it belongs under `state/`
- if it builds or stages commands, it belongs under `workflows/`
- if it edits or renders theme state, it belongs under `theme/`
- if it only exists to support package-wide launch/log/help behavior, it may
  stay at the root

## Fast Start

1. Launch the app from the repo root with `./scripts/operator_console.sh`.
2. Start on `Home` and read the current repo/review status.
3. Use `Dry Run` first to verify the workflow is healthy.
4. Use `Start Swarm` only when the preflight is green.
5. Use the diagnostics pane or `--dev-log` when something looks wrong.

## Current Scope

Phase-1 behavior:

- guided `Home` start screen that summarizes current state before you dive into
  raw panes
- `Mobile Relay` summaries on Home and Analytics that prefer the emitted
  `devctl mobile-status` bundle, with honest fallback to rebuilt merged
  control + review state and then raw controller `phone-status`
- side-by-side bridge-derived Codex, Claude, and Operator panes (parsed from `bridge.md`)
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
- workflow launchpads on Home and Activity that keep the selected markdown
  scope visible, show the latest audit/loop result inline, and make `Run
  Loop` audit `orchestrate-status` first before it launches the continuous
  `devctl swarm_run` loop
- automatic self-heal for stale markdown-bridge reviewer heartbeat metadata
  before `Dry Run`, `Launch Live`, `Start Swarm`, or `Rollover` continue, so
  the desktop app does not silently dead-end on an aged-out `Last Codex poll`
- typed Activity-tab quick actions for `review-channel --dry-run`,
  `status --ci`, `triage --ci`, and `process-audit --strict`
- staged Codex/Claude summary drafts derived from the selected report, with
  explicit provenance text copied from the current snapshot
- raw `bridge.md` view
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

## Agent And Dev Notes

If you are changing this app:

- do not add new feature files to the package root just because it is faster
- update the matching package-map README when ownership changes
- keep the main README simple and link to the package maps instead of dumping
  every implementation detail here
- treat `app/operator_console/AGENTS.md` as the local routing guide for future
  edits

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

Direct `app/operator_console/run.py` execution still works for development and
tests, but the shell wrapper above and the module invocation here are the
canonical operator-facing launch paths.

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

The `Audit` and `Run Loop` buttons use the same rule: visible launchpad state
first, raw launcher output second. `Run Loop` now audits the selected
workflow scope before it launches `devctl swarm_run --continuous`, so the app
blocks early on broken plan/sync state instead of pretending the loop started.

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
   python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format md --refresh-bridge-heartbeat-if-stale
   ```

4. If the dry run reports `ok: True`, `bridge_active: True`, and the expected
   Codex/Claude lane counts, the app's `Start Swarm` row should transition from
   `Swarm Preflight` to `Swarm Launching` and then to `Swarm Running` on
   macOS. The equivalent manual CLI live-launch path is:

   ```bash
   python3 dev/scripts/devctl.py review-channel --action launch --format md --refresh-bridge-heartbeat-if-stale
   ```

5. Watch the Operator Console plus `bridge.md`. A healthy run should show:
   - bridge-derived Codex and Claude panes refreshing from parsed `bridge.md` sections
   - diagnostics entries for launcher activity and bridge refreshes
   - `bridge.md` heartbeat fields changing instead of staying static
   - `markdown bridge only; live terminal telemetry unavailable` when `review_state.json` is absent

## Analytics Mode

The `Analytics` layout is currently a repo-visible review-signal dashboard, not
a live CI/deploy control tower. It shows bridge-derived warnings, approvals,
lane health, and worktree identity, and it marks unwired CI/test telemetry as
`n/a` instead of implying those feeds are already live.

1. When you want to test the handoff path, trigger a controlled rollover:

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
 bridge.md / review_state.json   devctl review-channel launch   dev-log artifacts
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
