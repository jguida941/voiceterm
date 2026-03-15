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
- Last Codex poll: `2026-03-15T03:13:28Z`
- Last Codex poll (Local America/New_York): `2026-03-14 23:13:28 EDT`
- Last non-audit worktree hash: `e4a75a4e2230c99663581d877ca367305163e402c1ee308eb1c47a7abe5fb1bd`
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


- Reviewer heartbeat refreshed at `2026-03-15T03:13:28Z` (local `2026-03-14 23:13:28 EDT`) for reviewed non-audit tree `e4a75a4e2230c99663581d877ca367305163e402c1ee308eb1c47a7abe5fb1bd`.
- The latest accepted code slice is now `86b902c` on `origin/feature/governance-quality-sweep`: `fix: return promotion candidate from --scope and wire --auto-promote (MP-358)`.
- The bounded `MP-377` path-extraction checkpoint is no longer the active task. The committed checkpoint is already on `origin/feature/governance-quality-sweep` at `0e10073` (`feat: complete RepoPathConfig path extraction across devctl tree (MP-377)`).
- Codex polling mode remains active conductor loop in the shared checkout; poll non-`code_audit.md` deltas every 2-3 minutes while Claude code is moving and do not park on a completed slice.
- Current active reviewer scope is now `MP-358` / `dev/active/continuous_swarm.md`, with `dev/active/review_channel.md` as the active runbook and `dev/active/operator_console.md` as a consumer/launchpad companion, not the conductor authority.
- Current audit result: the repo already has more of the tandem path than the stale bridge prose admitted. `review-channel --action launch` already supports `--scope`, the bridge refresh path exists, session artifacts exist, launch waits for a fresh Codex poll, and `swarm_run --continuous` is already the documented hands-off runner.
- Dry-run proof is green on the current code path:
  `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format json --scope continuous_swarm --refresh-bridge-heartbeat-if-stale`
  and
  `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json --refresh-bridge-heartbeat-if-stale`
  both returned `ok: true`, emitted session/projection paths, and kept bridge attention healthy.
- The `promotion: null` defect is now closed by `86b902c`: `apply_scope_if_requested()` returns the `PromotionCandidate`, `_run_bridge_action()` feeds it into the report, and `--auto-promote` is now wired into the parser/bridge action path.
- The real remaining gap is still end-to-end continuity, not missing primitives: automatic next-task promotion is only partially landed, reviewer heartbeat/session truth can still drift away from `Current Verdict` / `Open Findings` / `Current Instruction For Claude`, and stale-peer recovery/liveness are still not proven as a closed tool contract.
- New in-progress audit result: the follow-up `reviewed_hash_current` liveness signal exists in the dirty tree (`handoff.py`, `handoff_constants.py`, tests), and launch/status already thread the current worktree hash into `summarize_bridge_liveness(...)`. The remaining gap is that attention, warnings, handoff/report payloads, and other recovery surfaces do not use the new signal yet, so the bridge truth is only partially improved.
- Operator Console / PyQt is real and interconnected, but only as a launchpad/observer over repo-owned `review-channel` / `swarm_run` artifacts and commands. It must keep consuming the shared control-plane truth instead of becoming a second conductor implementation.

## Current Verdict
- Reviewed dirty-tree hash `e4a75a4e2230c99663581d877ca367305163e402c1ee308eb1c47a7abe5fb1bd`.
- `MP-377` path extraction is checkpointed and pushed. The repo-pack boundary work remains valid and reviewer-accepted; do not reopen that lane unless `MP-358` needs a narrow helper/facade follow-up.
- Direction remains reviewer-approved: keep hardening the internal boundary first, then package/split later. Do not do a mechanical repo extraction yet.
- The live blocker is now the tandem-loop contract, not missing path extraction. The current bridge was still telling Claude to finish a checkpoint that is already on `origin`, which is exactly the manual drift `MP-358` is supposed to eliminate.
- The repo-native tandem path is partially built, not absent. `review-channel --action launch` already has `--scope` plus heartbeat-refresh/support plumbing, and the launch path already fails closed when a fresh reviewer heartbeat never appears. `swarm_run --continuous` already exists as the intended hands-off runner.
- `86b902c` is reviewer-accepted for its bounded scope: the `--scope` launch report now returns a real promotion payload, and the `--auto-promote` entrypoint exists.
- What is not done yet: automatic next-task promotion is not yet proven end-to-end, bridge truth does not yet move heartbeat/hash/verdict/findings/instruction/session state together, and stale-peer recovery/liveness is still more documented intent than enforced tool contract.
- The current dirty-tree follow-up is directionally correct but incomplete: `reviewed_hash_current` is now available in live liveness for launch/status paths, but until attention/recovery/report surfaces consume it consistently, it still does not change the operator-facing behavior enough to close bridge-truth sync.
- Operator Console / PyQt should stay attached to the shared runner surfaces as a consumer/launcher shell. It is not the active loop authority right now and should not fork launcher/promoter logic out of `devctl`.
- The iOS preview/config slice remains partial, but it is not the active blocker for the continuous-runner work.

## Open Findings
- M1: `86b902c` closed the `promotion: null` bug, but automatic next-task promotion is still only partially landed. The loop is still not proven to continue across accepted slices without an external relaunch/prove step.
- M2: The new `reviewed_hash_current` liveness field is only partially wired into real behavior. Launch/status already pass `current_worktree_hash=...`, but attention, warnings, handoff/report payloads, and recovery surfaces still do not use the signal consistently.
- M3: Bridge truth sync remains open. `code_audit.md`, `latest.md`, `review_state.json`, session metadata, and any attention/recommended-action surface need to move together when reviewer state changes.
- M4: Peer-liveness and stale-peer recovery are still open. Claude should not start coding from stale review state, and Codex should not keep issuing fix cycles on stale Claude state without an explicit tool-owned waiting/recovery path.
- M5: `continuous_swarm.md` should now be updated narrowly to reflect what really landed: `--scope` is done, `--auto-promote` is partial, and bridge-truth sync / peer recovery remain open.
- M6: Keep Operator Console attached to the shared runner surfaces. Any MP-358 changes should reuse `review-channel` / `swarm_run` commands and artifacts rather than clone the orchestration inside PyQt.
- M7: Keep the iOS preview/config cleanup marked partial. Do not declare it closed while `MobileRelayPreviewData.swift` still duplicates literals.

## Claude Status

- **Session 25 — MP-358 tandem-loop promotion/sync fix**
- Started: `2026-03-15T02:55:00Z`
- Fixed the `--scope` promotion bug: `apply_scope_if_requested()` in `review_channel_bridge_support.py` now returns the `PromotionCandidate` instead of discarding it. `_run_bridge_action()` in `review_channel_bridge_handler.py` captures it and feeds it into the report when `resolve_promotion_and_terminal_state` returns `None`. Verified: `review-channel --action launch --scope continuous_swarm --dry-run --format json` now returns `promotion: {instruction: ..., source_path: ..., ...}` instead of `promotion: null`.
- Fixed `UnboundLocalError` in `resolve_promotion_and_terminal_state()`: the auto-promote lazy import of `promote_bridge_instruction` shadowed the module-level import. Removed the shadowing import.
- Added `--auto-promote` CLI flag to `review-channel` parser.
- Wired `reviewed_hash_current` into live callers: `bridge_launch_state()` in `bridge_support.py` and `refresh_status_snapshot()` in `state.py` now compute the current worktree hash via `compute_non_audit_worktree_hash()` (made public from `heartbeat.py`) and pass it to `summarize_bridge_liveness()`. Status output now shows `reviewed_hash_current: true/false`. Verified: `review-channel --action status --format json` returns `reviewed_hash_current: false` when tree has changed since last review.
- Verification: 1333 tests pass (77 review_channel tests), all guards green, bridge guard ok.

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

- MP-358 scope/promotion bug: fixed. `apply_scope_if_requested()` now returns `PromotionCandidate`, `_run_bridge_action` feeds it into the report. `--scope continuous_swarm` now returns real `promotion` data instead of `null`.
- MP-358 auto-promote shadowing: fixed. Removed `promote_bridge_instruction` from lazy import to avoid `UnboundLocalError`.
- MP-358 `--auto-promote` flag: added to parser.
- M2 (reviewed_hash_current not wired): fixed. Both `bridge_launch_state()` and `refresh_status_snapshot()` now pass `current_worktree_hash` to `summarize_bridge_liveness()`. The signal is live in status/launch output.
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


- `86b902c` is reviewer-accepted for the bounded `promotion: null` / `--auto-promote` slice. Do not reopen that exact bug.
- Keep the active lane on `MP-358` / `dev/active/continuous_swarm.md`.
- Use multiple Claude lanes now:
  1. one lane for bridge-truth sync code,
  2. one lane for focused tests/proof,
  3. one lane for plan/runbook/doc sync once the code gap is closed.
- Next concrete implementation target is the currently in-progress `reviewed_hash_current` follow-up. Finish wiring it end-to-end instead of leaving it as a dead field plus tests.
- Audit and patch the existing repo-owned tandem path in:
  `dev/scripts/devctl/review_channel/handoff.py`,
  `dev/scripts/devctl/review_channel/handoff_constants.py`,
  `dev/scripts/devctl/review_channel/state.py`,
  `dev/scripts/devctl/review_channel/attention.py`,
  `dev/scripts/devctl/review_channel/status_projection.py`,
  `dev/scripts/devctl/commands/review_channel_bridge_support.py`,
  `dev/scripts/devctl/commands/review_channel_bridge_handler.py`,
  and any narrow helpers/tests needed around them.
- Required behavior:
  - keep the current non-`code_audit.md` worktree hash threaded through every bridge-truth surface that needs it,
  - surface `reviewed_hash_current` through the real bridge status/projection path,
  - make attention/recommended-action/report/handoff state honest when the reviewed hash is stale even if the timestamp is fresh,
  - keep the bridge/projection path aligned with the same current-hash truth instead of only exposing it in tests.
- After the signal is live, prove it with focused tests plus a typed status/launch proof. If the signal changes attention or warnings, keep Operator Console consuming that shared truth instead of adding GUI-only logic.
- Update `dev/active/continuous_swarm.md`, `dev/active/review_channel.md`, and `dev/active/MASTER_PLAN.md` when this behavior lands so the plan matches the code.
- After a bounded green slice, commit and push the checkpoint to GitHub before widening the tree again.
- Minimum validation after edits:
  - `python3 -m pytest dev/scripts/devctl/tests/test_review_channel.py -q --tb=short`
  - `python3 -m pytest dev/scripts/devctl/tests/test_autonomy_run.py -q --tb=short`
  - `python3 dev/scripts/checks/check_review_channel_bridge.py --format md`
  - `python3 dev/scripts/checks/check_active_plan_sync.py`
  - `python3.11 dev/scripts/devctl.py docs-check --strict-tooling`

## Plan Alignment

- Current execution authority for this slice is `dev/active/continuous_swarm.md` and the mirrored MP rows in `dev/active/MASTER_PLAN.md` under `MP-358`.
- `dev/active/review_channel.md` is the active runbook for the live Codex/Claude loop; `dev/active/operator_console.md` is a companion plan for the PyQt launchpad/observer surface and should stay aligned with the shared devctl runner instead of replacing it.
- `dev/active/ai_governance_platform.md` remains the architecture authority for the broader extraction effort under `MP-377`, but it is not the current coding lane for this md pass.

## Last Reviewed Scope

- `code_audit.md`
- `AGENTS.md`
- `dev/active/INDEX.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/ai_governance_platform.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`
- `dev/active/review_channel.md`
- `dev/scripts/devctl/review_channel/core.py`
- `dev/scripts/devctl/review_channel/state.py`
- `dev/scripts/devctl/review_channel/parser.py`
- `dev/scripts/devctl/review_channel/event_store.py`
- `dev/scripts/devctl/repo_packs/voiceterm.py`
- `app/operator_console/state/snapshots/analytics_snapshot.py`
- `app/operator_console/state/snapshots/quality_snapshot.py`
- `app/operator_console/state/review/review_state.py`
- `app/operator_console/state/review/artifact_locator.py`
- `app/operator_console/state/review/operator_decisions.py`
- `app/operator_console/state/bridge/bridge_sections.py`
- `app/operator_console/state/sessions/session_trace_reader.py`
- `app/operator_console/state/snapshots/phone_status_snapshot.py`
- `app/operator_console/state/snapshots/watchdog_snapshot.py`
- `app/operator_console/state/snapshots/ralph_guardrail_snapshot.py`
- `app/operator_console/state/repo/repo_state.py`
- `app/operator_console/logging_support.py`
- `app/operator_console/run.py`
- `app/operator_console/layout/layout_state.py`
- `app/operator_console/collaboration/timeline_builder.py`
- `app/ios/VoiceTermMobile/Sources/VoiceTermMobileCore/MobileRelayPreviewData.swift`
- `app/ios/VoiceTermMobileApp/sync_live_bundle_to_simulator.sh`
- `app/ios/VoiceTermMobileApp/run_guided_simulator_demo.sh`
- `app/operator_console/workflows/workflow_presets.py`
