# Master Plan (Active, Unified)

## Canonical Plan Rule

- This file is the single active plan for strategy, execution, and release tracking.
- `dev/active/INDEX.md` is the canonical active-doc registry and read-order map for agents.
- `dev/active/theme_upgrade.md` is the consolidated Theme Studio specification + gate catalog + overlay visual research + redesign appendix, but not a separate execution tracker; implementation tasks stay in this file.
- `dev/active/memory_studio.md` is the Memory + Action Studio specification + gate catalog, but not a separate execution tracker; implementation tasks stay in this file.
- `dev/active/devctl_reporting_upgrade.md` is the phased `devctl` reporting/CIHub specification, but not a separate execution tracker; implementation tasks stay in this file under `MP-297..MP-300`, `MP-303`, `MP-306`.
- `dev/active/autonomous_control_plane.md` is the autonomous loop + mobile control-plane execution spec; implementation tasks stay in this file under `MP-325..MP-338, MP-340`.
- `dev/active/loop_chat_bridge.md` is the loop artifact-to-chat suggestion coordination runbook; execution evidence and operator handoffs for this path stay there under `MP-338`.
- `dev/active/naming_api_cohesion.md` is the naming/API cohesion execution spec; implementation tasks stay in this file under `MP-267`.
- `dev/active/ide_provider_modularization.md` is the IDE/provider adapter modularization execution spec; implementation tasks stay in this file under `MP-346`, `MP-354`.
- `dev/active/review_channel.md` now carries the reusable review/runtime
  contract slice for MP-355 plus the temporary markdown-swarm operating mode
  used by the current Codex/Claude cycle; implementation tasks stay in that
  file under MP-355 and must preserve the broader shared-backend boundary.
- `dev/active/ralph_guardrail_control_plane.md` is the Ralph guardrail control plane execution spec; implementation tasks stay in this file under `MP-360..MP-367`.
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- `dev/active/portable_code_governance.md` is the narrower engine/adoption
  companion under `MP-376`, not a second main product plan; implementation
  tasks stay in that file while product-level authority routes through
  `dev/active/ai_governance_platform.md`.
- `dev/active/ai_governance_platform.md` is the only main active product
  architecture plan for the extracted AI-governance system under `MP-377`.
  Repo-wide strategy, extraction, PyQt6, phone/mobile, and shared-backend
  questions must route from this tracker to that document before any narrower
  domain spec.
- `dev/active/platform_authority_loop.md` is the current subordinate `MP-377`
  execution spec for startup authority, repo-pack activation, typed plan
  registry, runtime/evidence/context spine closure, and the first cross-repo
  proof of the portable authority loop. Top-level product authority remains in
  `dev/active/ai_governance_platform.md`.
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b evidence gates pass.
- Deferred work lives in `dev/deferred/` and must be explicitly reactivated here before implementation.

## Status Snapshot (2026-03-17)

- Last tagged release: `v1.1.1` (2026-03-06)
- Current release target: `post-v1.1.1 planning`
- Active development branch: `develop`
- Current `MP-377` execution branch: `feature/governance-quality-sweep`
- Release branch: `master`
- Current main product lane: `MP-377` AI governance platform extraction. Treat
  `dev/active/ai_governance_platform.md` as the main scoped plan for the
  system that improves AI coding quality and is being pulled out of VoiceTerm.
- Required companion lane: `MP-376` portable code-governance engine/adoption
  work. It is subordinate to `MP-377`, not a peer product strategy.
- Current subordinate implementation lanes inside that extraction sequence:
  `MP-340` shared control-plane/mobile contract, `MP-355` review-channel,
  `MP-356` host-process hygiene, `MP-358` continuous swarm, and `MP-359`
  Operator Console.
- Current highest-priority subordinate `MP-377` lane:
  `dev/active/platform_authority_loop.md`. This is the execution spec for
  closing the portable authority loop:
  `ProjectGovernance -> RepoPack -> PlanRegistry -> PlanTargetRef ->
  WorkIntakePacket -> TypedAction -> ActionResult / RunRecord / Finding ->
  ContextPack`.
- Execution order: freeze and extract shared governance/runtime contracts
  first, converge CLI/VoiceTerm/PyQt6/phone on the same backend second,
  rebind VoiceTerm as a first consumer third, then resume broader Theme,
  Memory, and later product lanes.
- Current immediate `P0` execution order inside that authority-loop lane:
  first clear the blocking pre-spine hardening tranche (daemon attach/auth
  security, autonomy authority boundaries, JSONL/evidence integrity, and
  self-governance closure), then resume startup authority
  (`governance-draft` + reviewed `project.governance`), repo-pack activation
  and the full `active_path_config()` rewrite, typed plan registry, an
  evidence-identity freeze in parallel with the repo-pack/plan-registry work,
  one runtime slice through `TypedAction -> ActionResult -> RunRecord`,
  evidence/provenance/ledger closure, portable `ContextPack`, and then the
  two-repo proof with no core patches between adoptions.
- Accepted next Phase-6 direction inside that same lane: keep canonical
  pointer refs as the authority surface for plans/docs/repo-map/evidence,
  then layer native repo-owned `ConceptIndex` / optional ZGraph-compatible
  navigation plus a report-only `devctl` context-graph query surface on top
  of those pointers. Do not introduce a separate semantic authority store.
- Accepted retrieval/control stack inside that same lane: hard guards/probes
  stay the cheapest deterministic classifier layer, `ConceptIndex` /
  ZGraph-compatible graph outputs are the reversible search-space reducer over
  canonical refs, `startup-context` / `ContextPack` reconstruct the minimum
  cited working slice for the current scope, and review/autonomy/Ralph AI
  loops remain the expensive fallback/controller layer for work the cheaper
  layers cannot resolve. Do not collapse those layers into one prompt-local
  blob or let generated graph/context surfaces become a second authority.
- Current graph/intake follow-up inside that same lane: the live
  `context-graph` slice is still a bounded discovery helper, not the full
  least-effort scheduler. Next ladder is explicit: add command->handler/source
  closure plus first richer typed relation families, staged query filtering,
  bounded multi-hop inference, and honesty guards first, then a typed
  `startup-context` / `WorkIntakePacket` reducer that acts as the
  deterministic context router for command goal/intent + changed scope +
  budgeted cited read set + targeted checks, then live routing inputs (diff,
  findings, failed checks, plan scope), then symbol/test/finding/policy/
  workflow/config graph coverage, including Swift/iOS surfaces used by this
  repo.
- Current graph hygiene quick wins inside that same lane: unify `INDEX.md`
  parsing behind one canonical helper for doc-authority/context-graph/plan-
  resolution consumers, add a hard parity guard for `COMMAND_HANDLERS` versus
  `devctl list` command inventory, fix shared topology-scan exclusions so
  calibration/transient roots (`dev/repo_example_temp/**`,
  `.claude/worktrees/**`) never pollute live graph confidence, prefer fresh
  `dev/reports/probes/latest/file_topology.json` +
  `review_packet.json` for changed-path/hint/severity inputs with rescan
  fallback only when artifacts are stale or missing, normalize
  context-graph temperature from the shared hotspot scorer instead of
  maintaining a parallel algorithm, and formalize file-pattern trigger-table
  routing so the graph can request the right warm knowledge for a touched
  subsystem without inflating bootstrap.
- Current context-budget rule inside that same lane: keep the default startup
  packet slim (roughly <=2K tokens) and prefer query-on-demand / warm-context
  retrieval over preloading larger context blobs, because the platform should
  optimize for bounded discovery rather than "load everything just in case."
- Current startup-family rule inside that same lane: `startup-context`
  remains the canonical bounded startup packet; `context-graph --mode
  bootstrap` is a reducer/hot-index helper over the same cached authority,
  not a second peer bootstrap surface.
- Current bootstrap discoverability rule inside that same lane: generated
  `CLAUDE.md` and other repo-pack bootstrap surfaces must advertise the live
  governance capability set (`ai_instruction`, `decision_mode`,
  `governance-review --record`, packet-level operational feedback, and saved
  graph-snapshot baselines) and point agents back to
  `dev/guides/DEVELOPMENT.md` plus `dev/scripts/README.md` for the canonical
  "which tool do I run when?" routing. This is awareness guidance only;
  runtime authority still stays with `startup-context` / `WorkIntakePacket`.
- Current startup-surface closure inside that same lane: the repo-pack
  bootstrap steps, key command block, and post-edit checklist are now
  code-derived instead of manually curated policy prose, and
  `context-graph --mode bootstrap` now surfaces bounded probe/governance/
  watchdog/reliability summaries plus hotspot guidance from existing
  artifacts. Remaining closure is to move the same richer evidence family
  into canonical `startup-context` / `WorkIntakePacket` authority so the
  intake packet stays ahead of the helper surfaces.
- Current deterministic-routing rule inside that same lane: graph work only
  counts as usable startup/recovery help when one bounded request can return a
  cited read set before ad hoc file exploration. The first truthful router
  needs staged exact/canonical/typed-relation filtering, bounded multi-hop
  inference, and a small hot-query cache with explicit invalidation; keep all
  of that generated-only, reversible, and anchored in canonical typed
  relation families (`guards`, `scoped_by`, operation-semantic producer /
  consumer paths) instead of opaque semantic search.
- Current `P0` closure focus inside that sequence: canonical `Finding`-based
  packets, `FixPacket` / `DecisionPacket` split, schema/version matrices,
  `CommandGoalTaxonomy` + validation-routing closure, and a contract-closure
  guard so packet families, generated surfaces, and the runtime contract
  catalog cannot drift apart.
- Current meta-governance follow-up inside that `P0` closure: the platform
  must also prove its own checking stack is complete. Track guard/probe test
  coverage, CI invocation coverage, exception-list completeness, workflow
  timeout coverage, and data-as-code/configuration drift as first-class
  platform evidence instead of assuming the guard registry is self-policing.
- Current accepted self-hosting slice inside that `P0` work: `probe-report`
  now routes its first shared `Finding` / `DecisionPacket` contract seam
  through `devctl.runtime`, durable `ProbeReport` / `ReviewPacket` /
  `ReviewTargets` / `FileTopology` / `ProbeAllowlist` artifacts carry
  explicit schema metadata, and `check_platform_contract_closure.py` now
  enforces runtime-model/artifact-matrix/startup-surface closure for the
  current implemented platform families surfaced by `platform-contracts`.
- Current governance-surface readout: the repository still has 62 raw
  `check_*.py` entrypoints and 26 raw `probe_*.py` entrypoints on disk, while
  the active policy-enabled surface currently exposes 32 hard guards and 23
  review probes. Use the enabled counts for active enforcement scope and the
  raw counts for filesystem inventory only.
- Current VCS-governance proof point inside that same `P0` lane: the repo now
  has its first repo-pack-owned push-routing contract. `repo_governance.push`
  owns remote/default-branch/protected-branch rules plus preflight and
  post-push routing, `devctl push` is the canonical policy-backed branch push
  surface, and legacy `sync` / release helpers now read the same policy
  instead of hardcoding GitHub push defaults.
- Current checkpoint-intake follow-up inside that same lane: startup surfaces
  must expose not only whether a push is policy-guarded, but whether the
  current worktree is still within the repo-pack-defined continuation budget.
  Agents need deterministic `safe_to_continue_editing` /
  `checkpoint_required` state plus dirty-path budget evidence so they can
  stop and checkpoint a bounded slice before context debt grows, not only
  after the tree has already become arbitrarily messy. Bridge-backed
  `review-channel --action status` now projects the same
  `push_enforcement` snapshot and raises `checkpoint_required` attention so
  operator/read-only flows see that budget without a separate
  `startup-context` run. Accepted next closure rule: checkpoint/push events
  should also emit one generated repo-pack-owned packet into a managed cache
  root so startup can warm from fresh evidence instead of recomputing the same
  bounded git/plan/guard/review summary every session. Keep that layer
  generated-only, hash-invalidated, and disposable; canonical authority stays
  in git state, active plans, repo policy, and guard/review outputs.
- Current checkpoint-scope rule inside that same lane: `context-graph` /
  `ConceptIndex` / ZGraph-compatible outputs may help explain a candidate
  checkpoint by narrowing related plan/check/doc scope around the real diff,
  but they do not decide what belongs in a push. Canonical checkpoint truth
  remains git diff plus routed plan scope plus guard/review evidence; when the
  graph layer is low-confidence, the system should narrow the slice or stop,
  not widen the batch.
- Current self-hosting plan-doc gap inside that same lane: the repo already
  has meaningful typed governance/runtime contracts in code, but governed
  active-plan markdown is still less uniform than the contract layer it
  describes. The next self-hosting closure slice is to freeze one governed
  plan format, extend the existing active-plan/docs-governance enforcement
  path, and bring execution-plan docs into parity with the repo's own
  metadata/header/`Session Resume` expectations before the future
  `PlanRegistry` / `PlanTargetRef` loader claims markdown-derived authority.
- Current plan-authority follow-up after that self-hosting slice: discovery
  and blocking contract enforcement are now in place, but governed plans are
  still only partially consumed as structured runtime state. Today
  `review_channel/promotion.py` reads `## Execution Checklist`, while
  `Session Resume`, `Progress Log`, and `Audit Evidence` remain markdown-only
  restart/evidence surfaces, and `plan_patch_review` mutation ops are
  validated in packet contracts without runtime handlers that apply those
  mutations back to governed plan docs with typed receipts.
- Current typed-markdown runtime baseline inside that same lane: the first
  groundwork slice is now real in code. `ProjectGovernance` carries a typed
  `DocPolicy`, a typed `DocRegistry`, and parsed `PlanRegistry` entries built
  from governed markdown + `INDEX.md`, while keeping the existing path fields
  alive as compatibility seams. The next closure item is to make
  `startup-context` / `WorkIntakePacket` consume that same authority family
  instead of treating `context-graph --mode bootstrap` or ad hoc doc reads as
  peer startup paths.
- Current portability correction inside that typed-markdown slice: repo-pack /
  repo-policy context now owns governed markdown discovery. The runtime no
  longer relies only on `AGENTS.md` + `dev/active/*` assumptions; it now
  prefers `repo_governance.surface_generation.context` plus markdown-root
  policy for process doc, tracker, registry, bootstrap links, and
  startup-authority checks, with focused regressions proving a non-VoiceTerm
  layout. Remaining portability work is broader than path discovery:
  starter-bootstrap still needs to emit the full governed-plan doc set, and
  later `startup-context` / `WorkIntakePacket` still need to consume this
  policy-owned authority family end-to-end.
- Current review-channel bridge-authority cutover status: `review_state.json`
  and `compact.json` now carry a typed `current_session` block for live
  instruction revision, implementer status, implementer ACK state, findings,
  and reviewed scope, and `latest.md` current-status rendering now prefers
  that typed state over append-only bridge prose. The remaining work is to
  migrate writer/mutation paths plus the remaining push/preflight consumers so
  `bridge.md` becomes a generated compatibility projection instead of a live
  current-status authority or freshness gate. `check_tandem_consistency` now
  prefers typed `review_state.json` authority for 4 of 7 checks (reviewer
  freshness, implementer ACK, completion stall, promotion state); the
  remaining 3 checks still use bridge-text fallback where no typed equivalent
  exists. `startup-context` reads typed `review_accepted` from the projection,
  and the symmetric repo-owned `reviewer-wait` path now wakes from
  `reviewer_worker` hash drift plus projected `current_session`
  implementer ACK/status updates instead of one-shot status reads or ad hoc
  shell sleep loops.
- Current runtime-baseline correction after the 2026-03-21 architecture audit:
  Phase 1 closure must keep five runtime-behind-docs gaps explicit instead of
  treating them as background drift. Portability is still blocked first by
  VoiceTerm-default path/runtime authority, startup/review recovery still
  leaks bridge/projection fallback into the control path, provider-shaped
  review fields plus `active_dual_agent` defaults remain compatibility state
  rather than the final middle layer, `plan_patch_review` / `apply` still
  stops at event-state transition without executable plan mutation, and
  concrete slices such as `vcs.push` still need `ActionResult` business-state
  cleanup plus real `RunRecord` closure before the authority loop can claim
  runtime parity with the docs.
- Current deterministic self-governance closure rule after the 2026-03-21
  guard audit: do not treat more guard count or richer graph semantics as
  progress while typed/runtime authority still lies. First close the cheap
  truth gaps (`ActionResult.status` business-state drift in `vcs.push`,
  `context-graph` confidence type mismatch, and advisory-only mypy on the
  `dev/scripts/devctl` lane), then add narrow deterministic enforcement for
  contract-value domains, plan/runtime parity, authority-source integrity, and
  dead authority seams. Keep ZGraph / `context-graph` generated-only until
  those fixes plus the startup/path/review authority cutover are green.
- Current native-N-agent follow-up in the same neighborhood: packet routing,
  `TandemProfile.implementers`, the append-only event lane, and
  `autonomy-swarm` already scale past two agents, but the review-channel
  middle layer still hardcodes provider-shaped queue/bridge/liveness fields
  (`pending_codex`, `pending_claude`, `claude_ack`, `codex_poll_state`,
  fixed agent-id allowlists). Treat the current 8+8 loop as
  conductor-managed multi-agent operation; native N-agent current-session /
  packet-lane authority stays tracked follow-up work under MP-355 and MP-377.
- Current blocking follow-up after that closure slice: replace checkout-path-
  based finding identity with stable repo identity + repo-relative path, add
  the first hard-guard-to-`Finding` normalization seam so blocking and
  advisory evidence stop using different ontologies, extend the contract
  catalog/closure guard to the remaining `P0` families (`ActionResult`,
  `CommandGoalTaxonomy`, `RepoMapSnapshot` / `MapFocusQuery` /
  `TargetedCheckPlan`, `FixPacket`), and keep packaging / adoption proof plus
  tracker-hygiene follow-ups such as the `MASTER_PLAN` state/changelog split
  in `P1`.
- Current architecture caution: `platform-contracts` now covers the already-
  real `ActionResult` / `Finding` / `DecisionPacket` rows, so the spine is no
  longer missing from zero, but it is still not closed or authoritative for
  the whole app. The review ledger still duplicates checkout-path-based
  identity through `governance_review_log.py`, and the current frontend
  clients still converge mostly through emitted projections and compatibility
  adapters instead of one fully closed live backend/service protocol.
- Audit-intake sequencing rule: accepted 2026-03-17 whole-system audit items
  reinforce the current `P0 -> P1 -> P2` order rather than replacing it.
  Close finding identity and guard/`Finding` evidence convergence first, then
  do packaging / install-surface work and tracker compaction, then finish the
  PyQt6/operator-console seam consolidation over the shared backend.
- Whole-system audit alignment rule: `dev/guides/SYSTEM_AUDIT.md` is reference evidence, not
  a second tracker or spec. Only its code-backed blocker tranche changes the
  live execution order: daemon attach/auth hardening, autonomy authority
  hardening, evidence-integrity closure, and self-governance coverage move
  ahead of the remaining authority-loop spine. The rest of the 2026-03-19
  audit remains corroborating reference until its stale counts and internal
  contradictions are cleaned up, after which the tracked order still stays:
  bounded `startup-context` / `ContextPack`, hot/warm/cold session context,
  repo-pack/path-authority closure, then follow-on review-channel /
  guard-boilerplate simplification.
- Accepted semantic-context direction for `MP-377`: keep canonical pointer
  refs / typed anchors as authority, build the first native `devctl`
  `context-graph` / generated `HotIndex` surfaces on top of the existing
  repo-understanding `map` backend, and keep `ConceptIndex` / any
  ZGraph-compatible encoding generated-only. This stays inside the
  `ContextPack` / startup-boundary plan, not as a new MP or a second memory
  authority.
- `MP-377` Phase 6 context-graph implementation landed (Session 43): 7-file
  package at `dev/scripts/devctl/context_graph/`, 4 output modes (bootstrap,
  query, mermaid, dot), ZGraph concept layer with typed edges
  (`documented_by`, `related_to`, `contains`). Startup-authority contract
  updated through the canonical policy chain.
- Accepted next bounded use of that same context-graph slice: policy-driven
  context escalation for live agents. Conductors now get explicit
  unread-scope / failed-attempt / blast-radius query rules plus a preloaded
  lane packet, `loop-packet` / autonomy checkpoints now carry a bounded
  recovery packet forward, and the Ralph CodeRabbit fixer now injects the
  same packet into its Claude prompt. Keep this read-only and generated; it
  is recovery/navigation, not a second authority store.
- Immediate sequencing rule for that graph work: checkpoint the current green
  bounded context-escalation slice before widening graph scope again. Treat
  the passing CI/doc-governance state as the first stable Phase-6
  context-recovery proof, not as permission to pile richer graph work into
  the same mixed tree.
- Next `MP-377` graph order after that checkpoint: honest typed plan/doc/
  command edges plus first richer typed relation families and artifact-backed
  live routing/scoring inputs first (shared scan hygiene,
  `file_topology.json` / `review_packet.json` ingestion, shared hotspot
  scoring, severity-aware ranking, initial `guards` / `scoped_by` /
  operation-semantic producer-consumer paths, staged query filtering,
  bounded multi-hop inference, and a small bidirectional hot-query cache),
  then the remaining backend instruction emitters (review-channel
  promotion/event projections and fresh `swarm_run` prompts), then a
  validation matrix across review-channel / autonomy / Ralph, then richer
  graph capabilities such as transitive blast radius,
  review/governance/autonomy/workflow/config/test edges, and
  agent-authored graph queries.
- Follow-on graph/productization lane after those honesty/intake closures:
  add one portable `architecture-review` command/profile that aggregates the
  same graph, probe, guard, and contract evidence into one system-level health
  report instead of relying on ad hoc grep/manual synthesis. Keep it
  repo-pack-driven, JSON-canonical, and projected into audience-specific views
  rather than inventing a second architecture-analysis stack.
- Follow-up: `devctl` organization/readability cleanup — crowded roots
  (`dev/scripts/devctl/`, `commands/`, `tests/` all over freeze thresholds),
  naming/module convention consistency, and a portable naming-convention
  report/guard path. Current `package_layout` guards hold via freeze mode
  but do not drive cleanup. Keep this as a tracked self-hosting follow-up
  after the checkpointed graph slice rather than mixing it into the same
  implementation batch.
- Audit-integration rule: if a whole-system audit finding is accepted, rewrite it
  into canonical execution state in `MASTER_PLAN`, the relevant active plan
  doc, and maintainer docs when process policy changes. Do not keep live work
  pointing back to `dev/guides/SYSTEM_AUDIT.md` after the canonical docs have
  been updated. Once its accepted items are fully absorbed or explicitly
  rejected, retire the moved audit copy instead of keeping a shadow roadmap.
- Review-ledger caution: a zero false-positive rate is not a success metric on
  its own. Read `false_positive_rate_pct` together with reviewed-vs-
  unreviewed coverage, per-family disposition mix, and time-to-disposition
  before drawing quality conclusions from the ledger.
- Current startup-authority gap: the repo already has partial intake pieces
  (`AGENTS.md` bootstrap order, `check-router`, `orchestrate-status`,
  `docs-check`, `render-surfaces`, `swarm_run`), but not one enforced,
  repo-pack-driven startup path that reads the active plan registry, inspects
  the current git diff, maps the slice to MP scope, and routes accepted
  decisions/findings into the correct plan docs or ledgers automatically.
  Treat that as architecture work for the extracted platform, not as a
  VoiceTerm-only operator habit.
- Current governance-quality gap: plan/startup evidence still needs a
  meta-layer that can report not just code findings but governance findings.
  The platform should be able to say whether every guard has tests, every
  probe has tests, every registered guard runs in CI, every exception entry
  covers a real violation, and every workflow has a timeout. JSONL writers
  and evidence collectors also need integrity checks so a malformed row or
  silent skip is surfaced as a loss of evidence rather than disappearing from
  the record. When the system encodes large static tables as Python
  tuples/functions instead of policy or JSON/YAML config, that should surface
  as a separate data-as-code smell.
- Portable-engine framing: `MP-376` is the reusable engine/adoption layer
  and `MP-377` is the product/repo-governance platform. The engine should
  expose reusable guards, probes, evidence contracts, and startup artifacts;
  repo-governance should own per-repo policy, preset, and adoption routing.
  Keep that split explicit so portable machinery does not absorb product
  authority and product scope does not leak into the engine contract.
- Self-hosting simplification rule: once the blocker tranche and `P0` spine
  are green, run one governance-engine consolidation pass on plan overlap,
  bootstrap-token burden, review-channel sprawl, repeated checker/reporting
  boilerplate, and spec-vs-reality labeling so the platform becomes evidence
  that its own rules improve the codebase operating them.
- Self-hosting structure-governance follow-up: that consolidation pass must
  extend the existing package-layout / compatibility-shim governance into a
  broader repo-owned structure policy over `devctl` root budgets, parser and
  command placement, subsystem file-count budgets, source-of-truth ownership,
  active-doc lifecycle, and shim expiry so the engine can block the same
  accretive sprawl it currently reports.
- Documentation-authority follow-up: this self-hosting pass must also deliver
  one unified docs system for the platform itself. The repo needs governed
  doc classes/lifecycles, bounded hot/warm/cold AI context, active-plan and
  startup-token budgets, canonical markdown schema + anchor rules, and
  docs-governance enforcement so scope stops getting lost in doc sprawl.
- Documentation-authority first-step rule: do not start this cleanup as
  another prose-only effort. The first bounded operator/AI entrypoint should
  be a repo-owned `devctl` command that scans governed markdown, emits the
  current doc registry/authority state, reports format drift and over-budget
  docs, and proposes consolidation targets before `--write` remediation lands.
- Full `dev/guides/SYSTEM_AUDIT.md` intake rule: treat the audit's whole tiered action
  plan as canonical intake that must be mapped into the existing plan system,
  not left in a parallel document. Required mapping: Tier `-1` security ->
  blocker tranche; Tier `0` evidence/feedback -> startup/evidence/context
  closure; Tier `1` bootstrap compression -> hot/warm/cold startup context;
  Tier `2` memory/sessions -> `ContextPack` + memory bridge; Tier `3`
  structural debt -> self-hosting simplification; Tier `4` surface
  simplification -> command/workflow consolidation; Tier `5` portability ->
  repo-pack/packaging/adoption proof; Tier `6` black-box strengthening ->
  missing guards/probes + governance-ledger closure; Tier `7` test hardening
  -> guard/runtime/integration coverage.
- Portability-sequencing rule: do not wait until final packaging work to prove
  the authority loop detaches from VoiceTerm. Once startup authority plus one
  report-only runtime slice exist, run an intentionally rough second-repo
  smoke test through repo-pack selection, one typed action, one blocking
  check, one finding/evidence write, and one shared status/report render so
  hidden VoiceTerm assumptions fail early instead of in Phase 7 polish.
- Path-authority rule: do not replace `active_path_config()` sprawl with one
  new giant hidden authority object. `RepoPathConfig` must decompose into
  bounded groups such as repo roots, artifact/report roots, plan/docs
  authority paths, memory roots, and review/bridge paths so portable modules
  only learn the path family they actually need.
- Proof-scoreboard rule: the portable-governance proof should stay small and
  legible. At minimum track time-to-first-governed-run for a new repo, hard-
  guard blocked-change count, reviewed false-positive rate, quality/cost per
  successful fix, and whether a second repo works without core-engine
  patches.
- Next coherence-layer follow-up after the current `P0` blockers: widen the
  existing naming-consistency seed into a portable, repo-policy-backed
  naming/organization enforcement layer that can catch cross-file naming
  drift, contract-field naming drift, import-pattern drift, and structural
  template drift without hardcoding VoiceTerm-specific conventions into the
  engine. Start advisory where calibration is unknown; promote only after
  ledger-backed review evidence says the rules are accurate.
- Follow-up after that intake gap is explicit: add one repo-neutral,
  repo-pack-aware work-intake / startup-authority surface so AI agents and
  humans can derive "what plan is active, what changed, what bundle applies,
  and where accepted outcomes must be recorded" from the same executable
  model instead of reconstructing it from prose plus operator memory.
- Current plan amendment from the 2026-03-19 authority-loop audit: do not
  treat repo-pack definition alone as sufficient. The execution scope must
  also include the full runtime rewrite of module-level
  `active_path_config()` freezes, bundle/check extensibility, platform-wide
  contract versioning, proof-pack/evaluation schema, and provenance closure
  for findings/runs/policy state.
- Current transition-sequencing amendment from the 2026-03-19 validator pass:
  do not freeze runtime review identity before the evidence identity scheme is
  unified. Treat the evidence work as Phase `5a` (identity freeze in parallel
  with repo-pack activation and plan registry) plus Phase `5b`
  (provenance/ledger closure after the first runtime slice).
- Current migration-governance amendment from the same pass: Phase 2 must use
  a compatibility-first repo-pack rollout, the legacy governance-review
  ledger needs backfill/upgrade coverage before hard schema enforcement,
  `MP-359` path cleanup is a dependency of the repo-pack rewrite, and Phase 7
  proof criteria must distinguish portable guards from VoiceTerm-specific
  repo-structure guards.
- Current planning-review amendment from the same pass: repo-neutral plan
  hardening must flow through `PlanRegistry` + `PlanTargetRef` +
  `WorkIntakePacket`, reuse the review-channel packet/reducer path for
  plan-gap/patch/ready packets, and resolve canonical markdown targets by
  registry-generated stable anchors rather than brittle surrounding prose or
  raw line numbers. Planning review also needs intake-backed writer leases,
  explicit mutation ops, and a minimum bootstrap artifact set for non-
  VoiceTerm repos. Do not add a second authoritative `plan.md`.
- Current final architecture adjudication from the combined 2026-03-19
  Codex runtime slice plus Claude architecture pass: keep
  `WorkIntakePacket` and `CollaborationSession` as separate `P0`/`P1`
  contracts, keep intake-backed writer leases as the authority model for
  canonical plan/session mutation, and treat `version_counter` /
  `expected_revision` / `state_hash` checks as supplemental freshness guards
  rather than replacements for designated writer ownership. Startup may auto:
  inspect repo state, refresh stale authority artifacts, resume exactly one
  valid session, mark stale runtime/session attachment as `runtime_missing`
  or emit one bounded repair receipt, and emit one bounded intake/resume
  packet. Startup must not auto: guess among multiple active
  plans, launch conductors, or promote itself into `active_dual_agent`
  without explicit operator/policy choice. Phase 7 proof now also needs a
  replayable single-agent vs multi-agent comparison with adjudicated
  findings and quality-to-cost telemetry instead of asserting reviewer-loop
  value informally.
- Startup-token burden is now explicit product debt: the repo should stop
  re-deriving the same maintainer context every session and instead move to a
  cached repo-intelligence layer (`plan snapshot`, `command map`,
  `convention snapshot`, `map snapshot`, targeted-check hints, filtered probe
  view) plus one bounded `startup-context` / `work-intake` surface that
  refreshes only when git state, policy, or active-plan state actually
  changes.
- Memory-integration correction: the Rust Memory Studio already ships a real
  v1 substrate (`ContextPack`, `SurvivalIndex`, deterministic retrieval
  queries, JSONL persistence, in-memory index, staged SQLite schema), so the
  startup-authority path should compose with that system rather than rebuild a
  second unrelated memory stack. The open gap is integration: governance
  evidence and cached repo-intelligence artifacts still do not flow into one
  shared bounded packet with memory exports, and Memory Studio is not yet a
  standalone startup authority by itself.
- Bridge task: add one concrete governance-to-memory bridge that writes
  findings, run records, and repo-intelligence snapshots into the Rust memory
  substrate and lets `startup-context` / `master-report` consume that same
  bounded packet instead of stitching the evidence together ad hoc.
- Architectural Knowledge Base direction accepted (2026-03-17): the platform
  should provide a topic-keyed, SQLite-backed knowledge store so AI agents
  retrieve bounded architectural context by topic chapter instead of loading
  entire plan documents. Auto-capture scripts flag architecturally significant
  events (contract changes, guard/probe registration, plan milestones, schema
  migrations). Each topic chapter has a token budget and exports as JSON into
  the existing `ContextPack` system. The `ConceptIndex` / ZGraph navigation
  artifact maps topic dependencies for graph-traversal-based selective
  retrieval. `P0` prerequisite: activate the SQLite runtime and freeze the
  evidence-to-memory bridge. `P1` deliverable: full topic-keyed knowledge
  base with auto-capture, chapter budgets, and ConceptIndex integration.
  Architecture details in `dev/active/ai_governance_platform.md` under
  "Architectural Knowledge Base (Topic-Keyed AI Context)".
- Bootstrap/adoption should also stop starting from raw policy JSON plus
  scattered prose only. Add one reviewed repo-local governance contract
  surface (`project.governance.md` as the current working name) that AI can
  draft deterministically from repo facts, humans can finish with priorities /
  debt / exception intent, and later startup/policy flows can consume as one
  bounded source of truth.
- Accepted setup-flow shape: `governance-draft` scans repo structure,
  languages, test/CI shape, import topology, and current quality baselines to
  draft that contract; human review/approval fills the non-deterministic
  fields; `governance-bootstrap` and/or a later `governance-init` materialize
  repo policy and startup surfaces from the approved contract; later drift
  scans should suggest contract updates when the repo no longer matches the
  declared layers/roots/rules.
- Recursive convergence thesis is now explicit architecture work: the system
  already re-measures fixes in pieces (`guard-run`, `probe-report`, Ralph
  loops), but it still lacks one cached aggregate evidence surface
  (`master-report`) and one fixed-point orchestration surface (`converge`) for
  the whole guard/probe/ledger/convention stack. Do not treat that loop as
  "done" until the remaining artifact families are schema-versioned and the
  aggregated evidence contract is stable.
- Governance-completeness is part of that convergence surface: `master-report`
  should aggregate not only code findings but meta-findings about guard/test/
  CI/exception coverage, and `converge` should be able to drive the platform
  toward a fixed point where the governance layer itself is internally
  consistent.
- 25-agent architecture audit completed (2026-03-17): every major surface
  audited (Rust A-, Python governance B+, guards B, probes B-, operator
  console B+, CI B-, config A, docs A-, command UX B, portability 62/100,
  error handling B, AI bootstrap C+, self-consistency C). Concrete gaps
  closed in `ai_governance_platform.md` next-action items 30-33:
  `check_governance_closure` meta-guard, JSONL/exception immediate fixes,
  command UX standardization, CI workflow timeouts. Plans are now
  execution-ready.
- Accepted navigation-layer shape: add one deterministic concept index
  (`ConceptIndex`, optionally emitted in a ZGraph-compatible encoding) above
  the contract/policy/plan/map registry stack so startup/work-intake can route
  by concepts without rereading the whole repo. Keep that index generated from
  canonical contracts, plans, command taxonomy, and guard/probe metadata; do
  not let semantic/vector retrieval become the only authority.
- Startup-surface rule: keep one startup artifact family only. `startup-
  context`, `WorkIntakePacket`, and later `ContextPack` are the canonical
  startup/session packets; do not introduce a parallel `bootstrap-context`,
  second manifest family, or free-form session compass that can drift from the
  tracked authority chain.
- Knowledge-base sequencing rule: the architectural knowledge-base / chapter /
  ConceptIndex direction is valid, but it stays behind the current `P0`
  contract/evidence freeze. Immediate priority is to fix the concrete defects
  surfaced by the first governance-quality-feedback attempt: orphan library
  without CLI/artifact wiring, per-check scoring keyed too loosely, canonical
  `ReviewState` payload still carrying compatibility extras, Halstead file
  paths still absolute, and missing dedicated tests for the new package.
  Treat those as the next bounded execution slice before any broader
  knowledge-base capture/UX work.
- Quality-feedback scoring direction: do not treat the first single composite
  maintainability score as the final product contract. The repo-aligned target
  is a transparent multi-lens scorecard with explicit evidence coverage:
  `CodeHealthScore`, `GovernanceQualityScore`, and `OperabilityScore`, plus at
  most one secondary gated overall summary. Do not use median as the top-level
  cross-lens aggregator because it can hide a red lens; if robustness is
  needed, apply median only within one lens across related sub-metrics.
- Naming/convention ownership rule: keep `MP-267` limited to repo-local
  cohesion cleanup. Track the portable convention engine (`naming-scan`,
  `naming-report`, repo-policy schema, reusable naming/organization
  guards/probes) in `portable_code_governance.md`, and track startup/work-
  intake integration plus command-goal taxonomy in
  `ai_governance_platform.md`.
- Current probe-signal calibration: the canonical `devctl probe-report` output
  on this tree is dominated by Python readability/organization work rather
  than Rust ownership/concurrency work (`107` findings total, `98` Python,
  led by `probe_identifier_density` and `probe_blank_line_frequency`). Treat
  that as slice-specific cleanup pressure that should drive filtered
  startup/intake views, not as a claim that the repo's global architecture
  risk is primarily Python readability debt.
- Shared-state parity follow-up: Rust↔Swift daemon/mobile wire names already
  have an explicit guard, but equivalent Python runtime models remain
  unguarded copies. Keep the missing Rust daemon ↔ Python runtime parity guard
  in the `MP-377` contract-closure lane until the shared state/service seam is
  enforced across all consumers.
- Probe guidance still needs one authoring contract: the current probe family
  emits useful `ai_instruction` content, but authoring style is inconsistent
  across families (per-signal dicts, severity dicts, and inline constants).
  Treat a shared instruction template/keying rule as part of AI-usability
  hardening, not as optional polish.
- Current cross-surface convergence gap: the typed runtime direction is real,
  but the repo still emits multiple review/control shapes across backend and
  clients. `ReviewState` is still produced in different bridge-backed and
  event-backed forms, the live review loop still depends on `bridge.md`
  as temporary authority, the review-channel `project_id` is still derived
  from absolute checkout paths, the current mobile relay guard can return
  green with zero matched Rust↔Swift pairs, and PyQt6/iPhone still consume
  compatibility payloads before canonical typed state.
- Accepted next bounded cross-surface order: (1) make bridge-backed and
  event-backed review-channel producers emit one exact `ReviewState` contract
  and move review-channel identity onto stable repo identity instead of
  absolute paths; (2) add the missing daemon-state contract plus executable
  Rust ↔ Python ↔ Swift parity guard so the mobile/backend seam stops
  reporting false-green coverage; (3) migrate Operator Console and iPhone to
  typed-state-first consumers with markdown / `controller_payload` /
  `review_payload` fallback-only behavior; (4) only then keep burning down
  repo-pack path leaks, local risk bucketing, and hard-coded CLI argv
  contracts in surface code.
- Theme and Memory remain active tracked work, but they are not the repo's
  current top-level strategic lane while `MP-377` `P0` contract-freeze is
  active.
- Repo-wide status/read-order rule: after this snapshot, read
  `dev/active/ai_governance_platform.md` for current strategic context and use
  Theme/Memory/operator/mobile docs only for scoped implementation detail.
- Execution mode: prioritize platform extraction, runtime-authority cleanup,
  and cross-client parity; keep unrelated product-lane work maintenance-only
  unless it directly supports that sequence.
- Maintainer-doc clarity update: `dev/DEVELOPMENT.md` now includes an end-to-end lifecycle flowchart plus check/push routing sections while `AGENTS.md` remains the canonical policy router.
- Tooling docs-governance update: `devctl docs-check --strict-tooling` now enforces markdown metadata-header normalization for `Status`/`Last updated`/`Owner` blocks via `check_markdown_metadata_header.py`.
- External publication governance update: `devctl` is gaining a tracked
  publication-sync surface so external papers/sites can declare watched source
  paths, emit stale-publication drift reports, and surface hygiene warnings
  when repo changes outpace synced public artifacts.
- Loop architecture clarity update: `dev/ARCHITECTURE.md` and
  `dev/DEVELOPMENT.md` now document the custom repo-owned Ralph/Wiggum loop
  path and the federated-repo import model in simple flowchart form.
- Continuous swarm hardening kickoff: `dev/active/continuous_swarm.md` now
  tracks the local-first Codex-reviewer / Claude-coder continuation loop,
  launcher modularization, peer-liveness guards, context-rotation handoff, and
  the later proof-gated template-extraction path.
- Desktop operator console prototype update:
  `dev/active/operator_console.md` now tracks a bounded optional PyQt6
  VoiceTerm Operator Console wrapper over the existing Rust runtime and
  `devctl` control surfaces. The active plan now treats this as a repo-aware
  desktop controller shell over typed repo-owned commands, workflow guidance,
  and bounded AI assist, but still not as a replacement execution authority or
  second control plane.
- Loop comment transport hardening update: shared workflow-loop `gh` helpers now
  avoid invalid `--repo` usage for `gh api` calls so summary-and-comment mode
  can publish and upsert commit/PR comments reliably.
- Audit-remediation update: Round-2 high-severity audit fixes landed for prompt
  detection hot-path queue behavior, transcript merge-loop invariants,
  persistent-config duplication reduction, and devctl release/comment/report
  helper hardening with expanded unit coverage.
- Runtime cleanup update: startup splash logo coloring now uses a single
  theme-family accent (no rainbow line rotation), and the stale orphan
  `rust/src/bin/voiceterm/progress.rs` module has been removed.
- Theme Studio maintainability cleanup update: home/colors/borders/components/
  preview/export byte handling now routes through page-scoped helper functions
  in `theme_studio_input.rs`, with runtime style-adjustment routing split into
  focused helper paths; follow-up dedup also centralized vertical-arrow page
  navigation + runtime override cycle wiring so page handlers avoid repeated
  dispatch scaffolding. Theme Studio suite and full CI profile remained green.
- Theme Studio readability follow-up update: `theme_studio/home_page.rs` now
  uses a dedicated row-metadata struct with static tip strings (instead of
  per-row tip `String` allocations), and writer-state test-only timing
  constants were moved out of `writer/state.rs` production scope into
  `writer/state/tests.rs` so runtime modules stay focused on shipped code.
- CI compatibility hotfix update: release-binary workflow runner labels now use
  actionlint-supported macOS targets, latency guard script path resolution now
  supports `rust/` with `src/` fallback, and explicit `devctl triage --cihub`
  opt-in now preserves capability probing when PATH lookup misses the binary.
- Release workflow stability update: `release_attestation.yml` action pins were
  refreshed to valid GitHub-owned SHAs, and `scorecard.yml` now keeps
  workflow-level permissions read-only with write scopes isolated to the
  scorecard job so OpenSSF publish verification succeeds.
- Release preflight auth stability update: `.github/workflows/release_preflight.yml`
  runtime bundle step now exports `GH_TOKEN: ${{ github.token }}` so
  `devctl check --profile release` can run `gh`-backed release gates in CI.
- Release governance update (2026-03-09): the current pre-release audit
  showed that shipping the mobile/control-plane tranche cleanly requires full
  canonical-doc coverage, not just changelog plus a subset of guides.
  Maintainer docs (`AGENTS.md`, `dev/guides/DEVELOPMENT.md`,
  `dev/history/ENGINEERING_EVOLUTION.md`) and canonical user docs
  (`QUICK_START.md`, `guides/TROUBLESHOOTING.md`) now carry explicit release
  notes for the mobile app/install/control-plane path, and the release bundle
  expectation is that `check_mobile_relay_protocol.py` remains green so Rust,
  Python, and iOS payload contracts ship together.
- Release preflight SARIF permission update:
  `.github/workflows/release_preflight.yml` preflight job now grants
  `security-events: write` so zizmor SARIF uploads can publish to code scanning.
- Release preflight zizmor execution update:
  `.github/workflows/release_preflight.yml` now sets zizmor
  `online-audits: false` to prevent cross-repo compare API 403 failures from
  blocking release preflight.
- Release preflight security-scope update:
  `.github/workflows/release_preflight.yml` now runs
  `devctl security` with `--python-scope changed` and the same resolved
  `--since-ref/--head-ref` range used by AI-guard so preflight enforces
  commit-scoped Python checks instead of full-repo formatting backlog, and it
  avoids hard-failing on repository-wide open CodeQL backlog in release
  preflight; `cargo deny` remains blocking while `devctl security` report
  output is advisory evidence in that lane.
- Compat-matrix parser resilience update: compatibility/naming guard scripts now
  share a minimal YAML fallback parser so tooling CI and local checks stay
  deterministic in minimal Python environments without `PyYAML`.
- Compat-matrix parser fail-closed update: malformed inline collection scalars
  in fallback mode now raise explicit parse errors instead of silent coercion.
- Tooling security hardening update: `devctl` loop/mutation/release helper
  defaults now resolve temporary artifact paths via the system temp directory
  API instead of hardcoded `/tmp` literals, satisfying Bandit `B108` checks in
  release-security gates.
- Control-plane simplification update: MP-340 is now Rust-first only (Rust
  overlay + `devctl` + phone/SSH projections). The optional `app/pyside6`
  command-center track is retired from active execution scope.
- CI lane compatibility update: Rust CI MSRV lane now uses toolchain `1.88.0`
  to match current transitive dependency requirements (`time`/`time-core`);
  CI/docs references were synchronized to the new lane contract.
- MP-346 checkpoint update: `CP-016` automated continuation rerun is captured
  at `dev/reports/mp346/checkpoints/20260305T032253Z-cp016/`; operator
  release-scope matrix update is applied (IDE-first `4/4` required cells:
  Cursor+Codex, Cursor+Claude, JetBrains+Codex, JetBrains+Claude), with
  `other` host and `gemini` baseline checks deferred to post-release backlog.
- MP-346 architecture-audit status update (2026-03-05): IDE-first manual
  matrix closure requirement is complete (`4/4`), and no additional MP-346
  runtime/tooling blockers remain in the current non-regression rerun.
- MP-346 closure-followup update (2026-03-05): prior shape/duplication blockers are
  resolved via check-router/docs-check helper decomposition and duplication
  evidence is refreshed (`dev/reports/duplication/jscpd-report.json`,
  `duplication_percent=0.32`, `duplicates_count=14` after latest cleanup pass);
  closure non-regression rerun is green and the
  prior physical-host manual matrix `7/7` gate is superseded by the IDE-first
  release-scope matrix closure (`4/4`) recorded in `CP-016`.
- MP-347 verification refresh (2026-03-05): closure non-regression command pack
  row `2331` was rerun end-to-end and remains green after canonicalizing
  duplication-audit helper ownership and removing stale archive path literals
  from active docs/changelog.
- MP-347 guard-utility expansion update (2026-03-09): `devctl report` now
  supports `--python-guard-backlog` with ranked hotspot aggregation across
  `check_python_dict_schema`, `check_python_global_mutable`,
  `check_python_design_complexity`, `check_python_cyclic_imports`,
  `check_parameter_count`, `check_nesting_depth`, `check_god_class`,
  `check_python_broad_except`, and `check_python_subprocess_policy`, so Python
  clean-code debt can be burned down in priority order before stricter lane
  promotion.
- MP-347 broad-except hardening update (2026-03-09):
  `check_python_broad_except.py` now treats bare `except:` handlers as
  broad-except policy violations, and newly added fail-soft plotting/telemetry
  paths in devctl autonomy/data-science helpers now carry explicit
  `broad-except: allow reason=...` rationale comments.
- MP-347 mutable-state hardening update (2026-03-09):
  `check_python_global_mutable.py` now also enforces non-regressive growth of
  mutable default argument patterns (`[]`, `{}`, `set()/list()/dict()` style
  defaults) so Python mutable-state pitfalls are blocked even when `global`
  keywords are not involved.
- MP-347 suppression-debt update (2026-03-11): `check_python_suppression_debt.py`
  now enforces non-regressive growth of Python lint/type suppressions
  (`# noqa`, `# type: ignore`, `# pylint: disable`, `# pyright: ignore`)
  using tokenized comment scanning, and the portable Python preset now enables
  it by default so the same engine can block new suppression debt here or in
  another repo without hard-coded VoiceTerm path logic.
- MP-347 default-evaluation hardening update (2026-03-11):
  `check_python_global_mutable.py` now also blocks net-new function-call
  default arguments plus dataclass fields that evaluate mutable or callable
  defaults eagerly instead of routing through `field(default_factory=...)`, so
  the portable Python guard stack now covers the next default-argument trap
  slice without needing a second overlapping guard id.
- MP-347 portability hardening update (2026-03-11):
  `quality_policy.py` now resolves per-guard config payloads, standalone guard
  scripts can read those configs through `check_bootstrap.py`, and
  `devctl quality-policy` plus `devctl check --quality-policy` now surface and
  propagate the same policy-owned settings. VoiceTerm-specific `code_shape`
  namespace/layout rules moved out of the portable engine and into the
  repo-owned preset so another repo can reuse the same guard without hidden
  path assumptions.
- MP-347 portable complexity/import update (2026-03-11):
  `check_python_design_complexity.py` now blocks net-new branch-heavy or
  return-heavy Python functions using policy-owned thresholds (with a
  conservative portable default that repo policy can tighten), and
  `check_python_cyclic_imports.py` now blocks net-new top-level local import
  cycles with repo-policy allowlists for known transitional debt. Both guards
  are registered in the portable Python preset, catalog, bundles, workflows,
  and Python backlog report so the next portable hard-guard backlog narrows to
  Rust `result_large_err` / `large_enum_variant`.
- MP-376 portable governance execution-doc update (2026-03-11):
  added `dev/active/portable_code_governance.md` to track the broader
  reusable code-governance-engine direction explicitly: engine vs repo-policy
  boundaries, measurement/data-capture goals, off-repo snapshot/export needs,
  and the eventual multi-repo pilot rollout. This keeps the strategic
  portability/evaluation goal from being scattered across review-probe log
  entries alone.
- MP-377 reusable AI governance platform kickoff (2026-03-12):
  added `dev/active/ai_governance_platform.md` to separate the bigger product
  extraction problem from the portable-governance-engine plan. `MP-376` stays
  focused on guards/probes/policy/bootstrap/export/evaluation, while `MP-377`
  now owns the broader reusable platform architecture: shared runtime/action
  contracts, repo-pack/adopter boundaries, frontend convergence across CLI /
  PyQt6 / overlay / phone surfaces, and the path toward VoiceTerm becoming a
  first consumer of an installable AI-governance platform instead of the place
  where the whole system remains embedded.
- MP-377 runtime-contract expansion update (2026-03-12):
  `ControlState` is no longer the only executable runtime seam. The new
  `dev/scripts/devctl/runtime/review_state.py` contract now normalizes
  review-channel `review_state.json` and `full.json` artifacts into typed
  session/queue/bridge/packet/registry state, and the Operator Console
  review/session/collaboration readers now consume that shared runtime model
  instead of re-parsing raw review payloads locally. This keeps the current
  migration moving in the planned direction: compact cross-surface summary in
  `ControlState`, richer review-channel detail in adjacent runtime contracts,
  and thinner frontend adapters over both.
- MP-377 seam-cleanup follow-up (2026-03-13):
  the remaining live `probe_single_use_helpers` debt in the current runtime /
  governance extraction seam is burned down. `controller_action.py`,
  `docs_check.py`, `path_audit.py`, and `runtime/control_state.py` now keep
  only named seams instead of one-use private wrappers, and the probe backlog
  now narrows to the real portability issue: the large
  `dev/scripts/devctl` root compatibility-shim population that still needs
  package/repo-pack extraction work rather than more local cleanup.
- MP-377 repo-pack surface-generation update (2026-03-13):
  the first concrete Phase 2 vertical slice is now in repo state.
  `dev/config/devctl_repo_policy.json` owns a new
  `repo_governance.surface_generation` section for repo-pack metadata,
  template context, and governed surfaces; `devctl render-surfaces` renders or
  validates those outputs; `check_instruction_surface_sync` plus
  `docs-check --strict-tooling` enforce template-backed surface drift; and
  starter bootstrap/template flows now seed the same contract for adopter
  repos. The remaining Phase 2 follow-up is to add first-class context-budget
  profiles / usage-tier guidance on top of this generated-surface path.
- MP-377 generated-surface integration follow-up (2026-03-13):
  the new repo-pack surface-generation slice is now wired end to end instead
  of half-landed. `render-surfaces` is registered in the public CLI/listing,
  its parser and command implementation now live under governance-owned
  namespaces instead of crowded flat roots, and the paired
  `package_layout/check_instruction_surface_sync.py` guard now runs in
  tooling/release governance lanes.
- MP-377 repo-pack surface-generation hardening update (2026-03-13):
  report-mode surface checks now tolerate missing local-only outputs such as
  `CLAUDE.md` while `render-surfaces --write` still materializes them;
  bootstrap/template starter flows now point adopters at that write path; and
  maintainer docs plus targeted tests now cover the generated-surface contract
  instead of leaving it implicit.
- MP-377 generated-surface concurrency follow-up (2026-03-13):
  the broader governance namespace split briefly reintroduced stale targeted
  references after the first validation pass. The active runtime helper path is
  `dev/scripts/devctl/governance/surface_runtime.py`, the helper now resolves
  `check_agents_bundle_render` through the package import path so focused
  pytest collection stays stable, the public generated-surface runner now lives
  under `dev/scripts/checks/package_layout/`, and the strict-tooling
  docs-check fixture now points at
  `dev/scripts/devctl/commands/governance/render_surfaces.py` instead of the
  old flat command location.
- MP-377 self-hosting layout follow-up (2026-03-13):
  the generated-surface/layout slice is still green after the concurrent
  modularization churn, but that green status needs the right interpretation:
  `check_package_layout.py` is currently enforcing freeze-mode crowding rules
  for `dev/scripts/checks`, `dev/scripts/devctl`,
  `dev/scripts/devctl/commands`, and `dev/scripts/devctl/tests`. That means
  new sprawl is blocked and the recent governance files landed in the correct
  namespaces, but the repo still needs more package/test decomposition work
  before those roots are actually tidy rather than merely baselined.
- MP-377 machine-first governance-command follow-up (2026-03-13):
  the moved governance command family now shares one package-local output/error
  helper that treats JSON as the canonical machine payload and markdown as the
  human projection, and a dispatch-level CLI stability test now proves parser
  wiring, `COMMAND_HANDLERS`, and JSON output across
  `governance-bootstrap`, `governance-export`, `governance-review`, and
  `render-surfaces`. The self-hosting architecture guard was widened in the
  same slice so aliased nested command imports under
  `dev/scripts/devctl/commands/governance/` validate correctly instead of
  forcing the repo back toward flat-root-only command wiring.
- MP-377 machine-output contract audit (2026-03-13):
  audited the shared output path before widening the machine-first rule across
  the repo. The current `--output` flow already avoids full stdout JSON dumps;
  `write_output()` writes the artifact and prints only `Report saved to: ...`.
  The real remaining gap is architectural: that receipt is not a stable
  machine control envelope, and `RunRecord` / `devctl_events` /
  `data-science` still do not record artifact bytes, hashes, or estimated
  token cost. The next slice should add a dedicated machine-artifact emitter
  for JSON-canonical report/packet surfaces (`governance-*`,
  `platform-contracts`, `probe-report`, `data-science`, `loop-packet`, later
  review/autonomy) instead of globally rewriting `emit_output()` for every
  human-oriented command.
- MP-377 machine-artifact emission update (2026-03-13):
  landed the first extraction-friendly implementation of that contract. The
  JSON-canonical surfaces above now emit compact file artifacts plus compact
  JSON stdout receipts when `--format json --output ...` is used, and command
  telemetry/data-science aggregation now capture artifact path/hash/byte/token
  metrics instead of only success/duration. That gives the repo its first
  measurable control-channel contract for AI loops without forcing the same
  behavior onto human-first commands.
- MP-377 simple-command lane follow-up (2026-03-13):
  the first vibecoder-facing façade over policy selection is now in repo
  state. `dev/config/devctl_policies/launcher.json` defines a focused Python
  launcher lane for `scripts/` + `pypi/src`, and `devctl` now exposes that
  lane through short wrappers (`launcher-check`, `launcher-probes`,
  `launcher-policy`) instead of requiring raw `--quality-policy` path
  spelling. This keeps policy files authoritative while proving the product can
  project simpler task-shaped command names for repeated workflows.
- MP-377 launcher command-source pilot (2026-03-13):
  the first launcher-only hard guard is now live behind that focused lane.
  `check_command_source_validation.py` catches free-form `shlex.split(...)`
  on CLI/env/config input, raw `sys.argv` forwarding, and env-controlled
  command argv without validator helpers; `scripts/python_fallback.py` now
  rejects deprecated `--codex-args` free-form passthrough, and
  `pypi/src/voiceterm/cli.py` now validates bootstrap repo URL/ref plus
  forwarded argv before invoking `git` or the native binary.
- MP-377 repo-pack push-governance update (2026-03-21):
  the first repo-pack-owned VCS command-routing slice is now real. The new
  `repo_governance.push` policy owns default remote, development/release
  branch names, protected-branch rules, and the required preflight/post-push
  flow; `devctl push` is the new canonical branch-push surface with
  `TypedAction(action_id="vcs.push")` / `ActionResult` output; generated
  starter surfaces now include a pre-push hook stub; and legacy `sync` /
  `ship` helpers now consume the same policy instead of embedding branch and
  remote defaults in Python.
- MP-376 export/evaluation update (2026-03-11):
  `devctl governance-export` now packages the governance stack into an
  external snapshot/zip with fresh `quality-policy`, `probe-report`, and
  `data-science` artifacts, `dev/guides/PORTABLE_CODE_GOVERNANCE.md` now
  defines the engine/preset/repo-policy boundary plus the evaluation rubric,
  and template schemas now capture both the guarded-episode measurement
  contract and the multi-repo benchmark record. The first broad external pilot
  corpus source is explicitly the maintainer GitHub repo inventory
  (`https://github.com/jguida941?tab=repositories`), while actual non-VoiceTerm
  pilot execution remains open follow-up work.
- MP-376 pilot-onboarding update (2026-03-11):
  the first non-VoiceTerm pilot ran against `ci-cd-hub` and exposed the
  remaining portability leaks directly. `devctl governance-bootstrap` now
  normalizes copied/submodule repos with broken `.git` indirection, `check` /
  `probe-report` / `governance-export` now accept `--adoption-scan` for
  full-surface onboarding runs without a trusted baseline ref, and
  `probe_exception_quality.py` joins the review-probe suite to surface
  suppressive Python exception handling patterns seen in external tooling code.
- MP-376 measurement-ledger update (2026-03-11):
  `devctl governance-review` now records adjudicated guard/probe findings into
  `dev/reports/governance/finding_reviews.jsonl`, writes rolled-up
  `review_summary.{md,json}` artifacts, and feeds those metrics into
  `devctl data-science` so false-positive rate, confirmed-signal rate, and
  cleanup progress are tracked as durable repo evidence instead of chat-only
  notes.
- MP-376 live-cleanup adjudication update (2026-03-11):
  the first high-severity probe debt was burned down through that ledger:
  `probe_exception_quality` findings in `dev/scripts/devctl/collect.py` were
  fixed by narrowing fallback exception handling, the medium translation hint in
  `dev/scripts/devctl/commands/check_support.py` was removed by replacing the
  subprocess-based tempdir lookup with a direct Python implementation, and the
  reviewed outcomes are now recorded as `fixed` in `governance-review`.
- MP-376 portable shim-governance update (2026-03-12):
  compatibility shims are now a first-class portable governance primitive
  instead of a VoiceTerm-only package-layout exception. The engine now owns a
  shared package-layout bootstrap seam, validates shim shape structurally,
  supports policy-owned required metadata fields (`owner`, `reason`, `expiry`,
  `target`), and lets crowded-root/family reports exclude approved shims from
  implementation density while still surfacing shim counts explicitly.
- MP-376 shim-debt probe update (2026-03-12):
  the same portable shim primitive now powers an advisory review layer too.
  `probe_compatibility_shims.py` surfaces missing/expired shim metadata,
  unresolved shim targets, and shim-heavy roots/families, while the fallback
  `run_probe_report.py` path now resolves probe entrypoints from the shared
  quality policy/script catalog instead of carrying a stale hard-coded list.
- MP-376 package-layout wrapper follow-up (2026-03-12):
  the crowded `dev/scripts/checks/` root no longer hard-codes
  `package_layout.command` as its only allowed shim shape. The portable shim
  validator now ignores canonical shim metadata lines in the thin-wrapper line
  budget, accepts any `package_layout.*` wrapper at the crowded root, and the
  paired devctl tests moved under `dev/scripts/devctl/tests/checks/package_layout/`
  so the crowded test root mirrors the same package boundary.
- MP-376 shim-family cleanup update (2026-03-13):
  retired the next largest temporary `dev/scripts/devctl` root shim family,
  `autonomy_*`, by migrating the remaining repo-visible docs/history/plan
  references to the canonical `dev/scripts/devctl/autonomy/` modules, renaming
  the shim-probe's synthetic fixture paths away from a live wrapper name, and
  deleting 18 obsolete root wrappers. `probe-report` now shows the broader
  `dev/scripts/devctl` root backlog down from 57 temporary wrappers / 135
  repo-visible references to 39 wrappers / 87 references, with `cli_parser_*`
  now the largest remaining family by wrapper count and `triage_*` the next
  highest by repo-visible references.
- MP-376 shim-family cleanup update (2026-03-13):
  finished the next caller-migration tranche after `autonomy_*` by moving the
  remaining repo-visible `cli_parser_*`, `triage_*`, and `triage_loop_*`
  docs/history/active-plan references to the canonical
  `dev/scripts/devctl/cli_parser/` and `dev/scripts/devctl/triage/` packages,
  then deleting 16 obsolete root wrappers. `probe-report` now shows the
  broader `dev/scripts/devctl` root backlog down again from 39 temporary
  wrappers / 87 repo-visible references to 23 wrappers / 46 references; the
  next wrapper-heavy families are `process_sweep_*` and `security_*`, while
  the current repo-visible-reference examples include
  `data_science_metrics.py` and `governance_bootstrap_*`.
- MP-376 shim-family cleanup update (2026-03-13):
  retired the temporary `security_*` root shim family by moving workflow/docs/
  history references to the canonical `dev/scripts/devctl/security/`
  modules and deleting the four obsolete root wrappers. The next
  shim-governance follow-up is now the
  remaining `process_sweep_*` family plus the docs-led wrapper examples
  (`data_science_metrics.py`, `governance_bootstrap_*`) that still keep the
  `dev/scripts/devctl` root above its temporary-shim budget.
- MP-376 design-smell cleanup update (2026-03-11):
  the next medium-severity `probe_single_use_helpers` slice is now burned down
  too: `dev/scripts/devctl/collect.py` no longer carries one-use file-local
  helpers, and the data-science row collectors were split into
  `dev/scripts/devctl/data_science/source_rows.py` so
  `dev/scripts/devctl/data_science/metrics.py` stays focused on snapshot
  orchestration. Those reviewed outcomes are also now recorded as `fixed` in
  `governance-review`.
- MP-376 triage single-use-helper follow-up (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup moved the
  CIHub/external-input triage helpers out of
  `dev/scripts/devctl/commands/triage.py` so the command stays
  orchestration-focused, and the reviewed outcome is now recorded as `fixed`
  in `governance-review`.
- MP-376 loop-packet single-use-helper follow-up (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down too:
  `dev/scripts/devctl/commands/loop_packet_helpers.py` no longer hides JSON
  source loading/command normalization or packet-body dispatch behind one-call
  wrappers. This was treated as a real design-smell signal, not a false
  positive, because the flagged helpers had no reuse or test-seam value; the
  behavior now lives directly in `_discover_artifact_sources()` and
  `_build_packet_body()`, and the reviewed outcome is now recorded as `fixed`
  in `governance-review`.
- MP-376 review-channel single-use-helper adjudication (2026-03-11):
  the next `probe_single_use_helpers` candidate under
  `dev/scripts/devctl/commands/review_channel_bridge_handler.py` is now logged
  as `deferred`, not `false_positive`. Before review, the probe emitted one
  file-level hint over five private helpers; after review, the repo state now
  records the narrower call explicitly: `_validate_live_launch_conflicts()`
  and `_load_bridge_runtime_state()` look like real one-use wrappers,
  `_resolve_promotion_and_terminal_state()` and `_build_sessions()` remain
  defensible seams, and `_post_session_lifecycle_event()` is borderline. That
  keeps the next cleanup selective and auditable instead of treating the whole
  hint as either pure noise or a blanket inline order.
- MP-376 review-channel single-use-helper cleanup (2026-03-11):
  that deferred `review_channel_bridge_handler.py` follow-up is now burned down
  with the selective fix the adjudication called for. Before the fix, the file
  mixed two real one-use wrappers with three meaningful seams; after the fix,
  the live-launch conflict logic now reuses
  `review_channel_bridge_action_support.py`, the one-use bridge-state wrapper
  is removed, and the remaining session/promotion/event boundaries now live as
  named action-support helpers instead of private single-use functions.
  `review_channel_bridge_support.py` stays back under the code-shape soft
  limit after that split. This was still treated as a real design-smell
  signal, not a false positive, and `probe_single_use_helpers` no longer flags
  the handler; the reviewed outcome is now recorded as `fixed` in
  `governance-review`.
- MP-376 governance-export single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/governance_export_artifacts.py`. Before the fix, the
  export path hid quality-policy, probe-report, and data-science artifact
  generation behind three one-call private helpers with no reuse or test-seam
  value; after the fix, `write_generated_artifacts()` writes those artifact
  families directly, `probe_single_use_helpers` no longer flags the file, and
  the reviewed outcome is now recorded as `fixed` in `governance-review`.
- MP-376 governance-export builder single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/governance_export_support.py`. Before the fix, the
  export builder hid repository-external destination validation, snapshot
  source copying, manifest emission, and path-containment checking behind four
  one-call private helpers with no reuse or seam value; after the fix,
  `build_governance_export()` performs those steps directly, leaves
  `_sanitize_snapshot_name()` as the only local helper boundary, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-376 watchdog-episode single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/watchdog/episode.py`. Before the fix, the episode
  builder hid provider inference, guard-family classification, and
  escaped-findings counting behind three one-call private helpers with no
  reuse or test-seam value; after the fix, `build_guarded_coding_episode()`
  performs those derivations directly, leaves `_snapshot()` as the only reused
  local helper boundary, and `probe_single_use_helpers` no longer flags the
  file. This was treated as a real design-smell hit, not a false positive, and
  the reviewed outcome is now recorded as `fixed` in `governance-review`.
- MP-376 watchdog-probe-gate single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/watchdog/probe_gate.py`. Before the fix, the probe gate
  hid allowlist loading, allowlist matching, and report summarization behind
  three one-call private helpers with no reuse or test-seam value; after the
  fix, `run_probe_scan()` performs those steps directly, focused unit tests now
  cover allowlist filtering/fail-open behavior, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-376 quality-policy-scope single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/quality_policy_scopes.py`. Before the fix, the scope
  resolver hid Python-root discovery plus configured-root normalization and
  coercion behind four one-call private helpers with no reuse or test-seam
  value; after the fix, `resolve_quality_scopes()` performs those steps
  directly while `_discover_rust_scope_roots()` remains the only meaningful
  helper boundary, focused unit tests now cover common Python-root discovery
  plus invalid/duplicate scope handling, and `probe_single_use_helpers` no
  longer flags the file. This was treated as a real design-smell hit, not a
  false positive, and the reviewed outcome is now recorded as `fixed` in
  `governance-review`.
- MP-376 review-probe-report single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/review_probe_report.py`. Before the fix, the aggregated
  probe reporter hid per-probe subprocess execution, hint enrichment, batch
  collection, and terminal hotspot rendering behind four one-call private
  helpers with no reuse or seam value; after the fix, `build_probe_report()`
  drives probe execution and risk-hint enrichment directly,
  `render_probe_report_terminal()` renders the top hotspot inline, focused
  unit tests now cover the terminal hotspot path, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-376 triage-support single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/triage/support.py`. Before the fix, the markdown
  renderer hid project snapshot, issue list, CIHub, and external-input
  sections behind four one-call private helpers with no reuse or seam value;
  after the fix, `render_triage_markdown()` builds those sections directly,
  focused unit tests now cover CIHub/external-input markdown rendering, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-359 operator-console bundle unblock follow-up (2026-03-11):
  the desktop proof lane is back to green after two bounded fixes. First,
  `app/operator_console/views/layout/__init__.py` now lazy-loads
  `WindowShellMixin`, `HAS_THEME_EDITOR`, and workbench helpers instead of
  importing them eagerly during package init, breaking the package-init
  cycle `help_dialog -> layout.__init__ -> ui_window_shell -> help_dialog`
  that had been failing `test_help_dialog.py` during collection. Second,
  `dev/scripts/devctl/phone_status_views.py` now routes compact/trace/action
  projection through the existing `_section()` helper instead of calling
  removed `_controller/_loop/_source_run/_terminal/_ralph` helpers, so the
  Operator Console phone snapshot path is no longer stuck in unavailable
  fallback. `app/operator_console/tests/` is green again in the canonical
  bundle proof path.
- MP-376 phone-status projection hotspot cleanup (2026-03-11):
  the next high-severity Python review-probe hotspot is now burned down in
  `dev/scripts/devctl/phone_status_views.py`. Before the fix,
  `compact_view()`, `trace_view()`, and `actions_view()` returned large
  ad-hoc dict literals and `view_payload()` plus `_render_view_markdown()`
  branched on raw strings, so the `probe_dict_as_struct` and
  `probe_stringly_typed` hints were treated as real signal, not false
  positives. After the fix, `PhoneStatusView` parses the view boundary once,
  typed projection models live in
  `dev/scripts/devctl/phone_status_projection.py`, focused phone-status tests
  cover compact fallback plus trace markdown rendering, `probe-report` no
  longer flags the file, and the follow-on file split keeps
  `phone_status_views.py` back under the code-shape soft limit.
- MP-359 presentation-state probe cleanup follow-up (2026-03-11):
  the remaining Operator Console advisory debt from the probe suite is now
  burned down in `app/operator_console/state/presentation/presentation_state.py`.
  Before the fix, the file hid snapshot-digest lane serialization,
  repo-analytics change-mix rendering, and CI KPI text behind one-call
  private helpers with no reuse or seam value; after the fix,
  `probe_single_use_helpers` no longer flags the file, the residual low
  formatter-helper `probe_design_smells` hint disappears in the same pass, and
  `app/operator_console/tests/state/test_presentation_state.py` remains green.
- MP-376 operator-console presentation-state single-use-helper cleanup (2026-03-11):
  the final repo-wide `probe_single_use_helpers` ledger cleanup is now burned
  down in `app/operator_console/state/presentation/presentation_state.py`.
  Before the fix, the presentation layer hid snapshot-digest lane
  serialization, repo-analytics change-mix formatting, and CI KPI rendering
  behind one-call private helpers with no reuse or test-seam value; after the
  fix, `snapshot_digest()`, `_build_repo_text()`, and `_build_kpi_values()`
  perform those derivations directly, focused presentation-state tests remain
  green, `probe_single_use_helpers` no longer flags any file repo-wide, and
  the reviewed outcome is now recorded as `fixed` in `governance-review`.
- MP-378 code shape expansion audit intake (2026-03-16):
  `dev/active/code_shape_expansion.md` now serves as the subordinate research
  and calibration companion for the next review-probe tranche instead of a
  parallel execution roadmap. The re-audit kept the candidate families, but
  tightened promotion rules: implementation still lands through
  `dev/active/review_probes.md` Phase 5b, every promoted probe needs explicit
  `review_lens` / `risk_type` / severity thresholds / `practices.py` guidance,
  `probe_method_chain_length` is dropped pending redesign, sequential
  mutation-on-dict findings fold into `probe_dict_as_struct` instead of a new
  standalone probe, and the later cross-file/language-expansion phases remain
  blocked on `MP-377` runtime/packaging contracts. Current likely first
  implementation slice: readability probes with proven local signal quality
  plus tuple-return, fan-out, side-effect, and match-arm evaluation.
- MP-350 closure update (2026-03-05): additive read-only MCP adapter
  implementation is complete with code-level contract helpers/tests for
  `check --profile release`, `ship --verify`, and cleanup protections;
  execution tracker moved to
  `dev/archive/2026-03-05-devctl-mcp-contract-hardening.md` and durable
  guidance lives in `dev/guides/MCP_DEVCTL_ALIGNMENT.md`.
- MP-347 architecture-audit refresh (2026-03-05): core tooling/runtime guard
  packs are green (`check_code_shape`, duplication audit with fresh `jscpd`,
  rust quality guards, workflow parity, strict-tooling docs governance), and
  strict hygiene catalog/docs alignment is restored for
  `check_duplication_audit_support.py`; remaining follow-up is scoped to
  risk-add-on SSOT consolidation, local strict-hygiene repeatability noise
  (`__pycache__` warning churn unless `--fix`), function-exception paydown
  before `2026-05-15`, and dead-code allow backlog reduction.
- MP-347 docs-policy dedup update (2026-03-06): docs-check path policy now has
  single-source ownership (`docs_check_policy.py`), and
  `docs_check_constants.py` is a compatibility re-export shim with dedicated
  regression coverage in `dev/scripts/devctl/tests/test_docs_check_constants.py`.
- MP-347 shape-governance refresh (2026-03-06): code-shape policy budgets and
  temporary function exceptions were synchronized for the current tooling
  refactor batch (active-plan sync, multi-agent sync, release parser wiring,
  and devctl command runners), with explicit owner/follow-up metadata and
  expiry tracking through `2026-05-15`.
- MP-347 docs-IA boundary cleanup update (2026-03-06): Phase-15 backlog/active
  boundary work is closed; canonical local backlog now lives at
  `dev/deferred/LOCAL_BACKLOG.md`, canonical guard remediation scaffold output
  now lives at `dev/reports/audits/RUST_AUDIT_FINDINGS.md`, and canonical
  phase-2 research now lives at `dev/deferred/phase2.md` (with bridge pointers
  retained for one migration cycle).
- MP-347 mutation-policy update (2026-03-05): `devctl check --profile release`
  now runs mutation-score in report-only mode (non-blocking warnings with
  post-release follow-up guidance when outcomes are missing/stale/below
  threshold) so strict remote CI + CodeRabbit/Ralph gates remain release
  blockers while mutation hardening stays explicitly tracked work.
- MP-346 post-waiver guardrail hardening update: compatibility-matrix checks now
  parse YAML format directly, smoke runtime-backend detection now derives from
  `BackendRegistry` constructor ownership (not module declarations), and
  isolation scanning now skips broader test-only cfg attributes such as
  `cfg(any(test, ...))` with dedicated unit coverage.
- MP-346 review-driven cleanup update: IPC prompt/wrapper preemption now emits
  consistent `JobEnd(cancelled)` events, compatibility-matrix validation now
  fails on duplicate host/provider ids, and matrix smoke now enforces full
  parsed runtime host/backend/provider sets (excluding explicit
  `BackendFamily::Other` sentinel) to prevent silent governance drift.
- MP-346 reviewer follow-up hardening update: isolation cfg-test skipping now
  excludes mixed expressions containing `not(test)` to avoid production-path
  false negatives, matrix smoke backend discovery is no longer coupled to a
  specific `BackendRegistry` vector layout, matrix validation now fails
  malformed host/provider entries missing string `id` fields, and IPC
  cancellation regression coverage now includes active-Claude wrapper and
  `/cancel` `JobEnd(cancelled)` assertions; targeted IPC + memory-guard tests
  are green in this session.
- MP-346 closure-gate stabilization update: full `devctl check --profile ci`
  rerun is green after tightening `legacy_tui::tests::memory_guard_backend_threads_drop`
  to wait for backend-thread count return-to-baseline (removing a transient
  teardown race from suite-wide execution).
- Tooling governance update: workflow shell-heavy commit-range/scope/path
  resolution now routes through `dev/scripts/workflow_bridge/shell.py`,
  `docs-check --strict-tooling` now enforces `check_workflow_shell_hygiene.py`,
  and `tooling_control_plane.yml` now runs explicit naming-consistency and
  workflow-shell hygiene checks.
- Tooling layout cleanup update (2026-03-12): root-level Python wrappers under
  `dev/scripts/` were removed after package entrypoints were migrated into
  `mutation/`, `coderabbit/`, `workflow_bridge/`, `rust_tools/`, `badges/`,
  and `artifacts/`; `devctl path-audit/path-rewrite` now enforces those moved
  script paths repo-wide, and directory READMEs now make the entrypoint/helper
  split explicit. Portability review for the same slice is also explicit:
  reusable guard/probe policy resolution is ahead of the higher-level workflow
  helpers, while Ralph, mutation, process hygiene, and some docs/router policy
  still carry VoiceTerm-specific code that remains tracked follow-up work.
- Repo-governance portability update (2026-03-12): the next portability slice
  moved `check-router` lane/risk-addon rules and `docs-check`
  user-doc/tooling-doc/evolution/deprecated-reference path policy into
  `dev/config/devctl_repo_policy.json`, with `--quality-policy` overrides on
  both commands. That keeps current VoiceTerm behavior explicit while letting
  another repo adopt the same engine by swapping repo policy instead of
  patching command code.
- MP-346 tooling closure pass update: oversized workflow/devctl helper modules
  were split into companion modules (`autonomy_workflow_bridge`, hygiene ADR
  audits), workflow-shell hygiene now scans both `.yml` + `.yaml` with
  auditable rule-level suppression comments, and release docs now align to the
  same-SHA preflight-first release-gates sequence enforced by publish lanes.
- MP-346 Rust guardrail expansion update: `rust_ci.yml` now emits clippy lint
  histogram JSON and enforces `check_clippy_high_signal.py` against
  `dev/config/clippy/high_signal_lints.json`; `devctl` AI guard + scaffolding
  docs now include `check_rust_test_shape.py` and
  `check_rust_runtime_panic_policy.py`, with unit coverage extended across
  `test_check.py`, `test_audit_scaffold.py`, and dedicated new check-script
  tests.
- MP-346 runtime-lane AI-guard range update: `rust_ci.yml`,
  `release_preflight.yml`, and `security_guard.yml` now resolve commit ranges
  through `workflow_shell_bridge.py resolve-range` and pass those refs to
  `devctl check --profile ai-guard`; `devctl check` also now sequences
  clippy-lint histogram collection before `clippy-high-signal-guard`, and
  naming-consistency parsing was split into a companion module to keep shape
  policy green. Strict clippy zero-warning status was restored after new lint
  families surfaced, and `rust/Cargo.toml` now sets `rust-version = 1.88.0`
  to match the active MSRV lane contract.
- MP-346 pending-guardrail closure update: `devctl release-gates` rendering is
  now Python-3.11-compatible, planned Clippy threshold ratchet is complete
  (`cognitive-complexity-threshold=25`, `too_many_lines=warn`), and new
  duplicate-type + structural-complexity guards are wired into AI-guard and
  audit-scaffold flows; periodic `jscpd` duplication auditing now has a
  dedicated wrapper (`check_duplication_audit.py`) for freshness/threshold
  evidence capture.
- MP-346 continuation audit update: the previously interrupted
  `devctl check --profile ci` rerun is now confirmed green end-to-end, stale
  pre-remediation evidence rows were removed from
  `ide_provider_modularization.md`, and `code_shape_policy.py` now carries an
  explicit path budget for `check_rust_lint_debt.py` so the tooling bundle
  remains non-regressive after the new guardrail wiring.
- MP-347 tooling-ops update: `devctl check --profile fast` now aliases
  `quick` for local iteration naming clarity, and `devctl check-router`
  selects docs/runtime/tooling/release lanes from changed paths with optional
  `--execute` routing of bundle commands plus risk-matrix add-ons.
- MP-347 bundle-governance update: canonical command-bundle authority now
  lives in `dev/scripts/devctl/bundle_registry.py`; `check-router` and
  `check_bundle_workflow_parity.py` now consume the registry, while AGENTS
  bundle blocks are rendered/reference-only docs.
- MP-347 bundle-render automation update: added
  `check_agents_bundle_render.py` (`--write` regen mode) and wired
  `docs-check --strict-tooling` to fail when AGENTS rendered bundle docs drift
  from canonical registry output.
- MP-347 lint-debt governance update: Rust dead-code debt is now inventoryable
  and policy-gated (`--report-dead-code`, `--fail-on-undocumented-dead-code`)
  with all current `#[allow(dead_code)]` instances documented by explicit
  `reason` metadata.
- MP-347 architecture-governance intake update (2026-03-08): post-release
  DevCtl hardening backlog now explicitly includes an
  `architecture_surface_sync` guard for changed/untracked paths plus a
  duplicate/shared-logic candidate guard so new repo surfaces fail earlier
  when they are not wired into authority docs, bundles, workflows, and
  canonical shared-helper boundaries.
- MP-346 formal closure (2026-03-05): Phase 6 governance gate closed;
  all release-scope structural/tooling/governance/testing conditions met
  for IDE-first matrix (4/4); post-release backlog (Gemini overlay,
  JetBrains+Claude render-sync, AntiGravity readiness) tracked in
  `ide_provider_modularization.md` Steps 3g/3h and Phase 5.
- Pre-release architecture audit progress (2026-03-05): Phases 1-7
  are now complete (Phase-7 added 5 new guard scripts, extended 3 existing
  guards, and added hygiene checks; 596/596 tests green).
  Phases 8-14 remain default-deferred post-release unless explicitly promoted
  by operator direction.
- Pre-release architecture audit execution kickoff (2026-03-06): Phase 16
  governance alignment is complete (single pre-release audit authority kept in
  `dev/active/pre_release_architecture_audit.md`; strict tooling
  docs/governance checks green), and the first do-now runtime remediation
  landed by replacing `main.rs` `env::set_var` usage with runtime theme/backend
  overrides; `cargo test --bin voiceterm` remains green (`1526` passed).
- Pre-release architecture audit follow-up (2026-03-06): the
  `feed_prompt_output_and_sync` structural-complexity exception was removed
  after the prompt-occlusion detection split reduced the function below the
  default guard thresholds (`score=9`, `branch_points=7`, `depth=3`).
- Pre-release architecture audit follow-up (2026-03-06): the
  `writer/state/redraw.rs::maybe_redraw_status` structural-complexity
  exception was removed after splitting redraw gating/geometry/apply/render
  helpers reduced the function below the default guard thresholds
  (`score=13`, `branch_points=2`, `depth=2`).
- Pre-release architecture audit follow-up (2026-03-06): writer-state dispatch
  now uses `writer/state/dispatch.rs` for message routing and
  `writer/state/dispatch_pty.rs` for PTY-heavy output. Temporary complexity
  exceptions for dispatch/redraw/prompt were removed after guard checks
  (`check_structural_complexity` `exceptions_defined=0`).
- Pre-release architecture audit follow-up (2026-03-06): readability cleanup
  simplified dense comment/policy wording in the writer dispatch path and
  guard policy text; targeted rustfmt alignment was applied to active Rust
  files and full `devctl check --profile ci` rerun is green.
- Pre-release architecture audit follow-up (2026-03-06): transition
  compatibility cleanup retired `audit-scaffold` legacy `dev/active/` output
  support and retired strict-tooling `dev/DEVELOPMENT.md` alias acceptance;
  `collect_git_status` now uses `git status --porcelain --untracked-files=all`
  so canonical `dev/guides/*` updates are detected without legacy fallback.

## Multi-Agent Coordination Board

This board remains the execution tracker for lane ownership/status.
`dev/active/review_channel.md` now holds the merged markdown-swarm lane plan,
instruction log, shared ledger, and signoff template. `bridge.md` is the
only live cross-team reviewer/coder coordination surface during active swarm
execution.

Branch guards for all agents:

1. Start from `develop` (never from `master`).
2. Use dedicated worktrees and dedicated feature branches per agent.
3. Rebase each active agent branch after every merge to `origin/develop`.
4. Update this board before and after each execution batch.
5. Keep `master` release-only (merge/tag/publish only).
6. Shared hotspot files (`writer/state.rs`, `prompt_occlusion.rs`,
   `claude_prompt_detect.rs`, `theme/rule_profile.rs`,
   `theme/style_pack.rs`) require an explicit claim in the merged
   `review_channel.md` swarm ledger before edits when Theme
   (`MP-148..MP-182`), naming/API cohesion (`MP-267`), and MP-346 scopes
   overlap.

| Agent | Lane | Active-doc scope | MP scope (authoritative) | Worktree | Branch | Status | Last update (UTC) | Notes |
|---|---|---|---|---|---|---|---|---|
| `AGENT-1` | Codex architecture contract review | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` | `MP-340, MP-355` | `../codex-voice-wt-a1` | `feature/a1-codex-architecture-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for controller/review/memory contract boundaries. |
| `AGENT-2` | Codex clean-code and state-boundary review | `dev/active/review_channel.md` + runtime pack | `MP-267, MP-340, MP-355` | `../codex-voice-wt-a2` | `feature/a2-codex-clean-code-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for duplication, ownership drift, and mixed-state violations. |
| `AGENT-3` | Codex runtime and handoff review | `dev/active/review_channel.md`, `dev/active/memory_studio.md` + runtime pack | `MP-233, MP-238, MP-243, MP-340, MP-355` | `../codex-voice-wt-a3` | `feature/a3-codex-runtime-handoff-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for handoff, bootstrap, memory-bridge, and runtime correctness. |
| `AGENT-4` | Codex CI and workflow reviewer | `dev/active/review_channel.md` + tooling pack | `MP-297, MP-298, MP-303, MP-306, MP-355` | `../codex-voice-wt-a4` | `feature/a4-codex-ci-workflow-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for CI/CD, bundle/workflow parity, and push-safety. |
| `AGENT-5` | Codex devctl and process-hygiene reviewer | `dev/active/devctl_reporting_upgrade.md`, `dev/active/host_process_hygiene.md` | `MP-297, MP-298, MP-300, MP-303, MP-306, MP-356` | `../codex-voice-wt-a5` | `feature/a5-codex-devctl-process-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for `devctl`, cleanup/audit flow, and maintainer-surface correctness. |
| `AGENT-6` | Codex overlay and UX reviewer | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a6` | `feature/a6-codex-overlay-ux-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for Control/Review/Handoff UX, hitboxes, redraw, and footer honesty. |
| `AGENT-7` | Codex guard and test reviewer | `dev/active/review_channel.md`, `dev/active/host_process_hygiene.md` + tooling pack | `MP-303, MP-355, MP-356` | `../codex-voice-wt-a7` | `feature/a7-codex-guard-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for guard coverage, regression tests, and audit evidence quality. |
| `AGENT-8` | Codex integration and re-review loop | `dev/active/MASTER_PLAN.md`, `dev/active/review_channel.md` | `MP-340, MP-355, MP-356` | `../codex-voice-wt-a8` | `feature/a8-codex-integration-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; primary Codex merge/readiness lane that polls every 5 minutes when Claude is still coding. |
| `AGENT-9` | Claude bridge push-safety fixes | `dev/active/review_channel.md` + tooling pack | `MP-303, MP-306, MP-355` | `../codex-voice-wt-a9` | `feature/a9-claude-bridge-push-safety` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for bridge-gate, workflow-order, and branch push-safety fixes. |
| `AGENT-10` | Claude live Git-context fixes | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a10` | `feature/a10-claude-git-context-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for session-root Git context and repo-snapshot correctness. |
| `AGENT-11` | Claude refresh, redraw, and footer fixes | `dev/active/review_channel.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a11` | `feature/a11-claude-refresh-redraw-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for Control/Handoff refresh honesty, error redraw, and footer-hitbox alignment. |
| `AGENT-12` | Claude broker and clipboard fixes | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a12` | `feature/a12-claude-broker-clipboard-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for broker shutdown cleanup/reporting and writer-routed clipboard behavior. |
| `AGENT-13` | Claude handoff and bootstrap fixes | `dev/active/review_channel.md`, `dev/active/memory_studio.md` + runtime pack | `MP-233, MP-238, MP-243, MP-340, MP-355` | `../codex-voice-wt-a13` | `feature/a13-claude-handoff-bootstrap-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for fresh-prompt bootstrap docs, handoff packet context, and memory-compatible resume paths. |
| `AGENT-14` | Claude workflow and publication-sync fixes | `dev/active/devctl_reporting_upgrade.md` + tooling pack | `MP-297, MP-298, MP-300, MP-303, MP-306` | `../codex-voice-wt-a14` | `feature/a14-claude-workflow-publication-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for publication-sync scope, workflow ordering, and tooling-gate rationalization. |
| `AGENT-15` | Claude clean-code refactors | `dev/active/naming_api_cohesion.md`, `dev/active/review_channel.md` + runtime/tooling packs | `MP-267, MP-340, MP-355` | `../codex-voice-wt-a15` | `feature/a15-claude-clean-code-refactors` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for dedup, separation-of-concerns cleanup, and mixed-state untangling that reviewers flag. |
| `AGENT-16` | Claude proof and regression closure | `dev/active/review_channel.md`, `dev/active/host_process_hygiene.md` + runtime/tooling packs | `MP-303, MP-340, MP-355, MP-356` | `../codex-voice-wt-a16` | `feature/a16-claude-proof-regression-closure` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for final guard green runs, regression proofs, and cross-lane verification closeout. |

## Strategic Direction

- Protect current moat: terminal-native PTY orchestration, prompt-aware queueing, local-first voice flow.
- Close trust gap: latency metrics must match user perception and be auditable.
- Build differentiated product value in phases:
  1. Visual-first UX pass (telemetry, motion, layout polish, theme ergonomics)
  2. Workflow differentiators (voice navigation, history, CLI workflow polish)
  3. Theme-systemization (visual surfaces first, then full Theme Studio control parity)
  4. Advanced expansion (streaming STT, tmux/neovim, accessibility)

## Unified Active-Docs Phased Map (Execution Order)

This is the cross-plan execution map so agents and developers stay aligned on
main goal and sequence across all active docs.

### Phase A - Governance + Scope Integrity

1. Keep one execution tracker (`MASTER_PLAN`) and strict active-doc sync.
2. Enforce repeat-to-automate and audit evidence as default operating mode.

Mapped scopes:

- `MP-333`, `MP-337`
- `dev/active/INDEX.md`
- `dev/active/review_channel.md`

### Phase B - Runtime and Workspace Reliability Baseline

1. Keep runtime safety/perf/teardown/wake-word hardening green.
2. Complete workspace layout migration so path contracts are stable.

Mapped scopes:

- `MP-127..MP-138`, `MP-341`, `MP-346`, `MP-354`, runtime hardening + host/provider modularization docs.

### Phase C - Tooling Control Plane + Loop Foundations

1. Keep `devctl` reporting/control-plane lane as the automation backbone.
2. Keep Ralph + mutation loops bounded, source-correlated, and policy-gated.
3. Keep external federation bridges pinned and governed.

Mapped scopes:

- `MP-297..MP-300`, `MP-303`, `MP-306`, `MP-325..MP-329`, `MP-334`
- `dev/active/devctl_reporting_upgrade.md`
- `dev/active/autonomous_control_plane.md` (Phases 1-2/5/6)

### Phase D - Theme/Visual Platform Completion

1. Finish resolver-first Theme Studio migration.
2. Keep visual parity gates strict before any GA expansion.

Mapped scopes:

- `MP-148..MP-182`
- `dev/active/theme_upgrade.md`

### Phase E - Memory + Action Studio Platform

1. Build semantic memory + retrieval + action governance without runtime regressions.
2. Promote only with quality, isolation, and compaction gates passing.

Mapped scopes:

- `MP-230..MP-255`
- `dev/active/memory_studio.md`

### Phase F - Architect Controller (Rust TUI + iPhone + Agent Relay)

1. Deliver unified controller state model consumed by Rust Dev panel and phone.
2. Deliver guarded remote controls and reviewer-agent packet relay.
3. Keep branch/CI/replay policy gates mandatory before promote/write actions.

Mapped scopes:

- `MP-330..MP-332`, `MP-336`, `MP-338`
- `MP-340`
- `dev/active/autonomous_control_plane.md` (Phase 3 + 3.5 + 3.7 + 6.1)
- `dev/active/loop_chat_bridge.md`

### Phase G - Release Hardening + Template Extraction

1. Complete rollout soak, policy hardening, and full audit loops.
2. Extract reusable template package only after governance parity is proven.

Mapped scopes:

- `autonomous_control_plane` rollout/template phases
- release/tracker governance bundles and CI lanes.

## ADR Program Backlog (Cross-Plan, Pending)

Create these ADRs in order so agents/dev do not lose architectural scope.
Accepted authorities for unified controller state contract and agent relay
packet protocol have landed (see `dev/adr/0027-*` and `dev/adr/0028-*`).

Remaining backlog:

1. `ADR-0029` Operator Action Policy Model:
   action classes, approval gates, replay/nonce rules, and deny semantics.
2. `ADR-0030` Phone Adapter Architecture:
   SSH-first, push/SMS/chat adapters, auth boundaries, and fallback strategy.
3. `ADR-0031` Rust Dev-Panel Control-Plane Boundary:
   what stays runtime-local vs control-plane-fed; non-interference guarantees.
4. `ADR-0032` Autonomous Loop Stage Machine:
   triage/plan/fix/verify/review/promote transitions and stop conditions.
5. `ADR-0033` Autonomy Metrics + Scientific Audit Method:
   KPI definitions, experiment protocol, and promotion criteria.
6. `ADR-0034` Template Extraction Contract:
   what must be standardized before reuse across repositories.

## Phase 0 - Completed Release Stabilization (v1.0.51-v1.0.52)

- [x] MP-072 Prevent HUD/timer freeze under continuous PTY output.
- [x] MP-073 Improve IDE terminal input compatibility and hidden-HUD discoverability.
- [x] MP-074 Update docs for HUD/input behavior changes and debug guidance.
- [x] MP-075 Finalize latency display semantics to avoid misleading values.
- [x] MP-076 Add latency audit logging and regression tests for displayed latency behavior.
- [x] MP-077 Run release verification (`cargo build --release --bin voiceterm`, tests, docs-check).
- [x] MP-078 Finalize release notes, bump version, tag, push, GitHub release, and Homebrew tap update.
- [x] MP-096 Expand SDLC agent governance: post-push audit loop, testing matrix by change type, CI expansion policy, and per-push docs sync requirements.
- [x] MP-099 Consolidate overlay research into a single reference source (now consolidated under `dev/active/theme_upgrade.md`) and mirror candidate execution items in this plan.

## Phase 1 - Latency Truth and Observability

- [x] MP-079 Define and document latency terms (capture, STT, post-capture processing, displayed HUD latency).
- [x] MP-080 Hide latency badge when reliable latency cannot be measured.
- [x] MP-081 Emit structured `latency_audit|...` logs for analysis.
- [x] MP-082 Add automated tests around latency calculation behavior.
- [x] MP-097 Fix busy-output HUD responsiveness and stale meter/timer artifacts (settings lag under Codex output, stale REC duration/dB after capture, clamp meter floor to stable display bounds).
- [x] MP-098 Eliminate blocking PTY input writes in the overlay event loop so queued/thinking backend output does not stall live typing responsiveness.
- [x] MP-083 Run and document baseline latency measurements with `latency_measurement` and `dev/scripts/tests/measure_latency.sh` (`dev/archive/2026-02-13-latency-baseline.md`).
- [x] MP-084 Add CI-friendly synthetic latency regression guardrails (`.github/workflows/latency_guard.yml` + `measure_latency.sh --ci-guard`).
- [x] MP-194 Normalize HUD latency severity using speech-relative STT speed (`rtf`) while preserving absolute STT delay display and audit logging fields (`speech_ms`, `rtf`) to reduce false "slow" signals on long utterances.
- [x] MP-195 Stop forwarding malformed/fragmented SGR mouse-report escape bytes into wrapped CLI input during interrupts so raw `[<...` fragments do not leak to users.
- [x] MP-196 Expand non-speech transcript sanitization for ambient-sound hallucination tags (`siren`, `engine`, `water` variants) before PTY delivery.
- [x] MP-111 Add governance hygiene automation for archive/ADR/script-doc drift (`python3 dev/scripts/devctl.py hygiene`) and codify archive/ADR lifecycle policy.
- [x] MP-122 Prevent mutation-lane timeout by sharding scheduled `cargo mutants` runs and enforcing one aggregated score across shards.

## Phase 2 - Overlay Quick Wins

- [x] MP-085 Voice macros and custom triggers (`.voiceterm/macros.yaml`).
- [x] MP-086 Runtime macros ON/OFF toggle (settings state + transcript transform gate).
- [x] MP-087 Restore baseline send-mode semantics (`auto`/`insert`) without an extra review-first gate.
- [x] MP-112 Add CI voice-mode regression lane for macros-toggle and send-mode behavior (`.github/workflows/voice_mode_guard.yml`).
- [x] MP-088 Persistent user config (`~/.config/voiceterm/config.toml`) for core preferences (landed runtime load/apply/save flow with CLI-precedence guards, explicit-flag detection for default-valued args, and status-state restore coverage for macros toggle).

## Phase 2A - Visual HUD Sprint (Current Priority)

- [x] MP-101 Add richer HUD telemetry visuals (sparkline/chart/gauge) with bounded data retention.
- [x] MP-100 Add animation transition framework for overlays and state changes (TachyonFX or equivalent).
- [x] MP-054 Optional right-panel visualization modes in minimal HUD.
- [x] MP-105 Add adaptive/contextual HUD layouts and state-driven module expansion.
- [x] MP-113 Tighten startup splash ergonomics and IDE compatibility (shorter splash duration, reliable teardown in IDE terminals, corrected startup tagline centering, and better truecolor detection for JetBrains-style terminals).
- [x] MP-114 Polish startup/theme UX in IDE terminals (remove startup top-gap, keep requested themes on 256-color terminals, and render Theme Picker neutral when current theme is `none`).
- [x] MP-115 Stabilize terminal compatibility regressions (drop startup arrow escape noise during boot, suppress Ctrl+V idle pulse dot beside `PTT`, and restore conservative ANSI fallback when truecolor is not detected).
- [x] MP-116 Fix JetBrains terminal HUD duplication by hardening scroll-region cursor restore semantics.
- [x] MP-117 Prevent one-column HUD wrap in JetBrains terminals (status-banner width guard + row truncation safety).
- [x] MP-118 Harden cross-terminal HUD rendering and PTY teardown paths (universal one-column HUD safety margin, writer-side row clipping to terminal width, and benign PTY-exit write error suppression on shutdown).
- [x] MP-119 Restore the stable `v1.0.53` writer/render baseline for Full HUD while retaining the one-column layout safety margin to recover reliable IDE terminal rendering.
- [x] MP-120 Revert unstable post-release scroll-region protection changes that reintroduced severe Full HUD duplication/corruption during active Codex output.
- [x] MP-121 Harden JetBrains startup/render handoff by auto-skipping splash in IDE terminals and clearing stale HUD/overlay rows on resize before redraw.
- [x] MP-123 Harden PTY/IPC backend teardown to signal process groups and reap child processes, with regression tests that verify descendant cleanup.
- [x] MP-183 Add a PTY session-lease guard that reaps backend process groups from dead VoiceTerm owners before spawning new sessions, without disrupting concurrently active sessions.
- [x] MP-190 Restore Full HUD shortcuts-row trailing visualization alignment so the right panel remains anchored to the far-right corner in full-width layouts.
- [x] MP-124 Add Full-HUD border-style customization (including borderless mode) and keep right-panel telemetry explicitly user-toggleable to `Off`.
- [x] MP-125 Fix HUD right-panel `Anim only` behavior so idle state keeps a static panel visible instead of hiding the panel until recording.
- [x] MP-126 Complete product/distribution naming rebrand to VoiceTerm across code/docs/scripts/app launcher, and add a PyPI launcher package scaffold (`pypi/`) for `voiceterm`.
- [x] MP-139 Tighten user-facing docs information architecture (entrypoint clarity, navigation consistency, and guide discoverability).
- [x] MP-104 Add explicit voice-state visualization (idle/listening/processing/responding) with clear transitions.
- [x] MP-055 Quick theme switcher in settings.
- [x] MP-102 Add toast notification center with auto-dismiss, severity, and history review (landed runtime status-to-toast ingestion with severity mapping, `Ctrl+N` notification-history overlay toggle, periodic auto-dismiss/re-render behavior, and input/parser/help/docs coverage for toast-history control flow).
- [x] MP-226 Fix Claude-mode command/approval prompt occlusion in active overlay sessions: when Claude enters interactive Bash approval or sandbox permission prompts (for example `Do you want to proceed?` while running `Bash(...)` or cross-worktree read prompts), VoiceTerm HUD/overlay rows can obscure prompt text and controls; implement a Claude-specific prompt-state rendering policy (overlay layering, temporary HUD suppression/resume, or reserved prompt-safe rows) so prompts remain readable/actionable without losing runtime status clarity, with non-regression validation for Codex, Cursor, and JetBrains terminals. (2026-02-27 follow-up hardening: suppression now targets high-confidence interactive approval/permission contexts only; low-confidence generic/composer text no longer triggers HUD suppression to avoid disappear/reappear flicker during normal Codex runs. Additional 2026-02-27 resilience update: terminal row/col resolution now normalizes zero-size IDE probes and writer startup redraw uses normalized size fallback so HUD resume/startup does not wait for a keypress. 2026-02-28 targeted overlay follow-up: numbered approval-card detection now suppresses HUD for sparse `1/2/3` option cards, suppression transitions synchronize normalized geometry with writer redraw, and Cursor transition pre-clear now scrubs stale border fragments during `ClearStatus` handoff paths. 2026-02-28 anti-cycle follow-up: Cursor non-rolling hosts no longer engage suppression from tool-activity text alone, and now use explicit/numbered approval-card hints for suppression engagement to prevent keypress-triggered HUD disappearance in normal composer flow.)
  - Repro note (2026-02-19): issue severity appears higher for local/worktree permission prompts during multi-tool explore batches (`+N more tool uses`), while some single-command Claude prompt flows appear acceptable.
  - Additional repro signal (2026-02-19): severity appears correlated with vertical UI density (long wrapped absolute command paths, larger active task list sections, and multi-line tool-batch summaries), suggesting row-budget/stacking pressure near bottom prompt rows.
  - Repro note (2026-02-19, screenshot evidence): during parallel/background-agent orchestration in Claude, long "workaround options" + permission-wall text can exceed available row budget and push prompt/action rows into unreadable overlap, while equivalent Codex sessions remain readable; treat this as a Claude-specific layout compaction/reserved-row failure case.
  - Evidence to capture per repro: terminal rows/cols, HUD mode/style, prompt type (single-command approval vs local/worktree permission), command preview line-wrap count, tool-batch summary presence (`+N more tool uses`), and screenshot before/after prompt render.
  - 2026-02-28 diagnostic follow-up: added gated Claude HUD tracing (`VOICETERM_DEBUG_CLAUDE_HUD=1`) across prompt-occlusion transitions and writer redraw/defer decisions to isolate a new Cursor+Claude normal-typing regression where HUD disappears after the first keypress (non-approval flow).
  - 2026-02-28 writer follow-up: tightened tool-activity suppression overmatch for plain transcript headings, added explicit stale-banner-anchor clearing in writer redraw, and added a short delayed Cursor+Claude typing repair redraw path to recover minimal-HUD line clobber without reintroducing per-keystroke flash.
  - 2026-02-28 minimal-HUD follow-up: Cursor+Claude typing-hold deferral now bypasses for active one-row HUD frames so minimal-HUD redraw is not postponed behind typing bursts, while full-HUD deferral policy remains unchanged.
  - 2026-02-28 traceability follow-up: Cursor+Claude writer debug logs now emit explicit user-input activity scheduling and enhanced-status render decisions (`prev/next banner height`, `hud_style`, `prompt_suppressed`), and pre/post transition flags are now computed from pre-apply state to prevent false-no-change traces while reproducing the remaining disappearance/overwrite regressions.
  - 2026-02-28 repaint follow-up: pre-clear transition redraws now force full banner repaint (no previous-line diff reuse) in Cursor+Claude paths, with explicit `transition redraw mode` debug traces to prove redraw mode on failing keypress/tool-output sequences.
  - 2026-02-28 non-rolling approval-window follow-up: Cursor non-rolling prompt suppression now keeps a short ANSI-stripped rolling approval window so split approval cards (`Do you want to proceed?` + later `1/2/...` options) still suppress HUD deterministically, while debug traces now log chunk/window match sources (`chunk_*` vs `window_*`) to distinguish real prompt hits from missed detections. Writer repair scheduling was also hardened so future Cursor+Claude repair deadlines are not cleared by unrelated redraws before they fire, reducing one-row HUD “disappear until refresh” loops during typing.
  - 2026-02-28 non-rolling release-gate + row-budget tracing follow-up: Cursor non-rolling suppression now requires explicit input-resolution arming plus drained approval window before release (prevents debounce-only unsuppress while approval context remains live), prompt-context fallback markers now keep detection active when backend label routing is noisy (`Tool use`, `Claude wants to`, `What should Claude do instead?`), Cursor Claude extra gap rows increased (`8 -> 10`), and `apply_pty_winsize` debug traces now emit backend/mode/rows/cols/reserved-rows/PTY-rows so overlay overlap can be diagnosed from logs instead of screenshots alone.
  - 2026-02-28 high-confidence guard follow-up: explicit/numbered approval hints now promote `prompt_guard_enabled` in non-rolling paths, so approval cards can suppress HUD even when backend-label guard signals are noisy; runtime debug chunk logs now include `backend_label` + `prompt_guard` booleans for direct branch tracing; non-rolling suppression semantics are now covered by deterministic thread-local test overrides (no shared env mutation races under parallel test execution).
  - 2026-03-01 stress-loop traceability follow-up: added deterministic Cursor+Claude stress artifact capture under `dev/reports/audits/claude_hud_stress/*` (frame snapshots + log counters + anomaly summaries), narrowed non-rolling release-arm consumption to substantial post-input activity, deferred release-arm relatch on window-only stale hints, and hardened writer typing-hold urgency detection for post-`ClearStatus` suppression transitions so approval/HUD churn can be diagnosed via logs and artifact IDs instead of screenshot-only loops. Current status remains partial (approval overlap reduced but not eliminated; see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.10).
  - 2026-03-01 rapid-approval hold + frame/log correlation follow-up: non-rolling input-resolution now arms an explicit sticky suppression hold window to avoid unsuppress gaps between consecutive approval cards, and `claude_hud_stress.py` now records frame timestamps plus bottom-row HUD visibility and correlates each frame to suppression-transition/redraw-commit log events for deterministic overlap attribution (see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.11). Local stress execution in this sandbox remains blocked by detached `screen` session startup failure, so fresh artifact generation is still pending a full terminal host.
  - 2026-03-01 wrapped-approval depth + anomaly-capture follow-up: expanded non-rolling approval scan depth (`2048 -> 8192` bytes, `12 -> 64` lines) so long wrapped option cards in Cursor prompt UIs continue matching numbered approval semantics, and added explicit anomaly logging for `explicit approval hint seen without numbered-match` to surface residual detector misses in runtime logs instead of relying on screenshots alone (see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.12).
  - 2026-03-01 overlay occlusion closure follow-up: PTY startup winsize is now derived from measured terminal geometry before backend spawn (HUD-aware from frame 1), writer HUD rendering now fences PTY scrolling above reserved HUD rows via scroll-region controls, and resize transitions now force immediate redraw after pre-clear so grow/shrink cycles do not leave input rows hidden until another keypress.
  - 2026-03-01 JetBrains+Claude rendering follow-up: status/banner clear-to-EOL paths now reset ANSI attributes before trimming trailing columns so dark HUD style attributes cannot leak into typed prompt text, and JetBrains Claude extra gap rows now default to `2` for safer startup prompt/HUD separation.
  - 2026-03-01 post-v1.0.98 typing follow-up: JetBrains+Claude writer pre-clear now defers while user input is fresh (typing-hold window) so startup typing bursts do not destructively clear half-HUD rows before idle redraw can restore them.
- [x] MP-285 Standardize HUD policy across all backends: removed Gemini-specific compaction logic to ensure a consistent 4-row Full HUD experience and unified flicker-reduction behavior across Codex, Claude, and Gemini backends.

## Phase 2B - Rust Hardening Audit (Pre-Execution + Implementation)

- [x] MP-127 Replace IPC `/exit` hard process termination with graceful shutdown orchestration and teardown event guarantees (FX-001).
- [x] MP-128 Add explicit runtime ownership and bounded shutdown/join semantics for overlay writer/input threads (FX-002).
- [x] MP-129 Add voice-manager lifecycle hardening for quit-while-recording paths, including explicit stop/join policy and tests (FX-003).
- [x] MP-130 Consolidate process-group signaling/reaping helpers into one canonical utility with invariants tests (FX-004).
- [x] MP-131 Add security/supply-chain CI lane with policy thresholds and failing gates for high-severity issues (FX-005).
- [x] MP-132 Add explicit security posture/threat-model documentation and risky flag guidance (including permission-skip behavior) (FX-006).
- [x] MP-133 Enforce IPC auth timeout + cancellation semantics using tracked auth start timing (FX-007).
- [x] MP-134 Replace IPC fixed-sleep scheduling with event-driven receive strategy to reduce idle CPU jitter (FX-008).
- [x] MP-135 Decompose high-risk event-loop transition/wiring complexity to reduce change blast radius (FX-009).
- [x] MP-136 Establish unsafe-governance checklist for unsafe hotspots with per-invariant test expectations (FX-010).
- [x] MP-137 Add property/fuzz coverage lane for parser and ANSI/OSC boundary handling (FX-011).
- [x] MP-138 Enforce audit/master-plan traceability updates as a mandatory part of each hardening fix (FX-012).
- [x] MP-152 Consolidate hardening governance to `MASTER_PLAN` as the only active tracker: archive `RUST_GUI_AUDIT_2026-02-15.md` under `dev/archive/` and retire dedicated audit-traceability CI/tooling.

## Phase 2C - Theme System Upgrade (Architecture + Guardrails)

Theme Studio execution gate: MP-148..MP-182 are governed by the checklist in
this section. A Theme Studio MP may move to `[x]` only with documented pass
evidence for its mapped gates.

Theme/modularization integration rule: when refactors or fixes touch visual
runtime modules (`theme/*`, `theme_ops.rs`, `theme_picker.rs`, `status_line/*`,
`hud/*`, `writer/*`, `help.rs`, `banner.rs`), update or add the
corresponding `MP-148+` item here in `MASTER_PLAN` and attach mapped
`TS-G*` gate evidence from this section.

Settings-vs-Studio ownership matrix:

| Surface | Owner |
|---|---|
| Theme tokens/palettes, borders, glyph/icon packs, layout/motion behavior, visual state scenes, notification visuals, command-palette/autocomplete visuals | Theme Studio |
| Auto-voice/send-mode/macros, sensitivity/latency display mode, mouse mode, backend/pipeline, close/quit operations | Settings |
| Quick theme cycle and picker shortcuts | Shared entrypoint; deep editing still routes to Theme Studio |

Theme Studio Definition of Done (authoritative checklist):

| Gate | Pass Criteria | Fail Criteria | Required Evidence |
|---|---|---|---|
| `TS-G01 Ownership` | Theme Studio vs Settings ownership matrix is implemented and documented. | Any deep visual edit path remains in Settings post-migration. | Settings menu tests + docs diff. |
| `TS-G02 Schema` | `StylePack` schema/version/migration tests pass for valid + invalid inputs. | Parsing/migration panic, silent drop, or invalid pack applies without fallback. | Unit tests for parse/validate/migrate + fallback tests. |
| `TS-G03 Resolver` | All render paths resolve styles through registry/resolver APIs. | Hardcoded style constants bypass resolver on supported surfaces. | Coverage + static policy gate outputs. |
| `TS-G04 Component IDs` | Every renderable component/state has stable style IDs and defaults. | Unregistered component/state renders in runtime. | Component registry parity tests + snapshots. |
| `TS-G05 Studio Controls` | Every persisted style field is editable in Studio. | Any persisted field has no Studio control mapping. | Studio mapping parity test results. |
| `TS-G06 Snapshot Matrix` | Snapshot suites pass for widths, states, profiles, and key surfaces. | Layout overlap/wrap/clipping regressions vs expected fixtures. | Snapshot artifacts for narrow/medium/wide + state variants. |
| `TS-G07 Interaction UX` | Keyboard-only and mouse-enhanced flows both work with correct focus/hitboxes. | Broken focus order, unreachable controls, or hitbox mismatch. | Interaction integration tests + manual QA checklist output. |
| `TS-G08 Edit Safety` | Apply/save/import/export/undo/redo/rollback flows are deterministic. | User edits can be lost/corrupted or cannot be reverted safely. | End-to-end workflow tests across restart boundaries. |
| `TS-G09 Capability Fallback` | Terminal capability detection + fallback chains behave as specified. | Unsupported capability path crashes or renders unreadable output. | Compatibility matrix tests (truecolor/ansi, graphics/no-graphics). |
| `TS-G10 Runtime Budget` | Render/update paths remain within bounded allocation/tick budgets. | Unbounded buffers, allocation spikes, or frame-thrash in hot paths. | Perf/memory checks + regression benchmarks. |
| `TS-G11 Docs/Operator` | Architecture, usage, troubleshooting, and changelog are updated together. | User-visible behavior changes without aligned docs. | `docs-check` + updated docs references. |
| `TS-G12 Release Readiness` | Full Theme Studio GA validation bundle is green. | Any mandatory gate is missing evidence or failing. | CI report bundle + signoff checklist. |
| `TS-G13 Inspector` | Any rendered element can reveal style path and jump to Studio control. | Inspector cannot locate style ID/path for a rendered element. | Inspector integration tests + state preview tests. |
| `TS-G14 Rule Engine` | Conditional style rules are deterministic and conflict-resolved. | Rule priority conflicts or nondeterministic style outcomes. | Rule engine unit/property tests + scenario snapshots. |
| `TS-G15 Ecosystem Packs` | Third-party widget packs are allowlisted, version-compatible, and parity-mapped. | Dependency added without compatibility matrix or style/studio parity mapping. | Compatibility matrix + parity tests + allowlist audit. |

Theme Studio MP-to-gate mapping:

| MP | Required Gates |
|---|---|
| `MP-148` | `TS-G01`, `TS-G11` |
| `MP-149` | `TS-G02`, `TS-G06`, `TS-G09` |
| `MP-150` | `TS-G02`, `TS-G03` |
| `MP-151` | `TS-G11` |
| `MP-161` | `TS-G03`, `TS-G06`, `TS-G07` |
| `MP-162` | `TS-G03`, `TS-G05` |
| `MP-163` | `TS-G03` |
| `MP-172` | `TS-G04`, `TS-G06` |
| `MP-174` | `TS-G03`, `TS-G05`, `TS-G06` |
| `MP-175` | `TS-G09`, `TS-G15` |
| `MP-176` | `TS-G09`, `TS-G06` |
| `MP-179` | `TS-G15` |
| `MP-180` | `TS-G15`, `TS-G05`, `TS-G06` |
| `MP-182` | `TS-G14`, `TS-G05`, `TS-G06` |
| `MP-164` | `TS-G07` |
| `MP-165` | `TS-G01`, `TS-G07` |
| `MP-166` | `TS-G05`, `TS-G08`, `TS-G07` |
| `MP-167` | `TS-G06`, `TS-G09`, `TS-G10`, `TS-G11`, `TS-G12` |
| `MP-173` | `TS-G03`, `TS-G05`, `TS-G15` |
| `MP-177` | `TS-G15`, `TS-G05` |
| `MP-178` | `TS-G13`, `TS-G07` |
| `MP-181` | `TS-G07`, `TS-G10` |

Theme Studio mandatory verification bundle (per PR):

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py docs-check --user-facing`
- `python3 dev/scripts/devctl.py hygiene`
- `cd rust && cargo test --bin voiceterm`
- use `.github/PULL_REQUEST_TEMPLATE/theme_studio.md` for `TS-G01`..`TS-G15` evidence capture.

- [x] MP-148 Activate the Theme Studio phased track in `MASTER_PLAN` and lock the IA boundary: dedicated `Theme Studio` mode (not `Settings -> Studio`) plus Settings-vs-Studio ownership matrix (landed gate catalog + MP-to-gate map + ownership matrix directly in Phase 2C so visual modularization/fix work now maps to one canonical tracker).
- [x] MP-149 Implement Theme Upgrade Phase 0 safety rails (golden render snapshots, terminal compatibility matrix coverage, and style-schema migration harness) before any user-visible editor expansion (landed style-schema migration harness in `theme/style_schema.rs`, terminal capability matrix tests in `color_mode`, and golden snapshot-matrix coverage for startup banner, theme picker, and status banner render outputs).
- [x] MP-150 Implement Theme Upgrade Phase 1 style engine foundation (`StylePack` schema + resolver + runtime), preserving current built-in theme behavior and startup defaults (landed runtime resolver scaffold `theme/style_pack.rs`, routed `Theme::colors()` through resolver with palette-parity regression tests, enabled runtime schema parsing/migration (`theme/style_schema.rs`) for pack payload ingestion, and hardened schema-version mismatch/invalid-payload fallback to preserve base-theme palettes instead of dropping to `none`).
- [x] MP-151 Ship docs/architecture updates for the new theme system (`dev/ARCHITECTURE.md`, `guides/USAGE.md`, `guides/TROUBLESHOOTING.md`, `dev/CHANGELOG.md`) in lockstep with implementation, including operator guidance, settings-migration guidance, and fallback behavior (landed runtime resolver path docs, schema payload operator guidance, explicit settings-migration notes, and invalid-pack fallback behavior across architecture/usage/troubleshooting/changelog docs).

## Phase 2D - Visual Surface Expansion (Theme Studio Prerequisite)

- [ ] MP-161 Execute a visual-first runtime pass before deep Studio editing: with MP-102 complete, promote MP-103, MP-106, MP-107, MP-108, and MP-109 from Backlog into active execution order with non-regression gates (in progress: toast-history overlay row-width accounting and title rendering were hardened so unicode/ascii glyph themes keep border alignment without stale right-edge artifacts).
- [ ] MP-162 Extend `StylePack` schema/resolver so each runtime visual surface is style-pack addressable (widgets/graphs, toasts, voice-state scenes, command palette, autocomplete, dashboard surfaces), even before all Studio pages ship (in progress: schema/resolver now supports runtime visual overrides for border glyph sets, indicator glyph families, and glyph-set profile selection (`glyphs`: `unicode`/`ascii`) via style-pack payloads, including compact/full/minimal/hidden processing/responding indicator lanes in status rendering while preserving default processing spinner animation unless explicitly overridden; 2026-03-07 aligned next slice: persisted payload-driven runtime routing must close `surfaces.toast_position`, `surfaces.startup_style`, `components.toast_severity_mode`, and `components.banner_style`, not just runtime-only Theme Studio overrides. 2026-03-09 Codex re-review: the status-line ASCII separator leak is closed, but persisted payload-driven consumer proof is still incomplete for those startup/toast/banner fields; keep MP-162 open until consumer-level coverage lands, not just resolver wiring.)
- [x] MP-163 Add explicit coverage tests/gates that fail if new visual runtime surfaces bypass theme resolver paths with hardcoded style constants (landed `theme::tests::runtime_sources_do_not_bypass_theme_resolver_with_palette_constants`, a source-policy gate that scans runtime Rust modules and fails when `THEME_*` palette or `BORDER_*` border constants are referenced outside theme resolver/style-ownership allowlist files).
- [ ] MP-172 Add a styleable component registry and state-matrix contract for all renderable control surfaces (buttons, tabs, lists, tables, trees, scrollbars, modal/popup/tooltip, input/caret/selection) with schema + resolver + snapshot coverage (2026-03-07 alignment note: `theme::component_registry` is still gated by `theme_studio_v2`; the next slice must make that boundary explicit and separate live vs planned registry inventory before registry-backed Studio or CI parity becomes authoritative).
- [ ] MP-174 Migrate existing non-HUD visual surfaces into `StylePack` routing (startup splash/banner, help/settings/theme-picker chrome, calibration/mic-meter visuals, progress bars/spinners, icon/glyph sets) so no current visual path is left outside Theme Studio ownership (in progress: processing/progress spinner rendering paths now resolve through theme/style-pack indicators instead of hardcoded frame constants, glyph-family routing now drives HUD queue/latency/meter symbols + status-line waveform placeholders/pulse dots + progress bar/block/bounce glyphs, `components.progress_bar_family` now routes progress/meter glyph profiles through style-pack resolution, audio-meter calibration/waveform rendering resolves bar/wave/marker glyphs from the shared theme profile, overlay chrome/footer/slider glyphs across help/settings/theme-picker now route through the active glyph profile with footer close hit-testing parity for unicode/ascii separators, startup banner/footer separators now honor glyph-set overrides (`unicode`/`ascii`) across full/compact/minimal banner variants, explicit spinner-style overrides now fall back to ASCII-safe animation frames when glyph profile is ASCII, theme-switch interactions now surface explicit style-pack lock state (read-only/dimmed picker + locked status messaging) when schema payload `base_theme` is active, component-level border routing now resolves `components.overlay_border` across overlay surfaces including transcript-history plus `components.hud_border` for Full-HUD `Theme` border mode through style-pack resolver paths, and 2026-03-09 follow-up hardening routed the remaining status-line full/single-line/compact separators through glyph-aware helpers so ASCII packs stop leaking `│` / `·`; the remaining helper-routing follow-up is now toast severity icons, HUD mode glyphs, and audio-meter markers before introducing additional style-pack fields; post-slice cleanup landed: glyph tables/resolver helpers plus their focused tests extracted from `theme/mod.rs` into `theme/glyphs.rs`. 2026-03-09 Codex re-review confirmed the separator fix but keeps MP-174 open until the remaining helper-routing follow-up lands with focused proof.)
- [x] MP-175 Add a framework capability matrix + parity gate for shipped framework versions (Ratatui widget/symbol families and Crossterm color/input/render capabilities, including synchronized updates + keyboard enhancement flags), and track upgrade deltas before enabling new Studio controls (landed `theme/capability_matrix.rs` with `RatatuiWidget`/`RatatuiSymbolFamily`/`CrosstermCapability` enums, `FrameworkCapabilitySnapshot` pinned at ratatui 0.30 + crossterm 0.29, `check_parity()` gate detecting unregistered widgets and unmapped symbols, `compute_upgrade_delta()` for version transition tracking, `theme_capability_compatible()` for theme/terminal validation, and 18 passing tests covering snapshot parity, delta detection, and breaking-change gates; TS-G09 + TS-G15 evidence).
- [x] MP-176 Implement terminal texture/graphics capability track (`TextureProfile` + adapter policy): symbol-texture baseline for all terminals plus capability-gated Kitty/iTerm2 image paths with enforced fallback chain tests (landed `theme/texture_profile.rs` with `TextureTier` fallback chain (KittyGraphics > ITermInlineImage > Sixel > SymbolTexture > Plain), `SymbolTextureFamily` enum (shade/braille/block/line), `TextureProfile` with max/active tier + terminal detection, `TerminalId` enum covering Kitty/iTerm2/WezTerm/Foot/Mintty/VsCode/Cursor/JetBrains/Alacritty/Warp/Generic/Unknown, environment-based detection via TERM_PROGRAM/TERMINAL_EMULATOR/KITTY_WINDOW_ID/ITERM_SESSION_ID, `resolve_texture_tier()` enforcing fallback chain, and `texture_profile_with_override()` for style-pack tier overrides; 20 passing tests covering fallback ordering, tier resolution, terminal detection, and profile construction; TS-G09 + TS-G06 evidence).
- [x] MP-179 Add dependency baseline strategy for Theme Studio ecosystem packs (Ratatui/Crossterm version pin policy + compatibility matrix + staged upgrade plan) so third-party widget adoption does not fragment resolver/studio parity (landed `theme/dependency_baseline.rs` with `DependencyPin` structs for ratatui 0.30 and crossterm 0.29, `CompatibilityEntry`/`CompatibilityStatus` matrix covering tui-textarea/tui-tree-widget/throbber-widgets-tui/tui-popup/tui-scrollview/tui-big-text/tui-prompts/ratatui-image/tuirealm with per-dep ratatui+crossterm compat status, `UpgradeStep` staged plan (crossterm 0.30 before ratatui 0.31), `check_crate_compatibility()`/`check_pack_compatibility()` policy gates blocking unknown/incompatible crates, and `validate_pin_against_cargo()` for CI pin verification; 19 passing tests covering pin validation, matrix queries, compatibility semantics, and upgrade ordering; TS-G15 evidence).
- [x] MP-180 Pilot a curated widget-pack integration lane (`tui-widgets` family, `tui-textarea`, `tui-tree-widget`, `throbber-widgets-tui`) under style-ID/allowlist gates, with parity tests before feature flags graduate (landed `theme/widget_pack.rs` with `PackMaturity` lifecycle (Candidate > Pilot > Graduated > Retired), `WidgetPackEntry` registry with per-pack `StyleIdScope` namespaces and `ParityRequirement` gates, 6-entry `WIDGET_PACK_REGISTRY` (tui-textarea/tui-tree-widget/throbber-widgets-tui at Pilot; tui-popup/tui-scrollview/tui-big-text at Candidate), `GraduationCheckResult`-based gate blocking pilot packs with unmet parity requirements, `find_pack()`/`active_packs()`/`packs_at_maturity()` queries, `style_id_is_pack_owned()`/`owning_pack_for_style_id()` ownership resolution, and scope overlap detection; 21 passing tests covering registry integrity, scope isolation, maturity ordering, graduation gates, and ownership queries; TS-G15 + TS-G05 + TS-G06 evidence).
- [x] MP-182 Add `RuleProfile` no-code visual automation (threshold/context/state-driven style overrides) with deterministic priority semantics, preview tooling, and snapshot coverage (landed `theme/rule_profile.rs` with `RuleCondition` tagged-union supporting VoiceState/Threshold/Backend/Capability/ColorMode/All/Any conditions, `ThresholdMetric` enum (queue-depth/latency-ms/audio-level-db/terminal-width/terminal-height), `StyleOverride`/`OverrideEntry` for property-level style mutations, `StyleRule` with priority-based conflict resolution and enable/disable toggle, `RuleProfile` with add/remove/toggle operations and `active_rules()` priority-sorted accessor, `evaluate_condition()`/`evaluate_rules()` engine with deterministic first-match-per-key semantics, `preview_rules()` for Studio preview tooling, `parse_rule_profile()` JSON deserialization with nested condition support, and `RuleProfileError` for duplicate/not-found rule operations; 33 passing tests covering condition evaluation, priority semantics, conflict resolution, nested conditions, JSON parsing, and preview output; TS-G14 + TS-G05 + TS-G06 evidence).

## Phase 2E - Theme Studio Delivery (After Visual Surface Expansion)

- [x] MP-164 Implement dedicated `Theme Studio` overlay mode entry points/navigation and remove deep theme editing from generic Settings flows (landed `OverlayMode::ThemeStudio` with dedicated renderer/state selection, routed `Ctrl+Y`/theme-button entrypoints and cross-overlay theme hotkey flows into Theme Studio, added keyboard/mouse navigation (`Enter` action routing to Theme Picker/close plus arrow/ESC handling), wired periodic resize rerender + PTY reserved-row budgeting for Theme Studio mode, and covered interaction/status-row updates with new event-loop/theme-studio/status-line regression tests; TS-G07 evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-165 Migrate legacy visual controls out of settings list (`SettingsItem::Theme`, `SettingsItem::HudStyle`, `SettingsItem::HudBorders`, `SettingsItem::HudPanel`, `SettingsItem::HudAnimate`) so Settings keeps non-theme runtime controls only (landed by removing those rows from `SETTINGS_ITEMS`, preserving quick visual controls via `Ctrl+Y`/`Ctrl+G` theme paths plus `Ctrl+U` HUD-style cycling outside Settings).
- [ ] MP-166 Deliver Studio page control parity for all `StylePack` fields (tokens, layout, widgets, motion, behavior, notifications, command/discovery surfaces, voice-state scenes, startup/wizard/progress/texture surfaces, accessibility, keybinds, profiles) with undo/redo + rollback (in progress: Theme Studio now includes interactive visual-control rows for existing runtime styling (`HUD style`, `HUD borders`, `Right panel`, `Panel animation`) plus live `StylePack` runtime overrides for `Glyph profile`, `Indicator set`, `Progress spinner`, `Progress bars`, `Theme borders`, `Voice scene`, `Toast position`, `Startup splash`, `Toast severity`, and `Banner style`, all adjustable with Enter and Left/Right controls and live current-value labels; overlay rendering now uses settings-style `label + [ value ]` rows with selected-row highlighting, a dedicated `tip:` description row, wider studio-width clamps (`60..=82`), and footer hints that expose left/right adjustment controls; runtime style-pack override edit safety is now wired with dedicated `Undo edit`, `Redo edit`, and `Rollback edits` rows backed by bounded in-session history; Theme Studio input dispatch now routes through page-scoped helper handlers with shared global-key processing and focused runtime-style adjustment routing in `theme_studio_input.rs`, and home-page row rendering now uses structured row metadata with static tip ownership; 2026-03-09 bounded Components-page slice landed: `components_page.rs` now drills down `group -> component -> state` over canonical `style_id` rows, cycles local preview property edits through `StyleResolver`-owned `ResolvedComponentStyle`, and stays scoped away from `theme_studio_input.rs` / `component_registry.rs`; deep multi-page style-pack parity (`tokens`, `layout/motion`, broader field mapping), live reachability/persistence wiring, and `dead_code` allowance removal remain pending; 2026-03-07 aligned next slice: Components page work must edit `ResolvedComponentStyle` keyed by `(style_id, state)` and must not introduce per-component `ThemeColors` maps).
- [ ] MP-167 Run Theme Studio GA validation and docs lockstep updates (snapshot matrix, terminal compatibility matrix, architecture docs, user docs, troubleshooting guidance, changelog entry).
- [ ] MP-173 Add CI policy gates for future visuals: fail if a new renderable component lacks style-ID registration, and fail if post-parity a style-pack field lacks Studio control mapping (in progress: framework capability parity now fails on any newly added Ratatui widget/symbol without registration/mapping coverage, component-registry tests now require exact inventory parity plus unique stable style IDs, and Theme Studio now enforces explicit style-pack field classification (`mapped` vs `deferred`) with the post-parity gate enabled (`STYLE_PACK_STUDIO_PARITY_COMPLETE = true`) so mapping tests now require zero deferred style-pack fields; 2026-03-07 aligned next slice: registry-backed CI gates must count live renderable components only after the MP-172 live/planned boundary is explicit).
- [ ] MP-177 Add widget-pack extensibility parity (first-party plus allowlisted third-party widgets) so newly adopted widget families must register style IDs + resolver bindings + Studio controls before GA.
- [ ] MP-178 Add Theme Studio element inspector parity so users can select any rendered element and jump directly to component/state style controls (with state preview and style-path tracing).
- [ ] MP-181 Add advanced Studio interaction parity (resizable splits, drag/reorder, scrollview-heavy forms, large text/editor fields) with full keyboard fallback and capability-safe mouse behavior.

## Phase 3 - Overlay Differentiators

- [x] MP-090 Voice terminal navigation actions (scroll/copy/error/explain).
- [x] MP-140 Define and enforce macro-vs-navigation precedence (macros first, explicit built-in phrase escape path).
- [x] MP-141 Add Linux clipboard fallback support for voice `copy last error` (wl-copy/xclip/xsel).
- [x] MP-142 Add `devctl docs-check` commit-range mode for post-commit doc audits on clean working trees.
- [x] MP-156 Add release-notes automation (`generate-release-notes.sh`, `devctl release-notes`, `release.sh` notes-file handoff) so each tag has consistent diff-derived markdown notes for GitHub releases.
- [x] MP-144 Add macro-pack onboarding wizard hardening (expanded developer command packs, repo-aware placeholder templating, and optional post-install setup prompt).
- [x] MP-143 Decompose `voice_control/drain.rs` and `event_loop.rs` into smaller modules to reduce review and regression risk (adjacent runtime architecture debt; tracked separately from tooling-control-plane work).
  - [x] MP-143a Extract shared settings-item action dispatch in `event_loop.rs` so Enter/Left/Right settings paths stop duplicating mutation logic.
  - [x] MP-143b Split `event_loop.rs` overlay/input/output handlers into focused modules (`overlay_dispatch`, `input_dispatch`, `output_dispatch`, `periodic_tasks`) and move tests to `event_loop/tests.rs` while preserving regression coverage.
  - [x] MP-143c0 Move `voice_control/drain.rs` tests into `voice_control/drain/tests.rs` so runtime decomposition can land in smaller, reviewable slices.
  - [x] MP-143c1 Extract `voice_control/drain/message_processing.rs` for macro expansion, status message handling, and latency/preview helpers.
  - [x] MP-143c Split `voice_control/drain.rs` into transcript-delivery (`transcript_delivery.rs`), status/latency updates (`message_processing.rs`), and auto-rearm/finalize components (`auto_rearm.rs`) with unchanged behavior coverage.
- [x] MP-182 Decompose `ipc/session.rs` by extracting non-blocking codex/claude/voice/auth event processors into `ipc/session/event_processing/`, keeping command-loop orchestration in `session.rs` and preserving IPC regression coverage.
- [x] MP-170 Harden IPC test event capture isolation so parallel test runs remain deterministic under `cargo test` and `devctl check --profile ci`.
- [x] MP-091 Searchable transcript history and replay workflow (landed `Ctrl+H` overlay with bounded history storage, type-to-filter search, and replay-to-PTY integration plus event-loop/help wiring).
- [x] MP-229 Upgrade transcript-history from transcript-only snippets to source-aware conversation memory capture (`mic`/`you`/`ai`) with wider rows, selected-entry preview, control-sequence-safe search input (`\x1b[0[I`/focus noise no longer leaks into query text), non-replayable guardrails for assistant-output rows, and opt-in markdown session memory logging (`--session-memory`, `--session-memory-path`) for project-local conversation archives.
- [x] MP-199 Add wake-word runtime controls in settings/config (`OFF`/`ON`, sensitivity, cooldown), defaulting to `OFF` for release safety (landed overlay config flags `--wake-word`, `--wake-word-sensitivity`, `--wake-word-cooldown-ms`; settings overlay items + action handlers for wake toggle/sensitivity/cooldown; regression coverage in `settings_handlers::tests`).
- [x] MP-200 Add low-power always-listening wake detector runtime with explicit start/stop ownership and bounded shutdown/join semantics (landed `wake_word` runtime owner with local detector thread lifecycle, settings-driven start/stop reconciliation, bounded join timeout on shutdown, and periodic capture-active pause sync to avoid recorder contention).
- [x] MP-201 Route wake detections through the existing `Ctrl+R` capture path so wake-word and manual recording share one recording/transcription pipeline (landed shared trigger handling in `event_loop/input_dispatch.rs` so wake detections and manual `Ctrl+R` use the same start-capture path; wake detections ignore active-recording stop toggles by design).
- [x] MP-202 Add debounce and false-positive guardrails plus explicit HUD privacy indicator while wake-listening is active (landed explicit Full-HUD wake privacy badge states `Wake: ON`/`Wake: PAUSED`, plus stricter short-utterance wake phrase gating so long/background mentions are ignored before trigger delivery).
- [x] MP-203 Add wake-word regression + soak validation gates (unit/integration/lifecycle tests and long-run false-positive/latency checks) and require passing evidence before release/tag (landed deterministic wake runtime lifecycle tests via spawn-hooked listener ownership checks, expanded detection-path regression tests, long-run hotword false-positive/latency soak test, reusable guard script `dev/scripts/tests/wake_word_guard.sh`, `devctl check --profile release` wake-guard integration, and dedicated CI lane `.github/workflows/wake_word_guard.yml`).
- [x] MP-286 Add an image-capture interaction mode for Codex sessions: expose a persistent ON/OFF mode, show a concise HUD indicator, support click/hotkey capture triggers, and inject a capture prompt with saved image path into the active PTY so users can run picture-assisted chats without leaving VoiceTerm (landed `image_mode.rs` capture pipeline with platform-default command fallback + configurable `--image-capture-command`, added persistent `--image-mode` runtime toggle in CLI/settings/config, added `IMG` status badge, and routed manual trigger paths (`Ctrl+R` + rec button) to image capture only when image mode is enabled while preserving normal voice-record behavior when disabled; capture injects `Please analyze this image file: <path>` into active PTY respecting send mode (`auto` send with newline vs `insert` staged text); docs/changelog/help/flags updated in `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `dev/CHANGELOG.md`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-287 Resume a scoped slice of deferred Dev Mode behind a guarded launch flag: add `--dev` activation (with `--dev-mode`/`-D` aliases), keep default runtime behavior unchanged when absent, and surface explicit in-session mode visibility for dev-only experimentation (landed guarded CLI gate `--dev` with aliases in `config/cli.rs`, wired runtime state to `StatusLineState`, and added a `DEV` Full-HUD badge path so guarded mode is explicit only when enabled; default launch behavior remains unchanged when flag is absent; docs/changelog/help groups updated in `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `dev/CHANGELOG.md`, and `custom_help.rs`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-288 Start deferred Dev Mode foundation by introducing a shared `rust/src/devtools/` core (stable event schema + bounded in-memory session aggregator) and wiring guarded `--dev` runtime capture events into that shared model without changing non-dev runtime behavior (landed new shared `voiceterm::devtools` module with schema-versioned `DevEvent` model + bounded `DevModeStats` ring buffer/session snapshot aggregation in `rust/src/devtools/events.rs` and `rust/src/devtools/state.rs`, exported via `rust/src/devtools/mod.rs` and `rust/src/lib.rs`; runtime bridge now instantiates guarded in-memory dev stats only when `--dev` is enabled (`main.rs`) and records transcript/empty/error voice-job events from the existing drain path without affecting default mode (`event_state.rs`, `event_loop.rs`, `voice_control/drain.rs`); verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-289 Add guarded Dev Mode logging controls and on-disk event persistence: introduce `--dev-log` + `--dev-path`, enforce `--dev` guardrails, and append captured dev events to session JSONL files under the configured dev path without changing non-dev behavior (landed guarded CLI flags `--dev-log` and `--dev-path` in `config/cli.rs` with startup validation gates in `main.rs` (`--dev-log`/`--dev-path` now require `--dev`, and `--dev-path` requires `--dev-log`), added shared dev-event JSONL persistence in `rust/src/devtools/storage.rs` (`DevEventJsonlWriter`, per-session `session-*.jsonl` files under `<dev-root>/sessions/`, default dev root `$HOME/.voiceterm/dev` with `<cwd>/.voiceterm/dev` fallback), and wired runtime logging through the existing guarded voice-drain path so captured dev events append on transcript/empty/error messages only when guarded logging is enabled (`event_state.rs`, `event_loop.rs`, `voice_control/drain.rs`); default non-dev runtime behavior remains unchanged; docs/help/changelog updated in `guides/CLI_FLAGS.md`, `guides/USAGE.md`, `README.md`, `QUICK_START.md`, `custom_help.rs`, and `dev/CHANGELOG.md`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-290 Extend Dev CLI reporting with guarded Dev Mode session telemetry summaries: add optional `--dev-logs` support to `devctl status`/`devctl report` (plus `--dev-root` and `--dev-sessions-limit`) so maintainers can inspect recent `session-*.jsonl` event counts/latency/error summaries without opening raw files (landed `collect_dev_log_summary()` in `dev/scripts/devctl/collect.py`, wired CLI flags in `dev/scripts/devctl/cli.py`, rendered markdown/json summary blocks in `dev/scripts/devctl/commands/status.py` and `dev/scripts/devctl/commands/report.py`, and added regression coverage in `dev/scripts/devctl/tests/test_collect_dev_logs.py`, `dev/scripts/devctl/tests/test_status.py`, and `dev/scripts/devctl/tests/test_report.py`; verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_collect_dev_logs dev.scripts.devctl.tests.test_status dev.scripts.devctl.tests.test_report`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`).
- [x] MP-291 Add a guarded `Ctrl+D` Dev panel overlay for `--dev` sessions: landed new `dev_panel.rs` formatter/render contract (read-only guard/logging/session-counter view), added `InputEvent::DevPanelToggle` parsing for raw `Ctrl+D` (`0x04`) and CSI-u `Ctrl+D`, wired guarded toggle behavior (`--dev` opens/closes panel; non-dev forwards `Ctrl+D` EOF byte to PTY so legacy behavior is preserved), introduced `OverlayMode::DevPanel` rendering/open/close/resize/mouse/reserved-row handling (`event_loop.rs`, `overlay_dispatch.rs`, `periodic_tasks.rs`, `overlay_mouse.rs`, `terminal.rs`, `overlays.rs`), and updated shortcut/help docs (`help.rs`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `README.md`, `QUICK_START.md`, `dev/CHANGELOG.md`); verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `cd rust && cargo check --bin voiceterm`, `cd rust && cargo test --bin voiceterm`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-295 Harden prompt-occlusion guardrails for Codex/Claude reply boxes: extend `prompt/claude_prompt_detect.rs` detection beyond approval-only patterns to include reply/composer prompt markers (including Unicode prompt glyphs and Codex command-composer hint text), enable the guard for both Codex and Claude backend labels during startup (`main.rs`), preserve zero-row HUD suppression + PTY row-budget restore behavior when suppression toggles (`prompt/mod.rs`, `event_loop` suppression path), and keep reply/composer suppression active while users type (clear only on submit/cancel input instead of every typed byte); docs/changelog updated in `guides/TROUBLESHOOTING.md`, `dev/ARCHITECTURE.md`, and `dev/CHANGELOG.md`; verification evidence: `cd rust && cargo test claude_prompt_detect --bin voiceterm`, `cd rust && cargo test reply_composer_ --bin voiceterm`, `cd rust && cargo test set_claude_prompt_suppression_updates_pty_row_budget --bin voiceterm`, `cd rust && cargo test periodic_tasks_clear_stale_prompt_suppression_without_new_output --bin voiceterm`, `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [ ] MP-301 Investigate intermittent wake/send reliability for real-world speech variants (for example `hate codex`, `hate cloud`, and while-speaking submit attempts) using targeted matcher tests plus transcript-level debug evidence.
  - [x] Initial slice: expand wake alias/send-intent coverage (`hate`/`pay` -> `hey`, `cloud`/`clog` -> `claude`, plus `send it` / `sending` / `sand`) and emit wake transcript decision traces in debug logs (`voiceterm --logs --log-content`).
  - [x] Reliability slice (2026-02-27): align wake-listener VAD threshold to live mic-sensitivity baseline (plus wake headroom) so wake detection tracks the same voice setup users already tuned for normal capture; also relaxed short wake-capture bounds (`min speech`, `lookback`, `silence tail`) and expanded `claude` alias normalization (`claud`, `clawed`) for lower-effort phrase pickup without shouting.
  - [ ] Follow-up slice: collect reproducible field log samples and tune mid-utterance submit heuristics without increasing false positives from background conversation.

## Phase 3B - Tooling Control Plane Consolidation

- [x] MP-157 Execute tooling-control-plane consolidation (archived at `dev/archive/2026-02-17-tooling-control-plane-consolidation.md`): implement `devctl ship`, deterministic step exits, dry-run behavior, machine-readable step reports, and adapter conversion for release entry points.
- [x] MP-158 Harden `devctl docs-check` policy enforcement so docs requirements are change-class aware and deprecated maintainer command references are surfaced as actionable failures.
- [x] MP-159 Add a dedicated tooling CI quality lane for `devctl` command behavior and maintainer shell-script integrity (release, release-notes, PyPI, Homebrew helpers).
- [x] MP-160 Canonicalize maintainer docs and macro/help surfaces to `devctl` first (`AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, maintainer macro packs, and `Makefile` help), keeping legacy wrappers documented as transitional adapters.
- [x] MP-302 Expand docs-governance control plane and process traceability: enforce strict tooling docs checks plus conditional strict user-facing docs checks in CI, add markdown/image/CLI-flag integrity guards, block accidental root `--*` artifact files, and document handoff/source-of-truth workflow for both human and AI contributors.
- [x] MP-239 Reorganize `AGENTS.md` into an agent-first execution router (task classes, context packs, normal-push vs release workflows, branch sync policy, command bundles, and explicit autonomy/guardrail rules) so AI contributors can deterministically choose the right docs, tools, and checks for each task.
- [x] MP-245 Refine `AGENTS.md` and `dev/DEVELOPMENT.md` into an index-first, user-story-driven execution system: add explicit start-up bootstrap steps, dirty-tree protocol, single-source command bundles, CI lane mapping by risk/path, release version-parity checks (`Cargo.toml` + `pyproject.toml` + macOS `Info.plist` + changelog) with a dedicated parity guard (`dev/scripts/checks/check_release_version_parity.py`), add an AGENTS-structure guard (`dev/scripts/checks/check_agents_contract.py`), and add an active-plan registry/sync guard (`dev/scripts/checks/check_active_plan_sync.py` + `dev/active/INDEX.md`) so SOP/router/bundle and active-doc discovery contracts fail early in local/CI governance checks.
- [x] MP-256 Add an orphaned-test process guardrail to tooling governance by extending `devctl hygiene` to detect leaked `target/debug/deps/voiceterm-*` binaries (error on detached `PPID=1` candidates, warning on active runs), then harden `devctl check` with automatic pre/post orphaned-test cleanup sweeps so interrupted local runs do not accumulate stale test binaries across worktrees.
- [x] MP-258 Automate PyPI publish in release flow by adding `.github/workflows/publish_pypi.yml` (triggered on `release: published`) and aligning maintainer docs so release runs publish through GitHub Actions while `devctl pypi --upload --yes` remains an explicit fallback path.
- [x] MP-259 Automate Codecov coverage uploads by adding `.github/workflows/coverage.yml` (Rust `cargo llvm-cov` LCOV generation + Codecov OIDC upload) and aligning maintainer docs/lane mapping so the README coverage badge is backed by current CI reports instead of `unknown`.
- [x] MP-260 Add non-regressive source-shape guardrails for Rust/Python so oversized files cannot silently drift into new God-file debt: add `dev/scripts/checks/check_code_shape.py` (working-tree + commit-range modes with soft/hard file-size limits and oversize-growth budgets), wire it into `tooling_control_plane.yml`, and add bundle/docs coverage for local maintainer runs.
- [x] MP-261 Refresh README brand banner with a new VoiceTerm hero logo asset (`img/logo-hero.png`) based on the finalized artwork while keeping subtitle/icon identity and removing redundant platform chips from the banner artwork itself (README remains the only consumer; generation script exploration was one-off and not retained in repo tooling).
- [x] MP-282 Consolidate visual planning docs by folding `dev/active/overlay.md` and `dev/active/theme_studio_redesign.md` into `dev/active/theme_upgrade.md`, then update active-index/sync-governance references so one canonical visual spec remains.
- [x] MP-283 Harden release distribution automation by adding a CI release preflight lane (`release_preflight.yml`), a Homebrew publish workflow path (`publish_homebrew.yml`), and safety guards for Homebrew tarball/SHA validation plus `devctl ship` release-version parity enforcement before CI/local publish steps.
- [x] MP-284 Reconcile ADR inventory to runtime truth: remove stale unimplemented proposal ADRs, promote architecture ADRs that match shipped behavior (overlay mode, runtime config precedence, session history boundaries, writer render invariants), and add missing ADR coverage for wake-word ownership, voice-macro precedence, and Claude prompt-safe HUD suppression.
- [x] MP-292 Refactor `devctl` internals to reduce module size, remove command-output drift, and harden missing-binary behavior: extracted shared process-sweep helpers (`dev/scripts/devctl/process_sweep.py`) for `check`/`hygiene`, shared `check` profile normalization (`dev/scripts/devctl/commands/check_profile.py`), shared status/report payload+markdown rendering (`dev/scripts/devctl/status_report.py`), split ship orchestration from step/runtime helpers (`dev/scripts/devctl/commands/ship.py`, `dev/scripts/devctl/commands/ship_common.py`, `dev/scripts/devctl/commands/ship_steps.py`), extracted hygiene audit helpers (`dev/scripts/devctl/commands/hygiene_audits.py`), updated `run_cmd`/ship command checks to return structured failures instead of uncaught Python exceptions when required binaries are missing, and rewrote helper/module docstrings in plain language so junior developers and AI agents can quickly understand when/why each helper exists; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-293 Add a dedicated `devctl security` command so maintainers can run a local security gate aligned with CI policy: landed `dev/scripts/devctl/commands/security.py` (RustSec JSON capture + policy enforcement + optional `zizmor` workflow scan with `--require-optional-tools` strict mode), extracted security CLI parser wiring into `dev/scripts/devctl/security/parser.py` to keep `dev/scripts/devctl/cli.py` below code-shape growth limits, wired list output in `dev/scripts/devctl/commands/listing.py`, added regression coverage in `dev/scripts/devctl/tests/test_security.py`, expanded plain-language process-sweep context for interrupted/stalled test cleanup in `dev/scripts/devctl/process_sweep.py`, and updated maintainer/governance docs (`AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, `dev/history/ENGINEERING_EVOLUTION.md`); verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py security --dry-run --with-zizmor --require-optional-tools --format json`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-294 Consolidate engineering narrative docs into a single canonical history source by folding `dev/docs/TECHNICAL_SHOWCASE.md` and `dev/docs/LINKEDIN_POST.md` into appendices in `dev/history/ENGINEERING_EVOLUTION.md`, then retiring the duplicated `dev/docs/` source files so updates only target one document; verification evidence: `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-297 Execute a focused `devctl check` usability/performance hardening sequence from maintainer review findings in ordered slices:
  - [x] `#5` failure-output diagnostics: `run_cmd` now streams subprocess output while preserving bounded failure excerpts for non-zero exits (`dev/scripts/devctl/common.py`), `check` prints explicit failed-step summaries with captured context (`dev/scripts/devctl/commands/check.py`), markdown reports include a dedicated failure-output section (`dev/scripts/devctl/steps.py`), and regression coverage/docs were updated (`dev/scripts/devctl/tests/test_common.py`, `dev/scripts/README.md`, `dev/history/ENGINEERING_EVOLUTION.md`); verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
  - [x] `#1` check-step parallelism: `devctl check` now runs independent setup gates (`fmt`, `clippy`, AI guard scripts) and the test/build phase through deterministic parallel batches with stable report ordering (`dev/scripts/devctl/commands/check.py`), includes maintainer controls for sequential fallback and worker tuning (`--no-parallel`, `--parallel-workers` in `dev/scripts/devctl/cli.py`), and adds regression coverage for parser wiring, parallel-path selection, and ordered aggregation (`dev/scripts/devctl/tests/test_check.py`); verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_check`.
  - [x] `#7` profile-vs-flag conflict validation: extracted `validate_profile_flag_conflicts()` into `check_profile.py` with `PROFILE_PRESETS` single source of truth, added 12 regression tests in `test_check.py`.
  - [x] `#4` explicit progress feedback: extracted `count_quality_steps()` and `emit_progress()` into `check_progress.py` with serial `[N/M]` and parallel `[N-M/T]` formats, added 10 regression tests in `test_check.py`.
  - [x] `#2` runaway-process containment: `run_cmd` now starts child steps in isolated process groups and tears down the full subprocess tree on interrupt (`dev/scripts/devctl/common.py`), while process sweep now treats stale active `voiceterm-*` test runners as cleanup/error candidates in both `check` and `hygiene` (`dev/scripts/devctl/process_sweep.py`, `dev/scripts/devctl/commands/check.py`, `dev/scripts/devctl/commands/hygiene.py`); regression coverage added in `dev/scripts/devctl/tests/test_common.py`, `dev/scripts/devctl/tests/test_process_sweep.py`, `dev/scripts/devctl/tests/test_check.py`, and `dev/scripts/devctl/tests/test_hygiene.py`.
  - [x] `#8` ADR-reference + governance parity guard: `devctl hygiene` now flags stale ADR reference patterns (hard-coded ADR counts and wildcard ADR file ranges), validates ADR backlog parity between `MASTER_PLAN` and `autonomous_control_plane`, and enforces reserved-ID coverage for missing backlog ADR files, with regression coverage in `dev/scripts/devctl/tests/test_hygiene.py`; docs were normalized to index-based ADR references in `dev/active/theme_upgrade.md` and `dev/history/ENGINEERING_EVOLUTION.md`, and release/tooling workflows now run workflow-shell + IDE/provider isolation + compat-matrix schema/smoke + naming consistency checks in their governance bundles.
  - [x] `#9` external publication drift governance: landed the tracked
    publication registry (`dev/config/publication_sync_registry.json`),
    `devctl publication-sync` report/record flow
    (`dev/scripts/devctl/publication_sync.py`,
    `dev/scripts/devctl/publication_sync_parser.py`,
    `dev/scripts/devctl/commands/publication_sync.py`), hygiene warnings via
    `dev/scripts/devctl/commands/hygiene.py` +
    `dev/scripts/devctl/commands/hygiene_audits.py`, the explicit guard
    `dev/scripts/checks/check_publication_sync.py`, release-preflight wiring,
    and regression coverage in
    `dev/scripts/devctl/tests/test_publication_sync.py` plus
    `dev/scripts/devctl/tests/test_check_publication_sync.py`; verification
    evidence: `python3 -m unittest dev.scripts.devctl.tests.test_publication_sync dev.scripts.devctl.tests.test_check_publication_sync`,
    `python3 dev/scripts/devctl.py publication-sync --format json`,
    `python3 dev/scripts/checks/check_publication_sync.py --report-only`.
- [x] MP-298 Parallelize independent `devctl status`/`report` collection probes and `ship --verify` subchecks with deterministic aggregation so I/O-heavy control-plane workflows run faster without changing pass/fail policy semantics.
  - [x] 2026-03-09 Rust-audit reporting slice: `devctl report` now has an optional
    parallel-collected `--rust-audits` probe that aggregates the Rust
    best-practices, lint-debt, and runtime-panic guards into one human-readable
    Markdown section with risk/fix explanations, optional matplotlib charts via
    `--with-charts`, deterministic report bundle emission (`--emit-bundle`),
    and shared full-tree support after adding `--absolute` mode to
    `check_rust_runtime_panic_policy.py`; targeted regression coverage added in
    `test_report.py`, `test_status_report_parallel.py`,
    `test_rust_audit_report.py`, and
    `test_check_rust_runtime_panic_policy.py`.
  - [x] 2026-03-09 `ship --verify` closure slice: independent verify subchecks
    now run through deterministic parallel aggregation in
    `dev/scripts/devctl/commands/ship_steps.py`, using quiet worker execution
    plus ordered failure selection so the first failing declared substep still
    determines the verify result even when workers complete out of order;
    regression coverage added in `dev/scripts/devctl/tests/test_ship.py` and
    `dev/scripts/devctl/tests/test_common.py`, with local proof via
    `python3 -m unittest dev.scripts.devctl.tests.test_common dev.scripts.devctl.tests.test_ship`
    and `python3 dev/scripts/devctl.py ship --version 1.1.1 --verify --dry-run --format json`.
- [x] MP-299 Add a `devctl triage` workflow that emits both human-readable markdown and AI-friendly JSON, with optional CIHub ingestion: landed new command surface (`dev/scripts/devctl/commands/triage.py`) plus parser/command inventory wiring (`dev/scripts/devctl/cli.py`, `dev/scripts/devctl/commands/listing.py`), optional `cihub triage` execution + artifact ingestion (`triage.json`, `priority.json`, `triage.md`) under configurable emit directories, and bundle emission mode (`--emit-bundle` writes `<prefix>.md` + `<prefix>.ai.json`) for project handoff/automation use; regression coverage/docs updated in `dev/scripts/devctl/tests/test_triage.py` and `dev/scripts/README.md`; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-300 Deepen `devctl triage` CIHub integration with actionable routing data: map `cihub` artifact records (`priority.json`, `triage.json`) into normalized issues (`category`, `severity`, `owner`, `summary`) via shared enrichment helpers (`dev/scripts/devctl/triage/enrich.py`), add configurable category-owner overrides (`--owner-map-file`) in parser wiring (`dev/scripts/devctl/triage/parser.py`), include rollup counts by severity/category/owner in report payload + markdown output (`dev/scripts/devctl/triage/support.py`), and extend regression coverage for severity/owner routing + owner-map overrides (`dev/scripts/devctl/tests/test_triage.py`) with docs updates in `dev/scripts/README.md`; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py triage --format md --no-cihub --emit-bundle --bundle-dir /tmp --bundle-prefix vt-triage-smoke --output /tmp/vt-triage-smoke.md`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-306 Add proactive report-retention governance to the `devctl` control plane: landed `devctl reports-cleanup` with retention safeguards (`--max-age-days`, `--keep-recent`, protected-path exclusions, dry-run preview, confirmation/`--yes` delete path), wired `hygiene` to always surface stale report-growth warnings with direct cleanup guidance, and added parser/command/hygiene regression coverage plus maintainer docs updates (`dev/scripts/README.md`, `dev/DEVCTL_AUTOGUIDE.md`).
- [x] MP-339 Migrate repository Rust workspace path from `src/` to `rust/` and update runtime/tooling/CI/docs path contracts in one governed pass (`dev/archive/2026-03-07-rust-workspace-layout-migration.md`), preserving behavior while removing the `src/src` naming pattern (landed filesystem rename + path-contract rewrites across scripts/checks/workflows/docs; follow-up guard hardening landed rename-aware baseline mapping for Rust debt/security checks, active-root discovery + fail-fast behavior for `check_rust_audit_patterns.py`, and an explicit non-regressive `mem::forget` policy in `check_rust_best_practices.py`; sync/tooling gates and Rust build smoke from `rust/` succeeded).
- [x] MP-303 Add automated release-metadata preparation to the `devctl` control plane so maintainers can run one command path before verify/tag: added `--prepare-release` support on `devctl ship`/`devctl release` (`dev/scripts/devctl/cli.py`, `dev/scripts/devctl/commands/release.py`, `dev/scripts/devctl/commands/ship.py`), implemented canonical metadata updaters for Cargo/PyPI/macOS app plist plus changelog heading rollover under `dev/scripts/devctl/commands/release_prep.py` and `ship_steps.py`, and covered step wiring + idempotent prep behavior in `dev/scripts/devctl/tests/test_ship.py` and `dev/scripts/devctl/tests/test_release_prep.py`; docs/governance updates in `AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, and `dev/history/ENGINEERING_EVOLUTION.md`; verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_ship dev.scripts.devctl.tests.test_release_prep`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [ ] MP-257 Run a plain-language readability pass across primary `dev/` entry docs (`dev/README.md`, `dev/DEVELOPMENT.md`, `dev/ARCHITECTURE.md`) so new developers can follow workflows quickly without losing technical accuracy.
  - [x] 2026-02-25 workflow readability slice: added `.github/workflows/README.md` with plain-language explanations for all workflow lanes (what runs, when it runs, and local reproduce commands) and added short purpose headers to every `.github/workflows/*.yml` file so intent is visible without opening full YAML bodies.
  - [x] 2026-02-25 core-dev-doc readability slice: simplified workflow/process language in `dev/README.md`, `dev/DEVELOPMENT.md`, and `dev/ARCHITECTURE.md` so operators can scan what to run and why without policy-heavy wording.
  - [x] 2026-02-25 user-guide readability slice: simplified wording across `guides/README.md`, `guides/INSTALL.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `guides/TROUBLESHOOTING.md`, and `guides/WHISPER.md` while preserving command/flag behavior and technical accuracy.
  - [x] 2026-02-25 root-entry readability slice: simplified wording in `README.md`, `QUICK_START.md`, and `DEV_INDEX.md` so first-time users and maintainers can scan setup/docs links quickly without changing any commands, flags, or workflow behavior.
  - [x] 2026-02-25 follow-up dev-entry readability slice: refined plain-language wording in `dev/README.md`, `dev/DEVELOPMENT.md`, and `dev/ARCHITECTURE.md`, and replaced the outdated `src/src` tree in `dev/DEVELOPMENT.md` with the current `rust/` layout summary so docs are both easier to scan and accurate.

## Phase 3C - Codebase Best-Practice Consolidation (Active Audit Track)

- [x] MP-184 Publish a dedicated execution record for full-repo Rust best-practice cleanup and keep task-level progress scoped to that audit track.
- [x] MP-185 Decompose settings action handling for lower coupling and clearer ownership (`settings_handlers` runtime/test separation, enum-cycle consolidation, constructor removal, status-helper extraction, and `SettingsActionContext` sub-context split landed; adjacent `ButtonActionContext::new` constructor removal also landed for consistent context wiring).
- [x] MP-186 Consolidate status-line rendering/button logic (`status_line/buttons.rs` and `status_line/format.rs`) to remove duplicated style/layout decisions and isolate legacy compatibility paths (landed: shared button highlight + queue/ready/latency badge helpers; legacy row helpers are `#[cfg(test)]`-gated with shared framing/separator helpers and reduced dead-code surface; tests split into `status_line/buttons/tests.rs` and `status_line/format/tests.rs`).
- [x] MP-187 Consolidate PTY lifecycle internals into canonical spawn/shutdown helpers and harden session-guard identity/cleanup throttling to reduce stale-process risk without blocking concurrent sessions (landed shared PTY lifecycle helpers in `pty_session/pty.rs`, plus session-lease start-time identity validation and atomic cleanup cadence throttling in `pty_session/session_guard.rs`; additional detached-orphan sweep fallback now reaps stale backend CLIs with `PPID=1` when they are not lease-owned and no longer share a TTY with a live shell, with deterministic unit coverage for elapsed-time parsing and candidate filtering).
- [x] MP-188 Decompose backend orchestration hotspots (`codex/pty_backend.rs`, `ipc/session.rs`) into narrower modules with explicit policy boundaries and lower test/runtime coupling (completed in v1.0.80: landed `codex/pty_backend/{output_sanitize,session_call,job_flow,test_support}.rs` plus `ipc/session/{stdin_reader,claude_job,auth_flow,loop_control,state,event_sink,test_support}.rs`, keeping parent orchestrators focused on runtime control flow).
- [x] MP-189 Add a focused maintainer lint-hardening lane (strict clippy profile + targeted allowlist) and burn down high-value warnings (`must_use`, error docs, redundant clones/closures, risky casts, dead-code drift) (completed in v1.0.80: landed `devctl check --profile maintainer-lint` + `.github/workflows/lint_hardening.yml`, burned down targeted warnings, added Linux ALSA dependency setup for the lane, and documented intentional deferral of precision/truncation DSP cast families).
- [x] MP-191 Fix Homebrew `opt` launcher path detection in `scripts/start.sh` + `scripts/setup.sh` so upgrades reuse persistent user model storage (`~/.local/share/voiceterm/models`) instead of redownloading into versioned Cellar `libexec/whisper_models`.
- [x] MP-192 Fix Full HUD ribbon baseline rendering by padding short waveform history at floor level (`-60 dB`) so right-panel visuals ramp upward instead of drawing a full-height block.
- [x] MP-193 Restore insert-mode early-send behavior for `Ctrl+E` while recording so noisy-room captures can stop early and submit immediately (one-shot force-send path + regression tests + docs alignment).
- [x] MP-197 Make hidden-HUD idle launcher visuals intentionally subdued (dull/muted text and `[open]`) so hidden mode remains non-intrusive.
- [x] MP-198 Align insert-mode `Ctrl+E` dispatch semantics (send staged text, finalize+submit while recording, consume idle/no-staged input) and apply the same muted hidden-launcher gray to hidden recording output.
- [x] MP-204 Refine hidden-HUD idle launcher controls for lower visual noise and better explicitness (remove inline `Ctrl+U` hint from hidden launcher text, add muted `[hide]` control next to `[open]`, support collapsing hidden launcher chrome to `[open]` only, and make `open` two-step from collapsed mode: restore launcher first, then switch HUD style on the next open).
- [x] MP-205 Harden discoverability + feedback ergonomics (expand startup hints for `?`/settings/mouse discoverability, add grouped help overlay sections, and surface explicit idle `Ctrl+E` feedback with `Nothing to send`).
- [x] MP-206 Add first-run onboarding hint persistence (`~/.config/voiceterm/onboarding_state.toml`) so a `Getting started` hint remains until the first successful transcript capture.
- [x] MP-207 Extract shared overlay frame rendering helpers (`overlay_frame`) and route help/settings/theme-picker framing through the shared path to reduce duplicated border/title/separator logic.
- [x] MP-208 Standardize overlay/HUD width accounting with Unicode-aware display width and add HUD module `priority()` semantics so queue/latency indicators survive constrained widths ahead of lower-priority modules.
- [x] MP-209 Replace opaque runtime status errors with log-path-aware messages (`... (log: <path>)`) across capture/transcript failure paths.
- [x] MP-210 Keep splash unchanged, but move discoverability/help affordances into runtime HUD/overlay surfaces (hidden HUD idle hint now includes `? help` + `^O settings`; help overlay adds clickable Docs/Troubleshooting OSC-8 links).
- [x] MP-211 Replace flat clap default `--help` output with a themed, grouped renderer backed by clap command metadata (manual `-h`/`--help` interception, sectioned categories, single-accent hacker-style scan path with dim borders + bracketed headers, theme/no-color parity, and coverage guard so new flags cannot silently skip grouping).
- [x] MP-212 Remove stale pre-release/backlog doc references, align `VoiceTerm.app` Info.plist version with `rust/Cargo.toml`, and sync new `voiceterm` modules in changelog/developer structure docs.
- [x] MP-213 Add a Rust code-review research pack and wire it into the code-quality execution track with an explicit closure/archive handoff path into Theme Upgrade phases (`MP-148+`).
- [x] MP-218 Fix overlay mouse hit-testing for non-left-aligned coordinate spaces so settings/theme/help row clicks and slider adjustments still apply when terminals report centered-panel `x` coordinates.
- [x] MP-219 Clarify settings overlay footer control hints (`[×] close · ↑/↓ move · Enter select · Click/Tap select`) and add regression coverage so footer close click hit-testing stays intact after copy updates.
- [x] MP-220 Fix settings slider click direction handling so pointer input on `Sensitivity`/`Wake sensitivity` tracks can move left/right by click position, with regression tests for backward slider clicks.
- [x] MP-221 Fix hidden-launcher mouse click redraw parity so `[hide]` and collapsed `[open]` clicks immediately repaint launcher state (matching arrow-key `Enter` behavior), with regression tests for both click paths.
- [x] MP-222 Resolve post-release `lint_hardening` CI failures by removing redundant-closure clippy violations in `custom_help.rs` and restoring maintainer-lint lane parity on `master`.
- [x] MP-223 Unify README CI/mutation badge theming to black/gray endpoint styling and enforce red failure states via renderer scripts (`render_ci_badge.py`, `render_mutation_badge.py`) plus CI workflow auto-publish on `master`.
- [x] MP-224 Harden Theme Studio style-pack test determinism by isolating unit tests from ambient shell `VOICETERM_STYLE_PACK_JSON` exports (tests now ignore runtime style-pack env unless explicit opt-in is set, and lock-path tests opt in intentionally), preventing cross-shell snapshot/render drift during `cargo test --bin voiceterm`.
- [x] MP-225 Fix Enter-key auto-mode flip regression: when stale HUD button focus is on `ToggleAutoVoice`, pressing `Enter` now submits PTY input (no mode flip), backed by a focused event-loop regression test and docs sync.
- [x] MP-228 Audit user-doc information architecture and seed screenshot-refresh governance: rebalance `QUICK_START.md` to onboarding scope, move deep runtime semantics to guides, document transcript-history mouse behavior and env parity (`VOICETERM_ONBOARDING_STATE`), and add a maintainer capture matrix for pending UI surfaces.
- [x] MP-214 Close out the active code-quality track by triaging remaining findings, archiving audit records, and continuing execution from Theme Upgrade (`MP-148+`).
- [x] MP-215 Standardize runtime status-line width/truncation on Unicode-aware display width in remaining char-count paths (`rust/src/bin/voiceterm/writer/render.rs` and `rust/src/bin/voiceterm/status_style.rs`) with regression coverage for wide glyphs (landed Unicode-aware width/truncation in writer sanitize/render/status-style paths, preserved printable Unicode status text, and added regression tests for wide-glyph truncation and width accounting).
- [x] MP-216 Consolidate duplicate transcript-preview formatting logic shared by `rust/src/bin/voiceterm/voice_control/navigation.rs` and `rust/src/bin/voiceterm/voice_control/drain/message_processing.rs` into a single helper with shared tests (landed shared `voice_control/transcript_preview.rs` formatter and removed duplicated implementations from navigation/drain paths with focused unit coverage).
- [x] MP-217 Enable settings-overlay row mouse actions so row clicks select and apply setting toggles/cycles (including click paths for `Close` and `Quit`) instead of requiring keyboard-only action keys.
- [x] MP-262 Publish a full senior-level engineering audit baseline in `dev/archive/2026-02-20-senior-engineering-audit.md` with measured code-shape, lint-debt, CI hardening, and automation findings mapped to executable follow-up MPs.
- [x] MP-263 Harden GitHub Actions supply-chain posture: pin third-party actions by commit SHA, define explicit least-privilege `permissions:` on every workflow, and add `concurrency:` groups where duplicate in-flight runs can race or waste minutes (landed by pinning all workflow action refs to 40-char SHAs across `.github/workflows/*.yml`, adding explicit `permissions:`/`concurrency:` blocks to every workflow, and narrowing write scope to job-level where badge-update pushes require `contents: write`).
- [x] MP-264 Add repository ownership and dependency automation baseline by introducing `.github/CODEOWNERS` and `.github/dependabot.yml` (grouped update policies + review routing) so tooling/runtime changes always have accountable reviewers and timely dependency refresh cadence (landed with explicit ownership coverage for runtime/tooling/distribution paths and weekly grouped update policies for GitHub Actions, Cargo, and PyPI packaging surfaces).
- [ ] MP-265 Decompose oversized runtime modules with explicit shape budgets and staged extraction plans (top hotspots: `event_loop/input_dispatch.rs`, `status_line/format.rs`, `status_line/buttons.rs`, `theme/rule_profile.rs`, `theme/style_pack.rs`, `transcript_history.rs`; next maintainability-audit tranche should prioritize `event_loop.rs`, `main.rs`, `dev_command/{broker,review_artifact,command_state}.rs`, and `dev_panel/{review_surface,cockpit_page/mod}.rs`) while preserving non-regression behavior coverage (in progress: `dev/scripts/checks/check_code_shape.py` now enforces path-level non-growth budgets for the hotspot files so decomposition work is CI-measurable instead of policy-only; `event_loop/input_dispatch.rs` overlay-mode handling was extracted into `event_loop/input_dispatch/overlay.rs` + `event_loop/input_dispatch/overlay/overlay_mouse.rs`; prior slice extracted status-line right-panel formatting/animation helpers from `status_line/format.rs` into `status_line/right_panel.rs`; latest slices move minimal-HUD right-panel scene/waveform/pulse helpers from `status_line/buttons.rs` into `status_line/right_panel.rs` and extract queue/wake/latency badge formatting into `status_line/buttons/badges.rs`, reducing `status_line/buttons.rs` from 1059 to 801 lines while keeping focused status-line tests green; newest slices extract compact/minimal HUD helpers into `status_line/format/compact.rs`, then move single-line layout helpers into `status_line/format/single_line.rs`, reduce `theme/rule_profile.rs` by moving inline tests into `theme/rule_profile/tests.rs` (`922 -> 265`), and move writer-state test-only timing constants from `writer/state.rs` into `writer/state/tests.rs` so production writer modules remain runtime-focused; raised file-shape overrides were removed with focused runtime suites and clippy reruns green, writer message routing remains split across `writer/state/dispatch.rs` plus `writer/state/dispatch_pty.rs` after retiring temporary dispatch/redraw/prompt complexity exceptions, and the newest Rust-overlay cleanup split `dev_panel/review_surface.rs` lane helpers plus `dev_panel/cockpit_page/mod.rs` control sections into focused sibling modules (`review_surface_lanes.rs`, `cockpit_page/control_sections.rs`) so both Dev-panel hotspots now sit well below their prior shape-risk thresholds).
- [ ] MP-266 Burn down Rust lint-debt hotspots by reducing `#[allow(...)]` surface area and non-test `unwrap/expect` usage, then add measurable gates/reporting so debt cannot silently regress (in progress: landed `dev/scripts/checks/check_rust_lint_debt.py` with working-tree + commit-range modes, wired governance bundles/docs references, and added tooling-control-plane CI enforcement so changed Rust files cannot add net-new lint debt without an explicit failure signal; latest slice removes 22 `#[allow(dead_code)]` suppressions by scoping PTY counter helper APIs/re-exports to tests in `pty_session/counters.rs` + `pty_session/mod.rs`, with full `devctl check --profile ci` and lifecycle matrix test coverage green; newest enforcement slice keeps AI-guard scripts enabled in `check --profile quick|fast` so default local iteration and post-test quick follow-up paths no longer skip structural/code-quality guards by profile default).
- [ ] MP-267 Run a naming/API cohesion pass across theme/event-loop/status/memory surfaces to remove ambiguous names, tighten public API intent, and consolidate duplicated helper logic into shared modules (`dev/active/naming_api_cohesion.md`; in progress: canonical `swarm_run` command naming now enforced in parser/dispatch/workflow/docs with no legacy alias in active command paths, duplicate triage/mutation policy engines consolidated into shared `loop_fix_policy.py` helper with tests, duplicated devctl numeric parsing consolidated into `dev/scripts/devctl/numeric.py` (`to_int`/`to_float`/`to_optional_float`) with callsite rewiring, Theme Studio list navigation consolidated under shared `theme_studio/nav.rs` with consistent `select_prev`/`select_next` naming across page state + input-dispatch call paths, prompt-occlusion suppression transitions extracted into `event_loop/prompt_occlusion.rs` so output/input/periodic dispatchers share one runtime owner for suppression side effects, and the next portability slice is now explicit in `dev/guides/DEVCTL_ARCHITECTURE.md`: define one repo-policy-backed KISS naming-contract guard for public `devctl` words, generated AI/dev surfaces, and beginner-facing docs copy).
- [x] MP-268 Codify a Rust-reference-first engineering quality contract in `AGENTS.md` and `dev/DEVELOPMENT.md`, including mandatory official-doc reference pack links and handoff evidence requirements for non-trivial Rust changes.
- [ ] MP-269 Add Theme Studio style-pack hot reload (`notify` watcher + debounce + deterministic rollback-safe apply path) so theme iteration does not require restarting VoiceTerm.
- [ ] MP-270 Add algorithmic theme generation mode (`palette`-backed seed-color derivation with contrast guards) and expose it in Theme Studio as an optional starting point, not a replacement for manual edits.
- [ ] MP-271 Replace ad-hoc animation transitions with a deterministic easing profile layer (`keyframe`-style easing contracts or equivalent) and benchmark frame-cost impact on constrained terminals.
- [ ] MP-272 Define and implement Memory Studio context-injection contract for Codex/Claude handoff flows (selection policy, token budget, provenance formatting, failure rollback).
- [ ] MP-273 Produce an overlay architecture ADR evaluating terminal-only vs hybrid desktop overlay (`egui_overlay`/window-layer path) with explicit capability matrix, migration risk, and phased rollout recommendation.
- [x] MP-274 Add AI coding guardrails for Rust best-practice drift by introducing `dev/scripts/checks/check_rust_best_practices.py` (working-tree + commit-range non-regression checks for reason-less `#[allow(...)]`, undocumented `unsafe { ... }`, and public `unsafe fn` without `# Safety` docs), wiring it into `devctl check` (`--profile ai-guard` plus automatic `prepush`/`release` guard steps), and enforcing commit-range execution in `.github/workflows/tooling_control_plane.yml` with docs/bundle parity updates.
- [x] MP-275 Normalize `--input-device` values before runtime recorder lookup by collapsing wrapped whitespace/newline runs and rejecting empty normalized names so wake/manual capture initialization stays resilient to terminal line-wrap paste artifacts.
- [x] MP-276 Harden wake-word runtime diagnostics/ownership handoff: HUD now reflects listener-startup failures (`Wake: ERR` + status/log-path message) instead of false `Wake: ON` state when listener init fails, and wake detection now self-pauses listener capture before triggering shared capture startup to reduce microphone ownership races.
- [x] MP-277 Expand wake-word matcher alias normalization for common STT token-split variants (`code x` -> `codex`, `voice term` -> `voiceterm`) while preserving short-utterance guardrails and updating troubleshooting phrase guidance.
- [x] MP-278 Correct wake-trigger capture origin labeling end-to-end so wake-detected recordings flow through the shared capture path with explicit `WakeWord` trigger semantics (logs/status no longer misreport wake-initiated captures as manual starts).
- [x] MP-279 Reduce wake-state confusion and listener churn: keep `Wake: ON` badge styling steady (no pulse redraw), remove periodic wake-badge animation ticks, and extend wake-listener capture windows to reduce frequent microphone open/close cycling on macOS.
- [x] MP-280 Harden wake re-arm reliability after first trigger by decoupling wake detections from the auto-voice pause latch, allowing longer command tails when wake phrases lead the transcript, and adding no-audio retry backoff to reduce rapid microphone indicator churn on transient capture failures.
- [x] MP-281 Add built-in voice submit intents for insert mode (`send`, `send message`, `submit`) so staged transcripts can be submitted hands-free through the same newline path as Enter, including one-shot wake tails (`hey codex send` / `hey claude send`).
- [x] MP-296 Keep latency visibility stable in auto mode by preserving the last successful latency sample across auto-capture `Empty` cycles and allowing the shortcuts-row latency badge to remain visible during auto recording/processing (manual mode continues hiding during active capture); coverage added in `status_line/buttons/tests.rs` and `voice_control/drain/tests.rs`.

## Phase 3D - Memory + Action Studio (Planning Track)

Memory Studio execution gate: MP-230..MP-255 are governed by
`dev/active/memory_studio.md`. A Memory MP may move to `[x]` only with
documented `MS-G*` pass evidence.

- [x] MP-230 Establish canonical memory event schema + storage foundation (JSONL append log + SQLite index) for machine-usable local memory (`MS-G01`, `MS-G02`).
- [ ] MP-231 Implement deterministic retrieval APIs (topic/task/time/semantic) with provenance-tagged ranking and bounded token budgets (`MS-G03`, `MS-G04`, `MS-G18`, `MS-G19`). Current proving substrate is the shipped in-memory index plus `boot_pack` / `task_pack`; 2026-03-09 follow-ups now auto-extract bounded `MP-*` refs, repo file paths, and small topic tags on live ingest and emit operator-cockpit export artifacts for `task_pack`, `session_handoff`, and `survival_index`. The first scoring-trace/query-evidence closure slice is now live in `memory/survival_index.rs` and Memory cockpit exports (`query_traces` + deduplicated evidence rows); remaining scope is broader semantic/topic ranking coverage and browser-level retrieval UX.
- [x] MP-232 Ship context-pack generation (`context_pack.json` + `context_pack.md`) for AI boot/handoff workflows with explicit evidence references (`MS-G03`, `MS-G07`).
- [ ] MP-233 Deliver Memory Browser overlay (filter/expand/scroll/replay-safe controls) with keyboard+mouse parity (`MS-G06`, `MS-G20`). Current proving path should surface memory status/query/export views inside the Rust operator cockpit first, then expand into the fuller Memory Browser once the cross-plan operator flow is stable. The shipped proof is broader now: Control-tab memory status, a dedicated read-only Memory cockpit tab backed by ingest/review/boot-pack/handoff previews, the Boot-pack-backed Handoff preview, and repo-visible JSON/Markdown exports for `boot_pack`, `task_pack`, `session_handoff`, and the first `survival_index` preview are live. Remaining open scope is the full browser UX plus attach-by-ref/state-flow integration on top of those exports.
- [ ] MP-234 Deliver Action Center overlay with policy-tiered command execution (read-only/confirm-required/blocked), preview/approval flow, and action-run audit logging (`MS-G05`, `MS-G06`). Action policy/catalog scaffolding already exists in `memory/action_audit.rs`; this scope still needs runtime approval flows, audit wiring, and convergence with the MP-340 typed action router so memory-derived suggestions, overlay buttons, and review-channel requests share one approval/waiver model instead of parallel executors.
- [ ] MP-235 Add memory governance controls (retention, redaction hooks, per-project isolation) and regression tests for bounded growth/privacy invariants (`MS-G04`, `MS-G05`). Redaction plus retention-GC foundation is already shipped in `memory/governance.rs`; remaining scope is user-facing policy wiring, isolation profiles, and regression coverage.
- [ ] MP-236 Complete docs + release readiness for Memory Studio (architecture/user docs/changelog + CI evidence bundle) (`MS-G07`, `MS-G08`).
- [ ] MP-237 Add memory-evaluation harness and quality gates (`precision@k`, evidence coverage, deterministic pack snapshots, latency budgets) for release blocking (`MS-G03`, `MS-G04`, `MS-G08`).
- [ ] MP-238 Add model-adapter interop for context packs (Codex/Claude-compatible pack rendering while preserving canonical JSON provenance, including review-channel/controller handoff attachments) (`MS-G03`, `MS-G07`, `MS-G08`). Current runtime proof already builds a boot-pack-backed fresh bootstrap prompt in the Rust handoff cockpit, the Memory cockpit now emits repo-visible JSON/Markdown exports for `boot_pack`, `task_pack`, `session_handoff`, and `survival_index`, and the typed Rust action catalog carries review launch/rollover plus pause/resume actions with JSON summary rendering. Structured `review_state` attach-by-ref is now partially landed: event-backed review packets preserve `context_pack_refs` into reduced state/actions projections, Rust review surfaces/fresh prompts render those refs read-only, and the PyQt6 operator approval path keeps them lossless through decision artifacts. Missing scope is `controller_state` parity, broader provider-shaped review/control attachments, and packet-outcome ingest parity.
- [ ] MP-240 Add validated Memory Cards as a derived-truth layer (decision/project_fact/procedure/gotcha/task_state/glossary) with evidence links, TTL policies, and branch-aware validation-before-injection (`MS-G03`, `MS-G09`).
- [x] MP-241 Wire dev tooling and git intelligence into memory ingestion (`devctl status/report`, release-notes artifacts, git range summaries) and ship compiler outputs (`project_synopsis`, `session_handoff`, `change_digest`) in JSON+MD (`MS-G02`, `MS-G10`).
- [ ] MP-242 Ship read-only MCP memory exposure (resources + tools for search/context packs/validation) with deterministic provenance payloads and policy-safe defaults (`MS-G03`, `MS-G11`).
- [ ] MP-243 Add user memory-control modes (`off`, `capture_only`, `assist`, `paused`, `incognito`) with UI/state persistence and regression coverage for trust/privacy invariants (`MS-G05`, `MS-G06`). Current implementation now spans the Rust Dev-panel Control + Memory tabs with runtime mode/status visibility and mode-cycling, and the 2026-03-09 persistence slice landed startup restore plus persistent-config load/save so the configured `memory_mode` no longer resets on boot and dev-panel mode changes persist immediately into later snapshots. Closure still requires visible controls outside `--dev` plus negative-control/receipt UX.
- [ ] MP-244 Add sequence-aware action safety escalation so multi-command workflows increase policy tier when risk patterns combine (mutation + network + shell exec) and require explicit confirmation evidence (`MS-G05`, `MS-G11`).
- [ ] MP-246 Implement repetition-mining over memory events/command runs to detect high-frequency scriptable workflows, with support+confidence thresholds and provenance-scored candidates (`MS-G03`, `MS-G10`, `MS-G12`).
- [ ] MP-247 Ship automation suggestion flow that proposes script templates + `AGENTS.md` instruction patches + workflow snippets with preview/approve/reject UX (no auto-apply) and acceptance telemetry (`MS-G05`, `MS-G06`, `MS-G12`).
- [ ] MP-248 Add opt-in external transcript import adapters (for example ChatGPT export files) normalized into canonical memory schema with source tagging/redaction and retrieval-only defaults for safety (`MS-G01`, `MS-G05`, `MS-G13`).
- [ ] MP-249 Implement isolation profiles for action execution (`host_read_only`, `container_strict`, `host_confirmed`) with policy wiring, audit logging, and escape-attempt regression tests (`MS-G05`, `MS-G14`).
- [ ] MP-250 Build compaction experiment harness (A/B against no-compaction baseline) with replay fixtures, benchmark adapters, and report artifacts covering quality/citation/latency/token metrics (`MS-G03`, `MS-G15`).
- [ ] MP-251 Gate compaction default-on rollout behind non-inferiority/evidence thresholds and publish operator guidance for safe enablement strategy (`MS-G07`, `MS-G08`, `MS-G15`).
- [ ] MP-252 Prototype Apple Silicon acceleration paths (SIMD/Metal/Core ML where applicable) for memory retrieval/compaction workloads and publish backend benchmark matrix vs CPU reference (`MS-G03`, `MS-G16`).
- [ ] MP-253 Gate acceleration rollout behind non-inferiority quality checks, deterministic-evidence parity checks, and runtime fallback guarantees (`MS-G08`, `MS-G16`).
- [ ] MP-254 Evaluate ZGraph-inspired symbolic compaction for memory units/context packs (pattern aliases for repeated paths/commands/errors), with reversible transforms and deterministic citation-equivalence checks (`MS-G03`, `MS-G15`, `MS-G17`).
- [ ] MP-255 Gate any symbolic compaction rollout behind non-inferiority quality thresholds, round-trip parity fixtures, and explicit default-off operator guidance until `MS-G17` passes (`MS-G07`, `MS-G08`, `MS-G17`).

2026-03-09 implementation alignment for the memory lane: the current runtime
already ships JSONL-backed memory ingest/recovery, an in-memory retrieval
index, operator-cockpit memory status/mode snapshots, and a boot-pack-backed
handoff/bootstrap prompt. The 2026-03-09 runtime follow-ups also landed
operator-cockpit query/export views by emitting repo-visible `boot_pack`,
`task_pack`, `session_handoff`, and `survival_index` JSON/Markdown artifacts
from the Rust Memory tab. The first scoring-trace closure is now shipped via
`memory/survival_index.rs` + structured `survival_index` exports. The next
slice is to turn the remaining proof path into `MP-231`/`MP-238`/`MP-243`
closure evidence by expanding retrieval coverage, finishing review/control
`context_pack_refs` consumption, and landing packet-outcome ingest
before the full Memory Browser / Action Center overlays
become the main product surface.

## Phase 3A - Mutation Hardening (Parallel Track)

- [ ] MP-015 Improve mutation score with targeted high-value tests (promoted from Backlog).
  - [ ] Build a fresh shard-by-shard survivor baseline on `master` and rank hotspots by missed mutants.
  - [x] Add mutation outcomes freshness visibility and stale-data gating in local tooling (`check_mutation_score.py` + `devctl mutation-score` now report source path/age and support `--max-age-hours`).
  - [x] Add targeted mutation-killer coverage for `theme_ops::cycle_theme` ordering/wrap semantics so default-return/empty-list/position-selection mutants are caught deterministically.
  - [x] Add targeted mutation-killer coverage for `Theme::from_name` alias arms (`tokyonight`/`tokyo-night`/`tokyo`, `gruvbox`/`gruv`) and `Theme::available()` list parity so empty/placeholder return mutants are caught.
  - [x] Add targeted mutation-killer coverage for `status_style::status_display_width` arithmetic and `terminal::take_sigwinch` clear-on-read semantics so constant-return/math mutants are caught.
  - [x] Add targeted mutation-killer coverage for `main.rs` runtime guards (`contains_jetbrains_hint`, `is_jetbrains_terminal`, `resolved_meter_update_ms`, and `join_thread_with_timeout`) and eliminate focused survivors (`cargo mutants --file src/bin/voiceterm/main.rs`: 18 caught, 0 missed, 1 unviable).
  - [x] Add targeted mutation-killer coverage for `input/mouse.rs` protocol guards/parsers (SGR/URXVT/X10 prefix+length boundaries and dispatch detection), eliminating focused survivors (`cargo mutants --file src/bin/voiceterm/input/mouse.rs`: 76 caught, 0 missed, 17 unviable).
  - [x] Remove the equivalent survivor path in `config/theme.rs` (`theme_for_backend` redundant `NO_COLOR` branch), keep explicit env-behavior regression coverage, and re-verify focused mutants (`cargo mutants --file src/bin/voiceterm/config/theme.rs`: 6 caught, 0 missed) plus `devctl check --profile ci` green.
  - [x] Eliminate `event_loop.rs` helper/boundary survivors by adding direct coverage for drain/winsize/overlay rendering/button-registry/picker reset paths, hardening settings-direction boundary assertions, and refactoring slider sign math to non-equivalent `is_negative()` checks (`cargo mutants --file src/bin/voiceterm/event_loop.rs`: 58 caught, 0 missed, 2 unviable) with `devctl check --profile ci` green.
  - [x] Remove `config/backend.rs` argument-length equivalent survivors in backend command resolution (`command_parts.len() > 1`) by refactoring to iterator-based split (`next + collect`) and re-verifying focused mutants (`cargo mutants --file src/bin/voiceterm/config/backend.rs`: 1 caught, 0 missed, 1 unviable) with `devctl check --profile ci` green.
  - [x] Add targeted `config/util.rs` path-shape boundary coverage for `is_path_like` (absolute/relative path positives, bare binary and empty-value negatives) and re-verify focused mutants (`cargo mutants --file src/bin/voiceterm/config/util.rs`: 11 caught, 0 missed) with `devctl check --profile ci` green.
  - [x] Add targeted regression coverage for runtime utility hotspots `auth.rs` and `lock.rs` (login command validation + exit-status mapping paths and mutex poison-recovery paths) so low-coverage utility modules stay protected without introducing lint-debt growth.
  - [x] Harden `event_loop/input_dispatch/overlay/overlay_mouse.rs` boundary predicates and add focused Theme Studio/settings mouse regression coverage (footer non-close area, border columns, option-row activation/out-of-range guards), eliminating the focused survivor cluster (`cargo mutants --file src/bin/voiceterm/event_loop/input_dispatch/overlay/overlay_mouse.rs --re 'overlay_mouse\\.rs:(32|39|99|100|119|142|143|144|145):'`: 8 caught, 0 missed).
  - [ ] Add targeted tests for top survivors in current hotspots (`src/bin/voiceterm/config/*`, `src/bin/voiceterm/hud/*`, `src/bin/voiceterm/input/mouse.rs`) and any new top offenders.
  - [ ] Ensure shard jobs always publish outcomes artifacts even when mutants survive.
  - [ ] Re-run mutation workflow until aggregate score holds at or above `0.80` on `master` for two consecutive runs (manual + scheduled).
  - [ ] Keep non-mutation quality gates green after each hardening batch (`python3 dev/scripts/devctl.py check --profile ci`, `Security Guard`).
- MP-015 acceptance gates:
  1. `.github/workflows/mutation-testing.yml` passes on `master` with threshold `0.80`.
  2. Aggregated score gate passes via `python3 dev/scripts/checks/check_mutation_score.py --glob "mutation-shards/**/shard-*-outcomes.json" --threshold 0.80`.
  3. Shard outcomes artifacts are present for all 8 shards in each validation run.
  4. Added hardening tests remain stable across two consecutive mutation workflow runs.

## Phase 4 - Advanced Expansion

- [ ] MP-092 Streaming STT and partial transcript overlay.
- [ ] MP-093 tmux/neovim integration track.
- [ ] MP-094 Accessibility suite (fatigue hints, quiet mode, screen-reader compatibility).
- [ ] MP-095 Custom vocabulary learning and correction persistence.

## Backlog (Not Scheduled)

- [ ] MP-016 Stress test heavy I/O for bounded-memory behavior.
- [ ] MP-031 Add PTY health monitoring for hung process detection.
- [ ] MP-032 Add retry logic for transient audio device failures.
- [ ] MP-033 Add benchmarks to CI for latency regression detection.
- [ ] MP-034 Add mic-meter hotkey for calibration.
- [ ] MP-037 Consider configurable PTY output channel capacity.
- [ ] MP-145 Eliminate startup cursor/ANSI escape artifacts shown in Cursor (Codex and Claude backends), with focus on the splash-screen teardown to VoiceTerm HUD handoff window where artifacts appear before full load. (in progress: writer pre-clear is now constrained to JetBrains terminals to reduce Cursor typing-time HUD flash while preserving JetBrains scroll-ghost mitigation.)
- [x] MP-146 Improve controls-row bracket styling so `[` `]` tokens track active theme colors and selected states use stronger contrast/readability (especially for arrow-mode focus visibility) (landed controls-row bracket tint routing so unfocused pills inherit active button highlight colors instead of always dim brackets, plus focused button emphasis via bold+info-bracket rendering for stronger keyboard focus visibility; covered by `status_line::buttons` regressions `format_button_brackets_track_highlight_color_when_unfocused`, `focused_button_uses_info_brackets_with_bold_emphasis`, and existing focus-bracket parity tests).
- [x] MP-147 Fix Cursor-only mouse-mode scroll conflict: with mouse mode ON, chat/conversation scroll should still work in Cursor for both Codex and Claude backends; preserve current JetBrains behavior (works today in PyCharm/JetBrains), keep architecture/change scope explicitly Cursor-specific, and require JetBrains non-regression validation so the Cursor fix does not break JetBrains scrolling. (landed Cursor-specific scroll-safe mouse handling in writer mouse control: Cursor keeps wheel scrollback available while settings can remain `Mouse: ON - scroll preserved in Cursor`, while JetBrains and other terminals retain existing mouse behavior.) Regression note (2026-02-25): users still report Cursor touchpad/wheel scrolling failing while `Mouse` is ON, with scrollbar drag still working; follow-up tracked in `MP-344`.
- [ ] MP-227 Explore low-noise progress-animation polish for task/status rows (inspired by Claude-style subtle shimmer/accent transitions during active thinking), including optional tiny accent pulses/color sweeps with strict readability/contrast bounds and no distraction under sustained usage; keep as post-priority visual refinement (not current execution scope).
- [x] MP-153 Add a CI docs-governance lane that runs `python3 dev/scripts/devctl.py docs-check --user-facing --strict` for user-facing behavior/doc changes so documentation drift fails early (completed via MP-302 docs-policy lane hardening in `.github/workflows/tooling_control_plane.yml`).
- [ ] MP-154 Add a governance consistency check for active docs + macro packs so removed workflows/scripts are not referenced in non-archive content.
- [ ] MP-155 Add a single pre-release verification command/profile that aggregates CI checks, mutation threshold, docs-governance checks, and hygiene into one machine-readable report artifact.
- [ ] MP-322 Investigate and fix wake-word + send intent "nothing to send" false negative: when using `Hey Claude, send` or `Hey Codex, send` voice commands, VoiceTerm sometimes reports "Nothing to send" even though there is staged text in the PTY input buffer; reproduce with both Claude and Codex backends, capture transcript decision traces (`voiceterm --logs --log-content`), verify send-intent detection timing relative to transcript staging, add targeted matcher/integration tests for the wake-tail send flow, and ensure the send intent checks for staged PTY content (not just VoiceTerm internal staged text state). Physical testing required alongside automated coverage.
- [ ] MP-323 Restore keyboard left/right caret navigation while editing staged text: currently Left/Right (and equivalent arrow-key paths) are captured by tab/button focus navigation instead of moving the text cursor inside the transcript/input field, which blocks correction of Whisper transcription mistakes before submit. Reproduce in active VoiceTerm sessions with staged text, route Left/Right to caret movement whenever text input/edit mode is active, preserve existing tab/control navigation when text edit mode is not active, and add focused keyboard/mouse regression coverage to prevent future text-edit lockouts. (2026-02-27 input-path hardening landed for related navigation regressions: shared arrow parser now accepts colon-parameterized CSI forms used by keyboard-enhancement modes, preventing settings/theme/overlay arrow-navigation dropouts after backend prompt-state transitions. 2026-03-02 field report follow-up: Codex and Claude sessions still show split ownership where arrow keys route either to terminal caret or HUD buttons based on `insert_pending_send`, and users recover by pressing `Ctrl+T`/other hotkeys; scope now includes a deterministic input-ownership model with explicit HUD-focus entry/exit semantics so caret editing and HUD button access remain available without mode confusion. 2026-03-05 backlog clarification: preserve explicit up/down focus handoff between chat region and overlay controls so Left/Right operates on the active surface only; defer this fix until post-next-release unless it becomes a release blocker.)
- [ ] MP-324 Finalize Ralph loop rollout evidence on default branch: after the workflow lands on the default branch, run one `workflow_dispatch` `CodeRabbit Ralph Loop` execution on `develop` (`execution_mode=report-only`) and confirm `check_coderabbit_ralph_gate.py --branch develop` resolves by workflow-run evidence rather than fallback logic; capture run URL and gate output in tooling handoff notes so release gating assumptions are explicit for all agents.
- [x] MP-325 Harden Ralph loop source-run correlation: pin `triage-loop` execution to authoritative source run id/sha when launched from `workflow_run`, fail safely on source mismatch, and preserve manual-dispatch fallback behavior (landed `--source-run-id/--source-run-sha/--source-event` parser+command+core wiring, source-run attempt pinning, run/artifact SHA mismatch detection with explicit `source_run_sha_mismatch` reason codes, and workflow source-run id/sha forwarding in `.github/workflows/coderabbit_ralph_loop.yml`).
- [x] MP-326 Implement real `summary-and-comment` notify semantics for `triage-loop`: add comment-target resolution (`auto|pr|commit`), idempotent marker updates, and workflow permission hardening so comment mode is deterministic and non-spammy (landed comment target flags, PR/commit target resolver, marker-based upsert behavior via GitHub API, and workflow permission updates including `pull-requests: write` + `issues: write`).
- [x] MP-327 Add bounded mutation remediation command surface (`devctl mutation-loop`) with report-only default, scored hotspot outputs, freshness checks, and optional policy-gated fix attempts (landed `dev/scripts/devctl/commands/mutation_loop.py`, `mutation_loop_parser.py`, `mutation_ralph_loop_core.py`, bundle/playbook outputs, and targeted unit coverage).
- [x] MP-328 Add `.github/workflows/mutation_ralph_loop.yml` orchestration: mutation-loop mode controls, bounded retry parameters, artifact bundling, and optional notify surfaces with default non-blocking behavior (landed workflow_run + workflow_dispatch wiring, mode/threshold/notify/comment inputs, summary output, and artifact upload).
- [x] MP-329 Add mutation auto-fix command policy gate: enforce allowlisted commands/prefixes, explicit reason codes on deny paths, and auditable action traces for each attempt (landed `control_plane_policy.json` baseline, `AUTONOMY_MODE` + branch allowlist + command-prefix gating, and policy-deny reason surfacing in mutation loop reports).
- [ ] MP-330 Scaffold Rust containerized mobile control-plane service (`voiceterm-control`) with read-only health/loop/ci/mutation endpoints and constrained workflow-dispatch controls.
- [ ] MP-331 Add phone adapter track (SMS-first pilot + push/chat follow-up) with policy-gated action routing, webhook auth, response/audit persistence, and bounded remote-operation scope. (partial: `devctl autonomy-loop` now emits phone-ready status snapshots under `dev/reports/autonomy/queue/phone/latest.{json,md}` including terminal trace, draft text, and source run context for read-first mobile surfaces; `devctl phone-status` now provides SSH/iPhone-safe projection views (`full|compact|trace|actions`) with optional projection bundle emission for controller-state files; `devctl controller-action` now provides a guarded safe subset (`refresh-status`, `dispatch-report-only`, `pause-loop`, `resume-loop`) with allowlist/kill-switch policy checks and auditable outputs; `app/ios/VoiceTermMobileApp` is now the runnable first-party iPhone shell, `app/ios/VoiceTermMobile` is the shared core package it imports, the app now exposes a short tutorial + live-bundle-first startup path, `devctl mobile-app` now supports a real simulator demo, a live-review simulator mode, and physical-device wizard/install actions, and the mobile bundle now surfaces typed Ralph/controller action previews through the shared backend contract. Remaining scope is the real live adapter: connect the iPhone to the Mac-hosted Rust control service on the same network first, add typed approve/deny plus operator-note/message actions, provider-aware continue/retask flows, and staged phone voice-to-action input, then add a secure off-LAN/cellular path with reconnect/resume semantics so the phone can rejoin long-running plans already active on the home machine without opening raw PTY/devctl ports to the public internet.)
- [ ] MP-332 Add autonomy guardrails and traceability controls (`control_plane_policy.json`, replay protection, mode kill-switch, branch-protection-aware action rejection, duplicate/stale run suppression). (partial: `control_plane_policy.json` added, `AUTONOMY_MODE` + branch/prefix policy gate wired for both mutation and triage fix modes, triage loop now emits dedicated review-escalation comment upserts when retries exhaust unresolved backlog, marker-based duplicate comment suppression landed, `devctl check --profile release` now enforces strict remote release gates (`status --ci --require-ci` + CI-mode CodeRabbit/Ralph checks), bounded controller surfaces now ship via `devctl autonomy-loop` + `.github/workflows/autonomy_controller.yml` with run-scoped checkpoint packet queue artifacts, and scheduled autonomy/watchdog/mutation-loop workflow-run behavior is now mode-gated so background loops are opt-in instead of default red-noise; replay protection + deeper branch-protection/merge-queue enforcement remain pending.)
- [x] MP-333 Enforce active execution-plan traceability governance: non-trivial agent work must be anchored to a `dev/active/*.md` execution-plan doc (with checklist/progress/audit sections), and tooling guardrails must fail when contract markers/required sections drift (landed enforcement updates in `check_active_plan_sync.py` for required execution-plan docs + marker + required sections, plus AGENTS contract references).
- [x] MP-334 Add external-repo federation bridge for reusable autonomy components: pin `code-link-ide` + `ci-cd-hub` in `integrations/`, provide one-command sync path, and document governed selective-import workflow for this repo template path. (landed submodule links + shell helper + `devctl integrations-sync`/`integrations-import` command surfaces, policy allowlists in `control_plane_policy.json` (`integration_federation`), destination-root guards, and JSONL audit logging for sync/import actions.)
- [ ] MP-335 Fix wake word send intent not triggering in auto mode: when VoiceTerm is in auto-listen mode and actively listening, saying "Hey Codex send" (or "Hey Claude send") does not trigger the send action — the wake word is effectively ignored while the mic is already open. Expected behavior: the wake-word detector should remain active during auto-mode listening so that saying the send wake phrase finalizes and submits the current transcript. Distinct from MP-322 (which covers "nothing to send" false negatives when the wake word does fire); this issue is that the wake word never fires at all in auto mode. Reproduce by enabling auto mode, speaking a transcript, then saying "Hey Codex send" without pausing — observe that the message is not sent. Physical testing required.
- [ ] MP-336 Add `network-monitor-tui` to the external federation + dev-mode bridge scope: link a pinned `integrations/network-monitor-tui` source, define allowlisted import profile(s) for throughput/latency sampler primitives, expose a read-only metrics surface for `--dev` + phone status views without introducing remote-control side effects, and add isolated runtime mode flags (`--monitor` and/or `--mode monitor`) so monitor/tooling startup does not interfere with the default Whisper voice-overlay path. The future monitor entry path should open the same Rust operator cockpit used by `--dev`, not a second forked console.
- [x] MP-337 Add repeat-to-automate governance and baseline scientific audit program: require repeated manual work to become guarded automation or explicit debt, add tracked `dev/audits/` runbook/register/schema artifacts, ship analyzer tooling (`dev/scripts/audits/audit_metrics.py`) that quantifies script-only vs AI-assisted vs manual execution share with optional chart outputs, and auto-emit per-command `devctl` audit events (`dev/reports/audits/devctl_events.jsonl`) for continuous trend data.
- [ ] MP-338 Stand up a loop-output-to-chat coordination lane: maintain a dedicated runbook for loop suggestion handoff (`dev/active/loop_chat_bridge.md`), define dry-run/live-run evidence capture, and keep operator decisions/next actions append-only so loop guidance can be promoted safely into autonomous execution. (partial: added `devctl autonomy-report` dated digest bundles, upgraded `devctl autonomy-swarm` to one-command execution with default post-audit digest + reserved `AGENT-REVIEW` lane for live runs, added `devctl swarm_run` for guarded plan-scoped swarm + governance + plan-evidence append, added bounded continuous cycle support via `--continuous/--continuous-max-cycles` so runs keep advancing unchecked checklist items until `plan_complete`, `max_cycles_reached`, or `cycle_failed`, wired workflow-dispatch lane `.github/workflows/autonomy_run.yml`, and added `devctl autonomy-benchmark` matrix reports for plan-scoped swarm-size/tactic tradeoff evidence.)
- [ ] MP-340 Deliver one-system operator surfaces + deterministic autonomy learning: keep Rust overlay as runtime primary, keep iPhone/SSH surfaces over one `controller_state` contract, and implement artifact-driven playbook learning (fingerprints, confidence, promotion/decay gates) so repeated loop tasks are reused safely with auditable evidence. This umbrella scope also owns the cross-plan contract that keeps Memory Studio (`MP-230..MP-255`), the review channel (`MP-355`), and controller surfaces on one shared event/header model, one provider-aware handoff path, and one future unified timeline/replay view rather than three parallel side channels. Current direction: grow the existing Rust Dev panel into a staged operator cockpit (`Control`, `Ops`, `Review`, `Actions`, `Handoff`, plus developer-oriented Git/GitHub/CI/script/memory views), then let `--monitor` reuse that same cockpit as a dedicated startup path. The first `Ops` slice is the Rust-first lane for host-process hygiene, triage summaries, and later external monitor adapters, so those readouts stay in the typed control surface instead of Theme Studio or a parallel ad hoc UI. Buttons may emit high-level intents and AI may resolve those intents to the correct approved playbook, but execution must still route through one typed action catalog plus shared policy/approval/waiver model rather than bypassing safety with raw shell/API execution. MP-340 now also explicitly carries an overlay-native live guard-watchdog direction: the overlay may observe Codex/Claude PTY traffic, session-tail artifacts, repo diffs, and typed review/controller packets to infer what the agent is doing and trigger the matching repo guard family, but guard enforcement must stay typed, policy-gated, debounced, and auditable through `devctl` / controller actions rather than raw terminal injection. The watchdog is now also required to prove impact scientifically: capture matched before/after guarded coding episodes, use paired analysis by task, report effect sizes with confidence intervals plus practical-significance thresholds, and only then promote claims that the guards materially improve Codex/Claude output; the MP-340 analytics layer must also capture repo-owned speed/latency/churn/retry/collaboration metrics from terminal and guard episodes so the project can study time-to-green, guard-hit heatmaps, provider deltas, and other operational signals with a real dashboard instead of anecdotes. Later ML work is allowed, but only as a second-phase ranking/prediction layer over that same artifact corpus after deterministic learning and offline evaluation are already working. Current `phone-status` / `controller-action` payloads and Rust Dev-panel snapshot builders are still interim projections; `devctl mobile-status` is now the first merged SSH-safe phone shim that combines review + controller state, `app/ios/VoiceTermMobile` is the shared first-party core package over that payload, and `app/ios/VoiceTermMobileApp` is the runnable iPhone/iPad app shell over the same emitted mobile bundle with guided simulator demo plus live-review proving modes and typed Ralph/controller action previews, but true MP-340 convergence still only happens once Rust, phone, review, and memory all read one emitted `controller_state` projection set with parity tests and provider-aware memory pack attachments. The mobile end-state is no longer just read-first bundle import: the Mac-hosted Rust control service must become the shared live source for overlay/dev/phone clients, the iPhone must gain typed approvals and structured operator-note/message dispatch plus staged voice-to-action flows, and the same host state must remain reachable over both local Wi-Fi and a secure off-LAN/cellular adapter with reconnect/resume semantics so ongoing plans continue on the home machine without exposing raw PTY or freeform shell access publicly. Immediate follow-up is now explicit: prove a simple phone ping/alert path first, then close richer iPhone parity over the same backend with split/combined terminal-style lane mirrors, typed approvals/notes/instructions, plan-to-agent assignment, simple/technical modes, provider-aware continue/retask routing, and reconnect/resume behavior. PyQt6 today, iPhone now, and any future Electron/Tauri shell later are clients of that shared backend only; none of them become the backend. Execution profiles should be explicit: `Guarded` by default, `AI-assisted Guarded` when the planner picks from the approved catalog, and a visible dev-only `Unsafe Direct` mode for local bypasses that stays red, noisy, and auditable rather than hidden. (2026-02-26 reset: retired the optional `app/pyside6` desktop command-center scaffold to keep operator execution Rust-first; all active scope now routes through Rust Dev panel + `devctl phone-status` + policy-gated `controller-action`. 2026-02-26 federation follow-up: completed fit-gap audit and added narrow import profiles for targeted `code-link-ide`/`ci-cd-hub` reuse instead of broad tree imports.)
- [ ] MP-341 Runtime architecture hardening pass for product-grade boundaries: tighten `rust/src/lib.rs` public surface (remove legacy re-export drift and prefer internal/facade boundaries), replace stringly `VoiceJobMessage::Error(String)` with typed error categories at subsystem boundaries, harden command parsing (`CustomBackend` quoting-safe parsing), reduce global-side-effect risk in Whisper stderr suppression path, and modernize PyPI launcher distribution flow away from clone+local-build bootstrap toward verified binary delivery. (partial 2026-02-25: hardened SIGWINCH registration via `sigaction` + `SA_RESTART`, removed production `unreachable!()` fallback in Theme Studio non-home renderer path, and reduced silent PTY-output drop risk with explicit unexpected-branch diagnostics.)
- [ ] MP-342 Increase push-to-talk startup grace by about 1 second to prevent early cutoff when users do not speak immediately after pressing PTT: currently first-press captures can end too quickly if there is a short delay before speech starts. Reproduce in Codex/Claude sessions, tune initial-silence/warmup handling for natural speech onset, add regression coverage for delayed speech starts, and verify no regressions for intentional short taps.
- [ ] MP-343 Stabilize screenshot button reliability: screenshot capture currently succeeds intermittently and can stop unexpectedly after some successful attempts. Reproduce repeated capture attempts in active sessions, harden button-triggered capture lifecycle/error handling, add regression coverage for repeated runs, and verify physical behavior with screenshot evidence.
- [ ] MP-344 Re-investigate Cursor mouse-mode scroll behavior and restore reliable wheel/touchpad scrolling when `Mouse` is ON: current reports indicate wheel/touchpad scrolling does not move chat history in Cursor while the draggable scrollbar still works. Document and preserve current workaround (`Mouse` ON + drag scrollbar, or set `Mouse` OFF for touchpad/wheel scrolling and use keyboard button focus with `Enter`), reproduce on Codex/Claude sessions, harden input-mode handling, and add regression coverage for Cursor-specific scroll paths. Scientific baseline seeded on 2026-02-25 via `devctl autonomy-benchmark` run `mp342-344-baseline-matrix-20260225` (covers `MP-342/MP-343/MP-344`; artifacts under `dev/reports/autonomy/benchmarks/mp342-344-baseline-matrix-20260225/`); live control-vs-swarm A/B run captured via `mp342-344-live-baseline-matrix-20260225` plus graph bundle `dev/reports/autonomy/experiments/mp342-344-swarm-vs-solo-20260225/`. 2026-03-05 backlog clarification: keep this scoped as post-next-release work unless it becomes a release blocker.
- [x] MP-345 Stand up a visible `data_science` telemetry workspace and continuous devctl metrics refresh so every devctl command contributes to long-run productivity/agent-sizing research: landed `data_science/README.md` workspace docs, new `devctl data-science` command (`summary.{md,json}` + SVG charts), automatic post-command refresh hook in `dev/scripts/devctl/cli.py` (disable with `DEVCTL_DATA_SCIENCE_DISABLE=1`), and weighted agent recommendation scoring from swarm/benchmark history (`success`, `tasks/min`, `tasks/agent`) under `dev/reports/data_science/latest/`; docs/history updated in `AGENTS.md`, `dev/scripts/README.md`, `dev/DEVCTL_AUTOGUIDE.md`, and `dev/history/ENGINEERING_EVOLUTION.md`.
- [x] MP-346 Execute IDE/provider modularization and compatibility hardening so host-specific behavior (`cursor`, `jetbrains`, `other`) and provider-specific behavior (`codex`, `claude`, `gemini`) are isolated behind explicit adapters, validated by matrix tests, and protected by God-file/code-shape/tooling governance gates (`dev/active/ide_provider_modularization.md`). (2026-03-02 docs scope: published explicit user-facing IDE compatibility matrix in README/USAGE with aligned links in QUICK_START + guides so only verified hosts are advertised as supported. 2026-03-02 audit triage scope added: dependency-policy gate hardening, guard-script coverage closure, adapter-contract completion inventory, and cross-plan shared-file ownership gates. 2026-03-02 exhaustive audit intake triage added: Dependabot/CODEOWNERS path-contract repair, active-plan sync required-row expansion, failure-triage watchlist coverage, current `bytes` RustSec remediation decision, Gemini/docs wording parity, plus CI baseline hardening gaps (MSRV/feature-matrix/macOS runtime lane + `cargo doc` gate) and governance tracker drift fixes. 2026-03-02 seventh-pass audit scope added: explicit host/runtime policy mapping for rolling detector + output redraw and 3 additional RuntimeProfile cross-product decisions, plus check-script signal hardening (`check_rust_audit_patterns`, `check_release_version_parity`, stale code-shape override detection). 2026-03-02 post-review blocker cleanup landed: `check_active_plan_sync.py` shape-budget recovery, `check_ide_provider_isolation.py` docs inventory registration, dedicated `check_agents_contract.py` test coverage, refreshed path-audit aggregate reporting, Gemini backend wording parity across user/developer docs, a new `cargo doc --workspace --no-deps --all-features` gate in `rust_ci.yml`, and explicit `cargo deny` enforcement in security/release workflow lanes. 2026-03-02 dependency-policy remediation closure landed: transitive `bytes` moved to `1.11.1`, `rust/deny.toml` now documents crate-scoped license exceptions for current runtime dependencies plus explicit `RUSTSEC-2024-0436` (`paste`) ignore rationale, and local `cargo deny` gate rerun passes. 2026-03-02 phase-0 governance/tooling follow-up landed: Rust CI now includes explicit MSRV/feature-matrix/macOS runtime validation, failure triage initially expanded for broad watch coverage, `check_code_shape.py` enforces stale override review-window checks, tracker drift was resolved (`MASTER_PLAN` board + local backlog ID deconfliction), and cross-plan shared-hotspot ownership/freeze gates are now mandatory in the runbook + board policy. 2026-03-04 phase-1 incremental cleanup slice landed: status-line JetBrains+Claude single-line fallback routing now consumes canonical `runtime_compat` helper and writer render host detection now maps through canonical `detect_terminal_host()` ownership instead of duplicate local host sniffing logic. 2026-03-04 additional phase-1 host-enum unification landed: writer render/state paths now use canonical `TerminalHost` directly (removed `writer/render.rs` `TerminalFamily` enum and replaced state-side `TerminalFamily` references), with writer-focused plus full `cargo test --bin voiceterm` coverage rerun. 2026-03-04 CI signal hardening follow-up landed: failure-triage scope narrowed to high-signal failure conclusions, release publishers now wait for same-SHA CodeRabbit/Ralph + `Release Preflight` gates, and scheduled autonomy/watchdog/mutation-loop workflow-run behavior now defaults to opt-in mode controls to reduce non-actionable red runs. 2026-03-04 additional phase-1 host-routing cleanup landed for banner/color/theme paths: banner skip policy now routes through canonical `runtime_compat::is_jetbrains_terminal`, color truecolor inference now uses canonical `runtime_compat::detect_terminal_host` for JetBrains/Cursor signals, and `theme/detect.rs` Warp fallback now respects canonical host precedence with dedicated regression coverage. 2026-03-04 final phase-1 host-routing slice landed in `theme/texture_profile.rs`: Cursor/JetBrains identity now routes through canonical `runtime_compat::detect_terminal_host`, local parsing is limited to non-host capability IDs, and regression coverage now asserts host precedence plus Kitty/iTerm fallback markers. 2026-03-04 canonical host-cache contract slice landed: runtime host detection now owns `OnceLock<TerminalHost>` caching in `runtime_compat`, thread-local test override/reset coverage validates deterministic host injection, and writer render no longer duplicates host caching. 2026-03-04 host-cache panic-path hardening landed: `runtime_compat` test override scoping now restores prior thread-local host values via drop guard on unwind, with dedicated panic regression coverage. 2026-03-04 Phase-1.5 shared-helper extraction landed: duplicated HUD debug env parsing/preview helpers were removed from `writer/state.rs`, `event_loop/prompt_occlusion.rs`, and `terminal.rs` and replaced with a shared `hud_debug` module, with full `cargo test --bin voiceterm` rerun green. 2026-03-04 additional Phase-1.5 backend-detection cleanup landed: writer-state backend checks now route through canonical `runtime_compat::backend_family_from_env()` + `BackendFamily` enum matching instead of raw backend-label substring parsing, with full runtime suite rerun green. 2026-03-04 provider-contract scaffolding slice landed: new `provider_adapter` signature module defines `ProviderAdapter`/`PromptDetectionStrategy` and provider-policy enums/config so Phase-2+ extraction can target stable trait contracts; CI profile rerun is green after adding signature-only scaffolding. 2026-03-04 Phase-1.5 closure slice landed: ANSI stripping now routes through shared `ansi` utility, env-var locking in runtime tests now routes through shared `test_env` helper instead of duplicated per-module locks, and `claude_prompt_suppressed` was renamed to `prompt_suppressed` across runtime/test code with full runtime+bundle validation green. 2026-03-04 Phase-2a data-only host timing extraction landed: `runtime_compat::HostTimingConfig` now owns host timing values keyed by `TerminalHost`, and writer timing call sites route through config lookups while preserving characterization behavior and passing full runtime + bundle validation. 2026-03-04 Phase-2b preclear policy extraction landed: writer preclear decisioning now routes through typed `PreclearPolicy` + `PreclearOutcome` so preclear decision and post-preclear flag effects are centralized while preserving existing host/provider behavior and full runtime + bundle validation remained green. 2026-03-04 Phase-2c redraw policy extraction landed: writer output redraw decisioning now routes through typed `RedrawPolicy` + `RedrawPolicyContext` consuming `PreclearOutcome`, so scroll/non-scroll/destructive-clear redraw outcomes are centralized while preserving existing host/provider behavior and full runtime + bundle validation remained green. 2026-03-04 Phase-2d idle-gating timing extraction landed: `maybe_redraw_status` idle/quiet-window/repair-settle gating now routes through typed `IdleRedrawTimingContext` + `resolve_idle_redraw_timing` in `writer/timing.rs`, with full runtime + bundle validation remaining green. 2026-03-04 Phase-2e message-dispatch + runtime-profile extraction closure landed: WriterState now resolves and injects a typed RuntimeProfile at construction, handle_message is dispatch-only, and PTY handling routes through explicit preclear/redraw policy pipeline helpers plus state-update application helpers, and completed the writer-state decomposition target (`writer/state.rs` now 448 lines across dedicated `state/*` modules), so Step 2f is the next scope. 2026-03-04 post-closure governance audit added immediate Step-2f tightening scope: new Step 2f.1 (allowlist burn-down + shape-budget reset), Step 2f.2 (function-size guardrails for dispatcher/pipeline hotspots), and explicit Phase-4 compatibility-governance kickoff (`ide_provider_matrix.yaml`, `check_compat_matrix.py`, `compat_matrix_smoke.py`, `devctl compat-matrix`) directly after Step-2f closure. 2026-03-04 CP-013 closure landed: Step 2f/2f.1/2f.2 are now implemented with blocking isolation defaults, narrowed explicit allowlists, tightened shape budgets, function guardrails with owner/expiry exceptions, and the Phase-4 compatibility governance scaffold is active. 2026-03-04 post-CP-013 hardening slice landed: isolation scanner now catches host-enum + provider-backend helper coupling patterns without broad helper-name false positives, runtime mixed-condition callsites in writer render/dispatch/redraw were rerouted through runtime-profile and canonical compatibility helpers, prompt hotspots were reduced under hard limits (`prompt_occlusion.rs` 1143 and `claude_prompt_detect.rs` 623 via test-module extraction), and lint-debt guard now detects inner `#![allow(...)]` attributes with dedicated regression coverage. 2026-03-04 Phase-3a prompt strategy wiring landed: prompt detector construction now routes through provider adapters with Claude-owned strategy ownership plus temporary legacy-shim parity fallback; CI/runtime/docs governance bundle remains green. 2026-03-04 checkpoint/state sync: `CP-016` docs/state continuation sync is in progress; Step `3a.1` (legacy-shim retirement) is closed, Step `3c` is closed, Step `3b` is now closed (Steps `3e` and `3f` are closed), and Phase-5/Phase-6 closure gates (AntiGravity decision + ADR lock) remain pending. 2026-03-05 Phase-5 defer decision: AntiGravity moved to deferred scope until runtime host fingerprint evidence exists; active MP-346 host matrix scope is now `cursor`/`jetbrains`/`other`. 2026-03-05 Phase-6 governance closure landed: ADR `0035` and ADR `0036` are accepted and indexed, leaving IDE-first `CP-016` manual matrix closure (`4/4`) complete for release scope, with deferred `other`/`gemini` validation tracked as post-next-release backlog. 2026-03-04 additional CP-016 hardening landed: IPC lifecycle routing now delegates through a dedicated provider lifecycle adapter module and isolation guardrails now enforce file-scope coupling detection with explicit temporary allowlist debt for Step-3b hotspot files.)
- [ ] MP-347 Add an execution router for pre-push checks and tighten dead-code debt governance across Rust runtime/tooling paths. (2026-03-05 PR-1 landed: added `devctl check --profile fast` as a compatibility alias of `quick` and updated command/docs surfaces. 2026-03-05 PR-2 landed: added `devctl check-router` with changed-path lane selection (`docs`, `runtime`, `tooling`, `release`), strict unknown-path escalation to tooling lane, risk-add-on detection from AGENTS risk-matrix signals, and optional `--execute` mode that runs routed bundle commands. 2026-03-05 dead-code governance slice landed: `check_rust_lint_debt.py` now inventories dead-code allows and supports policy flags (`--report-dead-code`, `--fail-on-undocumented-dead-code`, `--fail-on-any-dead-code`), AI guard runs now include dead-code reporting, and all current runtime dead-code allow attributes carry explicit rationale metadata. 2026-03-05 PR-3 landed: command bundles moved into canonical `dev/scripts/devctl/bundle_registry.py`; `check-router` and `check_bundle_workflow_parity.py` now consume registry commands and AGENTS bundle blocks are rendered/reference-only. 2026-03-05 PR-4 landed: heavy-check placement formalized in maintainer docs (`prepush`/`release`/CI remain strict; `fast`/`quick` stay local-only minimal lanes). 2026-03-05 PR-5 landed: AGENTS rendered bundle docs are now auto-validated/regenerable via `check_agents_bundle_render.py` and strict-tooling docs gate wiring. 2026-03-05 post-implementation architecture audit reopened remaining scope: current `check_code_shape.py` merge-blockers (`check_router.py` and `docs_check_support.py` growth), router/docs-governance taxonomy duplication, risk-add-on SSOT drift risk, and missing `jscpd` report evidence in `check_duplication_audit.py` must be resolved before re-closing this MP. 2026-03-05 phase-1 closure cleanup landed: shape blockers are resolved via check-router/docs-check decomposition, `check_duplication_audit.py` now emits explicit `status`/`blocked_by_tooling` evidence fields plus an explicit constrained-environment fallback (`--run-python-fallback`) while preserving `jscpd` as primary, canonical `jscpd` report evidence is refreshed (`dev/reports/duplication/jscpd-report.json`), and the closure non-regression command pack is green; remaining MP-347 follow-up is taxonomy/SSOT hardening. 2026-03-05 verification refresh: canonical helper ownership for duplication audit is now stable (`check_duplication_audit_support.py`), stale archive literals were removed from active docs/changelog, and the row `2331` non-regression pack rerun remains fully green. 2026-03-06 docs-IA intake update: Round 4 developer-information-architecture + active-directory hygiene audit is now tracked in `dev/active/pre_release_architecture_audit.md` (Phase 15) and remains open pending migration implementation. 2026-03-06 docs-index follow-up: reduced duplicate entrypoint drift by making `dev/README.md` the explicit canonical developer index and converting `DEV_INDEX.md` into a thin bridge page. 2026-03-06 guide-path migration follow-up: moved durable maintainer guides to `dev/guides/` with one-cycle bridge files at legacy paths and updated mapped coupling surfaces (`docs_check_policy`, `check_router_constants`, `tooling_control_plane.yml`, AGENTS/README entrypoints, and docs-check/path-rewrite tests). 2026-03-08 maintainer-lint follow-up: add an explicit advisory `pedantic` `devctl check` profile, keep it out of required bundles and release gates, and document it as an opt-in lint-hardening sweep so agents use it intentionally instead of treating pedantic noise as mandatory release work. 2026-03-08 pedantic follow-up: keep pedantic on the existing `report`/`triage` architecture by having `check --profile pedantic` emit structured artifacts under `dev/reports/check/`, `report --pedantic` / `triage --pedantic` consume those artifacts through the shared project snapshot, support explicit inline regeneration via `--pedantic-refresh`, and use `dev/config/clippy/pedantic_policy.json` to record promote/defer/review decisions so AI classification is repo-owned instead of ad hoc per release. 2026-03-08 maintainability/IA follow-up: Phase-15 cleanup remains open for retiring temporary bridge entrypoints like `dev/ARCHITECTURE.md` and `dev/BACKLOG.md`, collapsing duplicate `dev/` entrypoints, and turning AGENTS trimming into a real post-release execution slice instead of a lingering note. 2026-03-09 guard follow-up: `check_rust_security_footguns.py` now also flags `unreachable!()` in hot runtime paths under `rust/src/bin/voiceterm/**`, `rust/src/audio/**`, and `rust/src/ipc/**`, with matching unit coverage, so the pre-push guard set keeps tightening around panic-shaped "should never happen" shortcuts in shipped runtime code.)
- [ ] MP-348 Investigate Codex composer/input-row occlusion after recent Codex CLI updates (reported 2026-03-05): during red/green diff-heavy output, IDE terminal sessions can show the backend input/composer row visually obscured near the HUD boundary. `Post-next-release only`; do not execute before release promotion unless explicitly reclassified as a blocker. Required evidence pack: one screenshot + `voiceterm --logs --codex` trace with terminal host/version, HUD style, terminal `rows/cols`, and overlap timing (`while working` vs `ready for input`). Initial code-audit hypothesis for follow-up validation: `terminal.rs` currently keeps Codex on a fixed v1.0.95 reserved-row budget (no extra safety-gap rows), and prompt-occlusion guard routing is presently Claude-only via `runtime_compat::backend_supports_prompt_occlusion_guard`, so Codex composer/card layout changes may bypass suppression and row-budget safeguards. Add targeted regression tests once logs confirm a deterministic repro.
- [ ] MP-349 Investigate Cursor+Claude plan-mode history/HUD corruption + transient garbled terminal output (reported 2026-03-05): in Cursor terminal sessions, asking Claude to enter plan mode (especially with local/background agents) can cause the visible history region to disappear while HUD/status UI rows render over output; some lines show garbled characters/symbols during the bad state. Repro clue from physical testing: issue clears after terminal resize/readjust, suggesting geometry/redraw synchronization drift. `Post-next-release only`; do not execute before release promotion unless explicitly reclassified as a blocker. Required evidence pack: before/after resize screenshots, terminal host/version, provider/backend, HUD style/mode, terminal `rows/cols` before and after resize, `voiceterm --logs` trace with `VOICETERM_DEBUG_CLAUDE_HUD=1`, and a timestamped sequence (`plan request -> corruption -> resize/readjust -> recovery`). Initial code-audit hypotheses: stale geometry cache, missed full-repaint transition, or prompt/HUD reserved-row mismatch in Cursor non-rolling flow. Add deterministic regression tests after a stable log-backed repro is confirmed.
- [x] MP-350 Keep `devctl` as primary control plane and add optional read-only
  MCP adapter without duplicate enforcement layers: locked release/check/cleanup
  semantics as executable contracts, documented MCP as additive (not a
  replacement), and closed the execution tracker into archive
  (`dev/archive/2026-03-05-devctl-mcp-contract-hardening.md`) while retaining
  durable guidance (`dev/MCP_DEVCTL_ALIGNMENT.md`, `dev/DEVCTL_AUTOGUIDE.md`,
  `dev/scripts/README.md`, `dev/ARCHITECTURE.md`).
- [ ] MP-351 Expand the built-in theme catalog with additional curated VoiceTerm
  themes, wire them through Theme Picker/Theme Studio/export surfaces, keep
  CLI/docs parity, and add snapshot coverage so new themes do not regress
  ANSI/256color fallback behavior.
- [ ] MP-352 Add slash-command control for voice modes so users can switch
  between `PTT`/manual voice, `AUTO`, and idle/listening-off flows without
  relying only on hotkeys; deliver `/voice` as a standalone command inside
  Codex CLI and Claude Code sessions without requiring the full VoiceTerm PTY
  overlay. Architecture audit (2026-03-06) confirmed PTY-based slash-menu
  injection is not viable; implementation path is phased: (A) `--capture-once`
  subprocess mode + markdown skill files for immediate `/voice` availability,
  (B) MCP server in Rust (`voiceterm-mcp`) exposing `voice_capture`,
  `voice_status`, `voice_mode_set` tools for both platforms, (C) Claude Code
  plugin packaging + Codex command file for native slash-menu UX. Execution
  spec: `dev/active/slash_command_standalone.md`. 2026-03-09 status: Phase A
  implementation is landed locally (`--capture-once --format text`, slash
  templates, user docs, targeted capture tests green), while full runtime
  validation remains open because current branch-wide guard/test failures are
  unrelated to the slash-command slice. Require manual validation of
  enable/disable/exit behavior before closure.
- [ ] MP-353 Add a settings toggle for momentary push-to-talk hotkey behavior
  ("hold to talk") so manual voice can run as either the current toggle model
  or a press-and-hold capture mode; wire the preference through Settings plus
  config/CLI surfaces, preserve current behavior by default, and require
  physical hotkey validation before closure.
- [x] MP-354 Execute post-release IDE/provider coupling remediation so the
  writer dispatch/timing/startup paths reduce cross-product blast radius before
  additional runtime feature work continues. Scope is tracked in
  `dev/active/ide_provider_modularization.md` Phase 7 (`Step 7a`-`Step 7f`):
  adapter-owned writer state split, `handle_pty_output` pipeline decomposition,
  redraw timing/policy de-tangling, `main.rs` startup decomposition, shared VAD
  factory ownership, and guard-script dedup follow-up with checkpoint packets.
  2026-03-07 status: `Step 7a`, `Step 7b`, `Step 7c`, `Step 7d`, `Step 7e`,
  and `Step 7f` complete (writer adapter-owned state split +
  `handle_pty_output` staged decomposition + runtime-variant timing/policy
  de-tangling + startup phase decomposition + shared
  `audio::create_vad_engine` ownership + guard bootstrap/helper dedup
  closure); queued follow-up `R8 + R9 + R10`, `R6 + R7 + R11`,
  `R12 + R13 + R18`, and residual low-risk `R14 + R15 + R16 + R17` are now
  complete, and Python residual follow-up `P11 + P12` is now complete as well
  (typed `RuleEvalContext`, `AppConfig::validate` helper split, grouped
  prompt-occlusion output signals, glyph-table style resolution,
  runtime/schema + style-schema macro dedup cleanup, parser control-byte
  dispatch helper extraction, wake-listener join lifecycle dedup, lookup-based
  wake send-intent suffix matching, named legacy UI color constants, typed
  `BannerConfig` ownership, render host-resolution threading cleanup,
  style-pack override state accessor dedup, UTC tooling/check report timestamp
  normalization, and explicit `SECONDS_PER_DAY` age-math constants). MP-354 is
  closed; the doc stays active only because post-next-release `MP-346` backlog
  items remain deferred there. Phase-7 priority queue remains closed.
- [ ] MP-355 Deliver a dedicated shared review-channel + staged shared-screen
  execution slice: extend the MP-340 control-plane direction with one
  review-focused packet/event contract (`review_event` append-only authority +
  `review_state` latest snapshot), standard projections (`json`, `ndjson`,
  `md`, `terminal_packet`), and a flat `devctl review-channel` action surface
  (`post`, `status`, `watch`, `inbox`, `ack`, `history`); render a shared
  VoiceTerm surface where Codex + Claude + operator lanes are visible
  together as one collaborative terminal-native workflow, keep separate
  PTY ownership in the initial phases while packets/staged drafts/peer
  awareness stay visible on that same surface, require Claude-side dual-agent
  repolls to consume direct reviewer packets through `inbox/watch` alongside
  bridge polling when the structured queue is available, add the structured
  `check_review_channel.py` guard plus retention/audit integration in the same
  tranche, and keep `check_review_channel_bridge.py` as the temporary
  markdown-bridge guard while `bridge.md` remains the active projection.
  Defer true concurrent shared-target-session writing until lock/lease,
  ack/apply, and audit guardrails are proven. Phase-0 design closure requires
  explicit reconciliation with MP-340 plus `ADR-0027`/
  `ADR-0028`, a lossless header mapping into Memory Studio's canonical event
  envelope, and one
  `context_pack_refs` contract for `task_pack` / `handoff_pack` /
  `survival_index` attachments. Early phases must emit
  `packet_posted|packet_acked|packet_dismissed|packet_applied` into the memory
  ingest path when capture is active and keep provider-specific attachment
  shaping routed through Memory adapter profiles instead of a review-only pack
  format. Current
  transitional operating mode uses repo-root `bridge.md` as a sanctioned
  temporary projection for the current Codex/Claude swarm, but MP-355 itself
  remains a reusable review/runtime contract slice over the shared backend
  rather than the product boundary.
  Current
  transitional operating mode uses repo-root `bridge.md` as a sanctioned
  coordination-log projection with explicit ownership, poll cadence, current-
  state fields, and `check_review_channel_bridge.py` governance until the
  structured artifact path lands, and the final artifact model must remain
  compatible with memory/handoff compilation. Routed actions requested from the
  review lane must go through the same typed command catalog and shared
  approval/waiver engine used by operator buttons and controller surfaces; no
  review-specific raw shell or raw API bypass is allowed. 2026-03-09 bridge-
  hardening follow-up landed: rollover now rejects
  `--await-ack-seconds <= 0` so fresh-session ACK stays fail-closed, and the
  temporary `check_review_channel_bridge.py` guard now requires live
  `Last Reviewed Scope` plus a non-idle `Current Instruction For Claude`
  section whenever the markdown bridge is active. 2026-03-09 bridge-backed
  status follow-up landed: `devctl review-channel --action status` now writes
  current-latest projections under `dev/reports/review_channel/latest/`
  (`review_state.json`, `compact.json`, `full.json`, `actions.json`,
  `latest.md`, `registry/agents.json`), and rollover ACK detection now
  normalizes markdown list items correctly so live visible ACK lines are
  actually observed. 2026-03-09 launch/freshness follow-up landed: fresh
  conductor bootstrap now fails closed on untracked bridge files, stale
  reviewer polls beyond the five-minute heartbeat contract, and idle/missing
  live next-action state; the bridge liveness model now distinguishes
  `poll_due` vs `stale`, and rollover ACK validation now requires the exact ACK
  line inside the provider-owned bridge section (`Poll Status` for Codex,
  `Claude Ack` for Claude) instead of raw substring matches. 2026-03-09
  workflow-parity follow-up landed: `check_bundle_workflow_parity.py` now
  parses per-job run scopes, requires the tooling bundle sequence to stay in
  `docs-policy`, and requires the operator-console pytest lane to stay in
  `operator-console-tests` so wrong-job or out-of-order regressions fail
  closed instead of passing on command-presence alone. Codex re-review later
  the same day narrowed the bridge-hardening closure: `launch` still does not
  invoke the full bridge guard before bootstrap, freshness enforcement is
  still split between the five-minute heartbeat contract and a looser guard
  threshold, generated rollover prompts still hardcode the default ACK
  timeout instead of threading the selected value end-to-end, and one
  duplicate `test_review_channel.py` name still shadows intended coverage.
  2026-03-22 live-loop follow-up: the current bridge/runtime path still
  collapses continuation-budget pauses into generic `waiting_on_peer` even
  when typed status already reports `attention.status=checkpoint_required` and
  `safe_to_continue_editing=false`; keep MP-355 open until checkpoint-gate
  pauses become a first-class typed wait reason across status/projection/
  bridge surfaces so Codex and Claude can stay synchronized while edits are
  intentionally paused. A later same-lane bounded follow-up also closed the
  adjacent reviewer-side stale-state ambiguity: active-dual-agent attention
  and bridge-poll routing now emit `review_follow_up_required` when Claude has
  changed the live tree under an active reviewer supervisor and
  `reviewed_hash_current=false`, so reviewer follow-up no longer looks like a
  generic done/stale state while Codex still owes a re-review pass. Focused
  review-channel tests (`231`) and `devctl check --profile ci` are green on
  that slice. The next bounded same-lane follow-up is now also in: the
  implementer wait/reporting surface exports typed attention status/summary/
  recommended-action fields and state-specific timeout/wake messages, so the
  loop no longer relies on generic "Holding for Codex review" text when the
  backend already knows it is paused on `review_follow_up_required` or
  `claude_ack_stale`. A later same-lane parity step now does the same on the
  reviewer side: `review-channel --action reviewer-wait` exports typed wait
  attention fields and state-specific wake/timeout/unhealthy messages, and the
  reviewer bootstrap contract now explicitly routes Codex onto that repo-owned
  wait path when parked on Claude progress instead of ad-hoc sleep loops. The
  checkpoint-gate pause projection and the broader repo-owned semantic
  reviewer-worker/service path still remain open.
  Keep MP-355 open until those launch/freshness/ACK/coverage gaps are closed.
  2026-03-09 operator
  validation follow-up confirmed the current dirty-tree behavior: focused
  `test_review_channel` coverage passed (`31` tests), `devctl review-channel
  --action status --terminal none --format md` wrote the latest projection
  bundle successfully, and `launch` / `rollover` dry-runs remain expected-red
  while `bridge.md` and `dev/active/review_channel.md` stay untracked
  bridge files in this checkout. A later 2026-03-09 fail-closed follow-up also
  closed the missing-`Claude Status` / missing-`Claude Ack` launch gap and
  stopped degraded `waiting_on_peer` bridge states from reporting `ok: true`
  or `claude.status == active` in review/mobile projections. A later same-day
  launcher follow-up also writes per-session metadata plus live-flushed
  conductor transcript logs under
  `dev/reports/review_channel/latest/sessions/` so repo-owned desktop shells
  can tail real session output without taking PTY ownership away from
  Terminal.app. Another same-day operator-blocker fix now clears inherited
  `CLAUDECODE` markers inside generated Claude conductor scripts so live
  Terminal-app launches do not fail as nested Claude Code sessions when
  started from an existing Claude-owned shell. A later 2026-03-09 Codex
  re-review also confirmed via focused `test_review_channel` coverage that
  custom `--await-ack-seconds` values are threaded end-to-end, so that older
  suspected ACK-timeout bug is no longer part of MP-355's open blocker set.
  A later same-day live-launch audit also found a new bootstrap honesty gap:
  non-dangerous Codex conductors can spend their first minutes on worker fan-
  out and approval-bound tool prompts before rewriting `Last Codex poll`,
  letting the bridge age into stale even while the session logs are active.
  The launcher prompt now requires Codex to stamp `Last Codex poll`, `Last
  non-audit worktree hash`, and `Poll Status` before fan-out and forbids
  parking silently on unanswered approval prompts without reflecting that
  blocked state in the bridge. A later same-day overlay/runtime follow-up also
  landed the first structured-authority consumer in the Rust shell: the Dev-
  panel Review surface now prefers event-backed review artifacts
  (`projections/latest/full.json`, `state/latest.json`, or legacy
  `latest/*.json` outputs) whenever review-channel event sentinels exist,
  parses those JSON projections into the same `ReviewArtifact` view model used
  by the existing markdown bridge, and falls back to `bridge.md` only when
  structured state is absent. That proves the overlay can move onto canonical
  review state without changing default startup mode. A later same-day
  launcher hardening fix now refuses a second live `review-channel --action
  launch --terminal terminal-app` when the existing repo-owned
  `latest/sessions/` artifacts still look active, so operators cannot
  accidentally open duplicate Codex/Claude conductor windows that race on the
  same session-tail files, but the remaining
  event-backed `watch|inbox|ack|dismiss|apply|history` path is still open. A
  2026-03-13 follow-up also closed the next live-launch honesty gap: the
  Terminal-app launch path now waits for `Last Codex poll` to advance and fails
  closed if a fresh reviewer heartbeat never appears, and the bridge-backed
  `review_state` payload now emits a typed `attention` contract so stale
  reviewer / poll-due / waiting-on-peer state is machine-readable instead of
  living only in warning prose. A same-slice cleanup follow-up extracted that
  attention/launch behavior into `attention.py`, `status_projection.py`, and
  `terminal_app.py` so the live-launch honesty path stays inside the repo's
  shape budget while keeping one typed liveness contract. The next MP-358
  follow-up is now explicit too: the newer `implementer_completion_stall`
  tandem guard must graduate into shared review-channel attention/runtime
  state so the same "Claude parked on review/polling" signal is visible to
  VoiceTerm, PyQt6, phone/mobile, CLI, and generated instruction surfaces
  instead of living only in prompt text plus an on-demand validator. Execution spec:
  `dev/active/review_channel.md`.
- [ ] MP-356 Tighten host-process hygiene automation so local AI/dev runs stop
  relying on manual Activity Monitor checks: add a dedicated host-side
  `devctl process-audit`/`devctl process-cleanup` surface, make the shared
  process sweep descendant-aware for leaked PTY child trees and orphaned-root
  cleanup descendants, update `AGENTS.md`/dev docs so post-test and pre-handoff
  host cleanup/audits are explicit, and close the remaining PTY lifeline
  watchdog leak so `cargo test --bin voiceterm theme` no longer sheds orphaned
  `voiceterm-*` helpers on the host. Follow-up widened the same audit/cleanup
  path to catch orphaned repo-tooling wrapper trees (for example stale
  `zsh -c python3 dev/scripts/...` roots with descendant helpers such as
  `qemu-system-riscv64`), direct shell-script wrappers, repo-runtime
  cargo/target trees from non-`--bin voiceterm` Rust tests, and repo-cwd
  generic helpers (`python3 -m unittest`, `node`/`npm`, `make`/`just`,
  `screen`/`tmux`, `qemu`, `cat`) that outlive their parent tree, while also
  excluding the current audit command's own ancestor tree. Follow-up synthetic
  leak repros tightened strict verification further: freshly detached
  repo-related helpers (`PPID=1`, still younger than the orphan age gate) now
  fail `process-audit --strict` / `process-cleanup --verify` immediately under
  a dedicated `recent_detached` state, and `process-watch` now exits zero once
  it actually recovers to a clean host instead of staying red because earlier
  dirty iterations are preserved in history. `check --profile quick|fast` now
  runs host-side cleanup/verify by default after raw cargo/test-binary
  follow-ups, and routed docs/runtime/tooling/release/post-push bundle
  authority ends with `process-cleanup --verify --format md` so the default
  AI/dev lane re-runs strict host cleanup automatically. Verified 2026-03-08
  with targeted PTY lifecycle tests, process-hygiene unit coverage, `cargo
  test --bin voiceterm theme -- --nocapture`, the required post-run quick
  sweep, strict host `process-audit`, live cleanup/verify of the orphaned
  repo-tooling `zsh -> qemu` tree, and live `process-watch` recovery from fresh
  synthetic repo-runtime + repo-tooling detached-orphan repros. Follow-up
  tracing closed one more live gap on 2026-03-08: banner tests no longer
  deadlock on nested env-lock acquisition, attached interactive helpers are no
  longer reported as stale repo-tooling failures, and AI-operated raw Rust
  tests now have a first-class `devctl guard-run` path that always executes
  the required post-run hygiene follow-up. Execution spec:
  `dev/active/host_process_hygiene.md`. 2026-03-09 Codex re-review reopened
  follow-up hardening: orphaned non-allowlisted repo-cwd descendants can
  still slip once the matched parent exits, tty-attached repo helpers
  (`python3 -m pytest` / `python3 -m unittest`) are still under-classified,
  and `guard-run --cwd <other-repo>` still audits/cleans this repo instead of
  the target cwd. Re-close only after focused regression proof covers those
  shapes.
- [ ] MP-357 Fix Claude/Cursor IDE overlay disappearing on terminal resize and
  when launching VoiceTerm in a terminal with pre-existing scrollback content:
  the HUD/status-line overlay can vanish or fail to render after a window resize
  event, and sessions started in terminals that already contain prior output
  sometimes never show the overlay at all. Reproduce both paths (resize-triggered
  disappearance and dirty-scrollback startup), capture `voiceterm --logs` traces
  with terminal host/version, `rows/cols` before and after resize, and scrollback
  line count at launch. Initial hypotheses: stale geometry cache not refreshed on
  SIGWINCH, or initial row-budget calculation not accounting for existing
  scrollback offset. Add deterministic regression coverage for both triggers
  before closure. `Post-next-release only`; do not execute before release
  promotion unless explicitly reclassified as a blocker.
- [ ] MP-358 Harden the local-first continuous Codex-reviewer / Claude-coder
  loop before any reusable template extraction: keep `MASTER_PLAN` plus the
  relevant active-plan checklist as the canonical queue, require automatic
  next-task promotion while scoped work remains, add peer-liveness/stale-peer
  guardrails so neither side keeps working blindly after the other goes stale,
  require Claude-side wait/repoll behavior to consume direct reviewer packets
  through `review-channel inbox/watch` on the same cadence as bridge polling
  when the structured queue exists,
  modularize and clean up the Python launcher/orchestration path with explicit
  failure-report coverage, rotate both conductor terminals through repo-visible
  handoff state once remaining context drops below 50%, and keep host-process
  hygiene green during relaunch/rotation so stale local test or conductor
  sessions do not accumulate detached repo processes. Only after this loop is
  proven stable on VoiceTerm should the same path be carved into a reusable
  toolkit/template. 2026-03-09 Codex re-review confirmed the report-level
  liveness state machine and fail-closed zero-second ACK rejection. The latest
  launcher slice now also supervises clean provider exits so conductors relaunch
  in-place instead of silently dying after one summary. A follow-up MP-358
  tranche also taught host hygiene/process-audit to keep attached supervised
  review-channel conductors visible without classifying them as stale leaks, and
  landed a typed `review-channel --action promote` path plus derived-next-task
  status projections so queue advancement is no longer ad hoc bridge editing.
  The latest launcher hardening slice also adds a typed
  `--refresh-bridge-heartbeat-if-stale` self-heal path for launch/rollover so
  stale reviewer-heartbeat metadata no longer strands the operator at a dead
  `Last Codex poll` guard failure when the rest of the bridge contract is
  still valid.
  The remaining open gaps are end-to-end auto-promotion proof, the 2-3 minute
  poll / five-minute heartbeat contract, and stale-peer recovery. A
  2026-03-13 follow-up also tightens the proof path: live launch now requires a
  real post-launch reviewer heartbeat instead of counting opened windows as
  success, and the same bridge-backed `review_state` path now emits typed
  stale-peer/reviewer `attention` state that downstream restart/UI surfaces can
  consume without re-deriving the condition ad hoc. The same follow-up now also
  drives Codex/operator lane health plus session stats in the default desktop
  workbench, so the local proof surface goes visibly stale instead of hiding
  the failure only in warnings. 2026-03-15 tandem-consistency guard landed:
  `check_tandem_consistency.py` validates role-profile seam alignment across
  peer-liveness, event-reducer, status-projection, launch, prompt, and handoff
  modules; wired into bundle.tooling, CI workflows, and quality-policy presets.
  A second 2026-03-15 anti-stall hardening pass now blocks the next real loop
  failure shape too: `implementer_completion_stall` fails when Claude-owned
  status/ack text parks on "instruction unchanged / continuing to poll /
  Codex should review" while the current instruction is still active and not in
  an explicit reviewer-owned wait state, and the bridge writer/guard now scrub
  + reject contradictory reviewer-mode prose in `Poll Status`.
  The next closure slice is now explicit too: keep one backend for developers
  and agents, add a repo-owned inactive-mode liveness emitter, expose only
  thin mode toggles/aliases (`agents` / `developer`) over that same contract
  instead of a separate dev-only control plane, and treat this loop as one
  local proof harness over the broader shared backend instead of the product
  boundary itself so future loop work removes or narrows VoiceTerm-embedded
  assumptions rather than deepening them. Latest swarm-topology follow-up
  (2026-03-17): Codex remains the sole conductor and final reviewer, Claude
  may fan out bounded coding workers only behind one Claude conductor without
  self-promoting scope or rewriting reviewer-owned bridge state, and every
  non-trivial slice must keep a separate Codex-side architecture-fit reviewer
  before acceptance so worker fan-out does not turn into a second control
  plane. Execution spec:
  `dev/active/continuous_swarm.md`.
- [ ] MP-359 Deliver a bounded optional PyQt6 VoiceTerm Operator Console for
  the current review-channel workflow: keep Rust as the PTY/runtime owner,
  keep `devctl review-channel` as the launcher/control surface, render Codex +
  Claude + Operator Bridge State side by side from repo-visible artifacts, and
  provide desktop launch/rollover plus operator decision capture without
  introducing a second control plane. Phase 1.5 (information hierarchy)
  landed: structured `KeyValuePanel` + `StatusIndicator` + toolbar dots
  replace text dumps, `widgets.py` extracted, 67 tests passing. Phases 3-8
  roadmap added: Approval Queue Center Stage, Agent Timeline, Guardrails /
  Kill Switch, System Health, Diff Viewer, and Validation. Phase 2.6 now has
  a concrete directory layout plan (`state/`, `views/`, `theme/`) to organize
  modules before more panels land. The Activity tab now exposes card-based
  agent summaries, typed quick actions (`review-channel --dry-run`,
  `status --ci`, `triage --ci`, `process-audit --strict`), selectable
  human-readable report topics, and staged Codex/Claude summary drafts with
  explicit provenance while keeping command execution on the shared repo-owned
  path. The next AI-assist tranche now explicitly includes an opt-in live
  provider-backed `AI Summary` path for the selected report, with bounded
  Codex/Claude execution, explicit provenance, repo-visible diagnostics, and a
  staged-draft fallback when live provider access is unavailable. The next
  operator-control tranche now
  explicitly includes a one-click `Start Swarm` flow plus direct typed yes/no
  and terminal-control buttons once the `review-channel` action surface grows
  beyond `launch|rollover`, plus a first-class CI/CD status + workflow/log
  visibility panel built on the existing `devctl` surfaces, push-linked run
  history, and an allowlisted script/action palette with AI-assisted action
  selection that still resolves to typed repo-owned commands. The same tranche
  has now landed its first operator-visible pieces: `Start Swarm` exposes
  JSON preflight -> live launch chaining with staged
  preflight/launch/running/failure status on Home + Activity, shared busy-state
  wiring, and command previews, and a new `Workbench` layout adds snap presets
  over resizable lane/report/monitor panes. The latest MP-359 follow-up also
  routes `Dry Run`, `Live`, `Start Swarm`, and `Rollover` through the typed
  review-channel stale-heartbeat self-heal path so the desktop shell no longer
  looks inert when the markdown bridge ages out, and now persists the selected
  layout/workbench tab/splitter state to
  `dev/reports/review_channel/operator_console/layout_state.json` so "screen
  got weird" reports stay reproducible. A follow-up in the same lane now adds
  explicit layout reset/export/import controls plus a new Workbench timeline
  surface that synthesizes per-agent/system events from snapshot + rollover
  handoff artifacts while keeping Raw Bridge as a dedicated tab. A further
  same-day Phase-4.5 slice adds shared workflow chrome to Workbench with a top
  strip (slice/goal/current writer/branch/swarm health), Codex/Claude last
  seen/applied markers, and a bottom posted->read->acked->implementing->tests
  ->reviewed->apply transition row with a script-derived next-action footer.
  The same tranche
  now explicitly includes a GUI swarm-planner surface that reuses
  `autonomy-swarm` / `swarm_run` token-aware sizing logic and feedback signals
  instead of inventing a desktop-only heuristic, plus a visible swarm
  efficiency governor that logs the metrics and control decision behind every
  hold/downshift/upshift/freeze/repurpose action. The same MP now also tracks
  a layout-workbench path for snap-aware pane resizing/repositioning plus a
  multi-theme registry meant to converge on Rust overlay theme/style-pack
  semantics instead of becoming a desktop-only styling fork, with explicit
  style-pack import/read parity first and export/write parity only after the
  desktop mapping is proven round-trip-safe. A 2026-03-13 follow-up also closed
  a read-model honesty gap: the PyQt6 snapshot builder now carries forward
  structured review-state warnings/errors/attention instead of only file-load
  failures, so the desktop shell can show the real repo-owned "Codex stale /
  poll due / waiting on peer" state that the review-channel runtime already
  computed. A same-slice follow-up now also maps non-healthy review attention
  into Codex/operator lane health and session stats, which makes the default
  session-first workbench visibly stale instead of burying the problem in the
  warning list alone. The plan now also explicitly
  includes a repo-aware Command Center, built-in `What this does / When to use
  it / Before you run it / What it will execute / Success / Failure` guidance
  surfaces, repo-state workflow modes (`Develop`, `Review`, `Swarm`,
  `CI Triage`, `Release`, `Process Cleanup`, `Docs/Governance`), and an
  integrated `Ask | Stage | Run` AI-help contract so the desktop app can
  answer questions, stage commands or draft artifacts, and execute the same
  typed repo-owned actions through both manual and AI-assisted paths. 2026-03-09 follow-up hardening
  landed: the live app and theme editor now share one stylesheet compositor,
  `bundle.tooling` now runs the operator-console suite in the canonical local
  proof path, and the GUI launcher now uses `sys.executable` instead of a bare
  `python3` shell assumption. The same tranche now also includes a fuller
  left-anchored theme workbench with `Colors` / `Typography` / `Metrics`
  pages, a real preview gallery, and tokenized typography/radius/padding
  styling so the editor can theme more than just raw color swatches.
  The latest workflow-controller hardening follow-up now makes `Run Loop`
  audit `devctl orchestrate-status` before it launches
  `devctl swarm_run --continuous`, and the shared Home/Activity launchpads
  keep the last audit/loop result inline so operators do not have to dig
  through raw launcher text to see whether the selected markdown scope is
  blocked, launching, or complete.
  2026-03-09 theme-authority follow-up landed: `ThemeState` now carries
  optional builtin `theme_id` identity, `ThemeEngine` is the single
  builtin/custom/draft apply authority, the toolbar reflects draft/custom
  state explicitly instead of keeping a parallel builtin-only truth, and
  detail dialogs now use live engine colors. The same bounded fix also
  repaired an accidental Operator Console import break in `views/widgets.py`
  and the local proof path is green aside from the known bridge-guard
  expected-red on untracked `bridge.md` / `dev/active/review_channel.md`.
  A later 2026-03-09 saved-theme compatibility fix hydrated legacy partial
  `_last_theme.json` and custom preset payloads onto the current semantic
  palette before apply, closing the PyQt6 startup crash on missing keys such
  as `toolbar_bg`.
  The first follow-up after that crash also moved the agent-detail diff pane
  off fixed RGB highlight tints and back onto the live theme palette, closing
  one of the remaining hardcoded desktop surfaces called out by MP-359.
  A further same-day continuation split the editor into surface-scoped
  `Surfaces` / `Navigation` / `Workflows` pages and expanded the in-editor
  preview to cover toolbar/header chrome, nav + monitor tabs, approval queue,
  diagnostics/log pane, diff pane, and representative empty/error states so
  the next theme passes can touch more of the real shell without guessing.
  The next bounded parity slice is now landed too: the desktop theme engine
  can read canonical style-pack JSON payloads plus theme-file TOML metadata,
  hydrate only the shared Rust `base_theme` onto the matching builtin desktop
  palette, and surface provenance plus explicit `Not yet mapped` reporting for
  Rust-only fields such as `overrides`, `surfaces`, `components`, and
  non-`meta` theme-file sections. Export/write parity remains intentionally
  open until that broader cross-surface contract is proven stable.
  A follow-up bounded write slice is now in too: the desktop editor can export
  canonical theme-file TOML and minimal style-pack JSON only when the current
  state still maps exactly to a shared builtin `base_theme`, while lossy
  desktop-only edits stay blocked with explicit messaging instead of fake
  canonical files. The same slice split theme state/storage/overlay parity
  helpers out of `theme_engine.py` so the coordinator no longer keeps growing
  into another mixed-responsibility desktop god-file.
  A further bounded cleanup then removed another obvious pocket of desktop-only
  literals: agent-detail diff fallback colors now resolve from the shared
  builtin semantic palette, and the theme-editor color swatch derives its own
  border/hover chrome from the active swatch instead of fixed hardcoded
  accent/border values. The broader remaining work is still the larger
  hardcoded-surface sweep across the rest of the desktop shell.
  The next same-day sweep narrowed that remaining shell work further by
  removing shared stylesheet RGBA literals from menu hover/border and
  scrollbar track chrome. Those values now derive from semantic theme colors
  (`hover_overlay`, `menu_border_subtle`, `scrollbar_track_bg`) materialized
  by the shared palette builder and exposed in the desktop editor, so later
  cleanup can target only component-specific hardcoded pockets instead of
  generic shell overlays. A final same-day cleanup then removed the last real
  user-facing literal fallback still left in the live theme/view path:
  `agent_detail.py` now falls back to the builtin semantic `text` color when a
  supplied theme value is invalid instead of dropping to raw white, leaving
  only seed data, example payload text, and generic contrast helpers as
  remaining literal hits in the desktop theme tree. One more bounded helper
  follow-up then removed those generic helper escapes from the live editor
  path too: theme-editor swatch buttons now derive contrast text and
  border/hover chrome from the active theme's `text`/`bg_top` colors instead
  of raw black/white constants, so the remaining literal hits are limited to
  palette seed data and example payload text rather than live component
  chrome.
  2026-03-09 screenshot-hardening follow-up landed: wrapped bridge panes now
  avoid the misleading lower-left scrollbar-handle affordance on the common
  read path, non-diff markdown is no longer painted as removal text in agent
  detail dialogs, provider badges and broader tooltips are visible in the
  chrome, in-window `Help` / `Developer` menus now explain the workflow
  without kicking operators out to repo docs, and the theme editor import page
  now explains current import/highlight semantics inline. 2026-03-09 home/read
  follow-up landed too: the app now opens on a guided `Home` launchpad instead
  of dropping directly into raw dashboards, and a shared `Read` mode switch
  now flips report/footer wording between simple and technical modes while
  feeding the same selected source report into staged AI drafts. A later
  2026-03-09 density/mobile-parity follow-up replaced stale Home/Analytics
  filler with repo-owned git/mutation/CI summaries plus read-only
  `phone-status` parity over the same payload planned for iPhone-safe
  surfaces, tightened sidebar/button density, and documented
  `integrations/code-link-ide` as a future reference adapter rather than a
  runtime dependency of the desktop shell. Next slice: expand
  the editor into fuller page-scoped controls for text/borders/buttons/nav/
  approvals/log panes, and push the remaining hardcoded desktop surfaces onto
  the shared token/preview path so the console can theme nearly the full UI
  without widening into a second control plane. Codex re-review later the same
  day narrowed the current closure: the theme-authority split is resolved, but
  live-launch portability/docs honesty, analytics/CI honesty, real
  startup/mutating-path proof, launcher-script execution coverage, and
  checklist/progress consistency remain open before MP-359 can be called
  green. A further bounded Step-6 follow-up is now closed too: the approval
  queue no longer vanishes when empty and instead keeps a visible `0 Pending`
  zero-state so operators retain the center approval affordance even before
  the larger `ApprovalSpine` card migration lands. Another same-day bounded
  technical-density follow-up then made `Read -> Technical` visually real
  instead of prose-only: the PyQt6 Home and Activity surfaces now switch to
  denser terminal-style digest framing with smaller toolbar-first guidance and
  monospace digest/read panes, addressing operator feedback that the shell was
  still too banner-heavy for a command-center workflow. A further same-day
  session-surface follow-up then fixed the next real live-tail gap: the
  desktop no longer crams terminal text, session metadata, and registry rows
  into one pane. `session_trace_reader.py` now keeps separate readable history
  plus current-screen snapshots while filtering private-CSI parse junk and
  `thinking with high effort` spinner noise, and the Workbench/Monitor/Sidebar
  session surfaces now render a large terminal-history pane with smaller
  stats/screen + registry support below so the lower deck carries useful live
  signal instead of blank space. A later same-day operator-feedback follow-up
  tightened that contract again: live session panes now prefer the
  reconstructed visible terminal screen over the noisier raw history stream
  whenever a `script(1)` trace is available, truncated tail reads align to the
  next line boundary so partial ANSI/control fragments do not leak into the
  UI, and the lower `Stats` / `Registry` pair is now one double-click
  flippable card per provider instead of two cramped panes. The next bounded
  follow-up then moved the default shell back onto a card-first snap-aware
  Workbench: visible preset pills returned, the three lane cards stay on
  screen together, launcher/bridge/diagnostics now render side by side
  instead of behind workbench tabs, and always-visible helper copy was
  compacted so terminal surfaces dominate. The next operator-feedback slice
  then restored explicit `Codex Session` and `Claude Session` panes backed by
  the review-channel full projection's agent registry plus bridge state, and
  the default Workbench now uses a top-row `Codex Session | Operator Spine |
  Claude Session` split with raw logs/digests below so the shell shows what
  each side is doing again without pretending those panes are live PTY
  emulators. The next same-day cleanup then grouped that lower deck by job
  instead of leaving every card visible at once: Workbench now uses
  `Terminal`, `Stats`, `Approvals`, and `Reports` tabs so launcher streams,
  repo stats, decision routing, and digest/draft work each live on one
  focused surface. The next operator-feedback follow-up then pushed that idea
  through the whole Workbench instead of keeping a fixed session strip above
  it: `Sessions`, `Terminal`, `Stats`, `Approvals`, and `Reports` are now
  full-page task tabs, so the streaming session row is its own focused page
  and the workbench tabs sit at the top of the surface instead of in the
  middle of the layout. The next same-day live-session follow-up then made
  those `Codex Session` / `Claude Session` panes prefer real tailed launch
  transcripts from `dev/reports/review_channel/latest/sessions/` whenever the
  review-channel launcher has emitted them, while keeping the prior
  full-projection bridge/registry digest as the honest fallback when no live
  log exists yet. A same-day Theme Editor follow-up then repurposed the right
  rail from an always-on preview gallery into `Quick Tune`, `Coverage`, and
  optional `Preview` tabs, and restyled the operator toolbar action buttons
  toward flatter dashboard/instrument-panel chrome. A later same-day theme
  tranche then promoted the editor from colors/tokens into a fuller theme
  contract with persisted `components` + `motion` settings, component-style
  families for borders/buttons/toolbar chrome/inputs/tabs/surfaces, new
  `Components` and `Motion` authoring pages, and a real preview playground for
  front/back card swaps plus pulse feedback so motion controls are no longer
  just roadmap copy. The next explicit planning follow-up now captures the
  remaining density/scale-up work too: chart-backed repo analytics and
  mutation/hotspot views, 4/6/8+ snap-aware multi-agent layouts, read-only
  split/combined lane terminal monitors, broader tooltip/help saturation, and
  richer QSS/theme-pack import plus semantic-highlight controls that keep
  normal report content from reading like an error state. Current stopping
  point: Cursor lane wiring now reaches the Activity summary cards and quality
  reports can emit live review-channel `finding` packets; follow-on cleanup of
  the architecture/memory/guardrail primer content is parked as an explicit
  backlog item in `dev/active/operator_console.md` Phase 4.7.
  (directory reorg) then Phase 3 (approval queue center stage), with `Start
  Swarm`, typed control wiring, and CI visibility tracked in parallel.
  Execution spec:
  `dev/active/operator_console.md`.

- [x] MP-360 Wire AI-driven remediation into Ralph loop: create
  `ralph_ai_fix.py` with Claude Code invocation, false-positive filtering,
  architecture-specific validation (Rust/PyQt6/devctl/iOS), approval-mode
  support, and commit/push automation. Update policy allowlist and workflow
  default fix command. Add cross-architecture guard enforcement policy to
  `AGENTS.md` and wire 7 new guard scripts into `tooling_control_plane.yml`.
- [ ] MP-361 Create guardrail configuration registry
  (`dev/config/ralph_guardrails.json`) mapping finding categories to AGENTS.md
  standards, documentation links, and AI fix skills so the AI brain has
  context for each finding class.
- [ ] MP-362 Emit structured guardrail report (`ralph-report.json`) from AI fix
  wrapper with per-finding status, standards refs, fix skills used, and
  aggregate analytics (fix rate, by-architecture, by-severity, false-positive
  rate).
- [ ] MP-363 Add `devctl ralph-status` CLI command with SVG charts (fix rate
  over time, findings by architecture, false-positive rate), data-science
  integration, and phone status projection.
- [ ] MP-364 Add operator console Ralph dashboard (PyQt6 widget with finding
  table, progress bars, guard health indicators, and control buttons for
  start/pause/resume/configure).
- [ ] MP-365 Integrate Ralph loop metrics into phone/iOS status views (compact
  phase/fix_rate/unresolved fields, start/pause/configure actions, and iOS
  MobileRelayViewModel display).
- [ ] MP-366 Deliver unified guardrail control surface
  (`ralph_control_state.json`) so devctl CLI, operator console, and phone app
  all read/write the same start/pause/configure/monitor state with policy
  gates and audit logging.
- [ ] MP-367 Add `check_ralph_guardrail_parity.py` guard to verify every entry
  in `AI_GUARD_CHECKS` has a step in `tooling_control_plane.yml`, a row in
  `ralph_guardrails.json`, and a skill mapping — closing the loop so new
  guards are automatically wired into the full pipeline.
  Execution spec: `dev/active/ralph_guardrail_control_plane.md`.
- [x] MP-368 Implement `probe_concurrency` so heuristic review probes can flag
  async/shared-state race signals without blocking CI.
- [x] MP-369 Implement `probe_design_smells` so Python AI-slop patterns such as
  heavy `getattr()` density and formatter sprawl become typed review targets.
- [x] MP-370 Implement `probe_boolean_params` so unreadable multi-bool
  signatures in Python and Rust are surfaced before they calcify into APIs.
- [x] MP-371 Implement `probe_stringly_typed` so string-dispatch paths that
  should become enums/contracts are surfaced as explicit review hints.
- [x] MP-372 Land the shared review-probe framework (`probe_bootstrap.py`,
  shared schema/utilities, probe registration, and check-profile integration).
- [x] MP-373 Wire the first end-to-end review-probe path with tests and
  non-blocking `devctl check` integration.
- [x] MP-374 Deliver the expanded review-probe catalog plus aggregated
  `devctl probe-report` / `status --probe-report` / `report --probe-report`
  surfaces and stable `review_targets.json` output. Remaining follow-up is
  operator-facing ranking/baselines and deeper probe-specific regression
  coverage, not initial plumbing.
- [ ] MP-375 Shift review-probe next work to operator-first adoption:
  ranking/baselines, self-contained senior-review packets, connectivity-aware
  hotspot scoring, changed-subgraph / hotspot visuals, governance parity, and
  optional operator-console review dashboards. 2026-03-10 follow-up:
  `devctl triage --probe-report` now promotes aggregated probe debt into
  routed issues/next actions, and local `loop-packet` fallback requests the
  same probe summary so packets stay probe-aware even without a prior
  artifact. Later 2026-03-10 follow-up: `devctl probe-report` now emits ranked
  hotspot scoring, `file_topology.json`, `review_packet.{json,md}`, and
  Mermaid/DOT hotspot views, while `status` / `report` / `triage` consume the
  same ranked hotspot summary. A first cleanup pass using that packet reduced
  live findings from 23 across 18 files to 18 across 14 files. Control-plane
  or Ralph adapters stay later and should build on the same stable probe
  artifacts. Latest follow-up: maintainer governance docs now explicitly tell
  AI when to run `check --profile ci`, `probe-report`, and `guard-run`, and
  document the topology/review-packet artifacts emitted by the probe stack.
  Latest portability follow-up: built-in guard/probe capability metadata now
  lives in `devctl/quality_policy_defaults.py`, repo-local
  enablement/default args now live in `dev/config/devctl_repo_policy.json`,
  and `check` / `probe-report` resolve active steps from the
  `quality_policy*.py` policy stack so the current behavior is preserved here
  while the engine moves toward repo-portable presets. Latest preset
  follow-up: VoiceTerm now extends reusable portable presets under
  `dev/config/quality_presets/`, VoiceTerm-only matrix/isolation guards live
  behind the repo-specific preset instead of the portable fallback, and
  `check` / `probe-report` plus probe-backed `status` / `report` / `triage`
  all accept `--quality-policy`; `DEVCTL_QUALITY_POLICY` provides the same
  automation override, and `devctl quality-policy` now renders the resolved
  policy/scopes so maintainers can validate another repo policy without
  editing orchestration code. Latest scope follow-up: scan roots are no longer baked
  into the standalone Python/Rust guard+probe scripts; the repo policy now
  owns `python_guard_roots`, `python_probe_roots`, `rust_guard_roots`, and
  `rust_probe_roots`, and probe-report artifacts surface those resolved roots
  for operator review. Latest onboarding follow-up: `governance-bootstrap`
  now writes a starter `dev/config/devctl_repo_policy.json` for the target
  repo when missing, chooses the nearest portable preset from detected
  Python/Rust capabilities, and ships exported template files
  (`portable_governance_repo_setup.template.md`,
  `portable_devctl_repo_policy.template.json`) so another repo gets a real
  first-run setup path instead of hand-assembling policy from scattered docs.
  Latest usability follow-up: the same bootstrap command now writes a
  repo-local `dev/guides/PORTABLE_GOVERNANCE_SETUP.md` file into the target
  repo so an AI or maintainer has one obvious first-read setup surface after
  export/bootstrap, and `dev/scripts/checks` moved another set of internal
  helper families behind documented subpackages (`active_plan/`,
  `python_analysis/`, `probe_report/`) to keep the root directory flatter.
  Latest portable-guard slices now ship
  `check_python_suppression_debt.py`, `check_python_design_complexity.py`, and
  `check_python_cyclic_imports.py` as default portable Python guards, while
  default-argument traps route through the expanded
  `check_python_global_mutable.py` guard. Latest portability follow-up:
  `check_code_shape.py` namespace/layout rules now resolve from repo-policy
  guard config instead of VoiceTerm-only hard-coded tuples. Next portable
  hard-guard backlog now narrows to Rust `result_large_err` /
  `large_enum_variant` evaluation. Latest next-signal intake: MP-375 now
  explicitly tracks an evidence-driven candidate tranche instead of treating
  probe work as closed. Immediate advisory candidates are tuple-return
  complexity, mutation density, method-chain length, fan-out, and
  side-effect/match-arm complexity. `check_enum_conversion_duplication` stays
  a hard-guard candidate pending portability proof, while cognitive-
  complexity/readability micro-metrics and Python return-type consistency stay
  research-only until they beat existing structural-complexity coverage and
  prior signal-quality findings.
  Execution spec: `dev/active/review_probes.md`.

- [ ] MP-376 Build the portable code-governance engine + evidence corpus:
  keep the guard/probe/report stack reusable across arbitrary repos without
  engine edits, define the boundary between engine code, portable presets, and
  repo-local policy, capture guarded coding episodes as evaluation data
  (initial output, guard hits, repair loops, accepted diff, human edits, test
  and later-review outcomes), keep the adjudicated finding ledger
  (`governance-review`) current so false-positive and cleanup rates are visible
  in `data-science`, keep first-run onboarding (`governance-bootstrap` +
  `--adoption-scan`) and export flows reusable across arbitrary repos, and
  keep mining repeated low-noise pattern families from live evidence before
  promoting more hard guards. The first external pilot (`ci-cd-hub`) is now
  complete; remaining scope is benchmark automation, active cleanup against the
  evidence log, more pilot-proof engine cleanup, and evidence-driven next
  pattern selection while holding guard code to the same or stricter
  structural standard as guarded code. Execution spec:
  `dev/active/portable_code_governance.md`. Latest CI-parity follow-up
  (2026-03-11): GitHub exposed that `dev/config/devctl_repo_policy.json` and
  the portable preset JSON files were still ignored local artifacts, so local
  validation and CI were resolving different guard/probe sets. The policy/preset
  files are now tracked repo assets, maintainer docs explicitly call out that
  policy changes must be committed, pre-commit CI is narrowed to changed files,
  the tooling-control-plane mypy env export bug is fixed, iOS CI now runs on
  `macos-15` for Swift 6 / newer Xcode project compatibility, and the current
  maintainer-lint redundant-closure regressions are burned down. Latest
  adoption-flow follow-up (2026-03-17): starter policy plus a setup guide is
  no longer enough for the portable path. The next onboarding contract is a
  reviewed repo-local governance doc (`project.governance.md` working name)
  that `governance-draft` can infer from repo facts, humans can finish with
  priorities/debt/exceptions, and `governance-bootstrap` or later
  `governance-init` can consume so adopter repos stop hand-authoring policy
  from scratch. Latest audit-intake follow-up (2026-03-22): portable scope now
  explicitly includes governance-completeness evidence for the engine itself
  (direct guard/probe/subsystem coverage surfaced as meta-findings), a
  portable repo-organization/report surface beyond today's partial
  `package_layout` + docs-governance coverage, tandem/review-infrastructure
  opt-in clarity for adopters so quick-start flows do not silently assume
  `bridge.md`, and continued burn-down of the crowded `dev/scripts/devctl`
  flat root behind the same policy-backed organization contract. Latest
  tracked follow-ups from that intake:
  - [ ] Surface self-hosting governance completeness as portable meta-findings
    so low test/guard/subsystem coverage becomes measured engine evidence, not
    audit-only prose. (evidence: `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 34)
  - [ ] Extend the portable organization contract to cover root markdown/file
    budgets, metadata/orphan/wrong-hierarchy gaps, and continued
    `dev/scripts/devctl` flat-root burn-down under the same policy-backed
    report surface. (evidence: `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 29,
    Part 40)
  - [ ] Keep tandem/review infrastructure opt-in in portable presets and setup
    until an adopter explicitly enables that enforcement, and make the enable
    point obvious in bootstrap/setup surfaces. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 41)
  Latest publication-sync follow-up: refreshed the external
  `terminal-as-interface` paper snapshot from committed VoiceTerm HEAD and
  recorded the new baseline in `dev/config/publication_sync_registry.json`
  (`source_ref=4deb8ec8f8c3709f1fb35955f9763c6147df6a95`,
  `external_ref=9cf965f`), returning `check_publication_sync.py` to zero drift.
  Latest PR-gate follow-up (2026-03-12): the remaining GitHub-only failures on
  PR #16 are burned down locally by making `process_sweep` fixtures checkout-
  agnostic, pinning review-channel stale-poll tests to explicit freshness
  policy, clearing leaked runtime/style-pack overrides from the startup-banner
  fallback test, switching iOS `xcode-build` to the generic simulator
  destination, and taking the changed-file `pre-commit` lane back to green.
  Latest closure pass (2026-03-12): the next rerun exposed real local
  portability debt instead of more GitHub workflow drift, so `devctl` now
  keeps repo-owned Python subprocesses on the invoking interpreter,
  compatibility exports are restored for split modules
  (`quality_policy`, `collect`, `status_report`, `triage/support`,
  `check_phases`, `check_python_global_mutable`), and new support modules for
  phone-status plus Activity-tab report helpers pull the touched Python files
  back under code-shape/function-duplication limits without changing behavior.
  Latest probe-cleanup follow-up (2026-03-12): the remaining working-tree
  review hints are now burned down too. `autonomy/phone_status.py` uses a
  typed `RalphSection` boundary instead of anonymous dict helpers,
  `mobile_status_views.py` now delegates typed payload/view support to the new
  `mobile_status_projection.py` module so the renderer stays below its
  code-shape cap, `loop_packet_helpers.py` uses `LoopPacketSourceCommand` for
  the last auto-send string dispatch, the probe packet rerun is clean, and the
  governance ledger is updated with six additional `fixed` probe rows.
  Latest push-repair follow-up (2026-03-12): the first rerun on the refreshed
  PR caught a real changed-file `pre-commit` regression where Ruff had stripped
  compatibility exports still used across the repo. Those re-export seams are
  now restored compactly in `common.py`, `status_report.py`, `collect.py`,
  `triage/support.py`, `commands/check_phases.py`, `process_sweep/core.py`,
  `phone_status_view_support.py`, `quality_policy.py`,
  `check_python_global_mutable.py`, and `probe_report_render.py`; `common.py`
  stays back under its shape cap; changed-file `pre-commit` is green locally
  again; and the full `dev/scripts/devctl/tests` suite reran at
  `1184 passed, 4 subtests passed`.
  Latest external-pilot rerun (2026-03-14): `probe-report --repo-path` plus
  starter-policy scope generation now resolve the target repo consistently
  enough to trust cross-repo counts; rerunning the 13 pilot repos changed the
  durable aggregate from the previously quoted `158` hints to `311`, because
  `ci-cd-hub` widened from a `scripts/`-only under-scan (`7` hints) to a full
  starter-scope scan of `scripts`, `_quarantine`, `cihub`, and `tests`
  (`159` hints). The harder onboarding lane now works too:
  `check --profile ci --repo-path /tmp/governance-pilots/ci-cd-hub --adoption-scan`
  completed and returned `13` failing guard families, and six representative
  `ci-cd-hub` probe findings were recorded into the governance-review ledger
  as `confirmed_issue` evidence. Remaining external coverage gap:
  non-Python/Rust repos still need JS/TS/Java guard/probe packs. Latest
  structural-readability follow-up (2026-03-20): the first repo-policy-backed
  naming advisory probe now exists. `probe_term_consistency.py` is wired into
  the shared script catalog and quality-policy registry, VoiceTerm policy now
  seeds canonical-vs-legacy review-channel vocabulary rules, and the portable
  readability tranche can start collecting reviewed signal quality for public
  wording drift instead of relying only on shape/complexity heuristics.
  Latest external-review adjudication follow-up (2026-03-17): reran the
  portable stack against the pinned `integrations/ci-cd-hub` federated
  checkout so the repo-local federation path has distinct evidence from the
  corrected `/tmp/governance-pilots/ci-cd-hub` benchmark. The local-path rerun
  produced `13/15` red AI guard steps plus a richer current probe packet
  (`1828` findings across `266` files), and the target repo now has `7`
  adjudicated ledger rows (`4 confirmed_issue`, `3 false_positive`) under
  `integrations/ci-cd-hub/dev/reports/governance/`. Keep those receipts
  separate from the March 14 cross-repo aggregate; today's run is the pinned
  submodule/local-path proof and finding-quality follow-up, not a replacement
  baseline.
  Latest docs-governance follow-up (2026-03-12): strict-tooling drift is
  closed too. `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, and
  `dev/scripts/README.md` now document that staged `dev/scripts/**` module
  splits must keep compatibility re-exports until repo importers, tests,
  workflows, and pre-commit hooks migrate together. After refreshing the
  review-channel heartbeat, `docs-check --strict-tooling` and the full
  canonical `bundle.tooling` replay are green again under `python3.11` on the
  local workstation, including `397 passed, 181 skipped` in the Operator
  Console suite and a clean `process-cleanup --verify`.
  Latest CI-runner parity follow-up (2026-03-12): the next GitHub rerun
  exposed two environment-sensitive Python regressions plus one operator-
  console timing bug, and they are now burned down locally. Review-channel
  bridge session generation no longer hard-fails when the default resolver
  cannot find `codex`/`claude` on the current PATH before a dry-run or
  simulated launch script is even written, `triage-loop` now passes the
  command module's CI/connectivity predicates through its preflight helper so
  the existing non-blocking-local connectivity test holds under GitHub
  Actions, and `JobRecord.duration_seconds` clamps negative monotonic deltas
  to zero. The reproduced failure shapes are green locally, the full
  `dev/scripts/devctl/tests` suite reran at `1184 passed, 4 subtests passed`,
  and `app/operator_console/tests/` reran at `397 passed, 181 skipped`.
  Review-channel heartbeat parity follow-up (2026-03-12): the next PR rerun
  showed one more CI-only mismatch. `devctl review-channel` auto-refreshes a
  stale bridge heartbeat before `status` / `launch`, but the helper had been
  keying that decision off `check_review_channel_bridge.py` metadata errors.
  On GitHub runners the bridge guard intentionally skips live heartbeat
  freshness enforcement (`GITHUB_ACTIONS=true`), so the refresh path never
  triggered even though bridge liveness was still stale. The helper now keeps
  using the guard for structural bridge validity but derives refreshability
  from direct bridge snapshot/liveness analysis, and the stale-heartbeat tests
  now pin `GITHUB_ACTIONS=true` explicitly so CI runner parity stays covered.
  Tooling-control-plane workflow parity follow-up (2026-03-12): after that fix
  landed, the only remaining PR blocker in `docs policy + governance guard`
  was not a docs regression at all. The workflow's nested
  `check_rust_compiler_warnings.py` step was compiling changed Rust files
  without provisioning the Rust toolchain or Linux ALSA development headers,
  even though the dedicated Rust lanes install both. `tooling_control_plane.yml`
  now installs Rust plus `libasound2-dev` before the compile-time Rust guard
  runs so the docs/governance lane matches the real Rust CI prerequisites.

- [ ] MP-377 Extract the reusable AI governance platform architecture:
  package the current VoiceTerm-local code-quality/control-plane stack as one
  installable system with shared backend contracts for runtime state, typed
  actions, repo packs, provider/workflow adapters, and artifact storage so the
  same platform can power VoiceTerm, a PyQt6 dashboard, CLI flows, and future
  phone/mobile surfaces across arbitrary repos. This scope owns the product-
  level extraction of Ralph/mutation/review-channel/process-hygiene loops and
  the filesystem/package reorganization needed to mirror those layers cleanly.
  It now explicitly includes self-hosting directory/layout governance for
  `devctl` itself plus baseline/adoption layout scanning so external repos can
  receive the same organization contract agents use here, including crowded
  flat-family namespace reporting for `devctl/commands` and other high-density
  roots. It also owns the context-budget architecture for AI-facing runs:
  typed context packs, repo-pack-tunable budget profiles, usage telemetry,
  overflow/fallback behavior, and future operator/adopter guidance so better
  code quality does not depend on hidden prompt bloat. This scope also now
  explicitly includes the real package/install surface (`pyproject.toml`,
  build backend, stable CLI entrypoints), repo-pack-owned path resolution for
  removing hard-coded VoiceTerm filesystem assumptions, repo-pack/platform
  compatibility checks, the central finding/review/metric evidence schema, and
  phase-scoped replay/evaluation plus waiver/promotion lifecycle work required
  before external pilots count as proof. It also now explicitly owns the
  self-hosting enforcement backlog behind "why didn't our tools catch this?":
  layer-boundary enforcement, portable-path construction purity,
  provider/workflow adapter routing, contract-completion/orphaned-contract
  checks, schema/platform compatibility validation, and the first repeatable
  command-source/shell-execution checks for platform-grade misses. Public proof
  is part of the deliverable too, not a marketing afterthought: external pilot
  packs should preserve the platform's differentiators in a durable/public
  whitepaper or comparison surface, not only in internal plan text.
  `MP-376` remains the narrower engine/policy/evaluation track. Execution spec:
  `dev/active/ai_governance_platform.md`. This spec is now the only main
  active architecture plan for the standalone governance product scope and
  carries the consolidated repo-grounded assessment, separation roadmap,
  documentation consolidation plan, phase-by-phase implementation order, the
  explicit platform completion gates, and the standing Python/Rust-first
  pattern-mining plus future-language-extension strategy. When present in the
  current shared worktree, `GUARD_AUDIT_FINDINGS.md` and
  `ZGRAPH_RESEARCH_EVIDENCE.md` may be consulted as local reference-only
  companions for supporting evidence and idea inventory, but they are not
  canonical execution authority and all accepted conclusions must be mirrored
  into tracked plan state here plus the `MP-377` spec chain before
  implementation or review.
  Do not treat this
  scope as complete when the repo is merely split or packaged; closure requires
  architecture boundary proof, pipeline parity, telemetry trust, replayable
  evidence quality, and cross-repo adoption evidence together. Current explicit
  follow-up: make typed JSON runtime state the live authority over markdown/UI
  projections, generate agent/developer startup surfaces from the same repo-pack
  policy, add one reviewed repo-local governance contract
  (`project.governance.md` working name) that AI can draft and startup
  surfaces can summarize, prove the same-context/same-check-path flow across
  Codex, Claude,
  `active_dual_agent`, `single_agent`, and `tools_only`, separate collaboration
  mode from objective profiles like `bootstrap` / `audit` / `refactor` /
  `review` / `remediation`, define the standalone platform-repo plus VoiceTerm
  back-import proof path, freeze the typed queue/action contract, promote the
  existing topology backend into a first-class portable `map` surface for
  flowcharts/AI context/hook reuse, with complexity/hotspot/evidence overlays,
  targeted-check hints, and a cacheable JSON-plus-SQLite artifact contract,
  keep every major subsystem standalone-usable in any repo while also fully
  composable into one integrated agent app, and keep local tandem validation
  honest about external CI/network/environment
  failures versus real code-quality
  regressions. Keep the whole system in scope here: governance core, runtime,
  adapters, frontends, repo packs, and VoiceTerm as a consumer plus first-party
  local operator shell. VoiceTerm may be the preferred main app and local host
  path, but the backend must remain callable without VoiceTerm by CLI, PyQt6,
  phone/mobile, skills/hooks, automation loops, and external repos. VoiceTerm
  should also be able to drive the full platform action surface through that
  same backend path: guards, probes, quality/reporting, bootstrap/export,
  review-channel actions, remediation loops, and generated instruction/skills
  surfaces. Remaining missing-proof items now explicitly include: local
  service lifecycle/attach semantics, a portable contract-sync guard for that
  lifecycle/authority surface, caller authority + approval matrix, and golden
  cross-client parity fixtures over the same backend snapshots. This scope
  now also explicitly requires one cross-cutting coherence matrix over
  vocabulary, identity, state, action, artifact, lifecycle, projections,
  parity, and portability so drift prevention is a planned platform contract
  instead of a collection of local checks. The latest architecture audit also
  promoted six more cross-cutting gaps into explicit scope: public
  deprecation/compatibility windows, multi-client write arbitration, extension
  and adopter conformance packs, whole-system artifact taxonomy/ledger
  classes, degraded-mode semantics, and the stable backend protocol boundary.
  This scope
  also owns durable operator-guide coverage as a first-class contract:
  maintain system-level guide/playbook surfaces (`DEVCTL_AUTOGUIDE`,
  starter instructions, generated local instructions) through repo-policy
  contracts and guard-backed sync rather than human memory alone. This scope
  also keeps the existing `package_layout` engine as the self-hosting
  organization seam rather than inventing a second crowding guard: the next
  platform follow-up is to generalize those layout/family rules beyond the
  current Python-biased/freeze-mode coverage so the same modular organization
  contract can govern Rust/workflow/docs families too.
  This scope
  also treats "why didn't the tools catch this?" as an execution rule:
  when a real issue slips through, the follow-up must decide whether the miss
  belongs in an existing reusable guard/probe/contract or a new low-noise
  modular enforcement path instead of stopping at a one-off patch.
  The same scope also owns operator-visible loop observability as a product
  requirement rather than a chat habit: reviewer/coder heartbeat, findings,
  next action, and stale/healthy state must publish automatically through the
  shared backend so chat, CLI, PyQt6, phone/mobile, and overlay users can see
  progress without reopening markdown bridges or manually prompting the loop.
  Latest self-hosting reporting follow-up (2026-03-17): the canonical
  `devctl probe-report` path now threads `repo_root` through markdown/
  terminal rendering so repo-owned `.probe-allowlist.json`
  `design_decision` entries shape the main operator packet instead of only the
  fallback script path; current local filtered probe backlog is medium-only
  (`0` active high, `14` active medium, `25` design decisions). Latest
  audit-intake follow-up (2026-03-22): the next `P0` closure work is wiring,
  not more architecture. `startup-context` must ingest real `Session Resume`
  state instead of a boolean marker, runtime startup/routing must consume live
  `ProjectGovernance` `startup_order` / `command_routing_defaults` /
  `workflow_profiles`, AI repair paths must read canonical `Finding` /
  `DecisionPacket` guidance fields, guard-run/autonomy/review close-out must
  auto-record `governance-review` outcomes, and top-level command crash
  handling must converge on structured `ActionResult` failures instead of raw
  tracebacks.
  - [ ] Land the missing authority-spine runtime nodes
    (`PlanTargetRef`, `WorkIntakePacket`, `CollaborationSession`) before
    widening `P1`/`P2` routing and adoption work. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 32)
  - [ ] Replace boolean-only `Session Resume` detection with typed continuity
    state in `startup-context` / intake routing. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 28)
  - [ ] Turn report-only governance-routing and AI-guidance fields into live
    runtime inputs across startup, repair, review, and `guard-run` flows.
    First proof slices landed: Ralph now consumes exact file-matched
    canonical probe `ai_instruction` from `review_targets.json`, autonomy
    `triage-loop` / `loop-packet` now consumes the same guidance from a
    bounded structured backlog slice, review-channel/conductor plus swarm
    inherit that contract through shared context packets, escalation packets
    now carry `## Probe Guidance` plus stable `guidance_refs`, and the
    deterministic route-closure guard now proves the Ralph / autonomy /
    `guard-run` family inside `check_platform_contract_closure.py`, including
    a family-completeness failure if any declared consumer disappears. The
    first carried decision semantic is now live too: matched probe guidance
    merges `DecisionPacket.decision_mode`, Ralph/autonomy/`guard-run` treat
    `approval_required` as a real behavior gate, and the same closure guard
    now proves that family as well. The remaining closure in this same
    tranche is broader single-authority + structured-routing enforcement so
    AI consumers cannot silently negotiate between multiple artifact
    authorities or keep deriving routing keys from prose when typed fields
    already exist, together with explicit adoption proof: prompts must keep
    telling AI to prefer attached probe guidance, matching must prefer
    structured identity, and runtime telemetry must record stable
    `guidance_id` / `guidance_followed` plus fix outcome. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 27, Part 38, Part 52, Part 54)
  - [ ] Route fresh `dev/reports/**` operational evidence into the live prompt
    builders and adjacent decision surfaces so bootstrap, conductor, swarm,
    Ralph, loop-packet, escalation, and other runtime controllers consume
    hotspot, verdict-history, watchdog, reliability, queue-state, quality-
    feedback, decision metadata, research-benchmark, and event-history data
    instead of leaving those artifacts write-only or display-only. Immediate
    zero-consumer backlog still called out by audit is now narrower:
    `finding_reviews.jsonl` history plus quality-feedback recommendations are
    flowing through shared context packets, watchdog episode digests plus
    data-science command-reliability lines now flow through the same shared
    packet family, and the first `DecisionPacket` behavior gate
    (`decision_mode`) now reaches live prompt/runtime consumers. Remaining
    backlog is broader decision/adoption metadata and impact measurement, not
    the original transport gap. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 42, Part 45, Part 54)
  - [ ] Finish the first graph-routing expansion by emitting live
    `EDGE_KIND_GUARDS` / `EDGE_KIND_SCOPED_BY` edges, land the guard-edge
    quick win first, add the missing node families (`test`, `workflow`,
    `config`, `finding`, `contract`) incrementally, and widen graph consumers
    beyond escalation-only packets into startup, autonomy, repair, and
    operator routing. Keep this behind the direct closure tranches:
    `ai_instruction` wiring, the produced-but-never-consumed meta-guard, and
    startup/session unification should not block on ZGraph; it becomes the
    query engine once these edges and consumers land. First closure slice is
    now live: the builder emits guard-coverage edges from active quality
    policy + scope roots and initial policy-backed plan-ownership edges from
    docs-policy tooling prefixes. Remaining work is the
    node-family rollout and wider non-escalation consumers. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 43, Part 47)
  - [ ] Add deterministic temporal ZGraph snapshots on top of that graph lane:
    save graph snapshots at CI/check boundaries, diff successive snapshots,
    and surface architecture-drift/trend answers by reusing the existing
    snapshot/delta patterns already present in data-science and quality-
    feedback instead of creating a second graph-analysis stack. First slice
    now live: `context-graph --mode bootstrap` persists a typed
    `ContextGraphSnapshot` artifact under `dev/reports/graph_snapshots/`, and
    `--save-snapshot` widens that same writer to the other graph modes.
    Second slice now live too: `context-graph --mode diff --from ... --to ...`
    resolves saved snapshots back into a typed `ContextGraphDelta`, reports
    added/removed/changed nodes and edges plus edge-kind/temperature deltas,
    and adds a rolling trend summary over recent snapshots. Follow-up
    hardening now landed too: `latest` / `previous` ordering comes from
    snapshot capture time instead of filesystem `mtime`, direct-path trend
    scans ignore non-snapshot sibling JSON, and delta/trend anchors now emit
    portable snapshot-store-relative paths instead of machine-local absolute
    paths. Remaining work is wider capture automation and richer drift
    interpretation, not basic diff/trend plumbing. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 53)
  - [ ] Unify the current startup systems behind one canonical
    `startup-context` / `WorkIntakePacket` path so bootstrap instructions,
    governed-plan `Session Resume`, repo memory, and recent episode evidence
    feed one bounded startup packet instead of four disconnected sources.
    Current partial proof: generated bootstrap surfaces and review-channel
    bootstrap prompts now explicitly tell agents when to escalate from the
    slim bootstrap helper to typed `startup-context`, and governance draft
    discovery now only serializes `memory_roots` when real canonical repo
    roots exist instead of emitting an always-empty placeholder. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 46)
  - [ ] Promote checkpoint budget from advisory status to fail-closed startup
    authority: when the typed startup / collaboration receipt reports
    `safe_to_continue_editing=false` or `checkpoint_required=true`, repo-owned
    launchers must refuse to start the next implementation slice and only
    promote checkpoint/review work until a fresh post-commit/push receipt
    clears the budget. Current partial proof: `review-channel --action
    launch|rollover` now treat the typed checkpoint budget as a hard launch
    blocker, `startup-context` itself now returns non-zero on that same typed
    checkpoint receipt, and `check_startup_authority_contract.py` now fails when the
    startup authority packet is already over budget or when repo-local Python
    imports only resolve from worktree-only modules instead of the git index,
    while separately validating committed importer content against `HEAD`
    without treating a legitimate staged atomic split as broken.
    Remaining closure: promote the same fail-closed rule across the rest of
    the repo-owned startup/work-intake launch surfaces. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 28, Part 36, Part 41)
  - [ ] Auto-record `governance-review` close-out and converge top-level
    failures on structured `ActionResult` crash envelopes. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 36, Part 39)
  - [ ] Turn session continuity into one typed path by combining parsed
    `Session Resume`, episode/execution digests, shared memory hints, and
    review/bridge liveness into the startup continuity packet instead of
    leaving them as disconnected silos. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 48)
  - [ ] Make architectural absorption a required finding-disposition rule: no
    important finding closes until it is classified for recurrence risk,
    mapped to an approved prevention surface or explicit waiver, and verified
    at both the local-fix and systemic-prevention layers. For externally found
    architecture smells, the closure step must also prove whether the current
    checker stack fired on the touched files and classify any miss as no-rule,
    too-narrow detection, or advisory-only severity before moving on.
  - [ ] Evaluate additive `devctl-mcp` transport over the existing
    context-graph / startup / plan-status read surfaces after authority-loop
    closure; keep it read-only first and route any writeback through the same
    typed action/approval path as the CLI. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 49)
  - [ ] Improve the portable governance CLI/operator surface with
    `guard-explain`, `which-tests`, described `devctl list` output, per-check
    status/timing, and an incremental check path so adopters can discover the
    right validation slice without source-diving. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 44)
  Latest audit-guide closure follow-up (2026-03-22): the full accepted
  `dev/guides/SYSTEM_AUDIT.md` action set is now explicitly owned in the
  canonical plan chain rather than partly implied in reference prose.
  `platform_authority_loop.md` now carries blocker/startup/memory/path-
  portability items
  (`D1-D5`, `S1-S4`, `E1`, `G1`, `A5-A12`, `A22-A23`), this `MP-377` platform
  plan carries feedback/runtime/self-governance closure (`A1-A4`, `A13`,
  `A16-A19`, `A27`, `A29`, `T3-T5`), `MP-376` carries portability/adoption
  proof (`A14`, `A20-A26`), `MP-355` carries review-channel consolidation
  (`A15`, `T1`), `review_probes.md` carries probe expansion/history wiring
  (`A28`, `A30`), and `MP-340` carries watchdog coverage (`T2`).
  `dev/guides/SYSTEM_AUDIT.md` is now integration-complete reference evidence
  pending retirement after the current Phase 7 proof/cleanup gate.
  `MP-340`,
  `MP-355`,
  and the current `MP-377` priority ladder is now explicit: `P0` = coherence,
  identity, registry, lifecycle, approvals, `map`, evidence bridge, and parity
  contracts; `P1` = product-operability, packaging/adoption, and full client/
  mode parity; `P2` = later enrichments that must not bypass the spine. Latest
  audit-intake sequencing: the 2026-03-16 architecture re-audit is now phased
  under that ladder instead of treated as a flat backlog. Current execution is
  limited to the `P0` contract-freeze tranche (`ActionResult`,
  `CommandGoalTaxonomy`, `RepoMapSnapshot` / `MapFocusQuery` /
  `TargetedCheckPlan`, attach/auth + service identity, write arbitration,
  degraded-mode, `Finding`/schema/artifact compatibility, and the first typed
  split between deterministic AI-fix packets and reusable design-decision
  packets with policy-owned auto-apply/recommend/approval semantics for the
  same AI/human evidence contract). Latest concrete landing (2026-03-17):
  `probe-report` now emits typed decision packets from `.probe-allowlist.json`
  `design_decision` entries with explicit decision modes and validation steps,
  so the self-hosting packet matches that contract instead of exposing a
  maintainer-only review bucket; latest contract-closure follow-up
  (2026-03-17): `check_platform_contract_closure.py` now enforces bounded
  closure between the shared blueprint, current runtime dataclass contracts,
  durable artifact schema metadata, and startup-surface command routing for
  the already-real platform families, with repo policy, bundles, and
  maintainer docs updated in the same slice;
  packaging/
  adoption/client-parity remains `P1`, and proof/scale extensions remain `P2`.
  `MP-358`, and `MP-359` are subordinate implementation lanes inside this
  boundary, not alternate product architectures. Immediate separation-first
  queue: remove direct `repo_packs.voiceterm` imports from portable/runtime
  layers, stop frontend imports of repo-internal `devctl` modules and bridge
  files, move typed JSON/runtime state to live authority over `bridge.md`
  while keeping markdown as an optional backend-fed mode/projection, freeze
  the VoiceTerm operator-shell boundary over the same backend used by
  CLI/PyQt6/phone, add one simple backend-owned agent lifecycle
  `ensure/start/resume/stop` surface for all clients, and push remaining
  VoiceTerm-only env/log/process defaults into adopter-layer wiring. Keep
  landing new loop/control-plane capability behind reusable seams while this
  extraction work is active; do not keep widening the VoiceTerm-embedded shape
  and defer separation to a later cleanup pass.
  Completion proof now explicitly includes collaboration-mode parity: the same
  system must work for `Codex+Claude`, `human+Claude`, and `human+tools-only`
  operation with one backend truth, the same routed checks, and the same
  operator-visible progress semantics across chat/CLI/PyQt6/phone/overlay.
  Naming/abstraction proof is now explicit too: keep the backend command/action
  inventory complete and stable, then project simpler user-facing aliases,
  skills, slash commands, and client buttons grouped by user goal (`inspect`,
  `review`, `fix`, `run`, `control`, `adopt`, `publish`, `maintain`) so the
  system stays understandable without hiding major architecture surfaces like
  review packets, control-plane loops, operator/device controls, portability,
  release/reporting flows, and whole-system maintenance/cleanup. Those
  user-facing wrappers should be repo-pack/policy configurable so developers
  and agent adopters can tune names/defaults without patching the portable
  core. Deep architecture review on 2026-03-16 also tightened the glue
  contract here: `Finding` stays the canonical evidence record and now needs
  family-wide migration, command/service outcomes need one typed
  `ActionResult` envelope, durable machine-output families need explicit
  schema-version coverage, and grouped command discovery must stay tied to the
  same command-goal taxonomy rather than drifting into ad hoc per-client help
  text. Do not demote multi-client write arbitration to later polish; many
  shells over one backend makes it part of the spine. The first concrete
  lifecycle/control-plane follow-up is now the shared
  `review-channel ensure/watch` slice so reviewer heartbeat/update publishing
  and mode-aware liveness move into the backend instead of remaining chat/MD
  habits. The first publisher step in that slice now exists as
  `review-channel ensure --follow`, which advances reviewer heartbeat on
  cadence and emits structured status frames, but controller-owned supervision
  and auto-start lifecycle still remain open. The newer
  `--start-publisher-if-missing` seam is real progress, but active dual-agent
  mode still false-greens when the publisher is missing because that lifecycle
  state is not yet part of the shared attention/runtime truth. The recent
  5-hour Claude wait also proved the same controller path still lacks timeout
  budgets, overdue escalation, and clean stop/cleanup semantics, so those are
  now part of the same lifecycle contract instead of future operator polish.
  The bounded M55 truth slice is now accepted, and the bounded M63 timeout/
  escalation slice is accepted too: the shared reviewer/coder loop now emits
  machine-readable `reviewer_overdue` attention with a configurable threshold.
  The bounded M64 clean-stop slice is accepted too: direct follow-backed
  controller runs now emit explicit stop reasons plus final publisher state.
  The bounded M65 detached publisher durability slice is accepted too:
  detached start now records `failed_start`, and later dead-PID reads infer
  `detached_exit` instead of leaving blank stop state. The bounded M66
  publisher-lifecycle attention slice is accepted too: shared attention/runtime
  state now distinguishes `failed_start` and `detached_exit` instead of
  collapsing both into generic `publisher_missing`, with the focused
  review-channel/runtime bundle green (`135` passing). The first bounded M67
  reviewer-worker seam is accepted too: `review-channel status`, `ensure`,
  `reviewer-heartbeat`, `reviewer-checkpoint`, and bridge-backed `full.json`
  projections now emit machine-readable `reviewer_worker` state, while
  `ensure --follow` cadence frames surface `review_needed` without pretending
  semantic review already happened. The bounded `M68` report-only supervisor/
  watch slice is accepted too: `reviewer-heartbeat --follow` now polls on
  cadence, refreshes reviewer heartbeat through the same repo-owned Python
  seam, and emits operator-visible `reviewer_worker` frames without claiming
  semantic review completion, with current local re-review green (`122`
  review-channel tests plus `check_review_channel_bridge.py`). The larger
  reviewer-lane blocker still remains explicit: the current Codex reviewer path
  is still chat-bound rather than a repo-owned persistent reviewer
  worker/service, so the loop can still stall even while Claude keeps polling
  correctly. The next bounded follow-up inside that blocker is now `M69`: add
  repo-owned detached lifecycle/status truth for the report-only supervisor
  path so it can stay alive and observable outside the current terminal/chat
  session before widening into semantic review automation. The first `M69`
  cleanup on the current local diff is already in: bridge-backed `status` and
  `_build_reviewer_state_report()` now reuse the already-computed
  `status_snapshot.reviewer_worker` value instead of re-running
  `check_review_needed()`, and the supporting lifecycle/follow helper split
  keeps `check_code_shape.py` green while preserving the same reviewer-worker
  contract. The next same-scope cleanup is in too: both extracted
  `output_error` follow-loop exits now persist final stopped publisher/
  supervisor heartbeat state, lifecycle reads treat explicit stop records as
  not running even if the writer PID is still briefly alive while the CLI
  unwinds, and lifecycle heartbeats now persist per-PID variants so readers
  can select the freshest live publisher/supervisor writer before falling back
  to the freshest stopped/dead record. That closes the bounded `M69`
  detached-lifecycle truth seam on the current local diff. The next same-scope
  platform contract now keeps repo/worktree-scoped service identity and
  discovery plus backend attach/auth semantics in the accepted local baseline:
  the Python `devctl/review_channel` seam emits stable `service_identity` and
  `attach_auth_policy` payloads across bridge-backed status/report/projection
  surfaces so clients attach to the correct repo/worktree instance and the
  current local-only approval boundary is explicit. The next same-scope
  daemon-event to runtime-state reducer is now in too: live publisher and
  reviewer-supervisor follow loops append `daemon_started` /
  `daemon_heartbeat` / `daemon_stopped` rows into the structured event log,
  bridge-backed `status` now derives both runtime daemons from persisted
  lifecycle heartbeat truth instead of hard-coding an empty supervisor,
  `latest.md` renders that same runtime block for operators, and auto
  event-backed status stays gated on materialized `state.json` so daemon-only
  event logs do not silently flip authority. The next same-scope follow-up is
  now the retirement path for VoiceTerm-local action brokerage so the "one
  backend" claim becomes executable rather than aspirational. Preferred
  end-state is now explicit too:
  VoiceTerm should host/supervise that shared daemon/controller stack as the
  best local shell when present, but the same backend must remain
  directly attachable by CLI, PyQt6, phone/mobile, and skills/hooks without
  hidden VoiceTerm-only orchestration. The existing VoiceTerm daemon/session
  transport is necessary, but it is not yet the controller loop: PTY/session
  attach and terminal packet staging do not by themselves satisfy reviewer
  heartbeat, agent lifecycle `ensure/watch`, queue/action routing, or shared
  review/control-state publishing. Publisher/supervisor daemons are runtime
  infrastructure and projection health only; they may report
  `runtime_missing`, but they must not rewrite reviewer/session mode
  authority. The next controller follow-up should upgrade that daemon role
  from passive bridge watcher to bounded round supervisor: fresh agent
  invocation/re-entry, explicit ACK deadlines, and no-progress/error-repeat
  circuit breakers sourced from typed session state rather than markdown
  polling alone.

Control-plane program sequencing (maps to MP-330/331/332/336/338/340/355/360..367):

1. Ship canonical multi-view controller state projections (`full/compact/trace/actions`) from one packet source.
2. Add SSH-first/iPhone-safe read surfaces (`phone-status`) and Rust Dev-panel parity for run/agent/policy visibility.
3. Land the dedicated review-channel state/event contract and multi-format
   projections as a review-focused profile over the broader
   `controller_state` direction so reviewer/coder communication is packetized
   instead of living in hidden chat state.
4. Add a shared-screen VoiceTerm review surface that shows Codex, Claude, and
   operator lanes together while keeping early PTY ownership separate.
5. Keep desktop GUI clients non-canonical; allow only thin optional wrappers
   over Rust surfaces (`--dev`, future shared-screen review UI),
   `phone-status`, `controller-action`, and `devctl` APIs.
6. Freeze a typed queue/action path (`plan item`/packet/operator intent ->
   queue record -> typed action -> adapter/runtime handler -> receipt/state)
   so VoiceTerm stages and renders actions without becoming a second backend.
7. Add guarded operator actions (`dispatch-report-only`, `pause`, `resume`, `refresh`) with full audit logging.
8. Add reviewer-agent packet ingestion lane so loop-review feedback is machine-consumable, not manual copy/paste.
9. Add charted KPI trend surfaces (loop throughput, unresolved trend, mutation trend, automation-vs-AI mix) for architect decisions.
10. Add deterministic learning loop (`fingerprint -> playbook -> confidence -> guarded promote/decay`) with explicit evidence.
11. Promote staged write controls and any true shared-session mode only after replay protection + branch-protection-aware promotion guards are verified.

## Deferred Plans

- `dev/deferred/DEV_MODE_PLAN.md` (paused until Phases 1-2 outcomes are complete).
- MP-089 LLM-assisted voice-to-command generation (optional local/API provider) is deferred; current product focus is Codex/Claude CLI-native flow quality, not an additional LLM mediation layer.
- Post-next-release MP-346 backlog: stabilize Gemini startup/HUD flash behavior in `cursor` and `jetbrains` via adapter-owned policy paths (no new mixed host/provider branching outside adapter/runtime-profile ownership), with checkpoint + matrix evidence before closure.
- Post-next-release MP-346 backlog: investigate JetBrains+Claude non-regressive render-sync artifacts seen during long-output sessions (intermittent help/settings overlay flashing and duplicated bottom status-strip/HUD rows after short replies), capture focused logs/screenshots, and route fixes through adapter/runtime-profile ownership paths.
- Post-next-release MP-346 backlog: start AntiGravity reactivation readiness intake by defining runtime host fingerprint requirements and a compatibility-test design for `codex`/`claude`/`gemini` expectations before lifting deferred scope.
- Post-next-release MP-348 backlog: Codex red/green diff-era composer/input-row occlusion investigation is explicitly deferred until after release and requires logs+screenshot evidence before any runtime change.
- Post-next-release MP-349 backlog: Cursor+Claude plan-mode history/HUD corruption and transient garbled terminal output is explicitly deferred until after release; resize/readjust-driven recovery is a primary diagnostic clue for geometry/redraw synchronization investigation.
- AntiGravity host support is deferred until runtime fingerprint evidence
  exists; current release-scope MP-346 matrix closure is IDE-first
  (`cursor`, `jetbrains`), while `other` host validation is explicit
  post-next-release backlog.

## Release Policy (Checklist)

1. Confirm version parity and changelog readiness (`rust/Cargo.toml`,
   `pypi/pyproject.toml`, app plist, `dev/CHANGELOG.md`).
2. Run release verification bundle (`bundle.release`).
3. Run and wait for `release_preflight.yml` success for the exact target
   version/SHA.
4. Create/tag release from `master` only after same-SHA preflight success.
5. Monitor publish workflows (`publish_pypi`, `publish_homebrew`,
   `publish_release_binaries`, `release_attestation`) and verify PyPI payload
   (`https://pypi.org/pypi/voiceterm/<version>/json`).
6. Use local manual publish fallbacks only if workflows are unavailable.

## Execution Gate (Every Feature)

1. Create or link an MP item before implementation.
2. Implement the feature and add/update tests in the same change.
3. Run SDLC verification for scope:
   `python3 dev/scripts/devctl.py check --profile ci`
4. Run docs coverage check for user-facing work:
   `python3 dev/scripts/devctl.py docs-check --user-facing`
5. Update required docs (`dev/CHANGELOG.md` + relevant guides) before merge.
6. Push only after checks pass and plan/docs are aligned.

## References

- Execution + release tracking: `dev/active/MASTER_PLAN.md`
- Theme Studio architecture + gate checklist + consolidated overlay research/redesign detail: `dev/active/theme_upgrade.md`
- Memory + Action Studio architecture + gate checklist: `dev/active/memory_studio.md`
- Pre-release architecture/tooling cleanup execution plan: `dev/active/pre_release_architecture_audit.md`
- Consolidated full-surface audit findings evidence (reference-only): `dev/active/audit.md`
- Raw multi-agent audit merge transcript evidence (reference-only): `dev/active/move.md`
- Devctl MCP + contract alignment guide: `dev/MCP_DEVCTL_ALIGNMENT.md`
- Autonomous loop + mobile control-plane execution spec: `dev/active/autonomous_control_plane.md`
- Loop artifact-to-chat suggestion coordination runbook: `dev/active/loop_chat_bridge.md`
- IDE/provider adapter modularization execution spec: `dev/active/ide_provider_modularization.md`
- Standalone slash command plan (Codex/Claude without overlay): `dev/active/slash_command_standalone.md`
- SDLC policy: `AGENTS.md`
- Architecture: `dev/ARCHITECTURE.md`
- Changelog: `dev/CHANGELOG.md`

## Archive Log

- `dev/archive/2026-03-05-devctl-mcp-contract-hardening.md`
- `dev/archive/2026-01-29-claudeaudit-completed.md`
- `dev/archive/2026-01-29-docs-governance.md`
- `dev/archive/2026-02-01-terminal-restore-guard.md`
- `dev/archive/2026-02-01-transcript-queue-flush.md`
- `dev/archive/2026-02-02-release-audit-completed.md`
- `dev/archive/2026-02-17-tooling-control-plane-consolidation.md`
- `dev/archive/2026-02-20-senior-engineering-audit.md`
