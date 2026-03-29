# Universal System Plan Intake Review

**Status**: active reference  |  **Last updated**: 2026-03-22 | **Owner:** Tooling/control plane/product architecture

This file is a reference-only companion for the shared worktree. It is not a
tracked execution plan, not a second tracker, and not a replacement authority
for `dev/active/MASTER_PLAN.md` or the `MP-377` spec chain.

Use it as audited intake for portability, self-governance, onboarding, guard
quality, and security follow-up. Accepted conclusions must be mirrored into the
tracked plan docs before implementation or review.

## Authority Rule

Canonical execution authority remains:

1. `dev/active/MASTER_PLAN.md`
2. `dev/active/ai_governance_platform.md`
3. `dev/active/platform_authority_loop.md`
4. `dev/active/portable_code_governance.md`
5. `dev/active/review_probes.md`

The current repo-aligned authority spine is:

`ProjectGovernance -> RepoPack -> DocPolicy / DocRegistry -> PlanRegistry -> PlanTargetRef -> startup-context -> WorkIntakePacket -> CollaborationSession -> TypedAction -> ActionResult / RunRecord / Finding -> ContextPack`

This companion must not create a parallel plan, front-load work ahead of that
spine, or redefine the governed-markdown contract away from the tracked
architecture.

## Summary Verdict

The original universal-system draft contained valuable audit material, but it
was not aligned enough to use as a tracked plan. The main corrections are:

- Keep this file reference-only instead of moving it into `dev/active/`.
- Keep local research companions local/reference-only unless they are promoted
  deliberately into tracked docs.
- Preserve the accepted `MP-377` order: blocker tranche first, then startup
  authority, repo-pack activation, typed registries/intake/session closure,
  then later self-governance/security/graph widening follow-ons.
- Treat governed markdown as a typed-runtime source through
  `ProjectGovernance`, `DocPolicy`, `DocRegistry`, and `PlanRegistry`, not as a
  cleanup-only or frontmatter-only exercise.
- Correct stale or false claims before using any section as evidence.

## Part-By-Part Disposition

| Part | Topic | Disposition | Canonical Home | Notes |
|------|-------|-------------|----------------|-------|
| 1 | Root directory cleanup | Rewrite + partial promote | `platform_authority_loop.md`, `MASTER_PLAN.md` | Keep the self-hosting cleanup idea, but do not move this file into `dev/active/` and do not treat root cleanup as the top priority ahead of the authority spine. |
| 2 | Documentation organization | Rewrite + partial promote | `platform_authority_loop.md`, `ai_governance_platform.md` | Keep doc-class/placement ideas only insofar as they flow through `DocPolicy` / `DocRegistry`, not as a separate docs-only roadmap. |
| 3 | Markdown format consistency | Rewrite + partial promote | `PLAN_FORMAT.md`, `platform_authority_loop.md` | Keep parseable metadata and governed-doc coverage; do not replace the inline metadata standard with mandatory YAML frontmatter. |
| 4 | Portability | Keep + promote | `platform_authority_loop.md`, `portable_code_governance.md` | Dead path activation, VoiceTerm leakage, repo-pack/policy opt-in, and bootstrap gaps remain valid after correcting stale counts. |
| 5 | Self-governance | Keep + promote | `platform_authority_loop.md`, `MASTER_PLAN.md` | Keep the "prove on own repo first" rule, but subordinate organization guards and metadata coverage to the blocker tranche and first typed startup proof. |
| 6 | Universal doc ingestion | Keep + promote | `portable_code_governance.md`, `platform_authority_loop.md` | Strongly aligned. Normalize on ingest, do not force source reformatting. |
| 7 | Industry standards integration | Rewrite | `portable_code_governance.md` | `markdownlint` and OpenSSF Scorecard already exist. Frontmatter is optional future ingest support, not the mandatory standard. |
| 8 | Proving it works | Rewrite + promote | `portable_code_governance.md`, `platform_authority_loop.md` | Keep self-hosting proof, external repo proof, and onboarding/template validation, but sequence them behind the authority spine. |
| 9 | "What Codex already did" | Drop | N/A | Stale context only. This should not stay as active planning material. |
| 10 | Priority order | Drop | N/A | Superseded by the tracked `MP-377` / `MP-376` ordering. |
| 11 | Architecture gap analysis | Rewrite + partial promote | `ai_governance_platform.md`, `platform_authority_loop.md` | Keep the validated portability/self-hosting gaps, but correct stale numbers and remove claims that tracked features are missing when they are already landed. |
| 12 | What the plans should add | Promote selectively | `MASTER_PLAN.md`, per-spec docs | Valid only after breaking items into the right tracked owners. |
| 13 | Universal system architecture | Rewrite + promote | `ai_governance_platform.md`, `platform_authority_loop.md`, `portable_code_governance.md` | Keep the universal-adopter scenarios, but frame them around `ProjectGovernance` / repo-pack / typed startup/session authority. |
| 14 | Cross-plan conflict and gap analysis | Rewrite | existing plan docs | Some items were valid intake, but several conflicts were already partially resolved and were overstated in the original draft. |
| 15 | Missing plan categories | Rewrite + selective promote | `portable_code_governance.md`, `review_probes.md`, `MASTER_PLAN.md` | Some categories are already partially tracked; others belong as bounded follow-ups rather than a new master plan. |
| 16 | AI code quality / feedback loop | Keep + promote | `review_probes.md` | Strong keep. Probe `ai_instruction`, failure context, attribution/fix archive, and learning-loop closure are real gaps. |
| 17 | Package modularization quality | Keep as reference | `portable_code_governance.md` when relevant | Useful supporting evidence, but not a new top-level plan by itself. |
| 18 | Updated priority order | Drop | N/A | Superseded by tracked order. |
| 19 | Success criteria | Rewrite + partial promote | per tracked owner | Keep corrected success criteria only where owned by tracked plans. |
| 20 | Deferred work / decision tracking gaps | Keep + selective promote | `MASTER_PLAN.md` or later self-governance lane | Useful intake, but separate from the immediate authority spine. |
| 21 | Rust code organization | Drop from this companion | N/A | Out of scope for the universal-plan companion except where it blocks portability or contracts. |
| 22 | Critical gaps before extraction | Rewrite + selective promote | `portable_code_governance.md`, `MASTER_PLAN.md` | Some gaps are valid; others were factually wrong (`--offline`, `SECURITY.md`, `disabled_guards`, Scorecard). |
| 23 | `devctl init` design | Keep + promote | `portable_code_governance.md` | Good direction for onboarding/init once tied to typed governance/intake contracts. |
| 24 | Updated final priority order | Drop | N/A | Superseded by tracked order. |

## Corrected Facts

The following original claims were corrected during review:

- Root markdown count was stale. The current shared worktree had 11 root `.md`
  files during review, not 10.
- `set_active_path_config()` having zero external callers was confirmed and
  remains a valid portability finding.
- VoiceTerm-leakage counts were directionally right but numerically stale. The
  problem is real; the old counts should not be reused as canonical evidence.
- The current governed-markdown standard is parseable inline metadata plus
  typed normalization, not mandatory YAML frontmatter.
- `check --offline`, `.github/SECURITY.md`, OpenSSF Scorecard, and a documented
  `disabled_guards` contract already exist, so those must not be described as
  entirely missing.
- `MP-375` / `MP-376` ownership and operator-console/memory boundaries were
  more explicit in tracked docs than the original draft claimed.

## Accepted Promotions Into Tracked Plans

The accepted conclusions from the original draft were promoted into tracked
plan state in these buckets:

### `MP-377` / authority-loop follow-up

- Treat VoiceTerm self-hosting proof as part of portability proof, not just
  external adopter proof.
- Keep docs-organization / governed-doc coverage work as a subordinate
  self-governance layer under `DocPolicy` / `DocRegistry`, not a parallel doc
  cleanup project.
- Keep repo-pack/path-authority cleanup, explicit startup authority, and
  non-VoiceTerm adopter proof on the tracked authority spine.

### `MP-376` / portable-engine and onboarding follow-up

- Keep onboarding/init/template-repo work as real follow-up scope.
- Keep format-agnostic doc ingestion and normalization as a real adoption path.
- Keep multi-repo benchmark automation as explicit proof work.
- Keep portable security / guard-quality hardening as a bounded engine/adoption
  lane instead of a free-floating audit wishlist.

### `MP-375` / probe-feedback-loop follow-up

- Wire probe `ai_instruction` into AI remediation surfaces.
- Carry failed-fix context into retries so repeated bad repairs do not loop.
- Add attribution/fix-strategy memory for guards/probes/repairs.
- Add lifecycle/meta-governance ownership for probes and guards.

## Explicit Drops

The following original recommendations are rejected in this companion:

- Moving this file into `dev/active/` as a tracked execution plan.
- Moving `GUARD_AUDIT_FINDINGS.md` or `ZGRAPH_RESEARCH_EVIDENCE.md` into
  tracked guides by default.
- Making YAML frontmatter the required governed-markdown standard.
- Replacing the tracked `MP-377` / `MP-376` queue with a cleanup-first order.
- Treating already-landed features as still missing without revalidation.

## How To Use This File Now

1. Read this file only as reference intake.
2. Use the tracked plan docs for execution authority.
3. Promote any future accepted conclusions into the proper tracked owner:
   `MASTER_PLAN`, `ai_governance_platform`, `platform_authority_loop`,
   `portable_code_governance`, or `review_probes`.
4. Do not turn this file into a second tracker.
