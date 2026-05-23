"""Guard violation and peer-spawn receipt contract rows for the platform blueprint.

These rows register the typed violation dataclasses emitted by repo guards in
``dev/scripts/checks`` and the peer-spawn receipts emitted by
``dev/scripts/devctl/runtime/peer_spawn.py`` so they appear in the repo-owned
``contract_registry.jsonl`` and pass the platform contract closure check.

Each ``ContractSpec`` declares the exact dataclass fields (excluding
``schema_version`` and ``contract_id`` metadata fields, which the closure
support strips before comparing) so the registry stays in sync with the source.
"""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


GUARD_VIOLATION_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="MissingDecisionRefreshHint",
        owner_layer="governance_runtime",
        purpose=(
            "Typed recovery hint emitted when the obedience layer cannot find "
            "a controller decision; names the expected decision path and the "
            "per-actor refresh command callers must run to recover."
        ),
        required_fields=(
            ContractField("hint_id", "str", "Stable hint id for this refresh evidence row."),
            ContractField("next_command", "str", "Typed next command callers must run."),
            ContractField("refresh_command", "str", "Refresh command that materializes a new decision."),
            ContractField("expected_decision_path", "str", "Controller decision artifact path the obedience layer expected."),
            ContractField("actor", "str", "Actor id requesting the refresh hint."),
            ContractField("role", "str", "Role the refresh hint applies to."),
            ContractField("session_id", "str", "Session id the refresh hint applies to."),
            ContractField("detail", "str", "Operator-readable failure detail."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.control_decision_obedience:"
            "MissingDecisionRefreshHint"
        ),
        startup_surface_tokens=("hint_id", "next_command", "expected_decision_path"),
    ),
    ContractSpec(
        contract_id="AgentSpawnReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed receipt recording the outcome of one peer-spawn attempt "
            "executed through the canonical peer-spawn driver under a typed "
            "BypassReceipt gate."
        ),
        required_fields=(
            ContractField("request_id", "str", "AgentSpawnRequest id this receipt resolves."),
            ContractField("provider", "str", "Provider conductor that was spawned or denied."),
            ContractField("role", "str", "Runtime role bound to the spawn attempt."),
            ContractField("bypass_receipt_id", "str", "BypassReceipt id authorizing the spawn."),
            ContractField("row_id", "str", "Plan row or slice associated with the spawn."),
            ContractField("status", "str", "Spawn status, e.g. launched, denied_bypass_missing, failed."),
            ContractField("issued_at_utc", "str", "UTC timestamp the receipt was issued."),
            ContractField("pid", "int", "Process id of the spawned conductor when known."),
            ContractField("script_path", "str", "Launch script path executed for the spawn."),
            ContractField("reason", "str", "Reason classifier when the spawn was denied."),
            ContractField("error", "str", "Error string captured during the spawn attempt."),
        ),
        runtime_model="dev.scripts.devctl.runtime.peer_spawn:AgentSpawnReceipt",
        startup_surface_tokens=("request_id", "provider", "status"),
    ),
    ContractSpec(
        contract_id="AgentTerminationReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed receipt recording the outcome of one peer-terminate attempt "
            "executed through the canonical peer-spawn driver."
        ),
        required_fields=(
            ContractField("request_id", "str", "Termination request id this receipt resolves."),
            ContractField("provider", "str", "Provider conductor that was terminated."),
            ContractField("session_id", "str", "Session id targeted by the termination."),
            ContractField("pid", "int", "Process id targeted by the termination signal."),
            ContractField("signal", "str", "Signal name dispatched, e.g. SIGTERM."),
            ContractField("status", "str", "Termination status, e.g. terminated, failed, denied."),
            ContractField("issued_at_utc", "str", "UTC timestamp the receipt was issued."),
            ContractField("actor", "str", "Actor that requested termination."),
            ContractField("reason", "str", "Reason classifier for the termination."),
            ContractField("error", "str", "Error string captured during termination."),
        ),
        runtime_model="dev.scripts.devctl.runtime.peer_spawn:AgentTerminationReceipt",
        startup_surface_tokens=("request_id", "provider", "status"),
    ),
    ContractSpec(
        contract_id="RoleCardinalityViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_role_cardinality_bounds when "
            "a role's live actor count drifts outside its declared [min,max] "
            "bounds or overflow occupancy lacks a typed merge owner."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Cardinality rule id that fired."),
            ContractField("role_id", "str", "Role id whose occupancy violated bounds."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
            ContractField("live_actor_count", "int", "Observed live actor count for the role."),
            ContractField("min_actors", "int", "Minimum allowed actors for the role."),
            ContractField("desired_actors", "int", "Declared desired actor count for the role."),
            ContractField("max_actors", "int", "Maximum allowed actors for the role."),
            ContractField("fallback_policy", "str", "Fallback policy classifier (block/degrade/queue)."),
            ContractField("evidence_actor_ids", "tuple[str, ...]", "Actor ids observed for the role."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_role_cardinality_bounds:RoleCardinalityViolation"
        ),
        startup_surface_tokens=("rule_id", "role_id", "live_actor_count"),
    ),
    ContractSpec(
        contract_id="HygieneViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_packet_hygiene_enforcement "
            "when packet hygiene rules are violated."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Hygiene rule id that fired."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
            ContractField("evidence_packet_ids", "tuple[str, ...]", "Packet ids implicated by the violation."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_packet_hygiene_enforcement:HygieneViolation"
        ),
        startup_surface_tokens=("rule_id", "detail", "remediation"),
    ),
    ContractSpec(
        contract_id="LeaseConflictViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_write_lease_conflicts when "
            "two typed-lease actors claim overlapping scope dimensions."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Lease overlap rule id that fired."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
            ContractField("left_actor_id", "str", "Actor id of the left side of the lease overlap."),
            ContractField("right_actor_id", "str", "Actor id of the right side of the lease overlap."),
            ContractField("scope_value", "str", "Overlapping scope value (path/file/symbol/etc)."),
            ContractField("plan_row_id", "str", "Plan row id associated with the lease, when known."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_write_lease_conflicts:LeaseConflictViolation"
        ),
        startup_surface_tokens=("rule_id", "left_actor_id", "right_actor_id"),
    ),
    ContractSpec(
        contract_id="DelegationViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_role_delegation_authority "
            "when a parent role's delegation grant breaks typed delegation "
            "authority rules."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Delegation rule id that fired."),
            ContractField("grant_id", "str", "Delegation grant id that violated authority."),
            ContractField("parent_role_occupancy_id", "str", "Parent role occupancy id granting delegation."),
            ContractField("child_actor_id", "str", "Child actor id receiving delegation."),
            ContractField("child_role_id", "str", "Child role id assigned via delegation."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_role_delegation_authority:DelegationViolation"
        ),
        startup_surface_tokens=("rule_id", "grant_id", "child_actor_id"),
    ),
    ContractSpec(
        contract_id="ExpiryRefreshViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_action_request_expiry_refresh "
            "when an action_request packet expiry is not refreshed in time."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Expiry-refresh rule id that fired."),
            ContractField("packet_id", "str", "Action request packet id implicated."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
            ContractField("evidence_packet_ids", "tuple[str, ...]", "Evidence packet ids supporting the violation."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_action_request_expiry_refresh:ExpiryRefreshViolation"
        ),
        startup_surface_tokens=("rule_id", "packet_id", "detail"),
    ),
    ContractSpec(
        contract_id="LooseChatViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_loose_chat_to_typed_lane "
            "when loose chat prose is detected outside typed lanes."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Loose-chat rule id that fired."),
            ContractField("packet_id", "str", "Offending packet id."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
            ContractField("evidence_packet_ids", "tuple[str, ...]", "Evidence packet ids."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_loose_chat_to_typed_lane:LooseChatViolation"
        ),
        startup_surface_tokens=("rule_id", "packet_id", "detail"),
    ),
    ContractSpec(
        contract_id="TransitionViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_reviewer_result_transition "
            "when a reviewer result transition violates the typed transition policy."
        ),
        required_fields=(
            ContractField("reason", "str", "Transition violation reason classifier."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
            ContractField("packet_id", "str", "Packet id implicated by the transition."),
            ContractField("session_id", "str", "Session id associated with the transition."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_reviewer_result_transition:TransitionViolation"
        ),
        startup_surface_tokens=("reason", "packet_id", "session_id"),
    ),
    ContractSpec(
        contract_id="AnchorViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_continuation_anchor_enforcement "
            "when continuation_anchor evidence is missing or stale."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Anchor enforcement rule id."),
            ContractField("anchor_packet_id", "str", "Continuation anchor packet id."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
            ContractField("evidence_packet_ids", "tuple[str, ...]", "Evidence packet ids."),
            ContractField("evidence_event_ids", "tuple[str, ...]", "Evidence event ids."),
            ContractField("target_role", "str", "Target role for the anchor enforcement."),
            ContractField("target_session_id", "str", "Target session id."),
            ContractField("target_scope", "str", "Target scope (actor/role/session) for the anchor."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_continuation_anchor_enforcement:AnchorViolation"
        ),
        startup_surface_tokens=("rule_id", "anchor_packet_id", "target_scope"),
    ),
    ContractSpec(
        contract_id="ChildActorScopeViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_child_actor_scope when a "
            "child actor exceeds its delegated scope of authority."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Child-actor scope rule id."),
            ContractField("actor_id", "str", "Child actor id."),
            ContractField("role_id", "str", "Role id of the child actor."),
            ContractField("parent_role_occupancy_id", "str", "Parent role occupancy id granting scope."),
            ContractField("delegation_id", "str", "Delegation grant id."),
            ContractField("action_kind", "str", "Action kind that exceeded scope."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_child_actor_scope:ChildActorScopeViolation"
        ),
        startup_surface_tokens=("rule_id", "actor_id", "action_kind"),
    ),
    ContractSpec(
        contract_id="PacketBodyRouteViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_packet_body_observation_route "
            "when packet body observation is routed outside the typed lane."
        ),
        required_fields=(
            ContractField("packet_id", "str", "Offending packet id."),
            ContractField("reason", "str", "Route violation reason classifier."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_packet_body_observation_route:PacketBodyRouteViolation"
        ),
        startup_surface_tokens=("packet_id", "reason", "remediation"),
    ),
    ContractSpec(
        contract_id="PeerLeaseVisibilityViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_peer_lease_visibility when "
            "peer lease evidence is invisible to a coordinating actor."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Visibility rule id."),
            ContractField("actor_id", "str", "Actor id missing peer lease visibility."),
            ContractField("row_id", "str", "Plan row id associated with the violation."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
            ContractField("missing_lease_ids", "tuple[str, ...]", "Lease ids missing from visibility."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_peer_lease_visibility:PeerLeaseVisibilityViolation"
        ),
        startup_surface_tokens=("rule_id", "actor_id", "row_id"),
    ),
    ContractSpec(
        contract_id="MergeGateViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_patch_submission_merge_gate "
            "when a child actor merges patches without parent role coordination."
        ),
        required_fields=(
            ContractField("child_actor_id", "str", "Child actor id."),
            ContractField("parent_role_coordinator_id", "str", "Parent role coordinator id."),
            ContractField("rule_id", "str", "Merge gate rule id."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_patch_submission_merge_gate:MergeGateViolation"
        ),
        startup_surface_tokens=("rule_id", "child_actor_id", "parent_role_coordinator_id"),
    ),
    ContractSpec(
        contract_id="MergeConflictViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_multi_actor_merge_conflict when "
            "multiple child actors emit patches with overlapping mutation scope."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Merge conflict rule id."),
            ContractField("conflict_id", "str", "Identifier for the conflict instance."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
            ContractField("child_patch_ids", "tuple[str, ...]", "Child patch ids that overlap."),
            ContractField("overlap_fields", "tuple[str, ...]", "Fields that overlap across patches."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_multi_actor_merge_conflict:MergeConflictViolation"
        ),
        startup_surface_tokens=("rule_id", "conflict_id", "child_patch_ids"),
    ),
    ContractSpec(
        contract_id="RoleRoundViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_role_round_closure when a "
            "role's round closure invariants are violated."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Round closure rule id."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
            ContractField("round_id", "str", "Round id implicated."),
            ContractField("role_id", "str", "Role id implicated."),
            ContractField("child_ids", "tuple[str, ...]", "Child ids implicated by the closure violation."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_role_round_closure:RoleRoundViolation"
        ),
        startup_surface_tokens=("rule_id", "round_id", "role_id"),
    ),
    ContractSpec(
        contract_id="SubagentAuthorityViolation",
        owner_layer="repo_packs",
        purpose=(
            "Typed violation row emitted by check_subagent_no_commit_push when "
            "a subagent attempts a commit/push action that exceeds its authority."
        ),
        required_fields=(
            ContractField("rule_id", "str", "Subagent authority rule id."),
            ContractField("attempt_id", "str", "Attempt id of the offending action."),
            ContractField("child_actor_id", "str", "Child actor id."),
            ContractField("parent_role_occupancy_id", "str", "Parent role occupancy id."),
            ContractField("action_kind", "str", "Action kind attempted."),
            ContractField("detail", "str", "Operator-readable violation detail."),
            ContractField("remediation", "str", "Typed remediation hint."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_subagent_no_commit_push:SubagentAuthorityViolation"
        ),
        startup_surface_tokens=("rule_id", "attempt_id", "action_kind"),
    ),
)


__all__ = ["GUARD_VIOLATION_CONTRACTS"]
