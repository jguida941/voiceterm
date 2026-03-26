# Architecture Alignment Audit

**Created**: 2026-03-26 | **Owner**: MP-377 / MP-376
**Method**: 8-agent parallel audit across all devctl subsystems

## Executive Summary

The AI governance platform is **~80% portable**. The core engine (guards,
probes, quality-policy, context-graph builder, autonomy orchestration) is
governance-driven and works on external repos (proven on ci-cd-hub). But
**~460 hardcoded VoiceTerm references** across 36 files create hidden
coupling that would break on non-VoiceTerm repos.

The root cause is a two-layer bootstrap design: runtime contracts resolve
from `ProjectGovernance` (portable), but when governance isn't loaded,
everything falls back to `VOICETERM_PATH_CONFIG` frozen at import time.

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

### Coverage: integrations layer — NO NEW ISSUES

- `federation_policy.py`: policy-driven, parameterized. PORTABLE.
- `integrations-sync`: generic git submodule sync. PORTABLE.
- `integrations-import`: uses allowlisted destination roots. PORTABLE.
- `import_core.py`: generic path collection. PORTABLE.
- One MEDIUM issue: `DEFAULT_ALLOWED_DESTINATION_ROOTS = ["dev/
  integrations/imports"]` should move to `RepoPathConfig`.

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
| MEDIUM | 3 | tandem hash exclusions (new), MCP server name (new), MCP tools autonomy coupling (new) |
| Coverage notes | 4 subsystems | mobile/phone/publication-sync: no issues. integrations: 1 minor. tandem: 4/7 portable |

## Combined Pass 1+2 Totals

| Severity | Pass 1 | Pass 2 | Total |
|---|---|---|---|
| HIGH | 7 | 1 | 8 |
| MEDIUM | 7 | 3 | 10 |
| Coverage (no issues) | 0 | 4 subsystems | 4 |

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
| MEDIUM | 7 | 3 | 1 | **11** |
| Coverage (no issues) | 0 | 4 | 3 | **7 subsystems clean** |

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
  retention policy.
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
| **Pass 5 review** | **Codex** | **0** | **2** |

Broad subsystem discovery is saturated, but the docs/plan review still found
two MEDIUM contract-teaching issues after Claude's zero-new Pass 5. All
Python control-plane subsystems and the reviewed authority docs now have
explicit coverage, but the closure bar is still not met until another bounded
architecture/docs/plan pass confirms zero new HIGH/MEDIUM after these
corrections.

**Closure criteria status:**
- [x] All HIGH/MEDIUM findings mapped to owner plans
- [ ] Fixed rows link to proof (findings tracked, fixes pending implementation)
- [x] Every subsystem has audit coverage
- [ ] Two consecutive bounded passes with zero new HIGH/MEDIUM
- [x] Plan ownership conflicts resolved by Codex mapping update
