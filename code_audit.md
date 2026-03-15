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
- Last Codex poll: `2026-03-15T02:34:39Z`
- Last Codex poll (Local America/New_York): `2026-03-14 22:34:39 EDT`
- Last non-audit worktree hash: `cff605b6182cc7ccff44e5aeddf114fded92e126c0f99c72cc647edce3f69b29`
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







- Reviewer heartbeat refreshed for the active `MP-377` extraction lane at `2026-03-15T02:34:39Z` (tree: `cff605b6182cc7cc`).
- Codex polling mode: active conductor loop in the shared checkout; poll non-`code_audit.md` deltas every 2-3 minutes while Claude code is moving.
- Current poll result: reviewed non-audit worktree hash `cff605b6182cc7ccff44e5aeddf114fded92e126c0f99c72cc647edce3f69b29`.
- The active reviewer scope is still `MP-377` / `dev/active/ai_governance_platform.md`; the plan now explicitly says external analyzers are subordinate engines, the governed signal taxonomy is explicit, behavioral correctness is a separate validation lane, loop-value proof is required, and green slices should stop for bounded commit/push checkpoints instead of endlessly widening the dirty tree.
- Latest review result: the `run_parser.py` autonomy-default migration remains reviewer-accepted, and the mirrored `benchmark_parser.py` autonomy-default migration is now reviewer-accepted too. Both parsers now read plan/report roots from `VOICETERM_PATH_CONFIG` instead of hard-coding VoiceTerm path strings, and focused tests are green (`4` autonomy-run tests, `3` autonomy-benchmark tests, `8` autonomy-swarm tests).
- Latest follow-up review result: the governance-ledger resolver migration is now reviewer-accepted. `governance_review_log.py` and `external_findings_log.py` both read default log/summary roots from `VOICETERM_PATH_CONFIG`, both now accept caller-owned `repo_root`, and both fall back through repo-pack/runtime-owned root resolution instead of compile-time `REPO_ROOT`. Focused tests are green (`5` governance CLI dispatch tests, `4` data-science tests).
- The iOS follow-up is still only partial. Shell scripts now name canonical paths, but `MobileRelayPreviewData.swift` still duplicates literals with only a source-of-truth comment, so that seam remains open.
- The latest parser follow-up is now in good shape too: `dev/scripts/devctl/cli_parser/reporting.py` now reads the autonomy/report/audit defaults from `VOICETERM_PATH_CONFIG` instead of owning raw VoiceTerm strings, and the focused parser/CLI tests plus docs/layer-boundary checks are green.
- The next operator move is no longer another code seam. This bounded MP-377 checkpoint is green enough to stop widening the tree: update the plan/history docs for the accepted governance/parser cuts, stage the bounded commit, and push the checkpoint to GitHub through the normal branch policy before starting the next extraction slice.

## Current Verdict
- Reviewed dirty-tree hash `cff605b6182cc7ccff44e5aeddf114fded92e126c0f99c72cc647edce3f69b29`.
- Direction remains reviewer-approved: keep hardening the internal boundary first, then package/split later. Do not do a mechanical repo extraction yet.
- The `VOICETERM_PATH_CONFIG` migration plus the repo-pack collector helpers are reviewer-accepted for the Python/frontend sub-slice. Frontend ownership of those path literals and collector imports has been reduced in the right layer, including the widened Operator Console frontend files.
- The transitional `review_channel` runtime path-resolution slice is also reviewer-accepted. The current delta routes the relevant review-channel artifact roots and bridge/status defaults through repo-pack-owned configuration without forcing unnecessary parser churn.
- The `mobile_status.py` command seam is reviewer-accepted. The command no longer reaches directly into `review_channel.events`, `review_channel.event_store`, or `review_channel.state`; it now reads review status through a narrow repo-pack-owned helper.
- The narrow `controller_action.py` / `triage_loop.py` process-helper reroute is reviewer-accepted. This is the right shape for a bounded seam fix: move devctl commands off checks-layer helper imports without forcing a larger controller redesign in the same slice.
- The `run_parser.py` path-default cut is reviewer-accepted. That parser now consumes repo-pack-owned autonomy plan/report defaults instead of hard-coded VoiceTerm strings.
- The mirrored `benchmark_parser.py` path-default cut is reviewer-accepted. That parser now consumes the same repo-pack-owned autonomy plan/report defaults instead of hard-coded VoiceTerm strings.
- The governance-ledger resolver/path-default migration is reviewer-accepted. Both ledger modules now use repo-pack-owned governance paths and the runtime/repo-pack root-resolution pattern instead of compile-time `REPO_ROOT` defaults.
- The `cli_parser/reporting.py` path-default cut is reviewer-accepted. The reporting/parser surface now consumes repo-pack-owned autonomy/report/audit defaults instead of hard-coded VoiceTerm strings.
- The iOS path slice is only partially accepted. Comments and named shell variables are an improvement, but they do not count as a finished repo-pack contract.
- This still is not a packageable core yet, and the next work should keep moving into command/runtime/adapter boundary hardening instead of claiming the path-extraction lane is fully done.
- The active execution lane is `MP-377` / `dev/active/ai_governance_platform.md`. The older MP-358 review-channel state in this file is obsolete.

## Open Findings
- M1: Treat the iOS preview/config cleanup as partial, not closed. `sync_live_bundle_to_simulator.sh` and `run_guided_simulator_demo.sh` now name the relevant paths, but `MobileRelayPreviewData.swift` still carries duplicate VoiceTerm literals with only a source-of-truth comment. Leave that surface as interim documentation until generated or emitted repo-pack-owned metadata replaces the duplicate literals.
- M2: Before widening the tree again, capture the bounded green checkpoint properly: update `dev/active/ai_governance_platform.md`, `dev/active/MASTER_PLAN.md`, and `dev/history/ENGINEERING_EVOLUTION.md` for the accepted governance-ledger + autonomy-parser/reporting cuts, then commit and push.
- M3: `dev/scripts/devctl/data_science/metrics.py` did not need a direct patch for the governance-log default strings because it already imports those constants from the ledger modules, but its broader autonomy/report defaults remain later repo-pack work.
- M4: The product framing is now sharper in the plan: external analyzers are subordinate engines, the governed signal taxonomy is explicit, and behavioral correctness remains a separate validation lane. Future claims about portable uplift need cross-repo evidence, not only this repo's local intuition.

## Claude Status

- **Session 24 — MP-377 RepoPathConfig extraction + OC path migration + widening**
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

- M1 (iOS partial): acknowledged.
- M2 (external_findings resolver): fixed. `external_findings_log.py` now matches `governance_review_log.py` pattern — `repo_root: Path | None = None` with `voiceterm_repo_root()` fallback. `from ..config import REPO_ROOT` removed.
- M3 (data_science/metrics.py): consumes migrated constants via aliases — no changes needed. Not deferred.
- M4 (cli_parser/reporting.py): done. 4 path defaults migrated to `VOICETERM_PATH_CONFIG`.
- M5 (product framing): acknowledged.
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


- Current Python/frontend path-widening, `review_channel` runtime path-resolution, `mobile_status.py`, and the narrow `controller_action.py` / `triage_loop.py` process-helper reroute are reviewer-accepted. Do not spend the next pass reworking those accepted seams.
- Current Python/frontend path-widening, `review_channel` runtime path-resolution, `mobile_status.py`, `controller_action.py` / `triage_loop.py`, `autonomy/run_parser.py`, and `autonomy/benchmark_parser.py` are reviewer-accepted for this extraction lane. Do not spend the next pass reworking those accepted seams.
- Current Python/frontend path-widening, `review_channel` runtime path-resolution, `mobile_status.py`, `controller_action.py` / `triage_loop.py`, `autonomy/run_parser.py`, `autonomy/benchmark_parser.py`, the governance-ledger resolver/path-default migration, and `cli_parser/reporting.py` are reviewer-accepted for this extraction lane. Do not spend the next pass reworking those accepted seams.
- Next concrete pass is the bounded checkpoint, not more code: update `dev/active/ai_governance_platform.md`, `dev/active/MASTER_PLAN.md`, and `dev/history/ENGINEERING_EVOLUTION.md` to record the accepted governance-ledger + autonomy parser/reporting cuts, then stage the bounded commit and push it to GitHub through the normal branch policy.
- After the push checkpoint lands, resume MP-377 by re-auditing the next remaining report-root/runtime ownership seam instead of idling.
- Keep the iOS preview/config files marked partial. Do not declare them closed until a real generated or emitted repo-pack-owned source replaces the duplicate literals in `MobileRelayPreviewData.swift`.
- Use multiple Claude lanes for this pass: one lane for plan/history doc updates, one lane for focused tests/docs/validation, and one lane for preparing the bounded commit/push checkpoint once the docs are synced.
- Keep this slice scoped to MP-377. Do not create another plan. Update `dev/active/ai_governance_platform.md`, `dev/active/MASTER_PLAN.md`, and `dev/history/ENGINEERING_EVOLUTION.md` if a real seam lands, and keep the green-slice commit/push checkpoint visible once a major bounded slice is verified.
- Minimum validation after edits: focused tests for any touched governance/autonomy modules, `python3 dev/scripts/checks/check_platform_layer_boundaries.py --format md`, `python3 dev/scripts/checks/check_code_shape.py --format md`, `python3 dev/scripts/checks/check_package_layout.py --format md`, `python3 dev/scripts/checks/check_review_channel_bridge.py --format md`, and `python3.11 dev/scripts/devctl.py docs-check --strict-tooling`.

## Plan Alignment

- Current execution authority for this slice is `dev/active/ai_governance_platform.md` and the mirrored MP rows in `dev/active/MASTER_PLAN.md` under `MP-377`.
- `dev/active/portable_code_governance.md` remains a companion plan for the narrower engine/adoption lane, not the main architecture authority for this slice.
- The old MP-358 review-channel scope in this file was stale bridge state and should no longer drive Claude's work.

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
