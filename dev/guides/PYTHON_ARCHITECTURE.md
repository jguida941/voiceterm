# Python Architecture Decision Tree

**Status**: active reference  |  **Last updated**: 2026-03-27 | **Owner:** Tooling/control plane/product architecture

Use `dev/active/ai_governance_platform.md` for tracked `MP-377` execution
state.
Use this guide for the durable Python modeling and composition rules that the
portable governance platform expects.
It is a companion guide, not a second execution plan.

## Core Rule

Choose the smallest shape that keeps the contract explicit.

- Use plain `dict` only for genuinely dynamic maps.
- Use `TypedDict` for fixed-key serialized packets.
- Use `dataclass` for internal runtime state and most domain records.
- Use boundary-validation models only when data crosses an untrusted or
  serialized boundary.
- Use `Protocol` for behavior and dependency seams, not for data bags.

Internal runtime code should stay mostly on stdlib typing plus `dataclass`.
Pydantic and similar boundary-model libraries are for parsing and validating
outside inputs, then converting them into internal contracts early.

## Decision Tree

1. Is the data arriving from an untrusted or serialized boundary such as JSON,
   CLI/env input, files, subprocess output, MCP payloads, or network I/O?
   If yes, validate it at the boundary, reject extra or malformed fields, then
   convert it into an internal `dataclass` or `TypedDict`.
2. Are the keys open-ended or user-defined?
   If yes, keep a `dict[str, T]` or `Mapping[str, T]`.
3. Is the shape a fixed-key packet whose main job is serialization,
   projection, or interop?
   If yes, use `TypedDict`.
4. Is the shape internal runtime state, a domain record, or something with
   invariants/defaults/helpers?
   If yes, use `dataclass`.
5. Do multiple implementations need to satisfy one behavioral contract?
   If yes, define a `Protocol` and inject that dependency from the composition
   root.

If more than one answer seems true, prefer this priority:

1. Boundary model at the trust edge.
2. `dataclass` inside the runtime.
3. `TypedDict` for machine-facing packets or renders.
4. `dict` only when the key space is genuinely flexible.

## Shape Guide

| Shape | Use it when | Avoid it when |
|---|---|---|
| `dict` | keys are dynamic, map-like, or pass-through | the keys are fixed and you are really hiding a struct |
| `TypedDict` | fixed-key JSON/report/receipt payloads, optional fields need names, machine projections | the object wants behavior, invariants, or non-trivial constructors |
| `dataclass` | internal runtime state, domain records, decision inputs/outputs, test fixtures | the object is only a thin wire-format shell |
| Boundary-validation model | external/untrusted input needs strict parsing, coercion policy, or JSON Schema | the model would leak deep into internal runtime call chains |
| `Protocol` | multiple adapters/services implement one capability and callers should depend on behavior | you only need a concrete helper or simple function argument |

## Boundary Pattern

Keep validation at the edge and convert immediately.

```python
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict


class StartupReceiptModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    command: str
    checkpoint_budget: int


@dataclass(frozen=True)
class StartupReceipt:
    command: str
    checkpoint_budget: int


def parse_startup_receipt(payload: dict[str, object]) -> StartupReceipt:
    boundary = StartupReceiptModel.model_validate(payload)
    return StartupReceipt(
        command=boundary.command,
        checkpoint_budget=boundary.checkpoint_budget,
    )
```

Why this is the default pattern:

- boundary code stays strict and explicit about bad input
- internal runtime code stays lightweight and predictable
- tests can construct internal records without bringing in boundary machinery
- adapters can emit JSON Schema without making the whole runtime depend on it

## Repository, Service, Unit Of Work, Dependency Injection

Use architecture patterns only when they clarify ownership.

### Repository

Use a repository when the same domain object can come from different storage
mechanisms and callers should not know whether it came from JSON, markdown,
SQLite, or generated artifacts.

- Repository returns domain/runtime objects, not raw storage dicts.
- Repository owns lookup and persistence details.
- Repository should usually satisfy a `Protocol`.

### Service

Use a service for one use case that coordinates multiple repositories,
policies, and adapters.

- Service should speak in domain/runtime contracts.
- Service should not parse raw JSON or shell output itself if an adapter can
  do that first.
- Service should not reach into global module state for dependencies.

### Unit Of Work

Use a unit of work when several writes must succeed or fail together.

- Good fit: one command updates plan state, review state, and artifact output
  as one logical mutation.
- Bad fit: read-only reporting paths or one-off helpers that touch a single
  file.

### Dependency Injection

Build concrete dependencies at the composition root, then pass behavior inward
through constructors or function parameters.

- Command entrypoints and adapters are the composition root.
- Inner runtime code should accept `Protocol`-shaped dependencies.
- Avoid module-global singletons unless the dependency is truly process-wide
  and immutable.

```python
from dataclasses import dataclass
from typing import Protocol


class PlanRegistry(Protocol):
    def resolve(self, plan_id: str) -> str: ...


@dataclass
class RoutingService:
    registry: PlanRegistry

    def route(self, plan_id: str) -> str:
        return self.registry.resolve(plan_id)
```

## Current Repo Priority Mapping

Use Cosmic Python vocabulary as a mapping aid, not as a rewrite order.

### Keep And Strengthen

- frozen `dataclass` value-object style for internal runtime contracts
- service/use-case orchestration in command/runtime layers
- CQRS-style projections where one typed state feeds several read views
- append-only event history reduced to one current typed state

### Adopt Next

- inject `repo_root` / repo-pack authority instead of reaching for
  `REPO_ROOT` or `voiceterm_repo_root()`
- move JSON/git/filesystem access behind `Protocol`-shaped repositories that
  return typed runtime/domain objects
- replace fixed-shape governance-ledger `dict[str, Any]` rows with typed
  records
- add narrow aggregate / unit-of-work ownership where one logical mutation
  must keep finding, decision, review, and current-session state consistent
- move subprocess/git lookups out of inner runtime code and into adapters or
  composition-root helpers
- execute `validation_plan` as real post-fix proof, not as documentation only
- treat contract testing as a first-class boundary tool with explicit marker
  routing and failure-to-finding normalization
- use strict boundary-validation models for receipt/trace/failure packets,
  then convert immediately into frozen runtime dataclasses
- compile selected plan truth into a typed expectation packet before
  validating runtime behavior against it

### Defer Or Reject

- global message-bus indirection on the main CLI authority path
- formal CQRS registries when existing projections are already clear
- ABC-heavy hierarchies where `Protocol` is enough
- letting observed behavior silently become plan truth

## AI With Source Docs

External docs are reference material. Repo plans, typed contracts, and
governed runtime evidence remain authority.

Use this workflow:

1. extract the concept from the source material
2. map it to existing repo files, types, and contracts
3. mark it `adopt`, `defer`, or `reject`
4. define one bounded implementation slice plus the guard/test that proves it
5. when plan truth and observed behavior disagree, emit a finding instead of
   silently rewriting the plan

## Practical Defaults

- Default to `@dataclass(frozen=True)` for small internal records that should
  not mutate.
- Use mutable dataclasses only when the runtime genuinely owns stateful
  updates.
- Use `TypedDict` for packet/render/export shapes that need named optional
  fields and stable serialization contracts.
- Keep `dict[str, object]` at boundaries narrow and short-lived.
- Prefer small functions plus typed records over giant helper dicts with
  string-key lookups.
- If a function returns a fixed-shape dict with many named fields, that is
  usually a `TypedDict` or `dataclass` candidate.

## Anti-Patterns

- Treating `dict[str, object]` as the default internal model for fixed-shape
  runtime state.
- Passing Pydantic models deep through the runtime instead of converting them
  at the edge.
- Returning raw storage payloads from repositories.
- Hiding process-wide dependencies in module globals when a constructor
  parameter would make the contract explicit.
- Creating a `Protocol` for a single concrete helper that has no real
  substitution need.

## Review Questions

Before adding or changing a Python shape, ask:

1. Is this data internal runtime state or a boundary payload?
2. Are the keys fixed and named, or truly open-ended?
3. Does the caller need behavior or only data?
4. Where should validation happen once, instead of being repeated everywhere?
5. Should this dependency be abstracted as a `Protocol`, or is one concrete
   collaborator enough?

## Starter Reading Spine

- Cosmic Python, Chapters 1-6, 8, and 13
  (`https://www.cosmicpython.com/book/preface.html`)
- Official Python typing documentation
- Pydantic strict mode and JSON Schema docs
- FastAPI docs on boundary/request-response models

Read those as implementation guides for this repo's contract-first style, not
as a license to make every internal Python object a framework model.
