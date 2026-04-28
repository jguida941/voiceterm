# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `8f41297527c2` — Refresh external review snapshot for 10ab0bce
- Tree hash: `19f0f2319f45`
- Generation stamp: `snap-5847a7dcdddf`
- Generated at (UTC): 2026-04-28T14:33:20Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 25 files, +3042/-1709
- Governance findings: 126 open / 88 fixed / 228 total
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
- HEAD SHA: `8f41297527c23849533a71489a7696168af573da`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-28T10:24:41-04:00

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
- current_push_authorization: `push-auth-20260428T141328904006Z` (valid=True)
- authorized_head_commit: `22fcd435bce993e6006a6d7cfab61f00c9bd6cb2`
- approved_target_identity: `tree-receipt-20260428T141328904006Z:e5282e5e9782ad056da0b9b4c10dfb57629a908c`
- publication_backlog: urgent
- publication_guidance: 62 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `active_dual_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`
- implementation_blocked: yes — runtime_missing

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `repair_reviewer_loop` — runtime_missing

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `8f41297527c2`

- commits: 24
- files changed: 25
- insertions: +3042
- deletions: -1709
- bundle classes touched: docs, tooling
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `8f412975` | Refresh external review snapshot for 10ab0bce | 2 | +42/-42 | docs |  |
| 2 | `10ab0bce` | Refresh external review snapshot for 22fcd435 | 1 | +62/-78 | tooling |  |
| 3 | `22fcd435` | Refresh external review snapshot for 00b8340f | 2 | +55/-58 | docs |  |
| 4 | `00b8340f` | Plan 4.1 live-runtime completed-handoff matcher fix (Codex… | 4 | +187/-72 | tooling |  |
| 5 | `20f1e4b6` | Refresh external review snapshot for cd3a1fb0 | 2 | +44/-44 | docs |  |
| 6 | `cd3a1fb0` | Refresh external review snapshot for 7a5b14a5 | 1 | +68/-85 | tooling |  |
| 7 | `7a5b14a5` | Refresh external review snapshot for ce90a950 | 2 | +43/-43 | docs |  |
| 8 | `ce90a950` | Refresh external review snapshot for ddf7bfe1 | 1 | +49/-46 | tooling |  |
| 9 | `ddf7bfe1` | Refresh external review snapshot for 8a2579eb | 2 | +67/-71 | docs |  |
| 10 | `8a2579eb` | Plan 4.1 5-layer completed-handoff bypass propagation (Code… | 17 | +605/-90 | tooling |  |
| 11 | `38ca87ad` | Refresh external review snapshot for 49a2c8ce | 2 | +42/-42 | docs |  |
| 12 | `49a2c8ce` | Refresh external review snapshot for 63542766 | 1 | +47/-44 | tooling |  |
| 13 | `63542766` | Refresh external review snapshot for 92f5c504 | 2 | +56/-59 | docs |  |
| 14 | `92f5c504` | Plan 4.1 governed projection refresh: regenerated SYSTEM_MA… | 2 | +53/-50 | tooling |  |
| 15 | `aa31fd7b` | Refresh external review snapshot for 9e5d1d33 | 2 | +64/-65 | docs |  |
| 16 | `9e5d1d33` | Plan 4.1 completed-handoff startup authority publication by… | 6 | +420/-182 | tooling |  |
| 17 | `59399406` | Refresh external review snapshot for 7ddb702b | 2 | +44/-44 | docs |  |
| 18 | `7ddb702b` | Refresh external review snapshot for 9c8f0ca5 | 1 | +46/-43 | tooling |  |
| 19 | `9c8f0ca5` | Refresh external review snapshot for 065a9587 | 2 | +59/-62 | docs |  |
| 20 | `065a9587` | Plan 4.1 T20 receipt-chain depth fix (Codex 33): _handoff_t… | 9 | +261/-124 | tooling |  |
| 21 | `32d84ab0` | Refresh external review snapshot for 17121f90 | 2 | +43/-43 | docs |  |
| 22 | `17121f90` | Refresh external review snapshot for 20ba8450 | 1 | +70/-69 | tooling |  |
| 23 | `20ba8450` | Refresh external review snapshot for 36e29446 | 2 | +64/-66 | docs |  |
| 24 | `36e29446` | Plan 4.1 T20 same-HEAD completed-handoff fallback (Codex 32… | 13 | +551/-187 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +3/-2 |
| `bridge.md` | docs | +66/-66 |
| `dev/active/MASTER_PLAN.md` | tooling | +27/-16 |
| `dev/active/ai_governance_platform.md` | tooling | +45/-10 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1250/-1284 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +4/-0 |
| `dev/config/templates/portable_governance_pre_commit_hook.sh` | tooling | +4/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +17/-14 |
| `dev/guides/SYSTEM_MAP.md` | docs | +3/-3 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +46/-3 |
| `dev/scripts/README.md` | tooling | +18/-9 |
| `dev/scripts/checks/startup_authority_contract/runtime_checks.py` | tooling | +3/-31 |
| `dev/scripts/checks/startup_authority_contract/runtime_reviewer_loop.py` | tooling | +89/-0 |
| `dev/scripts/devctl/commands/vcs/push_preflight_commit.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/vcs/push_recovery_loop_handoff.py` | tooling | +109/-111 |
| `dev/scripts/devctl/commands/vcs/push_recovery_loop_state.py` | tooling | +11/-2 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review.py` | tooling | +6/-1 |
| `dev/scripts/devctl/review_channel/agent_session_outcome_events.py` | tooling | +13/-71 |
| `dev/scripts/devctl/review_channel/event_projection_current_session.py` | tooling | +185/-2 |
| `dev/scripts/devctl/runtime/commit_permission_hook.py` | tooling | +62/-0 |
| `dev/scripts/devctl/runtime/completed_handoff_authority.py` | tooling | +173/-2 |
| `dev/scripts/devctl/runtime/managed_receipt_paths.py` | tooling | +38/-0 |
| `dev/scripts/devctl/runtime/review_snapshot_refresh.py` | tooling | +22/-23 |
| `dev/scripts/devctl/tests/vcs/test_commit_gate.py` | tooling | +156/-0 |
| `dev/scripts/devctl/tests/vcs/test_push.py` | tooling | +684/-59 |

## 4. Quality signals

### Governance review
- total findings: 228
- open: 126
- fixed: 88
- false positives: 0

Recent findings:
- `bridge_content_loss_on_rollover` — `dev/scripts/devctl/review_channel/projections` (class1, verdict=`confirmed_issue`)
- `actor_template_missing` — `dev/scripts/devctl/runtime/review_packet_inbox.py` (medium, verdict=`confirmed_issue`)
- `slice_1_2_rev_11` — `dev/scripts/devctl` (n/a, verdict=`fixed`)
- `x12_provider_name_pin_audit` — `dev/scripts/devctl` (n/a, verdict=`confirmed_issue`)
- `slice_1_2_rev_12` — `dev/scripts/devctl` (n/a, verdict=`fixed`)
- `dogfood.command.check` — `dev/scripts/devctl/commands/check/__init__.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.docs-check` — `dev/scripts/devctl/commands/docs/check.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.check-router` — `dev/scripts/devctl/commands/check/router.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.push` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.commit` — `dev/scripts/devctl/commands/vcs/commit.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_checks.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_reviewer_loop.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`8f412975`** — Refresh external review snapshot for 10ab0bce
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`10ab0bce`** — Refresh external review snapshot for 22fcd435
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`22fcd435`** — Refresh external review snapshot for 00b8340f
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`00b8340f`** — Plan 4.1 live-runtime completed-handoff matcher fix (Codex 37): event_projection_current_session.py metadata-free matcher now accepts devctl_commit:<sha> target_ref when both outcome target_revision AND ref revision (including unambiguous abbreviated SHA) are in the same managed-receipt chain (fixes target_revision/target_ref equality strict-check that rejected valid handoffs where receipts accumulated above content commit) + push_recovery_loop_state.py merges parsed compact startup output with extracted typed record fields (initial bypass evaluation no longer requires startup-context/ensure loop cost) + +4 live-shape regression tests in test_push.py covering abbreviated-SHA matching + receipts-above-content-commit + merged startup payload acceptance; full check --profile ci 40/42 (only expected dirty-checkpoint + stale-implementer-ACK live-state gates remaining); test_push.py 95 tests passed; closes the live-runtime bypass mismatch that pushes v6/v7/v8 hit despite Codex 33+34+35's prior fixes
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`20f1e4b6`** — Refresh external review snapshot for cd3a1fb0
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`cd3a1fb0`** — Refresh external review snapshot for 7a5b14a5
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`7a5b14a5`** — Refresh external review snapshot for ce90a950
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`ce90a950`** — Refresh external review snapshot for ddf7bfe1
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`ddf7bfe1`** — Refresh external review snapshot for 8a2579eb
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`8a2579eb`** — Plan 4.1 5-layer completed-handoff bypass propagation (Codex 35): (1) shared completed_handoff_authority extended to walk receipt-chain past publication-only intermediates; (2) new commit_permission_hook runtime module separates raw-git-hook evaluation from authority predicate; (3) new managed_receipt_paths module owns tracked-surface path resolution; (4) pre-commit hook scripts (portable_governance + pre-commit-review-snapshot) now consume completed_handoff_authority via hook-time managed-receipt intent marker; (5) push_preflight_commit + review_snapshot_refresh updated; full hook-test + push-test + docs-check + package-layout + code-shape + broad-except guards green; routed bundle 63 commands cleared with only expected live-state gates (stale bridge poll, dirty-worktree startup-auth, stale implementer ACK) remaining; full check --profile ci 39/42 then 40/42 after broad-except fix; closes rev_pkt_2088 push v6 receipt-chain-cut bug + pre-commit hook bypass propagation; +156 line regression test suite covers managed-receipt acceptance + fail-closed cases (wrong-target / wrong-provider / non-managed-projection commits remain blocked); maintainer docs (AGENTS/MASTER_PLAN/ai_governance_platform/DEVELOPMENT/ENGINEERING_EVOLUTION/README) + SYSTEM_MAP regenerated; ai_governance_platform.md +33 lines fold of architectural directives per rev_pkt_2079/2084/2091 long-horizon plan)
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`38ca87ad`** — Refresh external review snapshot for 49a2c8ce
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`49a2c8ce`** — Refresh external review snapshot for 63542766
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`63542766`** — Refresh external review snapshot for 92f5c504
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`92f5c504`** — Plan 4.1 governed projection refresh: regenerated SYSTEM_MAP.md after Codex 33+34 contract changes (rev_pkt_2073 + rev_pkt_2085 ripple); cleared dirty index from push v5 pre_validation_managed_projection_sync that pre-commit hook blocked; intermediate publication-flow recovery commit so push pre-validation no longer needs to auto-regenerate this file
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`aa31fd7b`** — Refresh external review snapshot for 9e5d1d33
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`9e5d1d33`** — Plan 4.1 completed-handoff startup authority publication bypass (Codex 34): shared completed_handoff_authority runtime helper + startup_authority_contract reviewer-loop block module split + runtime_reviewer_loop module + push_recovery_loop_handoff routes through shared predicate + 5-receipt-chain regressions + 35 startup-auth regressions; same-HEAD completed-handoff evidence accepted as publish/checkpoint-only authority when active_dual_agent blocked solely by missing/dead runtime; fail-closed for stale revision or wrong provider; review_accepted itself stays False (no synthesis of reviewer verdict) (rev_pkt_2085; closes rev_pkt_2084 push v4 startup-authority blocker; supersedes rev_pkt_2079; defers Phase 1b+1c per rev_pkt_2058 norm to Codex 35+; full check --profile ci 69/69 passed with DEVCTL_COMMIT_GATE_BYPASS_STARTUP_AUTHORITY=1; exact 40/42 passed with only dirty-checkpoint+stale-implementer-ACK live-state gates remaining)
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`59399406`** — Refresh external review snapshot for 7ddb702b
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`7ddb702b`** — Refresh external review snapshot for 9c8f0ca5
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`9c8f0ca5`** — Refresh external review snapshot for 065a9587
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`065a9587`** — Plan 4.1 T20 receipt-chain depth fix (Codex 33): _handoff_target_revisions walks full managed receipt-chain ancestry + includes content handoff parent when commit-pipeline receipt resolves to same content commit + 5-level synthetic regression in test_push.py + isort --profile black alignment + maintainer docs (AGENTS/DEVELOPMENT/MASTER_PLAN/ENGINEERING_EVOLUTION/README) + tandem-consistency direct guard cleared via typed heartbeat + implementer pending reset (rev_pkt_2081; closes rev_pkt_2079 publication blocker; explicitly declines Phase 1c finding pipeline scope per rev_pkt_2058 norm; full check --profile ci 41/42 passed only startup-authority-contract-guard blocked by dirty staged worktree cleared by this commit; rev_pkt_2080 Phase 3 stats spec queued for slice after Phase 1c)
  - evolution: Fact: push v6 proved the completed-handoff waiver was present in the push recovery caller, but the target matcher still stopped short of the actual handoff packet. A publication-only generated-surface recovery commit sa…
- **`32d84ab0`** — Refresh external review snapshot for 17121f90
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`17121f90`** — Refresh external review snapshot for 20ba8450
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`20ba8450`** — Refresh external review snapshot for 36e29446
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`36e29446` | MPs: MP-377** — Plan 4.1 T20 same-HEAD completed-handoff fallback (Codex 32) + push_recovery_loop_handoff/_payload/_result/_state/_types orchestrator split + agent_session_outcome_events same-head fallback matcher + tandem live-pending-reset projection fix + AgentSessionOutcome contract row + maintainer docs + MP-377 task rows update (rev_pkt_2073; closes rev_pkt_2042 + rev_pkt_2069 corner case; supersedes rev_pkt_2057+2061+2062+2066+2067+2068+2074+2075 via consolidated rev_pkt_2076; full check --profile ci 40/42 passed only failures expected dirty-worktree+Claude-ACK gates cleared by this commit)
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
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

- open governance findings: 126

### Startup advisories
- repair_reviewer_loop: runtime_missing

### Stale warnings
- Cut a checkpoint before doing anything else.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/review_channel/projections`): bridge_content_loss_on_rollover: Rollover convergence re-projects bridge from typed current_session authority, overwriting reviewer-checkpoint content. System warning names it explicitly. Every rollover loses prior reviewer decision. Recover-from-event-store fix proposed rev_pkt_1715.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/runtime/review_packet_inbox.py`): actor_template_missing: Live repro: first apply call failed with --actor required; retry with --actor claude succeeded. Matches codex Finding 3 independent confirmation. Template review_packet_inbox.py:27 omits --actor in generated command.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl`): x12_provider_name_pin_audit: X12 audit (16 production-code provider-name pins) posted to codex as rev_pkt_1782; operator-confirmed: identity binds to typed role, not provider name
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/check/__init__.py`): dogfood.command.check: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/docs/check.py`): dogfood.command.docs-check: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/check/router.py`): dogfood.command.check-router: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-5847a7dcdddf` binds this file to HEAD `8f41297527c2`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
