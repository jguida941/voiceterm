# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `2096395c9622` — Refresh external review snapshot for bcf72a35
- Tree hash: `55b0a853b8e7`
- Generation stamp: `snap-6ca318bac8a0`
- Generated at (UTC): 2026-05-03T08:50:05Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `single_agent`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 30 files, +2035/-1584
- Governance findings: 152 open / 88 fixed / 254 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm, a Rust voice-first terminal overlay for AI
CLIs). The product thesis is that executable local control — guards,
probes, typed actions, deterministic policy resolution — is what m...
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `feature/governance-quality-sweep`
- HEAD SHA: `2096395c96224031141d21ce4221bac322ee51e3`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-03T04:48:37-04:00

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
- current_push_authorization: `push-auth-20260503T084736764866Z` (valid=True)
- authorized_head_commit: `2096395c96224031141d21ce4221bac322ee51e3`
- approved_target_identity: `tree-receipt-20260503T084736764866Z:43cf204d51a3574d7885951b7efcf88997cdfff0`
- publication_backlog: recommended
- publication_guidance: 2 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `single_agent`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `2096395c9622`

- commits: 24
- files changed: 30
- insertions: +2035
- deletions: -1584
- bundle classes touched: docs, tooling
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `2096395c` | Refresh external review snapshot for bcf72a35 | 2 | +60/-56 | docs |  |
| 2 | `bcf72a35` | Fix idle review-channel status readiness | 8 | +246/-71 | tooling |  |
| 3 | `b3e303b7` | Refresh external review snapshot for 2ff46d1c | 2 | +44/-44 | docs |  |
| 4 | `2ff46d1c` | Refresh external review snapshot for fa2ca61c | 1 | +45/-42 | tooling |  |
| 5 | `fa2ca61c` | Refresh external review snapshot for 9b6cc0d0 | 2 | +65/-58 | docs |  |
| 6 | `9b6cc0d0` | Allow pending-publish pipeline authorization refresh | 6 | +191/-58 | tooling |  |
| 7 | `7cb7ba19` | Refresh external review snapshot for fde85cea | 2 | +50/-55 | docs |  |
| 8 | `fde85cea` | Refresh external review snapshot for d80d603a | 2 | +83/-115 | docs |  |
| 9 | `d80d603a` | Refresh external review snapshot for a1a0468d | 2 | +57/-58 | docs |  |
| 10 | `a1a0468d` | Refresh external review snapshot for de294ab4 | 2 | +69/-67 | docs |  |
| 11 | `de294ab4` | Refresh external review snapshot for 37eb2d78 | 2 | +63/-67 | docs |  |
| 12 | `37eb2d78` | Refresh external review snapshot for cc513241 | 2 | +54/-53 | docs |  |
| 13 | `cc513241` | Refresh external review snapshot for f5d534ad | 2 | +49/-49 | docs |  |
| 14 | `f5d534ad` | Refresh external review snapshot for 1ad2844d | 2 | +53/-50 | docs |  |
| 15 | `1ad2844d` | Refresh external review snapshot for 330a82e6 | 2 | +78/-83 | docs |  |
| 16 | `330a82e6` | Align review-channel launch dry-run test with visible policy | 2 | +67/-58 | tooling |  |
| 17 | `0278cb96` | Migrate Codex provider args from --full-auto to explicit ap… | 8 | +112/-93 | tooling |  |
| 18 | `a982d6d2` | Refresh external review snapshot for 4dee7ce3 | 2 | +46/-46 | docs |  |
| 19 | `4dee7ce3` | Refresh external review snapshot for 6e55bc00 | 1 | +43/-43 | tooling |  |
| 20 | `6e55bc00` | Refresh external review snapshot for e9a687a9 | 2 | +44/-44 | docs |  |
| 21 | `e9a687a9` | Refresh external review snapshot for 8f6e138e | 1 | +47/-44 | tooling |  |
| 22 | `8f6e138e` | Refresh external review snapshot for dbedb6d3 | 2 | +63/-68 | docs |  |
| 23 | `dbedb6d3` | Fix governed push managed projection parsing | 15 | +359/-215 | tooling |  |
| 24 | `04434ae5` | Refresh external review snapshot for 5799b3bf | 2 | +47/-47 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +1/-0 |
| `bridge.md` | docs | +155/-155 |
| `dev/active/MASTER_PLAN.md` | tooling | +8/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1217/-1249 |
| `dev/guides/DEVELOPMENT.md` | docs | +1/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +1/-1 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +24/-0 |
| `dev/scripts/README.md` | tooling | +4/-2 |
| `dev/scripts/devctl/approval_mode.py` | tooling | +9/-1 |
| `dev/scripts/devctl/commands/governance/session_reviewer_loop.py` | tooling | +8/-5 |
| `dev/scripts/devctl/commands/pipeline/auto_recover_action.py` | tooling | +3/-1 |
| `dev/scripts/devctl/commands/pipeline/support.py` | tooling | +12/-4 |
| `dev/scripts/devctl/commands/review_channel/status_readiness.py` | tooling | +35/-1 |
| `dev/scripts/devctl/commands/vcs/push_preflight_commit.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/vcs/push_projection_paths.py` | tooling | +26/-0 |
| `dev/scripts/devctl/commands/vcs/push_projection_receipt.py` | tooling | +5/-124 |
| `dev/scripts/devctl/commands/vcs/push_projection_staging.py` | tooling | +75/-0 |
| `dev/scripts/devctl/commands/vcs/push_projection_status.py` | tooling | +59/-0 |
| `dev/scripts/devctl/commands/vcs/push_worktree_changes.py` | tooling | +1/-1 |
| `dev/scripts/devctl/review_channel/current_session_support.py` | tooling | +37/-0 |
| `dev/scripts/devctl/runtime/remote_commit_pipeline_state.py` | tooling | +1/-0 |
| `dev/scripts/devctl/runtime/review_packet_inbox.py` | tooling | +16/-0 |
| `dev/scripts/devctl/runtime/review_packet_inbox_merge.py` | tooling | +25/-2 |
| `dev/scripts/devctl/tests/commands/test_pipeline_command.py` | tooling | +122/-0 |
| `dev/scripts/devctl/tests/review_channel/test_current_session_projection.py` | tooling | +30/-0 |
| `dev/scripts/devctl/tests/review_channel/test_launch_topology.py` | tooling | +6/-1 |
| `dev/scripts/devctl/tests/review_channel/test_review_channel.py` | tooling | +19/-10 |
| `dev/scripts/devctl/tests/review_channel/test_status_runtime_readiness.py` | tooling | +41/-0 |
| `dev/scripts/devctl/tests/vcs/test_push.py` | tooling | +92/-25 |
| `dev/state/plan_index.jsonl` | tooling | +1/-0 |

## 4. Quality signals

### Governance review
- total findings: 254
- open: 152
- fixed: 88
- false positives: 0

Recent findings:
- `dogfood.command.status` — `dev/scripts/devctl/commands/reporting/status.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.render-surfaces` — `dev/scripts/devctl/commands/governance/render_surfaces.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-loop` — `dev/scripts/devctl/commands/reporting/claude_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-mind` — `dev/scripts/devctl/commands/agent_mind/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-bootstrap` — `dev/scripts/devctl/commands/governance/bootstrap.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-status` — `dev/scripts/devctl/commands/reporting/orchestrate_status.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-watch` — `dev/scripts/devctl/commands/governance/orchestrate_watch.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.integrations-import` — `dev/scripts/devctl/commands/integrations_import.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-export` — `dev/scripts/devctl/commands/governance/export.py` (n/a, verdict=`confirmed_issue`)
- `packet.transition_session_disambiguation` — `dev/scripts/devctl/review_channel/instruction_transitions.py` (critical, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_state.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`2096395c`** — Refresh external review snapshot for bcf72a35
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`bcf72a35`** — Fix idle review-channel status readiness
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`b3e303b7`** — Refresh external review snapshot for 2ff46d1c
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`2ff46d1c`** — Refresh external review snapshot for fa2ca61c
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`fa2ca61c`** — Refresh external review snapshot for 9b6cc0d0
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`9b6cc0d0`** — Allow pending-publish pipeline authorization refresh
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`7cb7ba19`** — Refresh external review snapshot for fde85cea
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`fde85cea`** — Refresh external review snapshot for d80d603a
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`d80d603a`** — Refresh external review snapshot for a1a0468d
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`a1a0468d`** — Refresh external review snapshot for de294ab4
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`de294ab4`** — Refresh external review snapshot for 37eb2d78
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`37eb2d78`** — Refresh external review snapshot for cc513241
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`cc513241`** — Refresh external review snapshot for f5d534ad
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`f5d534ad`** — Refresh external review snapshot for 1ad2844d
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`1ad2844d`** — Refresh external review snapshot for 330a82e6
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`330a82e6`** — Align review-channel launch dry-run test with visible policy
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`0278cb96`** — Migrate Codex provider args from --full-auto to explicit approval/sandbox flags
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`a982d6d2`** — Refresh external review snapshot for 4dee7ce3
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`4dee7ce3`** — Refresh external review snapshot for 6e55bc00
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`6e55bc00`** — Refresh external review snapshot for e9a687a9
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`e9a687a9`** — Refresh external review snapshot for 8f6e138e
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`8f6e138e`** — Refresh external review snapshot for dbedb6d3
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`dbedb6d3`** — Fix governed push managed projection parsing
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`04434ae5`** — Refresh external review snapshot for 5799b3bf
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
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

- open governance findings: 152

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/reporting/status.py`): dogfood.command.status: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/render_surfaces.py`): dogfood.command.render-surfaces: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/reporting/claude_loop.py`): dogfood.command.agent-loop: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/agent_mind/command.py`): dogfood.command.agent-mind: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/bootstrap.py`): dogfood.command.governance-bootstrap: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/reporting/orchestrate_status.py`): dogfood.command.orchestrate-status: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/orchestrate_watch.py`): dogfood.command.orchestrate-watch: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/integrations_import.py`): dogfood.command.integrations-import: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-6ca318bac8a0` binds this file to HEAD `2096395c9622`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
