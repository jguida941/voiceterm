# External Research Intake And Scratch-Plan Consolidation (MP-377)

**Status**: archived-reference | **Last updated**: 2026-03-21 | **Owner:** AI governance platform
Execution plan contract: required

Closure note: this file preserves the raw research/audit conclusions that were
first collected in `temp_leftoff.md` while the execution-affecting decisions
were promoted into governed active plans. It is evidence and rationale, not
execution authority.

## Scope

- Preserve the external-research synthesis that informed the 2026-03-21
  `MP-377` authority-loop updates.
- Record which conclusions were promoted into governed active plans and which
  details remain reference-only research context.
- Retire `temp_leftoff.md` as hidden execution state so pushes no longer depend
  on a scratch markdown file.

## Execution Checklist

- [x] Verify the `MP-377` packet/cache conclusions are represented in
      `dev/active/platform_authority_loop.md`.
- [x] Verify the plan-format / markdown self-hosting conclusions are
      represented in `dev/active/platform_authority_loop.md` and
      `dev/active/MASTER_PLAN.md`.
- [x] Verify the review-channel N-agent middle-layer gap is represented in
      `dev/active/review_channel.md` and `dev/active/MASTER_PLAN.md`.
- [x] Verify the AI-push convergence gap is represented in
      `dev/active/portable_code_governance.md` and
      `dev/active/ai_governance_platform.md`.
- [x] Preserve the research rationale in a governed archive doc.
- [x] Mark `temp_leftoff.md` as disposable rather than a required source of
      plan or push truth.

## Progress Log

- 2026-03-21: Audited `temp_leftoff.md` against the current governed plan set
  before a checkpoint push. Conclusion: the active decisions had already been
  promoted into `platform_authority_loop.md`, `review_channel.md`,
  `MASTER_PLAN.md`, `portable_code_governance.md`, and
  `ai_governance_platform.md`, but the raw research transcript still lived only
  in scratch state.
- 2026-03-21: Created this archive record so the raw external-research
  rationale remains repo-owned and discoverable without leaving a hidden
  dependency in the active push path.

## Audit Evidence

- Raw scratch source preserved at the time of consolidation:
  - `temp_leftoff.md` sections `Shared Planning State - ZGraphs /
    Deterministic Layering Intake`
  - `External Repo Audit Setup - Shared Codex / Claude Plan`
  - `Claude Audit Results — Merged Into Shared Plan`
  - `Checkpoint/Push Packet Architecture — Research-Backed Field Mapping`
- Raw parallel Claude findings catalog:
  - `dev/repo_example_temp/CLAUDE_AUDIT_FINDINGS.md`
- Promoted execution authority destinations:
  - `dev/active/platform_authority_loop.md`
  - `dev/active/review_channel.md`
  - `dev/active/MASTER_PLAN.md`
  - `dev/active/portable_code_governance.md`
  - `dev/active/ai_governance_platform.md`

## Promoted Conclusions

### 1. Deterministic least-effort-first is the accepted architecture

The scratch audit converged on the same layered model across the research
repos:

- canonical repo evidence and typed contracts stay authoritative
- deterministic guards/probes/router classify first
- generated `ConceptIndex` / ZGraph-style layers only reduce search space
- bounded startup/context packets reconstruct the minimum cited working slice
- expensive AI loops remain fallback/controller layers

This conclusion is now captured in:

- `dev/active/platform_authority_loop.md` progress/session state
- `dev/active/ai_governance_platform.md` graph/authority boundary
- `dev/active/MASTER_PLAN.md` current architecture notes

### 2. Packet/cache is allowed only as a generated accelerator

The scratch packet architecture section established that checkpoint/push
packets are valid only when they remain:

- generated from canonical git/plan/guard/review truth
- disposable and invalidated by canonical drift
- stored in managed repo artifacts rather than hidden memory
- unable to override authority when stale or missing

The packet field mapping and sequencing are now captured directly in
`dev/active/platform_authority_loop.md`, including:

- tree hash / commit sha
- touched paths + diff stats
- routed plan scope / plan refs
- guard/check summary
- reviewer verdict summary
- checkpoint-budget snapshot
- invalidation metadata
- rolling calibration metrics
- proof envelope

### 3. Plan markdown is governed but still only partially consumed

The scratch audit originally over-called missing architecture. The corrected
result is:

- the repo already has substantial typed governance/runtime contracts
- plan discovery and section enforcement are real
- the remaining gap is semantic consumption and mutation handling

What still remains active follow-up:

- `## Execution Checklist` is the primary structured section consumed today
- `Session Resume`, `Progress Log`, and `Audit Evidence` are still mostly
  markdown restart/evidence surfaces
- plan mutation ops are validated in packet contracts but do not yet have a
  canonical runtime apply path back into governed plan docs

This follow-up is tracked in:

- `dev/active/platform_authority_loop.md`
- `dev/active/MASTER_PLAN.md`

### 4. Native N-agent support is partial, not complete

The scratch audit correctly found that lower layers are more N-agent-ready than
the middle review-channel layer:

- packet routing already uses string agent ids
- `TandemProfile.implementers` and swarm worker counts already scale
- event lanes and packet contracts are not hardwired to exactly two agents

The still-hardcoded middle layer remains:

- queue state (`pending_codex`, `pending_claude`, similar named fields)
- bridge/session fields (`claude_ack`, `codex_poll_state`, singular bridge
  projections)
- fixed routing/allowlist maps
- one-item promotion flow

That tracked follow-up now lives in:

- `dev/active/review_channel.md`
- `dev/active/MASTER_PLAN.md`

### 5. AI pushes must converge on the same governed push path

The scratch audit also identified the split between governed `devctl push`
behavior and raw `git push` in AI-operated flows. That gap is already tracked
in active plans:

- `dev/active/portable_code_governance.md`
- `dev/active/ai_governance_platform.md`

The accepted closure direction is:

- replace raw AI `git push` calls with `devctl push --execute`
- add caller-aware push policy / preflight profiles
- emit the same `TypedAction(action_id="vcs.push")` / `ActionResult` evidence
- carry push outcomes into loop-packet/governance-ledger surfaces

## Research Clusters Preserved

The scratch audit grouped the imported research into four reusable pattern
clusters. The raw repo/file-level details remain reference-only here:

1. Search / frontier reducers:
   - layered rejection filters
   - progressive relaxation
   - determinism baselines
   - density/telemetry-driven presets
2. Prime / proof / verification layers:
   - decision-path tracking
   - prediction logging
   - proof packaging
   - benchmark/fuzz harnesses
3. ZGraph / retrieval / relation systems:
   - relation mapper tuples
   - multi-key caches
   - advisory inference/transform chains
   - metrics/time-series tracking
4. ML tracing / auto-ML / dispatch:
   - structured traces
   - deterministic + ML dual dispatch
   - explicit `UNKNOWN` state
   - benchmark/manifest discipline

These clusters informed the accepted `MP-377` sequencing, but none of their
domain-specific code is authoritative or intended for direct import.
