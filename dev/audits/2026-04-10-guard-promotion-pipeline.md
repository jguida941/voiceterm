# Guard Promotion Pipeline — Issue-to-Guard Learning Loop

**Date**: 2026-04-10
**Trigger**: PyQt6 test segfault — 44 window-creating tests with no tearDown
escaped all 64 guards and 13 probes. Operator direction: build a system where
every issue gets evaluated for deterministic guard promotion, portable to any
repo.

## 1. Root Cause: Why This Escaped

The guard/probe system is strong on **structural code shape** (complexity,
duplication, size) and **architectural boundaries** (layers, imports, contracts)
but **blind to test quality and resource lifecycle patterns**.

- `check_rust_test_shape.py` covers Rust test files only
- No Python test quality guard exists
- No probe checks for missing `tearDown`, unclosed resources, or test isolation
- The `probe_design_smells` probe looks at production code patterns, not test
  patterns

## 2. Gap Inventory

Investigation identified 12 gap categories. Sorted by deterministic
detectability and ROI:

### Tier 1 — Fully deterministic, high ROI (implement first)

| Gap | Detection method | Portable? |
|-----|-----------------|-----------|
| Test quality (missing tearDown, resource leaks in tests) | AST: find TestCase subclasses creating resources without cleanup | Yes |
| Resource lifecycle (open() without with, unclosed connections) | AST: find resource-acquiring calls without context managers | Yes |
| Error handling gaps (empty except handlers, re-raise without from) | AST: check handler bodies and raise chains | Yes |
| Dependency health (unused imports, shadowed builtins) | AST: name resolution | Yes |

### Tier 2 — Partially deterministic, medium ROI

| Gap | Detection method | Portable? |
|-----|-----------------|-----------|
| None/null safety (unchecked .get(), Optional without guard) | AST + type hints | Yes |
| Type safety (missing hints, Any overuse) | AST | Yes |
| Documentation sync (docstring params vs signature) | AST comparison | Yes |
| Security (hardcoded secrets, string interpolation in queries) | Regex + AST | Yes |

### Tier 3 — Needs semantic analysis, lower confidence

| Gap | Detection method | Portable? |
|-----|-----------------|-----------|
| Concurrency safety (Python async/threading) | Pattern matching | Partial |
| Performance (N+1, unbounded loops) | Control flow analysis | Partial |
| API contract violations (signature changes) | Cross-file graph | Partial |
| Config drift (env vars, feature flags) | Static + runtime | Partial |

## 3. Guard Promotion Pipeline Design

The core idea: every issue gets evaluated → if deterministically detectable →
draft guard/probe → validate → register → track.

### Flow

```
Issue found (crash, review, AI finding, audit)
    ↓
[1] Log finding via governance-review --record
    ↓
[2] AI evaluates: "Can this be caught deterministically?"
    - Yes + high confidence → draft guard (blocking)
    - Yes + low confidence → draft probe (advisory)
    - No → document as review checklist item
    ↓
[3] Draft guard/probe using template
    - dev/scripts/checks/check_<name>.py  (guard)
    - dev/scripts/checks/probe_<name>.py  (probe)
    ↓
[4] Validate: must detect all original findings + zero FP on full repo
    ↓
[5] Register in quality_policy, script_catalog, AGENTS.md
    ↓
[6] Track promotion rate + gap coverage in metrics
```

### What already exists (reuse, don't rebuild)

| Surface | Purpose | Status |
|---------|---------|--------|
| `Finding` contract | Issue identity | Exists |
| `GovernanceReviewInput` | Verdicts + prevention_surface | Exists |
| `ExternalFindingInput` | Issue intake | Exists |
| `PROBE_TEMPLATE_README.md` | Probe scaffolding | Exists |
| `quality_policy/defaults.py` | Guard registry | Exists |
| `check_agents_contract.py` | Guard consistency validation | Exists |
| `script_catalog.py` | Script registration | Exists |

### What needs to be built

| Artifact | Purpose |
|----------|---------|
| `promotion_metadata` field on `GovernanceReviewInput` | Link findings to guard candidates |
| `devctl guard-promotion-list` command | Render promotion queue |
| `devctl validate-guard-proposal` command | Validate draft guard against seeded findings |
| `devctl promote-guard` command | Auto-register validated guard |
| `GUARD_PROPOSAL_TEMPLATE.md` | Scaffolding for new guards (like PROBE_TEMPLATE_README.md) |
| `promotion_policy.json` in repo-pack config | Confidence thresholds, automation gates |

### Making it continuous (the rule)

The pipeline must fire automatically, not depend on someone remembering:

1. **On every governance-review record**: if `prevention_surface=guard` or
   `prevention_surface=probe`, auto-create a promotion candidate entry
2. **On every probe-report run**: if a probe pattern has been seen N+ times
   with 0 false positives, flag it for guard promotion
3. **On every push preflight**: `check_guard_promotion_queue.py` warns if
   there are stale unactioned candidates older than 14 days
4. **On CI**: promotion metrics feed into the governance dashboard

### Making it portable (any repo)

The entire promotion pipeline must work through repo-pack config, not
hardcoded paths:

- Guard templates resolve paths through `ProjectGovernance`
- Promotion thresholds live in `promotion_policy.json` (repo-pack owned)
- `validate-guard-proposal` runs against the adopting repo's tree, not
  VoiceTerm-specific fixtures
- Guard registration uses the existing `script_catalog.py` registry pattern

## 4. Immediate Next Steps

### For Claude (implement now)

1. Create `probe_test_quality.py` — catches the exact pattern that escaped:
   - TestCase subclasses with resource-creating setUp/test methods but no
     tearDown
   - Qt widget creation without cleanup
   - File/connection opens without context manager in test code
2. Create `GUARD_PROPOSAL_TEMPLATE.md` — scaffolding for drafting new guards

### For Codex (review + design)

1. Review the gap inventory — are there categories we missed?
2. Review the promotion pipeline design — does it align with the existing
   governance architecture?
3. Decide: should promotion metadata be a new contract or extend
   `GovernanceReviewInput`?
4. Scope MP items for the promotion pipeline implementation
5. Investigate: which existing probes have enough signal to promote to guards?

## 5. Evidence

- Segfault trace: `ui_refresh.py:487` → `main_window.py:512` →
  `test_ui_layouts.py:275`
- Fix: `_WindowCleanupMixin` added to 7 test classes (commit `304708c2`)
- Full guard inventory: 64 hard guards, 13→25 review probes (after expansion)
- Full push passed: `a325bdae` → all 103 checks green
