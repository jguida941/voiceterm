# Governed Plan Format

**Status**: active reference  |  **Last updated**: 2026-03-21 | **Owner:** Tooling/control plane/product architecture

This reference defines the canonical markdown shape for governed active-plan
docs. It exists to close the self-hosting gap under `MP-377`: the platform is
already enforcing typed contracts and deterministic evidence in code, so the
active-plan markdown layer must be consistent enough for `check_active_plan_sync`,
`doc-authority`, and the future `PlanRegistry` / `PlanTargetRef` loader to
consume without brittle prose scraping.

This file is reference-only. Execution sequencing stays in
`dev/active/MASTER_PLAN.md`, `dev/active/ai_governance_platform.md`, and
`dev/active/platform_authority_loop.md`.

## Purpose

Use one shared markdown contract for governed execution-plan docs so:

1. the existing docs-governance stack can validate plans without ad hoc rules,
2. fresh AI sessions can find the current slice in a predictable place,
3. future `PlanRegistry` / `PlanTargetRef` code can promote reviewed markdown
   into typed startup authority without custom parsers per plan,
4. repo adoption does not depend on VoiceTerm-specific markdown habits.

## Base Contract

The current blocking contract for any active execution-plan doc is:

1. One parseable metadata header in the first 10 lines.
   Accepted today: the repo-owned metadata formats already parsed by
   `doc-authority` (`**Status** ...`, `Status: ...`, or the date-first
   compatibility style still used by legacy plans).
2. The marker line `Execution plan contract: required`.
3. These top-level sections in canonical order:
   - `## Scope`
   - `## Execution Checklist`
   - `## Progress Log`
   - `## Session Resume`
   - `## Audit Evidence`
4. The plan must be registered in `dev/active/INDEX.md`, mirrored in
   `dev/active/MASTER_PLAN.md` when it carries execution state, and stay under
   the existing active-doc governance path.

`Session Resume` is part of the blocking contract because active-plan markdown
is the canonical restart state for substantive AI sessions in this repo.

## Conditional Sections

Add extra governed sections only when the plan actually owns that surface.

- `## Data Contracts`
  Required when the plan defines, freezes, or consumes typed runtime artifacts
  or packet/schema families.
- dependency or handoff metadata
  Add upstream/downstream contract notes when the plan feeds or consumes other
  tracked execution lanes.

Do not add empty decorative sections just to satisfy a template.

## Canonical Template

```md
# Plan Title

**Status**: active  |  **Last updated**: 2026-03-21 | **Owner:** Tooling/lane
Execution plan contract: required
Short authority note and tracker mirror sentence.

## Scope

One concise paragraph describing what this plan owns.

## Execution Checklist

- [ ] Current open item
- [x] Closed item

## Progress Log

- 2026-03-21: Recorded a bounded change with concrete effect.

## Session Resume

- Current status: one sentence.
- Next action: one bounded next slice.
- Context rule: what a fresh session should load first.

## Audit Evidence

- Guard/test/doc evidence goes here.
```

## Migration Rules

Use this migration order:

1. extend the existing active-plan sync/docs-governance path instead of adding
   a second parallel plan-format workflow,
2. upgrade all execution-plan docs already on the active-plan contract,
3. migrate legacy active specs that still live outside the execution-plan
   marker/section contract,
4. only after the markdown contract is stable, build the typed `PlanRegistry`
   / `PlanTargetRef` loader on top of it.

Current legacy active-spec debt still outside the full execution-plan contract:

- `dev/active/devctl_reporting_upgrade.md`
- `dev/active/memory_studio.md`

## Non-Goals

- This file does not replace `MASTER_PLAN` as tracker authority.
- This file does not make markdown the runtime authority.
- This file does not require every plan to invent new metadata beyond what the
  current docs-governance parser can already read.
