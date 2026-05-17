"""Quality repair scheduler runtime contract rows."""

from __future__ import annotations

from ..runtime.quality_repair_scheduler import (
    CloudFinding,
    FindingAffectedScope,
    FindingApplicability,
    RepairPacket,
    StaleFindingReceipt,
)
from .contracts import ContractField, ContractSpec


def _spec(
    model: type[object],
    purpose: str,
    *fields: ContractField,
) -> ContractSpec:
    return ContractSpec(
        contract_id=model.__name__,
        owner_layer="governance_runtime",
        purpose=purpose,
        required_fields=fields,
        runtime_model=f"{model.__module__}:{model.__name__}",
        startup_surface_tokens=tuple(field.name for field in fields[:3]),
    )


QUALITY_REPAIR_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    _spec(
        FindingAffectedScope,
        "One file-hash scope affected by a cloud quality finding.",
        ContractField("path", "str", "Repo-relative affected file path."),
        ContractField(
            "file_sha256",
            "str",
            "File hash observed by the cloud proof.",
        ),
    ),
    _spec(
        CloudFinding,
        "Machine-readable cloud quality finding before local applicability is known.",
        ContractField("finding_id", "str", "Stable cloud finding id."),
        ContractField("source_snapshot_id", "str", "Cloud proof/source snapshot id."),
        ContractField(
            "affected_scopes",
            "tuple[FindingAffectedScope, ...]",
            "File-hash scopes the finding applies to.",
        ),
        ContractField("summary", "str", "Human-readable finding summary."),
        ContractField("severity", "str", "Finding severity."),
        ContractField("source_ref", "str", "Cloud artifact or workflow source ref."),
    ),
    _spec(
        FindingApplicability,
        "Local file-hash reconciliation decision for a CloudFinding.",
        ContractField("finding_id", "str", "Finding id being reconciled."),
        ContractField(
            "status",
            "str",
            "current, stale, missing_file, or reconciliation_only.",
        ),
        ContractField(
            "repair_authorized",
            "bool",
            "Whether a RepairPacket may be emitted.",
        ),
        ContractField(
            "current_paths",
            "tuple[str, ...]",
            "Affected paths whose hashes still match.",
        ),
        ContractField(
            "stale_paths",
            "tuple[str, ...]",
            "Affected paths whose hashes changed.",
        ),
        ContractField(
            "missing_paths",
            "tuple[str, ...]",
            "Affected paths no longer present.",
        ),
        ContractField(
            "observed_hashes",
            "dict[str, str] | None",
            "Current observed hashes.",
        ),
        ContractField("reason", "str", "Bounded decision reason."),
    ),
    _spec(
        RepairPacket,
        "Repair authority emitted only for currently applicable cloud findings.",
        ContractField("repair_packet_id", "str", "Stable repair packet id."),
        ContractField(
            "finding_id",
            "str",
            "Cloud finding id authorizing the repair.",
        ),
        ContractField(
            "affected_paths",
            "tuple[str, ...]",
            "Current affected file paths.",
        ),
        ContractField(
            "source_snapshot_id",
            "str",
            "Source snapshot that produced the finding.",
        ),
        ContractField("reason", "str", "Applicability reason authorizing repair."),
    ),
    _spec(
        StaleFindingReceipt,
        "Receipt proving a cloud finding became stale or reconciliation-only locally.",
        ContractField("receipt_id", "str", "Stable stale-finding receipt id."),
        ContractField(
            "finding_id",
            "str",
            "Cloud finding id that cannot authorize repair.",
        ),
        ContractField("stale_paths", "tuple[str, ...]", "Paths with changed hashes."),
        ContractField("missing_paths", "tuple[str, ...]", "Paths missing locally."),
        ContractField(
            "observed_hashes",
            "dict[str, str] | None",
            "Current observed hashes.",
        ),
        ContractField("reason", "str", "Applicability reason blocking repair."),
    ),
)


__all__ = ["QUALITY_REPAIR_STATE_CONTRACTS"]
