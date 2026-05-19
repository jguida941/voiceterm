# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `1efa1407ab5b` — Route publication-scope release checks through push refs
- Tree hash: `6b0152c5aea0`
- Generation stamp: `snap-5354597ee869`
- Generated at (UTC): 2026-05-19T04:57:55Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 72 files, +5280/-2098
- Governance findings: 27 open / 0 fixed / 27 total
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
- HEAD SHA: `1efa1407ab5b5bb0f50f24d38d55aa6697d22975`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-19T00:57:34-04:00

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
- publication_backlog: queued
- publication_guidance: Local branch still has unpublished work waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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
- advisory: `no_push_needed` — clean_worktree

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `1efa1407ab5b`

- commits: 24
- files changed: 72
- insertions: +5280
- deletions: -2098
- bundle classes touched: docs, tooling, runtime
- risk add-ons triggered: Threading / lifecycle / memory, Performance / latency
- authority surfaces touched: 6 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `1efa1407` | Route publication-scope release checks through push refs | 10 | +109/-51 | tooling |  |
| 2 | `4d80a6f9` | Refresh external review snapshot for a68c6b47 | 1 | +64/-79 | tooling |  |
| 3 | `a68c6b47` | Document release hygiene guard inventory | 8 | +84/-47 | tooling |  |
| 4 | `12600f3f` | Refresh external review snapshot for 7a272579 | 1 | +69/-64 | tooling |  |
| 5 | `7a272579` | Phase 0.6A: propagate validation scope through release chec… | 18 | +240/-85 | tooling | Threading / lifecycle / memory, Performance / latency |
| 6 | `38057f5c` | Refresh external review snapshot for 15425337 | 1 | +60/-61 | tooling |  |
| 7 | `15425337` | Phase 0.6A: carry push preflight refs into publication scope | 13 | +200/-61 | tooling |  |
| 8 | `cf75f3f4` | Refresh external review snapshot for 9716470b | 1 | +69/-76 | tooling |  |
| 9 | `9716470b` | Phase 0.6A: bind governed push to publication authorization | 19 | +815/-419 | tooling |  |
| 10 | `fcb709ef` | Refresh external review snapshot for 36a930f7 | 1 | +55/-57 | tooling |  |
| 11 | `36a930f7` | Phase 0.6A: fix typed collaboration routing and controller… | 21 | +1391/-447 | tooling |  |
| 12 | `ddaf58f5` | Refresh external review snapshot for f2f152dd | 1 | +67/-64 | tooling |  |
| 13 | `f2f152dd` | Phase 0A: bridge and boot-card projection kill-switch | 18 | +328/-224 | tooling |  |
| 14 | `b161e95b` | Phase 0.6.C: AGENTS.md vs CLAUDE.md projection-parity viola… | 2 | +2/-2 | tooling |  |
| 15 | `286b8703` | Phase 0.6.A: add alias-authority-parity guardrail | 2 | +2/-1 | tooling |  |
| 16 | `87f1248e` | Narrow Phase 0.6 to entrypoint, bridge containment, and top… | 2 | +69/-68 | tooling |  |
| 17 | `815901f4` | Refresh external review snapshot for b16d00a4 | 2 | +72/-74 | docs |  |
| 18 | `b16d00a4` | Phase 0.4-Bootstrap IMPLEMENTATION: launcher + post authori… | 21 | +900/-13 | tooling |  |
| 19 | `b85ed85a` | Phase 0.6 amendment: Entry-Point Hardening + Bridge Retirem… | 2 | +96/-1 | tooling |  |
| 20 | `f453f8c1` | Refresh external review snapshot for f6ef179c | 2 | +56/-53 | docs |  |
| 21 | `f6ef179c` | Phase 0.4-Bootstrap amendment: Bootstrap/Launcher/Topology… | 2 | +55/-1 | tooling |  |
| 22 | `5bf86443` | Refresh external review snapshot for 4b51058a | 1 | +42/-42 | tooling |  |
| 23 | `4b51058a` | Refresh external review snapshot for 50039a1b | 2 | +49/-43 | tooling |  |
| 24 | `50039a1b` | Phase 0.4: Sync canonical GuardIR extraction plan | 1 | +386/-65 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `AGENTS.md` | docs | +13/-9 |
| `bridge.md` | docs | +31/-153 |
| `dev/active/MASTER_PLAN.md` | tooling | +35/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +60/-2 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +942/-941 |
| `dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md` | tooling | +666/-140 |
| `dev/audits/plan_intake/sha256-manifest.txt` | tooling | +9/-6 |
| `dev/config/devctl_repo_policy.json` | tooling | +1/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +45/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +5/-5 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +127/-1 |
| `dev/scripts/README.md` | tooling | +57/-1 |
| `dev/scripts/checks/check_bridge_projection_only.py` | tooling | +47/-0 |
| `dev/scripts/checks/check_launcher_authority_ordering.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_publication_scope_integrity_for_push.py` | tooling | +14/-0 |
| `dev/scripts/checks/launcher_authority_ordering/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/launcher_authority_ordering/command.py` | tooling | +230/-0 |
| `dev/scripts/checks/publication_scope_integrity_for_push/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/publication_scope_integrity_for_push/command.py` | tooling | +81/-0 |
| `dev/scripts/checks/review_channel_bridge/report.py` | tooling | +36/-1 |
| `dev/scripts/devctl/cli_parser/builders_checks.py` | tooling | +13/-0 |
| `dev/scripts/devctl/commands/check/phases.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/check/router_range.py` | tooling | +29/-0 |
| `dev/scripts/devctl/commands/check/support.py` | tooling | +11/-0 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +84/-10 |
| `dev/scripts/devctl/commands/development/packet_attention_commands.py` | tooling | +49/-5 |
| `dev/scripts/devctl/commands/review_channel/bridge_action_prepare.py` | tooling | +17/-5 |
| `dev/scripts/devctl/commands/review_channel/bridge_handler.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_success_report.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_support.py` | tooling | +17/-0 |
| `dev/scripts/devctl/commands/review_channel/event_attempted_action_scope.py` | tooling | +180/-0 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +44/-168 |
| `dev/scripts/devctl/commands/review_channel_command/helpers.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/review_channel_command/models.py` | tooling | +5/-0 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +24/-265 |
| `dev/scripts/devctl/commands/vcs/push_attempted_command.py` | tooling | +29/-0 |
| `dev/scripts/devctl/commands/vcs/push_authorization_control.py` | tooling | +102/-0 |
| `dev/scripts/devctl/commands/vcs/push_control_decision.py` | tooling | +64/-0 |
| _32 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 27
- open: 27
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.process-cleanup` — `dev/scripts/devctl/commands/process/cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.install-git-hooks` — `dev/scripts/devctl/commands/governance/install_git_hooks.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/governance/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.render-surfaces` — `dev/scripts/devctl/commands/governance/render_surfaces.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.remote-control` — `dev/scripts/devctl/commands/remote_control/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.probe-report` — `dev/scripts/devctl/commands/probe_report.py` (n/a, verdict=`confirmed_issue`)
- `role_oriented_packet_inbox` — `dev/scripts/devctl/review_channel/event_reducer_inbox.py` (high, verdict=`confirmed_issue`)
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

### Targeted hints

- **risk**: Threading / lifecycle / memory — Delta touches a risk-sensitive surface; verify the routed bundle
- **risk**: Performance / latency — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_prepare.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_success_report.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_support.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_check_agents_contract.py`) — Commit f2f152dd changed dev/scripts/devctl/tests/checks/test_check_agents_contract.py

### Suggested verification commands

- `cd rust && cargo test --bin voiceterm`
- `cd rust && cargo clippy --all-targets -- -D warnings`
- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`1efa1407`** — Route publication-scope release checks through push refs
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`4d80a6f9`** — Refresh external review snapshot for a68c6b47
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`a68c6b47`** — Document release hygiene guard inventory
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`12600f3f`** — Refresh external review snapshot for 7a272579
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`7a272579`** — Phase 0.6A: propagate validation scope through release checks
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`38057f5c`** — Refresh external review snapshot for 15425337
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`15425337`** — Phase 0.6A: carry push preflight refs into publication scope
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`cf75f3f4`** — Refresh external review snapshot for 9716470b
- **`9716470b`** — Phase 0.6A: bind governed push to publication authorization
- **`fcb709ef`** — Refresh external review snapshot for 36a930f7
- **`36a930f7`** — Phase 0.6A: fix typed collaboration routing and controller reads
- **`ddaf58f5`** — Refresh external review snapshot for f2f152dd
- **`f2f152dd`** — Phase 0A: bridge and boot-card projection kill-switch
- **`b161e95b`** — Phase 0.6.C: AGENTS.md vs CLAUDE.md projection-parity violation captured
  - Operator-mandated 2026-05-18T~18:00 EDT. Empirical evidence that the topology-hardcode-via-projection bug source is dev/scripts/devctl/governance/instruction_boot_card.py — the template that generates AGENTS.md AND CLAUDE.md from render-surfaces. Both projections SHOULD be byte-equal (modulo surface_id marker) since any agent can play any role per cached-hammock P58.5, but they currently diverge on 8 lines hardcoding --role reviewer --actor codex (AGENTS.md) vs --role implementer --actor claude (CLAUDE.md).
- **`286b8703`** — Phase 0.6.A: add alias-authority-parity guardrail
  - Operator-mandated 2026-05-18T~17:45 EDT. Single guardrail added to Phase 0.6.A green criteria: no command alias may parse into a different authority model than /develop. /goal, /check-it, /archive-evidence, /session-log must be adapters into the SAME typed path as /develop, not parallel command systems. Regression test: byte-for-byte packet/event payload equality (modulo timestamp/id) between alias invocation and canonical /develop action.
- **`87f1248e`** — Narrow Phase 0.6 to entrypoint, bridge containment, and topology guards
  - Plan-only correction per operator scope-discipline directive 2026-05-18T~17:30 EDT. Phase 0.6 is scoped to bounded substrate guardrails before Phase 1 proof-integrity, not full bridge retirement or full N-agent topology refactor.
- **`815901f4`** — Refresh external review snapshot for b16d00a4
- **`b16d00a4`** — Phase 0.4-Bootstrap IMPLEMENTATION: launcher + post authority-ordering fix
  - Operator-issued 2026-05-18T~17:30 EDT. This commit lands the Phase 0.4-Bootstrap implementation files codex shipped during exec session (PID 61481, session 019e3cc2-c993-75c1-851a-24866d133b5d). Prior commit b85ed85a was the Phase 0.6 PLAN AMENDMENT only — this commit makes the Phase 0.4 IMPLEMENTATION durable on GuardIR extraction branch.
- **`b85ed85a`** — Phase 0.6 amendment: Entry-Point Hardening + Bridge Retirement + Role-Based Topology
  - Operator amendment 2026-05-18T~17:00 EDT. Threads three architectural root-cause concerns already specified in cached-hammock plan into canonical extraction plan as Phase 0.6 (lands BEFORE Phase 1 P0 proof-integrity).
- **`f453f8c1`** — Refresh external review snapshot for f6ef179c
- **`f6ef179c`** — Phase 0.4-Bootstrap amendment: Bootstrap/Launcher/Topology Reliability + authority-ordering defect
  - Operator amendment 2026-05-18T~16:30 EDT.
- **`5bf86443`** — Refresh external review snapshot for 4b51058a
- **`4b51058a`** — Refresh external review snapshot for 50039a1b
- **`50039a1b`** — Phase 0.4: Sync canonical GuardIR extraction plan
  - Operator-approved plan update (2026-05-18T~16:00 EDT via ChatGPT review chain):
  - - Replace stale 558-line plan-intake version with 879-line current text
  - - Correct trunk root from d92dc2ff (auto ReviewSnapshot artifact) to 92ef4032 (actual UNREVIEWED PRESERVATION SNAPSHOT content commit)
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

- open governance findings: 27

### Startup advisories
- no_push_needed: clean_worktree

### Stale warnings
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/process/cleanup.py`): dogfood.command.process-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
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

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-5354597ee869` binds this file to HEAD `1efa1407ab5b`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
