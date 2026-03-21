# VoiceTerm Operator Console Plan

Status: execution mirrored in `dev/active/MASTER_PLAN.md` (MP-359)
Execution plan contract: required
Owner lane: Operator Console / shared-screen wrapper

## Scope

Build a bounded optional PyQt6 VoiceTerm Operator Console for the current
Codex/Claude review-channel workflow without replacing the Rust PTY runtime or
the canonical `devctl` control plane.

Current priority directive:
This work must continue past the thin shared-screen prototype into a fully
integrated repo-aware dev-environment controller shell. That means the desktop
app needs to expose typed repo-owned commands through manual controls, include
built-in guidance for how and when to use each workflow, and integrate bounded
AI through the same `Ask | Stage | Run` contract used elsewhere in this plan.
The app may grow broad in surface area, but it must stay narrow in authority:
repo-owned commands, plans, artifacts, and reports remain canonical.

This plan covers:

1. A read-first shared-screen desktop view for the current bridge-gated
   reviewer/coder loop so the operator can see Codex-owned, Claude-owned, and
   operator/review state side by side.
2. Thin desktop wrappers around existing repo-owned commands such as
   `devctl review-channel --action launch` and `--action rollover`.
3. A minimal operator approval/decision surface that records repo-visible
   artifacts instead of relying on hidden UI-only state.
4. A strict ownership split:
   Rust keeps PTY/runtime/session ownership, `devctl` keeps command/policy
   ownership, and PyQt6 is only a thin Operator Console surface.
5. A future-proof path that can be retired or folded into the Rust shared
   screen once the overlay-native review surface becomes canonical.
6. A repo-visible diagnostics mode that records the wrapper's view of bridge
   state, warnings, launch/rollover command lifecycle, and operator decisions
   so desktop-specific issues are debuggable without hidden UI state.
7. A purpose-built dark theme for the desktop wrapper so long-running operator
   sessions are readable and visually distinct from the canonical Terminal and
   overlay surfaces.
8. A maintainable Python package layout for `app/operator_console/` so
   view/model/command/logging/theme logic does not collapse into a few large
   mixed-responsibility files as the wrapper grows.
9. A bounded AI-assist layer that can summarize, explain, draft, and recover
   operator context when scripts or raw artifacts are noisy or incomplete,
   without replacing the canonical script/policy path for real execution.
10. A one-click in-app swarm kickoff path (`Start Swarm`) that performs the
    same guarded launch sequence as the CLI path and immediately shows whether
    the run is healthy.
11. Direct in-app yes/no and terminal-control buttons that call typed
    repo-owned command surfaces once MP-355 exposes them, instead of stopping
    at artifact-only placeholder actions.
12. A repo-visible CI/CD status surface so the operator can see whether checks,
    workflows, and release gates are green, what failed, and where the
    relevant logs/artifacts live without leaving the app.
13. A push-aware workflow history surface so the operator can see the runs
    created by the latest pushes/SHAs, which branch/commit triggered them, and
    whether the repo is actually green enough to integrate.
14. An allowlisted script/action palette that can run repo-owned `devctl`
    workflows from buttons inside the app, with optional AI help to choose,
    explain, stage, or draft the right action without bypassing guardrails.
15. A swarm-planning surface that reuses the existing adaptive
    `autonomy-swarm` / `swarm_run` sizing logic so the app can recommend a
    sensible agent count from scope, diff size, prompt size, token budget, and
    feedback signals instead of making the operator guess.
16. A layout-workbench path so panes can be resized, snapped, and rearranged
    intentionally instead of being trapped in one hard-coded dashboard shape.
17. A multi-theme system that can start with Operator Console presets but is
    designed to converge on VoiceTerm overlay theme/style-pack semantics rather
    than becoming a separate desktop-only styling island.
18. A repo-aware Command Center that exposes allowlisted repo-owned workflows
    through buttons, forms, presets, and a searchable command palette while
    preserving exact command previews, exit status, logs, and audit trails.
19. A first-class instruction layer so every major panel and workflow can
    explain what it does, when to use it, preconditions, exact command path,
    success signals, and recovery steps without forcing the operator to leave
    the app for basic operating guidance.
20. Repo-state-aware workflow modes such as Develop, Review, Swarm, CI Triage,
    Release, Process Cleanup, and Docs/Governance so the desktop shell can
    steer the operator toward the right tools and checks for the current repo
    state instead of acting like a generic dashboard.
21. An integrated AI-help surface that can answer operator questions, explain
    failures, summarize raw artifacts/logs, recommend the next step, and stage
    commands or draft artifacts through an explicit `Ask | Stage | Run`
    interaction contract.
22. A full repo-workbench path that combines workspace state, artifacts,
    diff/review, CI visibility, process hygiene, and optional terminal/shell
    views so the desktop app can evolve into a real dev-environment controller
    without bypassing repo-owned backends.
23. A main-window decomposition pass that treats the current 12-mixin shell as
    architecture debt: move duplicated lane builders and shared presentation
    logic into explicit composition helpers so the window stays inspectable
    instead of becoming a hidden-indirection pile.

Out of scope for this tranche:

1. Replacing the Rust overlay with a desktop runtime.
2. Re-implementing PTY spawn, resize, ANSI rendering, or session cleanup in
   PyQt6.
3. Free-form agent coordination via pixels or screen scraping.
4. Desktop-specific policy bypasses outside the typed review/controller path.
5. Letting the desktop wrapper become an unbounded second tooling subtree with
   mixed UI, command, parsing, and artifact logic in the same files.
6. AI-issued raw shell execution or hidden side effects that bypass repo-owned
   `devctl` commands, typed artifacts, or operator approval.
7. Treating in-app guidance as optional polish; workflow instructions and
   failure-recovery cues are part of the controller surface, not external-only
   documentation.

## Execution Quality Contract (Plan-Specific)

All Operator Console work executed from this plan must preserve a simple,
maintainable Python package shape:

1. Keep public modules small enough that ownership is obvious at a glance;
   split files before UI/controller/model/theme/logging concerns tangle.
2. Prefer explicit names and short docstrings over implicit Qt-only behavior.
3. Keep repo-artifact parsing, subprocess command execution, widget rendering,
   and theme/style plumbing in separate modules whenever practical.
4. New desktop behavior must come with tests at the extracted-module seam, not
   only through one large window integration path.
5. Desktop docs must show the real launch/test flow so developers can validate
   the wrapper without reverse-engineering the command sequence.
6. Button clicks must stay thin wrappers over typed repo-owned command paths;
   the GUI should not invent private control logic that the CLI cannot audit.
7. Script/action buttons must stay allowlisted and auditable; AI may help pick
   or prefill an action, but real execution must still route through explicit
   repo-owned commands.
8. Swarm sizing in the GUI must reuse the repo-owned planner logic and report
   the inputs it used (`prompt_tokens`, `token_budget`, metadata, feedback
   signals), not invent a second desktop-only heuristic.
9. Desktop theming must be registry-driven and documented; do not scatter color
   literals across widgets once multiple theme packs exist.
10. Layout customization must remain bounded and inspectable: snap/grid/dock
    behavior should persist through explicit layout state, not hidden ad-hoc
    widget geometry mutations.
11. Every executable workflow surface must expose operator guidance in-app:
    `What this does`, `When to use it`, `Before you run it`,
    `What it will execute`, `What success looks like`, and
    `What to do if it fails`.
12. AI and manual control paths must share one typed command catalog and one
    validation layer; there may not be separate AI-only and button-only
    execution semantics.
13. AI interactions must follow `Ask | Stage | Run`: answer/explain first,
    prepare typed actions or draft artifacts second, and execute only through
    explicit approval on the same repo-owned backend used by manual controls.
14. Workflow modes must remain repo-state-aware and should point the operator
    back to active-plan scope, changed-path risk class, and required check
    bundles rather than acting like a generic terminal dashboard.
15. The main window must not accrete mixins faster than it accretes
    composition boundaries: any duplicated lane builder or repeated panel
    assembly logic should be extracted into a shared helper before the window
    gets larger.

## Locked Decisions

1. Rust remains the runtime/PTY owner. The desktop app is a wrapper around
   repo artifacts and repo commands, not a parallel runtime.
2. The current desktop slice is optional and non-canonical. If it diverges from
   Rust overlay or `devctl` behavior, the desktop wrapper is wrong.
3. The first delivery is read-first and wrapper-first:
   side-by-side state, launch/rollover controls, and operator decision logging.
4. Embedded interactive terminals are not a Phase-1 requirement. If they are
   needed later, they must still ride on the existing Rust/runtime ownership
   model instead of replacing it.
5. Operator decisions must be written into repo-visible artifacts under
   `dev/reports/review_channel/` so future command surfaces can ingest or
   supersede them.
6. AI integration in the wrapper is assistive, not authoritative: it may
   summarize, explain, draft, classify, and suggest, but any mutating action
   must still route through typed repo-owned commands or explicit operator
   decision artifacts.
7. The long-term desktop direction may grow into a repo-aware dev-environment
   controller, but only as a front-end over typed repo-owned commands,
   artifacts, plans, and reports rather than a second execution authority.
8. The canonical AI interaction contract is `Ask | Stage | Run`:
   the app may answer questions and stage commands/artifacts freely, but real
   execution still requires an explicit typed action routed through the shared
   command backend.
9. Built-in usage guidance and playbooks are required product surfaces, not
   optional README-only support material.
10. The desktop app remains deny-by-default for command execution; it may
    expose embedded terminals or shell views later, but those do not waive the
    allowlisted-command policy for controller actions.
11. Any future Electron/Tauri desktop shell is post-PyQt follow-up only; it
    must reuse the same repo-owned backend contract rather than becoming a
    second backend or control plane.

## Cross-Plan Dependencies

1. `dev/active/review_channel.md` owns the shared-screen semantics, packet
   vocabulary, and operator approval intent model for MP-355.
2. `dev/active/continuous_swarm.md` owns the launch/rollover/liveness contract
   the Operator Console wraps for MP-358.
3. `dev/active/autonomous_control_plane.md` owns the shared typed-action and
   approval/waiver direction for MP-340.
4. `dev/active/devctl_reporting_upgrade.md` owns the status/report/triage,
   CIHub, and CI artifact/reporting direction the Operator Console must reuse
   instead of inventing a second reporting stack.
5. `dev/active/memory_studio.md` owns memory pack semantics, memory-control
   closure, and review/control attachment rules; the Operator Console may
   mirror future memory/review/controller artifacts but must not become a
   second memory authority.
6. `AGENTS.md`, `dev/scripts/README.md`, and
   `dev/guides/DEVCTL_AUTOGUIDE.md` remain the policy/docs authority for the
   underlying command paths.

## Reference Inputs

1. `network-monitor-tui` is a reference for dense read-only observability
   panels and graph presentation, but repo-owned `devctl` collectors remain
   the only analytics source of truth for this shell.
2. The local `gitui-main/app` design reference is useful for agent-first
   side-rail/workboard hierarchy and phone-friendly information density, but
   it is a visual/layout reference only, not a runtime dependency.
3. `FileHasherV2_HistoryPatch` and related local PyQt theme/chart work are
   reference inputs for richer QSS/theme-pack import, chart widgets, and
   style-authoring UX, but all persisted styling must still target the
   canonical VoiceTerm theme/style-pack contract.
4. `integrations/code-link-ide` is a future pairing/notifier reference for
   desktop/phone relay work and must not become the desktop shell's backend or
   state authority.

## Execution Checklist

### Phase 0 - Reactivation And Architecture

- [x] Reactivate desktop wrapper work as a bounded optional prototype rather
      than a second control plane.
- [x] Record the non-negotiable ownership split:
      Rust runtime, `devctl` commands, PyQt6 wrapper.
- [x] Define the prototype artifact roots and decision-log behavior.
- [x] Document the retirement/fold-in trigger once the Rust shared screen is
      canonical.

### Phase 1 - Read-First Shared Screen

- [x] Add an optional PyQt6 app under `app/operator_console/`.
- [x] Show three visible panes:
      Codex Bridge Monitor, Claude Bridge Monitor, and Operator Bridge State.
- [x] Read current state from repo-visible files first:
      `bridge.md`, `dev/active/review_channel.md`, and optional future
      `review_state` JSON if present.
- [x] Add refresh polling that does not mutate the repo by default.
- [x] Provide launch/rollover command buttons that wrap existing `devctl`
      review-channel commands instead of cloning launcher logic.
- [x] Apply a deliberate desktop-cockpit theme that keeps the wrapper easy to
      read during long review sessions.
- [x] Preserve operator scroll position during bridge refreshes and only
      auto-follow output panes when the operator is already tailing the bottom.
- [x] Add an optional Operator Console dev-log mode that mirrors snapshot changes,
      wrapped command activity, and operator actions into repo-visible
      artifacts under `dev/reports/review_channel/operator_console/`.
- [x] Add a `Start Swarm` button that runs JSON dry-run preflight, then live
      launch chaining, and ends in a visible green/yellow/red status surface
      plus command preview instead of requiring the operator to chain those
      steps manually.

### Phase 1.5 - Information Hierarchy And Structured Views

- [x] Extract reusable widgets (`StatusIndicator`, `KeyValuePanel`,
      `SectionHeader`, `AgentSummaryCard`) into `widgets.py` so panel layout
      is composable and testable.
- [x] Add `AgentLaneData` dataclass to `bridge_model.py` with structured
      key-value rows and status-hint derivation (active/warning/stale/idle)
      from parsed section keywords and timestamps.
- [x] Replace text-dump `QPlainTextEdit` panels with structured `KeyValuePanel`
      widgets that show key-value pairs at a glance with a "View Raw" toggle.
- [x] Add toolbar status dots for Codex, Claude, and Operator with
      bridge-derived status hints (active/warning/stale/idle) and structured
      `KeyValuePanel` lane cards showing parsed `bridge.md` sections.
- [x] Extend `theme.py` with QSS for all new widget types: status dots,
      KV rows, section headers, summary cards, role badges.
- [x] Add 19 new tests covering all widget classes and structured lane builders.

### Phase 2 - Operator Decisions

- [x] Surface pending approval packets when structured `review_state` artifacts
      are available.
- [x] Until the full `review-channel` packet action surface exists, record
      operator `approve`/`deny` selections as repo-visible decision artifacts
      under `dev/reports/review_channel/operator_decisions/`.
- [x] Keep decision artifacts explicit about being prototype wrapper outputs so
      later `review-channel --action ack|apply|dismiss` work can supersede them
      cleanly.
- [x] Treat prototype operator decision artifacts as wrapper-only state:
      they do not satisfy Memory Studio `MP-238` / `MP-243` closure and must
      not become a second memory/control authority.
- [x] Do not silently execute approval-gated actions from the desktop wrapper.
- [ ] Promote `Approve` / `Deny` from artifact-only placeholders to direct
      typed `devctl review-channel` actions once the CLI exposes
      `ack|apply|dismiss` semantics.
- [ ] Add a button-to-command routing layer so operator yes/no actions write
      the same audit trail and state transitions as the CLI path, not a
      desktop-only side channel.
- [ ] Keep a clear fallback mode: if the typed action surface is unavailable,
      the UI must say that explicitly instead of pretending the click executed
      a live command.

### Phase 2.5 - Diagnostics And Triage

- [x] Add a visible diagnostics pane for launcher, refresh, warning, and
      approval events.
- [x] Add a persisted `--dev-log` mode that writes repo-visible event logs,
      NDJSON diagnostics, and raw command output under
      `dev/reports/review_channel/operator_console/`.
- [x] Document the operator triage path so desktop-specific failures are
      inspectable from the repo without relying on hidden UI memory.

### Phase 2.6 - Package Reorganization Into Directories

This migration is complete. The former flat-layout risk is retired and the
tree now follows the ownership boundaries below; keep future panels inside
`state/`, `views/`, and `theme/` instead of collapsing new work back into the
package root.

Target directory layout:

```
app/operator_console/
├── __init__.py
├── run.py                        # CLI entrypoint (stays at root)
├── state/                        # PyQt-free data models and artifact I/O
│   ├── __init__.py
│   ├── activity_assist.py        # bounded AI-assist draft builders
│   ├── bridge_sections.py        # markdown bridge parsing
│   ├── command_catalog.py        # allowlisted command registration + metadata
│   ├── command_builder.py        # devctl command generation
│   ├── lane_builder.py           # lane/status derivation
│   ├── models.py                 # shared dataclasses
│   ├── operator_decisions.py     # repo-visible decision artifact writes
│   ├── playbook_registry.py      # workflow guidance + usage contracts
│   ├── presentation_state.py     # snapshot-derived text, KPI, digest, risk projection
│   ├── review_state.py           # structured approval loading
│   ├── snapshot_builder.py       # file I/O + snapshot assembly
│   ├── workflow_modes.py         # mode routing + repo-state recommendations
│   ├── health_collector.py       # (Phase 6) system metrics
│   └── diff_model.py             # (Phase 7) git diff parsing
├── views/                        # PyQt6 panel widgets
│   ├── __init__.py
│   ├── ai_help_panel.py          # Ask | Stage | Run AI operator surface
│   ├── command_center.py         # allowlisted command palette / forms / history
│   ├── instruction_panel.py      # in-app usage guidance + playbooks
│   ├── main_window.py            # OperatorConsoleWindow (from ui.py)
│   ├── mode_switcher.py          # Develop / Review / Swarm / CI etc.
│   ├── widgets.py                # StatusIndicator, KeyValuePanel, etc.
│   ├── approval_panel.py         # (Phase 3)
│   ├── timeline_panel.py         # (Phase 4)
│   ├── guardrails_panel.py       # (Phase 5)
│   ├── health_panel.py           # (Phase 6)
│   ├── workspace_panel.py        # branch / dirty tree / active-plan snapshot
│   ├── ci_panel.py               # workflows / reports / blockers
│   └── diff_panel.py             # (Phase 7)
├── theme/                        # Styling
│   ├── __init__.py
│   ├── colors.py                 # COLOR dict
│   └── stylesheet.py             # QSS builder
├── logging_support.py            # Diagnostics (stays at root — cross-cutting)
└── tests/                        # Mirrors source structure
    ├── __init__.py
    ├── state/
    │   ├── __init__.py
    │   ├── test_state_modules.py
    │   ├── test_playbook_registry.py
    │   ├── test_presentation_state.py
    │   └── test_command_builder.py
    └── views/
        ├── __init__.py
        ├── test_ai_help_panel.py
        ├── test_command_center.py
        ├── test_widgets.py
        └── test_scroll_behavior.py
```

Checklist:

- [x] Extract `widgets.py` from `ui.py` (done in Phase 1.5).
- [x] Create `state/` directory: move `bridge_model.py` and
      `command_builder.py` into it.
- [x] Create `views/` directory: move `ui.py` → `views/main_window.py` and
      `widgets.py` → `views/widgets.py`.
- [x] Create `theme/` directory: split `theme.py` into `theme/colors.py`
      (COLOR dict) and `theme/stylesheet.py` (QSS builder).
- [x] Update all internal imports (`from .state.bridge_model import ...`,
      `from .views.widgets import ...`, etc.).
- [x] Move tests into mirrored subdirectories under `tests/`.
- [x] Update `run.py` import path from `from .ui import run` to
      `from .views.main_window import run`.
- [x] Verify 35+ operator console tests still pass after reorganization.
- [x] Document the recommended live-launch test flow in the app README so
      developers know how to start Codex + Claude and what panes/logs should
      move when the system is healthy.

### Phase 2.7 - Layout Workbench And Resizable Grid

- [x] Replace the fixed nested splitter-only mental model with a bounded layout
      workbench that supports one resize-first shared-screen composition over
      the same persistent panes.
- [x] Allow operators to resize both horizontally and vertically with visible
      handles and explicit snap presets.
- [x] Add snap-to-grid / preset recovery controls so panes can be repositioned
      deliberately without devolving into freeform pixel dragging.
- [x] Support a first bounded preset set:
      Balanced, Lane Focus, Launch Center, and Activity Focus.
- [x] Keep the layout state repo-visible or user-config-visible so issues are
      reproducible when a developer reports "the screen got weird."

### Phase 2.7.5 - Multi-Agent Layout Scale-Up

- [ ] Extend the Workbench from the current three-lane presets into bounded
      4/6/8+ visible-agent layouts with per-lane collapse/expand, snap-to-grid
      resizing, and lane-group presets for reviewer/coder/operator mixes.
- [ ] Keep high-lane-count layouts driven by repo-visible lane/session
      metadata (`review-channel`, `autonomy`, future `controller_state`) so
      the desktop does not invent placeholder agents or desktop-only lane ids.
- [x] Persist layout state with explicit reset/export/import so layout bugs are
      reproducible and recoverable instead of living in hidden widget memory.
- [ ] Support both summary-density and terminal-density variants for the same
      lane set so operators can flip between cards and dense monitors without
      hand-rebuilding the screen.

### Phase 2.8 - Theme Registry And Overlay Parity

- [x] Promote the desktop stylesheet into a theme registry with named presets,
      selector UI, and CLI support.
- [x] Ship at least one minimal theme plus desktop themes that intentionally
      echo VoiceTerm overlay themes such as Codex and Coral.
- [x] Tighten the active-theme identity/apply boundary so the toolbar theme
      selector and the theme editor/engine share one applied-theme authority
      instead of split preset/draft ownership.
- [ ] Keep launch/docs/status wording honest about current live-launch support
      and wired-vs-placeholder CI/analytics data so the desktop shell never
      implies broader execution or reporting coverage than the repo actually
      provides today.
- [ ] Strengthen proof beyond dry-run/mocked paths: exercise the real
      launcher/startup path plus representative mutating operator actions and
      launcher-script execution in local/CI coverage.
- [ ] Define the mapping contract between desktop theme ids and Rust overlay
      theme/style-pack semantics so the two surfaces can converge instead of
      drifting.
- [x] Add read-path parity first: the desktop console should be able to import
      Rust theme/style-pack metadata so a saved overlay theme can render with
      the same intent in PyQt without manual duplication.
- [ ] Add export/write parity second: desktop theme edits should only write the
      Rust style-pack/theme format once the mapping is proven stable and
      round-trip-safe.
- [ ] Do not invent a second persistent theme schema for the desktop app; keep
      one canonical VoiceTerm style-pack/theme contract with optional
      desktop-only preview derivations layered on top.
- [ ] Long-term: prefer importing/exporting shared style-pack/theme metadata
      over maintaining separate desktop-only theme definitions by hand.
- [x] Expand the theme editor beyond global colors/metrics into fuller
      page-scoped control groups for text, borders, buttons/inputs, sidebar
      navigation, lane cards, approval surfaces, diagnostics/log panes, and
      raw-text/diff views so the desktop editor can style nearly the full UI.
- [ ] Route the remaining hardcoded desktop styling through the shared semantic
      color + token registry so live theme edits reach the toolbar, tabs,
      approval queue, activity workspace, analytics/report panes, dialog
      chrome, splitters, and detail dialogs instead of stopping at the current
      partial surface set.
- [ ] Grow the live preview into fuller UI parity coverage: toolbar/header,
      approval cards, tabs, activity/report cards, diagnostics/log monitors,
      diff/raw panes, and representative empty/error states should all be
      visible in-editor before a preset is saved.
- [ ] Add richer editor controls comparable to the fuller reference workbench:
      dedicated text/border/effects/density sections, better field guidance,
      and reset/apply affordances that make broad theme authoring practical
      without hand-editing JSON.
- [ ] Add immediate in-app theme guidance so operators can understand import
      scope, color semantics, and preview behavior without leaving the app;
      this includes explicit explanation for diff/raw-text highlighting and
      what the current desktop theme editor can and cannot round-trip yet.
- [ ] Add explicit semantic highlight controls for neutral/info, success,
      warning, danger, diff-added, and diff-removed states so normal markdown
      or report emphasis never inherits misleading error colors by accident.
- [ ] Add broader PyQt/QSS theme-pack import and paste workflows that map
      source styles into the shared semantic token model, with explicit
      unmapped-field reporting instead of silent loss or a second desktop-only
      schema.

### Phase 3 - Approval Queue Center Stage

- [x] Extract a self-contained `ApprovalQueuePanel(QWidget)` into
      `views/approval_panel.py` that replaces the inline approval list.
- [x] Add per-item row widgets showing `packet_id`, `summary`, and
      `policy_hint` as a colored severity badge.
- [x] Add a detail pane that expands on selection showing `from_agent` →
      `to_agent` flow, `requested_action`, `body`, and `evidence_refs`.
- [x] Add a risk/confidence indicator derived from `policy_hint` keywords.
- [x] Restructure the top row to give the approval queue more visual weight
      (wider center column with vertical splitter, 5:4:4 stretch).

### Phase 4 - Agent Timeline

- [x] Add `TimelineEvent` dataclass and `build_timeline_from_snapshot()` in
      a dedicated PyQt-free state module to synthesize chronological events
      from snapshot state and historical handoff artifacts.
- [x] Create `timeline_panel.py` with a `TimelinePanel(QWidget)` showing
      color-coded per-agent events (green=Codex, blue=Claude, orange=Operator,
      gray=System) sorted newest-first.
- [x] Add filter toggle buttons per agent so the operator can focus the
      timeline.
- [x] Replace lower-row "Raw Bridge" panel with `TimelinePanel` (move raw
      bridge into a tab or toggle within it).

### Phase 4.5 - Shared Workflow Layout

- [x] Add a shared top strip showing:
      current slice, shared goal, current writer, branch, and swarm health.
- [ ] Keep the core center layout intentionally asymmetric:
      Claude lane, narrow relay/approval spine, Codex lane.
- [x] Add `last seen` and `last applied` markers to both actor lanes so the
      operator can tell they are mutually aware of each other's latest state.
- [x] Add a bottom workflow timeline showing transitions such as:
      posted -> read -> acked -> implementing -> tests -> reviewed -> apply.
- [x] Add a shared next-action footer so the screen always answers
      "what happens now?" without requiring the operator to inspect raw logs.
- [ ] Keep this layout readable as a single collaborative workflow rather than
      a generic dashboard or two unrelated terminal windows.

### Phase 4.6 - AI-Assisted Interpretation And Drafting

- [x] Add a bounded Activity-tab AI draft surface that stages audit/help
      prompts from the current snapshot with explicit provenance text and
      no hidden command execution.
- [x] Add a provider-targeted Activity-tab AI summary draft flow so the
      operator can choose Codex or Claude as the draft target without
      auto-running either provider in the background.
- [ ] Add an opt-in live `AI Summary` path that can send the selected
      Activity report to a bounded Codex or Claude session, return a readable
      result in-app, and keep the current staged-draft path as the safe
      fallback when no provider session or credentials are available.
- [ ] Require the live `AI Summary` result path to stay explicit and auditable:
      operator-triggered only, provider-selected, timeout-bounded,
      repo-visible in diagnostics/dev-log output, and labeled with model,
      timestamp, source report, and advisory-vs-script provenance.
- [ ] Add a first-class AI Help panel where the operator can ask repo,
      workflow, CI, plan, and tooling questions in plain language without
      leaving the app.
- [ ] Implement the canonical `Ask | Stage | Run` interaction model:
      `Ask` answers/explains, `Stage` prepares typed commands or draft
      artifacts, and `Run` executes only after explicit approval through the
      shared command backend.
- [ ] Add a bounded AI-assist panel/service layer that can use available
      Claude/Codex credentials or sessions for interpretation features.
- [ ] Use AI where scripts are weak or overly literal:
  - [ ] summarize packet/body/log noise into operator-readable state
  - [ ] explain why a lane is blocked or what changed since last poll
  - [ ] draft operator notes, review packets, handoff text, and job updates
  - [ ] propose next actions when artifacts are incomplete but observable state
        is sufficient
  - [ ] cluster noisy diagnostics into a likely root-cause summary
  - [ ] answer "what should I do now?" from repo state, active-plan scope,
        failing checks, dirty-tree status, and command history
  - [ ] map plain-language requests onto the allowlisted command catalog with
        an exact staged command preview
- [ ] Require provenance on all AI-produced output:
      model/source, timestamp, confidence, and whether the result is advisory
      vs typed-script-derived.
- [ ] Keep AI output staged-first:
      suggestions may prefill fields or create draft artifacts, but may not
      silently execute commands or mutate shared state outside typed handlers.
- [ ] When an AI suggestion implies a real action, route execution back through
      existing `devctl`/artifact paths rather than letting the model call raw
      shell from the GUI.
- [ ] Persist meaningful AI-generated operator help into repo-visible logs or
      draft artifacts so the wrapper does not become a hidden-memory side
      channel.

### Phase 4.7 - Usage Guidance And Playbooks

- [x] Add top-level `Help` and `Developer` menus so workflow guidance,
      color/highlight semantics, and "how this runs" explanations are visible
      inside the app instead of living only in repo docs.
- [x] Add a guided `Home` start surface so the app opens into an operator
      launchpad instead of dropping straight into raw dashboards.
- [x] Add a simple/technical read mode switch so summaries and footer state can
      be understood by both less-experienced and highly technical users.
- [ ] Add a reusable `InstructionPanel` / help drawer that every major surface
      can populate with `What this does`, `When to use it`,
      `Before you run it`, `What it will execute`, `What success looks like`,
      and `What to do if it fails`.
- [ ] Create built-in workflow playbooks for at least:
      Develop, Review, Swarm, CI Triage, Release, Process Cleanup, and
      Docs/Governance.
- [ ] Make playbooks repo-state-aware: branch, dirty tree, active-plan scope,
      pending approvals, failing workflows, and required check bundle should
      influence what the operator sees first.
- [ ] Link every guided step back to the exact typed command path, artifact
      path, and canonical docs authority so the guidance stays auditable.
- [ ] Allow AI to summarize or adapt playbooks for the current situation, but
      keep the canonical step graph repo-owned and inspectable.
- [ ] Expand tooltip/help coverage until every toolbar control, layout preset,
      analytics card, theme-editor control group, and action button has
      in-app help text instead of docs-only meaning.
- [ ] Add a first-pass in-app "System Primer" bundle that covers Architecture,
      Memory System, Dev Panel, Guardrails, Refactor Automation, AI Workflow,
      Rust Engineering, Testing Strategy, Operational Workflow, and Scaling
      using canonical repo docs as the source, then track section-by-section
      cleanup follow-ups so this hard-systems guidance keeps improving without
      becoming stale.

### Phase 5 - Guardrails And Pipeline Controls

- [ ] Add `write_pipeline_control_artifact()` and
      `read_pipeline_control_state()` to a dedicated PyQt-free state module
      for pause/resume/stop artifact-writing (agents poll these, not direct
      control).
- [ ] Create `guardrails_panel.py` with pipeline status indicator,
      pause/resume toggle, stop button with confirmation, and auto-mode
      selector (Manual / Semi-Auto / Full-Auto).
- [ ] In Semi-Auto/Full-Auto modes, auto-approve matching `policy_hint`
      approvals using existing `record_operator_decision()` path.
- [ ] Integrate into the header area or controls frame.
- [ ] Add typed terminal/session control buttons for `pause`, `resume`,
      `stop`, `rollover`, and future health/status refresh so the thin shell
      can call the same guarded logic the CLI uses instead of leaving that
      power outside the app.

### Phase 5.4 - Command Center And Workflow Modes

- [ ] Add an allowlisted `Command Center` with searchable command palette,
      favorite actions, presets, typed forms, exact command previews, and
      saved rerun history.
- [ ] Support manual execution via buttons/options/forms and AI-staged
      execution through the same shared command catalog and validation layer.
- [ ] Add workflow modes for:
      Develop, Review, Swarm, CI Triage, Release, Process Cleanup, and
      Docs/Governance.
- [ ] Make the mode switcher repo-state-aware so it can highlight the right
      mode, recommended actions, and required checks from branch, changed
      paths, dirty tree, failing workflows, and active-plan scope.
- [ ] Keep command output, exit code, duration, produced artifacts, and next
      recommended follow-up visible after every run instead of hiding that
      state inside transient widgets.
- [ ] Keep execution deny-by-default: new commands must be registered in the
      allowlisted catalog with docs metadata, AI summary hints, and tests
      before the GUI can run them.

### Phase 5.5 - Script Actions And AI-Orchestrated Controls

- [x] Add the first typed Activity-tab quick actions for
      `review-channel --dry-run`, `status --ci`, `triage --ci`, and
      `process-audit --strict`, all routed through the shared command-builder
      and Launcher Output monitor surface.
- [x] Add a selectable Activity-tab report picker so the operator can request
      overview/blocker/lane/approval summaries in plain language instead of
      reading every raw lane surface at once.
- [ ] Add an allowlisted command palette / action bar for the repo-owned
      script surfaces the operator actually uses, starting with actions like
      `review-channel`, `status --ci`, `report`, `triage`, `check`,
      `docs-check`, `hygiene`, `process-audit`, `process-cleanup`,
      `guard-run`, and other explicitly approved `devctl` workflows.
- [ ] Ensure every manual quick action also exists in the shared Command
      Center / command catalog so the UI does not split into one-off buttons
      with separate execution logic.
- [ ] Keep action execution typed and inspectable: every button should resolve
      to an exact command preview, structured status, and repo-visible log
      output rather than opaque hidden subprocess behavior.
- [ ] Add AI-assisted action selection/drafting so the operator can ask for
      intent-level help like "run the right verification pack", "show me the
      blocking workflow", or "prepare the safe cleanup path", while the model
      still resolves back to an allowlisted command or staged action.
- [ ] Add AI-assisted preflight for complex actions: summarize why a script is
      being suggested, what it will do, and what approvals/preconditions are
      still missing before the button is enabled.
- [ ] Allow multi-step typed flows where appropriate, for example
      preflight -> execute -> health-check -> summarize, as long as each step
      stays within the repo-owned command catalog and logs its result.
- [ ] Keep a deny-by-default policy for anything not in the allowlist; the GUI
      must not become a general shell just because AI is present.

### Phase 5.6 - Adaptive Swarm Planning Integration

- [ ] Add a swarm-planner panel that wraps the existing `devctl autonomy-swarm`
      / `swarm_run` planning path instead of inventing a separate GUI-only
      sizing model.
- [ ] Show the exact inputs used for the recommendation:
      scope/prompt summary, changed files, added/deleted lines,
      `prompt_tokens`, `token_budget`, per-agent token-cost assumptions, and
      any feedback-sizing signals from prior runs.
- [ ] Show the live swarm-efficiency governor inputs and score:
      `lane_utilization_pct`, `acceptance_yield_pct`,
      `duplicate_work_pct`, `stall_pct`, `review_backlog_pct`,
      `token_pressure_pct`, plus the resulting `efficiency_score`.
- [ ] Let AI help summarize the work and propose planner inputs, but require
      the final recommendation to come from the repo-owned planner output.
- [ ] Show the planner result as an operator-readable explanation:
      recommended agents, reviewer reservation, expected parallelism, token-cap
      effect, and why the system did not choose a larger/smaller swarm.
- [ ] Surface the control action the governor wants to take:
      hold, downshift, upshift, freeze to recovery pair, or repurpose lanes to
      review/audit/backlog work, with a short rationale instead of opaque
      autoscaling behavior.
- [ ] Add a one-click handoff from the planner to the right execution path:
      `review-channel` for the current 8+8 review swarm when that is the chosen
      lane, or `swarm_run` / `autonomy-swarm` when the broader autonomy path is
      the right fit.
- [ ] Add a graph-backed scope pane for planner/handoff views: render the same
      generated context packet / concept-view refs that AI uses so operators
      can inspect blast radius, related plans/docs, and likely verification
      scope without cold-reading the full doc stack.
- [ ] Add an architecture-health panel sourced from the future
      `architecture-review` payload: top risks, current health scores,
      blast-radius links, and audience-mode projections should come from the
      same canonical report the CLI/AI surfaces use instead of a
      console-specific analyzer.
- [ ] Persist planner outputs into repo-visible logs/artifacts so later AI runs
      and operators can see why a swarm size was selected.

### Phase 6 - System Health Panel

- [ ] Create `health_collector.py` (PyQt-free) collecting CPU, memory, bridge
      poll latency, error counts using `psutil` (optional dep with graceful
      fallback).
- [ ] Create `health_panel.py` with `QProgressBar` widgets for CPU/memory,
      color-coded latency display, and error count badge.
- [ ] Wire into the 2-second polling cycle.

### Phase 6.4 - Workspace State And Artifact Browser

- [x] Add a dense repo-pulse / working-tree summary on Home + Analytics using
      repo-owned git, mutation, and CI collectors so placeholder cards do not
      stay empty when the repo already has useful signal.
- [ ] Add a workspace-state panel showing branch, HEAD SHA, dirty tree,
      changed files, untracked files, and active-plan scope.
- [ ] Show the required bundle / risk-add-on recommendation for the current
      changed-path set so the operator can see what validation lane applies
      before running commands.
- [ ] Add an artifact browser for repo-visible logs, reports, review-channel
      outputs, operator decisions, and generated markdown so operators can
      inspect the current state without leaving the controller app.
- [ ] Add quick jumps from workspace/artifact surfaces into the relevant
      playbook, command, AI-help prompt, or review lane.

### Phase 6.45 - Charts, Mutation, And Hotspot Analytics

- [ ] Replace the remaining empty/filler cards with repo-owned analytics cards,
      sparklines, hotspot bars, and summary charts sourced from
      `devctl status`, `devctl report --rust-audits`, `devctl triage`,
      `mutation-score`, `process-audit`, and related emitted bundles.
- [ ] Add chart-backed views for CI state, Rust guard violations, code
      hotspots, mutation survivors, process hygiene, and swarm health, with
      every card explaining what the metric means and why it matters.
- [ ] Add a mutation-testing workspace that shows human-readable findings, raw
      data, and AI-readable bundle context side by side so operators can see
      the survivor/problem surface before asking AI or scripts to turn it into
      test work.
- [ ] Keep analytics dual-mode: `Simple` explains the signal in plain language,
      and `Technical` exposes raw counts, provenance, source commands, and
      artifact paths for the same underlying metric.

### Phase 6.5 - CI/CD And Report Visibility

- [x] Add read-only desktop parity for the repo-owned `phone-status`
      projection so desktop and iPhone-safe surfaces share one control-state
      contract before any push/notifier adapter lands.
- [ ] Add a CI status strip showing green/red/yellow state for the current
      branch/SHA using existing repo-owned reporting surfaces rather than
      ad-hoc GitHub parsing inside the GUI.
- [ ] Reuse `devctl status --ci`, `devctl report`, `devctl triage`,
      `devctl orchestrate-status`, and related report artifacts as the backing
      data model for the desktop view.
- [ ] Add a recent workflow/runs panel showing the important lanes,
      current conclusion, started/finished times, and the exact workflow or run
      that is currently blocking the operator.
- [ ] Add push-linked run history so the operator can select a recent push or
      SHA and immediately see the workflows triggered by that push, their
      conclusions, and whether follow-up pushes improved or regressed the repo
      state.
- [ ] Add a failure-details/logs panel that shows repo-visible excerpts or
      links/paths/commands for the relevant CI logs and artifacts instead of
      making the operator dig through GitHub manually.
- [ ] Surface release-gate state where relevant (`release_preflight`,
      publication sync, CodeRabbit/Ralph gates) so the operator can tell at a
      glance whether the repo is green enough to integrate.
- [ ] Fail clearly when CI auth or upstream reporting data is unavailable:
      show "auth missing", "offline", or "no report artifact yet" instead of a
      misleading empty green state.
- [ ] Keep CI visibility read-first by default; any retry/re-run controls must
      remain typed and policy-gated through repo-owned commands if they are
      added later.
- [ ] Show branch/SHA provenance on each visible CI run so the operator can
      distinguish "latest push is green" from "some older run was green".

### Phase 7 - Diff Viewer

- [ ] Create `diff_model.py` (PyQt-free) running `git diff` subprocess and
      parsing unified diff into structured `DiffHunk` dataclasses.
- [ ] Create `diff_panel.py` with file list, syntax-highlighted diff view
      (green=added, red=removed), and base-commit selector.
- [ ] Add as a new tab or fourth lower-row panel on its own 10-second timer.

### Phase 7.5 - Embedded Terminals And Shell Surfaces

- [ ] Add bounded embedded terminal panes for repo shells and long-running
      command sessions when they materially improve operator workflow.
- [ ] Keep embedded terminals subordinate to the typed controller path:
      they are observation/manual-assist surfaces, not a waiver of the
      allowlisted command policy for automation actions.
- [ ] Surface terminal provenance clearly: cwd, branch/SHA, command owner, and
      whether the session was launched manually, by a playbook, or from an AI
      staged action.
- [ ] Add read-only split/combined lane terminal monitors sourced from
      `review-channel` session artifacts first, then from any later live Rust
      control service, so operators can watch Codex/Claude/Operator work in a
      dense monitor without a second terminal app.

### Phase 2.9 - UI Redesign: Visual Hierarchy And Modern Surface Treatment

Accelerates Phases 2.7, 2.8, 3, and 4.5 by shipping the core visual overhaul
in one focused pass. The current UI has 14 identified problems: flat visual
hierarchy, monotone palette, boxy borders, tiny status indicators, cluttered
control bar, wasted vertical space from oversized KPI cards, and equal-weight
columns that prevent scan-at-a-glance operation.

Design principles: scanability over decoration, color as signal not decoration,
depth through shadows not borders, asymmetric layout with focal points,
progressive disclosure, and 8px base grid spacing.

#### Step 1 - Quick Wins (immediate visual lift)

- [x] Increase `StatusIndicator` size from 10px to 14px with 7px border-radius.
- [ ] Add subtle glow via `QGraphicsDropShadowEffect` on status indicators.
- [x] Increase window margins from 18px to 32px and section spacing from 14px
      to 20px for breathing room.
- [x] Remove individual `KVRow` borders — use spacing and hover-tint background
      instead of bordered frames.
- [x] Increase body font from 13px to 14px for readability.

#### Step 2 - Color System V2

- [x] Replace hard borders with `rgba(255,255,255,0.05-0.08)` hairline borders
      for glassmorphism-lite card edges on GroupBox, HeaderFrame, ControlFrame,
      AgentSummaryCard, KVContainer, splitter handles, and tabs.
- [x] Deepen background layer via ThemeSeed `base_bg` `#0d1820` → `#081420`
      (derived bg_top/bg_bottom are deeper through `_build_semantic_colors` mix).
- [x] Brighten accent signals in Codex seed: accent `#5cb8ff`, accent_soft
      `#4ade80`, warning `#fbbf24`, danger `#f87171`.
- [ ] Add shadow/glow tokens to the theme color dict for card elevation effects.
- [x] Update `StatusIndicator` colors: active `#4ade80`, warning `#fbbf24`,
      stale `#f87171`, idle `#64748b`.

#### Step 3 - Kill GroupBoxes, Ship LaneCards

- [ ] Remove `QGroupBox` wrappers from all lane panels and lower panels.
- [ ] Create `LaneCard(QFrame)` widget with rounded corners, translucent
      `rgba()` background, hairline white border, and `QGraphicsDropShadowEffect`
      for floating-card depth.
- [ ] Replace `_wrap_widget_box()` with `LaneCard`.
- [x] Remove `_wrap_text_box()` (lower panels now owned by QTabWidget).

#### Step 4 - Header Collapse And Status Pills

- [x] Replace the tall gradient `HeaderFrame` with a compact single-row header
      (title + inline KPI cards + pending badge + DEV LOG badge).
- [x] Remove the subtitle paragraph from the header.
- [x] Move `DEV LOG` badge into the header bar right side.
- [ ] Create `StatusPill(QFrame)` widget: inline `[● Name  status · timestamp]`
      with tooltip for full detail and click-to-scroll-to-lane.

#### Step 5 - Bottom Tabs

- [x] Replace the 3-panel lower `QSplitter` with a `QTabWidget` containing
      tabs for Bridge, Commands, and Diagnostics.
- [x] Style tabs to match the card surface treatment (QSS added).
- [x] Each tab gets full width instead of 33%, making logs readable.
- [ ] Preserve scroll state per-tab across refreshes.

#### Step 6 - Asymmetric Lane Layout With Approval Spine

- [x] Change lane splitter stretch from `1:1:1` to `5:2:5` so Codex and Claude
      get 42% each and the approval/operator spine gets 16% center.
- [ ] Create `ApprovalSpine(QFrame)` widget: vertical stack of per-item
      `ApprovalCard` widgets with inline approve/deny buttons.
- [ ] Move approval list, decision note, and approve/deny buttons out of the
      operator column and into the center spine.
- [x] Show a zero-state "0 Pending" indicator when the queue is empty.

#### Step 7 - Control Bar Grouping

- [x] Split the control bar into three visually separated groups:
      [Theme/Settings] | [Parameters] | [Action Buttons].
- [x] Add thin vertical separator lines between groups.
- [ ] Give action buttons more padding and visual weight than settings controls.

#### Step 8 - Typography Polish

- [x] Section headers: 20px/700 weight (up from 16px).
- [x] Title: 22px/800 weight with -0.3px tracking (down from 30px — compact).
- [x] KV labels: 11px/600 weight with 0.4px tracking and uppercase transform.
- [x] KV values: 14px/400 weight (up from 13px).
- [x] Switch primary font stack to "Inter", "SF Pro Display", system-ui.
- [x] Pending count badge: 28px/800 weight in warning color (was 22px neutral).
- [x] Role badges: semi-transparent white background (was opaque accent).

### Phase 8 - Validation And Integration Decision

- [ ] Prove the desktop wrapper is useful for launch/rollover monitoring and
      operator decision capture on the current codebase.
- [ ] Compare the wrapper against the Rust shared-screen plan and decide
      whether to:
      keep it optional, fold it into Rust, or retire it.
- [ ] If retained, document optional dependency/install behavior and guard it
      behind actionable import/runtime errors instead of hard failures.

## Progress Log

- 2026-03-19: Closed the next MP-359 workflow-authority correction after the
  live desktop audit found that `Run Loop` respected the selected workflow
  preset but `Launch Review` / `Start Swarm` still launched a fixed
  review-channel bootstrap. The Operator Console now freezes the selected
  preset into `review-channel --action launch` through both `--scope` and
  `--promotion-plan`, and the chained Start Swarm preflight/live path carries
  the same typed launch target instead of silently falling back to the default
  review plan. Extracted `ReviewLaunchTarget` / review-command completion
  helpers so the UI mixin stays under code-shape limits, revalidated the
  focused Operator Console launch tests, reran `check --profile ci`, and
  confirmed the current follow-up architecture question explicitly: keep
  subtree-local `AGENTS.md` docs only if they become part of a typed
  instruction-authority registry; otherwise collapse local placement guidance
  back into the package README / map docs to avoid doc-authority sprawl.
- 2026-03-17: Accepted the next MP-359 architecture correction after a shared
  backend/runtime review pass. The current desktop shell still treats the
  markdown bridge and compatibility payload rebuilds as primary data sources
  too often, and it still keeps repo/path/risk/CLI authority locally through
  `VOICETERM_PATH_CONFIG`, local risk bucketing, and hard-coded review-channel
  argv builders. The next bounded slice is now explicit: move the session and
  snapshot builders to `review_state` / typed full projections / registry-
  first reads, keep `bridge.md` as fallback-only when structured artifacts
  are missing, and preserve the remaining path/risk/argv cleanup as follow-up
  debt instead of mixing it into unrelated UI work.
- 2026-03-11: Closed the next MP-359 presentation-state cleanup after the
  guard-driven review pass narrowed the remaining Operator Console advisory
  debt to one file. `app/operator_console/state/presentation/presentation_state.py`
  no longer hides lane serialization, change-mix rendering, or CI KPI text
  behind one-call helpers, the targeted presentation-state tests are green,
  and the file drops out of both `probe_single_use_helpers` and the residual
  low `probe_design_smells` formatter-helper hint set.
- 2026-03-11: Revalidated the MP-359 desktop proof lane after the tooling
  bundle exposed a help-dialog collection failure. The real import cycle was
  package-init eager exports under `app/operator_console/views/layout/__init__.py`,
  not the help-topic rendering path itself, so the layout package now lazy-loads
  `WindowShellMixin`, `HAS_THEME_EDITOR`, and workbench helpers on demand.
  That breaks the loop
  `help_dialog -> layout.__init__ -> ui_window_shell -> help_dialog` without
  changing the public package surface, and
  `python3 -m pytest app/operator_console/tests/ -q --tb=short` is back to
  green (`578 passed`).
- 2026-03-10: Refactored the new watchdog readouts so the desktop shell now
  consumes one shared typed watchdog summary artifact instead of re-parsing
  JSON in multiple places. Snapshot loading is centralized under
  `state/snapshots/watchdog_snapshot.py`, watchdog formatting moved into a
  dedicated `state/watchdog_presenter.py`, and the Activity/Analytics surfaces
  now stay orchestration-only rather than mixing schema parsing, metric
  formatting, and report assembly in one long function.
- 2026-03-09: Added a subtree-local `app/operator_console/AGENTS.md` so future
  agent work in the desktop shell sees package placement rules close to the
  code instead of only the repo-wide policy. Updated the main Operator Console
  README plus the `views/`, `theme/`, `state/`, and `tests/` package-map docs
  to explain the new responsibility-first layout in simpler language, and
  linked those docs from `DEV_INDEX.md`, `dev/README.md`, and the in-app help
  resource list so the cleanup is actually discoverable.

- 2026-03-09: Continued the visible tree cleanup for MP-359 by moving the
  workflow and layout view files out of the flat `views/` directory. Workflow
  controls/launchpad/chrome now live under
  `app/operator_console/views/workflow/`, and layout registry/state/workbench
  plus shell chrome now live under `app/operator_console/views/layout/`.
  Internal imports and tests were updated to use the new package paths
  directly, and the old top-level collaboration shim files were removed so the
  directory shape now reflects the real responsibility split instead of hiding
  it behind duplicate files.
- 2026-03-09: Continued the responsibility-first cleanup into the UI layer.
  The collaboration surface is no longer flat under `views/`: conversation,
  task-board, timeline, and collaboration action-handler files now live under
  `app/operator_console/views/collaboration/`, with thin re-export shims left
  at the old top-level paths so the main window and existing tests can keep
  importing during the migration. A new `views/README.md` now documents the
  current UI split and the rule that feature-specific views should stop living
  forever in one flat directory.
- 2026-03-09: Continued the responsibility-first MP-359 cleanup across the
  theme surface. The flat `app/operator_console/theme/` directory now has
  explicit `config/` and `qss/` subpackages, with compatibility shims left at
  the old top-level module paths so existing imports stay stable during the
  transition. Theme-specific tests also now live under
  `app/operator_console/tests/theme/`, and a new `theme/README.md` documents
  where palette/runtime/editor/import/QSS files are supposed to live.
- 2026-03-09: Started the responsibility-first package cleanup for MP-359 so
  the Operator Console stops treating `state/` and `tests/` as junk drawers.
  Workflow command/preset/surface helpers now live under
  `app/operator_console/workflows/`, conversation/task/timeline/context-pack
  helpers now live under `app/operator_console/collaboration/`, and persisted
  layout helpers now live under `app/operator_console/layout/`, with
  compatibility shims left under `state/` so the existing app/tests keep
  importing cleanly during the transition. The developer docs were also
  simplified with a plain-language root README plus explicit `state/README.md`
  and `tests/README.md` maps so future work follows responsibility-first
  placement instead of continuing to flatten more files into `state/`.
- 2026-03-09: Reached a bounded stopping point on the current MP-359
  Cursor-plus-quality tranche. Cursor lane state now flows through
  snapshot/refresh/layout/activity surfaces (including the Activity summary
  card strip), live quality-backlog summary data now appears in
  snapshot-derived quality reports, and quality reports can now post as
  review-channel `finding` packets instead of generic drafts. The remaining
  architecture/memory/guardrail deep-cleanup pass is now explicitly parked as
  the new Phase-4.7 "System Primer" backlog item for the next slice.
- 2026-03-09: Closed the next MP-359 shape-hardening slice after operator
  feedback that `views/main_window.py` had turned into a god file. The PyQt
  shell is now split into bounded shell/layout/review/activity/operator
  result layers (`ui_window_shell.py`, `ui_layout_state.py`,
  `ui_swarm_status.py`, `ui_review_actions.py`, `ui_activity_actions.py`,
  `ui_operator_actions.py`, `ui_process_results.py`), which cuts
  `main_window.py` from `1274` lines to `615` and `ui_commands.py` from
  `776` to `251` while keeping the visible GUI contract stable. Focused and
  full Operator Console pytest runs remain green after the split, and
  `check_code_shape.py` no longer flags the new launcher/result files or
  `main_window.py`; the remaining shape failures are in other dirty-tree
  Operator Console theme/state modules plus separate `devctl` review-channel
  files that still need their own bounded decompositions.
- 2026-03-09: Closed the next MP-359 workflow-controller hardening slice for
  the PyQt shell. `Run Loop` no longer jumps straight into `devctl swarm_run`;
  it now runs `devctl orchestrate-status` first and only launches the
  continuous loop when the repo sync/audit guard is green. The shared
  Home/Activity launchpad also now owns a first-class last-result surface
  (`Workflow Audit Running`, `Loop Blocked`, `Loop Complete`, and similar)
  instead of leaving loop/audit outcomes buried in raw launcher text, and
  command labeling now distinguishes workflow audit vs plan loop instead of
  collapsing both into generic status/command output. Focused PyQt layout
  regressions cover the new preflight chain plus visible status updates.
- 2026-03-09: Closed the first shared-workflow-layout slice for MP-359 Phase
  4.5. Workbench now renders shared workflow chrome above and below the main
  tabs: a top strip with current slice/goal/writer/branch/swarm health plus
  Codex/Claude `last seen` + `last applied` markers, and a bottom transition
  timeline (`posted -> read -> acked -> implementing -> tests -> reviewed ->
  apply`) with a script-derived `Next action` footer. This path is state-driven
  through a new PyQt-free workflow-state builder so the layout stays tied to
  repo-visible snapshot + workflow scope signals instead of local-only widget
  state.
- 2026-03-09: Closed the first hard Timeline + layout-recovery tranche for
  MP-359. The desktop shell now synthesizes per-agent/system timeline events
  from snapshot state plus latest rollover handoff artifacts
  (`state/timeline_builder.py`), renders those events in a filterable
  `TimelinePanel`, and promotes that panel into the Workbench monitor stack
  while keeping Raw Bridge available as a separate tab. The same slice also
  adds explicit View->Layout controls to reset to defaults, export a
  reproducible layout snapshot, and import that snapshot back into a live
  session, closing the recoverability half of the persisted-layout contract.
- 2026-03-13: Closed the next honesty gap in the PyQt6 read model after the
  failed live review-channel launch. The desktop snapshot path was already
  loading structured `review_state`, but it was silently dropping the contract's
  own warnings/error/attention payload and therefore could miss the real
  "Codex reviewer stale / waiting on peer / poll due" reason even when the JSON
  already knew it. The snapshot builder now carries forward structured review
  warnings plus the new bridge-attention summary/command into the shared warning
  surface, so Home/Activity/Monitor can surface the same repo-owned stale-peer
  truth the launcher and runtime contracts see instead of looking green because
  the file merely parsed.
- 2026-03-13: Followed the same slice through the default session-first desktop
  layout. Non-healthy review attention now also degrades the Codex/operator
  lane health indicators and appears in session stats, so the workbench can
  show "reviewer stale / poll due / waiting on peer" at a glance instead of
  requiring the operator to notice the footer or drill into warnings first.
- 2026-03-09: Closed the first reproducible layout-state slice for MP-359.
  The desktop shell now persists the selected layout mode plus workbench
  preset/tab/splitter state under
  `dev/reports/review_channel/operator_console/layout_state.json`, restores that
  state on startup, and keeps it updated on layout changes, workbench tab
  switches, monitor-tab switches, splitter drags, and clean window close. This
  closes the old "screen got weird but we cannot reproduce it" gap without
  introducing a desktop-only control plane.
- 2026-03-09: Fixed a real operator-facing launch-feedback failure in the
  desktop wrapper after the `Live` button looked inert during review-channel
  launch attempts. The backend was correctly failing closed on a stale bridge
  guard (`Last Codex poll` too old), but the PyQt shell only showed a generic
  exit-code status and had no explicit failed-to-start path. `Live`, `Dry
  Run`, and `Rollover` now use structured JSON review-channel reports, the UI
  promotes the real backend error into visible launcher/status-bar copy, and
  `QProcess` failed-to-start now emits an immediate operator-facing error
  instead of silently leaving the click ambiguous.
- 2026-03-09: Expanded MP-359 after the latest operator/iPhone feedback so the
  remaining backlog is explicit before Claude resumes implementation. The plan
  now tracks chart-backed repo analytics and mutation/hotspot views in place
  of filler cards, 4/6/8+ snap-aware multi-agent workbench layouts, read-only
  split/combined lane terminal monitors, full tooltip/help saturation, richer
  semantic highlight controls, and broader PyQt/QSS theme-pack import mapping.
  It also records the design/code reference inputs (`network-monitor-tui`,
  `gitui-main/app`, FileHasher-style PyQt theme/chart work, and
  `code-link-ide`) as reference-only sources rather than runtime dependencies,
  and it locks any future Electron/Tauri shell behind the same backend
  contract instead of letting desktop UI work fork the control plane.
- 2026-03-09: Closed the next bounded MP-359 helper-layer theme cleanup after
  the shared QSS literal sweep. Theme-editor color swatches now derive their
  contrast text plus border/hover chrome from the live theme's own
  `text`/`bg_top` colors instead of raw black/white helper constants, and the
  agent-detail diff helper no longer drops to raw white when a theme color is
  invalid. That keeps even the local editor/detail helper layer anchored to
  the semantic palette instead of preserving tiny escape hatches outside the
  shared theme model.
- 2026-03-09: Closed the remaining real user-facing literal fallback still
  visible in the post-sweep theme/view path. `agent_detail.py` no longer drops
  to raw `#ffffff` when a theme color is invalid or missing; it now falls back
  to the builtin semantic `text` color from the shared palette, and the
  focused agent-detail tests cover that invalid-color path explicitly. This
  leaves the remaining literal hits in the desktop theme tree limited to seed
  definitions, preview/example payload text, and generic black/white contrast
  helpers rather than live component chrome bypassing the theme registry.
- 2026-03-09: Narrowed the next MP-359 stylesheet sweep onto shared desktop
  chrome instead of broad widget churn. The operator-console theme pipeline
  now materializes semantic `hover_overlay`, `menu_border_subtle`, and
  `scrollbar_track_bg` colors from the active palette, the editor exposes
  those tokens alongside the existing surface/navigation controls, and the QSS
  path now consumes them for menu hover, menu borders, and scrollbar tracks
  instead of carrying shared `RGBA_*` literals. This keeps the remaining
  cleanup focused on true component-specific pockets instead of generic shell
  overlays that already belong in the semantic theme model.
- 2026-03-09: Closed another bounded MP-359 hardcoded-surface cleanup without
  widening the theme sweep. Agent-detail diff highlighting now falls back to
  the shared Codex semantic palette instead of local RGB literals when a
  partial/empty theme is passed, the theme-editor color swatch button now
  derives its border/hover chrome from the current swatch color instead of
  fixed `#555` / `#00FFAA`, and the editor no longer falls back to raw black
  when syncing a missing color control. This keeps the next cleanup passes
  focused on real remaining surfaces instead of carrying obvious local
  literals in the editor shell itself.
- 2026-03-09: Landed a bounded MP-359 technical-density follow-up after
  operator feedback that the PyQt6 shell still felt too banner-heavy. The
  `Read -> Technical` mode now changes the visible workspace framing instead
  of only changing prose: Home swaps to denser `Ops/Repo/Quality/Relay`
  digest titles, shows the full technical overview body in the main card,
  tightens guidance copy around the small toolbar-owned controls, and marks
  digest labels with terminal-style monospace styling; Activity now switches
  to `Report Digest` / `Stage Prompt` / `Launch State` / `Operator Flow`
  framing so the page reads more like a compact command-center surface than a
  guided explainer. The shared `PanelRawText` QSS is also now explicitly
  monospace so bridge/report/log panes feel terminal-native across modes.
- 2026-03-09: Landed a bounded MP-359 overlay-theme write path without
  continuing to inflate `theme_engine.py`. The desktop editor can now export
  canonical VoiceTerm theme-file TOML plus minimal style-pack JSON when the
  current state still maps exactly to a shared builtin `base_theme`; lossy
  desktop-only edits are blocked with explicit UI messaging instead of writing
  fake canonical files. The same slice also split theme state, storage/QSS
  parsing, and overlay parity logic into focused modules so
  `theme_engine.py` returns to a thinner coordinator role.
- 2026-03-09: Landed the first bounded MP-359 overlay-theme parity import
  slice. The PyQt6 theme engine/editor can now read canonical VoiceTerm
  style-pack JSON payloads and theme-file TOML metadata, map the Rust
  `base_theme` onto the matching desktop builtin palette, and show an explicit
  operator-facing summary of provenance plus Rust-only sections that remain
  intentionally unmapped. This keeps the desktop path read-only for now:
  `overrides`, `surfaces`, `components`, and other non-`meta` TOML sections
  are reported as `Not yet mapped` instead of inventing a second persistent
  desktop schema or a fake one-to-one export contract.
- 2026-03-09: Tightened the MP-359 mobile-read boundary again so the desktop
  and phone client now prefer the same emitted bundle path. The PyQt6 console
  read model now checks `dev/reports/mobile/latest/full.json` from
  `devctl mobile-status` first and only falls back to on-the-fly merge logic
  when that bundle is missing, keeping the future iPhone client and the
  desktop shell on one repo-owned projection set instead of parallel merge
  paths.
- 2026-03-09: Continued the next MP-359 theme-editor tranche after the
  saved-theme crash fix instead of stopping at compatibility. The editor
  workbench now splits semantic color editing across surface-scoped
  `Surfaces`, `Navigation`, and `Workflows` pages rather than one flat color
  dump, and the live preview now covers the toolbar/header, nav + monitor
  tabs, approval queue, diagnostics/log pane, diff view, and representative
  empty/error states. The preview diff pane also now refreshes through the
  same live theme colors used by the real diff highlighter.
- 2026-03-09: Tightened the MP-359 mobile-read path after the first
  `devctl mobile-status` backend slice landed. The PyQt6 console now prefers
  the merged mobile relay state directly in its read model instead of showing
  only raw `phone-status`, so the GUI becomes the easier default surface for
  users while still falling back honestly when review bridge state is absent.
- 2026-03-09: Closed the smallest remaining Step-6 queue affordance before the
  larger `ApprovalSpine` rewrite. The approval panel no longer disappears when
  the queue is empty; it now stays present with an explicit `0 Pending`
  zero-state message, keeps the action buttons disabled, and clears the stale
  selection/detail affordances that previously only made sense when items
  existed.
- 2026-03-09: Landed the first post-crash MP-359 theme follow-up after the
  saved-theme hydration fix. The agent-detail diff highlighter now derives
  added/removed line foregrounds and translucent backgrounds from the active
  theme palette instead of fixed RGB values, which removes one of the
  remaining hardcoded desktop surfaces from the shared theme path.
- 2026-03-09: Closed the immediate MP-359 saved-theme startup regression on
  the active PyQt6 tranche. `ThemeState.from_dict()` now hydrates legacy
  partial color maps onto the correct builtin semantic palette before apply,
  so pre-`toolbar_bg` `_last_theme.json` files and older custom preset JSON
  no longer crash startup when the shared stylesheet compositor renders the
  current semantic QSS.
- 2026-03-09: Landed a bounded density/mobile-parity tranche after the latest
  operator screenshots. The `Home` launchpad now replaces stale filler copy
  with repo-derived Working Tree, Quality/CI, and Phone Relay summaries; the
  Analytics layout now renders separate repo-pulse, quality, working-tree, and
  phone-status sections instead of a single mostly-placeholder text block; the
  sidebar nav and Home action buttons are denser; and the in-app guide now
  explains the mobile boundary explicitly: `devctl phone-status` is the
  current first-party iPhone-safe state contract while
  `integrations/code-link-ide` remains a reference repo for future transport /
  pairing / notification adapters rather than a runtime dependency of the
  console.
- 2026-03-09: Codex re-review narrowed the current MP-359 closure. The
  active-theme authority split is genuinely closed now, but the desktop shell
  still needs stricter honesty and proof before this tranche can be called
  green: live-launch support remains bounded, some analytics/CI wording is
  still easier to over-read than the underlying repo-owned data warrants, the
  proof path still leans too heavily on dry-runs/mocked completion instead of
  the real startup/mutating paths, launcher-script execution coverage remains
  thin, and checklist/progress state must stay synchronized as follow-ups land.
- 2026-03-09: Closed a bounded launcher-portability honesty slice under
  MP-359. Operator-facing help, startup failure guidance, and the README now
  agree on the canonical launch paths (`./scripts/operator_console.sh` first,
  `python3 -m app.operator_console.run` as the direct fallback) instead of
  mixing in the less-portable `python app/operator_console/run.py` example,
  and focused coverage now locks those launch strings into the themed help and
  missing-PyQt startup path. This narrows the launcher-script proof gap but
  does not yet replace the broader real-startup / mutating-action evidence
  still called out in Phase 2.8.
- 2026-03-09: Clarified the MP-359 dependency boundary after the memory-plan
  audit. The Operator Console may mirror future memory/review/controller
  artifacts, but its prototype operator-decision artifacts remain wrapper-only
  state and do not satisfy Memory Studio `MP-238` / `MP-243` closure or create
  a second memory authority.
- 2026-03-09: Revalidated the MP-359 operator-shell proof path after the
  Rust memory/operator cockpit closure so the desktop shell and Rust overlay
  stay aligned. The full `app/operator_console/tests` suite is now green at
  `228` tests with the current Home/Workbench/Start-Swarm/help/theme surface,
  and the local governance path (`check_active_plan_sync`,
  `check_multi_agent_sync`, `docs-check --strict-tooling`,
  `process-cleanup --verify --format md`) is green alongside it.
- 2026-03-09: Fixed the live-launch dead-end that made the desktop app feel
  broken when `bridge.md` aged past the five-minute reviewer heartbeat
  contract. The Operator Console now routes `Dry Run`, `Launch Live`,
  `Start Swarm`, and `Rollover` through the typed
  `--refresh-bridge-heartbeat-if-stale` backend path, so stale/missing
  reviewer heartbeat metadata is auto-repaired before the launch flow
  continues. The UI still fails closed and surfaces the backend reason when
  the bridge has real blockers beyond heartbeat metadata.
- 2026-03-09: Closed the next MP-359 honesty-copy follow-up. The analytics
  surface now presents itself as repo-visible bridge/lane/approval state
  instead of live CI/code-quality telemetry, KPI cards mark CI/test data as
  `not wired`, and the operator README now states plainly that live
  launch/rollover remain Terminal.app-backed on macOS while other platforms
  should stay on `Dry Run` plus repo-visible artifacts.
- 2026-03-09: Landed a bounded MP-359 approval-routing slice without
  inventing unsupported `devctl review-channel ack|apply|dismiss` semantics.
  The `Approve` / `Deny` buttons now route through a typed repo-owned
  `python -m app.operator_console.state.operator_decisions` command path,
  return a structured JSON report back into the shared launcher/output flow,
  and keep the fallback explicit in the UI: the wrapper is still recording
  repo-visible operator decision artifacts because the final shared
  `review-channel` packet-action surface is not exposed yet.
- 2026-03-09: Landed the next MP-359 operator-shell tranche. `Start Swarm`
  now runs a JSON preflight before chaining into live launch, keeps the Home
  and Activity surfaces in an explicit busy/stateful flow
  (`Preflight`, `Launching`, `Running`, `Blocked`, `Failed`), and shows the
  exact last/next command preview so launch trust does not depend on hidden
  command output. The same slice introduced a real `Workbench` layout mode
  with nested resizable splitters and snap presets (`Balanced`, `Lane Focus`,
  `Launch Center`, `Activity Focus`) so the app is no longer trapped in one
  fixed dashboard shape while operators keep lanes, reports, and monitor
  output visible together.
- 2026-03-09: Added a real `Home` launchpad and a shared simple/technical read
  mode. The app now opens into a guided start screen with direct jumps into
  Dashboard, Monitor, Reports, Theme Editor, and Help; the same mode switch
  now drives Activity report wording, the staged AI-summary source report, and
  footer text so less-experienced operators can stay on a simpler read path
  while technical users can flip back to the denser status surface.
- 2026-03-09: Closed the remaining active-theme identity/apply split for the
  current toolbar/editor boundary. `ThemeState` now carries optional builtin
  `theme_id` identity, `ThemeEngine` exposes explicit builtin/custom/draft
  selection state, the main window syncs the toolbar combo from engine-owned
  state instead of holding a second stylesheet id, agent detail dialogs now
  read live engine colors, and draft edits surface an explicit `Draft:
  Custom` toolbar entry instead of silently pretending a builtin preset is
  still active. The same slice also repaired an accidental
  `views/widgets.py` PyQt fallback indentation break that had made the current
  dirty-tree Operator Console import path invalid.
- 2026-03-09: Re-ran the bounded MP-359 proof path after the theme-authority
  cleanup. Focused theme/layout tests are green (`86` tests), the full
  `app/operator_console/tests` suite is green (`186 passed, 1` pytest cache
  warning caused by sandboxed cache writes), `docs-check --strict-tooling`,
  `hygiene --strict-warnings`, `check_bundle_workflow_parity.py`,
  `check_active_plan_sync.py`, `check_multi_agent_sync.py`,
  `review-channel --action launch --dry-run --format json`, and
  `test_bundle_registry` all pass, and host-side
  `process-cleanup --verify --format md` returns a clean zero-process report.
  `check_review_channel_bridge.py` remains expected-red only because the live
  bridge files are still untracked in this dirty tree, not because of a new
  regression from the theme slice.
- 2026-03-09: Synced MP-359 checklist state to the current desktop tree. The
  Phase 2.6 package reorg is now described as complete, Phase 2.8 now marks
  the shipped theme registry / selector UI / CLI support as landed, and the
  remaining theme follow-up is now explicit as the active-theme
  identity/apply-boundary cleanup between the toolbar selector and the theme
  editor/engine draft state.
- 2026-03-09: Closed the highest-signal screenshot UX gaps in the current
  Operator Console shell. The wrapped bridge pane now hides the misleading
  lower-left horizontal-scrollbar handle on the common human-reading path,
  the agent detail dialog only applies red/green diff colors to actual
  unified diffs instead of ordinary markdown bullets, toolbar and sidebar
  surfaces gained broader tooltips plus visible provider badges, the app now
  exposes top-level `Help` and `Developer` menus with in-app workflow/theme
  guidance, and the theme editor import/export page now explains current
  import scope plus diff/highlight semantics inline.
- 2026-03-09: Expanded MP-359 from a thin shared-screen wrapper into a more
  explicit repo-aware dev-environment controller plan. The plan now tracks a
  first-class Command Center, built-in workflow guidance/playbooks, repo-state
  workflow modes, and an integrated AI `Ask | Stage | Run` contract so the
  desktop app can answer questions, stage actions, and run the same typed
  repo-owned commands through both manual and AI-assisted paths.

- 2026-03-09: Planning follow-up after operator feedback: MP-359 now tracks a
  fuller next theme tranche explicitly instead of leaving it implied. The
  remaining theme-editor scope is now recorded as broader page-scoped controls,
  wider live-preview parity, and removal of the remaining hardcoded styling so
  the desktop console can theme nearly every operator-facing surface rather
  than stopping at colors plus a small global token set.
- 2026-03-09: Expanded the desktop theme system from color-only tweaks into a
  fuller left-workbench editor tranche. The PyQt editor now opens as a
  non-modal left-anchored workbench instead of a centered blocking modal,
  exposes dedicated `Colors`, `Typography`, `Metrics`, and `Import / Export`
  pages, and renders a real preview gallery built from Operator Console
  surfaces instead of a plain text box. The theme engine now persists
  non-color tokens alongside semantic colors, the shared stylesheet builder
  consumes both layers, and typography/radius/padding/scrollbar sizing plus
  diff-view highlighting now route through theme-controlled values instead of
  fixed literals.
- 2026-03-09: Reworked the Activity tab into a readable report surface after
  the operator called out that the raw dashboard still held too much text at
  once. The tab now starts from a selected report topic (`Overview`,
  `Blockers`, `Codex`, `Claude`, `Operator`, `Approvals`), renders a
  human-readable script-derived summary with a recommended next step, and can
  turn that selected report into a staged Codex or Claude summary draft
  without auto-running either provider. This keeps the UX summary-first while
  preserving the bounded no-hidden-execution AI contract.
- 2026-03-09: Added the next AI-assist follow-up explicitly to MP-359 after
  operator feedback: the staged draft flow is no longer the only tracked end
  state. The active plan now includes an opt-in live Codex/Claude `AI Summary`
  path for the selected report, with explicit provenance, timeout bounds, and
  repo-visible diagnostics so any real provider-backed answer stays auditable.
- 2026-03-09: Closed the last real theme-compositor split in the desktop
  wrapper. `theme/stylesheet.py` now exposes a shared builder that accepts
  explicit semantic color maps, and `ThemeEngine.generate_stylesheet()` routes
  through that same compositor instead of a stale editor-only QSS fork. This
  keeps the live app and the theme editor on one stylesheet path, adds proof
  that the engine output matches the live theme output, and avoids reopening
  the earlier crash/regression path when the editor preview applies changes.
- 2026-03-09: Promoted the Operator Console suite into the canonical local
  tooling proof path and removed the last launcher interpreter mismatch. The
  `bundle.tooling` registry now includes `python3 -m pytest app/operator_console/tests/ -q --tb=short`,
  the rendered `AGENTS.md` bundle block is back in sync, and
  `state/command_builder.py` now uses `sys.executable` so button launches reuse
  the app's active interpreter instead of assuming a matching shell `python3`.
- 2026-03-09: Turned the read-only Activity tab into a real operator workspace.
  The tab now shows card-based Codex/Claude/Operator summaries, keeps the
  bridge-derived activity log visible, adds typed quick actions for dry-run
  launch, CI status, triage, and strict process audit, and stages bounded
  `AI Audit Draft` / `AI Help Draft` prompts with explicit provenance copied
  from the current snapshot. The command path still routes through the shared
  `command_builder.py` boundary and the AI path remains advisory-only.
- 2026-03-09: Tightened the first real ownership seam in the desktop wrapper.
  `ui_refresh.py` no longer hand-builds activity text, analytics text, KPI
  values, or snapshot digests inline; those pure snapshot-derived projections
  now live in `app/operator_console/state/presentation_state.py` alongside the
  shared approval-risk classifier. This keeps Qt refresh code focused on
  binding widgets, moves reusable policy/projection logic out of the view
  layer, and makes snapshot-change detection react to structured lane-state
  changes instead of only pre-rendered panel strings.
- 2026-03-09: Fixed a second operator-facing usability gap in the toolbar
  controls. `Launch`/`Dry Run`/`Rollover` were appending output into the
  hidden `Launcher Output` monitor pane in the default tabbed layout, so the
  clicks could look dead even when the command path was working. The wrapper
  now auto-reveals the output pane for command launches, disables the action
  buttons while a process is active, and shows a running label/state directly
  in the toolbar so command execution is visible without manual tab hunting.
- 2026-03-09: Diagnosed and fixed a real macOS Operator Console crash. After
  `analytics -> grid` switches, the 2-second refresh timer could still walk
  `_kpi_cards` references that pointed at Qt widgets already queued for
  `deleteLater()`, which raised `RuntimeError` inside a Qt slot and aborted
  the process. The wrapper now clears layout-owned widget handles during
  rebuilds, treats stale KPI widgets defensively, and logs `refresh_failed`
  instead of crashing the app on an uncaught refresh exception.
- 2026-03-09: Tightened the data-first hierarchy on the Home and Activity
  workspaces after screenshot review showed the action chrome outweighing the
  actual operator data. Navigation and quick-action controls now render as
  compact pill grids instead of full-width button stacks, sidebar mode
  reserves more width for data surfaces, and report/detail typography now
  uses larger body sizing so snapshot text reads as the primary content.
- 2026-03-09: Reworked the page architecture again after additional operator
  screenshots showed the console still felt like a prototype dashboard. The
  updated direction is explicitly terminal-first and toolbar-owned: Home and
  Activity no longer add redundant in-page action walls, Analytics now reads
  as a dense repo-intelligence page instead of embedding unrelated workspaces,
  Grid now prioritizes bridge/launcher/diagnostic surfaces over giant empty
  lane panes, and Workbench presets now bias the lower log row so splitters
  start in a sane, monitor-heavy state.
- 2026-03-09: Fixed two operator-facing regressions in the desktop launcher
  path. `app.operator_console.run` now accepts `--layout <mode>` so
  `./scripts/operator_console.sh --layout analytics|grid|workbench` works as
  advertised, and the `Read -> Technical` toggle no longer crashes after the
  home-page redesign because audience-mode refresh now reuses the cached
  analytics view before calling `_update_home_page(...)`.
- 2026-03-08: Tightened the desktop launch/install path and theme ownership.
  The Operator Console stylesheet is now split into navigation, panel, and
  summary fragments instead of mixing sidebar + KPI concerns in one layout
  file; status-dot styling moved out of widget code into QSS-backed semantic
  tokens; and source checkouts now have a canonical
  `./scripts/operator_console.sh` launcher that auto-installs `PyQt6` on
  demand before opening the app. User docs now point at the script instead of
  the raw Python entrypoint.
- 2026-03-08: Radical layout restructure — eliminated the fat header, KPI cards,
  control bar, and GroupBoxes. The UI now uses a single 40px toolbar (title +
  status dots + settings), puts the 3 lane panels as the centerpiece taking 75%+
  of screen height, moves action buttons into the approval spine, and uses tabbed
  bottom panel at 20% height. AgentSummaryCard removed from ui.py, replaced with
  3 StatusIndicator dots in the toolbar. All buttons made compact with smaller
  padding. Window margins shrunk to 12px to maximize content. 42/42 tests pass.
- 2026-03-08: Added Phase 2.9 (UI Redesign) after operator screenshot audit
  identified 14 visual hierarchy failures: monotone palette, boxy borders, tiny
  status dots, flat type scale, equal-weight columns, wasted vertical space from
  oversized KPI cards, and cluttered control bar. The phase ships 8 steps in
  priority order: quick wins, color system v2, GroupBox removal, header collapse,
  bottom tabs, asymmetric layout with approval spine, control bar grouping, and
  typography polish. Accelerates existing Phases 2.7, 2.8, 3, and 4.5.
- 2026-03-08: Shipped Phase 2.9 first pass — 17 of 28 checklist items complete.
  Changes: glassmorphism-lite borders replacing hard teal borders across all
  surfaces, KV rows de-bordered with hover tints, status dots 10→14px, body
  font 13→14px, section headers 16→20px, title compacted 30→22px, header
  collapsed to single-row layout with inline KPI cards, lower 3-panel splitter
  replaced with tabbed QTabWidget (full-width per tab), lane splitter made
  asymmetric 5:2:5 (Codex|Operator|Claude), control bar grouped with vertical
  separators, Inter/SF Pro Display font stack, and pending count badge styled in
  warning color at 28px. 42/42 tests pass.
- 2026-03-08: Reworked the live Operator Console hierarchy after screenshot
  review exposed unreadable structured panels and repetitive lane naming. The
  desktop app now uses dark inset surfaces for structured KV rows instead of
  fallback light widgets, separates provider/role/lane identity so cards read
  as `Codex` + `Codex Bridge Monitor` instead of duplicated titles, adds a desktop
  theme registry (`codex`, `coral`, `minimal`) with CLI/UI selection, and
  makes splitter handles visually obvious so the current layout is adjustable
  while the future snap-aware layout workbench is still pending.
- 2026-03-08: Tightened the theme-system contract after parity review. The
  desktop registry now needs to expose the full overlay theme id set
  (`coral`, `claude`, `codex`, `chatgpt`, `catppuccin`, `dracula`, `nord`,
  `tokyonight`, `gruvbox`, `ansi`, `none`) plus one desktop-only `minimal`
  preset, and the palette generation should flow through shared semantic
  helpers instead of hand-tuned per-theme CSS drift.
- 2026-03-08: Clarified the end-state for theme parity: yes, the PyQt console
  should eventually read and write the Rust style-pack/theme format, but in
  stages. MP-359 now makes import/read parity the first requirement and export
  parity a second step after the mapping is stable, so the desktop app does
  not create a competing persistent theme schema.
- 2026-03-08: Opened MP-359 to reactivate a bounded desktop wrapper path after
  the operator explicitly requested a PyQt6 side-by-side Codex/Claude surface
  with yes/no operator controls. The scope is intentionally narrower than the
  retired `app/pyside6` direction: this is an Operator Console over the
  existing Rust runtime and `devctl` launcher, not a replacement for them.
- 2026-03-08: Landed the first scaffold under `app/operator_console/`:
  pure bridge/approval helpers with unit coverage, a PyQt6 main window that
  reads `bridge.md`, wraps existing `review-channel` launch/rollover
  commands, shows Codex/Claude/Review-Operator panes side by side, and records
  repo-visible operator `approve` / `deny` artifacts under
  `dev/reports/review_channel/operator_decisions/`. This first slice remains
  read-first and wrapper-first; it does not embed a real terminal emulator
  or replace the Rust PTY engine.
- 2026-03-08: Extended the wrapper with a proper operator-facing console theme
  plus repo-visible diagnostics. The app now supports `--dev-log`, persists
  `latest.operator_console.log`, `latest.events.ndjson`, and
  `latest.command_output.log` under
  `dev/reports/review_channel/operator_console/`, mirrors high-level events
  into a dedicated diagnostics pane, and documents the desktop triage path in
  the collaboration guide and app README.
- 2026-03-08: Tightened pane scrolling so the Operator Console stops pushing
  the operator around during the 2-second refresh loop. Snapshot panes now
  preserve manual scroll position when content changes, command/dev-log panes
  only auto-follow while already tailed to the bottom, and the stylesheet now
  gives all panes clearer custom scrollbars.
- 2026-03-08: Promoted Operator Console package cleanup into MP-359 after a
  maintainability audit showed the current prototype already has three large
  Python hotspots (`ui.py` at 667 lines, `bridge_model.py` at 508 lines,
  `theme.py` at 380 lines). The plan now explicitly requires modularization,
  clearer directory ownership, Python best-practice naming/docstrings, and a
  documented live-test flow before the wrapper grows further.
- 2026-03-08: Landed Phase 1.5 (Information Hierarchy): replaced text-dump
  panels with structured `KeyValuePanel` widgets, added `AgentSummaryCard`
  KPI strip, and `StatusIndicator` dots. New `widgets.py` (262 lines) + 19
  widget tests. Expanded plan with Phases 3-8 roadmap (Approval Queue Center
  Stage, Agent Timeline, Guardrails, System Health, Diff Viewer, Validation)
  based on senior engineer UX review and modern dashboard pattern research.
- 2026-03-08: Folded in the latest operator UX direction for the wrapper:
  the preferred layout now uses a shared goal/current-slice strip, Claude lane,
  narrow relay/approval spine, Codex lane, and bottom workflow timeline so the
  whole process reads as one collaboration surface. Added a bounded AI-assist
  phase for explanation/drafting/fallback reasoning, with an explicit rule that
  scripts stay canonical for real execution and AI output must remain staged,
  provenance-labeled, and repo-visible.
- 2026-03-08: Added the next operator-control tranche after reviewing the
  current UI against the real CLI surface: the app now explicitly tracks a
  one-click `Start Swarm` flow plus direct typed yes/no and terminal-control
  buttons as planned work. The intent is not to bypass `devctl`, but to let
  the GUI call the same audited launch/ack/apply/pause/resume/stop logic once
  those command surfaces exist.
- 2026-03-08: Added explicit CI/CD visibility requirements after reviewing the
  current wrapper scope against operator expectations. MP-359 now tracks a
  first-class CI status/runs/logs panel that must reuse `devctl`
  status/report/triage/orchestration surfaces, show green/red gate state, and
  make missing auth/data explicit instead of silently showing nothing.
- 2026-03-08: Expanded the control-panel direction again after operator
  feedback: MP-359 now explicitly tracks push-linked workflow history plus an
  allowlisted script/action palette with AI-assisted action selection and
  staged multi-step flows. The intent is to let the app drive real repo-owned
  processes and scripts from buttons, while keeping every action typed,
  previewable, and auditable instead of turning the GUI into a freeform shell.
- 2026-03-08: Wired the adaptive swarm-sizing question into MP-359 explicitly.
  The desktop app should not guess how many agents to run; it should surface
  the existing `autonomy-swarm` / `swarm_run` planner logic, show token/budget
  inputs and feedback signals, and hand the operator from recommendation to
  execution without creating a second planner in the GUI.
- 2026-03-08: Extended MP-359 from token-aware sizing into a visible swarm
  efficiency governor surface. The console now explicitly needs to show the
  live efficiency metrics, the resulting score, and whether the system wants
  to hold, shrink, freeze, or repurpose lanes so the operator can see why the
  swarm is changing instead of guessing.
- 2026-03-08: Added the next UI-architecture asks after reviewing the live
  screenshots: MP-359 now explicitly tracks a layout workbench for snap-aware
  resizing/repositioning plus a theme registry that starts with desktop
  presets but is intended to converge on the Rust overlay theme/style-pack
  model instead of drifting into a separate styling system.
- 2026-03-09: Split the overloaded `app/operator_console/state/bridge_model.py`
  surface into focused modules (`models`, `bridge_sections`, `review_state`,
  `lane_builder`, `snapshot_builder`, `operator_decisions`) and cut every
  runtime/test import site over to those modules directly. `bridge_model.py`
  now exists only as a compatibility facade instead of carrying the real
  ownership boundary.
- 2026-03-09: Removed the temporary `state/bridge_model.py` facade after a
  repo-wide import audit confirmed nothing still depended on the old path.
  The console package now imports the focused state modules directly, and the
  renamed `tests/state/test_state_modules.py` covers the split surface.
- 2026-03-09: Tightened the desktop shell again after fresh operator
  screenshots showed the console still reading like a custom dashboard kit
  instead of a professional terminal workspace. The home surface now uses one
  primary overview pane plus a narrow signal rail, the toolbar actions were
  flattened to plain-text controls, analytics/grid/workbench were biased
  further toward log and repo-data visibility, and the QSS chrome was restyled
  toward a VS Code / Cursor-like editor shell with flatter tabs, subtler
  borders, and less ornamental button gloss.
- 2026-03-09: Reworked the default Workbench again after the first
  terminal-first pass still exposed too many panes at once. The visible preset
  bar is gone, the left side is now a dock with one lane visible at a time,
  Monitor is the dominant center/editor surface with `Launcher Output` opened
  first, and approvals/reports/snapshot content moved behind lower tabs so the
  shell reads like an IDE instead of a tiled dashboard.
- 2026-03-09: Moved more of the console chrome into the native macOS menu-bar
  model after another operator review. `Run`, `View`, `Theme`, and
  `Settings` actions now live in the real app menu bar, while the in-window
  toolbar was reduced to title, lane status, and the core run controls so the
  main surface can stay focused on terminals, analytics, and snapshot data.
- 2026-03-09: Applied the next operator-feedback correction after the
  editor-style rebuild still felt too tab-heavy and text-heavy in practice.
  The console now defaults to the snap-aware Workbench again, but the shell is
  back to card-first composition: all three lane cards stay visible in one
  dock, launcher output / bridge / diagnostics render side by side instead of
  hiding behind tabs, compact preset pills return for fast recovery, and the
  Home/Activity copy path now truncates always-visible helper prose so the
  terminal surfaces stay dominant.
- 2026-03-09: Restored explicit Codex/Claude session surfaces after another
  operator review pointed out that the desktop no longer showed what each side
  was doing. The snapshot model now reads the review-channel `full.json`
  projection, builds `Codex Session` and `Claude Session` panes from the
  agent registry plus bridge state, and makes that pair the front face of the
  default Workbench (`Codex Session | Operator Spine | Claude Session`) with
  raw bridge / launcher / diagnostics moved into a dense lower utility row.
  This is still honest about authority: the new panes are registry/bridge
  session digests, not embedded PTY emulators.
- 2026-03-09: Applied the next layout correction after the restored
  session-first Workbench still left the lower deck reading like a pile of
  unrelated cards. The top streaming row stays intact, but the lower deck is
  now grouped into task tabs: `Terminal` for launcher/bridge/diagnostics plus
  live snapshot/quality, `Stats` for lane cards + working-tree/phone context,
  `Approvals` for the decision queue, and `Reports` for digest/draft work.
  Home/toolbar routing now targets those same functional tabs so the shell
  stays organized around what the operator is trying to do instead of showing
  every card at once.
- 2026-03-09: Folded the session strip into that same job-based model after
  the intermediate split still felt like two layouts welded together. Workbench
  is now a full-page tab set: `Sessions`, `Terminal`, `Stats`, `Approvals`,
  and `Reports`. The `Sessions` tab keeps the Codex/Operator/Claude live row
  visible as one focused view, `Terminal` owns the stream/log surfaces, and
  the task tabs now expand across the top of the workbench instead of living
  halfway down the page with clipped labels.
- 2026-03-09: Rebalanced the Theme Editor after operator feedback pointed out
  that the always-on preview gallery was wasting the full right rail while the
  live app window already showed the theme in context. The right rail is now a
  `Theme Upgrades` workspace with `Quick Tune`, `Coverage`, and `Preview`
  tabs: quick high-signal controls for contrast/emphasis/density, explicit
  honesty that motion/animation tokens are not wired yet, and the synthetic
  gallery demoted to an optional preview tab. In the same pass the operator
  toolbar action buttons were restyled toward a flatter instrument-panel look
  so they read more like analytical dashboard controls and less like generic
  app chrome.
- 2026-03-09: Landed the next MP-359 Theme Editor expansion after operator
  feedback asked for a real full-surface authoring tool instead of a mostly
  color-only dialog. Theme state now persists `components` and `motion`
  sections alongside colors/tokens, the shared stylesheet builder consumes
  component families for corners/borders/surfaces/buttons/toolbar actions/
  inputs/tabs, and the editor exposes new `Components` and `Motion` pages plus
  quick-tune controls for style modes and motion timing. The preview also grew
  a real component/motion playground with front/back card swaps and pulse
  feedback, so button/tab/border family changes are live and motion settings
  have an actual preview contract instead of fake future-facing copy.
- 2026-03-09: Closed the next honesty gap after operator feedback asked where
  the real Codex/Claude terminals went. `devctl review-channel --action
  launch|rollover` now emits per-session metadata plus live-flushed transcript
  logs under `dev/reports/review_channel/latest/sessions/`, and the desktop
  `Codex Session` / `Claude Session` panes now tail those logs on the existing
  two-second refresh loop whenever real output exists, falling back to the
  prior full-projection bridge/registry digest only when no live session trace
  is available. This keeps Terminal.app as the actual PTY owner while finally
  making the desktop session panes behave like near-live terminal viewers
  instead of more report text.
- 2026-03-09: Closed the first live-tail readability regression after operator
  testing. The desktop no longer treats `script(1)` typescripts as plain line
  logs; `session_trace_reader.py` now replays a minimal ANSI terminal screen
  from the captured stream and only falls back to line-based stripping for
  simple logs, so the `Codex Session` / `Claude Session` panes render stable
  visible screen content plus deeper readable history instead of spinner glyph
  storms and partial cursor-repaint fragments.
- 2026-03-09: Landed the next MP-359 session-surface follow-up after live
  operator testing showed that the desktop was still stuffing terminal text,
  session metadata, and agent registry rows into one unreadable box. The
  session reader now keeps separate readable history and current-screen
  snapshots, ignores private CSI parse drift plus `thinking with high effort`
  spinner junk, and the desktop now renders each lane as a split surface:
  large terminal-history pane on top, smaller stats/screen digest plus
  registry pane below. Workbench, Monitor, and Sidebar all reuse that same
  split contract, so the lower blank space now carries freshness, token/context
  hints, worker budget, and full agent-registry detail instead of dead chrome.
- 2026-03-09: Closed the next live-readability/layout follow-up after fresh
  operator screenshots. The session surface now prefers the reconstructed
  visible terminal screen over the noisier raw history stream whenever a live
  `script(1)` trace is available, trims truncated tail reads to the next line
  boundary so partial ANSI/control fragments do not leak into the UI, and
  replaces the split `Stats` / `Registry` lower deck with one double-click
  flippable card per provider. That keeps the terminal pane readable, removes
  the lower-right dead-space feeling, and lets operators flip between
  freshness/signal detail and full registry state without losing lane context.
- 2026-03-11: Bundle-tooling unblock follow-up landed for the desktop shell.
  `views/help_dialog.py` now defers the layout-registry import until the
  `Controls` topic is rendered, which breaks the package-init cycle
  `help_dialog -> layout.__init__ -> ui_window_shell -> help_dialog` and
  restores `app/operator_console/tests/views/test_help_dialog.py` collection.
  The same validation pass exposed a real phone snapshot regression too:
  `dev/scripts/devctl/phone_status_views.py` was still calling removed
  `_controller/_loop/_source_run/_terminal/_ralph` helpers, so the Operator
  Console fell back to unavailable phone state. Routing those call sites back
  through the existing `_section()` helper restored compact/mobile snapshot
  projection, `test_phone_status_snapshot.py` is green again, and the full
  operator-console suite is back to green in the canonical tooling bundle path.

## Audit Evidence

- `python3 -m pytest app/operator_console/tests/test_help_render.py -q --tb=short`
  - 2026-03-09 local run: pass (`4` passed; one sandboxed pytest cache
    warning only) after adding the local Operator Console `AGENTS.md` link and
    the new view/theme/state/test map links to the in-app help surface
- `python3 dev/scripts/checks/check_active_plan_sync.py`
  - 2026-03-09 local run: pass after recording the Operator Console docs and
    subtree-agent guidance update in MP-359
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
  - 2026-03-09 local run: pass after wiring the new Operator Console package
    maps and local `AGENTS.md` into the repo discovery docs
- `python3 dev/scripts/checks/check_code_shape.py --format md`
  - 2026-03-09 local run: expected red on the dirty tree, but the new
    Operator Console refactor cleared the prior `main_window.py`,
    `_on_process_finished`, `ui_commands.py`, and new-file shape violations;
    remaining reds are in other changed Operator Console theme/state files and
    separate `devctl` review-channel modules outside this slice
- `python3 -m py_compile app/operator_console/views/main_window.py app/operator_console/views/ui_commands.py app/operator_console/views/ui_review_actions.py app/operator_console/views/ui_activity_actions.py app/operator_console/views/ui_layout_state.py app/operator_console/views/ui_window_shell.py app/operator_console/views/ui_swarm_status.py app/operator_console/views/ui_operator_actions.py app/operator_console/views/ui_process_results.py`
  - 2026-03-09 local run: pass after splitting the Operator Console window
    shell/layout/review/activity/operator-result layers
- `python3 -m pytest app/operator_console/tests/views/test_ui_layout.py app/operator_console/tests/views/test_ui_layouts.py -q --tb=short`
  - 2026-03-09 local run: pass (`115` passed; one sandboxed pytest cache
    warning only) after the mixin decomposition of the PyQt shell
- `python3 -m pytest app/operator_console/tests/ -q --tb=short`
  - 2026-03-09 local run: pass (`449` passed; one sandboxed pytest cache
    warning only) after the Operator Console shape-hardening split
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m unittest app.operator_console.tests.state.test_state_modules app.operator_console.tests.views.test_widgets app.operator_console.tests.views.test_ui_layout app.operator_console.tests.views.test_ui_layouts -q`
  - 2026-03-09 local run: pass (`170` tests total across the targeted modules)
    after preferring reconstructed screen text, trimming partial tail prefixes,
    and landing the flippable stats/registry session card contract
- `python3 -m py_compile app/operator_console/state/session_trace_reader.py app/operator_console/state/session_builder.py app/operator_console/state/snapshot_builder.py app/operator_console/state/models.py app/operator_console/views/main_window.py app/operator_console/views/ui_pages.py app/operator_console/views/workbench_layout.py app/operator_console/views/ui_refresh.py app/operator_console/tests/state/test_state_modules.py app/operator_console/tests/views/test_ui_layout.py app/operator_console/tests/views/test_ui_layouts.py`
  - 2026-03-09 local run: pass after splitting the session surfaces into
    terminal/stats/registry panes and hardening the live trace reader against
    private CSI + spinner-noise regressions
- `python3 -m pytest app/operator_console/tests/state/test_state_modules.py app/operator_console/tests/views/test_ui_layout.py app/operator_console/tests/views/test_ui_layouts.py app/operator_console/tests/state/test_presentation_state.py -q --tb=short`
  - 2026-03-09 local run: pass (`148` passed) covering the new split
    session-surface contract, trace-reader history filtering, and the added
    stats/registry widget parenting across tabbed/workbench layouts
- `python3 -m pytest app/operator_console/tests -q --tb=short`
  - 2026-03-09 local run: pass (`406` passed) after preferring reconstructed
    screen text, trimming partial tail prefixes, and landing the flippable
    session detail card contract
- `python3 -m py_compile dev/scripts/devctl/review_channel.py dev/scripts/devctl/review_channel/launch.py dev/scripts/devctl/commands/review_channel.py app/operator_console/state/session_trace_reader.py app/operator_console/state/session_builder.py app/operator_console/state/snapshot_builder.py app/operator_console/views/main_window.py app/operator_console/tests/state/test_state_modules.py dev/scripts/devctl/tests/test_review_channel.py`
  - 2026-03-09 local run: pass after wiring launcher-emitted session trace
    artifacts plus Operator Console live-tail preference
- `python3 -m pytest dev/scripts/devctl/tests/test_review_channel.py app/operator_console/tests/state/test_state_modules.py -q --tb=short`
  - 2026-03-09 local run: pass (`76` tests) covering dry-run launch bundle
    metadata, session-trace script wrapping, and Operator Console preference
    for live tailed session logs over the bridge/registry fallback
- `python3 -m py_compile app/operator_console/state/session_trace_reader.py app/operator_console/tests/state/test_state_modules.py`
  - 2026-03-09 local run: pass after replacing raw line stripping with the
    screen-replayed session-tail parser
- `python3 -m pytest app/operator_console/tests/state/test_state_modules.py -q --tb=short`
  - 2026-03-09 local run: pass (`44` tests) after adding regression coverage
    for ANSI cursor-motion screen reconstruction in live session traces
- `python3 -m py_compile app/operator_console/state/models.py app/operator_console/state/review_state.py app/operator_console/state/session_builder.py app/operator_console/state/snapshot_builder.py app/operator_console/views/main_window.py app/operator_console/views/ui_refresh.py app/operator_console/views/ui_pages.py app/operator_console/views/workbench_layout.py app/operator_console/tests/state/test_state_modules.py app/operator_console/tests/state/test_presentation_state.py app/operator_console/tests/views/test_ui_layout.py app/operator_console/tests/views/test_ui_layouts.py`
  - 2026-03-09 local run: pass after adding review-channel-projection-backed
    Codex/Claude session panes and rebalancing the Workbench/Monitor layouts
- `python3 -m pytest app/operator_console/tests/state/test_state_modules.py app/operator_console/tests/state/test_presentation_state.py app/operator_console/tests/views/test_ui_layout.py app/operator_console/tests/views/test_ui_layouts.py -q --tb=short`
  - 2026-03-09 local run: pass (`140` passed) covering the new session-surface
    snapshot contract, Monitor tab order, sidebar/workbench structure, and
    existing Operator Console state/presentation/layout behavior

- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m unittest app.operator_console.tests.test_theme_controls app.operator_console.tests.test_theme_editor app.operator_console.tests.views.test_agent_detail -q`
  - 2026-03-09 local run: pass (`13` tests; covers theme-aware editor swatch
    chrome, live swatch sync from the current palette, semantic diff
    highlighting, and invalid theme-color fallback in agent detail)
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m py_compile app/operator_console/theme/colors.py app/operator_console/theme/theme_controls.py app/operator_console/theme/theme_editor.py app/operator_console/views/agent_detail.py app/operator_console/tests/test_theme_controls.py app/operator_console/tests/test_theme_editor.py app/operator_console/tests/views/test_agent_detail.py`
  - 2026-03-09 local run: pass after the helper-layer theme cleanup
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m unittest app.operator_console.tests.views.test_agent_detail -q`
  - 2026-03-09 local run: pass (`5` tests; covers diff detection, semantic
    diff highlighting, builtin fallback colors, and invalid theme-color
    fallback for the agent-detail dialog)
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m py_compile app/operator_console/views/agent_detail.py app/operator_console/tests/views/test_agent_detail.py`
  - 2026-03-09 local run: pass after removing the last raw white fallback from
    the live agent-detail theme path
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m unittest app.operator_console.tests.test_theme app.operator_console.tests.test_theme_editor app.operator_console.tests.test_theme_engine -q`
  - 2026-03-09 local run: pass (`57` tests; covers the new semantic
    menu/hover/scrollbar tokens, theme-editor control exposure, and existing
    theme-engine/editor behavior under the stylesheet cleanup)
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m py_compile app/operator_console/theme/colors.py app/operator_console/theme/theme_state.py app/operator_console/theme/theme_editor.py app/operator_console/theme/qss_base.py app/operator_console/theme/qss_controls.py app/operator_console/theme/theme_tokens.py app/operator_console/tests/test_theme.py`
  - 2026-03-09 local run: pass after routing shared QSS RGBA literals through
    semantic theme colors
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m unittest app.operator_console.tests.views.test_agent_detail app.operator_console.tests.test_theme_controls app.operator_console.tests.test_theme_editor -q`
  - 2026-03-09 local run: pass (`10` tests; covers builtin semantic fallback
    colors for diff highlighting, derived swatch chrome in the theme-editor
    color picker, and the editor's overlay export status/preview surface)
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m py_compile app/operator_console/views/agent_detail.py app/operator_console/theme/theme_controls.py app/operator_console/theme/theme_editor.py app/operator_console/tests/views/test_agent_detail.py app/operator_console/tests/test_theme_controls.py`
  - 2026-03-09 local run: pass after the bounded hardcoded-surface cleanup
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m unittest app.operator_console.tests.test_theme_engine app.operator_console.tests.test_theme_editor app.operator_console.tests.test_overlay_import -q`
  - 2026-03-09 local run: pass (`45` tests; covers the engine split plus the
    bounded canonical overlay export path, export blocking for custom desktop
    edits, and the editor's new overlay-export preview/status surface)
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m py_compile app/operator_console/theme/theme_engine.py app/operator_console/theme/theme_state.py app/operator_console/theme/theme_storage.py app/operator_console/theme/theme_overlay_sync.py app/operator_console/theme/overlay_export.py app/operator_console/theme/theme_editor.py app/operator_console/tests/test_theme_engine.py app/operator_console/tests/test_theme_editor.py`
  - 2026-03-09 local run: pass after the engine split and bounded overlay
    export slice
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m unittest app.operator_console.tests.test_overlay_import app.operator_console.tests.test_theme_engine app.operator_console.tests.test_theme_editor -q`
  - 2026-03-09 local run: pass (`41` tests; covers style-pack JSON +
    theme-file TOML read-path import, overlay-import summary rendering,
    theme-engine builtin hydration from overlay metadata, and the expanded
    theme-editor import/preview surfaces)
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m py_compile app/operator_console/theme/overlay_import.py app/operator_console/theme/theme_engine.py app/operator_console/theme/theme_editor.py app/operator_console/tests/test_overlay_import.py`
  - 2026-03-09 local run: pass after the base-theme-only overlay import slice
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m unittest app.operator_console.tests.test_theme_editor -q`
  - 2026-03-09 local run: pass (`4` tests; covers the new surface-scoped
    editor nav plus expanded live-preview shell/approval/monitor surfaces)
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m unittest app.operator_console.tests.test_theme_engine app.operator_console.tests.views.test_agent_detail -q`
  - 2026-03-09 local run: pass (`34` tests; confirms the saved-theme
    hydration fix remains green alongside the diff-theme follow-up)
- `python3 -m pytest app/operator_console/tests/views/test_approval_panel.py -q --tb=short`
  - 2026-03-09 local run: pass (`10` tests; covers the persistent approval
    panel zero-state, empty-queue messaging, and disabled action controls)
- `python3 -m pytest app/operator_console/tests/views/test_ui_layout.py -q --tb=short`
  - 2026-03-09 local run: pass (`44` tests; covers the approval container
    remaining visible with `0 Pending` after initial empty and clear-after-fill
    transitions)
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m unittest app.operator_console.tests.views.test_agent_detail -q`
  - 2026-03-09 local run: pass (`3` tests; covers unified-diff detection plus
    live theme tint wiring for the agent-detail diff pane)
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m unittest app.operator_console.tests.test_theme_engine -q`
  - 2026-03-09 local run: pass (`31` tests; covers legacy saved/custom theme
    hydration so startup restore no longer crashes on missing semantic keys
    such as `toolbar_bg`)
- `/Users/jguida941/.pyenv/versions/3.10.4/bin/python -m py_compile app/operator_console/theme/*.py app/operator_console/tests/test_theme_engine.py`
  - 2026-03-09 local run: pass after the legacy theme-hydration fix
- `python3 -m pytest app/operator_console/tests -q`
  - 2026-03-09 local run: pass (`276` tests; covers the full operator-console
    package after the density/mobile-parity slice and the fail-closed
    repo-root analytics guard)
- `python3 -m pytest app/operator_console/tests/state/test_presentation_state.py app/operator_console/tests/state/test_phone_status_snapshot.py app/operator_console/tests/views/test_help_dialog.py app/operator_console/tests/views/test_ui_layout.py app/operator_console/tests/views/test_ui_layouts.py -q`
  - 2026-03-09 local run: pass (`96` tests; covers the new repo-pulse /
    quality / phone analytics sections, phone-status projection reader, mobile
    help topic, and the denser Home + Analytics layout contracts)
- `python3 -m py_compile app/operator_console/state/*.py app/operator_console/views/*.py app/operator_console/theme/*.py`
  - 2026-03-09 local run: pass after the density/mobile-parity slice
- `python3 -m pytest app/operator_console/tests/ -q --tb=short`
  - 2026-03-09 local run: pass (`210` tests; covers the current
    operator-console package including Home, Workbench, Start Swarm
    preflight/live flow, help surfaces, and theme/workflow guidance)
- `python3 -m pytest app/operator_console/tests/state/test_state_modules.py app/operator_console/tests/state/test_presentation_state.py app/operator_console/tests/views/test_ui_layout.py app/operator_console/tests/views/test_ui_layouts.py app/operator_console/tests/views/test_help_dialog.py -q`
  - 2026-03-09 local run: pass (`103` tests; covers the new home/start surface,
    audience-mode report/status behavior, and updated tab/sidebar routing)
- `python3 -m pytest app/operator_console/tests -q`
  - 2026-03-09 local run: pass (`194` tests; covers the full operator-console
    package after the home/readability slice)
- `python3 -m pytest app/operator_console/tests/views/test_ui_layout.py app/operator_console/tests/views/test_ui_layouts.py app/operator_console/tests/views/test_help_dialog.py -q`
  - 2026-03-09 local run: pass (`78` tests; covers mirrored Start-Swarm
    status, new workbench layout mode, preset buttons, and help text updates)
- `python3 -m pytest app/operator_console/tests/test_theme_editor.py app/operator_console/tests/test_theme_engine.py -q`
  - 2026-03-09 local run: pass (`28` tests; covers workbench/theme guidance
    follow-up after the new layout mode landed)
- `python3 -m unittest app.operator_console.tests.test_theme_engine app.operator_console.tests.views.test_ui_layout app.operator_console.tests.views.test_ui_layouts -q`
  - 2026-03-09 local run: pass (`86` tests; covers builtin-theme identity,
    draft-state toolbar sync, and layout/theme wiring after the active-theme
    authority cleanup)
- `python3 dev/scripts/checks/check_bundle_workflow_parity.py`
  - 2026-03-09 local run: pass after MP-359 theme-authority cleanup
- `python3 dev/scripts/checks/check_review_channel_bridge.py`
  - 2026-03-09 local run: expected red (`bridge.md` and
    `dev/active/review_channel.md` remain untracked in the active dirty tree)
- `python3 dev/scripts/devctl.py review-channel --action launch --dry-run --format json`
  - 2026-03-09 local run: pass after MP-359 theme-authority cleanup
- `python3 -m unittest dev.scripts.devctl.tests.test_bundle_registry -q`
  - 2026-03-09 local run: pass (`6` tests)
- `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
  - 2026-03-09 local host run: pass after the MP-359 Start-Swarm/workbench
    tranche (`0` detected before/after; sandboxed `ps` access is denied, so
    this verification required host execution)
- `python3 -m pytest app/operator_console/tests -q`
  - 2026-03-09 local run: pass (`186` tests; includes the new help-dialog,
    diff-detection, tooltip/layout, provider-badge coverage, and Start Swarm
    preflight/live outcome coverage for the screenshot-hardening slice)
- `python3 dev/scripts/devctl.py hygiene`
  - 2026-03-09 local run: pass
- `python3 dev/scripts/checks/check_active_plan_sync.py`
  - 2026-03-09 local run: pass after MP-359 UX/help/theme-hardening slice
- `python3 dev/scripts/checks/check_multi_agent_sync.py`
  - 2026-03-09 local run: pass after MP-359 UX/help/theme-hardening slice
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
  - 2026-03-09 local run: pass after MP-359 UX/help/theme-hardening slice
- `python3 dev/scripts/devctl.py hygiene --strict-warnings`
  - 2026-03-09 local run: pass after MP-359 controller-shell / AI-plan
    expansion
- `python3 -m py_compile app/operator_console/theme/*.py app/operator_console/views/*.py app/operator_console/tests/*.py`
  - 2026-03-09 local run: pass
- `python3 -m unittest app.operator_console.tests.test_theme app.operator_console.tests.test_theme_engine app.operator_console.tests.test_theme_editor app.operator_console.tests.test_help_render app.operator_console.tests.test_logging_support app.operator_console.tests.test_launch_support`
  - 2026-03-09 local run: pass (`54` tests; covers token-aware stylesheet generation, theme-engine persistence, theme-editor smoke paths, help rendering, launcher bootstrap, and install helpers)
- `python3 -m unittest app.operator_console.tests.state.test_state_modules app.operator_console.tests.state.test_presentation_state app.operator_console.tests.test_launch_support app.operator_console.tests.test_logging_support app.operator_console.tests.test_theme app.operator_console.tests.test_theme_engine app.operator_console.tests.views.test_widgets app.operator_console.tests.views.test_ui_layout app.operator_console.tests.views.test_ui_layouts app.operator_console.tests.views.test_approval_panel`
  - 2026-03-09 local run: pass (`152` tests; validates the extracted
    presentation-state seam, approval-risk policy move out of the widget
    layer, operator-console state helpers, themes, widgets, layouts, and
    approval panel behavior)
- `python3 -m unittest app.operator_console.tests.views.test_ui_layouts`
  - 2026-03-09 local run: pass (covers deferred-delete layout-switch refresh
    regression and refresh-slot exception containment)
- `python3 -m unittest app.operator_console.tests.views.test_ui_layout app.operator_console.tests.views.test_ui_layouts`
  - 2026-03-09 local run: pass (covers monitor-pane reveal behavior and toolbar
    busy-state feedback)
- `python3 -m unittest app.operator_console.tests.state.test_state_modules app.operator_console.tests.test_launch_support app.operator_console.tests.test_logging_support app.operator_console.tests.test_theme app.operator_console.tests.views.test_widgets app.operator_console.tests.views.test_ui_layout app.operator_console.tests.views.test_ui_layouts app.operator_console.tests.views.test_approval_panel`
  - 2026-03-09 local run: pass (`118` tests; validates the state-module split,
    direct imports off the old shim path, launcher/bootstrap behavior, theme
    fragments, widgets, approval panel, and layout refresh behavior)
- `python3 -m unittest app.operator_console.tests.state.test_state_modules`
  - 2026-03-08 local run: pass (the module was later renamed; includes
    Operator Console dev-log artifact coverage)
- `python3 -m py_compile app/operator_console/*.py app/operator_console/state/*.py app/operator_console/theme/*.py app/operator_console/views/*.py`
  - 2026-03-09 local run: pass
- `python3 dev/scripts/checks/check_active_plan_sync.py`
  - 2026-03-09 local run: pass
- `python3 dev/scripts/checks/check_multi_agent_sync.py`
  - 2026-03-09 local run: pass
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
  - 2026-03-09 local run: pass
- `./scripts/operator_console.sh --help`
  - 2026-03-08 local launcher probe: pass (script resolves repo root and
    routes into the Python entrypoint with auto-install support wired in;
    visible rendering still needs a manual desktop-host check)
- `python3 -m unittest app.operator_console.tests.test_logging_support`
  - 2026-03-08 local run: pass
- `python3 -m unittest app.operator_console.tests.test_ui_scroll_behavior`
  - 2026-03-08 local run: pass
- `python3 -m unittest app.operator_console.tests.test_launch_support app.operator_console.tests.test_logging_support app.operator_console.tests.test_theme app.operator_console.tests.views.test_widgets app.operator_console.tests.views.test_ui_layouts app.operator_console.tests.views.test_approval_panel`
  - 2026-03-09 local run: pass (`81` tests; covers launcher bootstrap, theme fragments, widgets, approval panel, layout selectors, deferred-delete regression, and refresh exception containment)
- `python3 -m unittest app.operator_console.tests.test_theme app.operator_console.tests.views.test_widgets app.operator_console.tests.views.test_ui_layout app.operator_console.tests.views.test_ui_layouts -q`
  - 2026-03-09 local run: pass (`126` tests; covers the terminal-first page
    redesign, toolbar-owned action routing, analytics/grid/workbench layout
    reshaping, and the updated stylesheet chrome)
- `python3 -m unittest app.operator_console.tests.test_logging_support app.operator_console.tests.views.test_ui_layout app.operator_console.tests.views.test_ui_layouts app.operator_console.tests.test_theme app.operator_console.tests.views.test_widgets -q`
  - 2026-03-09 local run: pass (`139` tests; covers launcher parser flags,
    Technical-mode refresh recovery, layout-mode startup routing, and the
    updated terminal-first Operator Console surfaces)
- `python3 -m unittest app.operator_console.tests.test_logging_support app.operator_console.tests.views.test_ui_layout app.operator_console.tests.views.test_ui_layouts app.operator_console.tests.test_theme app.operator_console.tests.views.test_widgets -q`
  - 2026-03-09 local run: pass (`139` tests; covers the flatter editor-shell
    chrome, home/analytics/workbench layout rebalancing, and the cleaned-up
    toolbar button/monitor hierarchy)
- `python3 -m unittest app.operator_console.tests.test_logging_support app.operator_console.tests.views.test_ui_layout app.operator_console.tests.views.test_ui_layouts app.operator_console.tests.test_theme app.operator_console.tests.views.test_widgets -q`
  - 2026-03-09 local run: pass (`140` tests; covers the editor-style
    workbench rebuild, default-layout resolution fallback, lane-dock monitor
    focus, and the refreshed toolbar/workspace expectations)
- `python3 -m unittest app.operator_console.tests.test_logging_support app.operator_console.tests.views.test_ui_layout app.operator_console.tests.views.test_ui_layouts app.operator_console.tests.test_theme app.operator_console.tests.views.test_widgets -q`
  - 2026-03-09 local run: pass (`144` tests; covers the native menu-bar move,
    session-aware monitor/sidebar expectations, current snapshot fixture shape,
    and the reduced in-window toolbar chrome)
- `python3 -m unittest app.operator_console.tests.views.test_widgets app.operator_console.tests.views.test_ui_layouts app.operator_console.tests.views.test_ui_layout app.operator_console.tests.test_logging_support -q`
  - 2026-03-09 local run: pass (`125` tests; covers the restored snap-preset
    workbench, terminal-card composition, default layout change, compact copy
    helper, and launcher-layout parser wording)
- `python3 -m pytest app/operator_console/tests -q --tb=short`
  - 2026-03-09 local run: pass (`362` tests; covers the full operator-console
    package after the card-first workbench/default-layout cleanup; one
    sandboxed pytest cache warning only)
- `python3 -m pytest app/operator_console/tests/views/test_ui_layout.py -q --tb=short`
  - 2026-03-09 local run: pass (`47` tests; covers the new technical-mode
    digest framing and denser Home/Activity UI state)
- `python3 -m pytest app/operator_console/tests/state/test_state_modules.py app/operator_console/tests/state/test_phone_status_snapshot.py -q --tb=short`
  - 2026-03-09 local run: pass (`46` tests; confirms the Operator Console
    read model still resolves canonical review-state/mobile paths after the
    denser technical-mode follow-up)
- `python3 -m py_compile app/operator_console/views/workbench_layout.py app/operator_console/views/ui_pages.py app/operator_console/views/main_window.py app/operator_console/tests/views/test_ui_layouts.py`
  - 2026-03-09 local run: pass after grouping the lower Workbench deck into
    task tabs and wiring Home/toolbar navigation back onto those surfaces
- `python3 -m unittest app.operator_console.tests.views.test_ui_layouts -q`
  - 2026-03-09 local run: pass (`46` tests; covers the new `Terminal /
    Stats / Approvals / Reports` workbench grouping plus workbench-specific
    reveal/navigation behavior)
- `python3 -m pytest app/operator_console/tests/views/test_ui_layouts.py -q --tb=short`
  - 2026-03-09 local run: pass (`46` tests; one sandboxed pytest cache
    warning only)
- `python3 -m py_compile app/operator_console/views/workbench_layout.py app/operator_console/views/ui_pages.py app/operator_console/tests/views/test_ui_layouts.py`
  - 2026-03-09 local run: pass after converting Workbench into full-page
    `Sessions / Terminal / Stats / Approvals / Reports` tabs
- `python3 -m unittest app.operator_console.tests.views.test_ui_layouts -q`
  - 2026-03-09 local run: pass (`47` tests; covers the new `Sessions` page,
    workbench start tab, and workbench home/monitor/activity routing)
- `python3 -m pytest app/operator_console/tests/views/test_ui_layouts.py -q --tb=short`
  - 2026-03-09 local run: pass (`47` tests; one sandboxed pytest cache
    warning only)
- `python3 -m py_compile app/operator_console/theme/theme_editor.py app/operator_console/theme/qss_controls.py app/operator_console/tests/test_theme_editor.py`
  - 2026-03-09 local run: pass after replacing the always-on preview rail with
    `Quick Tune / Coverage / Preview` tabs and restyling the toolbar action
    buttons
- `python3 -m unittest app.operator_console.tests.test_theme_editor app.operator_console.tests.test_theme -q`
  - 2026-03-09 local run: pass (`22` tests; covers the new Theme Editor side
    rail, quick control registration, preview tabs, and stylesheet output)
- `python3 -m pytest app/operator_console/tests/test_theme_editor.py app/operator_console/tests/test_theme.py -q --tb=short`
  - 2026-03-09 local run: pass (`22` tests; one sandboxed pytest cache
    warning only)
- `python3 -m py_compile app/operator_console/theme/*.py app/operator_console/views/help_dialog.py app/operator_console/tests/test_theme.py app/operator_console/tests/test_theme_engine.py app/operator_console/tests/test_theme_editor.py app/operator_console/tests/test_overlay_import.py`
  - 2026-03-09 local run: pass after adding persisted component/motion theme
    settings, the full Theme Editor component/motion pages, and the motion
    playground preview
- `python3 -m unittest app.operator_console.tests.test_theme app.operator_console.tests.test_theme_engine app.operator_console.tests.test_theme_editor app.operator_console.tests.test_overlay_import -q`
  - 2026-03-09 local run: pass (`69` tests; covers theme-state persistence,
    stylesheet variants, Theme Editor controls, preview motion plumbing, and
    overlay import/export readiness after the full-editor expansion)
- `python3 -m pytest app/operator_console/tests -q --tb=short`
  - 2026-03-09 local run: pass (`379` tests; full operator-console suite
    remains green after component-style + motion theme expansion; one
    sandboxed pytest cache warning only)
- `python3 dev/scripts/checks/check_active_plan_sync.py`
  - 2026-03-09 local run: pass after recording the Theme Editor/full-theme
    expansion in MP-359 docs
- `python3 dev/scripts/checks/check_multi_agent_sync.py`
  - 2026-03-09 local run: pass
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
  - 2026-03-09 local run: pass after syncing active-plan/docs copy for the
    new theme contract
- `python3 -m pytest app/operator_console/tests/test_launch_support.py app/operator_console/tests/test_help_render.py app/operator_console/tests/test_logging_support.py -q --tb=short`
  - 2026-03-09 local run: pass (`22` tests; launcher help, canonical fallback
    commands, and missing-PyQt startup guidance)
- `python3 dev/scripts/checks/check_active_plan_sync.py`
  - 2026-03-09 local run: pass after recording the launcher-portability
    honesty slice in MP-359
- `python3 -m compileall app/operator_console/theme app/operator_console/views app/operator_console/workflows app/operator_console/state`
  - 2026-03-09 local run: pass after the responsibility-first reorg that split
    `views/` into `actions/`, `workspaces/`, and `shared`, split `theme/` into
    `runtime/`, `editor/`, and `io/`, and removed the old root-level `state/`
    and theme shim clutter
- `python3 -m pytest app/operator_console/tests/views/test_help_dialog.py app/operator_console/tests/state/test_phone_status_snapshot.py dev/scripts/devctl/tests/test_phone_status.py -q --tb=short`
  - 2026-03-11 local run: pass (`8` tests; covers the lazy help-dialog import
    fix plus restored phone/mobile snapshot projection fallback)
- `python3 -m pytest app/operator_console/tests/ -q --tb=short`
  - 2026-03-11 local run: pass (`578` tests; full operator-console suite back
    to green after the help-dialog import-cycle break and phone snapshot
    projection repair)
