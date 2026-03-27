# Architecture Alignment Audit

**Created**: 2026-03-26 | **Owner**: MP-377 / MP-376
**Method**: Initial baseline from an 8-agent parallel audit across devctl subsystems

**Current operating mode**: Claude is the primary broad whole-system finder.
Codex is the reviewer/controller that verifies Claude deltas against code/docs
before promoting verified findings into `MASTER_PLAN` and the scoped owner
plans. This file is the shared audit ledger, not the execution owner.

## Executive Summary

Portability remains **partial and not yet scoreable by a governed rubric**.
The core engine (guards, probes, quality-policy, context-graph builder,
autonomy orchestration) is governance-driven and has real external-repo proof,
but hidden VoiceTerm defaults, governed-markdown shape assumptions, and review/
artifact path literals still block arbitrary-repo closure.

The root cause is broader than one fallback bug: runtime contracts, generated
instruction surfaces, docs-governance, and review/startup control-plane code
still mix portable authority (`ProjectGovernance`) with silent VoiceTerm
defaults, especially when governance payloads are partial or absent.

Self-hosting organization is part of that architecture gap too. The current
repo still has 27 markdown docs under `dev/active/` and 10 root-level
markdown entrypoints, so any archive/consolidation pass is blocked until
execution-relevant conclusions are absorbed into the canonical owner chain
(`MASTER_PLAN` plus scoped plans) instead of living only in reference docs.

## Live Blocker Routing

| Live blocker | Owner doc | Exact section | Why |
|---|---|---|---|
| Product-doc vs AI-system-doc boundary and self-hosting compression | `dev/active/ai_governance_platform.md` | `## Session Resume` -> `### Current status` | repo-wide `MP-377` architecture authority |
| `DocPolicy` / `DocRegistry`, fail-closed authority discovery, and push packet truth | `dev/active/platform_authority_loop.md` | `## Execution Checklist`, `## Session Resume` | current subordinate execution spec |
| Custom-layout proof, optional-capability gating, organization proof, and adopter-facing push honesty | `dev/active/portable_code_governance.md` | `## Session Resume` | narrower portable/adopter proof owner |
| Review-channel `current_session` producer cutover and bridge compatibility retirement | `dev/active/review_channel.md` | `## Session Resume` | subordinate `MP-355` producer lane |

Use this audit as evidence and routing support. Do not treat it as a second
execution roadmap once the owner docs above have absorbed a finding.

## Critical Architecture Issues

### Issue 1: Import-Time Path Freezing (36 Files Affected)

`review_channel/core.py` lines 38-42 freeze `active_path_config()` into
module-level constants at import time:

```python
DEFAULT_BRIDGE_REL = active_path_config().bridge_rel
DEFAULT_REVIEW_CHANNEL_REL = active_path_config().review_channel_rel
```

36 files import these frozen constants. Even if governance loads later
with different paths, the constants remain VoiceTerm values.

**Fix**: Replace module-level constants with function calls that resolve
at call time, or require `set_active_path_config()` before any imports.

### Issue 2: Governance Parser Fallback Defaults

`project_governance_parse.py` line 68 and `project_governance_contract.py`
hardcode defaults when governance JSON fields are missing:

```python
bridge_path = coerce_string(payload.get("bridge_path")) or "bridge.md"
review_channel_path = ... or "dev/active/review_channel.md"
```

These are VoiceTerm conventions. A repo without bridge.md or with plans
in a different directory gets wrong defaults silently.

**Fix**: Make defaults come from `RepoPathConfig` instead of string
literals. Or require explicit configuration (fail-closed when missing).

### Issue 2b: Portable Doc/Plan Authority Still Defaults To VoiceTerm Filenames

`project_governance_contract.py`, `project_governance_doc_parse.py`, and
`project_governance_plan_parse.py` still seed `AGENTS.md`,
`dev/active/INDEX.md`, and `dev/active/MASTER_PLAN.md` when doc/plan
authority fields are missing or partial.

These are VoiceTerm conventions, not universal platform requirements. A repo
with a different docs authority file, plan tracker name, or registry path can
silently collapse back to VoiceTerm-shaped startup authority instead of
surfacing an explicit missing-contract error.

**Fix**: keep repo-pack/bootstrap defaults scoped to this repo-pack only, but
require portable runtime/draft/startup layers either to discover repo-owned
authority from governance state or fail closed. Cross-repo proof must include
at least one custom-layout repo that does not use `AGENTS.md`,
`dev/active/INDEX.md`, or `dev/active/MASTER_PLAN.md`.

### Issue 2c: Docs Governance Still Pushes AI-System Guidance Into VoiceTerm User Docs

The repo still treats some `MP-355` / `MP-377` review-channel, startup, and
operator-control changes as if the right repair were to update VoiceTerm end-
user docs (`README`, `QUICK_START`, `guides/USAGE`, `guides/CLI_FLAGS`,
`guides/INSTALL`, `guides/TROUBLESHOOTING`).

That mixes two different products:

- VoiceTerm end-user behavior and product-facing help.
- The reusable AI-governance system's self-hosting, operator, startup, review,
  and organization contracts.

This is not just a wording issue. If docs policy keeps forcing AI-system
control-plane guidance into VoiceTerm product docs, the repo will keep hiding
the real architecture split behind markdown churn and external-repo adoption
will inherit the wrong mental model.

**Fix**: classify docs by typed artifact role and scope, keep VoiceTerm user
docs product-only, route AI-system self-hosting/operator guidance into the
`MP-377` owner chain plus maintainer/generated surfaces, and make docs policy
enforce that split before more packaging or adopter proof work.

### Issue 3: Conductor Prompt Hardcodes Product Name

`review_channel/prompt.py` lines 130-135:

```python
f"You are the fresh {provider_name} conductor for a planned VoiceTerm "
```

Any repo using the conductor tells Claude/Codex they're the "VoiceTerm
conductor." Also hardcodes "MP-355" as the review-channel plan ID.

**Fix**: Read product name from `ProjectGovernance.repo_identity.repo_name`
and plan ID from plan registry.

### Issue 4: 460+ Hardcoded References in Guard Scripts

| Category | Count | Files | Example |
|---|---|---|---|
| `voiceterm` substring | 160+ | 14 | check_repo_url_parity.py |
| `rust/src/bin/voiceterm/` | 75+ | 12 | check_rust_test_shape.py |
| `jguida941` username | 26 | 8 | check_repo_url_parity.py |
| `dev/active/MASTER_PLAN.md` | 10 | 5 | check_active_plan_sync.py |
| `dev/active/review_channel.md` | 180+ | 8+ | tandem_consistency/ |
| `bridge.md` literal | 9 | 3 | check_review_channel_bridge.py |

**Classification**: ~60% are legitimate repo-specific guards (code shape
policies, CLI flag checks). ~40% should be parameterized (governance
doc paths, repo identity, bridge path).

### Issue 5: Ralph Architecture Checks Hardcoded

`ralph_ai_fix.py` hardcodes test commands per architecture:

```python
"rust": [["cargo", "test", "--bin", "voiceterm", ...]],
"python-devctl": [["python3", "-m", "pytest", "dev/scripts/devctl/tests/", ...]],
```

**Fix**: Make architecture-to-test-command mapping configurable from
repo policy or RepoPathConfig.

## Portability by Subsystem

| Subsystem | Portable? | Key Blocker |
|---|---|---|
| **ProjectGovernance** | YES | None — fully governance-driven |
| **WorkIntakePacket** | YES | None — plan-registry-driven |
| **StartupContext** | CONDITIONAL | Requires `set_active_path_config()` call |
| **Context Graph builder** | 95% | 3 hardcoded concept keywords |
| **Context Graph query/render** | YES | None |
| **Guard-run orchestration** | YES | None |
| **Autonomy-loop** | YES | Policy-driven branches |
| **Quality-policy** | YES | None |
| **Render-surfaces** | YES | Needs policy config |
| **Data-science/watchdog** | YES | None |
| **Review-channel commands** | 60% | Import-time freezing, prompt hardcodes |
| **Ralph AI fix** | 60% | Architecture check hardcodes |
| **Docs-check** | NO | Hardcoded doc paths in policy_defaults |
| **Guard scripts** | 60% | 460+ hardcoded references |
| **Operator console** | NO (by design) | VoiceTerm-specific UI |
| **Bridge.md** | N/A | Being deprecated to optional projection |

## Feedback Loop Status

| Loop | Status | Evidence |
|---|---|---|
| Probe → fix → probe knows (allowlist) | **CLOSED** | probe_gate filters via allowlist |
| Governance verdict → next probe excludes | **CLOSED** | decision_packets filter by allowlist |
| Ralph fix → next attempt learns | **OPEN** | ralph-report.json not read by next attempt |
| Watchdog failure → context escalation | **CLOSED** | operational_feedback → context packet |
| Quality feedback → decision constraints | **CLOSED** | quality_feedback_lines → escalation |

## ZGraph Decision Wiring Points (~210 Lines Total)

| Component | Graph Data Available | Used? | Lines to Wire |
|---|---|---|---|
| ralph_prompt.py | Temperature in nodes | No (markdown only) | ~25 |
| autonomy_loop.py | Not loaded | No | ~50 |
| triage/enrich.py | Not queried | No (static severity) | ~65 |
| quality_backlog/priorities.py | fan_in/fan_out | No (static weights) | ~40 |
| WorkIntakePacket | Not loaded | No (text matching) | ~30 |

## Self-Hosting Status

| Aspect | Status |
|---|---|
| Guards run on own code | Quick passes; CI absolute finds 8 violations |
| 3 guard files exceed own limits | HARD violations (check_rust_best_practices.py 706 lines) |
| Plan docs governed by guards | YES (3+ guards scan dev/active/) |
| CLAUDE.md generated by render-surfaces | YES |
| Differential scanning catches violations | NO (needs --absolute) |
| System consumes own plans | YES (guards, startup-context, work-intake) |

## Proof/Explanation Gaps

| Artifact | Has Structured Proof? | Gap |
|---|---|---|
| Guard violations | YES (reason + guidance + policy) | — |
| Probe guidance | YES (decision_mode + rationale) | rationale optional |
| Autonomy stop | YES (reason codes) | No triage classification |
| Governance review | PARTIAL (verdict only) | No explanation field |
| Context graph query | MINIMAL (match count) | No "why matched" |
| Ralph fix | PARTIAL (status only) | No reasoning chain |

## Operator Visibility Gaps

- NO unified finding→guidance→fix→verdict chain view
- NO guidance_id populated in production (field exists, 0 rows use it)
- NO historical guard flakiness trends (current snapshot only)
- NO single "system health" dashboard command
- `devctl system-picture` planned but not implemented

## Codex's 4-Layer Enforcement Stack (Validated)

Codex proposed and Codex is correct that the fix is:

1. **Portable layers resolve from ProjectGovernance or fail closed**
2. **AI/bootstrap instructions render from governance, not hardcoded**
3. **Portability-drift guard flags repo/path literals in portable code**
4. **Fixture-repo proof: empty repo, existing repo, alternate layout**

This is tracked in:
- AGENTS.md:15 (portability rule)
- MASTER_PLAN.md:273 (portability audit correction)
- ai_governance_platform.md:2456
- platform_authority_loop.md:1177
- DEVELOPMENT.md:276

## Recommended Implementation Order

1. **Fix import-time freezing** (36 files) — highest blast radius
2. **Add portability-drift guard** — prevents regression
3. **Parameterize governance parser defaults** — fail-closed when missing
4. **Extract conductor prompt product name from governance**
5. **Make ralph architecture checks configurable**
6. **Add fixture-repo proof tests** (empty, alternate layout, tandem-disabled)
7. **Move docs-check hardcoded paths to governance config**

## Relationship to ChatGPT Integration Intake

This audit complements `dev/audits/2026-03-24-chatgpt-integration-intake.md`
which found 21 gaps + 20 disconnections + 4 self-improvement guards.
The architecture alignment audit focuses specifically on **portability**
and **VoiceTerm coupling** — a different dimension from the feedback
loop/decision-wiring gaps in the intake doc.

Both documents feed into the same MP-377 / MP-376 plan lanes.

## Second-Pass Findings (4-Agent Deep Audit)

### Plan Coverage: 6 of 7 Issues Tracked

All architecture alignment issues except one have explicit plan tasks:

| Issue | Plan Status | Location |
|---|---|---|
| Import-time freezing | TRACKED (51 call sites, guard planned) | platform_authority_loop.md:539-541, 1623 |
| Governance parser defaults | TRACKED (silent fallback removal) | platform_authority_loop.md:521-547 |
| Conductor prompt hardcodes | TRACKED (render from governed state) | platform_authority_loop.md:1184 |
| Portability drift guard | TRACKED (explicit guard spec) | platform_authority_loop.md:577-587 |
| Fixture-repo proof tests | TRACKED | platform_authority_loop.md:275-276 |
| 460 hardcoded refs | IMPLICIT (category tracked, not count) | platform_authority_loop.md:582 |
| **Ralph architecture-check parameterization** | **TRACKED** | ralph_guardrail_control_plane.md Phase 2 / MASTER_PLAN MP-361 |

### Import-Time Freezing: Exact Impact

36 frozen `active_path_config()` calls across 14 files:

- `review_channel/core.py`: 3 frozen (bridge, channel, rollover)
- `review_channel/event_store.py`: 4 frozen (artifact root, event log, state JSON, projections)
- `data_science/metrics.py`: 4 frozen (output root, swarm, benchmark, watchdog)
- `autonomy/report_helpers.py`: 3 frozen (source, library, event log)
- `autonomy/run_parser.py`: 8 frozen in argparse defaults
- `autonomy/benchmark_parser.py`: 4 frozen in argparse defaults
- `cli_parser/reporting.py`: 4 frozen in argparse defaults
- 6 more files with 1-2 frozen each

Safe calls (inside functions): 9 files call at runtime, not import time.

### Causal Chain: Architecture Issues → Intake Gaps

The 4-agent cross-reference found that architecture alignment issues
are ROOT CAUSES of ChatGPT intake disconnections:

1. **Import-time freezing** → prevents startup-context from updating
   paths → **causes intake Gap 4 (session decision log)** and
   **bootstrap skip** because system can't change course at startup
2. **Governance parser defaults** → prevents RepoPathConfig override →
   **causes intake Finding E (WorkIntakePacket never consumed)**
3. **Conductor hardcodes** → can't render from governance →
   **causes intake meta-finding "Missing Instruction Surface"**
4. **460 hardcoded refs** → blocks portability tests →
   **causes intake Finding G (79 orphan models never wired)**

### Portable Test Coverage: Critical Gaps

| Path | Unit Tested | Subprocess Tested | Manual Proof |
|---|---|---|---|
| governance-bootstrap | YES | YES | YES (ci-cd-hub) |
| Guard execution (49 types) | YES (mocked) | **NO** | YES (ci-cd-hub) |
| Probe execution (28 types) | YES (mocked) | **NO** | YES (ci-cd-hub) |
| Policy file resolution | YES (mocked) | **NO** | YES (ci-cd-hub) |
| Adoption-scan mode | YES (1 guard) | **NO** | YES (ci-cd-hub) |
| Full check --profile ci --repo-path | **NO** | **NO** | YES (ci-cd-hub) |

The "80% portable" claim is proven only by manual external runs.
No automated test creates a non-VoiceTerm repo layout and runs
guards/probes against it. The ci-cd-hub proof is real but not in CI.

**Needed**: 4 integration tests:
1. `test_guards_portable_execution.py` — guards against tmpdir repo
2. `test_probes_portable_execution.py` — probes with custom policy
3. `test_check_portable_adoption_scan.py` — full adoption-scan E2E
4. CI pipeline running ci-cd-hub validation automatically

### ZGraph Findings Consistent Across Both Audits

Both `architecture_alignment.md` and `chatgpt-integration-intake.md`
independently identify the same 5 ZGraph decision wiring points with
identical line counts (~210 total). No contradictions found between
the two audit documents.

## Pass 1 Findings (8-Agent Sweep, 2026-03-26)

Net-new HIGH/MEDIUM findings from first full subsystem sweep. Format:
subsystem | severity | evidence | class | prevention | owner plan.

### HIGH: cli.py handler imports freeze paths at module load

cli.py imports all 68 command handlers at module level (lines 17-71).
8 handlers import `active_path_config()` at import time, freezing
VoiceTerm defaults before `set_active_path_config()` can be called.
No env-var or CLI mechanism to override before handler dispatch.

**Class**: portability. **Prevention**: lazy-load handlers or add
pre-dispatch config gate. **Owner**: MP-377 startup authority.

### HIGH: check_phases.py hardcodes `--bin voiceterm` and `rust/` dir

`run_test_build_phase()` line 255: `["cargo", "build", "--release",
"--bin", "voiceterm"]`. `resolve_src_dir()` maps REPO_ROOT → rust/.
External repos with different binary names or source layouts fail.

**Class**: portability. **Prevention**: policy field `repo.build_target_
binaries` and `repo.source_dirs`. **Owner**: MP-376 portable engine.

### HIGH: governance draft hardcodes AGENTS.md/MASTER_PLAN/INDEX.md

`draft_policy_scan.py` lines 40, 53, 59 use these as fallbacks when
policy is empty. `surface_context.py` lines 36, 39, 43 repeat the
pattern. Minimal repos without `dev/active/` get wrong defaults.

**Class**: portability. **Prevention**: fail-closed when policy keys
missing, or derive from `RepoPathConfig`. **Owner**: MP-376.

### HIGH: event_store.py hardcodes `DEFAULT_REVIEW_CHANNEL_PLAN_ID = "MP-355"`

Used in 6+ files across status_projection, prompt builder, packet
contract. Another repo has a different plan ID. Conductor prompt says
"VoiceTerm MP-355 markdown-bridge swarm" — wrong for any other repo.

**Class**: portability. **Prevention**: governance-driven plan ID
resolver from plan registry. **Owner**: MP-377.

### HIGH: FP classifier hardcodes VoiceTerm's 13 probe check_ids

`fp_classifier.py` lines 37-49: static regex table for
`probe_blank_line_frequency`, `probe_single_use_helpers`, etc.
Unknown check_ids on other repos get classified as UNKNOWN silently.

**Class**: portability. **Prevention**: load from check catalog at
runtime. **Owner**: MP-375 probe quality.

### HIGH: recommendation_engine thresholds calibrated for VoiceTerm

`recommendation_engine.py` hardcodes: FP rate > 30%, cleanup < 30%,
Halstead MI < 40. Small repos or large enterprise repos have different
baselines. Recommendations become noise, not actionable.

**Class**: portability. **Prevention**: parameterize as
`RecommendationThresholds` dataclass. **Owner**: MP-375.

### HIGH: release gates hardcode `--branch master`

`check.py` lines 89-90 and `bundle_registry.py` lines 183-184:
CodeRabbit gates assume `master` branch. Policy defines
`release_branch: "master"` but it's NOT consumed by these commands.

**Class**: portability. **Prevention**: template from
`push_policy.release_branch`. **Owner**: MP-376.

### MEDIUM: governance draft returns success with empty plan_registry

When no INDEX.md exists and no plan docs match `PLAN_DOC_CLASSES`,
`scan_repo_governance()` succeeds with 0 plan entries. Downstream
code may fail silently expecting at least one tracker.

**Class**: authority. **Prevention**: startup validation should warn
on empty plan_registry. **Owner**: MP-377.

### MEDIUM: Halstead only scans .py and .rs

`halstead.py` line 275: `extensions=(".py", ".rs")`. Go, Java,
TypeScript repos get zero coverage and misleadingly low scores.

**Class**: portability. **Prevention**: accept `--extensions` or
auto-detect from policy. **Owner**: MP-376.

### MEDIUM: SUB_SCORE_WEIGHTS assume 50% governance signals

`models.py` lines 31-39: guard_issue_burden (20%), finding_density
(15%), cleanup_rate (15%). Non-governed repos without ledger/probe
history score artificially low on 50% of the formula.

**Class**: portability. **Prevention**: normalize by available
dimensions only. **Owner**: MP-375.

### MEDIUM: REQUIRED_SECTIONS hardcoded to VoiceTerm 5-section format

`doc_authority_models.py` lines 27-33 requires: Scope, Execution
Checklist, Progress Log, Session Resume, Audit Evidence. Repos
with different plan doc format get false violations.

**Class**: portability. **Prevention**: policy-driven
`doc_authority.required_plan_sections`. **Owner**: MP-376.

### MEDIUM: post-push bundle hardcodes `origin/develop`

`bundle_registry.py` line 132: diff-aware checks scope to
`origin/develop`. Policy defines `development_branch` but bundle
doesn't use it.

**Class**: portability. **Prevention**: template from
`policy.development_branch`. **Owner**: MP-376.

### MEDIUM: startup gate commands are hardcoded, not policy-driven

`startup_gate.py` lines 15-23: `_GATED_COMMANDS` is a static set.
Portable repos may need different gate rules.

**Class**: authority. **Prevention**: move gate rules to governance
config. **Owner**: MP-377.

### MEDIUM: quality scope roots lock probes to VoiceTerm layout

`devctl_repo_policy.json` lines 483-497: python_probe_roots lock to
`[dev/scripts/devctl, app/operator_console]`. Portable presets should
define broader defaults.

**Class**: portability. **Prevention**: broader defaults in
`portable_python_rust.json`. **Owner**: MP-376.

## Pass 1 Summary

| Severity | Count | New vs Already Known |
|---|---|---|
| HIGH | 7 | 5 new (cli.py, check_phases, event_store, FP classifier, recommendation thresholds), 2 refinements (governance draft, release gates) |
| MEDIUM | 7 | 5 new (empty plan_registry, Halstead .py/.rs only, weights, REQUIRED_SECTIONS, post-push develop), 2 refinements (startup gate, quality scopes) |
| LOW | 0 | — |

Pass 2 will target subsystems not yet covered: tandem-consistency
internals, mobile/phone status, publication-sync, MCP adapter,
integrations layer, and docs-check policy defaults.

## Pass 2 Findings (4-Agent Sweep, 2026-03-26)

### MEDIUM: tandem-consistency hash excludes hardcode `.voiceterm/memory/`

`heartbeat.py` line 64 and `reviewer_checks.py` inherit:
`NON_AUDIT_HASH_EXCLUDED_PREFIXES` includes `.voiceterm/memory/` and
`rust/target/`. These are VoiceTerm-specific. Portable repos with
different memory roots or build dirs get wrong hash exclusions.

**Class**: portability. **Prevention**: extract exclusion prefixes to
governance `ArtifactExclusions` config. **Owner**: MP-358.

### HIGH: docs-check has 11 hardcoded paths blocking portability

`policy_defaults.py` embeds: `AGENTS.md`, `dev/guides/DEVELOPMENT.md`,
`dev/scripts/README.md`, `dev/active/MASTER_PLAN.md`, `dev/history/
ENGINEERING_EVOLUTION.md`, plus 5 evolution trigger paths and 6 user-
facing doc paths. Strict-tooling mode registers 9 guard scripts
unconditionally — no conditional gate based on repo structure.

Fallback chain in `policy_runtime.py` silently uses hardcoded defaults
when governance config is empty. A portable repo cannot signal "no
evolution doc" because the fallback is non-null.

**Class**: portability (CRITICAL for extraction). **Prevention**: registry-
based gate orchestration, fail-closed when config empty, support null
evolution_doc. **Owner**: MP-376.

### MEDIUM: MCP server name hardcoded to "voiceterm-devctl-mcp"

`mcp.py` line 18: `MCP_SERVER_NAME = "voiceterm-devctl-mcp"`. External
repos using the MCP adapter identify as VoiceTerm to clients.

**Class**: portability. **Prevention**: derive from
`ProjectGovernance.repo_identity.repo_name`. **Owner**: MP-376.

### MEDIUM: MCP tools assume VoiceTerm autonomy infrastructure

`mcp_tools.py` lines 99-135: `tool_status_snapshot` and
`tool_report_snapshot` call `build_project_report()` which depends on
VoiceTerm's CI/mutation/watchdog infrastructure. External repos without
this infrastructure get empty or broken snapshots.

**Class**: portability. **Prevention**: abstract status provider
interface; separate VoiceTerm-specific tools from portable core.
**Owner**: MP-376.

### Coverage: mobile/phone/publication-sync — NO NEW ISSUES

- `mobile-status`: no VoiceTerm hardcoding in code; graceful fallback
  when review state missing. PORTABLE.
- `phone-status`: pure JSON transformation; fully agnostic. PORTABLE.
- `publication-sync`: generic git + registry; code is portable.
  Registry data (`terminal-as-interface`) is repo-specific but that's
  expected — it's data, not code.
- All three commands work on repos without iOS/mobile components.

### MEDIUM: integrations federation default destination root is still VoiceTerm-shaped

`federation_policy.py` lines 11 and 69 fall back to
`DEFAULT_ALLOWED_DESTINATION_ROOTS = ["dev/integrations/imports"]` when repo
policy omits `allowed_destination_roots`. External repos without that layout
silently inherit VoiceTerm's import destination root.

**Class**: portability. **Prevention**: resolve integration destination roots
from repo-pack / repo-policy authority or fail closed when the integration
surface is enabled without an explicit destination contract.
**Owner**: MP-376.

### Coverage: integrations layer — PARTIAL (1 MEDIUM issue)

- `federation_policy.py`: policy-driven, parameterized. PORTABLE.
- `integrations-sync`: generic git submodule sync. PORTABLE.
- `integrations-import`: uses allowlisted destination roots. PORTABLE.
- `import_core.py`: generic path collection. PORTABLE.
### Coverage: tandem-consistency sub-checks — 4/7 PORTABLE

- `reviewer_freshness`: PORTABLE (no hardcodes)
- `implementer_ack_freshness`: PORTABLE
- `implementer_completion_stall`: PORTABLE
- `plan_alignment`: PARTIAL (fallback defaults are VoiceTerm)
- `promotion_state`: PORTABLE
- `launch_truth`: PORTABLE
- `reviewed_hash_honesty`: NOT PORTABLE (hardcoded exclusions)

## Pass 2 Summary

| Severity | Count | New vs Already Known |
|---|---|---|
| HIGH | 1 | docs-check 11 hardcoded paths (new subsystem) |
| MEDIUM | 4 | tandem hash exclusions (new), MCP server name (new), MCP tools autonomy coupling (new), integrations destination-root fallback (new) |
| Coverage notes | 4 subsystems | mobile/phone/publication-sync: no issues. integrations: 1 medium issue. tandem: 4/7 portable |

## Combined Pass 1+2 Totals

| Severity | Pass 1 | Pass 2 | Total |
|---|---|---|---|
| HIGH | 7 | 1 | 8 |
| MEDIUM | 7 | 4 | 11 |
| Coverage (no issues) | 0 | 3 subsystems | 3 |

Subsystems now covered: cli.py, governance draft, check orchestration,
push/release, review-channel events, quality-feedback, probe system,
plan doc coverage, tandem-consistency, mobile/phone, publication-sync,
MCP adapter, integrations, docs-check.

Subsystems remaining for Pass 3: process-sweep, failure-cleanup,
reports-retention, launcher commands, security guard, and any
remaining check_*.py guards not individually reviewed.

## Pass 3 Findings (2-Agent Sweep, 2026-03-26)

### HIGH: process_sweep hardcodes VoiceTerm binary regex patterns

`process_sweep/config.py` lines 28-45: `VOICETERM_TEST_BINARY_RE`,
`VOICETERM_CARGO_TEST_RE`, `VOICETERM_STRESS_SCREEN_RE` all match
"voiceterm" binary names. `scan_voiceterm_test_process_tree()` and
`match_voiceterm_rows()` only detect VoiceTerm processes.

**Class**: portability. **Prevention**: extract binary name patterns
to `RepoPathConfig.test_binary_name_patterns`. **Owner**: MP-376.

### HIGH: reports_retention hardcodes subroots and protected paths

`reports_retention.py` lines 16-32: `MANAGED_REPORT_SUBROOTS` and
`PROTECTED_REPORT_PATHS` hardcode autonomy/benchmarks, failures/,
data_science/ etc. External repos can't define custom retention
policies without modifying this code.

**Class**: portability. **Prevention**: add
`managed_report_subroots` and `protected_report_paths` to
`RepoPathConfig`. **Owner**: MP-376.

### MEDIUM: 7 check scripts hardcode VoiceTerm paths (not portability-critical)

These are legitimately VoiceTerm-specific guards that would be
skipped or disabled on external repos via quality-policy:

- `ide_provider_isolation_core.py`: 15+ voiceterm file allowlists
- `check_cli_flags_parity.py`: `rust/src/bin/voiceterm/config/cli.rs`
- `check_release_version_parity.py`: `pypi/src/voiceterm/__init__.py`
- `check_repo_url_parity.py`: `github.com/jguida941/voiceterm`
- `check_naming_consistency.py`: `rust/src/bin/voiceterm/runtime_compat.rs`
- `daemon_state_parity/command.py`: `rust/src/bin/voiceterm/daemon/types.rs`
- `mobile_relay_protocol/support.py`: same daemon types path

These are correctly classified as repo-specific guards (not portable
engine). Quality-policy presets would exclude them for external repos.
No portability fix needed — they are VoiceTerm product guards.

### Coverage: launcher/security/cihub — NO NEW ISSUES

- `launcher-check`, `launcher-probes`, `launcher-policy`: policy-driven
- `security.py`: clean, no VoiceTerm hardcodes
- `cihub-setup.py`: clean
- Security tier definitions: portable

### Coverage: failure-cleanup — NO NEW HIGH/MEDIUM

`failure_cleanup.py` uses policy-relative paths (PORTABLE). One doc
gap: needs docstring explaining portability override mechanism.

## Pass 3 Summary

| Severity | Count | Details |
|---|---|---|
| HIGH | 2 | process_sweep binary patterns, reports_retention subroots |
| MEDIUM | 1 | 7 check scripts with VoiceTerm paths (legitimate, not engine) |
| Coverage | 3 subsystems | launcher/security/cihub: no issues. failure-cleanup: portable. |

## Combined Pass 1+2+3 Totals

| Severity | P1 | P2 | P3 | Total |
|---|---|---|---|---|
| HIGH | 7 | 1 | 2 | **10** |
| MEDIUM | 7 | 4 | 1 | **12** |
| Coverage (no issues) | 0 | 3 | 3 | **6 subsystems clean** |

**All Python control-plane subsystems now have at least one audit pass.**

Pass 3 added 2 HIGH + 1 MEDIUM. This is diminishing — Pass 1 had 14,
Pass 2 had 4, Pass 3 has 3. One more pass should confirm convergence
(target: zero new HIGH/MEDIUM to meet closure criteria).

## Shared Review Loop

This file is the shared architecture audit ledger for Claude and Codex.
It is not a second execution authority; `MASTER_PLAN` and the scoped plan
docs remain the owner surfaces for implementation.

For each audit pass:

1. Claude appends one bounded subsystem pass with only net-new HIGH/MEDIUM
   findings, refinements, or explicit "no new issues" coverage notes.
2. Codex reviews that delta against code and plan state, verifies evidence,
   resolves contradictions, and maps owner plans.
3. If a finding is unmapped, Codex promotes it into `MASTER_PLAN` plus the
   owning scoped plan in the same review loop.
4. Fixed findings should link back to code/test/guard/docs proof rather than
   disappearing from the ledger.

## Closure Criteria

This audit is aligned enough to merge into normal execution only when all of
the following are true:

- Every HIGH/MEDIUM finding is either mapped to an owner plan or explicitly
  waived with reason.
- Fixed rows link to proof in code, tests, guards, docs, or receipts.
- Every Python control-plane subsystem has at least one explicit audit pass or
  an explicit "covered, no new issues" note.
- Two consecutive bounded passes add no new HIGH/MEDIUM findings.
- Any plan/doc ownership conflicts found here are resolved back into
  `MASTER_PLAN` and the owning scoped plans, not left only in this file.

## Codex Owner-Mapping Update (2026-03-26)

- `MP-361` now explicitly owns Ralph architecture-validation command
  parameterization so `ralph_ai_fix.py` can stop hardcoding VoiceTerm build
  targets and repo-local test roots.
- `MP-376` now explicitly owns the Pass 1 portable-engine policy cluster:
  governance-draft fallbacks, build/source/branch literals, required-plan
  sections, quality-scope roots, and language coverage plus non-probe metric
  portability.
- `MP-375` now explicitly owns portable false-positive classification and
  recommendation/scoring calibration instead of leaving those as VoiceTerm-era
  constants.
- `MP-377` now explicitly owns removal of hardcoded review-plan ids and the
  fail-closed treatment of empty `plan_registry` startup authority.
- `MP-376` now explicitly owns the later-pass portable subsystem cluster too:
  fail-closed docs-check defaults, portable MCP identity/coupling,
  `process_sweep` binary-pattern generalization, and repo-pack-defined report
  retention policy, plus integration-federation destination roots that still
  fall back to `dev/integrations/imports`.
- `MP-377` now explicitly owns portable tandem hash/exclusion policy and the
  remaining non-review import-time repo-pack path freezes such as
  `publication_sync/core.py`.

## Pass 2 Findings (Codex Local Review, 2026-03-26)

### MEDIUM: tandem-consistency operator fallback still injects VoiceTerm plan paths

`operator_checks.py` lines 47-48 still fall back to
`dev/active/MASTER_PLAN.md` and `dev/active/review_channel.md` when the
governed tracker/scoped-plan pair is not injected. That means the
operator-side `Plan Alignment` check can still validate against the wrong
plan chain on a repo whose active tracker or review plan lives elsewhere.

**Class**: portability/authority. **Prevention**: fail closed or require
governed path injection instead of a VoiceTerm fallback. **Owner**: MP-377.

### MEDIUM: docs-check default policy still assumes VoiceTerm maintainer docs

`commands/docs/policy_defaults.py` still defaults `USER_DOCS`,
`TOOLING_REQUIRED_DOCS`, and evolution/deprecated-reference targets to
VoiceTerm's canonical doc set (`README.md`, `AGENTS.md`,
`dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`,
`dev/active/MASTER_PLAN.md`, etc.). `policy_runtime.py` is governance-aware,
but when a repo omits or partially defines `docs_check` policy, the fallback
still judges tooling/doc changes against VoiceTerm's doc surface.

**Class**: portability. **Prevention**: require repo policy for docs-governance
or derive defaults from governed doc registry instead of static VoiceTerm
lists. **Owner**: MP-376.

### MEDIUM: publication-sync still freezes repo-pack registry path at import time

`publication_sync/core.py` defines
`DEFAULT_PUBLICATION_SYNC_REGISTRY_REL = active_path_config().publication_sync_registry_rel`
at module load. That keeps publication-sync on the same hidden
VoiceTerm-default path freeze pattern already flagged in the broader
authority-loop audit, just in another subsystem.

**Class**: portability. **Prevention**: resolve registry paths at call time or
inject repo-pack state explicitly. **Owner**: MP-377.

### Coverage Note: no new repo-path issues in mobile/phone status projections

Reviewed `phone_status_projection.py`, `mobile_status_projection.py`,
`phone_status_views.py`, and `mobile_status_views.py` for direct repo-path
authority literals on this pass. No new HIGH/MEDIUM portability issues found;
the current projection surfaces are mostly typed view models rather than path
resolution/control-path owners.

## Pass 4: Convergence Confirmation (Claude, 2-Agent Sweep)

**Pass 4: zero new HIGH/MEDIUM findings. Convergence is close, but not
formally closed yet.**

Both agents swept all 589 Python files in `dev/scripts/devctl/` plus
all `dev/scripts/checks/` for remaining portability issues:

- Zero new `voiceterm` hardcodes in portable code (77 files checked)
- Zero `jguida941` references outside test fixtures
- All `bridge.md` references properly governed through ProjectGovernance
- All `dev/active/` accesses guarded with `.exists()` checks
- No frozen repo_packs imports beyond what Pass 1 documented
- All probe files clean of VoiceTerm hardcoding

## Audit Convergence

| Pass | Agent | New HIGH | New MEDIUM |
|---|---|---|---|
| Pass 1 | Claude (8 agents) | 7 | 7 |
| Pass 2 | Claude (4 agents) | 1 | 3 |
| Pass 3 | Claude (2 agents) | 2 | 1 |
| Pass 3 review | Codex | 0 | 3 (refinements of existing) |
| **Pass 4** | **Claude (2 agents)** | **0** | **0** |
| **Pass 5** | **Claude (4 agents)** | **0** | **0** |

Pass 4 was the first zero-new bounded pass. Pass 5 is the second consecutive
zero-new bounded pass, satisfying the closure rule.

## Pass 5: Bounded Architecture/Docs/Plan Confirmation (Claude, 4-Agent Sweep)

**Pass 5: zero new HIGH/MEDIUM findings. Second consecutive zero-new bounded
pass. Closure criteria for discovery saturation is now met.**

### Method

4 parallel agents swept the full 14-file required read set specified by the
reviewer instruction (revision `2d366ef7587b`):

- **Agent 1**: `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`
- **Agent 2**: `dev/active/platform_authority_loop.md`, `dev/active/portable_code_governance.md`, `dev/active/review_probes.md`
- **Agent 3**: `dev/active/review_channel.md`, `dev/active/continuous_swarm.md`, `dev/active/ai_governance_platform.md`
- **Agent 4**: `dev/guides/ARCHITECTURE.md`, `dev/guides/AI_GOVERNANCE_PLATFORM.md`, `dev/guides/DEVCTL_ARCHITECTURE.md`, `dev/guides/DEVELOPMENT.md`

Each agent checked 5 boundary assertions:
- A: VoiceTerm treated as CLIENT, not platform itself
- B: Portable authority from governed repo-pack state, not hardcoded paths
- C: MCP described as additive/read-only
- D: Tandem/review infra described as opt-in
- E: Fixed audit findings absorbed into canonical plans/docs

### Boundary Assertion Results

| Assertion | Status | Summary |
|---|---|---|
| A: VoiceTerm as client | CLEAN | Explicit in AGENTS.md:17, MASTER_PLAN.md:44, AI_GOVERNANCE_PLATFORM.md:66 |
| B: Portable authority | ALIGNED (target correct, implementation tracked) | Guides correctly specify governance-driven resolution; ~460 hardcodes are tracked implementation debt in MP-376/MP-377, not guide contradictions |
| C: MCP additive/read-only | CLEAN | Explicit in AGENTS.md:1466, ARCHITECTURE.md:275-293, review_channel.md:98-100 |
| D: Tandem opt-in | CLEAN | DEVELOPMENT.md:144-155 documents 3 peer modes; continuous_swarm mandatory language applies within opt-in active_dual_agent scope |
| E: Findings absorbed | CLEAN | All 10 HIGH + 11 MEDIUM mapped to owner plans via Codex mapping update; plan docs track them in correct scoped phases |

### Items Examined and Classified as NOT New

Agents flagged several items that were classified as re-discoveries or
plan-scheduling observations, not new architectural violations:

1. **Governance parser defaults / conductor prompt hardcodes**: Already in
   ledger as Issues 2 and 3 (lines 36-64). Agent 1 noted they aren't
   prominent in MASTER_PLAN blocking scope, but the Codex Owner-Mapping
   Update (lines 622-641) already maps them to MP-376/MP-377.

2. **MCP identity contract / docs-check defaults not phase-scheduled**:
   Already in Pass 2 findings (lines 444-450, 428-442). Agent 2 noted they
   lack explicit phase checklist items in portable_code_governance.md, but
   the progress log (line 442-447) tracks them as promoted work.

3. **Plan docs referencing their own plan IDs (MP-377, MP-358)**: Plan
   prose is inherently repo-specific. The portability boundary applies to
   code (runtime, guards, probes), not to plan document cross-references.

4. **continuous_swarm mandatory vs optional language**: The "must keep going"
   locked decision describes behavior within active_dual_agent mode, which
   is itself opt-in. Not a boundary violation.

5. **Guides don't mention ~80% portability gap**: Guides describe target
   architecture (correct); the audit ledger tracks the implementation gap.
   This is the intended division of labor, not a contradiction.

### Explicit Coverage Notes (Clean Sections)

- **MCP contract** across all 14 files: consistently additive, read-only,
  no enforcement authority claimed. Strongest boundary in the docs.
- **VoiceTerm client framing**: explicit in AGENTS.md, MASTER_PLAN.md,
  AI_GOVERNANCE_PLATFORM.md, and DEVCTL_ARCHITECTURE.md; the remaining
  review-channel/README compatibility wording drift is corrected in the
  Codex review notes below rather than left as an unresolved contradiction.
- **Tandem opt-in**: DEVELOPMENT.md 3-mode documentation (active_dual_agent,
  single_agent, tools_only) treats all as peer options. Operator Console
  explicitly marked optional and non-canonical.
- **ProjectGovernance authority pattern**: correctly specified as target in
  DEVELOPMENT.md:276-281, AI_GOVERNANCE_PLATFORM.md:152-159.
- **4-layer enforcement stack**: Layers 1-2 (governance resolution,
  governance-rendered instructions) explicit in guides. Layers 3-4
  (portability-drift guard, fixture-repo proof) correctly tracked in
  implementation plans (MP-376/MP-377), not architecture guides.
- **Owner mapping**: all HIGH/MEDIUM findings are mapped after the Codex
  review correction below clarified that probe-quality classification,
  recommendation thresholds, and composite scoring belong to `MP-375`, while
  `MP-376` keeps language coverage and non-probe metric portability.

### Doc Completeness Suggestions (Informational, Not Violations)

These are optional improvements, not boundary violations:

1. AI_GOVERNANCE_PLATFORM.md could add one sentence after ~line 106
   acknowledging current ~80% portability state and MP-376/MP-377 tracking.
2. ARCHITECTURE.md MCP section (lines 275-293) could note that MCP server
   name is currently VoiceTerm-specific and will be parameterized (MP-376).

## Pass 5 Review Corrections (Codex, 2026-03-26)

### MEDIUM: review-channel plan still taught the compatibility bridge as live authority

`review_channel.md` correctly says structured state is canonical and markdown
is only a projection, but the transitional bridge protocol still told Claude
to treat repo-root `bridge.md` as the live reviewer/coder authority. That
wording re-taught the compatibility bridge as effective backend truth instead
of a repo-owned coordination projection over typed `review_state`.

**Class**: docs/authority portability. **Prevention**: keep review-channel
runbook wording explicit that `bridge.md` is a compatibility coordination
surface while typed `review_state` remains canonical machine authority.
**Owner**: MP-355 / MP-377. **Status**: fixed in this pass via
`dev/active/review_channel.md`.

### MEDIUM: command docs still described fixed VoiceTerm review paths as the contract

`dev/scripts/README.md` described `review-channel` and `mobile-status` in
terms of fixed VoiceTerm paths (`dev/active/review_channel.md`, `bridge.md`,
`dev/reports/review_channel/latest/`) instead of governed review-channel
roots resolved through `ProjectGovernance` / repo-pack state. That taught
repo-local layout as if it were the universal backend contract.

**Class**: docs/portability. **Prevention**: document governed review roots
first and treat VoiceTerm paths as current-repo examples only.
**Owner**: MP-377 documentation-consolidation. **Status**: fixed in this pass
via `dev/scripts/README.md`.

### HIGH: startup/push contract taught clean worktree as push readiness

The runtime contract used `push_ready` for what was only raw git cleanliness:
`detect_push_enforcement_state()` set it to `not worktree_dirty`, and
`startup-context` then treated that field plus reviewer acceptance as
push-allowed. That wording taught "clean tree" as if it were the same thing
as actual push eligibility, even though the governed push path checks
additional policy/VCS conditions.

**Class**: runtime/contract teaching. **Prevention**: keep raw git posture,
review-gate allowance, and final push eligibility as separate named concepts.
**Owner**: MP-377 authority-loop / governed push path. **Status**: partially
fixed in this pass via `worktree_clean`, `review_gate_allows_push`, and
`await_review`; remaining follow-up is the deeper contract split between
continuation-budget state and branch-push mechanics.

### MEDIUM: governed push cleanliness still treated advisory scratch as authored drift

The reviewer/hash side already treats `convo.md` as advisory scratch context,
but the governed push gate still counted that untracked file as dirty state.
That stranded reviewed commits outside the canonical `devctl push` lane even
after the code slice was green and checkpointed.

**Class**: runtime/policy boundary mismatch. **Prevention**: let repo policy
declare advisory scratch/reference paths separately from compatibility
projections, and use that same exclusion list when computing push/checkpoint
cleanliness and in the live `devctl push` blocking path. **Owner**: MP-377
authority-loop / governed push path. **Status**: fixed in this pass via
repo-policy `advisory_context_paths` plus push-state, `devctl push`,
runtime/tests/docs updates.

### MEDIUM: maintainer docs still collapsed commit and push into one step

`AGENTS.md`, the `DEVELOPMENT.md` lifecycle chart, and the Ralph plan/tracker
still described "commit and push" as one atomic step. That taught future AI
sessions to treat a checkpointed green slice as automatically push-ready
instead of requiring a current review gate plus governed `devctl push`
validation.

**Class**: docs/process teaching. **Prevention**: teach commit/checkpoint as
the local bounded-slice action and push as a later governed remote action.
**Owner**: MP-377 documentation-consolidation plus MP-360/361 Ralph lane.
**Status**: fixed in this pass via `AGENTS.md`, `dev/guides/DEVELOPMENT.md`,
`dev/active/ralph_guardrail_control_plane.md`, and `dev/active/MASTER_PLAN.md`.

### Owner-Mapping Correction

The shared ledger had one remaining owner split wrong even after the first
Codex mapping update: `recommendation_engine` thresholds and
`SUB_SCORE_WEIGHTS` still pointed at `MP-376` in two Pass 1 rows even though
the scoped plans already moved false-positive classification, recommendation
thresholds, and composite/evidence scoring to `MP-375`. This pass corrects
the ledger so `MP-375` is the primary owner for probe-quality calibration,
while `MP-376` keeps language coverage and non-probe metric portability such
as Halstead extension coverage.

## Audit Convergence

| Pass | Agent | New HIGH | New MEDIUM |
|---|---|---|---|
| Pass 1 | Claude (8 agents) | 7 | 7 |
| Pass 2 | Claude (4 agents) | 1 | 3 |
| Pass 3 | Claude (2 agents) | 2 | 1 |
| Pass 3 review | Codex | 0 | 3 (refinements of existing) |
| Pass 4 | Claude (2 agents) | 0 | 0 |
| Pass 5 | Claude (4 agents) | 0 | 0 |
| **Pass 5 review** | **Codex** | **1** | **3** |
| **Pass 6** | **Claude (2 agents)** | **0** | **0** |
| **Pass 6 review** | **Codex** | **0** | **0** |

Pass 6 is the first zero-new bounded pass after the Codex Pass 5 review
corrections. The Codex review of Pass 6 found only ledger-mapping/proof
corrections, not new HIGH/MEDIUM issues, so the two-consecutive zero-new
closure criterion is now met for discovery saturation.

## Pass 6: Closure Control (Claude, 2-Agent Verification)

**Pass 6: zero new HIGH/MEDIUM findings. Closure control pass — owner
mapping verified, proof links added for fixed rows, mapping gaps noted.**

### Method

2 parallel agents verified canonical owner mapping for all 10 HIGH + 11
MEDIUM findings against MASTER_PLAN and scoped plan docs (platform_authority
_loop.md, portable_code_governance.md, review_probes.md). Also verified the
4 Codex Pass 5 review findings.

### HIGH Findings: Owner Mapping (10 of 10 MAPPED)

All 10 HIGH findings have explicit canonical ownership in MASTER_PLAN via
the Codex Owner-Mapping Update (lines 622-642). No contradictions or
duplicate ownership.

| # | Finding | Owner | MASTER_PLAN Lines |
|---|---------|-------|-------------------|
| 1 | cli.py handler imports freeze paths | MP-377 | 634-635 |
| 2 | check_phases.py hardcodes --bin voiceterm | MP-376 | 627-630 |
| 3 | governance draft hardcodes AGENTS.md/MASTER_PLAN | MP-376 | 627-630 |
| 4 | event_store.py hardcodes MP-355 plan ID | MP-377 | 634-635 |
| 5 | FP classifier hardcodes 13 probe check_ids | MP-375 | 631-633 |
| 6 | recommendation_engine thresholds | MP-375 | 631-633, 871-877 |
| 7 | release gates hardcode --branch master | MP-376 | 627-630 |
| 8 | docs-check 11 hardcoded paths | MP-376 | 636-639 |
| 9 | process_sweep binary patterns | MP-376 | 636-639 |
| 10 | reports_retention subroots | MP-376 | 636-639 |

### Pass 5 Review Findings: Proof Links (4 of 4 MAPPED)

| Finding | Owner | Proof |
|---------|-------|-------|
| startup/push contract teaching (HIGH) | MP-377 | `bd347a9`; `dev/scripts/devctl/runtime/startup_push_decision.py:13-83`, `dev/scripts/devctl/runtime/startup_context.py:52-70`, `dev/scripts/devctl/commands/governance/startup_context.py:61-73`, `dev/scripts/devctl/tests/runtime/test_startup_context.py:511-535`, `dev/scripts/devctl/tests/runtime/test_startup_receipt.py:64-75`, `AGENTS.md:771-772`, `dev/guides/DEVELOPMENT.md:66-68`, `dev/scripts/README.md:272-277` |
| review-channel bridge authority (MEDIUM) | MP-355/377 | `dev/active/review_channel.md:96-100` |
| command docs VoiceTerm paths (MEDIUM) | MP-377 | `dev/scripts/README.md:984-985` |
| maintainer docs commit/push collapse (MEDIUM) | MP-377+360/361 | `AGENTS.md:771-772`, `dev/guides/DEVELOPMENT.md:66-68`, `dev/active/MASTER_PLAN.md:304-313`, `dev/active/ralph_guardrail_control_plane.md:16-17`, `dev/active/ralph_guardrail_control_plane.md:75-77`, `dev/active/ralph_guardrail_control_plane.md:168-172` |

### MEDIUM Findings: Owner Mapping (11 items)

| # | Finding | Owner | Mapping |
|---|---------|-------|---------|
| 1 | governance draft empty plan_registry | MP-377 | PROSE-ONLY (platform_authority_loop.md:645) |
| 2 | Halstead .py/.rs only | MP-376 | PROSE-ONLY (portable_code_governance.md:144,517) |
| 3 | SUB_SCORE_WEIGHTS 50% governance | MP-375 | CHECKLIST (`review_probes.md:449-453`) plus engine-side portability cross-link (`portable_code_governance.md:333-336`) |
| 4 | REQUIRED_SECTIONS hardcoded | MP-376 | PROSE-ONLY (portable_code_governance.md:334) |
| 5 | post-push bundle origin/develop | MP-376 | PROSE-ONLY (portable_code_governance.md:451) |
| 6 | startup gate commands hardcoded | MP-377 | PROSE-ONLY (implicit in progress notes) |
| 7 | quality scope roots VoiceTerm layout | MP-376 | PROSE-ONLY (portable_code_governance.md:334) |
| 8 | tandem-consistency hash excludes | MP-377 | PROSE-ONLY (`dev/active/platform_authority_loop.md:593-598`) |
| 9 | MCP server name hardcoded | MP-376 | PROSE-ONLY (portable_code_governance.md:340) |
| 10 | MCP tools VoiceTerm autonomy coupling | MP-376 | PROSE-ONLY (portable_code_governance.md:340) |
| 11 | Codex Pass 2: tandem/docs-check/pub-sync | MP-377/376 | MAPPED (portable_code_governance.md:337-345) |

MEDIUM findings #1-10 were promoted as a batch ("absorb Pass 1/2/3
portability cluster") and appear in progress logs. Most are not tracked as
discrete checklist items — acceptable for owner mapping, but individual
proof-linking will need per-item verification when fixes land.

### Codex Review Corrections (2026-03-26)

- The `SUB_SCORE_WEIGHTS` row was a false gap. `dev/active/review_probes.md`
  already owns portable recommendation-threshold and score-normalization work
  in both the active checklist (`dev/active/review_probes.md:449-453`) and
  `## Session Resume` (`dev/active/review_probes.md:1456-1459`), while
  `dev/active/portable_code_governance.md:333-336` keeps the engine-side
  portability cross-link.
- The tandem-consistency hash-exclusion row stays under `MP-377`, not
  `MP-358`: the Codex owner-mapping update already promoted portable tandem
  hash/exclusion policy into the authority-loop lane, and the active scoped
  checklist is `dev/active/platform_authority_loop.md:593-598`.
- No new contradictions, unmapped findings, or boundary violations were
  discovered in this Codex review. This pass only corrected ledger truth and
  proof quality.

**Closure criteria status (updated):**
- [x] All HIGH/MEDIUM findings mapped to owner plans
- [x] Fixed rows link to proof (the currently fixed Pass 5 review rows now cite code/docs/tests/commit evidence)
- [ ] Whole-system coverage re-verified under the restored Claude-primary broad audit loop
- [ ] Two consecutive Claude+Codex broad passes produce no new HIGH/MEDIUM findings
- [x] Plan ownership conflicts resolved by Codex mapping update + Pass 6 verification

## Pass 7: Focused 4-Area Verification (Claude, 2-Agent, bounded)

**Pass 7 covered only four previously named areas from the then-current Codex
instruction. It is a bounded verification pass, not a whole-platform "zero
new issues" claim.**

### 1. Startup Gate Command Hardcodes

**Status**: PROSE-ONLY, code still hardcoded, already tracked.

`startup_gate.py` lines 15-23: `_GATED_COMMANDS` is still a static set of 7
commands. Not yet moved to governance config. MP-377 owns this per the audit
ledger (Pass 1, line 387-393). The scoped plan (platform_authority_loop.md)
references startup authority broadly but has no discrete checklist item for
this specific parameterization.

**Conclusion**: Already tracked, owner correct (MP-377), no new finding.

### 2. Integration Federation Destination Root Defaults

**Status**: PROSE-ONLY, code still hardcoded, already tracked.

`federation_policy.py` line 11: `DEFAULT_ALLOWED_DESTINATION_ROOTS =
["dev/integrations/imports"]` still hardcoded. MP-376 owns this per the
audit Pass 2 coverage notes (line 479-480). Tracked in
portable_code_governance.md:442-450 as promoted work but no MASTER_PLAN
checklist item.

**Conclusion**: Already tracked, owner correct (MP-376), no new finding.

### 3. MP-376 vs MP-377 Authority Boundary

**Status**: CLEAR, no contradictions.

The boundary is fully explicit in the Codex Owner-Mapping Update (audit
lines 631-651) and MASTER_PLAN.md:
- MP-376 = portable engine code (guards, probes, evidence contracts)
- MP-377 = startup authority, session state, repo-pack activation, platform
  extraction
- No remaining overlap or ambiguity detected.

**Conclusion**: No new finding.

### 4. Review-Channel Delegation of current_session / checkpoint / push

**Status**: Delegation is correct in code but implicit in plan docs.

- `current_session`: MP-355 implements `ReviewCurrentSessionState` in
  `review_state_models.py`. MP-377 consumes it for continuation/push
  decisions via `startup_push_decision.py`. The delegation is correct but
  not documented in review_channel.md Cross-Plan Dependencies (lines
  139-190), which lists 13 items but zero mention of push_enforcement,
  checkpoint_required, or current_session handoff to MP-377.

- `checkpoint semantics`: MP-377 owns authority (platform_authority_loop.md
  :271-278). MP-355 implements the checkpoint action (review_channel.md
  :1632). Cross-plan delegation is undocumented.

- `push authority`: MP-377 owns push eligibility decision (via
  `startup_push_decision.py`). MP-355's role in push UI/reporting is
  undefined in plan docs.

**Conclusion**: This is a plan-doc completeness gap (cross-plan dependency
documentation), not a new architecture violation. The code is correct and
the authority chain works. The missing cross-plan entries are a doc
improvement item, not a HIGH/MEDIUM finding. Recommend adding entries 14-15
to review_channel.md Cross-Plan Dependencies covering push_enforcement and
current_session delegation to MP-377.

### Pass 7 Summary

| Area | Status | New Finding? |
|------|--------|-------------|
| Startup gate commands | PROSE-ONLY, already tracked | No |
| Federation destination roots | PROSE-ONLY, already tracked | No |
| MP-376/377 boundary | CLEAR | No |
| Review-channel delegation | Implicit in docs, correct in code | No (doc improvement only) |

No new HIGH/MEDIUM findings were added within these four named areas. This
bounded result does not close broad discovery for the whole platform.

### Codex Re-open Correction (2026-03-26, broad-loop restore)

- Pass 7 remains valid only as a four-area bounded verification pass. It does
  not prove whole-platform completion, whole-platform "no new issues", or
  architecture-review closure.
- The live audit loop is now explicit: Claude performs the broad whole-system
  review across the full AI governance platform and connected Python control-
  plane surfaces; Codex verifies Claude deltas against the actual code/docs
  and only then promotes verified findings into owner plans.
- Until the reopened whole-system loop re-verifies coverage, do not use the
  earlier bounded-pass results as proof that broad discovery is saturated or
  that medium/high findings are exhausted platform-wide.

## Pass 8: Broad Whole-System Re-Walk (Claude broad pass)

**Pass 8: 1 new HIGH, 3 new MEDIUM findings. Broad re-walk across 14
subsystems with no closure assumptions. Prior closure framing withdrawn
per reviewer instruction f0a63acd1f9f.**

### Subsystem Coverage

Claude reported code coverage across 14 subsystems. Codex verified the new
HIGH/MEDIUM findings below against the cited code paths before promoting them
into owner plans.

| Agent | Subsystems Covered | Files Read |
|-------|-------------------|------------|
| 1 | governance bootstrap, startup authority, push | project_governance_parse.py, push_policy.py, push_routing.py, push_state.py, startup_context.py, startup_gate.py, startup_receipt.py, startup_push_decision.py, push.py |
| 2 | review-channel, autonomy, Ralph | core.py, event_store.py, prompt.py, handoff.py, status_projection.py, report_helpers.py, run_parser.py, benchmark_parser.py, ralph_ai_fix.py |
| 3 | guards, probes, docs-governance, reporting | check_phases.py, code_shape_policy.py, check_repo_url_parity.py, fp_classifier.py, recommendation_engine.py, policy_defaults.py, policy_runtime.py, halstead.py, metrics.py, quality_policy.py, quality_policy_scopes.py |
| 4 | integrations, MCP, process-sweep, plan-wiring, reports-retention | federation_policy.py, mcp.py, mcp_tools.py, config.py (process_sweep), matching.py, work_intake_routing.py, work_intake_models.py, reports_retention.py |

### NEW Findings (Not Previously in Ledger)

#### NEW HIGH: Silent bridge parse failures not elevated to startup receipt

`startup_context.py` lines 212-218: When bridge.md parsing fails
(OSError/ImportError/ValueError), the code returns a valid
`ReviewerGateState` with `bridge_parse_error` but this is not elevated to
the startup receipt. Operators see a blocked state but don't see that
governance was unrecoverable.

**Class**: authority. **Why**: Corrupted bridge silently blocks all work
without surfacing as a startup-authority failure. Operators may not realize
the repo is degraded. **Owner**: MP-377.

#### NEW MEDIUM: Incomplete exception handling in startup_context.py

`startup_context.py` line 261: `_resolve_bridge_path()` catches only
`ImportError` when calling `scan_repo_governance()`. If governance fails
with `OSError` or `ValueError`, the exception propagates uncaught.
`startup_receipt.py:257-265` correctly catches `(OSError, ValueError)`.
Inconsistent error handling between sibling modules.

**Class**: correctness. **Why**: Unpredictable failure behavior depending
on which startup module is called. **Owner**: MP-377.

#### NEW MEDIUM: Docs-check empty config returns VoiceTerm defaults without warning

`policy_runtime.py` lines 131-180: When `resolve_docs_check_policy()` is
called with no policy section, it returns VoiceTerm defaults (6 user docs,
4 tooling docs, non-null evolution_doc) without logging a warning. External
repos with empty governance get VoiceTerm doc requirements silently applied.
The failure mode is false violations ("AGENTS.md missing") on repos that
don't use this doc structure.

**Class**: authority. **Why**: Silent assumption of repo structure on empty
config. **Owner**: MP-376.

#### NEW MEDIUM: Language capability detection limited to Python+Rust

`quality_policy.py` lines 78-104: `detect_repo_capabilities()` only checks
for `Cargo.toml` (Rust) and `pyproject.toml`/`setup.py` (Python). Go,
TypeScript, Java repos report `capabilities: {python: false, rust: false}`,
disabling all language-dependent probes without warning. The system silently
skips quality gates instead of indicating unsupported languages.

**Class**: portability. **Why**: Polyglot repos get zero probe coverage
without indication. **Owner**: MP-376.

### Confirmed Existing Findings (Already in Ledger)

All 4 agents re-verified the following already-documented issues by reading
actual code. Evidence confirmed accurate at the reported line ranges:

| Finding | Ledger Lines | Confirmed? |
|---------|-------------|-----------|
| Import-time path freezing (36 files, 13+ modules) | 20-34, 216-229 | YES |
| Governance parser fallback defaults (bridge.md, review_channel) | 36-50 | YES |
| Conductor prompt hardcodes VoiceTerm + MP-355 | 52-64, 307-314 | YES |
| 460+ hardcoded VoiceTerm references | 66-79 | YES |
| check_phases.py --bin voiceterm | 289-296 | YES |
| FP classifier 13 hardcoded check_ids | 316-323 | YES |
| recommendation_engine calibration thresholds | 325-332 | YES |
| release gates --branch master | 334-341 | YES |
| docs-check 11 hardcoded paths | 428-442 | YES |
| MCP server name voiceterm-devctl-mcp | 444-450 | YES |
| MCP tools autonomy coupling | 452-461 | YES |
| process_sweep binary patterns | 519-527 | YES |
| reports_retention hardcoded subroots | 529-538 | YES |
| Halstead .py/.rs only | 352-358 | YES |
| SUB_SCORE_WEIGHTS 50% governance | 360-367 | YES |
| startup gate commands hardcoded | 387-393 | YES |
| quality scope roots | 395-402 | YES |
| Ralph binary name + arch mapping | 81-91 | YES |
| federation destination roots | 479-480 | YES |
| autonomy argparse frozen defaults | 224-225 | YES |

### Additional LOW Findings (Not Blocking)

- FP classifier test-path bias: `fp_classifier.py:76-80` assumes all test-
  file findings are threshold noise. Enterprise repos may have legitimate
  test quality issues. Owner: MP-375.
- Halstead MI formula uses academic calibration constants: `halstead.py:200`.
  Modern microservices have different complexity distributions. Owner: MP-375.
- code_shape_policy.py language extensions limited to .py/.rs: `lines 34-49`.
  Same pattern as Halstead. Owner: MP-376.
- Autonomy plan scope MP-338 hardcoded: `run_parser.py:28`, `benchmark_
  parser.py:30`. Partially tracked under import-time freezing category.

### Pass 8 Scope Notes

- Claude's pass covered the listed subsystems broadly enough to re-open
  whole-platform review instead of preserving the earlier bounded-closure
  framing.
- Codex verified the four new HIGH/MEDIUM findings above directly in
  `startup_context.py`, `startup_receipt.py`, `policy_runtime.py`, and
  `quality_policy.py`.
- The percentage-style portability scoring from the raw pass is withdrawn for
  now. This ledger does not yet have a governed scoring rubric that makes
  claims such as "98% portable" auditable enough to treat as authority.
- Work-intake / plan-wiring remains a relatively clean slice in this pass, but
  only the scoped claim "no new MEDIUM/HIGH found in the reviewed files" is
  accepted here.

### Pass 8 Summary

| Category | Count |
|----------|-------|
| NEW HIGH | 1 (bridge parse not elevated) |
| NEW MEDIUM | 3 (exception handling, empty docs config, language detection) |
| Confirmed existing | 20+ findings re-verified with code evidence |
| LOW additions | 4 (non-blocking) |
| Subsystems covered | 14 of 14 |
| Clean-scoped note | Work-intake / plan-wiring produced no new MEDIUM/HIGH in this pass |

## Pass 9: Codex Verification Corrections And Self-Hosting Tightening

**Pass 9: 1 new HIGH portability finding, 2 previously mapped fixes verified on
the current tree, and 1 self-hosting organization correction promoted into the
owner plans.**

### NEW HIGH: Portable authority still defaults to VoiceTerm doc/tracker names

`project_governance_contract.py:37-43,63-69,117-120,154-156`,
`project_governance_doc_parse.py:33-49,91-100`, and
`project_governance_plan_parse.py:39-50` still seed `AGENTS.md`,
`dev/active/INDEX.md`, and `dev/active/MASTER_PLAN.md` when portable
governance payloads are partial. The typed runtime therefore supports custom
names only after configuration is already correct; it does not yet fail closed
or prove custom-layout repos by default.

**Class**: authority/portability. **Why**: another repo can appear governed
while still resolving startup/doc authority through VoiceTerm defaults.
**Owner**: `MP-377` runtime/doc-authority contract, with fixture-proof follow-up
in `MP-376`.

### Verified Fixes In Current Tree

- `sync --push` no longer bypasses the governed push path with raw `git push`.
  The current implementation routes through the same startup/review gate,
  preflight, push action, and post-push flow as `devctl push`.
- Typed governance/runtime parsing no longer invents `review_root`,
  `bridge_path`, or `review_channel_path` from sparse governance payloads, and
  typed review-state lookup now consults repo-pack candidate paths only when a
  repo has explicitly overridden them.

### Self-Hosting Organization Correction

- Reference-doc cleanup is now explicitly an absorption-first operation, not a
  delete-first cleanup pass. The repo currently carries 27 `dev/active/*.md`
  docs and 10 root-level markdown entrypoints; until accepted conclusions from
  reference/audit companions are mirrored into `MASTER_PLAN` plus the scoped
  owner docs, those files are not safe to archive.
- Root evidence companions (`UNIVERSAL_SYSTEM_PLAN.md`,
  `UNIVERSAL_SYSTEM_EVIDENCE.md`, `ZGRAPH_RESEARCH_EVIDENCE.md`,
  `GUARD_AUDIT_FINDINGS.md`) remain reference-only. They are not execution
  authority, but they also must not be retired until the absorption audit says
  their execution-relevant conclusions are fully mapped into owner plans.

## Pass 10: Claude Intake — Doc Sprawl And Absorption Candidates (Pending Codex Verification)

**Purpose**: Capture ALL untracked findings from evidence files into this
shared ledger so evidence files can eventually be archived. Also document
the doc sprawl problem and product/platform mixing as architecture issues.

**Codex review note (2026-03-26):** only part of this pass is verified so far.
Locally re-verified facts are: 27 `dev/active/*.md` docs, 10 root-level
markdown entrypoints, shadow-authority pressure from root evidence files, and
the absorption-first archive rule. The broader repo-wide markdown totals,
bootstrap-time estimates, and several of the intake tables below remain
unverified. A raw tree scan on the current worktree sees `1,158` `.md` files
and `73` `dev/scripts/**/README.md` surfaces, so the earlier `867` / `39`
counts are not trustworthy authority without an explicit exclusion policy.

### HIGH: Doc Sprawl — 867 Files / 212K Lines

| Category | Files | Lines | Status |
|----------|-------|-------|--------|
| Total .md in repo | 867 | 211,986 | Crisis-level |
| `dev/active/` plans | 27 | ~25K | Too many |
| `dev/guides/` | 15 | ~10K | 3 major overlaps |
| Root MDs | 10 | ~12K | Evidence not migrated |
| `dev/scripts/` READMEs | 39 | ~2K | Fine |
| `dev/audits/` | 7 | ~4.7K | Fine |
| Integration subprojects | 218 | ~45K | Separate concerns |
| Reports/temp/generated | 300+ | ~100K | Exclude from AI |

Bootstrap tax: ~18K lines / 7-8 hours reading to start contributing.

**Class**: organization/portability. **Owner**: MP-377 + MP-376.

### HIGH: Product/Platform Plan Mixing in dev/active/

27 plan docs mix VoiceTerm product and AI platform in one directory:
- **Product only** (4): slash_command_standalone, operator_console,
  naming_api_cohesion, ide_provider_modularization
- **Platform only** (6): ai_governance_platform, review_probes,
  host_process_hygiene, ralph_guardrail_control_plane,
  devctl_reporting_upgrade, code_shape_expansion
- **Mixed** (4): audit, loop_chat_bridge, memory_studio, review_channel
- **Meta** (6): MASTER_PLAN, INDEX, README, PLAN_FORMAT, move, phase2
- **Platform subordinate** (3): platform_authority_loop,
  portable_code_governance, continuous_swarm
- **Product feature** (4): theme_upgrade, pre_release_architecture_audit,
  autonomous_control_plane, host_process_hygiene

**Class**: organization/separation. **Owner**: MP-377.

### HIGH: No AI Context Budget Enforcement

No guard enforces line/file budgets on `dev/active/`. Current sizes:
ai_governance_platform.md (6,294), MASTER_PLAN.md (3,712),
ide_provider_modularization.md (2,946), platform_authority_loop.md (2,135),
memory_studio.md (2,075), operator_console.md (1,998),
theme_upgrade.md (1,941).

**Class**: organization/portability. **Owner**: MP-377.

### Planned But Not Executed

1. Unified docs command (MASTER_PLAN 519-523) — MP-377
2. Hot/warm/cold AI context budgets — MP-377
3. Generated surfaces from repo-pack — MP-376
4. Minimum adoption kit — MP-376
5. Doc sprawl consolidation pass (MASTER_PLAN 518) — MP-377

### Codex Correction: Already Planned Vs Still Open

- The intake `Not planned` list was overstated. Doc lifecycle management,
  hot/warm/cold context budgets, active-doc/file-count budgets, line-budget
  policy, and the first consolidation detector are already planned in
  `MASTER_PLAN`, `ai_governance_platform.md`, and
  `platform_authority_loop.md`.
- Product/platform separation is also already owned at the architecture level
  by `MP-377`; what is still intake is the exact extraction/package/directory
  strategy, not the existence of a tracked separation problem.

### Intake Revalidation: audit.md

**Codex correction:** do not treat `dev/active/audit.md` as proof of
"7 items not in any plan." It is a reference artifact whose execution owner is
`dev/active/pre_release_architecture_audit.md`, and several rows in the
original intake are already tracked there or have gone stale on the current
tree. The file is still not archive-safe because smaller tooling-cleanup items
remain only partially absorbed: `run(args)` typing, logging standardization,
repeated `REPO_ROOT` definitions, and public-function docstring coverage still
need one clean owner chain before that evidence file can retire.

### Intake Revalidation: UNIVERSAL_SYSTEM_EVIDENCE.md

**Codex correction:** do not treat the original seven-row AI-wiring table as
live authority. Large parts of that companion were already promoted into
`review_probes.md`, `ai_governance_platform.md`, and
`platform_authority_loop.md`. The clean remaining absorption items after this
review are narrower:

- universal doc ingestion / existing-repo normalization remains a valid
  portable-adoption proof item, but it is already planned in
  `portable_code_governance.md` and the `MP-377` doc-authority chain.
- deferred-work / ADR execution enforcement was still under-specified as an
  executable contract; this pass promotes that gap into the tracked owner docs
  instead of leaving it stranded in the companion.

The rest of the original table needs line-by-line revalidation before it can be
counted as new open architecture debt.

### Intake Revalidation: GUARD_AUDIT_FINDINGS.md

**Codex correction:** the file remains useful reference evidence, but it is not
proof of planless backlog. Its authority-source, contract-value, and
plan-to-runtime items already map into the `MP-377` authority-closure chain.
Keep it as focused reference evidence unless a later pass finds an item that is
still missing from the owner plans.

### Intake Revalidation: convo.md

**Codex correction:** `convo.md` is raw external critique, not execution
authority. Its accepted themes already map to the existing convergence / AI
feedback-loop work in `review_probes.md`, `MASTER_PLAN`, and
`ai_governance_platform.md`. Keep it only if the raw critique transcript is
still useful; do not treat it as a second roadmap.

### Candidate Archival / Retention Verdicts (Codex Reviewed 2026-03-26)

| File | Lines | Status |
|------|-------|--------|
| `dev/active/move.md` | 33 | archive-safe; pure supporting transcript once `audit.md` remains reachable |
| `dev/active/RUST_AUDIT_FINDINGS.md` | 8 | keep bridge for now; migration pointer, not a cleanup blocker |
| `dev/active/phase2.md` | 8 | keep bridge for now; deferred pointer, not a cleanup blocker |
| `UNIVERSAL_SYSTEM_PLAN.md` | 142 | keep as reference; already disposition-shaped, not an immediate archive target |
| `dev/active/audit.md` | 82 | not archive-safe yet; still carries partially absorbed cleanup inventory |
| `UNIVERSAL_SYSTEM_EVIDENCE.md` | 1,680 | not archive-safe yet; two execution-relevant conclusions still needed owner-level absorption proof |
| `GUARD_AUDIT_FINDINGS.md` | 267 | keep as focused reference; no unique owner-mapping blocker found in this pass |
| `convo.md` | 5,668 | execution-state safe to move/drop once operator no longer needs the raw transcript; accepted themes are already mapped elsewhere |
| `ZGRAPH_RESEARCH_EVIDENCE.md` | 1,428 | keep preserved reference; later-phase research archive, not a demotion/cleanup target in this pass |

## Pass 11: Claude Intake — Product/Platform Separation Audit (Pending Codex Verification)

**Purpose**: Map the structural mixing of VoiceTerm product code and AI
governance platform code. Determine feasibility and risks of separation.

**Codex review note (2026-03-26):** the direction is useful, but this section
is still intake. The existence of product/platform mixing in docs/plans is
verified, and `MP-377` already owns the extraction problem. The exact import
counts, workflow classifications, AGENTS percentage splits, and proposed
three-phase extraction strategy below still need line-by-line verification
before they count as accepted architecture findings.

### HIGH: Directory Structure — Product and Platform Are Conceptually Clean But Operationally Tangled

**Code separation is good** — the actual source code directories are clean:
- `rust/` — Pure VoiceTerm product (Rust voice terminal overlay)
- `dev/scripts/devctl/` — AI governance platform engine (109+ Python modules)
- `dev/scripts/checks/` — Platform guard/probe enforcement (139 scripts)

**But plans, docs, config, and CI are tangled**:
- `dev/active/` — 27 plan docs mixing product and platform (classified above)
- `dev/guides/` — 10 of 15 guides are platform, 1 is product, 4 are mixed
- `AGENTS.md` — 60-62% platform rules, 12-15% product rules, 15-17% shared
- `.github/workflows/` — CI deeply monorepo-coupled (details below)
- `app/operator_console/` — Product UI that imports 23 files from platform

**Class**: organization/separation. **Owner**: MP-377.

### Directory Classification

| Directory | Classification | Notes |
|-----------|---------------|-------|
| `rust/` | PRODUCT | Pure Rust voice terminal |
| `app/macos/`, `app/ios/` | PRODUCT | Platform-specific launchers |
| `app/operator_console/` | SHARED (product UI importing platform) | 23 imports from devctl |
| `pypi/` | PRODUCT | PyPI distribution |
| `guides/` | PRODUCT | End-user docs (INSTALL, USAGE, etc.) |
| `scripts/` | PRODUCT | User-facing launchers (start.sh, install.sh) |
| `bin/` | PRODUCT | Entry point wrappers |
| `dev/scripts/devctl/` | PLATFORM | 109+ modules, governance engine |
| `dev/scripts/checks/` | PLATFORM | 139 guard/probe scripts |
| `dev/guides/` | MOSTLY PLATFORM | 10 platform, 1 product, 4 mixed |
| `dev/active/` | MIXED | 27 plan docs, both domains |
| `dev/config/` | SHARED | Repo policy + quality presets |
| `dev/reports/` | PLATFORM | Generated output |
| `integrations/` | PLATFORM | ci-cd-hub, code-link-ide |
| `data_science/` (root) | MISPLACED | Just a README pointing to dev/scripts/devctl/data_science/ |

### AGENTS.md Breakdown

| Category | Lines | Percentage |
|----------|-------|-----------|
| AI platform rules (devctl, guards, probes, governance) | ~1,150-1,200 | 60-62% |
| Shared process (git, commit, release, CI) | ~280-330 | 15-17% |
| VoiceTerm product rules (Rust, HUD, themes, audio) | ~240-280 | 12-15% |

If someone adopted just the AI platform, **85-88% of AGENTS.md is relevant**.
The 12-15% VoiceTerm content is in context packs, risk matrices, and
execution sections that could be isolated.

### dev/guides/ Classification

| File | Classification |
|------|---------------|
| DEVCTL_ARCHITECTURE.md | PLATFORM |
| DEVCTL_PRODUCT_FLOW.md | PLATFORM |
| DEVCTL_MULTI_AGENT_OPERATIONS.md | PLATFORM |
| DEVCTL_JSON_CONTRACTS.md | PLATFORM |
| MCP_DEVCTL_ALIGNMENT.md | PLATFORM |
| DEVCTL_AUTOGUIDE.md | PLATFORM |
| AI_GOVERNANCE_PLATFORM.md | PLATFORM |
| AGENT_COLLABORATION_SYSTEM.md | PLATFORM |
| PORTABLE_CODE_GOVERNANCE.md | PLATFORM |
| SYSTEM_AUDIT.md | PLATFORM |
| ARCHITECTURE.md | PRODUCT (Rust overlay) |
| SYSTEM_FLOWCHART.md | MIXED |
| SYSTEM_ARCHITECTURE_SPEC.md | MIXED |
| DEVELOPMENT.md | MIXED |
| README.md | META |

### MASTER_PLAN MP Item Breakdown

Total: 293 MP items (95 active, 198 completed).

| Category | Items | % |
|----------|-------|---|
| Mixed (product+platform) | 157 | 54% |
| AI platform only | 69 | 24% |
| VoiceTerm product only | 53 | 18% |
| Uncategorized | 14 | 5% |

Top active priority is **MP-377** (platform extraction) — explicitly about
separating the platform from VoiceTerm. MASTER_PLAN already plans this
separation; execution hasn't started.

### HIGH: Python Import Tangle Blocks Clean Separation

**operator_console → devctl**: 23 files import from devctl (repo_packs,
runtime, watchdog). This is the tightest coupling.

**checks ↔ devctl**: Bidirectional — 26 check files import from devctl,
31 devctl files import from checks. Uses try/except fallbacks, but creates
circular dependency risk.

**devctl → app**: ZERO imports. Clean.
**devctl → rust**: ZERO Python imports. Clean (Rust referenced as paths only).

| Direction | Files | Risk |
|-----------|-------|------|
| operator_console → devctl | 23 | BLOCKS MOVE |
| checks → devctl | 26 | MEDIUM |
| devctl → checks | 31 | MEDIUM |
| devctl → app | 0 | SAFE |
| devctl → rust | 0 | SAFE |

### HIGH: CI Workflows Are Monorepo-Coupled

32 workflows classified:

| Classification | Count | Examples |
|----------------|-------|---------|
| VOICETERM_PRODUCT | 10 | rust_ci, coverage, latency_guard, memory_guard, ios_ci, publish_release_binaries, publish_homebrew |
| AI_PLATFORM | 2 | pre_commit, publish_pypi |
| SHARED | 4 | docs_lint, dependency_review, security_guard, release_preflight |
| META | 6 | orchestrator_watchdog, autonomy_controller, coderabbit_triage, failure_triage |

**Critical breaking point**: `release_preflight.yml` runs 60+ checks across
BOTH Rust and Python assuming they're in the same checkout. `security_guard.yml`
checks both `Cargo.lock` and Python. `rust_ci.yml` calls `devctl ai-guard`
(Python) even in Rust CI.

Separating product from platform would require splitting release_preflight
into 2+ workflows, extracting devctl profiles per language, and creating
mirror security gates.

### Misplaced Directories

| Directory | Issue | Fix |
|-----------|-------|-----|
| `/data_science/` (root) | Just a README pointing to `dev/scripts/devctl/data_science/` | Move README into devctl/data_science/ or delete |

All other directories are intentionally placed. `/scripts/` (user-facing)
vs `/dev/scripts/` (maintainer) is correct. `/app/operator_console/` is
correctly at app root but has platform import coupling.

### Separation Strategy (From Agent Analysis)

**Phase 1 — Create platform boundary (no file moves)**:
- Create `platform/` directory with re-exports from dev/scripts/devctl/
- Create `platform/pyproject.toml` as publishable package
- Create `product_integrations/` for VoiceTerm-specific wiring
- External tools can `import platform` instead of `import dev.scripts.devctl`

**Phase 2 — Move actual code (2-3 weeks refactoring)**:
- Move `dev/scripts/devctl/governance/` → `platform/governance/`
- Move `app/operator_console/` → `platform/frontends/pyqt6_console/`
- Extract shared contracts into `platform/contracts/`
- Move `dev/config/quality_presets/` → `platform/repo_packs/`

**Phase 3 — Separate repo (optional, future)**:
- Platform becomes `ai-governance-platform/` standalone repo
- VoiceTerm depends on it as a package

**Minimum viable separation (zero breaking changes)**:
- Create `platform/__init__.py` re-exporting from devctl
- Add `platform/pyproject.toml` for package boundary
- Document separation rules in a plan doc
- Enforce with CI: "no VoiceTerm imports in platform modules"

### Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Circular imports (checks ↔ devctl) | HIGH | Extract shared contracts layer first |
| operator_console 23 imports break | HIGH | Create platform/shared/ with re-exports |
| Config paths hardcoded to dev/config/ | HIGH | Resolve all through RepoPathConfig |
| CI release_preflight assumes monorepo | HIGH | Split into per-component workflows |
| Shared type drift after separation | MEDIUM | Codegen contracts from plan docs |

### Pass 11 Summary

| Category | Count |
|----------|-------|
| NEW HIGH | 3 (import tangle, CI coupling, no context budget) |
| NEW MEDIUM | 1 (misplaced data_science README) |
| Structural findings | Product/platform mixing documented across plans, guides, AGENTS.md, CI |
| Separation feasibility | Possible in 3 phases; Phase 1 has zero breaking changes |
| Owner | MP-377 (extraction) + MP-376 (portable engine) |

## Pass 12: Claude Intake — Branch State Audit + New Repo Extraction Plan (Pending Codex Verification)

**Purpose**: Audit the state of all branches, what's pushed vs local, and
evaluate extracting the AI platform to a standalone repo.

**Codex review note (2026-03-26):** this section is intake, not accepted
branch-state authority. It already disagrees with current live repo state:
`git status -sb` shows the branch is ahead of upstream by `17` commits, not
`15`, and current review-channel status reports `44` modified plus `3`
untracked paths with checkpoint-required state. Treat the extraction strategy,
package counts, and branch-delta numbers below as proposals to verify, not as
accepted architecture truth.

### Branch State Summary

| Branch | Ahead of master | Status |
|--------|----------------|--------|
| master | baseline | v1.1.1 released 2026-03-06, 45 commits this month, stable |
| develop | +12 commits | iOS app, operator console, control plane, post-v1.1.1 cleanup |
| feature/governance-quality-sweep (current) | +130 commits | Governance hardening, review-channel, startup authority |

**Current branch → master delta**: 1,440 files changed, 241K insertions,
17K deletions. 130 commits.

**Current branch → develop delta**: 1,097 files changed, 142K insertions,
13K deletions. 30 commits.

### What's NOT on GitHub Yet

| Item | Count |
|------|-------|
| Uncommitted dirty files | 47 modified + 3 untracked |
| Unpushed commits (current branch) | 15 |
| Unpushed on master | 0 (in sync) |
| Unpushed on develop | 0 (in sync) |
| Stashed work items | 8 (across various branches) |

### Change Breakdown: Product vs Platform

**On the current branch (master..HEAD)**:

| Category | Files | % of total |
|----------|-------|-----------|
| AI Platform (devctl + checks + config + active + guides) | 960 | 66.6% |
| VoiceTerm Product (rust + app + pypi + guides + scripts) | 389 | 27.0% |
| Shared/CI/Docs | 91 | 6.3% |

**Key finding**: Two-thirds of branch work is AI platform. The VoiceTerm
product changes (172 Rust files) are real but secondary to the platform
work.

### Master State Assessment

Master is a **strong baseline for VoiceTerm**:
- v1.1.1 released, 2,413 test annotations in Rust
- Critical race conditions fixed, 5-15GB debug logging removed
- Production-quality product with comprehensive CI
- **All platform work (devctl, checks, governance) since master is on
  feature branches only** — master has the stable product

### New Repo Extraction: Feasibility

**The plan**: Create `ai-governance-platform` repo with just the platform
code, strip VoiceTerm references, re-integrate into VoiceTerm as dependency.

**Minimum file set for new repo**:
- `dev/scripts/devctl/` (726 Python modules, 21MB)
- `dev/scripts/checks/` (214 guard scripts, 4.5MB)
- `dev/config/` (policy configs, templates, 0.2MB)
- `dev/scripts/devctl/tests/` (110+ test files)
- New `pyproject.toml` (doesn't exist yet — BLOCKER)

**Current state**: NOT pip-installable. No `pyproject.toml` for the
platform. Only `dev/scripts/pyproject.toml` naming it "voiceterm-devtools"
with minimal metadata.

### Extraction Blockers

| Blocker | Severity | Detail |
|---------|----------|--------|
| No package metadata | HIGH | No pyproject.toml, no dependencies declared, no entry points |
| repo_packs hardcoded to VoiceTerm | HIGH | 36+ files import VoiceTerm-specific path config; 48 refs to VOICETERM_PATH_CONFIG |
| sys.path manipulation | MEDIUM | 8+ files use sys.path.insert to load checks dynamically |
| No declared Python dependencies | HIGH | No requirements.txt or pyproject.toml deps |
| Circular checks ↔ devctl imports | MEDIUM | 26 + 31 bidirectional file pairs |

**VoiceTerm binary references**: Minimal. Only 2 files import
`voiceterm_repo_root`. 96 files have "voiceterm" as strings (variable
names, comments, test data) but not in import statements.

### Recommended Extraction Sequence

**Step 1: Create new repo from current branch platform code**
```
ai-governance-platform/
├── pyproject.toml              (NEW)
├── src/ai_governance/
│   ├── platform/               (from devctl/governance/)
│   ├── guards/                 (from dev/scripts/checks/)
│   ├── config/                 (from dev/config/)
│   ├── repo_packs/             (refactored — no VoiceTerm defaults)
│   └── runtime/                (from devctl/runtime/)
└── tests/
```

**Step 2: Refactor repo_packs**
- Make VoiceTerm paths injectable, not default
- `set_active_path_config()` called at consumer init time
- Already partially designed in repo_packs/__init__.py

**Step 3: Create proper packaging**
- Audit all imports for external dependencies
- Create pyproject.toml with proper requires
- Pin Python 3.10+ (current minimum based on code)

**Step 4: Strip VoiceTerm references**
- Remove voiceterm.py from repo_packs
- Update templates to be generic
- Fix 2 files that import voiceterm_repo_root

**Step 5: Re-integrate into VoiceTerm as dependency**
- VoiceTerm pyproject.toml adds ai-governance-platform
- VoiceTerm provides VoiceTermPathConfig at startup
- All 48 VOICETERM_PATH_CONFIG refs resolve through injected config

### Why New Repo is Better Than In-Place Separation

1. **Clean room**: No risk of accidentally keeping VoiceTerm coupling
2. **Fresh docs**: Platform docs written for platform, not mixed with product
3. **Independent CI**: Platform CI tests portability, not VoiceTerm
4. **Forces the boundary**: Can't cheat with relative imports to parent dirs
5. **Proves portability**: If it works standalone, it works anywhere
6. **VoiceTerm stays stable**: Master is untouched, product keeps working

### Risk: Branch Work Not on Master

The platform code being extracted lives on `feature/governance-quality-sweep`
(130 commits ahead of master). Master has the stable VoiceTerm product but
NOT the latest platform work. The extraction should:
- Use the current branch as source for platform code
- Leave master alone as the VoiceTerm product baseline
- NOT merge 130 governance commits into master before extraction

### Estimated Effort

| Phase | Effort | Dependencies |
|-------|--------|-------------|
| Create repo + copy files | 1 day | None |
| Create pyproject.toml + deps | 2-3 days | Audit all imports |
| Refactor repo_packs | 3-5 days | Core architecture decision |
| Strip VoiceTerm refs | 2-3 days | repo_packs done first |
| Re-integrate into VoiceTerm | 3-5 days | Standalone tests passing |
| **Total** | **~2-3 weeks** | Sequential |

### Pass 12 Summary

| Finding | Severity | Owner |
|---------|----------|-------|
| 130 commits of platform work not on master | HIGH (risk) | MP-377 |
| 47 dirty + 15 unpushed files on current branch | HIGH (risk) | Immediate |
| No pyproject.toml for platform package | HIGH (blocker) | MP-376 |
| 48 VOICETERM_PATH_CONFIG refs to strip | HIGH (work) | MP-377 |
| Master is stable VoiceTerm baseline | POSITIVE | — |
| 66.6% of branch work is platform, not product | CONFIRMS | Extraction is the right move |
| New repo extraction feasible in 2-3 weeks | ASSESSMENT | MP-377 |

## Pass 13: VoiceTerm Product Work at Risk (Claude, 8-Agent Branch Audit)

**Purpose**: Before extracting the platform to a new repo, verify what
VoiceTerm PRODUCT work exists on branches that master doesn't have. This
determines whether master alone is a safe VoiceTerm baseline.

### CRITICAL: Master is NOT a Complete VoiceTerm Baseline

**Master (v1.1.1) is MISSING major product features** that exist on develop
and the current branch. Keeping only master would lose ~19,000 lines of
core product work.

### VoiceTerm Product Work on develop (NOT on master)

develop has 12 commits ahead of master with substantial product additions:

| Feature | Files | Lines | Severity if Lost |
|---------|-------|-------|-----------------|
| **Daemon architecture** (multiprocess, event bus, WebSocket, memory bridge) | 15+ new Rust files in daemon/ | ~3,000+ | CRITICAL — enables mobile relay |
| **iOS mobile app** (VoiceTermMobile, Swift, full relay UI) | 21 new files in app/ios/ | ~5,000+ | CRITICAL — entire new platform |
| **Operator console** (PyQt6 desktop, 170+ files) | 170 new Python files | ~32,000 | HIGH — enterprise control surface |
| **Memory system** (survival_index, enhanced retrieval) | 5+ Rust files | ~1,500+ | HIGH — core feature |
| **Dev panel overhaul** (artifact review, action catalog, brokers) | 20+ Rust files | ~4,000+ | MEDIUM |
| **Theme studio expansion** (component editor, export, preview) | 10+ Rust files | ~800+ | MEDIUM |
| **Status line refactor** (test suite split, format improvements) | 10+ Rust files | ~1,200 | MEDIUM |

### Additional VoiceTerm Work on Current Branch (NOT on develop)

The current branch has 52 more Rust files changed beyond develop:

| Feature | Files | Lines |
|---------|-------|-------|
| Daemon hardening (agent_driver, event_bus, memory_bridge, socket, ws) | 10+ | ~500+ |
| Memory subsystem (retrieval, survival_index, types, browser) | 5+ | ~400+ |
| UI components (status_line, overlays, transcript_history, banner) | 8+ | ~300+ |
| Action center and onboarding | 3+ | ~200+ |

Plus 63 more app/ changes (operator console collaboration, sessions, iOS).

### Rust Dependency Changes (Build Would Break on Master)

**4 new Rust dependencies added since master**:
- `tokio` (async runtime with multi-threaded support)
- `tokio-tungstenite` (async WebSocket)
- `tungstenite` (WebSocket protocol)
- `futures-util` (async stream utilities)

Plus 21 transitive dependencies (crypto, networking, etc). **Building the
current Rust code on master's Cargo.toml would FAIL** — async/await and
WebSocket code won't compile without these deps.

### CI Workflows Not on Master

20 of 32 CI workflows exist only on branches, including:

**Product-critical (would break VoiceTerm CI)**:

## Pass 14: Codex Self-Hosting Docs/Push Contract Audit (Verified 2026-03-27)

**Pass 14: 1 new HIGH finding, plus measured self-hosting baselines promoted
into owner plans.**

### NEW HIGH: Governed push is not fail-closed end-to-end

`dev/scripts/devctl/sync_parser.py:47-68` still exposes `devctl push`
`--skip-preflight` and `--skip-post-push`, and
`dev/scripts/devctl/commands/vcs/push.py:54-55,136,207,327-328` carries those
flags through the canonical governed push path. The parser contract is covered
by `dev/scripts/devctl/tests/vcs/test_push.py:76-93`, which asserts the CLI
accepts `--skip-post-push`.

Codex also verified the runtime consequence on the live branch during the
2026-03-27 governed push of `feature/governance-quality-sweep`: startup truth
correctly advanced to `push_allowed`, preflight passed, `git push` succeeded,
and the branch reached `origin/feature/governance-quality-sweep`; only after
publication did the configured post-push bundle fail on
`check_code_shape.py --since-ref origin/develop`.

**Class**: push-authority / workflow integrity. **Why**: the canonical push
surface can still publish a branch before the full governance contract is
green, and it still exposes explicit bypass switches for the same contract.
That is an architecture gap, not operator-only error handling.
**Owner**: `MP-377` push/startup authority contract, with adopter-surface
parity follow-up in `MP-376`.

### Measured Self-Hosting Baseline (No New Severity Promotion)

Codex re-ran the repo-owned self-hosting surfaces to replace vague
"too many docs" claims with measured baseline evidence:

- `python3 dev/scripts/devctl.py doc-authority --format md` reports
  `50` governed docs, `45,107` total lines, `19` budget violations,
  `4` authority overlaps, and `8` consolidation candidates.
- `python3 dev/scripts/checks/check_package_layout.py --format md` reports
  `4` frozen crowded directories
  (`dev/scripts/checks`, `dev/scripts/devctl`,
  `dev/scripts/devctl/commands`, `dev/scripts/devctl/tests`) plus
  `7` crowded namespace families.
- `python3 dev/scripts/devctl.py governance-draft --format md` confirms the
  universal authority shape is partially landed (`ProjectGovernance`,
  `PlanRegistry`, `DocPolicy`, `DocRegistry`, startup order, push-enforcement
  snapshot), but this repo still resolves those surfaces through VoiceTerm-
  shaped authority roots.

These measurements do **not** create a second new HIGH/MEDIUM finding by
themselves because the underlying doc-authority and self-hosting organization
gap is already owned in the active `MP-377` / `MP-376` chain. They do,
however, raise the priority of executing that existing plan instead of
treating it as background cleanup.

### Universal-Plan Clarification (Codex Verified)

The repo does not need a second universal-system roadmap. The universal
authority model is already the active owner chain:
`MASTER_PLAN -> ai_governance_platform -> platform_authority_loop ->
portable_code_governance`. Root companions such as `UNIVERSAL_SYSTEM_PLAN.md`,
`UNIVERSAL_SYSTEM_EVIDENCE.md`, `GUARD_AUDIT_FINDINGS.md`, and
`ZGRAPH_RESEARCH_EVIDENCE.md` remain intake/reference only until accepted
conclusions are mirrored into that owner chain.

The next closure therefore is executable compression, not more parallel docs:

1. Finish `DocPolicy` / `DocRegistry` / `doc-authority` as the bounded
   startup/read surface for governed markdown.
2. Separate self-hosting development authority from portable adopter/bootstrap
   surfaces so exported/generated instructions do not teach VoiceTerm-shaped
   defaults as universal truth.
3. Burn down over-budget active docs and crowded `devctl` roots through the
   existing organization contract rather than one-off cleanup.
4. Make the governed push contract fail closed end-to-end, including
   bypass-flag removal/policy gating and clear "published vs post-push green"
   semantics.

### Priority Routing Note

Pass 14 is now the active architecture-priority intake for this neighborhood,
not a side memo. Until the owner plans close the self-hosting authority
budget, the development-self-hosting vs adopter/bootstrap boundary, and the
governed-push integrity gap, new findings in this area should map back into
the same `MP-377` / `MP-376` tranche instead of spawning another parallel
organization roadmap.

### External Review Adjudication (2026-03-27, Codex verified)

An external architecture review usefully reinforced the main diagnosis:
split authority is still the current blocker, not missing platform ambition.
Codex verified the strongest parts against the repo and routed them into the
same owner chain instead of treating the write-up as a second roadmap.

Accepted direction, translated into current repo architecture:

1. Keep machine startup authority singular: use `ProjectGovernance`,
   generated `project.governance.json` (or equivalent typed materialization),
   typed registries, and startup/runtime receipts as the machine truth.
2. Keep the reviewed repo-governance markdown contract
   (`project.governance.md` as the current working name) as the human mirror
   of that machine authority, not as a competing runtime authority.
3. Make startup/intake classify artifact role more explicitly so AI can tell
   portable platform work, repo-pack/client work, development-self-hosting
   docs, and generated/compatibility projections apart.
4. Keep generated AI/bootstrap surfaces, bridge/status views, and similar
   projections derived from the typed authority path only.
5. Make repo-pack capability gating/adopter presets prove optional subsystems
   really are optional for non-VoiceTerm adopters.
6. Keep findings/remediation history on one canonical evidence path:
   strengthen `Finding` / `FindingReview` / quality-feedback / Ralph memory
   consumption rather than inventing a second pattern ledger with overlapping
   ownership.
7. Keep registry/config sprawl on the existing config-driven closure path:
   guard/probe/bundle/routing/provider registration should resolve from
   repo-pack/policy/typed registry surfaces rather than remaining as hidden
   hardcoded chains in portable layers.
8. Self-host the same authority/meta-governance rules on this repo and keep
   the "second repo without core patches" proof ahead of graph/memory
   expansion so portability is demonstrated, not narrated.

Required translation corrections:

- Do **not** replace the current typed authority spine with a new
  JSON-only constitution. The repo already plans
  `ProjectGovernance -> RepoPack -> PlanRegistry -> PlanTargetRef ->
  WorkIntakePacket -> CollaborationSession -> TypedAction -> ActionResult /
  RunRecord / Finding -> ContextPack`; the closure is to finish that cutover,
  not to discard it.
- Do **not** require a new shadow JSON twin for every plan before the current
  `PlanRegistry` / governed-markdown contract is ready. Close the existing
  typed-registry lane first, keep markdown execution authority reviewed, and
  only promote machine twins where the owner chain already calls for them.
- Do **not** widen into graph/memory work before authority, portability, and
  capability gating closure. The external review was right on sequencing, and
  that remains the accepted order here too.

Still-open owner-chain follow-ups sharpened by that review:

- 2026-03-27 first authority-closure tranche now exists as code and fixture
  proof, not just intake prose. `ProjectGovernance` doc/plan registries now
  carry typed `artifact_role`, `authority_kind`, `system_scope`, and
  `consumer_scope`; startup warm refs suppress compatibility projections and
  lane-specific docs by default; and `startup-context` no longer treats
  `bridge.md` prose as fallback startup authority when typed
  `review_state.json` is missing. Custom-layout and no-bridge governance
  fixtures now prove the same contract on alternate repo shapes.
- Make `startup_order` / warm-ref routing honor artifact-role and
  consumer-scope classification so development/tooling docs and compatibility
  projections load only for matching lanes instead of bleeding into every
  startup packet.
- Split or suppress mixed universal-vs-current-operating-mode docs where
  needed (especially temporary markdown-swarm material) so AI startup does
  not confuse a live VoiceTerm operating mode with the portable product
  contract.
- Keep config-driven registry closure, self-host meta-guards, and the second-
  repo proof in the same `MP-377` / `MP-376` tranche rather than as later
  cleanup ambitions.

### Pass 14 Summary

| Category | Count |
|----------|-------|
| NEW HIGH | 1 (governed push not fail-closed end-to-end) |
| Measured self-hosting baselines | 3 repo-owned command reads |
| Revalidated owner-chain clarification | 1 (universal plan already exists; execute it) |
- `rust_ci.yml` (core Rust CI — fmt, clippy, tests)
- `voice_mode_guard.yml`, `latency_guard.yml`, `memory_guard.yml`
- `wake_word_guard.yml`, `parser_fuzz_guard.yml`, `perf_smoke.yml`
- `coverage.yml`, `ios_ci.yml`
- `publish_release_binaries.yml`, `publish_homebrew.yml`

**Platform CI**: autonomy_controller, coderabbit_triage, orchestrator_watchdog, etc.

### User-Facing Changes Not on Master

| Change | Impact |
|--------|--------|
| PyPI auto-bootstrap of native binaries (bootstrap.py) | Users lose one-click install |
| New CLI flags: --capture-once, --format, --daemon, --ws-port | Feature loss |
| Operator console launcher script | New feature unavailable |
| iPhone/iPad companion docs and workflow guidance | Feature loss |
| User guide restructuring (Pick Your Level, new nav) | UX regression |
| README.md complete rewrite | Marketing/discovery impact |
| Fallback script NUL-byte injection protection | Security regression |

### iOS App Status

**NOT on master at all.** The entire iOS app (VoiceTermMobile, Swift
package, simulator tests, daemon WebSocket client) was introduced in commit
54ff89f on develop. 22 files exist on the current branch. Would be
completely lost if only master is kept.

### Operator Console Status

**NOT on master.** 170+ Python files (32K lines) with comprehensive
subsystems: theme engine, collaboration panels, session tracing, job
tracking, workflow presets, full test suite. First appeared on develop
at commit a334977. Classified as VoiceTerm PRODUCT (not platform) — it's a
PyQt6 desktop app that wraps devctl workflows for operators.

### Revised Extraction Plan

**Master alone is NOT a safe VoiceTerm baseline.** Before extracting the
platform to a new repo, VoiceTerm product work must be preserved:

**Option A: Merge product work to master first**
1. Cherry-pick or merge VoiceTerm product commits from develop → master
2. Include: daemon architecture, iOS app, operator console, Rust deps,
   CI workflows, user guides, PyPI bootstrap
3. Exclude: platform-only changes (devctl, checks, governance docs)
4. Then extract platform from current branch to new repo
5. Risk: Hard to separate product from platform commits (they're interleaved)

**Option B: Use develop as the VoiceTerm baseline instead of master**
1. Merge develop → master (12 commits, includes both product AND some platform)
2. Then extract platform from current branch to new repo
3. Then strip platform code from VoiceTerm master after re-integration
4. Risk: Puts some platform code on master temporarily

**Option C: Branch-based extraction (recommended)**
1. Push all unpushed work (15 commits + 47 dirty files) to remote
2. Create new repo by copying platform files from current branch
3. Keep current branch alive as the "full state" reference
4. Merge product-only changes to develop → master in a focused PR
5. Then integrate platform as dependency in VoiceTerm
6. Risk: Requires careful cherry-picking of product vs platform

### What Must Happen Before ANY Extraction

1. **Push everything** — 15 unpushed commits + 47 dirty files + 8 stashes
2. **Tag the current state** — `git tag pre-extraction-snapshot` so nothing is lost
3. **Decide the VoiceTerm baseline** — master, develop, or current branch
4. **Identify product-only commits** for merging to master

### Pass 13 Summary

| Finding | Severity |
|---------|----------|
| Master is MISSING daemon architecture, iOS app, operator console, memory system, 4 Rust deps, 20 CI workflows, user guide rewrites | CRITICAL |
| Building current Rust code on master's Cargo.toml would FAIL (missing tokio, tungstenite) | CRITICAL |
| iOS app exists ONLY on branches (22 files, entirely new platform) | CRITICAL |
| Operator console exists ONLY on branches (170 files, 32K lines) | HIGH |
| 20 CI workflows exist ONLY on branches (including product-critical Rust CI) | HIGH |
| PyPI bootstrap, new CLI flags, security fixes only on branches | HIGH |
| Option C (branch-based extraction with focused product PR) is safest path | RECOMMENDATION |
