"""Canonical script path registry for devctl and tooling checks."""

from __future__ import annotations

import shlex
from collections.abc import Mapping
from pathlib import Path

from ..config import REPO_ROOT

CHECKS_DIR = "dev/scripts/checks"

_CHECK_SCRIPT_ENTRIES = (
    ("action_result_status_domain", "check_action_result_status_domain.py"),
    ("active_plan_sync", "check_active_plan_sync.py"),
    ("architecture_surface_sync", "check_architecture_surface_sync.py"),
    ("review_snapshot_freshness", "check_review_snapshot_freshness.py"),
    ("system_picture_freshness", "check_system_picture_freshness.py"),
    ("agents_contract", "check_agents_contract.py"),
    ("agents_bundle_render", "check_agents_bundle_render.py"),
    ("bootstrap", "check_bootstrap.py"),
    ("bridge_projection_only", "check_bridge_projection_only.py"),
    ("bundle_registry_dry", "check_bundle_registry_dry.py"),
    ("bundle_workflow_parity", "check_bundle_workflow_parity.py"),
    ("check_cli_test_parity", "check_check_cli_test_parity.py"),
    ("cli_flags_parity", "check_cli_flags_parity.py"),
    ("clippy_high_signal", "check_clippy_high_signal.py"),
    ("command_source_validation", "check_command_source_validation.py"),
    ("commit_body_packet_anchors", "check_commit_body_packet_anchors.py"),
    ("commit_message_row_id_resolves", "check_commit_message_row_id_resolves.py"),
    ("command_output_consumed", "check_command_output_consumed.py"),
    ("control_decision_consistency", "check_control_decision_consistency.py"),
    ("control_decision_obeyed", "check_control_decision_obeyed.py"),
    ("contract_connectivity", "check_contract_connectivity.py"),
    (
        "contract_registry_composite_key_uniqueness",
        "check_contract_registry_composite_key_uniqueness.py",
    ),
    (
        "context_graph_snapshot_freshness",
        "check_context_graph_snapshot_freshness.py",
    ),
    ("duplication_audit", "check_duplication_audit.py"),
    ("duplication_audit_support", "check_duplication_audit_support.py"),
    ("duplicate_types", "check_duplicate_types.py"),
    ("commit_complete_proof", "check_commit_complete_proof.py"),
    ("feature_has_proof_receipt", "check_feature_has_proof_receipt.py"),
    ("push_complete_proof", "check_push_complete_proof.py"),
    ("no_projection_proof_misuse", "check_no_projection_proof_misuse.py"),
    ("non_trivial_output_proof", "check_non_trivial_output_proof.py"),
    ("role_review_completed", "check_role_review_completed.py"),
    ("guard_enforcement_inventory", "check_guard_enforcement_inventory.py"),
    (
        "guardir_extraction_plan_artifacts",
        "check_guardir_extraction_plan_artifacts.py",
    ),
    ("ground_truth_probe_gate", "check_ground_truth_probe_gate.py"),
    ("launcher_authority_ordering", "check_launcher_authority_ordering.py"),
    ("governed_transitions", "check_governed_transitions.py"),
    ("guide_contract_sync", "check_guide_contract_sync.py"),
    ("memory_not_authority", "check_memory_not_authority.py"),
    ("python_broad_except", "check_python_broad_except.py"),
    ("pytest_runtime_policy", "check_pytest_runtime_policy.py"),
    ("python_subprocess_policy", "check_python_subprocess_policy.py"),
    ("compat_matrix", "check_compat_matrix.py"),
    ("compat_matrix_smoke", "compat_matrix_smoke.py"),
    ("code_shape", "check_code_shape.py"),
    ("package_layout", "check_package_layout.py"),
    ("packet_absorption_required", "check_packet_absorption_required.py"),
    ("packet_pkt_bind_completeness", "check_packet_pkt_bind_completeness.py"),
    ("plan_index_commit_continuity", "check_plan_index_commit_continuity.py"),
    ("plan_gold_claims_resolve", "check_plan_gold_claims_resolve.py"),
    ("plan_metric_freshness", "check_plan_metric_freshness.py"),
    ("plan_row_contract_refs_resolve", "check_plan_row_contract_refs_resolve.py"),
    ("publication_scope_integrity", "check_publication_scope_integrity.py"),
    (
        "publication_scope_integrity_for_push",
        "check_publication_scope_integrity_for_push.py",
    ),
    (
        "task_started_adr_precedent_linking",
        "check_task_started_adr_precedent_linking.py",
    ),
    ("typed_namespace_composition", "check_typed_namespace_composition.py"),
    ("runtime_state_ignore_posture", "check_runtime_state_ignore_posture.py"),
    ("substrate_is_repo_portable", "check_substrate_is_repo_portable.py"),
    ("platform_layer_boundaries", "check_platform_layer_boundaries.py"),
    ("platform_contract_closure", "check_platform_contract_closure.py"),
    ("platform_contract_sync", "check_platform_contract_sync.py"),
    ("runtime_spine_closure", "check_runtime_spine_closure.py"),
    ("coderabbit_gate", "check_coderabbit_gate.py"),
    ("coderabbit_ralph_gate", "check_coderabbit_ralph_gate.py"),
    ("provider_list_parity_graph", "check_provider_list_parity_graph.py"),
    (
        "no_new_hardcoded_provider_authority",
        "check_no_new_hardcoded_provider_authority.py",
    ),
    (
        "no_new_topology_count_coupling",
        "check_no_new_topology_count_coupling.py",
    ),
    ("ide_provider_isolation", "check_ide_provider_isolation.py"),
    (
        "instruction_surface_sync",
        "check_instruction_surface_sync.py",
    ),
    ("naming_consistency", "check_naming_consistency.py"),
    ("mobile_relay_protocol", "check_mobile_relay_protocol.py"),
    ("daemon_state_parity", "check_daemon_state_parity.py"),
    ("devctl_cold_boot", "check_devctl_cold_boot.py"),
    (
        "orchestration_recommendation_closure",
        "check_orchestration_recommendation_closure.py",
    ),
    ("multi_agent_sync", "check_multi_agent_sync.py"),
    ("markdown_metadata_header", "check_markdown_metadata_header.py"),
    ("mutation_bypass_graph_closure", "check_mutation_bypass_graph_closure.py"),
    ("mutation_score", "check_mutation_score.py"),
    ("publication_sync", "check_publication_sync.py"),
    ("release_version_parity", "check_release_version_parity.py"),
    ("repo_url_parity", "check_repo_url_parity.py"),
    ("registry_path_integrity", "check_registry_path_integrity.py"),
    ("review_surface_consistency", "check_review_surface_consistency.py"),
    ("review_channel_bridge", "check_review_channel_bridge.py"),
    (
        "runtime_bridge_projection_separation",
        "check_runtime_bridge_projection_separation.py",
    ),
    ("schema_fixture_handshake", "check_schema_fixture_handshake.py"),
    ("schema_migration_spine", "check_schema_migration_spine.py"),
    ("schema_version_monotonic", "check_schema_version_monotonic.py"),
    ("state_store_authority", "check_state_store_authority.py"),
    (
        "substrate_commits_have_applied_plan_row",
        "check_substrate_commits_have_applied_plan_row.py",
    ),
    (
        "systemmap_covers_contract_registry",
        "check_systemmap_covers_contract_registry.py",
    ),
    ("tandem_consistency", "check_tandem_consistency.py"),
    ("rust_best_practices", "check_rust_best_practices.py"),
    ("rust_compiler_warnings", "check_rust_compiler_warnings.py"),
    ("rust_audit_patterns", "check_rust_audit_patterns.py"),
    ("serde_compatibility", "check_serde_compatibility.py"),
    ("rust_runtime_panic_policy", "check_rust_runtime_panic_policy.py"),
    ("rust_security_footguns", "check_rust_security_footguns.py"),
    ("rust_lint_debt", "check_rust_lint_debt.py"),
    ("function_duplication", "check_function_duplication.py"),
    ("god_class", "check_god_class.py"),
    ("nesting_depth", "check_nesting_depth.py"),
    ("parameter_count", "check_parameter_count.py"),
    ("python_dict_schema", "check_python_dict_schema.py"),
    ("python_typed_seams", "check_python_typed_seams.py"),
    ("python_global_mutable", "check_python_global_mutable.py"),
    ("python_design_complexity", "check_python_design_complexity.py"),
    ("python_cyclic_imports", "check_python_cyclic_imports.py"),
    ("python_suppression_debt", "check_python_suppression_debt.py"),
    ("structural_similarity", "check_structural_similarity.py"),
    ("facade_wrappers", "check_facade_wrappers.py"),
    ("structural_complexity", "check_structural_complexity.py"),
    ("rust_test_shape", "check_rust_test_shape.py"),
    ("rustsec_policy", "check_rustsec_policy.py"),
    ("screenshot_integrity", "check_screenshot_integrity.py"),
    ("checkpoint_budget_shape", "check_checkpoint_budget_shape.py"),
    ("startup_authority_contract", "check_startup_authority_contract.py"),
    ("test_coverage_parity", "check_test_coverage_parity.py"),
    ("typed_enum_connectivity", "check_typed_enum_connectivity.py"),
    ("workflow_action_pinning", "check_workflow_action_pinning.py"),
    ("workflow_shell_hygiene", "check_workflow_shell_hygiene.py"),
    ("governance_closure", "check_governance_closure.py"),
)

CHECK_SCRIPT_FILES = dict(_CHECK_SCRIPT_ENTRIES)

CHECK_SCRIPT_RELATIVE_PATHS = {
    name: f"{CHECKS_DIR}/{filename}" for name, filename in CHECK_SCRIPT_FILES.items()
}

CHECK_SCRIPT_PATHS = {
    name: REPO_ROOT / relative for name, relative in CHECK_SCRIPT_RELATIVE_PATHS.items()
}

_PROBE_SCRIPT_ENTRIES = (
    ("probe_concurrency", "probe_concurrency.py"),
    ("probe_architecture_connectivity", "probe_architecture_connectivity.py"),
    ("probe_typed_authority_provenance", "probe_typed_authority_provenance.py"),
    ("probe_event_id_uniqueness", "probe_event_id_uniqueness.py"),
    ("probe_command_result_contract", "probe_command_result_contract.py"),
    ("probe_inter_agent_communication_lag", "probe_inter_agent_communication_lag.py"),
    ("probe_packet_carry_forward_debt", "probe_packet_carry_forward_debt.py"),
    (
        "probe_event_field_naming_consistency",
        "probe_event_field_naming_consistency.py",
    ),
    ("probe_design_smells", "probe_design_smells.py"),
    ("probe_boolean_params", "probe_boolean_params.py"),
    ("probe_stringly_typed", "probe_stringly_typed.py"),
    ("probe_unwrap_chains", "probe_unwrap_chains.py"),
    ("probe_clone_density", "probe_clone_density.py"),
    ("probe_type_conversions", "probe_type_conversions.py"),
    ("probe_magic_numbers", "probe_magic_numbers.py"),
    ("probe_dict_as_struct", "probe_dict_as_struct.py"),
    ("probe_unnecessary_intermediates", "probe_unnecessary_intermediates.py"),
    ("probe_vague_errors", "probe_vague_errors.py"),
    ("probe_defensive_overchecking", "probe_defensive_overchecking.py"),
    ("probe_single_use_helpers", "probe_single_use_helpers.py"),
    ("probe_exception_quality", "probe_exception_quality.py"),
    ("probe_compatibility_shims", "probe_compatibility_shims.py"),
    ("probe_blank_line_frequency", "probe_blank_line_frequency.py"),
    ("probe_identifier_density", "probe_identifier_density.py"),
    ("probe_term_consistency", "probe_term_consistency.py"),
    ("probe_cognitive_complexity", "probe_cognitive_complexity.py"),
    ("probe_mutable_parameter_density", "probe_mutable_parameter_density.py"),
    ("probe_fan_out", "probe_fan_out.py"),
    ("probe_side_effect_mixing", "probe_side_effect_mixing.py"),
    ("probe_match_arm_complexity", "probe_match_arm_complexity.py"),
    ("probe_mixed_concerns", "probe_mixed_concerns.py"),
    ("probe_split_advisor", "probe_split_advisor.py"),
    ("probe_tuple_return_complexity", "probe_tuple_return_complexity.py"),
)

PROBE_SCRIPT_FILES = dict(_PROBE_SCRIPT_ENTRIES)

PROBE_SCRIPT_RELATIVE_PATHS = {
    name: f"{CHECKS_DIR}/{filename}" for name, filename in PROBE_SCRIPT_FILES.items()
}

PROBE_SCRIPT_PATHS = {
    name: REPO_ROOT / relative for name, relative in PROBE_SCRIPT_RELATIVE_PATHS.items()
}


def probe_script_relative_path(name: str) -> str:
    """Return a probe script's repository-relative path."""
    try:
        return PROBE_SCRIPT_RELATIVE_PATHS[name]
    except KeyError as exc:
        raise KeyError(f"unknown probe script id: {name}") from exc


def probe_script_path(name: str) -> Path:
    """Return a probe script's absolute filesystem path."""
    try:
        return PROBE_SCRIPT_PATHS[name]
    except KeyError as exc:
        raise KeyError(f"unknown probe script id: {name}") from exc


def probe_script_cmd(name: str, *args: str) -> list[str]:
    """Return a python command list for one probe script."""
    return ["python3", probe_script_relative_path(name), *args]


LEGACY_CHECK_SCRIPT_REWRITES = {
    f"dev/scripts/{filename}": relative
    for _name, filename in _CHECK_SCRIPT_ENTRIES
    for relative in (f"{CHECKS_DIR}/{filename}",)
}

_LEGACY_ENTRYPOINT_REWRITE_ENTRIES = (
    ("dev/scripts/autonomy_workflow_bridge.py", "dev/scripts/workflow_bridge/autonomy.py"),
    ("dev/scripts/coderabbit_triage_bridge.py", "dev/scripts/coderabbit/bridge.py"),
    ("dev/scripts/collect_clippy_warnings.py", "dev/scripts/rust_tools/collect_clippy_warnings.py"),
    ("dev/scripts/dependency_graph_probe.py", "dev/scripts/rust_tools/dependency_graph_probe.py"),
    ("dev/scripts/mutants.py", "dev/scripts/mutation/cli.py"),
    ("dev/scripts/mutation_ralph_workflow_bridge.py", "dev/scripts/workflow_bridge/mutation_ralph.py"),
    ("dev/scripts/ralph_ai_fix.py", "dev/scripts/coderabbit/ralph_ai_fix.py"),
    ("dev/scripts/render_ci_badge.py", "dev/scripts/badges/ci.py"),
    ("dev/scripts/render_clippy_badge.py", "dev/scripts/badges/clippy.py"),
    ("dev/scripts/render_mutation_badge.py", "dev/scripts/badges/mutation.py"),
    ("dev/scripts/workflow_shell_bridge.py", "dev/scripts/workflow_bridge/shell.py"),
    ("dev/scripts/write_sha256_checksum.py", "dev/scripts/artifacts/sha256.py"),
)

LEGACY_ENTRYPOINT_SCRIPT_REWRITES = dict(_LEGACY_ENTRYPOINT_REWRITE_ENTRIES)

LEGACY_SCRIPT_PATH_REWRITES = dict(LEGACY_CHECK_SCRIPT_REWRITES)
LEGACY_SCRIPT_PATH_REWRITES.update(LEGACY_ENTRYPOINT_SCRIPT_REWRITES)


def check_script_relative_path(name: str) -> str:
    """Return a check script's repository-relative path."""
    try:
        return CHECK_SCRIPT_RELATIVE_PATHS[name]
    except KeyError as exc:
        raise KeyError(f"unknown check script id: {name}") from exc


def check_script_path(name: str) -> Path:
    """Return a check script's absolute filesystem path."""
    try:
        return CHECK_SCRIPT_PATHS[name]
    except KeyError as exc:
        raise KeyError(f"unknown check script id: {name}") from exc


def check_script_cmd(name: str, *args: str) -> list[str]:
    """Return a python command list for one check script."""
    return ["python3", check_script_relative_path(name), *args]


def check_script_shell_command(
    name: str,
    *args: str,
    env: Mapping[str, str] | None = None,
) -> str:
    """Return a shell command string for one check script."""
    return _script_shell_command(check_script_relative_path(name), *args, env=env)


def probe_script_shell_command(
    name: str,
    *args: str,
    env: Mapping[str, str] | None = None,
) -> str:
    """Return a shell command string for one probe script."""
    return _script_shell_command(probe_script_relative_path(name), *args, env=env)


def _script_shell_command(
    relative_path: str,
    *args: str,
    env: Mapping[str, str] | None = None,
) -> str:
    command = shlex.join(["python3", relative_path, *args])
    if not env:
        return command
    prefix = " ".join(
        f"{key}={shlex.quote(str(value))}" for key, value in env.items()
    )
    return f"{prefix} {command}"
