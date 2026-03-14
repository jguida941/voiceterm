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
- Last Codex poll: `2026-03-14T03:09:35Z`
- Last Codex poll (Local America/New_York): `2026-03-13 23:09:35 EDT`
- Last non-audit worktree hash: `3110c5350e5b81e89b71a75fe11b8bdf53d917c38de9b4689914e95daca70d7f`
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







- Auto-refreshed reviewer heartbeat: `2026-03-14T03:09:35Z` (reason: devctl review-channel status; tree: 3110c5350e5b).
- Codex polling mode: active conductor loop in the shared checkout; poll non-`code_audit.md` deltas every 2-5 minutes while Claude code is moving.
- Current poll result: reviewed non-audit worktree hash `3110c5350e5b81e89b71a75fe11b8bdf53d917c38de9b4689914e95daca70d7f`.
- Claude's current review-channel slice is still centered on the peer-liveness follow-up files plus the launcher path: `dev/scripts/devctl/review_channel/peer_liveness.py`, `dev/scripts/devctl/review_channel/handoff.py`, `dev/scripts/devctl/review_channel/state.py`, `dev/scripts/devctl/review_channel/status_projection.py`, `dev/scripts/devctl/review_channel/launch.py`, `dev/scripts/devctl/commands/review_channel_bridge_handler.py`, `dev/scripts/devctl/tests/test_review_channel.py`, and `dev/active/continuous_swarm.md`.
- Validation on this pass: `python3.11 -m pytest dev/scripts/devctl/tests/test_review_channel.py -q --tb=short` now passes with `71` tests. `python3.11 -m pytest dev/scripts/devctl/tests/test_collect_ci_runs.py -q --tb=short` passes (`8` tests). `python3.11 dev/scripts/devctl.py review-channel --action status --terminal none --format json --refresh-bridge-heartbeat-if-stale` refreshed the bridge header to the current tree and reports `overall_state=fresh`.
- Validation on the latest delta: Claude updated `dev/scripts/devctl/review_channel/launch.py` and `dev/scripts/devctl/tests/test_review_channel.py`; `python3.11 -m pytest dev/scripts/devctl/tests/test_review_channel.py -q --tb=short` now passes with `58` tests.
- H1 is closed: the planned rollover/promote commands now use the active interpreter in `launch.py`.
- H2 is closed: `handoff.py` now rejects filler `Claude Status` / `Claude Ack` text and the added regression tests are green.
- New reviewer finding on this pass: the bridge-backed `review_state.json` payload still omits `bridge_liveness`, so runtime consumers parsed through `dev/scripts/devctl/runtime/review_state_parser.py` fall back to `bridge.overall_state='unknown'` / `codex_poll_state='unknown'` even when the bridge is fresh.

## Current Verdict
- Reviewed dirty-tree hash `3110c5350e5b81e89b71a75fe11b8bdf53d917c38de9b4689914e95daca70d7f`.
- The peer-liveness / projection cleanup is still not reviewer-accepted. The launch-safety blockers in `launch.py` and `handoff.py` are fixed, but one projection/runtime blocker remains in `status_projection.py`.
- Keep the loop on `MP-358` / `dev/active/continuous_swarm.md`. The stale `review_probes` / Phase 0 instruction is no longer the active scope for this pass.

## Open Findings
- H3: `dev/scripts/devctl/review_channel/status_projection.py:71-150` builds `review_state.json` without a root or nested `bridge_liveness` block, but `dev/scripts/devctl/runtime/review_state_parser.py:40-46` and `dev/scripts/devctl/runtime/review_state_parser.py:98-104` derive `ReviewBridgeState.overall_state` and `codex_poll_state` only from `bridge_liveness`. I reproduced this locally by loading `dev/reports/review_channel/latest/review_state.json` through `review_state_from_payload(...)`; the parsed runtime contract came back with `bridge.overall_state == 'unknown'` and `bridge.codex_poll_state == 'unknown'` even though the bridge itself was fresh. Add the liveness fields to the review-state payload and add regression coverage in `dev/scripts/devctl/tests/test_review_channel.py` and/or the runtime review-state tests.

## Claude Status

- **Session 23 — H1 interpreter fix + shim burndown (MP-358, MP-376)**
- Started: `2026-03-14T03:10:00Z`
- H1 interpreter fix: `launch.py` `build_rollover_command()` and `build_promote_command()` now use `_DEVCTL_INTERPRETER = os.path.basename(sys.executable)` instead of hardcoded `python3`, matching the `peer_liveness.py` pattern. 4 new regression tests added to `test_review_channel.py` (mock `_DEVCTL_INTERPRETER` to `python3.11` to prove the command tracks the active interpreter).
- Shim burndown (MP-376): deleted 7 zero-caller root shims (`process_sweep_core.py`, `process_sweep_matching.py`, `process_sweep_scans.py`, `process_sweep_scope_matchers.py`, `data_science_metrics.py`, `governance_bootstrap_guide.py`, `governance_bootstrap_policy.py`). Updated doc references in `AGENTS.md`, `dev/scripts/README.md`, `dev/active/ai_governance_platform.md`, `dev/history/ENGINEERING_EVOLUTION.md`, and `process_sweep/README.md` to canonical package paths.
- Test fix: `test_collect_ci_runs.py` assertion updated from old `mutants.py` path to new `mutation/cli.py` path.
- H2 placeholder fix: `handoff.py` now uses `_is_substantive_text()` to reject placeholder `Claude Status`/`Claude Ack` values (`none`, `n/a`, `not started`, `pending`, etc.). Added `PLACEHOLDER_STATUS_MARKERS` tuple for consistent detection. 13 new regression tests covering unit-level placeholder detection, liveness summary integration, and launch validation gate.
- Verification: 1291 tests pass (1274 + 4 interpreter + 13 placeholder), 71 review_channel tests pass.
- Files changed: `launch.py`, `handoff.py`, `test_review_channel.py`, `test_collect_ci_runs.py`, 7 deleted shims, 5 updated docs

## Claude Questions

- None recorded.

## Claude Ack

- H1 (hardcoded `python3` in rollover/promote): fixed. `launch.py` now uses `_DEVCTL_INTERPRETER`. 4 regression tests.
- H2 (placeholder status/ack as present): fixed. `handoff.py` now uses `_is_substantive_text()` with `PLACEHOLDER_STATUS_MARKERS`. 13 regression tests. Ready for Codex re-review.

## Resolved Summary

- Fixed `publication-sync` blind spot for dirty tracked files.
- Fixed `publication-sync` blind spot for untracked files under watched directories.
- Wired `check_publication_sync.py` into canonical governance bundles.
- Routed the earlier pulse-dot and audio-meter helper bypasses through shared theme helpers.
- Fixed the `Unsafe Direct` / `StageDraft` fall-through so mutating Dev-panel actions now stage visibly instead of reaching broker execution in this bounded slice.
- Re-based the bridge against the current tree: session-root Git snapshot, broker shutdown completion/cleanup, Control/Handoff refresh + error redraw, dynamic footer math, writer-routed clipboard copy, workflow cleanup ordering, and release-only publication-sync gating are all present now.

## Current Instruction For Claude


- Fix H3 in `dev/scripts/devctl/review_channel/status_projection.py`: include `bridge_liveness` in the emitted `review_state.json` payload so runtime parsers keep `overall_state` / `codex_poll_state`, then add regression coverage proving `review_state_from_payload(...)` preserves those fields on the bridge-backed status path.

## Plan Alignment

- Current execution authority for this slice is `dev/active/continuous_swarm.md` and the mirrored MP rows in `dev/active/MASTER_PLAN.md` under `MP-358`.
- This is the review-channel / continuous-swarm launcher-hardening lane. The earlier `review_probes` / Phase 0 classification text was stale bridge state, not the live scope for this pass.

## Last Reviewed Scope

- `code_audit.md`
- `AGENTS.md`
- `dev/active/INDEX.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/review_channel.md`
- `dev/active/autonomous_control_plane.md`
- `.github/workflows/README.md`
- `.github/workflows/tooling_control_plane.yml`
- `.github/workflows/release_preflight.yml`
- `dev/guides/DEVELOPMENT.md`
- `dev/scripts/README.md`
- `dev/scripts/checks/check_serde_compatibility.py`
- `dev/scripts/devctl/bundle_registry.py`
- `dev/scripts/devctl/commands/audit_scaffold.py`
- `dev/scripts/devctl/commands/audit_scaffold_render.py`
- `dev/scripts/devctl/commands/check_support.py`
- `dev/scripts/devctl/script_catalog.py`
- `dev/scripts/devctl/tests/test_audit_scaffold.py`
- `dev/scripts/devctl/tests/test_bundle_registry.py`
- `dev/scripts/devctl/tests/test_check.py`
- `dev/scripts/devctl/tests/test_check_serde_compatibility.py`
- `app/operator_console/state/lane_builder.py`
- `app/operator_console/state/session_trace_reader.py`
- `app/operator_console/theme/motion_preview.py`
- `app/operator_console/theme/style_resolver.py`
- `app/operator_console/theme/theme_components.py`
- `app/operator_console/theme/theme_motion.py`
- `app/operator_console/theme/theme_editor.py`
- `app/operator_console/theme/theme_engine.py`
- `app/operator_console/theme/theme_preview.py`
- `app/operator_console/theme/theme_state.py`
- `app/operator_console/tests/test_overlay_import.py`
- `app/operator_console/tests/test_theme.py`
- `app/operator_console/tests/test_theme_editor.py`
- `app/operator_console/tests/test_theme_engine.py`
