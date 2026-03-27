# Architectural Issues Register

**Status**: active  |  **Last updated**: 2026-03-27 | **Owner:** MP-377 / platform authority loop

This file tracks architectural gaps, wiring failures, and systemic issues
found during audits. Each issue includes root cause, evidence, and what would
close it. Plan refs are noted where partial or full tracking exists, but issues
remain here until the code fix is verified landed — a plan checklist item
existing does NOT mean the issue is resolved.

---

## ISS-001: Probes scan single files — cannot detect cross-file problem relocation

**Severity**: critical
**Category**: detection_gap
**Status**: in_progress
**Plan ref**: MASTER_PLAN:3074 (unchecked), review_probes.md:357 (unchecked), ai_governance_platform:3595

**Problem**: Many probes (`probe_design_smells`, `probe_fan_out`, etc.) still
operate on one file's text at a time. The repo now has a bounded fix for
`probe_single_use_helpers`: it can count cross-file Python call sites across
the changed-file set and detect moved single-use helpers in their new support
file. The broader architecture gap remains because other context-blind probes
still do not reuse a shared cross-file corpus before issuing findings.

**Root cause**: Cross-file context is not yet a shared default probe service.
`probe_single_use_helpers` now has a reusable Python call-site prepass through
`probe_bootstrap`, but the rest of the probe stack still mostly scans changed
files independently and ignores repo-level movement/import evidence.

**Evidence**: Governance review rows 8-10 show
`review_channel_bridge_handler.py` was "fixed" three times for
`probe_single_use_helpers` — each time by moving helpers to a new support file.
Regression coverage now exists in
`dev/scripts/devctl/tests/checks/test_probe_single_use_helpers.py`.

**What would close it**: Promote the shared cross-file corpus beyond
`probe_single_use_helpers`: adopt the same prepass in the remaining
context-blind probes and validate the move-heavy path against affected
neighbors before treating large reorganizations as broadly safe.

---

## ISS-002: Context graph metrics not wired into probe/fix pipeline

**Severity**: high
**Category**: integration_gap
**Status**: open
**Plan ref**: ai_governance_platform:3209-3221 (unchecked)

**Problem**: The context graph system computes temperature, fan_in, fan_out,
bridge scores, and coupling metrics. The probe topology builder
(`probe_topology_packet.py`) recomputes fan_in/fan_out independently from
scratch instead of loading the graph snapshot. The `bounded_next_slice`
instruction is hardcoded to "one file + one neighbor" regardless of coupling.
The autonomy loop receives graph data only as context-injection text, never for
fix ordering or risk assessment.

**Root cause**: The graph builder (`context_graph/builder.py`) and the probe
topology builder (`probe_topology_packet.py`) are parallel systems with no
shared data path. `priority_score()` in `probe_topology_packet.py:56-76` uses
locally computed fan_in/fan_out, not graph snapshot values.

**Evidence**: `bounded_next_slice()` at `probe_topology_packet.py:208-226`
always emits "Start in {file_path}; focus on {symbols}; fix the strongest hint
in one file" regardless of whether fan_in is 1 or 50.

**What would close it**: Load the latest context graph snapshot in
`probe_topology_builder.py` and use graph temperature/coupling to determine fix
scope and priority. `bounded_next_slice` should vary scope based on coupling.

---

## ISS-003: No post-fix re-verification of governance review verdicts

**Severity**: critical
**Category**: verification_gap
**Status**: open
**Plan ref**: platform_authority_loop:851 (partial — mentions validation_plan
as live contract but does not require re-scanning probes or verifying verdicts)

**Problem**: When AI marks a finding as "fixed" via
`governance-review --record --verdict fixed`, the system records the verdict in
the JSONL ledger without re-running the probe that originally detected the
finding. There is no code path that re-scans the file, verifies the finding is
gone, or checks whether the same pattern appeared elsewhere.

**Root cause**: `governance_review_log.py:build_governance_review_row()` writes
the verdict directly. The `--verdict` parameter is accepted on the AI's
self-report with no automated validation. The `guidance_followed` flag is
informational only.

**Evidence**: The `fp_classifier.py` pre-classifies `probe_single_use_helpers`
as `CONTEXT_BLIND` — the system knows the probe cannot see cross-file
relationships but nothing acts on that classification.

**What would close it**: Before accepting a "fixed" verdict, re-run the
original probe on the target file and at least its direct import neighbors.
Reject the verdict if the finding count did not decrease in the scanned area.

---

## ISS-004: improvement_tracker exists but is not wired into autonomy decisions

**Severity**: high
**Category**: wiring_gap
**Status**: open
**Plan ref**: platform_authority_loop:989 (unchecked), MASTER_PLAN:3649 (unchecked)
— both mention quality deltas and convergence proof but lack a concrete item to
wire `improvement_tracker.compute_improvement_delta()` into the autonomy loop.

**Problem**: `improvement_tracker.py` in
`governance/quality_feedback/improvement_tracker.py` computes quality deltas
(before/after maintainability scores, per-check precision improvements). This
data is only used in the governance quality feedback REPORT. It is never
consulted by the autonomy loop, guard-run, or any fix decision logic.

**Root cause**: The improvement tracker was built for reporting, not for
decision-making. The autonomy loop (`run_feedback.py:224-244`) tracks
round-to-round `unresolved_count` but does not compare to baseline or use the
improvement tracker.

**Evidence**: No import of `improvement_tracker` or
`compute_improvement_delta` found in any autonomy, guard-run, or loop module.

**What would close it**: Call `compute_improvement_delta()` after each autonomy
round. If the quality score did not improve or findings relocated without
decreasing, mark the round as `stall` and do not count as `improve_streak`.

---

## ISS-005: Decision packets are per-finding — no pattern-level aggregation

**Severity**: high
**Category**: architecture_gap
**Status**: open
**Plan ref**: platform_authority_loop:885-889 (partial — tracks GovernanceFinding
aggregate for lifecycle invariants, not for grouping same pattern across files)

**Problem**: `DecisionPacketRecord` wraps exactly one `FindingRecord`. When 7
files have the same `dict_as_struct` problem, the AI receives 7 separate
per-file instructions instead of one architectural recommendation. There is no
field for `related_finding_ids`, no aggregation by `check_id` across files, and
no mechanism to say "fix these together as one coherent change."

**Root cause**: `decision_packet_from_finding()` in `finding_contracts.py`
takes one finding and produces one packet. Hotspots aggregate by file, not by
pattern. `bounded_next_slice` emits file-scoped instructions.

**Evidence**: `AllowlistEntry.matches()` in `decision_packets.py:256` is a
one-to-one match (file + symbol + probe). No grouping logic exists.

**What would close it**: Add a pattern-aggregation layer that groups findings
with the same `check_id` across files into one architectural recommendation
with a unified fix strategy. Add `related_finding_ids` field to
`DecisionPacketRecord` or create a new `ArchitecturalRecommendation` aggregate.

---

## ISS-006: Autonomy loop has no baseline comparison — only round-to-round delta

**Severity**: medium
**Category**: measurement_gap
**Status**: open
**Plan ref**: review_probes.md:280 (unchecked), MASTER_PLAN:3649 (unchecked)

**Problem**: The autonomy loop's feedback system (`run_feedback.py:224-244`)
tracks `unresolved_count` from round N vs round N-1. It does not compare to the
baseline state when the loop started. This means the loop cannot answer "did we
actually fix anything overall?" — only "did the last round help?"

**Root cause**: `run_feedback.py` stores `last_unresolved_total` in transient
state but does not persist or compare to `initial_unresolved_total`.

**Evidence**: There is no `initial_unresolved_total` or `baseline_quality_score`
field in the autonomy loop state.

**What would close it**: Capture `initial_unresolved_total` and
`initial_quality_score` at loop start. Compare final state to initial state at
loop end. Report the actual net delta.

---

## ISS-007: Guard-run re-scans only changed files — not affected neighbors

**Severity**: high
**Category**: verification_gap
**Status**: open
**Plan ref**: NOT TRACKED in any active plan checklist.

**Problem**: After AI applies a fix, `guard_run.py` runs probes only on files
that appear in the git diff. If code was moved from `file_a.py` to
`file_b.py`, both files might be scanned — but files that IMPORT from
`file_a.py` or `file_b.py` are not re-scanned. A fix that breaks a consumer
is not detected until the next full probe run.

**Root cause**: The probe gate (`watchdog/probe_gate.py`) calls
`run_probe_report.py` which passes `--since-ref` to limit scanning to changed
files. No import-graph expansion is done.

**Evidence**: `run_probe_report.py:36-64` builds probe commands with
`--since-ref` / `--head-ref` flags that restrict scanning scope.

**What would close it**: After identifying changed files, expand the scan set
to include direct importers of those files (one hop in the import graph). The
context graph already tracks import edges — use them.

---

## ISS-008: "Rule gaming" recognized in plans but has no automated enforcement

**Severity**: medium
**Category**: enforcement_gap
**Status**: open
**Plan ref**: ai_governance_platform:917 (recognized as failure pattern, no
enforcement checklist item)

**Problem**: `ai_governance_platform.md:917` identifies "rule gaming" as a
known AI failure pattern: "changes that technically satisfy the rule but do not
improve readability, maintainability, or safe follow-up edits." No guard, probe,
or automated check detects this pattern. It relies on human review.

**Root cause**: Rule gaming is a semantic quality judgment that is harder to
detect structurally than syntactic patterns. The system detects code shape
violations but not whether a "fix" actually improved the underlying quality.

**Evidence**: The `probe_single_use_helpers` fixes in governance review rows
8-10 demonstrate rule gaming: helpers were moved between files three times for
the same finding, each time satisfying the probe without addressing the
architectural concern.

**What would close it**: Combine ISS-003 (post-fix re-verification) with
ISS-004 (improvement tracker in autonomy loop) to detect fixes that pass probes
without improving quality scores. If quality delta is zero or negative after a
"fix," flag as potential rule gaming.

---

## ISS-009: probe_topology_builder recomputes metrics that graph already has

**Severity**: low
**Category**: duplication
**Status**: open
**Plan ref**: ai_governance_platform:3211 (partial — mentions topology-scan
hygiene but not deduplication between probe topology and context graph)

**Problem**: `probe_topology_builder.py:205-206` calls
`collect_python_edges()` and `collect_rust_edges()` to compute fan_in/fan_out
from source. The context graph builder (`context_graph/builder.py`) does the
same computation and persists it to a snapshot. This is duplicated work that can
diverge if the two systems use different import-detection logic.

**Root cause**: The probe topology builder was written before or independently
of the context graph system. No integration was done afterward.

**What would close it**: Have `probe_topology_builder.py` load the latest
context graph snapshot and use its fan_in/fan_out values. Fall back to local
computation only if no snapshot exists.

---

## ISS-010: validation_plan field on DecisionPacketRecord is never executed

**Severity**: high
**Category**: dead_code
**Status**: open
**Plan ref**: platform_authority_loop:842-845 (unchecked), platform_authority_loop:851
(unchecked) — both in Phase 5b.1 which has not started.

**Problem**: `DecisionPacketRecord` (in `finding_contracts.py:172`) has a
`validation_plan` field containing typed validation steps (e.g., "Run
check --profile ci"). This field is serialized to JSON output and rendered in
probe topology reports, but no code path ever executes the validation steps.
Guard-run does not read or run them. The autonomy loop does not check them.

**Root cause**: The field was added as part of the decision packet contract
design but execution was deferred.

**Evidence**: `grep -r "validation_plan" dev/scripts/devctl/commands/` returns
no hits in guard_run.py, autonomy_loop.py, or any execution path.

**What would close it**: Wire validation_plan execution into guard-run's
post-fix verification step. Before accepting a fix, run the exact validation
selectors specified in the finding's decision packet.

---

## ISS-011: Review channel event log (trace.ndjson) grows unbounded

**Severity**: high
**Category**: operational_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: The `trace.ndjson` event log is append-only with no pruning,
rotation, or TTL mechanism. `load_events()` in `event_store.py:82` reads the
entire file every time under an exclusive lock. Long-running sessions accumulate
unbounded event data.

**Root cause**: `append_event()` only appends. `reports_cleanup` does not
target event logs. `DEFAULT_PACKET_TTL_MINUTES = 30` only controls packet
expiry, not event cleanup.

**What would close it**: Add event log rotation or TTL-based pruning. Define a
retention policy for review channel events.

---

## ISS-012: Startup receipt file has no concurrent-write locking

**Severity**: high
**Category**: concurrency_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `write_startup_receipt()` in `startup_receipt.py:126` overwrites
the receipt file with `path.write_text()` — no `fcntl.flock()` or atomic
write. If two agents call `startup-context` concurrently, they race on the
same file. `startup_receipt_problems()` can read partial/corrupted state.

**Root cause**: The receipt writer does not use the same locking pattern as
`event_store.py` (which properly uses `fcntl.flock()`).

**What would close it**: Add file-level locking to `write_startup_receipt()`
matching the event store pattern, or use atomic write-then-rename.

---

## ISS-013: Silent fallback when governance scanning fails in review state locator

**Severity**: medium
**Category**: error_handling_gap
**Status**: open
**Plan ref**: PARTIAL — platform_authority_loop mentions startup fail-closed
behavior but `_resolve_governance()` silently swallowing errors is not named.

**Problem**: `_resolve_governance()` in `review_state_locator.py:203-217`
catches `ImportError` and `(OSError, ValueError)` from governance loading and
silently returns `None`. Callers proceed without governance context, potentially
using wrong defaults. No structured error is surfaced.

**What would close it**: Surface governance load failures as structured
warnings in the startup receipt. Distinguish "governance not yet loaded" from
"governance load failed."

---

## ISS-014: Push bypass policy not re-checked when push_decision is honored

**Severity**: medium
**Category**: enforcement_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: The push enforcement system checks `--skip-preflight` and
`--skip-post-push` CLI flags against bypass policy in `push.py:104-116`. But if
`startup_push_decision.py` recommends `run_devctl_push`, it does not re-verify
that bypass restrictions still hold at execution time.

**What would close it**: Re-check bypass policy at push execution time, not
just at decision time.

---

## ISS-015: Bridge file truncation not protected by file locking

**Severity**: medium
**Category**: concurrency_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `bridge_file.py:27` calls `handle.truncate()` without acquiring
an exclusive lock. A concurrent reader can see partial/corrupted bridge content.

**What would close it**: Add `fcntl.flock(LOCK_EX)` around bridge file
truncation and write operations.

---

## ISS-016: Push tests use heavy mocking that masks integration failures

**Severity**: low
**Category**: test_quality
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `test_push.py` mocks `_git_stdout` with hardcoded `side_effect`
sequences. If the real implementation changes git call order, the mock sequence
breaks silently. No integration test runs real git against a test repo.

**What would close it**: Add at least one integration test using
`tempfile.TemporaryDirectory()` + `git init` that exercises the real push flow.

---

## ISS-017: subprocess imported in domain/runtime layer

**Severity**: medium
**Category**: layer_violation
**Status**: open
**Plan ref**: PARTIAL — PYTHON_ARCHITECTURE.md:180 says "move subprocess/git
lookups out of inner runtime code" but no concrete checklist item names the
specific files.

**Problem**: `startup_receipt.py` (line 8) and `vcs.py` (line 5) in
`dev/scripts/devctl/runtime/` import `subprocess` directly. The runtime layer
is supposed to be infrastructure-free domain contracts. These modules perform
git operations via subprocess, coupling domain logic to the Python subprocess
API and making unit testing require mocking.

**What would close it**: Accept `head_commit_sha: str` as a parameter in
`startup_receipt.py` instead of computing it. Move `vcs.py` git operations
behind a `GitRunner(Protocol)` and inject from the composition root.

---

## ISS-018: finding_id hash uses unordered signals — non-deterministic identity risk

**Severity**: high
**Category**: identity_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `build_finding_id()` in `finding_contracts.py:90` joins
`seed.signals` with `"|"` to build the hash input. The signals tuple is
populated from violation metadata in the order they appear in the source dict.
If a guard or probe emits the same signals in a different order across runs,
the hash changes and the same logical finding gets a different `finding_id`.

**Root cause**: `signals` is a tuple (ordered) but populated from iteration
over dicts or lists whose order may vary between runs or Python versions.

**What would close it**: Sort `seed.signals` before joining for the hash, or
document that signal order is part of the identity contract and enforce it at
the creation site.

---

## ISS-019: Fix commands in autonomy loop have no subprocess timeout

**Severity**: critical
**Category**: deadlock_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `coderabbit_ralph_loop_core.py:82-87` calls `subprocess.run()`
for AI fix commands without a `timeout` parameter. If the fix command hangs
(infinite loop, network stall, deadlock), the subprocess blocks indefinitely.
The autonomy loop checks elapsed time only between rounds
(`autonomy_loop_rounds.py:59`), so a hung fix command consumes the entire loop
time budget with no early failure signal.

**Root cause**: The fix executor assumes CLI commands are well-behaved. The
`timeout_seconds` parameter in `execute_loop()` is only passed to GitHub API
polling functions, not to the fix subprocess itself.

**What would close it**: Add `timeout=<budget>` to the `subprocess.run()` call
in the fix executor. Catch `subprocess.TimeoutExpired` and convert to a
retryable error.

---

## ISS-020: No schema_version validation when loading review_state.json

**Severity**: medium
**Category**: compatibility_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `projection_bundle.py:78-79` writes `schema_version: 1` when
building review_state.json projections. No reader validates that the loaded
`schema_version` matches the expected version before using fields. If the
schema evolves, old readers silently use new schema or new readers silently use
old schema, leading to data corruption or misinterpreted state.

**What would close it**: Add schema_version validation to every reader of
review_state.json. Reject or warn on version mismatch.

---

## ISS-021: Review channel follow-loop does not handle SIGTERM for graceful shutdown

**Severity**: medium
**Category**: signal_handling_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `follow_loop.py:261` catches `KeyboardInterrupt` (Ctrl+C) and
records `stop_reason = "manual_stop"`. But SIGTERM (signal 15) — sent by
orchestration systems during graceful shutdown — is not caught. SIGTERM
immediately terminates the process without recording lifecycle state or emitting
final snapshots, leaving stale session artifacts and incomplete event logs.

**Root cause**: No `signal.signal(SIGTERM, handler)` registered. Only the
synchronous KeyboardInterrupt exception is handled.

**What would close it**: Register a SIGTERM handler in the follow-loop setup
that sets a shutdown flag, allowing the same cleanup path as KeyboardInterrupt.

---

## ISS-022: Autonomy loop timeout checks only at round boundaries — mid-round hangs undetected

**Severity**: medium
**Category**: operational_gap
**Status**: open
**Plan ref**: PARTIAL — autonomy_loop.py:70-74 mentions max_hours_hard_cap but
enforcement is between-round only, not within rounds.

**Problem**: `autonomy_loop_rounds.py:56-64` checks elapsed time only at the
START of each round. If triage-loop or a fix command hangs for 3 hours and
max_hours is 2, the loop silently waits the full 3 hours before detecting the
timeout. The outer `autonomy_swarm_core.py` applies a per-agent kill timeout
(line 90), but that is a last-resort kill, not an instructive early failure.

**What would close it**: Pass a deadline timestamp to triage-loop and fix
commands so they can abort early if they exceed their time budget.

---

## ISS-023: Telemetry exceptions caught broadly and swallowed silently

**Severity**: low
**Category**: error_handling_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `triage.py:96-101` catches `except Exception` in the telemetry
path, prints a warning to stderr, and continues. If `append_metric()` or
`append_failure_kb()` fails, the command returns 0/1 based on output only.
Operators cannot distinguish command success with metrics collected from silent
metric loss.

**What would close it**: Log telemetry failures as structured warnings in the
command report or startup signals so metric infrastructure problems are visible.

---

## ISS-024: Quality policy references script ID with inconsistent naming

**Severity**: low
**Category**: naming_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `quality_policy_defaults.py:73-76` registers `"compat_matrix_smoke"`
as a `QualityStepSpec` script_id. The actual file is
`dev/scripts/checks/compat_matrix_smoke.py` — without the standard `check_` or
`probe_` prefix. Every other guard uses `check_<name>.py` and every probe uses
`probe_<name>.py`. This inconsistency may cause script resolution issues if the
resolver tightens its naming conventions.

**What would close it**: Rename the file to `check_compat_matrix_smoke.py` or
add an explicit exception to the script resolver.

---

## ISS-025: Frozen dataclasses with mutable fields passed by reference

**Severity**: medium
**Category**: immutability_violation
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: Several frozen dataclasses in the governance export path contain
mutable fields (`list`, `dict`) that are passed by reference at construction,
not copied. External code holding a reference to the original mutable object can
modify the "frozen" dataclass's contents.

**Evidence**: In `export.py:70-71`:
```
copied_sources=list(result.copied_sources),     # Good — copies
generated_artifacts=result.generated_artifacts,  # Bad — passes reference
```

The `generated_artifacts` dict in `GovernanceExportPayload`,
`GovernanceExportResult`, and `SnapshotManifest` can be mutated after the
frozen dataclass is constructed.

**What would close it**: Use `tuple` instead of `list` and
`types.MappingProxyType` or `dict(...)` copy at construction sites. Or convert
mutable fields to immutable equivalents matching the repo's existing
`tuple[str, ...]` convention.

---

## ISS-026: Snapshot name sanitizer does not handle null bytes or shell metacharacters

**Severity**: low
**Category**: input_validation_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `_sanitize_snapshot_name()` in `governance_export_support.py:186-189`
prevents `/` path traversal but does not filter null bytes (`\x00`), backslash
sequences, or shell metacharacters (`;`, `|`, `&`). A name like
`"name\x00malicious"` becomes `"name malicious"` — the null byte is replaced
with a space but not rejected.

**What would close it**: Reject names containing control characters, null bytes,
or shell metacharacters. Use an allowlist of safe characters rather than a
blocklist of dangerous ones.

---

## ISS-027: Expired review-channel packets accumulate without removal

**Severity**: medium
**Category**: resource_leak
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `summarize_packets()` in `event_packet_rows.py:12-36` counts
expired packets (`stale_packet_count`) but never removes them from state.
Expired packets remain in `packets_by_id` and are included in output. Over
time, expired packets accumulate unbounded in memory and projections.

**What would close it**: Filter expired packets out of the output rows, or
archive them to a separate collection. Persist the expiry status so restarts
don't lose the count.

---

## ISS-028: ProjectGovernance accepts partial/broken payloads without validation

**Severity**: high
**Category**: validation_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `project_governance_from_mapping()` in
`project_governance_parse.py:129-189` creates ProjectGovernance objects without
validating that required fields exist. `coerce_mapping()` returns `{}` when
fields are missing, so a payload with no `repo_identity` or `path_roots`
silently creates a broken governance object with empty defaults instead of
failing.

**What would close it**: Validate that required fields (`schema_version`,
`contract_id`, `repo_identity`, `repo_pack`, `path_roots`) are present and
non-empty before constructing ProjectGovernance. Raise or return a structured
error on missing required fields.

---

## ISS-029: Work intake returns None with no error when no plan targets match

**Severity**: medium
**Category**: error_handling_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `select_active_plan_entry()` in `work_intake_selection.py:27-52`
returns `None` when `governance.plan_registry.entries` is empty. Callers like
`build_work_intake_packet()` pass this None through to `build_target_ref()`
which also returns None. The resulting `WorkIntakePacket` has
`active_target=None` with no error logged or structured fallback documented.

**What would close it**: Log a structured warning when no plan target matches.
Set `WorkIntakePacket.fallback_reason` to a specific value like
`"no_plan_targets_found"` so startup-context can surface it.

---

## ISS-030: Operator console polling reads files without synchronization against devctl writes

**Severity**: medium
**Category**: concurrency_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: The PyQt6 operator console polls every 2 seconds via QTimer
(`main_window.py:532-535`). Each tick reads bridge snapshots, session traces,
and job states via `build_operator_console_snapshot()`. devctl commands write
to these same files concurrently without file locking. The UI may see
torn/partial reads or inconsistent state across multiple files read in sequence.

**What would close it**: Use atomic write-then-rename for devctl report output,
or add read-side locking in the operator console. At minimum, catch JSON parse
errors gracefully and retry on the next poll.

---

## ISS-031: Python version mismatch — requires-python says 3.9 but code uses 3.10+ syntax

**Severity**: high
**Category**: compatibility_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `pypi/pyproject.toml:10` declares `requires-python = ">=3.9"` but
the codebase uses `X | Y` union type syntax (Python 3.10+) in 50+ files.
Examples: `token_cap: int | None = None` in `swarm_helpers.py:219`,
`str | dict` patterns in `app/operator_console/state/core/models.py`. This
code will fail with `TypeError` on Python 3.9.

**What would close it**: Either raise `requires-python` to `">=3.10"` or
replace all `X | Y` annotations with `Optional[X]` / `Union[X, Y]` from
typing. Given the scope (50+ files), raising the version requirement is the
pragmatic fix.

---

## ISS-032: Autonomy swarm agents may collide writing to shared directories

**Severity**: high
**Category**: concurrency_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: When multiple swarm agents run in parallel via
`ThreadPoolExecutor` in `autonomy_swarm.py:67`, they write to shared
checkpoint, report, and queue directories. Directory creation uses
`mkdir(parents=True, exist_ok=True)` but file writes (JSON reports, summaries)
have no locking. Concurrent writes to the same summary files can corrupt data.

**Evidence**: `autonomy_swarm.py:257-258` shows multiple agents may write to
the same `summary.json`/`summary.md` when agent count > 1.

**What would close it**: Give each agent a unique subdirectory within the swarm
run directory, or add file-level locking on shared output files.

---

## ISS-033: Autonomy loop checkpoint writes not validated — silent data loss on disk failure

**Severity**: medium
**Category**: data_integrity_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `run_controller_rounds()` in `autonomy_loop_rounds.py:70-73`
creates round directories and writes multiple JSON checkpoint files without
validating that writes succeeded. If disk is full or permissions fail, the
round number increments and subsequent rounds proceed, but checkpoint data is
lost. The caller processes `round_results` without verifying file integrity.

**What would close it**: Validate that checkpoint JSON files were written
successfully (e.g., read-back verification or fsync). On write failure, mark
the round as `checkpoint_failed` instead of silently proceeding.

---

## ISS-034: Duplicate finding_ids in governance ledger with conflicting verdicts

**Severity**: high
**Category**: data_integrity_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `finding_reviews.jsonl` has 7 finding_ids that appear multiple
times with different verdicts (e.g., `357250ed5ef0d2b0` appears 3 times:
deferred, deferred, fixed). `latest_rows_by_finding()` deduplicates by keeping
only the last row, silently dropping earlier verdict history. No audit trail of
verdict changes is preserved. `append_governance_review_row()` does not check
for existing entries before appending.

**What would close it**: Add `previous_verdict` and `change_reason` fields to
verdict update rows. Or use a ledger with version numbers and an index file.

---

## ISS-035: Probe report artifacts written non-atomically — crash leaves partial state

**Severity**: high
**Category**: data_integrity_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `write_probe_artifacts()` in `probe_report_artifacts.py:27-96`
writes 8 files sequentially into the `latest/` directory without atomicity. If
the process crashes after file 3, the directory contains partial/stale data.
Consumers reading `latest/` may get inconsistent state.

**What would close it**: Write to a temporary staging directory, then
atomically rename to `latest/` when all files are complete.

---

## ISS-036: graph_snapshots directory never cleaned — 947 MB and growing

**Severity**: medium
**Category**: operational_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `dev/reports/graph_snapshots/` contains 134 files totaling ~947 MB
and is NOT in `reports_retention.py:MANAGED_REPORT_SUBROOTS`. The retention
policy only manages autonomy runs, benchmarks, experiments, library, and
failures. Graph snapshots, data_science, probes, and review_channel reports
grow unbounded.

**What would close it**: Add graph_snapshots (and other large report dirs) to
`MANAGED_REPORT_SUBROOTS` with appropriate retention policy.

---

## ISS-037: Config files use inconsistent version field names

**Severity**: low
**Category**: schema_inconsistency
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `mcp_tools_allowlist.json` uses `"version": "1"` (string),
`naming_glossary.json` uses `"version": 1` (integer), while the standard
across runtime contracts is `"schema_version": 1`. Inconsistent naming makes
schema evolution fragile.

**What would close it**: Standardize on `schema_version` (integer) across all
config files.

---

## ISS-038: devctl_repo_policy.json has undocumented fields read by code

**Severity**: medium
**Category**: schema_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `devctl_repo_policy.json` contains fields (`protocol_boundary`,
`quality_scopes`, `ai_guard_overrides`) that are read by Python code but have
no schema definition, no JSON Schema, and no documentation. Fields can be
added/removed without version bumping or validation.

**What would close it**: Define a JSON Schema for devctl_repo_policy.json.
Validate the payload against it during `startup-context`.

---

## ISS-039: Event reducer continues past malformed events — silent state loss

**Severity**: medium
**Category**: error_handling_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `reduce_events()` in `event_reducer.py:210-248` handles orphaned
transition events (e.g., `packet_acked` before `packet_posted`) by appending
an error string and continuing. The result is an incomplete but `ok=True` state
because errors are collected but don't prevent partial replay.

**What would close it**: Distinguish between recoverable out-of-order events
and actual corruption. Flag the result as `degraded=True` when orphaned events
are skipped so consumers know the state may be incomplete.

---

## ISS-040: Event ID format overflows at 10,000 events

**Severity**: low
**Category**: format_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `next_event_id()` in `event_store.py:232-249` uses
`rev_evt_{:04d}` format. At 10,000 events the format becomes
`rev_evt_10000` (5 digits), breaking the 4-digit padding. Consumers expecting
exactly 4 digits after the prefix will misbehave.

**What would close it**: Use a wider format (e.g., `{:06d}`) or switch to a
different ID scheme (UUID, timestamp-based).

---

## ISS-041: Hardcoded agent IDs in event reducer — not extensible

**Severity**: medium
**Category**: extensibility_gap
**Status**: open
**Plan ref**: PARTIAL — MASTER_PLAN mentions N-agent follow-up but event
reducer hardcoding is not named.

**Problem**: `event_reducer.py:207` initializes
`provider_state = {"codex": {}, "claude": {}, "cursor": {}, "operator": {}}`.
`_build_agents()` loops over `("codex", "claude", "cursor", "operator")`.
Adding a new agent (e.g., "gemini") requires code changes in multiple files.
Packets to/from unknown agents are silently dropped.

**What would close it**: Derive agent IDs from the event log or agent registry
instead of hardcoding them. Initialize `provider_state` dynamically from
observed events.

---

## ISS-042: No bridge vs event state reconciliation or conflict detection

**Severity**: high
**Category**: state_drift
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: Bridge-backed state (from `bridge.md`) and event-backed state
(from `trace.ndjson`) can disagree about current status. The bridge may show
"Claude: working on X" while review_state.json shows "claude: idle" (if packets
expired). No code validates consistency between them or alerts the operator to
divergence.

**What would close it**: Add a reconciliation check that compares bridge
liveness with event-backed state. Emit a structured warning when they disagree.

---

## ISS-043: Daemon heartbeat staleness never checked against time

**Severity**: medium
**Category**: dead_code
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `append_daemon_heartbeat()` writes heartbeat events to
trace.ndjson. `daemon_reducer.py` stores them in review_state. But nothing
compares `last_heartbeat_utc` to current time to flag a daemon as stale.
`DaemonSnapshot.running` checks `pid` and `stop_reason` but NOT heartbeat
freshness. A crashed daemon with no stop event stays marked "running."

**What would close it**: Add a staleness check: if
`now - last_heartbeat_utc > threshold`, mark daemon as `stale` regardless of
`stop_reason`.

---

## ISS-044: Daemon client callback list grows unbounded (memory leak)

**Severity**: medium
**Category**: resource_leak
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `DaemonClient._event_callbacks` in
`app/operator_console/collaboration/daemon_client.py:70-72` is an append-only
list. No `off_event()` method exists. Reconnections or re-registrations
accumulate callbacks that execute multiple times per event.

**What would close it**: Add `off_event(callback)`. Clear callbacks on
`disconnect()`. Consider `weakref.WeakSet`.

---

## ISS-045: Hardcoded ".voiceterm" paths in operator console

**Severity**: medium
**Category**: portability_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `DEFAULT_SOCKET_PATH = Path.home() / ".voiceterm" / "control.sock"`
and `CUSTOM_THEMES_DIR = Path.home() / ".voiceterm" / "themes"` are hardcoded
in daemon_client.py:29 and theme_engine.py:49. Cannot be configured for
different product names.

**What would close it**: Extract to `OperatorConsolePathConfig` or accept via
environment variable / constructor parameter.

---

## ISS-046: Daemon JSON event parsing has no error recovery

**Severity**: medium
**Category**: error_handling_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `DaemonEvent.from_json(line)` calls `json.loads(line)` without
try/except. A malformed JSON line from the daemon breaks the entire event
stream. The `read_one_event()` method recurses on empty lines with no depth
limit.

**What would close it**: Wrap `json.loads()` in try/except and skip/log
malformed lines. Replace recursion with a loop.

---

## ISS-047: Unix daemon socket created without restricted permissions

**Severity**: critical
**Category**: security
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `UnixListener::bind()` in `rust/src/bin/voiceterm/daemon/run.rs:72`
creates the control socket at `~/.voiceterm/control.sock` without explicit
permission restrictions. Default umask may allow any local user to connect and
send commands (spawn agents, read output, kill sessions).

**What would close it**: Set socket permissions to `0o600` after bind. Or use
`fchmod` on the socket fd before accepting connections.

---

## ISS-048: Predictable temp file paths — symlink attack risk

**Severity**: high
**Category**: security
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: Multiple modules use predictable temp paths:
- `triage/loop_support.py:46`: `/tmp/devctl-triage-loop-master-plan-proposal.md`
- `rust_audit/render.py:17,21`: `/tmp/voiceterm-mpl`, `/tmp/voiceterm-cache`

These are written without checking for existing symlinks. An attacker could
create a symlink at the predictable path pointing to a sensitive file, causing
devctl to overwrite it.

**What would close it**: Use `tempfile.mkdtemp()` or `tempfile.NamedTemporaryFile()`
instead of hardcoded paths. Never write to predictable locations in `/tmp/`.

---

## ISS-049: WebSocket bridge binds to 0.0.0.0 — network-accessible

**Severity**: medium
**Category**: security
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: WebSocket bridge in `daemon/run.rs:89` listens on `0.0.0.0:9876`
(default), making it accessible from the network. No documented authentication
model for the WebSocket protocol.

**What would close it**: Bind to `127.0.0.1` by default. Add authentication
token validation for WebSocket connections.

---

## ISS-050: Production unwrap() calls in Rust can panic

**Severity**: high
**Category**: crash_risk
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: Several production (non-test) Rust files use `unwrap()` on paths
that can fail:
- `memory/governance.rs:275`: `dir.to_str().unwrap()` — panics on non-UTF-8
- `memory/ingest.rs:807`: `writer.flush().unwrap()` — panics on I/O error
- `banner.rs:687`: `lines.iter().find(...).unwrap()` — panics if logo missing

**What would close it**: Replace with `?` operator or `expect()` with context
message. Return `Result` from these functions.

---

## ISS-051: Voice job Drop timeout leaks microphone resource

**Severity**: medium
**Category**: resource_leak
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `VoiceJob::Drop` in `voice.rs:55-72` sets `stop_flag` and waits
200ms for the worker thread. If the thread is blocked in a system call (waiting
for mic input), it detaches but is NOT killed. The thread keeps the microphone
open, causing the next capture to fail.

**What would close it**: Use a cancellation token or explicitly close the audio
device before waiting for the thread.

---

## ISS-052: startup_advisory_decision.py has zero unit tests (311 lines, 5 branches)

**Severity**: critical
**Category**: test_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `startup_advisory_decision.py` (311 lines) controls which advisory
action is returned at session start (continue_editing, await_review,
checkpoint_before_continue, etc.). It has 5 major decision branches and ZERO
dedicated unit tests. Only smoke-tested via `test_startup_context.py` which
mocks governance. A change to any branch condition would ship undetected.

**What would close it**: Add dedicated contract tests for each decision branch
with minimal governance fixtures, following the `test_finding_contracts.py`
pattern.

---

## ISS-053: startup_push_decision.py has zero unit tests (342 lines, 4 branches)

**Severity**: critical
**Category**: test_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `startup_push_decision.py` (342 lines) gates whether
`devctl push --execute` is safe. 4 major decision branches. ZERO dedicated
unit tests. Only mocked in `test_startup_context.py`. A regression in
`_local_readiness_decision()` or `_review_state_decision()` would allow
unauthorized pushes or block legitimate ones.

**What would close it**: Add TDD-style contract tests for each push decision
path.

---

## ISS-054: project_governance_parse.py deserialization untested (209 lines, 10+ helpers)

**Severity**: high
**Category**: test_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: 10+ deserialization helpers (`repo_identity_from_mapping()`,
`path_roots_from_mapping()`, etc.) have ZERO individual unit tests. Only the
happy-path full-payload test exists. Silent coercion behavior (missing fields →
empty defaults) is completely unvalidated.

**What would close it**: Add unit tests for each `*_from_mapping()` function
with missing fields, wrong types, and empty payloads.

---

## ISS-055: 19 of 28 probe scripts have only single-case smoke test coverage

**Severity**: high
**Category**: test_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: Probes like `probe_cognitive_complexity`, `probe_fan_out`,
`probe_identifier_density`, `probe_blank_line_frequency` have 50-300 lines of
AST traversal and threshold logic but only 1 smoke test case each. No tests
for boundary conditions (exactly at threshold), empty files, pathological
inputs, or false positive cases. A threshold change (e.g., `>20` to `>=20`)
would only be caught if the one smoke case happens to be at that boundary.

**What would close it**: Add boundary-condition tests for each probe's
threshold values.

---

## ISS-056: Governance review --record has zero negative input tests

**Severity**: high
**Category**: test_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `test_governance_review.py` tests valid inputs but has ZERO tests
for invalid enum values, malicious line numbers, path traversal in `--path`,
duplicate finding_ids, corrupt JSONL in existing log, or schema version
mismatches. The `require_choice()` validation would raise ValueError but no
test asserts this.

**What would close it**: Add negative tests for each enum field, boundary
values, and corrupt input conditions.

---

## ISS-057: Hardcoded VoiceTerm paths in 10+ guard scripts break portability

**Severity**: high
**Category**: portability_gap
**Status**: open
**Plan ref**: PARTIAL — platform_authority_loop Phase 2 mentions removing
VoiceTerm fallbacks but doesn't name specific guard scripts.

**Problem**: `check_release_version_parity.py` assumes
`pypi/src/voiceterm/__init__.py`. `check_naming_consistency.py` assumes
`rust/src/bin/voiceterm/runtime_compat.rs`. `check_router_constants.py`
hardcodes `--bin voiceterm`. `code_shape_function_exceptions.py` has 395 lines
of VoiceTerm-specific path exceptions. These guards crash or produce wrong
results on non-VoiceTerm repos.

**What would close it**: Move repo-specific paths into `devctl_repo_policy.json`
guard overrides. Have guards read their target paths from policy, not from
hardcoded constants.

---

## ISS-058: Unguarded git push in rust_ci.yml — race condition on badge updates

**Severity**: medium
**Category**: ci_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `rust_ci.yml:294` does `git push` for badge updates without error
handling. Concurrent CI runs can race on pushing. Compare to
`mutation-testing.yml:143-146` which properly handles non-fast-forward with
`git push || { echo "..."; exit 0 }`.

**What would close it**: Add the same `|| exit 0` fallback as mutation-testing,
or use a separate bot-owned branch for badge updates.

---

## ISS-059: Release workflows missing secret validation step

**Severity**: medium
**Category**: ci_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `publish_release_binaries.yml` and `release_attestation.yml` have
no secret validation step. `publish_pypi.yml` and `publish_homebrew.yml`
properly validate their secrets before use. Missing validation means mid-run
failures with unclear error messages.

**What would close it**: Add a pre-job step that validates required secrets are
configured, matching the pattern in publish_pypi.yml:89-97.

---

## ISS-060: Oversized functions in runtime/governance exceed 150-line guard limit without exceptions

**Severity**: high
**Category**: code_shape_violation
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: Several functions exceed the 150-line Python limit and are NOT
listed in `code_shape_function_exceptions.py`:
- `derive_push_decision` in `startup_push_decision.py` (~270 lines)
- `derive_advisory_decision` in `startup_advisory_decision.py` (~284 lines)
- `scan_governed_docs_for_layout` in `doc_authority_support.py` (~255 lines)
- `evaluate_surface` in `surface_runtime.py` (~217 lines)
- `build_surface_generation_governance` in `bootstrap_surfaces.py` (~177 lines)

**What would close it**: Either add time-bound exceptions or decompose into
smaller functions. These are decision-critical functions that should be
testable per-branch.

---

## ISS-061: Governance layer imports from commands layer (layer violation)

**Severity**: medium
**Category**: layer_violation
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `governance/surface_context.py:27` imports
`from ..commands.check_router_constants import resolve_check_router_config`.
The governance layer should not depend on the commands layer. This creates
circular dependency risk and tight coupling.

**What would close it**: Move `resolve_check_router_config` into the governance
or runtime layer, or extract the shared logic into a neutral module.

---

## ISS-062: TypedDict payloads use total=False for all fields — required fields not enforced

**Severity**: medium
**Category**: type_safety_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `FindingPayload` (23 fields) and `DecisionPacketPayload` (25
fields) in `finding_payload_contracts.py` use `total=False`, making ALL fields
optional. Fields like `schema_version`, `contract_id`, `finding_id` should be
required. Type checkers won't catch missing mandatory fields.

**What would close it**: Use `Required[]` / `NotRequired[]` annotations
(Python 3.11+) or split into a required base + optional extension.

---

## ISS-063: coerce_int() returns 0 on failure instead of None — masks missing data

**Severity**: medium
**Category**: silent_coercion
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `coerce_int()` in `value_coercion.py:27-31` returns `0` when
coercion fails. Callers expecting `None` for missing values get `0` instead.
Code like `if findings_count:` evaluates False for both "missing" and "zero
findings" — indistinguishable.

**What would close it**: Add `coerce_int_or_none()` that returns `int | None`.
Use it where missing-vs-zero distinction matters.

---

## ISS-064: JSON output contaminated by stderr telemetry warnings

**Severity**: medium
**Category**: output_corruption
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: Commands like `devctl status`, `devctl report`, `devctl triage`
print telemetry warnings to stderr even when `--format json` is requested.
Machine consumers parsing stdout+stderr get corrupted output.

**What would close it**: Guard stderr warnings with format check:
`if args.format != "json": print(..., file=sys.stderr)`.

---

## ISS-065: Probe scripts read files without specifying encoding — UnicodeDecodeError risk

**Severity**: medium
**Category**: encoding_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: Three probe-related files use `Path.read_text()` without
`encoding="utf-8"`:
- `probe_report_render.py:37`
- `probe_report/support.py:37`
- `probe_report/decision_packets.py:223`

Will fail with UnicodeDecodeError on non-UTF-8 files in system-default encoding
environments.

**What would close it**: Add `encoding="utf-8"` to all `read_text()` calls in
the checks layer.

---

## ISS-066: Probe thresholds scattered across 15+ scripts instead of centralized

**Severity**: medium
**Category**: configuration_sprawl
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: Each probe script defines its own thresholds as module-level
constants (e.g., `BOOL_PARAM_MEDIUM=3`, `CLONE_MEDIUM=5`, `DICT_KEY_HIGH=8`).
15+ scripts each have independent threshold definitions. Changing policy
requires editing each file individually. Inconsistent with
`code_shape_policy.py` which centralizes shape thresholds.

**What would close it**: Centralize probe thresholds in a
`probe_threshold_policy.py` or extend `code_shape_policy.py` to cover probes.

---

## ISS-067: check_mutation_score.py exits non-zero on internal JSON errors

**Severity**: medium
**Category**: false_failure
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `check_mutation_score.py:181` calls `read_counts(path)` which does
`json.load()` without try/except. A malformed `outcomes.json` causes exit
code 2 (internal error), which CI treats as a guard violation rather than an
infrastructure failure.

**What would close it**: Wrap JSON parsing in try/except and distinguish
between "violations found" (exit 1) and "infrastructure failure" (exit 2 with
structured error).

---

## ISS-068: No max_agents policy hard cap in autonomy swarm

**Severity**: high
**Category**: enforcement_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `control_plane_policy.json` has hard caps for `max_rounds`,
`max_hours`, and `max_tasks` in the autonomy loop, but NO `max_agents_hard_cap`
for the swarm. The `--max-agents` CLI flag is accepted without policy
validation. The feedback sizing system can upshift agents to the configured max
without policy override.

**What would close it**: Add `max_agents_hard_cap` to
`control_plane_policy.json` and validate in `autonomy_swarm_core.py`.

---

## ISS-069: GitHub API rate limit exhaustion not detected in triage loop preflight

**Severity**: medium
**Category**: integration_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `preflight_github_connectivity()` in `triage/loop_support.py:53-66`
runs `gh api rate_limit` and checks exit code. But a 403 rate-limit response
from GitHub returns exit code 0 with `"remaining": 0` in the JSON body. The
preflight treats this as "connectivity OK" and proceeds to `execute_loop()`
which will fail mid-run with no recovery strategy.

**What would close it**: Parse the rate_limit response JSON and check
`remaining > 0` before proceeding.

---

## ISS-070: Autonomy loop has no PID/lock file for concurrent instance prevention

**Severity**: high
**Category**: concurrency_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: The autonomy-loop command can be started multiple times
simultaneously. Unlike the review-channel which has `lifecycle_state.py` with
PID checking, the autonomy loop has no PID file, no lock file, and no
"already running" detection. Multiple instances race on phone status, packet
writes, and shared queue directories.

**What would close it**: Add a PID file at `dev/reports/autonomy/.pid` and
check at startup. Abort if another instance is alive.

---

## ISS-071: Feedback sizing oscillation when min_agents blocks downshift

**Severity**: medium
**Category**: logic_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: In `run_feedback.py:275-282`, when `stall_streak >= stall_rounds`
triggers a downshift but `next_agents == current_agents` (because
`current_agents == min_agents`), the `stall_streak` counter is never reset.
Each subsequent cycle re-triggers the downshift, gets blocked by min_agents,
and increments stall_streak indefinitely — a permanent "triggered but blocked"
state.

**What would close it**: Reset `stall_streak` when downshift is blocked by
min_agents floor, since the system has already acknowledged the stall.

---

## ISS-072: Phone status not written on mid-round autonomy loop crash

**Severity**: medium
**Category**: observability_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: In `autonomy_loop_rounds.py:56-228`, phone status is built AFTER
triage and packet completion (line 141). If the loop crashes between triage
start (line 93) and phone status write, operators see stale phone status with
no indication that a crash occurred.

**What would close it**: Write a "round_started" phone status at the beginning
of each round, then update to "round_completed" or "round_failed" at the end.

---

## ISS-073: Slack webhook URL accepted without validation

**Severity**: medium
**Category**: security
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `notifications.py:14-43` in `integrations/ci-cd-hub/` accepts
webhook URLs from environment variables and sends POST requests without
validating the URL format. No rate limiting, no TLS verification override, and
error messages may expose the webhook URL.

**What would close it**: Validate webhook URLs against an allowlist (e.g.,
must start with `https://hooks.slack.com/`). Redact URL from error messages.

---

## ISS-074: probe_report_render.py reads stdin without timeout — can hang CI

**Severity**: medium
**Category**: availability_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `probe_report_render.py:37` calls `sys.stdin.read()` when no
input file is provided. In CI, if stdin is not properly closed, the process
hangs indefinitely. No timeout or signal handler.

**What would close it**: Add `signal.alarm()` timeout or a `--stdin-timeout`
flag.

---

## ISS-075: Terminal session launch has unhandled CalledProcessError

**Severity**: medium
**Category**: error_handling_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `launch_terminal_sessions()` in
`review_channel/terminal_app.py:118-121` calls `subprocess.run()` with
`check=True` in a loop without try/except. If osascript fails (permissions,
terminal not available), CalledProcessError crashes the entire session launch.

**What would close it**: Wrap in try/except CalledProcessError and log a
warning per failed session instead of crashing the loop.

---

## ISS-076: ralph_guardrails.json loaded without JSON error handling

**Severity**: medium
**Category**: error_handling_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `load_guardrails_config()` in `ralph_guardrail_report.py:31` calls
`json.load(fh)` without try/except. A syntax error in the guardrails config
crashes the ralph AI fix loop.

**What would close it**: Wrap in try/except JSONDecodeError and return safe
defaults on parse failure.

---

## ISS-077: Workflow bridge validators have no maximum bounds

**Severity**: medium
**Category**: validation_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `validate_positive_int()` and `validate_decimal_hours()` in
`workflow_bridge/common.py:34-47` enforce minimum values but have no maximum
bounds. A user can set `--max-hours=9999999` which passes validation. The
autonomy loop's hard caps catch this later, but the workflow bridge accepts
and propagates unreasonable values.

**What would close it**: Add maximum bounds matching the policy hard caps.

---

## ISS-078: Quality preset extension silently ignores missing preset files

**Severity**: medium
**Category**: silent_failure
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `_resolve_extended_policy_path()` in `quality_policy_loader.py:19-33`
returns a path to a non-existent preset file without warning. A repo with
`extends: ["quality_presets/portable_python.json"]` silently skips the preset
if the file is missing, producing a policy with none of the intended guards.

**What would close it**: Log a structured warning or error when an extended
preset file is not found.

---

## ISS-079: Data science snapshot writes are not atomic

**Severity**: medium
**Category**: data_integrity_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `run_data_science_snapshot()` in `data_science/metrics.py:160-164`
writes `summary.json`, `summary.md`, and appends to `snapshots.jsonl`
sequentially without atomicity. A crash after the first write leaves
inconsistent state. Same pattern as ISS-035 (probe reports) but in a different
subsystem.

**What would close it**: Write to staging directory, then atomic rename.

---

## ISS-080: improvement_tracker does not validate previous snapshot structure

**Severity**: medium
**Category**: validation_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `compute_improvement_delta()` in `improvement_tracker.py:30-42`
accesses nested fields of `previous_snapshot` without validating the expected
structure. If a corrupted snapshot has `maintainability_score` as a string
instead of a dict, `(previous_snapshot.get("maintainability_score") or {}).get("overall", 0.0)`
will silently produce `0.0` instead of the real previous score, making the
delta nonsensical.

**What would close it**: Validate that previous_snapshot has the expected
schema before computing deltas. Return `degraded=True` on schema mismatch.

---

## ISS-081: quality_backlog git subprocess raises unhandled RuntimeError

**Severity**: medium
**Category**: error_handling_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `_run_git_lines()` in `quality_backlog/collect.py:30-40` raises
`RuntimeError` on non-zero git exit code. Callers like
`collect_source_inventory()` and `run_json_check()` do not catch this exception.
An unexpected git failure (permissions, corrupt repo) crashes quality backlog
collection.

**What would close it**: Catch RuntimeError in callers and return empty/partial
results with a structured warning.

---

## ISS-082: context_graph hardcodes bridge.md path instead of consulting ProjectGovernance

**Severity**: medium
**Category**: portability_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `_detect_bridge_liveness()` in `context_graph/query.py:205`
hardcodes `bridge_path = repo_root / "bridge.md"` instead of reading the
configured bridge path from ProjectGovernance. AGENTS.md explicitly says "do
not hardcode bridge.md as universal truth; resolve through ProjectGovernance."
Repos with a non-standard bridge path will get incomplete bootstrap context.

**What would close it**: Read bridge_path from ProjectGovernance's
`bridge_config` field. Fall back to `bridge.md` only when no governance is
available.

---

## ISS-083: check_agents_contract.py has O(n*m) regex performance on AGENTS.md

**Severity**: medium
**Category**: performance_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `check_agents_contract.py:121-124` runs `re.search()` 68 times
(once per REQUIRED_COMMANDS entry) on the full ~2000-line AGENTS.md text. As
AGENTS.md grows, this becomes progressively slower and could cause CI timeouts.

**What would close it**: Build one compiled regex with all 68 commands as
alternatives, or scan the file once building a set of found tokens.

---

## ISS-084: Multiple checks load entire large files into memory for repeated linear searches

**Severity**: medium
**Category**: performance_gap
**Status**: open
**Plan ref**: NOT TRACKED

**Problem**: `sync_report.py:193,252,263` and `check_agents_contract.py:112`
load entire markdown files via `.read_text()` and perform multiple `in` or
`re.search()` operations on the full text. If spec files grow beyond 50MB this
becomes a memory and performance issue.

**What would close it**: Use line-by-line scanning or build an index of markers
on first pass instead of repeated full-text searches.
