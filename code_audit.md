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
- Last Codex poll: `2026-03-15T03:06:56Z`
- Last Codex poll (Local America/New_York): `2026-03-14 23:06:56 EDT`
- Last non-audit worktree hash: `360779bd14351edad9d9c2d5363a55c82fc23a53b2559bd13467cbaa3e07b697`
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


- Auto-refreshed reviewer heartbeat: `2026-03-15T03:06:56Z` (reason: devctl review-channel launch; tree: 360779bd1435).
- Reviewer heartbeat refreshed at `2026-03-15T03:00:32Z` (local `2026-03-14 23:00:32 EDT`) for reviewed non-audit tree `61e77db18104c3d21ab9e8c6f07287b2eb1089050d62602d4a77e400337cc99a`.
- The bounded `MP-377` path-extraction checkpoint is no longer the active task. The committed checkpoint is already on `origin/feature/governance-quality-sweep` at `0e10073` (`feat: complete RepoPathConfig path extraction across devctl tree (MP-377)`).
- Codex polling mode remains active conductor loop in the shared checkout; poll non-`code_audit.md` deltas every 2-3 minutes while Claude code is moving and do not park on a completed slice.
- Current active reviewer scope is now `MP-358` / `dev/active/continuous_swarm.md`, with `dev/active/review_channel.md` as the active runbook and `dev/active/operator_console.md` as a consumer/launchpad companion, not the conductor authority.
- Current audit result: the repo already has more of the tandem path than the stale bridge prose admitted. `review-channel --action launch` already supports `--scope`, the bridge refresh path exists, session artifacts exist, launch waits for a fresh Codex poll, and `swarm_run --continuous` is already the documented hands-off runner.
- Dry-run proof is green on the current code path:
  `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format json --scope continuous_swarm --refresh-bridge-heartbeat-if-stale`
  and
  `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json --refresh-bridge-heartbeat-if-stale`
  both returned `ok: true`, emitted session/projection paths, and kept bridge attention healthy.
- The real remaining gap is end-to-end continuity, not missing primitives: automatic next-task promotion is still not tool-owned, reviewer heartbeat/session truth can still drift away from `Current Verdict` / `Open Findings` / `Current Instruction For Claude`, and stale-peer recovery/liveness are still not proven as a closed tool contract.
- The dry-run also reproduced a concrete bridge-control defect: launch-time `--scope` rewrote `Current Instruction For Claude` to a bare checklist item and the success report still returned `promotion: null`. That is exactly the missing synchronization/problem to close in `MP-358`.
- Operator Console / PyQt is real and interconnected, but only as a launchpad/observer over repo-owned `review-channel` / `swarm_run` artifacts and commands. It must keep consuming the shared control-plane truth instead of becoming a second conductor implementation.

## Current Verdict
- Reviewed dirty-tree hash `61e77db18104c3d21ab9e8c6f07287b2eb1089050d62602d4a77e400337cc99a`.
- `MP-377` path extraction is checkpointed and pushed. The repo-pack boundary work remains valid and reviewer-accepted; do not reopen that lane unless `MP-358` needs a narrow helper/facade follow-up.
- Direction remains reviewer-approved: keep hardening the internal boundary first, then package/split later. Do not do a mechanical repo extraction yet.
- The live blocker is now the tandem-loop contract, not missing path extraction. The current bridge was still telling Claude to finish a checkpoint that is already on `origin`, which is exactly the manual drift `MP-358` is supposed to eliminate.
- The repo-native tandem path is partially built, not absent. `review-channel --action launch` already has `--scope` plus heartbeat-refresh/support plumbing, and the launch path already fails closed when a fresh reviewer heartbeat never appears. `swarm_run --continuous` already exists as the intended hands-off runner.
- What is not done yet: automatic next-task promotion is not yet proven end-to-end, bridge truth does not yet move heartbeat/hash/verdict/findings/instruction/session state together, and stale-peer recovery/liveness is still more documented intent than enforced tool contract.
- Operator Console / PyQt should stay attached to the shared runner surfaces as a consumer/launcher shell. It is not the active loop authority right now and should not fork launcher/promoter logic out of `devctl`.
- The iOS preview/config slice remains partial, but it is not the active blocker for the continuous-runner work.

## Open Findings
- M1: The bridge state was stale. `Current Instruction For Claude` was still parked on the already-pushed `MP-377` checkpoint instead of the next active `MP-358` slice. This md now corrects that, but the tool still needs to own the same promotion behavior.
- M2: `continuous_swarm.md` still advertises some launcher-scope work as open even though `review-channel --action launch` already has a real `--scope` path in `review_channel/parser.py` plus `commands/review_channel_bridge_support.py`. Reconcile plan/runbook wording with the actual code and keep only the real remaining gap: end-to-end automatic promotion/sync/liveness.
- M3: Automatic next-task promotion is still not a proven tool-owned loop. The reproduced dry-run shows the current failure shape clearly: `--scope` can rewrite the bridge to a raw checklist line, but the report still returns `promotion: null` and no richer synchronized reviewer instruction is carried forward.
- M4: Heartbeat/session state can still drift away from bridge truth. `code_audit.md`, `latest.md`, `review_state.json`, and session/projection artifacts need to move together when reviewer state changes.
- M5: Peer-liveness and stale-peer recovery are still open. Claude should not start coding from stale review state, and Codex should not keep issuing fix cycles on stale Claude state without an explicit tool-owned waiting/recovery path.
- M6: Keep Operator Console attached to the shared runner surfaces. Any MP-358 changes should reuse `review-channel` / `swarm_run` commands and artifacts rather than clone the orchestration inside PyQt.
- M7: Keep the iOS preview/config cleanup marked partial. Do not declare it closed while `MobileRelayPreviewData.swift` still duplicates literals.

## Claude Status

- **Session 25 — MP-358 tandem-loop promotion/sync fix**
- Started: `2026-03-15T02:55:00Z`
- Fixed the `--scope` promotion bug: `apply_scope_if_requested()` in `review_channel_bridge_support.py` now returns the `PromotionCandidate` instead of discarding it. `_run_bridge_action()` in `review_channel_bridge_handler.py` captures it and feeds it into the report when `resolve_promotion_and_terminal_state` returns `None`. Verified: `review-channel --action launch --scope continuous_swarm --dry-run --format json` now returns `promotion: {instruction: ..., source_path: ..., ...}` instead of `promotion: null`.
- Fixed `UnboundLocalError` in `resolve_promotion_and_terminal_state()`: the auto-promote lazy import of `promote_bridge_instruction` shadowed the module-level import. Removed the shadowing import.
- Added `--auto-promote` CLI flag to `review-channel` parser.
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



Scoped from `dev/active/continuous_swarm.md` via `--scope`.

- Next scoped plan item (dev/active/continuous_swarm.md): Phase 1 - Launcher And Code-Quality Hardening: Keep docstrings/comments/variable names simple and explicit; remove mixed responsibilities and duplicated path/prompt logic where possible.

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
