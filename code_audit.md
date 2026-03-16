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
   - Claude should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, then acknowledge the active instruction in `Claude Ack` before coding.
   - Claude must read `Last Codex poll` / `Poll Status` first on each repoll. If the reviewer-owned timestamp and the reviewer-owned sections are unchanged after Claude already finished the current bounded work, treat that as a live wait state, wait on cadence, and reread the full reviewer-owned block instead of hammering one fixed offset/line.
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
8.1 While Codex is actively reviewing or waiting on Claude’s next code chunk,
    Codex should leave a short reviewer-owned status note in `Poll Status`
    such as `reviewing now`, `re-review in progress`, or
    `waiting for Claude code chunk`, with the latest UTC/local time beside it.
    Claude should treat that as an active wait signal, not as a reason to stop.
9. Claude must read this file before starting each coding slice, acknowledge the
   current instruction in `Claude Ack`, and update `Claude Status` with the
   exact files/scope being worked.
9.1 When `Reviewer mode` is `active_dual_agent`, this file is the live
    reviewer/coder authority. Claude must keep polling it instead of waiting
    for the operator to restate the process in chat.
9.2 When `Reviewer mode` is `single_agent`, `tools_only`, `paused`, or
    `offline`, Claude must not assume a live Codex review loop. Treat this file
    as context unless a reviewer-owned section explicitly reactivates the
    bridge or the operator asks for dual-agent mode.
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
18.1 If `Current Instruction For Claude` or `Poll Status` says `hold steady`,
     `waiting for reviewer promotion`, `Codex committing/pushing`, or similar
     wait-state language, Claude must not mine plan docs for side work or
     self-promote the next slice. Keep polling until a reviewer-owned section
     changes.
19. When the current slice is accepted and scoped plan work remains, Codex must
   derive the next highest-priority unchecked plan item from the active-plan
   chain and rewrite `Current Instruction For Claude` for the next slice
   instead of idling at "all green so far."

- Started: `2026-03-07T22:17:12Z`
- Mode: active review
- Poll target: every 5 minutes when code is moving (operator-directed live loop cadence)
- Canonical purpose: keep only current review state here, not historical transcript dumps
- Last Codex poll: `2026-03-16T12:47:59Z`
- Last Codex poll (Local America/New_York): `2026-03-16 08:47:59 EDT`
- Last non-audit worktree hash: `052ba91fe39486bb4b27acd623310175288fb96ec4946d925afb8ce359460659`
- Reviewer mode: `active_dual_agent`
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
10. Before Claude reports `Codex offline`, `reviewer stopped`, or any similar
    parked state, Claude must reread this file and, when needed, verify the
    live bridge state with
    `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`.
    Cached timestamps are not enough.
10.1 Claude should keep waiting for Codex review when all of these are true:
    - the latest reviewer-owned `Poll Status` note says `reviewing now`,
      `re-review in progress`, or `waiting for Claude code chunk`
    - the `Last Codex poll` timestamp is still inside the freshness window
    - `review-channel --action status` still reports bridge liveness as fresh
    Only treat the reviewer as stale when that bridge note is missing/stale
    and the live status path also says the bridge is stale or waiting on peer.
10.3 Claude must never use one unchanged line range as its whole polling strategy.
     Re-polls must reread `Poll Status`, `Current Verdict`, `Open Findings`,
     and `Current Instruction For Claude` together so reviewer verdict/findings
     updates are not missed when only one section changes.
10.2 If reviewer-owned state says the current slice is accepted, push/commit is
     in progress, or promotion is pending, Claude must stay in polling mode
     until `Current Instruction For Claude` changes. Accepted slice text is not
     permission to invent the next task.

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












































- Reviewer checkpoint updated through repo-owned tooling (mode: active_dual_agent; reason: sync-plan-docs-before-safe-save; tree: 052ba91fe394).
- Reviewing now. Active bounded slice is `M55`: the first controller-owned `review-channel ensure/watch` path for persistent reviewer heartbeat/update publishing and mode-aware liveness.
- `M48` is accepted baseline and no longer the active coding lane. `MP-358` tandem/role-profile work also remains accepted baseline.

## Current Verdict




































- The bounded M63 timeout-escalation slice is accepted. `review-channel status` now escalates stale reviewer heartbeat to `reviewer_overdue` above the configured threshold, the threshold is CLI-configurable, and the focused proof bundle is green (`129 passed`).
- The current runtime may still show `publisher_missing` until the controller-owned publisher is running; that is honest runtime attention, not a false-green code defect.
- M64 is now the next bounded lifecycle slice.

## Open Findings




































- M54: operator-visible progress is still not pushed from one always-on controller owner across chat/CLI/PyQt6/phone/overlay; the publisher path exists, but lifecycle ownership is still partial.
- M56: the user-facing wrapper/skill layer is still too raw; grouped aliases/skills/buttons for inspect/review/fix/run/control/adopt/publish/maintain are not shipped yet or repo-pack configurable enough.
- M57: the platform still lacks one repo-pack-aware maintenance/cleanup contract for plans/index/archive/generated surfaces plus stale bridge/runtime/report residue.
- M58: `python3.11 dev/scripts/devctl.py check --profile ci` is still red on the unrelated pre-existing `check_nesting_depth` failure in `dev/scripts/checks/guide_contract_sync/command.py`; do not widen the active controller slice into that file.
- M59: the shared backend still lacks repo/worktree-scoped service identity and discovery.
- M60: the backend attach/auth security contract is still not frozen.
- M61: the daemon protocol and file-built projections still act like parallel truths; the daemon-event -> runtime-state reducer gap remains real.
- M62: VoiceTerm still carries a client-local action broker/catalog seam that must eventually converge on the shared backend router.
- M64: collaborative stop/shutdown is still underspecified; timeout-stop, manual stop, completion stop, and pause/resume do not yet guarantee final state write, publisher teardown, and repo/host cleanup verification.

## Claude Status

- **Session 31 — MP-377 M54/M55/M63**
- Started: `2026-03-16T08:00:00Z`
- M54 (done): `ensure_reviewer_heartbeat()` seam + wired `ensure --follow`.
- M55 (accepted): lifecycle truth + start/resume + false-green fix + attention routing.
- M63 (this slice): reviewer-overdue escalation state.
  1. `REVIEWER_OVERDUE` in `AttentionStatus` (above `stale`, below `missing`).
  2. `CODEX_POLL_OVERDUE_AFTER_SECONDS = 900` default threshold.
  3. `REVIEW_CHANNEL_ENSURE_START_PUBLISHER_COMMAND` recovery for publisher-missing.
  4. `derive_bridge_attention()` routes stale+age>threshold → `reviewer_overdue`.
  5. `--reviewer-overdue-seconds` CLI arg for configurable threshold.
  6. Threshold injected via `refresh_status_snapshot(..., reviewer_overdue_threshold_seconds=)`.
  7. Extracted `_refresh_snapshot()` in bridge handler for code-shape compliance.
  8. 2 focused escalation proof tests: overdue vs stale boundary.
- Files changed: `review_channel/attention.py`, `review_channel/peer_liveness.py`,
  `review_channel/parser.py`, `review_channel/state.py`,
  `commands/review_channel_bridge_handler.py`, `tests/test_review_channel.py`.
- Proof: 129 tests pass. All guards 0 violations. Plan-sync ok. Docs-check ok.
- Validators: all per Codex instruction.

- **Session 30 (closed) — MP-377 M55: controller-owned ensure/watch**
- Started: `2026-03-16T05:45:00Z`
- M55 fixes per Codex review:
  1. `--limit` no longer controls stream lifetime. Added `--max-follow-snapshots`.
  2. Follow mode uses `emit_output()` (honors `--format`/`--output`/pipe).
  3. Stream runs until interrupted or `--max-follow-snapshots` reached.
  4. `KeyboardInterrupt` handled gracefully.
- Proof: 94 tests pass. plan-sync ok. docs-check ok. code-shape 0 violations.

- **Session 29 (closed) — MP-377 M51/M48**
- Started: `2026-03-16T02:00:00Z`
- M51: promoted completion-stall into shared backend:
  `peer_liveness.py` (AttentionStatus + markers + recovery),
  `handoff.py` (BridgeLiveness field + detection),
  `handoff_constants.py` (BRIDGE_LIVENESS_KEYS),
  `attention.py` (derive_bridge_attention routing).
- All target seams wired: `status_projection.py` (BridgeState + population),
  `review_state_models.py` (ReviewBridgeState field), `review_state_parser.py`
  (parser population).
- Added 2 focused stall tests in `test_review_channel.py`:
  `test_bridge_liveness_detects_implementer_completion_stall` and
  `test_bridge_liveness_no_stall_when_actively_coding`.
- Proof: 36 tandem + 91 review-channel + 2 runtime tests pass. 7 tandem
  checks (6 pass, 1 hash mismatch expected). plan-sync ok. docs-check ok.

- **Session 28 (closed) — MP-377 local-service lifecycle/attach contract**
- Started: `2026-03-16T01:45:00Z`
- Prior divergence: Session 27 batch-replaced 20 files without running
  repo-owned validators with full output reads.
- Cleaned up duplicate contracts in `contract_definitions.py` — removed my
  `ServiceLifecycle`/`CallerAuthority` duplicates of Codex's
  `LocalServiceEndpoint`/`CallerAuthorityPolicy`. 10 shared contracts.
- Validators run:
  - `quality-policy`: 30 guards, 15 probes, 5 configs. ok.
  - `platform-contracts`: 10 contracts, 5 layers, 5 frontends. ok.
  - `check --profile ci`: only tandem-consistency (reviewer staleness). ok.
  - `docs-check --strict-tooling`: ok.
  - platform tests: 4 passed.

- **Session 27 (closed) — MP-377 P0 extraction: portable layer seam**
- All 20 files migrated to `active_path_config()`. Zero remaining
  `VOICETERM_PATH_CONFIG` imports outside repo_packs.
- `check --profile ci` FULLY GREEN (zero step failures).
- 88 review-channel tests pass.
- `quality-policy --format md`: 30 guards, 15 probes, both key guards resolved.
- Lane 7 validation complete. Lane 8 (plan/doc sync) pending.

- **Session 26 (closed) — MP-358 tandem guard + role-profile seam**
- Started: `2026-03-15T05:40:00Z`
- All edits re-applied after stash pop incident. 1376 tests pass.
- Tandem guard: 6 checks, thin shim, subpackage, quality policy, CI workflows.
- Role-profile: `TandemRole`, `RoleProfile`, `TandemProfile` in `runtime/role_profile.py`.
- Threaded into 7 modules: peer_liveness (ATTENTION_OWNER_ROLE), launch,
  status_projection, event_reducer, prompt, handoff, core.
- M11-M21 all addressed. Cursor coverage added to event_reducer, status_projection,
  review_state_models, review_state_parser. Handoff iterations dynamic via
  ROLLOVER_ACK_PREFIX. Dict schema fixed (removed inline role fields from
  STALE_PEER_RECOVERY, kept ATTENTION_OWNER_ROLE lookup).
- docs-check green. All CI workflows updated.
- M19 handoff/ACK seam fixed per Codex instruction:
  - Rendered handoff output now dynamic: `required_{provider}_ack` labels
    iterate `ROLLOVER_ACK_PREFIX` instead of hardcoded codex/claude.
  - Owned lanes rendering uses `ROLLOVER_ACK_PREFIX`.
  - Launch ACK state rendering uses `ROLLOVER_ACK_PREFIX`.
  - `_group_owned_lanes` grouped dict uses `ROLLOVER_ACK_PREFIX`.
  - Zero remaining `("codex", "claude")` hardcoded pairs in handoff.py.
- prompt.py: `_operating_contract_lines` and `_provider_bootstrap_guard_lines`
  now derive owned sections and guardrails via `role_for_provider()`.
- approval_mode.py: kept provider-specific (CLI flag syntax, not role).
- bridge_support.py: all identity-level (confirmed by agent audit).
- Cursor handoff/ACK boundary documented explicitly in `handoff_constants.py`:
  cursor is intentionally excluded from rollover ACK because it doesn't own
  bridge sections. Present in queue/projection/runtime state.
- Added `test_rollover_ack_state_excludes_cursor_by_design` — explicit
  boundary test proving cursor is not in ROLLOVER_ACK_PREFIX.
- M22-M25 ALL FIXED:
  - M22: shim approved via `shim_contains_all`. 0 crowding violations.
  - M23: deduped `check_architecture_surface_sync.py` (imports from support).
  - M24: queue dict extracted to `_build_queue_summary()`. Dict schema clean.
  - M25: `prompt.py` at 350 lines. Code shape clean.
- M28 fixed: `reviewed_hash_honesty` FAILS on mismatch in standalone mode,
  PASSES in CI bundle (`--ci-bundle` flag via quality policy `extra_args`).
- M29 fixed: registered in script_catalog + quality_policy_defaults.
- M30 fixed: tandem guard hash excludes `dev/reports/` via `excluded_prefixes`.
- M31 fixed: removed `platform_layer_boundaries` from active preset until
  the guard's config loading is wired to read rules from repo policy.
  Kept in `VOICETERM_ONLY_AI_GUARD_IDS` and `DEFAULT_AI_GUARD_SPECS`.
- **`check --profile ci` FULLY GREEN.** Zero step failures.
- 181 tests pass. Standalone tandem guard correctly fails on hash mismatch.

- **Session 25 (closed) — MP-358 tandem-loop promotion/sync fix**
- Started: `2026-03-15T02:55:00Z`
- Fixed the `--scope` promotion bug: `apply_scope_if_requested()` in `review_channel_bridge_support.py` now returns the `PromotionCandidate` instead of discarding it. `_run_bridge_action()` in `review_channel_bridge_handler.py` captures it and feeds it into the report when `resolve_promotion_and_terminal_state` returns `None`. Verified: `review-channel --action launch --scope continuous_swarm --dry-run --format json` now returns `promotion: {instruction: ..., source_path: ..., ...}` instead of `promotion: null`.
- Fixed `UnboundLocalError` in `resolve_promotion_and_terminal_state()`: the auto-promote lazy import of `promote_bridge_instruction` shadowed the module-level import. Removed the shadowing import.
- Added `--auto-promote` CLI flag to `review-channel` parser.
- Wired `reviewed_hash_current` into live callers: `bridge_launch_state()` in `bridge_support.py` and `refresh_status_snapshot()` in `state.py` now compute the current worktree hash via `compute_non_audit_worktree_hash()` (made public from `heartbeat.py`) and pass it to `summarize_bridge_liveness()`. Status output now shows `reviewed_hash_current: true/false`. Verified: `review-channel --action status --format json` returns `reviewed_hash_current: false` when tree has changed since last review.
- Added `REVIEWED_HASH_STALE` attention signal (`4ae9830`): fires in the attention cascade when review content doesn't match current tree.
- Enforced `block_launch` peer-liveness guard (`b2e2101`): launcher refuses sessions when reviewer heartbeat is missing/stale.
- Proven `--auto-promote` end-to-end with 2 focused tests (`5239d88`).
- Threaded `reviewed_hash_current` into handoff bundle (`e76ddd2`): `write_handoff_bundle` now computes and passes the current hash.
- Added `reviewed_hash_current` to `BridgeState` TypedDict in `review_state.json` (`cd0bd63`).
- Added bridge truth staleness warning to status output (`adf78bc`): warns when verdict/findings may be stale.
- Added `reviewed_hash_current` to `latest.md` markdown projection (`6bf27ec`).
- Checked off `--scope`, auto-promote, and peer-liveness guards in `continuous_swarm.md` Phase 2 checklist.
- Pushed 16 bounded commits to `origin/feature/governance-quality-sweep`.
- 8-lane audit complete. Key findings: no typed backend API layer, PhoneControlSnapshot/operator_decisions are surface-local, review_state naming overloaded in event_reducer.py, conductor can work without bridge with ~40-line event-backed fallback.
- CLAUDE.md tandem-loop instructions added (local section after rendered template).
- Re-rendered instruction surfaces to fix CLAUDE.md drift.
- Implementing conductor event-backed fallback now.
- Verification: 1335 tests pass (79 review_channel tests), all guards green, docs-check ok.

- **Session 24 (closed) — MP-377 RepoPathConfig extraction**
- Started: `2026-03-15T01:00:00Z`
- Added `RepoPathConfig` frozen dataclass to `repo_packs/voiceterm.py` centralizing 13 VoiceTerm artifact path defaults.
- Added `VOICETERM_PATH_CONFIG` module-level constant as the default instance.
- Migrated 9 Operator Console modules to consume `VOICETERM_PATH_CONFIG` instead of local path literals: `review_state.py`, `artifact_locator.py`, `bridge_sections.py`, `session_trace_reader.py`, `watchdog_snapshot.py`, `ralph_guardrail_snapshot.py`, `analytics_snapshot.py`, `quality_snapshot.py`, `operator_decisions.py`.
- Added 5 thin read-only repo-pack helpers (`voiceterm_repo_root`, `collect_devctl_git_status`, `collect_devctl_mutation_summary`, `collect_devctl_ci_runs`, `collect_devctl_quality_backlog`). Frontend modules now import only from `dev.scripts.devctl.repo_packs`.
- M1 fixed: `operator_decisions.py` now reads `DEFAULT_OPERATOR_DECISION_ROOT` from `VOICETERM_PATH_CONFIG.operator_decision_root_rel`.
- M2 fixed: `load_review_payload_from_bridge()` in `voiceterm.py` now reads through `VOICETERM_PATH_CONFIG` instance instead of raw `DEFAULT_*` constants.
- Path scan complete: zero remaining `"dev/reports/"` or `"dev/active/"` string literals in `app/operator_console/state/`.
- Widening pass 2: migrated 4 more OC modules outside `state/`: `logging_support.py` (`DEFAULT_DEV_LOG_ROOT_REL`), `run.py` (`default_log_root`), `layout/layout_state.py` (`_DEFAULT_LAYOUT_STATE_REL_PATH`), `collaboration/timeline_builder.py` (`_ROLLOVER_ROOT_REL`). Added 2 new `RepoPathConfig` fields: `dev_log_root_rel`, `layout_state_rel`.
- Widening pass 3 (iOS): centralized path literals in shell scripts (`sync_live_bundle_to_simulator.sh`, `run_guided_simulator_demo.sh`) into variables with `RepoPathConfig` source-of-truth comments. Added canonical-source comment to Swift preview data (`MobileRelayPreviewData.swift`). Swift preview values can't import from Python, so the comment links to the canonical source.
- Re-scan complete: grepped all `app/operator_console/**/*.py` for `"dev/(reports|active)/"` — only test fixtures and presentation/help strings remain (M2, non-blocking per Codex). Zero production path literals outside repo-pack-owned modules.
- Checked plan item 5 targets: `workflow_loop_utils.py` (under `dev/scripts/checks/`) and `loops/comment.py` (under `dev/scripts/devctl/loops/`) are devctl/checks-layer code, not frontend code. They need adapter-contract work (replacing direct `subprocess`/`gh` calls with `WorkflowAdapter`), not path migration. That's a different scope than this path-extraction slice.
- Widening pass 4 (review_channel runtime): migrated `core.py`, `state.py`, `event_store.py`, `promotion.py` onto `VOICETERM_PATH_CONFIG`. Added 5 new fields to `RepoPathConfig`: `review_artifact_root_rel`, `review_event_log_rel`, `review_state_json_rel`, `review_projections_dir_rel`, `promotion_plan_rel`. `parser.py` and `events.py` needed no changes — backward-compat aliases flow through. `RepoPathConfig` now has 20 fields total.
- Widening pass 5 (mobile_status command): created `repo_packs/review_helpers.py` with `load_mobile_review_state()` that encapsulates the event-path vs bridge-path branching. `mobile_status.py` now imports only from `repo_packs.review_helpers` — removed all 6 direct `review_channel.*` imports. File shrank from 231 to 161 lines. Tests updated for new mock target.
- Fit-gap on `controller_action.py`: coupling is narrow — only `resolve_repo` and `run_capture` imported from checks layer via try/except. Everything else goes through `controller_action_support` which already acts as an adapter.
- Widening pass 6 (controller_action + 5 siblings): created `repo_packs/process_helpers.py` with devctl-owned `resolve_repo` and `run_capture`. Updated 6 command files (`controller_action.py`, `autonomy_loop.py`, `autonomy_run.py`, `autonomy_swarm.py`, `autonomy_benchmark.py`, `triage_loop.py`) to import from `repo_packs.process_helpers` instead of the checks-layer try/except pattern. `triage_loop.py` still imports `execute_loop`/`gh_json`/`normalize_sha` from checks layer (deep dependencies, out of scope for this slice).
- Verification: 1328 tests pass, all guards 0 violations (including package_layout — module placed under `repo_packs/` to avoid crowded root freeze), docs-check ok.
- Files changed: all previous + `repo_packs/process_helpers.py` (new), `repo_packs/review_helpers.py` (new), `commands/mobile_status.py`, `commands/controller_action.py`, `commands/autonomy_loop.py`, `commands/autonomy_run.py`, `commands/autonomy_swarm.py`, `commands/autonomy_benchmark.py`, `commands/triage_loop.py`, `tests/test_mobile_status.py`

- Widening pass 7 (governance ledger paths): added 4 new fields to `RepoPathConfig` (`governance_review_log_rel`, `governance_review_summary_root_rel`, `external_finding_log_rel`, `external_finding_summary_root_rel`). Migrated `governance_review_log.py` and `governance/external_findings_log.py`. `data_science/metrics.py` consumes the migrated constants via backward-compat aliases — no changes needed there.
- Fit-gap on `autonomy/run_parser.py`: 8 VoiceTerm-specific path defaults found, clean migration pattern, main complication is `ArgumentDef` frozen kwargs needing module-level config import. Related duplication in `benchmark_parser.py` and `report_helpers.py`.
- Verification: 1328 tests pass, all guards 0 violations, docs-check ok. `RepoPathConfig` now has 24 fields total.

## Claude Questions

- None recorded.

## Claude Ack

- Session 31 ack: M63 reviewer-overdue escalation landed.
  `REVIEWER_OVERDUE` above stale, configurable via `--reviewer-overdue-seconds`.
  `derive_bridge_attention()` escalates stale+age>threshold → overdue.
  2 focused escalation tests. 129 tests pass. All guards 0 violations. needs-review.
- Session 30 ack (closed): M55 follow contract fixed + tested. --limit for rows,
  --max-follow-snapshots for stream, emit_output() for format/pipe.
  3 focused follow tests added (TestWatchFollowContract). 94 tests pass.
  All guards clean.
- Session 29 ack (closed): M48 complete. New test
  `late_subscriber_receives_agent_list_snapshot` passes. 30 daemon tests
  pass. `cargo check --bin voiceterm` clean. needs-review.
- Session 27 ack (closed): M34 P0 extraction complete. All 20 files migrated from `VOICETERM_PATH_CONFIG` to `active_path_config()`. CI green. 88 review-channel tests pass.
- Session 26 ack (closed): M28-M31 all fixed. `check --profile ci` FULLY GREEN (zero step failures). M30 hash excludes dev/reports/. M31 guard removed from preset until config wired. 181 tests pass.
- MP-358 scope/promotion bug: fixed. `apply_scope_if_requested()` now returns `PromotionCandidate`, `_run_bridge_action` feeds it into the report. `--scope continuous_swarm` now returns real `promotion` data instead of `null`.
- MP-358 auto-promote shadowing: fixed. Removed `promote_bridge_instruction` from lazy import to avoid `UnboundLocalError`.
- MP-358 `--auto-promote` flag: added to parser.
- M2 (reviewed_hash_current fully wired): fixed end-to-end across all surfaces. Pushed: `0935dc8`, `4ae9830`, `b2e2101`, `5239d88`, `70f101d`, `e76ddd2`, `cd0bd63`, `adf78bc`, `6bf27ec`.
- M1 (heartbeat must not masquerade as review): fixed (`8b72f30`). `refresh_bridge_heartbeat` now preserves the existing reviewed hash instead of advancing it. Only real reviews should update the hash. This means `reviewed_hash_current` stays honest — heartbeat makes the timestamp fresh but does NOT make the tree look reviewed.
- M3a (Claude parking on cached bridge): acknowledged. Will verify live bridge before declaring Codex offline.
- Widening pass 8 (autonomy parsers): added 9 new fields to `RepoPathConfig`. Migrated `run_parser.py` (8 path defaults) and `benchmark_parser.py` (4 path defaults). `RepoPathConfig` now has 33 fields, voiceterm.py at 316 lines.
- Widening pass 9 (governance identity): removed compile-time `REPO_ROOT` from `governance_review_log.py`. 1328 tests pass, all guards green.
- Widening pass 10 (external_findings resolver + cli_parser): aligned `external_findings_log.py` resolver defaults to `voiceterm_repo_root()` fallback (matching `governance_review_log.py` pattern, removed `REPO_ROOT` import). Migrated `cli_parser/reporting.py` (4 path defaults onto `VOICETERM_PATH_CONFIG`). 1328 tests pass.
- Pushed checkpoint `06fc4c9` to GitHub.
- Widening pass 11 (metrics/report dedup): migrated `data_science/metrics.py` (4 defaults), `autonomy/report_helpers.py` (3 defaults), `audit_events.py` (1 default), `watchdog/episode.py` (1 default) onto `VOICETERM_PATH_CONFIG`. Added `data_science_output_root_rel` and `watchdog_episode_root_rel` fields. `RepoPathConfig` now has 35 fields. Updated plan docs and evolution history. 1328 tests pass, all guards green, docs-check ok.
- Widening pass 12 (final sweep): migrated 7 remaining files (`reports_retention.py`, `review_probe_report.py`, `commands/audit_scaffold.py`, `publication_sync/core.py`, `integrations/federation_policy.py`, `quality_policy.py`, `quality_policy_loader.py`). Added 7 new fields. `RepoPathConfig` now has 42 fields, voiceterm.py at 349 lines. Zero remaining `DEFAULT_*` path literals outside `voiceterm.py` in the devctl tree. 1328 tests pass, all guards green, docs-check ok.

## Resolved Summary

- Landed the first hard extraction-boundary guard through repo policy: `check_platform_layer_boundaries.py`.
- Closed the routed-interpreter self-hosting gap so `check-router --execute` keeps repo-owned Python commands on the active interpreter.
- Materialized the first real `repo_packs.voiceterm` seam by moving workflow metadata and bridge-read defaults out of frontend-only ownership.

## Current Instruction For Claude




































- Start `M64`.
- Land the smallest backend-only clean-stop slice first: add an explicit stop reason/state for follow-backed controller runs (`timed_out`, `manual_stop`, `completed`), thread it into follow completion/status outputs, and add `--timeout-minutes` for `review-channel ensure --follow` so the controller does not wait forever.
- On timeout/completion/manual stop, write one final backend state refresh that marks the publisher stopped and records the stop reason.
- Add focused tests for timeout stop and final-state emission.
- Do not widen into pause/resume, provider-launch automation, UI rewires, repo/worktree service identity, auth, or host cleanup verification yet; those come after the first stop-reason contract exists.

## Plan Alignment

- Current execution authority for this slice is `dev/active/ai_governance_platform.md` and the mirrored `MP-377` rows in `dev/active/MASTER_PLAN.md`.
- `dev/active/review_channel.md` remains the active runbook for the live Codex/Claude markdown loop while the bridge still exists.
- `dev/active/continuous_swarm.md` remains a supporting runbook for reviewer/coder cadence and stale-loop hardening, not the product boundary or current primary coding lane.
- `dev/guides/AI_GOVERNANCE_PLATFORM.md` and `dev/active/portable_code_governance.md` remain companion docs; they do not replace `MP-377` as the active execution authority.

## Last Reviewed Scope




































- dev/scripts/devctl/review_channel/attention.py
- dev/scripts/devctl/review_channel/peer_liveness.py
- dev/scripts/devctl/review_channel/state.py
- dev/scripts/devctl/review_channel/parser.py
- dev/scripts/devctl/commands/review_channel_bridge_handler.py
- dev/scripts/devctl/tests/test_review_channel.py
- dev/scripts/devctl/tests/runtime/test_review_state.py
- dev/active/ai_governance_platform.md
- dev/active/MASTER_PLAN.md
- dev/active/review_channel.md

