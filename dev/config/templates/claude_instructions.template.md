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

## Governance capabilities (available during work)

- Probe findings may carry `ai_instruction` with targeted fix guidance. Treat
  it as the default repair plan unless the current slice proves it wrong.
- `decision_mode` gates action: `auto_apply` means fix directly,
  `approval_required` means explain and wait, and `recommend_only` means
  suggest without mutating.
- Record adjudicated outcomes with `python3 dev/scripts/devctl.py governance-review --record ...`; add `--guidance-id ... --guidance-followed true|false` when guided remediation was involved.
- `startup-context` and other shared context packets may already include
  recent finding verdicts, quality recommendations, watchdog digests, and
  command-reliability summaries. Prefer those packet fields over ad hoc raw-
  ledger reads when they are present.
- `context-graph --mode bootstrap` auto-saves a `ContextGraphSnapshot` under
  `dev/reports/graph_snapshots/`; use `--save-snapshot` on other
  `context-graph` modes when a slice needs a durable baseline.
- For "which tool should I run now?", use `{{development_doc}}` (`What checks
  protect us`, `After file edits`) and the command table in
  `{{scripts_readme_doc}}` before inventing a narrower workflow.

## Mode-aware review-channel bootstrap

- If repo-root `bridge.md` is absent, or `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
  reports `reviewer_mode` as `single_agent`, `tools_only`, `paused`, or `offline`,
  do not assume a live Codex review loop. Use the normal `AGENTS.md` + active-plan
  flow unless the operator explicitly reactivates dual-agent mode.
- If repo-root `bridge.md` is present and `reviewer_mode` is
  `active_dual_agent`, treat the bridge as the live reviewer/coder authority:
  read `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`,
  and `Last Reviewed Scope` before acting, then keep polling the bridge instead of
  waiting for the operator to restate the process in chat.
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
  `done from my side`, or `Codex should review` and park. Keep executing the
  current bounded slice or post one concrete blocker in `Claude Questions`.

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
