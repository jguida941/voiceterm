# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `b1d68bf4ac6f` — Refresh external review snapshot for a811a874
- Tree hash: `83a6a8f54125`
- Generation stamp: `snap-f7963309e891`
- Generated at (UTC): 2026-04-26T02:07:15Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 41 files, +2764/-1401
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
- HEAD SHA: `b1d68bf4ac6ffde03c05f57ca25130f5dc021657`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-25T22:06:12-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (push_preflight_running)
- current_push_authorization: `push-auth-20260426T020553545571Z` (valid=True)
- authorized_head_commit: `b1d68bf4ac6ffde03c05f57ca25130f5dc021657`
- approved_target_identity: `tree-receipt-20260426T020553545571Z:3c41993101d95a23f6099a4be12c1ce0b7cea94e`
- publication_backlog: urgent
- publication_guidance: 26 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `active_dual_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `await_review` — review_pending_before_push

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `b1d68bf4ac6f`

- commits: 24
- files changed: 41
- insertions: +2764
- deletions: -1401
- bundle classes touched: docs, tooling
- authority surfaces touched: 5 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `b1d68bf4` | Refresh external review snapshot for a811a874 | 2 | +60/-60 | docs |  |
| 2 | `a811a874` | Refresh SYSTEM_MAP.md generated counts per rev_pkt_1909 (Sl… | 3 | +75/-85 | docs |  |
| 3 | `82dc701a` | Refresh external review snapshot for 0045e2fb | 1 | +4/-4 | docs |  |
| 4 | `0045e2fb` | Refresh external review snapshot for a04cd92e | 2 | +47/-44 | docs |  |
| 5 | `a04cd92e` | Refresh external review snapshot for 3c78537b | 2 | +53/-50 | docs |  |
| 6 | `3c78537b` | Refresh external review snapshot for 7aeefff3 | 2 | +84/-92 | docs |  |
| 7 | `7aeefff3` | Slice 0 review-channel stop-loop fix per Plan 4.1 (rev_pkt_… | 8 | +130/-71 | tooling |  |
| 8 | `7fa9122d` | Refresh external review snapshot for 7bdf0df3 | 2 | +85/-108 | docs |  |
| 9 | `7bdf0df3` | Slice 0 sub-fix: enforce headless terminal discipline in re… | 22 | +591/-207 | tooling |  |
| 10 | `c0a3b117` | Refresh external review snapshot for d2f0b725 | 1 | +3/-3 | docs |  |
| 11 | `d2f0b725` | Refresh external review snapshot for 1a0e8673 | 2 | +50/-47 | docs |  |
| 12 | `1a0e8673` | Refresh external review snapshot for 580855f7 | 2 | +74/-80 | docs |  |
| 13 | `580855f7` | Slice 0 + Slice A foundation per Plan 4.1 | 20 | +963/-100 | tooling |  |
| 14 | `e05ba55a` | Refresh external review snapshot for 44459afd | 2 | +51/-48 | docs |  |
| 15 | `44459afd` | Refresh external review snapshot for ab3efdb5 | 2 | +57/-65 | docs |  |
| 16 | `ab3efdb5` | Allow idle reviewer checkpoint revisions | 4 | +157/-57 | tooling |  |
| 17 | `9081e70f` | Refresh external review snapshot for 3ffc6309 | 1 | +3/-3 | docs |  |
| 18 | `3ffc6309` | Refresh external review snapshot for 39154ae4 | 2 | +49/-49 | docs |  |
| 19 | `39154ae4` | Refresh external review snapshot for db4ed1cf | 2 | +66/-72 | docs |  |
| 20 | `db4ed1cf` | Refresh external review snapshot for d0d35dc1 | 1 | +4/-4 | docs |  |
| 21 | `d0d35dc1` | Refresh external review snapshot for e3f98adb | 2 | +46/-43 | docs |  |
| 22 | `e3f98adb` | Refresh external review snapshot for 1366e4ed | 2 | +55/-55 | docs |  |
| 23 | `1366e4ed` | Refresh external review snapshot for 9962a164 | 1 | +4/-4 | docs |  |
| 24 | `9962a164` | Refresh external review snapshot for 3f173cdc | 1 | +53/-50 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +5/-1 |
| `bridge.md` | docs | +103/-103 |
| `dev/active/MASTER_PLAN.md` | tooling | +17/-1 |
| `dev/active/ai_governance_platform.md` | tooling | +33/-1 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +5/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1064/-1096 |
| `dev/guides/DEVELOPMENT.md` | docs | +12/-2 |
| `dev/guides/SYSTEM_MAP.md` | docs | +3/-3 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +49/-1 |
| `dev/scripts/README.md` | tooling | +13/-1 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/reporting/dogfood_governance.py` | tooling | +21/-28 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +12/-5 |
| `dev/scripts/devctl/commands/review_channel/bridge_handler.py` | tooling | +24/-0 |
| `dev/scripts/devctl/commands/review_channel/launcher_discipline.py` | tooling | +23/-8 |
| `dev/scripts/devctl/commands/review_channel_command/helpers.py` | tooling | +8/-2 |
| `dev/scripts/devctl/commands/vcs/commit.py` | tooling | +17/-0 |
| `dev/scripts/devctl/commands/vcs/commit_visibility.py` | tooling | +64/-17 |
| `dev/scripts/devctl/commands/vcs/push_diagnostics.py` | tooling | +141/-0 |
| `dev/scripts/devctl/commands/vcs/push_report.py` | tooling | +22/-0 |
| `dev/scripts/devctl/review_channel/attention_helpers.py` | tooling | +2/-0 |
| `dev/scripts/devctl/review_channel/bridge_projection_instruction.py` | tooling | +38/-0 |
| `dev/scripts/devctl/review_channel/bridge_projection_metadata.py` | tooling | +9/-22 |
| `dev/scripts/devctl/review_channel/bridge_projection_state.py` | tooling | +3/-11 |
| `dev/scripts/devctl/review_channel/bridge_validation.py` | tooling | +2/-4 |
| `dev/scripts/devctl/review_channel/current_session_packet_normalize.py` | tooling | +143/-0 |
| `dev/scripts/devctl/review_channel/current_session_projection.py` | tooling | +13/-5 |
| `dev/scripts/devctl/review_channel/handoff_constants.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/status_snapshot_authority.py` | tooling | +38/-83 |
| `dev/scripts/devctl/review_channel/write_preconditions.py` | tooling | +4/-3 |
| `dev/scripts/devctl/runtime/platform_finding_ingest.py` | tooling | +264/-0 |
| `dev/scripts/devctl/tests/review_channel/test_bridge_projection_mode_defaults.py` | tooling | +17/-0 |
| `dev/scripts/devctl/tests/review_channel/test_current_session_projection.py` | tooling | +55/-3 |
| `dev/scripts/devctl/tests/review_channel/test_launch_script.py` | tooling | +18/-0 |
| `dev/scripts/devctl/tests/review_channel/test_review_channel.py` | tooling | +43/-0 |
| `dev/scripts/devctl/tests/review_channel/test_reviewer_checkpoint_inputs.py` | tooling | +90/-0 |
| `dev/scripts/devctl/tests/review_channel/test_status_snapshot_authority.py` | tooling | +93/-0 |
| `dev/scripts/devctl/tests/runtime/test_platform_finding_ingest.py` | tooling | +117/-0 |
| `dev/scripts/devctl/tests/test_cli_audit_events.py` | tooling | +11/-1 |
| `dev/scripts/devctl/tests/vcs/test_commit_visibility.py` | tooling | +58/-0 |
| _1 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_instruction.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`7fa9122d`** — Refresh external review snapshot for 7bdf0df3
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`7bdf0df3`** — Slice 0 sub-fix: enforce headless terminal discipline in remote-control recover
  - Per rev_pkt_1900: when typed liveness proves an attached remote-control
  - provider, review-channel launch/recover must fail-closed before performing
  - local Terminal.app profile lookup or provider prompts. Status/doctor now
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`c0a3b117`** — Refresh external review snapshot for d2f0b725
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`d2f0b725`** — Refresh external review snapshot for 1a0e8673
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`1a0e8673`** — Refresh external review snapshot for 580855f7
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`580855f7`** — Slice 0 + Slice A foundation per Plan 4.1
  - Slice 0 — Runtime diagnostics (no model rebuild per Plan 4.1 required edit):
  - - Diagnostic clarity in commit/push render path: clearer states for git-failed
  -   vs git-landed-but-receipt-pending vs publication-awaiting-review
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`e05ba55a`** — Refresh external review snapshot for 44459afd
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`44459afd`** — Refresh external review snapshot for ab3efdb5
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`ab3efdb5`** — Allow idle reviewer checkpoint revisions
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`9081e70f`** — Refresh external review snapshot for 3ffc6309
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`3ffc6309`** — Refresh external review snapshot for 39154ae4
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`39154ae4`** — Refresh external review snapshot for db4ed1cf
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`db4ed1cf`** — Refresh external review snapshot for d0d35dc1
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`d0d35dc1`** — Refresh external review snapshot for e3f98adb
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`e3f98adb`** — Refresh external review snapshot for 1366e4ed
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`1366e4ed`** — Refresh external review snapshot for 9962a164
  - evolution: Fact: live dogfood showed expired-pending review packets accumulating even when Codex had addressed the substance in code or follow-up packets. The queue already hid expired pending rows from actionable inbox counts, bu…
- **`9962a164`** — Refresh external review snapshot for 3f173cdc
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
- await_review: review_pending_before_push

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/active/MASTER_PLAN.md`): plan_authority_gap: 
- **governance_open** (`dev/scripts/devctl/review_channel/handoff.py`): bridge_metadata_parsed_as_authority: 
- **governance_open** (`dev/scripts/devctl/commands/governance/startup_context.py`): dogfood.command.startup-context: 
- **governance_open** (`AGENTS.md`): agents_md_dual_purpose_conflict: 
- **governance_open** (`dev/scripts/devctl/commands/vcs/push.py`): dogfood.code_shape_push_regression: Push preflight bridge sync expanded push.py beyond the hard limit.
- **governance_open** (`dev/scripts/devctl/commands/review_channel/event_handler.py`): dogfood.review_channel_post_timeout: Timed out after 20s while posting review-channel --action post --kind action_request for the staged dogfood/governance handoff.

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-f7963309e891` binds this file to HEAD `b1d68bf4ac6f`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
