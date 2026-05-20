"""Platform reducer artifact schema rows."""

from __future__ import annotations

from .contracts import ArtifactSchemaSpec

PLATFORM_REDUCER_ARTIFACT_SCHEMAS: tuple[ArtifactSchemaSpec, ...] = (
    ArtifactSchemaSpec(
        contract_id="ConnectivityRegistrySnapshot",
        owner_layer="governance_runtime",
        purpose=(
            "Generated contract/writer/reader connectivity snapshot consumed by "
            "startup, context graph, guards, and SYSTEM_MAP renderers."
        ),
        schema_version=1,
        emitter_path="dev/scripts/devctl/platform/connectivity_registry.py",
        constants_module="dev.scripts.devctl.platform.connectivity_registry_models",
        contract_id_attr="CONNECTIVITY_REGISTRY_CONTRACT_ID",
        schema_version_attr="CONNECTIVITY_REGISTRY_SCHEMA_VERSION",
        compatibility_window="additive fields only; startup and SYSTEM_MAP consumers must continue to read existing summary fields.",
        migration_path="Add snapshot fields additively and update connectivity guards plus renderers before changing consumers.",
        rollback_path="Restore prior snapshot constants and renderer behavior before removing existing connectivity consumers.",
    ),
    ArtifactSchemaSpec(
        contract_id="CoordinationTopologySnapshot",
        owner_layer="governance_runtime",
        purpose=(
            "Generated coordination, ownership, fanout, and concurrency posture "
            "snapshot emitted by the topology reducer."
        ),
        schema_version=1,
        emitter_path="dev/scripts/devctl/platform/coordination_topology.py",
        constants_module="dev.scripts.devctl.platform.coordination_topology_models",
        contract_id_attr="COORDINATION_TOPOLOGY_CONTRACT_ID",
        schema_version_attr="COORDINATION_TOPOLOGY_SCHEMA_VERSION",
        compatibility_window="additive fields only; develop and status consumers must keep reading existing topology fields.",
        migration_path="Add topology fields additively and update reducer/render tests before changing consumer expectations.",
        rollback_path="Restore prior reducer constants and emitted field shape before removing existing topology consumers.",
    ),
    ArtifactSchemaSpec(
        contract_id="ExtensionBundle",
        owner_layer="repo_packs",
        purpose=(
            "Repo-pack extension bundle schema for generated agent-facing "
            "surfaces and governed automation definitions."
        ),
        schema_version=1,
        emitter_path="dev/scripts/devctl/platform/extension_bundle_defaults.py",
        constants_module="dev.scripts.devctl.platform.extension_bundle",
        contract_id_attr="EXTENSION_BUNDLE_CONTRACT_ID",
        schema_version_attr="EXTENSION_BUNDLE_SCHEMA_VERSION",
        compatibility_window="additive fields only; repo-pack bundle consumers must keep existing surface and automation fields readable.",
        migration_path="Add bundle fields additively and update default bundles plus projection tests before changing generated surfaces.",
        rollback_path="Restore prior bundle constants and default bundle shape before removing existing surface generators.",
    ),
    ArtifactSchemaSpec(
        contract_id="PlanningIRSnapshot",
        owner_layer="governance_runtime",
        purpose=(
            "Generated planning intermediate representation for scheduler-facing "
            "phase, task, finding, and next-slice reducers."
        ),
        schema_version=1,
        emitter_path="dev/scripts/devctl/platform/planning_ir.py",
        constants_module="dev.scripts.devctl.platform.planning_ir_models",
        contract_id_attr="PLANNING_IR_CONTRACT_ID",
        schema_version_attr="PLANNING_IR_SCHEMA_VERSION",
        compatibility_window="additive fields only; scheduler and context graph readers must keep resolving existing planning fields.",
        migration_path="Add planning IR fields additively and update reduction, context graph, and CLI tests before changing consumer expectations.",
        rollback_path="Restore prior planning IR constants and reducer output before removing existing scheduler consumers.",
    ),
)
