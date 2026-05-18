# Plan — GuardIR Extraction (Proof-Integrity → Plan/Packet Accountability → Multi-Repo POC → Identity Strip → VoiceTerm Quarantine)

## Context

On 2026-05-18 the devctl progress logger emitted `commit.complete sha=6cd8953a68cab904fed07f5bbad8638351f8cfb1; push is next` and `git-push ... returncode=0` to `origin feature/live-push` at 13:39-13:42Z. Empirically: commit `6cd8953a` does not exist (`git cat-file -t` returns bad object), `feature/live-push` does not exist locally or on origin, HEAD on `feature/governance-quality-sweep` remained `835060c2`. **The events log lied about commit and push success.** P0 = unverified events being consumed as proof.

Today's codex session was stopped via `kill -INT 5268`. The 69-path uncommitted governance patch + 3 untracked files + 2 dangling commits are preserved in `~/.cache/guardir-preserve/2026-05-18T14-22-00Z/` (SHA256-manifested) and pushed to `https://github.com/jguida941/guardir.git` as branch `preserve/guardir-extraction-unreviewed-2026-05-18` (verified by `git ls-remote` SHA match: `d92dc2ff6bce9830450b3f530dac3797fff8b7ce`). Origin (`jguida941/voiceterm.git`) is untouched at `835060c2`.

Operator strategic decision: VoiceTerm becomes an adopter/example shell; the portable governance engine moves to GuardIR. The false-proof bug is upstream of everything — if it stays, post-extraction "green" will lie just like post-commit "green" lied today. Therefore strict sequence: fix proof integrity FIRST, then plan/packet accountability, then prove POC on multiple repos, then identity strip, then shell strip, then dashboard, then role substrate.

**Operator's deeper priority surfaced 2026-05-18 ~11:10 EDT**: the thesis-level proof is "this engine works on many different types of repos, not hard-coded to VoiceTerm". Multi-repo POC is THE success proof, not a side effect. It must come early in the sequence (Phase 3), not be left until the end.

## Role Split (load-bearing — do not collapse)

- **Codex** = **implementer**. Writes the code for every phase. Owns red-then-green test cycles. Owns commit/push on `extraction/*` branches.
- **Claude** = **architecture reviewer + cached-hammock plan worker + verification runner**. Reviews codex's design for typed-state-lies recurrence and fake-proof drift. Works the cached-hammock plan (`~/.claude/plans/do-that-and-in-cached-hammock.md` once migrated into the repo) as parallel substrate. Runs verification (`devctl test-python`, `pytest -x`, `check-router`, direct `git rev-parse / git ls-remote / git show / git cat-file`) after each codex slice. Surfaces issues before they become commits. Does NOT take the implementation lane.

The reason: claude caught today's events.jsonl-lying failure because claude observed real git state while codex built on events-log narration. Codex codes; claude verifies; same-lane duplication = wasted work.

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

Step 0.1 — Preserve cached-hammock plan (URGENT, do before Phase 0.5):

```bash
mkdir -p dev/audits/plan_intake/
cp ~/.claude/plans/do-that-and-in-cached-hammock.md dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md
cp may17th.md dev/audits/plan_intake/2026-05-18-may17-plan.md
shasum -a 256 dev/audits/plan_intake/* > dev/audits/plan_intake/sha256-manifest.txt
```

Step 0.2 — Verify GuardIR state:
- `git remote -v` (confirm `guardir` + `origin`)
- `git ls-remote guardir refs/heads/preserve/guardir-extraction-unreviewed-2026-05-18` (confirm `d92dc2ff`)
- `git rev-parse HEAD` on extraction branch
- Confirm `~/.cache/guardir-preserve/2026-05-18T14-22-00Z/sha256-manifest.txt` integrity

Step 0.3 — Create real GuardIR trunk branch (per ChatGPT amendment #1):

```bash
git checkout -b guardir-main d92dc2ff6bce9830450b3f530dac3797fff8b7ce
git push --no-verify guardir guardir-main  # initial trunk seed; raw push for trunk creation only
git checkout extraction/guardir-core-p0-proof-integrity  # back to working branch
```

After this: `preserve/*` becomes **immutable evidence-locker** (no normal commits ever); `guardir-main` is trunk baseline; `extraction/*` are real working branches.

### Phase 0.5 — Repo identity safety + PII/local-path safety gates (NEW per ChatGPT #1 #8)

Codex implements three new guards:

**0.5.A — `dev/scripts/checks/check_guardir_remote_identity.py`** — fails if:
- Publication target resolves to `jguida941/voiceterm.git`
- Current branch starts with `preserve/` or `feature/governance-quality-sweep`
- `repo_pack_id` resolves to `voiceterm` in publication-identity context (vs adopter-registration context)

**0.5.B — `dev/scripts/checks/check_no_absolute_local_paths.py`** (per ChatGPT #8) — fails on any committed/generated state containing `/Users/`, `/home/`, `C:\Users\` except allowlisted fixtures. Critical because GuardIR is public-ish and local paths in state break CI/adopter portability.

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
    receipt_id: str                  # unique
    operation: Literal["commit", "push"]
    claimed_sha: str
    verified_local_sha: str          # git rev-parse --verify <sha>^{commit}
    verified_remote_sha: str         # git ls-remote <remote> <ref> (empty for commit op)
    intended_ref: str
    remote_name: str                 # empty for commit op
    remote_url: str                  # empty for commit op
    command_argv_digest: str         # sha256 of the argv list (per ChatGPT #4 — must match consumed event)
    command_returncode: int
    verified_at_utc: str
    verifier_version: str
    result: Literal["verified", "failed_verification"]
    failure_reason: str              # empty when verified
    contract_id: str = "GitMutationProofReceipt"
    schema_version: int = 1
```

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

Codex implementation:
- Extend `dev/scripts/devctl/runtime/packet_absorption_resolution.py` (preservation snapshot has the base) with strict durable-binding requirement
- Add `dev/scripts/checks/check_no_unbound_plan_packet_clearance.py` — fails if any cleared plan-bearing packet lacks durable binding
- Extend `dev/scripts/devctl/runtime/agent_loop_decision_builder.py` to never DROP unbound plan packets from `pending_packet_count`
- Extend startup-context / inbox / campaign reducers to surface unbound counts
- Expand `dev/scripts/devctl/tests/runtime/test_development_packet_pressure.py` with the 8 scenarios codex was working on (show→ingest→absorb without PlanRow stays live; expired plan-bearing surfaces as `stale_uningested_plan_pressure`; etc.)

This also addresses cached-hammock P3 (Receipt Schema 4 missing fields), P57 (consolidation), P59 (referential integrity), P60 (state machine coverage), DogfoodRecord integration.

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

**2.5.C — Charter ingestion** (cached-hammock P56):

The 4,314-line cached-hammock plan exists in markdown only; NOT YET ingested into `dev/state/plan_index.jsonl`. Codex builds the markdown→plan_index ingestion pipeline. Each P-marked finding in the cached-hammock becomes a typed PlanRow with proper provenance.

**2.5.D — finding_class backfill**:

882 rows in `dev/reports/governance/external_pilot_findings.jsonl` have `finding_class:null`. Codex backfills classification per the 9-value enum (engine_bug / adopter_finding / architecture_gap / etc.) using the existing triage rules.

### Phase 3 — Multi-Repo POC (operator's THESIS PRIORITY — bring forward in importance)

This is where the operator's "this works on any repo, not hard-coded to VoiceTerm" thesis gets proved. Split into local-deterministic + GitHub-integration (per ChatGPT #8):

**3A — Local deterministic CI** (no network dependency):

- Fixture adopter repos under `dev/fixtures/adopters/minimal_python_repo/`, `minimal_mixed_repo/`, `greenfield_python/`, `existing_plan_python/` (the last two already pass per `MP377-ADOPTER-PILOT-GATE-S1`)
- Local bare remotes for push/ls-remote verification
- `pytest dev/scripts/devctl/tests/portability/ -x`
- Verifies the P0 proof-integrity invariant on each adopter
- Verifies Phase 1.5 plan-packet-accountability invariant per adopter

**3B — PortabilityLeakInventory landing**:

Create the 22 typed PlanRow entries (currently prose-only in `ai_governance_platform.md:1150-1155`):
- Missing/partial `ServiceLifecycleConfig`, `BuildConfig`, `ProjectGovernance.workflow_adapters`
- Remaining `MemoryRoots` callers
- String-literal `INDEX.md` / `MASTER_PLAN.md` fallbacks
- Direct `VOICETERM_PATH_CONFIG` imports
- Hardcoded timezone/bridge formats
- Portable-named guards with VoiceTerm-only behavior
- VoiceTerm daemon/surface names
- Direct `voiceterm_repo_root()` calls
- `~/.voiceterm` metric paths
- Cargo/Rust templates in portable review/check-router paths

Each must resolve before extraction code moves are accepted.

**3C — GitHub integration CI**:

`.github/workflows/governance-freshness-check.yml` in GuardIR per `MP-GOVERNANCE-ECOSYSTEM-INTEGRATION-S1` (may17th.md:67) — the cached-hammock CI hook. Runs the engine against:
- VoiceTerm as adopter (via `jguida941/voiceterm` clone)
- Optional second real-world adopter (TBD)
- Emits `RuntimeAgreementReport` per ADR-013 per adopter
- Verifies Second-Repo Proof Ladder 7 gates green

**3D — Cloud proof** (cached-hammock P195-P198):

25 typed slices currently UNIMPLEMENTED. Phase 3 lands the foundation slices; full implementation extends into Phase 5.

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

## Open operator decisions (claude flags for explicit answer before Phase 1 starts)

1. **Codex restart**: operator restarts codex with reconciliation-only opening prompt (drafted at `/tmp/operator_stop_instruction.md` from earlier turn), then codex implements Phase 0 + Phase 0.5 first. Claude verifies each slice. **Recommended**: operator restart codex into reconciliation mode; codex implements; claude verifies.

2. **GuardIR trunk branch**: Phase 0.3 creates `guardir-main` from preservation snapshot SHA `d92dc2ff` and pushes once (raw, for trunk creation only). After that: `preserve/*` immutable, `guardir-main` baseline, `extraction/*` working. **Recommended**: execute Phase 0.3 immediately at the start of Phase 0.

3. **Adopter-2 selection**: Phase 3A uses fixture repos (`greenfield_python` + `existing_plan_python` already pass; plus new `minimal_python_repo` + `minimal_mixed_repo`). Phase 3C uses VoiceTerm as adopter-1; second real-world adopter TBD. **Recommended**: prove POC on fixtures first, real-world adopter-2 after Phase 3C green.

4. **Cached-hammock plan preservation timing**: copy `~/.claude/plans/do-that-and-in-cached-hammock.md` into `dev/audits/plan_intake/` as Phase 0.1 step. **Recommended**: do this IMMEDIATELY before any other Phase 0 work — it's outside any current preservation snapshot, the literal "afraid losing" file.

5. **finding_class backfill scope**: 882 rows in `external_pilot_findings.jsonl` need classification backfill. **Recommended**: Phase 2.5 task; codex applies classification batch using existing triage rules. Claude verifies sample correctness.

6. **PortabilityLeakInventory typing**: 22 blockers are prose-only in `ai_governance_platform.md:1150-1155`. **Recommended**: Phase 3B converts each to typed PlanRow with `MP377-GUARDIR-V21-PORTABILITY-S<n>` IDs.
