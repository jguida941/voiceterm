# A Repo-Local Governance Compiler for Probabilistic Coding Agents

## Evidence Document — codex-voice / VoiceTerm

**Author**: Justin Guida
**Repository**: codex-voice (VoiceTerm)
**Date**: 2026-03-27
**Codebase**: ~87K LOC Rust, ~191K LOC Python tooling, 64 hard guards, 25 review probes

All code citations reference files within this repository. Every file path,
line number, and code snippet is verifiable against the current codebase.

---

## 1. Thesis Statement

This system implements a **repo-local governance compiler for probabilistic
coding agents**. The core principle is:

> Don't trust a probabilistic system with execution authority when execution
> authority can be compiled from repo evidence and policy. The model can search,
> draft, and repair, but the repo-owned deterministic layer decides what is
> admissible.

The system unifies five fields — security, CI/CD, static analysis, compiler
design, and agent orchestration — under one architectural model:

```
repo + plan + policy          = source language
typed governance objects      = intermediate representation (IR)
guards / probes / router      = analysis passes
approved shell/git/push ops   = code generation
receipts / findings / traces  = runtime evidence
```

This is not a metaphor. The code implements each compiler phase with typed
frozen dataclasses, deterministic transfer functions, fail-closed invariants,
conservative approximation, and fixpoint-based convergence detection.

The critical distinction: **this is not a governed repo — it is a system that
can govern arbitrary repos.** VoiceTerm is the first consumer, not the product.
The governance engine is portable: given an arbitrary repository, it compiles a
repo-local governance envelope from that repo's files, manifests, paths, policy,
and plan surfaces, then lets AI operate inside that compiled envelope. The
repo-specific part is derived at setup time through capability detection,
preset selection, and governance scanning — not hardcoded.

This is proven by a 13-repo pilot (311 findings across 13 repositories, 0 scan
errors) where the same engine ran on diverse codebases (Python, Java, Rust)
with zero engine modifications.

---

## 2. Compiler Architecture: Four Phases

### 2.1 Frontend — Signal Extraction

The frontend scans concrete repo state (git, filesystem, configs) and emits
typed signal structures.

**Primary scanner**: `scan_repo_governance()` ingests a repository and emits a
fully-typed `ProjectGovernance` contract.

File: `dev/scripts/devctl/governance/draft.py` (lines 171-219)

```python
def scan_repo_governance(
    repo_root: Path,
    *,
    policy: dict[str, Any] | None = None,
    policy_path: str | Path | None = None,
) -> ProjectGovernance:
    """Scan a repo and build a ProjectGovernance contract from local facts."""
    # ... loads policy, discovers governed docs, scans plan registry ...
    return ProjectGovernance(
        schema_version=PROJECT_GOVERNANCE_SCHEMA_VERSION,
        contract_id=PROJECT_GOVERNANCE_CONTRACT_ID,
        repo_identity=_scan_repo_identity(repo_root, resolved_policy),
        repo_pack=scan_repo_pack_ref(resolved_policy),
        path_roots=discovery.path_roots,
        plan_registry=plan_registry,
        artifact_roots=_scan_artifact_roots(repo_root),
        push_enforcement=scan_push_enforcement(resolved_policy, repo_root=repo_root, ...),
        # ... 18 total typed fields ...
    )
```

**ProjectGovernance** is the canonical IR — a frozen dataclass with 18 typed
fields capturing all governance facts for one repository.

File: `dev/scripts/devctl/runtime/project_governance_contract.py` (lines 225-246)

```python
@dataclass(frozen=True, slots=True)
class ProjectGovernance:
    """Canonical startup-authority contract for one governed repository."""

    schema_version: int
    contract_id: str
    repo_identity: RepoIdentity
    repo_pack: RepoPackRef
    path_roots: PathRoots
    plan_registry: PlanRegistry
    artifact_roots: ArtifactRoots
    memory_roots: MemoryRoots
    bridge_config: BridgeConfig
    enabled_checks: EnabledChecks
    bundle_overrides: BundleOverrides
    doc_policy: DocPolicy
    doc_registry: DocRegistry
    push_enforcement: PushEnforcement
    startup_order: tuple[str, ...]
    docs_authority: str
    workflow_profiles: tuple[str, ...]
    command_routing_defaults: dict[str, object] | None
```

**Probes** are the secondary signal extractors. Each probe scans source code
for specific patterns and emits structured `RiskHint` entries:

File: `dev/scripts/checks/probe_support/bootstrap.py` (lines 43-57)

```python
@dataclass
class RiskHint:
    """One risk signal detected by a probe."""
    file: str
    symbol: str
    risk_type: str
    severity: str
    signals: list[str]
    ai_instruction: str
    review_lens: str
```

25 probes scan for: boolean parameter sprawl, clone density, cognitive
complexity, concurrency anti-patterns, defensive overchecking, design smells,
dict-as-struct, exception quality, fan-out, identifier density, magic numbers,
mixed concerns, mutable parameter density, side-effect mixing, single-use
helpers, stringly-typed dispatch, term consistency, tuple return complexity,
type conversions, unnecessary intermediates, unwrap chains, and vague errors.

Each probe always exits 0 (advisory only, never blocks CI):

File: `dev/scripts/checks/probe_support/bootstrap.py` (lines 160-166)

```python
def emit_probe_report(report: ProbeReport, *, output_format: str) -> int:
    """Print the probe report and return exit code (always 0)."""
    if output_format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(render_probe_md(report))
    return 0
```

**Capability detection** abstracts language facts from manifests:

File: `dev/scripts/devctl/quality_policy.py` (lines 87-104)

```python
def detect_repo_capabilities(repo_root: Path | None = None) -> RepoCapabilities:
    """Detect broad repo language capabilities using common manifests."""
    rust = _manifest_exists(repo_root, "Cargo.toml")
    python = any(
        _manifest_exists(repo_root, filename)
        for filename in ("pyproject.toml", "setup.py", "setup.cfg",
                         "requirements.txt", "requirements-dev.txt", "Pipfile")
    )
    return RepoCapabilities(python=python, rust=rust)
```

---

### 2.2 Midend — Semantic Reduction

The midend transforms raw signals into typed decision records through a
canonical normalization chain.

**Stage 1: Probe hint → FindingRecord**

File: `dev/scripts/devctl/runtime/finding_contracts.py` (lines 211-263)

```python
def finding_from_probe_hint(
    hint: Mapping[str, object],
    *,
    repo_name: str, repo_path: str,
    source_command: str, source_artifact: str,
) -> FindingRecord:
    """Normalize one probe hint into the canonical finding contract."""
    return FindingRecord(
        schema_version=FINDING_SCHEMA_VERSION,
        contract_id=FINDING_CONTRACT_ID,
        finding_id=build_finding_id(FindingIdentitySeed(
            repo_name=repo_name, repo_path=repo_path,
            signal_type="probe", check_id=check_id,
            file_path=file_path, symbol=symbol, ...
        )),
        signal_type="probe",
        check_id=check_id,
        severity=coerce_string(hint.get("severity")) or "medium",
        ai_instruction=coerce_string(hint.get("ai_instruction")),
        # ... 20 total typed fields ...
    )
```

**Deterministic identity** — finding IDs are stable SHA-1 hashes:

File: `dev/scripts/devctl/runtime/finding_contracts.py` (lines 76-93)

```python
def build_finding_id(seed: FindingIdentitySeed) -> str:
    """Build one deterministic finding identifier for a governance signal."""
    raw = "::".join([
        seed.repo_name, seed.repo_path, seed.signal_type,
        seed.check_id, seed.file_path, seed.symbol,
        str(seed.line or ""), str(seed.end_line or ""),
        seed.risk_type, seed.review_lens,
        "|".join(seed.signals),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
```

**Stage 2: FindingRecord → DecisionPacketRecord**

File: `dev/scripts/devctl/runtime/finding_contracts.py` (lines 266-296)

```python
def decision_packet_from_finding(
    finding: Mapping[str, object],
    *, policy: DecisionPacketPolicy,
) -> DecisionPacketRecord:
    """Project one canonical finding into a typed design-decision packet."""
    return DecisionPacketRecord(
        schema_version=DECISION_PACKET_SCHEMA_VERSION,
        contract_id=DECISION_PACKET_CONTRACT_ID,
        finding_id=coerce_string(finding.get("finding_id")),
        decision_mode=policy.decision_mode,
        rationale=policy.rationale,
        invariants=policy.invariants,
        validation_plan=policy.validation_plan,
        match_evidence=policy.match_evidence,
        rejected_rule_traces=policy.rejected_rule_traces,
        # ... 22 total typed fields ...
    )
```

The **DecisionPacketRecord** carries explainability artifacts:

File: `dev/scripts/devctl/runtime/finding_contracts.py` (lines 150-209)

```python
@dataclass(frozen=True, slots=True)
class DecisionPacketRecord:
    """Typed packet for an intentional design decision over one finding."""
    schema_version: int
    contract_id: str
    finding_id: str
    decision_mode: str          # "auto_apply" | "recommend_only" | "approval_required"
    rationale: str              # Why this decision was made
    ai_instruction: str         # Remediation guidance
    invariants: tuple[str, ...]       # Constraints that must hold
    validation_plan: tuple[str, ...]  # Verification steps
    match_evidence: tuple[RuleMatchEvidenceRecord, ...]
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...]
```

**Decision mode vocabulary** is a closed set preventing freeform AI directives:

File: `dev/scripts/checks/probe_report/decision_packets.py` (line 31)

```python
DECISION_MODES = frozenset({"auto_apply", "recommend_only", "approval_required"})
```

File: `dev/scripts/checks/probe_report/decision_packets.py` (lines 40-44)

```python
def _normalize_decision_mode(raw_mode: Any) -> str:
    mode = str(raw_mode or "recommend_only").strip().lower()
    if mode in DECISION_MODES:
        return mode
    return "recommend_only"
```

Any input outside the frozenset is rejected and replaced with the most
conservative default. This prevents AI from injecting arbitrary directives.

**Quality feedback** computes a composite maintainability score from weighted
sub-dimensions:

File: `dev/scripts/devctl/governance/quality_feedback/models.py` (lines 29-39)

```python
SUB_SCORE_WEIGHTS: dict[str, float] = dict((
    ("halstead_mi", 0.20),
    ("code_shape", 0.10),
    ("duplication", 0.10),
    ("guard_issue_burden", 0.20),
    ("finding_density", 0.15),
    ("time_to_green", 0.10),
    ("cleanup_rate", 0.15),
))
```

Three lenses decompose the score: `code_health` (halstead, shape, duplication),
`governance_quality` (guard burden, finding density, cleanup rate), and
`operability` (time to green).

---

### 2.3 Backend — Constrained Execution

The backend gates AI actions through typed state machines with fail-closed
defaults.

**TypedAction** is the IR for AI operations:

File: `dev/scripts/devctl/runtime/action_contracts.py` (lines 17-25)

```python
@dataclass(frozen=True, slots=True)
class TypedAction:
    schema_version: int
    contract_id: str
    action_id: str
    repo_pack_id: str
    parameters: dict[str, object]
    requested_by: str = ""
    dry_run: bool = False
```

**ActionResult** is the typed execution outcome:

File: `dev/scripts/devctl/runtime/action_contracts.py` (lines 89-114)

```python
@dataclass(frozen=True, slots=True)
class ActionResult:
    schema_version: int
    contract_id: str
    action_id: str
    ok: bool
    status: str = ActionOutcome.UNKNOWN   # pass | fail | unknown | defer
    reason: str = ""
    retryable: bool = False
    partial_progress: bool = False
    operator_guidance: str = ""
    warnings: tuple[str, ...] = ()
    findings_count: int = 0
    artifact_paths: tuple[str, ...] = ()
```

**ActionOutcome** provides four explicit states instead of boolean overloading:

File: `dev/scripts/devctl/runtime/action_contracts.py` (lines 74-86)

```python
class ActionOutcome:
    """Guards and startup surfaces use these instead of overloading pass/fail
    so they can escalate honestly when the answer is not yet known."""
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    DEFER = "defer"
    ALL = frozenset({PASS, FAIL, UNKNOWN, DEFER})
```

**Startup gate enforcement** blocks specific commands when preconditions fail:

File: `dev/scripts/devctl/runtime/startup_gate.py` (lines 13-23, 41-83)

```python
_GATED_COMMANDS = {
    "autonomy-swarm", "push", "guard-run", "sync",
    "autonomy-loop", "mutation-loop", "swarm_run",
}

def enforce_startup_gate(args, *, repo_root: Path = REPO_ROOT) -> str | None:
    """Return a blocking startup-gate message for launcher/mutation commands."""
    if not command_requires_startup_gate(args):
        return None
    authority_report = build_startup_authority_report(repo_root=repo_root)
    # ... validates receipt freshness, authority checks ...
    if bool(authority_report.get("ok", False)):
        return None
    return _format_gate_failure(args, heading="...", failures=[...])
```

**Guard-run** captures git state before/after AI actions:

File: `dev/scripts/devctl/guard_run_core.py` (lines 22-36)

```python
@dataclass(frozen=True)
class GuardGitSnapshot:
    """Typed representation of a pre/post guard-run git worktree snapshot."""
    reviewed_worktree_hash: str = ""
    files_changed: tuple[str, ...] = ()
    file_count: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    diff_churn: int = 0
```

---

### 2.4 Linker — Feedback Loop

The linker persists findings to append-only ledgers and feeds them back into
the next session's startup context.

**Governance review ledger** — append-only JSONL with typed rows:

File: `dev/scripts/devctl/governance_review_log.py` (lines 193-205)

```python
def append_governance_review_row(row: dict[str, Any], *, log_path: Path) -> None:
    """Append one governance review row to the JSONL log."""
    if "finding_id" not in row:
        raise ValueError("governance review row must contain finding_id")
    append_ledger_rows([row], log_path=log_path)
```

Each row carries: `finding_id`, `verdict` (fixed/confirmed_issue/deferred/
false_positive/waived), `finding_class` (local_defect/contract_mismatch/
missing_guard/missing_probe/authority_boundary/workflow_gap/docs_drift),
`recurrence_risk` (one_off/localized/recurring/systemic), and
`prevention_surface` (guard/probe/contract/authority_rule/parity_check/
regression_test).

**Startup signals** load prior session findings into the next bootstrap:

File: `dev/scripts/devctl/runtime/startup_signals.py` (lines 18-36)

```python
def load_startup_quality_signals(repo_root: Path) -> dict[str, object]:
    """Load bounded startup summaries from recent governance artifacts."""
    signals: dict[str, object] = {}
    probe_report = _load_probe_report_summary(repo_root)
    if probe_report:
        signals["probe_report"] = probe_report
    governance_review = _load_governance_review_summary(repo_root)
    if governance_review:
        signals["governance_review"] = governance_review
    # ... also loads guidance_hotspots, watchdog, command_reliability ...
    return signals
```

These signals are injected into the `StartupContext` that every AI agent reads
at session start:

File: `dev/scripts/devctl/runtime/startup_context.py` (lines 48-68)

```python
@dataclass(frozen=True, slots=True)
class StartupContext:
    """One typed packet for AI agent session startup.
    Carries everything an agent needs to understand the repo's governance
    posture, current worktree state, and what actions are safe — without
    re-reading prose docs."""

    schema_version: int = 1
    contract_id: str = "StartupContext"
    governance: ProjectGovernance | None = None
    reviewer_gate: ReviewerGateState = field(default_factory=ReviewerGateState)
    push_decision: PushDecisionState = field(default_factory=PushDecisionState)
    advisory_action: str = "continue_editing"
    quality_signals: dict[str, object] = field(default_factory=dict)
```

**Event sourcing** — the review channel uses append-only NDJSON with exclusive
file locking:

File: `dev/scripts/devctl/review_channel/event_store.py` (lines 109-155)

```python
def append_event(events_path, event, *, existing_events):
    """Append one event with serialized event-id allocation."""
    with events_path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            fresh_events = _read_events_under_lock(events_path)
            event["event_id"] = next_event_id(fresh_events)
            # ... idempotency key check, uniqueness check ...
            handle.write(json.dumps(event, sort_keys=True) + "\n")
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
    return event
```

The **event reducer** replays the log to derive current state — textbook event
sourcing:

File: `dev/scripts/devctl/review_channel/event_reducer.py` (lines 192-307)

```python
def reduce_events(*, events, repo_root, review_channel_path, lanes=None):
    """Reduce the append-only event log into the latest packet/state snapshot."""
    packets_by_id: dict[str, ReviewPacketRow] = {}
    for event in events:
        event_type = str(event.get("event_type") or "").strip()
        if event_type == "packet_posted":
            packets_by_id[packet_id] = packet_from_event(event)
        elif event_type in {"packet_acked", "packet_dismissed", "packet_applied"}:
            packets_by_id[packet_id] = apply_packet_transition(packet, event)
        elif event_type == "packet_expired":
            expired_packet["status"] = "expired"
    # ... constructs typed ReviewState from reduced packets ...
```

---

## 3. Abstract Interpretation Implementation

The system implements abstract interpretation concepts from compiler theory.

### 3.1 Abstract Domain

The system computes **11 boolean abstract facts** from concrete repo state:

| Abstract Fact | Type | Default | Defined In |
|---|---|---|---|
| `checkpoint_required` | bool | False | `project_governance_push.py:27` |
| `safe_to_continue_editing` | bool | True | `project_governance_push.py:28` |
| `worktree_clean` | bool | True | `project_governance_push.py:31` |
| `worktree_dirty` | bool | False | `project_governance_push.py:30` |
| `bridge_active` | bool | False | `startup_context.py:37` |
| `review_accepted` | bool | False | `startup_context.py:39` |
| `checkpoint_permitted` | bool | True | `startup_context.py:41` |
| `review_gate_allows_push` | bool | False | `startup_context.py:42` |
| `implementation_blocked` | bool | False | `startup_context.py:43` |
| `push_eligible_now` | bool | False | `startup_push_decision.py:30` |
| `startup_authority_ok` | bool | varies | `startup_receipt.py:46` |

### 3.2 Transfer Functions

**Advisory decision** — maps governance + gate state to next action:

File: `dev/scripts/devctl/runtime/startup_advisory_decision.py` (lines 28-140)

```python
def derive_advisory_decision(governance, gate) -> StartupAdvisoryDecision:
    push = governance.push_enforcement
    if push.checkpoint_required:                              # Branch 1
        return _checkpoint_required_decision(push)
    if not push.safe_to_continue_editing:                     # Branch 2
        return _budget_exceeded_decision(push)
    if gate.implementation_blocked:                           # Branch 3
        return _blocked_loop_decision(gate)
    if gate.bridge_active and not gate.review_accepted:       # Branch 4
        return _pending_review_decision(...)
    if push.worktree_clean and gate.review_gate_allows_push:  # Branch 5
        return _decision("push_allowed", ...)
    return _decision("continue_editing", ...)                 # Default
```

**Push decision** — sequential gate evaluation:

File: `dev/scripts/devctl/runtime/startup_push_decision.py` (lines 73-155)

```python
def derive_push_decision(governance, gate) -> PushDecisionState:
    local_readiness = _local_readiness_decision(inputs, pe)
    if local_readiness is not None:
        return local_readiness            # Gate 1: checkpoint/dirty
    review_decision = _review_state_decision(inputs, gate)
    if review_decision is not None:
        return review_decision            # Gate 2: review blocked/pending
    if not inputs.has_remote_work_to_push:
        return "no_push_needed"           # Gate 3: already synced
    return "run_devctl_push"              # Gate 4: all green
```

### 3.3 Conservative Approximation (Fail-Closed)

When the system cannot determine safety, it defaults to the restrictive option:

File: `dev/scripts/devctl/runtime/startup_context.py` (lines 160-186)

```python
def _detect_reviewer_gate_without_typed_state(governance):
    if governance is None:
        return ReviewerGateState(checkpoint_permitted=True,
                                review_gate_allows_push=True)
    # Bridge active but no typed state → BLOCK EVERYTHING
    return ReviewerGateState(
        bridge_active=True,
        review_accepted=False,                  # conservative
        review_gate_allows_push=False,          # conservative
        implementation_blocked=True,            # conservative
        implementation_block_reason="typed_review_state_required",
    )
```

**Checkpoint gate** — OR condition means any uncertainty blocks push:

File: `dev/scripts/devctl/governance/push_state.py` (lines 68-72)

```python
checkpoint_required = (
    dirty_path_count >= policy.checkpoint.max_dirty_paths_before_checkpoint
    or untracked_path_count >= policy.checkpoint.max_untracked_paths_before_checkpoint
)
safe_to_continue_editing = not checkpoint_required
```

### 3.4 Fixpoint Computation

The autonomy loop iterates rounds until `unresolved_count` stabilizes:

File: `dev/scripts/devctl/commands/autonomy_loop_rounds.py` (lines 56-215)

```python
for round_index in range(1, int(args.max_rounds) + 1):
    if elapsed > max_duration:
        reason = "max_hours_reached"; break    # Time budget
    if tasks_completed >= int(args.max_tasks):
        reason = "max_tasks_reached"; break    # Task budget
    # ... triage + packet generation ...
    if unresolved <= 0 and triage_reason == "resolved":
        resolved = True
        reason = "resolved"; break             # FIXPOINT: convergence
```

### 3.5 Widening and Narrowing (Adaptive Precision)

File: `dev/scripts/devctl/autonomy/run_feedback.py` (lines 20-31)

```python
def _downshift_target(*, current, minimum, factor):
    """NARROWING: Reduce agent count when problem is getting harder."""
    candidate = int(math.floor(float(current) * factor))
    return max(minimum, candidate)

def _upshift_target(*, current, maximum, factor):
    """WIDENING: Increase agent count when problem is getting easier."""
    candidate = int(math.ceil(float(current) * factor))
    return min(maximum, candidate)
```

Feedback sizing tracks three convergence signals:
- `stall_streak`: unresolved count doesn't decrease → **narrow** (downshift)
- `no_signal_streak`: zero productive workers → **narrow** (downshift)
- `improve_streak`: unresolved count decreases → **widen** (upshift)

---

## 4. Invariant Enforcement

### 4.1 Schema Versioning

Every typed contract carries `schema_version` and `contract_id`:

File: `dev/scripts/devctl/runtime/finding_contracts.py` (lines 18-25)

```python
FINDING_CONTRACT_ID, FINDING_SCHEMA_VERSION = "Finding", 1
DECISION_PACKET_CONTRACT_ID, DECISION_PACKET_SCHEMA_VERSION = "DecisionPacket", 1
PROBE_REPORT_CONTRACT_ID, PROBE_REPORT_SCHEMA_VERSION = "ProbeReport", 1
```

Deserialization validates against expected constants:

File: `dev/scripts/checks/probe_report/decision_packets.py` (lines 227-237)

```python
schema_version = data.get("schema_version")
if schema_version not in (None, PROBE_ALLOWLIST_SCHEMA_VERSION):
    raise ValueError(f"schema_version must be {PROBE_ALLOWLIST_SCHEMA_VERSION}")
contract_id = str(data.get("contract_id") or "").strip()
if contract_id and contract_id != PROBE_ALLOWLIST_CONTRACT_ID:
    raise ValueError(f"contract_id must be {PROBE_ALLOWLIST_CONTRACT_ID!r}")
```

### 4.2 Guard Determinism

Guards exit 0 (pass) or 1 (violations found) — binary, deterministic:

```python
return 0 if report["ok"] else 1
```

Probes always exit 0 — advisory only, never block CI.

Guard and probe registries are frozen:

File: `dev/scripts/devctl/quality_policy_defaults.py` (lines 8-17)

```python
@dataclass(frozen=True, slots=True)
class QualityStepSpec:
    step_name: str
    script_id: str
    extra_args: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    supports_commit_range: bool = True
```

64 guards and 25 probes are statically registered in immutable tuples.

---

## 5. Context Graph as Searchable Abstract Domain

The context graph (ZGraph) provides a mathematical structure for navigating
the codebase with typed coupling metrics.

### 5.1 Graph Structure

File: `dev/scripts/devctl/context_graph/models.py` (lines 8-18)

```python
@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_kind: str       # source_file | active_plan | guard | probe | guide | concept
    label: str
    canonical_pointer_ref: str
    provenance_ref: str
    temperature: float   # 0.0-1.0 hotness score
    metadata: dict[str, object]
```

Seven node kinds: `source_file`, `active_plan`, `devctl_command`, `guard`,
`probe`, `guide`, `concept`.

Seven edge kinds: `imports`, `documented_by`, `guards`, `routes_to`,
`scoped_by`, `contains`, `related_to`.

### 5.2 Temperature Formula

File: `dev/scripts/devctl/context_graph/builder.py` (lines 55-71)

```python
def _temperature_for_source(fan_in, fan_out, hint_count, changed, severity=""):
    score = 0.0
    score += min(hint_count * 0.15, 0.45)          # Hint weight (cap 0.45)
    bridge = min(fan_in, fan_out)
    score += min(bridge * 0.05, 0.2)               # Bridge score (cap 0.2)
    score += min((fan_in + fan_out) * 0.01, 0.15)  # Coupling (cap 0.15)
    if changed:
        score += 0.2                               # Recent change bonus
    score += _SEVERITY_BOOST.get(severity.lower(), 0.0)
    return min(round(score, 3), 1.0)
```

### 5.3 Snapshot Delta Computation

File: `dev/scripts/devctl/context_graph/snapshot_diff.py` (lines 52-107)

The system computes bounded deltas between graph snapshots: added/removed
nodes, added/removed edges, and temperature shifts — enabling trend analysis
across sessions.

---

## 6. Cross-Repository Portability

The system is designed to run on arbitrary repositories without engine edits.

### 6.1 Portable Presets

File: `dev/config/quality_presets/portable_python.json` — 15 guards, 17 probes,
zero VoiceTerm references.

### 6.2 Adoption Scan

File: `dev/scripts/devctl/quality_scan_mode.py` (lines 44-49)

```python
if adoption_scan:
    return ResolvedScanMode(
        mode="adoption-scan",
        since_ref="__DEVCTL_EMPTY_TREE_BASE__",
        head_ref="__DEVCTL_WORKTREE_HEAD__",
    )
```

The `__DEVCTL_EMPTY_TREE_BASE__` sentinel treats the entire worktree as
baseline, enabling first-time scans of any repository.

### 6.3 Proven Cross-Repository Execution

File: `dev/reports/audits/portable_governance_pilot_2026-03-14.json`

13 repositories scanned with the same engine:
- **311 total findings** (115 high, 193 medium, 3 low)
- **0 scan errors**
- **3 clean repositories**
- **ci-cd-hub**: 159 findings across 509 source files

The same `check --profile ci --adoption-scan` command ran on diverse repos
(Python, Java, Rust) with zero engine modifications.

---

## 7. Governance Statistics

Current state (2026-03-27):

| Metric | Value |
|---|---|
| Total findings reviewed | 95 |
| Fixed | 62 (65% cleanup rate) |
| Confirmed open | 19 |
| Deferred | 14 |
| False positive rate | 0% |
| Probes active | 25 |
| Guards active | 64 |
| CI workflows | 30 |
| Python tests | ~1,098 |

---

## 8. Multi-Agent Coordination

The system coordinates multiple AI agents (Codex as reviewer, Claude as
implementer) through a structured bridge protocol with lane assignments.

### 8.1 Lane Assignment System

File: `dev/scripts/devctl/review_channel/core.py` (lines 67-77)

```python
@dataclass(frozen=True)
class LaneAssignment:
    agent_id: str        # "AGENT-1", "AGENT-9", etc.
    provider: str        # "codex" or "claude"
    lane: str            # "Codex architecture contract review"
    docs: str            # Primary active docs URL/path
    mp_scope: str        # MP items assigned
    worktree: str        # Isolated git worktree path
    branch: str          # Feature branch
```

The system supports an 8+8 lane table: 8 Codex reviewer/auditor lanes and 8
Claude coding/fix lanes. Each lane has a dedicated git worktree for isolation.
The conductor model ensures only the Codex conductor updates reviewer-owned
bridge sections and only the Claude conductor updates implementer-owned
sections — preventing concurrent write collisions.

### 8.2 Bridge Protocol

The bridge (`bridge.md`) enforces ownership boundaries:

- **Codex-owned sections**: Poll Status, Current Verdict, Open Findings,
  Last Reviewed Scope, Current Instruction For Claude
- **Claude-owned sections**: Claude Status, Claude Ack, Claude Questions

Poll cadence is enforced: fresh < 180s, poll due 180-300s, stale 300-900s,
overdue > 900s. Liveness detection tracks heartbeat freshness, stale peer
detection, and active session conflicts.

File: `dev/scripts/devctl/review_channel/peer_liveness.py` defines:
- `CodexPollState` enum: MISSING, STALE, POLL_DUE, FRESH
- `OverallLivenessState` enum: INACTIVE, RUNTIME_MISSING, STALE,
  WAITING_ON_PEER, FRESH
- `AttentionStatus` enum: 29 machine-readable states for operator consumption

---

## 9. Watchdog Episode System

Every AI fix is tracked as a **guarded coding episode** with typed before/after
metrics.

File: `dev/scripts/devctl/watchdog/models.py` (lines 11-56)

```python
@dataclass(frozen=True, slots=True)
class GuardedCodingEpisode:
    """Canonical typed row for one guarded-coding watchdog episode."""
    episode_id: str
    task_id: str
    plan_id: str
    controller_run_id: str
    provider: str                    # "codex" | "claude" | "shared"
    session_id: str
    guard_family: str                # "runtime" | "tooling" | "docs"
    guard_command_id: str
    trigger_reason: str
    files_changed_before: int
    files_changed_after: int
    lines_added_before_guard: int
    lines_removed_before_guard: int
    diff_churn_before_guard: int
    lines_added_after_guard: int
    lines_removed_after_guard: int
    diff_churn_after_guard: int
    guard_result: str                # "pass" | "fail" | "skipped" | "noisy"
    guard_runtime_seconds: float
    test_runtime_seconds: float
    retry_count: int
    escaped_findings_count: int
    reviewer_verdict: str            # "accepted" | "rejected" | "deferred"
    stale_peer_pause_count: int
    handoff_count: int
```

Episodes are persisted to JSONL and aggregated into `WatchdogMetrics`:
total episodes, success rate, average time to green, average guard runtime,
false positive rate, and per-provider/per-guard-family breakdowns.

File: `dev/scripts/devctl/watchdog/episode.py` (lines 24-127) builds episodes
from guard-run reports with provider inference, guard-family classification,
and escaped-findings derivation.

---

## 10. Autonomy Swarm — Parallel AI Agents

The system runs multiple AI agents in parallel with adaptive feedback sizing.

### 10.1 Parallel Execution

File: `dev/scripts/devctl/commands/autonomy_swarm.py` (lines 66-72)

```python
worker_count = min(worker_agent_count, max(1, int(args.parallel_workers)))
with ThreadPoolExecutor(max_workers=worker_count) as executor:
    futures = [
        executor.submit(run_one_agent, AgentTask(index=i, name=f"agent-{i}", ...))
        for i in range(worker_count)
    ]
```

### 10.2 Adaptive Feedback Sizing

The swarm adapts agent count based on convergence signals:

File: `dev/scripts/devctl/autonomy/run_feedback.py` (lines 267-296)

```python
# NARROWING: reduce agents when stalling
if no_signal_streak >= no_signal_rounds:
    next_agents = _downshift_target(current=current_agents, minimum=min_agents,
                                     factor=downshift_factor)
    if next_agents < current_agents:
        decision = "downshift"

# NARROWING: reduce agents when findings aren't decreasing
elif stall_streak >= stall_rounds:
    next_agents = _downshift_target(...)
    if next_agents < current_agents:
        decision = "downshift"

# WIDENING: increase agents when improving
elif improve_streak >= upshift_rounds and signal_workers > 0 and unresolved > 0:
    next_agents = _upshift_target(current=current_agents, maximum=max_agents,
                                   factor=upshift_factor)
    if next_agents > current_agents:
        decision = "upshift"
```

This implements **adaptive precision** from abstract interpretation: narrow
the solver when it stalls (fewer agents, stricter focus), widen when it
improves (more agents, broader exploration).

---

## 11. Proof-Carrying Execution

Every decision carries explicit proof of **why** it was made and **what
alternatives were rejected** — inspired by proof-carrying code.

### 11.1 Match Evidence

File: `dev/scripts/devctl/runtime/finding_explainability_contracts.py` (lines 22-35)

```python
@dataclass(frozen=True, slots=True)
class RuleMatchEvidenceRecord:
    """One plain-language explanation for why a rule matched."""
    rule_id: str
    summary: str
    evidence: tuple[str, ...] = ()
```

### 11.2 Rejected Rule Traces

File: `dev/scripts/devctl/runtime/finding_explainability_contracts.py` (lines 38-53)

```python
@dataclass(frozen=True, slots=True)
class RejectedRuleTraceRecord:
    """One plain-language explanation for why a competing rule was rejected."""
    rule_id: str
    summary: str
    rejected_because: str
    evidence: tuple[str, ...] = ()
```

### 11.3 Proof in Push Decisions

Every push decision carries explicit proof. For example, when
`derive_push_decision()` returns `await_checkpoint`:

File: `dev/scripts/devctl/runtime/startup_push_decision.py` (lines 172-200)

```python
return _project_push_decision(inputs, PushDecisionSpec(
    action="await_checkpoint",
    reason=checkpoint_reason,
    match_evidence=(
        rule_match_evidence(
            "startup_push.await_checkpoint_gate",
            "The continuation gate fired before any push-specific rule could run.",
            f"checkpoint_required={checkpoint_required}",
            f"safe_to_continue_editing={safe_to_continue_editing}",
            f"checkpoint_reason={checkpoint_reason}",
        ),
    ),
    rejected_rule_traces=(
        rejected_rule_trace(
            "startup_push.await_review",
            "Wait for reviewer-owned state before pushing.",
            "Checkpoint readiness is a stricter prerequisite than review readiness.",
        ),
        rejected_rule_trace(
            "startup_push.run_devctl_push",
            "Run the governed push path immediately.",
            "The worktree is not ready for remote action yet.",
        ),
    ),
))
```

This means the system can explain: "I chose `await_checkpoint` because the
checkpoint gate fired. I rejected `await_review` because checkpoint readiness
is stricter. I rejected `run_devctl_push` because the worktree is not ready."

The AI agent and human operator see the same typed proof — not freeform prose.

---

## 12. CQRS / Event Sourcing

The review channel implements CQRS (Command Query Responsibility Segregation):
one canonical write model produces 7 separate read projections.

File: `dev/scripts/devctl/review_channel/projection_bundle.py` (lines 85-143)

```python
def write_projection_bundle(review_state, *, artifact_paths, ...):
    """Write all projections from one canonical review_state."""
    # 1. review_state.json — canonical typed state (write model)
    # 2. compact.json     — compact read projection for operator console
    # 3. full.json        — full read projection with extras
    # 4. actions.json     — pending packet action list
    # 5. trace.ndjson     — append-only event trace
    # 6. latest.md        — human-readable markdown rendering
    # 7. agents.json      — agent lane assignments registry
```

The event store (`event_store.py`) provides append-only persistence with
exclusive file locking. The event reducer (`event_reducer.py`) replays the
log to derive current state — textbook event sourcing. Multiple read
projections serve different consumers (AI agents, operator console, CLI,
mobile app, terminal overlay) from one canonical source of truth.

---

## 13. How This Differs From Vendor AI Tooling

Vendor AI tools (OpenAI Codex, Anthropic Claude Code) provide:
- **Sandboxing**: Container isolation, file access controls
- **Approvals**: Human-in-the-loop for tool use
- **CI/CD hooks**: GitHub Actions, pre-commit hooks

This system adds a **governance layer** that vendor tooling does not provide:

### 13.1 Startup Receipt (Typed Session Authority)

File: `dev/scripts/devctl/runtime/startup_receipt.py` (lines 23-45)

```python
@dataclass(frozen=True, slots=True)
class StartupReceipt:
    """Persistent proof of what the system decided at session start."""
    schema_version: int
    contract_id: str = "StartupReceipt"
    advisory_action: str              # continue | checkpoint | await_review | push
    advisory_reason: str
    push_action: str                  # await_checkpoint | run_devctl_push | no_push_needed
    push_eligible_now: bool
    checkpoint_required: bool
    safe_to_continue_editing: bool
    startup_authority_ok: bool
    startup_authority_errors: tuple[str, ...]
```

Vendor AI starts a session and begins coding. This system requires the AI to
prove the repo is in a known-good state before any mutation is allowed.

### 13.2 Push Enforcement (Governance Gate)

File: `dev/scripts/devctl/governance/push_state.py` (lines 38-112)

The system detects repo-owned pre-push hook installation, computes worktree
dirty/untracked path counts against policy thresholds, enforces checkpoint
requirements, and computes recommended actions — all before the AI can
execute `git push`. Vendor AI has no equivalent: it either allows or blocks
`git push` as a binary permission, with no policy-driven state machine.

### 13.3 Startup Authority Contract (11 Invariant Checks)

File: `dev/scripts/checks/startup_authority_contract/command.py` (lines 29-151)

11 checks enforced at every session start:
1. Startup authority file exists (AGENTS.md)
2. Active-plan registry file exists (INDEX.md)
3. Plan tracker file exists (MASTER_PLAN.md)
4. Path roots resolve (active_docs directory)
5. Path roots resolve (scripts directory)
6. repo_identity.repo_name is non-empty
7. plan_registry.registry_path is configured
8. plan_registry.tracker_path is configured
9. Checkpoint budget is fail-closed
10. Active reviewer loop cannot start fresh when stale
11. Repo-local Python imports resolve in git index

Vendor AI checks none of these. It begins executing the moment it receives
a prompt.

---

## 14. Summary

This system demonstrates that a **repo-local deterministic governance layer**
can serve as a **compiler for probabilistic AI agents**:

1. **Frontend** extracts typed signals from repo state (guards, probes, scans)
2. **Midend** reduces signals into decision records with fixed vocabulary
3. **Backend** gates execution through fail-closed state machines
4. **Linker** feeds evidence back to the next session via startup signals
5. **Multi-agent coordination** manages reviewer + implementer via typed bridge
6. **Watchdog episodes** track every AI fix with before/after metrics
7. **Autonomy swarm** runs parallel agents with adaptive feedback sizing
8. **Proof-carrying execution** attaches match evidence + rejected alternatives
9. **CQRS / event sourcing** produces 7 read projections from one write model
10. **Governance gates** enforce 11 startup invariants vendor AI doesn't check

The key architectural insight:

> AI is a heuristic search engine. This system compiles a deterministic
> execution envelope around it. The model proposes transitions; only proven
> or conservatively admitted transitions execute.

This is not automation with extra checks. It is the application of compiler
theory — abstract interpretation, transfer functions, invariant enforcement,
conservative approximation, and fixpoint convergence — to the problem of
governing AI-assisted software engineering.

The system is proven portable: 13 repositories scanned with zero engine
modifications. The same typed contracts, deterministic passes, and fail-closed
defaults that govern VoiceTerm govern any repository the engine is pointed at.

The unifying principle across security, CI/CD, compilers, logic, and agent
orchestration:

> Don't trust the search process with authority. Trust only the verified
> transition system around it.

---

## 15. Known Gaps (Honest Assessment)

The compiler analogy holds for the frontend and midend but has documented
gaps in the backend and linker. These are acknowledged here for academic
honesty.

### 15.1 Contract Spine Not Structurally Closed

The intended chain is:
`Finding → Decision → Action → Result → Feedback → Finding`

The current state:
- `FindingRecord` → `DecisionPacketRecord`: linked via `finding_id` field
- `DecisionPacketRecord` → `TypedAction`: **no structural link** (semantic only)
- `TypedAction` → `ActionResult`: linked via `action_id` but ActionResult has
  **no `finding_id`** — only an aggregate `findings_count: int`
- `ActionResult` → next session: feedback is through startup signals, not
  through typed back-references

The chain is conceptually closed but not structurally enforced with foreign
keys or typed references across all layers.

### 15.2 Runtime Type Looseness at IR Boundaries

52 instances of `dict[str, object]` remain in the `runtime/` layer. Critical
IR boundaries that are still untyped:
- `TypedAction.parameters: dict[str, object]` — action parameters are opaque
- `StartupContext.quality_signals: dict[str, object]` — feedback signals untyped
- `ProjectGovernance.command_routing_defaults: dict[str, object] | None`

The architectural guide (`dev/guides/PYTHON_ARCHITECTURE.md`) documents the
target: "Use boundary-validation models only when data crosses an untrusted
or serialized boundary" and "Internal runtime code should stay mostly on
stdlib typing plus dataclass." The gap is that some IR-boundary payloads are
still `dict` instead of typed contracts.

### 15.3 Context Graph as Analysis, Not Authority

The context graph computes temperature, fan-in/fan-out, and bridge scores,
but no guard, probe, or decision function reads graph data as an execution
gate. The graph is a query and discovery tool — it helps narrow the search
space but does not constrain execution.

The planned evolution (tracked in active plans) is:
`graph → constraint → guard → decision`

This would promote the graph from analysis layer to enforcement layer, making
coupling metrics a first-class input to fix scope decisions.

### 15.4 Finding Identity Stability

The `build_finding_id()` hash includes `repo_path`, which could theoretically
vary across checkout locations. A normalization layer
(`normalize_identity_repo_path()`) strips absolute paths before hashing, and
tests verify portability across checkout paths. One documented leak remains
where `review_probe_report.py` uses an empty-string workaround instead of
full normalization.

### 15.5 Guard→Finding Integration Is Complete But Not Self-Enforcing

The `finding_from_guard_violation()` adapter exists and is actively used —
27 guard-originated rows exist in the governance ledger. However, there is
no self-governance guard that blocks future guards from bypassing the Finding
pipeline. A guard could theoretically emit violations without creating
FindingRecord objects, and nothing would catch the bypass until manual audit.

---

These gaps represent the distance between "working compiler" and
"fully-closed compiler." The frontend (signal extraction) and midend
(semantic reduction) are structurally sound. The backend (constrained
execution) and linker (feedback) work correctly but rely on convention
rather than structural enforcement. Closing these gaps is tracked in
the active execution plan (`platform_authority_loop.md` Phases 4-5b).

---

## 16. Comparison With Existing Tools and Approaches

### 16.1 What Exists in the Market (March 2026)

The AI code governance landscape in 2026 falls into five categories. None
implements the full compiler model described in this system.

**Category 1: Vendor Agent Sandboxes (OpenAI Codex, Anthropic Claude Code)**

OpenAI Codex uses OS-enforced sandboxes that limit filesystem/network access
and an approval policy that controls when the agent must ask before acting.
Approval modes range from "suggest" (always ask) to "full-auto" (only ask for
network/external writes). Anthropic Claude Code uses hooks (PreToolUse,
PostToolUse, PermissionRequest, etc.) and subagent orchestration with
lifecycle-scoped triggers.

*What they provide*: Container isolation, permission gating, human-in-the-loop
approvals, tool-call interception.

*What they don't provide*: Typed intermediate representations of decisions,
deterministic transfer functions over repo state, finding-to-decision-to-action
IR chains, convergence detection, quality feedback loops across sessions,
fail-closed startup authority, or cross-repo portable governance presets.

**Category 2: Policy-as-Code Engines (Vectimus, AWS Bedrock AgentCore Policy)**

Vectimus intercepts every AI agent tool call and evaluates it against 78
deterministic Cedar policies (368 rules) before execution. It normalizes
tool-specific payloads from Claude Code, Cursor, Copilot, and Gemini CLI
into a unified Cedar request format, producing allow/deny/escalate decisions.
AWS Bedrock AgentCore Policy (GA March 2026) uses the same Cedar language for
centralized agent-to-tool access control.

*What they provide*: Deterministic pre-execution policy evaluation,
vendor-agnostic interception, credential/exfiltration pattern detection.

*What they don't provide*: Code-quality analysis, architectural pattern
detection, finding identity and lifecycle tracking, governance review with
verdicts, quality feedback computation, plan-aware routing, or cross-session
learning. They gate *tool calls* — they don't analyze *code quality* or
*architectural decisions*.

**Category 3: Code Quality Gates (CodeScene, Codacy, Snyk)**

CodeScene provides CodeHealth checks as quality gates in pull requests,
detecting code smells in AI-generated code with fix recommendations. Codacy
and Snyk offer similar PR-level quality scanning with security focus.

*What they provide*: PR-level code quality checks, code smell detection, fix
recommendations, IDE integration.

*What they don't provide*: Runtime execution gating, startup authority
enforcement, typed decision records, finding-to-action IR chains,
convergence-based autonomy loops, multi-agent coordination, or plan-aware
governance. They analyze code *after* it's written — they don't constrain
*how* the AI writes it or *whether* it can push.

**Category 4: Agent Frameworks (LangChain, CrewAI, AutoGen)**

Agent frameworks provide orchestration primitives: tool binding, memory,
multi-agent coordination, guardrail integration. LangChain offers guardrail
validators (toxicity, PII, jailbreak). CrewAI and AutoGen provide
role-based multi-agent workflows.

*What they provide*: Agent orchestration, tool binding, memory management,
prompt-level guardrails.

*What they don't provide*: Repo-local governance, deterministic code quality
passes, typed IR for decisions, fail-closed startup gates, plan-aware routing,
evidence-based convergence, or cross-repo portable presets. Guardrails operate
at the prompt/response level, not at the repo/execution-authority level.

**Category 5: Academic Frameworks (Agent Behavioral Contracts)**

Agent Behavioral Contracts (ABC, arxiv 2602.22302) defines formal contracts
with Preconditions, Invariants, Governance policies, and Recovery mechanisms
as runtime-enforceable components. Evaluated on AgentContract-Bench (200
scenarios across 7 models).

*What they provide*: Formal contract specification, runtime behavioral
enforcement, benchmark evaluation.

*What they don't provide*: Repo-local implementation, code quality analysis,
architectural pattern detection, finding lifecycle tracking, or cross-repo
portability. ABC is a specification framework — it defines what contracts
*should* look like but does not implement a full governance compiler with
signal extraction, semantic reduction, and feedback loops.

### 16.2 What Makes This System Different

No existing tool implements the full pipeline:

```
Signal → Finding → Decision → Action → Feedback → Signal
```

with typed IR at every stage, deterministic transfer functions, fail-closed
defaults, convergence detection, and cross-repo portability.

| Capability | This System | Vendor Sandboxes | Policy Engines | Quality Gates | Agent Frameworks | ABC (Academic) |
|---|---|---|---|---|---|---|
| **Typed IR chain** (Finding→Decision→Action) | Yes | No | No | No | No | Spec only |
| **Deterministic transfer functions** | Yes | No | Yes (Cedar) | No | No | Spec only |
| **Fail-closed startup authority** | Yes (11 checks) | Partial (approval) | No | No | No | No |
| **Finding identity & lifecycle** | Yes (SHA-1 hash, JSONL ledger) | No | No | No | No | No |
| **Quality feedback across sessions** | Yes (improvement tracker) | No | No | Partial (PR trends) | Partial (memory) | No |
| **Convergence/fixpoint detection** | Yes (stall/improve streaks) | No | No | No | No | No |
| **Cross-repo portable presets** | Yes (13-repo pilot) | No | Partial (Cedar policies) | Partial (rule configs) | No | No |
| **Proof-carrying decisions** | Yes (match_evidence, rejected_traces) | No | No | No | No | Yes (contracts) |
| **Multi-agent coordination** | Yes (8+8 lane table) | Partial (subagents) | No | No | Yes (roles) | No |
| **Plan-aware governance** | Yes (PlanRegistry, WorkIntakePacket) | No | No | No | No | No |
| **Event sourcing / CQRS** | Yes (7 projections) | No | No | No | No | No |
| **Abstract interpretation** | Yes (domain, transfer fns, fixpoint) | No | No | No | No | Yes (formal) |

### 16.3 The Key Architectural Difference

Existing tools operate at one of three levels:

1. **Permission level** (sandboxes, policy engines): "Can the agent run this
   command?" — binary allow/deny
2. **Output level** (quality gates): "Is the generated code good?" — post-hoc
   review
3. **Orchestration level** (agent frameworks): "How do agents coordinate?" —
   workflow management

This system operates at the **compilation level**: "What execution is
*admissible* given the current repo state, plan state, governance policy,
review status, and accumulated evidence?" The answer is computed
deterministically from typed contracts, not from AI judgment or human
approval alone.

The closest analog in the market is Vectimus (Cedar-based policy evaluation
before execution), but Vectimus gates *tool calls* without analyzing *code
quality*, tracking *finding lifecycles*, or computing *convergence*. It's
a policy firewall. This system is a policy compiler — it doesn't just
allow/deny; it extracts signals, reduces them to typed decisions, gates
execution, and feeds outcomes back into the next session.

### 16.4 Why Nothing Else Does This

The likely reason no existing tool implements this full model:

1. **Vendor AI tools own the agent, not the repo.** OpenAI and Anthropic
   build agent infrastructure. They don't build repo-local governance because
   governance is repo-specific — it depends on the repo's plans, policies,
   architecture, and quality history. A vendor can't ship that.

2. **Policy engines are stateless.** Cedar evaluates rules against a request.
   It doesn't track findings across sessions, compute quality deltas, or
   detect convergence. It's a firewall, not a compiler.

3. **Quality gates are post-hoc.** CodeScene and Codacy check code after it's
   written. They don't constrain the writing process or gate push decisions
   based on accumulated evidence.

4. **Agent frameworks are orchestration, not governance.** LangChain and
   CrewAI manage how agents talk to each other. They don't enforce what the
   agents are *allowed to conclude* based on repo evidence.

This system fills the gap between all four: it's repo-local (not vendor-owned),
stateful (not stateless evaluation), pre-hoc (not post-hoc review), and
evidence-based (not orchestration-only).

Sources consulted:
- [OpenAI Codex Agent Approvals & Security](https://developers.openai.com/codex/agent-approvals-security)
- [OpenAI Codex Sandboxing](https://developers.openai.com/codex/concepts/sandboxing)
- [Anthropic Claude Code Hooks Reference](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Anthropic Claude Code Advanced Patterns](https://www.anthropic.com/webinars/claude-code-advanced-patterns)
- [Vectimus — Deterministic Governance for AI Coding Agents](https://github.com/vectimus/vectimus)
- [AWS Bedrock AgentCore Policy (Cedar)](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html)
- [CodeScene AI Code Guardrails](https://codescene.com/use-cases/ai-code-quality)
- [Agent Behavioral Contracts (arxiv 2602.22302)](https://arxiv.org/abs/2602.22302)
- [Runtime Governance for AI Agents (arxiv 2603.16586)](https://arxiv.org/html/2603.16586)
- [Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit)
- [AI Code Quality in 2026: Guardrails for AI-Generated Code](https://tfir.io/ai-code-quality-2026-guardrails/)
- [The Agent Control Plane (CIO)](https://www.cio.com/article/4130922/the-agent-control-plane-architecting-guardrails-for-a-new-digital-workforce.html)
- [Top Runtime AI Governance Platforms 2026](https://accuknox.com/blog/runtime-ai-governance-security-platforms-llm-systems-2026)
