"""Additive Phase 0 metadata for plan-intent ingestion receipts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from .value_coercion import (
    coerce_mapping,
    coerce_mapping_items,
    coerce_int,
    coerce_string,
    coerce_string_items,
)


@dataclass(frozen=True, slots=True)
class PlanCompositionDispositionEntry:
    """Classify one proposed plan row before it becomes durable authority."""

    row_id: str
    disposition: str
    owning_mp_family: str
    existing_owner_row_refs: tuple[str, ...] = ()
    packet_binding_refs: tuple[str, ...] = ()
    source_snapshot_ref: str = ""
    why_not_duplicate: str = ""
    phase_allowed_to_block: str = ""
    phase_allowed_to_mutate: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["existing_owner_row_refs"] = list(self.existing_owner_row_refs)
        payload["packet_binding_refs"] = list(self.packet_binding_refs)
        return payload

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object] | object,
    ) -> "PlanCompositionDispositionEntry":
        mapping = coerce_mapping(payload)
        return cls(
            row_id=coerce_string(mapping.get("row_id")),
            disposition=coerce_string(mapping.get("disposition")),
            owning_mp_family=coerce_string(mapping.get("owning_mp_family")),
            existing_owner_row_refs=coerce_string_items(
                mapping.get("existing_owner_row_refs")
            ),
            packet_binding_refs=coerce_string_items(
                mapping.get("packet_binding_refs")
            ),
            source_snapshot_ref=coerce_string(mapping.get("source_snapshot_ref")),
            why_not_duplicate=coerce_string(mapping.get("why_not_duplicate")),
            phase_allowed_to_block=coerce_string(
                mapping.get("phase_allowed_to_block")
            ),
            phase_allowed_to_mutate=coerce_string(
                mapping.get("phase_allowed_to_mutate")
            ),
        )


@dataclass(frozen=True, slots=True)
class RepoStateFingerprint:
    """Best-effort git/worktree fingerprint captured alongside a receipt."""

    head_sha: str = ""
    branch: str = ""
    merge_base_sha: str = ""
    worktree_identity: str = ""
    staged_diff_hash: str = ""
    unstaged_diff_hash: str = ""
    untracked_manifest_hash: str = ""
    ignored_governed_artifact_hash: str = ""
    submodule_or_nested_repo_manifest: tuple[str, ...] = ()
    generated_projection_hashes: dict[str, str] | None = None
    dependency_lockfile_hashes: dict[str, str] | None = None
    observed_at_utc: str = ""
    dirty_policy: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["submodule_or_nested_repo_manifest"] = list(
            self.submodule_or_nested_repo_manifest
        )
        payload["generated_projection_hashes"] = dict(
            self.generated_projection_hashes or {}
        )
        payload["dependency_lockfile_hashes"] = dict(
            self.dependency_lockfile_hashes or {}
        )
        return payload

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object] | object,
    ) -> "RepoStateFingerprint":
        mapping = coerce_mapping(payload)
        generated_projection_hashes = dict(
            coerce_mapping(mapping.get("generated_projection_hashes"))
        )
        dependency_lockfile_hashes = dict(
            coerce_mapping(mapping.get("dependency_lockfile_hashes"))
        )
        return cls(
            head_sha=coerce_string(mapping.get("head_sha")),
            branch=coerce_string(mapping.get("branch")),
            merge_base_sha=coerce_string(mapping.get("merge_base_sha")),
            worktree_identity=coerce_string(mapping.get("worktree_identity")),
            staged_diff_hash=coerce_string(mapping.get("staged_diff_hash")),
            unstaged_diff_hash=coerce_string(mapping.get("unstaged_diff_hash")),
            untracked_manifest_hash=coerce_string(
                mapping.get("untracked_manifest_hash")
            ),
            ignored_governed_artifact_hash=coerce_string(
                mapping.get("ignored_governed_artifact_hash")
            ),
            submodule_or_nested_repo_manifest=coerce_string_items(
                mapping.get("submodule_or_nested_repo_manifest")
            ),
            generated_projection_hashes=generated_projection_hashes,
            dependency_lockfile_hashes=dependency_lockfile_hashes,
            observed_at_utc=coerce_string(mapping.get("observed_at_utc")),
            dirty_policy=coerce_string(mapping.get("dirty_policy")),
        )


@dataclass(frozen=True, slots=True)
class ReceiptCoverageInventory:
    """Summarize which existing MP-377 rows already have durable proof."""

    total_mp377_rows: int = 0
    accepted_receipt_rows: tuple[str, ...] = ()
    packet_binding_only_rows: tuple[str, ...] = ()
    source_snapshot_only_rows: tuple[str, ...] = ()
    superseded_rows: tuple[str, ...] = ()
    deferred_rows: tuple[str, ...] = ()
    missing_proof_rows: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["accepted_receipt_rows"] = list(self.accepted_receipt_rows)
        payload["packet_binding_only_rows"] = list(self.packet_binding_only_rows)
        payload["source_snapshot_only_rows"] = list(self.source_snapshot_only_rows)
        payload["superseded_rows"] = list(self.superseded_rows)
        payload["deferred_rows"] = list(self.deferred_rows)
        payload["missing_proof_rows"] = list(self.missing_proof_rows)
        return payload

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object] | object,
    ) -> "ReceiptCoverageInventory":
        mapping = coerce_mapping(payload)
        return cls(
            total_mp377_rows=coerce_int(mapping.get("total_mp377_rows")),
            accepted_receipt_rows=coerce_string_items(
                mapping.get("accepted_receipt_rows")
            ),
            packet_binding_only_rows=coerce_string_items(
                mapping.get("packet_binding_only_rows")
            ),
            source_snapshot_only_rows=coerce_string_items(
                mapping.get("source_snapshot_only_rows")
            ),
            superseded_rows=coerce_string_items(mapping.get("superseded_rows")),
            deferred_rows=coerce_string_items(mapping.get("deferred_rows")),
            missing_proof_rows=coerce_string_items(
                mapping.get("missing_proof_rows")
            ),
        )


@dataclass(frozen=True, slots=True)
class CommandManifestProof:
    """Registry-backed proof for one command referenced by the plan source."""

    command: str
    classification: str
    registry_owner: str = ""
    proof_status: str = ""
    resolved_entry: str = ""
    bundle_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["bundle_refs"] = list(self.bundle_refs)
        return payload

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object] | object,
    ) -> "CommandManifestProof":
        mapping = coerce_mapping(payload)
        return cls(
            command=coerce_string(mapping.get("command")),
            classification=coerce_string(mapping.get("classification")),
            registry_owner=coerce_string(mapping.get("registry_owner")),
            proof_status=coerce_string(mapping.get("proof_status")),
            resolved_entry=coerce_string(mapping.get("resolved_entry")),
            bundle_refs=coerce_string_items(mapping.get("bundle_refs")),
        )


@dataclass(frozen=True, slots=True)
class GuardMaturityRecord:
    """Best-effort guard maturity classification derived from existing registries."""

    guard_id: str
    maturity: str
    relative_path: str = ""
    source_command: str = ""
    bundle_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["bundle_refs"] = list(self.bundle_refs)
        return payload

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object] | object,
    ) -> "GuardMaturityRecord":
        mapping = coerce_mapping(payload)
        return cls(
            guard_id=coerce_string(mapping.get("guard_id")),
            maturity=coerce_string(mapping.get("maturity")),
            relative_path=coerce_string(mapping.get("relative_path")),
            source_command=coerce_string(mapping.get("source_command")),
            bundle_refs=coerce_string_items(mapping.get("bundle_refs")),
        )


def disposition_entries_from_mapping(
    value: object,
) -> tuple[PlanCompositionDispositionEntry, ...]:
    return tuple(
        PlanCompositionDispositionEntry.from_mapping(item)
        for item in coerce_mapping_items(value)
    )


def command_manifest_proofs_from_mapping(
    value: object,
) -> tuple[CommandManifestProof, ...]:
    return tuple(
        CommandManifestProof.from_mapping(item)
        for item in coerce_mapping_items(value)
    )


def guard_maturity_records_from_mapping(
    value: object,
) -> tuple[GuardMaturityRecord, ...]:
    return tuple(
        GuardMaturityRecord.from_mapping(item)
        for item in coerce_mapping_items(value)
    )


__all__ = [
    "CommandManifestProof",
    "GuardMaturityRecord",
    "PlanCompositionDispositionEntry",
    "RepoStateFingerprint",
    "ReceiptCoverageInventory",
    "command_manifest_proofs_from_mapping",
    "disposition_entries_from_mapping",
    "guard_maturity_records_from_mapping",
]
