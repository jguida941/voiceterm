# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `3737089c025f` — Refresh external review snapshot for 3b6b0aa2
- Tree hash: `aae8d35bf477`
- Generation stamp: `snap-883ed3888c21`
- Generated at (UTC): 2026-04-26T09:22:34Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 19 files, +1444/-1212
- Governance findings: 116 open / 88 fixed / 218 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm, a Rust voice-first terminal overlay for AI
CLIs). The product thesis is that executable local control — guards,
probes, typed actions, deterministic policy resolution — is what makes
AI-assisted engineering reliable, not prompt instructions alone.

**Mission**: Ship a reusable governance stack that any repo can adopt by
installing the platform and selecting a repo pack, without forking
VoiceTerm-specific code.

**Proof obligation**: Every claim about quality, safety, or process
compliance must be backed by a repo-owned executable artifact (guard
script, probe, typed action, CI workflow) that produces the same result
regardless of which AI model or operator runs it. Prompt-only governance
is not accepted as proof.

**Platform boundaries**: VoiceTerm is one client of the platform; portable
governance layers must not hardcode repo names, bridge paths, plan doc
locations, or product-specific defaults. Repo-local assumptions belong in
the repo pack, not in the platform core. MCP servers, operator consoles,
mobile surfaces, and overlay/TUI adapters are clients, not authority.

**Current priority**: Harden the governance stack for multi-repo adoption —
remove VoiceTerm-local assumptions from portable layers, stabilize the
typed contract surface (ProjectGovernance, StartupContext, ReviewState,
TypedAction → ActionResult → RunRecord), and close the remaining probe
and guard gaps so the platform proves its own thesis before external
adopters arrive.
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `feature/governance-quality-sweep`
- HEAD SHA: `3737089c025f351c9bc58f34889551104296fc49`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-26T05:16:11-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (push_preflight_running)
- publication_backlog: urgent
- publication_guidance: 44 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `3737089c025f`

- commits: 25
- files changed: 19
- insertions: +1444
- deletions: -1212
- bundle classes touched: tooling, docs
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `3737089c` | Refresh external review snapshot for 3b6b0aa2 | 1 | +46/-74 | tooling |  |
| 2 | `3b6b0aa2` | Refresh external review snapshot for b169224e | 1 | +42/-39 | tooling |  |
| 3 | `b169224e` | Refresh external review snapshot for 2fed15ef | 2 | +57/-58 | docs |  |
| 4 | `2fed15ef` | Refresh external review snapshot for ca9e2e23 | 1 | +2/-2 | docs |  |
| 5 | `ca9e2e23` | Refresh external review snapshot for 29139550 | 2 | +57/-64 | docs |  |
| 6 | `29139550` | Refresh external review snapshot for 6c510184 | 1 | +6/-6 | docs |  |
| 7 | `6c510184` | Refresh external review snapshot for 5c1aa56b | 2 | +49/-49 | docs |  |
| 8 | `5c1aa56b` | Refresh external review snapshot for a135d84a | 2 | +65/-61 | docs |  |
| 9 | `a135d84a` | Slice 0 reviewer-checkpoint projection convergence fix per… | 5 | +154/-64 | tooling |  |
| 10 | `92e433c1` | Refresh external review snapshot for 5b461819 | 2 | +48/-48 | docs |  |
| 11 | `5b461819` | Refresh external review snapshot for 434468cf | 1 | +5/-5 | docs |  |
| 12 | `434468cf` | Refresh external review snapshot for 900fd702 | 2 | +53/-50 | docs |  |
| 13 | `900fd702` | Refresh external review snapshot for 7bca9f66 | 2 | +65/-65 | docs |  |
| 14 | `7bca9f66` | Slice 0 runtime agreement + watch-follow discipline per Pla… | 11 | +196/-66 | tooling |  |
| 15 | `ddd4dbee` | Refresh external review snapshot for c5321b27 | 1 | +4/-4 | docs |  |
| 16 | `c5321b27` | Refresh external review snapshot for e918a6c1 | 2 | +52/-52 | docs |  |
| 17 | `e918a6c1` | Refresh external review snapshot for 92bb69a3 | 1 | +5/-5 | docs |  |
| 18 | `92bb69a3` | Refresh external review snapshot for b1d68bf4 | 2 | +85/-94 | docs |  |
| 19 | `b1d68bf4` | Refresh external review snapshot for a811a874 | 2 | +60/-60 | docs |  |
| 20 | `a811a874` | Refresh SYSTEM_MAP.md generated counts per rev_pkt_1909 (Sl… | 3 | +75/-85 | docs |  |
| 21 | `82dc701a` | Refresh external review snapshot for 0045e2fb | 1 | +4/-4 | docs |  |
| 22 | `0045e2fb` | Refresh external review snapshot for a04cd92e | 2 | +47/-44 | docs |  |
| 23 | `a04cd92e` | Refresh external review snapshot for 3c78537b | 2 | +53/-50 | docs |  |
| 24 | `3c78537b` | Refresh external review snapshot for 7aeefff3 | 2 | +84/-92 | docs |  |
| 25 | `7aeefff3` | Slice 0 review-channel stop-loop fix per Plan 4.1 (rev_pkt_… | 8 | +130/-71 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +123/-123 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1029/-1070 |
| `dev/guides/SYSTEM_MAP.md` | docs | +2/-2 |
| `dev/scripts/devctl/commands/review_channel/watch_follow.py` | tooling | +6/-0 |
| `dev/scripts/devctl/commands/review_channel/watch_follow_frames.py` | tooling | +10/-3 |
| `dev/scripts/devctl/commands/review_channel/watch_follow_runtime.py` | tooling | +15/-0 |
| `dev/scripts/devctl/commands/review_channel/watch_follow_state.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/attention_helpers.py` | tooling | +2/-0 |
| `dev/scripts/devctl/review_channel/bridge_validation.py` | tooling | +2/-4 |
| `dev/scripts/devctl/review_channel/current_session_projection.py` | tooling | +13/-5 |
| `dev/scripts/devctl/review_channel/handoff_constants.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/reviewer_runtime_contract.py` | tooling | +10/-0 |
| `dev/scripts/devctl/review_channel/watch_lifecycle.py` | tooling | +9/-2 |
| `dev/scripts/devctl/runtime/advisory_next_action_role_filter.py` | tooling | +5/-0 |
| `dev/scripts/devctl/tests/review_channel/test_current_session_projection.py` | tooling | +4/-3 |
| `dev/scripts/devctl/tests/review_channel/test_review_channel.py` | tooling | +111/-0 |
| `dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py` | tooling | +80/-0 |
| `dev/scripts/devctl/tests/review_channel/test_watch_lifecycle.py` | tooling | +4/-0 |
| `dev/scripts/devctl/tests/runtime/test_action_routing.py` | tooling | +17/-0 |

## 4. Quality signals

### Governance review
- total findings: 218
- open: 116
- fixed: 88
- false positives: 0

Recent findings:
- `plan_authority_gap` — `dev/active/MASTER_PLAN.md` (n/a, verdict=`confirmed_issue`)
- `bridge_metadata_parsed_as_authority` — `dev/scripts/devctl/review_channel/handoff.py` (n/a, verdict=`confirmed_issue`)
- `authority_snapshot_3_fields_missing` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`fixed`)
- `dogfood.command.startup-context` — `dev/scripts/devctl/commands/governance/startup_context.py` (n/a, verdict=`confirmed_issue`)
- `agents_md_dual_purpose_conflict` — `AGENTS.md` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.dogfood` — `dev/scripts/devctl/commands/reporting/dogfood.py` (n/a, verdict=`fixed`)
- `dogfood.code_shape_push_regression` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.review_channel_post_timeout` — `dev/scripts/devctl/commands/review_channel/event_handler.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.review_channel_post_timeout` — `dev/scripts/devctl/review_channel/event_projection_queue.py` (n/a, verdict=`fixed`)
- `portability_python_310` — `dev/scripts/devctl/runtime/worktree_orphan_inventory_support.py` (p0, verdict=`confirmed_issue`)

### Probe report
- run_state: `missing`
- warnings: 0
- errors: 0
- files scanned: 0
- total hints: 0

## 5. Architecture surface

### Contract ownership map

| Contract | Owner layer | Runtime model | Tokens |
|---|---|---|---|
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id, state |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id, bridge |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit a135d84a changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py`) — Commit a135d84a changed dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`3737089c`** — Refresh external review snapshot for 3b6b0aa2
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`3b6b0aa2`** — Refresh external review snapshot for b169224e
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`b169224e`** — Refresh external review snapshot for 2fed15ef
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`2fed15ef`** — Refresh external review snapshot for ca9e2e23
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`ca9e2e23`** — Refresh external review snapshot for 29139550
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`29139550`** — Refresh external review snapshot for 6c510184
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`6c510184`** — Refresh external review snapshot for 5c1aa56b
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`5c1aa56b`** — Refresh external review snapshot for a135d84a
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`a135d84a`** — Slice 0 reviewer-checkpoint projection convergence fix per Plan 4.1 (rev_pkt_1918)
  - Per Codex's typed handoff (rev_pkt_1918 stage_commit_pipeline) addressing
  - the post-rev_pkt_1914 convergence bug: reviewer-checkpoint could write
  - accepted/no-findings bridge state but the projection refresh still
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`92e433c1`** — Refresh external review snapshot for 5b461819
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`5b461819`** — Refresh external review snapshot for 434468cf
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`434468cf`** — Refresh external review snapshot for 900fd702
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`900fd702`** — Refresh external review snapshot for 7bca9f66
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`7bca9f66`** — Slice 0 runtime agreement + watch-follow discipline per Plan 4.1 (rev_pkt_1914)
  - Per Codex's typed handoff (rev_pkt_1914 stage_commit_pipeline) addressing
  - both rev_pkt_1912 (proof-tick parity mismatch on next_command) and
  - rev_pkt_1913 (watch/follow discipline + watcher metadata).
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`ddd4dbee`** — Refresh external review snapshot for c5321b27
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`c5321b27`** — Refresh external review snapshot for e918a6c1
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`e918a6c1`** — Refresh external review snapshot for 92bb69a3
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`92bb69a3`** — Refresh external review snapshot for b1d68bf4
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`b1d68bf4`** — Refresh external review snapshot for a811a874
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`a811a874`** — Refresh SYSTEM_MAP.md generated counts per rev_pkt_1909 (Slice 0 surface regen)
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`82dc701a`** — Refresh external review snapshot for 0045e2fb
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`0045e2fb`** — Refresh external review snapshot for a04cd92e
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`a04cd92e`** — Refresh external review snapshot for 3c78537b
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`3c78537b`** — Refresh external review snapshot for 7aeefff3
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`7aeefff3`** — Slice 0 review-channel stop-loop fix per Plan 4.1 (rev_pkt_1905)
  - Codex's typed handoff via rev_pkt_1905 (action_request/stage_commit_pipeline)
  - asks Claude to stage and commit the coherent Slice 0 dirty set.
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/autonomous_governance_loop_v2.md` MP-377): headless
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 116

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/active/MASTER_PLAN.md`): plan_authority_gap: 
- **governance_open** (`dev/scripts/devctl/review_channel/handoff.py`): bridge_metadata_parsed_as_authority: 
- **governance_open** (`dev/scripts/devctl/commands/governance/startup_context.py`): dogfood.command.startup-context: 
- **governance_open** (`AGENTS.md`): agents_md_dual_purpose_conflict: 
- **governance_open** (`dev/scripts/devctl/commands/vcs/push.py`): dogfood.code_shape_push_regression: Push preflight bridge sync expanded push.py beyond the hard limit.
- **governance_open** (`dev/scripts/devctl/commands/review_channel/event_handler.py`): dogfood.review_channel_post_timeout: Timed out after 20s while posting review-channel --action post --kind action_request for the staged dogfood/governance handoff.

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-883ed3888c21` binds this file to HEAD `3737089c025f`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
