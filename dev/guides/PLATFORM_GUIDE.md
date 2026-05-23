# GuardIR Platform Guide

**Status**: active reference  |  **Last updated**: 2026-05-22 | **Owner:** Tooling/control plane/product architecture

> GuardIR is a repo-local AI-governance platform that decides whether AI-assisted
> work is admissible under typed plan, policy, and evidence state. This guide
> is the operational reference: when to run what, why each step exists, what
> proof it leaves behind, and which files are authority versus projection.

### Document metadata (machine-readable)

| Field | Value |
|---|---|
| `contract_id` | `PlatformGuide` |
| `schema_version` | `1` |
| `audiences` | `human_developer`, `ai_agent` |
| `authority_tier` | `4` (reference; see `dev/guides/SYSTEM_MAP.md` §0.7) |
| `projection_only` | `true` — points at typed state; never replaces it |
| `source_of_truth` | `dev/state/plan_index.jsonl`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md` |
| `tracked_under` | `MP-GUARDIR-V4-PHASE-0-6-E-INSTRUCTION-SURFACE-USABILITY-S1`, `MP-377` |

This guide explains the AI governance platform architecture in developer terms:
what the platform is, why it exists, how its state model works, how to use it
in day-to-day engineering, and what is already implemented versus still being
proved under `MP-377`.

Use this guide for the durable architecture and operating model. Use
`dev/active/ai_governance_platform.md` for current execution state and roadmap
tracking, `dev/scripts/README.md` for the command reference, and
`dev/guides/DEVELOPMENT.md` for the exact post-edit check inventory.

## How To Read This Guide

> Pick your audience. Each path lands you at the section that answers your
> first question without making you scroll the whole file.

### For human developers (first time)

1. Read [What This Is](#what-this-is) and [Why It Exists](#why-it-exists) to
   get the thesis in two minutes.
2. Read [Boot Sequence](#boot-sequence) to run your first session.
3. Read [Developer Workflows](#developer-workflows) for the day-to-day path.
4. Use [Command Map](#command-map) and [Companion Docs Map](#companion-docs-map)
   as lookup tables.

### For human developers (returning)

Skip to [Boot Sequence](#boot-sequence), then jump to the workflow that matches
your task class — edit, commit, push, packet-post, surface-render, or adopt.

### For AI agents (Claude, Codex, peer sessions)

Go directly to [AI Agent Quick Reference](#ai-agent-quick-reference). It is the
agent-addressed section. Authority is still typed state; this guide is tier-4
reference and never overrides `dev/state/`, contracts, receipts, or guards.

### Diátaxis quadrant map

This guide deliberately mixes the four documentation modes from the
[Diátaxis framework](https://diataxis.fr/start-here/). Each section is labeled
in the heading so you can grep for the genre you need.

| Quadrant | Serves | Sections here |
|---|---|---|
| **Tutorial** | learning by doing | (Not included — see `QUICK_START.md` for VoiceTerm; platform tutorial is roadmap.) |
| **How-to** | doing a known task | [Boot Sequence](#boot-sequence), [Developer Workflows](#developer-workflows), [Extending The Platform](#extending-the-platform) |
| **Reference** | austere lookup | [Command Map](#command-map), [Slash Commands And Skills](#slash-commands-and-skills), [Operational: Bundles, Hooks, And `check-router`](#operational-bundles-hooks-and-check-router), [Companion Docs Map](#companion-docs-map), [Glossary](#glossary) |
| **Explanation** | understanding why | [What This Is](#what-this-is), [Why It Exists](#why-it-exists), [The Compiler Model](#the-compiler-model), [Architecture Layers](#architecture-layers), [The Typed State Spine](#the-typed-state-spine), [Review Channel And Multi-Agent Work](#review-channel-and-multi-agent-work), [Anti-Patterns And Stop Signals](#anti-patterns-and-stop-signals) |

## Contents

- [How To Read This Guide](#how-to-read-this-guide)
- [AI Agent Quick Reference](#ai-agent-quick-reference)
- [What This Is](#what-this-is)
- [Why It Exists](#why-it-exists)
- [How To Position It](#how-to-position-it)
- [Current Status](#current-status)
- [The Compiler Model](#the-compiler-model)
- [Architecture Layers](#architecture-layers)
- [The Typed State Spine](#the-typed-state-spine)
- [Companion Docs Map](#companion-docs-map)
- [Boot Sequence](#boot-sequence)
- [Review Channel And Multi-Agent Work](#review-channel-and-multi-agent-work)
- [Slash Commands And Skills](#slash-commands-and-skills)
- [Guards, Probes, And Findings](#guards-probes-and-findings)
- [Operational: Bundles, Hooks, And `check-router`](#operational-bundles-hooks-and-check-router)
- [Developer Workflows](#developer-workflows)
- [Extending The Platform](#extending-the-platform)
- [Anti-Patterns And Stop Signals](#anti-patterns-and-stop-signals)
- [Design Rules](#design-rules)
- [Command Map](#command-map)
- [Glossary](#glossary)
- [Surface Provenance](#surface-provenance)

## AI Agent Quick Reference

> You are an AI agent reading this guide. This section is written in imperative
> second person and addressed to you directly. Authority is typed state
> (`dev/state/`, contracts, receipts, guards). This section is projection.
> When the two disagree, typed state wins.

### Boot in three commands

Run these in order at the start of every session.

```bash
# 1. Compose the session orientation packet (StartupContext + SessionResume +
#    review-channel + context-graph). This is the ONLY sanctioned entry.
python3 dev/scripts/devctl.py session \
  --role observer \
  --include-review-status always \
  --format json

# 2. Get the next typed development command. Do not invent next steps.
python3 dev/scripts/devctl.py develop next --actor agent --format md

# 3. Before any final response or TASK_COMPLETE, run the gate. Treat denial
#    as continuation work, not permission to summarize and exit.
python3 dev/scripts/devctl.py develop next --actor agent \
  --enforce-final-response-gate --format json
```

The individual `startup-context`, `session-resume`, `review-channel status`,
and `context-graph` commands are **diagnostic fallback only** — use them when
`devctl session` is unavailable, never as the primary chain.

### What to do when the gate denies final response

| Gate field | Meaning | What you do |
|---|---|---|
| `final_response_allowed=false` | More work required before stopping | Run the `next_required_command` and continue the loop |
| `continuation_state=must_continue` | Active continuation goal pending | Address the goal; do not summarize |
| `next_required_command` present | Specific command must run first | Run that command verbatim, do not paraphrase |
| `final_response_allowed=true` and `continuation_state=can_stop` | OK to wrap up | Emit final response or `TASK_COMPLETE` |

### Slash commands you can post (project-defined)

| Slash | Wrapped devctl call | When to invoke |
|---|---|---|
| `/develop` | `devctl develop <action>` | Status, next, show, watch, ingest-plan |
| `/goal` | `devctl develop --post-continuation-anchor` | Set the active continuation target |
| `/handshake` | `review-channel --action post --kind peer_session_handshake` | Coordinate with a peer agent |
| `/agent-spawn` | `review-channel --action recover` (typed) | Recover a crashed agent or spawn into a typed role |
| `/bypass` | `devctl bypass grant --scope edit-only` | Request scoped edit-only authority (never raw bypass) |
| `/check-it` | `devctl develop --post-task-produced` | Hand reviewers the exact verification command |
| `/session-log` | `devctl develop --log-progress` | Record session milestone as typed progress (not prose) |
| `/archive-evidence` | `devctl develop --post-evidence --target-kind artifact` | Mark an artifact as durable evidence |
| `/typed-remote-control` | `devctl remote-control enter|heartbeat` | Govern Claude's built-in /remote-control attach |

Every slash command is a thin typed adapter to one `devctl` call. Authority
lives in the typed backend, never in the slash definition. The `allowed-tools:`
frontmatter in each `.claude/commands/*.md` file scopes the exact CLI pattern
the slash may run — that is your sandbox boundary.

Skills (the things named in your system reminders like `/check-it`, `/loop`,
`/verify`, `/review`) come from the **Claude Code harness**, not from this
repo. Project-defined skills: zero. If you cannot find a skill in this repo's
`.claude/skills/` directory, do not invent one — it is harness-provided.

### Files that are authority

| Tier | Files | Use |
|---|---|---|
| 1 | `dev/state/plan_index.jsonl`, `dev/state/contract_registry.jsonl`, `dev/state/transition_modules.jsonl`, all other `dev/state/*.jsonl`, ingested receipts | Durable typed authority. Read these before acting. |
| 1 | `dev/reports/feature_proof_receipts/`, `dev/reports/push/latest_push_report.json` | Per-SHA evidence the next session can replay |
| 2 | `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, `dev/active/ai_governance_platform.md`, `dev/active/review_channel.md`, `dev/active/review_probes.md` | Maintained projections over tier 1. Read for navigation. |

### Files that are projections (read; never trust as authority)

- `AGENTS.md`, `CLAUDE.md` — generated boot cards
- `bridge.md` — deprecated compatibility projection (may be stale)
- `dashboard` / `mobile-status` / `phone-status` output
- This file, `PLATFORM_GUIDE.md`
- Every `.md` under `dev/guides/`
- Generated slash command templates

If a projection disagrees with tier 1 typed state, **tier 1 wins**. Re-render
the projection with `devctl render-surfaces --write --format md`.

### Commands you must never invent

- Any `devctl` subcommand not listed by `python3 dev/scripts/devctl.py --help`
- Raw `git push` (blocked by pre-push hook; route through `devctl push --execute`)
- Raw `--approval-mode trusted` without an active `BypassReceipt`
- A parallel finding system, lifecycle, or controller path
- A new typed contract without entry in `dev/state/contract_registry.jsonl`
- An "amend" of a published commit (always create a new commit)

### When you must stop

Stop immediately and surface the state to the operator if you see any of:

- `startup-context.action` requests `checkpoint`, `repair`, or `stop`
- `final.safe_to_continue=false` in the session orientation packet
- The final-response gate keeps denying after the next command runs
- A guard fails closed and the fix is not in the active plan row scope
- You are about to mutate a `preserve/*` branch (immutable evidence locker)
- Your session id no longer matches the live session in `review-channel status`

### One-line fixes for common surprises

| Symptom | First-line response |
|---|---|
| "Pre-commit hook blocked commit" | Read its message; the offending guard is named; fix root cause, don't `--no-verify` |
| "Active plan sync check failing" | Run `devctl render-surfaces --write --format md` |
| "Stale packet looks live" | Verify `source_session_id` matches the live session before acting on it |
| "Can't find the next step" | Run `devctl develop next --actor agent --format md` — never guess |
| "Slash command not recognized" | It's a harness skill, not a repo command — see the system reminder list |
| "Push blocked" | Read `dev/reports/push/latest_push_report.json`; do not bypass |

## What This Is

GuardIR is a repo-local governance and admissibility layer for AI-assisted
software development.

It is not primarily a coding agent. Coding agents generate, edit, review, or
automate code. GuardIR is the repo-owned layer that decides whether AI-produced
work is allowed to advance under the repository's plan, policy, lifecycle
state, review history, guard evidence, and typed runtime state.

The practical output is not just a code diff. A governed change should also
leave evidence:

- the work scope that was active
- the policy and plan authority that applied
- the checks that ran
- the findings and decisions that mattered
- the packet or approval lifecycle, when collaboration was involved
- the action result and run receipts that future sessions can replay

VoiceTerm is the first product adopter and proof environment. The platform
target under `MP-377` is broader: reusable governance machinery that can be
installed into other repositories through repo packs, typed policy, and
bounded runtime contracts. VoiceTerm-specific defaults belong in VoiceTerm's
repo pack or product integration layer, not in portable platform code.

## Why It Exists

The core thesis is:

> Do not trust a probabilistic system with mutation power when the execution
> path can be compiled from repo evidence and policy (typed PlanRow rows,
> contracts, receipts, and guard results).

LLMs are useful because they can search, explain, draft, and repair quickly.
They are risky when they are asked to remember every project rule from prompt
text, chat history, or implicit convention. A model may forget a branch rule,
skip a documentation update, miss a stale review gate, or treat an old approval
as current.

GuardIR turns those rules into executable repo-owned machinery:

- policy is parsed into typed governance state
- session startup emits a typed next-action packet
- work is bounded by plan and ownership state
- review and approval move through typed packets
- guards and probes emit normalized findings
- commit and push are routed through governed commands
- run receipts and artifacts become evidence for the next session

The goal is not to make the AI deterministic. The goal is to make the
admission boundary deterministic enough that AI output can be reviewed,
replayed, and safely advanced.

## How To Position It

The safest short description is:

> GuardIR is a repo-local governance compiler for AI coding agents. Coding
> clients propose work; GuardIR adjudicates whether that work is admissible.

This should be stated carefully. Many adjacent tools have valuable governance
mechanisms: hooks, rules, PR checks, sandboxes, guardrails, approvals, agent
workflows, and hosted review surfaces. Do not claim that other tools have no
governance or no checks.

The distinction is the primary question each layer answers.

| Layer | Primary question |
|---|---|
| Coding clients and IDE agents | What code should be written next? |
| Agent frameworks | How should agents, tools, handoffs, and workflows run? |
| PR review bots and CI checks | What does this diff or PR appear to violate? |
| Capability registries and MCP servers | What tools can an agent call? |
| GuardIR | Given this repo's plan, policy, typed state, review history, and evidence, is this work allowed to advance? |

So the correct claim is scope and integration, not novelty-by-negation:

- GuardIR treats AI software development as an admissibility problem over
  repo-local typed state.
- It is designed to sit around coding clients rather than replace them.
- It aims to make authority portable across clients by exposing deterministic
  CLI commands and machine-readable contracts.
- It records why a change was allowed, not only that a command succeeded.

Avoid claims like "nobody else has guards" or "no other tool has contracts."
Prefer claims like "adjacent systems provide hooks, rules, checks, or
guardrails, while this system's center of gravity is repo-owned typed
admissibility over plan, policy, packet lifecycle, and execution evidence."

## Current Status

The architecture is real in this repository, but the portable platform is not
finished.

Implemented or actively used here:

- `devctl` as the primary command surface
- typed startup context and work-intake state
- `ProjectGovernance` and repo-policy resolution
- hard guards, advisory probes, findings, and governance-review ledgers
- review-channel packet posting, acknowledgement, application, and history
- governed commit and push paths
- dashboard, mobile, and operator projections over typed state
- repo-pack and generated-surface work toward portability

Still active under `MP-377`:

- removing remaining VoiceTerm-shaped defaults from portable layers
- proving first-run behavior in non-VoiceTerm repos without manual babysitting
- tightening event-backed authority and lifecycle reducers
- completing repo-pack/bootstrap/export packaging
- making graph, swarm, and remote-control evidence consume one shared typed
  authority model rather than parallel compatibility projections

The honest state is: portable by architecture direction, partially portable in
implementation, and still using VoiceTerm as the main live proof bed.

## The Compiler Model

The platform is easiest to understand as a compiler-style control system.

| Compiler idea | GuardIR equivalent |
|---|---|
| Source program | repo state + git state + plans + repo policy |
| Frontend | startup, policy resolution, guards, probes, graph/context scans |
| Intermediate representation | typed contracts such as `ProjectGovernance`, `StartupContext`, `WorkIntakePacket`, `Finding`, `DecisionPacket`, `TypedAction`, `ActionResult`, `RunRecord` |
| Analysis passes | `check-router`, guard bundles, review-channel reducers, validation plans, governance review |
| Code generation | actual file edits, staging, commit, push, release, or generated surfaces |
| Runtime evidence | receipts, findings, ledgers, snapshots, run records, review history |

This model matters because it keeps authority out of prompt-local memory. A
prompt can explain a rule, but a reducer, guard, or typed command can enforce
it consistently.

## Architecture Layers

The intended platform split is five layers plus adopter integrations.

| Layer | Owns | Should not own |
|---|---|---|
| Portable governance core | policy resolution, guard/probe semantics, findings, review ledger, bootstrap/export primitives | VoiceTerm paths, product branding, local terminal assumptions |
| Shared runtime | typed contracts, action/result envelopes, run records, authority snapshots, state projections | provider-specific lifecycle hacks |
| Adapters | VCS, CI, provider, notification, dashboard/mobile transports | admission policy |
| Frontends | CLI, dashboard, mobile, overlay/TUI, optional MCP read surfaces | independent backend truth |
| Repo packs | repo-specific paths, docs, branch policy, thresholds, generated surfaces | portable engine logic |
| Adopters | VoiceTerm, future repo integrations, product shells | universal authority defaults |

Rule of thumb: frontends render typed state and dispatch typed actions. They do
not reimplement the policy decision. Repo packs describe local behavior. They
do not fork the platform.

## The Typed State Spine

The platform works because important facts are represented as typed contracts,
not as private chat memory.

### `ProjectGovernance`

`ProjectGovernance` is the repo-policy envelope. It describes repo identity,
repo-pack reference, path roots, plan registry, doc policy, enabled checks,
artifact roots, bridge configuration, startup order, workflow profiles, and
push enforcement.

Use it when code needs to know what this repo considers authoritative. Do not
hardcode `dev/active`, `dev/reports`, `bridge.md`, VoiceTerm names, or branch
policy in portable layers when the value should come from governance state.

### `StartupContext`

`startup-context` is the session gate. It answers: should this actor edit,
repair, review, checkpoint, wait, push, or stop?

Run it before starting work:

```bash
python3 dev/scripts/devctl.py startup-context --format summary
python3 dev/scripts/devctl.py startup-context --format json
```

Important fields include `action`, `reason`, `interaction_mode`,
`implementation_permission`, `push_decision`, reviewer/runtime state, allowed
and blocked actions, and the embedded work-intake packet.

### `WorkIntakePacket`

`WorkIntakePacket` bounds the slice. It connects current work to plan state,
ownership, coordination mode, continuation context, and pacing. It exists so
agents do not widen scope just because more files are visible.

### `Finding` And `DecisionPacket`

A `Finding` is a normalized signal from a guard, probe, review import, or
governance scan. It should carry stable identity, severity, source, location,
evidence, and AI-actionable repair guidance.

A `DecisionPacket` is the policy verdict on a finding. It separates "the tool
observed a risk" from "this repo decided to fix, defer, accept, override, or
escalate it." That separation is what lets rule libraries remain portable
while decisions stay repo-specific.

### `CollaborationSession`, `AuthoritySnapshot`, And `SessionPosture`

These contracts describe who is present, who owns mutation, who owns
verification, which lane is occupied, and which capabilities are currently
granted. Mutation authority is identity-bound. Code should prefer capability
facts such as `repo.commit` or `repo.stage` over string-matching a reviewer
mode label.

### `TypedAction`, `ActionResult`, And `RunRecord`

`TypedAction` is a proposed mutation or command with explicit parameters.
`ActionResult` is the result envelope with `pass`, `fail`, `unknown`, or
`defer`, plus reason chains, errors, warnings, remediation, and artifact refs.
`RunRecord` is the durable execution-row model that future sessions can
inspect when a lane has emitted it. Not every command has completed conversion
to this full receipt path yet, so architecture docs should describe it as the
target and bounded-lane model unless a specific command already proves it.

The pattern is:

```text
proposal -> typed action -> governed execution -> action result -> run record
```

When a command can explain a blocker, it should emit structured fields rather
than only prose. Dashboards, mobile views, agents, and CI all need the same
truth.

### Projections

Markdown, dashboards, mobile views, and generated instruction surfaces are
projections. They can be useful and user-facing, but they should render from
typed state. A projection can be stale or compatibility-only; the typed
producer remains the authority.

## Companion Docs Map

> The repo has 200+ markdown files. Most are projections or scoped reference;
> only a handful are durable authority. This map sorts every doc by tier so
> you can answer "which file do I open?" without grepping the whole tree.

The tier model comes from `dev/guides/SYSTEM_MAP.md` §0.7. When tiers conflict,
tier 1 wins.

### Tier 1 — Typed state (durable authority)

| Path | Contract | When to read |
|---|---|---|
| `dev/state/plan_index.jsonl` | `PlanRow` | Find current/active rows and their status |
| `dev/state/contract_registry.jsonl` | contract metadata | Validate a typed object schema |
| `dev/state/transition_modules.jsonl` | `GovernedTransitionModule` | Trace state-machine wiring |
| `dev/state/plan_row_closure_receipts.jsonl` | `PlanRowClosureReceipt` | Confirm a row is closed with proof |
| `dev/state/bypass_lifecycles.jsonl` | `BypassLifecycle` | Audit edit-bypass authority |
| `dev/state/governed_exception_lifecycles.jsonl` | `GovernedExceptionLifecycle` | Trace approved exceptions |
| `dev/state/ground_truth_probe_receipts.jsonl` | `GroundTruthProbeRunReceipt` | Verify probe freshness |
| `dev/state/raw_git_bypass_receipts.jsonl` | `RawGitBypassReceipt` | Audit raw-git exemptions |
| `dev/state/governance_reconciliation_receipts.jsonl` | `GovernanceReconciliationReceipt` | Investigate drift repair |
| `dev/state/artifact_receipts.jsonl` | `ArtifactReceiptRecord` | Track artifact production |
| `dev/state/baseline_authority_inventories.jsonl` | `BaselineAuthorityInventoryReceipt` | Compare against boot snapshot |
| `dev/reports/feature_proof_receipts/` | `FeatureProofReceipt` | Per-SHA proof a feature is real |
| `dev/reports/push/latest_push_report.json` | `PushAuthorizationRecord` | Verify a publication succeeded |

### Tier 2 — Active-doc projections (read for navigation)

| Path | Owns | When to read |
|---|---|---|
| `dev/active/INDEX.md` | Registry of every `dev/active/` file | Every session, after the boot chain |
| `dev/active/MASTER_PLAN.md` | Tracker projection over `plan_index.jsonl` | When you need the strategic picture |
| `dev/active/ai_governance_platform.md` | MP-377 spec (portable platform extraction) | When working on governance platform |
| `dev/active/review_channel.md` | MP-355 spec (review-channel protocol) | When working on packet lifecycle |
| `dev/active/review_probes.md` | MP-368..375 spec (heuristic probes) | When calibrating probes |
| `dev/active/PLAN_FORMAT.md` | Governance contract for plan-doc schema | Before editing any active-plan markdown |
| `dev/active/portable_code_governance.md` | MP-376 reference (portable guard/probe engine) | When porting governance to another repo |

**Scoped reference (load only when the active typed phase names it):**
`platform_authority_loop.md`, `autonomous_governance_loop_v2.md`,
`remote_commit_pipeline.md`, `remote_control_runtime.md`,
`theme_upgrade.md`, `memory_studio.md`, `devctl_reporting_upgrade.md`,
`autonomous_control_plane.md`, `agent_substrate_architecture_review.md`,
`host_process_hygiene.md`, `continuous_swarm.md`, `operator_console.md`,
`loop_chat_bridge.md`, `naming_api_cohesion.md`, `ide_provider_modularization.md`,
`pre_release_architecture_audit.md`, `audit.md`, `move.md`,
`slash_command_standalone.md`, `ralph_guardrail_control_plane.md`,
`code_shape_expansion.md`, `CLAUDE_SESSION_AUTOMATION_SAFETY_DECLARATION.md`,
`phase2.md`.

Reading these by default pollutes context. Read them only when typed phase
state names them.

### Tier 3 — Navigation and connectivity (consult after the boot chain)

| Path | Purpose |
|---|---|
| `dev/guides/SYSTEM_MAP.md` | Living connectivity index; subsystem deep-dives, priority backlog |
| `dev/guides/SYSTEM_FLOWCHART.md` | Codebase audit with LOC counts and component relationships |
| `System_Connection_Flowchart.md` (root) | Platform-only subsystem map with mermaid spine; deep-dive for duplicate-system and disconnected-island work |

### Tier 4 — Reference guides (`dev/guides/`, this file's neighborhood)

| Path | One-line purpose |
|---|---|
| `dev/guides/README.md` | Index of maintainer guides |
| `dev/guides/PLATFORM_GUIDE.md` | This file — platform architecture and operating model |
| `dev/guides/AI_GOVERNANCE_PLATFORM.md` | Whitepaper thesis (companion to `dev/active/ai_governance_platform.md` — that one tracks execution; this one carries the durable thesis) |
| `dev/guides/ARCHITECTURE.md` | VoiceTerm Rust overlay architecture |
| `dev/guides/DEVCTL_ARCHITECTURE.md` | `devctl` control-plane map |
| `dev/guides/DEVCTL_AUTOGUIDE.md` | Running `devctl` end-to-end with automation |
| `dev/guides/DEVCTL_JSON_CONTRACTS.md` | Machine-readable JSON/JSONL contracts emitted by devctl |
| `dev/guides/DEVCTL_MULTI_AGENT_OPERATIONS.md` | Multi-agent operating model via devctl + active-plan + bridge |
| `dev/guides/DEVCTL_PRODUCT_FLOW.md` | Intended final-product flow |
| `dev/guides/DEVELOPMENT.md` | Development workflow, post-edit checks, verification gates |
| `dev/guides/MCP_DEVCTL_ALIGNMENT.md` | How MCP fits without replacing devctl |
| `dev/guides/PORTABLE_CODE_GOVERNANCE.md` | Treating guard/probe stack as reusable system |
| `dev/guides/PORTABLE_GOVERNANCE_SETUP.md` | Bootstrap a new repo onto portable governance |
| `dev/guides/PYTHON_ARCHITECTURE.md` | Python modeling and composition rules |
| `dev/guides/SYSTEM_ARCHITECTURE_SPEC.md` | Consolidated architecture spec (draft; defer decisions to `dev/active/`) |
| `dev/guides/SYSTEM_AUDIT.md` | 13-dimension system audit findings |
| `dev/guides/AGENT_COLLABORATION_SYSTEM.md` | Python orchestration stack for Codex/Claude collaboration |

### Root-level orientation files

| Path | Audience | Purpose |
|---|---|---|
| `README.md` | end user + dev | Project overview, install pointers |
| `QUICK_START.md` | end user | VoiceTerm voice-input setup (NOT the platform quickstart) |
| `AGENTS.md` | AI agent | Generated boot card |
| `CLAUDE.md` | AI agent | Generated boot card (Claude-specific) |
| `THESIS_EVIDENCE.md` | research audience | Governance-thesis evidence |
| `System_Connection_Flowchart.md` | platform reviewer | Platform subsystem map (excludes VoiceTerm) |
| `UNIVERSAL_SYSTEM_EVIDENCE.md` / `UNIVERSAL_SYSTEM_PLAN.md` | reference | Shared-worktree companions (not tracked execution) |
| `bridge.md` | (deprecated) | Compatibility projection; may be stale during migration |
| `backlog.md` | shared | Open backlog items |
| `codesmells.md` | shared | Running log of architectural smells |
| `delete_after_ingest.md` | operator | Plan-ingestion staging; delete after ingest |

### Decision tree: which doc do I open?

```text
Starting a session?
  └─ Run boot chain (see Boot Sequence below)
     └─ Then read AGENTS.md → dev/active/INDEX.md → dev/active/MASTER_PLAN.md

Need the strategic picture?
  └─ dev/active/MASTER_PLAN.md

Working on a specific MP scope?
  └─ Find the active doc in dev/active/INDEX.md
     └─ Read only the named owner doc; skip scoped-reference docs unless phase names them

Need system topology / connectivity?
  └─ dev/guides/SYSTEM_MAP.md (after the boot chain)
     └─ Deeper: System_Connection_Flowchart.md (root)

Need a command reference?
  └─ This file's Command Map, plus dev/scripts/README.md

Need to port to another repo?
  └─ dev/guides/PORTABLE_GOVERNANCE_SETUP.md
     └─ Then dev/active/portable_code_governance.md

Guard or check failed?
  └─ Read the guard's error message; cross-ref with Operational: Bundles section below
```

## Boot Sequence

> This is a how-to. Follow it verbatim every session. The three commands below
> are the canonical entry; everything else is diagnostic fallback.

### The canonical three-command chain

```bash
# 1. Compose the session orientation packet.
#    Why: this is the only sanctioned entry. It composes startup-context,
#         session-resume, review-channel status, and context-graph bootstrap
#         into one typed SessionOrientationPacket.
#    Proves: orientation is current; safe_to_continue gate evaluated;
#            review channel projected.
python3 dev/scripts/devctl.py session \
  --role observer \
  --include-review-status always \
  --format json
```

`--role` is one of `reviewer`, `implementer`, `dashboard`, `observer`. The
default this surface uses is `observer` plus `--actor agent`; switch only when
typed startup authority, operator direction, or session assignment says to.

After step 1, if `final.safe_to_continue=false` or `final.next_command`
requires checkpoint or repair, **stop**. Do not proceed to step 2.

```bash
# 2. Get the next typed development command.
#    Why: selection comes from typed plan/lifecycle authority. Packet ids alone
#         are intake/provenance, not directives.
#    Proves: the next slice is bounded and identified.
python3 dev/scripts/devctl.py develop next --actor agent --format md
```

If step 2 returns `continuation_required`, run its `next_step_command` and
loop step 2 until a slice is selected. Archived packet history is audit
evidence, not live packet-attention.

```bash
# 3. Before final response or TASK_COMPLETE, run the gate.
#    Why: stops you from summarizing-and-exiting when continuation work is
#         still required. Denial is continuation work, not permission to stop.
#    Proves: final response is allowed; the continuation anchor is closed
#            (or a stop_anchor stops the goal).
python3 dev/scripts/devctl.py develop next --actor agent \
  --enforce-final-response-gate --format json
```

If the gate reports `final_response_allowed=false`, `continuation_state=must_continue`,
or a `next_required_command`, run the named command and re-check. Do not emit
final completion prose until the gate allows it.

### Diagnostic fallback (only when `devctl session` is unavailable)

| Command | What it gives you |
|---|---|
| `python3 dev/scripts/devctl.py startup-context --role observer --format json` | Just the `StartupContext` packet |
| `python3 dev/scripts/devctl.py session-resume --role observer --format bootstrap` | Compact (~500-token) cached session state |
| `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json` | Live review-channel state |
| `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md` | Context-graph bootstrap projection |

These are the same components `devctl session` composes. Use them only when
the composer is broken; otherwise prefer the canonical chain.

### Operator command wrappers

When `develop` emits an `Operator Command Wrappers` block, run the wrapped
command verbatim instead of reconstructing a long inline command. Wrappers
are built by `development/operator_command_wrappers.py` and are rendered only
when the actor + proxy + mutation-risk classification says it is safe — so a
present wrapper is an authority signal, not just a formatting nicety.

### When to stop the loop

| Signal | Stop because |
|---|---|
| `final.safe_to_continue=false` | Orientation says do not edit |
| `startup-context.action ∈ {checkpoint, repair, stop}` | The next legal action is not "continue" |
| Gate denies repeatedly after running its `next_required_command` | Underlying state is stuck — surface to operator |
| Active plan row is `await_review` and you are the implementer | Wait for reviewer; do not auto-advance |
| You are about to touch `preserve/*` | Immutable evidence locker |

## Review Channel And Multi-Agent Work

The review channel is the typed coordination system for multi-agent work. In
this repo it is commonly used with Codex as reviewer and Claude as implementer,
but portable code must not assume those names or roles.

The packet vocabulary includes `finding`, `question`, `draft`, `instruction`,
`action_request`, `approval_request`, `decision`, `system_notice`,
`plan_gap_review`, `plan_patch_review`, `plan_ready_gate`, and
`commit_approval`.

Important lifecycle rule:

```text
posted -> pending -> acked -> acted on -> disposition
```

Acknowledgement is not enough. `acked` means the receiver saw the packet.
`applied` means the requested work or disposition was actually recorded with
evidence. If code treats acknowledgement as terminal, stale packets reappear
and different surfaces disagree. The event-backed reducer projects
`PacketLifecycleHistory` and `PacketDisposition`; terminal or acted-on states
can include `applied`, `dismissed`, `archived`, `failed`, and
`apply_pending_after_execution` depending on what happened after the packet was
seen.

Useful commands:

```bash
python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md
python3 dev/scripts/devctl.py review-channel --action doctor --terminal none --format md
python3 dev/scripts/devctl.py review-channel --action post --kind action_request --terminal none --format md
python3 dev/scripts/devctl.py review-channel --action apply --packet-id <id> --terminal none --format md
python3 dev/scripts/devctl.py review-channel --action history --include-outcomes --format md
```

`bridge.md` is a compatibility projection. It can help humans and older loops,
but new authority should come from typed review-channel state and reducers.

Remote-control sessions have a stricter rule: when typed liveness proves a
headless remote operator, local GUI prompts, ad hoc process killing, local
commit authority, and raw push work are not the control path. Privileged work
routes through typed action-request packets or bounded repo commands.

## Slash Commands And Skills

> The repo has nine project-defined slash commands and zero project-defined
> skills. Everything else you see in your agent (`/loop`, `/verify`, `/review`,
> `/code-review`, etc.) comes from the Claude Code harness. This section
> distinguishes the two so you stop guessing whether a slash is real here.

### Project slash commands (`.claude/commands/`)

Every project slash command is a thin typed adapter to one `devctl` post.
Authority and validation live in the typed backend; the `.md` definition only
declares the exact CLI pattern via `allowed-tools:` frontmatter.

| Slash | Wrapped devctl | When to invoke | What it proves |
|---|---|---|---|
| `/develop <action>` | `devctl develop <action>` | Inspect status, next, show, watch, ingest-plan, audit-packets | Read-only typed view; no mutation |
| `/goal` | `devctl develop --post-continuation-anchor` | Set or inspect the active continuation goal | `continuation_anchor` packet present; final-response gate honors it |
| `/handshake` | `review-channel --action post --kind peer_session_handshake` | Coordinate with a peer agent | `peer_session_handshake` packet recorded; inter-agent liveness |
| `/agent-spawn` | `review-channel --action recover` (typed launch) | Recover crashed agent or spawn into typed role | `AgentDispatchRouter` accepted scope; spawn from session posture |
| `/bypass` | `devctl bypass grant --scope edit-only` | Request scoped edit-only authority | `BypassLifecycle` row written (request → evaluation → receipt → expiry) |
| `/check-it` | `devctl develop --post-task-produced` | Hand reviewers the exact verification command | `task_produced` packet with command + evidence ref |
| `/session-log` | `devctl develop --log-progress` | Mark a session milestone | Progress log row; session-resume can replay |
| `/archive-evidence` | `devctl develop --post-evidence --target-kind artifact` | Preserve a durable artifact | Evidence packet bound to artifact ref |
| `/typed-remote-control` | `devctl remote-control enter` / `heartbeat` | Govern Claude's built-in `/remote-control` attach | Typed remote-control lifecycle recorded |

### Why slash commands are typed adapters

This is a security and authority pattern, not an aesthetic one.

- The `allowed-tools:` declaration in each `.claude/commands/*.md` file scopes
  the exact CLI pattern the slash may run (e.g. `Bash(python3 dev/scripts/devctl.py develop:*)`).
  Arbitrary subprocess calls are blocked.
- Slash commands never mutate state directly; they post **typed packets** into
  the review channel. The packet lifecycle engine decides validity, scope, and
  expiry.
- This means "what authority does a slash carry?" is answerable by reading
  `dev/scripts/devctl/runtime/` and the slash's `allowed-tools` line — not by
  reading the slash command's prose.

### Skills

**Project-defined skills:** none. This repo does not define any
`.claude/skills/SKILL.md` files. Everything an agent does that requires
multi-step orchestration goes through `devctl` and the review channel.

**Harness-provided skills (Claude Code):** when your system reminder lists
skills like `agent-spawn`, `develop`, `goal`, `handshake`, `check-it`,
`session-log`, `archive-evidence`, `bypass`, `update-config`, `verify`,
`code-review`, `loop`, `schedule`, `init`, `review`, `security-review` — those
are the harness's built-in or org-distributed skills. Treat them as upstream
tooling. Do not invent skill definitions to "match" the names; the project
slash commands above already wrap their typed adapters in `.claude/commands/`.

### Operator command wrappers

When `devctl develop` emits an **Operator Command Wrappers** block, the wrapped
form is the safe, classification-checked invocation. Run it verbatim. Wrapper
authority lives in `dev/scripts/devctl/commands/development/operator_command_wrappers.py`;
rendering is gated by `classification.is_safe_to_render` (actor + proxy +
mutation-risk checks).

### Generators and templates

| Path | Purpose |
|---|---|
| `dev/config/templates/claude_voice_skill.template.md` | Provider-level voice-skill template (VoiceTerm-specific, not a slash) |
| `dev/scripts/devctl/commands/development/parser.py` | `devctl develop` argument parser; defines every `--post-*` action a slash wraps |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | Top-level devctl registration; the typed parser that defines which subcommands are legal (read this rather than guessing) |

## Guards, Probes, And Findings

The platform separates blocking checks from advisory review.

| Surface | Purpose | Expected behavior |
|---|---|---|
| Hard guards | prevent known regressions | fail closed |
| Review probes | surface design smells and AI-style risks | report findings without blocking by default |
| Findings | normalize guard/probe/review signals | stable identity and repair guidance |
| Decision packets | record repo-specific disposition | explain fix, defer, accept, override, or escalate |
| Bundles | run the correct check set for a task class | use repo-owned registry, not hand-picked guesses |

This separation matters. A noisy signal can begin as a probe, become a finding,
gain decision history, and later be promoted into a hard guard once the
contract is clear.

## Operational: Bundles, Hooks, And `check-router`

> The previous section explained what guards and probes *are*. This section
> explains *when each one fires, what it blocks, and how to fix a failure*.
> If you remember nothing else, remember: `check-router` picks the right
> bundle by changed paths; you do not hand-pick.

### Inventory snapshot

- **Hard guards** (`check_*.py`): 166
- **Probes** (`probe_*.py`): 70+
- **Total** in `dev/scripts/checks/`: 236+ distinct checks (596 Python files
  counting support modules)
- **Composed into bundles**: 67 in `_GUARD_CHECKS`, 50+ in
  `_SHARED_GOVERNANCE_CHECKS`
- **Named bundles**: 7
- **Git hooks**: 3 (pre-commit, post-commit, pre-push)
- **`check-router` lanes**: 4 (release, tooling, runtime, docs)

Authority: `dev/scripts/devctl/bundles/registry.py` (bundle composition) +
`dev/scripts/devctl/governance/script_catalog_registry.py` (script catalog).

### The seven bundles (what to run when)

| Bundle | Trigger / context | What's inside |
|---|---|---|
| `bundle.bootstrap` | Cold boot of a new repo or session | `git status`, branch, remotes, log, plan snapshot, devctl list, orphan files |
| `bundle.current-row-proof` | Validating that the current plan row can close | Plan row proof, topology liveness, provider hooks, projection render |
| `bundle.runtime` | After editing Rust or Python source code | `check --profile ci`, process hygiene, docs-check, hygiene sweep, all `_GUARD_CHECKS` |
| `bundle.docs` | After editing docs / guides / CHANGELOG | `docs-check --user-facing`, hygiene, all 67 `_GUARD_CHECKS` |
| `bundle.tooling` | After editing `dev/scripts/`, `.github/workflows/`, or `CLAUDE.md` | `docs-check --strict-tooling`, hygiene `--strict-warnings`, orchestrate commands, `_SHARED_GOVERNANCE_CHECKS` + `_GUARD_CHECKS`, control-decision-consistency |
| `bundle.release` | Release or publication phase | `check --profile release`, docs-check (user-facing + strict-tooling), release hygiene, orchestrate, `_SHARED_GOVERNANCE_CHECKS`, publication-sync, coderabbit gates, `_GUARD_CHECKS` |
| `bundle.post-push` | After a successful `devctl push --execute` | `git status` / `log`, `status --ci`, orchestrate, docs-check, hygiene, active-plan-sync, review-channel-bridge, diff-aware `_POST_PUSH_GUARD_CHECKS` |

You do not choose. `check-router` picks the bundle for you based on the
changed paths since your `--since-ref`.

### How `check-router` picks the bundle

```bash
python3 dev/scripts/devctl.py check-router \
  --since-ref origin/develop --execute
```

The algorithm (see `dev/scripts/devctl/commands/check/router.py:run`):

1. **Collect changed paths** vs `--since-ref` (default `origin/develop`).
2. **Classify each path** against `router_constants.py:14-100`:
   - `.github/workflows/release_preflight*.yml`, `rust/Cargo.toml`,
     `rust/Cargo.lock`, version files → **release lane**
   - `dev/scripts/`, `.github/workflows/`, `.github/scripts/`,
     `dev/active/`, `dev/config/` → **tooling lane**
   - `rust/src/`, `rust/tests/`, `rust/benches/` → **runtime lane**
   - `guides/`, `docs/`, `README.md`, `QUICK_START.md` → **docs lane**
   - Unclassified → defaults to **runtime lane**
3. **Resolve the bundle** via `BUNDLE_BY_LANE`:
   `release → bundle.release`, `tooling → bundle.tooling`,
   `runtime → bundle.runtime`, `docs → bundle.docs`.
4. **Detect risk add-ons** (overlay/input/status/HUD, Python test nodeids)
   and append extra checks.
5. **Apply scope** — `--validation-scope` (`live_worktree`,
   `staged_tree`, `pipeline_authorized_phase`) controls how strict the
   diff-aware guards run.
6. **Execute or report** — with `--execute`, run all commands; without,
   return the plan in markdown or JSON.

### The hook chain (pre-commit → post-commit → pre-push)

#### Pre-commit (`dev/config/git_hooks/pre-commit-review-snapshot.sh`)

Fires before `git commit` seals the index. **All blockers are hard failures.**
Runs in order:

1. `check_role_lane_mutation_authority --mode pre_mutation`
2. `check_current_plan_authority`
3. `check_orphan_files`
4. `check_feature_completion`
5. `check_plan_row_must_advance`
6. `check_no_ingestion_churn_without_advancement`
7. `check_receipt_schema_validation`
8. `check_receipt_store_has_active_consumer`
9. `check_receipt_store_coverage_sweep`
10. `check_every_applied_row_has_closure_receipt`
11. `check_receipt_commit_anchor_refs`
12. **Commit permission gate** — `devctl.runtime.commit_permission_hook`
    enforces the `commit_permission` typed contract when NOT using
    `devctl commit`.

Governed `devctl commit` paths bypass via `DEVCTL_GOVERNED_COMMIT=1`. Do not
`--no-verify`; fix the root cause.

#### Post-commit (`dev/config/git_hooks/post-commit-review-snapshot.sh`)

Fires after a commit succeeds. **Fail-open**: errors are warnings, never
blockers (the commit has already landed). Refreshes
`dev/audits/REVIEW_SNAPSHOT.md` and writes a receipt-only commit if it changed.
Timeout: 90s (override with `DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS`). CI's
`check_review_snapshot_freshness` catches stale snapshots at push time.

#### Pre-push (`dev/config/git_hooks/pre-push-governed-push.sh`)

Fires before `git push`. **Hard failure**: raw `git push` is blocked. Resolves
repo root and startup context, emits typed action/reason, then blocks with:

> [pre-push hook] Raw git push is blocked in this repo

The governed path is `python3 dev/scripts/devctl.py push --execute` (sets
`devctl.governed-push=true` git config flag for the push).

### Top guards every contributor should know

These are the most likely to fire and the most likely to confuse. The fix
column is "where to look first" — not a promise of one-step recovery.

| Guard | Blocks | Fires in | Fix recipe pointer |
|---|---|---|---|
| `check_role_lane_mutation_authority` | Commits without typed plan ownership | pre-commit | `devctl develop next` to accept work into active lane |
| `check_current_plan_authority` | Commits outside active plan scope | pre-commit | `dev/active/INDEX.md` and re-run `devctl session` |
| `check_orphan_files` | Staged untracked files | pre-commit | Delete orphans or move into tracked dirs |
| `check_plan_row_must_advance` | Commits that don't move the plan | pre-commit | `devctl develop --advance` or accept a new row |
| `check_active_plan_sync` | Drift in `dev/active/` files | all bundles | `devctl render-surfaces --write` |
| `check_receipt_schema_validation` | Malformed receipt YAML/JSON | pre-commit | Fix YAML/JSON syntax in `dev/reports/` |
| `check_code_shape` | Functions too large / complexity threshold | `bundle.runtime` | See `dev/guides/DEVELOPMENT.md#code-shape-debt` for exceptions |
| `check_package_layout` | Vendored code, private imports, import cycles | `bundle.runtime` | Run with `--baseline-debt-root` for ratchets |
| `check_platform_contract_closure` | Unimplemented contracts / broken connectivity | `bundle.tooling` | `devctl platform-contracts --format md` to inspect |
| `check_runtime_spine_closure` | Spine type/value mismatches | `bundle.tooling` | Inspect schema migration spine and fix type refs |
| `check_multi_agent_sync` | Review-channel packet lifecycle violations | `bundle.runtime`, `bundle.post-push` | `devctl review-channel --action doctor` |
| `check_python_subprocess_policy` | Unsafe subprocess calls in Python | `bundle.runtime` | Use typed `spawn_subprocess_unit()` or raise exemption |
| `check_rust_compiler_warnings` | Rust warnings-as-errors | `bundle.runtime` | Fix warning or raise baseline-debt exemption |
| `check_bridge_projection_only` | Modifying typed state through `bridge.md` projection | `bundle.tooling` | Edit typed source, not generated bridge |
| `check_publication_sync` | External website/repo sync stale | `bundle.release` | Run sync scripts or update publication cache |

### Guard vs probe vs check (one paragraph)

- **Guard**: deterministic blocking check; fails closed; embedded in commit /
  push / CI gates.
- **Probe**: advisory review signal; surfaces design smells without blocking
  by default; flows through `probe-report` and findings.
- **Check**: the union term. Both are `dev/scripts/checks/check_*.py` /
  `probe_*.py`, registered in `script_catalog_registry.py`, composed into
  bundles via `bundle_registry.py`.

Probes graduate into guards once their signal is calibrated.

## Developer Workflows

### Start A Session

Run startup first and let the typed packet tell you the next legal action:

```bash
python3 dev/scripts/devctl.py startup-context --format summary
```

Then read the active-doc projections for your scope (each is a maintained
projection over typed state, not durable authority):

- `AGENTS.md`
- `dev/active/INDEX.md`
- `dev/active/MASTER_PLAN.md`
- the active plan named by startup or `INDEX.md`

Do not treat chat memory, a stale summary, or an old terminal scrollback as
current authority.

### Inspect The Platform State

Use these when you need to understand what the platform knows:

```bash
python3 dev/scripts/devctl.py quality-policy --format md
python3 dev/scripts/devctl.py platform-contracts --format md
python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md
python3 dev/scripts/devctl.py system-picture --format md
python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md
```

### Make A Code Or Docs Change

Keep the edit scoped to the active intake. After editing, run the task-class
bundle and any risk add-ons from `AGENTS.md` and
`dev/guides/DEVELOPMENT.md#after-file-edits`.

For this repo, the bundle authority lives in
`dev/scripts/devctl/bundles/registry.py`. The usual entry points are:

```bash
python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py check --profile ci
```

### Commit

Prefer governed commit paths when the change is part of the controlled
pipeline:

```bash
python3 dev/scripts/devctl.py commit --paths <path>... -m "message"
```

The governed path can stage selected files, refresh managed projections, run
the routed checks, enforce approval boundaries, and report the content commit
separately from any generated receipt commit.

### Push

Do not infer push readiness from a clean worktree alone. Read the typed
`push_decision`:

| `push_decision` | Meaning | Next step |
|---|---|---|
| `await_checkpoint` | work needs a local checkpoint first | commit, then rerun startup |
| `await_review` | checkpoint exists but reviewer acceptance is not current | wait for review state to advance |
| `run_devctl_push` | governed push is allowed | run `python3 dev/scripts/devctl.py push --execute` |
| `no_push_needed` | upstream already matches | stop |

Use:

```bash
python3 dev/scripts/devctl.py startup-context --format summary
python3 dev/scripts/devctl.py push
python3 dev/scripts/devctl.py push --execute
```

Raw `git push` is intentionally not the normal publication path.

### Adopt Another Repo

The intended model is not "copy the whole VoiceTerm tooling tree and edit it by
hand." The intended model is:

1. install or export the reusable platform
2. bootstrap a target repo
3. generate or select a repo pack
4. write the minimum repo-local policy, hook, workflow, and guide surfaces
5. keep repo-specific behavior behind policy and repo-pack seams

Current commands:

```bash
python3 dev/scripts/devctl.py governance-bootstrap --target-repo /tmp/copied-repo --format md
python3 dev/scripts/devctl.py governance-export --format md
python3 dev/scripts/devctl.py probe-report --repo-path /tmp/copied-repo --adoption-scan --format md
python3 dev/scripts/devctl.py check --profile ci --repo-path /tmp/copied-repo --adoption-scan --format md
```

Treat this as active platform work, not a finished one-command product install.

## Extending The Platform

### Add A Guard

A new hard guard should:

- have a clear blocking invariant
- emit actionable failures
- be registered in the script catalog
- be wired into quality policy, bundles, and workflows or explicitly exempted
- have tests that prove the failure and pass cases
- update maintainer docs when behavior changes

### Add A Probe

A new probe should:

- identify a review-worthy risk without pretending it is always a bug
- emit structured risk hints
- include `ai_instruction` repair guidance
- stay advisory until the signal is calibrated
- flow through `probe-report` and findings review

### Add A Typed Contract

A new contract should:

- name its producer and consumers
- define closed domains as enums or validated string sets where appropriate
- include schema version and contract id when persisted
- avoid raw dict handoffs when a typed model is available
- be discoverable through platform contract or connectivity checks
- include migration or compatibility behavior if it replaces an older surface

### Add A Frontend Or Adapter

A frontend should render typed state and dispatch typed actions. It should not
compute its own admission decision. If a dashboard, mobile view, MCP tool, or
overlay needs a new fact, add it to the runtime/read model first and then
project it outward.

### Add Repo-Specific Behavior

Put repo-specific paths, thresholds, branch policy, docs requirements, and
generated surfaces in repo policy or repo packs. Do not put VoiceTerm literals
in portable modules as fallback truth.

## Anti-Patterns And Stop Signals

> Named failure modes. When you see the symptom, grep for the pattern name.
> Naming the pattern is half the fix.

### The "I'll just edit out of band" trap

**Symptom**: An agent edits a file directly to "save time" instead of routing
the change through `devctl develop next` and the active plan row.

**Why it breaks**: The pre-commit hook fails (`check_role_lane_mutation_authority`,
`check_current_plan_authority`, or `check_plan_row_must_advance`). The commit
is blocked. The agent's diff sits in the worktree with no place to land.

**Fix**: Re-enter the typed loop. Run `devctl develop next --actor agent`. If
the slice for this work doesn't exist, post a packet for it; do not push the
diff sideways.

### The stale-packet directive

**Symptom**: A packet in the review channel inbox says "do X". The agent acts
on it. The user is surprised because the packet was from a dead session two
days ago.

**Why it breaks**: Packet ids are intake / provenance, not authority. A live
typed plan row is authority. The packet inbox accumulates across sessions.

**Fix**: Before acting on any packet, verify its `source_session_id` matches a
live session in `review-channel status`. If it doesn't, archive it and
re-resolve from typed plan state.

### The bridge-as-authority trap

**Symptom**: An agent reads `bridge.md` to decide what to do next. The bridge
says one thing; `review-channel status` says another.

**Why it breaks**: `bridge.md` is a deprecated compatibility projection. It may
be stale, contradictory, or stubbed during migration. Typed state always wins.

**Fix**: Read typed state (`devctl review-channel --action status` plus
`develop next`). If you need to update the bridge, run
`devctl render-surfaces --write --format md`.

### The dashboard / mobile / chat-as-proof trap

**Symptom**: A dashboard row, a phone-status surface, or chat history says
"the push succeeded". The agent reports success.

**Why it breaks**: None of these are proof. The only push proof is
`dev/reports/push/latest_push_report.json` plus the `git rev-parse` / `git
ls-remote` you can run yourself.

**Fix**: Always verify mutations with a direct git command or a typed receipt.
Treat dashboards as visualization over typed state, not as durable authority.

### The over-stuffed CLAUDE.md trap

**Symptom**: An agent appends new rules to `CLAUDE.md` to "make Claude remember".

**Why it breaks**: `CLAUDE.md` is a generated projection — `surface_id:
claude_boot_card`. Hand-edits are overwritten on the next
`devctl render-surfaces --write`. Authority lives in repo policy, contracts,
guards, and receipts.

**Fix**: If a rule is durable, encode it in `dev/config/devctl_repo_policy.json`,
in a guard, in a contract, or in an active doc. If it's process guidance,
add it to this file (`PLATFORM_GUIDE.md`).

### The "kept retrying through gate denial" trap

**Symptom**: The final-response gate keeps denying. The agent re-runs the same
command. The denial persists. The agent decides to ignore it and emit final
response anyway.

**Why it breaks**: Denial is the typed system telling you continuation work is
required. Ignoring it leaves orphan state in `dev/state/`.

**Fix**: Read the gate's `next_required_command` and run it verbatim. If the
gate keeps denying after the named command runs, the underlying state is
stuck — surface to the operator. Do not force a stop.

### The "preserve/\*" branch trap

**Symptom**: An agent finds a `preserve/something` branch and assumes it can be
modified or deleted.

**Why it breaks**: `preserve/*` is an immutable evidence locker. Modifications
break the audit chain.

**Fix**: Never check out, edit, or push to a `preserve/*` branch.

### The "same lane, two agents, no coordination" trap

**Symptom**: Two agents both editing the same plan row in parallel. Both
produce diffs. The diffs conflict.

**Why it breaks**: The substrate is **any-model-any-role** — `mutation_owner`
and `verification_owner` are typed role slots in `CollaborationSession`, not
model-to-role assignments. Same-lane duplication is wasted work regardless of
which model occupies which lane. Hard-coded model-to-role assumptions (e.g.
"model X is always the coder") are themselves an anti-pattern, tracked under
the any-agent-any-role migration in `dev/active/agent_substrate_architecture_review.md`.

**Fix**: Read role assignment from typed state at session start
(`review_state.projections.latest.json::collaboration.mutation_owner` /
`verification_owner`). Act inside the lane you actually hold. If a packet
arrives addressed to a role you do not currently hold, do not act on it —
hand off or route through `review-channel`.

### The "residual gap" / "MVP scope" trap

**Symptom**: A slice ships with "residual gap", "MVP scope", or "follow-up
SLICE-X.1" markers. Both sides of a lifecycle are not finished in one slice.

**Why it breaks**: Half-finished lifecycles leave the typed state in a
"continuation_required" loop that future sessions cannot close.

**Fix**: Finish both sides of a lifecycle in one slice. If you cannot, the
slice is wrong — re-scope before starting.

### Stop signals (when to halt immediately)

| Signal | Source | What to do |
|---|---|---|
| `final.safe_to_continue=false` | `devctl session` | Stop. Do not advance. |
| `startup-context.action ∈ {checkpoint, repair, stop}` | StartupContext | Run the named recovery; do not edit. |
| `final_response_allowed=false` persists after `next_required_command` runs | Final-response gate | Surface to operator; do not force. |
| Pre-commit hook fails | git | Read the message; fix the root cause; do not `--no-verify`. |
| Pre-push blocks raw `git push` | git | Use `devctl push --execute`; that is the path. |
| `source_session_id` on packet ≠ live session | review-channel | Archive packet; re-resolve from plan state. |
| About to touch `preserve/*` | branch name | Stop. Different branch. |
| Reviewer/implementer role mismatch with typed state | `review_state.projections.latest.json` | Hand off; do not cross-lane. |

## Design Rules

1. Typed state beats prose. If a rule matters, encode it in code, policy, a
   contract, a guard, or a reducer.
2. Prompts explain authority; they do not own authority.
3. VoiceTerm is the first adopter, not the hidden default for portable layers.
4. Markdown coordination surfaces are compatibility projections unless a
   specific contract says otherwise.
5. Capability grants attach to actor identity, not reviewer-mode labels.
6. `unknown` and `defer` are real outcomes. Do not collapse missing evidence
   into success.
7. Raw git operations are escape hatches. Governed commit and push are the
   normal publication path.
8. Every mutation needs evidence: guard result, packet state, receipt, or
   explicit typed approval.
9. Frontends and adapters should not fork backend truth.
10. Portability claims need proof in non-VoiceTerm repos before being described
    as finished behavior.

## Command Map

> Sorted by phase: boot → orient → develop → check → mutate → publish →
> extend. Use the canonical chain at the top for the standard session entry;
> the rest are reference.

### Boot (canonical chain)

| Goal | Command | When | Proves |
|---|---|---|---|
| Compose session orientation | `python3 dev/scripts/devctl.py session --role observer --include-review-status always --format json` | Every session start | `SessionOrientationPacket`; `safe_to_continue` evaluated |
| Get next typed slice | `python3 dev/scripts/devctl.py develop next --actor agent --format md` | After boot succeeds | Bounded next slice with scope |
| Gate final response | `python3 dev/scripts/devctl.py develop next --actor agent --enforce-final-response-gate --format json` | Before final response / TASK_COMPLETE | `final_response_allowed` |

### Diagnostic fallback (only when `devctl session` is unavailable)

| Goal | Command |
|---|---|
| Just `StartupContext` | `python3 dev/scripts/devctl.py startup-context --role observer --format json` |
| Compact resume state | `python3 dev/scripts/devctl.py session-resume --role observer --format bootstrap` |
| Review-channel status | `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json` |
| Context-graph bootstrap | `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md` |

### Orient and inspect

| Goal | Command |
|---|---|
| Inspect command inventory | `python3 dev/scripts/devctl.py list` |
| Inspect quality policy | `python3 dev/scripts/devctl.py quality-policy --format md` |
| Inspect contracts | `python3 dev/scripts/devctl.py platform-contracts --format md` |
| Render system-map snapshot | `python3 dev/scripts/devctl.py system-map --format md` |
| Render system-picture reducer | `python3 dev/scripts/devctl.py system-picture --format md` |
| Query context graph | `python3 dev/scripts/devctl.py context-graph --query '<term>' --format md` |
| Generate context-graph snapshot | `python3 dev/scripts/devctl.py context-graph --mode bootstrap --save-snapshot` |
| Dashboard view | `python3 dev/scripts/devctl.py dashboard --format md` |
| Git + mutation status | `python3 dev/scripts/devctl.py status --format md` |
| Governance review history | `python3 dev/scripts/devctl.py governance-review --format md` |
| Campaign / debt posture | `python3 dev/scripts/devctl.py develop campaign --format md` |

### Develop and coordinate

| Goal | Command |
|---|---|
| Show a slice | `python3 dev/scripts/devctl.py develop show --slice-id <id> --format md` |
| Read review-channel status | `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md` |
| Diagnose review-channel readiness | `python3 dev/scripts/devctl.py review-channel --action doctor --terminal none --format md` |
| Post a typed packet | `python3 dev/scripts/devctl.py review-channel --action post --kind <kind> --target-kind <k> --target-ref <ref> --terminal none --format md` |
| Apply a packet's requested work | `python3 dev/scripts/devctl.py review-channel --action apply --packet-id <id> --terminal none --format md` |
| Packet history with outcomes | `python3 dev/scripts/devctl.py review-channel --action history --include-outcomes --format md` |
| Manage exceptions lifecycle | `python3 dev/scripts/devctl.py exceptions --format md` |

### Check (CI / pre-push / per-edit)

| Goal | Command |
|---|---|
| Route required bundle by changed paths | `python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute` |
| Plan only, no execute | `python3 dev/scripts/devctl.py check-router --since-ref origin/develop --dry-run --format md` |
| Run normal CI profile | `python3 dev/scripts/devctl.py check --profile ci` |
| Pre-push profile (CI + perf/mem) | `python3 dev/scripts/devctl.py check --profile prepush` |
| AI-guard profile | `python3 dev/scripts/devctl.py check --profile ai-guard` |
| Focused Python tests via task-class | `python3 dev/scripts/devctl.py test-python --suite devctl --path <test>` |
| Tooling docs gate | `python3 dev/scripts/devctl.py docs-check --strict-tooling` |
| User-facing docs gate | `python3 dev/scripts/devctl.py docs-check --user-facing` |
| Build probe packet | `python3 dev/scripts/devctl.py probe-report --format md` |

### Mutate (governed paths only)

| Goal | Command |
|---|---|
| Commit through governed path | `python3 dev/scripts/devctl.py commit --paths <path>... -m "message"` |
| Request scoped edit-only bypass | `python3 dev/scripts/devctl.py bypass grant --scope edit-only` (lifecycle: request → evaluation → receipt → expiry) |
| Render projection surfaces | `python3 dev/scripts/devctl.py render-surfaces --write --format md` |
| Strict projection-drift check | `python3 dev/scripts/devctl.py docs-check --strict-tooling --format json` |

### Publish

| Goal | Command |
|---|---|
| Validate push (no execute) | `python3 dev/scripts/devctl.py push` |
| Execute governed push | `python3 dev/scripts/devctl.py push --execute` |
| Read latest push report | `cat dev/reports/push/latest_push_report.json` |

### Extend / adopt

| Goal | Command |
|---|---|
| Bootstrap another repo | `python3 dev/scripts/devctl.py governance-bootstrap --target-repo <path> --format md` |
| Export governance | `python3 dev/scripts/devctl.py governance-export --format md` |
| Scan + emit ProjectGovernance for current repo | `python3 dev/scripts/devctl.py governance-draft --format md` |
| Probe-scan a target repo | `python3 dev/scripts/devctl.py probe-report --repo-path <path> --adoption-scan --format md` |
| Adoption-scan check | `python3 dev/scripts/devctl.py check --profile ci --repo-path <path> --adoption-scan --format md` |

## Glossary

**Admissibility:** The question "is this work allowed to advance from the
current repo state?"

**Authority:** The typed source that is allowed to decide a fact or transition.

**Compatibility projection:** A legacy or human-facing surface rendered from
typed state. It can help humans but should not become a second source of truth.

**Guard:** A deterministic blocking check.

**Probe:** An advisory review signal that finds risks without blocking by
default.

**Repo pack:** The repo-specific policy, path, docs, workflow, and generated
surface configuration that lets the portable engine adapt to one repository.

**Review channel:** The typed packet transport and reducer model for
collaboration between agents, operators, and runtime surfaces.

**Run receipt:** A durable record of what command or action ran, what it
decided, and which artifacts prove the result.

**VoiceTerm:** The first adopter and live proof environment for this platform,
not the universal authority for portable governance behavior.

## Surface Provenance

> This guide is itself a projection. It points at typed authority and never
> overrides it. The block below mirrors the projection-only frontmatter that
> the repo's generated surfaces use, so external indexers and projection-drift
> guards can validate this file alongside the others.

| Field | Value |
|---|---|
| `contract_id` | `PlatformGuide` |
| `schema_version` | `1` |
| `surface_id` | `platform_guide_main` |
| `authority_tier` | `4` — reference (per `dev/guides/SYSTEM_MAP.md` §0.7) |
| `projection_only` | `true` |
| `source_of_truth` | `dev/state/plan_index.jsonl`, `dev/state/contract_registry.jsonl`, `dev/state/transition_modules.jsonl`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md` |
| `companion_thesis` | `dev/guides/AI_GOVERNANCE_PLATFORM.md` (durable whitepaper); `dev/active/ai_governance_platform.md` (tracked execution) |
| `command_authority` | `dev/scripts/devctl/cli_parser/entrypoint.py`, `dev/scripts/devctl/bundles/registry.py`, `dev/scripts/devctl/governance/script_catalog_registry.py` |
| `tracked_under` | `MP-GUARDIR-V4-PHASE-0-6-E-INSTRUCTION-SURFACE-USABILITY-S1`, `MP-377` |
| `refresh_command` | `python3 dev/scripts/devctl.py render-surfaces --write --format md` (when promoted to a generated surface) |
| `drift_check` | `python3 dev/scripts/devctl.py docs-check --strict-tooling --format json` |

### How to update this guide

1. Make the smallest change that captures the new fact.
2. Verify the fact is **derivable from tier-1 typed state** (a contract, a
   plan row, a guard, a receipt). If it's not, this guide is not the right
   home — encode it in repo policy, an active doc, or a typed contract first.
3. Run `python3 dev/scripts/devctl.py docs-check --strict-tooling` to confirm
   no projection-drift guards trip.
4. Commit through `devctl commit` so the change carries through the governed
   pipeline.
5. If you renamed sections or added new H2s, update the
   [Contents](#contents) list and any cross-references.

### Known gaps (iteration backlog)

These are deliberate omissions to be filled in subsequent iterations:

- **Worked examples appendix**: real annotated boot transcript, real packet
  post, real receipt — direct copy-paste material.
- **Tutorial quadrant**: a guided "your first governed change" walkthrough
  (Diátaxis tutorial cell).
- **Per-typed-state-file deep reference**: one H3 per `dev/state/*.jsonl` with
  schema, write authority, and read consumers.
- **`devctl` per-subcommand reference**: one H3 per high-traffic subcommand
  with full flag table and exit codes.
- **Promotion to generated surface**: this guide is currently hand-maintained.
  Future closure should register it in `repo_governance.surface_generation.surfaces`
  with a freshness guard, so projection drift is mechanically detected.
