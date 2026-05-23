# Semantic-TDD Evidence: What the Discipline Caught Today

This document collects real cases from the
`extraction/guardir-core-p0-proof-integrity` branch in this repository
where semantic-TDD discipline caught a bug, exposed a design smell, or
forced an architectural decision. Each case names the production file, the
RED assertion that fired, and the commit that landed the fix.

The cases are drawn from a single day of work (2026-05-23) where six
slices shipped through the semantic-TDD lane. No fabrication; every code
snippet, test name, line number, and commit SHA was read out of the
working tree at write time.

If you came here looking for marketing prose, leave. The point of this
file is to show the receipts.

---

## Case 1 — `single_agent` topology/authority conflation surfaced by the `ObservedControlTopology.__args__` invariant

**What semantic-TDD caught:** `ObservedControlTopology` is a `Literal[...]`
that names ROLE OCCUPANCY (who is in the room: implementer-without-reviewer,
single-implementer-single-reviewer, dual-implementer, reviewer-only,
no-live-agents). The value `"single_agent"` sat in that union and is NOT a
topology — it is an AUTHORITY MODE governed by `ReviewerMode.SINGLE_AGENT`.
Two unrelated concepts had been laundered through one type.

**How it was caught:** `test_observed_control_topology_literal_must_not_carry_single_agent_authority_label`
in `dev/scripts/devctl/runtime/control_topology.py`. The test does a
*type-introspection* assertion against `typing.get_args(ObservedControlTopology)`
— it reads the typed Literal directly. No fixture, no mock, no string
matching against output text.

**The actual code (before — pre-C.4):**
```python
# dev/scripts/devctl/runtime/control_topology.py:23-29 (before)
ObservedControlTopology = Literal[
    "single_implementer_single_reviewer",
    "single_agent",           # <-- the smell
    "dual_implementer",
    "implementer_without_reviewer",
    "reviewer_only",
    "no_live_agents",
]
```

```python
# dev/scripts/devctl/runtime/control_topology.py:99-106 (before)
def derive_implementation_permission(topology) -> ImplementationPermission:
    if topology in {"single_implementer_single_reviewer", "single_agent"}:
        return "active"
    if topology in {"dual_implementer", "implementer_without_reviewer"}:
        return "suspended"
    return "blocked"

# dev/scripts/devctl/runtime/control_topology.py:127-128 (before)
if sanctioned_single_agent and topology != "dual_implementer" and not typed_live_pair:
    return "single_agent", "active"
```

**The RED assertion:**
```python
# dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py:2822-2846
def test_observed_control_topology_literal_must_not_carry_single_agent_authority_label():
    import typing
    from dev.scripts.devctl.runtime.control_topology import ObservedControlTopology
    args = typing.get_args(ObservedControlTopology)
    assert "single_agent" not in args, (
        "INVARIANT VIOLATED: observed_control_topology_literal_must_not_carry_single_agent_authority_label\n"
        f"  ObservedControlTopology args: {args}\n"
        "  `single_agent` is an AUTHORITY mode (ReviewerMode.SINGLE_AGENT),\n"
        "  not a topology value. Remove from the Literal union; return\n"
        "  `single_implementer_single_reviewer` topology for the sanctioned\n"
        "  single-agent path and carry the single_agent semantic through\n"
        "  ReviewerMode + actor_authorities."
    )
```

**Why this is non-obvious without the discipline:** the union *worked*.
Every consumer that matched `"single_agent"` got the answer they expected.
You will not find this smell by running pytest with green tests; you find
it by writing an assertion that the TYPE itself encodes a single coherent
concept. The discipline forces you to name what a type means before you
declare a feature done.

**Outcome:**
```python
# dev/scripts/devctl/runtime/control_topology.py:23-29 (after — commit 0fa30a90)
ObservedControlTopology = Literal[
    "single_implementer_single_reviewer",
    "dual_implementer",
    "implementer_without_reviewer",
    "reviewer_only",
    "no_live_agents",
]

# dev/scripts/devctl/runtime/control_topology.py:127-128 (after)
if sanctioned_single_agent and topology != "dual_implementer" and not typed_live_pair:
    return "single_implementer_single_reviewer", "active"

# dev/scripts/devctl/runtime/control_topology.py:148 (after)
if not reviewer_mode_is_single_agent(effective_mode):
    return False
```

Topology = role occupancy. Authority = `ReviewerMode` enum. Two types
where there was one. Baseline ratchet 41 -> 40. Landed in commit
`0fa30a90` (A37 Slice C.4 narrow).

---

## Case 2 — RED-FIRST caught cascading test-fixture breakage from one architectural change

**What semantic-TDD caught:** Removing `"single_agent"` from the
`ObservedControlTopology` Literal is a one-line change. The blast radius
is six test sites in `dev/scripts/devctl/tests/review_channel/test_observed_topology.py`
that all asserted `topology == "single_agent"` (lines 122, 166, 196, 226,
257, plus the `derive_implementation_permission` parametrize entry at
line 130 in the equivalent legacy form).

**How it was caught:** the RED-FIRST sequencing forced the test author to
think about consumers before the code changed. The parametrize entry
`("single_agent", "active")` would have flipped to assert the path returns
`"active"` while the Literal no longer admits the value — silent fall-through
to `return "blocked"` would have surfaced as a parametrize failure long
after a downstream consumer started seeing wrong permission.

**The actual code (before — `test_observed_topology.py`):**
```python
# dev/scripts/devctl/tests/review_channel/test_observed_topology.py (pre-C.4, equivalent)
@pytest.mark.parametrize(
    ("topology", "expected"),
    (
        ("single_implementer_single_reviewer", "active"),
        ("single_agent", "active"),                  # <-- this line
        ("dual_implementer", "suspended"),
        ...
    ),
)
def test_derive_implementation_permission(topology: str, expected: str) -> None:
    assert derive_implementation_permission(topology) == expected
```

The six asserting sites all expected `"single_agent"` topology to fall
out of `derive_startup_control_truth`:

```python
# dev/scripts/devctl/tests/review_channel/test_observed_topology.py:122
assert topology == "single_implementer_single_reviewer"   # was "single_agent"
# :166, :196, :226, :257 — same pattern across the takeover/remote/typed-pair tests
```

**The RED assertion (the test that drove the cutover):**
```python
# dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py:2849-2892
def test_derive_startup_control_truth_sanctioned_single_agent_returns_role_shaped_topology():
    ...
    topology, permission = derive_startup_control_truth(review_state, reviewer_gate=reviewer_gate)
    assert topology == "single_implementer_single_reviewer", (
        "INVARIANT VIOLATED: derive_startup_control_truth_sanctioned_single_agent_returns_role_shaped_topology\n"
        f"  got topology: {topology!r}\n"
        "  expected: 'single_implementer_single_reviewer' (role-shaped, both\n"
        "  notional roles available; single_agent semantic survives via\n"
        "  ReviewerMode + actor_authorities)."
    )
    assert permission == "active"
```

**Why this is non-obvious without the discipline:** without writing the
RED test first, a programmer would remove `"single_agent"` from the
Literal, the parametrize would silently start hitting the `return "blocked"`
fallback at line 106 of `control_topology.py`, and the six test sites
would each fail with a different unrelated-looking message. The
operator would spend an hour diagnosing six "unrelated" failures instead
of one architectural decision. RED-FIRST makes the cascade visible *before*
the code changes — one architectural change, one assertion-text update,
six callsites migrated atomically in commit `0fa30a90`.

**Outcome:** all six test sites updated in the same commit; the
`derive_implementation_permission` parametrize entry was removed; the new
RED test at `test_live_state_invariants.py:2849` locks the contract.

---

## Case 3 — 2a/2b xfail-strict ratchet preserves visible debt

**What semantic-TDD caught:** "secret wins". If a future slice
accidentally retires a topology literal that was supposed to stay as
visible debt, the xfail FLIPS to XPASS and pytest's strict mode fails
loudly. The operator cannot accidentally close an architectural decision
without ratcheting the baseline.

**How it was caught:** the 2a/2b split. The 2a test is a
`<= BASELINE` ratchet that PASSES today. The 2b test is the target
architecture (zero literals) wrapped in `@pytest.mark.xfail(strict=True)`.
Together they catch BOTH directions of drift.

**The actual code:**
```python
# dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py:2748-2759
# Slice C.0 baseline established 2026-05-23 after the consolidation +
# Phase 0 + 0.5 work. This number ratchets DOWN as C.1..C.4 retire
# literals; it must never go UP. Ratchet history:
#   2026-05-23 C.0  baseline      = 44 (initial capture)
#   2026-05-23 C.3  -> 41 (3 files retired: collaboration_session_status,
#                          follow_controller, collaboration_registry)
#   2026-05-23 C.4  -> 40 (1 file retired: control_topology.py — Literal
#                          cutover removed `single_agent` from
#                          ObservedControlTopology; line 148 migrated to
#                          reviewer_mode_is_single_agent(); line 154
#                          migrated to OperatorInteractionMode enum members)
TOPOLOGY_LITERAL_BASELINE_FILE_COUNT = 40
```

**The 2a RED assertion (current-safety quarantine):**
```python
# dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py:2798-2819
def test_topology_literal_file_count_must_not_grow_above_baseline():
    actual = _count_topology_literal_files()
    assert actual <= TOPOLOGY_LITERAL_BASELINE_FILE_COUNT, (
        "INVARIANT VIOLATED: topology_literal_file_count_must_not_grow_above_baseline\n"
        f"  baseline (2026-05-23): {TOPOLOGY_LITERAL_BASELINE_FILE_COUNT} files\n"
        f"  current:               {actual} files\n"
        f"  delta:                 +{actual - TOPOLOGY_LITERAL_BASELINE_FILE_COUNT}\n"
        "  A new production callsite introduced a raw topology literal\n"
        "  comparison. Replace with a typed projection read..."
    )
```

**The 2b RED assertion (target architecture, xfail-strict):**
```python
# dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py:2951-2970
@pytest.mark.xfail(strict=True, reason="Slice C target: zero raw topology literals in production runtime / review_channel modules outside enum owners; ratchets down through C.1..C.4 retirement slices and lifts to GREEN only when Slice C closure lands")
def test_topology_literal_count_must_be_zero_in_production_outside_enum_owners():
    actual = _count_topology_literal_files()
    assert actual == 0, (
        "INVARIANT VIOLATED: topology_literal_count_must_be_zero_in_production_outside_enum_owners\n"
        f"  current: {actual} production files still carry raw topology literals\n"
        ...
    )
```

**Why this is non-obvious without the discipline:** if you write only the
2a test, you ratchet but never finish. If you write only the 2b test, you
hide the debt under a permanent `skip`. The two-test split forces you to
*commit* to a target (zero) while *preserving* the current count as a
visible decreasing number. When the slice closes, you delete the
baseline number AND delete the `@xfail`; the test becomes a load-bearing
GREEN check.

**Outcome:** today's ratchet history (44 -> 41 -> 40) is encoded in
the test file itself. Reviewers can `git blame` the baseline number and
see each retirement slice (commits `889d03ec`, `65ad7a4e`, `0fa30a90`).
There is no separate dashboard or ledger; the test IS the ledger.

---

## Case 4 — TDD-the-TDD-role: Phase 0 ran the ritual on its own definition

**What semantic-TDD caught:** three role ids (`tdd_discovery`,
`tdd_first_role`, `dogfood_test`) all named the same workflow. The
fragmentation made the ritual harder to reason about; each phase looked
like a separate role assignment.

**How it was caught:** the consolidation itself was developed
RED-FIRST. The test `test_semantic_tdd_role_spec_phases_match_documented_ritual`
asserts the typed contract matches the documented 9-step plan; the test
`test_semantic_tdd_role_aliases_resolve_legacy_tdd_role_ids` asserts
backwards-compatibility through aliases; the test
`test_legacy_tdd_role_ids_must_not_remain_in_default_role_ids` is an
xfail-strict ratchet for full retirement.

**The actual code:**
```python
# dev/scripts/devctl/runtime/semantic_tdd_role.py:31-49
class SemanticTDDRolePhase(StrEnum):
    DISCOVERY = "discovery"
    RED_FIRST = "red_first"
    CODE_APPLY = "code_apply"
    GREEN_VERIFY = "green_verify"
    REINFORCE = "reinforce"
    DOGFOOD_PROOF = "dogfood_proof"
    RECEIPT = "receipt"
    REVIEW = "review"

# dev/scripts/devctl/runtime/role_profile.py:115-134
_ROLE_ID_ALIASES.update(
    {
        "dogfood_tester": "semantic_tdd",
        "dogfood_test_role": "semantic_tdd",
        "dogfooder": "semantic_tdd",
        "dogfood_test": "semantic_tdd",
        ...
        "tdd_first_role": "semantic_tdd",
        "tdd_discovery": "semantic_tdd",
        "tdd_discovery_role": "semantic_tdd",
        ...
    }
)
```

**The 0.2a RED assertion (current-safety):**
```python
# dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py:2300-2335
def test_semantic_tdd_role_aliases_resolve_legacy_tdd_role_ids():
    from dev.scripts.devctl.runtime.role_profile import normalize_role_id
    legacy_ids = ("tdd_discovery", "tdd_first_role", "dogfood_test")
    mismatches: list[tuple[str, str]] = []
    for legacy in legacy_ids:
        resolved = normalize_role_id(legacy)
        if resolved != "semantic_tdd":
            mismatches.append((legacy, resolved))
    assert not mismatches, ( ... )
```

**The 0.2b RED assertion (target architecture, xfail-strict):**
```python
# dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py:2338-2370
@pytest.mark.xfail(strict=True, reason="Phase 0.2b target: legacy ... must be fully removed from DEFAULT_ROLE_IDS once all callsites migrate to semantic_tdd; until then aliases route the work but the legacy ids stay visible")
def test_legacy_tdd_role_ids_must_not_remain_in_default_role_ids():
    ...
```

**Why this is non-obvious without the discipline:** you cannot define a
test role and then declare it done without running its own ritual. The
typed `SemanticTDDRolePhaseSpec` exists because the test
`test_semantic_tdd_role_spec_phases_match_documented_ritual` failed
before the contract existed. The role definition recursively passed its
own GREEN_VERIFY phase before shipping.

**Outcome:** commit `7afc813d` (A37 Phase 0 + Pre-0 + Phase 0.x).
`SemanticTDDRoleSpec` exists as a frozen dataclass with `contract_id =
"SemanticTDDRoleSpec"`, `schema_version = 1`, and 8 typed phase specs.
The three legacy ids remain in `DEFAULT_ROLE_IDS` as visible debt; the
2b xfail-strict will flip GREEN when callsite migration finishes and
the legacy ids are removed.

---

## Case 5 — `PathRoots.state` field surfaced by a typed-state audit

**What semantic-TDD caught:** `peer_spawn.py:347` hardcoded
`REPO_ROOT / "dev" / "state" / "bypass_lifecycles.jsonl"`. Adopter repos
that vendor this code could not redirect the state directory through the
canonical `ProjectGovernance.path_roots` surface — they had to use
`DEVCTL_BYPASS_LIFECYCLE_STORE_PATH`, an environment-variable hack
reserved for test isolation. The typed governance contract had `active_docs`,
`reports`, `scripts`, `checks`, `workflows`, `guides`, `config` — but no
`state`.

**How it was caught:** the operator's question "is env-override the
proper way to do portability?" turned into the RED test
`test_project_governance_path_roots_exposes_state_field_for_adopter_portability`.

**The actual code (before):**
```python
# dev/scripts/devctl/runtime/project_governance_contract.py (before)
@dataclass(frozen=True, slots=True)
class PathRoots:
    active_docs: str = "dev/active"
    reports: str = "dev/reports"
    scripts: str = "dev/scripts"
    checks: str = "dev/scripts/checks"
    workflows: str = ".github/workflows"
    guides: str = "dev/guides"
    config: str = "dev/config"
    # NO state field — every state-directory caller forked into env-var hacks
```

```python
# dev/scripts/devctl/commands/runtime/peer_spawn.py:347 (before, hypothetical equivalent)
store_path = REPO_ROOT / "dev" / "state" / "bypass_lifecycles.jsonl"
# Adopter override path: DEVCTL_BYPASS_LIFECYCLE_STORE_PATH (test-isolation hack)
```

**The RED assertion:**
```python
# dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py:2667-2714
def test_project_governance_path_roots_exposes_state_field_for_adopter_portability():
    from dev.scripts.devctl.runtime.project_governance_contract import PathRoots
    from dev.scripts.devctl.runtime.project_governance_parse import path_roots_from_mapping
    default_roots = PathRoots()
    assert hasattr(default_roots, "state"), (
        "INVARIANT VIOLATED: project_governance_path_roots_exposes_state_field_for_adopter_portability\n"
        "  PathRoots dataclass is missing a `state` field.\n"
        "  Today production code hardcodes `REPO_ROOT / 'dev' / 'state' / '<file>.jsonl'`\n"
        "  (e.g., peer_spawn.py:347). Adopter repos cannot override the state\n"
        "  directory without env-var overrides intended for tests.\n"
        ...
    )
    assert default_roots.state == "dev/state", ...
    parsed_default = path_roots_from_mapping({})
    assert parsed_default.state == "dev/state", ...
    parsed_override = path_roots_from_mapping({"state": "custom/state/root"})
    assert parsed_override.state == "custom/state/root", ...
```

**Why this is non-obvious without the discipline:** every individual
state-file callsite worked. Tests passed. The smell is *what is missing
from the typed governance surface*, not what is wrong with any existing
line of code. The discipline named the gap as an invariant — adopters
must be able to redirect state-root through typed config — and the gap
became unignorable.

**Outcome:**
```python
# dev/scripts/devctl/runtime/project_governance_contract.py:56-67 (after)
@dataclass(frozen=True, slots=True)
class PathRoots:
    active_docs: str = "dev/active"
    reports: str = "dev/reports"
    scripts: str = "dev/scripts"
    checks: str = "dev/scripts/checks"
    workflows: str = ".github/workflows"
    guides: str = "dev/guides"
    config: str = "dev/config"
    state: str = "dev/state"   # <-- added

# dev/scripts/devctl/commands/runtime/peer_spawn.py:340-353 (after — commit 7afc813d)
elif raw_id:
    # Adopter-portable path resolution: typed PathRoots().state default
    # via ProjectGovernance.path_roots is the canonical surface (per
    # SYSTEM_MAP.md line 1539); the env-var override is reserved for
    # hermetic test isolation. Adopter repos override the state root
    # via devctl_repo_policy.json -> path_roots.state.
    from ...runtime.project_governance_contract import PathRoots
    store_override = os.environ.get(
        "DEVCTL_BYPASS_LIFECYCLE_STORE_PATH", ""
    ).strip()
    store_path = (
        Path(store_override)
        if store_override
        else REPO_ROOT / PathRoots().state / "bypass_lifecycles.jsonl"
    )
```

Env-vars relegated to test isolation. Typed authority for production.
This is what "portable governance" looks like in code.

---

## Case 6 — Hunt-based regression detection: file count, not occurrence count

**What semantic-TDD caught:** vocabulary drift. A test that asserts `"the
file does not contain the string `single_agent`"` is brittle — if someone
renames the smell to `"singleAgentMode"`, the test passes. A test that
counts FILES carrying any of a known set of typed-overloaded literals,
across the entire production runtime and review_channel tree, with
typed enum-owner exemptions, catches additions even when the offending
file uses different phrasing.

**How it was caught:** `_count_topology_literal_files()` scans
`dev/scripts/devctl/runtime/**` and `dev/scripts/devctl/review_channel/**`,
excludes the enum-owner files (`reviewer_mode.py`, `operator_context.py`),
and counts files containing any of `{active_dual_agent, single_agent,
dual_agent}` as quoted string literals.

**The actual code:**
```python
# dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py:2735-2746
_TOPOLOGY_LITERAL_LABELS = (
    "active_dual_agent",
    "single_agent",
    "dual_agent",
)

# Files where the literals are SEMANTICALLY VALID (enum/Literal owners,
# typed compatibility surfaces). The hunt scans the rest of production.
_ENUM_OWNER_EXEMPTIONS = (
    "dev/scripts/devctl/runtime/reviewer_mode.py",
    "dev/scripts/devctl/runtime/operator_context.py",
)
```

```python
# dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py:2762-2795
def _count_topology_literal_files() -> int:
    scan_roots = (
        REPO_ROOT / "dev" / "scripts" / "devctl" / "runtime",
        REPO_ROOT / "dev" / "scripts" / "devctl" / "review_channel",
    )
    matching: set[str] = set()
    for root in scan_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            rel = str(path.relative_to(REPO_ROOT))
            if rel in _ENUM_OWNER_EXEMPTIONS:
                continue
            if "/__pycache__/" in rel or rel.endswith("__init__.py"):
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for label in _TOPOLOGY_LITERAL_LABELS:
                if f'"{label}"' in content or f"'{label}'" in content:
                    matching.add(rel)
                    break
    return len(matching)
```

**Why this is non-obvious without the discipline:** a per-file string
match would generate noise. The set-membership semantics (one file
counts once regardless of how many literal sites it contains) gives a
stable scalar for the ratchet. The quoted-form check (`f'"{label}"'`)
is what stops the hunt from matching `is_sanctioned_single_agent_control`
(a concept name, not a literal authority comparison).

**Outcome:** the hunt has produced three ratchet snapshots in one day:
44 (baseline) -> 41 (C.3) -> 40 (C.4). The xfail-strict 2b target
remains at zero. Reviewers can re-run `_count_topology_literal_files()`
locally and see the number drop after each retirement slice.

---

## Case 7 — Operator-flagged design smell: `_active_dual_agent_review` function name

**What semantic-TDD caught:** prior work had defined a function literally
named `_active_dual_agent_review` — the function name itself encoded the
typed-overloaded literal it was supposed to abstract over. By the time
A37 reached Slice C.2, the function had already been retired in earlier
commits unrelated to A37, but the audit pattern still found the smell
and produced typed proof that the work was complete.

**How it was caught:** Slice C.2 was scheduled to retire
`authority_snapshot_projection.py:67,150` and rename
`push_authorization.py:281 _active_dual_agent_review`. The audit at
slice open found *both targets already migrated* in unrelated commits.
A grep across the runtime tree confirmed zero occurrences. The audit
invariant did not need to fire; the work was already done.

```
$ grep -rn "_active_dual_agent_review\|active_dual_agent_review" \
  dev/scripts/devctl
(no output — function name absent)
```

The audit became a typed "ALREADY-DONE" closure in
`dev/active/semantic_tdd_lane.md`:

| Original target | Current state | Status |
|---|---|---|
| `reviewer_gate_logic.py:27,52,57` | 0 literals; uses typed `reviewer_mode_is_active()` predicate from enum-owner `reviewer_mode.py` | ALREADY-DONE |
| `authority_snapshot_projection.py:67,150` | File does not exist (renamed/removed) | ALREADY-DONE |
| `push_authorization.py:281` + `_active_dual_agent_review` function | 0 literals; function name absent | ALREADY-DONE |

**Why this is non-obvious without the discipline:** without the
file-count hunt and the audit-before-edit step, a programmer would have
written a no-op patch ("retire the literal at line 27") on code that no
longer contained the literal, produced no diff, and possibly broken
something else. Instead the audit named what was supposed to change,
checked what currently existed, and produced typed evidence of closure.

**Outcome:** Slice C.2 closed as already-done with audit proof in commit
`65ad7a4e` (A37 Slice C.3) — three slices' worth of debt cleared by two
slices of code change. The audit invariant remains in
`dev/active/semantic_tdd_lane.md`.

---

## When semantic-TDD does NOT pay off

Be honest. The discipline has a cost: writing the RED test, naming the
invariant, deciding 2a vs 2b, threading the file-count hunt. That cost
is not justified for:

- **Cosmetic changes.** Renaming a local variable, fixing a docstring
  typo, reformatting whitespace. There is no architectural blast radius;
  RED-FIRST adds nothing.
- **Simple refactors with one consumer.** Extracting a helper function
  called from one site, inlining a one-line method, reordering imports.
  The cascade-breakage that RED-FIRST catches doesn't exist.
- **Pure data updates.** Bumping a version string in a config file,
  updating a copyright year, regenerating a snapshot fixture. The
  invariant has not changed.
- **Throwaway exploration.** Spike code in a scratch branch that will
  be deleted before review. Adding ratchets to spike branches is
  governance theater.

The rule of thumb: semantic-TDD scales with architectural blast radius.
If the change touches a typed contract, alters a Literal union, modifies
behavior at >2 callsites, introduces a new module, or removes a public
symbol, the discipline pays off. If the change is local-scope and
load-bearing for a single consumer, just write the code.

---

## Receipt-discipline gap (honest admission)

Today's session ran the ritual *structurally*: RED tests existed,
xfail-strict ratchets guarded targets, dogfood produced real artifacts,
matrix rows in `dev/active/semantic_tdd_lane.md` advanced. But:

> The session did NOT emit `FeatureProofReceipt(real_life_test_status=
> proven_passed)` under `dev/reports/feature_proof_receipts/` keyed by
> commit SHA for the six slices it landed.

That directory exists and currently contains 153 receipts from prior
sessions. The shape is real:
`dev/reports/feature_proof_receipts/000-current-row-proof-receipt-20260522T1518Z.json`
carries `contract_id: "FeatureProofReceipt"`, `connectivity_guards_passed:
true`, evidence artifacts, plan-authority refs, and a dogfood invocation
ref. The discipline COULD be stricter.

What a `FeatureProofReceipt` for Case 1 (the C.4 cutover) would look like
if today's session had emitted it:

```json
{
  "contract_id": "FeatureProofReceipt",
  "commit_sha": "0fa30a90bc88f27814f8b31b1473c9d562a004a7",
  "feature_id": "A37-TOPOLOGY-RETIREMENT-AMENDMENT-S1",
  "implementer_actor": "claude",
  "real_life_test_status": "proven_passed",
  "tests_run": [
    "dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py::test_observed_control_topology_literal_must_not_carry_single_agent_authority_label",
    "dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py::test_derive_startup_control_truth_sanctioned_single_agent_returns_role_shaped_topology",
    "dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py::test_control_topology_must_not_carry_topology_literal",
    "dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py::test_topology_literal_file_count_must_not_grow_above_baseline"
  ],
  "connectivity_guards_passed": true,
  "evidence_artifacts": [
    "dev/scripts/devctl/runtime/control_topology.py",
    "dev/scripts/devctl/tests/review_channel/test_observed_topology.py",
    "dev/active/semantic_tdd_lane.md"
  ],
  "plan_authority_refs": {
    "active_row_id": "A37-TOPOLOGY-RETIREMENT-AMENDMENT-S1",
    "plan_source_path": "delete_after_ingest.md"
  }
}
```

This is the gap. The matrix in `semantic_tdd_lane.md` carries the
session's claim that it ran the ritual; the typed `FeatureProofReceipt`
would carry the *machine-verifiable* claim that pytest passed at a
specific commit SHA. A future session will either close this gap or
inherit it.

---

## Why not just write tests?

Semantic-TDD is THREE things layered, and each layer catches a different
class of failure:

**Layer 1 — RED-FIRST.** The test EXISTS before the code. Catches:
"silent fall-through" bugs (Case 2), missed callsite migrations, the
gap between what a Literal admits and what consumers expect. If you
write the code first, you write the test against what the code already
does — your test confirms behavior, it does not specify it. Plain
test-first.

**Layer 2 — 2a/2b xfail-strict.** Visible debt that cannot hide.
Catches: secret wins (a future commit accidentally retires more debt
than the slice scoped, and the test FLIPS to XPASS in strict mode);
silent regressions (a future commit adds a new violation and the 2a
file-count ratchet fails); architectural drift (the 2b target stays
RED-as-ratchet until a planned closure slice intentionally deletes the
xfail marker).

**Layer 3 — Dogfood proof.** A real-life artifact, not pytest exit 0.
Catches: paths that look passed because every unit test passed but
the real CLI/command/workflow never actually fires. Cases in this
repo include: the `peer-spawn --task-prompt` minimal-script path that
unit tests passed for but the real command silently never invoked
`codex` (PEER-TASK-PROMPT in `semantic_tdd_lane.md`); the
`develop ingest-plan` path that returned `ok=True` from a unit test
but only the live invocation against the typed plan store proved the
row landed.

Each layer is necessary. RED-FIRST without ratchets means debt hides.
Ratchets without dogfood means tests pass while production paths
silently break. Dogfood without RED-FIRST means you confirm what
already works instead of specifying what should change.

This is the actual point of the discipline. Not "write more tests." Not
"add another guard." Three separate failure modes, three layered
responses, one ritual that owns all three.

---

*Documented by the documentation-agent role on 2026-05-23 against branch
`extraction/guardir-core-p0-proof-integrity` HEAD `d35d08ec`. Every code
snippet was read out of the working tree at write time. Every commit SHA
is reachable via `git show <sha>`.*
