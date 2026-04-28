# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `8543d8ce760f` — Refresh external review snapshot for c985fc64
- Tree hash: `524caff17088`
- Generation stamp: `snap-56ef70da4ea2`
- Generated at (UTC): 2026-04-28T01:40:32Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 78 files, +6876/-2118
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
- HEAD SHA: `8543d8ce760f28f4e4c3bb78b2c1c127f3be67db`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-27T19:09:41-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 30
- unstaged_path_count: 1
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260427T230311212331Z` (valid=False)
- authorized_head_commit: `4d3b48639cb153805e10ea0ad6f496284d102296`
- approved_target_identity: `tree-receipt-20260427T230311212331Z:cc6a249d2fccfce6a1a077b5aa0809ff87f6789b`
- publication_backlog: urgent
- publication_guidance: 35 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `active_dual_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`
- implementation_blocked: yes — checkpoint_required

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `8543d8ce760f`

- commits: 24
- files changed: 78
- insertions: +6876
- deletions: -2118
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 11 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `8543d8ce` | Refresh external review snapshot for c985fc64 | 2 | +43/-43 | docs |  |
| 2 | `c985fc64` | Refresh external review snapshot for 4d3b4863 | 1 | +71/-68 | tooling |  |
| 3 | `4d3b4863` | Refresh external review snapshot for f0a34191 | 2 | +92/-78 | docs |  |
| 4 | `f0a34191` | Plan 4.1 Path I commit-pipeline self-resolution + rev_pkt_2… | 47 | +1887/-367 | tooling | Parser / ANSI boundary |
| 5 | `120c1249` | Refresh external review snapshot for eee2cc6d | 2 | +44/-44 | docs |  |
| 6 | `eee2cc6d` | Refresh external review snapshot for 05a30319 | 1 | +56/-56 | tooling |  |
| 7 | `05a30319` | Refresh external review snapshot for 92b1f57d | 2 | +43/-43 | docs |  |
| 8 | `92b1f57d` | Refresh external review snapshot for 62cd83cc | 1 | +48/-46 | tooling |  |
| 9 | `62cd83cc` | Refresh external review snapshot for 499baa8b | 1 | +1/-1 | tooling |  |
| 10 | `499baa8b` | Refresh external review snapshot for f6e3783d | 2 | +64/-65 | docs |  |
| 11 | `f6e3783d` | Refresh external review snapshot for 80c1791a | 1 | +43/-43 | tooling |  |
| 12 | `80c1791a` | Refresh external review snapshot for aebed8b5 | 1 | +50/-47 | tooling |  |
| 13 | `aebed8b5` | Refresh external review snapshot for f86e0db2 | 2 | +55/-60 | docs |  |
| 14 | `f86e0db2` | Plan 4.1 catch-22 unblock: push.py import for build_push_ac… | 2 | +59/-58 | tooling |  |
| 15 | `d70b2b6f` | Plan 4.1 catch-22 unblock: post-receipt startup-context ref… | 4 | +236/-64 | tooling |  |
| 16 | `0503204b` | Refresh external review snapshot for 196a2f7f | 1 | +40/-40 | tooling |  |
| 17 | `196a2f7f` | Refresh external review snapshot for f429524b | 1 | +43/-43 | tooling |  |
| 18 | `f429524b` | Refresh external review snapshot for 7e78f6c0 | 1 | +69/-72 | tooling |  |
| 19 | `7e78f6c0` | Refresh external review snapshot for 7bf66f03 | 2 | +81/-82 | docs |  |
| 20 | `7bf66f03` | Plan 4.1 bounded slice: G1 push.py duplicate fix + G2 push_… | 35 | +2281/-513 | tooling |  |
| 21 | `dc4863ea` | Refresh external review snapshot for 1c5e13e2 | 2 | +71/-72 | docs |  |
| 22 | `1c5e13e2` | Plan 4.1 bounded push pre-validation recovery phase + revie… | 22 | +1383/-101 | tooling |  |
| 23 | `ab077ec4` | Refresh external review snapshot for f650da29 | 1 | +49/-46 | tooling |  |
| 24 | `f650da29` | Refresh external review snapshot for ee0558a2 | 2 | +67/-66 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +4/-0 |
| `bridge.md` | docs | +78/-78 |
| `dev/active/MASTER_PLAN.md` | tooling | +79/-0 |
| `dev/active/agent_substrate_architecture_review.md` | tooling | +17/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +118/-1 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +5/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1291/-1274 |
| `dev/guides/DEVELOPMENT.md` | docs | +19/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +5/-5 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +115/-0 |
| `dev/scripts/README.md` | tooling | +25/-4 |
| `dev/scripts/checks/review_surface_consistency/proof_tick.py` | tooling | +27/-2 |
| `dev/scripts/devctl/commands/review_channel/event_action_support.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/vcs/commit.py` | tooling | +18/-0 |
| `dev/scripts/devctl/commands/vcs/commit_action_result_report.py` | tooling | +27/-0 |
| `dev/scripts/devctl/commands/vcs/commit_guard_bundle.py` | tooling | +225/-3 |
| `dev/scripts/devctl/commands/vcs/commit_guard_replay.py` | tooling | +3/-3 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_stage_failure.py` | tooling | +144/-0 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_validators.py` | tooling | +12/-70 |
| `dev/scripts/devctl/commands/vcs/governed_executor.py` | tooling | +18/-36 |
| `dev/scripts/devctl/commands/vcs/governed_executor_actions.py` | tooling | +41/-36 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +13/-4 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py` | tooling | +8/-5 |
| `dev/scripts/devctl/commands/vcs/governed_executor_index_lock.py` | tooling | +82/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_packets.py` | tooling | +26/-18 |
| `dev/scripts/devctl/commands/vcs/governed_executor_phases.py` | tooling | +61/-70 |
| `dev/scripts/devctl/commands/vcs/governed_executor_push_result.py` | tooling | +48/-3 |
| `dev/scripts/devctl/commands/vcs/governed_executor_recovery_actions.py` | tooling | +75/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_stage_index.py` | tooling | +93/-0 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +118/-136 |
| `dev/scripts/devctl/commands/vcs/push_diagnostics.py` | tooling | +7/-1 |
| `dev/scripts/devctl/commands/vcs/push_executor_routing.py` | tooling | +47/-6 |
| `dev/scripts/devctl/commands/vcs/push_findings.py` | tooling | +12/-0 |
| `dev/scripts/devctl/commands/vcs/push_findings_identity.py` | tooling | +137/-0 |
| `dev/scripts/devctl/commands/vcs/push_findings_identity_validation.py` | tooling | +158/-0 |
| `dev/scripts/devctl/commands/vcs/push_findings_payloads.py` | tooling | +163/-0 |
| `dev/scripts/devctl/commands/vcs/push_flow.py` | tooling | +98/-4 |
| `dev/scripts/devctl/commands/vcs/push_git_status.py` | tooling | +47/-0 |
| `dev/scripts/devctl/commands/vcs/push_preflight_projection.py` | tooling | +38/-1 |
| `dev/scripts/devctl/commands/vcs/push_projection_runtime_refresh.py` | tooling | +225/-21 |
| _38 more files trimmed_ | | |

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

- **risk**: Parser / ANSI boundary — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_index_lock.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_stage_index.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_push_result.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_recovery_actions.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_identity_contract_rows.py`) — Commit f0a34191 changed dev/scripts/devctl/platform/runtime_identity_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit f0a34191 changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit f0a34191 changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/pending_packet_models.py`) — Commit f0a34191 changed dev/scripts/devctl/review_channel/pending_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/action_contracts.py`) — Commit f0a34191 changed dev/scripts/devctl/runtime/action_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_packet_models.py`) — Commit f0a34191 changed dev/scripts/devctl/runtime/review_state_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/runtime/test_action_contracts.py`) — Commit f0a34191 changed dev/scripts/devctl/tests/runtime/test_action_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`8543d8ce`** — Refresh external review snapshot for c985fc64
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`c985fc64`** — Refresh external review snapshot for 4d3b4863
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`4d3b4863`** — Refresh external review snapshot for f0a34191
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`f0a34191` | markers: F2, F1** — Plan 4.1 Path I commit-pipeline self-resolution + rev_pkt_2059 stage_commit_pipeline evidence gate: ActionResult structured errors/reason_chain/remediation/auto_executable (N2) + bounded .git/index.lock retry (F2) + host-process-cleanup-post age-out auto-retry (F1) + helper seam splits + ActionResult builder ownership move to runtime/action_contracts.py + git index-lock classification to runtime/vcs.py + full_guard_bundle_evidence field on packet_contract gate; includes Codex 28 N1 auto-heartbeat-refresh + maintainer docs (rev_pkt_2063; closes rev_pkt_2055 + rev_pkt_2052 + rev_pkt_2059; publishes pending rev_pkt_1997 + rev_pkt_2003 + rev_pkt_2008 + Codex 13/18/19/23/25/26/27/28/29/30 fixes; rev_pkt_2057+2058+2061+2062 explicitly queued for next slice with documented architectural reasoning per rev_pkt_2058 norm)
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`120c1249`** — Refresh external review snapshot for eee2cc6d
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`eee2cc6d`** — Refresh external review snapshot for 05a30319
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`05a30319`** — Refresh external review snapshot for 92b1f57d
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`92b1f57d`** — Refresh external review snapshot for 62cd83cc
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`62cd83cc`** — Refresh external review snapshot for 499baa8b
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`499baa8b`** — Refresh external review snapshot for f6e3783d
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`f6e3783d`** — Refresh external review snapshot for 80c1791a
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`80c1791a`** — Refresh external review snapshot for aebed8b5
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`aebed8b5`** — Refresh external review snapshot for f86e0db2
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`f86e0db2`** — Plan 4.1 catch-22 unblock: push.py import for build_push_action (rev_pkt_2047 M2 path C completion)
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`d70b2b6f`** — Plan 4.1 catch-22 unblock: post-receipt startup-context refresh auto-recovery in push_projection_runtime_refresh + regression test (rev_pkt_2047 M2 path C; bootstrap break for rev_pkt_2039 publication)
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`0503204b`** — Refresh external review snapshot for 196a2f7f
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`196a2f7f`** — Refresh external review snapshot for f429524b
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`f429524b`** — Refresh external review snapshot for 7e78f6c0
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`7e78f6c0`** — Refresh external review snapshot for 7bf66f03
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`7bf66f03`** — Plan 4.1 bounded slice: G1 push.py duplicate fix + G2 push_findings canonical Finding seam refactor + 3-module split + noqa rationale + MP377-P0-T13..T18 plan rows + ADR-024..027 + 5 regression tests (rev_pkt_2039; supersedes rev_pkt_2034/2037; closes rev_pkt_2029/2030/2032/2035/2041/2042; publishes rev_pkt_1997 + rev_pkt_2003 + rev_pkt_2008 + Codex 13/18/19/23/25/26 fixes)
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`dc4863ea`** — Refresh external review snapshot for 1c5e13e2
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`1c5e13e2`** — Plan 4.1 bounded push pre-validation recovery phase + reviewer_mode parity authority shift (rev_pkt_2022 + rev_pkt_2024 shape extraction; supersedes rev_pkt_2016/2015; closes rev_pkt_2019/2020/2021/2023; publishes pending rev_pkt_1997 + rev_pkt_2003 + rev_pkt_2008 + Codex 13 fix)
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`ab077ec4`** — Refresh external review snapshot for f650da29
  - evolution: Fact: the live `rev_pkt_2053` publication attempt exposed two places where the commit pipeline still behaved like a manual checklist. A quick guard run could fail only because `host-process-cleanup-post` saw recently de…
- **`f650da29`** — Refresh external review snapshot for ee0558a2
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
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-56ef70da4ea2` binds this file to HEAD `8543d8ce760f`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
