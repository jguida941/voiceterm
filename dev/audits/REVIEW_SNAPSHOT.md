# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `69c856ebd13e` — Record push proof closure receipts
- Tree hash: `3bce0e9f92d9`
- Generation stamp: `snap-bc668540349f`
- Generated at (UTC): 2026-05-20T06:19:00Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 29 files, +2568/-1395
- Governance findings: 26 open / 0 fixed / 26 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm...
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD SHA: `69c856ebd13e31f15220b731712c77b7602fa333`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-20T02:17:59-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 30 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `local_terminal`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `69c856ebd13e`

- commits: 24
- files changed: 29
- insertions: +2568
- deletions: -1395
- bundle classes touched: tooling, docs

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `69c856eb` | Record push proof closure receipts | 6 | +59/-62 | tooling |  |
| 2 | `20a808a3` | Refresh external review snapshot for 3e35699c | 1 | +54/-51 | tooling |  |
| 3 | `3e35699c` | Fix push-owned commit proof receipts | 5 | +282/-78 | tooling |  |
| 4 | `af8ef168` | Refresh policy-owned generated surfaces for 58a30236 | 1 | +2/-2 | docs |  |
| 5 | `58a30236` | Refresh external review snapshot for ef1f4365 | 1 | +54/-63 | tooling |  |
| 6 | `ef1f4365` | Record packet attention plan closure | 5 | +51/-48 | tooling |  |
| 7 | `6ec72fd2` | Refresh external review snapshot for 623a21ac | 1 | +60/-61 | tooling |  |
| 8 | `623a21ac` | Fix packet attention drain accounting | 6 | +258/-131 | tooling |  |
| 9 | `a1f4a834` | Refresh external review snapshot for 6f94e606 | 1 | +62/-63 | tooling |  |
| 10 | `6f94e606` | Record contract connectivity plan closure | 5 | +51/-48 | tooling |  |
| 11 | `200af3e3` | Refresh external review snapshot for bad81bdf | 1 | +86/-95 | tooling |  |
| 12 | `bad81bdf` | Gate contract connectivity debt through typed plans | 9 | +277/-55 | tooling |  |
| 13 | `d480a306` | Refresh external review snapshot for b5214fdd | 1 | +48/-49 | tooling |  |
| 14 | `b5214fdd` | Record plan closure for proof ledger guard | 5 | +55/-52 | tooling |  |
| 15 | `acd9bd92` | Refresh external review snapshot for c023e7bc | 1 | +51/-52 | tooling |  |
| 16 | `c023e7bc` | Classify plan closure receipts as proof ledger | 7 | +82/-58 | tooling |  |
| 17 | `5fb57f5a` | Refresh external review snapshot for ee079435 | 1 | +52/-52 | tooling |  |
| 18 | `ee079435` | Scope feature proof enforcement to source commits | 3 | +171/-56 | tooling |  |
| 19 | `1489c777` | Refresh external review snapshot for 01290117 | 1 | +48/-48 | tooling |  |
| 20 | `01290117` | Backfill packet binding continuity receipts | 4 | +76/-62 | tooling |  |
| 21 | `3486373d` | Refresh external review snapshot for 30211cd7 | 1 | +51/-51 | tooling |  |
| 22 | `30211cd7` | Record ground truth probe receipt | 2 | +52/-51 | tooling |  |
| 23 | `b8901376` | Refresh external review snapshot for 3b60f794 | 1 | +53/-53 | tooling |  |
| 24 | `3b60f794` | Surface contract connectivity debt at startup | 9 | +533/-54 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `dev/active/MASTER_PLAN.md` | tooling | +1/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1233/-1277 |
| `dev/guides/SYSTEM_MAP.md` | docs | +4/-4 |
| `dev/scripts/checks/contract_connectivity/models.py` | tooling | +22/-0 |
| `dev/scripts/checks/contract_connectivity/planned_debt.py` | tooling | +58/-0 |
| `dev/scripts/checks/contract_connectivity/report.py` | tooling | +42/-0 |
| `dev/scripts/checks/contract_connectivity/support.py` | tooling | +34/-8 |
| `dev/scripts/checks/feature_has_proof_receipt/command.py` | tooling | +70/-1 |
| `dev/scripts/devctl/commands/development/packet_attention_body_followup.py` | tooling | +8/-8 |
| `dev/scripts/devctl/commands/vcs/push_owned_commit_proof.py` | tooling | +67/-0 |
| `dev/scripts/devctl/commands/vcs/push_preflight_commit.py` | tooling | +45/-7 |
| `dev/scripts/devctl/commands/vcs/push_projection_receipt.py` | tooling | +46/-7 |
| `dev/scripts/devctl/context_graph/quality_signal_render.py` | tooling | +45/-0 |
| `dev/scripts/devctl/review_channel/agent_packet_attention.py` | tooling | +53/-72 |
| `dev/scripts/devctl/review_channel/agent_packet_attention_lifecycle.py` | tooling | +96/-0 |
| `dev/scripts/devctl/runtime/startup_signal_contract_connectivity.py` | tooling | +278/-0 |
| `dev/scripts/devctl/runtime/startup_signals.py` | tooling | +36/-0 |
| `dev/scripts/devctl/tests/checks/contract_connectivity/test_check_contract_connectivity.py` | tooling | +69/-0 |
| `dev/scripts/devctl/tests/checks/test_check_feature_has_proof_receipt.py` | tooling | +48/-0 |
| `dev/scripts/devctl/tests/context_graph/test_context_graph.py` | tooling | +20/-0 |
| `dev/scripts/devctl/tests/review_channel/test_agent_packet_attention_focus.py` | tooling | +49/-0 |
| `dev/scripts/devctl/tests/review_channel/test_packet_history_lookup.py` | tooling | +5/-3 |
| `dev/scripts/devctl/tests/runtime/test_startup_signals.py` | tooling | +99/-1 |
| `dev/scripts/devctl/tests/vcs/test_push.py` | tooling | +69/-0 |
| `dev/state/ground_truth_probe_receipts.jsonl` | tooling | +1/-0 |
| `dev/state/plan_index.jsonl` | tooling | +20/-7 |
| `dev/state/plan_ingestion_receipts.jsonl` | tooling | +19/-0 |
| `dev/state/plan_row_closure_receipts.jsonl` | tooling | +12/-0 |
| `dev/state/plan_source_snapshots.jsonl` | tooling | +19/-0 |

## 4. Quality signals

### Governance review
- total findings: 26
- open: 26
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.install-git-hooks` — `dev/scripts/devctl/commands/governance/install_git_hooks.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/governance/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.render-surfaces` — `dev/scripts/devctl/commands/governance/render_surfaces.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.remote-control` — `dev/scripts/devctl/commands/remote_control/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.probe-report` — `dev/scripts/devctl/commands/probe_report.py` (n/a, verdict=`confirmed_issue`)
- `role_oriented_packet_inbox` — `dev/scripts/devctl/review_channel/event_reducer_inbox.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.pipeline` — `dev/scripts/devctl/commands/pipeline/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-mind` — `dev/scripts/devctl/commands/agent_mind/command.py` (n/a, verdict=`confirmed_issue`)

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

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`69c856eb`** — Record push proof closure receipts
- **`20a808a3`** — Refresh external review snapshot for 3e35699c
- **`3e35699c`** — Fix push-owned commit proof receipts
- **`af8ef168`** — Refresh policy-owned generated surfaces for 58a30236
- **`58a30236`** — Refresh external review snapshot for ef1f4365
- **`ef1f4365`** — Record packet attention plan closure
- **`6ec72fd2`** — Refresh external review snapshot for 623a21ac
- **`623a21ac`** — Fix packet attention drain accounting
- **`a1f4a834`** — Refresh external review snapshot for 6f94e606
- **`6f94e606`** — Record contract connectivity plan closure
- **`200af3e3`** — Refresh external review snapshot for bad81bdf
- **`bad81bdf`** — Gate contract connectivity debt through typed plans
- **`d480a306`** — Refresh external review snapshot for b5214fdd
- **`b5214fdd`** — Record plan closure for proof ledger guard
- **`acd9bd92`** — Refresh external review snapshot for c023e7bc
- **`c023e7bc`** — Classify plan closure receipts as proof ledger
- **`5fb57f5a`** — Refresh external review snapshot for ee079435
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`ee079435`** — Scope feature proof enforcement to source commits
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`1489c777`** — Refresh external review snapshot for 01290117
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`01290117`** — Backfill packet binding continuity receipts
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`3486373d`** — Refresh external review snapshot for 30211cd7
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`30211cd7`** — Record ground truth probe receipt
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`b8901376`** — Refresh external review snapshot for 3b60f794
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`3b60f794`** — Surface contract connectivity debt at startup
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- 2026-05-11 slice 18 fix arc + bilateral protocol consolidation (MP-377):
- 2026-05-14 launch-bootstrap repair family (MP-378): after the relaunch
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 26

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/governance/install_git_hooks.py`): dogfood.command.install-git-hooks: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/relaunch_loop.py`): dogfood.command.relaunch-loop: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/relaunch_loop.py`): dogfood.command.relaunch-loop: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/render_surfaces.py`): dogfood.command.render-surfaces: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/remote_control/command.py`): dogfood.command.remote-control: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/probe_report.py`): dogfood.command.probe-report: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/review_channel/event_reducer_inbox.py`): role_oriented_packet_inbox: Packet inbox routing is still provider-keyed in several runtime readers. Visibility and consumption must resolve through actor role plus exact session when scoped so provider role switches cannot hide, consume, or drop pending packets.
- **governance_open** (`dev/scripts/devctl/commands/pipeline/command.py`): dogfood.command.pipeline: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-bc668540349f` binds this file to HEAD `69c856ebd13e`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
