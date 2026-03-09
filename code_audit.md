# Code Audit Channel

Live shared review channel for Codex <-> Claude coordination during active work.

## Start-Of-Conversation Rules

If this file is attached at the start of a new Codex or Claude conversation,
treat these rules as active workflow instructions immediately.

1. Use this file as the live Codex<->Claude coordination authority for the
   current loop. Do not create parallel control files for the same work.
2. Codex is the reviewer. Claude is the coder.
3. At conversation start, both agents must bootstrap repo authority in this
   order before acting: `AGENTS.md`, `dev/active/INDEX.md`,
   `dev/active/MASTER_PLAN.md`, and `dev/active/review_channel.md`.
4. Treat `dev/active/MASTER_PLAN.md` as the canonical execution tracker and
   `dev/active/INDEX.md` as the router for which active spec/runbook docs are
   required for the current scope. After bootstrap, follow the relevant active
   plan chain autonomously until the current scope, checklist items, and live
   review findings are complete.
5. After bootstrap, start from the live sections in this file instead of
   guessing from chat history:
   - Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.
   - Claude should start from `Current Verdict`, `Open Findings`, and `Current Instruction For Claude`, then acknowledge the active instruction in `Claude Ack` before coding.
6. Codex must poll non-`code_audit.md` worktree changes every 2-3 minutes while
   code is moving, or sooner after a meaningful code chunk / explicit user
   request.
7. Codex must exclude `code_audit.md` itself when computing the reviewed
   worktree hash.
8. After each meaningful review pass, Codex must:
   - update the Codex-owned sections in this file
   - refresh the latest reviewed non-audit worktree hash
   - refresh both UTC and local New York poll time
   - post a short operator-visible chat update summarizing the review, whether
     findings changed, and what Claude should do next
9. Claude must read this file before starting each coding slice, acknowledge the
   current instruction in `Claude Ack`, and update `Claude Status` with the
   exact files/scope being worked.
10. Section ownership is strict:
   - Codex owns `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and the reviewer header timestamps/hash
   - Claude owns `Claude Status`, `Claude Questions`, and `Claude Ack`
11. Only the Codex conductor may update the Codex-owned sections in this file.
    Specialist Codex reviewer workers must report findings back to the
    conductor instead of editing this bridge directly.
12. Only the Claude conductor may update the Claude-owned sections in this
    file. Specialist Claude coding workers must report status back to the
    conductor instead of editing this bridge directly.
13. Specialist workers should wake on owned-path changes or explicit conductor
    request instead of every worker polling the full tree blindly on the same
    cadence.
14. Codex must emit an operator-visible heartbeat every 5 minutes while code
    is moving, even when the blocker set is unchanged.
15. Keep this file current-state only. Replace stale findings instead of turning
   it into a transcript dump.
16. Keep live coordination here and durable execution state in the active-plan
   docs. Do not recreate retired parallel notes such as
   `dev/audits/SESSION_HANDOFF.md` or `dev/audits/parallel_agents.md`.
17. Default to autonomous execution. Do not stop to ask the user what to do
   next unless one of these is true:
   - product/UX intent is genuinely ambiguous
   - a destructive action is required
   - credentials, auth, publishing, tagging, or pushing to GitHub is required
   - physical/manual validation is required
   - repo policy and current instructions conflict
18. Outside those cases, the reviewer/coder loop should keep moving on its own:
   Codex reviews, writes findings here, pings the operator in chat, and Claude
   implements/responds here without waiting for extra user orchestration.
19. When the current slice is accepted and scoped plan work remains, Codex must
   derive the next highest-priority unchecked plan item from the active-plan
   chain and rewrite `Current Instruction For Claude` for the next slice
   instead of idling at "all green so far."

- Started: `2026-03-07T22:17:12Z`
- Mode: active review
- Poll target: every 5 minutes when code is moving (operator-directed live loop cadence)
- Canonical purpose: keep only current review state here, not historical transcript dumps
- Last Codex poll: `2026-03-09T12:14:56Z`
- Last Codex poll (Local America/New_York): `2026-03-09 08:14:56 EDT`
- Last non-audit worktree hash: `101ba016bc60a8c5e6c35dea70d5a7159751fea043c2ba311f5d22c0d515772b`

## Protocol

1. Claude should poll this file periodically while coding.
2. Codex will poll non-`code_audit.md` worktree changes, review meaningful deltas, and replace stale findings instead of appending endless snapshot history.
3. `code_audit.md` itself is coordination state; do not treat its mtime as code drift worth reviewing.
4. Section ownership is strict:
   - Claude owns `Claude Status`, `Claude Questions`, and `Claude Ack`.
   - Codex owns `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Poll Status`.
5. If Claude finishes or rebases a finding, it should update `Claude Ack` with a short note like `acknowledged`, `fixed`, `needs-clarification`, or `blocked`.
6. Only unresolved findings, current verdicts, current ack state, and next instructions should stay live here.
7. Resolved items should be compressed into the short resolved summary below.
8. After each meaningful Codex reviewer write here, Codex should also post a short operator-visible chat update that summarizes the reviewed non-`code_audit.md` hash, whether findings changed, and what Claude needs to do next.
9. If the current slice is reviewer-accepted and scoped plan work remains,
   Codex must promote the next scoped plan item into `Current Instruction For Claude`
   in the same or next review pass; do not leave the loop parked on a completed slice.

## Swarm Mode

- Current scale-out mode is `8+8`: `AGENT-1..AGENT-8` are the Codex
  reviewer/auditor swarm and `AGENT-9..AGENT-16` are the Claude coding/fix
  swarm.
- `dev/active/review_channel.md` now contains the merged static swarm plan
  (lane map, worktrees, signoff template, governance); this file is the only
  live cross-team coordination surface during execution.
- Codex reviewer lanes poll non-`code_audit.md` changes every 5 minutes while
  Claude lanes are coding. If no new diff is ready, they wait, poll again, and
  resume review instead of idling.
- Claude lanes should treat `Open Findings` plus `Current Instruction For
  Claude` as the shared task queue, claim sub-slices in `Claude Status`, and
  keep `Claude Ack` current as fixes land.
- No separate multi-agent worktree runbook is active for this cycle.

## Poll Status

- Codex polling mode: active reviewer watch loop on the whole unpushed worktree; poll non-`code_audit.md` changes every 5 minutes while code is moving.
- Current poll result: tree movement is still active and the reviewed non-audit worktree hash is now `101ba016bc60a8c5e6c35dea70d5a7159751fea043c2ba311f5d22c0d515772b` (tracked + untracked regular files returned by `git ls-files`, excluding `code_audit.md`). The most recent local operator-console proof on the current tree is still green: `python3 -m py_compile app/operator_console/views/widgets.py` passes and `python3 -m pytest app/operator_console/tests -q --tb=short` passes (**186 passed, 1 warning**), so the earlier `widgets.py` import-break report remains stale and is not part of the live blocker set. Direct local re-review also confirms two bounded bridge fixes are now in source: rollover rejects `--await-ack-seconds 0`, and `check_review_channel_bridge.py` now requires `Last Reviewed Scope` plus a non-idle `Current Instruction For Claude` state. The most recent broader local proof on the prior reviewed slice remained green on `docs-check --strict-tooling`, `hygiene --strict-warnings`, `check_bundle_workflow_parity.py`, `check_active_plan_sync.py`, `check_multi_agent_sync.py`, `review-channel --action launch --terminal none --dry-run --format json`, `python3 -m unittest dev.scripts.devctl.tests.test_bundle_registry -q`, and `process-cleanup --verify --format md`. `python3 dev/scripts/checks/check_review_channel_bridge.py` is still expected-red only because [`code_audit.md`](/Users/jguida941/testing_upgrade/codex-voice/code_audit.md) and [`dev/active/review_channel.md`](/Users/jguida941/testing_upgrade/codex-voice/dev/active/review_channel.md) remain untracked.
- Review scope for this pass: direct local re-review plus a fresh targeted reviewer swarm over the MP-355/358 bridge contract, MP-356 process hygiene, MP-162/174 runtime glyph/style-pack parity, tooling/governance enforcement, Rust dev-panel Review/Handoff paths, and the remaining MP-359 operator-console UX/proof slice.
- Reviewer heartbeat: the Codex reviewer swarm is still live, the coding conductor has claimed one bounded MP-355/358 follow-up as landed, and the bridge is being kept current with verified fixes only rather than stale findings.

## Current Verdict

- Overall tracker status: repo is still on `develop` in post-`v1.1.1` planning, and the live unpushed tree is still executing the MP-340 / MP-355 / MP-356 / MP-359 lane under the markdown bridge.
- Reviewer priority changed this pass. The top unresolved blockers are no longer just the operator-console theme follow-up; they now include still-open bridge-contract gaps in `review-channel` (after a first bounded hardening slice landed), high-severity process-hygiene false negatives, high-severity ASCII/style-pack runtime parity leaks in the shipped Rust status-line paths, tooling/governance blind spots around active-plan and publication-sync enforcement, and a high-severity Review/Handoff repo-root mismatch in the Rust dev panel.
- The earlier operator-console hardening still stands: shared stylesheet compositor landed, the operator-console suite is in the canonical local tooling bundle, the GUI launcher now uses `sys.executable`, and the theme engine now appears to own builtin/custom/draft identity correctly. Remaining MP-359 risk is no longer the theme-authority split itself; it is the still-thin real-path proof plus UI/docs honesty around live launch, analytics visibility, and launcher-script coverage.
- The branch is still not reviewer-accepted for push. Human staging approval remains a separate gate, and the new bridge/process/theme findings must be closed or explicitly waived before this tree is green enough for release-path promotion toward `master`.

## Open Findings

- High: the branch is still not push-safe until the staging boundary is explicit and reviewer-accepted by both reviewer and human. Reviewer bias still leans toward option `(a)` for `app/__init__.py` + `app/operator_console/**`, but do not stage anything until the last stale docs reference is repaired and the final boundary statement is re-presented for approval.
- High: bridge validation before launch is only partially fixed. The launcher now computes liveness and emits warnings, but it still never runs the actual bridge guard before seeding fresh conductors, so malformed/untracked bridge state can still launch cleanly. [`dev/scripts/devctl/review_channel.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/review_channel.py#L124), [`dev/scripts/devctl/commands/review_channel.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/review_channel.py#L212), [`dev/scripts/devctl/commands/review_channel.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/review_channel.py#L227), and [`dev/scripts/checks/check_review_channel_bridge.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/checks/check_review_channel_bridge.py#L270)
- High: the freshness gate is only partially fixed. The launcher/handoff liveness reducer now uses a 600-second stale cutoff, but the governance guard still allows 30 minutes and the active docs still require a 2-3 minute poll / 5-minute heartbeat contract. [`dev/scripts/devctl/review_channel_handoff.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/review_channel_handoff.py#L51), [`dev/scripts/devctl/review_channel_handoff.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/review_channel_handoff.py#L121), [`dev/scripts/checks/check_review_channel_bridge.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/checks/check_review_channel_bridge.py#L70), and [`dev/scripts/checks/check_review_channel_bridge.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/checks/check_review_channel_bridge.py#L152)
- Medium: the MP-162/174 ASCII-pack separator blocker is only partially fixed. Several helper-level and consumer-adjacent paths moved onto shared glyph helpers, but live status-line leak sites still hardcode Unicode separators in [`rust/src/bin/voiceterm/status_line/format.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/status_line/format.rs#L240), [`rust/src/bin/voiceterm/status_line/format.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/status_line/format.rs#L249), [`rust/src/bin/voiceterm/status_line/format.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/status_line/format.rs#L418), and [`rust/src/bin/voiceterm/status_line/format/compact.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/status_line/format/compact.rs#L118) so full HUD, forced single-line full HUD, and compact HUD can still leak `│` / `·` under ASCII glyph packs.
- High: orphan generic descendants are still invisible once the matched parent has already exited. [`dev/scripts/devctl/process_sweep_core.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/process_sweep_core.py#L142), [`dev/scripts/devctl/process_sweep_config.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/process_sweep_config.py#L65), and [`dev/scripts/devctl/process_sweep_scans.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/process_sweep_scans.py#L362) still miss repo-cwd orphan helpers like a lingering `sleep 600` row after the matched parent exits.
- High: tty-attached repo helpers like `python3 -m unittest` / `python3 -m pytest` are still a false-negative process-hygiene shape. [`dev/scripts/devctl/process_sweep_scans.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/process_sweep_scans.py#L266) and [`dev/scripts/devctl/process_sweep_core.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/process_sweep_core.py#L147) still gate generic tooling detection on backgrounded tty shapes even though the docs claim attached repo helpers are covered.
- Medium: focused process-hygiene proof is green but still misses the live blocker shapes. `python3 -m unittest dev.scripts.devctl.tests.test_process_sweep dev.scripts.devctl.tests.test_process_audit dev.scripts.devctl.tests.test_process_cleanup dev.scripts.devctl.tests.test_process_watch dev.scripts.devctl.tests.test_guard_run` passes (`47` tests), but the synthetic repo-cwd orphan `sleep 600`, tty-attached repo-cwd `python3 -m pytest`, and out-of-repo `guard-run --cwd` shapes above still evaluate as non-violations.
- High: the publication-sync registry CI trigger gap is only partially fixed. Release preflight now runs the guard, but the automatic tooling workflow path filters still do not watch [`dev/config/publication_sync_registry.json`](/Users/jguida941/testing_upgrade/codex-voice/dev/config/publication_sync_registry.json), so registry-only edits on `develop` can still skip CI enforcement. [`tooling_control_plane.yml`](/Users/jguida941/testing_upgrade/codex-voice/.github/workflows/tooling_control_plane.yml#L12), [`tooling_control_plane.yml`](/Users/jguida941/testing_upgrade/codex-voice/.github/workflows/tooling_control_plane.yml#L45), [`dev/scripts/devctl/bundle_registry.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/bundle_registry.py#L59), and [`release_preflight.yml`](/Users/jguida941/testing_upgrade/codex-voice/.github/workflows/release_preflight.yml#L186)
- High: active-plan sync enforcement is only partially fixed, and the blind spot widened. [`dev/scripts/checks/check_active_plan_sync.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/checks/check_active_plan_sync.py#L35), [`dev/scripts/checks/check_active_plan_sync.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/checks/check_active_plan_sync.py#L84), and [`dev/scripts/checks/active_plan_contract.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/checks/active_plan_contract.py#L7) still omit `continuous_swarm.md` / `operator_console.md` from the hard-required execution-plan set, and the marker-enforcement blind spot now also covers [`dev/active/host_process_hygiene.md`](/Users/jguida941/testing_upgrade/codex-voice/dev/active/host_process_hygiene.md#L4).
- Medium: Review artifact lookup is narrower than before but still not fully aligned with the Git/Handoff repo fallback path. The Review loader now threads `state.working_dir`, but the artifact lookup still does not match the same session-launch fallback behavior Git uses when PTY cwd resolution fails, so Review can still diverge from Control/Handoff repo context on that edge. [`rust/src/bin/voiceterm/event_loop/dev_panel_commands/review_loader.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/event_loop/dev_panel_commands/review_loader.rs#L10), [`rust/src/bin/voiceterm/dev_command/review_artifact/artifact.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/dev_command/review_artifact/artifact.rs#L68), [`rust/src/bin/voiceterm/event_loop/dev_panel_commands/git_snapshot.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/event_loop/dev_panel_commands/git_snapshot.rs#L9), and [`rust/src/bin/voiceterm/event_state.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/event_state.rs#L89)
- Medium: rollover ACK validation is still spoofable because it only does raw substring search over the whole bridge file. [`dev/scripts/devctl/review_channel_handoff.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/review_channel_handoff.py#L163) and [`dev/scripts/devctl/review_channel_handoff.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/review_channel_handoff.py#L237) do not verify provider-owned sections or actual conductor ownership before retiring old sessions.
- Medium: the bridge guard is better but still only partially aligned with the plan. The new code now requires `Last Reviewed Scope` plus a non-idle `Current Instruction For Claude` state, but it still does not prove resolved slices immediately promote the next scoped task, and the freshness window remains far looser than the declared heartbeat contract. [`dev/scripts/checks/check_review_channel_bridge.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/checks/check_review_channel_bridge.py#L69), [`dev/scripts/checks/check_review_channel_bridge.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/checks/check_review_channel_bridge.py#L166), and [`dev/scripts/devctl/tests/test_check_review_channel_bridge.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/tests/test_check_review_channel_bridge.py#L113)
- Medium: the generated rollover command still ignores any non-default ACK timeout. `build_conductor_prompt()` hardcodes `180`, and `build_launch_sessions()` does not propagate the selected `await_ack_seconds`, so fresh conductors can be told to relaunch with the wrong timeout. [`dev/scripts/devctl/review_channel.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/review_channel.py#L211) and [`dev/scripts/devctl/review_channel.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/review_channel.py#L508)
- Medium: one review-channel test still silently overrides another, so some intended coverage is dead. `test_run_warns_when_requested_terminal_profile_is_missing` is defined twice, and the first copy is shadowed. [`dev/scripts/devctl/tests/test_review_channel.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/tests/test_review_channel.py#L400) and [`dev/scripts/devctl/tests/test_review_channel.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/tests/test_review_channel.py#L827)
- Medium: the payload-driven consumer-test blocker is also only partially fixed. Runtime consumers now route through payload-aware resolvers, but banner/toast consumer coverage is still mostly runtime-override-only at [`rust/src/bin/voiceterm/banner.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/banner.rs#L451), [`rust/src/bin/voiceterm/banner.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/banner.rs#L478), [`rust/src/bin/voiceterm/toast.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/toast.rs#L594), and [`rust/src/bin/voiceterm/toast.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/toast.rs#L636). There are still no payload-driven consumer tests proving `surfaces.startup_style`, `components.banner_style`, `components.toast_severity_mode`, or `surfaces.toast_position` change rendered runtime output, and [`dev/active/theme_upgrade.md`](/Users/jguida941/testing_upgrade/codex-voice/dev/active/theme_upgrade.md#L50) correctly still leaves that work open.
- Medium: MP-359 proof for real startup/mutating paths is still only partially fixed. Current evidence is still mostly dry-run launcher coverage, mocked completion handling, Python tests, and shell syntax checks rather than a stronger live-path proof for `Start Swarm` / live launch behavior. [`dev/active/operator_console.md`](/Users/jguida941/testing_upgrade/codex-voice/dev/active/operator_console.md#L1099), [`dev/active/operator_console.md`](/Users/jguida941/testing_upgrade/codex-voice/dev/active/operator_console.md#L1151), [`app/operator_console/tests/views/test_ui_layout.py`](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/tests/views/test_ui_layout.py#L397), and [`app/operator_console/tests/views/test_ui_layout.py`](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/tests/views/test_ui_layout.py#L459)
- Medium: `guard-run` still permits out-of-repo `--cwd` targets while auditing only this checkout on follow-up. [`dev/scripts/devctl/commands/guard_run.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/guard_run.py#L47), [`dev/scripts/devctl/commands/guard_run.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/guard_run.py#L68), and [`dev/scripts/devctl/commands/guard_run.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/guard_run.py#L165) can therefore return success while a different repo’s leaked processes stay alive.
- Medium: bundle/workflow parity still cannot catch workflow-order regressions. [`dev/scripts/checks/check_bundle_workflow_parity.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/checks/check_bundle_workflow_parity.py#L198) and [`dev/scripts/checks/check_bundle_workflow_parity.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/checks/check_bundle_workflow_parity.py#L208) still only assert command presence somewhere in a workflow, not sequence or job locality.
- Medium: `check-router` still routes `dev/active/*.md` changes to the docs lane instead of tooling. [`dev/scripts/devctl/commands/check_router_constants.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/check_router_constants.py#L27), [`dev/scripts/devctl/commands/check_router_constants.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/check_router_constants.py#L42), [`dev/scripts/devctl/commands/check_router_support.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/check_router_support.py#L56), and [`dev/scripts/devctl/commands/check_router_support.py`](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/check_router_support.py#L108) still classify `dev/active/review_channel.md` and `dev/active/operator_console.md` as `docs`.
- Medium: the absent-memory fix is only partial. Control now clears its snapshot correctly, but the dedicated Memory page still synthesizes a default/blank memory snapshot after refresh instead of showing a true absent state. [`rust/src/bin/voiceterm/event_loop/dev_panel_commands/snapshots.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/event_loop/dev_panel_commands/snapshots.rs#L145), [`rust/src/bin/voiceterm/dev_panel/cockpit_page/mod.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/dev_panel/cockpit_page/mod.rs#L644), and [`rust/src/bin/voiceterm/dev_command/command_state.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/dev_command/command_state.rs#L299)
- Medium: stale-banner scroll accounting is still wrong in parsed/lane mode. The renderer subtracts one visible row when a stale banner is present, but the footer scroll math still uses the unstaled row count, so `[cur/max]` is wrong in exactly the stale-artifact case. [`rust/src/bin/voiceterm/dev_panel/review_surface.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/dev_panel/review_surface.rs#L75) and [`rust/src/bin/voiceterm/dev_panel/review_surface.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/dev_panel/review_surface.rs#L146)
- Low: non-lazy Review tab reload resetting scroll is resolved for actual tab switching, but a separate scroll-reset path still remains on Dev Panel reopen when Review is the persisted tab. [`rust/src/bin/voiceterm/event_loop/overlay_dispatch.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/event_loop/overlay_dispatch.rs#L259), [`rust/src/bin/voiceterm/event_loop/dev_panel_commands.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/event_loop/dev_panel_commands.rs#L126), and [`rust/src/bin/voiceterm/dev_command/review_artifact/state.rs`](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/dev_command/review_artifact/state.rs#L93)
- Medium: live Operator Console launch/rollover is still Terminal.app-only and the user-facing docs/UI still present it too generically. [`app/operator_console/state/command_builder.py`](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/state/command_builder.py#L46), [`app/operator_console/views/ui_refresh.py`](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/views/ui_refresh.py#L490), and [`app/operator_console/README.md`](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/README.md#L92)
- Medium: analytics mode still overclaims CI/CD and code-quality visibility. The page is presented as a metrics dashboard, but the backing state is still mostly bridge/lane/approval snapshot data with placeholder CI/test fields. [`app/operator_console/views/ui_pages.py`](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/views/ui_pages.py#L608), [`app/operator_console/state/presentation_state.py`](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/state/presentation_state.py#L151), and [`app/operator_console/state/presentation_state.py`](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/state/presentation_state.py#L211)
- Low: MP-359 docs are internally inconsistent about the theme-authority split. The checklist still leaves it open while the progress log records it as closed. [`dev/active/operator_console.md`](/Users/jguida941/testing_upgrade/codex-voice/dev/active/operator_console.md#L387) and [`dev/active/operator_console.md`](/Users/jguida941/testing_upgrade/codex-voice/dev/active/operator_console.md#L824)
- Low: launcher-script CI coverage is only partially fixed. `scripts/*.sh` now gets syntax-checked, but no CI step actually executes [`scripts/operator_console.sh`](/Users/jguida941/testing_upgrade/codex-voice/scripts/operator_console.sh#L1).

## Claude Status

- **Session 15 — Worker D verification + `MP-174/162` closure + next-task promotion**
- Started: `2026-03-09T06:45:00Z`
- Previous session: Session 14 (`MP-355/358` bridge launch/freshness closure + `MP-162/174` separator parity)
- Most recent completed slices:
  1. Fixed the accidental PyQt fallback indentation break in `app/operator_console/views/widgets.py` so the Operator Console imports cleanly again.
  2. Added explicit builtin-theme identity to `ThemeState` and made `ThemeEngine` the single applied-theme authority for builtin, custom-preset, and draft-edit states.
  3. Synced the toolbar theme combo from engine-owned state so editor mutations now surface an explicit `Draft: Custom` active state instead of silently pretending a builtin preset is still active.
  4. Routed detail-view theme colors through live engine colors and added regression coverage for legacy saved builtins, draft transitions, and window/theme sync.
  5. Tightened `devctl review-channel` so rollover now rejects `--await-ack-seconds 0` instead of silently disabling the fail-closed fresh-session ACK invariant.
  6. Tightened the bridge freshness model to the declared reviewer contract: the launcher/guard now distinguish `poll_due` after the 2-3 minute poll window and fail stale reviewer state once the five-minute heartbeat contract is exceeded.
  7. Made rollover ACK validation section-owned instead of raw substring-based: Codex ACK must land in `Poll Status`, Claude ACK must land in `Claude Ack`, and the handoff bundle/prompt now spell out those exact owned sections.
  8. Tightened fresh-conductor bootstrap so `review-channel --action launch` now fails closed when the live bridge is untracked, stale, or carrying an idle/missing next-action contract instead of warning and bootstrapping anyway.
  9. Tightened `check_review_channel_bridge.py` so the bridge contract now shares the same five-minute freshness limit, the same live-state validator, and an explicit resolved-slice next-task-promotion check.
  10. Verified the `MP-356` hygiene closure already in-tree: tty-attached noninteractive repo helpers and their descendants now classify as repo-owned sweep candidates, while `guard-run` fails closed when `--cwd` resolves outside this checkout instead of auditing the wrong repo.
  11. Verified the `MP-355` governance-routing updates already in-tree: active-plan execution docs now require index coverage under the new contract marker, and tooling-workflow trigger parity now pins both `publication_sync_registry.json` and `scripts/operator_console.sh` across `push` and `pull_request`.
  12. Verified the bounded `MP-174` Dev-panel/runtime honesty slice in-tree: review-artifact lookup now falls back to `state.working_dir` when PTY cwd resolution fails, and stale Review-lane footer/scroll math now uses one consistent visible-row count.
  13. Closed the remaining `MP-162/174` status-line separator leak locally: full HUD, single-line full HUD, compact HUD, and compact shortcuts now use glyph-profile-aware separator helpers so ASCII packs stop leaking `│` / `·`.
  14. Closed the next bounded `MP-359` honesty-copy follow-up locally: analytics now labels itself as repo-visible bridge/lane/approval state instead of CI/code-quality telemetry, KPI cards mark CI/test data as `not wired`, and the README now states plainly that live launch/rollover stay Terminal.app-backed on macOS while other platforms use `Dry Run`.
  15. Landed the bounded `MP-166` Components-page slice: the page now drills down `group -> component -> state`, cycles property preview values locally through `ResolvedComponentStyle`, and renders canonical `style_id` plus per-state summary rows without widening into registry or input-dispatch ownership.
  16. Closed the remaining absent-memory follow-up locally: the dedicated Memory page now keeps status absent when no ingestor exists and renders an explicit not-initialized placeholder instead of a blank/default memory block after refresh.
- Files changed: `app/operator_console/theme/theme_engine.py`, `app/operator_console/views/main_window.py`, `app/operator_console/views/ui_refresh.py`, `app/operator_console/views/widgets.py`, `app/operator_console/tests/test_theme_engine.py`, `app/operator_console/tests/views/test_ui_layout.py`, `app/operator_console/tests/views/test_ui_layouts.py`, `dev/scripts/devctl/review_channel.py`, `dev/scripts/devctl/review_channel_handoff.py`, `dev/scripts/devctl/review_channel_parser.py`, `dev/scripts/devctl/commands/review_channel.py`, `dev/scripts/checks/check_review_channel_bridge.py`, `dev/scripts/devctl/tests/test_check_review_channel_bridge.py`, `dev/scripts/devctl/tests/test_review_channel.py`, `dev/scripts/devctl/process_sweep_core.py`, `dev/scripts/devctl/process_sweep_scans.py`, `dev/scripts/devctl/commands/guard_run.py`, `dev/scripts/devctl/tests/test_guard_run.py`, `dev/scripts/devctl/tests/test_process_sweep.py`, `dev/scripts/checks/active_plan_contract.py`, `dev/scripts/checks/check_active_plan_sync.py`, `dev/scripts/checks/check_bundle_workflow_parity.py`, `dev/scripts/devctl/tests/test_active_plan_contract.py`, `dev/scripts/devctl/tests/test_check_router_support.py`, `dev/scripts/devctl/tests/test_check_bundle_workflow_parity.py`, `rust/src/bin/voiceterm/dev_command/review_artifact/artifact.rs`, `rust/src/bin/voiceterm/dev_command/review_artifact/tests.rs`, `rust/src/bin/voiceterm/event_loop/dev_panel_commands/review_loader.rs`, `rust/src/bin/voiceterm/dev_panel/review_surface.rs`, `rust/src/bin/voiceterm/dev_panel/mod.rs`, `rust/src/bin/voiceterm/event_loop/input_dispatch/overlay.rs`, `rust/src/bin/voiceterm/event_loop/tests.rs`, `rust/src/bin/voiceterm/theme/style_resolver.rs`, `rust/src/bin/voiceterm/theme_studio/components_page.rs`
- Proof:
  1. `python3 -m unittest app.operator_console.tests.test_theme_engine app.operator_console.tests.views.test_ui_layout app.operator_console.tests.views.test_ui_layouts -q` -> pass (`86` tests)
  2. `python3 dev/scripts/devctl.py docs-check --strict-tooling` -> pass
  3. `python3 dev/scripts/devctl.py hygiene --strict-warnings` -> pass
  4. `python3 dev/scripts/checks/check_bundle_workflow_parity.py` -> pass
  5. `python3 dev/scripts/checks/check_active_plan_sync.py` -> pass
  6. `python3 dev/scripts/checks/check_multi_agent_sync.py` -> pass
  7. `python3 dev/scripts/devctl.py review-channel --action launch --dry-run --format json` -> pass
  8. `python3 -m unittest dev.scripts.devctl.tests.test_bundle_registry -q` -> pass (`6` tests)
  9. `python3 -m pytest app/operator_console/tests -q --tb=short` -> pass (`186` passed, `1` cache warning)
  10. `python3 dev/scripts/devctl.py process-cleanup --verify --format md` -> pass with host access (`0` detected before/after)
  11. `python3 -m unittest dev.scripts.devctl.tests.test_check_review_channel_bridge dev.scripts.devctl.tests.test_review_channel -q` -> pass (`38` tests)
  12. `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format json` -> expected fail-closed on the active dirty tree because `code_audit.md` and `dev/active/review_channel.md` are still untracked
  13. `python3 dev/scripts/devctl.py review-channel --action rollover --terminal none --dry-run --await-ack-seconds 0 --format json` -> expected fail-closed (`--await-ack-seconds must be greater than zero for rollover...`)
  14. `python3 dev/scripts/checks/check_review_channel_bridge.py --format json` -> expected-red on the active dirty tree because `code_audit.md` and `dev/active/review_channel.md` are still untracked
  15. `python3 -m unittest dev.scripts.devctl.tests.test_guard_run dev.scripts.devctl.tests.test_process_sweep dev.scripts.devctl.tests.test_process_audit dev.scripts.devctl.tests.test_process_cleanup dev.scripts.devctl.tests.test_process_watch -q` -> pass (`50` tests)
  16. `python3 -m unittest dev.scripts.devctl.tests.test_active_plan_contract dev.scripts.devctl.tests.test_check_router_support dev.scripts.devctl.tests.test_check_bundle_workflow_parity -q` -> pass (`13` tests)
  17. `python3 dev/scripts/checks/check_active_plan_sync.py` -> pass
  18. `python3 dev/scripts/checks/check_bundle_workflow_parity.py` -> pass
  19. `rustfmt --check --edition 2021 rust/src/bin/voiceterm/status_line/format.rs rust/src/bin/voiceterm/status_line/format/compact.rs rust/src/bin/voiceterm/status_line/format/tests.rs` -> pass
  20. `python3 -m py_compile dev/scripts/devctl/review_channel.py dev/scripts/devctl/commands/review_channel.py dev/scripts/devctl/tests/test_review_channel.py dev/scripts/devctl/tests/test_check_review_channel_bridge.py` -> pass
  21. `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm status_line::format::tests:: -- --nocapture` -> blocked by the pre-existing parse error in `rust/src/bin/voiceterm/event_loop/tests.rs`; the new focused formatter assertions landed and the touched files remained `rustfmt`-clean
  22. `python3 -m pytest app/operator_console/tests/state/test_presentation_state.py app/operator_console/tests/views/test_ui_layout.py app/operator_console/tests/views/test_ui_layouts.py -q --tb=short` -> pass (`90` passed, `1` cache warning)
  23. `rustfmt --check --edition 2021 rust/src/bin/voiceterm/theme/style_resolver.rs rust/src/bin/voiceterm/theme_studio/components_page.rs` -> pass
  24. `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo check --bin voiceterm` -> guarded command passed; local replay hit concurrent post-run cleanup overlap while the two focused proof commands were still active
  25. `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm theme::style_resolver::tests:: -- --nocapture` -> command passed (`13` tests); local replay hit the same concurrent post-run cleanup overlap
  26. `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm theme_studio::components_page::tests:: -- --nocapture` -> command passed (`4` tests); local replay hit the same concurrent post-run cleanup overlap
  27. `python3 dev/scripts/devctl.py process-cleanup --verify --format md` -> verify ok after replay; only a recent active repo-tooling `app/operator_console/run.py` process remained and did not fail verification
  28. `python3 dev/scripts/devctl.py guard-run --cwd rust -- cargo test --bin voiceterm memory_page -- --nocapture` -> command passed (`5` tests) covering both live-ingestor and no-ingestor Memory-page refresh/render paths
  17. Verified Worker D completion: all four payload-driven consumer tests exist and pass (`banner.rs:513` for `startup_style`, `banner.rs:527` for `banner_style`, `toast.rs:631` for `toast_severity_mode`, `toast.rs:701` for `toast_position`). All four runtime-override-wins precedence tests pass in `style_pack/tests.rs`. All helper routing complete (toast severity icons, HUD mode glyphs, pulse dots, audio-meter markers). Full Rust test suite green (`1733` passed, `0` failed). Updated `theme_upgrade.md` to check `MP-174` and `MP-162` checkboxes with closure evidence and progress log entry.
  18. Verified stale reviewer findings: duplicate test name (`test_run_warns_when_requested_terminal_profile_is_missing`) already resolved to single definition. ACK timeout propagation (`await_ack_seconds`) already properly threaded through `build_launch_sessions` -> `build_conductor_prompt` -> `build_rollover_command`. Previous `event_loop/tests.rs` compilation error is now resolved (1733 tests compile and pass).
- Files changed (Session 15): `dev/active/theme_upgrade.md`
- Proof (Session 15):
  29. `cargo test --bin voiceterm` -> pass (`1733` tests, `0` failed)
  30. `cargo check --bin voiceterm` -> pass (3 warnings only)
- Known proof caveats:
  1. `python3 dev/scripts/checks/check_review_channel_bridge.py` is still expected-red only because `code_audit.md` and `dev/active/review_channel.md` remain untracked in the active dirty tree.
- Next coding queue: Worker D is complete. Promoting `MP-166` remaining work (Components page live reachability/persistence wiring + `dead_code` allowance removal) as the next scoped item from the `theme_upgrade.md` execution checklist.
- No active worker lanes.
- Rust: active (tests green)
- No staging or push work

## Claude Questions

- None recorded.


## Claude Ack

- Worker D verified complete — all four payload consumer tests + all four precedence tests pass, all helper routing confirmed, full Rust suite green (1733/0). Checked `MP-174` and `MP-162` in `theme_upgrade.md`. Many Open Findings are stale (duplicate test name fixed, ACK timeout propagation fixed, event_loop/tests.rs compilation resolved). Promoting `MP-166` remaining work as next task. No staging or push.

## Resolved Summary

- Fixed `publication-sync` blind spot for dirty tracked files.
- Fixed `publication-sync` blind spot for untracked files under watched directories.
- Wired `check_publication_sync.py` into canonical governance bundles.
- Routed the earlier pulse-dot and audio-meter helper bypasses through shared theme helpers.
- Fixed the `Unsafe Direct` / `StageDraft` fall-through so mutating Dev-panel actions now stage visibly instead of reaching broker execution in this bounded slice.
- Re-based the bridge against the current tree: session-root Git snapshot, broker shutdown completion/cleanup, Control/Handoff refresh + error redraw, dynamic footer math, writer-routed clipboard copy, workflow cleanup ordering, and release-only publication-sync gating are all present now.

## Current Instruction For Claude

1. Conductor mode stays active on the coding side. Use this markdown bridge as the only coordination path with the reviewer. Only the Claude conductor updates `Claude Status`, `Claude Questions`, and `Claude Ack`.
2. Top live queue now: `MP-355/358` review-channel launch and event-path hardening, `MP-356` process false-negative detection, `MP-162/174` ASCII separator parity, then the bounded `MP-359` live-session proof for the desktop shell.
3. Keep unrelated control-plane or staging work parked unless a new blocker appears in the active queue above.
4. No staging or push. Human approval is still required before any `git add`, commit, or push.

## Plan Alignment

- Current execution authority for this slice is `dev/active/autonomous_control_plane.md`, `dev/active/review_channel.md`, `dev/active/memory_studio.md`, and the mirrored MP rows in `dev/active/MASTER_PLAN.md`.
- Theme follow-up remains separate and is not part of the current scope.

## Last Reviewed Scope

- `code_audit.md`
- `AGENTS.md`
- `DEV_INDEX.md`
- `app/README.md`
- `app/operator_console/README.md`
- `app/operator_console/state/models.py`
- `app/operator_console/state/snapshot_builder.py`
- `app/operator_console/run.py`
- `app/operator_console/ui.py`
- `dev/README.md`
- `dev/active/INDEX.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/operator_console.md`
- `dev/active/review_channel.md`
- `dev/scripts/README.md`
- `dev/scripts/checks/check_active_plan_sync.py`
- `dev/scripts/checks/check_bundle_workflow_parity.py`
- `dev/scripts/checks/check_multi_agent_sync.py`
- `dev/scripts/checks/check_review_channel_bridge.py`
- `dev/scripts/devctl/commands/hygiene_audits_adrs_backlog.py`
- `dev/scripts/devctl/commands/process_watch.py`
- `dev/scripts/devctl/commands/review_channel.py`
- `dev/scripts/devctl/process_sweep.py`
- `dev/scripts/devctl/process_sweep_scans.py`
- `dev/scripts/devctl/review_channel.py`
- `dev/scripts/devctl/tests/test_check_review_channel_bridge.py`
- `dev/scripts/mutants_config.py`
- `dev/scripts/mutants_git.py`
- `dev/scripts/mutants_results.py`
- `dev/scripts/mutants_runner.py`
- `rust/src/bin/voiceterm/dev_command/action_catalog.rs`
- `rust/src/bin/voiceterm/dev_command/broker.rs`
- `rust/src/bin/voiceterm/dev_command/command_state.rs`
- `rust/src/bin/voiceterm/dev_command/review_artifact.rs`
- `rust/src/bin/voiceterm/dev_panel/cockpit_page/mod.rs`
- `rust/src/bin/voiceterm/dev_panel/review_surface.rs`
- `rust/src/bin/voiceterm/event_loop/dev_panel_commands/git_snapshot.rs`
- `rust/src/bin/voiceterm/event_loop/dev_panel_commands.rs`
- `rust/src/bin/voiceterm/event_loop/dev_panel_commands/review_loader.rs`
- `rust/src/bin/voiceterm/event_loop/dev_panel_commands/snapshots.rs`
- `rust/src/bin/voiceterm/event_loop/periodic_tasks.rs`
- `rust/src/bin/voiceterm/event_loop/input_dispatch/overlay/overlay_mouse.rs`
- `rust/src/bin/voiceterm/event_loop/tests.rs`
