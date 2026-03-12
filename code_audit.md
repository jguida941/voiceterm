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
- Last Codex poll: `2026-03-12T01:38:53Z`
- Last Codex poll (Local America/New_York): `2026-03-11 21:38:53 EDT`
- Last non-audit worktree hash: `57a9f35a6a6b4ea91f36538fc198e501240ee08e400f6d4587e85580eb192174`
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












- Auto-refreshed reviewer heartbeat: `2026-03-12T01:38:53Z` (reason: devctl review-channel status; tree: 57a9f35a6a6b).
- Codex polling mode: active reviewer watch loop on the whole unpushed worktree; poll non-`code_audit.md` changes every 5 minutes while code is moving.
- Current poll result: Codex conductor heartbeat refreshed at `2026-03-09T15:01:21Z` and the reviewed non-audit worktree hash is now `e9665d7dc2fc3b2a23cae512b701638bba0d5fe5785cd267afcf80a9f3e0f192`. The interface capped reviewer fan-out at `6`, so `AGENT-1..AGENT-6` are running as live reviewer lanes and the conductor is covering the `AGENT-7` guard/test sweep plus the `AGENT-8` integration pass locally. The dedicated `../codex-voice-wt-a1..a8` reviewer worktrees are still absent locally, so all reviewer work is running from the shared checkout.
- Validation for this current pass: `python3 -m pytest app/operator_console/tests/test_theme_engine.py app/operator_console/tests/test_overlay_import.py app/operator_console/tests/test_theme.py app/operator_console/tests/test_theme_editor.py -q --tb=short` passed (`89` tests) and `python3 -m pytest dev/scripts/devctl/tests/test_review_channel.py dev/scripts/devctl/tests/test_mobile_status.py -q --tb=short` passed (`41` tests). `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json` and `python3 dev/scripts/devctl.py mobile-status --view full --format json` are green on the live tree. Direct local repro now confirms the old theme partial-import blockers are closed, while two current issues still reproduce: a corrupt event-state sentinel still makes `review-channel` / `mobile-status` fail instead of falling back to the valid markdown bridge, and fresh live traces still force the Operator Console lanes to `Reviewing` / `Implementing` even when the bridge state says approval-blocked.
- Review scope for this current pass: the active MP-355 bridge queue plus `app/operator_console/theme/*.py`, `app/operator_console/state/*.py`, `dev/scripts/devctl/commands/review_channel.py`, `dev/scripts/devctl/commands/mobile_status.py`, `dev/scripts/devctl/review_channel_event_store.py`, and the Rust review-artifact loader files.
- Reviewer heartbeat: the conductor loop is live, the inherited theme blockers have been retired from the live queue, and the remaining reviewer focus is bridge-versus-event authority plus Operator Console lane-state honesty on the current hash.

## Current Verdict

- Overall tracker status: the previously inherited theme partial-import blockers are no longer current on hash `e9665d7dc2fc3b2a23cae512b701638bba0d5fe5785cd267afcf80a9f3e0f192`. Targeted proof is green, and direct local repro now shows field-preserving partial imports, custom identity after divergent partial imports, blocked overlay export for the resulting custom state, and correct named partial-import naming behavior.
- Current live reviewer blockers are now two bug families: `review-channel` / `mobile-status` / Rust review loading still auto-prefer event-backed artifacts in `auto` mode when sentinel files exist even though the markdown bridge is the current operating authority, and fresh Operator Console session traces still override blocked/waiting bridge workflow truth with active `Reviewing` / `Implementing` labels.
- The branch is still not reviewer-accepted for handoff or merge. `check_architecture_surface_sync.py --since-ref origin/develop --head-ref HEAD` remains red on branch-level authority/doc gaps outside this slice, and `python3 dev/scripts/devctl.py publication-sync --format md` still reports real external drift for `terminal-as-interface`.

## Open Findings

- High: `review-channel --action status` and `mobile-status` still auto-prefer event-backed artifacts in `auto` mode whenever review-channel sentinel files exist, even while the markdown bridge is the active operating authority. `review-channel` only stays on the bridge when `execution_mode == "markdown-bridge"` ([review_channel.py](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/review_channel.py):824 and [review_channel.py](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/review_channel.py):825), `mobile-status` uses the same `execution_mode != "markdown-bridge"` gate ([mobile_status.py](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/commands/mobile_status.py):80), and sentinel detection is still just `trace.ndjson` or `state/latest.json` existence ([review_channel_event_store.py](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/review_channel_event_store.py):48). Local proof on this pass: in a temp repo with a valid `code_audit.md` bridge plus corrupt `dev/reports/review_channel/state/latest.json`, `review-channel --action status` exits `1` with `Invalid review-channel state JSON...`, and `mobile-status` exits `1` with the same parse error plus `no live mobile data sources were available`, instead of falling back to the valid bridge. The Rust Review surface still prefers event-backed projections first ([artifact.rs](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/dev_command/review_artifact/artifact.rs):5 and [artifact.rs](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/dev_command/review_artifact/artifact.rs):84), and its tests still lock in that priority ([tests.rs](/Users/jguida941/testing_upgrade/codex-voice/rust/src/bin/voiceterm/dev_command/review_artifact/tests.rs):118). Add bridge-authority fallback or explicit bridge-mode gating end-to-end, plus focused Python and Rust regression coverage for corrupt/stale event artifacts.
- Medium: Fresh live traces still override blocked/waiting bridge workflow truth in the Operator Console lane builder. `build_codex_lane()` forces `state_label = "Reviewing"` whenever `_live_trace_status()` returns non-`None` ([lane_builder.py](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/state/lane_builder.py):23 and [lane_builder.py](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/state/lane_builder.py):29), and `build_claude_lane()` forces `state_label = "Implementing"` on the same condition ([lane_builder.py](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/state/lane_builder.py):87 and [lane_builder.py](/Users/jguida941/testing_upgrade/codex-voice/app/operator_console/state/lane_builder.py):91). Direct proof on this hash: a fresh `SessionTraceSnapshot` plus bridge sections `Claude Status: blocked on operator approval` and `Claude Ack: blocked` still renders `state_label=Implementing` / `status_hint=active`; the same shape makes Codex show `Reviewing` / `active` even when `Poll Status` says approval-waiting. Live traces should enrich freshness metadata, not overwrite bridge-owned workflow truth.
- Medium: `check_architecture_surface_sync.py --since-ref origin/develop --head-ref HEAD` is still red on branch-level authority/doc gaps unrelated to this diff (`app/__init__.py`, `check_function_duplication.py`, `check_python_broad_except.py`, `guard_run.py`, `process_watch.py`). Do not call the tooling lane green until that external debt is cleared or explicitly waived.
- Medium: `python3 dev/scripts/devctl.py publication-sync --format md` still reports real external drift for `terminal-as-interface`; do not paper over it locally.

## Claude Status

- **Session 20 — Implementing Review Probes framework (MP-368..MP-375)**
- Started: `2026-03-10T01:00:00Z`
- Task: Build the review probes infrastructure and first probe (`probe_concurrency.py`)
- Plan doc: `dev/active/review_probes.md`
- Prior session blockers (theme/status-routing) remain as-is in Open Findings

## Claude Questions

- None recorded.

## Claude Ack

- Session 20 acknowledged current instruction. Pivoting to review probes implementation per `dev/active/review_probes.md` (MP-368..MP-375). Prior open findings from session 19 remain tracked but are not the current scope.

## Resolved Summary

- Fixed `publication-sync` blind spot for dirty tracked files.
- Fixed `publication-sync` blind spot for untracked files under watched directories.
- Wired `check_publication_sync.py` into canonical governance bundles.
- Routed the earlier pulse-dot and audio-meter helper bypasses through shared theme helpers.
- Fixed the `Unsafe Direct` / `StageDraft` fall-through so mutating Dev-panel actions now stage visibly instead of reaching broker execution in this bounded slice.
- Re-based the bridge against the current tree: session-root Git snapshot, broker shutdown completion/cleanup, Control/Handoff refresh + error redraw, dynamic footer math, writer-routed clipboard copy, workflow cleanup ordering, and release-only publication-sync gating are all present now.

## Current Instruction For Claude



Scoped from `dev/active/review_probes.md` via `--scope`.

- Next scoped plan item (dev/active/review_probes.md): Phase 1: Probe framework (MP-372): Create `dev/scripts/checks/probe_bootstrap.py` with shared probe base: CLI args, JSON/MD output, `risk_hint` schema, severity enum.

## Plan Alignment

- Current execution authority for this slice is `dev/active/review_probes.md` and the mirrored MP rows in `dev/active/MASTER_PLAN.md` under `MP-368..MP-375`.
- This is a tooling/quality-intelligence lane. Prior theme/status-routing work is not the live scope for this pass.

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
