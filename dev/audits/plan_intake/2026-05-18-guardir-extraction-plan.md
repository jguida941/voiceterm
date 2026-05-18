# Plan — GuardIR Extraction (Proof-Integrity → Plan/Packet Accountability → Multi-Repo POC → Identity Strip → VoiceTerm Quarantine)

## Context

On 2026-05-18 the devctl progress logger emitted `commit.complete sha=6cd8953a68cab904fed07f5bbad8638351f8cfb1; push is next` and `git-push ... returncode=0` to `origin feature/live-push` at 13:39-13:42Z. Empirically: commit `6cd8953a` does not exist (`git cat-file -t` returns bad object), `feature/live-push` does not exist locally or on origin, HEAD on `feature/governance-quality-sweep` remained `835060c2`. **The events log lied about commit and push success.** P0 = unverified events being consumed as proof.

Today's codex session was stopped via `kill -INT 5268`. The 69-path uncommitted governance patch + 3 untracked files + 2 dangling commits are preserved in `~/.cache/guardir-preserve/2026-05-18T14-22-00Z/` (SHA256-manifested) and pushed to `https://github.com/jguida941/guardir.git` as branch `preserve/guardir-extraction-unreviewed-2026-05-18` (verified by `git ls-remote` SHA match: `d92dc2ff6bce9830450b3f530dac3797fff8b7ce`). Origin (`jguida941/voiceterm.git`) is untouched at `835060c2`.

Operator strategic decision: VoiceTerm becomes an adopter/example shell; the portable governance engine moves to GuardIR. The false-proof bug is upstream of everything — if it stays, post-extraction "green" will lie just like post-commit "green" lied today. Therefore strict sequence: fix proof integrity FIRST, then plan/packet accountability, then prove POC on multiple repos, then identity strip, then shell strip, then dashboard, then role substrate.

**Operator's deeper priority surfaced 2026-05-18 ~11:10 EDT**: the thesis-level proof is "this engine works on many different types of repos, not hard-coded to VoiceTerm". Multi-repo POC is THE success proof, not a side effect. It must come early in the sequence (Phase 3), not be left until the end.

## Role Split (load-bearing — do not collapse)

- **Codex** = **implementer**. Writes the code for every phase. Owns red-then-green test cycles. Owns commit/push on `extraction/*` branches. **MAY delegate dogfood/verification/architect-review/cached-hammock-audit tasks to claude via typed `review-channel post` packets** (kind=`task_started` or `action_request`, target_role=`dashboard` or `reviewer`).
- **Claude** = **architect + tester + TDD + reviewer + verification runner + cached-hammock plan worker**. Reviews codex's design for typed-state-lies recurrence and fake-proof drift. Works the preserved cached-hammock plan at `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md` as parallel substrate. Runs verification (`devctl test-python`, `pytest -x`, `check-router`, direct `git rev-parse / git ls-remote / git show / git cat-file`) after each codex slice. Responds to codex's typed task packets with typed `finding` packets carrying dogfood evidence + receipt refs. May spawn multiple Explore/Plan agents in parallel for verification work. Surfaces issues before they become commits. Does NOT take the implementation lane.

**Bidirectional collaboration via typed system** (operator directive 2026-05-18 ~15:10 EDT — "you guys need to both start working together and you need to let Kodak know it's allowed to do out tasks to you"):
- Codex implements feature X → posts typed packet to claude (kind=`task_started` with target_ref=feature commit/test path) → claude dogfoods + verifies → claude posts typed `finding` packet back with dogfood receipt
- Every feature codex ships MUST be proved by claude's dogfood + receipt (no chat-prose acceptance, no events.jsonl narration as proof)
- Receipts land in typed state (`dev/state/git_mutation_proof_receipts.jsonl` after Phase 1; closure-proof receipts in `dev/state/plan_row_closure_receipts.jsonl`)
- If claude finds the feature broken on dogfood, claude posts `task_blocked` or `review_failed` packet back to codex with evidence_refs — system catches it before commit lands as "green"

The reason: claude caught today's events.jsonl-lying failure because claude observed real git state while codex built on events-log narration. Codex codes; claude verifies via typed packets + receipts; same-lane duplication = wasted work.

**Claude's explicit permission boundary** (per ChatGPT review 2026-05-18 ~15:25 EDT):

Claude MAY:
- run verification (devctl test-python, pytest -x, check-router)
- inspect git state directly (git rev-parse / git ls-remote / git show / git cat-file)
- spawn read-only Explore/Plan audit agents (multi-agent for verification work)
- post typed `finding` / `review_accepted` / `review_failed` / `task_blocked` packets
- dogfood codex's shipped features
- check that receipts exist + bind correctly
- verify no VoiceTerm/origin leakage
- verify no memory/plan sprawl
- preserve source files into `dev/audits/plan_intake/` with SHA256 manifest

Claude MUST NOT:
- create new plans (only edit the canonical extraction plan when operator explicitly requests amendment)
- mutate implementation files (codex's lane)
- create memory files (memory is pointer-only)
- rewrite canonical plan docs unless operator explicitly requests
- autonomously append addenda or "preservation context" markdown
- treat transcript/memory/bridge/events narration as authority
- take the implementation lane

Claude outputs MUST be one of: typed `finding`, typed `review_failed`, typed `task_blocked`, typed `review_accepted`, or explicit verification receipt. No chat-prose acceptance, no new memory/plan documents, no narration-as-proof.

## Comprehensive plan inventory (audit-verified — what must not be lost)

Audit Agent A5 inventoried **32 active plan files (1.8 MB)** in `dev/active/` + **1,778 rows** in `dev/state/plan_index.jsonl`. Landing-zone summary:

| Disposition | Count | Examples |
|---|---|---|
| `kept_core` | 12 files + ~1,000 rows | MASTER_PLAN, INDEX, ai_governance_platform, platform_authority_loop, autonomous_governance_loop_v2, portable_code_governance, review_probes, review_channel, remote_commit_pipeline, remote_control_runtime, PLAN_FORMAT, P102 typed-state work, MP-378 launch-bootstrap rows |
| `moved_to_adopter_voiceterm` | 8 files | operator_console.md (Qt6, 134 KB), theme_upgrade.md, MP377-MOBILE-CONTROL-ROOM-S1, MP-NEW-001 through MP-NEW-030 (30 VoiceTerm pilot rows), VoiceTerm daemon/surface names |
| `merged_into_guardir_plan` | 10 files | memory_studio.md, continuous_swarm.md, code_shape_expansion.md, devctl_reporting_upgrade.md, pre_release_architecture_audit.md, audit.md, agent_substrate_architecture_review.md, ide_provider_modularization.md, ralph_guardrail_control_plane.md, naming_api_cohesion.md, slash_command_standalone.md, MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1 |
| `archived_obsolete` | 4 files | move.md (raw audit merge transcript), phase2.md (bridge to deferred), CLAUDE_SESSION_AUTOMATION_SAFETY_DECLARATION, RUST_AUDIT_FINDINGS bridge |
| `needs_operator_decision` | 2+ files | autonomous_control_plane.md (mobile control-plane), host_process_hygiene.md, loop_chat_bridge.md |

**Operator-named embedded plans (found in audit — not separate docs, embedded in MP-377/MP-378):**
- Web browser / HTML dashboard plan: `may17th.md:18-46` + `MP377-GUARDIR-COMMAND-MODE-FRONTEND-ADAPTERS` plan row
- File-system bypass plan: `portable_code_governance.md:100-110` (P58.3 leakage points 1-10) + `dev/active/audit.md`
- Qt6 app plans: `dev/active/operator_console.md` (134 KB, MP-359, 81 sections) — moves to adopter
- Type digestion (typed state) plans: `ai_governance_platform.md` P102 typestate sections + `platform_authority_loop.md` — kept_core, already integrated into MP-377

**Repo matrix + statistics (audit-verified existing infrastructure):**
- External Python Repo Matrix: `dev/active/portable_code_governance.md:104-117` (9 repos, 4 buckets, Wave 1 = 5 complete)
- External pilot findings: `dev/reports/governance/external_pilot_findings.jsonl` (882 rows; `finding_class:null` on all — classification backfill needed)
- Autonomy benchmark: `dev/reports/autonomy/mp342-344-baseline-matrix-20260225.{json,md}` (12 scenarios, 36 swarms, 100% success) + live-baseline (4 scenarios, 12 swarms, 100%)
- Adopter pilot gate `MP377-ADOPTER-PILOT-GATE-S1` PASSED on 2 fixture repos: `greenfield_python` + `existing_plan_python` (508 hints each, `dev/reports/probes/latest/summary.json` exists)
- PortabilityLeakInventory: NOT YET CREATED as typed PlanRow entries — 22 blockers documented as prose only in `ai_governance_platform.md:1150-1155`

## Cached-hammock plan (CRITICAL — preserve before any other work)

Audit Agent A7 confirmed the cached-hammock plan lives at:

**`/Users/jguida941/.claude/plans/do-that-and-in-cached-hammock.md` — 4,314 lines, OUTSIDE the repo entirely.**

It is NOT in any preservation snapshot, NOT in GuardIR, NOT in VoiceTerm. This is the literal "afraid losing" file. It contains 20+ unresolved findings the operator was actively surfacing across 3 multi-agent investigation rounds (May 12-16). Specific findings (each requiring a Phase-N landing zone in this plan, not vague Phase 6 deferral):

| Cached-hammock section | Finding | Maps to phase |
|---|---|---|
| P1 FeatureShipLifecycle | Precondition `task_produced` exists but `check_router` lacks task-class routing | Phase 1 (proof integrity) |
| P3 Receipt Schema | 4 missing fields in unified envelope (reason_for_risk_level, needs_codex_action, needs_claude_verification, unresolved_issues) | Phase 1.5 |
| P6 CognitiveRoleFleet | 8 roles exist as chat-prose only; no typed state, no slash commands, no operator editability | Phase 6 (role substrate) |
| P10 Provider/Model Contracts | Portable AI integration layer missing; only VoiceTerm bindings exist | Phase 2 (identity strip) |
| P13-P32 Composable Extensions | 20 priorities lack composition verification and lifecycle wiring | Phase 1.5 |
| P53 GuardCoverageGapLedger | 52 architectural gaps; no typed surface recording which guard SHOULD have caught each | Phase 5 (dashboard) |
| P55 /guardlab Mode | Development-mode command for surfacing guard gaps + self-discovery probes missing | Phase 5 |
| P56 Charter Ingestion | P1-P56 exists in markdown only; NOT YET ingested into `dev/state/plan_index.jsonl` | Phase 2.5 (migration map) |
| P57 Consolidation | Duplicate authority across P1+P3+P4 receipt schemas; should unify to `UnifiedReceiptEnvelope` | Phase 1 |
| P59 Referential Integrity | No guard verifies `_ref` fields across JSONL stores point to valid target rows | Phase 1.5 |
| P60 State Machine Coverage | 12 lifecycle contracts lack guard ensuring all enum states have transitions + receipts | Phase 1.5 |
| P62 MetaCoverageInvariant | No typed surface fires when investigation gap-density exceeds policy threshold | Phase 5 |
| P65-P74 Source-of-Truth Registry | Multiple review/control shapes emitted across backend/clients; identity still absolute paths | Phase 0.5 (PII path guard) |
| P75-P82 AI Coding Lifecycle | 5-stage chain (LEX/PARSE/SEMANTIC/CODEGEN/LINK) partially incomplete; missing stage blocks gates | Phase 1 |
| Bridge Authority Retirement | 52 bridge-backed fields not yet mapped to typed sources; deprecation plan incomplete | Phase 2 |
| P195-P198 Cloud Proof | 25 typed slices queued but genuinely UNIMPLEMENTED; starting from ZERO code | Phase 3 (multi-repo CI) |
| Proof Index Caching | Hybrid `proof_index.jsonl` + `.cache/proof_index.sqlite` NOT YET IMPLEMENTED (~25-230ms compute) | Phase 5 |
| DogfoodRecord Integration | ~90% governance pipeline exists; missing wiring to unified receipt system | Phase 1.5 |
| BypassReceipt CLI Surface | `devctl bypass` subcommand not registered; only legacy `/bypass` slash adapter exists | Phase 2 |
| Cognitive role fleet missing | 6 components: CognitiveRoleFleetAssignment, config file, CLI subcommand family, slash adapters, agents.json field, startup integration | Phase 6 |

**Phase 0 MUST preserve `~/.claude/plans/do-that-and-in-cached-hammock.md` into the repo before any other work.** Specifically, copy it to `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md` (per ChatGPT amendment #9 source-snapshot-durability decision) and reference it from `dev/state/plan_index.jsonl` as the typed source for the findings table above.

## Existing plans this composes with

- `dev/active/ai_governance_platform.md` — canonical MP-377 Phase 4 extraction authority around lines 4204-4222
- `dev/active/portable_code_governance.md:56-73` — Second-Repo Proof Ladder (7 gates ensuring engine runs on 2+ external repos with no core patches)
- `dev/active/portable_code_governance.md:104-117` — External Python Repo Matrix (4-bucket structure)
- `may17th.md` — operative cloud-dashboard-repo-split plan (now in preservation snapshot)
- `may17th.md:67` — MP-GOVERNANCE-ECOSYSTEM-INTEGRATION-S1 (cached-hammock:1761) cached-hammock ↔ CI integration point
- Plan rows: `MP377-VOICETERM-EXTRACTION-S1`, `MP377-ADOPTER-PILOT-GATE-S1`, `MP377-GUARDIR-V21-PORTABILITY` (PortabilityLeakInventory, 22 blockers), `MP377-GUARDIR-V21-RUNTIME-AGREEMENT` (ADR-013 RuntimeAgreementReport), `MP-NEW-P194-S1-REPO-EXTRACTION-PHASE-1`, `MP377-P0-MAY17-CLOUD-DASHBOARD-REPO-SPLIT-S1`, `MP377-P0-CACHED-HAMMOCK-ROLE-AUDIT-S1`

---

## Revised phase sequence (per ChatGPT amendments + audit findings)

### Phase 0 — Freeze / Preserve / Verify (no implementation edits)

**Step 0.0 — Quarantine 228 orphan feedback_*.md files** (operator + ChatGPT directive 2026-05-18 ~15:10 EDT):

The memory dir at `/Users/jguida941/.claude/projects/-Users-jguida941-testing-upgrade-codex-voice/memory/` has 228 `feedback_*.md` files orphaned from prior sessions. MEMORY.md (now gutted to 70-line pointer table) doesn't reference them. Do NOT delete — quarantine as evidence:

```bash
mkdir -p ~/.cache/guardir-memory-archive/2026-05-18-feedback-orphans
mv ~/.claude/projects/-Users-jguida941-testing-upgrade-codex-voice/memory/feedback_*.md ~/.cache/guardir-memory-archive/2026-05-18-feedback-orphans/
find ~/.cache/guardir-memory-archive/2026-05-18-feedback-orphans -type f -print0 | sort -z | xargs -0 shasum -a 256 > ~/.cache/guardir-memory-archive/2026-05-18-feedback-orphans.sha256
```

Add ONE pointer line to MEMORY.md (no content copied):
> Archived orphan feedback files: `~/.cache/guardir-memory-archive/2026-05-18-feedback-orphans/` — evidence only, not active memory or planning authority.

**Step 0.1 — Preserve cached-hammock + may17 + approved plan** (DONE 2026-05-18T~14:50Z via commit `ccf6b4f5` + auto post-commit `bf21b66a`, pushed to guardir `extraction/guardir-core-p0-proof-integrity`):

```bash
# Already executed — leave as evidence
ls dev/audits/plan_intake/  # 2026-05-18-cached-hammock-role-audit.md, 2026-05-18-guardir-extraction-plan.md, 2026-05-18-may17-plan.md, sha256-manifest.txt
```

Typed PlanRow `GUARDIR-EXTRACTION-MASTER-PLAN-2026-05-18-S1` added to `dev/state/plan_index.jsonl` (1778 → 1779 rows).

**Step 0.2 — Verify GuardIR state + SHA reconciliation** (operator-flagged via ChatGPT 2026-05-18 ~15:00 EDT):

Two commits both reachable from preserve branch (verified inline 2026-05-18T~15:15):
- `d92dc2ff6bce9830450b3f530dac3797fff8b7ce` — auto post-commit ReviewSnapshot ("Refresh external review snapshot for 92ef4032"); current preserve branch HEAD
- `92ef403200300169fe3e43b966c9e8288354b340` — UNREVIEWED PRESERVATION SNAPSHOT (parent of `d92dc2ff`; the actual content commit with the 6246-line preservation payload)
- Chain: `835060c2 (origin yesterday)` ← `92ef4032 (preservation content)` ← `d92dc2ff (auto-snapshot artifact)`

Verification commands (run before any trunk creation):
```bash
git remote -v
git ls-remote guardir refs/heads/preserve/guardir-extraction-unreviewed-2026-05-18    # expect d92dc2ff
git ls-remote guardir refs/heads/extraction/guardir-core-p0-proof-integrity           # expect bf21b66a (will become ccf6b4f5-or-newer after Phase 0.4 sync)
git rev-parse HEAD
git status --short
git show --no-patch --format="%H | %s | parent: %P" 92ef403200300169fe3e43b966c9e8288354b340  # expect parent 835060c2
git show --no-patch --format="%H | %s | parent: %P" d92dc2ff6bce9830450b3f530dac3797fff8b7ce  # expect parent 92ef4032
shasum -c ~/.cache/guardir-preserve/2026-05-18T14-22-00Z/sha256-manifest.txt  # bundle integrity
wc -l dev/active/MASTER_PLAN.md                                               # ChatGPT-flagged anomaly: connector returned empty; verify locally that MASTER_PLAN is not actually empty
sed -n '1,5p' dev/active/MASTER_PLAN.md                                       # confirm tracker is alive; if empty, that's a governance defect, NOT just a documentation quirk
```

**Step 0.3 — Create GuardIR trunk from content commit (NOT from auto-snapshot)**:

Use `92ef4032` (the actual UNREVIEWED PRESERVATION SNAPSHOT content) as trunk root, NOT `d92dc2ff` (which is just the auto-snapshot refresh for `92ef4032`). Trunk should anchor on meaningful content, not generated-surface artifacts.

**CRITICAL SEQUENCE (per ChatGPT review 2026-05-18 ~15:50 EDT — must REPLAY preservation commits, not drop them)**:

The existing `extraction/guardir-core-p0-proof-integrity` already contains preservation commit `ccf6b4f5` (Phase 0.1: cached-hammock + may17 + plan-intake) + its auto-snapshot `bf21b66a`. A naive `git checkout -B extraction guardir-main` would DROP those preservation commits. Use cherry-pick replay:

```bash
# Step A — Create trunk from meaningful preservation content commit (NOT the auto-snapshot artifact)
git checkout -B guardir-main 92ef403200300169fe3e43b966c9e8288354b340
git push guardir guardir-main
# If the governed push fails, inspect the hook output. Raw bypass is acceptable ONLY when blocked solely because Phase 1 P0 not yet implemented; label as bootstrap exception.
# Then if and only if confirmed: git push --no-verify guardir guardir-main    # governed first; raw fallback only if hooks block
git ls-remote guardir refs/heads/guardir-main                                  # verify remote SHA matches 92ef4032

# Step B — Rebuild extraction off trunk, REPLAY preservation commits
git checkout -B extraction/guardir-core-p0-proof-integrity guardir-main
git cherry-pick ccf6b4f5f21cad5d290d90fe79d332178ceaded1                       # Phase 0.1 preservation (cached-hammock + may17 + plan-intake + plan_index.jsonl row)
# Do NOT replay bf21b66a — it's only the auto ReviewSnapshot refresh for ccf6b4f5; the new HEAD's auto-snapshot will be regenerated

# Step C — Phase 0.4 plan-sync (applied on top of replayed preservation)
cp /Users/jguida941/.claude/plans/yes-now-that-the-synthetic-pinwheel.md dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md
shasum -a 256 dev/audits/plan_intake/*.md > dev/audits/plan_intake/sha256-manifest.txt
git add dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md dev/audits/plan_intake/sha256-manifest.txt
git commit -m "Phase 0.4: Sync canonical GuardIR extraction plan — plan synchronization only; Phase 1 proof-integrity not yet implemented"

# Step D — Push extraction with --force-with-lease (remote diverged due to rebuild)
git push --force-with-lease guardir extraction/guardir-core-p0-proof-integrity
# If hook blocks: inspect output, confirm cause is Phase 1 P0 not yet implemented, then explicitly:
# git push --no-verify --force-with-lease guardir extraction/guardir-core-p0-proof-integrity

# Step E — Verify
git ls-remote guardir refs/heads/extraction/guardir-core-p0-proof-integrity     # should match new local HEAD
git log --oneline guardir-main..extraction/guardir-core-p0-proof-integrity      # should show ccf6b4f5 + Phase 0.4 commit + auto-snapshot
```

After this:
- `preserve/guardir-extraction-unreviewed-2026-05-18` = **immutable evidence locker** at `d92dc2ff` (no normal commits ever)
- `guardir-main` = real trunk baseline, rooted at content commit `92ef4032`
- `extraction/guardir-core-p0-proof-integrity` = real working branch rooted at `guardir-main`, with replayed preservation + plan-sync commits

The identity check `check_guardir_remote_identity.py` (Phase 0.5.A) MUST fail if the current branch starts with `preserve/` or `feature/governance-quality-sweep`.

**Step 0.4 — Canonical plan synchronization + drift guard** (per ChatGPT review 2026-05-18 ~15:40 EDT — **BLOCKING; do this BEFORE codex restart**):

The latest operator-approved plan text (this file at `/Users/jguida941/.claude/plans/yes-now-that-the-synthetic-pinwheel.md`) is **materially newer** than the committed `dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md` (~558-line older version). Stale committed plan would cause codex to root trunk on `d92dc2ff` (generated artifact) instead of `92ef4032` (content commit), and would skip Phase 0.0 quarantine, Phase 0.4 drift guard, Phase 1.25, Phase 1.75 RED baseline, and the tightened Claude verification boundary.

**Mandatory sync before any codex restart**:

```bash
git checkout extraction/guardir-core-p0-proof-integrity
cp /Users/jguida941/.claude/plans/yes-now-that-the-synthetic-pinwheel.md dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md
shasum -a 256 dev/audits/plan_intake/*.md > dev/audits/plan_intake/sha256-manifest.txt
git diff -- dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md dev/audits/plan_intake/sha256-manifest.txt
# Then governed-commit the plan-sync change (raw --no-verify if Phase 1 P0 not yet implemented).
# Commit message: "Phase 0.4: Sync canonical GuardIR extraction plan — plan synchronization only; Phase 1 proof-integrity is not yet implemented."
git push guardir extraction/guardir-core-p0-proof-integrity  # governed first; --no-verify only if hooks block
```

**Plan freshness guard family (6 checks, all wired into `check-router` default bundle)**:

| Check | Blocks when |
|---|---|
| `check_guardir_extraction_plan_current.py` | Committed canonical plan differs from approved plan SHA / no typed PlanRow references it / competing plan-prose files exist / MEMORY/feedback files contain active-plan authority |
| `check_plan_source_snapshot_freshness.py` | PlanRows point to old/missing source hashes; `PlanSourceSnapshot` SHA doesn't match current source file SHA |
| `check_plan_row_source_refs.py` | PlanRows lack `source_doc_path` + `source_doc_sha256` + `source_section_id` + `plan_revision_id` |
| `check_packet_plan_ref_integrity.py` | Packets reference plan rows without `plan_revision_id` + `source_snapshot_id` |
| `check_plan_code_drift.py` | A commit changed files in a PlanRow's `target_ref` scope AND that PlanRow has no new `ValidationReceipt` after the commit AND no `PlanAmendmentReceipt` / `PlanRowClosureReceipt` / `NoPlanUpdateNeededReceipt` |
| `check_no_unbound_plan_packet_clearance.py` | Plan-bearing packets clear via expiry/absorption/ack without durable binding (also Phase 1.5) |

**SourceTruthRef format** (typed references that include identity + revision; invariant: "no packet, PlanRow, receipt, or closure can reference mutable authority without a revision/hash"):

```
plan-source://guardir/dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md@sha256:<hash>#section:phase-1
plan-row://guardir/GUARDIR-EXTRACTION-MASTER-PLAN-2026-05-18-S1@revision:<rev>
packet://review-channel/<packet_id>@projection:<snapshot_id>
git://jguida941/guardir@<commit_sha>:dev/scripts/checks/check_commit_complete_proof.py
receipt://git-mutation-proof/<receipt_id>@sha256:<hash>
```

Phase 0.4 lands the FIRST check (`check_guardir_extraction_plan_current.py`) as blocking; the remaining 5 land in Phase 1.5 alongside the typed contracts.

**`check_guardir_extraction_plan_current.py` design constraints (per ChatGPT review 2026-05-18 ~15:50 EDT — no absolute local paths in default/CI mode)**:

Default-mode authority sources (repo-local only, no `/Users/...`):
- `dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md`
- `dev/audits/plan_intake/sha256-manifest.txt`
- `dev/state/plan_index.jsonl`
- `dev/state/plan_source_snapshots.jsonl`
- `dev/state/plan_amendment_receipts.jsonl` (after Phase 1.5)

Optional operator-sync override via env var (NOT required for default/CI mode):
```bash
GUARDIR_APPROVED_PLAN_PATH=/Users/jguida941/.claude/plans/yes-now-that-the-synthetic-pinwheel.md \
  python3 dev/scripts/checks/check_guardir_extraction_plan_current.py
```

**Phase 0.4 has TWO modes** (per ChatGPT review 2026-05-18 ~16:00 EDT — avoid circular dependency where Phase 0.4 requires Phase 1.5 contracts):

**Minimal mode (lands NOW, before codex implements Phase 0.5/1)** — `python3 dev/scripts/checks/check_guardir_extraction_plan_current.py --mode minimal`:
1. Canonical plan file `dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md` exists
2. Its SHA matches `dev/audits/plan_intake/sha256-manifest.txt`
3. `dev/state/plan_index.jsonl` has `GUARDIR-EXTRACTION-MASTER-PLAN-2026-05-18-S1`
4. If a `PlanSourceSnapshot` row for the plan path already exists in `dev/state/plan_source_snapshots.jsonl`, it MUST NOT contradict the canonical plan path/hash. Full `source_snapshot_id` / `plan_revision_id` enforcement is deferred to strict mode.
5. No competing plan/addendum files exist outside the canonical plan path (guard greps `dev/audits/plan_intake/` and `dev/active/` for stray `*extraction*plan*.md`)
6. `MEMORY.md` and `feedback_*.md` files in memory dir are pointer-only (no active plan authority)
7. Wired into `check-router` default bundle
8. Default mode does NOT require absolute local operator paths (`/Users/`, `/home/`, `C:\Users\`); optional `GUARDIR_APPROVED_PLAN_PATH` env var supports the operator-sync workflow only

**Strict mode (lands in Phase 1.5 after `PlanSourceSnapshot` extension + `PlanAmendmentReceipt` + PlanRow ref-binding fields exist)** — `python3 dev/scripts/checks/check_guardir_extraction_plan_current.py --mode strict`:
1. All minimal-mode criteria PLUS:
2. PlanRows for this extraction work have `source_doc_path` + `source_doc_sha256` + `source_snapshot_id` + `source_section_id` + `plan_revision_id` populated
3. Packets referencing those PlanRows have `plan_row_id` + `plan_revision_id` + `source_snapshot_id` populated
4. Current canonical plan file SHA matches the latest `PlanSourceSnapshot` row's `source_doc_sha256`
5. Plan changes since the last `PlanSourceSnapshot` snapshot are accompanied by a `PlanAmendmentReceipt` linking old → new revision
6. Stale packets referencing outdated `plan_revision_id` are surfaced as blockers (must revalidate or supersede)

**Step 0.5-prep — Branch policy is permanent**: never make `preserve/*` the long-term default branch. After Phase 1 P0 lands and `guardir-main` exists, promote `guardir-main` to default on GitHub via repo settings (separate operator action). `preserve/*` stays as evidence locker only, forever. ChatGPT confirmed via GitHub connector at ~15:40 EDT that GuardIR's current default IS still `preserve/guardir-extraction-unreviewed-2026-05-18` — that's acceptable only until Phase 1 lands.

### Phase 0.5 — Repo identity safety + PII/local-path safety gates (NEW per ChatGPT #1 #8)

Codex implements three new guards:

**0.5.A — `dev/scripts/checks/check_guardir_remote_identity.py`** — fails if:
- Publication target resolves to `jguida941/voiceterm.git`
- Current branch starts with `preserve/` or `feature/governance-quality-sweep`
- `repo_pack_id` resolves to `voiceterm` in publication-identity context (vs adopter-registration context)

**0.5.B — `dev/scripts/checks/check_no_absolute_local_paths.py`** (per ChatGPT #8, refined #4) — fails on LIVE generated state, repo-pack config, generated surfaces, or proof receipts containing `/Users/`, `/home/`, `C:\Users\`. MUST distinguish live state from historical audit evidence: preserved files under `dev/audits/plan_intake/` or `dev/fixtures/proof_integrity/` are EVIDENCE and MUST be allowlisted (`allowed_in=historical_only` / `fixture_only`). The guard fails on **NEW** leakage, not on preserved historical leakage. Critical because GuardIR is public-ish and live local paths in state break CI/adopter portability.

**0.5.C — Branch policy as repo checks** (per operator correction #9 from earlier round):
- `preserve/*` branches: evidence-locker only, no normal commits ever
- `extraction/*` branches: real working branches, require proof-integrity checks after Phase 1
- `guardir-main`: governed push only, no direct raw push

Wire all three into `check-router` default bundle.

### Phase 1 — Git Proof Integrity (REFINED per ChatGPT #2-#7)

**Architectural distinction** (per ChatGPT #3 — event naming split):
- `command.git_push.completed` / `command.git_commit.completed` = observed command-level events (not proof)
- `command.complete returncode=0` = observed (not proof)
- `git.commit.proof_verified` / `git.push.proof_verified` = downstream proof events, only emitted after a verified `GitMutationProofReceipt`
- `git.commit.proof_failed` / `git.push.proof_failed` = downstream rejection events

Dashboard/proof consumers ONLY accept `git.{commit,push}.proof_verified`. They NEVER accept `command.complete`, bridge narration, or events.jsonl narration as proof.

**1A — Typed contract `GitMutationProofReceipt`** (per ChatGPT #2):

```python
@dataclass(frozen=True)
class GitMutationProofReceipt:
    receipt_id: str                       # unique
    operation: Literal["commit", "push"]
    claimed_sha: str
    verified_local_sha: str               # git rev-parse --verify <sha>^{commit}
    verified_remote_sha: str              # git ls-remote <remote> <ref> (empty for commit op)
    intended_ref: str
    ref_before: str                       # ref state immediately before mutation (ChatGPT #5 binding)
    ref_after: str                        # ref state immediately after mutation
    remote_name: str                      # empty for commit op
    remote_url: str                       # empty for commit op
    repo_remote_resolved_url: str         # what git config resolved at receipt time (ChatGPT #5)
    repo_worktree_root_digest: str        # sha256 of git rev-parse --show-toplevel + .git/HEAD (binds receipt to specific worktree)
    command_argv_digest: str              # sha256 of the argv list (must match consumed event — ChatGPT #4)
    command_returncode: int
    event_id: str                         # bound to the events.jsonl event_id that claimed this proof
    event_path: str                       # bound to the events.jsonl path that contains the event
    push_report_path: str                 # bound to dev/reports/push/latest_push_report.json (empty for commit op)
    verified_at_utc: str
    verifier_version: str
    result: Literal["verified", "failed_verification"]
    failure_reason: str                   # empty when verified
    contract_id: str = "GitMutationProofReceipt"
    schema_version: int = 1
```

Receipt binds: WHO (repo worktree + remote), WHAT (operation + argv digest), WHERE (ref before/after + event_id + event_path + push_report_path), WHEN (verified_at_utc), and WITH-WHAT-PROOF (local/remote SHA + returncode). Faking proof requires forging ALL of these consistently — much harder than today's single-SHA-string fake.

**1B — Receipt storage** (per ChatGPT #2 storage path):

`dev/state/git_mutation_proof_receipts.jsonl` — append-only typed store. Each `commit.complete` / `push.complete` event MUST reference a `git_mutation_proof_receipt_id` field, otherwise consumers reject it.

**1C — Emission-time verification** (fail-closed at source):

- `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py:222` — wrap `emit_vcs_progress("commit.complete", f"recorded sha={commit_sha}; push is next")` so it constructs a `GitMutationProofReceipt` for `operation="commit"` BEFORE emit. On `result="failed_verification"`, emit `git.commit.proof_failed` (not `git.commit.proof_verified`) and raise.
- `dev/scripts/devctl/commands/vcs/push_flow.py:122` — wrap the `"git-push"` emission with `git ls-remote <remote> <ref>` verification; construct receipt before `git.push.proof_verified` becomes a proof event.
- `dev/scripts/devctl/runtime/stage_progress.py` (events.jsonl writer) — add `verify_git_proof_receipt_id_present` predicate at writer boundary for `git.*.proof_verified` event kinds.

**1D — Consumption-time guards** (defense in depth):

Mirror existing `dev/scripts/checks/check_command_output_consumed.py` / `check_non_trivial_output_proof.py` pattern:

- `dev/scripts/checks/check_commit_complete_proof.py` — verifies each `git.commit.proof_verified` event has a matching receipt with `result="verified"` AND `command_argv_digest` matches the event's argv digest (per ChatGPT #4)
- `dev/scripts/checks/check_push_complete_proof.py` — same for push; ALSO re-runs `git ls-remote <remote> <ref>` at consumption time (per ChatGPT #5 TOCTOU) and reports `push_proof_stale_remote_ref` if the ref moved (does not invalidate the original receipt, just marks it stale)
- `dev/scripts/checks/check_no_projection_proof_misuse.py` (per ChatGPT #4 + operator correction #4) — fails if any consumer accepts `bridge.md`, `events.jsonl command.complete`, agent narration, review snapshot prose, dashboard rows, or mobile transcript as git proof without a corresponding `GitMutationProofReceipt`

Wire all three into `check-router` default bundle.

**1E — Historical events handling** (per ChatGPT #6):

Do NOT rewrite history to erase today's bad event. Preserve it as evidence. Add compatibility rule:

- Historical events (created before this fix) may exist in `events.jsonl`
- They cannot be consumed as proof unless linked to a verified `GitMutationProofReceipt`
- The guard's failure mode for historical events: emit warning `historical_unverified_event` (not error) to allow grandfathering

**1F — Regression fixture** (per ChatGPT #7):

`dev/fixtures/proof_integrity/2026_05_18_false_commit_push/` containing:
- Minimal `events.jsonl` excerpt with the verbatim `commit.complete sha=6cd8953a...` event
- Minimal `events.jsonl` excerpt with the verbatim `git-push returncode=0` event for `feature/live-push`
- Minimal `latest_push_report.json` with the mismatch
- `README.md` explaining what each fixture proves

Tests load from these fixtures, NOT from live repo state — so the regression is reproducible forever even after the live repo evolves.

**1G — Regression tests** (per ChatGPT #3 — local bare remotes):

Codex creates tests using `git init --bare /tmp/guardir-test-remote-<uuid>.git` so the suite is deterministic and network-free. Test files:

- `dev/scripts/devctl/tests/checks/test_check_commit_complete_proof.py`
- `dev/scripts/devctl/tests/checks/test_check_push_complete_proof.py`
- `dev/scripts/devctl/tests/checks/test_check_no_projection_proof_misuse.py`
- `dev/scripts/devctl/tests/checks/test_check_no_absolute_local_paths.py`
- `dev/scripts/devctl/tests/checks/test_check_guardir_remote_identity.py`
- `dev/scripts/devctl/tests/runtime/test_git_mutation_proof_receipt.py`
- `dev/scripts/devctl/tests/runtime/test_stage_progress_proof_verification.py`
- `dev/scripts/devctl/tests/fixtures/test_2026_05_18_false_commit_push_regression.py`

Each test recreates today's failure modes:
- `commit.complete sha=6cd8953a...` for nonexistent SHA → guard rejects, no receipt exists
- `git-push returncode=0` to nonexistent local-bare ref → guard rejects, receipt missing remote-ref match
- Consumer attempts to read `bridge.md` "pushed" prose as proof → guard rejects via check_no_projection_proof_misuse
- `command_argv_digest` mismatch between receipt and event → guard rejects (covers ChatGPT #4)
- Re-verify-at-consumption catches stale remote ref → marked `push_proof_stale_remote_ref` (covers ChatGPT #5 TOCTOU)

Reuse existing test pattern from `dev/scripts/devctl/tests/runtime/test_governed_exception_contracts.py:129-140`.

### Phase 1.25 — post_action_request strict gate (NEW per ChatGPT #11)

`review-channel.post_action_request` allowed ONLY when:
- `--kind action_request`
- `requested_action=stage_commit_pipeline` (or whitelisted action name)
- `target_kind=runtime`
- `target_ref` starts with `devctl_commit:` (or whitelisted prefix)
- `target_revision` present
- `full_guard_bundle_evidence` present
- actor/role/session matches the active decision
- `proxy_authority_ref` matches exact decision/snapshot/latest event if proxy

Negative constraints (the things that often "look like" authority but aren't):
- `post_finding` cannot satisfy `action_request`
- `post_continuation_anchor` cannot satisfy `action_request`
- `post_stop_anchor` cannot satisfy `action_request`

Implementation files:
- `dev/scripts/devctl/runtime/post_action_request_gate.py` (new)
- `dev/scripts/checks/check_post_action_request_strict_gate.py` (new)
- `dev/scripts/devctl/tests/checks/test_check_post_action_request_strict_gate.py` (new — regressions for each negative case)

### Phase 1.5 — Plan/Packet Accountability + dashboard read-model criteria (REFINED per ChatGPT #10 + operator round)

**Invariant**: A plan-bearing packet cannot clear live pressure by expiry, ack, semantic ingestion, or absorption unless it has durable binding. Durable binding = ONE OF:
- `PlanRow` + `PlanIntentIngestionReceipt` + `PlanSourceSnapshot`
- Valid `action_request` (with target_kind + target_ref + requested_action + Phase 1.25 strict gate satisfied)
- Typed `finding` with reducer-visible state
- Explicit `rejected` / `deferred` / `blocked` / `superseded` receipt with full evidence fields
- Closure receipt: `FeatureProofReceipt` or `PlanRowClosureReceipt`

**Acceptance criteria across the dashboard/read-model layer** (per ChatGPT #10 — fixing one reducer is not enough):
- `develop next` MUST NOT drop unbound plan-bearing packets from its consideration set
- `review-channel inbox` MUST show unbound plan-bearing packets prominently
- `startup-context` MUST summarize unbound plan pressure count + IDs in its blockers section
- `dashboard/read-model` MUST expose live counts of: unbound plan-bearing packets, expired plan-bearing without ingestion, absorbed plan-bearing without durable binding
- `develop campaign` MUST surface these in its blocker summary
- **NEW (per ChatGPT review)**: if a packet was semantically ingested as `accepted` and no durable binding exists, absorption MUST either BLOCK or produce a typed `absorbed_unbound_plan_pressure` classification — NOT silently archive. This prevents `absorbed` from becoming the next fake-done state.

**Minimal accountability dashboard (per ChatGPT review — moved earlier)**: Phase 1.5 ships a thin `devctl dashboard --mode accountability --format md|json` view, NOT the full Phase 6 dashboard. Minimum fields:
- unbound plan-bearing packets (count + IDs)
- expired plan-bearing packets (count + IDs)
- absorbed-but-unbound packets (count + IDs, classified `absorbed_unbound_plan_pressure`)
- queued PlanRows without closure receipt (count + IDs)
- action_requests not consumed (count + IDs)
- proof events without `GitMutationProofReceipt` (count — surfaces residual Phase 1 gaps)
- current repo/remote/branch identity
- current blocker reason (one sentence summary)

This is a fast typed query against `dev/state/plan_index.jsonl` + `dev/reports/review_channel/*` + `dev/reports/progress/events.jsonl` + `dev/state/git_mutation_proof_receipts.jsonl`. No HTML, no rendering pipeline — just a typed read-model. Lets operator know what's broken WITHOUT reading transcripts.

Codex implementation:
- Extend `dev/scripts/devctl/runtime/packet_absorption_resolution.py` (preservation snapshot has the base) with strict durable-binding requirement
- Add `dev/scripts/checks/check_no_unbound_plan_packet_clearance.py` — fails if any cleared plan-bearing packet lacks durable binding
- Extend `dev/scripts/devctl/runtime/agent_loop_decision_builder.py` to never DROP unbound plan packets from `pending_packet_count`
- Extend startup-context / inbox / campaign reducers to surface unbound counts
- Expand `dev/scripts/devctl/tests/runtime/test_development_packet_pressure.py` with the 8 scenarios codex was working on (show→ingest→absorb without PlanRow stays live; expired plan-bearing surfaces as `stale_uningested_plan_pressure`; etc.)

This also addresses cached-hammock P3 (Receipt Schema 4 missing fields), P57 (consolidation), P59 (referential integrity), P60 (state machine coverage), DogfoodRecord integration.

**Plan/code drift contracts (per ChatGPT review 2026-05-18 ~15:50 EDT — EXTEND existing infrastructure, do NOT create parallel)**:

**`PlanSourceSnapshot` already exists** at `dev/scripts/devctl/runtime/plan_source_retention_models.py:25` with 28 fields (`snapshot_id`, `plan_row_id`, `source_kind`, `source_ref`, `source_hash`, `body_hash`, `captured_at_utc`, retention/integrity/composition fields, etc.). Store constant `PLAN_SOURCE_SNAPSHOT_STORE_REL = "dev/state/plan_source_snapshots.jsonl"`.

Phase 1.5 **EXTENDS** this existing model — does NOT create a parallel `PlanSourceSnapshot`. New fields added to the same dataclass:

- `source_doc_path: str = ""` — canonical alias for `source_ref` when source is a file path (vs packet)
- `source_doc_sha256: str = ""` — canonical alias for `source_hash` when content-hash is SHA256
- `source_doc_git_blob_sha: str = ""` — `git hash-object` of the file (vs SHA256 of the text)
- `source_doc_commit_sha: str = ""` — the commit that introduced this revision
- `plan_revision_id: str = ""` — bumps on every operator-approved amendment
- `manifest_path: str = ""` — pointer to `dev/audits/plan_intake/sha256-manifest.txt`

Existing `source_ref` / `source_hash` / `body_hash` remain backward-compatible aliases during migration. No second lifecycle, no parallel storage path — same `plan_source_snapshots.jsonl`.

**`PlanAmendmentReceipt` is genuinely new** (no existing contract with this name):

```python
@dataclass(frozen=True)
class PlanAmendmentReceipt:
    receipt_id: str
    old_plan_revision_id: str
    old_source_doc_sha256: str
    new_plan_revision_id: str
    new_source_doc_sha256: str
    changed_sections: list[str]           # markdown section IDs
    affected_plan_row_ids: list[str]
    superseded_plan_row_ids: list[str]
    new_plan_row_ids: list[str]
    reason: str
    operator_approval_ref: str            # SourceTruthRef to operator's approval packet
    verified_at_utc: str
    contract_id: str = "PlanAmendmentReceipt"
    schema_version: int = 1
```

Storage: new `dev/state/plan_amendment_receipts.jsonl`.

**PlanRow ref-binding fields** (extension to existing 21-field PlanRow):
- `source_doc_path`, `source_doc_sha256` (binds row to specific source-doc revision)
- `source_snapshot_id` (binds to `PlanSourceSnapshot`)
- `source_section_id` / `source_span` (which markdown section the row was generated from)
- `plan_revision_id` (current at row creation)

**Packet ref-binding fields** (review-channel packet posts):
- `plan_row_id`, `plan_revision_id` (binds packet to plan row at specific revision)
- `source_snapshot_id` (binds to snapshot)
- `target_kind`, `target_ref`, `target_revision` (already exist; enforce non-empty for plan-bearing packets)

Lifecycle for plan changes (no silent drift):

```
Plan source-doc changes (operator amends extraction plan)
  → new PlanSourceSnapshot created
  → PlanAmendmentReceipt links old_revision → new_revision + lists affected/superseded/new PlanRow IDs
  → packets referencing old plan_revision_id become stale (require revalidation)
  → code work continues only against new revision
  → closure receipt binds final code commit to final plan revision via SourceTruthRef
```

The system formalizes "plans are allowed to change; the dangerous thing is unrecorded change or unbound change". No more silent stale plans.

### Phase 1.75 — Multi-Repo Harness + RED Baseline (NEW per ChatGPT review 2026-05-18 ~15:25 EDT)

**Purpose**: prove WHERE GuardIR still leaks VoiceTerm assumptions BEFORE identity strip, so the identity strip work is targeted at real leaks (not hypothetical ones). Expected outcome of this phase: **engine RUNS but FAILS** on the fixture repos — that's the baseline. The failures map to PortabilityLeakInventory rows that Phase 2 identity strip resolves.

ChatGPT's reasoning: "Otherwise Codex may waste time trying to make a pre-strip POC pass when the expected result is 'fail because VoiceTerm is still hardcoded.'"

**1.75.A — Fixture adopter repos**:

- `dev/fixtures/adopters/minimal_python_repo/` — smallest Python adopter (engine bootstrap + 1 probe + clean)
- `dev/fixtures/adopters/minimal_mixed_repo/` — Python + non-Python file mix
- `dev/fixtures/adopters/greenfield_python/` — already passes (per `MP377-ADOPTER-PILOT-GATE-S1`)
- `dev/fixtures/adopters/existing_plan_python/` — already passes

Local bare remotes (`git init --bare /tmp/guardir-adopter-<name>-remote-<uuid>.git`) for each fixture so push/ls-remote testing is deterministic.

**1.75.B — Run engine against fixtures (expected RED)**:

```bash
pytest dev/scripts/devctl/tests/portability/ -x  # expected: some fail with VoiceTerm-leak errors
```

Each leak produces a typed `PortabilityLeakFinding` (new contract) with:
- `leak_id`, `leak_classification` (hardcoded_path / hardcoded_repo_pack_id / shell_string / etc.)
- `engine_file`, `engine_line`
- `adopter_repo`, `adopter_test_path`
- `failure_message`
- `proposed_fix_target_phase` (which Phase 2 sub-step resolves this)

**1.75.C — PortabilityLeakInventory typed rows**:

Convert 22 prose-only blockers in `ai_governance_platform.md:1150-1155` to typed PlanRows `MP377-GUARDIR-V21-PORTABILITY-S<n>` in `dev/state/plan_index.jsonl`. Each row references the corresponding `PortabilityLeakFinding`. Total typed rows = 22 prose + N new from fixture failures.

**1.75.D — RED baseline receipt**:

Codex emits a typed `MultiRepoHarnessBaselineReceipt` at `dev/state/multi_repo_harness_baseline_receipts.jsonl` listing every fixture + pass/fail + leak findings. This is the **proof** that the leaks exist BEFORE Phase 2 starts. Phase 4 will produce the green counterpart.

Claude verification: dogfood each fixture run, confirm RED matches `PortabilityLeakFinding` count, post typed `finding` packet back to codex.

### Phase 2 — GuardIR Identity Strip + categorical allowlist (REFINED per ChatGPT #12)

**2A — Repo-pack rename** (from earlier round, unchanged):
- `dev/scripts/devctl/platform/extension_bundle_defaults.py:13` — `repo_pack_id="voiceterm"` → `"guardir"`
- `dev/scripts/devctl/repo_packs/__init__.py:9-25` — refactor direct `from .voiceterm` to a name-keyed registry
- `dev/scripts/devctl/repo_packs/voiceterm.py` → `dev/scripts/devctl/repo_packs/adopters/voiceterm.py`
- Create `dev/scripts/devctl/repo_packs/guardir.py` as primary
- Migrate boundary tests: `tests/repo_packs/test_repo_packs.py:12` and `tests/governance/test_session_resume.py:1262,1278,1295,1338,1360,1376`

**2B — Categorical allowlist** (per ChatGPT #12):

`dev/config/guardir_voice_term_reference_allowlist.json` with each remaining VoiceTerm reference declared:

```json
[
  {
    "path": "dev/scripts/devctl/repo_packs/adopters/voiceterm.py",
    "line_or_key": "*",
    "reason": "adopter_fixture",
    "allowed_in": "adopter_only",
    "owner": "guardir-extraction",
    "expiration": "none"
  }
]
```

Valid `allowed_in` categories:
- `adopter_only` — only allowed in `dev/scripts/devctl/repo_packs/adopters/` and `adopters/voiceterm/` paths
- `historical_only` — only allowed in `dev/audits/`, archived plans
- `fixture_only` — only allowed in `dev/fixtures/`, test fixtures
- `migration_note_only` — only allowed in `dev/docs/migration/`, changelog files

`dev/scripts/checks/check_no_unowned_voiceterm_core_refs.py` — fails if `grep -i voiceterm` finds references in `dev/scripts/devctl/` (core engine) that are NOT in the allowlist OR whose `allowed_in` category doesn't match the location.

**2C — Bridge authority retirement** (cached-hammock finding):

52 bridge-backed fields not yet mapped to typed sources. Phase 2 maps them. Codex creates `dev/state/bridge_field_migration_map.jsonl` with one row per bridge field → typed authority source. Generates new render path that pulls from typed source. Bridge becomes pure projection.

**2D — Provider/Model contracts** (cached-hammock P10):

Create portable AI integration layer; VoiceTerm bindings move to `adopters/voiceterm/`. Codex creates `dev/scripts/devctl/runtime/provider_contract.py` as the portable boundary.

**2E — BypassReceipt CLI surface** (cached-hammock finding):

Register `devctl bypass` subcommand properly; legacy `/bypass` slash adapter becomes thin adapter. Codex implements `dev/scripts/devctl/commands/bypass/` subcommand family.

**2F — Generated surfaces re-render**:

```bash
python3 dev/scripts/devctl.py render-surfaces --write --format md
```

AGENTS.md, CLAUDE.md, SYSTEM_MAP.md, bridge.md re-render with GuardIR-first identity.

### Phase 2.5 — Plan migration map + source snapshot durability (NEW per ChatGPT #6 #9)

**2.5.A — Plan migration map**:

`dev/state/guardir_plan_migration_map.jsonl` — one record per old plan row in `dev/active/*.md` and `dev/state/plan_index.jsonl`:

```json
{"old_plan_row_id": "MP377-…", "old_path": "dev/active/foo.md", "disposition": "kept_core|moved_to_adopter_voiceterm|archived_obsolete|merged_into_guardir_plan|needs_operator_decision", "new_path": "...", "merged_into_row_id": "...", "rationale": "…"}
```

Pre-populated from A5 audit findings (32 active files + 1,778 rows mapped). Each `needs_operator_decision` row gets surfaced to the dashboard for explicit operator triage.

**2.5.B — Source snapshot durability** (per ChatGPT #9):

Source files (`may17th.md`, `~/.claude/plans/do-that-and-in-cached-hammock.md`) migrate to typed-state-friendly paths:

```
dev/audits/plan_intake/2026-05-18-may17-plan.md
dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md
```

Each carries a SHA256 in `dev/audits/plan_intake/sha256-manifest.txt` so future state can verify the source file hasn't drifted. `dev/state/plan_index.jsonl` row sources update to point at `dev/audits/plan_intake/...` paths.

**2.5.C — Charter ingestion** (cached-hammock P56, refined per ChatGPT review #9):

The 4,314-line cached-hammock plan exists in markdown only; NOT YET ingested into `dev/state/plan_index.jsonl`.

**DO NOT explode into hundreds of PlanRows.** That recreates the current sprawl problem. Instead:
- ONE source-snapshot row pointing at `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md` (already exists: `GUARDIR-EXTRACTION-MASTER-PLAN-2026-05-18-S1`)
- ONE typed umbrella PlanRow: `MP377-CACHED-HAMMOCK-ROLE-AUDIT-INGESTION-S1` (status=in_progress)
- **10-20 high-value child rows MAX**, one per cached-hammock finding listed in the table at the top of THIS plan (P1, P3, P6, P10, P53, P55, P56, P57, P59, P60, P62, P65-74 collapsed to 1 row, P75-82 collapsed to 1 row, Bridge Auth Retirement, P195-P198 collapsed to 1 row, Proof Index Caching, DogfoodRecord Integration, BypassReceipt CLI, Cognitive Role Fleet) = ~18 child rows
- Everything ELSE in the 4,314-line cached-hammock plan stays searchable source evidence (via grep) until a specific Phase work-slice needs it

This prevents the "1000 plan rows" failure mode. Codex builds the markdown→plan_index ingestion pipeline as a typed feature, but the FIRST ingestion run is bounded to these ~18 child rows.

**2.5.D — finding_class backfill**:

882 rows in `dev/reports/governance/external_pilot_findings.jsonl` have `finding_class:null`. Codex backfills classification per the 9-value enum (engine_bug / adopter_finding / architecture_gap / etc.) using the existing triage rules.

### Phase 3 — Multi-Repo GREEN Proof + CI (re-run of Phase 1.75 after identity strip)

After Phase 2 identity strip resolves the leaks Phase 1.75 surfaced, re-run the harness — must now go GREEN. This is the operator's thesis proof: "engine works on any repo, not hard-coded to VoiceTerm".

**3A — Re-run local deterministic harness (expected GREEN)**:

```bash
pytest dev/scripts/devctl/tests/portability/ -x  # expected: all green now
```

Each fixture from Phase 1.75 must now pass. Any remaining red is a Phase 2 gap requiring iteration.

**3B — GitHub integration CI** (per `MP-GOVERNANCE-ECOSYSTEM-INTEGRATION-S1` / cached-hammock:1761):

`.github/workflows/governance-freshness-check.yml` runs the engine against:
- VoiceTerm as adopter-1 (via `jguida941/voiceterm` clone in CI)
- Optional second real-world adopter (deferred per ChatGPT recommendation — fixtures first)

Emits `RuntimeAgreementReport` per ADR-013 (`MP377-GUARDIR-V21-RUNTIME-AGREEMENT`) for each adopter. Verifies Second-Repo Proof Ladder 7 gates green (per `portable_code_governance.md:56-73`).

**3C — Multi-repo GREEN proof receipt**:

Codex emits a typed `MultiRepoHarnessGreenProofReceipt` at `dev/state/multi_repo_harness_green_proof_receipts.jsonl`. Each row references the corresponding `MultiRepoHarnessBaselineReceipt` from Phase 1.75 + the resolved `PortabilityLeakFinding` IDs + the new RuntimeAgreementReport ref. The closure pattern: every RED baseline finding has a GREEN counter-receipt with linkage.

**3D — Cloud proof foundation** (cached-hammock P195-P198):

25 typed slices currently UNIMPLEMENTED. Phase 3 lands the foundation slices (CI workflow + RuntimeAgreementReport + Second-Repo Proof Ladder); full cloud-proof implementation extends into Phase 5 with the rest of the dashboard work.

Claude verification: dogfood each fixture + GitHub workflow result, confirm GREEN matches all Phase 1.75 RED findings closed, post typed `finding` packet (kind=`review_accepted` or `review_failed`) back to codex with receipt refs.

### Phase 4 — VoiceTerm shell quarantine/strip (only after Phases 1-3 green)

Safe-to-move paths (per A2 dependency audit):
- `rust/` and `rust/src/bin/voiceterm/` → `adopters/voiceterm/rust/`
- `app/operator_console/` (PyQt6) → `adopters/voiceterm/operator_console/`
- `app/ios/`, `app/macos/` → `adopters/voiceterm/`
- `docs/voice/` → `adopters/voiceterm/docs/`

Cosmetic string updates (caught by Phase 2's `check_no_unowned_voiceterm_core_refs`):
- `dev/scripts/devctl/platform/surface_definitions.py:102-136` — `service_id="voiceterm_daemon"` → adopter-specific optional service
- `dev/scripts/devctl/collect_dev_logs.py:205-206` — `~/.voiceterm/dev/metrics` → configurable
- `dev/scripts/devctl/cli_parser/entrypoint.py` — `"VoiceTerm Dev CLI"` → `"GuardIR Dev CLI"`

Engine-pure tests stay green (~150-180 tests in `tests/runtime/`, `tests/checks/`, `tests/review_channel/` per A4). Adopter tests test the adopter binding, not the shell — they stay in engine test tree.

### Phase 5 — Operator dashboard

Visibility lane per `MP377-DASHBOARD-EXTRACT-CANONICAL-S1`. Shows:
- Current GuardIR branch + repo identity
- Packet pressure (with Phase 1.5 unbound-clearance gauge)
- Plan rows without closure
- Unconsumed action requests
- Governed-push blockers
- Stale VoiceTerm references (from `check_no_unowned_voiceterm_core_refs`)
- Cached-hammock findings status (from Phase 2.5 charter ingestion + Phase 6 substrate)
- CI/adopter status (per Phase 3 RuntimeAgreementReport)
- GuardCoverageGapLedger (cached-hammock P53 — 52 gaps surface here)
- `/guardlab` mode (cached-hammock P55)
- MetaCoverageInvariant trigger (cached-hammock P62)
- Proof index caching status (cached-hammock — SQLite hybrid store, ~25-230ms compute)

### Phase 6 — Cached-hammock role substrate

Codifies the cached-hammock role plan (4,314 lines) as typed substrate. Specific deliverables per cached-hammock findings:
- 6 missing components for CognitiveRoleFleet:
  - `CognitiveRoleFleetAssignment` typed container
  - `dev/config/cognitive_role_fleet.json` config file
  - `devctl cognitive-role-fleet {list/invoke/assign/update}` CLI subcommand family
  - Slash adapter registration (`/round-orchestrator`, `/watcher`, `/codex-research`, etc.)
  - `agents.json` `current_cognitive_roles` field
  - Startup integration for role-aware context loading per session

Claude scaffolds the role definitions and dispatch-receipt schemas as parallel work starting in Phase 1 (claude's lane, doesn't conflict with codex's implementation).

---

## Critical files (Codex-implemented unless noted)

**Phase 0.5 (identity + PII safety):**
- `dev/scripts/checks/check_guardir_remote_identity.py` (new)
- `dev/scripts/checks/check_no_absolute_local_paths.py` (new)

**Phase 1 (P0 proof-integrity):**
- `dev/scripts/devctl/runtime/git_mutation_proof_receipt.py` (new — typed contract)
- `dev/state/git_mutation_proof_receipts.jsonl` (new — typed receipt store)
- `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py:222` (verify before emit)
- `dev/scripts/devctl/commands/vcs/push_flow.py:122` (verify before emit)
- `dev/scripts/devctl/runtime/stage_progress.py` (writer boundary check)
- `dev/scripts/checks/check_commit_complete_proof.py` (new)
- `dev/scripts/checks/check_push_complete_proof.py` (new)
- `dev/scripts/checks/check_no_projection_proof_misuse.py` (new)
- `dev/fixtures/proof_integrity/2026_05_18_false_commit_push/` (new fixture dir, the exact regression)
- 7-8 regression test files in `dev/scripts/devctl/tests/checks/` and `tests/runtime/`

**Phase 1.25 (post_action_request strict gate):**
- `dev/scripts/devctl/runtime/post_action_request_gate.py` (new)
- `dev/scripts/checks/check_post_action_request_strict_gate.py` (new)
- `dev/scripts/devctl/tests/checks/test_check_post_action_request_strict_gate.py` (new)

**Phase 1.5 (plan/packet accountability):**
- `dev/scripts/devctl/runtime/packet_absorption_resolution.py` (extend)
- `dev/scripts/checks/check_no_unbound_plan_packet_clearance.py` (new)
- `dev/scripts/devctl/tests/runtime/test_development_packet_pressure.py` (expand)
- Reducer extensions in: `agent_loop_decision_builder.py`, startup-context, inbox, campaign

**Phase 2 (identity strip):**
- `dev/scripts/devctl/repo_packs/__init__.py:9-25` (registry refactor)
- `dev/scripts/devctl/repo_packs/voiceterm.py` → `adopters/voiceterm.py`
- `dev/scripts/devctl/repo_packs/guardir.py` (new)
- `dev/scripts/devctl/platform/extension_bundle_defaults.py:13`
- `dev/config/guardir_voice_term_reference_allowlist.json` (new — categorical)
- `dev/scripts/checks/check_no_unowned_voiceterm_core_refs.py` (new)
- `dev/state/bridge_field_migration_map.jsonl` (new — 52 fields)
- `dev/scripts/devctl/runtime/provider_contract.py` (new — portable AI layer)
- `dev/scripts/devctl/commands/bypass/` (new — register CLI subcommand)

**Phase 2.5 (migration map + source durability):**
- `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md` (preserved copy)
- `dev/audits/plan_intake/2026-05-18-may17-plan.md` (preserved copy)
- `dev/audits/plan_intake/sha256-manifest.txt`
- `dev/state/guardir_plan_migration_map.jsonl` (new — populated from A5 audit)
- Markdown→plan_index ingestion pipeline (cached-hammock P56)
- finding_class backfill on `dev/reports/governance/external_pilot_findings.jsonl`

**Phase 3-6:** see phase sections.

**Existing functions/utilities to reuse:**
- Guard pattern from `dev/scripts/checks/check_command_output_consumed.py` and `check_non_trivial_output_proof.py`
- Test pattern from `dev/scripts/devctl/tests/runtime/test_governed_exception_contracts.py:129-140`
- Check-router infrastructure
- Stage progress writer in `dev/scripts/devctl/runtime/stage_progress.py`
- External Python Repo Matrix structure in `dev/active/portable_code_governance.md:104-117`

---

## Verification approach (Claude executes after each codex slice)

```bash
# Focused: new tests go red without fix, green with it
python3 dev/scripts/devctl.py test-python --suite devctl --path <new_test_paths> --format md

# Full suite: no regressions
python3 dev/scripts/devctl.py test-python --suite devctl --format md

# Typed guards: new checks wired into router
python3 dev/scripts/devctl.py check-router --format md

# Real-git verification — proof contract works under provocation
python3 -c "from dev.scripts.devctl.runtime.git_mutation_proof_receipt import GitMutationProofReceipt; ..."

# Remote-state real-truth check
git ls-remote guardir refs/heads/extraction/guardir-core-p0-proof-integrity
```

Claude also runs branch-/remote-identity sanity each verification round:
```bash
git remote -v | grep -v voiceterm    # no accidental origin pushes
git rev-parse --abbrev-ref HEAD       # confirm on extraction/* branch (not preserve/*)
```

## Push policy

After Phase 1 green proves push events are now verified-real:
- Normal work: `python3 dev/scripts/devctl.py push --execute` (governed pipeline)
- Emergency preservation: raw `git push --no-verify` reserved for evidence-locker only (used once today; not normal work)

All pushes go to `guardir` remote. `origin` (voiceterm) stays frozen at `835060c2` indefinitely.

## Out of scope for this plan

- Restarting codex in reconciliation-only mode (operator action; codex was SIGINT-stopped)
- Modifying `jguida941/voiceterm` (origin untouched)
- Cleanup of the 2 pending governed exceptions from yesterday (separate exception-debt slice)
- Renaming GitHub repos (voiceterm and guardir stay separate repos)

## Open operator decisions (resolved + remaining)

**Resolved 2026-05-18T~14:55Z:**

1. ~~Cached-hammock plan preservation timing~~ — **DONE** via commit `ccf6b4f5` + auto post-commit `bf21b66a`. Files at `dev/audits/plan_intake/`. Typed PlanRow added.

**Resolved 2026-05-18T~15:10 EDT (operator + ChatGPT directive):**

2. ~~228 orphan `feedback_*.md` files~~ — **QUARANTINE** (not delete) per Phase 0.0 above. Move to `~/.cache/guardir-memory-archive/2026-05-18-feedback-orphans/` with SHA256 manifest; add one pointer line to MEMORY.md.

3. ~~GuardIR trunk SHA selection~~ — **`92ef4032`** (the actual UNREVIEWED PRESERVATION SNAPSHOT content commit), NOT `d92dc2ff` (which is just the auto-snapshot artifact for `92ef4032`). Per Phase 0.3 above. Try governed push first; raw `--no-verify` only if Phase 1 P0 not yet implemented and hooks block.

**Pending (operator action needed):**

4. **Codex restart in strict Phase 0.5 + Phase 1 ONLY mode** (operator + ChatGPT directive 2026-05-18 ~15:10 EDT): operator launches codex CLI with this prompt — narrow scope, no Phase 2+ work yet:

> Restart in reconciliation-only mode. Repo: jguida941/guardir. Do NOT work in or push to jguida941/voiceterm. Do NOT work on preserve/* except to verify evidence. Branch: `extraction/guardir-core-p0-proof-integrity` rooted at `guardir-main` (SHA `92ef4032`). Run `python3 dev/scripts/devctl.py session --role reviewer --include-review-status always --format json`, then `python3 dev/scripts/devctl.py develop next --actor codex --format md`. Read the plan it points at (`dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md`) + AGENTS.md + cached-hammock source.
>
> Scope for this restart: Phase 0.4 minimal + Phase 0.5 + Phase 1 ONLY.
>
> **First (BLOCKING — Phase 0.4 minimal mode)**: implement `check_guardir_extraction_plan_current.py --mode minimal` and wire into `check-router`. DO NOT proceed to Phase 0.5/1 work if the canonical plan file is stale, a competing plan exists, or memory files contain active plan authority.
>
> Then Phase 0.5 + Phase 1:
> 0. `check_guardir_extraction_plan_current.py` minimal mode (Phase 0.4) — first
> 1. `check_guardir_remote_identity.py` + `check_no_absolute_local_paths.py` (Phase 0.5)
> 2. `GitMutationProofReceipt` typed contract at `dev/scripts/devctl/runtime/git_mutation_proof_receipt.py` (expanded 7+ binding fields per plan section 1A)
> 3. Receipt store `dev/state/git_mutation_proof_receipts.jsonl`
> 4. Emission-time verification at `governed_executor_commit_phase.py:222` + `push_flow.py:122`
> 5. Writer-boundary check in `stage_progress.py`
> 6. Consumption-time guards: `check_commit_complete_proof.py` + `check_push_complete_proof.py` + `check_no_projection_proof_misuse.py`
> 7. Local bare-remote regression tests (`git init --bare /tmp/...`)
> 8. Regression fixture at `dev/fixtures/proof_integrity/2026_05_18_false_commit_push/`
>
> DO NOT: create new plans/memory/active-docs, dashboard work, CI lane, VoiceTerm shell strip, cached-hammock role substrate. Those come AFTER Phase 1 + Phase 1.5 green.
>
> **You MAY delegate dogfood/verification/architect-review tasks to claude via typed `review-channel post` packet (kind=`task_started` or `action_request`, target_role=`dashboard` or `reviewer`). Claude responds via typed `finding` packet with dogfood evidence + receipt refs. Every feature you ship MUST be proved by claude's dogfood + receipt — no chat-prose acceptance, no events.jsonl narration as proof.**
>
> Respond to claude via typed `finding` packet with verdict (approve / amend / reject) + concrete commit shape before any code change.

5. **Adopter-2 selection** (Phase 3A): use fixture repos first (`greenfield_python` + `existing_plan_python` already pass `MP377-ADOPTER-PILOT-GATE-S1`; add `minimal_python_repo` + `minimal_mixed_repo` per ChatGPT recommendation). VoiceTerm is adopter-1 in Phase 3C. Real-world adopter-2 deferred.

6. **finding_class backfill scope**: 882 rows in `external_pilot_findings.jsonl` have `finding_class:null`. **Recommended**: Phase 2.5 task; codex applies classification batch using existing 9-value enum + triage rules. Claude verifies sample correctness via dogfood-receipt loop.

7. **PortabilityLeakInventory typing**: 22 blockers are prose-only in `ai_governance_platform.md:1150-1155`. **Recommended**: Phase 3B converts each to typed PlanRow with `MP377-GUARDIR-V21-PORTABILITY-S<n>` IDs.

**Anti-sprawl rule** (operator directive — applies to ALL phases): do NOT create new plans, memory files, active docs, strategy docs, or "preservation context" markdown unless typed state explicitly requires the file. Claude memory is short-term continuity only; durable rules live in typed contracts, repo policy, receipts, guards. One planning document = this file. Source files (cached-hammock, may17, ai_governance_platform, MASTER_PLAN, INDEX, SYSTEM_MAP, AGENTS, CLAUDE.md) are referenced, not duplicated.
