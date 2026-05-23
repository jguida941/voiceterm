"""TDD-discovery audit: are the 17 new G23-G40 + Invariant H/C + topology
implementations actually CONNECTED to the running system, or just isolated
unit tests claiming GREEN?

Operator assertion: claude shipped 17 implementations this session, each
passing its own unit tests. The proof-of-correctness definition in
``delete_after_ingest.md`` (lines 469-476) explicitly disallows declaring
GREEN from unit tests alone; GREEN requires:
  - multi-attempt durability
  - dogfood proof
  - receipt
  - final gate output not referencing a packet id

Per the AntiDumbass Role-Boundary Amendment (lines 731-870) and the TDD
role definition (lines 776-781), the TDD-discovery role writes the failing
assertion first. A test that FAILS here is the discovery of a real
disconnection between guard code and running system.

The 17 implementations under audit
----------------------------------
G23  packet_body_observation_route
G24  action_request_expiry_refresh
G25  loose_chat_to_typed_lane
G26  reviewer_result_transition
G27  continuation_anchor_enforcement
G30  role_delegation_authority
G31  role_cardinality_bounds
G32  write_lease_conflicts (recently consolidated with
     ``scope_path_claims.paths_overlap``)
G33  child_actor_scope
G34  shared_round_state_observed
G35  peer_lease_visibility
G36  patch_submission_merge_gate
G37  multi_actor_merge_conflict
G38  role_round_closure
G39  subagent_no_commit_push
G40  packet_hygiene_enforcement
Invariant H  ``unsafe_continue_with_edit_grant`` rule in
             check_role_lane_mutation_authority
Invariant C  ``MissingDecisionRefreshHint`` in control_decision_obedience
Topology     hardcoded 4-site sweep: event_handler,
             development_collaboration_profiles, peer_awareness,
             control_topology_bridge_counts

Test markers
-------------
- Tests prefixed ``test_red_*`` are EXPECTED TO FAIL on current code. A
  failure here is the connectivity-gap discovery. ``-v`` will print each
  one explicitly.
- This file performs NO mutations and writes NO files. It only inspects
  source, registry state, and runs the live guard runtime modules in
  pure-Python.

Plan refs:
- delete_after_ingest.md lines 311-333 (Jump Index G23-G40)
- delete_after_ingest.md lines 469-476 (GREEN definition)
- delete_after_ingest.md lines 731-870 (AntiDumbass role boundary)
- delete_after_ingest.md lines 776-781 (TDD-discovery role rule)
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Repo path resolution (this file lives 5 dirs deep under repo root)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_REGISTRY_PATH = REPO_ROOT / "dev/state/contract_registry.jsonl"
QUALITY_DEFAULTS_PATH = (
    REPO_ROOT / "dev/scripts/devctl/quality_policy/defaults.py"
)
SCRIPT_CATALOG_ENTRIES_PATH = (
    REPO_ROOT / "dev/scripts/devctl/governance/script_catalog_entries.py"
)
EVENT_HANDLER_PATH = (
    REPO_ROOT / "dev/scripts/devctl/commands/review_channel/event_handler.py"
)
DEVELOPMENT_COLLAB_PATH = (
    REPO_ROOT
    / "dev/scripts/devctl/runtime/development_collaboration_profiles.py"
)
PEER_AWARENESS_PATH = (
    REPO_ROOT / "dev/scripts/devctl/commands/agent_mind/peer_awareness.py"
)
BRIDGE_COUNTS_PATH = (
    REPO_ROOT / "dev/scripts/devctl/runtime/control_topology_bridge_counts.py"
)


# Canonical guard-id list for the 17 implementations under audit. Order is
# stable so a single PASS/FAIL matrix can be assembled per section in the
# returned report.
IMPLS_UNDER_AUDIT: tuple[tuple[str, str], ...] = (
    ("G23", "packet_body_observation_route"),
    ("G24", "action_request_expiry_refresh"),
    ("G25", "loose_chat_to_typed_lane"),
    ("G26", "reviewer_result_transition"),
    ("G27", "continuation_anchor_enforcement"),
    ("G30", "role_delegation_authority"),
    ("G31", "role_cardinality_bounds"),
    ("G32", "write_lease_conflicts"),
    ("G33", "child_actor_scope"),
    ("G34", "shared_round_state_observed"),
    ("G35", "peer_lease_visibility"),
    ("G36", "patch_submission_merge_gate"),
    ("G37", "multi_actor_merge_conflict"),
    ("G38", "role_round_closure"),
    ("G39", "subagent_no_commit_push"),
    ("G40", "packet_hygiene_enforcement"),
    ("InvariantH", "role_lane_mutation_authority"),
)


# Typed-shape contract ids the guards advertise via ``contract_id`` /
# ``CONTRACT_ID`` and that should therefore appear in
# ``dev/state/contract_registry.jsonl``. These names come from grepping the
# guard sources directly:
#   RoleLaneMutationAuthorityGuard, RoleCardinalityBoundsGuard,
#   PacketHygieneEnforcementGuard, MissingDecisionRefreshHint, ...
EXPECTED_CONTRACT_IDS: tuple[str, ...] = (
    "RoleLaneMutationAuthorityGuard",
    "RoleCardinalityBoundsGuard",
    "PacketHygieneEnforcementGuard",
    "MissingDecisionRefreshHint",
    "RoleLaneViolation",
    "RoleCardinalityViolation",
    "HygieneViolation",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_contract_registry() -> tuple[Mapping[str, object], ...]:
    if not CONTRACT_REGISTRY_PATH.exists():
        return ()
    rows: list[Mapping[str, object]] = []
    for line in CONTRACT_REGISTRY_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return tuple(rows)


def _registry_contract_ids() -> frozenset[str]:
    return frozenset(
        str(row.get("contract_id") or "") for row in _read_contract_registry()
    )


def _quality_policy_script_ids() -> tuple[str, ...]:
    """Return script_ids currently registered in DEFAULT_AI_GUARD_SPECS."""
    from dev.scripts.devctl.quality_policy.defaults import (
        DEFAULT_AI_GUARD_SPECS,
    )

    return tuple(spec.script_id for spec in DEFAULT_AI_GUARD_SPECS)


def _script_catalog_entries() -> dict[str, str]:
    """Return script_id -> filename mapping in the canonical check catalog."""
    from dev.scripts.devctl.governance.script_catalog_entries import (
        CHECK_SCRIPT_ENTRIES,
    )

    return dict(CHECK_SCRIPT_ENTRIES)


# ---------------------------------------------------------------------------
# Section 1 — Contract registry connection
# ---------------------------------------------------------------------------


def test_red_contract_registry_carries_typed_shapes_from_17_impls():
    """Any guard advertising ``contract_id`` / ``CONTRACT_ID`` MUST be
    registered in ``dev/state/contract_registry.jsonl``. Otherwise the typed
    shape is private to the guard and no other surface can compose against
    it (no consumer count, no parity command, no fixture path).

    GREEN definition (delete_after_ingest.md lines 469-476) excludes
    "unit tests only" — the typed contract has to be inspectable from the
    central registry.
    """
    registry = _registry_contract_ids()
    missing = sorted(c for c in EXPECTED_CONTRACT_IDS if c not in registry)
    assert not missing, (
        "Contract registry is missing typed shapes advertised by the 17 "
        "guard implementations. Each guard returns a payload labeled with "
        f"these ``contract_id`` strings but none are registered: {missing}. "
        "Without registry entries, system-map, platform-contracts, and "
        "context-graph cannot link consumers to these contracts."
    )


# ---------------------------------------------------------------------------
# Section 2 — script_catalog_entries.py connection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("g_label", "script_id"),
    IMPLS_UNDER_AUDIT,
    ids=[g for g, _ in IMPLS_UNDER_AUDIT],
)
def test_green_script_catalog_has_entry(g_label: str, script_id: str):
    """Each of the 17 implementations MUST appear in the canonical
    ``CHECK_SCRIPT_ENTRIES`` registry so check-router, profile loaders, and
    pre-commit coverage scanners can address them. Cleanup-subagent claimed
    to add 15; verify all 17.
    """
    entries = _script_catalog_entries()
    assert script_id in entries, (
        f"{g_label} ({script_id}) is NOT in CHECK_SCRIPT_ENTRIES. The check "
        f"file may exist at dev/scripts/checks/check_{script_id}.py but no "
        f"governance surface can resolve it without the catalog row."
    )
    expected_filename = f"check_{script_id}.py"
    actual_filename = entries[script_id]
    assert actual_filename == expected_filename, (
        f"{g_label} ({script_id}) maps to {actual_filename!r}, expected "
        f"{expected_filename!r}."
    )


def test_green_script_catalog_files_exist():
    """The catalog entry is meaningless if the file is missing."""
    entries = _script_catalog_entries()
    missing = []
    for _g, script_id in IMPLS_UNDER_AUDIT:
        if script_id not in entries:
            missing.append(f"{script_id}: catalog entry missing")
            continue
        filename = entries[script_id]
        path = REPO_ROOT / "dev/scripts/checks" / filename
        if not path.exists():
            missing.append(f"{script_id}: {path} does not exist")
    assert not missing, missing


# ---------------------------------------------------------------------------
# Section 3 — quality_policy/defaults.py connection
# ---------------------------------------------------------------------------


def test_red_quality_policy_runs_the_17_guards_in_a_standard_bundle():
    """A guard that is NOT referenced in ``DEFAULT_AI_GUARD_SPECS`` exists
    but never fires from any standard quality bundle.
    ``role_lane_mutation_authority`` is already in defaults — anchor that
    one and verify the other 16 are wired the same way.
    """
    quality_ids = set(_quality_policy_script_ids())
    orphans = [
        f"{g}:{sid}"
        for g, sid in IMPLS_UNDER_AUDIT
        if sid not in quality_ids
    ]
    assert not orphans, (
        "These guards exist as files but are NOT wired into "
        "DEFAULT_AI_GUARD_SPECS. They will not run in any check-router or "
        f"quality-policy bundle: {orphans}"
    )


# ---------------------------------------------------------------------------
# Section 4 — Review-channel runtime path connection (G23-G27)
# ---------------------------------------------------------------------------


# Map G-id -> (module name, expected symbol). The expected symbol is what
# the guard module advertises; production code that wires the guard into
# the post-packet observation path must import the symbol (or the parent
# module). We grep the event_handler source for that import.
G23_G27_GUARDS: dict[str, str] = {
    "G23 packet_body_observation_route": (
        "dev.scripts.checks.check_packet_body_observation_route"
    ),
    "G24 action_request_expiry_refresh": (
        "dev.scripts.checks.check_action_request_expiry_refresh"
    ),
    "G25 loose_chat_to_typed_lane": (
        "dev.scripts.checks.check_loose_chat_to_typed_lane"
    ),
    "G26 reviewer_result_transition": (
        "dev.scripts.checks.check_reviewer_result_transition"
    ),
    "G27 continuation_anchor_enforcement": (
        "dev.scripts.checks.check_continuation_anchor_enforcement"
    ),
}


@pytest.mark.parametrize(
    ("label", "guard_module"),
    list(G23_G27_GUARDS.items()),
    ids=list(G23_G27_GUARDS.keys()),
)
def test_red_post_packet_runtime_path_imports_the_guard(
    label: str, guard_module: str
):
    """G23-G27 are *behavioral* guards — they must run while a packet is
    posted via ``review-channel --action post``. If the production code
    path that handles the post does NOT import the guard module (or a
    helper from it), the guard is orphaned: unit tests pass in isolation
    but the live post route never consults it.

    G23 wires via ``record_packet_body_observation``; verify the other
    four follow the same pattern.
    """
    event_handler_source = EVENT_HANDLER_PATH.read_text(encoding="utf-8")
    # G23 imports record_packet_body_observation, which in turn defines the
    # observation event. The other four guards (G24-G27) have no equivalent
    # production import.
    guard_short = guard_module.rsplit(".", 1)[-1]
    needle_a = f"from dev.scripts.checks import {guard_short}"
    needle_b = f"from dev.scripts.checks.{guard_short}"
    needle_c = (
        # G23-style: the guard's runtime hook lives in a separate module.
        # For G23 the runtime hook is ``record_packet_body_observation``
        # imported from ``...review_channel.packet_body_observation``.
        f"check_{label.split()[1]}"
    )
    wired = (
        needle_a in event_handler_source
        or needle_b in event_handler_source
        or needle_c in event_handler_source
    )
    assert wired, (
        f"{label} is orphaned: review_channel/event_handler.py does NOT "
        f"import {guard_module} (or any helper named after it). The guard "
        f"will never observe a real packet post. (Wired path for G23 is "
        f"``record_packet_body_observation`` via "
        f"``review_channel.packet_body_observation`` — verify G24-G27 use "
        f"an equivalent typed entrypoint.)"
    )


# ---------------------------------------------------------------------------
# Section 5 — Invariant C deployment (MissingDecisionRefreshHint)
# ---------------------------------------------------------------------------


def test_green_invariant_c_emits_missing_decision_refresh_hint():
    """When the live obedience evaluator runs with ``decision=None`` it
    must emit the typed ``MissingDecisionRefreshHint`` payload — NOT just a
    bare ``no_control_decision_input`` violation. The hint is what
    downstream code uses to refresh the controller artifact.
    """
    from dev.scripts.devctl.runtime.control_decision_obedience import (
        evaluate_control_decision_obedience,
    )

    report = evaluate_control_decision_obedience(
        decision=None,
        attempted_actions=({"action": "implementation.edit"},),
    )
    payload = report.to_dict()
    hint = payload.get("missing_decision_refresh_hint")
    reasons = [v.get("reason") for v in payload.get("violations", ())]
    assert "no_control_decision_input" in reasons, (
        "Sanity: evaluator should still emit the raw violation. Got "
        f"reasons={reasons}"
    )
    assert hint is not None, (
        "Invariant C orphaned: evaluator returned a bare "
        "no_control_decision_input violation WITHOUT the typed "
        "MissingDecisionRefreshHint payload. The hint is supposed to name "
        "the per-actor/role/session refresh command and the canonical "
        "expected_decision_path so consumers can refresh and retry."
    )
    assert str(hint.get("contract_id")) == "MissingDecisionRefreshHint", (
        f"Hint emitted but contract_id={hint.get('contract_id')!r}; expected "
        "MissingDecisionRefreshHint."
    )


# ---------------------------------------------------------------------------
# Section 6 — Invariant H deployment (unsafe_continue_with_edit_grant)
# ---------------------------------------------------------------------------


def test_green_invariant_h_rule_fires_on_unsafe_continue_with_edit_grant():
    """When an ``AgentLoopDecision`` carries ``safe_to_continue=False`` PLUS
    an ``implementation.edit`` grant in allowed_actions but no scoped
    operator override, the role-lane mutation guard must emit the
    ``unsafe_continue_with_edit_grant`` violation. (Invariant H proves the
    grant cannot be smuggled past the model.)

    Note: payload envelope mirrors the production fixture shape used in
    ``test_check_role_lane_mutation_authority.py`` (``agent_loop_decision``
    + ``attempted_action`` keys).
    """
    from dev.scripts.checks.check_role_lane_mutation_authority import (
        build_report,
    )

    decision_payload = {
        "agent_loop_decision": {
            "contract_id": "AgentLoopDecision",
            "actor_id": "codex",
            "actor_role": "implementer",
            "session_id": "sess-test-h",
            "safe_to_continue": False,
            "may_mutate": False,
            "can_run_next_command": False,
            # Contradictory grant: edit allowed even though continue is unsafe.
            "allowed_actions": ["implementation.edit"],
            "blocked_actions": [],
            "granted_capabilities": [],
            "operator_override": {"requested": False, "active": False},
        },
        "attempted_action": {
            "action_kind": "implementation_edit",
            "command": "apply_patch",
            "actor": "codex",
            "role": "implementer",
            "session_id": "sess-test-h",
            "mutates": True,
            "writes_state": True,
            "executes_command": True,
        },
    }

    report = build_report(report_override=decision_payload)
    reasons = {
        str(v.get("reason"))
        for v in report.get("violations", ())
        if isinstance(v, Mapping)
    }
    assert "unsafe_continue_with_edit_grant" in reasons, (
        "Invariant H orphaned: role-lane guard did NOT fire on the "
        "safe_to_continue=False + implementation.edit contradiction. "
        f"Violations seen: {sorted(reasons)}. Hand-crafted decision "
        "payloads can therefore smuggle edit grants past the guard."
    )


# ---------------------------------------------------------------------------
# Section 7 — Topology hardcoding deployment (4-site sweep)
# ---------------------------------------------------------------------------


def test_green_bridge_role_counts_respects_typed_role_assignments():
    """``bridge_role_counts`` must classify a ``codex`` provider into the
    implementer role when typed ``role_assignments`` say so — provider
    identity alone must not dictate the role.
    """
    from dev.scripts.devctl.runtime.control_topology_bridge_counts import (
        bridge_role_counts,
    )

    bridge = {
        "active_conductor_providers": ["codex"],
        "codex_conductor_active": True,
        "role_assignments": [
            {
                "role_id": "implementer",
                "provider": "codex",
                "session_id": "sess-codex-as-impl",
                "liveness_state": "live",
            }
        ],
    }
    counts = bridge_role_counts(bridge)
    # If hardcoded behavior persists, codex will be counted as reviewer.
    assert counts.get("live_implementer_total", 0) >= 1, (
        "Topology hardcoding still classifies provider=codex as reviewer "
        "even when typed role_assignments declare codex=implementer. "
        f"counts={counts}"
    )


def test_red_event_handler_does_not_hardcode_provider_to_role():
    """``event_handler.py`` must not contain raw provider->role literals
    such as ``provider == "codex"`` mapped to reviewer. Verify by static
    scan of the source.
    """
    source = EVENT_HANDLER_PATH.read_text(encoding="utf-8")
    forbidden = (
        'provider == "codex"',
        'provider == "claude"',
        'reviewer_provider = "codex"',
        'implementer_provider = "claude"',
    )
    hits = [needle for needle in forbidden if needle in source]
    assert not hits, (
        f"event_handler.py still contains hardcoded provider->role "
        f"literals: {hits}"
    )


def test_red_development_collaboration_profiles_does_not_hardcode_pair():
    """``development_collaboration_profiles.py`` may keep
    ``DEFAULT_PROFILE_PROVIDERS = ("codex", "claude")`` for adapter
    defaults, but production stop-anchor commands must not assume the
    codex=reviewer / claude=implementer pair when typed role_bindings are
    available.
    """
    source = DEVELOPMENT_COLLAB_PATH.read_text(encoding="utf-8")
    # The runtime must surface ``MissingTypedCollaborationSessionError`` —
    # not a silent two-provider fallback.
    assert "MissingTypedCollaborationSessionError" in source, (
        "development_collaboration_profiles.py no longer raises "
        "MissingTypedCollaborationSessionError when typed role_bindings "
        "are absent. Hardcoded pair fallback is back."
    )


def test_red_peer_awareness_warns_when_no_typed_topology():
    """``commands/agent_mind/peer_awareness.py`` must emit the
    ``no_live_peer_topology_in_collaboration_session`` warning instead of a
    silent codex<->claude reciprocal.
    """
    source = PEER_AWARENESS_PATH.read_text(encoding="utf-8")
    assert "NO_LIVE_PEER_TOPOLOGY_WARNING" in source, (
        "peer_awareness.py no longer carries the "
        "NO_LIVE_PEER_TOPOLOGY_WARNING typed signal. Hardcoded "
        "codex<->claude reciprocal may be back."
    )


# ---------------------------------------------------------------------------
# Section 8 — proof_bundle connection
# ---------------------------------------------------------------------------


def test_red_current_row_proof_bundle_dogfood_is_passing():
    """``check_current_row_proof_bundle.py`` is the typed proof-of-correctness
    aggregator for the active row. After 17 implementations land, the
    dogfood + final_gate + closure_receipt fields must transition from
    ``failed/blocked/missing`` to ``passed/allowed/present``.

    If dogfood is still ``failed``, the 17 guards did not move the row
    closer to closing — they are unit-test-only orphans.
    """
    from dev.scripts.checks import check_current_row_proof_bundle as bundle

    report = bundle.build_report()
    dogfood = report.get("dogfood_statuses") or {}
    if isinstance(dogfood, Mapping):
        dogfood_status = str(dogfood.get("status") or "")
    else:
        dogfood_status = ""
    final_gate = report.get("final_gate_status") or {}
    if isinstance(final_gate, Mapping):
        final_allowed = bool(final_gate.get("final_response_allowed"))
    else:
        final_allowed = False
    closure = report.get("closure_receipt_status") or {}
    if isinstance(closure, Mapping):
        closure_status = str(closure.get("status") or "")
    else:
        closure_status = ""

    summary = {
        "dogfood_status": dogfood_status,
        "final_response_allowed": final_allowed,
        "closure_receipt_status": closure_status,
        "row_status": report.get("status"),
    }
    assert (
        dogfood_status == "passed"
        and final_allowed is True
        and closure_status == "present"
    ), (
        "proof_bundle for the active row is STILL NOT CLOSING. After 17 "
        f"implementations, the typed evidence shows: {summary}. dogfood "
        "must be ``passed``, final gate must allow response, closure "
        "receipt must be ``present``. None of these are satisfied."
    )


# ---------------------------------------------------------------------------
# Section 9 — Aggregate connectivity summary
# ---------------------------------------------------------------------------


def test_red_aggregate_pass_fail_summary_of_17_impls():
    """Final cross-cut: count how many of the 17 implementations are
    actually CONNECTED (catalog + quality + (registry OR runtime wiring)).
    Anything with catalog only and no quality wiring is an orphan.
    """
    catalog = _script_catalog_entries()
    quality = set(_quality_policy_script_ids())
    registry = _registry_contract_ids()
    event_handler_src = EVENT_HANDLER_PATH.read_text(encoding="utf-8")
    runtime_wired_ids = {"packet_body_observation_route"}
    # G23 wires via the record_packet_body_observation helper, not the
    # check module directly. Verify the helper import is present.
    if "record_packet_body_observation" not in event_handler_src:
        runtime_wired_ids.discard("packet_body_observation_route")

    rows = []
    orphans = []
    for label, script_id in IMPLS_UNDER_AUDIT:
        in_catalog = script_id in catalog
        in_quality = script_id in quality
        runtime_wired = script_id in runtime_wired_ids
        # Approximate "typed registry connection" by checking the guard
        # contract id derived from the script_id stem (e.g.
        # ``packet_hygiene_enforcement`` -> ``PacketHygieneEnforcementGuard``).
        guard_contract = (
            "".join(piece.capitalize() for piece in script_id.split("_"))
            + "Guard"
        )
        in_registry = guard_contract in registry
        passed = in_catalog and in_quality
        rows.append(
            {
                "g_id": label,
                "script_id": script_id,
                "in_catalog": in_catalog,
                "in_quality_policy": in_quality,
                "runtime_wired": runtime_wired,
                "typed_contract_in_registry": in_registry,
                "connected": passed,
            }
        )
        if not passed:
            orphans.append(f"{label}:{script_id}")

    rendered = json.dumps(rows, indent=2)
    assert not orphans, (
        "These implementations are orphaned (catalog present but quality "
        "policy missing OR no runtime wiring OR no typed-contract registry "
        f"entry):\n{rendered}\n\nOrphan count: {len(orphans)}/{len(rows)}"
    )
