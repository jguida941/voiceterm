# GuardIR Platform Guide

**Status**: active reference  |  **Last updated**: 2026-04-30 | **Owner:** Tooling/control plane/product architecture

This guide explains the AI governance platform architecture in developer terms:
what the platform is, why it exists, how its state model works, how to use it
in day-to-day engineering, and what is already implemented versus still being
proved under `MP-377`.

Use this guide for the durable architecture and operating model. Use
`dev/active/ai_governance_platform.md` for current execution state and roadmap
tracking, `dev/scripts/README.md` for the command reference, and
`dev/guides/DEVELOPMENT.md` for the exact post-edit check inventory.

## Contents

- [What This Is](#what-this-is)
- [Why It Exists](#why-it-exists)
- [How To Position It](#how-to-position-it)
- [Current Status](#current-status)
- [The Compiler Model](#the-compiler-model)
- [Architecture Layers](#architecture-layers)
- [The Typed State Spine](#the-typed-state-spine)
- [Review Channel And Multi-Agent Work](#review-channel-and-multi-agent-work)
- [Guards, Probes, And Findings](#guards-probes-and-findings)
- [Developer Workflows](#developer-workflows)
- [Extending The Platform](#extending-the-platform)
- [Design Rules](#design-rules)
- [Command Map](#command-map)
- [Glossary](#glossary)

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

> Do not trust a probabilistic system with execution authority when execution
> authority can be compiled from repo evidence and policy.

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

## Developer Workflows

### Start A Session

Run startup first and let the typed packet tell you the next legal action:

```bash
python3 dev/scripts/devctl.py startup-context --format summary
```

Then read the active authority docs for your scope:

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

| Goal | Command |
|---|---|
| Start a session | `python3 dev/scripts/devctl.py startup-context --format summary` |
| Inspect command inventory | `python3 dev/scripts/devctl.py list` |
| Inspect quality policy | `python3 dev/scripts/devctl.py quality-policy --format md` |
| Inspect contracts | `python3 dev/scripts/devctl.py platform-contracts --format md` |
| Run routed checks | `python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute` |
| Run normal CI profile | `python3 dev/scripts/devctl.py check --profile ci` |
| Run tooling docs gate | `python3 dev/scripts/devctl.py docs-check --strict-tooling` |
| Run user-docs gate | `python3 dev/scripts/devctl.py docs-check --user-facing` |
| Build probe packet | `python3 dev/scripts/devctl.py probe-report --format md` |
| Read review-channel status | `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md` |
| Diagnose review-channel readiness | `python3 dev/scripts/devctl.py review-channel --action doctor --terminal none --format md` |
| Commit through governed path | `python3 dev/scripts/devctl.py commit --paths <path>... -m "message"` |
| Validate push | `python3 dev/scripts/devctl.py push` |
| Execute governed push | `python3 dev/scripts/devctl.py push --execute` |
| Regenerate governed surfaces | `python3 dev/scripts/devctl.py render-surfaces --write --format md` |
| Bootstrap another repo | `python3 dev/scripts/devctl.py governance-bootstrap --target-repo <path> --format md` |

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
