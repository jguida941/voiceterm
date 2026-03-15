"""Shared contract definitions for the reusable governance platform."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


def _runtime_contracts() -> tuple[ContractSpec, ...]:
    return (
        ContractSpec(
            contract_id="RepoPack",
            owner_layer="repo_packs",
            purpose=(
                "Declares repo policy, docs templates, workflow defaults, and "
                "adoption checks for one repository family."
            ),
            required_fields=(
                ContractField("pack_id", "str", "Stable repo-pack identifier."),
                ContractField(
                    "policy_path",
                    "str",
                    "Path to the repo policy file used by quality/governance commands.",
                ),
                ContractField(
                    "workflow_profiles",
                    "list[str]",
                    "Allowlisted workflow/action profiles exposed for this repo.",
                ),
            ),
        ),
        ContractSpec(
            contract_id="TypedAction",
            owner_layer="governance_runtime",
            purpose=(
                "Canonical command payload for check, probe, bootstrap, fix, "
                "report, export, review, and remediation actions."
            ),
            required_fields=(
                ContractField("action_id", "str", "Stable typed action identifier."),
                ContractField(
                    "repo_pack_id",
                    "str",
                    "Repo pack responsible for repo-local policy or defaults.",
                ),
                ContractField(
                    "parameters",
                    "dict[str, object]",
                    "Machine-readable action arguments after parsing/validation.",
                ),
            ),
        ),
        ContractSpec(
            contract_id="ControlState",
            owner_layer="governance_runtime",
            purpose=(
                "Machine-readable status snapshot for runs, queue state, "
                "approvals, warnings, and errors across clients."
            ),
            required_fields=(
                ContractField("timestamp", "str", "UTC timestamp for the snapshot."),
                ContractField(
                    "active_runs",
                    "list[dict[str, object]]",
                    "Current governed runs visible to CLI/UI clients.",
                ),
                ContractField(
                    "approvals",
                    "dict[str, object]",
                    "Approval/waiver state projected into every frontend.",
                ),
            ),
        ),
        ContractSpec(
            contract_id="ReviewState",
            owner_layer="governance_runtime",
            purpose=(
                "Machine-readable review-channel snapshot for session metadata, "
                "queue state, packets, bridge status, and agent registry."
            ),
            required_fields=(
                ContractField("timestamp", "str", "UTC timestamp for the snapshot."),
                ContractField(
                    "review",
                    "dict[str, object]",
                    "Typed review session metadata shared by CLI/UI clients.",
                ),
                ContractField(
                    "packets",
                    "list[dict[str, object]]",
                    "Typed review-channel packets, including approval state.",
                ),
            ),
        ),
        ContractSpec(
            contract_id="RunRecord",
            owner_layer="governance_runtime",
            purpose=(
                "Durable record for one governed execution episode, including "
                "inputs, findings, repairs, and outcomes."
            ),
            required_fields=(
                ContractField("run_id", "str", "Stable execution episode identifier."),
                ContractField(
                    "action_id",
                    "str",
                    "Typed action executed for the episode.",
                ),
                ContractField(
                    "artifact_paths",
                    "list[str]",
                    "Materialized artifacts emitted during the episode.",
                ),
            ),
        ),
        ContractSpec(
            contract_id="ArtifactStore",
            owner_layer="governance_runtime",
            purpose=(
                "Stable storage contract for reports, projections, review "
                "packets, snapshots, and benchmark evidence."
            ),
            required_fields=(
                ContractField("root", "str", "Root path for managed artifacts."),
                ContractField(
                    "retention_policy",
                    "dict[str, object]",
                    "Retention/deletion rules enforced for this artifact family.",
                ),
                ContractField(
                    "managed_kinds",
                    "list[str]",
                    "Artifact kinds stored under the root.",
                ),
            ),
        ),
    )


def _adapter_contracts() -> tuple[ContractSpec, ...]:
    return (
        ContractSpec(
            contract_id="ProviderAdapter",
            owner_layer="governance_adapters",
            purpose=(
                "Abstracts provider-specific launch/status/fix behavior so loops "
                "do not hard-code Codex or Claude."
            ),
            required_fields=(
                ContractField("provider_id", "str", "Stable provider adapter identifier."),
                ContractField(
                    "capabilities",
                    "list[str]",
                    "Provider features the runtime may rely on.",
                ),
                ContractField(
                    "launch_mode",
                    "str",
                    "How the adapter executes typed actions for the provider.",
                ),
            ),
        ),
        ContractSpec(
            contract_id="WorkflowAdapter",
            owner_layer="governance_adapters",
            purpose=(
                "Abstracts CI/workflow execution so Ralph, mutation, and "
                "review loops stay reusable across repos."
            ),
            required_fields=(
                ContractField("adapter_id", "str", "Stable workflow adapter identifier."),
                ContractField(
                    "transport",
                    "str",
                    "Workflow transport such as local, GitHub, or future CI hosts.",
                ),
                ContractField(
                    "allowed_actions",
                    "list[str]",
                    "Allowlisted workflow actions exposed through the adapter.",
                ),
            ),
        ),
    )


def shared_contracts() -> tuple[ContractSpec, ...]:
    """Return the shared backend contracts the extracted platform should expose."""
    return _runtime_contracts() + _adapter_contracts()
