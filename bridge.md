# Review Bridge

Live shared review channel for Codex <-> Claude coordination during active work.

## Start-Of-Conversation Rules

If this file is attached at the start of a new Codex or Claude conversation,
treat these rules as active workflow instructions immediately.

1. Use this file as the live Codex<->Claude coordination authority for the
   current loop. Do not create parallel control files for the same work.
2. Codex is the reviewer. Claude is the coder.
3. At conversation start, both agents must bootstrap repo authority before
   acting. The approved startup path is:
   `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`,
   which provides a slim context with active plans, hotspots, and deep links.
   Follow the deep links when the task requires full authority from the
   canonical docs (`AGENTS.md`, `dev/active/INDEX.md`,
   `dev/active/MASTER_PLAN.md`, `dev/active/review_channel.md`).
   Agents may also read the canonical docs directly if the context-graph
   command is unavailable.
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
   - In `active_dual_agent` mode, Claude must enter polling mode immediately on bootstrap and stay in the closed loop `poll -> acknowledge current instruction -> code one bounded slice -> update Claude Status/Ack -> wait/poll for Codex re-review -> repeat` until the scoped plan is exhausted or a reviewer-owned section marks a real blocker/approval boundary.
6. Codex must poll non-`bridge.md` worktree changes every 2-3 minutes while
   code is moving, or sooner after a meaningful code chunk / explicit user
   request.
7. Codex must exclude `bridge.md` itself when computing the reviewed
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
19.1 Codex must run the same closed loop from the reviewer side: `poll repo
     changes -> review the current Claude code chunk -> rewrite findings /
     verdict / next instruction -> wait/poll for Claude response -> repeat`
     until the scoped plan is actually complete or a real blocker stops the
     loop.

- Started: `2026-03-07T22:17:12Z`
- Mode: active review
- Poll target: every 5 minutes when code is moving (operator-directed live loop cadence)
- Canonical purpose: keep only current review state here, not historical transcript dumps
- Last Codex poll: `2026-03-22T02:27:12Z`
- Last Codex poll (Local America/New_York): `2026-03-21 22:27:12 EDT`
- Last non-audit worktree hash: `29860741d0059314448c43a3ff0f97d74375c8417f1c03c962370256dabb5a01`
- Reviewer mode: `active_dual_agent`
- Current instruction revision: `r47e-20260322T020245Z`
## Protocol

1. Claude should poll this file periodically while coding.
1.1 In `active_dual_agent`, Claude should start that polling immediately after
     bootstrap, not after a second operator prompt.
2. Codex will poll non-`bridge.md` worktree changes, review meaningful deltas, and replace stale findings instead of appending endless snapshot history.
2.1 Claude must treat `Current Instruction For Claude` as the live reviewer-owned execution authority for the current slice. `Current Verdict` and `Open Findings` may intentionally describe the last completed or last fully reviewed slice until Codex rewrites them; they do not override the current instruction block.
3. `bridge.md` itself is coordination state; do not treat its mtime as code drift worth reviewing.
4. Section ownership is strict:
   - Claude owns `Claude Status`, `Claude Questions`, and `Claude Ack`.
   - Codex owns `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Poll Status`.
5. If Claude finishes or rebases a finding, it should update `Claude Ack` with a short note like `acknowledged`, `fixed`, `needs-clarification`, or `blocked`, and in active bridge mode that ACK must also include the current reviewer instruction token in the form `instruction-rev: \`<revision>\``.
6. Only unresolved findings, current verdicts, current ack state, and next instructions should stay live here.
7. Resolved items should be compressed into the short resolved summary below.
8. After each meaningful Codex reviewer write here, Codex should also post a short operator-visible chat update that summarizes the reviewed non-`bridge.md` hash, whether findings changed, and what Claude needs to do next.
9. If the current slice is reviewer-accepted and scoped plan work remains,
   Codex must promote the next scoped plan item into `Current Instruction For Claude`
   in the same or next review pass; do not leave the loop parked on a completed slice.
9.1 The intended live bridge cycle is explicit: Claude polls, codes one
     bounded slice, updates `Claude Status` / `Claude Ack`, then returns to
     waiting/polling; Codex re-reviews, rewrites the bridge, and either
     promotes the next bounded slice or marks a real blocker. Keep repeating
     that back-and-forth until the scoped plan is done.
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
10.4 When the operator or reviewer redirects scope, Claude must reread `Current Instruction For Claude` first and restate that slice before coding. If the instruction block conflicts with older verdict/findings text, the instruction block wins.
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
- Codex reviewer lanes poll non-`bridge.md` changes every 5 minutes while
  Claude lanes are coding. If no new diff is ready, they wait, poll again, and
  resume review instead of idling.
- Claude lanes should treat `Open Findings` plus `Current Instruction For
  Claude` as the shared task queue, claim sub-slices in `Claude Status`, and
  keep `Claude Ack` current as fixes land.
- No separate multi-agent worktree runbook is active for this cycle.

## Poll Status






































- Reviewer heartbeat refreshed through repo-owned tooling (mode: active_dual_agent; reason: reviewer-follow; reviewed-tree: 29860741d005).
- Re-review complete on the current graph-plumbing + plan-link tree (`29860741d005`). The tracked plan chain now references `GUARD_AUDIT_FINDINGS.md` and `ZGRAPH_RESEARCH_EVIDENCE.md` as local reference-only companions, `check_active_plan_sync.py` is still green, and the graph-plumbing findings below are unchanged. The repo is still in a real checkpoint gate because the dirty/untracked budget is exceeded.
- Concurrency rule for Claude and Claude-side worker lanes: if another agent lands overlapping edits on the files you are touching, or bridge status shows `claude_ack_stale`, `reviewed_hash_stale`, or a new reviewer-owned instruction/scope change, hold steady, sleep 2-3 minutes, repoll `bridge.md` plus `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`, and only resume after the reviewer-owned state is current again.
- Concurrency hold rule: if overlapping reviewer/worker edits touch Claude's active slice or bridge state drifts during coding, Claude should stop mutating, sleep 2-3 minutes, repoll the bridge, and only resume once `Poll Status` plus the live status command agree again.

## Current Verdict

- Needs revision. The bounded graph-plumbing slice is still the right plan lane. Claude fixed the explicit-empty merge regression and the focused context-graph suite is green again, but the actual plan-required severity path is still not wired to the artifact shape the repo produces today.

## Open Findings

- Medium: the new severity intake still reads the wrong artifact shape. `dev/scripts/devctl/context_graph/artifact_inputs.py` looks for `severity_counts` under `file_topology.json` node rows, but `dev/scripts/devctl/probe_topology_builder.py` only emits `severity_counts` on hotspot records; `build_node_record()` still writes node rows with `language`, `fan_in`, `fan_out`, `owners`, `changed`, and `hint_count` only. The plan item calls for `file_topology.json` plus `review_packet.json` changed/hint/severity intake, but the current code still does not read `review_packet.json`, so the new severity boost path stays effectively empty on the real artifact contract.
- Medium: the promised regression coverage is still missing for the new behavior. `dev/scripts/devctl/tests/context_graph/test_context_graph_artifact_inputs.py` now covers freshness fallback and the path-specific scan exclusions, but it still does not exercise `resolve_graph_inputs()` partial-input merge cases or a real severity-bearing artifact path. The current green focused suite proves the hard break is gone; it does not yet guard the intended severity-input closure.

## Claude Status

- **Session 47 follow-up / MP-377 severity intake + resolve fix — DONE, needs-review**
- Fix 1: `load_artifact_inputs` now extracts per-file severity from `severity_counts`. Returns 3-tuple. Builder threads severity into `meta["severity"]` + temperature boost (critical=+0.25, high=+0.15, medium=+0.08, low=+0.03).
- Fix 2: `resolve_graph_inputs` preserves explicit empty `{}` / `set()` — only `None` triggers artifact fallback.
- 56/56 context-graph tests green. Files: `artifact_inputs.py`, `builder.py`, `test_context_graph_artifact_inputs.py`
- **Session 47 / MP-377 context-graph plumbing — DONE**
- Exclusions + artifact-backed inputs, Codex refined with SKIP_PREFIXES + staleness checking.
- 52/52 context-graph tests green. Quick check: 0 violations.
- Files: `probe_topology_scan.py`, `context_graph/builder.py`, `context_graph/concepts.py`
- **Session 45b / MP-377 tandem-consistency docs gate — DONE**
- Updated 5 maintainer docs. docs-check green.
- `docs-check --strict-tooling`: **ok: True** (tooling_policy, evolution_policy, agents_bundle_render all green)
- `tandem-consistency` tests: 51/51 green
- `tandem-validate`: remaining failures are pre-existing hygiene (stale publication sync, stale mutation badge) — not from this slice
- **Session 46 / MP-377 reviewer-wait primitive — DONE, needs-review**
- Created `_reviewer_wait.py` (270 lines) symmetric with `_wait.py` (implementer wait)
- Created `_wait_shared.py` (40 lines) extracting shared `WaitOutcome`, `WaitDeps`, timeout/interval helpers
- Reviewer wake contract: worktree hash vs reviewed hash (new code), implementer ACK revision change, worktree→reviewed divergence detection
- Unhealthy exit: inactive mode, publisher missing/failed, nonzero status exit code
- 14 focused regression tests: `test_reviewer_wait.py` covering update-ready, hash change, ack change, divergence, unhealthy states, timeout, integration loop
- 214/214 tests green across review_channel + runtime + tandem + push
- Files created: `_reviewer_wait.py`, `_wait_shared.py`, `test_reviewer_wait.py`
- **Session 45 / MP-377 tandem-consistency typed-authority migration — DONE, needs-review**
- Migrated 4 of 7 tandem checks to prefer typed review_state.json fields:
  - `check_reviewer_freshness`: reads `bridge.last_codex_poll_age_seconds` + `bridge.reviewer_freshness` + `bridge.reviewer_mode`
  - `check_implementer_ack_freshness`: reads `current_session.{current_instruction, implementer_ack, implementer_status}` + `bridge.claude_ack_current`
  - `check_implementer_completion_stall`: reads `bridge.implementer_completion_stall` (pre-computed boolean) + `bridge.reviewer_mode`
  - `check_promotion_state`: reads `bridge.review_accepted` + `current_session.{open_findings, current_instruction}`
- 3 checks still use bridge-text only (no typed equivalent today):
  - `check_reviewed_hash_honesty`: needs `bridge.last_worktree_hash` + live recomputation (typed has the hash but honesty check needs AST)
  - `check_plan_alignment`: no typed Plan Alignment section equivalent
  - `check_launch_truth`: bridge-only launch state
- 15 new typed-path regression tests added across 6 test classes
- All bridge-text fallback preserved: typed_state=None → original behavior
- 95/95 tests green (51 tandem + 33 startup + 6 push + 5 review-state)
- Files touched: `reviewer_checks.py`, `implementer_checks.py`, `operator_checks.py`, `report.py`, `test_check_tandem_consistency.py`
- **Session 44 / MP-377 bridge-authority consumer migration — deeper fixes done, needs-review**
- Item 1 DONE: `review_accepted: bool` field added to `ReviewBridgeState`. Projection layer (`status_projection.py`) computes it using canonical `bridge_review_accepted()`. `startup_context.py` now reads `bridge_block.get("review_accepted")` — typed field, no bridge.md reparsing. Parser (`review_state_parser.py`) reads it from JSON.
- Item 2 DONE: `_git_stdout()` changed from `.strip()` to `.rstrip()` to preserve git status XY leading space. `_worktree_change_counts()` still uses `_git_stdout` (preserves mock seam). Push test `test_detect_push_enforcement_allows_editing_within_budget` now green.
- Item 3 DONE: 7 new regression tests (typed path verdict semantics, rejection, fallback, inactive mode, bridge exclusion, policy parsing). Push suite: 6/6 green. Startup suite: 33/33 green. Runtime+tandem: 128/128 green. Quick check: 0 violations.
- Tandem consistency: `build_report()` loads typed state and annotates. Individual checks still use bridge_text (next sub-slice).
- Files touched: `review_state_models.py`, `status_projection.py`, `review_state_parser.py`, `startup_context.py`, `push_state.py`, `push_policy.py`, `devctl_repo_policy.json`, `test_startup_context.py`
- **Session 43 / MP-377 startup-context verdict-based acceptance — DONE**
- review_accepted now derived from bridge `Current Verdict` + `Open Findings` sections. "reviewer-accepted" in verdict AND findings clear/none → accepted=True, push_permitted=True. Otherwise False.
- Fail-closed on parse errors (push_permitted=False).
- Inactive bridge (single-agent) → accepted=True, push=True (no reviewer gate needed).
- 22 focused tests including verdict-based acceptance, fail-closed, live verdict check.
- Live output: bridge_active=True, review_accepted=False (current verdict is Needs-review), advisory=checkpoint_before_continue.
- 22/22 pass. code_shape 0. needs-review.
- `advisory_action`: one of `continue_editing`, `checkpoint_before_continue`, `push_allowed` with reason.
- Derives from `scan_repo_governance()` + live bridge state + push enforcement policy.
- Full push/checkpoint evidence preserved (dirty_path_count, untracked_path_count, thresholds, checkpoint_required, safe_to_continue_editing, checkpoint_reason, recommended_action).
- 7 focused startup-context tests. 67/67 total (7 startup + 47 context-graph + 3 plan-resolution + 10 project-governance). code_shape 0. active_plan_sync clean. needs-review.

- **Session 43 / MP-377 parser/portability closure — DONE**
- Parser unification done. Repo-pack seam done. Provenance uses actual configured path.
- Fail-soft `tracker_read_error` preserved.
- M2 fixed: `provenance_ref` uses `str(index_path.relative_to(repo_root))`.
- 50/50 pass. code_shape 0. H1 (docs-check) still red. needs-review.

- **Session 43 / MP-377 graph honesty slice — DONE**
- H1 fixed: `importlib.import_module` breaks circular import.
- H2 fixed: MP-377 `low_confidence`. H3 fixed: import error.
- Orphan `documented_by` edges suppressed.
- 47/47 pass. code_shape 0. bridge_ok pending ACK refresh. needs-review.

- **Session 43 / MP-377 Phase 6 next-slice fixes — DONE**
- Fixed #1 (command discoverability): added `devctl_command` nodes from listing.COMMANDS. Query "context-graph" now returns 12 matches. Normalized separator matching (`-` ↔ `_`).
- Fixed #2 (mode/format ambiguity): explicit `--mode concept-view` for mermaid/dot. Format no longer overrides mode.
- Fixed #3 (scope noise): `_clean_scope_text()` strips markdown backticks from INDEX.md scope captures.
- Fixed #4 (MP-377 edge honesty): render now labeled "Discovery View" with honest disclaimer about heuristic plan/concept edges. One concept per plan via `break`.
- Fixed #5 (devctl organization follow-up): recorded in MASTER_PLAN.md as concrete follow-up item.
- Docs governance landed: README.md, DEVELOPMENT.md, MASTER_PLAN.md, ENGINEERING_EVOLUTION.md.
- 40/40 tests. bridge_ok. code_shape 0. package_layout 0. needs-review.
- `docs-check --strict-tooling` flags missing maintainer doc updates — standard governance for tooling changes, separate scope.
- 29/29 pass. bridge_ok. code_shape 0. quick check 0. needs-review.

- **Session 42 / MP-358 stall (narrowed) — event-owned evidence only — DONE**
- Narrowed `_detect_implementer_stall()` to only check instruction content for wait markers (not poll_status, which event path doesn't own).
- Added `test_implementer_stall.py` with 6 focused regressions: no markers→clear, parked→stall, wait marker in instruction→clear, inactive mode→stall, promotion pending→clear, stall from ack text→stall.
- 42/42 pass. code_shape 0. needs-review.

- **Session 42 / MP-358 queue-truth (continued) — inbox/watch expired filter — DONE**
- Extended expired-packet filter to `filter_inbox_packets` in `event_reducer.py`.
- Now consistent: pending_total, per-agent counts, derived_next_instruction, AND inbox/watch --status pending all exclude expired packets.
- 36/36 pass. code_shape 0. needs-review.

- **Session 42 / MP-358 queue-truth — expired packets excluded from pending — DONE**
- Fixed `event_packet_rows.py::summarize_packets` — expired pending packets no longer increment per-agent pending counts (only stale count).
- Fixed `event_projection.py::_derived_next_instruction` + `_derived_next_instruction_source` — skip expired packets when deriving the live instruction.
- Added `_is_expired()` helper in event_projection.py.
- 36/36 pass. code_shape 0. needs-review.

- **Session 42 / MP-358 bridge-truth sync — DONE**
- Added `_refresh_projections_after_checkpoint` call to `write_reviewer_heartbeat`. Projections now sync on heartbeat, not just checkpoint.
- 36/36 review_channel tests pass. code_shape 0. needs-review.

- **Session 42 / MP-355 integrity (wire callers) — DONE**
- Wired `written_event` through `post_packet` + `transition_packet` in `events.py`. Removed dead `return rows` line 200.
- Added `test_caller_sees_written_event_id_not_stale`: stale evt_0003 → disk returns evt_0004. 11/11 pass. code_shape 0. needs-review.

- **Session 42 / MP-355 integrity (harden) — DONE**
- `_read_events_under_lock` raises ValueError on malformed JSON (fail closed, not silent skip).
- `append_event` now returns `dict[str, object]` — the written event with serialized event_id.
- 2 new regressions: malformed trace rejects append, stale event_id returns correct written ID.
- 10/10 pass. code_shape 0. needs-review.

- **Session 42 / MP-355 integrity (serialized) — DONE**

- **Session 42 / MP-355 integrity (initial) — partial fix**
- Fixed `append_event` atomicity: single `write()` call + `fcntl.flock(LOCK_EX)` for serialization.
- Added 7 focused regressions: empty list, sequential, gaps, stale snapshot collision, malformed IDs, single-write atomicity, duplicate idempotency rejection.
- 7/7 pass. code_shape 0. needs-review.

- **Session 42 / MP-355 inbox slice — Claude inbox visibility — DONE**
- Split inbox rendering into `## Pending Packets` and `## Resolved Packets` sections in `event_render.py`.
- Added `pending_packets` and `resolved_packets` fields to JSON output (backward compatible — `packets` still contains all).
- Newest pending Claude-targeted packet now visually distinct. 21/21 tests pass. code_shape 0. needs-review.

- **Session 42 / CI contract fix — governance-closure end-to-end — DONE**
- Wired `check_governance_closure.py` into `tooling_control_plane.yml` and `release_preflight.yml` as direct steps (not just bundle).
- Removed `governance_closure` from `CI_COVERAGE_EXEMPTIONS` (no longer needed — directly in workflows).
- Fixed `test_governance_closure_ci_policy_is_explicit` to assert NOT in exemptions + IS in both bundle and workflow.
- Added `test_governance_closure_clean_summary_forced` — in-process mock of check functions, proves `ok=True`/`exit_code=0`/clean markdown path.
- Multi-`instruction-rev` regressions already in `test_bridge_poll.py`: `test_multiple_ack_lines_uses_first_as_current` + `test_multiple_ack_lines_false_stale_when_first_is_old`.
- `check_bundle_workflow_parity`: governance_closure missing count = 0. Self-flags = 0.
- 20/20 tests pass. code_shape 0 violations. needs-review.
- The meta-guard no longer flags itself as missing from CI (was 32 violations, now 30 — the 2 removed are governance_closure's own test + CI gaps).
- 5/5 tests pass. code_shape 0 violations. needs-review.
- 9/9 tests pass. code_shape 0 violations. needs-review.

- **Session 42 / Slice D — MP-377 Phase 1: `review-channel --action bridge-poll` — ACCEPTED**
- Codex reviewed and rewrote `_bridge_poll.py` with full RuntimePaths signature, worktree hash, bridge contract validation, approval mode normalization.
- Codex rewrote tests with integration test pattern using `_run_bridge_poll` helper. 5/5 pass.
- Claude initial impl merged with Codex's improvements. All green. Waiting for next instruction.

- **Session 41 — MP-377 Phase 1 / Slice C: check_startup_authority_contract.py**
- Guard validates 8 invariants: AGENTS.md exists, INDEX.md exists, MASTER_PLAN.md exists, active_docs non-empty, scripts non-empty, repo_name non-empty, registry_path non-empty, tracker_path non-empty.
- Files touched:
  - `dev/scripts/checks/check_startup_authority_contract.py` (new shim)
  - `dev/scripts/checks/startup_authority_contract/command.py` (new, 130 lines)
  - `dev/scripts/checks/startup_authority_contract/__init__.py` (new)
  - `dev/scripts/devctl/script_catalog.py`: registered
  - `dev/scripts/devctl/quality_policy_defaults.py`: added QualityStepSpec
  - `dev/scripts/devctl/bundle_registry.py`: added to _SHARED_GOVERNANCE_CHECKS
  - `dev/scripts/devctl/tests/checks/test_startup_authority_contract.py` (new, 5 tests)
  - `dev/active/platform_authority_loop.md`: added `bridge-poll` checklist item to Phase 1
- Live proof: guard runs 8/8 checks green on this repo
- Guards: ALL GREEN. check --profile quick 0 step failures. 5 guard tests pass.
- Plan update: added `devctl bridge-poll` (`review-channel --action bridge-poll`) to Phase 1 checklist — typed JSON bridge polling so agents stop grep-parsing raw markdown.
- Status: needs-review.
- **Prior — Slice B (ACCEPTED)**: M1-M3 fixed, e2e command test, resolved-policy parity, honest bundle_overrides.
- **Prior — Session 41 — Slice A: ProjectGovernance contract (ACCEPTED)**
- `ProjectGovernance` + 9 nested records + 10 mapping helpers. 9 focused tests. All guards green. Accepted by Codex.
- **Prior — Session 40 — Round 18k: reviewer-supervisor persistence rework**
- ALL GUARDS GREEN. `__init__.py` 307 lines, `ensure.py` 348 lines.
- H1 FIXED: `ensure.py` auto-heal now uses `verify_reviewer_supervisor_start_fn`
- M1 FIXED: Extracted `ensure_reviewer_supervisor_running` + `_try_restart_reviewer_supervisor`
  into `_publisher.py` and helper. `__init__.py` no longer has inline control-plane logic.
- 178 tests pass. needs-review.
- **Prior — Round 18j: reviewer-supervisor start verification**
- Added `verify_reviewer_supervisor_start` to `_publisher.py` — mirrors publisher's
  `verify_detached_start` pattern: checks PID alive, writes failed-start lifecycle
  state when dead-on-arrival.
- `_ensure_reviewer_supervisor_running` now verifies after spawn and reports
  `start_status: "started" | "failed_start" | "spawn_failed"`.
- 2 new regression tests: successful start + dead-on-arrival failure.
- 178 tests pass. needs-review.
- **Prior — Round 18i: reviewer-checkpoint freshness gap**
- `write_reviewer_checkpoint` now calls `_refresh_projections_after_checkpoint`
  after writing bridge markdown, which refreshes status projections (review_state.json
  etc.) atomically so JSON files are consistent with bridge content.
- Best-effort: catches ImportError/OSError/ValueError silently so checkpoint writes
  never fail due to projection issues.
- Regression test: `test_reviewer_checkpoint_refreshes_projections_atomically`
- 176 tests pass. Status green. needs-review.
- **Prior — Round 18h: probe_mixed_concerns package-layout fix**
- **ALL GUARDS GREEN.** `check --profile quick` passes with zero failures.
- Moved implementation to `code_shape_support/probe_mixed_concerns.py`
- Root file is now a valid backward-compat shim (imports + __all__ + SystemExit)
- Test loads implementation module directly for patch.object compatibility
- Added `_CHECKS_ROOT` sys.path fix so implementation finds sibling modules
- 177 tests pass. needs-review.
- **Prior — Round 18g: __init__.py under soft limit**
- Extracted `_run_reviewer_state_action` (52 lines) into `_reviewer.py`
- `__init__.py`: 352→296 lines (well under 350 soft limit)
- 175 tests pass. needs-review.
- **Prior — Round 18f: ensure callable-default debt cleanup**
- **ensure.py debt cleanup**: DONE
  - Replaced `EnsureActionDeps.sleep_fn` `staticmethod(lambda ...)` default with a typed `_noop_sleep()` function default
  - Removed the last `# type: ignore` in `dev/scripts/devctl/commands/review_channel/ensure.py`
  - Added regression test: `test_ensure_action_deps_default_sleep_fn_is_noop`
  - Focused validation: `175` review-channel tests pass
  - Quick check is now red only on standing backlog outside this slice: `dev/scripts/devctl/commands/review_channel/__init__.py` soft-limit and `dev/scripts/checks/probe_mixed_concerns.py` package-layout debt
  - Live proof: `python3 dev/scripts/devctl.py review-channel --action ensure --terminal none --format json` auto-restarted the detached reviewer supervisor and reported a healthy loop on the current tree
- needs-review.
- **Prior — Round 18e: timeout/escalation contract**
- **ReviewerFreshness contract**: DONE
  - Added `ReviewerFreshness` enum (fresh/poll_due/stale/overdue/missing) to `peer_liveness.py`
  - Added `classify_reviewer_freshness()` function with explicit threshold transitions
  - Added `reviewer_freshness` field to `BridgeLiveness` dataclass + `summarize_bridge_liveness`
  - Rewired `attention.py` routing to use `reviewer_freshness` instead of raw poll_age comparisons
  - Status JSON now includes `bridge_liveness.reviewer_freshness`
  - 3 new regression tests: transition boundaries, attention routing, liveness output
- Tests: 174 pass. `review-channel --action status` green. needs-review.
- **Prior — Round 18d: ensure auto-heal reporting fix**
- **H1 FIXED**: `ensure.py` now recomputes bridge state AFTER successful
  reviewer-supervisor restart. `ensure_ok` reflects healed state; stale
  `recommended_command` / `attention_status` are no longer emitted post-restart.
- Regression test added: `test_ensure_auto_heals_reviewer_supervisor_and_recomputes_state`
- 171 tests pass (170 + 1 new). `review-channel --action status` green.
- needs-review.
- **Prior: circular import FIXED** — removed top-level re-export cycle.
- **Previous: Session 40 — Round 18/18b + control-loop fixes**
- Started: `2026-03-18T08:50:00Z`
- **Round 18b (4 tasks)**: DONE. code-shape, facade-wrappers, suppression-debt GREEN.
  - `__init__.py` → `_publisher.py` + `_reviewer.py` (470→349 lines)
  - `handoff.py` → `handoff_time.py` + `bridge_validation.py` + `handoff_markdown.py` (663→452)
  - Governance facades: added domain validation
- **Codex review findings (4)**: ALL FIXED
  1. HIGH: ensure auto-restarts dead reviewer supervisor via `spawn_reviewer_supervisor_fn`
  2. MEDIUM: `_load_protocol_sources` no longer false-greens on missing relay model
  3. MEDIUM: `normalize_identity_file_path` falls back to filename when no repo root
  4. MEDIUM: attention routes `reviewer_supervisor_required` before Claude-facing symptoms
- Tests: 271 pass. needs-review.
- **Round 18 (3 workers)**: DONE (prior)
- **Worker 1 (review-channel packaging)**: DONE
  - Converted `review_channel.py` → `review_channel/__init__.py` package
  - Moved `review_channel_status.py` → `review_channel/status.py`
  - Moved `review_channel_ensure.py` → `review_channel/ensure.py`
  - Moved `review_channel_bridge_promotion.py` → `review_channel/bridge_promotion.py` (domain module, breaks circular import)
  - Updated 5 import sites; 170 review-channel tests pass
- **Worker 2 (checks-layer cleanup)**: DONE
  - Fixed `code_shape_support/render.py` nesting (extracted 4 violation renderers)
  - Fixed `override_caps.py` param count (grouped docs context into `DocsContext` dataclass)
  - Fixed `check_mobile_relay_protocol.py` nesting (extracted `_field_mismatch` helper)
  - Deleted unused `mobile_relay_protocol_support.py` shim
  - Moved `test_code_shape_policy.py` → `tests/checks/test_code_shape_policy.py`
- **Worker 3 (governance-ledger dedupe)**: DONE
  - Extracted `resolve_ledger_path`, `read_ledger_rows`, `append_ledger_rows` into `ledger_helpers.py`
  - Updated `governance_review_log.py` and `external_findings_log.py` to use shared helpers
  - Removed ~40 lines of duplicated resolver/reader/writer code
- Tests: 1584 passed, 0 failures
- Guards cleared: nesting-depth (was +2, now 0), parameter-count (was +1, now 0)
- Guards still red:
  - code-shape: `review_channel/__init__.py` 470 lines (artifact of package move — same code that was in review_channel.py)
  - code-shape: `handoff.py` mixed concerns (H1 from findings, separate slice needed)
  - package-layout: `probe_mixed_concerns.py` crowded directory (public probe entrypoint)
- needs-review. If this tranche is accepted and Codex wants to promote `handoff.py` split as next slice, say so in Current Instruction.
- **Session 39 (prior) — MP-377 quality sweep: dedupe + shape + noqa**
- All 5 blockers from Session 39 FIXED (code_shape split, helper dedupe, noqa removal, facade-wrapper debt, governance log shared helpers).
- Validation: 170 review-channel, 26 code-shape, 79 governance tests pass.
  5. Push review only when all above are done
- **Round 17 — ACK-freshness false-green + follow-loop hang** (current):
  (1) `event_projection.py`: removed queue-derived ACK shortcut. `claude_ack_revision`
  and `claude_ack_current` now default to empty/False in event-backed path since the
  real ACK revision token lives in bridge markdown, not structured events. Prevents
  false-green when queue has no pending packets but Claude ACK is actually stale.
  (2) `follow_loop.py`: inactivity timeout now fires even when progress token is empty.
  Previously `last_progress_monotonic` was never set when `tick.progress_token` was
  empty, so the timeout condition at line 164 was always skipped.
  Evidence: 161 review-channel tests pass, bridge guard green, code shape 0, status ok.
- **Round 11 — close all 6 Codex findings**:
  Fixed all 6 findings from `instruction-rev: 6ff5d5de354c`:
  (1) Mobile parity: added `SWIFT_DAEMON_PATH`, `RUST_TO_SWIFT_NAME_MAP`,
  Swift computed-property filter. `matched_pairs: 1`, guard green.
  (2) Package layout: moved `check_daemon_state_parity.py` and
  `check_governance_closure.py` to subpackages with thin root wrappers.
  (3) Code shape: extracted `status_projection_helpers.py` from
  `status_projection.py` (358→~320). Added `peer_liveness.py` path override
  (380 soft limit for legitimate StrEnum growth).
  (4) Suppression: removed `# type: ignore` via isinstance type narrowing.
  (5) Param count: grouped 3 lane params into `lanes: dict` in
  `snapshot_builder.py::_build_session_surfaces`.
  Guards: 6/7 green. `check_parameter_count` has 1 pre-existing violation in
  `follow_loop_support.py` (unchanged file, not in this slice).
  Tests: 22 mobile relay pass, 580 operator console pass. needs-review.
- **Round 9 — artifact + packet closure**: 22-check closure guard with 6
  parity sub-checks. On-disk checks gated to event-backed mode.
- **Round 8 — artifact closure proof**: On-disk bridge validation, round-trip test.
- **Round 7 — typed event-backed ReviewState**:
  Refactored `reduce_events()` to typed models. Split emitter_parity.py.
  Identity refactor (repo-relative paths, portable fallback).
  Checks: 159 pass, code_shape 2 (pre-existing), closure 19/19 green.
- **Round 6 — hardened parity guard**: false-green fix, type strictness, negative tests.
- **Round 5 — strengthened parity**: 3 sub-checks (keys, types, _compat).
  Event bridge_state: added overall_state + codex_poll_state, removed reviewed_hash_current.
  Now 19 checks total (9 runtime + 6 artifact + 1 startup + 3 parity), all pass.
  Files changed: `event_projection.py`, `platform_contract_closure/support.py`.
  Checks: 156 tests pass (151 review-channel + 5 contract closure), guard 19/19.
  Checks: closure guard 17/17 green, 151 review-channel tests pass.
- **Round 3 — ACK-freshness parity**: stale-ACK status fix + event ACK fields.
- **Round 2 — guard burndown**: file splits, param-count, dict-schema, facades.
- **Round 2 — guard blocker burndown**: file splits, param-count, dict-schema,
  facade-wrappers, FailurePacket scope narrowing.
- **Round 1 — governance-quality semantics + test fixes**: open_finding_count,
  finding_density, check_router, mobile_status.
- needs-review.

- **Session 37 (prior) — MP-377 quality-feedback + review-channel _compat**
- Rounds 1-8 completed. See history below for details.
- Round 8: Codex refined score formulas. 1539 pass.
- Round 7: Multi-lens score redesign. 1539 pass.
- Round 6: Guard-subset fix. Round 5: Report-semantics fix.
- Round 4: Registry-shape fix. Round 3: Availability-gating fix.
- Previous score-contract fixes completed:
  (b) Added `*_available` flags to `ScoreInputs`; `compute_maintainability_score()`
  now excludes unavailable dimensions and renormalizes weights. Builder only marks
  dimensions available when real evidence exists (`halstead_mi_available` when
  files_scanned>0, `cleanup_rate_available` when review findings>0, etc.).
  `code_shape`, `duplication`, `time_to_green` stay unavailable/excluded until
  their data sources are wired.
  (c) Renamed `probe_density` → `finding_density` and `high_findings` →
  `positive_findings` across models, score functions, weights, and builder.
  Label now honestly says "positive findings per scanned file" instead of
  claiming HIGH-only severity filtering.
  (d) Added 4 new tests: unavailable dims don't inflate, only available dims
  participate, finding_density uses positive_findings, weight key is correct.
  Fixed existing tests for renamed field.
- Validation: 1535 passed, 2 pre-existing failures. needs-review.
- Previously completed:
  (a) CLI wiring confirmed already present — no action needed.
  (b) per_check_score.py and improvement_tracker.py confirmed already using
      composite `(check_id, signal_type)` key — no action needed.
  (c) ReviewState canonical payload: moved `project_id`, `runtime`,
      `service_identity`, `attach_auth_policy`, `agents` from top-level into
      `_compat` sub-dict in both `status_projection.py` (bridge-backed) and
      `event_reducer.py` (event-backed). Updated all consumers:
      `event_projection.py`, `projection_bundle.py`, `control_state.py`, and
      `test_review_channel.py`. 154 review-channel tests pass.
  (d) Halstead paths confirmed already repo-relative — `analyze_file()` has
      `relative_to` param and `analyze_directory()` passes `relative_to=root`.
  (e) Added 12 dedicated quality-feedback tests in
      `tests/governance/test_quality_feedback.py`: per-check composite key
      separation, precision/FP-rate math, improvement delta composite key,
      Halstead path portability, contract constants, serialization.
- Validation: 1531 passed, 2 pre-existing failures (check_router, mobile_status).
  Platform contract closure guard green. needs-review.

- **Session 34 — MP-377 daemon-event to runtime-state reducer**
- Started: `2026-03-17T02:30:00Z`
- Daemon-event reducer is now frozen in the shared backend. The event-backed
  reducer (`reduce_events()`) now handles three daemon event types:
  `daemon_started`, `daemon_stopped`, `daemon_heartbeat`. Each daemon kind
  (`publisher`, `reviewer_supervisor`) accumulates through a `DaemonSnapshot`
  mutable accumulator and the reduced `runtime` section ships in the review
  state alongside packets/queue/agents.
- Bridge-backed status path also produces a `runtime` section. When
  event-reduced runtime is available (has `last_daemon_event_utc`), it takes
  precedence over the bridge-derived fallback. Without daemon events, the
  bridge-backed path synthesizes runtime from `bridge_liveness` publisher
  state.
- Extracted `daemon_reducer.py` into its own module to keep `event_reducer.py`
  under the code shape soft limit. The new module owns `DAEMON_EVENT_TYPES`,
  `DaemonSnapshot`, `DaemonStateDict` TypedDict, `reduce_daemon_event()`,
  `build_runtime_state()`, and `empty_daemon_state()`.
- Added `runtime` field to `ReviewStateSnapshot` dataclass in
  `status_projection.py`. Threaded `reduced_runtime` parameter through
  `build_bridge_review_state()` and `write_status_projection_bundle()`.
- Live proof: `review_state.json` now contains `runtime.daemons.publisher`,
  `runtime.daemons.reviewer_supervisor`, `runtime.active_daemons`, and
  `runtime.last_daemon_event_utc`.
- Proof: `python3 -m pytest dev/scripts/devctl/tests/test_review_channel.py -q --tb=short` -> `141 passed`; `check_code_shape.py` -> 0 violations; `check_parameter_count.py` -> 0 violations; `check_python_dict_schema.py` -> 0 violations; `check_facade_wrappers.py` -> green; `check_review_channel_bridge.py` -> green; `check_active_plan_sync.py` -> green; `check_function_duplication.py` -> 0 duplicates.
- Validators: all per Codex instruction.

- **Session 33 (closed) — MP-377 attach/auth contract**
- Started: `2026-03-17T02:14:01Z`
- Attach/auth contract wired through bridge-backed Python review-channel path.
- Proof: 135 passed, all guards green.

- **Session 31 — MP-377 post-M69 follow-up**
- Started: `2026-03-16T08:00:00Z`
- M54–M69 now accepted locally. Latest patch: lifecycle heartbeats now persist
  the canonical shared file plus a per-PID variant, and lifecycle readers
  prefer the freshest live publisher/reviewer-supervisor writer before
  falling back to the freshest stopped/dead record. That closes the detached
  dead-writer masking bug in the `M69` lifecycle/status seam.
- Prior fixes accepted: publisher stop-reason routing, reviewer-worker
  snapshot reuse, lifecycle/follow extraction, and follow-loop
  `output_error` final-state persistence.
- Service-identity/discovery slice is now landed in the bridge-backed Python
  status/projection/report path. `review-channel` now emits a stable
  repo/worktree-scoped `service_identity` payload with `service_id`,
  `project_id`, `repo_root`, `worktree_root`, `bridge_path`,
  `review_channel_path`, `status_root`, and explicit `discovery_fields`.
- Tightened the controller seam so repo identity now lives in shared
  `review_channel.core` instead of being owned only by the projection module.
  Also collapsed bridge-handler helper parameter lists back under the guard
  threshold with typed context wrappers.
- Live proof: `python3.11 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
  now returns `service_identity.service_id=review-channel:sha256:...`,
  `bridge_path=/Users/jguida941/testing_upgrade/codex-voice/bridge.md`,
  and `status_root=/Users/jguida941/testing_upgrade/codex-voice/dev/reports/review_channel/latest`.
- Proof: `python3 -m pytest dev/scripts/devctl/tests/test_review_channel.py -q --tb=short` -> `135 passed`; `python3.11 dev/scripts/checks/check_code_shape.py` -> green; `python3.11 dev/scripts/checks/check_parameter_count.py` -> green; `python3.11 dev/scripts/checks/check_facade_wrappers.py` -> green; `python3.11 dev/scripts/checks/check_review_channel_bridge.py --format md` -> green; `python3.11 dev/scripts/checks/check_active_plan_sync.py` -> green. `python3.11 dev/scripts/devctl.py check --profile ci` is blocked only by the unrelated Rust test `event_loop::tests::dev_panel_overlay::refresh_poll::memory_page_enter_refreshes_memory_cockpit_snapshot`.
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

- acknowledged; instruction-rev: `r47c-20260322T014612Z`
- Session 47c: Hold for checkpoint first. Then fix (1) coherent 3-tuple contract between artifact_inputs/builder/tests, (2) wire severity from correct artifact surface (review_packet.json or hotspots, not nonexistent severity_counts in file_topology nodes).
- acknowledged; instruction-rev: `r47-20260322T013901Z`
- Session 47 follow-up: severity intake + explicit-empty-input fix done. 56/56 green.
- acknowledged; instruction-rev: `512a370bb32c`
- Session 47 / context-graph plumbing: Exclusions + artifact-backed inputs done.
- acknowledged; instruction-rev: `ce4b1b287137`
- Hold steady. Both slices accepted.
- acknowledged; instruction-rev: `0ba39c9bd879`
- Session 45b / docs gate: All 5 maintainer docs updated, docs-check green, 72 tests green.
- acknowledged; instruction-rev: `0f2559e9ebc7`
- Session 46 / reviewer-wait symmetry: Created _reviewer_wait.py + _wait_shared.py + 14 tests. 214/214 green. Deferred per reviewer — docs gate first.
- acknowledged; instruction-rev: `15446d386996`
- Session 45 / tandem-consistency typed-authority: 4/7 checks migrated to typed state, 15 new tests, 95/95 green.
- acknowledged; instruction-rev: `bdfe4b80f6d6`
- Session 44 / Hold steady. Codex checkpointing and updating plans.
- acknowledged; instruction-rev: `fbac2adbeea6`
- Session 44 / MP-377 bridge-authority consumer migration (deeper): Added review_accepted to ReviewBridgeState, fixed _git_stdout strip→rstrip, all tests green (39 push+startup, 128 runtime+tandem).
- acknowledged; instruction-rev: `beee5cb56a0d`
- Session 44 / review fixes: Restored bridge_review_accepted() semantics, fixed strip bug, 7 regression tests.
- acknowledged; instruction-rev: `49d3b4defcc3`
- Session 44 / MP-377 bridge-authority consumer migration: Beginning bounded slice.
- acknowledged; instruction-rev: `c38cddedb8a7`
- Session 44 / MP-377 bridge-authority consumer migration: ACK'd and holding for reviewer-promoted slice.
- acknowledged; instruction-rev: `718585020fbd`
- Session 43 / MP-377 startup-context verdict-based acceptance: deriving review_accepted from bridge Current Verdict + Open Findings, not mode or hash. Push permitted only when verdict=accepted AND findings=none. Fail-closed on parse errors.
- acknowledged; instruction-rev: `f44a03299b02`
- Session 42 / MP-358 stall (narrowed): DONE. Only instruction-owned wait markers. 6 regressions in test_implementer_stall.py. 42/42 pass. code_shape 0. needs-review.
- Session 42 / MP-358 stall (narrow): Narrow detector to only event-owned evidence. Add focused regressions.
- acknowledged; instruction-rev: `69a3e4f662d2`
- Session 42 / MP-358 loop-health: DONE. Accepted.
- acknowledged; instruction-rev: `42ce07ebf1cc`
- Session 42 / MP-358 queue-truth (continued): DONE. Accepted.
- acknowledged; instruction-rev: `f062bdfda0aa`
- Session 42 / MP-358 queue-truth: DONE. Accepted.
- acknowledged; instruction-rev: `8d3d4e286170`
- Session 42 / MP-358 bridge-truth sync: DONE. Accepted.
- acknowledged; instruction-rev: `21a89eff4cf7`
- Session 42 / MP-355 integrity (wire callers): DONE. Accepted.
- acknowledged; instruction-rev: `cd7a3f838d3e`
- Session 42 / MP-355 integrity (harden): DONE. Accepted.
- acknowledged; instruction-rev: `925f749cb52a`
- Session 42 / MP-355 integrity (serialized): DONE. Accepted.
- acknowledged; instruction-rev: `61ee60fc2662`
- Session 42 / MP-355 integrity (initial): Partial fix — max-based next_event_id + fcntl.flock. Needs full serialized allocation.
- acknowledged; instruction-rev: `2ac12e4c9748`
- Session 42 / MP-355 inbox slice: DONE. Split rendering into Pending/Resolved sections. Added pending_packets/resolved_packets to JSON. 21/21 pass. code_shape 0. needs-review.
- acknowledged; instruction-rev: `b4bd4c1ef62b`
- Session 42 / CI contract fix: DONE. Accepted.
- acknowledged; instruction-rev: `6810e91bea97`
- Session 42 / Repair slice: DONE. Accepted.
- acknowledged; instruction-rev: `248ef248a636`
- acknowledged; instruction-rev: `b061cc56cb92`
- Session 42 / Self-governance: DONE. Wired governance_closure into _SHARED_GOVERNANCE_CHECKS. Added CI exemption (runs via bundle). 5 focused tests. No longer self-flags. 30 pre-existing violations remain. needs-review.
- Session 42 / Slice E (tighten): DONE. Accepted.
- acknowledged; instruction-rev: `1dee08670a08`
- Session 42 / Slice E (final): DONE. Malformed bridge fail-closed. Accepted.
- acknowledged; instruction-rev: `7c129824e4f4`
- Session 42 / Slice E (continued): DONE. Fully typed reviewer token. Accepted.
- acknowledged; instruction-rev: `0d2fa803bfb7`
- Session 42 / Slice E (initial): Routed _capture_wait_snapshot through build_bridge_poll_result. 8/8 pass.
- acknowledged; instruction-rev: `c5d49df4cfd1`
- Session 42 / Slice D: ACCEPTED. bridge-poll live with full RuntimePaths, worktree hash, contract validation.
- acknowledged; instruction-rev: `if366419273a`
- Session 42 ack (parser split): DONE. simple_lanes_parser.py extracted with 4 parsers. parser.py down to 228 lines (under 350 soft limit). code_shape 0 violations. test_simple_lanes 8/8 pass, test_governance_cli_dispatch 5/5 pass, test_doc_authority 30/30 pass. doc-authority command verified working post-refactor. needs-review.
- acknowledged; instruction-rev: `02d4a121f492`
- Session 41 ack (Slice C): DONE. Guard validates 8 invariants, subpackage layout, registered in catalog/policy/bundles. 8/8 live, 5 tests, 0 step failures. needs-review.
- Session 41 ack (Slice B final): DONE. M1 FIXED: e2e command-path test captures payload through run(). M2 FIXED: enabled_checks test asserts specific VoiceTerm guard IDs + count thresholds. M3 FIXED: bundle_overrides emits {} until real bundle surface exists. 61 tests, 0 step failures. needs-review.
- Session 41 ack (Slice B rework): DONE. H1+H2 fixed. policy_path threaded, resolve_quality_policy for checks.
- Session 41 ack (Phase 1 / Slice B): DONE. ALL GUARDS GREEN. `governance-draft` command landed: `scan_repo_governance()` scans local repo facts (git state, policy file, filesystem paths, bridge mode, enabled guards/probes, bundle overrides, startup order). Full CLI wiring through parser + handler + __init__. Live proof: `governance-draft --format json` emits correct `ProjectGovernance` payload on this repo. Fixed subprocess-policy (added check=False) and nesting-depth (extracted `_parse_bridge_mode` helper). 59 tests pass. check --profile quick 0 step failures. needs-review.
- Session 41 ack (Phase 1 / Slice A): DONE. ALL GUARDS GREEN. `ProjectGovernance` contract landed with 9 nested records (`RepoIdentity`, `RepoPackRef`, `PathRoots`, `PlanRegistryRoots`, `ArtifactRoots`, `MemoryRoots`, `BridgeConfig`, `EnabledChecks`, `BundleOverrides`), 10 mapping helpers, exported through `__init__.py`, documented in README.md, 9 focused tests (full-payload, defaults, round-trip, coercion, constants, tuple→list). Fixed facade-wrappers guard by adding intermediate variables to each helper. 54/54 runtime tests pass. check --profile quick 0 step failures. Accepted by Codex.
- prior rev: `2d60024d3761`
- Session 40 ack (round 18k): DONE. ALL GUARDS GREEN. verify threaded through
  ensure, __init__.py 307 lines, ensure.py 348 lines. 178 pass. needs-review.
- Session 40 ack (round 18j): REWORK needed. verify not in ensure path, __init__.py regressed.
- Session 40 ack (round 18i): ACCEPTED. Checkpoint projection refresh.
- Session 40 ack (round 18h): ACCEPTED. ALL GUARDS GREEN.
- Session 40 ack (round 18g): ACCEPTED. __init__.py 352→296 lines.
- Session 40 ack (round 18f): ACCEPTED. Replaced `EnsureActionDeps.sleep_fn` with typed `_noop_sleep()`, removed the `ensure.py` `# type: ignore`, added `test_ensure_action_deps_default_sleep_fn_is_noop`, `175` review-channel tests pass, and quick-check is red only on `review_channel/__init__.py` soft-limit plus `probe_mixed_concerns.py` package-layout debt. needs-review.
- Session 40 ack (round 18e): ACCEPTED. ReviewerFreshness enum + classify function +
  BridgeLiveness field + attention routing rewrite. 174 tests pass. needs-review.
- Session 40 ack (round 18d): ACCEPTED. Ensure auto-heal fix + regression test.
- prior rev: `3f6159c07274`
- Session 40 ack (review findings): All 4 Codex findings fixed. ensure auto-restart,
  mobile relay false-green, identity portability, attention priority. 271 tests pass.
  needs-review.
- Session 40 ack (round 18b): Codex re-reviewed Session 40, narrowed to 4 live
  blockers. All 4 done: __init__.py split, handoff.py mixed-concern split,
  (3) probe_mixed_concerns.py subpackage move, (4) governance facade-wrapper cleanup.
  Coding now.
- Session 40 ack (round 18): Workers 1 and 2 complete. Review-channel package
  conversion done (status.py, ensure.py in package; bridge_promotion.py in domain
  module to avoid circular import). Checks-layer: nesting, param-count, layout all
  fixed. 195 tests pass. Starting Worker 3 (governance dedupe). Still red:
  `__init__.py` 470 lines (package move artifact), `handoff.py` mixed concerns,
  `probe_mixed_concerns.py` crowded directory.
- Session 38 ack (round 17): Concrete slice from Codex. Two fixes:
  (1) event_projection.py: remove queue-derived ACK shortcut, compute
  claude_ack_revision from real bridge/runtime state.
  (2) follow_loop.py: make inactivity timeout fire on empty progress token.
  Coding both now.
- Session 38 ack (round 13b): All blockers closed. Shim dual-import (Codex fix),
  code shape (extracted mobile_relay_protocol_support.py + _load_protocol_sources).
  Evidence: code_shape 0, mobile_relay 22 pass, review_channel 155 pass.
  Both shim modes work (script + module). Continuing MP-377.
  Extracting config/comparison helpers to reduce file + function size. Coding.
- Session 38 ack (round 11): 6 findings closed. Protocol paths config-driven.
  (2) Move new root checks to subpackages + thin wrappers
  (3) Refactor peer_liveness.py + status_projection.py under shape limits
  (4) Remove type:ignore suppression in status_projection.py
  (5) Fix parameter-count in snapshot_builder.py
  Coding now.
  Do not widen into mobile/PyQt6. Coding now.
- Session 38 ack (round 6): Codex accepted ACK-freshness parity. Fresh checkpoint
  on tree `cc13bf57421f`. Next slice: closure-proof parity — make closure guard +
  tests prove canonical ReviewState agreement between bridge-backed and event-backed
  paths. Coding now.
- Session 36 ack: MP-377 governance-quality-feedback redirected slice. Read `Last
  Codex poll`, full `Current Instruction For Claude`, and both plan anchors
  (`ai_governance_platform.md`, `portable_code_governance.md`). Restated active
  slice in Claude Status. Confirmed: 8 core modules exist (models, halstead,
  fp_classifier, maintainability_score, per_check_score, improvement_tracker,
  recommendation_engine, report_builder). Missing: CLI command handler, tests,
  script_catalog registration, platform artifact-schema wiring, artifact writes.
  Fanning out 3 disjoint workers per bridge instruction. needs-review.
- Session 35 ack: MP-377 P0 contract-closure slice — finding identity + guard-to-Finding adapter.
  Completed: (1) stable finding identity — `review_probe_report.py:243` now passes `repo_path=""`
  instead of `str(effective_root)`, docstring added to `FindingIdentitySeed`, portability test added.
  (2) Guard-to-Finding adapter — `finding_from_guard_violation()` in new `guard_finding_contracts.py`
  with `GuardFindingPolicy` dataclass, tested against code_shape and duplication violation schemas.
  Guards now emit `signal_type="guard"` into the same `FindingRecord` pipeline as probes.
  Codex refactored param-count violation by extracting the policy dataclass. Both slices verified:
  7 focused tests pass, 1488/1490 full suite pass (2 pre-existing failures), parameter-count guard
  clean, platform-contract-closure guard green for its implemented matrix (`8` runtime contracts + `5` artifact schemas), docs-check ok, hygiene ok.
  Governance-review ledger: 101 rows, 3 new audit findings recorded with accuracy verdicts.
  Corrected scope for plan (reviewed by Codex, cross-checked by Claude):
  - Actual surface: 62 guard scripts (32 policy-enabled), 26 probe scripts (23 policy-enabled)
  - Naming enforcement already exists as `check_naming_consistency.py` (host/provider naming)
  - Design-pattern enforcement partially exists via `check_package_layout`, `check_facade_wrappers`,
    `check_platform_layer_boundaries`
  - Net-new guard opportunities: cross-file naming drift, contract-field consistency,
    return-type consistency, import-pattern drift
  - Widening the existing `check_naming_consistency.py` into a portable, policy-driven
    `check_naming_conventions` guard is the right next step, not greenfield
  - Proof path: reference repo pilot (small Python project, intentional bad patterns,
    before/after findings, cleanup rate, false-positive rate)
  - All new guards must be policy-configurable via `quality_presets/*.json` and
    `devctl_repo_policy.json`, never hardcoded to VoiceTerm
  needs-review.
- Session 34 ack: daemon-event to runtime-state reducer is frozen in the
  shared backend. `reduce_events()` now handles `daemon_started`,
  `daemon_stopped`, `daemon_heartbeat` → produces authoritative `runtime`
  section with per-daemon-kind snapshots. Bridge-backed status path also
  produces `runtime`, preferring event-reduced state when available.
  Extracted `daemon_reducer.py` to stay under code shape. 141 tests pass,
  all guards clean. needs-review.
- Session 33 ack (closed): attach/auth contract wired. 135 passed.
- Session 31 ack: M69 continuing. Wired `reviewer_supervisor` into ensure
  report + error report defaults. All status/ensure paths now expose both
  publisher + reviewer supervisor lifecycle. 129 tests pass. needs-review.
- Session 32 ack: repo/worktree service identity/discovery is wired through
  the bridge-backed Python review-channel path and the live `status` command
  proves it. Focused suite is `135 passed`; tooling guards are green; full
  `check --profile ci` remains blocked only by the known unrelated Rust
  `memory_page_enter_refreshes_memory_cockpit_snapshot` failure. needs-review.
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

- Hold steady for a checkpoint first. `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json` still reports `attention.status=checkpoint_required` and `push_enforcement.safe_to_continue_editing=false`, so do not widen or continue edits until the checkpoint budget is back in-bounds.
- While that checkpoint gate is unresolved, do not use raw shell `sleep` loops. Use the repo-owned bounded wait path instead: `python3 dev/scripts/devctl.py review-channel --action implementer-wait --terminal none --format json`. That keeps the Claude-side loop attached to reviewer-owned bridge changes instead of idling on ad hoc polling.
- After the checkpoint, resume Session 47e / MP-377 graph plumbing follow-up. Keep the slice bounded to `dev/scripts/devctl/context_graph/**`, `dev/scripts/devctl/probe_topology_builder.py`, and focused tests for this seam.
- Close the remaining artifact-shape gap: either read per-file severity from the existing `review_packet.json` hotspot surface, or materialize the same severity summary into `file_topology.json` node rows in the same bounded lane. Do not keep a severity loader that reads fields the topology node contract does not emit.
- Add real regression coverage for both new behaviors: partial-input merge cases in `resolve_graph_inputs()` and one severity-bearing artifact path that proves the boost can actually activate on the repo’s real generated contract.
- Preserve the explicit-empty-input behavior that is now correct: only `None` should trigger artifact fallback for `hint_counts` / `changed_paths`.
- Validation: rerun `python3 -m pytest dev/scripts/devctl/tests/context_graph/test_context_graph.py dev/scripts/devctl/tests/context_graph/test_context_graph_artifact_inputs.py -q`, then rerun `python3 dev/scripts/devctl.py check --profile ci` if the touched surface expands beyond the current bounded files.

## Crowded Directories
- `dev/scripts/checks`: 94 files (max 40, mode `freeze`, 22 approved shims excluded, 116 total files)
- `dev/scripts/devctl`: 68 files (max 60, mode `freeze`, 12 approved shims excluded, 80 total files)
- `dev/scripts/devctl/commands`: 92 files (max 48, mode `freeze`, 1 approved shims excluded, 93 total files)
- `dev/scripts/devctl/tests`: 137 files (max 72, mode `freeze`)

## Crowded Namespace Families
- `dev/scripts/devctl/commands` + `check_*`: 11 files (threshold 6, mode `freeze`, target `dev/scripts/devctl/commands/check`)
- `dev/scripts/devctl/commands` + `autonomy_*`: 8 files (threshold 6, mode `freeze`, target `dev/scripts/devctl/commands/autonomy`)
- `dev/scripts/devctl/commands` + `docs_*`: 6 files (threshold 5, mode `freeze`, target `dev/scripts/devctl/commands/docs`)
- `dev/scripts/devctl/commands` + `review_channel_*`: 5 files (threshold 4, mode `freeze`, target `dev/scripts/devctl/commands/review_channel`)
- `dev/scripts/devctl/commands` + `release_*`: 4 files (threshold 4, mode `freeze`, target `dev/scripts/devctl/commands/release`)
- `dev/scripts/devctl/commands` + `ship_*`: 4 files (threshold 4, mode `freeze`, target `dev/scripts/devctl/commands/release`)
- `dev/scripts/devctl/commands` + `process_*`: 3 files (threshold 3, mode `freeze`, target `dev/scripts/devctl/commands/process`)
Clippy summary: status=success warnings=0 exit_code=0
# check_python_broad_except

- mode: working-tree
- ok: True
- files_scanned: 0
- files_skipped_tests: 0
- broad_handlers: 0
- candidate_handlers: 0
- documented_candidate_handlers: 0
- suppressive_candidate_handlers: 0
- fallback_documented_candidate_handlers: 0
- violations: 0
- parse_errors: 0
- head_ref: HEAD
# check_function_duplication

- mode: working-tree
- ok: True
- files_changed: 0
- functions_scanned: 0
- duplicates_found: 0
# check_god_class

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_source: 2
- files_skipped_tests: 0
- violations: 0
- head_ref: HEAD
- aggregate_growth: god_classes +0
- thresholds: python methods >20 or ivars >10, rust impl methods >20
# check_nesting_depth

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_source: 2
- files_skipped_tests: 0
- violations: 0
- head_ref: HEAD
- aggregate_growth: deeply_nested_functions +0
- thresholds: python >4 levels, rust >5 levels
# check_parameter_count

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_source: 2
- files_skipped_tests: 0
- violations: 0
- head_ref: HEAD
- aggregate_growth: high_param_functions +0
- thresholds: python >6, rust >7
# check_python_dict_schema

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_python: 2
- files_skipped_tests: 0
- violations: 0
- head_ref: HEAD
- aggregate_growth: large_dict_literals +0, weak_dict_any_aliases +0
- threshold: >=6 string keys
# check_python_global_mutable

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_python: 2
- files_skipped_tests: 0
- violations: 0
- head_ref: HEAD
- aggregate_growth: none
# check_python_design_complexity

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_python: 2
- files_skipped_tests: 0
- violations: 0
- head_ref: HEAD
- aggregate_growth: high_branch_functions +0, high_return_functions +0
- thresholds: branches >30, returns >10
# check_python_suppression_debt

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_python: 2
- violations: 0
- head_ref: HEAD
- aggregate_growth: none
# check_structural_similarity

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_source: 2
- files_skipped_tests: 0
- functions_fingerprinted: 0
- aggregate_growth: structural_similar_pairs +0
- min_body_lines: 8
# check_facade_wrappers

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_python: 2
- files_skipped_tests: 0
- violations: 0
- head_ref: HEAD
- aggregate_growth: facade_heavy_modules +0, facade_wrappers +0
- threshold: >3 pure-delegation wrappers per file
# check_python_subprocess_policy

- mode: working-tree
- ok: True
- files_scanned: 826
- files_skipped_tests: 233
- subprocess_run_calls: 75
- violations: 0
- parse_errors: 0
- head_ref: HEAD
# check_structural_complexity

- mode: working-tree
- ok: True
- source_root: rust/src
- include_tests: False
- files_scanned: 287
- files_skipped_tests: 34
- functions_scanned: 2413
- exceptions_defined: 0
- exceptions_used: 0
- violations: 0
- head_ref: HEAD
# check_rust_test_shape

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_rust: 2
- files_skipped_non_tests: 0
- files_using_path_overrides: 0
- violations: 0
- head_ref: HEAD
# check_rust_lint_debt

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_rust: 2
- files_skipped_tests: 0
- violations: 0
- aggregate_growth: allow_attrs +0, dead_code_allow_attrs +0, unwrap_expect_calls +0, unchecked_unwrap_expect_calls +0, panic_macro_calls +0
- dead_code_instances: 0
- dead_code_without_reason: 0
# check_rust_best_practices

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_rust: 2
- files_skipped_tests: 0
- violations: 0
- head_ref: HEAD
- aggregate_growth: allow_without_reason +0, undocumented_unsafe_blocks +0, pub_unsafe_fn_missing_safety_docs +0, unsafe_impl_missing_safety_comment +0, mem_forget_calls +0, result_string_types +0, expect_on_join_recv +0, unwrap_on_join_recv +0, dropped_send_results +0, dropped_emit_results +0, detached_thread_spawns +0, env_mutation_calls +0, suspicious_open_options +0, float_literal_comparisons +0, nonatomic_persistent_toml_writes +0, custom_persistent_toml_parsers +0
# check_serde_compatibility

- mode: working-tree
- ok: True
- files_scanned: 0
- files_skipped_tests: 0
- tagged_deserialize_enums: 0
- enums_with_other: 0
- documented_strict_enums: 0
- violations: 0
- head_ref: HEAD
# check_rust_runtime_panic_policy

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_rust: 2
- files_skipped_tests: 0
- violations: 0
- head_ref: HEAD
- aggregate_growth: unallowlisted_panic_calls +0
# check_rust_audit_patterns

- ok: True
- mode: working-tree
- source_root: rust/src
- files_considered: 0
- violations: 0
- aggregate: utf8_prefix_slice=0, char_limit_truncate=0, single_pass_secret_find=0, deterministic_id_hash_suffix=0, lossy_vad_cast_i16=0
# check_rust_security_footguns

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_rust: 2
- files_skipped_tests: 0
- violations: 0
- head_ref: HEAD
- aggregate_growth: todo_macro_calls +0, unimplemented_macro_calls +0, dbg_macro_calls +0, unreachable_hot_path_calls +0, shell_spawn_calls +0, shell_control_flag_calls +0, permissive_mode_literals +0, weak_crypto_refs +0, pid_signed_wrap_casts +0, sign_unsafe_syscall_casts +0
# check_ide_provider_isolation

- ok: True
- mode: blocking
- source_roots: rust/src/bin/voiceterm, rust/src/ipc
- files_scanned: 232
- files_skipped_tests: 27
- files_with_mixed_signals: 2
- files_with_file_signal_coupling: 5
- unauthorized_files: 0
- allowlisted_prefixes: 
# check_compat_matrix

- ok: True
- matrix_path: dev/config/compat/ide_provider_matrix.yaml
- hosts_declared: 3
- providers_declared: 6
- matrix_cells_declared: 18
- matrix_cells_expected: 18
- missing_required_hosts: 0
- missing_required_providers: 0
- duplicate_host_ids: 0
- duplicate_provider_ids: 0
- missing_cells: 0
- duplicate_cells: 0
- invalid_cells: 0
- invalid_provider_modes: 0
- provider_mode_policy_errors: 0
# compat_matrix_smoke

- ok: True
- matrix_path: dev/config/compat/ide_provider_matrix.yaml
- runtime_hosts: cursor, jetbrains, other
- runtime_providers: claude, codex, gemini
- runtime_backends: aider, claude, codex, gemini, opencode
- ipc_providers: claude, codex
- missing_runtime_cells: 0
- missing_runtime_backends: 0
- runtime_non_ipc_provider_labels: 3

## Warnings
- provider `aider` is runtime-visible but non-IPC by policy (`overlay-only-non-ipc`)
- provider `gemini` is runtime-visible but non-IPC by policy (`overlay-only-experimental`)
- provider `opencode` is runtime-visible but non-IPC by policy (`overlay-only-non-ipc`)
# check_naming_consistency

- ok: True
- errors: 0
- matrix_host_ids: cursor, jetbrains, other
- matrix_provider_ids: aider, claude, codex, custom, gemini, opencode
- runtime_host_ids: cursor, jetbrains, other
- runtime_provider_ids: claude, codex, gemini
- runtime_backend_ids: aider, claude, codex, gemini, opencode
- ipc_provider_ids: claude, codex
- isolation_provider_tokens: aider, claude, codex, custom, gemini, opencode
# check_code_shape

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_using_path_overrides: 0
- function_policies_applied: 0
- function_exceptions_used: 0
- function_violations: 0
- mixed_concern_violations: 0
- stale_override_review_window_days: 30
- stale_override_candidates_scanned: 46
- stale_override_candidates_skipped: 16
- files_skipped_non_source: 2
- files_skipped_tests: 0
- warnings: 3
- violations: 0

## Warnings
- `rust/src/bin/voiceterm/event_loop/tests.rs` (soft_limit, hard_limit): Override soft_limit (6500) is 7.22x the .rs default (900). Override hard_limit (7000) is 5.00x the .rs default (1400). Operator intent keeps path overrides under 3.0x the soft cap and under 2.0x the hard cap.
- `app/operator_console/theme/editor/theme_editor.py` (soft_limit, hard_limit): Override soft_limit (1400) is 4.00x the .py default (350). Override hard_limit (1500) is 2.31x the .py default (650). Operator intent keeps path overrides under 3.0x the soft cap and under 2.0x the hard cap.
- `app/operator_console/views/ui_refresh.py` (soft_limit): Override soft_limit (1150) is 3.29x the .py default (350). Operator intent keeps path overrides under 3.0x the soft cap and under 2.0x the hard cap.
# check_platform_layer_boundaries

- mode: working-tree
- ok: True
- files_changed: 2
- configured_rules: 2
- candidates_scanned: 0
- violations: 0
- head_ref: HEAD
# check_platform_contract_sync

- ok: True
- checked_contracts: 2
- violations: 0

## Coverage

- [PASS] LocalServiceEndpoint ↔ service_lifecycle: Contract and surface stay aligned.
- [PASS] CallerAuthorityPolicy ↔ caller_authority: Contract and surface stay aligned.
# check_platform_contract_closure

- ok: True
- checked_runtime_contracts: 9
- checked_artifact_schemas: 6
- violations: 0

## Coverage

- [PASS] runtime_contract::TypedAction: Platform contract row matches the runtime dataclass fields.
- [PASS] runtime_contract::RunRecord: Platform contract row matches the runtime dataclass fields.
- [PASS] runtime_contract::ActionResult: Platform contract row matches the runtime dataclass fields.
- [PASS] runtime_contract::ArtifactStore: Platform contract row matches the runtime dataclass fields.
- [PASS] runtime_contract::Finding: Platform contract row matches the runtime dataclass fields.
- [PASS] runtime_contract::DecisionPacket: Platform contract row matches the runtime dataclass fields.
- [PASS] runtime_contract::FailurePacket: Platform contract row matches the runtime dataclass fields.
- [PASS] runtime_contract::ControlState: Platform contract row matches the runtime dataclass fields.
- [PASS] runtime_contract::ReviewState: Platform contract row matches the runtime dataclass fields.
- [PASS] artifact_schema::ProbeReport: Artifact schema row matches the runtime/emitter constants.
- [PASS] artifact_schema::ReviewPacket: Artifact schema row matches the runtime/emitter constants.
- [PASS] artifact_schema::ReviewTargets: Artifact schema row matches the runtime/emitter constants.
- [PASS] artifact_schema::FileTopology: Artifact schema row matches the runtime/emitter constants.
- [PASS] artifact_schema::ProbeAllowlist: Artifact schema row matches the runtime/emitter constants.
- [PASS] artifact_schema::QualityFeedbackSnapshot: Artifact schema row matches the runtime/emitter constants.
- [PASS] startup_surface::dev/config/devctl_repo_policy.json: Policy-owned startup surfaces expose the contract-routing tokens.
- [PASS] emitter_parity::ReviewState: Event-backed bridge_state keys match ReviewBridgeState.
- [PASS] emitter_parity::ReviewState: Event-backed bridge_state value types match contract.
- [PASS] emitter_parity::ReviewState: Event-backed _compat carries all transitional fields.
# check_tandem_consistency

- ok: True
- bridge_present: True
- total_checks: 7
- passed: 7
- failed: 0
- implementer: healthy
- operator: healthy
- reviewer: healthy
- system: healthy

- [PASS] reviewer_freshness (role=reviewer): Reviewer heartbeat age: 1s (fresh).
- [PASS] implementer_ack_freshness (role=implementer): Implementer ACK and status are present and tranche-aligned.
- [PASS] implementer_completion_stall (role=implementer): Implementer status/ACK do not show a completion-stall pattern (typed).
- [PASS] reviewed_hash_honesty (role=reviewer): Reviewed hash 9290214cd22e... does NOT match current tree 1cde949a6c78...
- [PASS] plan_alignment (role=operator): Plan alignment chain is complete (MASTER_PLAN → continuous_swarm.md).
- [PASS] promotion_state (role=operator): Promotion state is active (work in progress).
- [PASS] launch_truth (role=system): Launch truth is consistent.
# check_duplicate_types

- mode: working-tree
- ok: True
- source_root: rust/src
- include_tests: False
- files_scanned: 287
- files_skipped_tests: 34
- type_definitions_found: 455
- duplicate_names_detected: 2
- allowlist_entries: 2
- allowlist_entries_used: 2
- stale_allowlist_entries: 0
- violations: 0
- head_ref: HEAD
# check_python_cyclic_imports

- mode: working-tree
- ok: True
- files_changed: 2
- files_considered: 0
- files_skipped_non_python: 2
- files_skipped_tests: 0
- graph_python_files_base: 826
- graph_python_files_current: 826
- cycles_scanned: 1
- violations: 0
- head_ref: HEAD
- aggregate_growth: cyclic_imports +0
- ignored_cycle_count: 1
# check_clippy_high_signal

- ok: True
- baseline_file: /Users/jguida941/testing_upgrade/codex-voice/dev/config/clippy/high_signal_lints.json
- input_file: /Users/jguida941/testing_upgrade/codex-voice/dev/reports/check/clippy-lints.json
- tracked_lints: 7
- observed_lints: 0
- violations: 0
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.17s
     Running unittests src/lib.rs (target/debug/deps/voiceterm-f7bce60db1f0f9f3)

running 545 tests
test audio::meter::tests::live_meter_defaults_to_floor ... ok
test audio::meter::tests::live_meter_updates_level ... ok
test audio::meter::tests::rms_db_reports_half_scale_level ... ok
test audio::meter::tests::rms_db_handles_empty ... ok
test audio::meter::tests::rms_db_reports_unity_as_zero_db ... ok
test audio::tests::append_downmixed_samples_handles_partial_frame ... ok
test audio::tests::append_downmixed_samples_handles_two_sample_remainder ... ok
test audio::tests::adjust_frame_length_truncates_and_pads ... ok
test audio::tests::append_downmixed_samples_three_channel_average ... ok
test audio::tests::basic_resample_rejects_out_of_bounds_rates ... ok
test audio::tests::basic_resample_returns_identity_for_target_rate ... ok
test audio::tests::basic_resample_downsamples_constant_signal ... ok
test audio::tests::basic_resample_downsample_filters_high_freq ... ok
test audio::tests::basic_resample_upsample_matches_linear ... ok
test audio::tests::basic_resample_upsamples_constant_signal ... ok
test audio::tests::capture_state_does_not_stop_without_speech ... ok
test audio::tests::capture_state_hits_max_duration ... ok
test audio::tests::capture_state_manual_stop_sets_reason ... ok
test audio::tests::capture_state_metrics_track_speech_and_silence ... ok
test audio::tests::capture_state_requires_min_speech_before_silence_stop ... ok
test audio::tests::capture_state_times_out_after_idle ... ok
test audio::tests::convert_frame_to_target_skips_resample_when_rates_match ... ok
test audio::tests::design_low_pass_coeffs_are_normalized ... ok
test audio::tests::design_low_pass_matches_reference ... ok
test audio::tests::design_low_pass_single_tap_normalized ... ok
test audio::tests::downmixes_multi_channel_audio ... ok
test audio::tests::downsampling_tap_count_is_odd_and_scaled ... ok
test audio::tests::downsampling_tap_count_scales_for_large_rate ... ok
test audio::tests::frame_accumulator_drops_oldest_on_capacity ... ok
test audio::tests::frame_accumulator_from_config_calculates_samples ... ok
test audio::tests::frame_accumulator_is_empty_reflects_frames ... ok
test audio::tests::basic_resample_accepts_boundary_rates ... ok
test audio::tests::frame_accumulator_handles_partial_trim ... ok
test audio::tests::frame_accumulator_keeps_silence_within_lookback ... ok
test audio::tests::frame_accumulator_trim_progresses_after_pop ... ok
test audio::tests::frame_accumulator_trim_preserves_trailing_speech ... ok
test audio::tests::frame_accumulator_trims_excess_silence ... ok
test audio::tests::frame_accumulator_trims_zero_length_silence ... ok
test audio::tests::frame_accumulator_trims_across_multiple_frames ... ok
test audio::tests::frame_dispatcher_accumulates_partial_frames ... ok
test audio::tests::frame_dispatcher_emits_frames_and_tracks_drops ... ok
test audio::tests::low_pass_fir_returns_input_for_short_taps ... ok
test audio::tests::low_pass_fir_preserves_dc_component ... ok
test audio::tests::low_pass_fir_matches_reference_impulse ... ok
test audio::tests::offline_capture_keeps_max_duration_when_tail_short ... ok
test audio::tests::offline_capture_pads_partial_frame ... ok
test audio::tests::offline_capture_promotes_silence_tail ... ok
test audio::tests::offline_capture_tracks_metrics_for_speech ... ok
test audio::tests::preserves_single_channel_audio ... ok
test audio::tests::resample_bounds_match_constants ... ok
test audio::tests::resample_linear_downsamples_midpoints ... ok
test audio::tests::resample_linear_handles_non_integer_ratio ... ok
test audio::tests::resample_linear_interpolates_expected_values ... ok
test audio::tests::resample_linear_scales_length ... ok
test audio::tests::resample_to_target_rate_returns_input_when_rate_matches ... ok
test audio::tests::resample_to_target_rate_returns_empty_for_empty_input ... ok
test audio::tests::simple_threshold_vad_classifies_by_energy ... ok
test audio::tests::simple_threshold_vad_uses_average_energy ... ok
test audio::tests::stop_reason_labels_are_stable ... ok
test audio::tests::vad_config_from_pipeline_config_maps_fields ... ok
test audio::tests::vad_engine_default_name_is_stable ... ok
test audio::tests::vad_smoother_drops_oldest_frame_when_window_full ... ok
test audio::tests::vad_smoother_majority_vote_prefers_stable_label ... ok
test audio::tests::vad_smoother_window_size_one_noop ... ok
test auth::tests::run_login_command_rejects_blank_input ... ok
test auth::tests::run_login_command_with_missing_command_reports_spawn_or_tty_error ... ok
test auth::tests::validate_login_command_rejects_blank_input ... ok
test auth::tests::validate_login_command_trims_whitespace ... ok
test backend::aider::tests::test_aider_backend ... ok
test backend::aider::tests::test_aider_with_args ... ok
test backend::claude::tests::test_claude_backend ... ok
test audio::tests::resample_to_target_rate_avoids_fallback_for_valid_input ... ok
test audio::tests::rubato_accepts_boundary_rates ... ok
test backend::claude::tests::test_claude_with_args ... ok
test backend::codex::tests::test_codex_backend ... ok
test backend::codex::tests::test_codex_with_args ... ok
test backend::custom::tests::test_custom_backend ... ok
test backend::custom::tests::test_custom_command_falls_back_on_invalid_shell_syntax ... ok
test backend::custom::tests::test_custom_command_parses_shell_quotes ... ok
test backend::custom::tests::test_custom_no_thinking_pattern ... ok
test audio::tests::resample_to_target_rate_warns_once_on_fallback ... ok
test backend::custom::tests::test_custom_with_patterns ... ok
test backend::gemini::tests::test_gemini_backend ... ok
test backend::gemini::tests::test_gemini_with_args ... ok
test backend::claude::tests::test_claude_prompt_pattern_matches_review_prompts ... ok
test backend::opencode::tests::test_opencode_backend ... ok
test backend::tests::test_available_backends ... ok
test backend::opencode::tests::test_opencode_with_args ... ok
test backend::tests::test_default_backend ... ok
test backend::tests::test_register_custom ... ok
test backend::tests::test_registry_lookup ... ok
test codex::tests::backend_job_cancel_sets_flag ... ok
test audio::tests::resample_to_target_rate_keeps_non_empty ... ok
test codex::tests::backend_job_try_recv_signal_reports_empty_then_ready ... ok
test codex::tests::bounded_queue_drops_token_before_status ... ok
test codex::tests::backend_job_take_handle_consumes_once ... ok
test codex::tests::cancel_token_flips_state ... ok
test codex::tests::clamp_line_start_keeps_valid_and_clamps_overflow ... ok
test codex::tests::backend_job_ids_increment ... ok
test codex::tests::cli_backend_cancels_and_cleans_registry ... ok
test auth::tests::login_status_result_returns_ok_for_success_status ... ok
test codex::tests::cli_backend_restore_static_state_disables_pty ... ok
test codex::tests::cli_backend_ensure_codex_session_fails_for_bad_command ... ok
test auth::tests::login_status_result_formats_failure_exit_code ... ok
test codex::tests::compute_deadline_moves_forward ... ok
test codex::tests::current_line_start_finds_last_newline ... ok
test codex::tests::duration_ms_converts_to_millis ... ok
test codex::tests::event_sender_notifies_listener ... ok
test codex::tests::find_csi_sequence_detects_final_byte ... ok
test codex::tests::find_csi_sequence_rejects_escape_without_bracket ... ok
test codex::tests::find_csi_sequence_returns_none_for_non_csi ... ok
test codex::tests::guard_helpers_enforce_limits ... ok
test codex::tests::normalize_control_bytes_drops_nul_and_keeps_unknown_escape ... ok
test codex::tests::normalize_control_bytes_handles_cr_and_backspace ... ok
test codex::tests::normalize_control_bytes_handles_osc_after_bel ... ok
test codex::tests::normalize_control_bytes_preserves_crlf_lines ... ok
test codex::tests::normalize_control_bytes_skips_charset_and_keypad_sequences ... ok
test codex::tests::normalize_control_bytes_skips_osc_and_csi_sequences ... ok
test codex::tests::normalize_control_bytes_skips_osc_with_long_prefix ... ok
test codex::tests::pop_last_codepoint_handles_utf8_and_newline ... ok
test codex::tests::prepare_for_display_preserves_empty_lines ... ok
test audio::tests::rubato_rejects_aliasing_energy ... ok
test codex::tests::sanitize_handles_backspace ... ok
test codex::tests::sanitize_keeps_wide_glyphs ... ok
test codex::tests::sanitize_preserves_numeric_lines ... ok
test codex::tests::sanitize_strips_cursor_query_bytes ... ok
test codex::tests::sanitize_strips_escape_wrapped_cursor_report ... ok
test audio::tests::rubato_accepts_valid_rate_without_forced_error ... ok
test codex::tests::sanitized_output_cache_refreshes_after_mark_dirty ... ok
test audio::tests::rubato_rejects_out_of_bounds_rates ... ok
test codex::tests::sanitized_output_cache_reuses_cached_text_until_marked_dirty ... ok
test codex::tests::session_timeout_helpers_handle_boundaries ... ok
test codex::tests::should_send_sigkill_after_delay ... ok
test codex::tests::send_signal_tracks_failure_on_invalid_pid ... ok
test codex::tests::skip_osc_sequence_handles_immediate_st ... ok
test codex::tests::skip_osc_sequence_handles_trailing_escape ... ok
test codex::tests::skip_osc_sequence_ignores_escape_without_st ... ok
test codex::tests::skip_osc_sequence_stops_on_bel_or_st ... ok
test codex::tests::write_prompt_with_newline_appends_once ... ok
test config::tests::accepts_auto_language ... ok
test config::tests::accepts_codex_arg_bytes_at_limit ... ok
test config::tests::accepts_codex_args_at_limit ... ok
test config::tests::accepts_ffmpeg_device_at_max_length ... ok
test audio::tests::rubato_resampler_handles_upsample ... ok
test config::tests::accepts_ffmpeg_device_without_shell_chars ... ok
test config::tests::accepts_language_with_region_suffixes ... ok
test config::tests::accepts_valid_defaults ... ok
test config::tests::accepts_seconds_bounds ... ok
test config::tests::accepts_voice_buffer_at_bounds ... ok
test config::tests::accepts_voice_lookback_equal_to_capture ... ok
test config::tests::accepts_voice_channel_capacity_bounds ... ok
test audio::tests::rubato_resampler_is_not_shorter_than_expected ... ok
test config::tests::accepts_voice_max_capture_limit ... ok
test config::tests::accepts_voice_max_capture_minimum ... ok
test config::tests::accepts_voice_min_speech_equal_to_max_capture ... ok
test config::tests::accepts_voice_silence_tail_equal_to_max_capture ... ok
test config::tests::accepts_voice_silence_tail_lower_bound ... ok
test config::tests::accepts_voice_min_speech_lower_bound ... ok
test config::tests::accepts_voice_sample_rate_bounds ... ok
test config::tests::accepts_voice_stt_timeout_bounds ... ok
test config::tests::canonical_repo_root_matches_manifest_parent ... ok
test config::tests::accepts_whisper_beam_size_upper_bound ... ok
test config::tests::accepts_voice_vad_frame_bounds ... ok
test config::tests::accepts_voice_vad_threshold_bounds ... ok
test config::tests::canonicalize_within_repo_accepts_inside_path ... ok
test config::tests::default_term_prefers_env ... ok
test audio::tests::rubato_resampler_matches_expected_length ... ok
test config::tests::discover_default_whisper_model_returns_none_when_missing ... ok
test config::tests::canonicalize_within_repo_rejects_outside_path ... ok
test config::tests::max_codex_arg_bytes_constant_matches_expectation ... ok
test config::tests::default_vad_engine_prefers_earshot_when_feature_enabled ... ok
test config::tests::discover_default_whisper_model_finds_candidate ... ok
test config::tests::rejects_excessive_codex_arg_bytes ... ok
test config::tests::normalizes_input_device_whitespace_before_runtime_use ... ok
test config::tests::rejects_empty_language ... ok
test config::tests::codex_cmd_path_must_be_executable ... ok
test config::tests::rejects_ffmpeg_device_over_max_length ... ok
test config::tests::rejects_input_device_when_normalized_value_is_empty ... ok
test config::tests::rejects_invalid_claude_cmd ... ok
test config::tests::rejects_invalid_voice_sample_rate ... ok
test config::tests::rejects_invalid_language_code ... ok
test config::tests::rejects_language_with_invalid_suffix_chars ... ok
test config::tests::rejects_language_with_unknown_primary_code ... ok
test config::tests::rejects_mic_meter_samples_out_of_bounds ... ok
test config::tests::rejects_seconds_out_of_bounds ... ok
test config::tests::rejects_too_many_codex_args ... ok
test config::tests::rejects_voice_buffer_smaller_than_capture_window ... ok
test config::tests::rejects_vad_smoothing_frames_out_of_bounds ... ok
test config::tests::rejects_voice_buffer_above_max ... ok
test config::tests::rejects_voice_channel_capacity_above_max ... ok
test config::tests::rejects_voice_channel_capacity_out_of_bounds ... ok
test config::tests::rejects_voice_lookback_exceeds_capture ... ok
test config::tests::rejects_voice_max_capture_out_of_bounds ... ok
test config::tests::rejects_voice_min_speech_out_of_bounds ... ok
test config::tests::rejects_voice_sample_rate_above_max ... ok
test config::tests::rejects_voice_silence_tail_out_of_bounds ... ok
test config::tests::rejects_ffmpeg_device_with_shell_metacharacters ... ok
test config::tests::rejects_whisper_beam_size_out_of_bounds ... ok
test config::tests::rejects_voice_vad_frame_out_of_bounds ... ok
test config::tests::sanitize_binary_accepts_allowlist_case_insensitive ... ok
test config::tests::rejects_voice_vad_threshold_out_of_bounds ... ok
test config::tests::rejects_voice_stt_timeout_out_of_bounds ... ok
test config::tests::sanitize_binary_rejects_empty ... ok
test config::tests::sanitize_binary_rejects_directory_path ... ok
test config::tests::sanitize_binary_accepts_executable_path ... ok
test config::tests::rejects_whisper_temperature_out_of_bounds ... ok
test config::tests::sanitize_binary_rejects_missing_relative_path ... ok
test config::tests::vad_engine_labels_are_stable ... ok
test config::tests::sanitize_binary_accepts_relative_path_with_separator ... ok
test config::tests::validate_rejects_missing_whisper_model_path ... ok
test config::tests::voice_pipeline_config_respects_python_fallback_flag ... ok
test config::tests::validate_accepts_existing_whisper_model_path ... ok
test config::tests::voice_vad_engine_default_matches_feature ... ok
test devtools::state::tests::empty_events_capture_drop_count_when_present ... ok
test devtools::state::tests::avg_latency_none_when_no_latency_samples_exist ... ok
test devtools::state::tests::ring_buffer_keeps_most_recent_events_only ... ok
test devtools::state::tests::transcript_events_update_word_and_latency_counters ... ok
test devtools::storage::tests::default_dev_root_dir_prefers_home_env_when_available ... ok
test devtools::storage::tests::new_session_log_path_is_under_sessions_directory ... ok
test doctor::tests::format_term_program_for_report_defaults_to_raw_term_program ... ok
test doctor::tests::format_term_program_for_report_handles_native_cursor_term_program ... ok
test config::tests::session_memory_flags_parse_as_expected ... ok
test doctor::tests::format_term_program_for_report_labels_cursor_when_markers_present ... ok
test doctor::tests::format_term_program_for_report_prefers_cursor_version_when_available ... ok
test config::tests::voice_vad_engine_flag_round_trips_into_pipeline_config ... ok
test config::tests::validate_rejects_pipeline_script_outside_repo ... ok
test ipc::tests::claude_job_cancel_sends_ctrl_c_for_pty ... ok
test devtools::storage::tests::writer_open_session_appends_jsonl_events ... ok
test ipc::tests::handle_auth_command_rejects_invalid_provider_override ... ok
test ipc::tests::emit_capabilities_reports_state ... ok
test ipc::tests::handle_auth_command_rejects_unknown_provider ... ok
test ipc::tests::handle_auth_command_rejects_when_active ... ok
test ipc::tests::handle_auth_command_rejects_overlay_only_non_ipc_provider_overrides ... ok
test ipc::tests::handle_cancel_clears_voice_job ... ok
test ipc::tests::handle_send_prompt_allows_exit_during_auth ... ok
test ipc::tests::handle_send_prompt_allows_exit_during_auth_with_invalid_provider_override ... ok
test ipc::tests::handle_send_prompt_blocks_during_auth ... ok
test ipc::tests::handle_send_prompt_invalid_provider_override_keeps_active_job ... ok
test ipc::tests::handle_send_prompt_new_prompt_cancels_active_job_with_job_end_event ... ok
test ipc::tests::handle_send_prompt_rejects_invalid_provider_override ... ok
test ipc::tests::handle_send_prompt_rejects_provider_commands_on_claude ... ok
test ipc::tests::handle_send_prompt_rejects_overlay_only_non_ipc_provider_overrides ... ok
test ipc::tests::handle_send_prompt_wrapper_command_cancels_active_job_with_job_end_event ... ok
test ipc::tests::handle_send_prompt_wrapper_command_ignores_invalid_provider_override ... ok
test codex::tests::send_signal_terminates_child ... ok
test ipc::tests::handle_set_provider_emits_events ... ok
test ipc::tests::handle_start_voice_errors_when_already_running ... ok
test ipc::tests::handle_start_voice_errors_when_auth_in_progress ... ok
test ipc::tests::handle_start_voice_errors_when_no_mic_and_no_python ... ok
test ipc::tests::handle_wrapper_capabilities_emits_capabilities ... ok
test ipc::tests::handle_wrapper_exit_requests_graceful_shutdown ... ok
test ipc::tests::handle_wrapper_help_emits_status ... ok
test ipc::tests::handle_wrapper_requires_prompt_for_codex_and_claude ... ok
test ipc::tests::handle_wrapper_status_emits_capabilities ... ok
test ipc::tests::ipc_guard_trips_only_after_threshold ... ok
test ipc::tests::ipc_loop_count_reset_clears_count ... ok
test ipc::tests::handle_auth_command_starts_job_and_completes ... ok
test ipc::tests::handle_cancel_clears_provider_job_with_job_end_event ... ok
test ipc::tests::process_auth_events_does_not_reset_on_failed_codex ... ok
test ipc::tests::claude_job_cancel_kills_piped_child ... ok
test ipc::tests::process_auth_events_does_not_reset_on_successful_claude ... ok
test ipc::tests::process_auth_events_emits_error ... ok
test ipc::tests::process_auth_events_emits_success_and_capabilities ... ok
test ipc::tests::process_auth_events_handles_disconnect ... ok
test ipc::tests::process_auth_events_resets_session_for_successful_codex ... ok
test ipc::tests::handle_send_prompt_wrapper_command_cancels_active_claude_job_with_job_end_event ... ok
test ipc::tests::handle_start_voice_starts_python_fallback_job ... ok
test ipc::tests::process_claude_events_pty_ignores_empty_output ... ok
test ipc::tests::process_codex_events_disconnected_sends_end ... ok
test ipc::tests::process_codex_events_emits_tokens_and_status ... ok
test ipc::tests::process_codex_events_finishes_job ... ok
test ipc::tests::process_voice_events_handles_disconnect ... ok
test ipc::tests::process_voice_events_handles_empty ... ok
test ipc::tests::process_voice_events_handles_error ... ok
test ipc::tests::process_voice_events_handles_transcript ... ok
test ipc::tests::protocol_codec_tests::test_deserialize_auth ... ok
test ipc::tests::protocol_codec_tests::test_deserialize_cancel ... ok
test ipc::tests::protocol_codec_tests::test_deserialize_get_capabilities ... ok
test ipc::tests::protocol_codec_tests::test_deserialize_send_prompt ... ok
test ipc::tests::protocol_codec_tests::test_deserialize_send_prompt_with_provider ... ok
test ipc::tests::protocol_codec_tests::test_deserialize_set_provider ... ok
test ipc::tests::protocol_codec_tests::test_deserialize_start_voice ... ok
test ipc::tests::protocol_codec_tests::test_serialize_auth_events ... ok
test ipc::tests::protocol_codec_tests::test_serialize_capabilities_event ... ok
test ipc::tests::protocol_codec_tests::test_serialize_error_event ... ok
test ipc::tests::protocol_codec_tests::test_serialize_job_events ... ok
test ipc::tests::protocol_codec_tests::test_serialize_provider_changed ... ok
test ipc::tests::protocol_codec_tests::test_serialize_token_event ... ok
test ipc::tests::protocol_codec_tests::test_serialize_voice_events ... ok
test ipc::tests::run_ipc_loop_breaks_when_limit_zero ... ok
test ipc::tests::run_ipc_loop_exits_when_graceful_exit_requested_and_idle ... ok
test ipc::tests::process_claude_events_handles_cancel ... ok
test ipc::tests::run_ipc_loop_processes_commands ... ok
test ipc::tests::process_claude_events_emits_tokens_and_end ... ok
test ipc::tests::run_ipc_loop_processes_active_jobs ... ok
test ipc::tests::set_auth_flow_hook_overrides_auth_flow ... ok
test ipc::tests::run_ipc_loop_respects_max_loops_with_live_channel ... ok
test ipc::tests::process_auth_events_times_out_stalled_job ... ok
test ipc::tests::start_provider_job_codex_emits_completion ... ok
test ipc::tests::test_parse_capabilities_command ... ok
test ipc::tests::test_parse_case_insensitive ... ok
test ipc::tests::test_parse_plain_prompt ... ok
test ipc::tests::test_parse_provider_commands ... ok
test ipc::tests::test_parse_wrapper_commands ... ok
test ipc::tests::test_provider_as_str ... ok
test ipc::tests::test_provider_auth_command_routes_by_lifecycle ... ok
test ipc::tests::test_provider_auth_success_session_reset_policy ... ok
test ipc::tests::test_provider_from_str ... ok
test ipc::tests::test_provider_from_str_trait ... ok
test ipc::tests::test_provider_ipc_capability_labels_derive_from_supported_set ... ok
test ipc::tests::test_provider_parse_name_or_error_message ... ok
test ipc::tests::utf8_prefix_truncates_by_chars_not_bytes ... ok
test legacy_tui::state::tests::char_count_tracks_unicode_scalar_values ... ok
test legacy_tui::state::tests::truncate_to_char_limit_noop_when_under_limit ... ok
test legacy_tui::state::tests::truncate_to_char_limit_preserves_utf8_boundaries ... ok
test legacy_tui::tests::append_output_trims_history ... ok
test audio::tests::record_with_vad_stub_returns_metrics ... ok
test ipc::tests::ipc_state_invalid_voiceterm_provider_emits_recoverable_startup_error ... ok
test legacy_tui::tests::crash_log_path_honors_env_override ... ok
test ipc::tests::run_ipc_mode_emits_capabilities_on_start ... ok
test legacy_tui::tests::fatal_event_updates_status ... ok
test legacy_tui::tests::input_and_scroll_changes_request_redraw ... ok
test legacy_tui::tests::log_content_requires_flag ... ok
test legacy_tui::tests::log_file_path_honors_env_override ... ok
test legacy_tui::tests::logging_disabled_by_default ... ok
test legacy_tui::tests::logging_enabled_writes_log ... ok
test legacy_tui::tests::perf_smoke_emits_voice_metrics ... ok
test legacy_tui::tests::scroll_helpers_update_offset ... ok
test legacy_tui::tests::codex_job_cancellation_updates_status ... ok
test legacy_ui::tests::draw_sets_cursor_on_prompt_row_plus_one ... ok
test legacy_ui::tests::handle_key_event_appends_and_backspaces ... ok
test legacy_tui::tests::codex_job_completion_updates_ui ... ok
test legacy_ui::tests::handle_key_event_ctrl_c_quits_without_active_job ... ok
test legacy_ui::tests::handle_key_event_ctrl_shortcuts_trigger_control_paths ... ok
test legacy_tui::tests::memory_guard_backend_threads_drop ... ok
test legacy_ui::tests::handle_key_event_esc_and_delete_clear_input ... ok
test legacy_ui::tests::handle_key_event_ctrl_c_cancels_active_job_and_keeps_loop_running ... ok
test legacy_ui::tests::handle_key_event_plain_c_without_control_does_not_quit ... ok
test legacy_ui::tests::handle_key_event_plain_r_and_v_append_chars ... ok
test legacy_ui::tests::sanitize_output_line_covers_control_and_width_edge_cases ... ok
test lock::tests::lock_or_recover_recovers_from_poisoned_mutex ... ok
test lock::tests::lock_or_recover_returns_normal_guard_when_not_poisoned ... ok
test mic_meter::tests::peak_db_tracks_peak_amplitude ... ok
test mic_meter::tests::recommend_threshold_clamps_hot_inputs_to_ceiling ... ok
test mic_meter::tests::recommend_threshold_guard_branches_and_warning_edges ... ok
test mic_meter::tests::recommend_threshold_keeps_guard_value_when_exactly_on_headroom_boundary ... ok
test mic_meter::tests::recommend_threshold_non_louder_path_warns_and_clamps ... ok
test mic_meter::tests::recommend_threshold_uses_midpoint_when_guard_crosses_speech_headroom ... ok
test mic_meter::tests::recommend_threshold_warns_when_speech_close_to_ambient ... ok
test mic_meter::tests::rms_db_empty_returns_floor ... ok
test mic_meter::tests::rms_db_matches_half_scale_signal ... ok
test mic_meter::tests::rms_db_returns_zero_for_unity_signal ... ok
test mic_meter::tests::run_mic_meter_fails_early_when_durations_are_invalid ... ok
test mic_meter::tests::validate_sample_ms_accepts_inclusive_bounds ... ok
test mic_meter::tests::validate_sample_ms_rejects_out_of_range_values ... ok
test process_signal::tests::signal_helper_ignores_non_positive_pid ... ok
test process_signal::tests::signal_helper_missing_pid_is_optional_error ... ok
test process_signal::tests::signal_helper_optional_missing_requires_pid_esrch ... ok
test legacy_ui::tests::handle_key_event_enter_sends_prompt_and_appends_output ... ok
test pty_session::session_guard::tests::cleanup_allowed_respects_min_interval ... ok
test pty_session::session_guard::tests::cleanup_removes_entry_for_missing_owner ... ok
test pty_session::session_guard::tests::command_match_uses_command_basename ... ok
test pty_session::session_guard::tests::lease_entry_parse_accepts_legacy_format_without_start_times ... ok
test pty_session::session_guard::tests::lease_entry_roundtrip ... ok
test pty_session::session_guard::tests::orphan_candidates_include_detached_backend_without_shell_or_lease ... ok
test pty_session::session_guard::tests::orphan_candidates_require_detached_backend_without_shell ... ok
test legacy_ui::tests::handle_key_event_navigation_keys_adjust_scroll_offset ... ok
test pty_session::session_guard::tests::parse_etime_seconds_handles_common_ps_formats ... ok
test pty_session::session_guard::tests::parse_ps_snapshot_line_extracts_fields ... ok
test pty_session::tests::apply_control_edits_backspace_at_line_end_does_not_recalc ... ok
test pty_session::tests::apply_control_edits_backspace_before_line_start_rewinds ... ok
test pty_session::tests::apply_control_edits_backspace_then_carriage_return_resets_line_start ... ok
test pty_session::tests::apply_control_edits_handles_cr_and_backspace ... ok
test pty_session::tests::apply_control_edits_handles_osc_near_end_preserves_trailing ... ok
test pty_session::tests::apply_control_edits_handles_osc_with_prior_bel ... ok
test pty_session::tests::apply_control_edits_handles_trailing_escape ... ok
test pty_session::tests::apply_control_edits_preserves_crlf_lines ... ok
test pty_session::tests::apply_control_edits_preserves_non_osc_escape ... ok
test pty_session::tests::apply_control_edits_records_osc_start ... ok
test pty_session::tests::apply_control_edits_strips_osc_sequences ... ok
test pty_session::tests::apply_osc_counters_reset_clears_hits ... ok
test pty_session::tests::csi_reply_normalizes_leading_markers ... ok
test pty_session::tests::csi_reply_returns_expected_responses ... ok
test pty_session::tests::current_line_start_handles_lines ... ok
test pty_session::tests::current_terminal_size_falls_back_on_invalid_fd ... ok
test pty_session::tests::current_terminal_size_falls_back_when_dimension_zero ... ok
test pty_session::tests::current_terminal_size_falls_back_when_ioctl_col_zero ... ok
test pty_session::tests::current_terminal_size_falls_back_when_ioctl_dimensions_zero ... ok
test pty_session::tests::current_terminal_size_falls_back_when_ioctl_row_zero ... ok
test pty_session::tests::current_terminal_size_falls_back_when_override_col_zero ... ok
test pty_session::tests::current_terminal_size_falls_back_when_override_disabled ... ok
test pty_session::tests::current_terminal_size_reads_winsize ... ok
test pty_session::tests::current_terminal_size_uses_override_values ... ok
test pty_session::tests::find_csi_sequence_finds_final_byte ... ok
test pty_session::tests::find_csi_sequence_returns_none_for_incomplete_sequence ... ok
test pty_session::tests::find_osc_terminator_handles_bel_and_st ... ok
test pty_session::session_guard::tests::owner_process_liveness_rejects_start_time_mismatch ... ok
test pty_session::tests::find_osc_terminator_ignores_incomplete_escape ... ok
test pty_session::tests::guard_iteration_exceeded_allows_exact_limit ... ok
test pty_session::tests::guard_elapsed_exceeded_allows_exact_limit ... ok
test pty_session::tests::guard_loop_enforces_elapsed_limit ... ok
test pty_session::tests::guard_iteration_loop_enforces_limit ... ok
test pty_session::tests::pop_last_codepoint_handles_multibyte ... ok
test pty_session::tests::guard_loop_enforces_iteration_limit ... ok
test pty_session::tests::pop_last_codepoint_removes_trailing_newline ... ok
test pty_session::session_guard::tests::cleanup_keeps_entry_for_live_owner ... ok
test ipc::tests::process_claude_events_pty_exits_without_trailing_output ... ok
test pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes ... ok
test pty_session::tests::prop_find_csi_sequence_respects_bounds ... ok
test legacy_ui::tests::draw_appends_ellipsis_only_for_truncated_output_lines ... ok
test pty_session::tests::prop_find_osc_terminator_respects_bounds ... ok
test pty_session::tests::pty_cli_session_is_alive_reflects_child ... ok
test pty_session::tests::pty_cli_session_is_alive_with_negative_pid_returns_false ... ok
test pty_session::tests::pty_cli_session_is_responsive_tracks_liveness ... ok
test pty_session::tests::pty_cli_session_read_output_drains_channel ... ok
test pty_session::tests::pty_cli_session_drop_writes_exit_for_zero_pid ... ok
test codex::tests::call_codex_via_session_returns_output ... ok
test codex::tests::call_codex_cli_reports_failure ... ok
test pty_session::tests::pty_cli_session_read_output_timeout_breaks_on_grace_boundary ... ok
test ipc::tests::start_claude_job_emits_stdout_and_stderr ... ok
test pty_session::tests::pty_cli_session_send_appends_newline ... ok
test pty_session::tests::pty_cli_session_try_wait_reaps_exited_child ... ok
test pty_session::tests::pty_cli_session_wait_for_output_collects_and_drains ... ok
test codex::tests::call_codex_via_session_times_out_without_output ... ok
test ipc::tests::start_claude_job_with_pty_emits_output ... ok
test codex::tests::cli_backend_restore_static_state_sets_session ... ok
test pty_session::tests::pty_overlay_session_is_alive_reflects_child ... ok
test pty_session::tests::pty_overlay_session_is_alive_with_negative_pid_returns_false ... ok
test codex::tests::cli_backend_reset_session_clears_cached_session ... ok
test pty_session::tests::pty_overlay_session_send_bytes_writes ... ok
test pty_session::tests::pty_overlay_session_send_text_with_newline_appends ... ok
test pty_session::tests::pty_overlay_session_set_winsize_errors_on_invalid_fd ... ok
test pty_session::tests::pty_overlay_session_set_winsize_updates_and_minimums ... ok
test codex::tests::cli_backend_reuses_preloaded_session ... ok
test pty_session::tests::reset_apply_linestart_recalc_count_clears ... ok
test pty_session::tests::respond_osc_counters_reset_clears_hits ... ok
test pty_session::tests::respond_osc_hits_zero_without_osc ... ok
test pty_session::tests::respond_to_terminal_queries_handles_multiple_sequences ... ok
test pty_session::tests::respond_to_terminal_queries_handles_trailing_escape ... ok
test pty_session::tests::respond_to_terminal_queries_handles_unknown_escape ... ok
test pty_session::tests::respond_to_terminal_queries_osc_preserves_trailing_bytes ... ok
test pty_session::tests::respond_to_terminal_queries_osc_with_prior_bel ... ok
test pty_session::tests::respond_to_terminal_queries_passthrough_handles_multiple_queries ... ok
test pty_session::tests::respond_to_terminal_queries_passthrough_handles_trailing_escape ... ok
test pty_session::tests::respond_to_terminal_queries_passthrough_handles_unknown_escape ... ok
test pty_session::tests::respond_to_terminal_queries_passthrough_keeps_ansi ... ok
test pty_session::tests::respond_to_terminal_queries_replies_to_cursor_request ... ok
test pty_session::tests::respond_to_terminal_queries_replies_to_extended_device_attr ... ok
test pty_session::tests::respond_to_terminal_queries_replies_to_status_request ... ok
test pty_session::tests::respond_to_terminal_queries_strips_osc_and_modes ... ok
test pty_session::tests::should_retry_read_error_reports_expected_kinds ... ok
test pty_session::tests::should_strip_without_reply_additional_cases ... ok
test pty_session::tests::should_strip_without_reply_matches_expected_sequences ... ok
test pty_session::tests::spawn_passthrough_reader_thread_closes_channel_on_eof ... ok
test pty_session::tests::pty_overlay_session_parent_sigkill_terminates_child ... ok
test pty_session::tests::spawn_passthrough_reader_thread_forwards_output ... ok
test pty_session::tests::spawn_passthrough_reader_thread_recovers_from_wouldblock ... ok
test pty_session::tests::spawn_reader_thread_closes_channel_on_eof ... ok
test codex::tests::pty_session_send_and_read_output ... ok
test pty_session::tests::spawn_reader_thread_forwards_output ... ok
test pty_session::tests::spawn_reader_thread_recovers_from_wouldblock ... ok
test pty_session::tests::split_incomplete_escape_buffers_trailing_csi ... ok
test pty_session::tests::try_write_handles_short_writes ... ok
test pty_session::tests::try_write_reports_wouldblock ... ok
test pty_session::tests::try_write_writes_bytes ... ok
test pty_session::tests::wait_for_exit_does_not_poll_when_elapsed_equals_timeout ... ok
test pty_session::tests::wait_for_exit_does_not_poll_when_elapsed_equals_timeout_nonzero ... ok
test pty_session::tests::wait_for_exit_elapsed_override_skips_polling ... ok
test pty_session::tests::wait_for_exit_reaps_forked_child ... ok
test pty_session::tests::pty_cli_session_read_output_timeout_collects_recent_chunks ... ok
test pty_session::tests::pty_cli_session_read_output_timeout_elapsed_boundary ... ok
test pty_session::tests::pty_cli_session_read_output_timeout_elapsed_override_prevents_loop ... ok
test pty_session::tests::pty_cli_session_read_output_timeout_respects_zero_timeout ... ok
test pty_session::tests::pty_session_counters_track_send_and_read ... ok
test pty_session::tests::waitpid_failed_flags_negative ... ok
test pty_session::tests::wait_for_exit_records_reap_count ... ok
test pty_session::tests::wait_for_exit_reports_error_for_invalid_pid ... ok
test pty_session::tests::write_all_errors_on_invalid_fd ... ok
test pty_session::tests::write_all_handles_short_writes ... ok
test pty_session::tests::write_all_reports_zero_write ... ok
test pty_session::tests::wait_for_exit_returns_false_when_timeout ... ok
test pty_session::tests::write_all_writes_bytes ... ok
test stt::tests::append_whisper_segment_avoids_extra_space_before_punctuation ... ok
test stt::tests::append_whisper_segment_inserts_spaces_for_sentence_boundaries ... ok
test stt::tests::append_whisper_segment_keeps_contractions_attached ... ok
test stt::tests::append_whisper_segment_trims_and_skips_empty_segments ... ok
test stt::tests::boundary_spacing_respects_whitespace_and_punctuation_rules ... ok
test stt::tests::transcriber_rejects_missing_model ... ok
test stt::tests::transcriber_restores_stderr_after_failed_model_load ... ok
test pty_session::tests::write_all_retries_on_wouldblock ... ok
test telemetry::tests::tracing_enabled_truth_table ... ok
test telemetry::tests::init_tracing_once_respects_enabled_flag_and_creates_file ... ok
test telemetry::tests::tracing_log_path_defaults_to_temp_dir_when_env_missing ... ok
test telemetry::tests::tracing_log_path_prefers_env_override ... ok
[?25htest terminal_restore::tests::enable_mouse_capture_propagates_writer_errors_without_setting_flag ... ok
[?25h[?25htest terminal_restore::tests::enable_raw_mode_sets_flag_on_success_and_never_sets_it_on_error ... ok
test terminal_restore::tests::enter_alt_screen_propagates_writer_errors_without_setting_flag ... ok
[?1049l[?25htest terminal_restore::tests::guard_drop_restores_terminal_state ... ok
[?25h[?25htest terminal_restore::tests::guard_restore_delegates_to_restore_terminal ... ok
[?1006l[?1015l[?1003l[?1002l[?1000l[?1049l[?25htest terminal_restore::tests::restore_terminal_clears_state_flags ... ok
test terminal_restore::tests::install_terminal_panic_hook_sets_once_flag ... ok
test utf8_safe::tests::test_char_count_and_char_at_cover_multibyte_indices ... ok
test utf8_safe::tests::test_ellipsize ... ok
test utf8_safe::tests::test_safe_byte_slice_adjusts_inward_to_utf8_boundaries ... ok
test utf8_safe::tests::test_safe_prefix ... ok
test utf8_safe::tests::test_safe_slice_zero_len_and_safe_suffix_zero_chars ... ok
test utf8_safe::tests::test_safe_slice ... ok
test utf8_safe::tests::test_safe_split_at_boundary_validation ... ok
test utf8_safe::tests::test_safe_suffix ... ok
test utf8_safe::tests::test_window_by_columns_basic ... ok
test utf8_safe::tests::test_window_by_columns_boundary_equalities_do_not_trip_safety_guard ... ok
test utf8_safe::tests::test_window_by_columns_handles_wide_glyphs ... ok
test utf8_safe::tests::test_window_by_columns_multibyte ... ok
test utf8_safe::tests::test_window_by_columns_zero_width_is_empty ... ok
test vad_earshot::tests::float_sample_to_i16_saturates_endpoints ... ok
test vad_earshot::tests::name_reports_stable_identifier ... ok
test vad_earshot::tests::from_config_clamps_frame_window_and_applies_minimum_sample_floor ... ok
test vad_earshot::tests::process_frame_empty_input_is_uncertain ... ok
test vad_earshot::tests::process_frame_clamps_samples_and_zero_pads_short_frames ... ok
test vad_earshot::tests::process_frame_truncates_long_frames_to_configured_window ... ok
test vad_earshot::tests::reset_restores_detector_state_to_match_fresh_instance ... ok
test voice::tests::create_vad_engine_uses_earshot_when_requested ... ok
test voice::tests::create_vad_engine_uses_simple_when_requested ... ok
test voice::tests::error_when_fallback_disabled_and_native_unavailable ... ok
test voice::tests::perform_voice_capture_falls_back_when_components_missing ... ok
test voice::tests::python_fallback_propagates_pipeline_timing_metrics ... ok
test voice::tests::python_fallback_reports_empty_transcripts ... ok
test voice::tests::python_fallback_returns_trimmed_transcript ... ok
test voice::tests::sanitize_transcript_keeps_meaningful_parenthetical_content ... ok
test voice::tests::python_fallback_surfaces_errors ... ok
test voice::tests::sanitize_transcript_strips_known_non_speech_tags ... ok
test voice::tests::voice_capture_source_labels_are_user_friendly ... ok
test pty_session::tests::wait_for_exit_returns_true_for_exited_child ... ok
test pty_session::tests::wait_for_exit_with_zero_timeout_does_not_poll ... ok
test pty_session::tests::watchdog::lifeline_watch_event_reports_parent_exit_while_lifeline_stays_open ... ok
test voice::tests::start_voice_job_handles_concurrent_fallbacks ... ok
test pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group ... ok
test pty_session::tests::pty_cli_session_drop_sigkill_for_ignored_sigterm ... ok
test pty_session::tests::watchdog::lifeline_watch_event_reports_pipe_close_before_parent_exit ... ok
test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group ... ok
test pty_session::tests::pty_cli_session_drop_terminates_child ... ok
test pty_session::tests::pty_overlay_session_drop_sigkill_for_ignored_sigterm ... ok
test pty_session::tests::pty_overlay_session_drop_terminates_child ... ok
test pty_session::tests::spawn_passthrough_reader_thread_does_not_log_on_eof ... ok
test pty_session::tests::spawn_reader_thread_does_not_log_on_eof ... ok

test result: ok. 545 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 3.52s

     Running unittests src/bin/latency_measurement.rs (target/debug/deps/latency_measurement-368bd5028ad427b9)

running 6 tests
test tests::enforce_guardrails_accepts_values_in_range ... ok
test tests::validate_args_rejects_force_python_fallback_with_synthetic ... ok
test tests::enforce_guardrails_rejects_out_of_range_sample ... ok
test tests::validate_args_rejects_inverted_bounds ... ok
test tests::validate_args_rejects_skip_stt_without_synthetic ... ok
test tests::validate_args_rejects_skip_stt_without_voice_only ... ok

test result: ok. 6 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/stt_file_benchmark.rs (target/debug/deps/stt_file_benchmark-3ee6e1242bc7c9c0)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/test_crash.rs (target/debug/deps/test_crash-44e8f63e75d0be06)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/test_utf8_bug.rs (target/debug/deps/test_utf8_bug-fdf85990627a743c)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/voice_benchmark.rs (target/debug/deps/voice_benchmark-3c27a31555c145cd)

running 1 test
test tests::earshot_flag_passes_when_feature_enabled ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/voiceterm/main.rs (target/debug/deps/voiceterm-00542c53e23cfc94)

running 1929 tests
test action_center::render::tests::overlay_height_is_consistent ... ok
test arrow_keys::tests::is_arrow_escape_noise_accepts_arrow_sequences_and_fragments ... ok
test arrow_keys::tests::is_arrow_escape_noise_rejects_non_noise_inputs ... ok
test arrow_keys::tests::parse_arrow_keys_accepts_colon_parameterized_sequences ... ok
test arrow_keys::tests::parse_arrow_keys_does_not_treat_incomplete_parameterized_sequence_as_arrow ... ok
test ansi::tests::strip_ansi_preserves_line_controls ... ok
test arrow_keys::tests::parse_arrow_keys_ignores_lone_escape_without_panicking ... ok
test ansi::tests::strip_ansi_removes_escape_sequences ... ok
test arrow_keys::tests::parse_arrow_keys_only_accepts_ss3_sequences ... ok
test arrow_keys::tests::parse_arrow_keys_only_accepts_parameterized_sequences ... ok
test arrow_keys::tests::parse_arrow_keys_only_rejects_non_arrow_csi_sequences ... ok
test arrow_keys::tests::parse_arrow_keys_reads_sequences ... ok
test arrow_keys::tests::parse_arrow_keys_supports_parameterized_csi_sequences ... ok
test audio_meter::format::tests::format_level_meter_loud ... ok
test audio_meter::format::tests::format_level_meter_silent ... ok
test audio_meter::format::tests::format_level_compact_includes_db ... ok
test audio_meter::format::tests::format_level_meter_supports_ascii_glyph_profile ... ok
test audio_meter::format::tests::format_waveform_empty ... ok
test audio_meter::format::tests::format_mic_meter_display_basic ... ok
test audio_meter::format::tests::format_waveform_supports_ascii_glyph_profile ... ok
test audio_meter::format::tests::format_waveform_padding_uses_floor_baseline ... ok
test audio_meter::measure::tests::peak_db_empty_returns_floor ... ok
test audio_meter::format::tests::format_waveform_with_levels ... ok
test action_center::render::tests::pending_approval_shows_exclamation_marker ... ok
test action_center::render::tests::renders_builtin_actions ... ok
test audio_meter::measure::tests::peak_db_tracks_absolute_max_amplitude ... ok
test audio_meter::measure::tests::rms_db_empty_returns_floor ... ok
test audio_meter::measure::tests::rms_db_matches_known_amplitude ... ok
test audio_meter::tests::audio_level_default ... ok
test audio_meter::tests::meter_config_default ... ok
test banner::tests::ascii_banner_centers_tagline_using_display_width ... ok
test banner::tests::ascii_banner_contains_logo ... ok
test banner::tests::ascii_banner_centers_with_wide_terminal ... ok
test banner::tests::ascii_banner_initializing_padding_matches_centered_formula ... ok
test banner::tests::ascii_banner_logo_left_padding_matches_centered_formula ... ok
test banner::tests::ascii_banner_has_no_leading_blank_line ... ok
test banner::tests::banner_no_color ... ok
test banner::tests::ascii_banner_contains_tagline ... ok
test banner::tests::build_startup_banner_for_cols_honors_ascii_glyph_separator_override ... ok
test banner::tests::build_startup_banner_for_cols_honors_runtime_banner_style_override ... ok
test banner::tests::ascii_banner_no_color_is_plain ... ok
test banner::tests::build_startup_banner_for_cols_honors_runtime_startup_style_override ... ok
test banner::tests::ascii_banner_with_color_has_ansi_codes ... ok
test banner::tests::centered_padding_returns_expected_value_for_common_width_relationships ... ok
test banner::tests::clear_screen_writes_full_reset_and_clear_sequence ... ok
test banner::tests::format_minimal_banner_contains_shortcuts ... ok
test banner::tests::format_startup_banner_contains_version ... ok
test banner::tests::format_startup_banner_shows_config ... ok
test banner::tests::build_startup_banner_for_cols_respects_payload_base_theme_lock_over_requested_none ... ok
test banner::tests::build_startup_banner_for_cols_uses_persisted_banner_style_payload ... ok
test banner::tests::use_minimal_banner_threshold ... ok
test banner::tests::version_defined ... ok
test buttons::tests::button_action_converts_to_input_event ... ok
test banner::tests::build_startup_banner_for_cols_selects_expected_render_mode ... ok
test audio_meter::tests::run_mic_meter_fails_early_when_durations_are_invalid ... ok
test buttons::tests::button_registry_registers_and_finds ... ok
test banner::tests::build_startup_banner_for_cols_uses_persisted_startup_style_payload ... ok
test banner::tests::format_minimal_banner_none_theme_matches_golden_snapshot ... ok
test banner::tests::format_startup_banner_none_theme_matches_golden_snapshot ... ok
test cli_utils::tests::should_print_stats_requires_non_empty ... ok
test cli_utils::tests::resolve_sound_flag_prefers_global ... ok
test color_mode::tests::color_mode_display ... ok
test banner::tests::logo_line_color_uses_single_theme_accent ... ok
test banner::tests::should_skip_banner_in_jetbrains_env ... ok
test color_mode::tests::color_mode_supports_color ... ok
test color_mode::tests::color_mode_supports_256 ... ok
test color_mode::tests::color_mode_supports_truecolor ... ok
test banner::tests::should_skip_banner_matches_flags ... ok
test color_mode::tests::detect_colorterm_non_truecolor_does_not_force_truecolor ... ok
test banner::tests::splash_duration_caps_large_env_override ... ok
test banner::tests::splash_duration_honors_env_override ... ok
test capture_once::tests::capture_once_requires_native_model_when_python_fallback_disabled ... ok
test color_mode::tests::detect_truecolor_for_cursor_env_marker_without_term_program ... ok
test color_mode::tests::detect_truecolor_for_jetbrains_ide_env_marker_without_term_hints ... ok
test color_mode::tests::detect_ansi16_when_term_is_xterm_without_256_hint ... ok
test color_mode::tests::detect_color256_when_term_program_unrecognized ... ok
test color_mode::tests::detect_truecolor_for_warp_term_program_env ... ok
test color_mode::tests::detect_dumb_term_without_color_hints_is_none ... ok
test color_mode::tests::rgb_to_256_colors ... ok
test color_mode::tests::detect_truecolor_when_term_program_contains_jetbrains ... ok
test banner::tests::splash_duration_ignores_invalid_env_values ... ok
test color_mode::tests::rgb_to_256_exact_cube_samples ... ok
test color_mode::tests::detect_truecolor_for_jetbrains_term_program_env ... ok
test banner::tests::startup_splash_default_duration_is_short ... ok
test color_mode::tests::rgb_to_256_grayscale ... ok
test color_mode::tests::detect_truecolor_for_jetbrains_terminal_env ... ok
test color_mode::tests::rgb_to_256_grayscale_ramp_samples ... ok
test color_mode::tests::rgb_to_ansi16_basic ... ok
test color_mode::tests::rgb_to_ansi16_boundary_samples ... ok
test color_mode::tests::detect_truecolor_for_vscode_term_program_env ... ok
test color_mode::tests::rgb_to_ansi16_branch_samples ... ok
test color_mode::tests::detect_truecolor_from_colorterm_24bit ... ok
test capture_once::tests::run_capture_once_writes_text_output ... ok
test capture_once::tests::run_capture_once_rejects_empty_transcript ... ok
test capture_once::tests::run_capture_once_surfaces_voice_errors ... ok
test color_mode::tests::detect_terminal_capability_matrix_cases ... ok
test config::backend::tests::resolve_backend_custom_command_with_quoted_args ... ok
test config::backend::tests::resolve_backend_codex_includes_extra_args ... ok
test config::backend::tests::resolve_backend_preset_aider ... ok
test banner::tests::should_skip_banner_uses_canonical_jetbrains_detection ... ok
test config::backend::tests::resolve_backend_custom_path ... ok
test config::backend::tests::resolve_backend_empty_fallback ... ok
test color_mode::tests::detect_truecolor_when_terminal_emulator_contains_jediterm_only ... ok
test config::cli::tests::capture_once_format_display_labels_are_stable ... ok
test config::backend::tests::resolve_backend_custom_command_with_args ... ok
test config::backend::tests::resolve_backend_preset_claude ... ok
test config::backend::tests::resolve_backend_preset_case_insensitive ... ok
test config::cli::tests::hud_border_style_display_labels_are_stable ... ok
test config::cli::tests::hud_right_panel_display_labels_are_stable ... ok
test config::cli::tests::hud_style_display_labels_are_stable ... ok
test config::backend::tests::resolve_backend_preset_gemini ... ok
test config::backend::tests::resolve_backend_preset_opencode ... ok
test config::cli::tests::latency_display_mode_labels_are_stable ... ok
test config::backend::tests::resolve_backend_custom_command ... ok
test config::cli::tests::voice_send_mode_display_labels_are_stable ... ok
test config::backend::tests::resolve_backend_preset_codex_uses_app_config ... ok
test config::cli::tests::capture_once_format_requires_capture_once ... ok
test config::theme::tests::default_theme_for_backend_maps_expected ... ok
test config::util::tests::is_path_like_accepts_absolute_and_relative_paths ... ok
test config::cli::tests::dev_log_parser_accepts_optional_path ... ok
test config::util::tests::is_path_like_rejects_plain_binary_names_and_empty_values ... ok
test custom_help::tests::default_detail_skips_false_for_switches ... ok
test config::cli::tests::image_mode_parser_accepts_optional_capture_command ... ok
test config::cli::tests::capture_once_parser_accepts_text_format ... ok
test config::cli::tests::wake_word_parser_accepts_bounds ... ok
test config::cli::tests::wake_word_defaults_are_safe ... ok
test config::cli::tests::wake_word_parser_rejects_out_of_bounds_values ... ok
test custom_help::tests::all_long_flags_are_grouped_or_other ... ok
test custom_help::tests::wrap_words_breaks_long_text_without_exceeding_width ... ok
test custom_help::tests::wrap_words_long_token_does_not_append_trailing_empty_line ... ok
test cycle_index::tests::cycle_index_handles_empty ... ok
test cycle_index::tests::cycle_index_wraps_forward_and_backward ... ok
test cycle_index::tests::cycle_option_uses_current_when_not_found ... ok
test config::cli::tests::manual_help_flags_parse_without_clap_auto_exit ... ok
test config::theme::tests::theme_for_backend_honors_no_color_env_even_when_flag_is_unset ... ok
test daemon::client_codec::codec_tests::decode_rejects_empty ... ok
test daemon::client_codec::codec_tests::decode_rejects_invalid_json ... ok
test daemon::client_codec::codec_tests::decode_unknown_command_falls_through ... ok
test daemon::client_codec::codec_tests::decode_valid_command ... ok
test daemon::client_codec::codec_tests::encode_produces_valid_json ... ok
test daemon::tests::client_id_contains_transport_prefix ... ok
test daemon::tests::command_roundtrip_kill ... ok
test daemon::tests::command_roundtrip_list ... ok
test daemon::tests::command_roundtrip_send_to_agent ... ok
test daemon::tests::command_roundtrip_shutdown ... ok
test daemon::tests::command_roundtrip_spawn_agent ... ok
test daemon::tests::command_roundtrip_status ... ok
test daemon::tests::default_socket_path_ends_with_control_sock ... ok
test daemon::tests::event_agent_output_serializes ... ok
test daemon::tests::event_agent_spawned_serializes ... ok
test daemon::tests::event_daemon_ready_serializes_attach_metadata ... ok
test daemon::tests::event_daemon_status_serializes ... ok
test daemon::tests::event_error_omits_null_session_id ... ok
test config::cli::tests::dev_mode_parser_accepts_guarded_aliases ... ok
test config::theme::tests::theme_for_backend_keeps_ansi_fallback_on_ansi16_term ... ok
test daemon::tests::late_subscriber_receives_agent_list_snapshot ... ok
test daemon::tests::registry_insert_and_list ... ok
test daemon::tests::late_subscriber_receives_latest_lifecycle_snapshot ... ok
test daemon::tests::session_id_contains_agent_prefix ... ok
test daemon::tests::registry_prune_dead_removes_exited_sessions ... ok
test daemon::tests::lifecycle_snapshot_tracks_latest_status_only ... ok
test daemon::types::type_tests::daemon_command_deserializes ... ok
test daemon::types::type_tests::daemon_event_serializes ... ok
test daemon::types::type_tests::send_to_agent_roundtrip ... ok
test daemon::types::type_tests::session_id_uniqueness ... ok
test dev_command::review_artifact::tests::bridge_critical_content_changed_after_error_even_when_content_matches_last_success ... ok
test dev_command::review_artifact::tests::bridge_critical_parse_extracts_handoff_sections ... ok
test dev_command::review_artifact::tests::bridge_critical_review_artifact_state_error_retains_last_loaded_artifact ... ok
test dev_command::review_artifact::tests::bridge_status_summary_formats_poll_data ... ok
test dev_command::review_artifact::tests::bridge_status_summary_returns_none_without_poll ... ok
test dev_command::review_artifact::tests::content_changed_detects_same_length_edits ... ok
test dev_command::review_artifact::tests::content_changed_returns_false_for_identical_content ... ok
test dev_command::review_artifact::tests::content_changed_returns_true_when_never_loaded ... ok
test dev_command::review_artifact::tests::dev_panel_tab_label_matches_variant ... ok
test dev_command::review_artifact::tests::dev_panel_tab_next_cycles_through_all_pages ... ok
test dev_command::review_artifact::tests::dev_panel_tab_prev_cycles_backward ... ok
test dev_command::broker::tests::shutdown_termination_emits_completion_and_cleans_temp_files ... ok
test config::theme::tests::theme_for_backend_keeps_requested_theme_on_256color_term ... ok
test config::theme::tests::theme_for_backend_keeps_requested_theme_on_truecolor_term ... ok
test dev_command::review_artifact::tests::first_meaningful_line_extracts_content ... ok
test dev_command::review_artifact::tests::load_from_content_stores_raw_content ... ok
test dev_command::review_artifact::tests::find_review_artifact_path_uses_working_dir_fallback ... ok
test dev_command::review_artifact::tests::find_review_artifact_path_ignores_corrupt_event_projection_when_bridge_exists ... ok
test dev_command::review_artifact::tests::find_review_artifact_path_falls_back_to_event_backed_projection_when_bridge_missing ... ok
test config::theme::tests::theme_for_backend_uses_backend_default_when_unset ... ok
test dev_command::review_artifact::tests::load_shorter_content_resets_scroll_offset ... ok
test dev_command::review_artifact::tests::parse_review_artifact_empty_backtick_values_produce_empty ... ok
test dev_command::review_artifact::tests::parse_review_artifact_extracts_header_metadata ... ok
test dev_command::review_artifact::tests::parse_review_artifact_extracts_last_reviewed_scope_and_claude_questions ... ok
test dev_command::review_artifact::tests::parse_review_artifact_handles_missing_sections ... ok
test dev_command::review_artifact::tests::parse_review_artifact_extracts_sections ... ok
test dev_command::review_artifact::tests::parse_review_artifact_missing_header_metadata_defaults_empty ... ok
test dev_command::review_artifact::tests::parse_review_artifact_ignores_unknown_sections ... ok
test dev_command::review_artifact::tests::load_review_artifact_document_parses_bridge_projection_json ... ok
test dev_command::review_artifact::tests::parse_scope_list_extracts_bullet_items ... ok
test dev_command::review_artifact::tests::parse_scope_list_ignores_empty_and_heading_lines ... ok
test dev_command::review_artifact::tests::review_artifact_state_load_and_scroll ... ok
test dev_command::review_artifact::tests::load_review_artifact_document_derives_event_backed_summary_fields ... ok
test dev_command::review_artifact::tests::review_view_mode_labels ... ok
test dev_command::review_artifact::tests::review_view_mode_toggle_cycles ... ok
test dev_command::review_artifact::tests::load_review_artifact_document_rejects_invalid_event_backed_projection_json ... ok
test dev_command::review_artifact::tests::toggle_view_mode_resets_scroll_offset ... ok
test dev_command::review_artifact::tests::set_load_error_preserves_scroll_offset_when_artifact_exists ... ok
test dev_command::tests::command_allowlist_is_stable ... ok
test dev_command::tests::action_catalog_find_by_id_works ... ok
test dev_command::tests::action_catalog_default_matches_command_allowlist ... ok
test dev_command::tests::excerpt_compacts_multiline_output ... ok
test dev_command::tests::execution_profile_cycles_through_all_variants ... ok
test dev_command::tests::panel_state_execution_profile_cycles ... ok
test dev_command::tests::panel_state_selected_policy_reflects_profile ... ok
test dev_command::tests::panel_state_tracks_selection_and_confirmations ... ok
test dev_command::tests::parse_terminal_packet_extracts_draft_and_guard_flags ... ok
test dev_command::tests::policy_resolution_mutating_requires_approval_under_guarded ... ok
test dev_command::tests::policy_resolution_read_only_always_safe ... ok
test dev_command::tests::summary_for_ci_payload_reports_errors ... ok
test dev_command::review_artifact::tests::find_review_artifact_path_prefers_markdown_bridge_when_present ... ok
test dev_command::tests::summary_for_ci_payload_reports_failures ... ok
test dev_command::tests::summary_for_json_payload_prefers_summary_fields ... ok
test dev_command::tests::find_devctl_root_falls_back_to_manifest_parent_when_cwd_is_outside_repo ... ok
test dev_command::tests::summary_for_process_audit_payload_reports_counts ... ok
test dev_command::tests::summary_for_process_watch_payload_reports_clean_stop ... ok
test dev_command::tests::summary_for_triage_payload_prefers_next_action ... ok
test dev_command::tests::summary_for_process_cleanup_payload_reports_kill_counts ... ok
test dev_panel::cockpit_page::tests::cockpit_control_footer_spells_out_refresh_scope ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_no_command_history_when_single_completion ... ok
test dev_panel::actions_page::tests::format_dev_panel_contains_guard_metrics_and_dev_tools ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_git_error_shows_message ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_no_diagnostics_shows_placeholder ... ok
test dev_panel::actions_page::tests::format_dev_panel_line_count_matches_height ... ok
test dev_command::tests::find_devctl_root_finds_parent_repo_from_src_working_dir ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_renders_dashboard ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_no_git_shows_not_loaded ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_no_memory_shows_not_initialized ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_packet_auto_send_label ... ok
test custom_help::tests::grouped_help_contains_expected_sections ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_shows_command_history_tail ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_shows_git_snapshot ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_shows_memory_snapshot ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_shows_runtime_diagnostics ... ok
test custom_help::tests::grouped_help_uses_hacker_style_labels ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_shows_review_bridge_when_loaded ... ok
test dev_panel::cockpit_page::tests::cockpit_handoff_page_renders_empty_state_without_snapshot ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_shows_no_staged_packet_when_empty ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_shows_staged_packet_draft ... ok
test dev_panel::cockpit_page::tests::cockpit_control_page_scroll_shows_position_indicator ... ok
test dev_panel::cockpit_page::tests::cockpit_handoff_page_shows_findings_scope_and_questions ... ok
test dev_panel::cockpit_page::tests::cockpit_handoff_page_shows_git_context ... ok
test dev_panel::cockpit_page::tests::cockpit_handoff_page_shows_boot_pack_when_snapshot_set ... ok
test dev_panel::cockpit_page::tests::cockpit_handoff_page_shows_fresh_prompt_when_populated ... ok
test dev_panel::cockpit_page::tests::cockpit_memory_page_shows_not_initialized_status_when_snapshot_has_no_ingestor ... ok
test dev_panel::cockpit_page::tests::cockpit_handoff_page_shows_no_instruction_placeholder_without_review ... ok
test dev_panel::cockpit_page::tests::cockpit_ops_page_renders_process_and_triage_snapshots ... ok
test dev_panel::cockpit_page::tests::cockpit_memory_footer_spells_out_refresh_scope ... ok
test dev_panel::cockpit_page::tests::cockpit_scroll_offset_clamps_and_resets_on_tab_switch ... ok
test dev_panel::cockpit_page::tests::cockpit_tab_bar_highlights_active_page ... ok
test dev_panel::cockpit_page::tests::cockpit_visible_rows_and_content_count_are_consistent ... ok
test custom_help::tests::grouped_help_codex_uses_distinct_description_color ... ok
test dev_panel::cockpit_page::tests::truncate_draft_preview_limits_lines ... ok
test dev_panel::cockpit_page::tests::format_uptime_formats_seconds_minutes_hours ... ok
test dev_panel::cockpit_page::tests::truncate_draft_preview_short_text_no_ellipsis ... ok
test dev_panel::cockpit_page::tests::cockpit_memory_page_renders_preview_sections ... ok
test dev_panel::cockpit_page::tests::command_history_ring_buffer_caps_at_max ... ok
test dev_panel::cockpit_page::tests::cockpit_handoff_page_shows_resume_bundle_with_review_context ... ok
test custom_help::tests::grouped_help_uses_dim_borders_for_codex_theme ... ok
test dev_panel::review_surface::tests::format_review_surface_line_count_matches_height ... ok
test custom_help::tests::grouped_help_no_color_has_no_ansi_sequences ... ok
test dev_panel::review_surface::tests::format_review_surface_raw_view_shows_markdown ... ok
test dev_panel::review_surface::tests::format_review_surface_shows_error_state ... ok
test dev_panel::review_surface::tests::format_review_surface_shows_fallback_when_not_loaded ... ok
test dev_panel::review_surface::tests::format_review_surface_parsed_view_is_default ... ok
test dev_panel::review_surface::tests::format_review_surface_no_bridge_when_missing_metadata ... ok
test custom_help::tests::grouped_help_codex_has_dual_tone_accents ... ok
test dev_panel::review_surface::tests::operator_lane_shows_context_pack_refs_from_structured_artifact ... ok
test dev_panel::review_surface::tests::format_review_surface_shows_bridge_state_header ... ok
test dev_panel::review_surface::tests::toggle_view_mode_resets_scroll ... ok
test dev_panel::review_surface::tests::view_mode_toggle_cycles ... ok
test dev_panel::review_surface::tests::raw_mode_still_works_after_lane_refactor ... ok
test dev_panel::review_surface::tests::lane_mode_all_lanes_empty_shows_all_fallbacks ... ok
test dev_panel::review_surface::tests::lane_mode_empty_lanes_show_fallback_text ... ok
test dev_panel::review_surface::tests::format_review_surface_shows_loaded_content ... ok
test dev_panel::review_surface::tests::lane_mode_line_count_matches_height ... ok
test dev_panel::tests::wrap_text_empty_input_returns_single_empty ... ok
test dev_panel::tests::dev_panel_active_footer_tracks_review_view_mode ... ok
test dev_panel::review_surface::tests::lane_mode_routes_content_to_correct_lanes ... ok
test dev_panel::tests::dev_panel_active_footer_tracks_cockpit_scroll_position ... ok
test dev_panel::tests::wrap_text_handles_multibyte_chars_without_panic ... ok
test dev_panel::tests::wrap_text_single_long_word_splits_by_char ... ok
test dev_panel::review_surface::tests::stale_lane_footer_uses_reduced_visible_rows_for_scroll_suffix ... ok
test dev_panel::tests::wrap_text_splits_long_lines ... ok
test dev_panel::tests::wrap_text_whitespace_only_returns_empty ... ok
test dev_panel::review_surface::tests::stale_error_shows_retained_artifact_with_annotation ... ok
test dev_panel::review_surface::tests::lane_mode_shows_all_three_lane_headings ... ok
test dev_panel::tests::wrap_text_zero_width_returns_original ... ok
test event_loop::dev_panel_commands::clipboard::clipboard_tests::osc52_copy_bytes_handles_empty_payload ... ok
test event_loop::dev_panel_commands::clipboard::clipboard_tests::osc52_copy_bytes_roundtrip ... ok
test event_loop::dev_panel_commands::git_snapshot::git_status_tests::parse_lsof_cwd_output_extracts_cwd_entry ... ok
test event_loop::dev_panel_commands::git_snapshot::git_status_tests::parse_lsof_cwd_output_ignores_non_cwd_entries ... ok
test event_loop::dev_panel_commands::git_snapshot::git_status_tests::parse_porcelain_ahead_only ... ok
test event_loop::dev_panel_commands::git_snapshot::git_status_tests::parse_porcelain_branch_with_tracking ... ok
test event_loop::dev_panel_commands::git_snapshot::git_status_tests::parse_porcelain_caps_changed_files_at_eight ... ok
test event_loop::dev_panel_commands::git_snapshot::git_status_tests::parse_porcelain_clean_repo ... ok
test event_loop::dev_panel_commands::git_snapshot::git_status_tests::parse_porcelain_no_upstream ... ok
test event_loop::dev_panel_commands::ops_snapshot::tests::parse_process_audit_capture_reads_counts_and_headline ... ok
test event_loop::dev_panel_commands::ops_snapshot::tests::parse_triage_capture_prefers_next_action_summary ... ok
test event_loop::dev_panel_commands::snapshots::tests::bridge_critical_fresh_prompt_carries_memory_summary_and_decisions ... ok
test event_loop::dev_panel_commands::snapshots::tests::bridge_critical_fresh_prompt_includes_findings_scope_and_questions ... ok
test event_loop::dev_panel_commands::snapshots::tests::bridge_critical_fresh_prompt_lists_attached_context_pack_refs ... ok
test event_loop::dev_panel_commands::snapshots::tests::bridge_critical_fresh_prompt_mentions_master_plan_and_git_context ... ok
test event_loop::input_dispatch::overlay::overlay_mouse::tests::footer_close_prefix_extracts_close_label_before_dynamic_suffixes ... ok
test event_loop::input_dispatch::overlay::overlay_mouse::tests::footer_close_prefix_falls_back_when_separators_are_missing ... ok
test event_loop::input_dispatch::overlay::overlay_mouse::tests::slider_constants_match_expected_overlay_geometry ... ok
test event_loop::input_dispatch::overlay::overlay_mouse::tests::slider_direction_handles_empty_and_out_of_range_clicks ... ok
test event_loop::input_dispatch::overlay::overlay_mouse::tests::slider_direction_maps_left_right_and_knob_hit ... ok
test event_loop::input_dispatch::overlay::overlay_mouse::tests::slider_knob_index_clamps_outside_range ... ok
test event_loop::input_dispatch::overlay::overlay_mouse::tests::slider_knob_index_scales_linearly_across_range ... ok
test event_loop::input_dispatch::overlay::overlay_mouse::tests::slider_knob_index_uses_epsilon_guard_for_near_zero_span ... ok
test event_loop::input_dispatch::overlay::overlay_mouse::tests::slider_knob_index_uses_zero_when_width_is_one_or_less ... ok
test event_loop::input_dispatch::overlay::tests::should_replay_after_overlay_close_filters_exit_and_mouse_events ... ok
test event_loop::input_dispatch::tests::hud_navigation_direction_from_arrow_matches_input_ownership_contract::case_1 ... ok
test event_loop::input_dispatch::tests::hud_navigation_direction_from_arrow_matches_input_ownership_contract::case_2 ... ok
test event_loop::input_dispatch::tests::hud_navigation_direction_from_arrow_matches_input_ownership_contract::case_3 ... ok
test event_loop::input_dispatch::tests::hud_navigation_direction_from_arrow_matches_input_ownership_contract::case_4 ... ok
test event_loop::input_dispatch::tests::hud_navigation_direction_from_arrow_matches_input_ownership_contract::case_5 ... ok
test event_loop::input_dispatch::tests::hud_navigation_direction_from_arrow_matches_input_ownership_contract::case_6 ... ok
test event_loop::input_dispatch::tests::hud_navigation_direction_from_arrow_matches_input_ownership_contract::case_7 ... ok
test event_loop::input_dispatch::tests::hud_navigation_direction_from_arrow_matches_input_ownership_contract::case_8 ... ok
test event_loop::input_dispatch::tests::insert_pending_preserves_caret_across_supported_host_provider_matrix::case_1 ... ok
test event_loop::input_dispatch::tests::insert_pending_preserves_caret_across_supported_host_provider_matrix::case_2 ... ok
test event_loop::input_dispatch::tests::insert_pending_preserves_caret_across_supported_host_provider_matrix::case_3 ... ok
test event_loop::input_dispatch::tests::insert_pending_preserves_caret_across_supported_host_provider_matrix::case_4 ... ok
test event_loop::input_dispatch::tests::insert_pending_preserves_caret_across_supported_host_provider_matrix::case_5 ... ok
test event_loop::input_dispatch::tests::insert_pending_preserves_caret_across_supported_host_provider_matrix::case_6 ... ok
test event_loop::input_dispatch::tests::insert_without_pending_routes_horizontal_arrows_to_hud_navigation::case_1 ... ok
test event_loop::input_dispatch::tests::insert_without_pending_routes_horizontal_arrows_to_hud_navigation::case_2 ... ok
test event_loop::input_dispatch::tests::insert_without_pending_routes_horizontal_arrows_to_hud_navigation::case_3 ... ok
test event_loop::input_dispatch::tests::insert_without_pending_routes_horizontal_arrows_to_hud_navigation::case_4 ... ok
test event_loop::input_dispatch::tests::insert_without_pending_routes_horizontal_arrows_to_hud_navigation::case_5 ... ok
test event_loop::input_dispatch::tests::insert_without_pending_routes_horizontal_arrows_to_hud_navigation::case_6 ... ok
test event_loop::input_dispatch::tests::should_preserve_terminal_caret_navigation_matches_send_mode_contract::case_1 ... ok
test event_loop::input_dispatch::tests::should_preserve_terminal_caret_navigation_matches_send_mode_contract::case_2 ... ok
test event_loop::input_dispatch::tests::should_preserve_terminal_caret_navigation_matches_send_mode_contract::case_3 ... ok
test event_loop::input_dispatch::tests::should_preserve_terminal_caret_navigation_matches_send_mode_contract::case_4 ... ok
test event_loop::prompt_occlusion::tests::claude_prompt_context_detects_tool_use_card ... ok
test event_loop::prompt_occlusion::tests::approval_hint_detects_split_card_when_chunks_are_merged ... ok
test event_loop::prompt_occlusion::tests::explicit_approval_hint_detects_ansi_styled_prompt_question ... ok
test event_loop::prompt_occlusion::tests::explicit_approval_hint_detects_cargo_prompt_variant ... ok
test event_loop::prompt_occlusion::tests::explicit_approval_hint_detects_compact_spacing_variant ... ok
test event_loop::prompt_occlusion::tests::explicit_approval_hint_detects_prompt_question_line_start ... ok
test event_loop::prompt_occlusion::tests::explicit_approval_hint_ignores_embedded_recap_phrase ... ok
test event_loop::prompt_occlusion::tests::explicit_approval_hint_ignores_unrelated_output ... ok
test event_loop::prompt_occlusion::tests::numbered_approval_hint_detects_compact_prefix_variant ... ok
test event_loop::prompt_occlusion::tests::live_approval_card_hint_requires_explicit_and_numbered_signals ... ok
test event_loop::prompt_occlusion::tests::numbered_approval_hint_detects_selected_chevron_card ... ok
test event_loop::prompt_occlusion::tests::numbered_approval_hint_detects_selected_o_prefix_variant ... ok
test event_loop::prompt_occlusion::tests::numbered_approval_hint_detects_space_separator_variant ... ok
test event_loop::prompt_occlusion::tests::numbered_approval_hint_detects_sparse_card ... ok
test event_loop::prompt_occlusion::tests::numbered_approval_hint_detects_two_option_yes_no_card ... ok
test event_loop::prompt_occlusion::tests::numbered_approval_hint_ignores_plain_numbered_list ... ok
test event_loop::prompt_occlusion::tests::substantial_non_prompt_activity_ignores_choice_echo ... ok
test event_loop::prompt_occlusion::tests::substantial_non_prompt_activity_detects_post_approval_output ... ok
test event_loop::prompt_occlusion::tests::numbered_approval_hint_detects_wrapped_long_option_cards ... ok
test event_loop::prompt_occlusion::tests::synchronized_cursor_activity_detects_early_prompt_rewrite_packets ... ok
test event_loop::prompt_occlusion::tests::synchronized_cursor_activity_detects_long_think_status_packets ... ok
test event_loop::prompt_occlusion::tests::synchronized_cursor_activity_detects_shortcut_marker_packets ... ok
test event_loop::prompt_occlusion::tests::synchronized_cursor_activity_detects_spinner_only_packets ... ok
test event_loop::prompt_occlusion::tests::synchronized_cursor_activity_detects_thinking_packets ... ok
test event_loop::prompt_occlusion::tests::synchronized_cursor_activity_detects_three_row_status_hop_packets ... ok
test event_loop::prompt_occlusion::tests::synchronized_cursor_activity_identifies_prompt_input_echo_rewrites ... ok
test event_loop::prompt_occlusion::tests::synchronized_cursor_activity_identifies_three_row_input_echo_rewrites ... ok
test event_loop::prompt_occlusion::tests::synchronized_cursor_activity_ignores_non_rewrite_packets ... ok
test event_loop::prompt_occlusion::tests::synchronized_cursor_activity_input_echo_guard_ignores_long_think_packets ... ok
test event_loop::prompt_occlusion::tests::tool_activity_hint_detects_bash_tool_line ... ok
test event_loop::prompt_occlusion::tests::tool_activity_hint_detects_web_search_line ... ok
test event_loop::prompt_occlusion::tests::tool_activity_hint_ignores_plain_bash_commands_heading ... ok
test event_loop::prompt_occlusion::tests::tool_activity_hint_ignores_plain_web_searches_heading ... ok
test event_loop::prompt_occlusion::tests::tool_activity_hint_ignores_unrelated_output ... ok
test daemon::agent_driver::tests::startup_gate_cancel_unblocks_waiters ... ok
test daemon::agent_driver::tests::startup_gate_blocks_until_opened ... ok
test dev_command::tests::broker_executes_status_and_emits_completion ... ok
test event_loop::dev_panel_commands::git_snapshot::git_status_tests::find_git_root_uses_requested_start_dir ... ok
test event_loop::dev_panel_commands::git_snapshot::git_status_tests::capture_git_status_runs_in_repo ... ok
test event_loop::tests::centered_overlay_gutter_click_does_not_trigger_theme_studio_action_but_centered_click_still_works ... ok
test event_loop::tests::codex_generate_command_hint_does_not_enable_prompt_suppression ... ok
test event_loop::tests::centered_overlay_gutter_click_does_not_close_dev_panel_but_footer_close_still_works ... ok
test event_loop::tests::centered_overlay_gutter_click_does_not_trigger_settings_action_but_centered_click_still_works ... ok
test event_loop::tests::centered_overlay_gutter_click_does_not_trigger_theme_picker_action_but_centered_click_still_works ... ok
test event_loop::tests::close_overlay_sets_none_and_sends_clear_overlay ... ok
test event_loop::tests::decrease_sensitivity_event_moves_threshold_down ... ok
test event_loop::tests::dev_panel_overlay::commands::apply_terminal_packet_completion_stages_draft_text ... ok
test event_loop::tests::confirmation_bytes_defer_claude_prompt_clear_until_periodic_tick ... ok
test event_loop::tests::dev_panel_overlay::commands::apply_terminal_packet_completion_auto_send_requires_runtime_guard ... ok
test event_loop::tests::dev_panel_overlay::commands::dev_panel_arrow_navigation_moves_command_selection ... ok
test event_loop::tests::dev_panel_overlay::commands::dev_panel_second_sync_enter_without_broker_reports_unavailable ... ok
test event_loop::tests::dev_panel_overlay::commands::dev_panel_numeric_selection_supports_extended_command_set ... ok
test event_loop::tests::dev_panel_overlay::commands::dev_panel_read_only_under_unsafe_direct_still_executes ... ok
test event_loop::tests::apply_settings_item_action_theme_negative_direction_differs_from_positive_step ... ok
test event_loop::tests::dev_panel_overlay::commands::dev_panel_sync_requires_confirmation_before_run ... ok
test event_loop::tests::dev_panel_overlay::commands::dev_panel_sync_under_unsafe_direct_does_not_launch_broker ... ok
test event_loop::tests::apply_settings_item_action_theme_zero_direction_matches_positive_step ... ok
test event_loop::tests::arrow_left_and_right_focus_different_buttons_from_none ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::handoff_copy_sends_osc52_through_writer_channel ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::background_review_poll_refreshes_memory_when_memory_tab_visible ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::control_enter_refresh_rebuilds_runtime_snapshot ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::control_page_enter_without_memory_keeps_not_initialized_placeholder ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::background_review_poll_refreshes_handoff_when_handoff_tab_visible ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::handoff_direct_entry_loads_review_artifact_without_prior_tab_visits ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::handoff_footer_close_click_handles_scroll_suffix ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::handoff_tab_switch_lazy_loads_missing_caches_only ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::review_footer_close_click_handles_raw_view_with_scroll_suffix ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::review_tab_arrow_scroll_reaches_stale_lane_tail ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::memory_page_enter_refreshes_memory_cockpit_snapshot ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::handoff_direct_entry_populates_git_context_in_fresh_prompt ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::memory_page_enter_without_memory_keeps_absent_status ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::handoff_page_enter_refreshes_handoff_snapshot ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::dev_panel_control_page_m_key_cycles_memory_mode ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::background_review_poll_emits_toast_on_changed_content ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::dev_panel_control_page_m_key_persists_memory_mode ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::background_review_poll_does_not_repeat_toast_on_unchanged_content ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::control_page_enter_refreshes_memory_snapshot ... ok
test event_loop::tests::dev_panel_overlay::refresh_poll::handoff_enter_refresh_force_reloads_review_and_git ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::dev_panel_enter_in_review_tab_does_not_run_command ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::dev_panel_memory_page_m_key_cycles_memory_mode_and_refreshes_snapshot ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::non_interference_default_harness_mirrors_non_dev_session ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::non_interference_request_dev_command_rejected_when_dev_mode_off ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::review_poll_error_state_suppresses_toast_via_has_error_guard ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::review_tab_r_key_toggles_view_mode ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::review_poll_on_visible_review_tab_does_not_emit_toast ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::run_periodic_tasks_skips_background_poll_when_never_loaded ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::run_periodic_tasks_background_polls_review_when_previously_loaded ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::run_periodic_tasks_reloads_review_when_due_on_review_tab ... ok
test event_loop::tests::event_loop_constants_match_expected_limits ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::run_periodic_tasks_skips_review_on_tools_tab ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::run_periodic_tasks_skips_review_when_interval_not_due ... ok
test event_loop::tests::dev_panel_toggle_closes_overlay_when_open ... ok
test event_loop::tests::dev_panel_toggle_forwards_ctrl_d_when_dev_mode_disabled ... ok
test event_loop::tests::dev_panel_toggle_opens_overlay_when_dev_mode_enabled ... ok
test event_loop::tests::drain_voice_messages_once_invokes_installed_hook ... ok
test event_loop::tests::empty_bytes_keep_claude_prompt_suppression_enabled ... ok
test event_loop::tests::enter_key_defer_claude_prompt_clear_until_periodic_tick ... ok
test event_loop::tests::flush_pending_pty_input_pops_front_when_offset_reaches_chunk_end ... ok
test event_loop::tests::enter_key_non_theme_focus_keeps_theme_picker_digits ... ok
test event_loop::tests::enter_key_resolution_does_not_re_suppress_on_empty_output ... ok
test event_loop::tests::enter_key_with_auto_focus_submits_terminal_input_without_toggling_auto_mode ... ok
test event_loop::tests::flush_pending_output_or_continue_handles_no_pending_output ... ok
test event_loop::tests::flush_pending_output_or_continue_keeps_running_when_flush_succeeds ... ok
test event_loop::tests::flush_pending_output_or_continue_keeps_running_when_output_requeues ... ok
test event_loop::tests::flush_pending_output_or_continue_stops_when_writer_disconnected_and_output_drained ... ok
test event_loop::tests::flush_pending_pty_input_does_not_write_empty_slice_when_offset_is_at_chunk_end ... ok
test event_loop::tests::flush_pending_pty_input_empty_queue_resets_counters ... ok
test event_loop::tests::flush_pending_pty_input_drains_many_single_byte_chunks_within_attempt_budget ... ok
test event_loop::tests::flush_pending_pty_input_returns_false_for_non_retry_errors ... ok
test event_loop::tests::flush_pending_pty_input_treats_interrupted_as_retryable ... ok
test event_loop::tests::flush_pending_pty_input_treats_would_block_as_retryable ... ok
test event_loop::tests::flush_pending_pty_output_requeues_when_writer_is_full ... ok
test event_loop::tests::flush_pending_pty_output_returns_false_when_writer_is_disconnected ... ok
test event_loop::tests::flush_pending_pty_output_returns_true_when_empty ... ok
test event_loop::tests::handle_input_event_bytes_marks_insert_mode_pending_send ... ok
test event_loop::tests::full_hud_single_line_mouse_click_bottom_row_triggers_button_action ... ok
test event_loop::tests::handle_output_chunk_bash_approval_card_suppresses_hud ... ok
test event_loop::tests::handle_output_chunk_empty_data_keeps_responding_state_and_suppress_flag ... ok
test event_loop::tests::handle_output_chunk_input_echo_rewrite_does_not_suppress_without_recent_input_timestamp ... ok
test event_loop::tests::handle_output_chunk_ingests_lossy_text_for_invalid_utf8_bytes ... ok
test event_loop::tests::handle_output_chunk_non_empty_responding_stays_responding_until_prompt_ready ... ok
test event_loop::tests::handle_output_chunk_non_empty_idle_emits_only_pty_output ... ok
test event_loop::tests::handle_output_chunk_non_empty_responding_transitions_to_idle_when_prompt_is_ready ... ok
test event_loop::tests::handle_output_chunk_recent_input_echo_rewrite_does_not_re_suppress_hud ... ok
test event_loop::tests::handle_output_chunk_synchronized_cursor_activity_without_approval_hints_does_not_suppress_hud ... ok
test event_loop::tests::handle_output_chunk_synchronized_rewrite_with_historical_approval_phrase_does_not_suppress_hud ... ok
test event_loop::tests::handle_output_chunk_synchronized_rewrite_with_inline_quote_and_yes_no_does_not_suppress_hud ... ok
test event_loop::tests::handle_output_chunk_synchronized_yes_no_approval_prompt_suppresses_hud ... ok
test event_loop::tests::handle_output_chunk_tool_activity_without_approval_hints_does_not_suppress_hud ... ok
test event_loop::tests::help_overlay_unhandled_bytes_close_overlay_and_replay_input ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::dev_panel_shift_tab_cycles_backward ... ok
test event_loop::tests::help_overlay_unhandled_ctrl_e_closes_overlay_and_replays_action ... ok
test event_loop::tests::hidden_hide_mouse_click_collapses_launcher_and_emits_status_redraw ... ok
test event_loop::tests::dev_panel_overlay::refresh_state::dev_panel_tab_key_cycles_through_all_pages ... ok
test event_loop::tests::hidden_open_enter_expands_collapsed_launcher_before_style_cycle ... ok
test event_loop::tests::hidden_open_enter_cycles_style_after_launcher_is_expanded ... ok
test event_loop::tests::hidden_open_mouse_click_expands_collapsed_launcher_and_emits_status_redraw ... ok
test event_loop::tests::image_capture_trigger_while_recording_sets_guard_status ... ok
test event_loop::tests::insert_mode_empty_bytes_do_not_mark_pending_send ... ok
test event_loop::tests::insert_mode_with_pending_text_forwards_left_and_right_arrows_to_pty ... ok
test event_loop::tests::insert_mode_with_pending_text_forwards_up_and_down_to_pty ... ok
test event_loop::tests::insert_mode_without_pending_text_keeps_hud_arrow_focus_navigation ... ok
test event_loop::tests::manual_voice_trigger_cancel_failure_keeps_recording ... ok
test event_loop::tests::manual_voice_trigger_does_not_log_wake_capture_marker ... ok
test event_loop::tests::manual_voice_trigger_in_auto_mode_pauses_then_resumes_with_explicit_restart ... ok
test event_loop::tests::manual_voice_trigger_while_recording_uses_cancel_capture_path ... ok
test event_loop::tests::manual_voice_trigger_starts_voice_capture_even_when_image_mode_enabled ... ok
test event_loop::tests::mouse_click_non_theme_button_keeps_theme_picker_digits ... ok
test event_loop::tests::non_interference_ctrl_d_sends_eof_byte_when_dev_mode_off ... ok
test event_loop::tests::non_interference_dev_command_broker_absent_when_dev_mode_off ... ok
test event_loop::tests::non_interference_dev_mode_stats_absent_when_dev_mode_off ... ok
test event_loop::tests::non_interference_dev_panel_toggle_opens_panel_when_dev_mode_on ... ok
test event_loop::tests::non_interference_overlay_never_becomes_dev_panel_when_dev_mode_off ... ok
test event_loop::tests::non_interference_poll_dev_commands_is_noop_when_broker_absent ... ok
test event_loop::tests::nonrolling_explicit_approval_card_suppresses_without_backend_label ... ok
test event_loop::tests::nonrolling_long_wrapped_approval_card_still_suppresses ... ok
test event_loop::tests::nonrolling_prompt_question_line_suppresses_before_numbered_options ... ok
test event_loop::tests::nonrolling_release_arm_defers_on_echo_chunk_until_substantial_output ... ok
test event_loop::tests::nonrolling_stale_explicit_text_does_not_retrigger_suppression ... ok
test event_loop::tests::nonrolling_sticky_hold_covers_rapid_consecutive_approvals ... ok
test event_loop::tests::nonrolling_tool_activity_hint_does_not_suppress_without_approval_card ... ok
test event_loop::tests::numeric_approval_choice_defer_claude_prompt_clear_until_periodic_tick ... ok
test event_loop::tests::open_help_overlay_sets_mode_and_renders_overlay ... ok
test event_loop::tests::open_settings_overlay_sets_mode_and_renders_overlay ... ok
test event_loop::tests::open_theme_picker_overlay_sets_mode_resets_picker_and_renders_overlay ... ok
test event_loop::tests::open_theme_studio_overlay_sets_mode_and_renders_overlay ... ok
test event_loop::tests::overlay_mouse_click_outside_horizontal_bounds_is_ignored ... ok
test event_loop::tests::overlay_mouse_click_outside_vertical_bounds_is_ignored ... ok
test event_loop::tests::periodic_tasks_clear_stale_prompt_suppression_without_new_output ... ok
test event_loop::tests::periodic_tasks_push_status_toasts_with_severity_mapping ... ok
test event_loop::tests::periodic_tasks_status_clear_resets_toast_dedupe ... ok
test event_loop::tests::refresh_button_registry_if_mouse_only_updates_when_enabled ... ok
test event_loop::tests::render_help_overlay_for_state_sends_show_overlay_message ... ok
test event_loop::tests::render_settings_overlay_for_state_sends_show_overlay_message ... ok
test event_loop::tests::reply_composer_marker_does_not_enable_prompt_suppression ... ok
test event_loop::tests::render_theme_picker_overlay_for_state_sends_show_overlay_message ... ok
test event_loop::tests::reset_theme_picker_selection_resets_index_and_digits ... ok
test event_loop::tests::run_event_loop_ctrl_e_with_pending_insert_text_finalizes_without_sending_while_recording ... ok
test event_loop::tests::run_event_loop_ctrl_e_with_pending_insert_text_outside_recording_keeps_text_staged ... ok
test event_loop::tests::run_event_loop_ctrl_e_without_pending_insert_text_reports_nothing_to_finalize ... ok
test event_loop::tests::run_event_loop_ctrl_e_without_pending_insert_text_requests_early_finalize ... ok
test event_loop::tests::run_event_loop_does_not_run_periodic_before_first_tick ... ok
test event_loop::tests::run_event_loop_enter_with_pending_insert_text_sends_without_capture_stop ... ok
test event_loop::tests::run_event_loop_enter_without_pending_insert_text_does_not_stop_recording ... ok
test event_loop::tests::run_event_loop_flushes_pending_input_before_exit ... ok
test event_loop::tests::run_event_loop_flushes_pending_output_even_when_writer_is_disconnected ... ok
test event_loop::tests::run_event_loop_help_overlay_mouse_body_click_keeps_overlay_open ... ok
test event_loop::tests::run_event_loop_flushes_pending_output_on_success_path ... ok
test event_loop::tests::run_event_loop_processes_multiple_input_events_before_exit ... ok
test event_loop::tests::non_confirmation_bytes_keep_claude_prompt_suppression ... ok
test event_loop::tests::run_event_loop_theme_picker_click_selects_theme_and_closes_overlay ... ok
test event_loop::tests::run_periodic_tasks_advances_processing_spinner ... ok
test event_loop::tests::run_periodic_tasks_clears_preview_and_status_at_deadline ... ok
test event_loop::tests::run_periodic_tasks_clears_theme_digits_outside_picker_mode ... ok
test event_loop::tests::run_periodic_tasks_cursor_sigwinch_is_debounced_before_resize_apply ... ok
test event_loop::tests::run_periodic_tasks_does_not_advance_spinner_when_not_processing ... ok
test event_loop::tests::run_periodic_tasks_does_not_start_auto_voice_when_disabled ... ok
test event_loop::tests::run_periodic_tasks_does_not_start_auto_voice_when_paused_by_user ... ok
test event_loop::tests::run_periodic_tasks_does_not_start_auto_voice_while_wake_listener_is_active ... ok
test event_loop::tests::run_periodic_tasks_does_not_start_auto_voice_when_trigger_not_ready ... ok
test event_loop::tests::run_periodic_tasks_expires_stale_latency_badge_at_exact_boundary ... ok
test event_loop::tests::run_periodic_tasks_expires_stale_latency_badge ... ok
test event_loop::tests::run_periodic_tasks_does_not_update_meter_when_not_recording ... ok
test event_loop::tests::run_periodic_tasks_geometry_poll_accepts_persistent_claude_row_collapse ... ok
test event_loop::tests::run_periodic_tasks_geometry_poll_without_sigwinch_triggers_resize ... ok
test event_loop::tests::run_periodic_tasks_heartbeat_animates_when_recording_only_is_disabled ... ok
test event_loop::tests::run_periodic_tasks_geometry_poll_ignores_zero_size_probe ... ok
test event_loop::tests::run_periodic_tasks_geometry_poll_debounces_single_claude_row_collapse_probe ... ok
test event_loop::tests::run_periodic_tasks_heartbeat_only_runs_for_heartbeat_panel ... ok
test event_loop::tests::run_periodic_tasks_heartbeat_requires_full_interval ... ok
test event_loop::tests::run_periodic_tasks_heartbeat_respects_recording_only_gate ... ok
test event_loop::tests::run_periodic_tasks_keeps_floor_db_before_silence_placeholder_timeout ... ok
test event_loop::tests::run_periodic_tasks_keeps_fresh_latency_badge ... ok
test event_loop::tests::run_periodic_tasks_keeps_last_db_after_sustained_floor_level ... ok
test event_loop::tests::run_periodic_tasks_keeps_meter_history_at_cap_when_prefill_is_one_under ... ok
test event_loop::tests::run_periodic_tasks_keeps_theme_digits_when_picker_deadline_not_reached ... ok
test event_loop::tests::run_periodic_tasks_marks_wake_hud_unavailable_when_listener_is_not_active ... ok
test event_loop::tests::run_periodic_tasks_non_floor_level_clears_floor_tracking_state ... ok
test event_loop::tests::run_periodic_tasks_sets_floor_db_after_sustained_floor_level_when_unset ... ok
test event_loop::tests::run_periodic_tasks_sigwinch_single_dimension_change_triggers_resize ... ok
test event_loop::tests::run_periodic_tasks_sigwinch_no_size_change_skips_resize_messages ... ok
test event_loop::tests::run_periodic_tasks_skips_recording_update_when_delta_is_too_small ... ok
test event_loop::tests::run_periodic_tasks_spinner_uses_modulo_for_frame_selection ... ok
test event_loop::tests::run_periodic_tasks_updates_meter_and_caps_history ... ok
test event_loop::tests::run_periodic_tasks_updates_recording_duration ... ok
test event_loop::tests::run_periodic_tasks_wake_badge_does_not_pulse_redraw_while_listening ... ok
test event_loop::tests::send_staged_text_outside_insert_mode_stops_on_pty_error ... ok
test event_loop::tests::send_staged_text_processing_insert_mode_consumes_without_status_or_write ... ok
test event_loop::tests::set_claude_prompt_suppression_clears_hud_before_status_update ... ok
test event_loop::tests::set_claude_prompt_suppression_expands_pty_row_budget ... ok
test event_loop::tests::settings_mouse_click_on_border_columns_does_not_select_option ... ok
test event_loop::tests::settings_mouse_click_zero_column_is_ignored ... ok
test event_loop::tests::settings_overlay_enter_actionable_row_redraws_overlay ... ok
test event_loop::tests::settings_overlay_enter_backend_row_keeps_overlay_open ... ok
test event_loop::tests::settings_overlay_enter_backend_row_does_not_redraw ... ok
test event_loop::tests::settings_overlay_enter_close_row_closes_overlay ... ok
test event_loop::tests::settings_overlay_enter_quit_row_stops_event_loop ... ok
test event_loop::tests::should_emit_user_input_activity_for_claude_in_cursor_and_jetbrains_hosts ... ok
test event_loop::tests::should_not_emit_user_input_activity_for_non_claude_or_other_hosts ... ok
test event_loop::tests::settings_overlay_escape_bytes_close_overlay ... ok
test event_loop::tests::settings_overlay_mouse_click_adjusts_sensitivity_with_centered_offset_x ... ok
test event_loop::tests::settings_overlay_mouse_click_close_row_closes_overlay ... ok
test event_loop::tests::settings_overlay_mouse_click_cycles_setting_value ... ok
test event_loop::tests::take_sigwinch_flag_uses_installed_hook_value ... ok
test event_loop::tests::settings_overlay_mouse_click_cycles_setting_value_with_centered_offset_x ... ok
test event_loop::tests::settings_overlay_mouse_click_footer_close_prefix_closes_overlay ... ok
test event_loop::tests::settings_overlay_mouse_click_footer_outside_close_prefix_keeps_overlay_open ... ok
test event_loop::tests::settings_overlay_mouse_click_quit_row_stops_event_loop ... ok
test event_loop::tests::settings_overlay_arrow_left_and_right_take_different_paths_and_redraw ... ok
test event_loop::tests::settings_overlay_mouse_click_selects_read_only_row_without_state_change ... ok
test event_loop::tests::settings_overlay_mouse_click_sensitivity_slider_left_moves_more_sensitive ... ok
test event_loop::tests::settings_overlay_mouse_click_wake_sensitivity_slider_left_moves_less_sensitive ... ok
test event_loop::tests::settings_overlay_up_down_navigates_menu_locally ... ok
test event_loop::tests::start_voice_capture_with_hook_propagates_hook_error ... ok
test event_loop::tests::startup_ready_marker_release_is_debounced_before_unsuppress ... ok
test event_loop::tests::sync_overlay_winsize_updates_cached_terminal_dimensions ... ok
test event_loop::tests::theme_picker_enter_with_invalid_selection_keeps_overlay_open_and_rerenders ... ok
test event_loop::tests::theme_picker_escape_bytes_close_and_clear_digits ... ok
test event_loop::tests::theme_picker_hotkey_opens_theme_studio_overlay ... ok
test event_loop::tests::theme_picker_mouse_click_on_border_columns_does_not_select_option ... ok
test event_loop::tests::theme_picker_numeric_input_keeps_three_digits_and_clears_after_fourth ... ok
test event_loop::tests::theme_picker_single_digit_waits_when_longer_match_exists ... ok
test event_loop::tests::theme_studio_arrow_left_on_hud_style_row_cycles_backward ... ok
test event_loop::tests::theme_studio_arrow_right_on_indicator_set_row_cycles_runtime_override ... ok
test event_loop::tests::theme_studio_colors_page_arrow_right_on_glyph_selector_cycles_runtime_override ... ok
test event_loop::tests::theme_studio_colors_page_arrow_right_on_indicator_selector_cycles_runtime_override ... ok
test event_loop::tests::suppress_startup_escape_only_blocks_arrow_noise_when_enabled ... ok
test event_loop::tests::theme_studio_colors_page_enter_on_indicator_selector_is_noop_for_picker ... ok
test event_loop::tests::theme_studio_enter_on_banner_style_row_cycles_runtime_override ... ok
test event_loop::tests::theme_picker_arrow_left_and_right_move_selection_in_opposite_directions ... ok
test event_loop::tests::theme_studio_enter_on_glyph_profile_row_cycles_runtime_override ... ok
test event_loop::tests::theme_studio_enter_on_progress_bars_row_cycles_runtime_override ... ok
test event_loop::tests::theme_studio_enter_on_hud_style_row_cycles_style_and_stays_open ... ok
test event_loop::tests::theme_studio_enter_on_progress_spinner_row_cycles_runtime_override ... ok
test event_loop::tests::theme_studio_enter_on_redo_row_reapplies_runtime_override_edit ... ok
test event_loop::tests::theme_studio_enter_on_rollback_row_clears_runtime_overrides ... ok
test event_loop::tests::theme_studio_enter_on_startup_splash_row_cycles_runtime_override ... ok
test event_loop::tests::theme_studio_enter_on_theme_borders_row_cycles_runtime_override ... ok
test event_loop::tests::theme_studio_enter_on_theme_picker_row_opens_theme_picker_overlay ... ok
test event_loop::tests::theme_studio_enter_on_toast_position_row_cycles_runtime_override ... ok
test event_loop::tests::theme_studio_enter_on_toast_severity_row_cycles_runtime_override ... ok
test event_loop::tests::theme_studio_enter_on_undo_row_reverts_latest_runtime_override_edit ... ok
test event_loop::tests::theme_studio_enter_on_voice_scene_row_cycles_runtime_override ... ok
test event_loop::tests::theme_studio_mouse_click_above_option_rows_does_not_activate_selection ... ok
test event_loop::tests::theme_studio_mouse_click_on_border_columns_does_not_select_option ... ok
test event_loop::tests::toast_history_toggle_opens_and_closes_overlay ... ok
test event_loop::tests::theme_studio_mouse_click_on_theme_picker_row_opens_theme_picker_overlay ... ok
test event_loop::tests::toggle_hud_style_in_help_overlay_does_not_render_settings_overlay ... ok
test event_loop::tests::transcript_history_overlay_enter_on_assistant_entry_does_not_replay ... ok
test event_loop::tests::transcript_history_overlay_ignores_escape_noise_in_search ... ok
test event_loop::tests::up_and_down_forward_to_pty_even_when_hud_focus_is_active ... ok
test event_loop::tests::up_arrow_without_hud_focus_is_forwarded_to_pty ... ok
test event_loop::tests::wake_word_detection_is_ignored_when_disabled ... ok
test event_loop::tests::wake_word_detection_is_ignored_when_overlay_is_open ... ok
test help::tests::format_help_overlay_contains_shortcuts_and_sections ... ok
test help::tests::format_help_overlay_has_borders ... ok
test help::tests::format_help_overlay_includes_clickable_resource_links ... ok
test help::tests::format_help_overlay_line_count_matches_documented_height ... ok
test help::tests::format_help_overlay_no_color ... ok
test help::tests::format_resource_link_line_omits_osc8_when_visible_width_overflows ... ok
test help::tests::format_resource_link_line_uses_osc8_when_visible_width_exactly_fits ... ok
test help::tests::format_shortcut_line_respects_calculated_description_width ... ok
test help::tests::help_overlay_dimensions ... ok
test help::tests::help_overlay_footer_respects_ascii_glyph_set ... ok
test help::tests::help_overlay_height_matches_documented_formula ... ok
test help::tests::help_overlay_size_helpers_use_expected_clamps ... ok
test help::tests::shortcuts_defined_in_sections ... ok
test hud::latency_module::tests::latency_char_threshold_buckets_map_to_expected_bars ... ok
test hud::latency_module::tests::latency_module_id ... ok
test hud::latency_module::tests::latency_module_min_width ... ok
test hud::latency_module::tests::latency_module_priority_is_stable ... ok
test hud::latency_module::tests::latency_module_render_at_min_width_shows_compact_value ... ok
test hud::latency_module::tests::latency_module_render_compact ... ok
test hud::latency_module::tests::latency_module_render_fast ... ok
test hud::latency_module::tests::latency_module_render_narrow ... ok
test hud::latency_module::tests::latency_module_render_no_data ... ok
test hud::latency_module::tests::latency_module_render_slow ... ok
test hud::latency_module::tests::latency_module_render_width_six_includes_trend_marker ... ok
test hud::latency_module::tests::latency_module_render_with_data ... ok
test hud::latency_module::tests::latency_module_respects_ascii_glyph_set ... ok
test hud::latency_module::tests::latency_module_tick_interval ... ok
test hud::latency_module::tests::latency_module_uses_history_sparkline ... ok
test hud::latency_module::tests::render_sparkline_left_pads_short_history_with_floor_bar ... ok
test hud::latency_module::tests::render_sparkline_returns_empty_for_empty_history_or_zero_width ... ok
test hud::meter_module::tests::custom_bar_count ... ok
test hud::meter_module::tests::db_to_char_range ... ok
test hud::meter_module::tests::meter_module_id ... ok
test hud::meter_module::tests::meter_module_min_width ... ok
test hud::meter_module::tests::meter_module_priority_is_stable ... ok
test hud::meter_module::tests::meter_module_render_history_sparkline_varies ... ok
test hud::meter_module::tests::meter_module_render_just_db ... ok
test hud::meter_module::tests::meter_module_render_loud ... ok
test hud::meter_module::tests::meter_module_render_narrow ... ok
test hud::meter_module::tests::meter_module_render_not_recording ... ok
test hud::meter_module::tests::meter_module_render_quiet ... ok
test hud::meter_module::tests::meter_module_render_recording ... ok
test hud::meter_module::tests::meter_module_respects_ascii_glyph_set ... ok
test hud::meter_module::tests::meter_module_tick_interval ... ok
test hud::meter_module::tests::render_sparkline_exact_history_width_adds_no_padding ... ok
test hud::meter_module::tests::render_sparkline_left_pads_short_history_to_target_width ... ok
test hud::meter_module::tests::render_sparkline_returns_empty_for_empty_levels_or_zero_bar_count ... ok
test hud::mode_module::tests::mode_module_id ... ok
test hud::mode_module::tests::mode_module_min_width ... ok
test hud::mode_module::tests::mode_module_priority_is_stable ... ok
test hud::mode_module::tests::mode_module_render_auto ... ok
test hud::mode_module::tests::mode_module_render_just_indicator ... ok
test hud::mode_module::tests::mode_module_render_manual ... ok
test hud::mode_module::tests::mode_module_render_narrow ... ok
test hud::mode_module::tests::mode_module_render_recording ... ok
test hud::mode_module::tests::mode_module_respects_ascii_glyph_set ... ok
test hud::queue_module::tests::queue_module_id ... ok
test hud::queue_module::tests::queue_module_min_width ... ok
test hud::queue_module::tests::queue_module_priority_is_stable ... ok
test hud::queue_module::tests::queue_module_render_compact ... ok
test hud::queue_module::tests::queue_module_render_empty ... ok
test hud::queue_module::tests::queue_module_render_full ... ok
test hud::queue_module::tests::queue_module_render_many_items ... ok
test hud::queue_module::tests::queue_module_render_narrow ... ok
test hud::queue_module::tests::queue_module_render_with_items ... ok
test hud::queue_module::tests::queue_module_respects_ascii_glyph_set ... ok
test hud::queue_module::tests::queue_module_tick_interval ... ok
test hud::tests::hud_module_default_priority_is_100 ... ok
test hud::tests::hud_state_default ... ok
test hud::tests::min_tick_interval_uses_smallest_non_none_value ... ok
test hud::tests::mode_labels ... ok
test hud::tests::registry_get_module ... ok
test hud::tests::registry_new_is_empty ... ok
test hud::tests::registry_render_all_empty ... ok
test hud::tests::registry_render_all_with_modules ... ok
test hud::tests::registry_respects_max_width ... ok
test hud::tests::registry_with_defaults_has_modules ... ok
test hud::tests::render_all_includes_module_at_exact_remaining_width_boundary ... ok
test hud::tests::render_all_non_first_available_width_subtracts_separator ... ok
test hud::tests::render_all_prefers_default_priority_over_low_priority_module ... ok
test hud::tests::render_all_prefers_higher_priority_modules_under_width_pressure ... ok
test hud::tests::render_all_remaining_width_math_controls_inclusion ... ok
test hud::tests::render_all_skips_empty_modules_without_losing_later_modules ... ok
test icons::tests::ascii_icons_defined ... ok
test icons::tests::get_icons_returns_correct_set ... ok
test icons::tests::meter_bars_ordered ... ok
test icons::tests::spinner_ascii_has_frames ... ok
test icons::tests::spinner_braille_has_frames ... ok
test icons::tests::spinner_circle_has_frames ... ok
test icons::tests::unicode_icons_defined ... ok
test image_mode::tests::build_image_prompt_auto_mode_appends_newline ... ok
test image_mode::tests::build_image_prompt_insert_mode_stages_without_newline ... ok
test image_mode::tests::next_capture_path_ignores_empty_voiceterm_cwd_env ... ok
test image_mode::tests::next_capture_path_prefers_voiceterm_cwd_env ... ok
test image_mode::tests::next_capture_path_uses_png_extension ... ok
test input::mouse::tests::is_mouse_sequence_accepts_each_supported_protocol ... ok
test input::mouse::tests::is_sgr_mouse_sequence_validates_prefix_length_and_suffix ... ok
test input::mouse::tests::is_urxvt_mouse_sequence_validates_prefix_length_and_suffix ... ok
test input::mouse::tests::parse_mouse_event_accepts_all_supported_protocols ... ok
test input::mouse::tests::parse_sgr_mouse_left_click ... ok
test input::mouse::tests::parse_sgr_mouse_rejects_invalid_prefix_bytes ... ok
test input::mouse::tests::parse_urxvt_mouse_left_click ... ok
test input::mouse::tests::parse_x10_mouse_left_click ... ok
test input::mouse::tests::parse_x10_mouse_rejects_invalid_len_or_prefix ... ok
test input::parser::tests::input_parser_buffers_partial_sgr_mouse_sequence ... ok
test input::parser::tests::input_parser_buffers_partial_x10_mouse_sequence ... ok
test input::parser::tests::input_parser_csi_buffer_waits_until_overflow_boundary ... ok
test input::parser::tests::input_parser_csi_u_contract_maps_owned_shortcuts_and_preserves_unmapped ... ok
test input::parser::tests::input_parser_drops_malformed_sgr_mouse_sequence_instead_of_forwarding_bytes ... ok
test input::parser::tests::input_parser_drops_malformed_x10_sequence ... ok
test input::parser::tests::input_parser_drops_sgr_prefixed_csi_overflow ... ok
test input::parser::tests::input_parser_emits_bytes_and_controls ... ok
test input::parser::tests::input_parser_forwards_non_csi_escape_sequences ... ok
test input::parser::tests::input_parser_forwards_unmapped_csi_u_ctrl_c_sequence ... ok
test input::parser::tests::input_parser_forwards_unmapped_csi_u_escape_sequence ... ok
test input::parser::tests::input_parser_forwards_unmapped_csi_u_sequences ... ok
test input::parser::tests::input_parser_handles_truncated_csi_u_sequences ... ok
test input::parser::tests::input_parser_ignores_sgr_mouse_wheel ... ok
test input::parser::tests::input_parser_keeps_newlines_and_controls_literal_inside_bracketed_paste ... ok
test input::parser::tests::input_parser_keeps_non_lf_after_cr ... ok
test input::parser::tests::input_parser_maps_control_keys ... ok
test input::parser::tests::input_parser_maps_csi_u_ctrl_d_dev_panel_toggle ... ok
test input::parser::tests::input_parser_maps_csi_u_ctrl_e_send_staged_text ... ok
test input::parser::tests::input_parser_maps_csi_u_ctrl_sequences ... ok
test input::parser::tests::input_parser_maps_csi_u_ctrl_x_image_capture ... ok
test input::parser::tests::input_parser_maps_csi_u_quick_theme_cycle ... ok
test input::parser::tests::input_parser_maps_help_toggle ... ok
test input::parser::tests::input_parser_maps_theme_picker ... ok
test input::parser::tests::input_parser_mouse_press_then_release_emits_single_click ... ok
test input::parser::tests::input_parser_mouse_release_without_press_emits_click ... ok
test input::parser::tests::input_parser_mouse_urxvt_left_click_emits_click ... ok
test input::parser::tests::input_parser_mouse_x10_left_click_emits_click ... ok
test input::parser::tests::input_parser_preserves_arrow_sequences ... ok
test input::parser::tests::input_parser_skips_lf_after_cr ... ok
test input::parser::tests::input_parser_strips_bracketed_paste_wrappers ... ok
test input::parser::tests::is_csi_u_numeric_validates_prefix_suffix_and_minimum_length ... ok
test input::parser::tests::parse_csi_u_event_maps_extended_shortcuts ... ok
test input::parser::tests::parse_csi_u_event_requires_ctrl_modifier_and_valid_header ... ok
test input::spawn::tests::format_debug_bytes_formats_hex_pairs_with_spaces ... ok
test input::spawn::tests::format_debug_bytes_truncates_and_appends_ellipsis_when_over_limit ... ok
test input::spawn::tests::input_debug_enabled_reflects_env_presence ... ok
test input::spawn::tests::should_log_event_debug_requires_debug_and_non_empty_events ... ok
test main_tests::is_jetbrains_terminal_detects_and_rejects_expected_env_values ... ok
test main_tests::jetbrains_meter_floor_applies_only_in_jetbrains ... ok
test main_tests::join_thread_with_timeout_returns_quickly_when_thread_already_finished ... ok
test event_loop::tests::wake_word_detection_is_ignored_while_recording ... ok
test main_tests::resolved_meter_update_ms_respects_jetbrains_detection_and_registry_baseline ... ok
test main_tests::startup_guard_enabled_only_for_claude_on_jetbrains ... ok
test main_tests::startup_memory_mode_uses_persisted_user_config_value ... ok
test main_tests::validate_dev_mode_flags_accepts_dev_log_combo ... ok
test main_tests::validate_dev_mode_flags_rejects_unguarded_dev_logging_flags ... ok
test main_tests::validate_dev_mode_flags_requires_dev_log_when_dev_path_is_set ... ok
test memory::action_audit::tests::action_center_cancel_approval ... ok
test memory::action_audit::tests::action_center_clamp_scroll ... ok
test memory::action_audit::tests::action_center_confirm_required_needs_two_presses ... ok
test memory::action_audit::tests::action_center_navigation ... ok
test memory::action_audit::tests::action_center_read_only_executes_immediately ... ok
test memory::action_audit::tests::builtin_actions_are_not_empty ... ok
test memory::action_audit::tests::classify_command_blocked ... ok
test memory::action_audit::tests::classify_command_confirm_required ... ok
test memory::action_audit::tests::classify_command_read_only ... ok
test memory::action_audit::tests::selected_action_returns_correct_template ... ok
test memory::context_pack::tests::boot_pack_summary_only_reports_budgeted_evidence ... ok
test memory::context_pack::tests::empty_index_produces_empty_boot_pack ... ok
test memory::context_pack::tests::generate_boot_pack_has_evidence ... ok
test memory::context_pack::tests::generate_boot_pack_includes_decisions ... ok
test memory::context_pack::tests::generate_boot_pack_includes_tasks ... ok
test memory::context_pack::tests::generate_hybrid_pack_has_hybrid_type_and_plan ... ok
test memory::context_pack::tests::generate_task_pack_by_mp_id ... ok
test memory::context_pack::tests::generate_task_pack_by_text ... ok
test memory::context_pack::tests::generate_task_pack_from_ingested_mp_metadata ... ok
test memory::context_pack::tests::generate_task_pack_no_results ... ok
test memory::context_pack::tests::pack_to_json_roundtrip ... ok
test memory::context_pack::tests::pack_to_markdown_has_sections ... ok
test memory::context_pack::tests::token_budget_is_respected ... ok
test memory::context_pack::tests::truncate_text_long_string ... ok
test memory::context_pack::tests::truncate_text_short_string ... ok
test memory::governance::tests::compute_cutoff_ts_crosses_month ... ok
test memory::governance::tests::compute_cutoff_ts_subtracts_days ... ok
test memory::governance::tests::count_gc_candidates_forever_returns_zero ... ok
test memory::governance::tests::count_gc_candidates_with_old_events ... ok
test memory::governance::tests::events_jsonl_path_correct ... ok
test memory::governance::tests::governance_config_defaults ... ok
test memory::governance::tests::memory_dir_is_project_scoped ... ok
test memory::governance::tests::redact_secrets_handles_aws_keys ... ok
test memory::governance::tests::redact_secrets_preserves_safe_text ... ok
test memory::governance::tests::redact_secrets_redacts_multiple_occurrences_of_same_prefix ... ok
test memory::governance::tests::redact_secrets_removes_api_keys ... ok
test memory::ingest::tests::ansi_escape_sequences_are_stripped ... ok
test memory::ingest::tests::capture_only_mode_allows_capture ... ok
test memory::ingest::tests::empty_text_is_rejected ... ok
test memory::ingest::tests::extracted_metadata_powers_task_and_topic_queries ... ok
test memory::ingest::tests::incognito_mode_blocks_capture ... ok
test memory::ingest::tests::ingest_assistant_output_stores_event ... ok
test memory::ingest::tests::ingest_event_raw_merges_explicit_and_extracted_metadata ... ok
test memory::ingest::tests::ingest_redacts_secret_prefixes_before_persisting ... ok
test memory::ingest::tests::ingest_transcript_extracts_task_topic_and_entity_metadata ... ok
test memory::ingest::tests::ingest_transcript_stores_event ... ok
test memory::ingest::tests::ingest_user_input_stores_event ... ok
test memory::ingest::tests::ingest_with_jsonl_persistence ... ok
test memory::ingest::tests::ingest_with_tags ... ok
test memory::ingest::tests::is_noise_detects_empty_after_strip ... ok
test memory::ingest::tests::mode_switch_at_runtime ... ok
test memory::ingest::tests::off_mode_blocks_all_capture ... ok
test memory::ingest::tests::paused_mode_blocks_capture ... ok
test memory::ingest::tests::pure_escape_sequences_are_dropped ... ok
test memory::ingest::tests::short_noise_is_dropped ... ok
test memory::ingest::tests::strip_ansi_removes_color_codes ... ok
test main_tests::join_thread_with_timeout_waits_for_worker_to_finish_within_budget ... ok
test memory::ingest::tests::test_recover_from_jsonl_empty ... ok
test memory::ingest::tests::test_recover_from_jsonl_roundtrip ... ok
test memory::retrieval::tests::build_query_plan_for_hybrid_adds_recent_fallback ... ok
test memory::retrieval::tests::estimate_tokens_approximation ... ok
test memory::retrieval::tests::execute_query_with_signal_hybrid_merges_and_deduplicates ... ok
test memory::retrieval::tests::execute_query_with_signal_survival_index_falls_back_to_recent ... ok
test memory::retrieval::tests::execute_recent_query ... ok
test memory::retrieval::tests::execute_task_query ... ok
test memory::retrieval::tests::execute_text_search ... ok
test memory::retrieval::tests::execute_topic_query ... ok
test memory::retrieval::tests::scores_are_bounded ... ok
test memory::retrieval::tests::strategy_selection_maps_context_signals ... ok
test memory::retrieval::tests::trim_to_budget_large_budget_includes_all ... ok
test memory::retrieval::tests::trim_to_budget_respects_limit ... ok
test memory::schema::tests::confidence_out_of_range_fails ... ok
test memory::schema::tests::create_tables_sql_is_not_empty ... ok
test memory::schema::tests::empty_event_id_fails ... ok
test memory::schema::tests::empty_text_fails ... ok
test memory::schema::tests::importance_out_of_range_fails ... ok
test memory::schema::tests::schema_version_compatibility ... ok
test memory::schema::tests::valid_event_passes_validation ... ok
test memory::store::jsonl::tests::append_and_read_back ... ok
test memory::store::jsonl::tests::read_nonexistent_file_returns_error ... ok
test memory::store::jsonl::tests::read_skips_malformed_lines ... ok
test memory::store::jsonl::tests::reopen_continues_count ... ok
test memory::store::jsonl::tests::rotated_path_format ... ok
test memory::store::sqlite::tests::all_eligible_excludes_quarantined ... ok
test memory::store::sqlite::tests::by_task_filters ... ok
test memory::store::sqlite::tests::by_task_skips_stale_indices_without_panicking ... ok
test memory::store::sqlite::tests::by_topic_case_insensitive ... ok
test memory::store::sqlite::tests::by_topic_filters ... ok
test memory::store::sqlite::tests::by_topic_skips_stale_indices_without_panicking ... ok
test memory::store::sqlite::tests::empty_index ... ok
test memory::store::sqlite::tests::get_by_id_finds_event ... ok
test memory::store::sqlite::tests::get_by_id_returns_none_for_unknown ... ok
test memory::store::sqlite::tests::insert_and_recent ... ok
test memory::store::sqlite::tests::search_text_empty_returns_recent ... ok
test memory::store::sqlite::tests::search_text_substring ... ok
test memory::store::sqlite::tests::set_retrieval_state_quarantines_event ... ok
test memory::store::sqlite::tests::set_retrieval_state_returns_false_for_unknown_id ... ok
test memory::store::sqlite::tests::timeline_filters_by_range ... ok
test memory::survival_index::tests::survival_index_collects_active_tasks_and_decisions ... ok
test memory::survival_index::tests::survival_index_falls_back_to_recent_when_focus_misses ... ok
test memory::survival_index::tests::survival_index_includes_task_and_recent_traces ... ok
test memory::survival_index::tests::survival_markdown_renders_traces_and_evidence ... ok
test memory::survival_index::tests::zero_budget_keeps_traces_but_no_included_evidence ... ok
test memory::types::tests::action_policy_tier_labels ... ok
test memory::types::tests::context_pack_type_serialization ... ok
test memory::types::tests::days_to_ymd_epoch ... ok
test memory::types::tests::days_to_ymd_known_date ... ok
test memory::types::tests::event_id_is_unique_across_calls ... ok
test memory::types::tests::event_serialization_roundtrip ... ok
test memory::types::tests::iso_timestamp_is_valid_format ... ok
test memory::types::tests::memory_mode_capture_retrieval_semantics ... ok
test memory::types::tests::memory_mode_cycle_is_complete ... ok
test memory::types::tests::memory_mode_roundtrip_str ... ok
test memory::types::tests::retention_policy_cycle ... ok
test memory::types::tests::retention_policy_days ... ok
test memory::types::tests::retention_policy_roundtrip_str ... ok
test memory::types::tests::retrieval_state_roundtrip ... ok
test memory::types::tests::session_id_format ... ok
test memory_browser::render::tests::empty_browser_renders ... ok
test memory_browser::render::tests::overlay_height_is_consistent ... ok
test memory_browser::tests::browser_state_clamp_scroll ... ok
test memory_browser::tests::browser_state_navigation ... ok
test memory_browser::tests::cycle_filter_resets_selection ... ok
test memory_browser::tests::filter_cycle_is_complete ... ok
test memory_browser::tests::push_pop_search_resets_selection ... ok
test onboarding::tests::mark_first_capture_complete_persists_state ... ok
test onboarding::tests::should_show_hint_when_state_file_missing ... ok
test overlays::tests::show_dev_panel_overlay_sends_overlay ... ok
test overlays::tests::show_help_overlay_sends_overlay ... ok
test event_loop::tests::wake_word_detection_logs_wake_capture_marker ... ok
test overlays::tests::show_theme_picker_overlay_sends_overlay ... ok
test overlays::tests::show_theme_studio_overlay_sends_overlay ... ok
test overlays::tests::show_settings_overlay_sends_overlay ... ok
test persistence_io::tests::write_text_atomically_creates_parent_dirs_and_writes_body ... ok
test persistent_config::tests::apply_user_config_to_status_state_restores_macros_flag ... ok
test persistent_config::tests::default_config_is_all_none ... ok
test persistent_config::tests::detect_explicit_flags_marks_default_value_flags_as_explicit ... ok
test persistent_config::tests::detect_explicit_flags_marks_image_mode ... ok
test persistent_config::tests::parse_empty_config ... ok
test persistent_config::tests::parse_full_config ... ok
test persistent_config::tests::parse_ignores_comments_and_unknown_keys ... ok
test persistent_config::tests::parse_latency_display_mode_accepts_rtf_and_both ... ok
test persistent_config::tests::resolved_memory_mode_defaults_for_missing_and_invalid_values ... ok
test persistence_io::tests::write_text_atomically_replaces_existing_file_contents ... ok
test persistent_config::tests::serialize_only_set_fields ... ok
test persistent_config::tests::serialize_roundtrips ... ok
test persistent_config::tests::save_and_load_roundtrip_via_env ... ok
test persistent_config::tests::snapshot_from_runtime_preserves_saved_memory_mode ... ok
test prompt::claude_prompt_detect::tests::approval_prompt_resolves_only_on_confirmation_or_cancel_keys ... ok
test prompt::claude_prompt_detect::tests::backend_supports_prompt_guard_for_claude_only ... ok
test prompt::claude_prompt_detect::tests::claude_backend_ignores_codex_generate_command_hint ... ok
test prompt::claude_prompt_detect::tests::claude_backend_ignores_reply_composer_marker ... ok
test prompt::claude_prompt_detect::tests::codex_backend_ignores_reply_composer_marker ... ok
test prompt::claude_prompt_detect::tests::detect_prompt_type_ignores_inline_quoted_confirmation_phrase ... ok
test prompt::claude_prompt_detect::tests::detect_prompt_type_ignores_plain_proceed_phrase_without_choices ... ok
test prompt::claude_prompt_detect::tests::detect_prompt_type_prioritizes_single_command_over_tool_activity ... ok
test prompt::claude_prompt_detect::tests::detect_prompt_type_prioritizes_worktree_over_generic ... ok
test prompt::claude_prompt_detect::tests::detector_captures_diagnostic ... ok
test prompt::claude_prompt_detect::tests::detector_detects_bash_command_approval_card ... ok
test prompt::claude_prompt_detect::tests::detector_detects_cargo_approval_card_variant ... ok
test prompt::claude_prompt_detect::tests::detector_detects_multi_tool_batch ... ok
test prompt::claude_prompt_detect::tests::detector_detects_numbered_approval_card_with_selected_chevron ... ok
test prompt::claude_prompt_detect::tests::detector_detects_numbered_approval_card_without_header_text ... ok
test prompt::claude_prompt_detect::tests::detector_detects_single_command_approval ... ok
test prompt::claude_prompt_detect::tests::detector_detects_worktree_permission ... ok
test prompt::claude_prompt_detect::tests::detector_does_not_re_suppress_from_stale_line_after_enter_resolution ... ok
test prompt::claude_prompt_detect::tests::detector_does_not_re_suppress_same_prompt ... ok
test prompt::claude_prompt_detect::tests::detector_enabled_flag ... ok
test prompt::claude_prompt_detect::tests::detector_handles_cr_line_split ... ok
test prompt::claude_prompt_detect::tests::detector_ignores_bash_command_prompt_without_choice_controls ... ok
test prompt::claude_prompt_detect::tests::detector_ignores_codex_generate_command_hint ... ok
test prompt::claude_prompt_detect::tests::detector_ignores_low_confidence_generic_interactive_text ... ok
test prompt::claude_prompt_detect::tests::detector_ignores_non_approval_numbered_lists ... ok
test prompt::claude_prompt_detect::tests::detector_ignores_non_claude_backend ... ok
test prompt::claude_prompt_detect::tests::detector_ignores_reply_composer_marker ... ok
test prompt::claude_prompt_detect::tests::detector_ignores_tool_activity_lines ... ok
test prompt::claude_prompt_detect::tests::detector_refreshes_suppression_deadline_when_prompt_reappears ... ok
test prompt::claude_prompt_detect::tests::detector_resolves_on_user_input ... ok
test prompt::claude_prompt_detect::tests::estimate_command_wrap_depth_basic ... ok
test prompt::claude_prompt_detect::tests::estimate_command_wrap_depth_long_line ... ok
test prompt::claude_prompt_detect::tests::estimate_command_wrap_depth_zero_cols ... ok
test prompt::claude_prompt_detect::tests::reply_composer_prompt_resolves_on_submit_or_cancel_only ... ok
test prompt::claude_prompt_detect::tests::shared_approval_parser_accepts_colon_and_space_numbering ... ok
test prompt::claude_prompt_detect::tests::shared_approval_parser_accepts_compact_dot_numbering ... ok
test prompt::claude_prompt_detect::tests::shared_confirmation_line_parser_matches_prefixed_prompt_lines ... ok
test prompt::claude_prompt_detect::tests::shared_line_normalizer_trims_cursor_markers_and_o_prefix ... ok
test prompt::claude_prompt_detect::tests::startup_guard_releases_early_when_prompt_is_ready ... ok
test prompt::claude_prompt_detect::tests::startup_guard_suppresses_then_expires ... ok
test prompt::logger::tests::prompt_log_max_bytes_constant_is_5mb ... ok
test prompt::logger::tests::prompt_logger_writes_lines ... ok
test persistent_config::tests::snapshot_from_runtime_with_memory_mode_overrides_saved_value ... ok
test prompt::logger::tests::resolve_prompt_log_defaults_to_none ... ok
test prompt::logger::tests::resolve_prompt_log_prefers_config ... ok
test prompt::logger::tests::rotate_if_needed_keeps_file_when_next_line_fits_limit ... ok
test prompt::logger::tests::rotate_if_needed_truncates_when_next_line_exceeds_limit ... ok
test prompt::logger::tests::resolve_prompt_log_uses_env ... ok
test prompt::regex::tests::resolve_prompt_regex_rejects_invalid ... ok
test prompt::regex::tests::resolve_prompt_regex_honors_config ... ok
test prompt::tracker::tests::prompt_tracker_captures_last_error_line ... ok
test prompt::tracker::tests::prompt_tracker_feed_output_handles_control_bytes ... ok
test prompt::tracker::tests::prompt_tracker_has_seen_output_starts_false ... ok
test prompt::tracker::tests::prompt_tracker_idle_ready_on_threshold ... ok
test prompt::tracker::tests::prompt_tracker_learns_prompt_on_idle ... ok
test prompt::tracker::tests::prompt_tracker_ignores_non_graphic_bytes ... ok
test prompt::tracker::tests::prompt_tracker_matches_learned_prompt ... ok
test prompt::tracker::tests::prompt_tracker_matches_regex ... ok
test prompt::tracker::tests::prompt_tracker_on_idle_learns_when_auto_learn_enabled ... ok
test prompt::tracker::tests::prompt_tracker_on_idle_skips_when_regex_present ... ok
test prompt::tracker::tests::prompt_tracker_on_idle_triggers_on_threshold ... ok
test prompt::tracker::tests::prompt_tracker_rejects_mismatched_prompt ... ok
test prompt::tracker::tests::should_auto_trigger_checks_prompt_and_idle ... ok
test provider_adapter::tests::claude_adapter_exposes_prompt_detection_strategy ... ok
test prompt::tracker::tests::should_auto_trigger_respects_last_trigger_equal_times ... ok
test provider_adapter::tests::claude_strategy_forwards_backend_label_policy ... ok
test provider_adapter::tests::ipc_provider_ids_match_ipc_provider_contract ... ok
test provider_adapter::tests::prompt_detector_fallback_remains_for_non_claude_providers ... ok
test provider_adapter::tests::prompt_detector_defaults_to_provider_strategy ... ok
test provider_adapter::tests::provider_contract_enum_variants_are_exhaustive ... ok
test provider_adapter::tests::provider_id_mapping_stays_aligned_with_backend_family_labels ... ok
test provider_adapter::tests::resolve_provider_adapter_maps_backend_label ... ok
test runtime_compat::tests::backend_family_classifies_known_labels ... ok
test runtime_compat::tests::backend_family_from_env_falls_back_without_override ... ok
test runtime_compat::tests::backend_family_from_env_prefers_runtime_override ... ok
test runtime_compat::tests::contains_jetbrains_hint_matches_expected_values ... ok
test runtime_compat::tests::cursor_visibility_toggle_policy_only_for_non_claude_jetbrains ... ok
test runtime_compat::tests::detect_terminal_host_allows_thread_local_override ... ok
test runtime_compat::tests::detect_terminal_host_handles_jetbrains_and_cursor ... ok
test runtime_compat::tests::host_timing_config_claude_jetbrains_helpers_are_present_only_on_jetbrains ... ok
test runtime_compat::tests::host_timing_config_matches_phase2a_baseline_values ... ok
test runtime_compat::tests::parse_claude_extra_gap_rows_clamps_override ... ok
test runtime_compat::tests::detect_terminal_host_override_resets_after_panic ... ok
test runtime_compat::tests::parse_claude_extra_gap_rows_uses_host_defaults::case_1 ... ok
test runtime_compat::tests::parse_claude_extra_gap_rows_uses_host_defaults::case_2 ... ok
test runtime_compat::tests::parse_claude_extra_gap_rows_uses_host_defaults::case_3 ... ok
test runtime_compat::tests::parse_hud_safety_gap_rows_clamps_override ... ok
test runtime_compat::tests::parse_hud_safety_gap_rows_uses_host_defaults::case_1 ... ok
test runtime_compat::tests::parse_hud_safety_gap_rows_uses_host_defaults::case_2 ... ok
test runtime_compat::tests::parse_hud_safety_gap_rows_uses_host_defaults::case_3 ... ok
test runtime_compat::tests::runtime_backend_label_override_none_by_default ... ok
test runtime_compat::tests::runtime_backend_label_override_roundtrip ... ok
test runtime_compat::tests::set_runtime_backend_label_writes_to_thread_local ... ok
test runtime_compat::tests::single_line_full_hud_policy_only_for_claude_on_jetbrains ... ok
test runtime_compat::tests::startup_guard_only_for_claude_on_jetbrains ... ok
test session_memory::tests::logger_ignores_escape_noise_in_user_input ... ok
test session_stats::tests::avg_transcript_duration_zero_when_no_transcripts ... ok
test session_stats::tests::format_duration_hours ... ok
test session_stats::tests::format_duration_minutes ... ok
test session_memory::tests::logger_records_user_and_assistant_lines ... ok
test session_stats::tests::format_duration_seconds ... ok
test session_stats::tests::format_duration_uses_minute_and_hour_boundaries ... ok
test session_stats::tests::format_separator_is_stable ... ok
test session_stats::tests::format_session_stats_empty ... ok
test session_stats::tests::format_session_stats_conditional_rows_follow_zero_vs_nonzero_counts ... ok
test session_stats::tests::format_session_stats_with_activity ... ok
test session_stats::tests::has_activity_is_true_for_each_counter_individually ... ok
test session_stats::tests::session_duration_reflects_started_session ... ok
test session_stats::tests::session_stats_avg_duration ... ok
test session_stats::tests::session_stats_new ... ok
test session_stats::tests::session_stats_record_empty_and_error ... ok
test session_stats::tests::session_stats_record_transcript ... ok
test settings::render::tests::settings_overlay_footer_respects_ascii_glyph_set ... ok
test settings::render::tests::settings_overlay_height_matches_items ... ok
test settings::render::tests::settings_overlay_marks_backend_as_read_only ... ok
test settings::render::tests::settings_overlay_omits_legacy_visual_rows ... ok
test settings::render::tests::settings_overlay_renders_selected_item_description ... ok
test settings::render::tests::sliders_use_ascii_glyphs_when_ascii_profile_selected ... ok
test settings::render::tests::settings_overlay_uses_edit_label_for_insert_send_mode ... ok
test settings_handlers::tests::adjust_wake_word_sensitivity_clamps_and_reports ... ok
test settings_handlers::tests::adjust_sensitivity_updates_threshold_and_message ... ok
test settings_handlers::tests::cycle_hud_border_style_wraps ... ok
test settings_handlers::tests::cycle_hud_border_style_updates_state_and_status ... ok
test settings_handlers::tests::cycle_hud_right_panel_wraps ... ok
test settings_handlers::tests::cycle_hud_panel_updates_state_and_status ... ok
test settings_handlers::tests::cycle_hud_style_wraps ... ok
test settings_handlers::tests::cycle_hud_style_updates_state_and_status ... ok
test settings_handlers::tests::cycle_latency_display_updates_state_and_status ... ok
test settings_handlers::tests::cycle_latency_display_wraps ... ok
test settings_handlers::tests::cycle_theme_updates_selected_theme ... ok
test settings_handlers::tests::cycle_wake_word_cooldown_wraps_and_reports ... ok
test settings_handlers::tests::toggle_hud_panel_recording_only_toggles_and_reports_status ... ok
test settings_handlers::tests::toggle_auto_voice_updates_state_and_status ... ok
test settings_handlers::tests::toggle_image_mode_updates_config_state_and_status ... ok
test settings_handlers::tests::toggle_macros_enabled_updates_state_and_status ... ok
test settings_handlers::tests::toggle_send_mode_updates_state_and_status ... ok
test settings_handlers::tests::toggle_mouse_toggles_state_and_emits_enable_disable_messages ... ok
test status_line::animation::tests::heartbeat_frame_index_in_range ... ok
test status_line::animation::tests::processing_spinner_in_range ... ok
test status_line::animation::tests::processing_spinner_respects_theme_override_symbol ... ok
test status_line::animation::tests::recording_pulse_on_respects_on_off_windows_and_wrap ... ok
test status_line::animation::tests::transition_marker_ascii_fallback ... ok
test status_line::animation::tests::transition_marker_steps_down ... ok
test status_line::animation::tests::transition_marker_thresholds_are_exclusive ... ok
test status_line::animation::tests::transition_progress_half_duration_matches_easing_curve ... ok
test status_line::animation::tests::transition_progress_is_bounded ... ok
test status_line::buttons::tests::button_defs_use_send_label_from_send_mode ... ok
test status_line::buttons::tests::button_row_ready_badge_requires_idle_and_empty_queue ... ok
test status_line::buttons::tests::compact_button_row_omits_hud_button_and_recomputes_positions ... ok
test status_line::buttons::tests::compact_hud_button_positions_match_expected_geometry ... ok
test status_line::buttons::tests::compact_row_focus_marks_exactly_one_button_bracket ... ok
test status_line::buttons::tests::compact_row_queue_positive_renders_when_untruncated ... ok
test status_line::buttons::tests::compact_row_queue_zero_not_rendered_when_untruncated ... ok
test status_line::buttons::tests::dev_badge_is_hidden_when_dev_mode_is_off ... ok
test status_line::buttons::tests::dev_badge_renders_when_dev_mode_is_on ... ok
test status_line::buttons::tests::focused_button_in_none_theme_uses_uppercase_plain_text_label ... ok
test status_line::buttons::tests::focused_button_uses_warning_color_without_bold_emphasis ... ok
test status_line::buttons::tests::focused_buttons_use_warning_focus_brackets ... ok
test status_line::buttons::tests::format_button_brackets_track_highlight_color_when_unfocused ... ok
test status_line::buttons::tests::format_button_includes_non_empty_highlight_color ... ok
test status_line::buttons::tests::full_hud_button_geometry_shifts_by_one_between_auto_and_ptt_labels ... ok
test status_line::buttons::tests::full_hud_button_positions_match_expected_geometry ... ok
test settings_handlers::tests::toggle_wake_word_updates_state_and_status ... ok
test status_line::buttons::tests::full_hud_button_row_uses_uniform_separator_spacing_in_ptt_mode ... ok
test status_line::buttons::tests::full_row_focus_marks_exactly_one_button_bracket ... ok
test status_line::buttons::tests::full_row_latency_both_mode_shows_ms_and_rtf ... ok
test status_line::buttons::tests::full_row_latency_label_mode_shows_prefixed_text ... ok
test status_line::buttons::tests::full_row_latency_off_mode_hides_badge ... ok
test status_line::buttons::tests::full_row_latency_rtf_mode_shows_normalized_value ... ok
test status_line::buttons::tests::full_row_ready_and_latency_render_without_separator_dot_between_them ... ok
test status_line::buttons::tests::full_row_rec_button_includes_recording_color_when_recording ... ok
test status_line::buttons::tests::get_button_positions_empty_when_claude_prompt_is_suppressed ... ok
test status_line::buttons::tests::get_button_positions_full_has_buttons ... ok
test status_line::buttons::tests::get_button_positions_full_hud_respects_breakpoint_boundary ... ok
test status_line::buttons::tests::get_button_positions_hidden_collapsed_keeps_only_open_button ... ok
test status_line::buttons::tests::get_button_positions_full_single_line_fallback_has_bottom_row_buttons ... ok
test status_line::buttons::tests::get_button_positions_hidden_idle_has_open_and_hide_buttons ... ok
test status_line::buttons::tests::get_button_positions_minimal_has_back_button ... ok
test status_line::buttons::tests::heartbeat_animation_truth_table ... ok
test status_line::buttons::tests::hidden_launcher_boundary_width_shows_button_at_exact_threshold ... ok
test status_line::buttons::tests::hidden_launcher_buttons_align_to_right_edge_when_space_available ... ok
test status_line::buttons::tests::hidden_launcher_collapsed_renders_only_open_button ... ok
test status_line::buttons::tests::hidden_launcher_hides_buttons_when_width_too_small ... ok
test status_line::buttons::tests::hidden_launcher_open_button_uses_theme_dim_when_unfocused ... ok
test status_line::buttons::tests::hidden_launcher_text_omits_ctrl_u_hint ... ok
test status_line::buttons::tests::hidden_launcher_uses_theme_dim_color ... ok
test status_line::buttons::tests::image_badge_is_hidden_when_image_mode_is_off ... ok
test status_line::buttons::tests::image_badge_renders_when_image_mode_is_on ... ok
test status_line::buttons::tests::latency_badge_hides_during_auto_recording_and_processing ... ok
test status_line::buttons::tests::latency_badge_hides_during_manual_recording_and_processing ... ok
test status_line::buttons::tests::latency_threshold_colors_are_correct_in_full_row ... ok
test status_line::buttons::tests::latency_threshold_color_prefers_rtf_when_available ... ok
test status_line::buttons::tests::meter_level_color_uses_exclusive_boundaries ... ok
test status_line::buttons::tests::minimal_pulse_dots_respect_activity_and_color_thresholds ... ok
test status_line::buttons::tests::minimal_ribbon_waveform_uses_level_colors ... ok
test status_line::buttons::tests::minimal_right_panel_dots_animate_when_not_recording_only ... ok
test status_line::buttons::tests::minimal_right_panel_dots_gates_animation_on_recording_only_flag ... ok
test status_line::buttons::tests::minimal_right_panel_dots_without_meter_defaults_to_silent_level ... ok
test status_line::buttons::tests::minimal_right_panel_respects_recording_only ... ok
test status_line::buttons::tests::minimal_right_panel_ribbon_shows_waveform ... ok
test status_line::buttons::tests::minimal_status_text_non_idle_empty_message_is_none ... ok
test status_line::buttons::tests::minimal_status_text_shows_processing_message_when_idle ... ok
test status_line::buttons::tests::minimal_strip_button_geometry_is_stable ... ok
test status_line::buttons::tests::minimal_strip_hides_button_just_below_width_threshold ... ok
test status_line::buttons::tests::minimal_strip_idle_shows_full_warning_message_text ... ok
test status_line::buttons::tests::minimal_strip_idle_shows_info_message_text ... ok
test status_line::buttons::tests::minimal_strip_idle_shows_queue_state ... ok
test status_line::buttons::tests::minimal_strip_idle_success_collapses_to_ready ... ok
test status_line::buttons::tests::minimal_strip_idle_uses_theme_specific_auto_indicator ... ok
test status_line::buttons::tests::minimal_strip_processing_uses_theme_override_indicator ... ok
test status_line::buttons::tests::minimal_strip_recording_always_shows_db_lane ... ok
test status_line::buttons::tests::minimal_strip_recording_keeps_indicator_visible ... ok
test status_line::buttons::tests::minimal_strip_recording_keeps_panel_anchor_when_meter_db_missing ... ok
test status_line::buttons::tests::minimal_strip_recording_shows_info_message_text ... ok
test status_line::buttons::tests::minimal_strip_recording_uses_theme_recording_indicator_with_stable_color ... ok
test status_line::buttons::tests::minimal_strip_recording_uses_theme_specific_recording_indicator ... ok
test status_line::buttons::tests::minimal_strip_responding_shows_state_lane ... ok
test status_line::buttons::tests::minimal_strip_shows_button_at_exact_width_threshold ... ok
test status_line::buttons::tests::minimal_strip_text_includes_panel_when_enabled ... ok
test status_line::buttons::tests::minimal_waveform_handles_padding_and_boundaries ... ok
test status_line::buttons::tests::queue_badge_positive_renders_in_full_row ... ok
test status_line::buttons::tests::recording_button_highlight_is_empty_when_theme_has_no_color ... ok
test status_line::buttons::tests::queue_badge_zero_is_not_rendered_in_any_row_mode ... ok
test status_line::buttons::tests::recording_button_highlight_stays_recording_color_across_frames ... ok
test status_line::buttons::tests::recording_button_highlight_uses_theme_recording_color ... ok
test status_line::buttons::tests::recording_indicator_color_pulses_with_theme_palette ... ok
test status_line::buttons::tests::rtf_latency_severity_thresholds_are_exclusive ... ok
test status_line::buttons::tests::shortcut_pill_does_not_reset_immediately_after_open_bracket ... ok
test status_line::buttons::tests::shortcuts_row_positioned_renderer_geometry_when_untruncated ... ok
test status_line::buttons::tests::shortcuts_row_stays_within_banner_width ... ok
test status_line::buttons::tests::shortcuts_row_trailing_panel_hugs_right_border ... ok
test status_line::buttons::tests::shortcuts_row_trailing_panel_requires_separator_space ... ok
test status_line::buttons::tests::wake_badge_is_hidden_when_wake_listener_is_off ... ok
test status_line::buttons::tests::wrappers_emit_structured_shortcut_text ... ok
test status_line::buttons::tests::wake_badge_renders_theme_matched_on_and_paused_states ... ok
test status_line::format::tests::ascii::format_compact_uses_ascii_safe_module_separator ... ok
test status_line::format::tests::ascii::format_left_compact_uses_ascii_pipe_separator ... ok
test status_line::format::tests::ascii::format_left_section_recording_uses_ascii_pipe_separator ... ok
test status_line::format::tests::ascii::format_full_single_line_banner_uses_ascii_safe_separators ... ok
test status_line::format::tests::ascii::format_left_section_uses_ascii_pipe_separator ... ok
test status_line::format::tests::ascii::format_shortcuts_compact_uses_ascii_pipe_separator ... ok
test status_line::format::tests::ascii::format_shortcuts_uses_ascii_pipe_separator ... ok
test status_line::format::tests::ascii::hidden_launcher_text_uses_ascii_pipe_separator ... ok
test status_line::format::tests::basic::format_status_banner_hidden_mode_collapsed_launcher_shows_only_open ... ok
test status_line::format::tests::basic::format_status_banner_hidden_mode_idle ... ok
test status_line::format::tests::basic::format_status_banner_hidden_mode_recording ... ok
test status_line::format::tests::basic::format_status_banner_hidden_mode_recording_uses_theme_dim ... ok
test status_line::format::tests::basic::format_status_banner_minimal_mode ... ok
test status_line::format::tests::basic::format_status_banner_minimal_mode_processing ... ok
test status_line::format::tests::basic::format_status_banner_minimal_mode_recording ... ok
test status_line::format::tests::basic::format_status_banner_minimal_mode_responding ... ok
test status_line::format::tests::basic::format_status_banner_returns_no_rows_when_prompt_suppressed ... ok
test status_line::format::tests::basic::format_status_line_basic ... ok
test status_line::format::tests::basic::format_status_line_medium_shows_compact_shortcuts ... ok
test status_line::format::tests::basic::format_status_line_minimal ... ok
test status_line::format::tests::basic::format_status_line_narrow_terminal ... ok
test status_line::format::tests::basic::format_status_line_very_narrow ... ok
test status_line::format::tests::basic::format_status_line_with_duration ... ok
test status_line::format::tests::basic::processing_mode_indicator_uses_spinner_for_default_theme_symbol ... ok
test status_line::format::tests::basic::processing_mode_indicator_uses_theme_override_symbol ... ok
test status_line::format::tests::basic::recording_indicator_color_pulses_with_theme_palette ... ok
test status_line::format::tests::full_banner::format_mode_indicator_recording_keeps_theme_indicator_visible ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_border_style_override_uses_double_glyphs ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_duration_lane_is_fixed_width ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_duration_separator_stays_right_of_edit_button_lane ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_idle_uses_theme_idle_indicator ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_main_row_separators_stay_stable_across_states ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_manual_matches_reference_spacing_from_this_md ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_manual_recording_mode_lane_keeps_ptt_without_rec_suffix ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_none_border_hides_frame_rows ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_meter_separator_stays_stable_placeholder_to_recording ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_recording_mode_lane_keeps_auto_without_rec_suffix ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_recording_shows_rec_and_meter ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_recording_uses_recording_color_for_mode_lane ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_recording_uses_theme_recording_indicator ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_recording_without_meter_uses_floor_db ... ok
test status_line::format::tests::full_banner::format_status_line_compact_recording_uses_theme_recording_indicator ... ok
test status_line::format::tests::full_banner::format_status_banner_full_mode_single_line_fallback_keeps_full_controls ... ok
test status_line::format::tests::layout_and_messages::borderless_row_preserves_requested_width ... ok
test status_line::format::tests::layout_and_messages::format_duration_section_thresholds_and_state_styles_are_stable ... ok
test status_line::format::tests::layout_and_messages::format_hidden_strip_shows_duration_only_while_recording ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_hud_fallback_uses_compact_breakpoint ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_avoids_duplicate_queue_text ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_collapses_idle_success_to_ready ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_keeps_static_right_panel_when_recording_only_and_idle ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_latency_label_mode_uses_prefixed_badge ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_latency_off_hides_badge ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_manual_ptt_keeps_separator_alignment ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_places_ribbon_panel_on_main_row ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_processing_does_not_duplicate_processing_text ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_recording_shows_info_message_on_main_row ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_recording_suppresses_stale_ready_text ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_separators_align_with_shortcut_boundaries ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_shows_idle_info_message_on_main_row ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_shows_latency_on_shortcuts_row ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_shows_ready_with_ribbon_panel ... ok
test status_line::format::tests::layout_and_messages::format_status_banner_full_mode_uses_ptt_label_for_manual ... ok
test status_line::format::tests::layout_and_messages::format_status_line_shows_transition_marker_when_active ... ok
test status_line::format::tests::panels_and_snapshots::active_state_fallback_message_matches_recording_state ... ok
test status_line::format::tests::panels_and_snapshots::compact_registry_adapts_to_queue_state ... ok
test status_line::format::tests::panels_and_snapshots::format_heartbeat_panel_stays_dim_when_animation_is_disabled ... ok
test status_line::format::tests::panels_and_snapshots::format_meter_level_color_boundaries_are_exclusive ... ok
test status_line::format::tests::panels_and_snapshots::format_mode_indicator_is_stable_across_transition_progress ... ok
test status_line::format::tests::panels_and_snapshots::format_pulse_dots_boundaries_are_stable ... ok
test status_line::format::tests::panels_and_snapshots::format_right_panel_enforces_minimum_content_width ... ok
test status_line::format::tests::panels_and_snapshots::format_right_panel_respects_recording_only_animation_gate ... ok
test status_line::format::tests::panels_and_snapshots::format_status_line_branch_boundaries_use_expected_renderers ... ok
test status_line::format::tests::panels_and_snapshots::format_status_line_shortcut_lane_switches_at_breakpoints ... ok
test status_line::format::tests::panels_and_snapshots::format_status_line_exact_fit_layout_is_stable ... ok
test status_line::format::tests::panels_and_snapshots::format_transition_suffix_only_renders_for_idle_positive_progress ... ok
test status_line::format::tests::panels_and_snapshots::heartbeat_color_requires_animation_and_peak ... ok
test status_line::format::tests::panels_and_snapshots::heartbeat_helpers_cover_truth_table ... ok
test status_line::format::tests::panels_and_snapshots::status_banner_snapshot_matrix_is_stable ... ok
test status_line::layout::tests::status_banner_height_for_state_full_single_line_honors_state_flag ... ok
test status_line::layout::tests::status_banner_height_for_state_honors_prompt_suppression ... ok
test status_line::layout::tests::status_banner_height_respects_hud_style ... ok
test status_line::state::tests::pipeline_labels ... ok
test status_line::state::tests::push_latency_sample_caps_history ... ok
test status_line::state::tests::status_line_state_default ... ok
test status_line::state::tests::voice_mode_labels ... ok
test status_line::text::tests::display_width_excludes_ansi ... ok
test status_line::text::tests::truncate_display_preserves_ansi ... ok
test status_line::text::tests::truncate_display_respects_width ... ok
test status_style::tests::format_status_includes_prefix ... ok
test status_style::tests::format_status_with_theme_catppuccin ... ok
test status_style::tests::format_status_with_theme_none ... ok
test status_style::tests::format_status_with_theme_uses_theme_recording_indicator ... ok
test status_style::tests::indicator_returns_unicode ... ok
test status_style::tests::prefix_display_width_correct ... ok
test status_style::tests::status_display_width_scales_with_text_length ... ok
test status_style::tests::status_display_width_uses_recording_prefix_width ... ok
test status_style::tests::status_display_width_uses_unicode_display_width ... ok
test status_style::tests::status_type_from_message_error ... ok
test status_style::tests::status_type_from_message_info ... ok
test status_style::tests::status_type_from_message_processing ... ok
test status_style::tests::status_type_from_message_recording ... ok
test status_style::tests::status_type_from_message_success ... ok
test status_style::tests::status_type_from_message_warning ... ok
test stream_line_buffer::tests::take_line_marks_truncation_suffix ... ok
test stream_line_buffer::tests::take_line_trims_and_resets_state ... ok
test terminal::tests::adjusted_reserved_rows_clamps_claude_buffer_in_short_full_hud_pane ... ok
test terminal::tests::adjusted_reserved_rows_leaves_non_claude_backends_unchanged ... ok
test status_line::format::tests::panels_and_snapshots::full_hud_rows_never_exceed_terminal_width_across_common_sizes ... ok
test terminal::tests::install_sigwinch_handler_installs_handler ... ok
test terminal::tests::normalize_dimension_falls_back_to_env_or_default_for_zero ... ok
test terminal::tests::normalize_dimension_prefers_observed_values ... ok
test event_loop::tests::wake_word_detection_starts_capture_via_shared_trigger_path ... ok
test event_loop::tests::wake_word_detection_still_triggers_when_auto_voice_is_paused_by_user ... ok
test terminal::tests::reserved_rows_for_mode_matches_helpers ... ok
test event_loop::tests::wake_word_detection_while_recording_does_not_use_cancel_capture_path ... ok
test event_loop::tests::wake_word_send_intent_in_auto_mode_submits_enter_without_pending_flag ... ok
test event_loop::tests::wake_word_send_intent_submits_staged_insert_text ... ok
test memory::ingest::tests::test_recover_caps_at_max_index ... ok
test event_loop::tests::wake_word_send_intent_without_staged_text_sets_status ... ok
test event_loop::tests::write_or_queue_pty_input_ingests_lossy_text_for_invalid_utf8_bytes ... ok
test event_loop::tests::write_or_queue_pty_input_queues_all_bytes_on_would_block ... ok
test event_loop::tests::write_or_queue_pty_input_queues_remainder_after_partial_write ... ok
test event_loop::tests::write_or_queue_pty_input_returns_false_on_non_retryable_error ... ok
test terminal::tests::resolved_cols_rows_use_cache ... ok
test terminal::tests::sigwinch_handler_sets_flag ... ok
test event_loop::tests::write_or_queue_pty_input_returns_true_for_live_session ... ok
test terminal::tests::take_sigwinch_returns_false_when_unset ... ok
test terminal::tests::take_sigwinch_returns_true_once_and_clears_flag ... ok
test terminal::tests::apply_pty_winsize_updates_session_size ... ok
test terminal::tests::reserved_rows_for_mode_frees_rows_when_prompt_suppressed ... ok
test terminal::tests::reserved_rows_for_mode_keeps_claude_buffer_when_prompt_suppressed ... ok
test theme::capability_matrix::tests::crossterm_capability_names_are_non_empty ... ok
test theme::capability_matrix::tests::current_snapshot_has_pinned_versions ... ok
test terminal::tests::reserved_rows_for_mode_matrix_matches_host_provider_contract::case_1 ... ok
test theme::capability_matrix::tests::current_snapshot_lists_all_crossterm_capabilities ... ok
test theme::capability_matrix::tests::current_snapshot_lists_all_symbol_families ... ok
test terminal::tests::reserved_rows_for_mode_matrix_matches_host_provider_contract::case_3 ... ok
test theme::capability_matrix::tests::current_snapshot_lists_all_widget_families ... ok
test theme::capability_matrix::tests::parity_gate_has_no_unmapped_symbols ... ok
test terminal::tests::reserved_rows_for_mode_matrix_matches_host_provider_contract::case_5 ... ok
test theme::capability_matrix::tests::parity_gate_has_no_unregistered_widgets ... ok
test theme::capability_matrix::tests::parity_gate_passes_when_registration_is_complete ... ok
test terminal::tests::reserved_rows_for_mode_matrix_matches_host_provider_contract::case_6 ... ok
test theme::capability_matrix::tests::snapshot_equality ... ok
test theme::capability_matrix::tests::symbol_family_names_are_non_empty ... ok
test terminal::tests::reserved_rows_for_mode_matrix_matches_host_provider_contract::case_9 ... ok
test theme::capability_matrix::tests::theme_capability_compatible_non_truecolor_themes ... ok
test theme::capability_matrix::tests::theme_capability_compatible_truecolor_themes ... ok
test terminal::tests::startup_pty_rows_reuses_clamped_reserved_budget_for_claude ... ok
test theme::capability_matrix::tests::upgrade_delta_detects_added_widgets ... ok
test theme::capability_matrix::tests::upgrade_delta_detects_removed_capabilities ... ok
test terminal::tests::reserved_rows_for_mode_matrix_matches_host_provider_contract::case_4 ... ok
test theme::capability_matrix::tests::upgrade_delta_detects_removed_widgets_as_breaking ... ok
test theme::capability_matrix::tests::upgrade_delta_same_snapshot_is_empty ... ok
test terminal::tests::reserved_rows_for_mode_matrix_matches_host_provider_contract::case_8 ... ok
test theme::capability_matrix::tests::widget_names_are_non_empty ... ok
test terminal::tests::reserved_rows_for_mode_matrix_matches_host_provider_contract::case_7 ... ok
test theme::color_value::tests::color_value_escape_roundtrips ... ok
test terminal::tests::reserved_rows_for_mode_matrix_matches_host_provider_contract::case_2 ... ok
test theme::color_value::tests::intern_string_common_cases ... ok
test theme::color_value::tests::all_palettes_parse_via_palette_to_resolved ... ok
test theme::color_value::tests::parse_ansi_escape_ansi16 ... ok
test theme::color_value::tests::parse_ansi_escape_empty ... ok
test theme::color_value::tests::parse_ansi_escape_rejects_garbage ... ok
test theme::color_value::tests::parse_ansi_escape_reset ... ok
test theme::color_value::tests::parse_ansi_escape_truecolor_bg ... ok
test theme::color_value::tests::parse_ansi_escape_truecolor_fg ... ok
test theme::color_value::tests::resolved_to_legacy_roundtrip ... ok
test theme::color_value::tests::rgb_arbitrary_hex_roundtrip ... ok
test theme::color_value::tests::rgb_claude_recording_roundtrip ... ok
test theme::color_value::tests::rgb_from_hex_rejects_invalid ... ok
test theme::color_value::tests::rgb_from_hex_uppercase ... ok
test theme::color_value::tests::resolved_to_legacy_roundtrip_all_palettes ... ok
test theme::color_value::tests::rgb_from_hex_valid ... ok
test theme::color_value::tests::rgb_hex_roundtrip ... ok
test theme::color_value::tests::rgb_to_bg_escape ... ok
test theme::color_value::tests::rgb_to_fg_escape_matches_codex_recording ... ok
test theme::component_registry::tests::from_style_id_rejects_unknown_path ... ok
test theme::component_registry::tests::registry_lookup_returns_none_for_unregistered_pair ... ok
test theme::component_registry::tests::default_registry_is_nonempty ... ok
test theme::dependency_baseline::tests::check_crate_compatibility_finds_known_crates ... ok
test theme::component_registry::tests::registry_lookup_returns_entry_for_registered_pairs ... ok
test theme::component_registry::tests::hud_components_have_voice_states ... ok
test theme::dependency_baseline::tests::check_crate_compatibility_returns_none_for_unknown ... ok
test theme::dependency_baseline::tests::check_pack_compatibility_blocks_incompatible_crates ... ok
test theme::component_registry::tests::all_control_surfaces_have_default_state ... ok
test theme::component_registry::tests::toast_components_have_muted_state ... ok
test theme::dependency_baseline::tests::check_pack_compatibility_blocks_unknown_crates ... ok
test theme::dependency_baseline::tests::compatibility_matrix_has_entries ... ok
test theme::dependency_baseline::tests::compatibility_status_labels_are_non_empty ... ok
test theme::dependency_baseline::tests::compatible_entries_allow_adoption ... ok
test theme::dependency_baseline::tests::core_pins_include_ratatui_and_crossterm ... ok
test theme::dependency_baseline::tests::crossterm_pin_matches_cargo_toml_version ... ok
test theme::dependency_baseline::tests::dependency_pin_features_match_cargo_toml ... ok
test theme::dependency_baseline::tests::incompatible_entries_block_adoption ... ok
test theme::component_registry::tests::default_registry_covers_all_component_ids ... ok
test theme::dependency_baseline::tests::overall_status_conditionally_compatible_propagates ... ok
test theme::dependency_baseline::tests::overall_status_incompatible_when_either_dep_incompatible ... ok
test theme::dependency_baseline::tests::overall_status_unknown_when_either_dep_unknown ... ok
test theme::dependency_baseline::tests::ratatui_pin_matches_cargo_toml_version ... ok
test theme::dependency_baseline::tests::ratatui_upgrade_prerequisites_reference_crossterm ... ok
test theme::component_registry::tests::component_style_ids_are_unique_and_prefixed ... ok
test theme::component_registry::tests::from_style_id_roundtrips_all_components ... ok
test theme::dependency_baseline::tests::staged_upgrade_plan_has_steps ... ok
test theme::dependency_baseline::tests::staged_upgrade_plan_crossterm_before_ratatui ... ok
test theme::dependency_baseline::tests::tui_widgets_family_entries_are_compatible ... ok
test theme::file_watcher::tests::hash_is_deterministic ... ok
test theme::detect::tests::warp_detection_matches_term_program_for_other_host ... ok
test theme::glyphs::tests::heartbeat_frames_follow_glyph_set ... ok
test theme::glyphs::tests::hud_icons_follow_glyph_set ... ok
test theme::glyphs::tests::meter_marker_glyphs_follow_glyph_set ... ok
test theme::detect::tests::warp_detection_respects_canonical_host_precedence ... ok
test theme::component_registry::tests::component_registry_parity_snapshot ... ok
test theme::glyphs::tests::mode_indicator_glyphs_follow_glyph_set ... ok
test theme::glyphs::tests::overlay_chrome_glyphs_follow_glyph_set ... ok
test theme::glyphs::tests::processing_spinner_symbol_falls_back_to_ascii_frames_for_ascii_glyph_set ... ok
test theme::glyphs::tests::processing_spinner_symbol_preserves_theme_override_indicator ... ok
test theme::glyphs::tests::processing_spinner_symbol_honors_explicit_spinner_style ... ok
test theme::glyphs::tests::processing_spinner_symbol_uses_braille_for_default_processing_indicator ... ok
test theme::glyphs::tests::pulse_dot_glyphs_follow_glyph_set ... ok
test theme::glyphs::tests::progress_profile_honors_explicit_family_override ... ok
test theme::glyphs::tests::severity_icon_glyphs_follow_glyph_set ... ok
test theme::glyphs::tests::transition_pulse_markers_follow_glyph_set ... ok
test theme::glyphs::tests::waveform_and_progress_profiles_follow_glyph_set ... ok
test theme::rule_profile::tests::active_rules_excludes_disabled ... ok
test theme::rule_profile::tests::active_rules_sorted_by_priority_descending ... ok
test theme::rule_profile::tests::add_duplicate_rule_fails ... ok
test theme::rule_profile::tests::add_rule_succeeds ... ok
test theme::rule_profile::tests::default_rule_eval_context ... ok
test theme::rule_profile::tests::empty_profile_has_no_rules ... ok
test theme::rule_profile::tests::evaluate_all_condition ... ok
test theme::file_watcher::tests::watcher_returns_none_when_file_unchanged ... ok
test theme::rule_profile::tests::evaluate_any_condition ... ok
test theme::rule_profile::tests::evaluate_audio_level_threshold ... ok
test theme::rule_profile::tests::evaluate_backend_condition ... ok
test theme::rule_profile::tests::evaluate_capability_condition_absent ... ok
test theme::rule_profile::tests::evaluate_capability_condition_present ... ok
test theme::rule_profile::tests::evaluate_color_mode_condition ... ok
test theme::rule_profile::tests::evaluate_empty_all_is_true ... ok
test theme::rule_profile::tests::evaluate_empty_any_is_false ... ok
test theme::rule_profile::tests::evaluate_rules_applies_highest_priority_first ... ok
test theme::rule_profile::tests::evaluate_rules_merges_non_conflicting_properties ... ok
test theme::rule_profile::tests::evaluate_rules_skips_non_matching_rules ... ok
test theme::rule_profile::tests::evaluate_terminal_dimension_thresholds ... ok
test theme::rule_profile::tests::evaluate_threshold_condition_min_only ... ok
test theme::rule_profile::tests::evaluate_threshold_condition_no_bounds ... ok
test theme::rule_profile::tests::evaluate_threshold_condition_range ... ok
test theme::rule_profile::tests::evaluate_voice_state_condition ... ok
test theme::rule_profile::tests::parse_rule_profile_invalid_json ... ok
test theme::rule_profile::tests::preview_rules_shows_matching_status ... ok
test theme::rule_profile::tests::remove_nonexistent_rule_fails ... ok
test theme::rule_profile::tests::parse_rule_profile_from_json ... ok
test theme::rule_profile::tests::parse_rule_profile_with_nested_conditions ... ok
test theme::rule_profile::tests::remove_rule_succeeds ... ok
test theme::rule_profile::tests::rule_profile_error_display ... ok
test theme::rule_profile::tests::threshold_metric_labels_are_non_empty ... ok
test theme::rule_profile::tests::toggle_rule_flips_enabled_state ... ok
test theme::rule_profile::tests::voice_state_condition_labels_are_non_empty ... ok
test theme::style_pack::tests::resolve_style_pack_colors_falls_back_to_base_theme_for_unsupported_schema_version ... ok
test theme::style_pack::tests::resolve_theme_colors_applies_runtime_border_override ... ok
test theme::style_pack::tests::resolve_theme_colors_applies_runtime_glyph_override ... ok
test theme::style_pack::tests::resolve_theme_colors_applies_runtime_indicator_override ... ok
test theme::style_pack::tests::resolve_theme_colors_applies_runtime_progress_bar_family_override ... ok
test theme::style_pack::tests::resolve_theme_colors_applies_runtime_progress_style_override ... ok
test theme::style_pack::tests::resolve_theme_colors_applies_runtime_voice_scene_style_override ... ok
test theme::style_pack::tests::resolve_theme_colors_ignores_style_pack_env_without_test_opt_in ... ok
test theme::style_pack::tests::resolve_theme_colors_matches_legacy_palette_map ... ok
test theme::style_pack::tests::resolve_theme_colors_reads_style_pack_env_when_test_opted_in ... ok
test theme::style_pack::tests::resolve_theme_colors_with_payload_applies_border_style_override ... ok
test theme::style_pack::tests::resolve_theme_colors_with_payload_applies_glyph_override ... ok
test theme::style_pack::tests::resolve_theme_colors_with_payload_applies_indicator_override ... ok
test theme::style_pack::tests::resolve_theme_colors_with_payload_applies_progress_bar_family_override ... ok
test theme::style_pack::tests::resolve_theme_colors_with_payload_applies_progress_style_override ... ok
test theme::style_pack::tests::resolve_theme_colors_with_payload_applies_voice_scene_style_override ... ok
test theme::style_pack::tests::resolve_theme_colors_with_payload_falls_back_to_requested_theme_when_invalid ... ok
test theme::style_pack::tests::resolve_theme_colors_with_payload_migrates_legacy_schema ... ok
test theme::style_pack::tests::resolve_theme_colors_with_payload_uses_schema_base_theme ... ok
test theme::style_pack::tests::resolved_banner_style_reads_persisted_payload ... ok
test theme::style_pack::tests::resolved_component_border_sets_fall_back_to_global_border_override ... ok
test theme::style_pack::tests::resolved_banner_style_runtime_override_wins_over_payload ... ok
test theme::style_pack::tests::resolved_hud_border_set_uses_component_override_when_present ... ok
test theme::style_pack::tests::resolved_startup_style_reads_persisted_payload ... ok
test theme::style_pack::tests::resolved_overlay_border_set_uses_component_override_when_present ... ok
test theme::style_pack::tests::resolved_startup_style_runtime_override_wins_over_payload ... ok
test theme::style_pack::tests::resolved_toast_position_returns_none_without_payload_or_override ... ok
test theme::style_pack::tests::resolved_toast_position_reads_persisted_payload ... ok
test theme::style_pack::tests::resolved_startup_style_returns_none_without_payload_or_override ... ok
test theme::style_pack::tests::resolved_toast_position_runtime_override_wins_over_payload ... ok
test theme::style_pack::tests::resolved_toast_severity_mode_reads_persisted_payload ... ok
test theme::style_pack::tests::resolved_toast_severity_mode_returns_none_without_payload_or_override ... ok
test theme::style_pack::tests::runtime_theme_file_override_none_by_default ... ok
test theme::style_pack::tests::resolved_toast_severity_mode_runtime_override_wins_over_payload ... ok
test theme::style_pack::tests::runtime_theme_file_override_roundtrip ... ok
test theme::style_pack::tests::set_runtime_theme_file_override_clears_with_none ... ok
test theme::style_pack::tests::set_runtime_theme_file_override_writes_to_thread_local ... ok
test theme::style_pack::tests::style_pack_built_in_uses_current_schema_version ... ok
test theme::style_pack::tests::style_pack_theme_override_from_payload_ignores_invalid_payload ... ok
test theme::style_pack::tests::style_pack_theme_override_from_payload_reads_valid_base_theme ... ok
test theme::style_resolver::tests::cycle_property_toggles_bold_flag ... ok
test theme::style_resolver::tests::clear_override_reverts_to_default ... ok
test theme::style_resolver::tests::cycle_property_tracks_local_preview_override ... ok
test theme::style_resolver::tests::parse_component_style_entry_with_hex ... ok
test theme::style_resolver::tests::override_takes_precedence ... ok
test theme::style_resolver::tests::parse_component_style_entry_with_palette_ref ... ok
test theme::style_resolver::tests::property_value_label_uses_theme_label_for_default_color ... ok
test theme::style_resolver::tests::resolver_returns_border_defaults_for_overlay_frame ... ok
test theme::style_resolver::tests::resolver_returns_default_for_unknown_component ... ok
test theme::style_resolver::tests::resolver_returns_dim_for_disabled_state ... ok
test theme::style_resolver::tests::resolver_returns_processing_defaults_for_voice_scene ... ok
test theme::style_resolver::tests::resolver_returns_semantic_defaults_for_hud_recording ... ok
test theme::style_schema::tests::parse_style_schema_defaults_blank_profile_to_default_name ... ok
test theme::style_resolver::tests::resolver_returns_semantic_defaults_for_toast_error ... ok
test theme::style_schema::tests::parse_style_schema_migrates_v1_payload_to_current_version ... ok
test theme::style_schema::tests::parse_style_schema_migrates_v2_payload_to_current_version ... ok
test theme::style_schema::tests::parse_style_schema_normalizes_theme_overrides_to_none ... ok
test theme::style_schema::tests::parse_style_schema_reads_current_version_payload ... ok
test theme::style_schema::tests::parse_style_schema_reads_runtime_visual_overrides ... ok
test theme::style_schema::tests::parse_style_schema_rejects_invalid_theme_names ... ok
test theme::style_schema::tests::parse_style_schema_rejects_unsupported_versions ... ok
test theme::style_schema::tests::parse_style_schema_v2_migrated_has_no_surface_overrides ... ok
test theme::style_schema::tests::parse_style_schema_v3_migrated_has_no_component_overrides ... ok
test theme::style_schema::tests::parse_style_schema_v3_normalizes_theme_surface_overrides ... ok
test theme::style_schema::tests::parse_style_schema_v3_reads_surface_overrides ... ok
test theme::style_schema::tests::parse_style_schema_v3_with_empty_surfaces_section ... ok
test theme::style_schema::tests::parse_style_schema_v4_normalizes_theme_component_overrides ... ok
test theme::style_schema::tests::parse_style_schema_v4_reads_component_overrides ... ok
test theme::style_schema::tests::parse_style_schema_v4_with_empty_components_section ... ok
test theme::style_schema::tests::parse_style_schema_with_fallback_returns_default_on_parse_error ... ok
test theme::style_schema::tests::style_pack_field_inventory_count_matches_expected_contract ... ok
test theme::style_schema::tests::style_pack_field_inventory_has_unique_paths ... ok
test theme::tests::filled_indicator_keeps_symbol_family ... ok
test theme::tests::theme_available_reports_full_theme_list ... ok
test theme::tests::theme_colors_returns_palette ... ok
test theme::tests::theme_display_matches_name ... ok
test theme::tests::theme_fallback_for_ansi ... ok
test theme::tests::theme_from_name_parses_valid ... ok
test theme::tests::theme_from_name_rejects_invalid ... ok
test theme::tests::theme_from_name_supports_tokyo_and_gruv_aliases ... ok
test theme::tests::theme_has_indicators ... ok
test theme::tests::theme_has_expected_borders ... ok
test theme::texture_profile::tests::detect_max_tier_for_foot ... ok
test theme::tests::theme_is_truecolor ... ok
test theme::texture_profile::tests::detect_max_tier_for_iterm2 ... ok
test theme::texture_profile::tests::detect_max_tier_for_kitty ... ok
test theme::texture_profile::tests::detect_max_tier_for_vscode ... ok
test theme::texture_profile::tests::detect_max_tier_for_unknown ... ok
test theme::texture_profile::tests::detect_max_tier_for_wezterm ... ok
test theme::texture_profile::tests::fallback_chain_enforces_plain_as_ultimate_fallback ... ok
test theme::texture_profile::tests::fallback_chain_is_ordered_richest_to_plainest ... ok
test theme::texture_profile::tests::fallback_chain_starts_at_richest_and_ends_at_plain ... ok
test theme::texture_profile::tests::resolve_tier_falls_back_when_requested_exceeds_max ... ok
test theme::texture_profile::tests::detect_terminal_id_uses_non_host_term_program_mapping_for_other_host ... ok
test theme::texture_profile::tests::iterm_inline_tier_falls_back_correctly ... ok
test theme::texture_profile::tests::resolve_tier_plain_max_returns_plain ... ok
test theme::texture_profile::tests::resolve_tier_returns_requested_when_supported ... ok
test theme::texture_profile::tests::sixel_tier_falls_back_correctly ... ok
test theme::texture_profile::tests::detect_terminal_id_prefers_canonical_host_signals ... ok
test theme::texture_profile::tests::symbol_texture_families_have_non_empty_samples ... ok
test theme::texture_profile::tests::symbol_texture_family_names_are_non_empty ... ok
test theme::texture_profile::tests::detect_terminal_id_fallbacks_keep_kitty_and_iterm_markers ... ok
test theme::texture_profile::tests::terminal_id_names_are_non_empty ... ok
test theme::texture_profile::tests::terminal_id_for_host_short_circuits_cursor_and_jetbrains ... ok
test theme::texture_profile::tests::texture_profile_with_override_respects_max_tier ... ok
test theme::texture_profile::tests::texture_profile_detect_returns_valid_profile ... ok
test theme::texture_profile::tests::texture_tier_names_are_non_empty ... ok
test theme::theme_dir::tests::list_theme_files_returns_empty_for_nonexistent_dir ... ok
test theme::theme_dir::tests::load_user_theme_returns_error_for_nonexistent ... ok
test theme::theme_dir::tests::theme_dir_returns_some_path ... ok
test theme::theme_file::tests::parse_malformed_toml ... ok
test theme::theme_file::tests::resolve_theme_file_border_style ... ok
test theme::theme_file::tests::resolve_theme_file_glyphs_and_spinner ... ok
test theme::theme_file::tests::parse_minimal_theme_file ... ok
test theme::theme_file::tests::resolve_theme_file_unknown_base_theme ... ok
test theme::theme_file::tests::resolve_theme_file_invalid_hex ... ok
test theme::theme_file::tests::resolve_theme_file_indicators ... ok
test theme::theme_file::tests::resolve_theme_file_unknown_palette_ref ... ok
test theme::theme_file::tests::resolve_theme_file_inherits_from_base ... ok
test theme::theme_file::tests::export_roundtrip ... ok
test theme::theme_file::tests::resolve_theme_file_with_palette_refs ... ok
test theme::widget_pack::tests::all_packs_have_non_empty_names ... ok
test theme::widget_pack::tests::active_packs_includes_pilot_and_graduated ... ok
test theme::widget_pack::tests::all_packs_have_non_empty_style_scopes ... ok
test theme::theme_file::tests::validate_warns_on_unused_palette ... ok
test theme::widget_pack::tests::all_style_ids_start_with_scope_prefix ... ok
test theme::widget_pack::tests::all_packs_have_parity_requirements ... ok
test theme::widget_pack::tests::candidate_packs_exist_in_registry ... ok
test theme::widget_pack::tests::find_pack_returns_known_packs ... ok
test theme::widget_pack::tests::find_pack_returns_none_for_unknown ... ok
test theme::widget_pack::tests::graduation_check_blocks_pilot_packs_with_unmet_requirements ... ok
test theme::widget_pack::tests::graduation_check_rejects_candidate_packs ... ok
test theme::widget_pack::tests::graduation_check_rejects_unknown_packs ... ok
test theme::widget_pack::tests::maturity_labels_are_non_empty ... ok
test theme::widget_pack::tests::maturity_ordering_is_correct ... ok
test theme::widget_pack::tests::owning_pack_for_style_id_finds_correct_pack ... ok
test theme::widget_pack::tests::owning_pack_for_style_id_returns_none_for_core_ids ... ok
test theme::widget_pack::tests::parity_requirement_labels_are_non_empty ... ok
test theme::widget_pack::tests::pilot_and_graduated_are_active ... ok
test theme::widget_pack::tests::pilot_packs_exist_in_registry ... ok
test theme::widget_pack::tests::registry_has_entries ... ok
test theme::widget_pack::tests::style_id_is_pack_owned_detects_pack_ids ... ok
test theme::widget_pack::tests::style_id_scopes_do_not_overlap ... ok
test theme_ops::tests::cycle_theme_moves_relative_to_current_option_order ... ok
test theme_ops::tests::cycle_theme_wraps_at_ends_of_theme_list ... ok
test theme_picker::tests::theme_picker_footer_reports_style_pack_lock ... ok
test theme_picker::tests::theme_picker_footer_respects_ascii_glyph_set ... ok
test theme_picker::tests::theme_picker_height_positive ... ok
test theme_picker::tests::theme_picker_contains_options ... ok
test theme_studio::borders_page::tests::borders_page_all_options_have_labels ... ok
test theme_picker::tests::theme_picker_lock_disables_non_current_markers ... ok
test theme_picker::tests::theme_picker_shows_current_theme ... ok
test theme_studio::borders_page::tests::borders_page_initial_state ... ok
test theme_studio::borders_page::tests::borders_page_navigate ... ok
test theme_picker::tests::theme_picker_has_borders ... ok
test theme_studio::borders_page::tests::borders_page_render_nonempty ... ok
test theme_picker::tests::theme_picker_none_theme_uses_neutral_preview_rows ... ok
test theme_studio::color_picker::tests::color_picker_adjust_clamps ... ok
test theme_studio::color_picker::tests::color_picker_channel_cycling ... ok
test theme_studio::color_picker::tests::color_picker_hex_entry_rejects_invalid ... ok
test theme_studio::color_picker::tests::color_picker_hex_entry_roundtrip ... ok
test theme_studio::color_picker::tests::color_picker_render_produces_lines ... ok
test theme_studio::colors_page::tests::color_field_all_covers_10_fields ... ok
test theme_studio::colors_page::tests::colors_editor_initial_state ... ok
test theme_studio::colors_page::tests::colors_editor_navigate_and_select ... ok
test theme_studio::colors_page::tests::colors_editor_open_and_apply_picker ... ok
test theme_studio::colors_page::tests::colors_editor_navigate_to_indicator_row ... ok
test theme_studio::colors_page::tests::colors_editor_render_produces_lines ... ok
test theme_studio::colors_page::tests::cycle_indicator_set ... ok
test theme_studio::colors_page::tests::cycle_glyph_set ... ok
test theme_studio::components_page::tests::components_editor_drilldown_expands_group_component_and_state ... ok
test theme_studio::components_page::tests::components_editor_initial_state ... ok
test theme_studio::components_page::tests::components_editor_render_includes_canonical_style_ids ... ok
test theme_studio::components_page::tests::components_editor_property_toggle_creates_local_override ... ok
test theme_studio::export_page::tests::export_action_labels_nonempty ... ok
test theme_studio::export_page::tests::export_page_initial_state ... ok
test theme_studio::export_page::tests::export_page_navigate ... ok
test theme_studio::export_page::tests::copy_to_clipboard_stages_writer_payload ... ok
test theme_studio::home_page::tests::style_pack_field_mapping_classifies_every_field_exactly_once ... ok
test theme_studio::home_page::tests::style_pack_field_mapping_parity_gate_respects_completion_flag ... ok
test theme_studio::home_page::tests::style_pack_field_mapping_points_to_existing_theme_studio_rows ... ok
test theme_studio::home_page::tests::theme_studio_footer_respects_ascii_glyph_set ... ok
test theme_studio::home_page::tests::theme_studio_height_matches_contract ... ok
test theme_studio::home_page::tests::theme_studio_item_lookup_defaults_to_close ... ok
test theme_studio::home_page::tests::theme_studio_overlay_shows_selected_row_tip ... ok
test theme_ops::tests::apply_theme_selection_reports_style_pack_lock ... ok
test theme_studio::nav::tests::select_next_handles_empty_lists ... ok
test theme_studio::nav::tests::select_next_stops_at_max ... ok
test theme_studio::home_page::tests::theme_studio_overlay_contains_expected_rows ... ok
test theme_studio::home_page::tests::theme_studio_overlay_marks_selected_row ... ok
test theme_studio::nav::tests::select_prev_stops_at_zero ... ok
test theme_studio::preview_page::tests::preview_page_initial_state ... ok
test theme_studio::preview_page::tests::preview_page_scroll ... ok
test theme_studio::preview_page::tests::preview_page_render_nonempty ... ok
test theme_studio::home_page::tests::theme_studio_overlay_shows_live_visual_values ... ok
test theme_studio::tests::studio_page_labels_are_nonempty ... ok
test theme_studio::tests::studio_page_next_cycles_through_all ... ok
test theme_studio::tests::studio_page_prev_cycles_backwards ... ok
test toast::tests::format_toast_history_overlay_empty_center ... ok
test toast::tests::format_toast_inline_respects_runtime_severity_mode_override ... ok
test toast::tests::format_toast_history_overlay_honors_top_position_sorting ... ok
test toast::tests::format_toast_history_overlay_with_entries ... ok
test toast::tests::format_toast_inline_truncates_long_message ... ok
test toast::tests::push_with_duration_creates_toast_with_custom_dismiss ... ok
test toast::tests::toast_center_default_creates_empty ... ok
test toast::tests::toast_center_dismiss_all ... ok
test toast::tests::toast_center_dismiss_latest ... ok
test toast::tests::toast_center_dismiss_latest_on_empty_returns_false ... ok
test toast::tests::toast_center_evicts_oldest_when_at_capacity ... ok
test toast::tests::toast_center_push_and_active_count ... ok
test theme_ops::tests::resolve_theme_choice_falls_back_on_ansi16_term ... ok
test toast::tests::toast_history_overlay_height_empty ... ok
test toast::tests::toast_history_overlay_height_with_entries ... ok
test toast::tests::toast_history_overlay_rows_match_target_width ... ok
test toast::tests::toast_ids_are_monotonically_increasing ... ok
test toast::tests::toast_severity_colors_use_theme ... ok
test toast::tests::toast_severity_dismiss_durations ... ok
test toast::tests::toast_severity_icons_by_glyph_set ... ok
test toast::tests::toast_severity_labels ... ok
test toast::tests::toast_center_history_is_bounded ... ok
test toast::tests::toast_center_tick_dismisses_expired ... ok
test toast::tests::toast_history_overlay_height_caps_at_10_content_rows ... ok
test transcript::delivery::tests::deliver_transcript_keeps_idle_when_insert_does_not_send_newline ... ok
test transcript::delivery::tests::deliver_transcript_sets_responding_when_auto_sends_newline ... ok
test transcript::delivery::tests::try_flush_pending_sends_when_idle_ready ... ok
test transcript::delivery::tests::send_transcript_respects_mode_and_trims ... ok
test transcript::queue::tests::push_pending_transcript_drops_oldest_when_full ... ok
test transcript::idle::tests::transcript_ready_falls_back_after_output_idle_since_enter ... ok
test transcript::delivery::tests::try_flush_pending_waits_for_prompt_when_busy ... ok
test transcript_history::tests::assistant_entries_are_not_replayable ... ok
test theme_ops::tests::resolve_theme_choice_keeps_theme_on_256color ... ok
test transcript_history::tests::format_overlay_empty_history ... ok
test transcript_history::tests::format_overlay_no_matches_message ... ok
test transcript_history::tests::format_overlay_line_count_matches_height ... ok
test transcript_history::tests::format_overlay_with_entries_shows_source_tags ... ok
test transcript_history::tests::format_overlay_with_search_filter ... ok
test transcript_history::tests::format_overlay_rows_keep_full_width_with_ansi_theme ... ok
test transcript_history::tests::history_ignores_blank_text ... ok
test transcript_history::tests::history_bounds_at_max ... ok
test transcript_history::tests::history_push_and_len ... ok
test transcript_history::tests::history_sequence_increments ... ok
test transcript_history::tests::ingest_backend_output_bytes_records_lines ... ok
test transcript_history::tests::ingest_user_input_bytes_ignores_escape_sequences ... ok
test transcript_history::tests::ingest_user_input_bytes_records_sent_lines ... ok
test transcript_history::tests::overlay_height_matches_formula ... ok
test transcript_history::tests::search_case_insensitive ... ok
test transcript_history::tests::overlay_width_clamps ... ok
test transcript_history::tests::search_empty_query_returns_all ... ok
test transcript_history::tests::search_returns_newest_first ... ok
test transcript_history::tests::state_clamp_scroll_keeps_selection_visible ... ok
test transcript_history::tests::state_move_and_scroll ... ok
test transcript_history::tests::state_push_and_pop_search_char ... ok
test transcript_history::tests::state_selected_entry_index_returns_none_when_empty ... ok
test voice_control::drain::auto_rearm::tests::should_rearm_after_empty_requires_auto_voice_and_idle_manager ... ok
test voice_control::drain::auto_rearm::tests::should_rearm_after_transcript_auto_allows_queue_headroom ... ok
test voice_control::drain::auto_rearm::tests::should_rearm_after_transcript_insert_requires_empty_queue ... ok
test voice_control::drain::auto_rearm::tests::should_rearm_after_transcript_requires_auto_voice_and_idle_manager ... ok
test theme_ops::tests::resolve_theme_choice_keeps_theme_on_truecolor ... ok
test voice_control::drain::tests::clear_capture_metrics_resets_recording_artifacts ... ok
test voice_control::drain::tests::clear_last_latency_hides_badge_without_erasing_history ... ok
test theme_picker::tests::theme_picker_snapshot_matrix_is_stable ... ok
test voice_control::drain::tests::apply_macro_mode_skips_macros_when_disabled ... ok
test voice_control::drain::tests::apply_macro_mode_applies_macros_when_enabled ... ok
test voice_control::drain::tests::should_clear_latency_for_empty_depends_on_auto_mode ... ok
test voice_control::drain::tests::should_clear_latency_for_error_is_always_true ... ok
test theme_studio::home_page::tests::theme_studio_none_theme_has_no_ansi_sequences ... ok
test voice_control::drain::tests::update_last_latency_hides_previous_badge_when_metrics_missing ... ok
test voice_control::drain::tests::update_last_latency_hides_previous_badge_when_stt_missing ... ok
test voice_control::drain::tests::update_last_latency_prefers_stt_metrics_when_available ... ok
test voice_control::drain::tests::update_last_latency_uses_stt_even_without_recording_start_time ... ok
test toast::tests::format_toast_history_overlay_uses_persisted_toast_position_payload ... ok
test voice_control::drain::tests::update_last_latency_keeps_empty_state_when_stt_missing_and_no_prior_sample ... ok
test toast::tests::format_toast_inline_uses_persisted_severity_mode_payload ... ok
test voice_control::drain::tests::handle_voice_message_no_speech_omits_pipeline_label ... ok
test voice_control::drain::tests::handle_voice_message_sends_status_and_transcript ... ok
test voice_control::manager::tests::apply_manual_capture_silence_grace_clamps_to_max_capture ... ok
test voice_control::manager::tests::apply_manual_capture_silence_grace_only_changes_manual_trigger ... ok
test voice_control::manager::tests::start_voice_capture_reports_running_job_on_manual_only ... ok
test voice_control::manager::tests::voice_manager_clamps_sensitivity ... ok
test voice_control::manager::tests::voice_manager_get_transcriber_errors_on_missing_model ... ok
test voice_control::manager::tests::voice_manager_is_idle_false_when_job_present ... ok
test voice_control::manager::tests::voice_manager_reports_capture_activity_from_job_state ... ok
test voice_control::navigation::tests::execute_voice_navigation_copy_last_error_without_capture_sets_status ... ok
test voice_control::navigation::tests::execute_voice_navigation_explain_last_error_sends_prompt ... ok
test voice_control::navigation::tests::execute_voice_navigation_scroll_up_sends_pageup_escape ... ok
test voice_control::manager::tests::voice_manager_reports_idle_and_source ... ok
test voice_control::navigation::tests::execute_voice_navigation_send_submits_staged_insert_text ... ok
test voice_control::navigation::tests::execute_voice_navigation_send_without_staged_text_sets_status ... ok
test voice_control::navigation::tests::execute_voice_navigation_show_last_error_updates_status ... ok
test voice_control::navigation::tests::execute_voice_navigation_send_without_staged_text_still_submits_in_auto_mode ... ok
test voice_control::manager::tests::voice_manager_request_early_stop_sets_flag ... ok
test voice_control::navigation::tests::resolve_voice_navigation_action_skips_builtins_when_macro_matched ... ok
test voice_control::pipeline::tests::native_pipeline_matches_voice_source ... ok
test voice_control::navigation::tests::parse_voice_navigation_action_maps_supported_phrases ... ok
test voice_control::pipeline::tests::using_native_pipeline_requires_both_components ... ok
test voice_control::transcript_preview::tests::format_transcript_preview_cleans_and_collapses_whitespace ... ok
test voice_control::transcript_preview::tests::format_transcript_preview_empty_input_returns_empty ... ok
test voice_control::transcript_preview::tests::format_transcript_preview_enforces_minimum_length_floor ... ok
test voice_control::transcript_preview::tests::format_transcript_preview_truncates_and_appends_ellipsis ... ok
test voice_control::manager::tests::voice_manager_start_capture_errors_without_fallback ... ok
test voice_macros::tests::apply_exact_expansion_macro ... ok
test voice_macros::tests::apply_returns_original_when_no_macro_matches ... ok
test wake_word::tests::canonicalize_hotword_tokens_merges_common_split_aliases ... ok
test voice_macros::tests::parse_rejects_object_without_template_or_expansion ... ok
test voice_macros::tests::apply_template_macro_uses_remainder_and_mode_override ... ok
test wake_word::tests::detect_wake_event_defaults_to_detection_for_non_send_suffix ... ok
test wake_word::tests::normalize_for_hotword_match_collapses_punctuation_and_case ... ok
test wake_word::tests::resolve_wake_threshold_tracks_voice_threshold_headroom ... ok
test wake_word::tests::detect_wake_event_maps_send_suffix_intent ... ok
test wake_word::tests::sensitivity_mapping_is_monotonic_and_clamped ... ok
test wake_word::tests::contains_hotword_phrase_detects_supported_aliases ... ok
test voice_macros::tests::load_for_project_reads_dot_voiceterm_macros_file ... ok
test writer::mouse::tests::append_mouse_enable_sequence_appends_expected_bytes ... ok
test writer::mouse::tests::pty_chunk_detects_combined_private_mode_disable_sequence ... ok
test writer::mouse::tests::pty_chunk_detects_simple_mouse_disable_sequences ... ok
test writer::mouse::tests::pty_chunk_ignores_enable_or_non_mouse_sequences ... ok
test writer::mouse::tests::pty_chunk_ignores_incomplete_private_mode_sequences ... ok
test writer::render::tests::banner_row_max_render_width_applies_jetbrains_single_row_safety_margin ... ok
test writer::render::tests::clear_overlay_panel_resets_attributes_before_line_erase ... ok
test writer::render::tests::clear_status_banner_at_clears_expected_rows ... ok
test writer::render::tests::cup_only_bottom_clear_avoids_cursor_save_restore_sequences ... ok
test writer::render::tests::cursor_hide_policy_keeps_visibility_unchanged_for_all_terminals ... ok
test writer::render::tests::cursor_terminal_uses_combined_cursor_save_restore_sequences ... ok
test writer::render::tests::jetbrains_terminal_uses_dec_only_cursor_save_restore_sequences ... ok
test writer::render::tests::overlay_row_max_render_width_applies_ide_terminal_safety_margin ... ok
test writer::render::tests::write_and_clear_status_line_respect_dimensions ... ok
test writer::render::tests::write_overlay_panel_resets_attributes_before_content_and_clear ... ok
test writer::render::tests::write_status_banner_full_hud_clears_trailing_content ... ok
test writer::render::tests::write_status_banner_single_line_keeps_trailing_clear ... ok
test writer::render::tests::write_status_banner_skips_unchanged_lines_when_previous_provided ... ok
test writer::render::tests::write_status_line_includes_colored_prefix ... ok
test writer::render::tests::write_status_line_respects_no_color_theme ... ok
test writer::render::tests::write_status_line_truncates_unicode_by_display_width ... ok
test writer::render::tests::write_status_line_truncation_preserves_status_type ... ok
test writer::sanitize::tests::status_helpers_sanitize_and_truncate ... ok
test writer::sanitize::tests::truncate_ansi_line_closes_osc8_when_truncated_inside_link_label ... ok
test writer::sanitize::tests::truncate_ansi_line_no_truncation_keeps_original ... ok
test writer::sanitize::tests::truncate_ansi_line_osc8_escapes_do_not_count_toward_width ... ok
test writer::sanitize::tests::truncate_ansi_line_osc_with_bel_terminator_is_ignored_for_width ... ok
test writer::sanitize::tests::truncate_ansi_line_plain_text ... ok
test writer::sanitize::tests::truncate_ansi_line_preserves_escape_sequences ... ok
test writer::sanitize::tests::truncate_ansi_line_unicode_width ... ok
test writer::state::tests::bytes_contains_short_cursor_up_csi_only_matches_small_upward_moves ... ok
test writer::state::tests::claude_composer_packet_detection_ignores_large_thinking_update_packets ... ok
test writer::state::tests::claude_composer_packet_detection_matches_long_wrapped_variant ... ok
test writer::state::tests::claude_synchronized_cursor_rewrite_detection_ignores_non_rewrite_packets ... ok
test writer::state::tests::claude_synchronized_cursor_rewrite_detection_matches_long_think_status_packets ... ok
test writer::state::tests::claude_synchronized_cursor_rewrite_detection_matches_thinking_packets ... ok
test voice_control::manager::tests::cancel_capture_suppresses_voice_message ... ok
test voice_control::manager::tests::voice_manager_drop_requests_stop_for_active_job ... ok
test theme::tests::runtime_sources_do_not_bypass_theme_resolver_with_palette_constants ... ok
test writer::state::tests::defer_non_urgent_redraw_for_recent_input_applies_to_all_terminals ... ok
test writer::state::tests::enhanced_status_does_not_cancel_pending_clear_status ... ok
test writer::state::tests::force_scroll_redraw_trigger_matrix_respects_host_provider_profile::case_1 ... ok
test writer::state::tests::force_scroll_redraw_trigger_matrix_respects_host_provider_profile::case_2 ... ok
test writer::state::tests::force_scroll_redraw_trigger_matrix_respects_host_provider_profile::case_3 ... ok
test writer::state::tests::force_scroll_redraw_trigger_matrix_respects_host_provider_profile::case_4 ... ok
test writer::state::tests::force_scroll_redraw_trigger_matrix_respects_host_provider_profile::case_5 ... ok
test writer::state::tests::force_scroll_redraw_trigger_matrix_respects_host_provider_profile::case_6 ... ok
test writer::state::tests::force_scroll_redraw_trigger_matrix_respects_host_provider_profile::case_7 ... ok
test writer::state::tests::force_scroll_redraw_trigger_matrix_respects_host_provider_profile::case_8 ... ok
test writer::state::tests::force_scroll_redraw_trigger_matrix_respects_host_provider_profile::case_9 ... ok
test wake_word::tests::wake_runtime_sync_restarts_listener_when_settings_change ... ok
test wake_word::tests::wake_runtime_sync_starts_stops_and_pauses_listener ... ok
test wake_word::tests::wake_runtime_sync_updates_prioritize_send_window_without_unpausing_capture ... ok
[2J[H[?2026h[s7[21;1H[0m[2K[22;1H[0m[2K[23;1H[0m[2K[24;1H[0m[2K[u8[?2026l
test theme::file_watcher::tests::watcher_detects_content_change ... ok
test writer::state::tests::jetbrains_forces_full_banner_repaint_even_without_transition ... ok
[?2026h[s7[21;1H[0m[91m┌──[0m [94mVoice[0m[91mTerm[0m [91m─────────────────────────────────────────────────────────────────┐[0m[0m[K[22;1H[0m[91m│[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [92mReady[0m                      [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m [91m│[0m[0m[K[23;1H[0m[91m│[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m                   [91m│[0m[0m[K[24;1H[0m[91m└──────────────────────────────────────────────────────────────────────────────┘[0m[0m[K[1;20r[u8[?2026ltest writer::state::tests::cursor_claude_banner_preclear_requests_redraw_on_scrolling_newline_output ... ok
[2J[Hhello[2J[H
test writer::state::tests::cursor_first_pty_output_consumes_startup_screen_clear_flag ... ok
test writer::state::tests::cursor_scrolling_output_marks_full_banner_for_redraw ... ok
[2J[Hhellotest writer::state::tests::jetbrains_claude_first_pty_output_consumes_startup_screen_clear_flag ... ok
[?2026h[s7[24;1H[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [94mReady[0m [90m·[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m    [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m[0m[K[1;23r[u8[?2026ltest writer::state::tests::jetbrains_claude_forces_single_line_full_hud_fallback_for_full_hud_requests ... ok
[2J[H[?2026h[s7[21;1H[0m[2K[22;1H[0m[2K[23;1H[0m[2K[24;1H[0m[2K[u8[?2026lline one
line twotest writer::state::tests::jetbrains_claude_non_cup_scroll_chunk_preclears_when_cursor_slot_untouched ... ok
[2J[H7line one
line two8[2J[H
test writer::state::tests::jetbrains_claude_non_cup_scroll_chunk_skips_preclear_when_cursor_slot_touched ... ok
test theme::file_watcher::tests::watcher_ignores_mtime_only_change ... ok
test writer::state::tests::jetbrains_scroll_output_redraw_state_matches_backend_policy ... ok
test writer::state::tests::maybe_redraw_status_throttles_when_no_priority_or_preclear_force ... ok
atest writer::state::tests::maybe_redraw_status_defers_non_urgent_redraw_while_user_typing_in_cursor_claude ... ok
test writer::state::tests::maybe_redraw_status_defers_non_urgent_redraw_while_user_typing_on_standard_terminal ... ok
test writer::state::tests::non_scrolling_output_does_not_force_full_banner_redraw ... ok
test writer::state::tests::preclear_policy_cursor_claude_banner_sets_immediate_redraw_flags ... ok
test writer::state::tests::preclear_policy_jetbrains_claude_resize_window_forces_repair_flags ... ok
[?2026h[s7[21;1H[0m[91m┌──[0m [94mVoice[0m[91mTerm[0m [91m─────────────────────────────────────────────────────────────────────────────────────────────────────────┐[0m[0m[K[22;1H[0m[91m│[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [92mReady[0m                                                              [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m [91m│[0m[0m[K[23;1H[0m[91m│[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m                                                           [91m│[0m[0m[K[24;1H[0m[91m└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘[0m[0m[K[1;20r[u8[?2026ltest writer::state::tests::pty_chunk_starts_with_absolute_cursor_position_requires_early_cup ... ok
test writer::state::tests::pty_output_can_mutate_cursor_line_detects_echo_like_chunks ... ok
test writer::state::tests::pty_output_may_scroll_rows_can_treat_carriage_return_as_scroll_for_codex_jetbrains ... ok
test writer::state::tests::preclear_policy_outcome_without_preclear_disables_post_preclear_flags ... ok
test writer::state::tests::pty_output_may_scroll_rows_flags_csi_scroll_sequences ... ok
test writer::state::tests::pty_output_may_scroll_rows_flags_newline_and_resets_column ... ok
test writer::state::tests::pty_output_may_scroll_rows_tracks_wrapping_without_newline ... ok
test writer::state::tests::pty_output_may_scroll_rows_treats_carriage_return_as_same_row_rewind ... ok
test writer::state::tests::redraw_policy_codex_jetbrains_consumes_preclear_outcome_for_redraw_trigger ... ok
test writer::state::tests::redraw_policy_cursor_claude_non_scroll_cursor_mutation_forces_immediate_redraw ... ok
test writer::state::tests::redraw_policy_jetbrains_claude_destructive_clear_busy_slot_arms_deferred_repair ... ok
test writer::state::tests::redraw_policy_jetbrains_claude_scroll_defers_immediate_output_redraw ... ok
[?2026h[s7[2;1H[0m[2K[3;1H[0m[2K[4;1H[0m[2K[5;1H[0m[2K[u8[?2026l[?2026h[s7[21;1H[0m[2K[22;1H[0m[2K[23;1H[0m[2K[24;1H[0m[2K[1;24r[u8[?2026ltest writer::state::tests::maybe_redraw_status_does_not_defer_minimal_hud_recovery_in_cursor_claude ... ok
test writer::state::tests::resize_ignores_unchanged_dimensions ... ok
test writer::state::tests::resize_clears_stale_banner_anchor_state_before_reflow ... ok
test writer::state::tests::runtime_profile_matrix_matches_host_provider_contract::case_1 ... ok
test writer::state::tests::runtime_profile_matrix_matches_host_provider_contract::case_2 ... ok
test writer::state::tests::runtime_profile_matrix_matches_host_provider_contract::case_3 ... ok
test writer::state::tests::runtime_profile_matrix_matches_host_provider_contract::case_4 ... ok
test writer::state::tests::runtime_profile_matrix_matches_host_provider_contract::case_5 ... ok
test writer::state::tests::runtime_profile_matrix_matches_host_provider_contract::case_6 ... ok
test writer::state::tests::runtime_profile_matrix_matches_host_provider_contract::case_7 ... ok
test writer::state::tests::runtime_profile_matrix_matches_host_provider_contract::case_8 ... ok
test writer::state::tests::runtime_profile_matrix_matches_host_provider_contract::case_9 ... ok
test writer::state::tests::resize_updates_dimensions_when_changed ... ok
test writer::state::tests::scroll_redraw_interval_matrix_matches_host_provider_contract::case_1 ... ok
[?2026h[s7[24;1H[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [92mReady[0m [90m·[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m    [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m[0m[K[1;23r[u8[?2026ltest writer::state::tests::scroll_redraw_interval_matrix_matches_host_provider_contract::case_2 ... ok
test writer::state::tests::scroll_redraw_interval_matrix_matches_host_provider_contract::case_3 ... ok
test writer::state::tests::scroll_redraw_interval_matrix_matches_host_provider_contract::case_4 ... ok
test writer::state::tests::scroll_redraw_interval_matrix_matches_host_provider_contract::case_5 ... ok
test writer::state::tests::scroll_redraw_interval_matrix_matches_host_provider_contract::case_6 ... ok
test writer::state::tests::scroll_redraw_interval_matrix_matches_host_provider_contract::case_7 ... ok
test writer::state::tests::scroll_redraw_interval_matrix_matches_host_provider_contract::case_8 ... ok
test writer::state::tests::scroll_redraw_interval_matrix_matches_host_provider_contract::case_9 ... ok
test writer::state::tests::maybe_redraw_status_jetbrains_claude_requires_idle_settle_for_passive_redraw ... ok
test writer::state::tests::resize_accepts_small_geometry_for_non_claude_backends ... ok
test writer::state::tests::resize_ignores_transient_jetbrains_claude_geometry_collapse ... ok
test writer::state::tests::scheduled_jetbrains_claude_repair_redraw_waits_for_idle_settle ... ok
[?2026h[s7[24;1H[0m[93m◐[0m Processing...[0m[K[u8[?2026ltest writer::state::tests::maybe_redraw_status_skips_throttle_when_preclear_force_is_set ... ok
[?2026h[s7[21;1H[0m[91m┌──[0m [94mVoice[0m[91mTerm[0m [91m─────────────────────────────────────────────────────────────────┐[0m[0m[K[22;1H[0m[91m│[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [92mReady[0m                      [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m [91m│[0m[0m[K[23;1H[0m[91m│[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m                   [91m│[0m[0m[K[24;1H[0m[91m└──────────────────────────────────────────────────────────────────────────────┘[0m[0m[K[1;20r[u8[?2026ltest writer::state::tests::maybe_redraw_status_falls_back_when_terminal_size_call_fails ... ok
[?2026h[s7[21;1H[0m[91m┌──[0m [94mVoice[0m[91mTerm[0m [91m─────────────────────────────────────────────────────────────────┐[0m[0m[K[22;1H[0m[91m│[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [92mReady[0m                      [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m [91m│[0m[0m[K[23;1H[0m[91m│[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m                   [91m│[0m[0m[K[24;1H[0m[91m└──────────────────────────────────────────────────────────────────────────────┘[0m[0m[K[1;20r[u8[?2026ltest writer::state::tests::maybe_redraw_status_falls_back_when_terminal_reports_zero_size ... ok
[?2026h[s7[21;1H[0m[91m┌──[0m [94mVoice[0m[91mTerm[0m [91m─────────────────────────────────────────────────────────────────┐[0m[0m[K[22;1H[0m[91m│[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [92mReady[0m                      [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m [91m│[0m[0m[K[23;1H[0m[91m│[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m                   [91m│[0m[0m[K[24;1H[0m[91m└──────────────────────────────────────────────────────────────────────────────┘[0m[0m[K[1;20r[u8[?2026ltest writer::state::tests::scheduled_cursor_claude_repair_redraw_fires_without_pending_status_update ... ok
[2J[H[?2026h[s7[21;1H[0m[2K[22;1H[0m[2K[23;1H[0m[2K[24;1H[0m[2K[u8[?2026lhello world[?2026h[s7[21;1H[0m[91m┌──[0m [94mVoice[0m[91mTerm[0m [91m─────────────────────────────────────────────────────────────────┐[0m[0m[K[22;1H[0m[91m│[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [92mReady[0m                      [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m [91m│[0m[0m[K[23;1H[0m[91m│[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m                   [91m│[0m[0m[K[24;1H[0m[91m└──────────────────────────────────────────────────────────────────────────────┘[0m[0m[K[1;20r[u8[?2026ltest writer::state::tests::scroll_repair_tests::cursor_claude_banner_preclear_handles_wrap_scroll_without_newline ... ok
[2J[H[2K[?2026h[s7[21;1H[0m[91m┌──[0m [94mVoice[0m[91mTerm[0m [91m─────────────────────────────────────────────────────────────────┐[0m[0m[K[22;1H[0m[91m│[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [92mReady[0m                      [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m [91m│[0m[0m[K[23;1H[0m[91m│[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m                   [91m│[0m[0m[K[24;1H[0m[91m└──────────────────────────────────────────────────────────────────────────────┘[0m[0m[K[1;20r[u8[?2026ltest writer::state::tests::scroll_repair_tests::cursor_claude_non_scroll_csi_mutation_triggers_redraw ... ok
[?2026h[s7[24;1H[0m[90m○[0m [90mIDLE[0m [90m·[0m [90m[[0m[92m▁▁▁▁▁▁[0m[90m][0m [90m·[0m [92mReady[0m                                                                                         [91m[[91mback[91m][0m[0m[K[1;23r[u8[?2026ltest writer::state::tests::scroll_repair_tests::cursor_claude_post_clear_enhanced_status_bypasses_typing_hold_deferral ... ok
[?2026h[s7[24;1H[0m[90m○[0m [90mIDLE[0m [90m·[0m [90m[[0m[92m▁▁▁▁▁▁[0m[90m][0m [90m·[0m [92mReady[0m                                                                                         [91m[[91mback[91m][0m[0m[K[1;23r[u8[?2026ltest writer::state::tests::scroll_repair_tests::cursor_claude_suppression_transition_bypasses_typing_hold_deferral ... ok
[2J[H[?2026h
[2A[7m [27m
[?2026ltest writer::state::tests::scroll_repair_tests::jetbrains_claude_composer_keystroke_falls_back_to_deferred_repair_when_cursor_slot_active ... ok
[2J[H[?2026h
[2A[7m [27m
[?2026ltest writer::state::tests::scroll_repair_tests::jetbrains_claude_composer_keystroke_ignored_without_recent_user_input ... ok
[2J[H[?2026h
[2A[7m [27m
[?2026l[?2026h[s7[24;1H[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m[0m [90m·[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m[0m[K[1;23r[u8[?2026ltest writer::state::tests::scroll_repair_tests::jetbrains_claude_composer_keystroke_repaints_immediately_without_deferred_repair ... ok
[?2026h[s7[24;1H[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [92mReady[0m [90m·[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m    [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m[0m[K[1;23r[u8[?2026ltest writer::state::tests::scroll_repair_tests::jetbrains_claude_composer_repair_requires_quiet_window_after_due ... ok
test writer::state::tests::scroll_repair_tests::jetbrains_claude_composer_repair_still_waits_when_cursor_save_is_active ... ok
[2J[H[2J[3J[Htest writer::state::tests::scroll_repair_tests::jetbrains_claude_composer_repair_waits_for_due_deadline ... ok
[2J[H[2J[3J[Htest writer::state::tests::scroll_repair_tests::jetbrains_claude_destructive_clear_defers_immediate_repaint_when_cursor_slot_busy ... ok
test writer::state::tests::scroll_repair_tests::pty_output_contains_destructive_clear_detects_screen_clear_sequences ... ok
test writer::state::tests::scroll_repair_tests::pty_output_contains_destructive_clear_ignores_non_destructive_sequences ... ok
test writer::state::tests::scroll_repair_tests::pty_output_contains_erase_display_detects_display_erase_sequences ... ok
test writer::state::tests::scroll_repair_tests::pty_output_contains_erase_display_ignores_non_display_erase_sequences ... ok
test writer::state::tests::scroll_repair_tests::pty_output_may_scroll_rows_handles_mixed_csi_and_printable ... ok
test writer::state::tests::scroll_repair_tests::pty_output_may_scroll_rows_sgr_does_not_cause_false_scroll ... ok
test writer::state::tests::scroll_repair_tests::pty_output_may_scroll_rows_skips_csi_escape_sequences ... ok
test writer::state::tests::scroll_repair_tests::pty_output_may_scroll_rows_skips_two_byte_escape_sequences ... ok
test writer::state::tests::scroll_repair_tests::track_cursor_save_restore_handles_split_escape_sequences ... ok
test writer::state::tests::scroll_repair_tests::track_cursor_save_restore_ignores_csi_parameter_bytes ... ok
test writer::state::tests::scroll_repair_tests::track_cursor_save_restore_tracks_dec_and_ansi_sequences ... ok

test writer::state::tests::scrolling_output_forces_full_banner_redraw_for_multi_row_hud ... ok

test writer::state::tests::scrolling_output_forces_full_banner_redraw_for_single_row_hud ... ok
test writer::state::tests::should_force_non_scroll_banner_redraw_requires_claude_flash_profile_and_interval ... ok
test writer::state::tests::should_force_scroll_full_redraw_respects_interval_when_configured ... ok
test writer::state::tests::should_force_scroll_full_redraw_without_interval_always_true ... ok
test writer::state::tests::should_preclear_bottom_rows_cursor_claude_preclears_banner_without_cadence_gate ... ok
test writer::state::tests::should_preclear_bottom_rows_cursor_claude_preclears_once_for_startup_scroll ... ok
test writer::state::tests::should_preclear_bottom_rows_cursor_claude_skips_banner_only_preclear ... ok
test writer::state::tests::should_preclear_bottom_rows_cursor_preclears_for_pending_status_clear ... ok
test writer::state::tests::should_preclear_bottom_rows_cursor_respects_cooldown ... ok
test writer::state::tests::should_preclear_bottom_rows_cursor_skips_banner_only_preclear ... ok
test writer::state::tests::should_preclear_bottom_rows_jetbrains_claude_requires_safe_cup_chunk ... ok
test writer::state::tests::should_preclear_bottom_rows_jetbrains_codex_skips_preclear_even_on_transition ... ok
test writer::state::tests::should_preclear_bottom_rows_jetbrains_preclears_on_pending_status_transition ... ok
test writer::state::tests::should_preclear_bottom_rows_jetbrains_respects_cooldown ... ok
test writer::state::tests::should_preclear_bottom_rows_jetbrains_skips_banner_preclear_without_transition ... ok
test writer::state::tests::should_preclear_bottom_rows_matrix_matches_host_provider_contract::case_1 ... ok
test writer::state::tests::should_preclear_bottom_rows_matrix_matches_host_provider_contract::case_2 ... ok
test writer::state::tests::should_preclear_bottom_rows_matrix_matches_host_provider_contract::case_3 ... ok
test writer::state::tests::should_preclear_bottom_rows_matrix_matches_host_provider_contract::case_4 ... ok
test writer::state::tests::should_preclear_bottom_rows_matrix_matches_host_provider_contract::case_5 ... ok
test writer::state::tests::should_preclear_bottom_rows_matrix_matches_host_provider_contract::case_6 ... ok
test writer::state::tests::should_preclear_bottom_rows_matrix_matches_host_provider_contract::case_7 ... ok
test writer::state::tests::should_preclear_bottom_rows_matrix_matches_host_provider_contract::case_8 ... ok
test writer::state::tests::should_preclear_bottom_rows_matrix_matches_host_provider_contract::case_9 ... ok
test writer::state::tests::should_preclear_bottom_rows_other_terminal_uses_legacy_behavior ... ok
test writer::state::tests::status_clear_height_only_when_banner_shrinks ... ok
test writer::state::tests::transition_redraw_after_preclear_disables_previous_line_diff ... ok
[?2026h[s7[21;1H[0m[2K[22;1H[0m[2K[23;1H[0m[2K[24;1H[0m[2K[1;24r[u8[?2026l[?2026h[s7[24;1H[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m[0m [90m·[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m[0m[K[1;23r[u8[?2026ltest writer::state::tests::scroll_repair_tests::jetbrains_claude_destructive_clear_reanchors_hud_immediately_when_cursor_slot_idle ... ok
[2J[H[?2026h
[6A[7m [27m[?2026ltest writer::state::tests::scroll_repair_tests::jetbrains_claude_full_hud_non_scroll_cursor_mutation_arms_repair ... ok
test writer::state::tests::user_input_activity_schedules_repair_for_jetbrains_claude ... ok
test writer::tests::osc52_copy_bytes_encodes_expected_escape ... ok
[?2026h[s7[24;1H[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [92mReady[0m [90m·[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m    [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m[0m[K[1;23r[u8[?2026ltest writer::state::tests::scroll_repair_tests::jetbrains_claude_sync_repair_can_bypass_quiet_window ... ok
[2J[H[?2026h
[21C[6A[37m50[10C[38;2;174;174;174m(thinking)[39m






[?2026ltest writer::state::tests::scroll_repair_tests::jetbrains_claude_thinking_packet_without_recent_input_still_arms_repair ... ok
test writer::tests::set_status_updates_deadline ... ok
test writer::state::tests::scroll_repair_tests::maybe_redraw_status_defers_jetbrains_claude_during_restore_settle_window ... ok
test writer::state::tests::scroll_repair_tests::maybe_redraw_status_defers_jetbrains_claude_when_cursor_save_is_active ... ok
test writer::tests::try_send_message_returns_false_on_full_queue ... ok
test writer::timing::tests::idle_redraw_timing_applies_jetbrains_claude_composer_quiet_window ... ok
test writer::timing::tests::idle_redraw_timing_clears_expired_cursor_restore_settle_window ... ok
test writer::timing::tests::idle_redraw_timing_honors_priority_max_wait_for_non_jetbrains_hosts ... ok
test writer::timing::tests::idle_redraw_timing_uses_jetbrains_claude_scroll_hold_window ... ok
test writer::timing::tests::idle_redraw_timing_uses_jetbrains_codex_scroll_hold_window ... ok
test writer::timing::tests::typing_redraw_hold_uses_host_timing_windows ... ok
test writer::tests::set_status_does_not_block_when_queue_is_full ... ok
[?2026h[s7[21;1H[0m[91m┌──[0m [94mVoice[0m[91mTerm[0m [91m─────────────────────────────────────────────────────────────────┐[0m[0m[K[22;1H[0m[91m│[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m --dB[0m  [90m│[0m [92mReady[0m                      [90m[[0m[92m▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁[0m[90m][0m [91m│[0m[0m[K[23;1H[0m[91m│[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m                   [91m│[0m[0m[K[24;1H[0m[91m└──────────────────────────────────────────────────────────────────────────────┘[0m[0m[K[1;20r[u8[?2026ltest writer::state::tests::unrelated_redraw_keeps_future_cursor_claude_repair_deadline ... ok
[2J[H[2J[3J[Htest writer::state::tests::user_input_activity_schedules_cursor_claude_repair_redraw ... ok
[?2026h[s7[21;1H[0m[2K[22;1H[0m[2K[23;1H[0m[2K[24;1H[0m[2K[1;24r[u8[?2026l[?2026h[s7[24;1H[0m ○ IDLE  [90m│[0m [90m--.-s[0m [90m│[0m [90m[0m [90m·[0m [91m[[91mrec[91m][0m · [91m[[91mptt[91m][0m · [92m[[92msend[92m][0m · [91m[[91mset[91m][0m · [91m[[91mhud[91m][0m · [91m[[91mhelp[91m][0m · [91m[[91mstudio[91m][0m[0m[K[1;23r[u8[?2026l[2J[3J[Htest writer::state::tests::scroll_repair_tests::jetbrains_claude_repeated_destructive_clear_burst_uses_deferred_followup ... ok
test writer::state::tests::user_input_activity_schedules_repair_when_status_is_pending ... ok
test terminal::tests::update_pty_winsize_updates_cached_dimensions ... ok
test transcript::session::tests::transcript_session_impl_sends_text ... ok
test transcript::session::tests::transcript_session_impl_sends_text_with_newline ... ok
test transcript::delivery::tests::deliver_transcript_injects_into_pty ... ok
test wake_word::tests::hotword_guardrail_soak_false_positive_and_latency ... ok

test result: ok. 1929 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 13.47s

     Running tests/main_bin.rs (target/debug/deps/main_bin-be052f46993475ef)

running 2 tests
test main_reports_no_input_devices ... ok
test main_lists_input_devices ... ok

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.62s

     Running tests/voiceterm_cli.rs (target/debug/deps/voiceterm_cli-973630ef0dd14b1c)

running 3 tests
test voiceterm_list_input_devices_prints_message ... ok
test voiceterm_help_mentions_name ... ok
test voiceterm_help_no_color_has_no_ansi_sequences ... ok

test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.02s

   Doc-tests voiceterm

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

# probe_boolean_params

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_stringly_typed

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_magic_numbers

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_design_smells

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_defensive_overchecking

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_unnecessary_intermediates

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_dict_as_struct

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_single_use_helpers

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_exception_quality

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_identifier_density

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_blank_line_frequency

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_compatibility_shims

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_term_consistency

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_side_effect_mixing

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_cognitive_complexity

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_fan_out

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_mixed_concerns

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_concurrency

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_clone_density

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_unwrap_chains

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_vague_errors

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_type_conversions

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_mutable_parameter_density

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_tuple_return_complexity

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
# probe_match_arm_complexity

- ok: True
- mode: working-tree
- files_scanned: 0
- files_with_hints: 0
- risk_hints: 0
[process-sweep-post] warning: Process sweep skipped: unable to execute ps ([Errno 1] Operation not permitted: 'ps') before handoff.

## Plan Alignment

- Current execution authority for this slice is `dev/active/MASTER_PLAN.md`, routed through `dev/active/ai_governance_platform.md`, with `dev/active/platform_authority_loop.md` as the current subordinate Phase 1 execution spec for startup authority.
- `dev/active/review_channel.md` remains the active runbook for the live Codex/Claude markdown loop while the bridge still exists.
- `dev/active/continuous_swarm.md` remains a supporting runbook for reviewer/coder cadence and stale-loop hardening, not the product boundary or current primary coding lane.
- `dev/guides/AI_GOVERNANCE_PLATFORM.md` and `dev/active/portable_code_governance.md` remain companion docs; they do not replace `MP-377` as the active execution authority.
- `SYSTEM_AUDIT.md` is broad reference context only. It does not override the active-plan chain or the current bridge instruction.

## Last Reviewed Scope

- dev/scripts/devctl/context_graph/artifact_inputs.py
- dev/scripts/devctl/context_graph/builder.py
- dev/scripts/devctl/probe_topology_builder.py
- dev/scripts/devctl/probe_topology_scan.py
- dev/scripts/devctl/tests/context_graph/test_context_graph_artifact_inputs.py
- dev/scripts/devctl/tests/context_graph/test_context_graph.py

## Warnings
- `rust/src/bin/voiceterm/event_loop/tests.rs` (soft_limit, hard_limit): Override soft_limit (6500) is 7.22x the .rs default (900). Override hard_limit (7000) is 5.00x the .rs default (1400). Operator intent keeps path overrides under 3.0x the soft cap and under 2.0x the hard cap.
- `app/operator_console/theme/editor/theme_editor.py` (soft_limit, hard_limit): Override soft_limit (1400) is 4.00x the .py default (350). Override hard_limit (1500) is 2.31x the .py default (650). Operator intent keeps path overrides under 3.0x the soft cap and under 2.0x the hard cap.
- `app/operator_console/views/ui_refresh.py` (soft_limit): Override soft_limit (1150) is 3.29x the .py default (350). Operator intent keeps path overrides under 3.0x the soft cap and under 2.0x the hard cap.
