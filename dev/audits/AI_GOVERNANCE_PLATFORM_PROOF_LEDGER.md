# AI Governance Platform Proof Ledger

**Status**: active reference  |  **Last updated**: 2026-04-03 | **Owner:** Tooling/control plane/product architecture

Reference-only proof and differentiation ledger for the `MP-377` AI governance
platform work.

This file is not execution authority. Canonical execution state remains in:

- `dev/active/MASTER_PLAN.md`
- `dev/active/ai_governance_platform.md`
- `dev/active/platform_authority_loop.md`
- `dev/active/portable_code_governance.md`

Use this ledger to keep one maintained, repo-backed answer to these questions:

- What is already proved in this repo today?
- What is only partially proved or still open?
- What evidence exists for cross-repo adoption?
- How is this different from the current market without overstating uniqueness?
- Which artifacts, ledgers, tests, commands, commits, and changed files back the claim?

## Upkeep Contract

Update this file in the same change when any of the following happens:

- the claimed POC scope changes
- a new contract surface becomes executable
- a cross-repo proof claim changes
- a proof command, artifact path, or ledger owner changes
- a new benchmark, adoption run, or audit materially changes the evidence
- a market-comparison claim materially changes

Do not hand-edit machine ledgers here. Keep the underlying evidence in the
repo-owned artifacts and update this file as the human-facing index over them.

When this ledger changes, update the owning plan/docs in the same change as
needed:

- `dev/active/ai_governance_platform.md` for product-scope proof claims
- `dev/active/platform_authority_loop.md` for startup/runtime/evidence closure
- `dev/active/portable_code_governance.md` for cross-repo adoption proof
- `dev/guides/AI_GOVERNANCE_PLATFORM.md` when the durable thesis or
  differentiation wording changes
- `dev/scripts/README.md` when the proof command surface changes

## Current Claim Boundary

What is honestly proved now:

- a self-hosting repo-local governance runtime exists in code
- startup, work intake, review state, and governed commit/push use typed
  contracts and machine-readable projections
- fail-closed startup/review/checkpoint behavior is live, not just planned
- the platform already has real cross-repo pilot evidence for `probe-report`
  and routed `check` adoption scans

What is not honestly proved yet:

- full extracted product closure
- broad any-repo startup/push portability
- completion of the authority-loop closure
- a finished market moat around raw coding-agent primitives

## Claim Matrix

| Claim | Status | Evidence anchors | Next gate |
|---|---|---|---|
| Self-hosting repo-local AI governance runtime exists in code today | proved | `dev/scripts/devctl/runtime/project_governance_contract.py`, `dev/scripts/devctl/runtime/startup_context.py`, `dev/scripts/devctl/runtime/work_intake.py`, `dev/scripts/devctl/runtime/review_state_models.py` | keep the typed/runtime surfaces green under `MP-377` |
| Startup, review, and governed commit/push use typed contracts instead of prompt-only policy | proved | `dev/scripts/devctl/runtime/startup_context.py`, `dev/scripts/devctl/runtime/reviewer_runtime_models.py`, `dev/scripts/devctl/runtime/action_contracts.py`, `dev/scripts/devctl/runtime/remote_commit_pipeline_models.py` | finish the remaining authority-loop closure tracked in `dev/active/platform_authority_loop.md` |
| Fail-closed startup/review/checkpoint behavior is live, not just planned | proved | `python3 dev/scripts/devctl.py startup-context --format summary`, `python3 dev/scripts/devctl.py review-channel --action doctor --terminal none --format json`, `dev/reports/review_channel/latest/review_state.json` | keep the fail-closed receipts stable as bridge/projection authority narrows |
| Cross-repo adoption proof exists for guard/probe/adoption-scan paths | proved but scoped | `dev/reports/audits/2026-03-14-portable-governance-pilot-rerun.md`, `dev/reports/audits/portable_governance_pilot_2026-03-14.json`, `dev/reports/governance/external_pilot_findings.jsonl`, `dev/active/portable_code_governance.md` | extend the proof from adoption-scan surfaces into stronger startup/push portability |
| External auditors using GitHub-connected review flows or ChatGPT-style repo review can audit the system from tracked docs and evidence surfaces | supported now | this ledger, `dev/guides/AI_GOVERNANCE_PLATFORM.md`, `dev/guides/PORTABLE_CODE_GOVERNANCE.md`, `dev/audits/2026-03-24-chatgpt-integration-intake.md` | keep routing accepted external findings into owner plans instead of leaving them as standalone audit prose |
| Broad any-repo startup/push portability is complete | not proved | `dev/active/platform_authority_loop.md`, `dev/active/portable_code_governance.md` | close repo-pack / Step-0 / push-authority portability gaps |

## Current Proof Snapshot

Baseline observed from this checkout on 2026-04-03:

| Signal | Current evidence |
|---|---|
| Branch | `feature/governance-quality-sweep` |
| Bootstrap graph | `2406` source files, `69` guards, `25` probes, `19` active plans, `53023` edges |
| `startup-context --format summary` | `action=checkpoint_before_continue`, `reason=dirty_and_untracked_budget_exceeded`, exit non-zero |
| `review-channel --action doctor --terminal none --format json` | `attention.status=bridge_contract_error`, typed `reviewer_runtime`, typed `commit_pipeline`, typed `push_decision` present |
| Focused validation run | `67` `startup_context` tests passed, `17` `work_intake` / `project_governance` tests passed, `16` `action_contracts` / `governed_executor` tests passed |

This is important because the current repo state is not merely describing
fail-closed governance. It is actively enforcing it.

## Repo-Backed POC Evidence

### 1. Typed governance and startup authority

Executable surfaces:

- `dev/scripts/devctl/runtime/project_governance_contract.py`
- `dev/scripts/devctl/runtime/startup_context.py`
- `dev/scripts/devctl/runtime/work_intake_models.py`
- `dev/scripts/devctl/runtime/work_intake.py`
- `dev/scripts/devctl/tests/runtime/test_project_governance.py`
- `dev/scripts/devctl/tests/runtime/test_startup_context.py`
- `dev/scripts/devctl/tests/runtime/test_work_intake.py`

What this proves:

- repo identity, repo-pack, path roots, plan/doc registries, enabled checks,
  push-enforcement, and startup order are real runtime objects
- startup emits a bounded `StartupContext` with a typed `WorkIntakePacket`
  rather than relying only on prose rereads
- the startup path has test coverage and live fail-closed behavior

### 2. Typed review/runtime state

Executable surfaces:

- `dev/scripts/devctl/runtime/review_state_models.py`
- `dev/scripts/devctl/runtime/reviewer_runtime_models.py`
- `dev/scripts/devctl/commands/review_channel/status.py`
- `dev/scripts/devctl/commands/review_channel/doctor_support.py`
- `dev/reports/review_channel/latest/review_state.json`
- `dev/reports/review_channel/latest/commit_pipeline.json`
- `dev/reports/review_channel/latest/compact.json`
- `dev/reports/review_channel/latest/latest.md`

What this proves:

- reviewer/implementer/operator state is represented in typed runtime models
- review-channel status and doctor project machine-readable runtime truth
- the system can surface unhealthy state honestly instead of treating stale or
  contradictory reviewer data as green

### 3. Governed commit/push execution

Executable surfaces:

- `dev/scripts/devctl/runtime/action_contracts.py`
- `dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`
- `dev/scripts/devctl/commands/vcs/governed_executor.py`
- `dev/scripts/devctl/tests/vcs/test_governed_executor.py`

What this proves:

- the repo has a typed `TypedAction -> ActionResult` path for staging,
  approval, commit, push, and recovery
- remote commit intent, approval, and recovery are not limited to prose or raw
  shell steps

### 4. Multi-surface backend direction

Executable and documented surfaces:

- `dev/active/ai_governance_platform.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`
- `app/operator_console/README.md`
- `app/operator_console/views/main_window.py`

What this proves:

- the repo is not only a terminal wrapper
- the target architecture is one backend consumed by CLI, PyQt6 desktop
  console, overlay/TUI, and phone/mobile surfaces
- the Operator Console is explicitly documented as a thin wrapper over repo
  state and `devctl`, not a second hidden backend

## Cross-Repo Adoption Evidence

Current supporting proof is real but scoped.

Primary evidence:

- `dev/reports/audits/2026-03-14-portable-governance-pilot-rerun.md`
- `dev/reports/audits/portable_governance_pilot_2026-03-14.json`
- `dev/reports/governance/external_pilot_findings.jsonl`
- `dev/reports/data_science/latest/summary.md`
- `dev/active/portable_code_governance.md`

What this currently proves:

- `governance-bootstrap`, `probe-report --repo-path --adoption-scan`, and
  `check --profile ci --repo-path --adoption-scan` have been run against other
  local repos without core-engine crashes
- imported external findings are preserved in a repo-owned ledger instead of
  one-off notes
- the repo already tracks external-finding corpus size, repo counts, and
  adjudication coverage in the data-science surface

Current honest limitation:

- startup/push proof is still incomplete for arbitrary repos because
  `startup-context` does not yet provide the fully target-local Step-0 proof
  path from the engine checkout alone

## External Audit Consumers

Use this ledger as the first maintained handoff surface for:

- GitHub-side reviewers who need one tracked place to verify what is already
  proved versus still open
- ChatGPT Pro or other repo-connected external reviewers who can read the repo
  but should not invent their own authority hierarchy
- internal/external developers auditing whether the platform really improves
  code quality across repos

Recommended read order:

- `dev/guides/AI_GOVERNANCE_PLATFORM.md` for the durable system thesis
- this ledger for the live claim boundary, evidence map, and proof commands
- `dev/active/portable_code_governance.md` plus
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md` for the external-repo proof bar,
  pilot corpus, and evaluation framework
- `dev/audits/2026-03-24-chatgpt-integration-intake.md` as proof that an
  external architecture review can find genuine gaps, get reswept against the
  live codebase, and then be routed into tracked owner plans instead of
  remaining free-floating audit commentary
- `dev/integrations/EXTERNAL_REPOS.md` when the audit needs the federated repo
  set and pinned upstream references that informed reuse/adoption work

## Evidence Map

### Canonical machine ledgers

| Surface | Path | Why it matters |
|---|---|---|
| command telemetry | `dev/reports/audits/devctl_events.jsonl` | proves what commands ran, when, and with what success/failure shape |
| governance adjudication | `dev/reports/governance/finding_reviews.jsonl` | proves reviewed findings, cleanup rate, false-positive rate, and systemic absorption |
| external adoption findings | `dev/reports/governance/external_pilot_findings.jsonl` | preserves imported cross-repo findings instead of relying on narrative summaries |

### Canonical human projections over those ledgers

| Surface | Path | Why it matters |
|---|---|---|
| governance review summary | `dev/reports/governance/latest/review_summary.md` | current scoreboard for findings fixed, open, deferred, and by-check cleanup |
| data science summary | `dev/reports/data_science/latest/summary.md` | current telemetry rollup, watchdog metrics, and external-finding corpus counts |
| probe summary | `dev/reports/probes/latest/summary.md` | current review-probe risk picture for the active tree |
| review-channel doctor/status bundle | `dev/reports/review_channel/latest/` | current typed runtime truth for live reviewer/session/commit-pipeline state |

### Audit and proof companions

| Surface | Path | Why it matters |
|---|---|---|
| portable pilot rerun | `dev/reports/audits/2026-03-14-portable-governance-pilot-rerun.md` | narrative audit of the current external-repo proof slice |
| active product plan | `dev/active/ai_governance_platform.md` | canonical product-scope proof framing under `MP-377` |
| authority-loop plan | `dev/active/platform_authority_loop.md` | canonical startup/runtime/evidence closure path |
| portable adoption plan | `dev/active/portable_code_governance.md` | canonical external-repo/adopter proof path |

## Market Review

As of 2026-04-03, the raw primitives are no longer unique:

- OpenAI Codex now markets coding-agent execution, parallel work, built-in
  worktrees, AGENTS.md guidance, and verifiable evidence surfaces
- Claude Code documents read/edit/run behavior, hooks, subagents, multiple
  surfaces, and parallel work
- Continue covers agent workflows across Mission Control, terminal, and CI/CD
- Aider covers terminal pair programming, repo maps, git integration, and
  lint/test repair loops

This repo should not claim novelty at the level of "AI coding agent in a
terminal."

What is still differentiated here is the composition:

- repo-owned typed authority instead of prompt-only policy
- bounded startup and work-intake packets instead of unrestricted repo
  recrawling as startup authority
- explicit reviewer/implementer/operator separation with typed runtime state
- fail-closed checkpoint/push gating
- packetized approval and review receipts
- a documented plan to keep all frontends on one backend instead of letting
  each surface invent its own control plane

## Proof Log

- 2026-04-03: Maintained reference ledger created and linked from the active
  `MP-377` product plan and the durable platform guide so the repo has one
  tracked answer to "what is proved now?" without promoting chat analysis into
  execution authority.
- 2026-04-03: Current bootstrap receipt refreshed via
  `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`.
  Snapshot: `dev/reports/graph_snapshots/963566eda357a8694a8e81c910df7a17f5801917_20260404T000136Z.json`.
  Current graph counts: `2411` source files, `69` guards, `25` probes,
  `19` active plans, `53166` edges.
- 2026-04-03: Current startup receipt refreshed via
  `python3 dev/scripts/devctl.py startup-context --format summary`.
  Result: exit non-zero, `action=continue_editing`, `reason=review_pending`,
  `blockers=startup_authority`, `ahead_of_upstream_commits=1`. This keeps the
  proof honest: the repo is still enforcing startup/review authority instead
  of pretending the branch is clean.
- 2026-04-03: Focused self-hosting validation rerun already recorded for the
  typed startup/governance/action surfaces: `67` `startup_context` tests,
  `17` `work_intake` / `project_governance` tests, and `16`
  `action_contracts` / `governed_executor` tests passed.
- 2026-03-24 to 2026-03-25: External ChatGPT architecture review was captured
  in `dev/audits/2026-03-24-chatgpt-integration-intake.md`, reswept against
  the live codebase, and split into "already exists" versus genuine gaps with
  tracked owner-plan routing. This is evidence that outside review can improve
  the system without becoming shadow authority.
- 2026-03-14: Corrected portable-governance pilot rerun established the current
  cross-repo proof baseline in
  `dev/reports/audits/2026-03-14-portable-governance-pilot-rerun.md` and
  `dev/reports/audits/portable_governance_pilot_2026-03-14.json`.

## Canonical Claim Language

Use claims like these:

- "This repo already proves a self-hosting POC of a repo-local AI governance
  runtime."
- "The unusual part is not the raw coding-agent primitive. It is the typed
  governance/control-plane shape assembled around it."
- "The system treats AI as the implementation/search layer, not the authority
  layer."
- "Cross-repo proof exists for adoption-scan guard/probe paths, but broad
  startup/push portability is still an explicit open gate."

Do not claim:

- "Nobody else has built anything similar."
- "The full extracted product is already proved."
- "Any-repo startup/push portability is complete."

## Current Proof Commands

These are the shortest live commands to rerun when updating this ledger:

```bash
python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md
python3 dev/scripts/devctl.py startup-context --format summary
python3 dev/scripts/devctl.py review-channel --action doctor --terminal none --format json
python3 dev/scripts/devctl.py governance-review --format md
python3 dev/scripts/devctl.py data-science --format md
python3 dev/scripts/devctl.py probe-report --format md
python3 dev/scripts/devctl.py check --profile ci
```

For cross-repo proof, use the policy/adoption surfaces already documented in
`dev/scripts/README.md`, especially:

```bash
python3 dev/scripts/devctl.py governance-bootstrap --target-repo /tmp/copied-repo --format md
python3 dev/scripts/devctl.py check --profile ci --repo-path /tmp/copied-repo --adoption-scan --format md
python3 dev/scripts/devctl.py probe-report --repo-path /tmp/copied-repo --adoption-scan --format md
```

## Ongoing Append Rule

When future proof changes land, append concise dated bullets to the owning
plans and refresh this ledger so it remains the easiest maintained answer to:

- what is proved
- how it is proved
- where the evidence lives
- what still blocks the next claim

Each new proof-log entry should include, when available:

- date and owning scope (`MP-377`, `MP-376`, or a narrower owner)
- branch and/or commit hash
- the changed files or runtime surfaces that matter to the claim
- the validating commands and artifact paths
- the result, limitation, and next gate

Keep this file as the maintained index. Keep the machine truth in the typed
contracts, repo-owned artifacts, tests, ledgers, and active plans.
