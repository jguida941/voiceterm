# Portable Code Governance Plan

**Status**: active  |  **Last updated**: 2026-04-15 | **Owner:** Tooling/code governance
Execution plan contract: required
This spec remains execution mirrored in `dev/active/MASTER_PLAN.md` under
`MP-376`. It is the narrower engine/adoption companion to
`dev/active/ai_governance_platform.md`, not a peer architecture authority for
the full standalone governance product.

Do not use this file as a second main plan for the product. Keep cross-product
architecture, documentation-consolidation, extraction sequencing, and
standalone-repo boundary decisions in `dev/active/ai_governance_platform.md`,
then use this file only for deeper engine/adoption detail within that frame.

## Scope

Turn the current VoiceTerm guard/probe/report stack into a reusable code-governance
engine that can be pointed at arbitrary repositories without editing the engine
itself. The goal is deterministic structural governance for AI-assisted coding:
guards reject recurring bad pattern families, probes rank the remaining design
smells, and the same artifact stream becomes evaluation data for later retrieval
and training work.

The broader "full reusable product" extraction now lives in
`dev/active/ai_governance_platform.md`, which is the main active plan for that
scope. This plan stays narrower on purpose: portable engine boundaries, repo
policy/preset layering, measurement/data capture, external-repo rollout, and
export/bootstrap packaging for off-repo analysis.

This scope is broader than `dev/active/review_probes.md`. That spec still owns
probe implementation and operator-facing review artifacts. This plan owns the
portable-engine boundary, repo-policy/preset layering, measurement/data capture,
external-repo rollout, and export/snapshot packaging for off-repo analysis.

### Strategic outcome

1. Separate engine from repo policy cleanly enough that another repo can adopt
   the same system by swapping policy/preset files instead of editing Python
   orchestration code.
2. Hold guard code to the same or stricter structural standard than guarded code;
   path budgets are temporary stabilization bridges, not the target state.
3. Capture enough run data to evaluate whether the system materially improves
   AI-assisted code quality over time without quietly demanding unsustainable
   prompt/context volume.
4. Package the system and its reports cleanly enough that a reasoning model or a
   maintainer can inspect the full governance stack outside this repo.

## Ownership Split

| Concern | Owner doc | This plan's role |
|---|---|---|
| Canonical docs-authority/runtime split and platform-vs-client boundary | `dev/active/ai_governance_platform.md` | consume the architecture contract; do not replace it |
| Startup authority, `DocPolicy` / `DocRegistry`, fail-closed defaults, push packet truth | `dev/active/platform_authority_loop.md` | prove the contract works on adopters instead of redefining it |
| Custom-layout proof, optional-capability proof, organization proof, and adopter-facing push semantics | `dev/active/portable_code_governance.md` | this file owns the external-adopter proof and portability evidence |

## Second-Repo Proof Ladder

Portable claims should graduate through this ladder, not through self-hosting
confidence alone.

1. Empty-repo bootstrap succeeds from repo-pack/policy inputs.
2. Custom-layout repo with non-VoiceTerm authority filenames/roots stays
   fail-closed and green without core patches.
3. Existing mixed-language repo can draft/ratify governance and run the routed
   base checks from the same engine.
4. Repo with tandem/review disabled stays green without inheriting
   bridge/review-only assumptions.
5. One real external repo runs the same bootstrap/startup/check path and emits
   reviewed evidence.
6. No core-engine patches are required between adoptions.
7. Drift guards and portability fixtures remain green after each additional
   adopter or layout proof.

## External Python Corpus Protocol

Two repos are enough to expose real engine bugs and seed regression anchors.
They are not enough to claim "works on any repo." Keep the portability proof
honest with one governed external Python corpus loop:

1. Keep a visible external Python repo matrix in this plan instead of relying
   on one-off chat notes or memory.
2. Run the same adoption path on every repo:
   - `python3 dev/scripts/devctl.py governance-bootstrap --target-repo <path> --force-starter-policy --format md`
   - `python3 dev/scripts/devctl.py probe-report --repo-path <path> --adoption-scan --format json`
   - `python3 dev/scripts/devctl.py check --profile ci --repo-path <path> --adoption-scan --format json`
3. Classify every failure before importing findings:
   - `engine_bug`: crash, VoiceTerm path/policy leakage, wrong-repo writes,
     repo-layout dependence, or other core-engine portability miss.
   - `adopter_finding`: the engine run is honest and the result is about the
     target repo's code, policy, or layout.
4. Fix engine bugs here immediately, then rerun the newly failing repo plus
   every previously tested repo in the matrix before widening portability
   claims.
5. Only import or adjudicate adopter findings after the engine path is clean
   on that repo:
   - raw findings -> `governance-import-findings`
     (`--input-format md` for `LIVE_RUN.md` compatibility intake; repo-scoped
     `repo_name:Q-ID` sync ids keep repeated imports stable)
   - adjudicated outcomes -> `governance-review --record`
6. If the remaining failures reduce to Step 0/startup or governed push, treat
   them as blocking architecture work under `MP-377`, not as "portable
   enough."

## External Python Repo Matrix

| Repo | Local path | Current honest run state | Engine defects exposed here | Remaining blocker |
|---|---|---|---|---|
| `ci-cd-hub` | `/tmp/ci-cd-hub-governance-proof` | `governance-bootstrap`, `probe-report --repo-path --adoption-scan`, and `check --profile ci --repo-path --adoption-scan` complete without new core patches after the latest reruns. | None unique in the latest rerun; keep as a regression anchor after future engine fixes. | Step-0 `startup-context` and governed push still require target-local/exported authority proof. |
| `adaptive-hashmap-studio` | `/tmp/adaptive-hashmap-studio-governance-proof` | Same engine-run path is now honest after the latest fixes and reruns. | Valid Python signature scan crash and VoiceTerm-only code-shape override leakage fixed in `19ca688`; packaged-check/root-shim portability break fixed in `52ed830`. | Same Step-0 `startup-context` and governed push blocker. |
| `zgraph-scientific-package` | `/tmp/zgraph-scientific-package-governance-proof` | Wave 1 complete: `governance-bootstrap`, `probe-report`, and `check` all ran; `268` probe hints across `28` files. Classified as `adopter_finding`. | None new; governed path stayed target-local for the full run. | No engine-side blocker. Optional next work is adopter finding import/adjudication for code shape, broad exceptions, subprocess policy, and large-file topology debt. |
| `vector_space` | `/tmp/vector-space-governance-proof` | Seeded clean clone; held as the first maintainer reserve behind Wave 1. | None yet; governed path not run. | Wave 1 capacity intentionally capped at five repos. |
| `mkgui` | `/tmp/mkgui-governance-proof` | Wave 1 complete: `governance-bootstrap`, `probe-report`, and `check` all ran; `155` probe hints across `16` files. Classified as `adopter_finding`. | None new; governed path stayed target-local for the full run. | No engine-side blocker. Optional next work is adopter finding import/adjudication for code shape, broad exceptions, subprocess policy, and inspector/CLI complexity debt. |
| `MemLite` | `/tmp/memlite-governance-proof` | Seeded clean clone; held as the second maintainer reserve. | None yet; governed path not run. | Wave 1 capacity intentionally capped at five repos. |
| `requests` | `/tmp/requests-governance-proof` | Wave 1 complete: `governance-bootstrap`, `probe-report`, and `check` all ran; `154` probe hints across `11` files. Classified as `adopter_finding`. | None new; governed path stayed target-local for the full run. | No engine-side blocker. Optional next work is adopter finding import/adjudication for code shape, broad exceptions, suppression debt, and facade wrappers. |
| `interactions.py` | `/tmp/interactions-py-governance-proof` | Wave 1 complete: `governance-bootstrap`, `probe-report`, and `check` all ran; `508` probe hints across `79` files. Classified as `adopter_finding`. | None new; governed path stayed target-local for the full run. | No engine-side blocker. Optional next work is adopter finding import/adjudication for code shape, broad exceptions, parameter-count pressure, and facade-wrapper/cyclic-import debt. |
| `yamllint` | `/tmp/yamllint-governance-proof` | Seeded clean clone; held as the next external mainstream reserve. | None yet; governed path not run. | Wave 1 capacity intentionally capped at five repos. |
| `pre-commit-hooks` | `/tmp/pre-commit-hooks-governance-proof` | Wave 1 complete: `governance-bootstrap`, `probe-report`, and `check` all ran; `75` probe hints across `33` files. Classified as `adopter_finding`. | None new; governed path stayed target-local for the full run. | No engine-side blocker. Optional next work is adopter finding import/adjudication for duplication, nesting, dict-schema, and structural-similarity debt. |

Do not treat the two rows above as generality proof. They are the current
adversarial samples and regression anchors for the next corpus expansion.

## Current Corpus-First Execution Order

For the current portability slice, do this before widening broader product or
architecture work that is not needed to interpret corpus failures:

1. Checkpoint the current plan/docs slice so startup authority stops failing on
   dirty-after-checkpoint state.
2. Seed the first fixed Python anchor corpus and record it in the repo matrix.
3. Resume future corpus waves at `3` repos at a time; only widen back toward
   `5` once one clean wave adds no new `engine_bug` class.
4. Stop the wave immediately on the first new `engine_bug`.
5. Fix that engine bug here, rerun the failing repo plus every previously green
   anchor repo, and only then resume widening.
6. If the remaining failures reduce to Step-0/startup or governed push, stop
   adding repos and close those `MP-377` blockers before widening again.
7. Only after `2-3` consecutive waves add no new engine-bug class and all
   current anchors still rerun clean should this lane describe the engine as
   "broadly working so far." Do not call that universal proof.

## Initial Anchor-Corpus Shape

Build one fixed Python anchor corpus before the exploratory queue grows:

| Bucket | Target count | Why it exists |
|---|---:|---|
| Maintainer-source Python repos | `3-4` | Useful seed corpus and likely to expose repeated assumptions shared across the maintainer's own repos. |
| External mainstream Python repos | `3-4` | Pressure-test the engine against repos that do not share local conventions or repo-pack history. |
| External adversarial/weird Python repos | `1-2` | Force unusual layouts, docs roots, test roots, or mixed tooling assumptions to surface quickly. |
| Existing regression anchors | `2` | Keep `ci-cd-hub` and `adaptive-hashmap-studio` in every rerun set after engine fixes. |

Seeded 2026-04-02 anchor set:

| Bucket | Selected repos | Why this seed is useful |
|---|---|---|
| Maintainer-source Python repos | `zgraph-scientific-package`, `vector_space`, `mkgui` | Covers a requirements-only package, an app/docs/scripts repo, and a `src/` layout package without depending on VoiceTerm-specific authority. |
| Maintainer-source reserve | `MemLite` | Keep one fourth maintainer repo ready if the first three miss a shape that matters before broader widening. |
| External mainstream Python repos | `requests`, `interactions.py`, `yamllint` | Covers a classic `src/` package, a larger docs/tests-heavy library, and a real lint/tooling repo that does not share the maintainer's repo-pack history. |
| External adversarial/weird Python repos | `pre-commit-hooks` | Deliberately exercises a hook-script repo with many small entrypoints and detached-head cache provenance. |
| Existing regression anchors | `ci-cd-hub`, `adaptive-hashmap-studio` | Preserve the already-proven adversarial samples as the rerun set after any new engine fix. |

Selection rule:

1. Do not overfit the first anchor set to one owner or one repo shape.
2. Prefer repos that are real enough to have layout/documentation/test
   conventions, not only tiny toy samples.
3. Keep an exploratory queue outside the fixed anchors, but do not widen into
   it while the current wave still has an unfixed `engine_bug`.

## Anchor Corpus Seed Queue

Fill these slots before widening into a larger exploratory queue:

| Slot | Source bucket | Repo | Local path | Current status |
|---|---|---|---|---|
| `anchor-existing-01` | existing regression anchor | `ci-cd-hub` | `/tmp/ci-cd-hub-governance-proof` | active anchor |
| `anchor-existing-02` | existing regression anchor | `adaptive-hashmap-studio` | `/tmp/adaptive-hashmap-studio-governance-proof` | active anchor |
| `anchor-maintainer-01` | maintainer-source Python | `zgraph-scientific-package` | `/tmp/zgraph-scientific-package-governance-proof` | seeded clean clone; Wave 1 order `1` |
| `anchor-maintainer-02` | maintainer-source Python | `vector_space` | `/tmp/vector-space-governance-proof` | seeded clean clone; reserve behind Wave 1 |
| `anchor-maintainer-03` | maintainer-source Python | `mkgui` | `/tmp/mkgui-governance-proof` | seeded clean clone; Wave 1 order `2` |
| `anchor-maintainer-04` | maintainer-source Python | `MemLite` | `/tmp/memlite-governance-proof` | seeded clean clone; optional reserve |
| `anchor-external-01` | external mainstream Python | `requests` | `/tmp/requests-governance-proof` | seeded clean clone; Wave 1 order `3` |
| `anchor-external-02` | external mainstream Python | `interactions.py` | `/tmp/interactions-py-governance-proof` | seeded clean clone; Wave 1 order `4` |
| `anchor-external-03` | external mainstream Python | `yamllint` | `/tmp/yamllint-governance-proof` | seeded clean clone; reserve behind Wave 1 |
| `anchor-external-04` | external mainstream Python | no fourth mainstream repo selected in fixed v1 corpus | slot intentionally held open | add only if the current three mainstream anchors miss a clear shape |
| `anchor-adversarial-01` | external adversarial/weird Python | `pre-commit-hooks` | `/tmp/pre-commit-hooks-governance-proof` | seeded clean clone; Wave 1 order `5` |
| `anchor-adversarial-02` | external adversarial/weird Python | no second weird repo selected in fixed v1 corpus | slot intentionally held open | add only if the current weird anchor misses a clear shape |

## Wave 1 Setup

Wave 1 is intentionally capped at five repos so a new `engine_bug` stops the
slice quickly instead of turning the first portability pass into open-ended
noise.

| Order | Repo | Source bucket | Local path | Why it is in Wave 1 | Current status |
|---|---|---|---|---|---|
| `1` | `zgraph-scientific-package` | maintainer-source Python | `/tmp/zgraph-scientific-package-governance-proof` | Requirements-driven maintainer repo with docs/tests but no `pyproject.toml`. | completed; classified `adopter_finding` |
| `2` | `mkgui` | maintainer-source Python | `/tmp/mkgui-governance-proof` | `src/` layout maintainer package with tests and packaging metadata. | completed; classified `adopter_finding` |
| `3` | `requests` | external mainstream Python | `/tmp/requests-governance-proof` | Mainstream external `src/` package with docs/tests and no maintainer-local history. | completed; classified `adopter_finding` |
| `4` | `interactions.py` | external mainstream Python | `/tmp/interactions-py-governance-proof` | Larger external library to pressure-test docs/tests-heavy assumptions. | completed; classified `adopter_finding` |
| `5` | `pre-commit-hooks` | external adversarial/weird Python | `/tmp/pre-commit-hooks-governance-proof` | Weird hook-script topology with many small entrypoints. | completed; classified `adopter_finding` |

Wave 1 result (2026-04-02): no new `engine_bug`. All five repos completed the
governed bootstrap/probe/check path and surfaced only `adopter_finding`
results.

Keep `vector_space`, `yamllint`, and `MemLite` as the seeded next-wave reserve
set. Checkpoint before widening into them so the next wave starts from clean
authority state.

## Failure Triage For Corpus Waves

Use one deterministic triage on every failing repo before widening again:

1. `engine_bug`
   crash, wrong-repo write, VoiceTerm path/policy leakage, repo-layout
   assumption, broken `--repo-path` behavior, or other core-engine portability
   miss. Fix immediately in this repo.
2. `already_planned_architecture_gap`
   Step-0/startup authority, governed push, repo-pack activation, onboarding
   ratification/provenance, docs-authority fallback, or other failure already
   owned by `MP-376` / `MP-377`. Keep it explicit in the owner plan; do not
   keep rediscovering it as if it were a fresh mystery.
3. `adopter_finding`
   Honest engine run succeeded and the result is about the target repo's code,
   policy, or layout. Import/adjudicate it only after the engine path is clean
   on that repo.
4. `ambiguous_signal`
   The current output is too noisy to classify confidently. Tighten the
   contract or automation before widening the corpus.

## Execution Checklist

- [x] Move built-in guard/probe capability metadata into portable resolver code.
- [x] Move repo enablement and scope roots into repo policy/preset files.
- [x] Add `devctl quality-policy` plus `--quality-policy` overrides for reuse.
- [x] Ship portable Python guards for suppression debt, default-evaluation traps,
      design complexity, and cyclic imports.
- [x] Remove VoiceTerm-only `code_shape` namespace/layout assumptions from the
      portable engine and resolve them from repo-owned guard config instead.
- [x] Document the portable-governance system as an active execution target so
      portability and measurement do not get lost between sessions.
- [x] Define the engine/preset/repo-policy boundary explicitly enough that a new
      repo-adoption guide and future packaging command can be derived from it.
- [x] Define the measurement/event schema for guarded coding episodes:
      task class, changed files, initial diff/output, guard hits, repair loops,
      accepted diff, human edits, test outcomes, and later review outcomes.
- [ ] Extend guarded-episode measurement with context-budget metrics:
      estimated prompt size (`tokens` when available, otherwise bytes/lines/
      files), compression ratio, overflow path, and actual provider usage when
      exposed so quality gains can be evaluated against prompt cost.
- [x] Decide artifact retention rules for portable evaluation data and sample
      exports so the corpus is usable for retrieval/evaluation before any model
      training is attempted.
- [x] Add a first-class snapshot/export path for the full governance system
      (engine, guards, probes, policy, docs, latest reports) so it can be
      reviewed outside the repo without manual file hunting.
- [x] Add a portable evaluation framework that treats correctness as a gate,
      objective structural deltas as the primary signal, and AI/human pairwise
      review as a secondary preference layer.
- [x] Add a durable adjudication ledger for guard/probe findings so the repo
      tracks false-positive rate, fixed-vs-deferred cleanup, and real signal
      quality over time instead of relying only on ephemeral chat notes.
- [x] Add a repo-pack-resolved guard/probe promotion queue so adjudicated
      `governance-review` rows can create portable follow-up candidates
      without hardcoding VoiceTerm-only artifact paths.
- [x] Seed the first broad pilot corpus source from the maintainer GitHub repo
      inventory so external-repo testing does not depend on this machine's
      local checkout layout.
- [x] Run one non-VoiceTerm pilot repo through the portable stack using
      policy-only customization and record what still leaks VoiceTerm
      assumptions.
- [x] Add a first-class onboarding/full-surface scan mode so `check`,
      `probe-report`, and `governance-export` can evaluate a repo before a
      trustworthy baseline ref exists.
- [ ] Freeze a typed onboarding/adoption contract for external repos:
      `OnboardingContract` should capture onboarding mode, inferred policy
      payload, path roots, unresolved authority fields, ratification state,
      and per-field `InferenceProvenance` so adopters do not have to infer
      what the engine guessed from starter JSON or generated prose.
- [ ] Add repo-owned onboarding modes and ratification flow on top of that
      contract: `auto`, `assisted`, and `locked_down` should be explicit
      adoption modes; deterministic discovery stays automatic, but human
      authority over policy/runtime decisions should be recorded through one
      reviewed ratification surface instead of manual starter-file edits.
- [x] Add copied-repo bootstrap support so pilot repos with broken submodule
      `.git` indirection can be normalized without manual git surgery.
- [x] Freeze the corpus-first portability execution protocol in the active
      plan chain: fixed anchors plus exploratory queue, `3-5` repo waves,
      stop-on-first-`engine_bug`, full-anchor reruns after each engine fix,
      and explicit failure triage.
- [x] Seed the first fixed Python anchor corpus:
      `3-4` maintainer-source repos, `3-4` external mainstream repos, `1-2`
      external adversarial/weird repos, plus the two existing regression
      anchors already proven in this lane.
- [x] Record the first anchor corpus directly in this plan's repo matrix with
      repo class, source bucket, local path, and current run state so the same
      rerun set survives across sessions.
- [x] Run Wave 1 of the corpus-first proof program on `3-5` newly seeded
      repos, stop on the first new `engine_bug`, and rerun all green anchors
      after each engine fix before widening again.
- [ ] Keep corpus widening subordinate to blocker honesty: if the current wave
      bottoms out into only Step-0/startup or governed-push failures, stop
      adding repos and close those `MP-377` blockers before resuming corpus
      expansion.
- [ ] Treat typed-authority convergence as an explicit second-repo exit gate:
      at least one repo-pack-enabled non-VoiceTerm repo must prove custom-
      layout authority discovery, canonical review-state path resolution,
      generated bootstrap surfaces, and governed push/read-only control
      behavior without VoiceTerm defaults or bridge-required fallbacks.
- [ ] Add the portability fence as a graph/query proof, not a naming
      convention: no governance/runtime/platform module may take a direct
      import on `dev/scripts/devctl/repo_packs/voiceterm.py` unless it lives
      inside repo-pack adapters or explicit compatibility tests. Fail the
      adopter proof when VoiceTerm-shaped defaults leak past that boundary.
- [ ] Keep that second-repo proof sequenced after the `MP-377` owner blockers
      close: if the fixture run bottoms out into startup, review-state,
      generated-surface, or governed-push drift, route it back to
      `platform_authority_loop.md`, `remote_commit_pipeline.md`, or
      `remote_control_runtime.md` before widening the corpus.
- [ ] Add portable-defaults discovery via config diff: compare the adopter's
      `ProjectGovernance`, repo-pack state, and coordination/runtime snapshots
      against the baseline portable contract, emit the minimal override set,
      and use that diff to pressure-test repo-pack codegen instead of
      hand-tuning a second repo.
- [ ] Keep the second-repo graph ambition honest. Narrow deterministic
      portability questions such as import-fence closure, repo-pack defaults
      diffing, and bootstrap/guard/surface routing parity belong here once
      the owner blockers close, but strong graph-isomorphism claims remain
      deferred until both repos share a mature schema/type substrate. Do not
      widen this lane into embeddings-driven dedup, AI-synthesized repair
      hints, or other speculative graph features before the smaller portable
      proofs are stable.
- [ ] Add a second-repo graph/isomorphism proof on top of the controlled
      fixture matrix only after the graph/schema substrate matures: at least
      one non-VoiceTerm repo should eventually answer the same deterministic
      questions about plan scope, guard lane, surface resolution, and
      bootstrap command routing without core-engine edits, but this is a
      later-phase proof rather than part of the immediate graph-query slice.
- [ ] Version the graph/probe schema explicitly across adopter artifacts and
      fail cross-repo proofs on schema mismatch instead of comparing unlike
      graphs or silently reusing stale reducer output.
- [x] Promote compatibility shims into a portable governance primitive with
      structural validation and policy-owned metadata requirements instead of
      leaving wrapper exceptions as repo-specific layout hacks.
- [x] Add an explicit long-lived public-shim allowlist plus lifecycle
      classification so temporary shims split into `migrate-callers` vs
      `remove-now` instead of one undifferentiated budget warning.
- [x] Burn down the first zero-caller temporary shim tranche once the lifecycle
      scan can prove removal safety from repo-visible evidence.
- [x] Migrate the remaining `review_channel_*` root shim callers to the
      `dev/scripts/devctl/review_channel/` package and delete the leftover
      temporary wrappers once repo-visible usage is gone.
- [x] Re-run the shim governance bundle after the `review_channel_*` migration
      and record the remaining temporary-wrapper counts in the plan and
      governance ledger.
- [x] Burn down the next largest temporary `dev/scripts/devctl` shim families
      or explicitly bless any deliberate long-lived public seams in repo
      policy so the root wrapper count keeps converging instead of plateauing.
- [x] Continue burning down the remaining temporary `dev/scripts/devctl` root
      shim families, starting with `cli_parser_*` by wrapper count and
      `triage_*` by repo-visible reference count, so the post-autonomy shim
      backlog keeps converging from 39 wrappers / 87 references instead of
      plateauing again.
- [x] Continue burning down the remaining temporary `dev/scripts/devctl` root
      shim families, now starting with `process_sweep_*` while the current
      docs-led probe examples keep flagging `data_science_metrics.py` plus
      `governance_bootstrap_*`, so the post-security backlog keeps converging
      instead of flattening out again.
- [ ] Automate the multi-repo benchmark runner around the new evaluation
      schema/templates instead of keeping the experiment contract doc-only.
- [ ] Add a portable structural-readability governance tranche for repo-policy-
      driven file/module/symbol naming and API-intent checks. Keep deterministic
      filename/layout rules eligible for hard guards, but start function/symbol
      clarity and broader KISS/readability enforcement as advisory probes or
      optional autofix/report surfaces until signal quality is proven across
      multiple repos.
- [ ] Add a portability-safe "data-as-code" follow-up to that tranche: when a
      portability surface is effectively a static table of contracts or policy
      rows, the engine should be able to recommend moving that data into JSON/
      YAML/config artifacts instead of leaving it embedded as Python tuples and
      wrapper functions. Keep this advisory until the false-positive rate is
      proven low across more than one repo.
- [ ] Keep the portable-engine / repo-governance split explicit: the portable
      engine owns reusable checks, evidence contracts, cache formats, and
      startup artifacts, while repo-governance owns per-repo policy, preset
      selection, adoption routing, and local exception decisions. Do not let
      the engine accumulate product-specific authority that should live in the
      repo-governance layer.
- [ ] Add portable convention-discovery/report surfaces on top of that tranche:
      a repo should be able to run a one-time `naming-scan` to discover
      dominant patterns, emit a starter convention policy, then use
      `naming-report` as the AI/human-readable surface for active convention
      rules, drift probes, and recommended next checks.
- [ ] Freeze a portable repo-shape policy contract on top of those same
      organization/convention surfaces: starter adoption should work with one
      process doc, one execution tracker, one shared backlog, and one
      repo-pack-owned shape/convention policy that can express either default
      best-practice structure or explicit repo-owner preferences for
      directories, naming, boundaries, and exceptions. Additional scoped plan
      docs should be an escalation path for larger execution slices, not the
      mandatory baseline shape for every adopting repo.
- [ ] Define the portable package-role contract under that same repo-shape
      policy: `public_entrypoint`, `compat_shim`, `implementation_package`,
      `support_module`, `generated_artifact`, and `doc_authority` roles should
      declare allowed roots, flat-root allowances, import/export rules,
      naming/location constraints, and the expected owner surface for
      exceptions.
- [ ] Add a role-aware organization-review / package-cohesion surface on top
      of `package_layout`: detect helper-drawer roots, mixed-role directories,
      suffix-heavy helper families (`*_parser`, `*_support`, `*_policy`,
      `*_report`, `*_render`, `*_views`) outside approved packages, and roots
      where "green" only means budget-edge compliance instead of real
      structure convergence.
- [ ] Make that same organization contract report raw file volume separately
      from implementation density and shim/public-entrypoint density so adopters
      can see when a root still looks flat or helper-heavy even if only one
      density slice is currently blocking.
- [ ] Explicitly align that structural-readability tranche with the existing
      metric research: identifier density, cognitive complexity, Halstead
      volume, and later entropy/cohesion probes should provide portable
      severity/ranking evidence and AI fix hints, but repo-policy-backed
      naming/organization contracts remain the authority for convention drift.
- [ ] Extend the portable engine's confidence model to include governance
      completeness evidence: flag when a guard family has no tests, when a CI
      workflow never invokes a registered guard, when exception registries are
      incomplete, when workflow timeouts are missing, or when JSONL/evidence
      writers can silently skip malformed rows. Start from the current
      self-hosting baseline explicitly: low direct coverage across
      command/autonomy subsystems plus most guard/probe families must show up
      as measured meta-findings, not just audit prose. Route those as
      first-class repo-portable findings instead of assuming the guard stack
      validates itself. (evidence: `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 34)
- [ ] Close the repo-policy, export, and retention portability backlog cluster
      from `issues.md`: `ISS-024`, `ISS-026`, `ISS-036`, `ISS-038`,
      `ISS-057`, `ISS-078`, and `ISS-082` stay owned here until repo-policy
      /script naming is coherent, governance export snapshot names use strict
      safe-character validation, portable artifacts such as graph snapshots
      have retention/cleanup policy, repo-policy fields are documented and
      schema-backed, remaining VoiceTerm-path literals are removed from
      portable guards/context-graph surfaces, and preset extension failures
      stop degrading silently.
- [ ] Extract the first shared guard-family base where the current
      implementation has already converged on one pattern: `GrowthGuard`
      variants should inherit the same bounded core instead of maintaining
      parallel near-duplicate implementations, and the extraction should stay
      repo-pack-neutral so self-hosting proves the portability claim before
      Phase 7 adoption expands. Owner/phase: `MP-376` self-hosting engine
      cleanup tranche before broader Phase 7 proof. (audit mapping:
      `SYSTEM_AUDIT.md` A14)
- [ ] Add a repo-organization governance/report surface on top of
      `package_layout` + `doc-authority`: root markdown/file-count budgets,
      governed-doc metadata/registry coverage, zero-byte/orphan file
      detection, and wrong-hierarchy placement should be portable
      policy-backed checks instead of repo-local cleanup lore. (evidence:
      `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 29)
- [ ] Use that same organization contract to keep burning down the crowded
      `dev/scripts/devctl` flat root (currently ~80 top-level files) into real
      feature namespaces and freeze further flat-family growth so self-hosting
      proves the adoption contract before more external rollouts. (evidence:
      `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 40)
- [ ] Finish the workflow-portability cleanup tranche behind that same
      adoption contract: split the overloaded tooling-control-plane workflow
      into smaller policy-owned lanes and extract one shared Rust/ALSA setup
      composite action so portable repos do not inherit VoiceTerm-specific CI
      sprawl as the default. Owner/phase: `MP-376` workflow-portability
      cleanup before Phase 7 cross-repo proof. (audit mapping:
      `SYSTEM_AUDIT.md` A20, A21)
- [ ] Promote repo understanding into a portable evidence contract: define a
      versioned `map` schema that combines topology, complexity, hotspots,
      changed scope, and guard/probe overlays with machine-readable targeted-
      check hints so humans and AI can reuse one public surface instead of
      inventing prompt-local repo walkthroughs.
- [ ] Extend that portable map contract with optional test nodes and
      test-to-code edges so adopters can derive targeted test plans from
      changed files instead of guessing at validation scope.
- [ ] Add a bounded transitive blast-radius query contract on top of that map:
      start with explainable hop-limited closure over typed relations instead
      of opaque ranking so portability proofs can show why a file/test/config
      was pulled into scope.
- [ ] Add a portable typed-query layer beyond substring search so callers,
      importers, tests, configs, workflows, and plan/doc relations are
      queryable as explicit graph questions rather than prompt-local prose.
- [ ] Add a repo-portable `architecture-review` surface on top of that same
      map/query/probe/guard stack: another repo should be able to run one
      command/profile and get cycles, layer violations, god-module risk,
      blast-radius context, health scoring, and audience projections without
      copying VoiceTerm-only thresholds or docs.
- [ ] Keep that architecture-review path repo-pack-driven: layer rules,
      coupling thresholds, score weights, and audience defaults must resolve
      from repo policy / repo pack metadata instead of hardcoded VoiceTerm
      assumptions.
- [ ] Make push-enforcement state explicit for adopters: distinguish
      `devctl push`, optional installed pre-push hooks, and raw `git push`;
      startup/status surfaces should say whether repo-owned push validation is
      merely available or actually active so operators do not assume a GitHub
      push is guarded when no hook/install path is in force. The same tranche
      now also owns bypass-proofing and publish-state honesty: policy-backed
      push surfaces should not expose unrestricted `--skip-preflight` /
      `--skip-post-push` paths to normal AI/operator workflows, and typed
      status/receipts must distinguish "remote updated" from "post-push green"
      when a branch is published before the broader bundle finishes.
- [ ] Add an optional clean-slate / rollback-on-failure safety mode for
      external-adopter remediation loops: capture a pre-fix baseline, allow a
      bounded rollback to that baseline when post-fix validation worsens or
      fails, and support opt-in clean-slate rounds for autonomy experiments.
      Keep this explicit and policy-owned; do not silently replace the current
      bounded escalation model with unbounded auto-regeneration.
- [ ] Add portable release-artifact governance before stronger adopter release
      claims: `release` / `ship` surfaces must fail closed until
      `check_release_artifact_contents.py` (or a repo-pack-declared
      equivalent) passes, the forbidden-file policy proves no internal-only
      files or internal-infrastructure references leak through published
      artifacts, and `publish_receipt.py` emits a typed published-boundary
      receipt consumable by startup/status/report surfaces.
- [ ] Add supply-chain trust as planned portable work instead of hand-waving
      it into later polish: repo packs should be able to declare dependency/
      source trust policy, SBOM and attestation requirements, and language-
      specific verifier adapters (`cargo-vet`, `cargo-auditable`, or repo-
      appropriate equivalents) so another repo can say whether published
      artifacts are structurally clean and provenance-reviewed, not just
      layout-clean.
- [ ] Add one deterministic reproducibility integration test for the portable
      engine: run the same repo snapshot + policy twice through the
      deterministic layers and assert identical canonical findings, packets,
      and receipts except for explicitly allowed volatile fields such as
      timestamps or run ids.
- [ ] Keep exported measurement schemas honest about lifecycle:
      `portable_governance_episode` and `portable_governance_eval_record`
      remain reference/export artifacts until importer or validator code exists;
      if they graduate into live portable evidence, land executable validation
      and consumer paths in the same slice instead of counting templates as
      active contracts.
- [ ] Route all AI-initiated VCS pushes through `devctl push` instead of raw
      `git push`: Ralph (`ralph_ai_fix.py`), autonomy-loop, and swarm agents
      currently bypass `repo_governance.push` policy, preflight bundles,
      `TypedAction(action_id="vcs.push")` receipts, post-push bundles, and
      governance-ledger recording. The fix is to replace raw `git push` calls
      in AI agent paths with `devctl push --execute --caller <agent-id>`, add
      `allowed_callers` with per-caller preflight profiles to push policy, and
      carry push `ActionResult` forward in loop-packet checkpoint evidence so
      the operator console and governance ledger see every AI push through the
      same contract that governs human pushes.
- [ ] Make checkpoint-budget state portable for adopters too: another repo's
      startup/status surfaces should expose when the current dirty slice is
      still safe to keep editing versus when the agent must checkpoint before
      adding more changes. That decision must come from repo-pack policy
      thresholds plus current worktree counts, not from model-local judgment.
- [ ] Make tandem/review infrastructure opt-in and explicit for adopters:
      portable presets and starter policies should keep `check --profile quick`
      green without `bridge.md` until a repo explicitly enables tandem /
      review-channel enforcement, and bootstrap/setup surfaces must say when
      that infrastructure becomes required. (evidence:
      `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 41)
- [ ] Add one portable authority-drift scanner/report on top of that same
      adoption contract: detect hardcoded repo names, fixed governed-doc or
      artifact path literals in portable/control-path modules, import-time
      `active_path_config()` capture, and bridge-markdown current-status reads
      outside approved compatibility adapters. Start report-only, then promote
      low-noise subsets into blocking guards once the current fallback backlog
      is burned down. Seed the first report pattern set with `dev/active`,
      `dev/reports`, `dev/scripts`, `bridge.md`, `local_terminal`,
      `VOICETERM_*`, fixed review-status/session-cache paths, and VoiceTerm
      package/layout names when they appear outside repo-pack or product-
      integration boundaries.
- [ ] Land the first explicit authority-drift guards from that scan: implement
      `check_repo_pack_activation.py` for hidden VoiceTerm-default resolution
      and `check_frozen_path_config_imports.py` for import-time path-config
      capture so the second-repo proof can fail on the real portability leaks
      instead of review prose alone.
- [ ] Add a repo-pack-owned surface-ownership map for adopters that classifies
      paths into product client, governance engine, and thin integration seams;
      route review posture, boundary checks, and later push/default bundles
      from that map instead of ambient directory naming.
- [ ] Add a multi-repo portability fixture matrix that exercises the governed
      startup/adoption path on at least four shapes with no core patching:
      tiny Python app, Rust CLI, mixed Python/Rust repo, and custom docs/layout
      repo with non-VoiceTerm authority filenames, report roots, and tandem /
      review disabled. Keep this controlled matrix ahead of random external
      repo trials so failures classify cleanly as startup authority,
      repo-pack activation, capability gating, generated-surface, or governed
      VCS blockers. The matrix must prove `governance-bootstrap`,
      `startup-context`, routed base checks, and generated instruction
      surfaces work through repo policy / repo-pack inputs instead of
      VoiceTerm defaults.
- [ ] Keep the governed external Python repo matrix explicit and honest:
      two real repos are enough to expose engine defects and seed regression
      anchors, but not enough to claim broad portability. Expand the matrix
      before making any "works on arbitrary repos" claim.
- [ ] Record every corpus run as `engine_bug` or `adopter_finding`, rerun the
      failing repo plus every previously tested matrix repo after each engine
      fix, and only import/adjudicate adopter findings once the engine path is
      clean on that repo.
- [ ] Treat that fixture matrix as a permanent benchmark suite, not a one-off
      audit. Keep a fixed minimal set of portability fixtures plus at least one
      real external repo so regressions in adoption honesty are caught by the
      same governed startup/check path over time.
- [ ] Make generated AI instruction/setup surfaces part of the portability
      proof, not only a docs nicety: starter `CLAUDE.md`, setup guides, and
      related bootstrap renders must explain the platform purpose, the target
      repo's own product summary, and the client-vs-core boundary so adopters
      do not inherit VoiceTerm-specific identity or teach agents to hardcode
      VoiceTerm paths back into portable runtime work.
- [ ] Add a portable work-intake / startup-authority layer on top of that map
      and policy stack: another repo should be able to ask "what is active,
      what changed, what bundle should run, and where should accepted outcomes
      be recorded?" without copying VoiceTerm-specific docs/layout logic. The
      answer should come from repo-pack metadata, changed-file inspection,
      command-goal taxonomy, and generated surfaces rather than from one repo's
      hardcoded paths or hand-written starter prose.
- [ ] Make the repo-understanding path-resolution seam explicit for that same
      portable layer: `context-graph`, startup lookup, and concept-routing
      inputs must resolve active docs, roots, and warm-context hints through
      `RepoPack` / `RepoPathConfig` / repo-policy trigger tables rather than
      through VoiceTerm-specific literals like `dev/active/INDEX.md`,
      fixed directory assumptions, or keyword maps that only make sense in one
      checkout.
- [ ] Add graph-scoped post-edit verification routing on top of that same
      portable map: when a repo-understanding surface can prove related tests,
      guards, configs, or workflows for the changed scope, post-edit
      verification should prefer that targeted plan over generic broad
      bundles.
- [ ] Add language-aware guard/probe routing on top of the same repo-policy and
      changed-scope contract: when a diff clearly touches only Python roots or
      only Rust roots, skip inapplicable language families with explicit skip
      receipts, but fail closed back to the broader bundle whenever language
      detection is mixed, stale, or uncertain. This is a policy-owned
      optimization over one guard pipeline, not a second scheduler.
- [ ] Make that startup-authority layer convention-aware too: when a repo has
      declared convention policy or freshly generated convention reports, AI
      startup surfaces should include the relevant convention summary and the
      right convention checks instead of expecting agents to infer repo style
      from scattered examples.
- [ ] Benchmark portable context injection across repos with token cost,
      right-file selection, right-test selection, retry count, and
      false-confidence rate so graph-backed startup/context claims are measured
      rather than assumed.
- [ ] Keep startup context bounded and task-scoped for adopters: another repo
      should not need to read tens of thousands of tokens of global docs just
      to start safely. Add a minimal generated startup surface per task type
      and a filtered probe/convention view so adoption/bootstrap remains
      practical outside this repo's full maintainer context.
- [ ] Add a portable developer-discovery and delta-check surface on top of
      that same startup/routing contract: ship `devctl guard-explain <name>`,
      `devctl which-tests <path>`, descriptions in `devctl list`, per-check
      status/timing in `devctl check` output, and a user-facing incremental
      check surface (`check-delta` or equivalent routed dry-run/apply path) so
      maintainers can discover the right guard, the right tests, and the exact
      impacted verification slice without reading source or running the full
      repo bundle blind. (evidence: `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 44)
- [ ] Add a repo-portable governance-contract draft flow for adopters:
      `governance-draft` should scan languages, source/test roots, CI shape,
      import topology, architecture hints, and current quality baselines to
      emit a reviewed `project.governance.md` starter contract with explicit
      human-fill fields for priorities, ignored debt, and approved exceptions.
- [ ] Let that reviewed contract drive onboarding and evolution: approved
      `project.governance.md` state should feed `governance-bootstrap` and/or
      a later `governance-init`, and adoption scans should suggest contract
      updates when repo structure drifts instead of letting starter docs rot
      silently.
- [ ] Freeze typed onboarding modes plus ratification/provenance on top of
      that same contract: support `auto`, `assisted`, and `locked_down`
      flows, emit field-level inference provenance plus unresolved-authority
      prompts, and add one repo-owned `governance-ratify` path so first-run
      approval is durable typed state instead of an edited starter file only.
- [ ] Keep engine-owned resources separate from adopter authority in that same
      onboarding/productization lane: packaged presets, templates, and setup
      assets may ship with the engine, but docs authority, plan/backlog
      ownership, review mode, report roots, and path authority must remain
      repo-owned and overridable by the adopter contract.
- [ ] Absorb the architecture-alignment Pass 1 portability cluster into the
      portable engine contract: `governance-draft` / surface discovery must
      not fall back to `AGENTS.md` / `MASTER_PLAN.md` / `INDEX.md`,
      `check_phases.py` and push-routing helpers must resolve build targets,
      source roots, and branches from repo policy instead of `voiceterm` /
      `rust/` / `origin/develop` / `master`, and policy-owned defaults must
      cover plan-section requirements, quality-scope roots, available
      language families, and score-weight normalization so other repos do not
      inherit VoiceTerm-era assumptions.
- [ ] Absorb the architecture-alignment Pass 2/3 portable subsystem cluster
      into the same engine lane: `docs-check` must not silently fall back to
      VoiceTerm maintainer docs when repo policy is empty/partial, optional
      MCP transport surfaces must derive identity from governed repo metadata
      and keep VoiceTerm-only status providers out of the portable core,
      `process_sweep` must not hardcode `voiceterm` binary/process patterns,
      and `reports_retention` must move managed/protected path families onto
      repo-pack / repo-policy retention definitions instead of embedded
      VoiceTerm subroot tables.
- [ ] Close the remaining adopter-productization proof before broader Phase 7
      claims: ship the installable governance entrypoint plus the reviewed
      `governance-init` bootstrap path, then require a second-repo /
      no-core-engine-patches proof as the portability bar instead of treating
      export/bootstrap-only use as sufficient. Owner/phase: `MP-376`
      adoption/productization tranche before broader rollout. (audit mapping:
      `SYSTEM_AUDIT.md` A24, A25, A26)
- [ ] Make that startup-authority layer cache-first instead of re-scan-first:
      expensive repo-intelligence work should materialize durable artifacts
      (`plan snapshot`, `command map`, `convention snapshot`, `map snapshot`,
      targeted-check hints, filtered probe view) under one portable artifact /
      refresh-ledger contract, then refresh only the slices invalidated by git
      changes, plan/policy edits, or missing cache state.
- [ ] Make the adopter session-start path explicit in that same portable
      contract: first run should seed canonical artifacts through
      `governance-bootstrap`, `check --adoption-scan` /
      `probe-report --adoption-scan`, and a bounded startup packet; later
      runs should reuse cached artifacts, refresh only content-hash/git-diff-
      invalidated slices, and emit the next warm start without re-reading the
      whole repo.
- [ ] Define the portable storage/index contract for that repo-understanding
      surface: canonical JSON snapshot, append-only refresh ledger, optional
      SQLite query cache, stable artifact receipts, and repo-policy retention
      rules so another repo can reuse cached focus state without VoiceTerm-
      specific memory paths.
- [ ] Keep the non-Rust fallback first-class in that same portable path:
      canonical JSON snapshots plus refresh-ledger rows must be sufficient for
      warm-start portability even before an adopter activates the optional
      SQLite runtime/query cache.
- [ ] Build the short-term anti-pattern feedback loop before any model-training
      push: when guards/probes fire, emit compact repair packets, attach the
      most relevant repo-local good examples and policy hints, rerun targeted
      repair passes, and store reviewed bad->fixed episodes as machine-readable
      evidence for later retrieval, evaluation, and only then possible
      fine-tuning.
- [ ] Make the portable engine self-hosting before exporting stronger claims:
      the governance stack should run its own guards/probes with an
      explainable clean report, and code-shape/file-layout thresholds must be
      calibrated against coupling/cohesion/fan-out so the engine is not forced
      into line-count-compliant but less comprehensible fragmentation.
- [ ] Keep self-hosting validation aligned with the canonical internal seams:
      when package-layout or similar engine internals move behind shared
      loaders/helpers, the routed validation/default targeted suites must
      still cover the support-level tests that patch those canonical seams.
      A green command-level check is not enough if the support-layer tests can
      still silently target the pre-refactor boundary and miss the live loader
      contract.
- [ ] Extract shared governance-engine primitives where repetition is clearly
      structural rather than domain-specific: mapping/decoder helpers, guard or
      probe registration, markdown/report builders, and JSON/JSONL artifact
      writers should converge on reusable engine surfaces instead of spreading
      hand-written boilerplate across every checker and report path. Exact
      mechanics may be decorators, generators, or shared base helpers, but the
      portable contract should remove copy-paste as the default authoring mode.
- [ ] Define one portable versioned finding schema for guard/probe output so
      rule families, review packets, suppression flow, autofix metadata, and
      later replay/eval records all project from the same evidence contract
      instead of growing separate per-surface payload shapes.
- [ ] Expand the compact machine-output receipt path into a portable artifact-
      cost contract: path/hash/bytes/token estimates, content type, receipt
      size, and rule-family/command metadata should be emitted consistently for
      JSON-canonical surfaces so context spend and reread avoidance are
      measurable across repos.
- [ ] Build the replayable benchmark corpus earlier and more concretely:
      seeded must-flag and must-not-flag Python/Rust examples, reviewed
      historical repo findings, and stable replay inputs for rule-precision
      comparisons before stronger portability or ML claims are made.
- [ ] Tighten Python type/boundary enforcement for the portable engine by
      evaluating stricter typed-contract lanes and executable import-boundary
      checks on core/runtime/report/policy modules instead of relying only on
      the current advisory mypy posture.
- [ ] Evaluate bounded structural-search/autofix integrations for portable
      rule families: AST/semgrep-style matching is useful where it improves
      deterministic detection or safe rewrites, but repo-owned policy and
      evidence contracts must stay authoritative.
- [ ] Add first-class machine-readable wrappers for the highest-value external
      quality lanes so adopters get the same evidence model across native and
      third-party tools: typed Python checks, import-boundary checks, Rust test
      execution, dependency/security audit, and coverage artifacts.
- [ ] Close the false-green layout gap in crowded roots: package-layout
      governance should prove real namespace decomposition for
      `dev/scripts/devctl`, `dev/scripts/devctl/commands`, and the mirrored
      test roots, not only freeze further flat growth while existing crowded
      trees remain mostly intact.
- [ ] Keep package-layout honest but scoped: it remains the coarse structural
      self-hosting guard for crowded roots and compatibility shims, not the
      semantic architecture proof for Typed Authority Convergence. Portable
      closure should come from authority/parity guards and graph-backed probes
      that catch duplicate authority, stale fallbacks, guard-coverage gaps,
      and false-confidence cases across adopter runs.
- [ ] Turn the documented `devctl/commands` taxonomy into tree reality instead
      of policy-only intent: converge the still-flat command families on the
      target subpackages (`check/`, `autonomy/`, `review_channel/`,
      `release/`, `process/`) so layout checks and docs describe the same
      package boundary.
- [ ] Burn down the remaining temporary root shim backlog to policy budget and
      remove zero-caller wrappers promptly; current probe evidence should not
      keep tolerating dead root shims once repo-visible usage is confirmed
      absent.
- [ ] Align bootstrap/self-hosting interpreter contracts with the repo's Python
      3.11+ requirement so governance entrypoints and AGENTS bootstrap commands
      do not fail on machines where `python3` still resolves to 3.10 before the
      real layout/quality checks can even start.
- [ ] Mine the next repeated pattern families from live evidence before
      promoting any more hard guards; prefer probe-first rollout unless the
      signal is low-noise and clearly portable.
- [ ] Treat `context-graph` / `ConceptIndex` / ZGraph-style signals the same
      way in this lane: start with measured graph-backed probes or routing
      reducers over canonical contracts, validate them across the adopter
      corpus, and only then promote proven low-noise signals into blocking
      guards.

## Progress Log

- 2026-04-15: Turned the external-repo campaign rules into explicit operator
  authority instead of leaving them split between chat and historical wave
  notes. Future matrix work now resumes in waves of `3` repos, widens back
  toward `5` only after a clean wave, and keeps the current active anchors
  (`ci-cd-hub`, `adaptive-hashmap-studio`, `zgraph-scientific-package`,
  `mkgui`, `requests`, `interactions.py`, `pre-commit-hooks`) distinct from
  the held reserve wave (`vector_space`, `yamllint`, `MemLite`). The ingress
  contract is explicit too: honest adopter findings may arrive as JSON/JSONL
  or `LIVE_RUN.md` through `governance-import-findings --input-format md`,
  with repo-scoped `repo_name:Q-ID` identity so the markdown mirror does not
  become a second backlog. The next matrix widening is therefore blocked on
  real engine cleanliness, not on whether the repo list looks impressive.
- 2026-04-10: Routed the guard-promotion pipeline's portable slice here: the
  queue path now lives in repo-pack configuration and the initial command reads
  it through the same governance ledger helpers as other portable review
  artifacts. The queue is not yet a guard generator; it is the durable intake
  seam needed before validation and auto-registration can be made portable.
- 2026-04-08: Integrated the typed-authority convergence synthesis into the
  adopter lane. This plan is now the explicit second-repo/custom-layout proof
  pressure for the owner-chain closure, not a parallel architecture source:
  it proves that repo-pack-selected startup, review-state pathing, generated
  bootstrap surfaces, and governed push/read-only control behavior stay
  portable once the `MP-377` owner docs land the contracts.
- 2026-04-09: Routed the repo-specific portability proofs into this owner doc
  instead of leaving them as audit notes. The adopter lane now explicitly
  owns the non-VoiceTerm import fence, config-diff repo-pack defaults proof,
  graph-schema-version compatibility, and the second-repo isomorphism query
  over plan scope, guard lane, surface resolution, and bootstrap routing.
- 2026-04-09: Accepted the smarter-guard layering for the adopter lane.
  Package-layout stays in scope, but only as the coarse self-hosting pressure
  that keeps crowded roots honest. The portable engine proof should now also
  measure authority/parity guards and graph-backed probes against external
  repos so duplicate-authority detection, fallback drift, and guard-dispatch
  coverage graduate from theory into replayed corpus evidence before they
  become blocking semantics.
- 2026-04-07: Re-reviewed the portability phasing against the current
  validation-contract concern. The lane is still ordered correctly: multi-repo
  matrix proof is a primary pressure test for VoiceTerm leakage, but it must
  not jump ahead of `MP-377` repo-pack/startup/validation authority blockers.
  When the matrix exposes Step-0, repo-pack activation, governed commit/push,
  or validation-plan gaps, stop classifying them as adopter quirks and route
  them back to `dev/active/platform_authority_loop.md` /
  `dev/active/remote_commit_pipeline.md`. Resume wider corpus waves only after
  the blocker is typed, guarded, and rerun across the already-green anchors.
- 2026-04-07: Accepted the stronger portability-by-default correction for the
  adopter lane. Do not frame the next work as "try random repos and see what
  breaks." First make the drift scanner explicit, then keep the controlled
  fixture matrix small enough to diagnose root causes: tiny Python app, Rust
  CLI, mixed Python/Rust repo, and custom-layout/no-tandem repo. Only after
  that matrix proves repo-pack/bootstrap/check/generated-surface behavior
  without VoiceTerm fallbacks should the lane widen back into broad real-world
  repo trials and imported adopter finding adjudication.
- 2026-04-02: Completed Wave 1 on `zgraph-scientific-package`, `mkgui`,
  `requests`, `interactions.py`, and `pre-commit-hooks`. All five repos
  completed `governance-bootstrap`, `probe-report --repo-path --adoption-scan`,
  and `check --profile ci --repo-path --adoption-scan` without a new
  `engine_bug`, wrong-repo write, or VoiceTerm-specific fallback leak. Every
  failing `check` in this wave is currently classified as `adopter_finding`:
  `zgraph-scientific-package` (`268` hints / `9` failing guard families),
  `mkgui` (`155` / `9`), `requests` (`154` / `9`), `interactions.py`
  (`508` / `13`), and `pre-commit-hooks` (`75` / `5`). The next widened wave
  should start from the seeded reserve set `vector_space`, `yamllint`, and
  `MemLite` after a clean checkpoint rather than reopening Wave 1.
- 2026-04-02: Seeded the first fixed Python anchor corpus into clean `/tmp`
  clones and locked Wave 1 ordering before widening further. Maintainer-side
  seeds are `zgraph-scientific-package`, `vector_space`, and `mkgui`, with
  `MemLite` held as the fourth maintainer reserve. External mainstream seeds
  are `requests`, `interactions.py`, and `yamllint`, with `pre-commit-hooks`
  as the first adversarial/weird anchor. Wave 1 is capped at five repos in
  this order: `zgraph-scientific-package`, `mkgui`, `requests`,
  `interactions.py`, `pre-commit-hooks`. Keep `vector_space`, `yamllint`, and
  `MemLite` seeded but out of the first wave until either Wave 1 stays clear
  or a new engine fix requires broader reruns.
- 2026-04-02: Promoted corpus-first proof from review advice into the active
  `MP-376` execution order. This lane now explicitly says to checkpoint the
  current slice, seed a fixed Python anchor corpus, run waves of `3-5` repos,
  stop on the first new `engine_bug`, rerun all anchors after each fix, and
  treat Step-0/startup or governed-push failures as `MP-377` blocker work
  rather than excuses to keep widening the corpus. That keeps repo pressure
  testing aggressive without letting the lane collapse into open-ended
  anecdotal bug-chasing.
- 2026-04-02: Tightened the portability-proof standard after the first honest
  external Python reruns. `ci-cd-hub` and `adaptive-hashmap-studio` were
  enough to expose real core-engine defects and are now useful regression
  anchors, but they are still only two adversarial samples, not a generality
  proof. This plan now locks the governed external-Python corpus protocol,
  failure classification (`engine_bug` vs `adopter_finding`), and visible repo
  matrix into the active plan chain so future claims expand the same honest
  adoption path instead of relying on one-off reruns.
- 2026-04-02: The immediate self-hosting rerun after the honest cross-repo
  proof surfaced one more portability seam in the package-extraction layer.
  `check_structural_complexity` could still fail in repo-package mode because
  moved shared helpers/root shims only worked when `dev/scripts/checks` was on
  `sys.path`. Closed that follow-on gap in the same lane: the new shared
  `python_function_scan` helper now has an explicit root shim, the affected
  `code_shape_*` / `rust_*` root shims now fall back cleanly in repo-package
  mode, and regression coverage now proves both the root import surface and
  packaged `check_structural_complexity` load path. Keep the proof rule
  explicit: do not treat direct-script green as full portability closure when
  packaged guards still import through root compatibility seams.
- 2026-04-02: Re-ran real cross-repo proof on disposable local clones of
  `ci-cd-hub` and `adaptive-hashmap-studio` instead of treating self-hosting
  green as portability proof. `governance-bootstrap`, `render-surfaces`,
  `probe-report --repo-path --adoption-scan`, and `check --profile ci
  --repo-path --adoption-scan` now run on both repos without core-engine
  crashes, and the two escaped engine defects were closed in the same slice:
  `scan_python_functions()` now handles valid Python headers with inline
  comments and indented method signatures, and `check_code_shape` now scopes
  override-cap/stale-override self-hosting debt to files that actually exist
  in the target repo so external scans stop reporting VoiceTerm-only
  `app/operator_console/**` budgets. Imported cross-repo findings are now
  logged under `dev/reports/governance/external_pilot_findings.jsonl`
  (`882` rows across the two pilot runs). The remaining honest adopter gap is
  startup/push proof: `startup-context` still has no `--repo-path` mode, so
  true Step-0 proof must run from a target-local/exported governance stack
  rather than from the engine checkout.
- 2026-04-01: Absorbed the useful parts of `dev/intrgrate_analysis.md` into
  the portable adoption lane instead of leaving another shadow roadmap on the
  tree. The accepted additions are narrower than the source dump: explicit
  second-repo proof ladder, typed onboarding/ratification/provenance contract,
  real authority-drift guards for repo-pack activation and frozen path-config
  capture, a repo-pack-owned surface-ownership map for adopters, and a
  permanent portability benchmark suite. This keeps `MP-376` focused on
  adopter proof rather than duplicating the whole `MP-377` product plan.
- 2026-04-01: Re-reviewed self-hosting organization after the latest
  package-layout cleanup and locked the missing contract more precisely. The
  current `package_layout` / shim system is useful but still too growth-based:
  `check_package_layout` can report clean while the live tree still presents a
  helper-drawer root (`dev/scripts/devctl` currently has `80` root Python
  files, `20` shim-tagged wrappers, `60` non-shim files, and `13` non-shim
  `*_parser` modules). That means the next portable tranche is not another
  count tweak. It is a role-aware repo-shape contract layered onto the same
  engine: package roles, package-cohesion review, mixed-role/root-helper drift
  detection, and raw-vs-implementation-vs-shim density reporting so a repo can
  distinguish "no new drift" from "actually organized."
- 2026-03-27: Clarified the owner split for the next cross-repo organization
  decision instead of leaving it in ad hoc chat/backlog discussion. The
  portable baseline should stay small: one process doc, one execution
  tracker, one shared backlog, and one repo-pack-owned repo-shape/convention
  policy. This lane owns the reusable shape/convention contract plus
  enforcement/discovery surfaces, while `MP-377` keeps ownership of how that
  baseline shows up in startup/work-intake packets. Keep shared backlog empty
  unless there is real queued work; architecture decisions belong in the
  tracked owner plans.
- 2026-03-27: Closed a real self-hosting validation miss in the portable
  package-layout engine without widening the runtime surface again. The recent
  rule-loading extraction into `dev/scripts/checks/package_layout/
  rule_resolution.py` was directionally correct, but the paired support tests
  were still monkeypatching the old `support.py` seam and therefore failed
  after the refactor even though the command-level package-layout path stayed
  green. Fixed the tests to patch the canonical loaded `rule_resolution`
  module instead of reintroducing a duplicate compatibility alias in
  `support.py`, and accepted the explicit follow-up that package-layout
  internal refactors must keep the support-level suite in the default routed
  validation story so self-hosting proof keeps pace with the architecture.
- 2026-03-27: Re-audited the portable-engine lane against the current repo
  organization problem and tightened the owner split. The platform plans were
  already carrying the right direction; the missing piece was making the
  portable proof bar restartable and explicit. Locked this lane to four proof
  obligations only: custom-layout authority discovery, optional-capability
  gating, portable organization enforcement from `doc-authority` /
  `check_package_layout`, and adopter-facing push semantics that separate a
  remote update from full post-push green.
- 2026-03-27: Added the first portable authority fixtures that matter for
  adoption proof instead of talking about them abstractly. Governance-draft
  and startup/runtime tests now cover a policy-owned custom layout plus a
  no-bridge repo, and the runtime no longer needs `bridge.md` prose as a
  startup fallback when typed review state is absent. The same slice proves
  default warm refs can stay on startup-authority docs while suppressing
  compatibility projections and repo-pack lane docs.
- 2026-03-27: Re-ran the self-hosting portability evidence on the pushed
  branch instead of relying on broad complaints. `doc-authority` now reports
  `50` governed docs / `45,107` lines, `19` budget violations, `4` authority
  overlaps, and `8` consolidation candidates; `check_package_layout` still
  reports four frozen crowded directories plus seven crowded namespace
  families. That keeps the portable-engine ownership sharp: another repo
  cannot get a clean adoption story until this repo can prove the same
  organization contract on itself without drifting into shadow docs or flat-
  root sprawl.
- 2026-03-27: Closed the self-hosting side of the adopter-facing push gap.
  The canonical `devctl push` surface now gates skip-flag bypasses through
  repo policy and reports typed publish truth (`validation_ready`,
  `published_remote`, `post_push_green`) instead of one overloaded success
  state. That narrows the remaining `MP-376` push work to proving the same
  semantics on custom-layout / optional-capability adopters without core
  patches.
- 2026-03-26: Elevated the repo's own markdown sprawl into the portable-engine
  proof criteria instead of leaving it as an aesthetic complaint. Verified
  local pressure is now explicit: 27 `dev/active/*.md` docs and 10 root-level
  markdown entrypoints. The portable path therefore needs two linked closures:
  absorption-before-archive for reference companions, and a real
  file-count/budget/report surface that proves the governance system can keep
  its own repo startup-safe before it claims external-adopter readiness.
- 2026-03-26: Verified Claude's next broad architecture pass against the live
  portable-engine code before promoting it. Two additional `MP-376` gaps are
  now confirmed on the current tree: `commands/docs/policy_runtime.py`
  silently falls back to VoiceTerm maintainer-doc defaults when the
  `repo_governance.docs_check` section is empty, and `quality_policy.py`
  capability detection still recognizes only Python/Rust families so other
  repo types silently lose language-dependent probe coverage. Keep both as
  portable-engine authority work under the existing Pass 1/2 portability
  checklist instead of treating them as ad hoc audit notes.
- 2026-03-26: Promoted the next architecture-alignment owner tranche after
  Claude's later passes widened coverage to the remaining control-plane
  subsystems. `MP-376` now explicitly owns four more portable-engine gaps:
  fail-closed `docs-check` defaults, portable MCP identity and non-VoiceTerm
  status-provider boundaries, repo-policy-driven `process_sweep` binary
  patterns, repo-pack-defined report-retention path families, and
  integration-federation destination roots that still fall back to
  `dev/integrations/imports`.
- 2026-03-26: Promoted the first architecture-alignment Pass 1 owner cluster
  into `MP-376` instead of leaving it as audit-only prose. The portable lane
  now explicitly owns the repo-policy follow-up for governance-draft
  fallbacks, `check_phases.py` build/source assumptions, release/post-push
  branch literals, policy-owned required plan sections, quality-scope roots,
  and language coverage plus non-probe metric portability for non-VoiceTerm
  repos.
- 2026-03-26: Promoted a broader portability-audit tranche after the live
  reviewer-state repair exposed that the remaining risk is bigger than one
  bridge bug. The codebase already has starter bootstrap flows,
  `ProjectGovernance`, repo-policy-owned doc discovery, and typed review-state
  authority, but portable/control-path consumers still leak VoiceTerm through
  silent fallback, import-time path capture, and bridge-prose reads outside
  approved compatibility seams. The portable-engine plan now tracks the fix as
  explicit work: authority-drift scanning, cross-repo fixture proof, and
  generated AI/setup surfaces that teach the right repo-pack boundary instead
  of repo-specific folklore.
- 2026-03-25: Rechecked the deeper config/template intake against the live
  portable code and narrowed it before promotion. The broad orphan-file claim
  does not hold here: starter policy/templates already ship through
  export/bootstrap, `voiceterm.json` is a live preset extension, and
  `claude_voice_skill.template.md` is a live repo-pack surface. The remaining
  portable follow-up worth tracking is lifecycle honesty for the exported
  episode/eval schema templates if they are promoted beyond reference/export
  status.
- 2026-03-24: Folded the remaining aligned external-review items into the
  portable-engine lane instead of leaving them in intake prose. `MP-376` now
  keeps clean-slate / rollback-on-failure explicit for adopter safety and
  also requires one end-to-end reproducibility integration test so portable
  deterministic layers can prove stable outputs on the same repo snapshot.
- 2026-03-22: Integrated `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 44 into the
  portable-engine lane. The portable startup/discoverability contract now
  explicitly owns `guard-explain`, `which-tests`, described `devctl list`
  output, per-check status/timing, and an incremental check surface instead of
  leaving those operator-facing gaps in reference-only evidence.
- 2026-03-22: Filled the remaining audit-owned adoption/productization gap in
  the portable plan. Beyond self-hosting engine cleanup, the canonical
  portability proof now explicitly includes installable-entrypoint /
  `governance-init` work plus the same second-repo/no-core-patches adoption
  bar the audit called out as `A24-A26`.
- 2026-03-22: Finished the remaining `SYSTEM_AUDIT.md` mapping for the
  portable-engine lane instead of leaving structural/workflow cleanup in the
  audit guide. Canonical portable ownership is now explicit: `A14` is the
  self-hosting guard-family extraction tranche, while `A20`/`A21` stay in the
  workflow-portability lane that must land before broader Phase 7 adoption
  proof.
- 2026-03-22: Integrated the root evidence intake into the portable-engine
  lane and corrected the stale parts before promoting them into tracked work.
  The adoption/layout problem is real, but the precise 2026-03-22 self-hosting
  read is narrower: portable presets do not currently force tandem validation,
  `package_layout` and docs-governance already enforce part of the
  organization contract, and the live `dev/scripts/devctl` flat root is now
  roughly eighty files rather than the older `79` shorthand. The promoted
  follow-up is therefore explicit portable coverage/meta-governance,
  portable repo-organization checks beyond today's partial coverage, tandem
  opt-in/setup clarity for adopters, and continued flat-root burn-down behind
  the same policy-backed organization contract.
- 2026-03-21: Added the missing language-aware execution optimization to the
  portable-engine backlog. The current policy/preset stack already knows which
  guard families are language-specific, but the plan had not yet recorded the
  next step: use changed-scope plus repo-policy language knowledge to skip
  inapplicable lanes with explicit receipts while failing closed to broader
  bundles when the diff is mixed or uncertain.
- 2026-03-17: Aligned a proposed `governance-quality-feedback` /
  maintainability-snapshot surface with the portable engine boundary instead of
  letting it become a repo-local side system. Portable ownership here is the
  reusable evidence ingestion and evaluation contract: consume adjudicated
  false-positive/fixed/deferred outcomes, cross-repo pilot evidence, and later
  quality snapshots through the same engine/reporting path, while reusing the
  `MP-378` Halstead/Maintainability Index research lane from
  `dev/active/code_shape_expansion.md` rather than duplicating metric design in
  another plan doc. Keep operator-console/mobile integration out of the first
  slice; the portable core is CLI/artifact/reporting first.
- 2026-03-17: Refined that same portable scoring direction: adopter-facing
  evaluation should converge on a multi-lens scorecard with explicit evidence
  coverage rather than one opaque composite. The portable target is now
  `CodeHealthScore` + `GovernanceQualityScore` + `OperabilityScore`, plus at
  most one secondary gated overall summary. Median is not the preferred
  top-level cross-lens aggregator because it can hide a failing lens; if median
  is used at all, keep it inside one lens across closely related sub-metrics.
  Portable reports should explain which evidence fed each lens, which
  dimensions are unmeasured, and why the summary score moved.
- 2026-03-17: Added separate local-path evidence for `ci-cd-hub` against the
  pinned `integrations/ci-cd-hub` federated checkout so the corrected
  2026-03-14 `/tmp/governance-pilots/ci-cd-hub` benchmark is not overwritten.
  The local rerun used `governance-bootstrap`, the bootstrapped starter
  policy, `check --profile ci --adoption-scan`, and `probe-report
  --adoption-scan` against the pinned submodule path; it returned `13/15` red
  AI guard steps and a richer current review packet with `1828` findings
  across `266` files. Reviewed signal quality is now durable too: the target
  repo governance ledger has `7` adjudications (`4 confirmed_issue`,
  `3 false_positive`) covering real orchestration/exception/cycle debt plus
  representative false-positive/noise cases. Treat this as a local-path
  portability proof and reviewed-ledger follow-up, not as a replacement for
  the March 14 cross-repo aggregate baseline.
- 2026-03-17: Accepted a more concrete portable onboarding contract. Another
  repo should not have to start from raw policy JSON and scattered setup prose
  alone; the engine needs a reviewed repo-local governance doc
  (`project.governance.md` as the current working name) that AI can draft from
  deterministic scans and humans can finish with priorities, exclusions, debt,
  and exception intent. Portable ownership here is the draft/evolution engine:
  infer identity, languages, roots, CI/test shape, architecture hints, and
  quality baselines; leave the non-deterministic team-preference fields
  explicit; then let `governance-bootstrap` or later `governance-init` consume
  the approved contract instead of forcing first-run policy authoring from
  scratch.
- 2026-03-17: Fixed a real self-hosting reporting bug in the portable
  governance packet path. `devctl probe-report` had been rendering markdown
  and terminal packets without passing `repo_root` into the shared render
  helpers, which meant repo-root `.probe-allowlist.json` design-decision
  entries were silently ignored in the main operator command even though the
  fallback `run_probe_report.py` path already honored them. The main command
  now threads `repo_root` through artifact generation and both render modes,
  and the maintainer docs now describe the true allowlist contract:
  top-level `entries`, `disposition`, and file+symbol matching with `probe`
  retained only as audit intent. That closes the "why didn't the tools show
  the filtered result?" gap for the canonical probe surface and leaves the
  current local filtered backlog medium-only (`0` active high, `14` active
  medium, `25` design decisions).
- 2026-03-17: Clarified ownership after the naming/navigation audit. This plan
  owns the portable convention engine itself: repo-policy convention schema,
  discovery/report surfaces (`naming-scan`, `naming-report`), and the reusable
  naming/organization guard/probe families. It does not own AI-facing startup/
  work-intake routing or command-goal taxonomy; those remain `MP-377`
  product-facing work in `ai_governance_platform.md`.
- 2026-03-17: Accepted the cache-first framing for portable startup. Another
  repo should not have to pay the full maintainer-doc/bootstrap cost every
  session; the right architecture is cached repo-intelligence artifacts plus
  explicit invalidation/refresh, not repeated full rereads. The portable lane
  now assumes canonical JSON snapshots with an optional SQLite query cache,
  stable artifact receipts, and repo-policy retention rules so adopters can
  answer "what changed and what matters?" from stored evidence instead of raw
  prose bootstrap.
- 2026-03-21: Tightened that portable startup rule into an explicit first-run
  versus later-run contract. Adopters should seed canonical artifacts once via
  bootstrap + adoption-scan, then use content-hash/git-diff refresh to keep
  the next startup packet warm. JSON artifacts remain the required fallback
  until optional SQLite caching is activated in the target repo.
- 2026-03-11: Created this execution-plan doc after maintainership review
  highlighted a tracking gap. Existing active docs already covered probe
  implementation and portable-guard slices, but not the broader portable
  governance engine, data-capture, and external-repo rollout direction.
- 2026-03-11: Current state entering this plan:
  `quality_policy*.py` resolves built-in metadata, repo-local scope roots,
  per-guard config, and preset inheritance; `devctl quality-policy` renders the
  resolved configuration; VoiceTerm-specific `code_shape` namespace rules now
  live in repo-owned config; and the portable Python preset ships suppression
  debt, default-evaluation, design-complexity, and cyclic-import guards.
- 2026-03-11: Maintainer direction is now explicit:
  keep guard code at the same structural standard as guarded code, treat
  path-budget exceptions as temporary only, and sequence next work as
  stabilization -> structural cleanup -> evidence-driven next patterns.
- 2026-03-11: The next strategic expansion beyond portability is the
  measurement layer. The intended dataset shape is:
  raw task/input -> initial output/diff -> guard/probe findings -> repair loops
  -> final accepted diff -> tests/review outcomes.
- 2026-03-11: Requested an external-review snapshot pack containing duplicated
  engine/policy/check/report files plus generated quality-policy/probe artifacts
  so a reasoning model can inspect the whole system out of band.
- 2026-03-11: Added `dev/guides/PORTABLE_CODE_GOVERNANCE.md` as the durable
  reference for engine/preset/repo-policy boundaries, export rules, pilot repo
  selection, and the benchmark/evaluation model. Added schema templates at
  `dev/config/templates/portable_governance_episode.schema.json` and
  `dev/config/templates/portable_governance_eval_record.schema.json` so the
  measurement contract exists outside chat history.
- 2026-03-11: Added `devctl governance-export`, which exports the governance
  stack only to paths outside the repo root, copies the engine/tests/docs/
  workflows, and generates fresh `quality-policy`, `probe-report`, and
  `data-science` artifacts in the exported bundle.
- 2026-03-11: The first broad pilot corpus source is now explicit:
  `https://github.com/jguida941?tab=repositories`. Pilot selection should start
  there instead of relying on whichever sibling repos happen to exist on the
  current machine.
- 2026-03-11: Evaluation direction is now explicit in active state:
  correctness gate first, objective structural/safety deltas second, blind
  pairwise human/AI preference review third. AI judging is a secondary signal,
  not proof by itself.
- 2026-03-11: Ran the first non-VoiceTerm pilot against `ci-cd-hub`. The pilot
  found real external issues and surfaced the remaining portability leaks:
  copied submodule `.git` pointers break git-backed guards, first-run scans
  need a full current-worktree adoption mode, and export/bootstrap packaging
  must carry every file the governance stack expects.
- 2026-03-11: Closed the pilot-onboarding gaps with two portable additions:
  `devctl governance-bootstrap` repairs copied repo git state for disposable
  pilots, and `--adoption-scan` now gives `check`, `probe-report`, and
  `governance-export` a first-class full-surface onboarding mode.
- 2026-03-12: Tightened the bootstrap handoff for adopted repos so the target
  checkout now gets one obvious repo-local first-read file:
  `dev/guides/PORTABLE_GOVERNANCE_SETUP.md`. `governance-bootstrap` still
  writes the starter repo policy, but now also writes a concrete AI-friendly
  run order and customization checklist into the target repo instead of
  leaving the exported markdown template as the only onboarding surface.
- 2026-03-12: Split the broader architecture ownership cleanly. `MP-376`
  continues to own the portable governance engine, policy layering,
  onboarding/export, and evaluation corpus; the new `MP-377` plan at
  `dev/active/ai_governance_platform.md` now owns the full reusable product
  extraction across runtime/control-plane contracts, repo-pack packaging,
  frontend convergence, and the path toward VoiceTerm becoming one consumer of
  an installable platform.
- 2026-03-12: Added the next shim-governance layer on top of the shared
  compatibility-shim primitive. `probe_compatibility_shims.py` now reuses the
  same AST-first shim validator to rank missing canonical metadata, expired
  wrappers, broken `shim-target` convergence, and shim-heavy roots/families,
  while `run_probe_report.py` now resolves probe entrypoints from the shared
  quality policy/script catalog instead of keeping a second hard-coded probe
  list.
- 2026-03-12: Continued the structural cleanup inside `dev/scripts/checks`
  without moving public entrypoints: the `active_plan`, `python_analysis`, and
  `probe_report` helper families now live behind documented internal
  subpackages so the root of `checks/` stays closer to a list of runnable
  guard/probe scripts instead of mixed entrypoints plus support modules.
- 2026-03-13: Split the new `package_layout` shim-governance seams internally
  without changing the public contract. `package_layout.rules` now re-exports
  focused model/loading/shim-validation helpers, and
  `package_layout.probe_compatibility_shims` now keeps `build_report()` /
  `main()` stable while delegating rule loading, scan logic, and hint building
  to internal modules. This keeps the self-hosting import surface flat and
  testable while letting the implementation stop growing as two large files.
- 2026-03-13: Captured the next pattern-mining direction explicitly after
  maintainership discussion: portable readability governance, not one monolithic
  "clean code" script. The intended slice is repo-policy-driven filename/module
  naming, symbol clarity, and public API intent checks with machine-readable
  findings. Rollout should stay modular: deterministic filename/layout contracts
  can graduate to hard guards once low-noise, while function naming, KISS/
  readability, and broader Python clean-code heuristics should start as
  advisory probes plus optional autofix/report surfaces until cross-repo
  evidence proves them portable.
- 2026-03-13: Captured the short-term path toward better AI output more
  explicitly. The next leverage point is not immediate model training; it is a
  governed repair loop with compact guard/probe repair packets, targeted
  repo-local example retrieval, and reviewed bad->fixed episode storage. That
  gives the platform a practical near-term path to better first-pass code and a
  cleaner long-term dataset for retrieval or fine-tuning later, instead of
  trying to learn directly from raw noisy failure logs.
- 2026-03-16: Maintainer review sharpened a second missing engine-level piece:
  the repo already has topology scans, hotspot packets, and review artifacts,
  but they still read like probe byproducts instead of a portable public
  contract. The next portable surface should be a versioned `map` evidence
  model that combines topology, complexity, changed scope, and guard/probe
  overlays with targeted-check hints. Its storage contract should mirror the
  broader platform direction: canonical JSON snapshot, refresh ledger rows,
  optional SQLite query cache, and repo-policy-owned retention rules so cached
  AI focus state works in any repo without depending on VoiceTerm memory paths.
- 2026-03-13: Captured the next portable-engine follow-ups from a broader
  architecture/product review so they do not stay trapped in chat. The review
  largely matched the repo's existing direction, but it sharpened the missing
  engine-level pieces: one versioned finding schema, stable machine receipts
  plus artifact-cost telemetry, a replayable must-flag/must-not-flag corpus,
  stronger typed/boundary enforcement for portable Python contracts, bounded
  structural-search/autofix integration, and machine-readable wrappers for the
  highest-value third-party lanes. The repo already has early receipt helpers,
  advisory mypy, and security/dependency tooling, so the actual task is to
  harden and productize those seams rather than starting from zero.
- 2026-03-13: Logged a concrete self-hosting gap from live maintainership
  review: the current layout guards are still green for partially the wrong
  reason. `freeze`-mode crowding prevents new flat growth, but it does not yet
  prove the crowded `devctl` roots are actually decomposed, and the intended
  `commands/{check,autonomy,review_channel,release,process}` taxonomy still
  exists more strongly in docs/policy than in the tree. The same review also
  confirmed that root shim debt remains above policy budget and that bootstrap
  still has a Python-version footgun on machines where `python3` is 3.10, so
  those are now explicit execution items rather than chat-only warnings.
- 2026-03-13: Burned down the next self-hosting crowded-root slice in
  `dev/scripts/devctl` without breaking public imports. The new portable
  bootstrap helpers now live under `dev/scripts/devctl/governance/`, the
  `platform-contracts` implementation lives under `dev/scripts/devctl/platform/`,
  the `PathAuditAggregateReport` model moved under
  `dev/scripts/devctl/path_audit_support/`, and the new runtime/platform/probe
  tests moved under topic-aligned test packages instead of the crowded root test
  directory. The root files stay as metadata-bearing compatibility shims, the
  direct unit slices plus `check_package_layout` stay green, `devctl check
  --profile ci` now passes on this branch head, and the remaining pre-existing
  medium `probe_compatibility_shims` backlog for older `devctl` root shims was
  explicitly recorded as `deferred` in `governance-review`.
- 2026-03-13: Finished the next shim-governance follow-up on that same
  `dev/scripts/devctl` root backlog. All 84 previously metadata-free root
  compatibility shims now carry canonical `shim-owner` / `shim-reason` /
  `shim-expiry` / `shim-target` fields, the stale `# noqa` suppressions were
  removed from those wrappers, and the missing-metadata variant of
  `probe_compatibility_shims` is gone. The post-fix audit is now much cleaner:
  `devctl check --profile ci` still passes, `probe-report` narrows to pure shim
  budget pressure, and the next highest-signal extraction target is the
  `review_channel_*` root family (13 approved wrappers against a family budget
  of 4) rather than more wrapper metadata work.
- 2026-03-13: Extended shim governance from metadata-only auditing into an
  explicit lifecycle model. `probe_compatibility_shims` now loads a
  repo-policy allowlist for long-lived public shims, treats every other valid
  wrapper as temporary by default, and scans repo-visible imports/path/module
  references to classify temporary shims into `migrate-callers` vs
  `remove-now`. The first VoiceTerm policy seed deliberately stays narrow:
  public `dev/scripts/checks/{check_,probe_,run_}*.py` entrypoints are
  allowlisted, generated artifacts under `dev/reports/` are excluded from
  usage scanning so probe output does not self-justify wrappers, and the
  remaining `dev/scripts/devctl` root wrappers now show up as explicit
  temporary migration debt unless future repo policy blesses specific public
  seams.
- 2026-03-13: Used that new lifecycle scan to burn down the first concrete
  removal slice immediately instead of just recording it. Deleted 25
  zero-caller temporary root shims from `dev/scripts/devctl` (including the
  stale `watchdog_episodes.py` wrapper and six `review_channel_*` wrappers),
  updated the watchdog README to point at the canonical package module, and
  reran the governance bundle. The shim audit state is now materially better:
  the `remove-now` high-severity bucket is gone, `dev/scripts/devctl` root
  temporary wrappers dropped from 88 to 63, and the `review_channel_*` family
  dropped from 13 wrappers to 6. The remaining shim backlog is now purely
  medium-severity caller migration / budget pressure, which makes
  `review_channel_*` the clean next family to finish instead of a mixed
  metadata-plus-delete cleanup.
- 2026-03-13: Finished that `review_channel_*` cleanup tranche end-to-end.
  Updated the remaining docs/tests/active-plan references to the canonical
  `dev/scripts/devctl/review_channel/{event_store,handoff,launch,parser,prompt,state}.py`
  modules, deleted the six leftover temporary root wrappers, reran the review
  channel regression slice plus the shim-governance bundle, and recorded the
  new state. `probe-report` no longer emits a `review_channel_*` family
  finding; the broader `dev/scripts/devctl` root backlog dropped again from 63
  temporary wrappers / 143 repo-visible references to 57 wrappers / 135
  references. The next highest-signal shim work is now the larger remaining
  temporary root families rather than review-channel residue.
- 2026-03-13: Retired the temporary `security_*` root shim family after the
  next probe rerun narrowed the backlog to 23 wrappers / 46 repo-visible
  references. Workflow trigger paths, maintainer docs, active-plan notes, and
  engineering history now point at the canonical
  `dev/scripts/devctl/security/{parser,codeql,python_scope,tiers}.py`
  modules, and the four obsolete root wrappers were deleted. The next
  shim-governance target is now `process_sweep_*` plus the remaining
  docs-led callers for `data_science_metrics.py` and
  `governance_bootstrap_{guide,policy}.py`.
- 2026-03-13: Retired the next largest temporary `dev/scripts/devctl` root
  shim family, `autonomy_*`. Migrated the remaining repo-visible
  docs/history/plan references to the canonical
  `dev/scripts/devctl/autonomy/{benchmark_helpers,benchmark_matrix,benchmark_parser,benchmark_render,benchmark_runner,loop_helpers,loop_parser,phone_status,report_helpers,report_render,run_feedback,run_helpers,run_parser,run_plan,run_render,status_parsers,swarm_helpers,swarm_post_audit}.py`
  modules, renamed the package-layout probe's synthetic fixture paths so tests
  no longer self-justify a real wrapper name, deleted the 18 obsolete root
  autonomy shims, and reran autonomy plus review-channel regression coverage.
  The shim-governance state improved materially again: `probe-report` dropped
  the broader `dev/scripts/devctl` root backlog from 57 temporary wrappers /
  135 repo-visible references to 39 wrappers / 87 references, and the next
  highest-signal families are now `cli_parser_*` by wrapper count (8 wrappers /
  12 references) and `triage_*` by repo-visible references (4 wrappers / 14
  references).
- 2026-03-13: Finished the next caller-migration tranche after `autonomy_*`.
  Migrated the remaining repo-visible `cli_parser_*`, `triage_*`, and
  `triage_loop_*` docs/history/active-plan references to the canonical
  `dev/scripts/devctl/cli_parser/` and `dev/scripts/devctl/triage/`
  package-owned modules, then deleted 16 obsolete root wrappers. The shim
  backlog dropped again: `probe-report` now shows 23 temporary
  `dev/scripts/devctl` root shims with 46 repo-visible callers or references,
  down from 39 / 87. The remaining wrapper-heavy families are now
  `process_sweep_*` and `security_*` (4 wrappers each), while the current
  repo-visible-reference examples point at `data_science_metrics.py` and the
  `governance_bootstrap_*` wrappers.
- 2026-03-13: Retired the next shim tranche: `process_sweep_*` (4 wrappers),
  `data_science_metrics.py`, and `governance_bootstrap_{guide,policy}.py`.
  All seven had zero active Python callers; only doc/markdown references
  remained. Updated `AGENTS.md`, `dev/scripts/README.md`,
  `dev/active/ai_governance_platform.md`, `dev/history/ENGINEERING_EVOLUTION.md`,
  and the `process_sweep/README.md` to point at canonical package paths, then
  deleted the root shims. The `dev/scripts/devctl` root temporary wrapper
  count dropped from 23 to 16. All 1274 tests pass.
- 2026-03-11: Added `probe_exception_quality.py` as the next evidence-driven
  Python review probe. It surfaces suppressive broad handlers and generic
  exception translation without runtime context, which showed up as a real
  pattern family in external-tooling-style Python code.
- 2026-03-11: Added `devctl governance-review` plus the
  `portable_governance_finding_review.schema.json` template so reviewed
  guard/probe findings are recorded in a durable JSONL ledger with rolled-up
  false-positive, positive-signal, and cleanup-rate metrics. `data-science`
  now ingests that ledger so the main telemetry snapshot shows whether the
  governance stack is actually finding real issues and whether cleanup is
  converging over time.
- 2026-03-11: Burned down the first live advisory debt through that ledger:
  fixed the `probe_exception_quality` findings in `dev/scripts/devctl/collect.py`
  by narrowing fail-soft exception handling and fixed the translation-quality
  hint in `dev/scripts/devctl/commands/check_support.py` by removing the
  needless subprocess wrapper entirely. This is the first explicit proof that
  `governance-review` is part of the real cleanup loop, not just a future
  measurement hook.
- 2026-03-11: Burned down the next medium-severity design-smell slice from the
  same ledger: `probe_single_use_helpers` no longer flags
  `dev/scripts/devctl/collect.py`, and the row-loading helpers were moved out
  of `dev/scripts/devctl/data_science/metrics.py` into the dedicated
  `data_science/source_rows.py` module so the snapshot builder stays readable
  without carrying one-use file-local helpers.
- 2026-03-11: Burned down the next `probe_single_use_helpers` follow-up from
  the same ledger: the CIHub/external-input triage helpers were moved out of
  `dev/scripts/devctl/commands/triage.py` so the command stays
  orchestration-focused, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the next `probe_single_use_helpers` follow-up from
  the same ledger: `dev/scripts/devctl/commands/loop_packet_helpers.py` no
  longer carries one-call wrapper helpers for JSON source loading/command
  normalization or packet-body dispatch. This was not adjudicated as a false
  positive because those helpers had no reuse or test-seam value; the behavior
  now lives directly in `_discover_artifact_sources()` and
  `_build_packet_body()`, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Reviewed the next `probe_single_use_helpers` candidate in
  `dev/scripts/devctl/commands/review_channel_bridge_handler.py` and recorded
  it as `deferred`, not `false_positive`. Before review, the probe emitted one
  file-level hint covering five private helpers. After review, the finding
  stays open with narrower rationale: `_validate_live_launch_conflicts()` and
  `_load_bridge_runtime_state()` look like real one-use wrappers,
  `_resolve_promotion_and_terminal_state()` and `_build_sessions()` are
  defensible seams, and `_post_session_lifecycle_event()` is borderline. The
  audit log now captures that mixed call explicitly so the next cleanup can be
  selective instead of blindly inlining the whole file.
- 2026-03-11: Burned down that deferred
  `review_channel_bridge_handler.py` `probe_single_use_helpers` follow-up.
  Before the fix, the handler carried two real one-use wrappers plus three
  meaningful seams under private helper names, so the probe was not a false
  positive but the right remediation was selective. After the fix,
  `validate_live_launch_conflicts()` is reused from
  `review_channel_bridge_action_support.py`, the one-use bridge-state wrapper
  is gone, and the surviving session/promotion/event boundaries now live as
  named action-support helpers in
  `review_channel_bridge_action_support.py` instead of looking like throwaway
  file-local privates. `review_channel_bridge_support.py` stays below the
  code-shape soft limit after that split. `probe_single_use_helpers` no longer
  flags the handler, and the reviewed outcome is now recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/governance_export_artifacts.py`. Before the fix, the
  export writer delegated quality-policy, probe-report, and data-science
  artifact generation through three one-call private helpers with no reuse or
  test-seam value, so the probe was not a false positive. After the fix,
  `write_generated_artifacts()` writes those three artifact families directly,
  the file drops out of the probe backlog, and the reviewed outcome is recorded
  as `fixed` in `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/governance_export_support.py`. Before the fix, the
  export builder hid repository-external destination validation, snapshot
  source copying, manifest emission, and path-containment checking behind four
  one-call private helpers with no reuse or seam value, so the probe was not a
  false positive. After the fix, `build_governance_export()` performs those
  steps directly while `_sanitize_snapshot_name()` remains the only local
  helper boundary, the file drops out of the probe backlog, and the reviewed
  outcome is recorded as `fixed` in `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/watchdog/episode.py`. Before the fix, the episode
  builder delegated provider inference, guard-family classification, and
  escaped-findings counting through three one-call private helpers with no
  reuse or test-seam value, so the probe was not a false positive. After the
  fix, `build_guarded_coding_episode()` derives those values inline while
  `_snapshot()` remains the only reused local helper boundary, the file drops
  out of the probe backlog, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/watchdog/probe_gate.py`. Before the fix, the probe gate
  hid allowlist loading, allowlist matching, and report summarization behind
  three one-call private helpers with no reuse or test-seam value, so the
  probe was not a false positive. After the fix, `run_probe_scan()` performs
  those steps directly, focused unit coverage now exercises allowlist
  filtering/fail-open behavior, the file drops out of the probe backlog, and
  the reviewed outcome is recorded as `fixed` in `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/quality_policy_scopes.py`. Before the fix, the scope
  resolver hid Python-root discovery plus configured-root normalization and
  coercion behind four one-call private helpers with no reuse or test-seam
  value, so the probe was not a false positive. After the fix,
  `resolve_quality_scopes()` performs the Python default discovery and
  configured-root normalization directly while `_discover_rust_scope_roots()`
  remains the only meaningful helper boundary, focused unit coverage now
  exercises common Python-root discovery and invalid/duplicate scope handling
  in `dev/scripts/devctl/tests/test_quality_policy.py`, the file drops out of
  the probe backlog, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/review_probe_report.py`. Before the fix, the aggregated
  probe reporter hid per-probe subprocess execution, hint enrichment, batch
  collection, and terminal hotspot rendering behind four one-call private
  helpers with no reuse or test-seam value, so the probe was not a false
  positive. After the fix, `build_probe_report()` drives probe execution and
  risk-hint enrichment directly, `render_probe_report_terminal()` renders the
  top hotspot inline, focused unit coverage now exercises the terminal hotspot
  path in `dev/scripts/devctl/tests/test_probe_report.py`, the file drops out
  of the probe backlog, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the next
  `probe_single_use_helpers` follow-up in
  `dev/scripts/devctl/triage/support.py`. Before the fix, the markdown
  renderer hid project snapshot, issue list, CIHub, and external-input
  sections behind four one-call private helpers with no reuse or seam value,
  so the probe was not a false positive. After the fix,
  `render_triage_markdown()` builds those sections directly, focused unit
  coverage now exercises CIHub/external-input markdown rendering in
  `dev/scripts/devctl/tests/test_triage.py`, the file drops out of the probe
  backlog, and the reviewed outcome is recorded as `fixed` in
  `governance-review`.
- 2026-03-11: Burned down the final repo-wide
  `probe_single_use_helpers` follow-up in
  `app/operator_console/state/presentation/presentation_state.py`. Before the
  fix, the presentation layer hid snapshot-digest lane serialization,
  repo-analytics change-mix formatting, and CI KPI rendering behind one-call
  private helpers with no reuse or test-seam value, so the probe was not a
  false positive. After the fix, `snapshot_digest()`, `_build_repo_text()`,
  and `_build_kpi_values()` perform those derivations directly, focused unit
  coverage remains green in
  `app/operator_console/tests/state/test_presentation_state.py`, the file
  drops out of the `probe_single_use_helpers` backlog, and the residual low
  `probe_design_smells` formatter-helper hint disappears in the same pass. The
  reviewed outcome is recorded as `fixed` in `governance-review`.
- 2026-03-11: Burned down the next high-severity `probe-report` hotspot in
  `dev/scripts/devctl/phone_status_views.py`. Before the fix, the
  compact/trace/actions projections returned large ad-hoc dict literals and
  `view_payload()` plus `_render_view_markdown()` dispatched on raw view
  strings, so the combined `probe_dict_as_struct` and
  `probe_stringly_typed` hints were not false positives. After the fix,
  `PhoneStatusView` parses the selected view once at the boundary,
  typed projection models live in `dev/scripts/devctl/phone_status_projection.py`,
  `compact_view()`, `trace_view()`, and `actions_view()` emit the same JSON
  shapes through explicit `to_dict()` methods, focused unit coverage now
  exercises compact fallback plus trace-markdown rendering in
  `dev/scripts/devctl/tests/test_phone_status.py`, the file drops out of the
  probe backlog, and the follow-on code-shape split keeps the view renderer
  back under the soft file-size limit. The reviewed outcomes are recorded as
  `fixed` in `governance-review`.
- 2026-03-11: Closed the next portability leak that GitHub CI exposed directly:
  the repo quality-policy files existed only as ignored local JSON, so local
  `check`/`probe-report` runs resolved the VoiceTerm policy while GitHub fell
  back to the portable default surface and drifted from local results. The
  fix was governance, not engine behavior: commit the repo policy plus portable
  preset JSON files, document them as versioned source in maintainer docs, and
  keep workflow validation aligned with that tracked policy surface. The same
  CI-parity cleanup also narrowed pre-commit to changed files, fixed the
  tooling-control-plane mypy env export bug, moved iOS CI to `macos-15` so the
  Swift 6 / newer Xcode project lane can run, and burned down the current
  maintainer-lint redundant-closure regressions in the touched Rust files.
- 2026-03-11: Refreshed the external `terminal-as-interface` publication from
  the committed VoiceTerm branch head and then recorded the new sync baseline
  in `dev/config/publication_sync_registry.json`
  (`source_ref=4deb8ec8f8c3709f1fb35955f9763c6147df6a95`,
  `external_ref=9cf965f`). The paper repo now derives its appendix snapshot
  stats from the shared JSON snapshot instead of freezing those counts in
  prose, and `check_publication_sync.py` is back to zero drift.
- 2026-03-12: Closed the next GitHub-only parity follow-up after PR #16 moved
  onto the refreshed governance branch head. `test_process_sweep.py` now
  derives repo and `rust/` cwd fixtures from the live checkout root instead of
  a hard-coded workstation path, review-channel bridge tests pin freshness
  enforcement explicitly so `GITHUB_ACTIONS=true` no longer changes stale-poll
  expectations by accident, the startup-banner render-mode test now clears
  runtime/style-pack overrides before asserting the fallback path, iOS
  `xcode-build` now targets the generic simulator destination instead of a
  runner-specific device name, and the changed-file `pre-commit` lane is back
  to green after explicit watchdog/snapshot re-export cleanup plus the
  corresponding Ruff/format sweep across the touched PR file set.
- 2026-03-12: Finished the next CI-parity cleanup pass on top of that branch
  refresh. `devctl` now keeps repo-owned Python subprocesses on the invoking
  interpreter so local `python3.11 dev/scripts/devctl.py check|probe-report`
  runs no longer fall back to an older `python3` on PATH, split-module
  compatibility exports were restored for `quality_policy`, `collect`,
  `status_report`, `triage/support`, `check_phases`, and
  `check_python_global_mutable`, new support modules
  `dev/scripts/devctl/phone_status_view_support.py`,
  `dev/scripts/devctl/text_utils.py`, and
  `app/operator_console/state/activity/activity_report_support.py` pulled
  `phone_status_views.py` and `activity_reports.py` back under code-shape
  limits without duplicate logic, and the follow-up guard fixes removed the new
  broad-except / suppression-debt / nesting-depth regressions introduced during
  the changed-file Ruff sweep.
- 2026-03-12: Burned down the remaining working-tree review-probe debt from
  the phone/mobile control-plane surfaces. `dev/scripts/devctl/autonomy/phone_status.py`
  now uses a typed `RalphSection` boundary instead of large anonymous helper
  dicts and inlines the one-call latest-attempt / trace-normalization logic in
  `build_phone_status()`, `dev/scripts/devctl/mobile_status_projection.py`
  now carries the typed mobile compact/alert/actions payload models plus view
  parsing/render helpers so `mobile_status_views.py` stays under its
  code-shape limit, and `dev/scripts/devctl/commands/loop_packet_helpers.py`
  now uses `LoopPacketSourceCommand` instead of the last remaining auto-send
  string-literal chain. Focused `phone_status` / `mobile_status` /
  `loop_packet` tests are green, `probe-report` now returns a clean packet,
  and the reviewed outcomes are recorded as `fixed` in `governance-review`.
- 2026-03-12: Closed the post-push pre-commit/compatibility follow-up that the
  refreshed PR surfaced immediately. Ruff had stripped several legacy
  re-export seams that the repo still imports/tests through, so
  `dev/scripts/devctl/common.py`, `status_report.py`, `collect.py`,
  `triage/support.py`, `commands/check_phases.py`,
  `process_sweep/core.py`, `phone_status_view_support.py`,
  `quality_policy.py`, `check_python_global_mutable.py`, and
  `probe_report_render.py` now keep those compatibility names explicitly while
  `common.py` stays under code-shape via a compact compatibility-export table
  instead of line-by-line alias boilerplate. The changed-file `pre-commit`
  lane is clean locally again, `check_code_shape.py` is green, and the full
  `dev/scripts/devctl/tests` suite reran at `1184 passed, 4 subtests passed`.
- 2026-03-12: Closed the docs-governance follow-up on that same repaired tree.
  `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, and `dev/scripts/README.md` now
  state the maintainer contract explicitly: staged `dev/scripts/**` module
  splits must preserve compatibility re-exports until repo importers/tests/
  workflows move together. With that rule documented, `docs-check
  --strict-tooling` is green again, the bridge heartbeat was refreshed before
  rerun, and the full canonical `bundle.tooling` command list replayed cleanly
  under `python3.11` on this workstation (`397 passed, 181 skipped` in the
  Operator Console suite, zero repo processes left after cleanup).
- 2026-03-12: Closed the next GitHub runner parity bugs the new PR SHA exposed.
  Review-channel launch/rollover tests were environment-sensitive because
  session-script generation resolved `codex`/`claude` from the current PATH
  before the script even launched; bridge session building now falls back to
  the provider command name for the default resolver so dry-run and simulated
  launch paths stay portable while explicit missing-CLI tests still patch the
  failure path. `triage-loop` now threads the command module's CI/connectivity
  predicates into the preflight helper so the existing non-blocking-local test
  stays valid inside GitHub Actions, and `JobRecord.duration_seconds` now clamps
  negative monotonic deltas to zero so the Operator Console job-state surface no
  longer fails on runners whose monotonic counter is below the test fixture's
  synthetic `started_at`. Reproduced CI-shaped tests are green locally,
  `dev/scripts/devctl/tests` reran at `1184 passed, 4 subtests passed`, and
  `app/operator_console/tests/` reran at `397 passed, 181 skipped`.
- 2026-03-12: Closed the final review-channel CI parity leak from the same PR
  rerun. The stale-heartbeat auto-refresh path for `devctl review-channel`
  had been using `check_review_channel_bridge.py` metadata errors as its
  trigger, but that guard intentionally suppresses live heartbeat freshness on
  GitHub-hosted CI because the runner is not the real Codex conductor. That
  meant `status` / `launch` could still see a stale bridge snapshot while the
  auto-refresh helper saw no refreshable guard error. The helper now treats
  the bridge guard as a structural gate only and derives refreshability from
  direct bridge snapshot/liveness state instead; the stale-heartbeat tests now
  pin `GITHUB_ACTIONS=true` so the CI runner contract is exercised locally.
- 2026-03-12: Closed the last workflow-only parity blocker on PR #16 too. The
  docs/governance workflow was invoking `check_rust_compiler_warnings.py`
  inside `tooling_control_plane.yml` without the Rust toolchain or Linux ALSA
  headers that the dedicated Rust CI lanes install first, so the docs-policy
  job could fail even while the real Rust jobs stayed green. The workflow now
  provisions Rust and `libasound2-dev` before the compile-time Rust guard, and
  maintainer docs now call out that tooling/docs jobs cannot assume Rust lane
  prerequisites automatically.
- 2026-03-12: Promoted compatibility shims into the portable governance engine
  instead of treating them as an ad hoc VoiceTerm carve-out. The package-layout
  support now uses a shared bootstrap seam, validates shim shape structurally
  before reading optional metadata, supports policy-owned required metadata
  fields such as `owner` / `reason` / `expiry` / `target`, and lets crowded
  root/family reports exclude approved shims from implementation density while
  still surfacing shim counts explicitly.
- 2026-03-12: Tightened the crowded `checks/` root follow-through for that
  shim primitive. The root shim exemption no longer hard-codes
  `package_layout.command`; it now accepts any thin `package_layout.*` wrapper,
  ignores canonical shim metadata lines in the wrapper-size budget, and keeps
  both `check_package_layout.py` and `probe_compatibility_shims.py` as stable
  root entrypoints over package-owned implementations. The paired devctl tests
  also moved under `dev/scripts/devctl/tests/checks/package_layout/` so the
  crowded test root mirrors the same package boundary.
- 2026-03-13: Added context-efficiency as an explicit portable-governance
  measurement requirement. The engine plan already tracked guarded-episode
  data, evaluation corpora, and adoption evidence, but it did not yet say
  whether better rule outcomes had to be weighed against prompt/context cost.
  The execution checklist now requires context-budget metrics so future
  evaluation can compare code-quality gains against actual context usage rather
  than treating prompt volume as invisible overhead.
- 2026-03-14: Corrected the external-repo proof path after validating that the
  earlier March 14 `ci-cd-hub` claim was only partially portable. The raw
  `probe-report --repo-path` numbers were reproducible, but policy resolution,
  relative artifact paths, topology scans, and git-status collection still
  leaked the engine checkout, while starter policies only scanned `scripts/`
  in repos with larger top-level Python packages. The portable fixes now route
  repo-root lookups through the runtime override, seed portable preset JSON
  files into bootstrapped repos, and write explicit `quality_scopes` into
  starter policies so repos like `ci-cd-hub` scan `scripts`, `_quarantine`,
  `cihub`, and `tests` instead of silently narrowing to `scripts/`.
- 2026-03-14: Reran the corrected pilot corpus after those fixes. The previous
  quoted `ci-cd-hub` result (`7` hints: `1 high`, `5 medium`, `1 low`) was an
  under-scan; the corrected March 14 onboarding run found `159` hints
  (`53 high`, `104 medium`, `2 low`) across `509` source files with `93`
  hinted files. The corrected 13-repo aggregate is now `311` hints
  (`115 high`, `193 medium`, `3 low`) with `3` clean repos and `0` scan
  errors, replacing the previously quoted `158`-hint aggregate. The durable
  audit note and machine-readable summary live at
  `dev/reports/audits/2026-03-14-portable-governance-pilot-rerun.md` and
  `dev/reports/audits/portable_governance_pilot_2026-03-14.json`.
- 2026-03-14: The rerun also clarified why some repos still look "low":
  current portable coverage is Python/Rust-only, so repos with large Java,
  TypeScript, or React surfaces only get findings from Python-side tooling or
  scripts until language packs for those ecosystems are added. That gap is now
  explicit evidence for the next portability tranche instead of a vague chat
  concern.
- 2026-03-14: Confirmed that the hard-guard lane is now portable enough to use
  in onboarding mode, not just the probe lane. Running
  `check --profile ci --repo-path /tmp/governance-pilots/ci-cd-hub --adoption-scan`
  completed without engine crashes and returned `13` failing guard families out
  of `16` executed steps, while `package-layout-guard`, `god-class-guard`, and
  `audit-scaffold-auto` stayed clean. That result is now captured beside the
  corrected probe counts in the audit note/JSON, and six representative
  `ci-cd-hub` probe findings were recorded into `governance-review` as
  `confirmed_issue` rows so the proof path includes adjudicated external
  evidence, not only raw packets.
- 2026-03-20: Started the portable structural-readability tranche with the
  first repo-policy-backed term probe. `probe_term_consistency.py` now reads
  repo-configured canonical-vs-legacy wording rules, surfaces legacy names
  such as `code_audit` and mixed review-channel term families as advisory
  `naming_contract` hints, and is registered through the shared script catalog
  plus quality-policy registry instead of living as another one-off repo
  script. VoiceTerm policy now seeds the first review-channel vocabulary rules
  while maintainer docs point at the current `review_channel` package paths.

## Session Resume

- 2026-04-15 corpus-wave contract:
  resume future external-repo proof in waves of `3`, not by widening the full
  seeded matrix at once. The active anchors remain `ci-cd-hub`,
  `adaptive-hashmap-studio`, `zgraph-scientific-package`, `mkgui`,
  `requests`, `interactions.py`, and `pre-commit-hooks`; the next reserve wave
  stays `vector_space`, `yamllint`, and `MemLite` until one clean wave adds no
  new `engine_bug`.
- 2026-04-15 finding-ingress rule:
  keep adopter findings canonical. Import honest target-repo debt through
  `governance-import-findings` (including `--input-format md` for
  `LIVE_RUN.md` compatibility evidence), let repo-scoped `repo_name:Q-ID`
  identity collapse repeated imports, and keep `governance-review` as the only
  disposition sink.
- 2026-04-10 guard-promotion portability seam:
  resume with promotion-candidate storage treated as a repo-pack path, not a
  VoiceTerm literal. Future `validate-guard-proposal` / `promote-guard`
  work should run against adopter repos through their policy and queue paths,
  while this first slice only proves durable candidate intake and listing.
- 2026-04-08 typed-authority convergence proof rule: resume this lane only as
  the second-repo/custom-layout acceptance pressure after the owner-chain
  blockers close. The next honest proof is one repo-pack-enabled adopter that
  exercises `startup-context`, canonical review-state resolution, generated
  AI/bootstrap surfaces, and governed push/read-only control behavior without
  VoiceTerm defaults; if any failure reduces to `MP-377` startup/review-state/
  push drift, route it back immediately instead of widening the corpus.
- 2026-04-09 guard/probe validation rule:
  keep `package_layout` and shim governance as the structural backstop, but
  treat portable semantic closure as a measured guard/probe problem too. The
  next honest adopter pressure should tell us whether graph-backed probes over
  duplicate authority, stale fallbacks, and guard-coverage gaps are actually
  precise enough to promote, not just whether crowded roots still exist.
- 2026-04-09 second-repo graph-proof intake:
  once the `MP-377` owner blockers close, prove portability with the direct
  import fence, config-diff defaults, graph-schema-version compatibility, and
  the isomorphism queries instead of another ad hoc walkthrough or one-off
  adopter memo.
- 2026-04-07 portability-by-default review: keep this lane focused on proof,
  not new platform architecture. `MP-377` owns removing hidden VoiceTerm
  defaults and adding typed capability/repo-pack contracts; this `MP-376`
  companion proves those contracts on controlled adopters. Resume by making
  the authority-drift scanner concrete, running the small Python/Rust/mixed/
  custom-layout fixture matrix before random repo trials, and routing any
  Step-0/startup/repo-pack/generated-surface/governed-push failures back to
  the `MP-377` owner blockers rather than classifying them as adopter quirks.
- 2026-04-02 Wave 1 result: no new `engine_bug` across the first five seeded
  repos. `zgraph-scientific-package`, `mkgui`, `requests`, `interactions.py`,
  and `pre-commit-hooks` all completed the governed
  bootstrap/probe/check path and are currently classified as
  `adopter_finding`, not `engine_bug` or `already_planned_architecture_gap`.
  Resume from a clean checkpoint, then widen into the seeded reserves
  `vector_space`, `yamllint`, and `MemLite` or start importer/adjudication
  work if that becomes the next active slice.
- 2026-04-02 priority lock: do the corpus-first proof setup before broader
  portability widening. Immediate order is: 1) checkpoint the current plan
  slice, 2) seed the first fixed Python anchor corpus, 3) run Wave 1 on
  `3-5` repos, 4) stop on the first new `engine_bug`, and 5) if the failures
  collapse to Step-0/startup or governed push, switch to the owner `MP-377`
  blocker instead of adding more repos.
- 2026-04-02 proof-standard correction: do not describe the current state as
  "portable" or "fixed" from two repos alone. The honest read is narrower:
  two real Python repos found core-engine portability bugs and now serve as
  regression anchors, but broader proof still requires a growing governed
  corpus on the same bootstrap/probe/check path plus target-local/exported
  Step-0 and governed-push authority closure.
- 2026-04-02 follow-on proof rule: keep the current portability lane on
  closure, not corpus growth. After any future shared-helper/package move,
  rerun both the legacy root shim surface and the packaged check load path
  before widening external repo proof again.
- 2026-04-02 portable proof is now honest on two real repos for engine-run
  `check --repo-path` and `probe-report --repo-path`. The next portable slice
  is not another self-hosting cleanup memo. It is to finish the adopter
  startup contract: either install/export the governance stack into pilot repos
  as the default proof path or add a repo-path-aware startup receipt surface,
  then start adjudicating the imported `882` external findings instead of only
  collecting them.
- 2026-04-01 organization-contract correction: do not treat current
  `package_layout` green as architecture completion. The next portable slice is
  package-role and semantic package-cohesion authority on top of the existing
  `package_layout` engine, not a second unrelated topology framework and not
  another one-off cleanup memo.
- 2026-04-01 immediate execution order: 1) freeze the repo-pack-owned package
  role schema, 2) ship an advisory organization-review / package-cohesion
  report against the self-hosting tree, 3) use that output to burn down the
  `dev/scripts/devctl` helper-drawer root, and 4) only then promote the
  reliable subset to blocking policy.
- 2026-03-27 baseline-contract clarification: do not use `backlog.md` as the
  decision log for core architecture. Keep the shared backlog empty until
  there is real queued work. The next organization/convention slice belongs in
  this lane as a portable repo-shape policy contract, while `MP-377` owns the
  startup/work-intake projection that should expose only the minimal adopter
  baseline by default.
- 2026-03-27 ownership clarification: `MP-376` does not own the canonical
  docs-authority/runtime split itself. It owns proof that an adopter can use
  that split without VoiceTerm-shaped docs, paths, enabled capabilities, or
  push habits. Keep this lane on custom-layout, optional-capability,
  organization, and publish-state-honesty proof instead of pulling main
  architecture ownership out of `MP-377`.
- 2026-03-27 fixture-proof follow-up landed: the portable lane now has code
  proof that custom-layout and no-bridge repos do not need `bridge.md` to act
  as startup authority, and startup warm refs can suppress compatibility
  projections plus lane-specific docs when `ProjectGovernance` classification
  is present. Keep the next `MP-376` slice on explicit capability gating and
  second-repo/adopter proof rather than widening back into VoiceTerm-only
  operating-mode cleanup.
- 2026-03-27 portable-proof priority lock: keep the next `MP-376` tranche
  focused on proving that adopters do not need VoiceTerm-shaped docs, paths,
  or push habits. The immediate proof bar is narrow: custom-layout authority
  discovery, generated bootstrap/instruction surfaces that only emit
  repo-pack-selected docs, portable organization enforcement from
  `doc-authority` / `check_package_layout`, and adopter-facing push semantics
  that do not treat a remote update as full policy success. Do not spend this
  tranche on more evidence memos unless they directly advance that proof.
- 2026-03-27 optional-capability proof follow-up: the next adopter proof must
  show that review-channel, bridge compatibility, autonomy, operator-console,
  and mobile/phone surfaces are genuinely repo-pack/capability gated. Starter
  adoption should be able to run with those capabilities absent, and
  generated setup/instruction surfaces must advertise only the enabled
  capability set instead of teaching VoiceTerm's full operating stack as the
  universal baseline. Keep the same proof tranche responsible for config-
  driven registry closure too: starter/adopter repos should not need hardcoded
  bundle/script/provider chains copied from VoiceTerm to discover the portable
  engine correctly.
- 2026-03-27 push/organization follow-up: the next `MP-376` proof should use
  the measured self-hosting baseline, not another general audit memo.
  `doc-authority` and `check_package_layout` now give the portable lane real
  numbers for the repo's own organization debt, and the governed push flow
  proved the adopter-facing push contract is still not bypass-proof or
  publish-state-honest. Resume from portable organization enforcement,
  custom-layout proof, and explicit push-state semantics before claiming a
  clean adopter kit.
- 2026-03-26 self-hosting/organization follow-up: the next `MP-376` proof is
  not another big evidence memo. It is a custom-layout and low-doc-count
  proof. Before archiving reference docs, verify their accepted conclusions are
  mirrored into the owner chain. Before claiming portability, prove one repo
  that does not use `AGENTS.md`, `dev/active/INDEX.md`,
  `dev/active/MASTER_PLAN.md`, or VoiceTerm report roots.
- 2026-03-26 Pass 2/3 follow-up: the next portable-engine closure is no
  longer just governance-draft and bundle/path defaults. It also has to make
  `docs-check`, optional MCP transport identity, `process_sweep`, and
  `reports_retention` resolve from repo policy / repo-pack state so later
  adopters do not inherit VoiceTerm-shaped defaults after the main authority
  loop is cleaned up.
- 2026-03-26 Pass 1 follow-up: after the path-authority drift tranche, the
  next portable-engine review slice should verify that repo-policy really
  owns governance-draft defaults, build/source/branch routing,
  required-plan-sections, quality-scope roots, and metric/score portability
  instead of leaving those as VoiceTerm-shaped fallback behavior.
- 2026-03-26 portability-drift follow-up: the next `MP-376` evidence slice
  should stop treating "works on one pilot repo" as enough. The broader
  architecture audit confirmed that portable layers can still inherit
  VoiceTerm defaults through typed-model/parser fallbacks, generated AI
  surfaces, and frozen repo-pack accessors even when adoption scans look
  healthy. Next work under this doc is the detection/proof stack itself:
  static portability-drift checks plus fixture repos that exercise empty
  bootstrap, existing-repo adoption, alternate layout roots, and
  tandem-disabled operation.
- 2026-03-22 evidence follow-up: Part 44 is now explicitly tracked here.
  The next portable implementation slice should improve operator discovery and
  delta-aware validation with `guard-explain`, `which-tests`, described
  `devctl list` output, per-check status/timing, and an incremental check
  command/path instead of requiring source-diving for common guard/test
  questions.
- 2026-03-22 follow-up: the remaining `SYSTEM_AUDIT.md` portable-engine items
  are now mapped here. Next implementation under this doc is not another audit
  pass; it is the actual `GrowthGuard` extraction plus workflow-lane/composite-
  action cleanup behind the current Phase 7 adoption gate.
- The same mapping pass now makes the adopter-productization bar explicit too:
  installable entrypoint + reviewed `governance-init` + second-repo proof are
  tracked here, not left as audit-only portability advice.
- 2026-03-22 intake narrowed the next self-hosting/adoption slice to four
  concrete gaps: governance-completeness evidence, portable repo-organization
  enforcement, tandem/review opt-in clarity, and continued
  `dev/scripts/devctl` flat-root grouping under the same contract.
- Keep the corrected 2026-03-14 `/tmp/governance-pilots/ci-cd-hub` benchmark
  distinct from the 2026-03-17 rerun against the pinned
  `integrations/ci-cd-hub` federated checkout; today's local-path proof uses
  the current richer packet surface and should not overwrite the March 14
  cross-repo aggregate baseline.
- The pinned local rerun produced `13/15` red AI guard steps and `1828`
  probe findings across `266` files; durable artifacts now live under
  `integrations/ci-cd-hub/dev/reports/{probes,governance}/latest`.
- The target-repo governance ledger now has `7` reviewed rows
  (`4 confirmed_issue`, `3 false_positive`), which is enough to start
  separating real portable signal from rule-tuning debt on external repos.
- `devctl probe-report` now applies repo-root allowlist/design-decision
  filtering consistently in artifact, markdown, and terminal modes; the
  current local filtered backlog is `0` active high, `14` active medium, and
  `25` design decisions.
- Corrected March 14 pilot evidence is now durable in
  `dev/reports/audits/2026-03-14-portable-governance-pilot-rerun.md` and
  `dev/reports/audits/portable_governance_pilot_2026-03-14.json`.
- `probe-report --repo-path` now resolves target repo policy, scope, topology,
  git-status, and artifact paths consistently enough to trust cross-repo
  counts for Python/Rust repos.
- `ci-cd-hub` is the strongest proof point: `7` hints was an under-scan;
  corrected onboarding counts are `159` hints across `scripts`, `_quarantine`,
  `cihub`, and `tests`.
- The harder validation path now works too: `check --repo-path --adoption-scan`
  on `ci-cd-hub` completes and surfaces `13` failing guard families, so the
  engine is catching real hard-guard debt instead of only emitting probes.
- The next portability review also closed a product/engine gap: topology and
  hotspot artifacts need to graduate into a portable `map` evidence contract
  with targeted-check overlays and cacheable query state. Canonical truth
  should be JSON plus refresh-ledger rows with optional SQLite indexing, not
  VoiceTerm-only memory storage.
- Next portability step should expand beyond Python/Rust so mixed Java/React
  and TypeScript repos stop looking artificially clean.

## Audit Evidence

- Maintained platform proof ledger (reference-only, non-authoritative):
  `dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md` collects the current
  cross-repo proof boundary, external-pilot evidence links, machine-ledger
  map, and external-audit ingress path. Keep the portable proof bar and
  execution decisions in this plan; use the ledger as the maintained index over
  those artifacts and claims.
- External Python corpus loop:
  `python3 dev/scripts/devctl.py governance-bootstrap --target-repo <path> --force-starter-policy --format md`
  `python3 dev/scripts/devctl.py probe-report --repo-path <path> --adoption-scan --format json`
  `python3 dev/scripts/devctl.py check --profile ci --repo-path <path> --adoption-scan --format json`
  `python3 dev/scripts/devctl.py governance-import-findings --input <raw-findings.jsonl> --repo-name <repo> --repo-path <path> --scan-mode external --format md`
  `python3 dev/scripts/devctl.py governance-import-findings --input <LIVE_RUN.md> --input-format md --repo-name <repo> --repo-path <path> --scan-mode external --format md`
  `python3 dev/scripts/devctl.py governance-review --record --repo-name <repo> --repo-path <path> --scan-mode external --signal-type <guard|probe|audit> --check-id <id> --verdict <verdict> --finding-class <class> --recurrence-risk <risk> --prevention-surface <surface> --path <repo-relative-path> --format md`
- Portable resolver inspection: `python3 dev/scripts/devctl.py quality-policy --format md`
- Probe packet + hotspot report: `python3 dev/scripts/devctl.py probe-report --format md`
- First-run onboarding scan:
  `python3 dev/scripts/devctl.py check --profile ci --quality-policy <policy> --adoption-scan`
  `python3 dev/scripts/devctl.py probe-report --quality-policy <policy> --adoption-scan --format md`
- Main guard lane validation:
  `python3 dev/scripts/devctl.py check --profile ci --skip-fmt --skip-clippy --skip-tests --skip-build`
- Structural cleanup validation:
  `python3 dev/scripts/checks/check_code_shape.py --format json`
  `python3 dev/scripts/checks/check_parameter_count.py --format json`
  `python3 dev/scripts/checks/check_function_duplication.py --format json`
- Governance checks:
  `python3 dev/scripts/checks/check_active_plan_sync.py`
  `python3 dev/scripts/checks/check_multi_agent_sync.py`
  `python3 dev/scripts/checks/check_architecture_surface_sync.py`
  `python3 dev/scripts/checks/check_guard_enforcement_inventory.py`
  `python3 dev/scripts/checks/check_bundle_workflow_parity.py`
  `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- 2026-03-13 autonomy shim-family retirement evidence:
  `python3.11 -m pytest dev/scripts/devctl/tests/checks/package_layout/test_probe_compatibility_shims.py dev/scripts/devctl/tests/test_autonomy_benchmark.py dev/scripts/devctl/tests/test_autonomy_loop.py dev/scripts/devctl/tests/test_autonomy_report.py dev/scripts/devctl/tests/test_autonomy_run.py dev/scripts/devctl/tests/test_autonomy_swarm.py dev/scripts/devctl/tests/test_review_channel.py -q --tb=short`
  `python3 dev/scripts/devctl.py probe-report --format md`
  `python3 dev/scripts/devctl.py check --profile ci`
  `python3 dev/scripts/devctl.py governance-review --record --finding-id devctl-autonomy-root-shims --signal-type probe --check-id probe_compatibility_shims --verdict fixed --path dev/scripts/devctl --symbol 'autonomy_*' --severity medium --risk-type compatibility_shim_family_budget --source-command "python3 dev/scripts/devctl.py probe-report --format md" --scan-mode working-tree --notes "...deleted 18 temporary root autonomy shims..." --format md`
  `python3 dev/scripts/devctl.py docs-check --strict-tooling`
  `python3 dev/scripts/checks/check_active_plan_sync.py`
  `python3 dev/scripts/checks/check_review_channel_bridge.py` (`bridge.md` failed only because `Last Codex poll` was stale in the live bridge state)
  `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
  `python3 dev/scripts/devctl.py process-cleanup --verify --format md`
- Export path:
  `python3 dev/scripts/devctl.py governance-export --format md`
- Finding-quality ledger:
  `python3 dev/scripts/devctl.py governance-review --format md`
  `python3 dev/scripts/devctl.py governance-review --record --signal-type <guard|probe> --check-id <id> --verdict <verdict> --path <file> --format md`
- Pilot bootstrap path:
  `python3 dev/scripts/devctl.py governance-bootstrap --target-repo <path> --format md`
- 2026-03-14 corrected external-pilot rerun:
  `python3 dev/scripts/devctl.py governance-bootstrap --target-repo /tmp/governance-pilots/ci-cd-hub --force-starter-policy --format json`
  `python3 dev/scripts/devctl.py probe-report --adoption-scan --repo-path /tmp/governance-pilots/ci-cd-hub --format json --output /tmp/cihub-probe-report.json`
  `python3 dev/scripts/devctl.py check --profile ci --repo-path /tmp/governance-pilots/ci-cd-hub --adoption-scan --format json --output /tmp/cihub-check-adoption.json`
  `python3 dev/scripts/devctl.py governance-review --record --signal-type probe --check-id <probe_id> --verdict confirmed_issue --repo-name ci-cd-hub --repo-path /tmp/governance-pilots/ci-cd-hub ...`
  local 13-repo rerun over `/tmp/governance-pilots/*` via repeated
  `governance-bootstrap --force-starter-policy` plus
  `probe-report --adoption-scan --repo-path`; durable summary saved to
  `dev/reports/audits/portable_governance_pilot_2026-03-14.json` and
  `dev/reports/audits/2026-03-14-portable-governance-pilot-rerun.md`
- 2026-03-17 pinned local rerun over the federated checkout:
  `python3 dev/scripts/devctl.py governance-bootstrap --target-repo integrations/ci-cd-hub --format md`
  `python3 dev/scripts/devctl.py quality-policy --quality-policy integrations/ci-cd-hub/dev/config/devctl_repo_policy.json --format md`
  `python3 dev/scripts/devctl.py check --profile ci --repo-path integrations/ci-cd-hub --adoption-scan --format md --output /tmp/cihub-check.md`
  `python3 dev/scripts/devctl.py probe-report --repo-path integrations/ci-cd-hub --adoption-scan --format md --output /tmp/cihub-probe.md --json-output /tmp/cihub-probe.json`
  repeated `python3 dev/scripts/devctl.py governance-review --record ... --log-path integrations/ci-cd-hub/dev/reports/governance/finding_reviews.jsonl --summary-root integrations/ci-cd-hub/dev/reports/governance/latest`
  `python3 dev/scripts/devctl.py governance-review --log-path integrations/ci-cd-hub/dev/reports/governance/finding_reviews.jsonl --summary-root integrations/ci-cd-hub/dev/reports/governance/latest --format md`
- Known unrelated hygiene warning:
  `python3 dev/scripts/devctl.py hygiene --strict-warnings` remains red because
  of pre-existing publication drift and because hygiene can observe the cleanup
  subprocess while it runs; standalone cleanup verify is green.
