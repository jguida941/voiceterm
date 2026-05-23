"""Path-aware Python test add-ons for check-router."""

from __future__ import annotations

from ...config import REPO_ROOT

_FOCUSED_DEVCTL_TEST_BASE_TIMEOUT_SECONDS = 420
_FOCUSED_DEVCTL_TEST_PER_TEST_TIMEOUT_SECONDS = 90
_FOCUSED_DEVCTL_TEST_PARALLEL_WORKERS = 1
_FOCUSED_DEVCTL_TEST_SHARDED_PARALLEL_WORKERS = 4
_FOCUSED_DEVCTL_TEST_TARGET_TIMEOUT_SECONDS = {
    "dev/scripts/devctl/tests/commands/test_development_command.py": 900,
    "dev/scripts/devctl/tests/review_channel/test_review_channel.py": 900,
    "dev/scripts/devctl/tests/vcs/test_push.py": 240,
}
_FOCUSED_DEVCTL_TEST_TARGET_SHARDS = {
    "dev/scripts/devctl/tests/vcs/test_push.py": (
        "dev/scripts/devctl/tests/vcs/test_push.py::PushParserTests",
        "dev/scripts/devctl/tests/vcs/test_push.py::PushCommandTests",
        "dev/scripts/devctl/tests/vcs/test_push.py::PushBridgeSyncTests",
        "dev/scripts/devctl/tests/vcs/test_push.py::PushLiveExecutionTests",
        "dev/scripts/devctl/tests/vcs/test_push.py::PushReceiptTests",
        "dev/scripts/devctl/tests/vcs/test_push.py::PushPipelineStateSyncTests",
    ),
}


def detect_python_test_addons(changed_paths: list[str]) -> list[dict]:
    """Select bounded Python tests from touched paths instead of static bundles."""
    addons: list[dict] = []
    cold_boot_paths = _devctl_cold_boot_paths(changed_paths)
    if cold_boot_paths:
        addons.append(
            {
                "id": "devctl-cold-boot",
                "label": "devctl cold-boot import smoke",
                "matched_paths": cold_boot_paths,
                "commands": [
                    "python3 dev/scripts/checks/check_devctl_cold_boot.py --format md"
                ],
            }
        )

    operator_paths = _operator_console_test_paths(changed_paths)
    if operator_paths:
        addons.append(
            {
                "id": "python-tests.operator-console",
                "label": "Operator Console Python tests",
                "matched_paths": operator_paths,
                "commands": [_operator_console_test_command(operator_paths)],
            }
        )

    devctl_paths = _matching_paths(
        changed_paths,
        (
            "conftest.py",
            "pytest.ini",
            "dev/scripts/checks/",
            "dev/scripts/devctl/",
        ),
    )
    devctl_test_paths = _devctl_test_targets_for(changed_paths)
    if devctl_test_paths:
        addons.append(
            {
                "id": "python-tests.devctl-focused",
                "label": "Focused devctl Python tests",
                "matched_paths": devctl_paths,
                "commands": _devctl_test_commands(devctl_test_paths),
            }
        )
    return addons


def _matching_paths(changed_paths: list[str], prefixes: tuple[str, ...]) -> list[str]:
    return sorted(
        {
            path
            for path in changed_paths
            if any(
                path == prefix.rstrip("/") or path.startswith(prefix)
                for prefix in prefixes
            )
        }
    )


def _operator_console_test_paths(changed_paths: list[str]) -> list[str]:
    return [
        path
        for path in _matching_paths(changed_paths, ("app/operator_console/",))
        if path.endswith(".py")
    ]


def _devctl_cold_boot_paths(changed_paths: list[str]) -> list[str]:
    return [
        path
        for path in _matching_paths(
            changed_paths,
            (
                "dev/scripts/devctl/cli.py",
                "dev/scripts/devctl/commands/",
                "dev/scripts/devctl/runtime/",
                "dev/scripts/checks/check_devctl_cold_boot.py",
            ),
        )
        if path.endswith(".py")
    ]


def _operator_console_test_command(matched_paths: list[str]) -> str:
    touched_tests = tuple(
        path
        for path in matched_paths
        if path.startswith("app/operator_console/tests/") and path.endswith(".py")
    )
    if touched_tests:
        paths = " ".join(f"--path {path}" for path in touched_tests)
        return (
            "python3 dev/scripts/devctl.py test-python --suite operator-console "
            f"{paths} --timeout-seconds 300 --per-test-timeout-seconds 30"
        )
    return (
        "python3 dev/scripts/devctl.py test-python --suite operator-console "
        "--timeout-seconds 900 --per-test-timeout-seconds 30"
    )


def _devctl_test_commands(test_paths: tuple[str, ...]) -> list[str]:
    commands: list[str] = []
    for test_path in sorted(test_paths):
        shard_targets = _FOCUSED_DEVCTL_TEST_TARGET_SHARDS.get(test_path)
        if shard_targets:
            commands.append(
                _devctl_test_command_for_targets(
                    shard_targets,
                    timeout_seconds=_devctl_test_timeout_seconds(test_path),
                    parallel_workers=_FOCUSED_DEVCTL_TEST_SHARDED_PARALLEL_WORKERS,
                )
            )
            continue
        commands.append(_devctl_test_command(test_path))
    return commands


def _devctl_test_command(test_path: str) -> str:
    return _devctl_test_command_for_targets(
        (test_path,),
        timeout_seconds=_devctl_test_timeout_seconds(test_path),
        parallel_workers=_FOCUSED_DEVCTL_TEST_PARALLEL_WORKERS,
    )


def _devctl_test_command_for_targets(
    test_targets: tuple[str, ...],
    *,
    timeout_seconds: int,
    parallel_workers: int,
) -> str:
    paths = " ".join(f"--path {test_target}" for test_target in test_targets)
    return (
        "python3 dev/scripts/devctl.py test-python --suite devctl "
        f"{paths} "
        f"--timeout-seconds {timeout_seconds} "
        f"--per-test-timeout-seconds {_FOCUSED_DEVCTL_TEST_PER_TEST_TIMEOUT_SECONDS} "
        f"--parallel-workers {parallel_workers}"
    )


def _devctl_test_timeout_seconds(test_path: str) -> int:
    return _FOCUSED_DEVCTL_TEST_TARGET_TIMEOUT_SECONDS.get(
        test_path,
        _FOCUSED_DEVCTL_TEST_BASE_TIMEOUT_SECONDS,
    )


def _devctl_test_targets_for(changed_paths: list[str]) -> tuple[str, ...]:
    targets: set[str] = set()
    for path in changed_paths:
        if path.startswith("dev/scripts/devctl/tests/") and path.endswith(".py"):
            targets.add(path)
        for source_prefix, test_paths in _DEVCTL_TEST_TARGETS:
            if path == source_prefix.rstrip("/") or path.startswith(source_prefix):
                targets.update(test_paths)
    return tuple(sorted(path for path in targets if (REPO_ROOT / path).exists()))


_DEVCTL_TEST_TARGETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "dev/scripts/devctl/commands/ground_truth_probe.py",
        (
            "dev/scripts/devctl/tests/commands/test_ground_truth_probe.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/commands/test_ground_truth_probe.py",
        (
            "dev/scripts/devctl/tests/commands/test_ground_truth_probe.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_review_channel_post_finds_control_decision_artifact.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_review_channel_post_finds_control_decision_artifact.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_agent_loop_decision_grants_allowed_action_for_next_command.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_agent_loop_decision_grants_allowed_action_for_next_command.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_packet_body_observation_carries_typed_evidence.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_packet_body_observation_carries_typed_evidence.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_active_action_request_not_silently_expired.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_active_action_request_not_silently_expired.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_selected_attention_packet_is_newest_same_row.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_selected_attention_packet_is_newest_same_row.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_reviewer_decision_grants_review_result_action.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_reviewer_decision_grants_review_result_action.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_continuation_anchor_blocks_final_response.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_continuation_anchor_blocks_final_response.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_child_actor_carries_typed_delegation.py",
        ("dev/scripts/devctl/tests/scenarios/test_child_actor_carries_typed_delegation.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_per_role_actor_count_within_bounds.py",
        ("dev/scripts/devctl/tests/scenarios/test_per_role_actor_count_within_bounds.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_no_overlapping_write_scopes_among_mutating_actors.py",
        ("dev/scripts/devctl/tests/scenarios/test_no_overlapping_write_scopes_among_mutating_actors.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_child_actor_scope_does_not_exceed_parent.py",
        ("dev/scripts/devctl/tests/scenarios/test_child_actor_scope_does_not_exceed_parent.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_mutating_actor_observed_shared_round_state.py",
        ("dev/scripts/devctl/tests/scenarios/test_mutating_actor_observed_shared_round_state.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_peer_write_leases_visible_to_mutating_actor.py",
        ("dev/scripts/devctl/tests/scenarios/test_peer_write_leases_visible_to_mutating_actor.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_child_patch_references_parent_merge_gate.py",
        ("dev/scripts/devctl/tests/scenarios/test_child_patch_references_parent_merge_gate.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_overlapping_child_patches_have_typed_disposition.py",
        ("dev/scripts/devctl/tests/scenarios/test_overlapping_child_patches_have_typed_disposition.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_role_round_not_closed_while_children_pending.py",
        ("dev/scripts/devctl/tests/scenarios/test_role_round_not_closed_while_children_pending.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_child_actor_has_no_direct_repo_publish_caps.py",
        ("dev/scripts/devctl/tests/scenarios/test_child_actor_has_no_direct_repo_publish_caps.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_final_response_denied_without_proof_bundle.py",
        ("dev/scripts/devctl/tests/scenarios/test_final_response_denied_without_proof_bundle.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_feature_proof_receipt_proven_passed_carries_node_id.py",
        ("dev/scripts/devctl/tests/scenarios/test_feature_proof_receipt_proven_passed_carries_node_id.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_receipt_steward_substrate.py",
        ("dev/scripts/devctl/tests/scenarios/test_receipt_steward_substrate.py",),
    ),
    (
        "dev/scripts/devctl/runtime/receipt_steward_role.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_receipt_steward_substrate.py",
            "dev/scripts/devctl/tests/scenarios/test_receipt_steward_audit_cli.py",
        ),
    ),
    (
        "dev/scripts/devctl/runtime/receipt_steward_scope_claim.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_receipt_steward_audit_cli.py",
        ),
    ),
    (
        "dev/scripts/devctl/runtime/receipt_steward_audit.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_receipt_steward_audit_cli.py",
        ),
    ),
    (
        "dev/scripts/devctl/commands/receipt_steward/",
        (
            "dev/scripts/devctl/tests/scenarios/test_receipt_steward_audit_cli.py",
        ),
    ),
    (
        "dev/scripts/devctl/cli_parser/receipt_steward.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_receipt_steward_audit_cli.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_receipt_steward_audit_cli.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_receipt_steward_audit_cli.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_system_map_steward_substrate.py",
        ("dev/scripts/devctl/tests/scenarios/test_system_map_steward_substrate.py",),
    ),
    (
        "dev/scripts/devctl/runtime/system_map_steward_role.py",
        ("dev/scripts/devctl/tests/scenarios/test_system_map_steward_substrate.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_semantic_tdd_cadence_substrate.py",
        ("dev/scripts/devctl/tests/scenarios/test_semantic_tdd_cadence_substrate.py",),
    ),
    (
        "dev/scripts/devctl/runtime/semantic_tdd_cadence.py",
        ("dev/scripts/devctl/tests/scenarios/test_semantic_tdd_cadence_substrate.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_peer_spawn_returns_typed_receipt.py",
        ("dev/scripts/devctl/tests/scenarios/test_peer_spawn_returns_typed_receipt.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_bypass_grant_scopes_cover_peer_spawn_requirement.py",
        ("dev/scripts/devctl/tests/scenarios/test_bypass_grant_scopes_cover_peer_spawn_requirement.py",),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_peer_spawn_resolves_active_bypass_receipt_id.py",
        ("dev/scripts/devctl/tests/scenarios/test_peer_spawn_resolves_active_bypass_receipt_id.py",),
    ),
    (
        "dev/scripts/devctl/commands/runtime/peer_spawn.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_peer_spawn_returns_typed_receipt.py",
            "dev/scripts/devctl/tests/scenarios/test_peer_spawn_resolves_active_bypass_receipt_id.py",
            "dev/scripts/devctl/tests/scenarios/test_peer_spawn_task_prompt_writes_minimal_script.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_peer_spawn_task_prompt_writes_minimal_script.py",
        ("dev/scripts/devctl/tests/scenarios/test_peer_spawn_task_prompt_writes_minimal_script.py",),
    ),
    (
        "dev/scripts/devctl/commands/review_channel/event_handler.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_review_channel_post_finds_control_decision_artifact.py",
        ),
    ),
    (
        "dev/scripts/devctl/runtime/typed_controller_consistency.py",
        (
            "dev/scripts/devctl/tests/runtime/test_typed_controller_consistency.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/runtime/test_typed_controller_consistency.py",
        (
            "dev/scripts/devctl/tests/runtime/test_typed_controller_consistency.py",
        ),
    ),
    (
        "conftest.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_architecture_surface_sync.py",
            "dev/scripts/devctl/tests/checks/test_check_pytest_runtime_policy.py",
        ),
    ),
    (
        "pytest.ini",
        (
            "dev/scripts/devctl/tests/checks/test_check_pytest_runtime_policy.py",
        ),
    ),
    (
        "dev/scripts/checks/check_pytest_runtime_policy.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_pytest_runtime_policy.py",
        ),
    ),
    (
        "dev/scripts/checks/pytest_runtime_policy/",
        (
            "dev/scripts/devctl/tests/checks/test_check_pytest_runtime_policy.py",
        ),
    ),
    (
        "dev/scripts/checks/check_contract_consumer_coverage_sweep.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_contract_consumer_coverage_sweep.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/"
        "test_check_contract_consumer_coverage_sweep.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_contract_consumer_coverage_sweep.py",
        ),
    ),
    (
        "dev/scripts/checks/check_role_lane_mutation_authority.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_role_lane_mutation_authority.py",
        ),
    ),
    (
        "dev/scripts/checks/check_role_delegation_authority.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_role_delegation_authority.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_role_delegation_authority.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_role_delegation_authority.py",
        ),
    ),
    (
        "dev/scripts/checks/check_write_lease_conflicts.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_write_lease_conflicts.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_write_lease_conflicts.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_write_lease_conflicts.py",
        ),
    ),
    (
        "dev/scripts/checks/check_active_topology_liveness.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_active_topology_liveness.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_active_topology_liveness.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_active_topology_liveness.py",
        ),
    ),
    (
        "dev/scripts/checks/check_provider_pre_tool_hook_coverage.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_provider_pre_tool_hook_coverage.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_provider_pre_tool_hook_coverage.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_provider_pre_tool_hook_coverage.py",
        ),
    ),
    (
        "dev/scripts/checks/check_current_plan_authority.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_current_plan_authority.py",
            "dev/scripts/devctl/tests/scenarios/test_current_plan_authority_dogfood.py",
        ),
    ),
    (
        "dev/scripts/checks/check_current_row_proof_bundle.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_current_row_proof_bundle.py",
        ),
    ),
    (
        "dev/scripts/devctl/runtime/current_row_proof_bundle.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_current_row_proof_bundle.py",
        ),
    ),
    (
        "dev/scripts/devctl/commands/plan_execution_projection.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_current_row_proof_bundle.py",
        ),
    ),
    (
        "dev/scripts/checks/check_staging_source_ingested.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_staging_source_ingested.py",
        ),
    ),
    (
        "dev/scripts/checks/current_plan_authority/",
        (
            "dev/scripts/devctl/tests/checks/test_check_current_plan_authority.py",
            "dev/scripts/devctl/tests/scenarios/test_current_plan_authority_dogfood.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_current_plan_authority.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_current_plan_authority.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_current_plan_authority_dogfood.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_current_plan_authority_dogfood.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/commands/review_channel/"
        "test_event_control_decision_fallback.py",
        (
            "dev/scripts/devctl/tests/commands/review_channel/"
            "test_event_control_decision_fallback.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/commands/review_channel/"
        "test_event_implementer_ack_action.py",
        (
            "dev/scripts/devctl/tests/commands/review_channel/"
            "test_event_implementer_ack_action.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/commands/runtime/test_peer_spawn_command.py",
        (
            "dev/scripts/devctl/tests/commands/runtime/test_peer_spawn_command.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_tdd_audit_codex_session_edits.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_tdd_audit_codex_session_edits.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_tdd_connectivity_audit_17_impls.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_tdd_connectivity_audit_17_impls.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_tdd_orphan_contract_audit.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_tdd_orphan_contract_audit.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/scenarios/test_tdd_topology_hardcoding_hunt.py",
        (
            "dev/scripts/devctl/tests/scenarios/test_tdd_topology_hardcoding_hunt.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_role_lane_mutation_authority.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_role_lane_mutation_authority.py",
        ),
    ),
    (
        "dev/scripts/checks/check_pre_commit_guard_coverage.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_pre_commit_guard_coverage.py",
        ),
    ),
    (
        "dev/scripts/checks/check_packet_body_observation_route.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_packet_body_observation_route.py",
            "dev/scripts/devctl/tests/scenarios/test_tdd_packet_lifecycle_invariants.py",
        ),
    ),
    (
        "dev/scripts/checks/check_packet_hygiene_enforcement.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_packet_hygiene_enforcement.py",
            "dev/scripts/devctl/tests/scenarios/test_tdd_packet_lifecycle_invariants.py",
        ),
    ),
    (
        "dev/scripts/checks/check_typed_agent_spawn_authority.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_typed_agent_spawn_authority.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_typed_agent_spawn_authority.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_typed_agent_spawn_authority.py",
        ),
    ),
    (
        "dev/scripts/checks/check_subagent_no_commit_push.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_subagent_no_commit_push.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_subagent_no_commit_push.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_subagent_no_commit_push.py",
        ),
    ),
    (
        "dev/scripts/checks/check_shared_round_state_observed.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_shared_round_state_observed.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_shared_round_state_observed.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_shared_round_state_observed.py",
        ),
    ),
    (
        "dev/scripts/checks/check_continuation_anchor_enforcement.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_continuation_anchor_enforcement.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/"
        "test_check_continuation_anchor_enforcement.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_continuation_anchor_enforcement.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_pre_commit_guard_coverage.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_pre_commit_guard_coverage.py",
        ),
    ),
    (
        "dev/scripts/checks/check_no_prose_authority_promotion.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_no_prose_authority_promotion.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_no_prose_authority_promotion.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_no_prose_authority_promotion.py",
        ),
    ),
    (
        "dev/scripts/checks/check_orphan_files.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_orphan_files.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_orphan_files.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_orphan_files.py",
        ),
    ),
    (
        "dev/scripts/checks/check_feature_completion.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_feature_completion.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_feature_completion.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_feature_completion.py",
        ),
    ),
    (
        "dev/scripts/checks/check_plan_row_must_advance.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_plan_row_must_advance.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_plan_row_must_advance.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_plan_row_must_advance.py",
        ),
    ),
    (
        "dev/scripts/checks/check_no_ingestion_churn_without_advancement.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_no_ingestion_churn_without_advancement.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_no_ingestion_churn_without_advancement.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_no_ingestion_churn_without_advancement.py",
        ),
    ),
    (
        "dev/scripts/checks/check_receipt_schema_validation.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_receipt_schema_validation.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_receipt_schema_validation.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_receipt_schema_validation.py",
        ),
    ),
    (
        "dev/scripts/checks/check_receipt_store_has_active_consumer.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_receipt_store_has_active_consumer.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_receipt_store_has_active_consumer.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_receipt_store_has_active_consumer.py",
        ),
    ),
    (
        "dev/scripts/checks/check_receipt_store_coverage_sweep.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_receipt_store_coverage_sweep.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_receipt_store_coverage_sweep.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_receipt_store_coverage_sweep.py",
        ),
    ),
    (
        "dev/scripts/checks/check_packet_body_observation_route.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_packet_body_observation_route.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_packet_body_observation_route.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_packet_body_observation_route.py",
        ),
    ),
    (
        "dev/scripts/checks/check_packet_hygiene_enforcement.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_packet_hygiene_enforcement.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_packet_hygiene_enforcement.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_packet_hygiene_enforcement.py",
        ),
    ),
    (
        "dev/scripts/checks/check_peer_lease_visibility.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_peer_lease_visibility.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_peer_lease_visibility.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_peer_lease_visibility.py",
        ),
    ),
    (
        "dev/scripts/checks/check_patch_submission_merge_gate.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_patch_submission_merge_gate.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_patch_submission_merge_gate.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_patch_submission_merge_gate.py",
        ),
    ),
    (
        "dev/scripts/checks/check_role_cardinality_bounds.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_role_cardinality_bounds.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_role_cardinality_bounds.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_role_cardinality_bounds.py",
        ),
    ),
    (
        "dev/scripts/checks/check_child_actor_scope.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_child_actor_scope.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_child_actor_scope.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_child_actor_scope.py",
        ),
    ),
    (
        "dev/scripts/checks/check_role_round_closure.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_role_round_closure.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_role_round_closure.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_role_round_closure.py",
        ),
    ),
    (
        "dev/scripts/checks/check_continuation_anchor_enforcement.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_continuation_anchor_enforcement.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/"
        "test_check_continuation_anchor_enforcement.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_continuation_anchor_enforcement.py",
        ),
    ),
    (
        "dev/scripts/checks/check_loose_chat_to_typed_lane.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_loose_chat_to_typed_lane.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_loose_chat_to_typed_lane.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_loose_chat_to_typed_lane.py",
        ),
    ),
    (
        "dev/scripts/checks/check_multi_actor_merge_conflict.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_multi_actor_merge_conflict.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/"
        "test_check_multi_actor_merge_conflict.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_multi_actor_merge_conflict.py",
        ),
    ),
    (
        "dev/scripts/checks/check_reviewer_result_transition.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_reviewer_result_transition.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_reviewer_result_transition.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_reviewer_result_transition.py",
        ),
    ),
    (
        "dev/scripts/checks/check_action_request_expiry_refresh.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_action_request_expiry_refresh.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/"
        "test_check_action_request_expiry_refresh.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_action_request_expiry_refresh.py",
        ),
    ),
    (
        "dev/scripts/checks/check_every_applied_row_has_closure_receipt.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_every_applied_row_has_closure_receipt.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/"
        "test_check_every_applied_row_has_closure_receipt.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_every_applied_row_has_closure_receipt.py",
        ),
    ),
    (
        "dev/scripts/checks/check_receipt_commit_anchor_refs.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_receipt_commit_anchor_refs.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_receipt_commit_anchor_refs.py",
        (
            "dev/scripts/devctl/tests/checks/"
            "test_check_receipt_commit_anchor_refs.py",
        ),
    ),
    (
        "dev/scripts/checks/check_slice_finishes_or_reverts.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_slice_finishes_or_reverts.py",
        ),
    ),
    (
        "dev/scripts/devctl/tests/checks/test_check_slice_finishes_or_reverts.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_slice_finishes_or_reverts.py",
        ),
    ),
    (
        "dev/scripts/checks/check_guardir_extraction_plan_artifacts.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_topology_hardcode_guards.py",
        ),
    ),
    (
        "dev/scripts/checks/guardir_extraction_plan_artifacts/",
        (
            "dev/scripts/devctl/tests/checks/test_check_topology_hardcode_guards.py",
        ),
    ),
    (
        "dev/scripts/checks/check_no_new_hardcoded_provider_authority.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_topology_hardcode_guards.py",
        ),
    ),
    (
        "dev/scripts/checks/check_no_new_topology_count_coupling.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_topology_hardcode_guards.py",
        ),
    ),
    (
        "dev/scripts/checks/topology_hardcode/",
        (
            "dev/scripts/devctl/tests/checks/test_check_topology_hardcode_guards.py",
        ),
    ),
    (
        "dev/scripts/devctl/cli_parser/python_tests.py",
        (
            "dev/scripts/devctl/tests/commands/test_python_tests.py",
        ),
    ),
    (
        "dev/scripts/devctl/commands/python_tests.py",
        (
            "dev/scripts/devctl/tests/commands/test_python_tests.py",
        ),
    ),
    (
        "dev/scripts/devctl/commands/python_test_runner/",
        (
            "dev/scripts/devctl/tests/commands/test_python_tests.py",
        ),
    ),
    (
        "dev/scripts/devctl/runtime/python_test_contract.py",
        (
            "dev/scripts/devctl/tests/commands/test_python_tests.py",
        ),
    ),
    (
        "dev/scripts/devctl/bundles/",
        (
            "dev/scripts/devctl/tests/commands/check/test_check_router.py",
            "dev/scripts/devctl/tests/governance/test_bundle_registry.py",
        ),
    ),
    (
        "dev/scripts/devctl/commands/check/",
        (
            "dev/scripts/devctl/tests/commands/check/test_check_router.py",
        ),
    ),
    (
        "dev/scripts/devctl/governance/script_catalog_registry.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_pytest_runtime_policy.py",
            "dev/scripts/devctl/tests/governance/test_bundle_registry.py",
        ),
    ),
)
