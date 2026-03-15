# Portable Code Governance

**Status**: active reference  |  **Last updated**: 2026-03-14 | **Owner:** Tooling/code governance

This guide explains how to treat the current guard/probe stack as a reusable
system instead of a VoiceTerm-only pile of scripts.

This guide stays focused on the portable governance engine and repo-adoption
path. The broader reusable product/package/runtime/frontend architecture now
lives in `dev/active/ai_governance_platform.md`, which is the main active plan
for that scope.
This guide is not a second main plan; when engine work changes the broader
product boundary or extraction sequence, update
`dev/active/ai_governance_platform.md` first and keep this guide subordinate.

## Purpose

The goal is not "AI writes perfect code."

The goal is:

1. AI or human proposes code.
2. Portable guards reject recurring structural hazards.
3. Portable probes rank the remaining design smells.
4. The same artifact stream becomes evaluation data for later benchmark work.

That makes the system a deterministic post-generation control layer for code.

## System Boundary

Use these boundaries consistently:

- Engine:
  `dev/scripts/devctl/`, `dev/scripts/checks/`, and generic templates under
  `dev/config/templates/`
- Portable presets:
  `dev/config/quality_presets/*.json`
- Repo policy:
  `dev/config/devctl_repo_policy.json`
- Repo-only enforcement and documentation:
  `.github/workflows/`, `AGENTS.md`, `dev/active/*.md`, and repo-owned guides

Rules:

1. Another repo should adopt the system by swapping policy/preset files first.
2. Engine edits are only for generic logic that should help more than one repo.
3. Repo-specific layout, allowlists, thresholds, and lane wiring belong in
   repo policy or repo workflows, not in the engine.
4. Guard code must stay at least as structurally clean as the code it enforces.

## Measurement Model

Current runtime telemetry already emits watchdog episode rows under
`dev/reports/autonomy/watchdog/episodes/guarded_coding_episode.jsonl`.

Portable planning needs two schema layers:

- Episode/event schema:
  `dev/config/templates/portable_governance_episode.schema.json`
- Multi-repo evaluation record schema:
  `dev/config/templates/portable_governance_eval_record.schema.json`
- Adjudicated finding-review schema:
  `dev/config/templates/portable_governance_finding_review.schema.json`

Episode fields should cover:

- task metadata
- initial output or diff shape
- guard/probe hits
- repair loop count
- accepted diff summary
- human edit involvement
- test/build/lint outcomes
- later review outcome

The evaluation record should roll those episodes up into before/after deltas
plus judge scores across a repo or task slice.

Use `governance-review` to keep the adjudication layer honest:

```bash
python3 dev/scripts/devctl.py governance-review --format md
python3 dev/scripts/devctl.py governance-review --record --signal-type probe --check-id probe_exception_quality --verdict false_positive --path some/file.py --line 41 --format md
python3 dev/scripts/devctl.py data-science --format md
```

That path gives the repo a durable ledger for:

- false-positive rate by guard/probe
- confirmed-issue rate
- fixed-vs-deferred cleanup progress
- current backlog that still needs human or AI follow-up

## Export Path

Use `governance-export` when the whole governance stack needs to be reviewed
outside the repo or copied into another repo for a pilot.

```bash
python3 dev/scripts/devctl.py governance-export --format md
python3 dev/scripts/devctl.py governance-export --quality-policy dev/config/devctl_repo_policy.json --since-ref origin/develop --head-ref HEAD --format md
python3 dev/scripts/devctl.py governance-export --quality-policy /tmp/pilot-policy.json --adoption-scan --format md
```

Behavior:

- exports outside the repo root only
- copies the governance stack, tests, policy, active docs, and workflows
- generates fresh `quality-policy`, `probe-report`, and `data-science` artifacts
- writes a sibling zip by default for handoff to another model or maintainer

The export fails closed if the destination lives inside the repo because
duplicate-source snapshots inside the tree poison duplication audits.

## Pilot Onboarding Flow

Use this when the target repo is new to the governance stack or was copied from
another checkout:

```bash
python3 dev/scripts/devctl.py governance-bootstrap --target-repo /path/to/copied-repo --format md
cd /path/to/copied-repo
python3 dev/scripts/devctl.py quality-policy --format md
python3 dev/scripts/devctl.py render-surfaces --write --format md
python3 dev/scripts/devctl.py check --profile ci --adoption-scan
python3 dev/scripts/devctl.py probe-report --adoption-scan --format md
python3 dev/scripts/devctl.py governance-export --adoption-scan --format md

# Or run the scan from the engine checkout without `cd`:
python3 /path/to/engine/dev/scripts/devctl.py probe-report --repo-path /path/to/copied-repo --adoption-scan --format md
```

Why these steps exist:

- `governance-bootstrap` repairs copied/submodule `.git` indirection so git-based
  guards can run locally instead of failing on stale `gitdir:` pointers.
- The same bootstrap command now also writes a starter
  `dev/config/devctl_repo_policy.json` when the target repo does not already
  have one, choosing the nearest portable preset from detected Python/Rust
  capabilities and seeding conservative `check-router` / `docs-check`
  repo-governance defaults plus starter
  `repo_governance.surface_generation` policy for local instructions and
  tracked starter artifacts. It now also copies the portable preset JSON files
  into `dev/config/quality_presets/` and writes explicit `quality_scopes` so
  first-run scans do not silently narrow large Python repos to `scripts/` only.
- The same bootstrap command now also writes a repo-local
  `dev/guides/PORTABLE_GOVERNANCE_SETUP.md` guide so an AI or maintainer has
  one obvious file to read inside the adopted repo instead of starting from the
  exported template set alone.
- `render-surfaces --write` materializes the starter instruction/stub surfaces
  owned by that repo-pack policy so adopters begin from generated files instead
  of hand-copying local instructions or workflow stubs.
- `--adoption-scan` treats the full current worktree as the baseline when the
  repo has no trusted historical ref for growth-only checks yet.
- `probe-report` should usually run in the same onboarding mode so the first
  packet ranks the whole repo instead of only a meaningless empty diff.
- When `probe-report` is driven from the engine repo with `--repo-path`, the
  default artifact root now follows the target repo, so the packet lands under
  `<target>/dev/reports/probes/` instead of the engine checkout.
- `probe_compatibility_shims.py` is now the portable stale-wrapper review
  layer: package-layout keeps the structural/baseline contract, while the
  probe ranks missing metadata, expired wrappers, broken shim targets, and
  shim-heavy roots/families without forcing every adopting repo to hard-fail
  that debt on day one.

Starter artifacts exported with the governance stack:

- `dev/config/templates/portable_governance_repo_setup.template.md`
- `dev/config/templates/portable_devctl_repo_policy.template.json`

Use those when an AI or maintainer needs one obvious file set to follow rather
than reverse-engineering the engine layout from the whole repo. After running
`governance-bootstrap`, the repo-local first-read file becomes
`dev/guides/PORTABLE_GOVERNANCE_SETUP.md`.

## Pilot Corpus

The first broad pilot corpus should come from the maintainer GitHub repo set:

- `https://github.com/jguida941?tab=repositories`

Selection rules:

1. Start with repos that have obvious Python and/or Rust sources plus tests.
2. Prefer repos where a repo-local policy file can be added without engine edits.
3. Log every remaining VoiceTerm assumption leak into `MP-376` before widening
   the pilot set.

Current proof point:

- `ci-cd-hub` still anchors the strongest external proof. The early March 14
  narrow rerun (`7` hints) turned out to be a `scripts/`-only under-scan.
  After the corrected portability pass, the same repo now scans `scripts`,
  `_quarantine`, `cihub`, and `tests`, and the March 14 rerun found
  `159` hints (`53 high`, `104 medium`, `2 low`) across `509` source files.
- The corrected 13-repo pilot aggregate is now `311` hints
  (`115 high`, `193 medium`, `3 low`) with `3` clean repos and `0` scan
  errors. The previous `158`-hint aggregate should not be reused as proof.
- Remaining coverage caveat: the portable pack is still Python/Rust only, so
  repos dominated by Java, TypeScript, or React code remain partially covered
  until those language packs exist.

## Evaluation Framework

Do not try to prove "the code is objectively better in all ways."

The measurable claim is narrower:

Code is better designed when behavior is preserved while unnecessary
complexity, hidden failure modes, and review burden go down.

Use this stack:

1. Correctness gate:
   build, tests, lint, type-check, and critical warnings must stay green
2. Objective deltas:
   structure and safety metrics before vs after
3. Pairwise review:
   blind human and/or AI A/B preference on a fixed rubric

Recommended score shape:

```text
FinalScore =
Gate * (
0.30 * ReliabilityScore +
0.40 * MaintainabilityScore +
0.20 * ReviewabilityScore -
0.10 * ChurnPenalty
)
```

Use AI judging only as a secondary signal. The preferred setup is blind A/B
comparison with justification, not free-form "rate this code 1-10" prompting.

## Metrics That Matter

Treat these as the default portable buckets:

- Reliability:
  tests/build/lint/type-check pass rate, warning deltas, runtime error deltas
- Maintainability:
  function/file size, nesting, duplication, broad exceptions, vague errors,
  single-use helpers, dependency fan-out
- Reviewability:
  diff size, files touched, reviewer acceptance, follow-up fixes, pairwise
  preference

Percentile metrics matter. Keep p95 function length and p95 nesting alongside
averages so a few monster functions do not hide inside a healthy mean.

## Guard Promotion Rules

Promote a pattern from probe to hard guard only when all of these are true:

1. The bad pattern repeats in real repo evidence.
2. The pattern is structurally detectable.
3. False-positive risk is low.
4. Cleanup value is material.
5. The rule belongs in the engine or a portable preset, not only here.

Probe-first remains the default rollout.

Portable example:

- Compatibility shims are now a first-class portable governance concept rather
  than a VoiceTerm-only exception. The engine should validate shim shape from
  structure first (AST/minimal wrapper semantics), use text parsing only for
  metadata extraction when needed, and let repo policy decide allowed roots,
  required metadata fields, whether approved shims count toward density, and
  how much shim debt is tolerated.
