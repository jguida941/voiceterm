# 📋 Research Report — Dashboard / Cloud / Repo-Separation (2026-05-17)

For ChatGPT Pro review → then codex.

## TL;DR

You **already have ~70% of the substrate** for all three asks. The work is mostly:
(a) **finish current enforcement-path / absorb-layer slice**,
(b) **land P58.3 portability boundary**,
(c) **materialize P195-P198 cloud-proof contracts + ProofIndex + `governance_cloud_proof.yml`**,
(d) **add HTML dashboard renderer + DashboardPublishPolicy**,
(e) **deploy public dashboard only after proof + redaction guards**,
(f) **extract platform repo only after second-repo proof ladder passes**.

---

## 1️⃣ HTML Dashboard / Web Frontend

### What's already shipped
- **`DashboardSnapshot` v3** typed contract at `dev/scripts/devctl/runtime/dashboard_snapshot_authority.py:24-37` — sections: `agent_minds`, `session_outcomes`, `ack_freshness`, `session_posture`, `session_liveness`, `packet_continuity_index`
- **`devctl dashboard`** command + 11 sibling dashboard modules
- **`dashboard_render/`** package (1712 LOC): `terminal.py` (489) + `markdown.py` (396) + `mobile.py` + `typed_state.py` + 6 others — **no `html.py`**
- **`render-surfaces` pipeline** (`runtime/key_surfaces.py` + `surface_snapshot.py`) — already used for SYSTEM_MAP.md, MASTER_PLAN.md, boot cards. Markdown-only today.
- **`devctl context-graph`** already supports `mermaid` and `dot` output (ready for HTML graph viz)
- **`dev/reports/review_channel/latest/monitor_snapshot.json`** — already designed for operator consumption
- **MP-359 operator_console** (PyQt6 desktop) — sibling not replacement; explicitly desktop-only

### Plan items queued (not shipped)
- `MP377-DASHBOARD-EXTRACT-CANONICAL-S1` (plan_index.jsonl:245)
- `MP377-P0-T22AG-A..H` + `MP377-P0-T22AK-A..F` (frontend adapters for slash/CLI/MCP/mobile/dashboard/Operator Console)
- Cached-hammock: `GovernedSurface[TContent]` base (line 1128) — `TContent` generic is exactly where HTML renderer slots
- P39 `RoleAwareCommandRegistry`, P52 `BridgeAuthorityRetirementContract`, P85 `ClaudeCommandsPortabilityShip` — all touch dashboard but **none mention HTML**

### Gaps
- No `html.py` in `dashboard_render/`
- No `governed_surfaces` entry for HTML projection
- **No `.github/workflows/dashboard-pages.yml`** (you have 32 workflows but no GH Pages deploy)
- No HTML-specific typed contract (`HtmlDashboardSnapshot`)
- No `dev/web/` or `docs/` asset tree

### Recommended approach (single architecture-consistent path)
1. Add `dashboard_render/html.py` consuming `DashboardSnapshot` v3 → emits static `index.html` + per-section pages (lifecycles, packets, plan, commits, push)
2. Add `governed_surfaces` entry `html_dashboard` so `devctl render-surfaces --write` regenerates it (same pattern as SYSTEM_MAP)
3. Add `.github/workflows/dashboard-pages.yml`: run `devctl render-surfaces` → publish `dev/reports/dashboard/html/` to `gh-pages` branch on master push
4. Stable URL: `https://<user>.github.io/<repo>/` — surface_provenance baked in (each page shows source commit + source contract)

---

## 2️⃣ GitHub Actions / Cloud-Runtime Proof

### What's already shipped (heavy)
- **32 workflows** in `.github/workflows/`:
  - `release_preflight.yml` (308 lines, `workflow_dispatch`) — runs ~80 `check_*.py` guards + 5 `devctl` profiles (check, docs-check, security, orchestrate-*) = **existing cloud-runtime template**
  - `tooling_control_plane.yml` (push/PR) — 30+ check guards inline
  - `pre_commit.yml`, `security_guard.yml`, `coverage.yml`, `mutation-testing.yml` (8-shard), `release_attestation.yml`, etc.
- **`workflow_bridge/shell.py`** — already resolves PR/push commit ranges in CI
- **`devctl check --profile ci|prepush|release|ai-guard`** — same code path runs locally or in CI
- **`devctl push`** already invokes `PUSH_PREFLIGHT_CHECK_ROUTER_REPORT` pre-push

### Plan items queued (specifically this operator vision)
**This is already deeply planned** — operator coined the framing in P191. Plan rows (status=`queued`):
- **P191** "asynchronous cloud proof for runtime systems"
- **P195** `MP-NEW-P195-ASYNC-CLOUD-PROOF-S1..S6` — `RepoSnapshotIdentity` + `CloudProofRequest` + `CloudProofApplicability`
- **P196** `MP-NEW-P196-AHEAD-OF-RUNTIME-PROOF-CACHE-S1..S6` — exact operator quote: *"CI runs expensive proof BEFORE trusted runtime; runtime queries `ProofIndex` for matching `CodeIdentity → ProofReceipt`"*. S3 = workflow emits `proof_receipt.json` + ingests into `ProofIndex`
- **P197** `MP-NEW-P197-CONTINUOUS-PROOF-SCHEDULER-S1..S7` — `SafeContinuationDecision` + `ProofExecutionMode` (cloud_only/local_only/hybrid/disabled)
- **P198** `MP-NEW-P198-QUALITY-REPAIR-SCHEDULER-S1..S6` — emit `cloud_findings.json` + convert to `RepairPacket`
- **`MP-GOVERNANCE-ECOSYSTEM-INTEGRATION-S1`** (cached-hammock:1761) already specs `.github/workflows/governance-freshness-check.yml`

### Top candidate guards to port (of 139 `check_*.py`)
`check_governance_closure`, `check_governed_transitions`, `check_platform_contract_closure/sync`, `check_typed_namespace_composition`, `check_contract_registry_composite_key_uniqueness`, `check_memory_not_authority`, `check_bridge_projection_only`, `check_plan_row_contract_refs_resolve`, `check_function_duplication`, `check_python_subprocess_policy`, `check_pytest_runtime_policy`, plus `devctl governance-import-findings`

### Recommended architecture (consistent with queued plan)
Add `governance_cloud_preflight.yml` on PR + push: runs `devctl check --profile ci --report-cloud-receipt`, uploads typed `proof_receipt.json` + `cloud_findings.json` per P196-S3/P198-S3. `devctl push` consults `ProofIndex` via `CodeIdentity` lookup, **refusing push when no current `ValidationReceipt` matches HEAD tree-hash** (the "authority gate" shifts left, not the Python execution).

### Open questions for ChatGPT Pro
1. Block on P195-S1 contract landing first OR ship stringly-typed intermediate?
2. Workflow concurrency: split into matrix shards or keep monolithic for atomic `proof_receipt.json`?
3. `ProofExecutionMode` default: `hybrid` or `cloud_only`?
4. Land `governance-freshness-check.yml` first OR broader `governance_cloud_preflight.yml`?

---

## 3️⃣ VoiceTerm-Strip + New Repo

### Voice-specific (separable cleanly)
- `rust/` — 352 `.rs` files, ~3,841 LOC (voice/STT/TUI/audio/PTY/telemetry/IPC + `bin/voiceterm/` subcrate)
- `pypi/src/voiceterm/` — install/bootstrap shim
- `app/ios/`, `app/macos/` (371 MB total — `app/operator_console/` PyQt6 is debatable: client over governance)
- `dev/scripts/devctl/repo_packs/voiceterm.py` — already correctly isolated as repo-pack
- `dev/config/quality_presets/voiceterm.json`, `.voiceterm/`, `bin/`, `pypi/dist/voiceterm-*`

### Platform-generic (the new repo)
- `dev/scripts/devctl/` — **3,047 Python files, 113 MB** — `runtime/`, `governance/`, `commands/`, `cli.py`, `repo_packs/` (infrastructure), `context_graph/`, `control_plane/`, `data_science/`, `platform/`
- `dev/scripts/checks/` — 139 guard library
- `dev/state/` schemas (not data) — 27 MB ledgers
- `dev/active/` governance plan docs (ai_governance_platform.md, portable_code_governance.md, MASTER_PLAN.md, platform_authority_loop.md)
- `dev/config/` minus voiceterm preset

### 🚨 Intertwined leakage points (~10 — must fix BEFORE extraction)
Already speced as **P58.3 `PortabilityEnforcementGuard`** in cached-hammock plan lines 1260-1297:
1. `dev/scripts/checks/ide_provider_isolation_core.py` — 11 hardcoded `"voiceterm"` refs (SOURCE_ROOTS)
2. `dev/scripts/devctl/governance/instruction_boot_card.py` lines 47, 109, 173 — generates the `repo_pack_id: voiceterm` boot-card literals
3. `dev/scripts/devctl/governance/guard_promotion_queue.py` + `external_findings_log.py` — direct `from ..repo_packs.voiceterm import voiceterm_repo_root` (should use repo-pack registry indirection)
4. `dev/scripts/devctl/governance/bootstrap_support.py` lines 281, 300, 310 — `_contains_voiceterm_literal()` (the guard itself names the adopter)
5. `dev/scripts/devctl/commands/release/prep_updates.py` — `"pypi/src/voiceterm/__init__.py __version__"`
6. `dev/scripts/devctl/commands/governance/session_reviewer_loop.py` — `.voiceterm/memory/` prefix
7. `dev/scripts/devctl/commands/governance/hygiene_render.py` — `"voiceterm test processes detected"` label
8. `dev/scripts/checks/check_repo_url_parity.py` — hardcoded `CANONICAL_URL = "github.com/jguida941/voiceterm"`
9. `CLAUDE.md` / `AGENTS.md` — `repo_pack_id: voiceterm`, "first-party adopter" (regenerated from boot_card.py)
10. Pre-commit hooks, GH workflows, Makefile — VoiceTerm-named entrypoints

### Plan items (extraction is the main lane)
- **MP-377** — `dev/active/ai_governance_platform.md` (canonical, ~14,000 lines). **Phase 4 lines 4204-4222** "Extract the standalone repository and package" with explicit acceptance criteria. F.5 Standalone-Repo Migration Roadmap (4224-4246). Extraction Sequence (2865-2878).
- **MP-376** — `dev/active/portable_code_governance.md`: "Second-Repo Proof Ladder" (56-73), External Python Corpus Protocol (74-100)
- **MP-378** — VoiceTerm-specific lanes
- **MP-340, MP-355, MP-358, MP-359** — subordinate implementation lanes inside MP-377

### Recommended strategy (matches MP-377 Phase 4)
1. **Land P58.3 portability fixes FIRST** (10+ leakage points) — otherwise platform-tier won't run against non-voiceterm host
2. Prove second-repo bootstrap green per MP-376 Second-Repo Proof Ladder
3. Extract per MP-377 Phase 4: new repo `governance-platform` (or `guardir` per Plan 4.1 V2.1 framing). Moves `dev/scripts/devctl/`, `dev/scripts/checks/`, `dev/state/` schemas, `dev/active/` governance docs, `dev/config/` minus voiceterm
4. VoiceTerm repo retains `rust/`, `app/`, `pypi/`, `bin/`, `.voiceterm/` + slim repo-pack (`repo_packs/voiceterm.py` + `quality_presets/voiceterm.json`) pinning a platform version

---

## 4️⃣ Existing Observability Inventory (HTML dashboard inputs)

### Audit trail (massive — already there)
- `dev/reports/review_channel/events/trace.ndjson` — **83,178 lines** master event spine
- `dev/reports/commit_receipts/`, `feature_proof_receipts/`, `governance/audit_receipts/` (dated)
- `dev/reports/dashboard_findings/` (dated markdown)
- `dev/reports/agent_minds/{claude,codex}_latest.json`
- `dev/reports/peer_heartbeat/latest/`
- `dev/audits/REVIEW_SNAPSHOT.md` + `AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md`

### Typed state (operator would surface)
17 ledgers: `plan_index.jsonl`, `contract_registry.jsonl`, `bypass_lifecycles.jsonl`, `governed_exception_lifecycles.jsonl`, `raw_git_bypass_receipts.jsonl`, `plan_row_closure_receipts.jsonl`, `artifact_receipts.jsonl`, `plan_source_snapshots.jsonl`, etc.

### Top 12 HTML dashboard input candidates (highest-value)
1. `dev/reports/review_channel/latest/monitor_snapshot.json` — **already most-curated for operator**
2. `devctl dashboard --view overview --format json` — multi-view aggregate
3. `devctl mobile-status --view full --format json` — phone/web friendly
4. `dev/audits/REVIEW_SNAPSHOT.md` — narrative snapshot
5. `dev/state/plan_index.jsonl` — plan rows (status/closure derivable)
6. `dev/reports/push/latest_push_report.json` — most recent push proof
7. `dev/reports/review_channel/events/trace.ndjson` — event spine (tail/filter for timeline)
8. `devctl context-graph --mode bootstrap --format json|mermaid` — connectivity for graph viz (already supports mermaid!)
9. `devctl render-surfaces --format json` — surface drift indicator
10. `dev/reports/governance/latest/review_summary.json` + `.md`
11. `dev/reports/agent_minds/{claude,codex}_latest.json` — agent narration
12. `dev/state/bypass_lifecycles.jsonl` + `governed_exception_lifecycles.jsonl` — gate status

### Existing dashboard-like devctl commands (~100 subcommands available)
`dashboard`, `mobile-status`, `phone-status`, `monitor`, `orchestrate-status`, `orchestrate-watch`, `progress-status`, `system-map`, `system-picture`, `platform-contracts`, `context-graph`, `data-science`, `autonomy-report`, `ralph-status`, `governance-review`, `probe-report`, `render-surfaces`, `session`/`startup-context`/`session-resume`

---

## 🎯 Synthesis for ChatGPT Pro

**One key insight**: all three asks (dashboard, cloud-runtime, repo-split) are **already deeply planned** in MP-376/MP-377/P191-P198/P58.3/MP-359 — but largely UNSHIPPED. The fastest path:

1. **Land P58.3 PortabilityEnforcementGuard** (unblocks extraction; ~10 grep-fix sites)
2. **Add HTML renderer** to `dashboard_render/` + `governed_surfaces` entry (~1 day; composes with shipped `DashboardSnapshot v3`)
3. **Land P196 + workflow** for cloud-proof receipts (already speced; biggest payoff = `devctl push` refuses unproven HEAD)
4. **Add `.github/workflows/dashboard-pages.yml`** to deploy HTML to gh-pages
5. **Extract per MP-377 Phase 4** once P58.3 green + second-repo proof ladder passes

**Codex is currently mid-slice** on Rule 4 enforcement-path (raw-git ✓ + devctl push ✓ + checkpoint/staging in progress) — do NOT derail until that lands. The dashboard + cloud + repo-split work should queue after current slice, ideally as one combined Phase 5 follow-up.

---

# 📋 ADDENDUM — GitHub Actions as Typed Runtime Proof + Codex Absorb-Layer Critique (2026-05-17 R469)

Operator pasted detailed ChatGPT-pro-style analysis covering (a) CI as typed runtime proof source, (b) MP-NEW-P240-GITHUB-ACTIONS-RUNTIME-PROOF-S1 proposal, (c) detailed critique of codex's in-progress absorb work. Verified inline + cross-referenced existing plan.

## 5️⃣ GitHub Actions as Typed Runtime Proof — already speced as P195-P198

### Operator's framing (correct)

The right loop:
```
AI edits → local fast checks → AI reads stdout/stderr/artifacts → local typed receipts → commit only with proof → governed push → GitHub clean-room → AI ingests CI logs/artifacts → GitHubActionsRunReceipt → AI fixes failures → repeat
```

GitHub Actions becomes the clean-room verifier (fresh checkout, no local cache lies, artifacts captured centrally). Local checks still needed for fast iteration; CI required before publish/merge/trust.

### Workflow trigger gap — CONFIRMED with refinement

- **`tooling_control_plane.yml:12-50`** — `push:` is `branches: [master, develop]` + path-filtered; `pull_request:` runs from any branch into master/develop. Feature-branch direct push does NOT trigger it.
- **`release_preflight.yml:13-40`** — pure `workflow_dispatch:` (manual), hard-requires `GITHUB_REF_NAME == master`.
- **Branch-restricted push workflows** (master/develop only): `coverage.yml`, `security_guard.yml`, `scorecard.yml`, `adopter_portability.yml`, `pre_commit.yml`, `workflow_lint.yml`, `coderabbit_triage.yml`, `parser_fuzz_guard.yml`, `docs_lint.yml`
- **Wide-net push** (NO branch filter, runs on feature branches): `rust_ci.yml`, `ios_ci.yml`, `lint_hardening.yml`, `perf_smoke.yml`, `memory_guard.yml`, `latency_guard.yml`, `voice_mode_guard.yml`, `wake_word_guard.yml` — ALL path-filtered to `rust/src/**` / `app/ios/**`

**Net**: governance/Python edits under `dev/scripts/devctl/` on `feature/governance-quality-sweep` get essentially **zero CI coverage** until PR open. Only `lint_hardening.yml` partially matches.

### Typed CI receipt status — ALL MISSING

Verified via `grep -rn "GitHubActionsRunReceipt|CIOutputConsumptionReceipt|CIProofReceipt"` returns **zero matches** in `dev/scripts/`, `dev/state/`, `dev/active/`. Same for `ci_watch|ci-watch|github.actions.ingest|gha.ingest`.

Adjacent existing: `dev/scripts/devctl/runtime/feature_proof_receipt.py:37 FeatureProofReceipt` (local feature evidence, not CI ingestion). `triage/loop_parser.py:76` is the only `workflow_run` consumer (for triage loops, not typed receipts).

### MP-NEW-P240 proposal vs existing P195-P198 — SUBSTANTIAL OVERLAP

**Recommendation: DO NOT add MP-NEW-P240 as a new plan row.** The four root causes operator names map 1-for-1 onto unstarted P195-P198 slices (25 typed slices total, all `status: queued` in plan_index.jsonl lines 101-160):

| Operator's MP-NEW-P240 need | Already in P195-P198 |
|---|---|
| `GitHubActionsRunReceipt` | **P195** `CloudProofReceipt` + `CloudProofRun` + `CloudProofArtifact` (6 slices) |
| `CIOutputConsumptionReceipt` | **P196** `ProofReceipt` + `ProofIndex` + `RuntimeProofLookup` + `ProofAuthorityDecision` (6 slices) |
| `devctl ci-watch` / `github-actions ingest` | **P197** `ProofExecutionMode` + continuous scheduler + `SafeContinuationDecision` (7 slices) |
| Machine-readable CI failures → repair | **P198** `CloudFinding` + `FindingApplicability` + `RepairPacket` (6 slices) |
| Missing-CI-run fails publication | **P195** `CloudProofApplicability` + `StaleProofReceipt` + **P196** `ProofAuthorityDecision` + `BypassWithoutProofReceipt` |

Adding MP-NEW-P240 would be a **parallel surface** (violates memory ×14 ProofGraphKernel + ×16 TypedGovernanceGraph — duplicate node instead of extending typed parent).

### Best next packet (NOT MP-NEW-P240)

Send typed **PacketAttentionPivotRequest** citing P195-S3+P196-S3+P197-S3+P198-S3 as the BUILD GAP path, with two `composes_with` scope additions:

1. **Add `feature_branch_governance_coverage`** requirement to P195-S3 acceptance — the new `proof.yml` workflow must trigger on feature branches, not just master/develop
2. **Add `devctl github-actions ingest`** (renamed from operator's `ci-watch`) as the runtime verb under P197-S2 SafeContinuationDecision MVP — operator note at cached-hammock:3722 already specs <150 LOC composition of `scope_path_claims.py` + `collect.py gh integration` + `AffectedTestSelection`

### What's right about codex's S1 work for this

`dev/scripts/devctl/runtime/command_output_consumed.py:19-36` authority-bearing commands list **already covers** operator's set (`agent-loop`, `develop next`, `startup-context`, `session-resume`, `review-channel`, `push`, `raw-git`) **plus extras** (`check-feature-has-proof-receipt`, `check-publication-scope-integrity`, `check-substrate-commits-have-applied-plan-row`, `check-startup-authority-contract`). The pattern operator wants (`GitHub logs → CommandOutputReceipt → CommandOutputConsumptionReceipt → check_command_output_consumed → CIProofReceipt`) is exactly P196's `ProofIndex` extending the existing consumption substrate.

---

## 6️⃣ Codex Absorb-Layer Critique — 4 of 7 fixes ALREADY DONE

Operator's 7 proposed fixes verified against codex's in-progress local work (36 dirty files including `runtime/packet_absorption.py` + `review_channel/packet_absorption.py` + `event_handler.py`):

| # | Operator fix | Verified Status | File:Line |
|---|---|---|---|
| 1 | Stop conflating `blocked → needs_operator_decision` | **PARTIAL** — row-level OK (no-op passthrough); receipt-summary `blocked_reason` still merges 3 dispositions | `review_channel/packet_absorption.py:331-332` (row OK); `:128-131` (summary merges) |
| 2 | Add `source_semantic_ingestion_receipt_id` field | **ALREADY DONE** — declared + required | `runtime/packet_absorption.py:54` (field); `:847-858` (violation if empty); `review_channel/packet_absorption.py:162-164` (bound) |
| 3 | Deterministic multi-receipt selection rule | **NEW WORK** — `_valid_semantic_ingestion_receipts:695-707` returns ALL valid receipts in iteration order; no `max(ingested_at_utc)` timestamp tiebreak | `runtime/packet_absorption.py:695-707` |
| 4 | Block silent plan mutation; require `PlanProposal`/`PacketPlanIntegration` evidence | **ALREADY DONE** — `_row_is_plan_affecting` + `_row_has_plan_evidence` guards present | `review_channel/packet_absorption.py:346-389` |
| 5a | Test: no semantic ingestion → absorb blocks | **DONE** | `test_packet_absorption.py:test_ack_does_not_satisfy_absorption_for_actionable_packet` |
| 5b | Test: malformed rows → blocks | **DONE** | `test_semantic_ingestion_requires_structured_action_item_rows` + `test_invalid_absorption_disposition_fails` |
| 5c | Test: wrong actor/role → blocks | **NEW** — `packet_semantically_ingested_by:467` exists but no test exercises scope filtering | `runtime/packet_absorption.py:467` |
| 5d | Test: ack without absorb doesn't clear pressure | **DONE** | `test_semantic_ingestion_does_not_satisfy_acked_absorption` |
| 5e | Test: plan-affecting row without plan evidence → blocks | **NEW** — guard exists but is untested | `review_channel/packet_absorption.py:346-389` |
| 6 | `ControlDecisionObeyedGuard` before append_event for all actions | **PARTIAL** — verified for `push` (push.py:580+) + `post`/`ack`/`apply`/`dismiss`/`absorb`/`ingest` via `event_handler.py:529-639` | `commands/review_channel/event_handler.py:529-639` |
| 7 | Multiple semantic receipts: latest valid wins | **NEW** — same as fix #3 above |  |

### NEW work needed (3 items)

1. **Fix receipt-summary disposition conflation** at `review_channel/packet_absorption.py:128-131`: `_joined_row_reasons` should give `blocked` / `rejected` / `needs_operator_decision` distinct summary fields. Only map to `needs_operator_decision` if row has explicit `operator_question_ref` or operator-decision reason.

2. **Add deterministic selection rule** for multiple valid semantic receipts at `runtime/packet_absorption.py:695-707`: sort by `ingested_at_utc` descending, take latest; OR allow absorb to explicitly select via `--source-semantic-ingestion-receipt-id` flag. Bind absorb-receipt to selected `receipt_id`.

3. **Add 2 missing regression tests** in `test_packet_absorption.py`:
   - `test_absorb_blocks_when_semantic_ingestion_wrong_scope` (different actor/role/session than the absorb caller)
   - `test_absorb_blocks_plan_affecting_row_without_plan_evidence` (semantic row classified plan-affecting per `_row_is_plan_affecting` but no `PlanProposal`/`PacketPlanIntegration` evidence; should fail closed)

### What codex got right (preserve)

- `body_observed != semantic_ingestion != absorption` typed distinction (rev_pkt_4396 + 4398)
- `ack` kept separate from absorption (no longer treated as safe packet observation)
- `PacketAbsorptionReceipt.source_semantic_ingestion_receipt_id` field present + required (fix #2)
- `_row_has_plan_evidence` guard blocks silent plan mutation (fix #4)
- `ControlDecisionObeyedGuard` extended to all review-channel mutations (fix #6 — though this is what's blocking my claude→codex packet channel right now)
- 3 of 5 absorb regression tests already present (fix #5a/b/d)

---

## 🎯 Updated Synthesis for ChatGPT Pro

**Headline**: operator's instinct is correct — typed CI receipts are the missing piece — **BUT** P195-P198 already cover the entire design space (25 typed slices, all queued, total spec at cached-hammock:3640-3789). The actionable shift is **landing P195-P198 + 2 scope additions**, NOT adding MP-NEW-P240 as a new row.

**Updated path (single combined Phase 5)**:

1. **Codex finishes Rule 4 enforcement-path slice** (raw-git ✓ + devctl push ✓ + checkpoint/staging in progress + review-channel mutation gates partially) — already in flight
2. **Codex adds 3 NEW absorb-layer fixes** before publication: disposition-conflation at summary layer, deterministic semantic-receipt selection, 2 missing regression tests
3. **Codex relaxes `ControlDecisionObeyedGuard` for non-mutating packet kinds** (`decision`, `finding`, `task_progress`) OR provides claude with valid `AgentLoopDecision` template — currently blocks my feedback channel
4. **Land P195-S3 + P196-S3 + P197-S2 + P198-S3** (the cloud-proof BUILD GAP):
   - New `governance_cloud_proof.yml` workflow triggered on `[push, pull_request, workflow_dispatch]` with **feature_branch_governance_coverage** (operator's MP-NEW-P240 #1+#4)
   - `devctl github-actions ingest --sha <SHA> --workflow <name> --format json` command emits `CloudProofReceipt` (operator's #3)
   - `devctl push` consults `ProofIndex` via `CodeIdentity` — refuses if no matching `ProofReceipt` for HEAD tree-hash (operator's #5)
   - CI logs/artifacts feed `CommandOutputReceipt` → `CommandOutputConsumptionReceipt` → `check_command_output_consumed` (operator's #6 — composes with already-shipped substrate from commit 47944776)
5. **Land P58.3 PortabilityEnforcementGuard** + extract per MP-377 Phase 4
6. **Add HTML renderer** (Section 1 above) once dashboard pipeline can include CI proof state from P196 `ProofIndex`

Sequence is: enforcement-path → cloud-proof → portability → repo extract → HTML dashboard. Each blocks the next architecturally.

---

# 📋 ADDENDUM 2 — Codex/ChatGPT-Pro Architectural Review (2026-05-17 R470)

Codex reviewed the prior addendum + provided sequencing correction + 2 critical safety additions. Claude AGREES with everything below.

## Codex caveat: snapshot precision

> Branch tip `835060c235c53c56d6fda2c3ea280ac9cc72a3b3` is one projection/snapshot-refresh commit ahead of REVIEW_SNAPSHOT.md target `47944776`. Treat snapshot as strong evidence for parent implementation state + latest projection refresh, but NOT as independent proof of every byte at branch tip.

## Verdict from codex: idea is good — sequencing needs correction

**My original ordering (worse)**: dashboard → Pages → repo split → cloud proof
**Codex's ordering (better)**: portability → proof receipts → cloud validation → dashboard projection → public Pages → repo split

The dashboard makes the system **legible**. The cloud proof layer makes it **trustworthy**. The portability work makes extraction **possible**. The repo split should be the **result** of those proofs, not the mechanism used to discover whether they work.

## 5 critical corrections from codex

### Change 1 — Proof receipts BEFORE dashboard publishing
HTML dashboard is more valuable once it can show real proof state (P196 `ProofIndex` + `ProofReceipt`) rather than just current local projection state. The dashboard becomes a **view over verified proof state**.

### Change 2 — Treat dashboard as governed projection, NOT web app
- Static HTML first. No React. No backend service. No live API. No auth story. No database.
- Matches existing `render-surfaces` model. Avoids introducing second runtime authority path.
- Each page shows: source commit + source contract + source files + generated timestamp + renderer version + staleness status

### Change 3 — Public/internal dashboard split
```
dev/reports/dashboard/internal/   (full detail: agent minds, findings, local paths, review notes)
dev/reports/dashboard/public/     (redacted: health, proof status, release posture, high-level plan closure)
```
Workflow deploys ONLY the public target. Add `check_dashboard_publish_policy.py` guard that fails if internal-only sections leak into public bundle.

### Change 4 — Extraction gated by evidence, not confidence
Repo split blocked until ALL of:
- Second repo can install governance substrate
- Second repo can mint repo-pack config
- Guards run without VoiceTerm assumptions
- System map generates
- Review snapshot generates
- No hardcoded voiceterm references outside adopter config

### Change 5 — Reuse `DashboardSnapshotV3`, do NOT create `HtmlDashboardSnapshot`
```
DashboardSnapshotV3
  ├── terminal renderer
  ├── markdown renderer
  ├── mobile renderer
  └── html renderer
```
Keeps HTML dashboard as another view over the same authority model. Composes with memory ×14 ProofGraphKernel principle.

## State ownership correction for repo split

| Platform repo (new `governance-platform` / `guardir`) | VoiceTerm adopter repo (current) |
|---|---|
| devctl package/runtime | VoiceTerm product code (rust/, app/, pypi/) |
| Guard library | VoiceTerm repo-pack config |
| Schemas / contract definitions | **VoiceTerm-specific ledgers/receipts** |
| Renderers | **VoiceTerm generated projections** |
| Repo-pack registry mechanism | VoiceTerm adoption docs |
| Docs/templates | |
| Generic workflows | |

**Key correction to Addendum 1**: do NOT move all instance state to platform repo. VoiceTerm retains its own evidence/receipts/projections/product-specific plan rows.

## Network-fallback rule for `devctl push`

`devctl push` must NOT depend on live GitHub network availability:
```
CI writes receipt
  ↓
receipt downloaded/ingested into ProofIndex
  ↓
local gate checks ProofIndex (no network call)
  ↓
missing receipt => fail closed OR require explicit governed fallback
```

This avoids turning every local operation into a cloud/network dependency.

## Codex's 5-phase implementation sequence

### Phase 1 — Portability boundary (P58.3)
Fix hardcoded VoiceTerm leakage points. Acceptance:
```bash
grep -R "voiceterm" dev/scripts/devctl dev/scripts/checks .github Makefile AGENTS.md CLAUDE.md
```
Every remaining hit must be repo-pack config / VoiceTerm product code / VoiceTerm adopter projection / explicit test fixture.

### Phase 2 — Proof contracts + cloud receipt
Land: `CodeIdentity`, `CloudProofRequest`, `ProofReceipt`, `ProofFinding`, `ProofIndex`, `ProofApplicability`.

Add ONE workflow: `.github/workflows/governance_cloud_preflight.yml`:
```yaml
- checkout
- setup python/uv
- devctl scan
- devctl check --profile ci --report-cloud-receipt
- emit proof_receipt.json
- emit cloud_findings.json
- upload artifacts
```

### Phase 3 — Static HTML dashboard
```
dev/scripts/devctl/dashboard_render/html.py
dev/scripts/devctl/dashboard_render/assets/
dev/reports/dashboard/html/
```
Wire into governed surface registry. No JS-heavy frontend. Static HTML with small embedded JSON blobs or linked JSON artifacts.

### Phase 4 — Safe Pages deployment
`.github/workflows/dashboard_pages.yml` — deploy ONLY public/redacted target. Include `check_dashboard_publish_policy.py` guard.

### Phase 5 — Shadow extraction
Create local sibling package boundary first:
```
governance_platform/
  devctl/
  checks/
  schemas/
  renderers/
  workflows/templates/
```
Prove VoiceTerm consumes it as adopter. Only THEN separate repo becomes canonical.

## Pre-Phase-1 fix codex flagged

Latest review snapshot reports MEDIUM stale/contradiction risk around **bridge projection semantics + vendored external-agent event interpretation**. Fix should be small: make the delegation explicit with projection metadata, contract pointer, or guard proving `bridge.py` is projection-only AND that durable external-agent interpretation lives in vendored/external-agent authority.

---

## 7️⃣ Verification of Codex's Architectural Review

Inline research after codex's analysis confirmed:

### Bridge projection finding — precisely located
Documented in **`dev/audits/architecture_alignment.md:2169-2185`** (Issues 14.3 + 14.4):

1. **Root cause (CRITICAL, 21 days old)**: `audit_review_state_contract_drift` in `dev/scripts/devctl/runtime/review_state_parser.py` — *"Bridge-backed and event-backed review-channel producers emit different shapes; compatibility glue normalizes instead of enforcing one authoritative ReviewState contract. Blocks typed contract closure."*

2. **HIGH SYSTEMIC cluster (5 days old)**:
   - `bridge_projection_drops_operator_direction` — `dev/scripts/devctl/review_channel/bridge_projection_state.py`
   - `bridge_acceptance_should_be_projection` — `dev/scripts/devctl/review_channel/bridge_validation_acceptance.py`
   - `push_invalidation_head_equality` — `dev/scripts/devctl/review_channel/push_state.py`

**Existing fix lever**: `dev/scripts/checks/check_bridge_projection_only.py` (226 LOC AST guard) covers hardcoded 2-file list. Cached-hammock:723 proposes extension to `runtime/session_posture*.py` + `runtime/control_plane_loop_wake.py` + `runtime/review_state_contract_drift.py`. Tracked under `MP377-GUARDIR-BRIDGE-AUTHORITY-INVERSION-S1`.

### `CodeIdentity` status — MISSING as composite, PARTIAL primitives exist

NO `CodeIdentity` symbol anywhere in `dev/scripts/devctl/`. BUT partial primitives DO exist:
- `CommitReceipt.tree_content_hash` at `dev/scripts/devctl/runtime/commit_receipt.py:64` (plus `commit_sha`)
- `compute_non_audit_worktree_hash()` in `review_channel/heartbeat.py` (used in bridge_promotion / reviewer_state)
- `FeatureProofReceipt` carries `commit_sha` only (no tree/config/policy composition)
- `guard_run_core.py:26` has `reviewed_worktree_hash`

**No composite identity** (commit + tree + config + policy + guard-bundle + deps hash) exists. P196-S1 must create it from these primitives.

### `ProofIndex` status — MISSING

No `ProofIndex` / `proof_index` / `ProofCache` / `RuntimeProofLookup` exists in code or `dev/state/`. Closest analog: `dev/reports/feature_proof_receipts/` (flat per-commit JSON directory, no index/cache, no SHA-keyed lookup).

Cached-hammock:3679-3681 specs hybrid `dev/state/proof_index.jsonl` + `dev/state/.cache/proof_index.sqlite` with `code_identity_cache.json` (~25ms clean / 75-230ms dirty compute). NOT YET IMPLEMENTED.

### Network-fallback pattern — `devctl push` is FULLY LOCAL ✓

Verified `dev/scripts/devctl/commands/vcs/push.py` imports only `subprocess`-style runners + local governance/runtime modules. NO `requests`, `urllib`, `http.client`, `gh api`, or `github.com` references in push.py or `dev/scripts/devctl/governance/`. Publication uses git only via subprocess.

**ProofIndex consultation will fit cleanly as a local-file lookup before the subprocess git call** — codex's design constraint is already feasible.

### `DashboardPublishPolicy` substrate — BUILD NEW FROM SCRATCH

Verified NO existing redaction/publish-policy substrate for dashboards:
- `DashboardSnapshot` v3 has NO public/internal field tags (sensitive payload composed unconditionally)
- 14 dashboard files under `dev/scripts/devctl/commands/dashboard*.py` + `dashboard_render/` — none gate sections by audience
- No PII/secret guards enforce dashboard public-safety
- Only adjacent: Rust-side `redact_secrets()` in `rust/src/bin/voiceterm/memory/governance.rs:29` (text-prefix scrubber for memory only); `_collaboration_profile_session` redactor (scoped to collaboration profiles)
- `remote_publish_policy` in `runtime/governed_exception_policy.py:122` is about git push publishing, NOT HTML/dashboard — false-positive name collision
- `MP-235` + `MP-248` cover memory redaction only

**Recommendation**: Build NEW `DashboardPublishPolicy` contract from scratch. Extend `dev/scripts/devctl/runtime/surface_provenance.py` with `public_audience` axis. Add per-section `audience: public|internal|operator_only` to `DashboardSnapshot` composed via `normalize_dashboard_snapshot()`. Pair with new `check_dashboard_publish_policy.py` modeled on `check_bridge_projection_only.py` (sibling discipline at content-sanitization layer).

---

## ⚠️ CRITICAL CAVEAT — P195-P198 METRIC INFLATION

`dev/active/MASTER_PLAN.md:8925` (rev_pkt_4351 / R372 P263) flagged:

> "SINGLE BIGGEST METRIC-INFLATION of session at P195-P198 (1450 LOC claim vs 0 LOC actual; all 7 cited runtime files NON-EXISTENT; proof_index.jsonl + sqlite cache ABSENT)"

P195-P198 are **genuinely UNIMPLEMENTED** despite extensive scope/detail in cached-hammock:3640-3789 and 25 typed plan rows queued. Earlier session claims that they were "partial" or "starting" were stale narration.

**Implication**: when codex tackles Phase 2 (proof contracts + cloud receipt), it's starting from ZERO not from "extend partial implementation". The cached-hammock plan + queued plan rows give the design but no code exists.

---

## 🎯 Final Synthesis for ChatGPT Pro (after codex review)

**Updated sequenced path** (codex's correction + claude verification):

| Phase | Work | Blocker for | Acceptance |
|---|---|---|---|
| **0** | Fix bridge-projection medium finding (`MP377-GUARDIR-BRIDGE-AUTHORITY-INVERSION-S1`) | All downstream dashboard/cloud work depends on stable bridge semantics | `check_bridge_projection_only.py` extended to cover 5 flagged files; `audit_review_state_contract_drift` resolved |
| **1** | Codex finishes Rule 4 enforcement-path slice (checkpoint/staging gate + remaining review-channel mutations). **Codex must NOT proceed to cloud-proof or dashboard work while checkpoint/staging/push publication remains dirty or blocked, except for surgical bridge/projection fixes explicitly marked Phase 0.** | Phase 2 needs typed `AgentLoopDecision` infrastructure | Currently in flight; ETA based on tree dynamics |
| **2** | **P58.3 Portability Boundary** — fix ~10 hardcoded `voiceterm` leakage points | Repo extraction blocked until clean | `grep voiceterm dev/scripts/devctl/...` returns only repo-pack/product/adopter/test |
| **3** | **P196 Proof Contracts + ProofIndex + Cloud Workflow** (start from ZERO per metric-inflation caveat) | Dashboard truth + push gate depends on this | `CodeIdentity` + `ProofReceipt` + `ProofIndex` typed + `governance_cloud_preflight.yml` emits typed receipts + `devctl push` consults local index |
| **4** | **`DashboardSnapshotV3.html` renderer** (extend existing, do NOT create `HtmlDashboardSnapshot`) + `DashboardPublishPolicy` contract + `check_dashboard_publish_policy.py` guard | Phase 5 publish needs the safety guard | Renderer composes with DashboardSnapshot v3; guard fails on internal-section leak |
| **5** | **`.github/workflows/dashboard_pages.yml`** publishing PUBLIC target only | Operator/ChatGPT-Pro visibility | Stable URL serving redacted dashboard |
| **6** | **Shadow extraction** to local `governance_platform/` sibling package; prove VoiceTerm adopts via repo-pack | Repo split | Adoption works; tests green |
| **7** | **Separate repo** for `governance-platform` (canonical) — VoiceTerm pins platform version | End state | Two-repo architecture stable |

**Codex is currently on Phase 1** (Rule 4 enforcement-path: raw-git ✓ + devctl push ✓ + checkpoint/staging in progress + review-channel mutations partial). Phase 0 (bridge fix) can happen in parallel since it's a small surgical fix.

**3 NEW absorb-layer fixes** from Addendum's Section 6 should land within current slice (Phase 1) before any publication: receipt-summary disposition conflation, deterministic semantic-receipt selection, 2 missing regression tests.

**META request to operator**: please send this updated MD back to codex for one more iteration round, focused on Phase 0 + Phase 2 specifics (codex agreed to architecture; next step is decomposition of P196-S1 into concrete dataclass field-by-field).

---

# 📋 ADDENDUM 3 — Final ChatGPT-Pro Architectural Review (2026-05-17 R471)

ChatGPT-Pro reviewed Addendum 2. Verdict: **strong + mostly right**. Key architectural correction (mine) is confirmed: **do not create parallel MP-NEW-P240 lane; use P195-P198 as canonical cloud-proof lane**.

The 8-phase sequence is mostly correct; one slight adjustment:

## Confirmed final sequence (with adjustment)

| Phase | Work | Why this order |
|---|---|---|
| **0** | Bridge/projection authority cleanup | Bridge stale semantics poison all downstream projections |
| **1** | Finish current enforcement-path / absorb-layer / checkpoint slice | Avoid increasing surface area while authority semantics still changing |
| **2** | **P58.3 portability boundary** | Hardcoded VoiceTerm assumptions will **poison both cloud-proof workflow AND dashboard** if platform is still adopter-coupled |
| **3** | P195-P198 cloud proof + ProofIndex | Proof contracts must land before public dashboard publishing (otherwise dashboard = public projection of weak/local proof) |
| **4** | Dashboard HTML renderer + DashboardPublishPolicy | Composes over verified proof state |
| **5** | GitHub Pages public dashboard | Public surface only after Phase 4 guard exists |
| **6** | Shadow extraction → local `governance_platform/` package | Prove adoption locally before separate repo |
| **7** | Separate repo (canonical platform) | Result of proofs, not mechanism to discover whether they work |

**Reason P58.3 before P195-P198**: hardcoded voiceterm assumptions in `dev/scripts/devctl/` will poison BOTH the cloud-proof workflow AND dashboard if platform is still adopter-coupled. **But proof contracts must land before public dashboard publishing** — otherwise the dashboard becomes a public projection of weak/local proof.

## Critical refinement: ControlDecisionObeyedGuard fix is typed classification, NOT broad bypass

Do NOT broadly relax `ControlDecisionObeyedGuard` (which is blocking my claude→codex feedback channel). Instead use **typed packet-kind classification**:

```
Non-mutating feedback events (safe typed authorization path):
  decision / finding / task_progress / operator_routed
  → classify as non-mutating feedback events
  → require FeedbackEmissionDecision or equivalent typed non-mutating authorization
  → do NOT require mutation-authority gate

Mutating actions (still require ControlDecisionObeyedGuard):
  post / apply / dismiss / absorb / ingest
  → ControlDecisionObeyedGuard required
```

The fix is a **typed classification + typed non-mutating authorization** at the gate logic in `dev/scripts/devctl/commands/review_channel/event_handler.py:529-639`, NOT a `--bypass` arg or relaxed default. The goal is typed safety, not a bypass lane.

## Answers to 4 open cloud-proof questions (from Addendum 1 Section 2)

### Q1 — Block on P195-S1 contract landing first, or stringly-typed intermediate?

**Answer: Block on minimal typed contract. No stringly intermediate.**

Minimum dataclasses:
```
CodeIdentity
CloudProofRun
CloudProofReceipt
CloudProofArtifact
ProofIndexEntry
```

### Q2 — Workflow concurrency: matrix shards or monolithic?

**Answer: Matrix shards + single aggregator receipt.**

```
job/shard receipts
  → aggregate proof_receipt.json
  → ProofIndex
```

Avoid one giant monolithic job (slow + brittle). Also avoid treating each shard as independent final authority (would split proof). Aggregator pattern gives both speed AND atomicity.

### Q3 — `ProofExecutionMode` default?

**Answer: `hybrid`**

Local proof for fast iteration; cloud proof for trust/publication. Maximizes both shift-left iteration AND remote clean-room verification.

### Q4 — `governance-freshness-check.yml` first OR broader `governance_cloud_preflight.yml`?

**Answer: `governance_cloud_proof.yml` first, but keep v1 focused. Include freshness as a component, NOT a separate first-class lane.**

Avoids workflow proliferation. Freshness is one of many checks the proof workflow runs.

## What composes from existing substrate (do not rebuild)

GitHub Actions proof should flow through existing `command_output_consumed` / `command_output_consumption_receipt` substrate from commit `47944776`:

```
GitHub job logs
  → CommandOutputReceipt (existing)
  → CommandOutputConsumptionReceipt (existing)
  → check_command_output_consumed.py (existing)
  → CloudProofReceipt / ProofIndex (NEW per P195-P196)
```

`dev/scripts/devctl/runtime/command_output_consumed.py:19-36` already treats `agent-loop`, `develop next`, `startup-context`, `session-resume`, `review-channel`, `push`, `raw-git`, and key proof checks as authority-bearing commands. The cloud-proof workflow extends this list to GitHub Actions output.

## Phase 0 surgical scope (bridge fix)

Should be small + surgical, NOT a new architecture lane:
- Extend `check_bridge_projection_only.py` (currently 226 LOC hardcoded 2-file list) to cover the 5 flagged files at `architecture_alignment.md:2169-2185`
- Add `projection_only` metadata + contract pointer to bridge surfaces
- Add `semantic producer/consumer rows` so bridge→event drift becomes typed
- Guard proving bridge is NOT authority

Existing `check_systemmap_covers_contract_registry.py` validates generated contract-token coverage, NOT full semantic connectivity. The bridge fix should add semantic-connectivity discipline at the bridge layer specifically.

## Repo split state-ownership rule (re-emphasized)

```
Platform repo (new governance-platform / guardir):
  devctl runtime
  guards
  schemas
  contract definitions
  renderers
  workflow templates
  generic docs/templates

VoiceTerm repo (current — kept as adopter):
  rust/app/pypi/bin
  repo-pack config
  VoiceTerm ledgers/receipts/projections      ← keep VoiceTerm evidence here
  VoiceTerm-specific plan rows/history         ← keep VoiceTerm history here
```

**Do not move all `dev/state/` instance ledgers into platform repo.** Move schemas/fixtures/templates, NOT VoiceTerm evidence history.

---

> ⚠️ **SUPERSEDED BY ADDENDUM 6**: This Codex-ready packet was the current operative version when written. Addendum 6 (below) now supersedes it. This block is retained for audit history only — do NOT use as active instruction to codex.

## 📦 CODEX-READY PACKET (copy-paste for codex when ready — final clean version)

```
Title: Phase 5 substrate path: implement existing P195-P198 cloud proof, P58.3 portability, and dashboard projection without parallel P240

Summary:
Operator's dashboard/cloud/repo-split report is accepted with sequencing corrections.
Do not add MP-NEW-P240; the cloud-proof design maps to existing P195-P198. Dashboard
is a projection over DashboardSnapshot v3, not a new authority contract. Repo split
is blocked on P58.3 portability. ProofIndex must exist before public dashboard publishing.

Immediate directives:

0. Surgical Phase 0 bridge/projection cleanup:
   - Fix bridge/projection authority semantics before dashboard/cloud projection work.
   - Extend check_bridge_projection_only.py to cover the currently flagged bridge/projection files.
   - Add projection_only metadata and source contract pointers.
   - Ensure bridge/event projections cannot become durable authority.

1. Finish current enforcement-path / absorb-layer / checkpoint work:
   - distinct blocked / rejected / needs_operator_decision summary fields
   - deterministic latest-valid semantic ingestion receipt selection
   - tests for wrong actor/role/session scope
   - tests for plan-affecting row without PlanProposal or PacketPlanIntegration evidence
   - safe typed path for non-mutating feedback events under ControlDecisionObeyedGuard:
     decision / finding / task_progress / operator_routed are classified as non-mutating
     feedback events and require typed non-mutating authorization, not mutation authority
   - do NOT proceed to cloud-proof or dashboard work while checkpoint/staging/push
     publication remains dirty or blocked, except for surgical Phase 0 bridge fixes

2. Land P58.3 portability:
   - remove hardcoded voiceterm leakage from generic platform paths
   - remaining hits must be repo-pack / product / adopter / test only
   - do NOT extract repo before P58.3 is green

3. Land P195-P198 as cloud proof:
   - CodeIdentity as composite of commit SHA, tree hash, config hash, policy hash,
     guard-bundle hash, and dependency/environment identity
   - CloudProofRun
   - CloudProofReceipt
   - CloudProofArtifact
   - ProofIndex
   - ProofAuthorityDecision
   - CloudFinding
   - RepairPacket
   - governance_cloud_proof.yml for feature branch + PR + workflow_dispatch
   - use matrix shards with one aggregate proof_receipt.json
   - devctl github-actions ingest
   - devctl push consults local ProofIndex for HEAD tree hash
   - no live GitHub network call inside devctl push
   - CI logs feed CommandOutputReceipt + CommandOutputConsumptionReceipt
   - default ProofExecutionMode is hybrid

4. Add dashboard HTML only after proof substrate:
   - dashboard_render/html.py consumes DashboardSnapshot v3
   - do NOT create HtmlDashboardSnapshot
   - add DashboardPublishPolicy
   - add internal/public dashboard split
   - add check_dashboard_publish_policy.py
   - dashboard_pages.yml deploys public bundle only

5. Repo extraction only after:
   - P58.3 green
   - second-repo proof ladder green
   - governance substrate installs in second repo
   - repo-pack config can be minted in second repo
   - guards run without VoiceTerm assumptions
   - system map and review snapshot generate in adopter repo
   - no hardcoded voiceterm refs outside allowed adopter config

Do not:
- create P240 as a parallel cloud-proof lane
- create HtmlDashboardSnapshot
- publish internal dashboard sections
- extract repo before portability proof
- make devctl push depend on live GitHub network calls
- treat GitHub Actions green as proof unless logs/artifacts are ingested into typed receipts

Caveat:
P195-P198 are queued/speced but UNIMPLEMENTED per metric-inflation flag at
MASTER_PLAN.md:8925 (rev_pkt_4351). Start from ZERO, not "extend partial".
The plan gives the design, not existing code.
```

## VoiceNode-short version

```
Final decision:
Do not create P240. P195 through P198 are the cloud-proof lane.

The correct order is:
Phase 0: Fix bridge and projection authority semantics.
Phase 1: Finish the current enforcement, absorb-layer, checkpoint, and staging work.
Phase 2: Land P58.3 portability. Remove hardcoded VoiceTerm leakage before any repo split.
Phase 3: Land P195 through P198 cloud proof. Add CodeIdentity, CloudProofReceipt,
         ProofIndex, CloudFinding, RepairPacket, governance_cloud_proof.yml, and
         devctl github-actions ingest. Devctl push should check local ProofIndex,
         not call GitHub live.
Phase 4: Add HTML dashboard only after ProofIndex exists. Use DashboardSnapshot v3.
         Do not create HtmlDashboardSnapshot. Add DashboardPublishPolicy and
         public/internal split.
Phase 5: Deploy public dashboard only.
Phase 6: Shadow extraction into a local governance_platform package.
Phase 7: Separate repo only after second-repo proof ladder passes.

Important: GitHub Actions green is not proof unless logs and artifacts are ingested
into typed receipts.
Important: non-mutating feedback packets should be typed as safe feedback events, not
broad ControlDecisionObeyedGuard bypasses.
Important: platform repo gets schemas, contracts, guards, renderers, workflows, and
templates. VoiceTerm keeps its own product code, repo-pack config, ledgers, receipts,
projections, and history.

Bottom line: finish absorb-layer fixes, then implement the first P195/P196 proof
contracts and governance_cloud_proof.yml.
```

---

## 🎯 Final Bottom Line (from ChatGPT-Pro)

**4 strongest final decisions**:
1. **P195-P198 are the cloud-proof lane** (not new P240)
2. **P58.3 is the extraction gate** (everything blocks on this)
3. **Dashboard HTML is a projection over DashboardSnapshot v3** (not a new authority contract)
4. **ProofIndex must exist before dashboard/public Pages become trustworthy** (Phase 3 before Phase 4-5)

**Next codex work should be narrow**: finish the absorb-layer fixes (Phase 1) → materialize the first P195/P196 proof contracts and `governance_cloud_proof.yml` (Phase 3 minimal slice).

---

# 📋 ADDENDUM 4 — Missing Existing-System Tie-Ins (2026-05-17 R472)

Final missing-items scan found **2 CRITICAL gaps** + 4 lower-priority additions. The MD was treating already-shipped substrate as "new work to build". Adjust before sending to codex.

## 🚨 CRITICAL GAP A — `devctl ship` / `release` / `release-gates` orchestration

### What already exists (substantial)

The full release pipeline that P195-P196 cloud-proof should **compose with**, NOT duplicate:

- **`python3 dev/scripts/devctl.py ship --version X`** (mega-orchestrator: `--prepare-release --verify --verify-docs --tag --notes --github --pypi --homebrew --verify-pypi`)
- **`python3 dev/scripts/devctl.py release --version X`** (with `--prepare-release --homebrew --allow-ci --dry-run`)
- **`python3 dev/scripts/devctl.py release-gates`** — polls CI workflows by SHA/branch; `DEFAULT_RELEASE_PREFLIGHT_WORKFLOW = "release_preflight.yml"`
- **Package**: `dev/scripts/devctl/commands/release/` — `gates.py`, `guard.py`, `notes.py`, `prep.py`, `ship.py`, `ship_release_steps.py`, `ship_verify_pypi_step.py`, `prep_updates.py`
- **Shipped workflows**: `publish_homebrew.yml`, `publish_pypi.yml`, `publish_release_binaries.yml`, `release_attestation.yml`, `release_preflight.yml`
- **`dev/scripts/checks/check_release_version_parity.py`**

### Correction needed in MD

**Phase 3 cloud-proof framing was wrong** — `governance_cloud_proof.yml` is NOT new infrastructure for SHA-keyed CI polling. The `release-gates` command ALREADY does SHA-keyed CI workflow polling. P196 `ProofIndex` should:

1. **Plug into `ship_release_steps.py`** as a new step BEFORE `--pypi`/`--homebrew` upload — publication itself becomes proof-receipt-gated, not just push
2. **Extend `release-gates`** to consume `ProofReceipt` from `ProofIndex` instead of only checking workflow conclusion
3. **`devctl ship --verify`** becomes the natural caller for `CodeIdentity` lookup before any external publish step

**Updated Phase 3 directive**: "P195-P196 composes with existing `devctl ship --verify` and `release-gates` orchestration; ProofIndex lookup becomes a new step in `ship_release_steps.py`, not a parallel poller."

## 🚨 CRITICAL GAP B — `AdopterPortabilityValidation` + `dogfood` typed substrate (full second-repo proof system already shipped)

### What already exists

The repo-split proof loop already has typed shipping substrate:

- **`python3 dev/scripts/devctl.py dogfood`** (`--record --report --run-scenario {plan41-tandem,development-loop} --fix-mode {observe,authorized,isolated-worker,conflict-drill} --topology --lane-role --live-run-ref --governance-finding-id --repo-scope --repo-path`)
- **Files**: `dogfood_models.py`, `dogfood_scenarios.py`, `dogfood_scenario_plan41{,_extract,_support}.py`, `dogfood_governance.py`, `dogfood_log.py`, `dogfood_scenario_models.py`
- **`python3 dev/scripts/devctl.py governance-bootstrap --target-repo <path> --force-starter-policy`** — typed bootstrap for adopter repos
- **`.github/workflows/adopter_portability.yml`** — already runs `governance-bootstrap` on greenfield + existing-plan Python adopter fixtures, asserts `AdopterPortabilityValidation` contract contains `ProjectGovernance + MasterPlan + PlanRow` WITHOUT VoiceTerm assumptions
- **`dev/test_data/adopter_repo_fixtures/`** — adopter fixtures dir

### Correction needed in MD

**Phase 6 (Shadow extraction) framing was wrong** — repo-split proof is NOT new work to build. The contract, workflow, fixtures, and CLI all exist.

**Updated Phase 6 directive**: "Repo split proof reuses the shipped `AdopterPortabilityValidation` contract, `adopter_portability.yml` workflow (already gating PR/push on changes to `dev/scripts/devctl/**`), and `dogfood --repo-scope --repo-path` recording; the new work is **graduating `adopter_repo_fixtures/` → real `governance-platform/` standalone checkout**, not building a new proof system."

This significantly reduces Phase 6 scope.

---

## Lower-priority additions

### Addition 1 — Second-Repo Proof Ladder (MP-376)

`dev/active/portable_code_governance.md` has **"Second-Repo Proof Ladder"** (7 graduated steps) + **"External Python Corpus Protocol"** (classify failure as `engine_bug` vs `adopter_finding`). Phase 6 should cite these 7 steps explicitly rather than re-derive acceptance criteria.

### Addition 2 — `concept-view` mode + `graph-walk` for HTML graph viz

`context-graph --mode concept-view` (in `dev/scripts/devctl/context_graph/command.py:172`) renders subsystem-level concept diagrams — exactly what HTML dashboard graph page needs.

`graph-walk --from --to --strategy {cost-ranked,bfs,astar}` with explainable edge weights — enables "trace this packet to its closure receipt" interactive viz.

`--save-snapshot` writes versioned `ContextGraphSnapshot` under `dev/reports/graph_snapshots/` — HTML dashboard could show graph-evolution over time.

**Update Phase 4 directive**: HTML dashboard graph viz consumes `concept-view` mode + `graph-walk` for click-through traces + snapshot-diff for historical viz.

### Addition 3 — `install-git-hooks` managed-hook as local leg of cloud-proof

`python3 dev/scripts/devctl.py install-git-hooks [--check|--uninstall|--force]` already installs typed managed hooks:
- pre-commit commit-permission gate
- post-commit ReviewSnapshot receipts (time-bounded, fail-open)
- pre-push hooks

**Update Phase 3 directive**: cloud-proof `governance_cloud_proof.yml` composes with existing `install-git-hooks` managed pre-push hook — local pre-push already runs the commit-permission gate; cloud proof becomes the second leg of the same authority chain, NOT a parallel system.

### Addition 4 — `RepoPathConfig` swap mechanism (partially solves portability)

`dev/scripts/devctl/repo_packs/` has `RepoPathConfig` dataclass + `VOICETERM_PATH_CONFIG` instance + `WorkflowPresetDefinition` + `_active_path_config_state()` with lru_cache override mechanism. `dev/scripts/devctl/runtime/project_governance_contract.py:289` already accepts `repo_pack_id: str = "portable"`.

**Correction to Addendum 1 Section 3 item 3** — registry indirection ALREADY partially exists as `_active_path_config_state()` swap mechanism. P58.3 work is to: (a) add second repo-pack entry alongside `voiceterm.py` (e.g., `guardir.py`), (b) route `active_path_config()` through typed registry. This is incremental, not greenfield.

---

## Overall Assessment from Agent

> "MD is comprehensive on dashboard architecture, governed_surfaces pipeline, P58.3 portability guard, CodeIdentity primitives, MP-377/376/378 extraction plan, and bridge projection findings. The two gaps above are about **failing to recognize what's already shipped** in the release/dogfood corner of the system, not about missing architectural insight."

> ⚠️ **SUPERSEDED BY ADDENDUM 6**: These updates were merge-deltas to Addendum 3's packet. Both are now superseded by Addendum 6 (below). Retained for audit history only.

## Updated codex-ready packet addendum

Add to the Codex-Ready Packet section under Phase 3:

```
3. (continued) Land P195-P198 as cloud proof:
   - ProofIndex lookup becomes a new step in ship_release_steps.py
     (BEFORE --pypi/--homebrew upload), composing with existing devctl ship
     and release-gates orchestration. Do NOT build parallel SHA-keyed poller.
   - governance_cloud_proof.yml composes with existing install-git-hooks
     managed pre-push hook (same authority chain, two legs).
```

Add to the Codex-Ready Packet section under Phase 6:

```
6. (continued) Shadow extraction reuses already-shipped substrate:
   - AdopterPortabilityValidation contract (already shipped)
   - .github/workflows/adopter_portability.yml (already shipped, gating PR/push on dev/scripts/devctl/**)
   - dogfood --repo-scope --repo-path recording (already shipped)
   - dev/test_data/adopter_repo_fixtures/ (already shipped)
   New work: graduate adopter_repo_fixtures/ → real governance-platform/ standalone checkout.
   New work: route dev/active/portable_code_governance.md "Second-Repo Proof Ladder" (7 steps).
```

## Final Bottom Line (updated for Addendum 4)

The MD's architecture is sound; the **two corrections reduce scope** by recognizing that release-pipeline orchestration + adopter-portability proof infrastructure are ALREADY SHIPPED. Codex's actual implementation work is narrower than the MD originally suggested:

- **Phase 3 = extend `ship_release_steps.py` + `release-gates` with ProofIndex lookup** (not build new orchestration)
- **Phase 6 = graduate adopter fixtures to real repo + route through Second-Repo Proof Ladder** (not build new proof system)

This is good news for codex — less new infrastructure, more composing with existing.

---

# 📋 ADDENDUM 5 — `integrations/ci-cd-hub` (sibling project) + `integrations/code-link-ide` already mapped (2026-05-17 R472)

🎉 **MAJOR DISCOVERY**: operator was right that "CI plans should have been ingested". Two sibling projects at `integrations/` are **already partially adapter-wrapped** + have **typed fit-gap audit mapping specific components to MP scopes with explicit "import pattern now" decisions**. The new cloud-proof + dashboard work should ADAPT these, not reinvent.

## What's at `integrations/ci-cd-hub`

Operator's sibling project (`github.com/jguida941/ci-cd-hub`, pinned SHA submodule) — **Centralized CI/CD for Java and Python repos with config-driven toggles, reusable workflows, single hub running pipelines across many repos**.

### License gate (BEFORE any code copy)
- codex-voice = **MIT** (LICENSE at repo root)
- ci-cd-hub = **Elastic License 2.0** → treat as **reference-only** unless explicit relicensing/permission confirmed
- code-link-ide = no top-level license at pinned SHA → do NOT copy verbatim
- **Safe path**: reimplement patterns in first-party code, validate behavior with local tests

### ci-cd-hub shipped capabilities (verified inline)

**16 reusable workflows** at `integrations/ci-cd-hub/.github/workflows/`:
```
ai-ci-loop.yml          hub-ci.yml              hub-orchestrator.yml
hub-production-ci.yml   hub-run-all.yml         hub-security.yml
java-ci.yml             python-ci.yml           kyverno-ci.yml
kyverno-validate.yml    publish-pypi.yml        release.yml
smoke-test.yml          sync-templates.yml      template-guard.yml
config-validate.yml
```

**Badges JSON** at `integrations/ci-cd-hub/badges/`:
```
bandit.json   mutmut.json   pip-audit.json   ruff.json   zizmor.json
```
(shields.io-compatible badge endpoint format)

**Dashboards JSON** at `integrations/ci-cd-hub/dashboards/`:
```
overview.json     repo-detail.json
```

**23 ADRs** at `integrations/ci-cd-hub/docs/adr/` — high-value design sources for our cloud-proof + dashboard work:
- `0004-aggregation-reporting.md`
- `0005-dashboard-approach.md`
- `0006-quality-gates-thresholds.md`
- `0010-dispatch-token-and-skip.md`
- `0017-scanner-tool-defaults.md`
- `0019-report-validation-policy.md`
- `0020-schema-backward-compatibility.md`
- `0023-deterministic-correlation.md`
- (full list 0001-0023 covers central-vs-distributed, config-precedence, dispatch-orchestration, dashboard-approach, quality-gates, fixtures, monorepo, dispatch-tokens, workflow-versioning, mutation-testing, scanner-defaults, schema-compatibility, java-pom, summary-verification, deterministic-correlation)

**Triage system** (the cloud-proof "AI must consume CI output" pattern operator described):
```bash
cihub triage --latest              # most recent failed run
cihub triage --run <id>            # specific run by ID
# outputs: .cihub/triage.json + .cihub/priority.json + .cihub/triage.md
# env: CIHUB_DEBUG, CIHUB_VERBOSE, CIHUB_DEBUG_CONTEXT, CIHUB_EMIT_TRIAGE
```

**Pre-push validation graduated tiers**:
```bash
cihub check              # Fast: lint, format, type, test (~30s)
cihub check --audit      # + links, adr, configs (~45s)
cihub check --security   # + bandit, pip-audit, trivy, gitleaks (~2min)
cihub check --full       # + templates, matrix, license, zizmor (~3min)
cihub check --all        # Everything including mutation (~15min)
```

**Multi-tool security stack** (exactly what operator referenced):
- Python: Bandit, pip-audit, Semgrep, Trivy, mutmut, Black, Ruff, isort, mypy, pytest, Hypothesis
- Java: jqwik, JaCoCo, Checkstyle, SpotBugs, PMD, OWASP Dependency-Check, Semgrep, Trivy, PITest
- Shared: Semgrep, Trivy, CodeQL, SBOM, Docker
- Kyverno policies at `integrations/ci-cd-hub/policies/kyverno/`

**Core Python package** at `integrations/ci-cd-hub/cihub/`:
```
aggregation.py    badges.py        ci_config.py     ci_report.py
ci_runner.py      cli.py           correlation.py   reporting.py
+ subdirs: ai/, cli_parsers/, commands/, config/, core/, data/,
            diagnostics/, output/, services/, tools/, utils/, wizard/
```

**TypeScript CLI** at `integrations/ci-cd-hub/cihub-cli/` (Node.js separate CLI)

**Central + Distributed dispatch modes**:
- **Central**: hub clones repos + runs pipelines from single workflow
- **Distributed**: hub dispatches workflows to each repo via caller templates + reusable workflows
- 3-tier merge: `defaults → hub config → repo config (repo wins)`

## What codex-voice ALREADY HAS for ci-cd-hub integration (partial adapter)

**Verified existing in this repo**:

1. **`devctl cihub-setup`** command (typed adapter):
```
python3 dev/scripts/devctl.py cihub-setup
  --steps {detect,init,update,validate}
  --cihub-bin CIHUB_BIN
  --repo REPO
  --apply --strict-capabilities --yes --dry-run
  --format {json,md}
```

2. **Parsers + tests**:
   - `dev/scripts/devctl/cihub_setup_parser.py`
   - `dev/scripts/devctl/cli_parser/cihub_setup.py`
   - `dev/scripts/devctl/cli_parser/entrypoint.py` (registers it)
   - `dev/scripts/devctl/tests/test_cihub_setup.py`
   - `dev/scripts/devctl/tests/test_integrations_sync.py`
   - `dev/scripts/devctl/tests/test_triage_loop.py` + `test_triage.py` + `test_mutation_loop.py`

3. **External-repos registry** at `dev/integrations/EXTERNAL_REPOS.md` (2026-02-26):
   - Tracks both `ci-cd-hub` and `code-link-ide` as pinned federation sources
   - Has typed Fit-Gap Audit mapping components to MP scopes

4. **Sync infrastructure**:
   - `dev/scripts/sync_external_integrations.sh`

5. **Documented intake** at `dev/audits/2026-03-24-chatgpt-integration-intake.md`:
   - "ChatGPT Conversation Integration Intake"
   - Has **2026-03-25 Resweep Refresh** noting what's landed vs still-open
   - Owner: MP-377 authority-loop / MP-375 probe-feedback-loop
   - Includes "Authority Rule" — intake is NOT tracked execution plan; must be promoted into MASTER_PLAN.md / platform_authority_loop.md / review_probes.md / portable_code_governance.md

6. **2 partially-ingested packet findings** in `dev/state/plan_index.jsonl`:
   - `PKT-BIND-REV-PKT-3964` (queued) — "Packet finding: Unified settings projection (operator-directed): 24 gates + ci-cd-hub..."
   - `PKT-BIND-REV-PKT-3989` (queued) — "Packet finding: OPERATOR-DRIVEN: ci-cd-hub (already at integrations/ci-cd-hub..."
   - These ARE the lost packets operator mentioned

7. **References across docs**:
   - `dev/audits/architecture_alignment.md` (cihub mention)
   - `dev/audits/2026-02-24-autonomy-baseline-audit.md`
   - `dev/guides/PORTABLE_CODE_GOVERNANCE.md`
   - `dev/guides/DEVCTL_AUTOGUIDE.md`
   - `dev/guides/DEVELOPMENT.md`
   - `dev/guides/ARCHITECTURE.md`
   - `dev/guides/SYSTEM_MAP.md`
   - `dev/config/devctl_repo_policy.json`
   - `dev/config/control_plane_policy.json`
   - `dev/state/baseline_authority_inventories.jsonl`
   - `dev/state/plan_ingestion_receipts.jsonl`

## 🎯 Specific ci-cd-hub components flagged for reuse (per EXTERNAL_REPOS.md Fit-Gap Audit 2026-02-26)

Already mapped against active MP scopes:

| Source | Component | Why it helps codex-voice | MP scope | Decision |
|---|---|---|---|---|
| `ci-cd-hub` | `cihub/services/report_validator/{schema,content,artifact}.py` | Stronger artifact/schema consistency when ingesting CIHub triage outputs | MP-297, MP-298 | **`import pattern now`** |
| `ci-cd-hub` | `cihub/services/triage/{types,evidence,detection}.py` | Better failure typing (`required_not_run`, evidence-based status) and regression signals | MP-297, MP-298, MP-338 | **`import pattern now`** |
| `ci-cd-hub` | `cihub/services/registry/{diff,sync}.py` | Deterministic diff planning for federation sync/import previews | MP-298, MP-334 | `implement later` |
| `ci-cd-hub` | Full workflow/template trees | Too broad / high drift risk | n/a | `do not bulk import` |

## Specific code-link-ide components flagged for reuse (sibling integration)

| Source | Component | Why | MP scope | Decision |
|---|---|---|---|---|
| `code-link-ide` | `agent/src/commands/path.rs` | Canonical-path + allowlist guard for remote-action safety | MP-332, MP-340 | **`import pattern now`** |
| `code-link-ide` | `agent/src/schema.rs`, `agent/schemas/*` | Deterministic schema validation for controller-state/action payload contracts | MP-330, MP-340 | **`import pattern now`** |
| `code-link-ide` | `agent/src/audit.rs` | **Hash-chain audit log + retention/compression for tamper-evident control actions** | MP-332, MP-340 | **`import pattern now`** |
| `code-link-ide` | `agent/src/ws/routing.rs`, `agent/src/commands/types.rs` | Typed envelope + error-code surface for future Rust voiceterm-control | MP-330, MP-331 | `implement later` |

## 🔥 MAJOR IMPACT on may17th.md Phase plan

### Phase 3 (P195-P198 cloud proof) is NARROWER than originally framed

The new packet should explicitly route through ci-cd-hub patterns:

- **Triage bundles**: do NOT design from scratch — adapt `cihub/services/triage/{types,evidence,detection}.py` per EXTERNAL_REPOS.md decision. ChatGPT-Pro's "machine-readable CI failures → repair" = ci-cd-hub's `priority.json` + `triage.md` + `triage.json` already.
- **Report validation**: do NOT design from scratch — adapt `cihub/services/report_validator/{schema,content,artifact}.py`. P198 `CloudFinding` shape comes directly from ci-cd-hub's existing artifact/schema validation.
- **Badges**: ci-cd-hub already emits shields.io-compatible badge JSONs (bandit/mutmut/pip-audit/ruff/zizmor). Our dashboard's public projection should use the same pattern.
- **Multi-tool security stack**: ci-cd-hub's Bandit + pip-audit + Semgrep + Trivy + CodeQL + SBOM + zizmor is exactly what `governance_cloud_proof.yml` should compose. We don't need to invent the security check matrix.
- **Graduated tiers** (`cihub check` → `--audit` → `--security` → `--full` → `--all`): exact same pattern operator implicitly wants for local fast → cloud comprehensive.

### Phase 4 (HTML dashboard) gets free architecture sources

- ADR `0005-dashboard-approach.md` is the design source. Read this BEFORE designing `dashboard_render/html.py`.
- ADR `0004-aggregation-reporting.md` informs how dashboard aggregates from multiple sources.
- ADR `0019-report-validation-policy.md` informs DashboardPublishPolicy.
- ADR `0006-quality-gates-thresholds.md` informs public-dashboard gating.
- ci-cd-hub's `dashboards/overview.json` + `dashboards/repo-detail.json` are template structures.

### Phase 2 (P58.3 portability) gets cross-repo dispatch design

ci-cd-hub's Central vs Distributed dispatch modes + 3-tier merge directly informs second-repo proof:
- Central mode = how `dogfood --repo-scope --repo-path` should orchestrate
- Distributed mode = how second-repo adopter triggers governance run via PAT/dispatch
- 3-tier merge (`defaults → hub → repo config`) = exact pattern for repo-pack config layering

### Phase 6 (Shadow extraction) gets adopter integration pattern

ci-cd-hub's own `init` / `setup` / `validate` flow IS the adopter onboarding pattern:
```bash
python -m cihub init --repo . --apply       # generate config + workflow
cihub validate --repo .                      # validate .ci-hub.yml against schema
```
Our `devctl cihub-setup --steps {detect,init,update,validate}` already wraps this; extend to general adopter case.

## 🚨 What was "lost in packets" (operator's concern)

Specifically:
- `PKT-BIND-REV-PKT-3964` (queued) — Unified settings projection (24 gates + ci-cd-hub)
- `PKT-BIND-REV-PKT-3989` (queued) — "OPERATOR-DRIVEN: ci-cd-hub (already at integrations/ci-cd-hub..."

Both are `status: queued` in plan_index.jsonl — never promoted to active execution. The 2026-03-25 Resweep Refresh in `chatgpt-integration-intake.md` did partial reconciliation but doesn't capture these specific packets.

**Recommendation**: When codex starts Phase 3, the first step should be to:
1. Read `dev/audits/2026-03-24-chatgpt-integration-intake.md` 2026-03-25 Resweep Refresh section
2. Read `dev/integrations/EXTERNAL_REPOS.md` Fit-Gap Audit (2026-02-26)
3. Read 6-8 most relevant ci-cd-hub ADRs (0004, 0005, 0006, 0010, 0017, 0019, 0020, 0023)
4. Re-promote PKT-BIND-REV-PKT-3964 + PKT-BIND-REV-PKT-3989 from queued → applied with explicit composition pattern
5. THEN start P196 `CodeIdentity` design using ci-cd-hub's existing `correlation.py` + `aggregation.py` as reference

> ⚠️ **SUPERSEDED BY ADDENDUM 6**: These additions are now folded into Addendum 6's operative 9-phase packet. Retained for audit history only.

## Updated codex-ready packet addendum (Phase 3 specific)

Add to Codex-Ready Packet under Phase 3:

```
3. (continued) Land P195-P198 as cloud proof — compose with ci-cd-hub patterns:
   - Adapt cihub/services/triage/{types,evidence,detection}.py for P198 CloudFinding
     (per EXTERNAL_REPOS.md 2026-02-26 decision "import pattern now")
   - Adapt cihub/services/report_validator/{schema,content,artifact}.py for
     ProofReceipt artifact validation
   - Reuse shields.io-compatible badge JSON pattern from cihub/badges/ for
     public dashboard projection
   - Read ADRs 0004 (aggregation-reporting), 0005 (dashboard-approach),
     0006 (quality-gates-thresholds), 0019 (report-validation-policy),
     0020 (schema-backward-compatibility), 0023 (deterministic-correlation)
     BEFORE designing P196 substrate
   - LICENSE GATE: ci-cd-hub is Elastic 2.0; reimplement patterns, do NOT
     copy-paste verbatim. codex-voice is MIT.
   - Re-promote PKT-BIND-REV-PKT-3964 + PKT-BIND-REV-PKT-3989 from queued
     to applied with composition decisions per EXTERNAL_REPOS.md Fit-Gap Audit
```

Add to Codex-Ready Packet under Phase 6:

```
6. (continued) Shadow extraction also reuses ci-cd-hub adopter pattern:
   - cihub init/setup/validate flow IS the adopter onboarding pattern
   - devctl cihub-setup --steps {detect,init,update,validate} already wraps it
   - Extend devctl cihub-setup to general "governance-platform-setup" verb for
     new repos adopting the standalone platform
   - 3-tier config merge (defaults → hub → repo) directly informs repo-pack
     config layering for guardir/voiceterm separation
```

## Final Bottom Line (after Addendum 5)

The MD's architecture is sound; the **third correction** (Addendum 5) **further reduces scope** by recognizing that ci-cd-hub already implements substantial cloud-proof + dashboard + adopter patterns. The 2026-02-26 Fit-Gap Audit at `EXTERNAL_REPOS.md` already made specific "import pattern now" decisions for 5 components across MP-297/MP-298/MP-330/MP-332/MP-338/MP-340.

**Codex's actual implementation work** is even narrower than Addendum 4 suggested:

- **Phase 3 = adapt 2 ci-cd-hub service trees** (triage + report_validator) + read ~8 ADRs as design source + extend `devctl cihub-setup` per existing partial adapter — NOT build from scratch
- **Phase 4 = adopt ci-cd-hub dashboards + badges JSON pattern** + add HTML renderer + DashboardPublishPolicy
- **Phase 6 = generalize `devctl cihub-setup` flow** to platform-adopter onboarding + adopt ci-cd-hub's 3-tier merge

The 2 "lost" packets (PKT-BIND-REV-PKT-3964 + PKT-BIND-REV-PKT-3989) get re-promoted as part of Phase 3 entry. The ChatGPT-Pro intake at `chatgpt-integration-intake.md` gets its 2026-03-25 Resweep Refresh extended with the cloud-proof + dashboard items from this MD.

**This means the operator's whole research session (Addendums 1-5) ultimately produces a packet that says: "do the work that was already speced as ci-cd-hub composition + 5 EXTERNAL_REPOS.md Fit-Gap items + 2 queued PKT-BINDs."** That's a much smaller ask than "build new cloud-proof infrastructure" — it's "execute the already-decided composition decisions, with the architectural sequencing of Addendum 2 + 3 + 4 governing order."

---

# 📋 ADDENDUM 6 — Final Operative Codex Packet: P58.3 → P195-P198 via ci-cd-hub composition (2026-05-17 R473)

## ⚠️ Supersession note

**This Addendum 6 contains the CURRENT OPERATIVE Codex-ready packet.** Earlier Codex-ready packets in Addendums 3–5 are retained for audit history only and should NOT be used as the active instruction to codex. Supersession markers have been added to each prior packet block above. Use the packet in this Addendum 6 as the single source operator sends to codex.

## Final decision

The original research (Addendums 1-2) identified the architecture. Codex/ChatGPT-Pro reviews (Addendums 3-5) corrected sequencing + recognized already-shipped substrate (release-gates, AdopterPortabilityValidation, ci-cd-hub partial adapter). This Addendum 6 finalizes the 9-phase operative sequence with one critical addition: **explicit intake-recovery preflight step before P195/P196 coding**, preventing the recurring failure class operator identified ("CI plans were supposed to be ingested but lost in packets").

**Architecture**: P195-P198 = cloud-proof lane. P58.3 = extraction gate. Dashboard HTML = projection over DashboardSnapshot v3. ProofIndex must exist before public dashboard publishing. ci-cd-hub patterns are design source (reimplement under MIT, do not copy under Elastic 2.0).

**Sequence (9 phases)**:
| Phase | Work |
|---|---|
| **0** | Bridge/projection authority cleanup |
| **1** | Finish current enforcement/absorb/checkpoint slice |
| **2** | P58.3 portability boundary (BEFORE cloud proof — keep here, don't reorder) |
| **3** | Intake recovery preflight (read existing ci-cd-hub decisions; re-promote lost packets) |
| **4** | P195-P198 cloud proof implementation (compose with release-gates + ship + ci-cd-hub patterns) |
| **5** | Dashboard HTML renderer + DashboardPublishPolicy + check_dashboard_publish_policy.py |
| **6** | Public Pages deployment (public bundle only) |
| **7** | Shadow extraction (governance_platform/ local sibling package) |
| **8** | Separate repo (only after second-repo proof ladder green) |

**Operational deliverable** (Phase 3 must produce this BEFORE Phase 4 coding begins):
- Re-promote `PKT-BIND-REV-PKT-3964` (Unified settings projection: 24 gates + ci-cd-hub) from `queued` → typed composition decision row
- Re-promote `PKT-BIND-REV-PKT-3989` (OPERATOR-DRIVEN: ci-cd-hub already at integrations/ci-cd-hub) from `queued` → typed composition decision row
- Mark dispositions clearly: `applied` / `composed` / `superseded` per repo's valid status model
- Tie both rows to `dev/integrations/EXTERNAL_REPOS.md` Fit-Gap Audit (2026-02-26) + `dev/audits/2026-03-24-chatgpt-integration-intake.md` 2026-03-25 Resweep evidence
- This deliverable IS the intake-recovery proof; without it, Phase 4 risks rebuilding what was already designed

## 📦 OPERATIVE Codex-ready packet (single source — copy-paste this version)

```
Title:
Execute existing cloud-proof/dashboard/repo-split plan through P58.3 + P195-P198 + ci-cd-hub composition; do not create parallel P240

Summary:
Operator's dashboard/cloud/repo-split research is accepted with sequencing
corrections. Do not create MP-NEW-P240. The cloud-proof design maps to existing
P195-P198 and to previously documented ci-cd-hub fit-gap decisions. Dashboard
is a projection over DashboardSnapshot v3, not a new authority contract. Repo
split is blocked on P58.3 portability.

Immediate directives:

0. Surgical bridge/projection cleanup:
   - Fix bridge/projection authority semantics before dashboard/cloud projection work.
   - Extend check_bridge_projection_only.py to the currently flagged bridge/projection files.
   - Add projection_only metadata and source contract pointers.
   - Ensure bridge/event projections cannot become durable authority.

1. Finish current enforcement-path / absorb-layer / checkpoint work:
   - distinct blocked / rejected / needs_operator_decision summary fields
   - deterministic latest-valid semantic ingestion receipt selection
   - regression test for wrong actor/role/session scope
   - regression test for plan-affecting row without PlanProposal or
     PacketPlanIntegration evidence
   - safe typed path for non-mutating feedback events under ControlDecisionObeyedGuard:
     decision / finding / task_progress / operator_routed are classified as
     non-mutating feedback events and require typed non-mutating authorization,
     not mutation authority
   - do NOT proceed to cloud-proof or dashboard work while checkpoint/staging/push
     publication remains dirty or blocked, except for surgical Phase 0 bridge fixes

2. Land P58.3 portability:
   - remove hardcoded voiceterm leakage from generic platform paths
   - remaining voiceterm hits must be repo-pack / product / adopter / test only
   - use existing RepoPathConfig / active_path_config registry mechanism where possible
   - add or extend a guard proving generic platform code is adopter-portable
   - do NOT extract repo before P58.3 is green

3. Phase 3 preflight — recover existing ci-cd-hub decisions BEFORE coding:
   - read dev/integrations/EXTERNAL_REPOS.md Fit-Gap Audit from 2026-02-26
   - read dev/audits/2026-03-24-chatgpt-integration-intake.md AND 2026-03-25 Resweep Refresh
   - inspect PKT-BIND-REV-PKT-3964 and PKT-BIND-REV-PKT-3989 in plan_index.jsonl
   - PROMOTE these packet-bindings into typed composition decision rows
     (applied / composed / superseded per repo status model)
   - tie rows to EXTERNAL_REPOS.md Fit-Gap Audit + ChatGPT integration intake/resweep
   - read ci-cd-hub ADRs:
     0004 aggregation-reporting
     0005 dashboard-approach
     0006 quality-gates-thresholds
     0010 dispatch-token-and-skip
     0017 scanner-tool-defaults
     0019 report-validation-policy
     0020 schema-backward-compatibility
     0023 deterministic-correlation
   - LICENSE GATE: ci-cd-hub is Elastic 2.0 and codex-voice is MIT.
     Reimplement patterns; do NOT copy code verbatim unless permission/relicensing is confirmed.

4. Land P195-P198 as cloud proof, composing with existing release/ship and ci-cd-hub patterns:
   - CodeIdentity as composite of commit SHA, tree hash, config hash, policy hash,
     guard-bundle hash, and dependency/environment identity
   - CloudProofRun
   - CloudProofReceipt
   - CloudProofArtifact
   - ProofIndex
   - ProofAuthorityDecision
   - CloudFinding
   - RepairPacket
   - governance_cloud_proof.yml for feature branch + PR + workflow_dispatch
   - use matrix shards with one aggregate proof_receipt.json
   - devctl github-actions ingest
   - CI logs feed CommandOutputReceipt + CommandOutputConsumptionReceipt
   - default ProofExecutionMode is hybrid
   - ProofIndex lookup becomes a step in existing devctl ship / ship_release_steps.py
     before pypi/homebrew/external publish
   - release-gates should consume ProofReceipt / ProofIndex rather than only
     checking workflow conclusion
   - devctl push consults local ProofIndex for HEAD tree hash; NO live GitHub
     network call inside push
   - governance_cloud_proof.yml composes with existing install-git-hooks managed
     pre-push hook as the cloud leg of the same authority chain

5. Use ci-cd-hub patterns for Phase 4 implementation:
   - reimplement cihub triage patterns for P198 CloudFinding / RepairPacket
   - reimplement cihub report-validator patterns for ProofReceipt artifact validation
   - reuse shields.io-compatible badge JSON pattern for public dashboard status
   - use ci-cd-hub graduated tiers as model:
     fast local → audit → security → full → mutation/all
   - do NOT bulk-import ci-cd-hub workflows or service trees

6. Add dashboard HTML only after proof substrate:
   - dashboard_render/html.py consumes DashboardSnapshot v3
   - do NOT create HtmlDashboardSnapshot
   - add DashboardPublishPolicy
   - add internal/public dashboard split
   - add check_dashboard_publish_policy.py
   - dashboard_pages.yml deploys public bundle only
   - dashboard graph view should use context-graph concept-view, graph-walk,
     and snapshot diffs where available
   - dashboard public state may use ci-cd-hub badge JSON pattern

7. Shadow extraction reuses already-shipped adopter proof substrate:
   - AdopterPortabilityValidation contract
   - .github/workflows/adopter_portability.yml
   - dogfood --repo-scope --repo-path
   - dev/test_data/adopter_repo_fixtures
   - governance-bootstrap --target-repo
   - devctl cihub-setup --steps detect,init,update,validate
   - new work is graduating adopter_repo_fixtures into real governance_platform
     standalone checkout
   - route through dev/active/portable_code_governance.md Second-Repo Proof Ladder
   - generalize cihub-setup pattern into governance-platform setup for new adopter repos
   - use 3-tier config merge pattern: defaults → platform/hub → repo config

8. Repo extraction only after:
   - P58.3 green
   - second-repo proof ladder green
   - governance substrate installs in second repo
   - repo-pack config can be minted in second repo
   - guards run without VoiceTerm assumptions
   - system map and review snapshot generate in adopter repo
   - no hardcoded voiceterm refs outside allowed adopter config

Do not:
- create P240 as a parallel cloud-proof lane
- create HtmlDashboardSnapshot
- publish internal dashboard sections
- extract repo before portability proof
- make devctl push depend on live GitHub network calls
- treat GitHub Actions green as proof unless logs/artifacts are ingested into typed receipts
- copy ci-cd-hub or code-link-ide code verbatim without license clearance
- build a new adopter proof system when AdopterPortabilityValidation and dogfood substrate already exist

Caveat:
P195-P198 are queued/speced but unimplemented. Start from ZERO implementation,
but do NOT start from zero design. Use the existing plan rows, EXTERNAL_REPOS.md
fit-gap audit, ci-cd-hub ADRs, and PKT-BIND-REV-PKT-3964 / PKT-BIND-REV-PKT-3989
as design authority.
```

## VoiceNode-short version (operative)

```
Final decision:
Do not create P240. P195 through P198 are the cloud-proof lane.

The order is:
Phase 0: fix bridge and projection authority semantics.
Phase 1: finish the current enforcement, absorb-layer, checkpoint, and staging work.
Phase 2: land P58.3 portability. Remove hardcoded VoiceTerm leakage BEFORE cloud
         proof, dashboard, or repo split.
Phase 3: recover existing ci-cd-hub decisions before coding. Read EXTERNAL_REPOS.md,
         the ChatGPT integration intake, the 2026-03-25 resweep, and packets 3964
         and 3989. PROMOTE those packets into typed composition decision rows.
         Use ci-cd-hub patterns, but do not copy code because ci-cd-hub is
         Elastic 2.0 and this repo is MIT.
Phase 4: land P195 through P198 cloud proof. Add CodeIdentity, CloudProofReceipt,
         ProofIndex, CloudFinding, RepairPacket, governance_cloud_proof.yml, and
         devctl github-actions ingest. Devctl push checks local ProofIndex, not
         GitHub live. Release-gates and devctl ship should consume ProofIndex
         before publishing.
Phase 5: add HTML dashboard only after ProofIndex exists. Use DashboardSnapshot v3.
         Do not create HtmlDashboardSnapshot. Add DashboardPublishPolicy and
         public/internal split.
Phase 6: deploy the public dashboard only.
Phase 7: shadow extraction into a local governance_platform package. Reuse
         AdopterPortabilityValidation, adopter_portability.yml, dogfood
         repo-scope, governance-bootstrap, and devctl cihub-setup.
Phase 8: separate repo only after the second-repo proof ladder passes.

Important: GitHub Actions green is not proof unless logs and artifacts are
ingested into typed receipts.
Important: non-mutating feedback packets should be typed as safe feedback events,
not broad ControlDecisionObeyedGuard bypasses.
Important: VoiceTerm keeps its ledgers, receipts, projections, and history. The
platform repo gets schemas, contracts, guards, renderers, workflow templates,
and generic docs.

Bottom line: finish absorb-layer fixes, land P58.3, then implement the first
P195/P196 proof contracts and governance_cloud_proof.yml by adapting existing
ci-cd-hub patterns.
```

## Why append + supersede (not replace)

Replacing Addendums 3-5's packets would hide the evolution of the decision and lose audit trail. Leaving them without a supersession note creates ambiguity (which is current?). The supersession-note pattern is the clean governance move: prior packets remain inspectable as research-history, Addendum 6 is unambiguously identified as the operative version.

This pattern matches the broader memory ×14 ProofGraphKernel principle — every architectural decision should be auditable through its evolution, not collapsed into final state with history erased.
