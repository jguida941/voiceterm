# Claude Instructions

This file is generated from the `{{repo_pack_id}}` repo-pack surface policy.
The canonical SDLC + documentation policy lives in `{{process_doc}}`. Read it
and follow it for any non-trivial task. Keep AI notes local-only (this file is
gitignored).

## Bootstrap (read on every session start)

{{bootstrap_steps}}

- Before coding or validating a non-trivial slice, also read
  `dev/guides/DEVELOPMENT.md` and `dev/scripts/README.md` so the routed check
  stack and failure-recovery rules stay aligned with the maintainer flow.
- In `active_dual_agent` mode, also read `dev/guides/DEVCTL_AUTOGUIDE.md`
  before acting so the live review-channel/tandem workflow matches the
  repo-owned command surface instead of chat memory.

## Platform scope

- Treat this repo's product files as one adopter/client over a portable
  governance platform unless the active plan explicitly scopes the work to a
  repo-pack or product-integration surface.
- In shared governance/runtime/startup/review-channel code, resolve repo-local
  paths, plan docs, and bridge surfaces through `startup-context`,
  `ProjectGovernance`, repo-pack policy, or typed runtime state. Do not
  hardcode repo names, `bridge.md`, or `dev/...` literals back into portable
  layers.
- If a markdown bridge is enabled, treat it as a repo-pack-owned compatibility
  projection over typed review state unless the active plan explicitly says
  the migration is incomplete and that bridge prose is still temporary live
  authority for the current repo.

## Governance capabilities (available during work)

- Probe findings may carry `ai_instruction` with targeted fix guidance. Treat
  it as the default repair plan unless the current slice proves it wrong.
- `decision_mode` gates action: `auto_apply` means fix directly,
  `approval_required` means explain and wait, and `recommend_only` means
  suggest without mutating.
- Record adjudicated outcomes with `python3 dev/scripts/devctl.py governance-review --record --signal-type probe|guard|audit --check-id <id> --verdict <verdict> --path <repo-path> --finding-class <class> --recurrence-risk <risk> --prevention-surface <surface> --format md`; add `--guidance-id ... --guidance-followed true|false` when guided remediation was involved.
- `startup-context` now carries compact governance, reviewer gate, advisory
  action/reason, and a bounded `WorkIntakePacket` with typed continuity and
  routing hints. `context-graph --mode bootstrap` and escalation packets may
  additionally carry recent probe/governance/watchdog/reliability summaries
  when those artifacts exist. Prefer actual packet fields over assumptions.
- `context-graph --mode bootstrap` auto-saves a `ContextGraphSnapshot` under
  `dev/reports/graph_snapshots/`; use `--save-snapshot` on other
  `context-graph` modes when a slice needs a durable baseline, and use
  `python3 dev/scripts/devctl.py context-graph --mode diff --from previous --to latest --format md`
  when the slice needs a typed delta over saved snapshots.
- For "which tool should I run now?", use `{{development_doc}}` (`What checks
  protect us`, `After file edits`) and the command table in
  `{{scripts_readme_doc}}` before inventing a narrower workflow.

## Checkpoint / Review / Push Contract

- After any commit/checkpoint, rerun
  `python3 dev/scripts/devctl.py startup-context --format md`. Do not stop at
  a clean worktree alone.
- Treat `push_decision` as the canonical next remote-action state machine:
  `await_checkpoint`, `await_review`, `run_devctl_push`, `no_push_needed`.
- When `push_decision` is `run_devctl_push`, the next governed step is
  `python3 dev/scripts/devctl.py push --execute`. Do not substitute raw
  `git push`.
- When `push_decision` is `await_review`, pause editing/push work, refresh the
  repo-owned review state, and rerun `startup-context` after reviewer-owned
  acceptance changes.
- In `single_agent`, `tools_only`, `paused`, or portable adopted repos with no
  live dual-agent bridge, the same `startup-context` / `push_decision` contract
  still applies. Push readiness must not depend on bridge prose existing.

## Platform Boundary

- The long-term product direction is a portable AI-governance platform. In
  this repo, `{{product_name}}` is one client/integration of that platform,
  not permission to treat repo-local paths or product defaults as universal.
- In portable/runtime/tooling layers, resolve docs, report roots, bridge
  files, startup order, and review-state paths through governed repo state
  (`ProjectGovernance`, repo pack metadata, repo policy, typed runtime
  contracts) instead of hardcoding `bridge.md`, `dev/active/*`,
  `dev/reports/*`, repo names, or one client's defaults.
- If a behavior is intentionally repo-local or client-local, keep that scope
  explicit in code, docs, and tests. If the behavior should work on arbitrary
  repos, empty repos, or already-built repos, treat hardcoded local literals
  as a bug or compatibility seam to remove.

## Task Router Quick Map

Canonical task-router authority lives in
`dev/scripts/devctl/governance/task_router_contract.py`. This quick map is
rendered from that typed router.

{{task_router_block}}

- If the touched scope is mixed or unclear, run
  `python3 dev/scripts/devctl.py check-router --format md` before narrowing
  the lane yourself.

## Mode-aware review-channel bootstrap

- If the repo's configured markdown bridge projection is absent, or
  `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
  reports `reviewer_mode` as `single_agent`, `tools_only`, `paused`, or `offline`,
  do not assume a live Codex review loop. Use the normal `AGENTS.md` + active-plan
  flow unless the operator explicitly reactivates dual-agent mode.
- If a bridge projection is present and `reviewer_mode` is `active_dual_agent`,
  treat that projection as the live reviewer/coder surface for the current
  repo-pack. Read `Poll Status`, `Current Verdict`, `Open Findings`,
  `Current Instruction For Claude`, and `Last Reviewed Scope` before acting,
  but prefer typed `review_state.json` / `current_session` fields whenever a
  current-status question can be answered without rereading prose.
- On each repoll, read `Last Codex poll` / `Poll Status` first. If the reviewer-owned
  timestamp and the reviewer-owned sections are unchanged after you already finished
  the current bounded work, treat that as a live wait state, wait on the documented
  cadence, and reread the full reviewer-owned block instead of hammering one fixed
  offset or one cached line range.
- If reviewer-owned bridge state says `hold steady`, `waiting for reviewer promotion`,
  `Codex committing/pushing`, or equivalent wait-state language, stay in polling mode.
  Do not self-promote side work or mine unchecked plan items until a reviewer-owned
  bridge section changes.
- If `Current Instruction For Claude` still contains active work and the reviewer
  has not written an explicit wait state, do not say `instruction unchanged`,
  `done from my side`, `No change. Continuing.`, or `Codex should review` and
  park. Keep executing the current bounded slice or post one concrete blocker
  in `Claude Questions`.
- If the current instruction is still active and the reviewer has not written
  an explicit wait state, every `Claude Status` / `Claude Ack` update must
  name concrete files, subsystems, findings, or one concrete blocker/question.
  Low-information polling/completion notes are contract violations, not valid
  active-work state.
- Do not use raw shell sleep loops such as `sleep 60` or
  `bash -lc 'sleep 60'` to emulate polling. Use
  `python3 dev/scripts/devctl.py review-channel --action implementer-wait --reason awaiting-reviewer --terminal none --format json`
  only when reviewer-owned state is explicitly in a wait posture.

## Mode-aware validation starter

- In `active_dual_agent`, start by reading
  `python3 dev/scripts/devctl.py quality-policy --format md`, then use
  `python3 dev/scripts/devctl.py tandem-validate --format md` as the canonical
  post-edit validator. Do not substitute a hand-written mini-checklist.
- In `single_agent` or `tools_only`, use the same routed bundles/checks
  (`check --profile ci`, `probe-report`, docs-check, path/risk add-ons) and
  record the live mode with
  `python3 dev/scripts/devctl.py review-channel --action reviewer-heartbeat --reviewer-mode <mode> --reason <why> --terminal none --format md`.
  Use `reviewer-checkpoint` only after a real review pass.
- For architecture, policy, template, or control-plane changes, read the full
  output from `quality-policy`, `check --profile ci`, and the applicable docs
  checks end to end before claiming success. Do not grep only for `ok:` or
  `step failed`.
- If generated instruction surfaces may have changed, run
  `python3 dev/scripts/devctl.py render-surfaces --write --format md` and
  reread the generated output before continuing.

## Project: {{product_name}} ({{repo_name}})

- **What**: {{project_summary}}
- **Rust source**: `{{rust_source}}`
- **Python tooling**: `{{python_tooling}}`
- **Guard scripts**: `{{guard_scripts}}`
- **MSRV**: {{msrv}}
- **Branches**: {{branch_policy}}

## Source-of-truth quick map

| What | Where |
|---|---|
| Execution state | `{{execution_tracker_doc}}` |
| Active doc registry | `{{active_registry_doc}}` |
| SDLC / process | `{{process_doc}}` |
| Architecture | `{{architecture_doc}}` |
| Build/test/release | `{{development_doc}}` |
| devctl commands | `{{scripts_readme_doc}}` |
| CLI flags | `{{cli_flags_doc}}` |
| CI workflows | `{{ci_workflows_doc}}` |

## Key commands

```bash
{{key_commands_block}}
```

## Mandatory post-edit verification (blocking)

{{post_edit_verification_intro}}

{{post_edit_verification_steps}}

{{post_edit_verification_done_criteria}}

## Guard-enforced limits (CI will block violations)

{{guard_limits_block}}

## User preferences

{{user_preferences_block}}
