"""Finding reducers for contract-connectivity analysis."""

from __future__ import annotations

from pathlib import PurePosixPath

from .inventory import (
    GENERIC_FIELDS,
    LAYER_ROOTS,
    ContractDefinition,
    SourceIndex,
    contract_references,
)
from .models import (
    DuplicateContractFinding,
    LayerContractCount,
    OrphanedContractFinding,
    StrandedContractFinding,
)

STRANDED_OVERLAP_THRESHOLD = 0.8
SEMANTIC_DUPLICATE_THRESHOLD = 0.8
PURPOSE_GUIDED_DUPLICATE_THRESHOLD = 0.6


def orphaned_contracts(
    index: SourceIndex,
    *,
    duplicate_findings: tuple[DuplicateContractFinding, ...] = (),
) -> tuple[OrphanedContractFinding, ...]:
    """Return contracts with zero explicit importer modules."""
    duplicate_keys = _duplicate_contract_keys(duplicate_findings)
    findings: list[OrphanedContractFinding] = []
    for contract in sorted(index.contracts, key=lambda row: row.module_path):
        if contract.key in duplicate_keys:
            continue
        importer_modules = tuple(
            sorted(
                index.importers_by_contract.get(contract.key, ()),
                key=lambda row: row.module_path,
            )
        )
        external_importers = tuple(
            importer
            for importer in importer_modules
            if not _same_package(contract.module_path, importer.module_path)
        )
        if external_importers:
            continue
        consumer_scope = "unreferenced" if not importer_modules else "internal_only"
        findings.append(
            OrphanedContractFinding(
                contract_name=contract.contract_name,
                layer=contract.layer,
                module_name=contract.module_name,
                module_path=contract.module_path,
                field_names=contract.field_names,
                consumer_scope=consumer_scope,
                importer_modules=tuple(
                    importer.module_name for importer in importer_modules
                ),
                importer_paths=tuple(
                    importer.module_path for importer in importer_modules
                ),
                cross_layer_importer_count=sum(
                    1
                    for importer in importer_modules
                    if importer.layer and importer.layer != contract.layer
                ),
            )
        )
    return tuple(findings)


def duplicate_contracts(
    contracts: tuple[ContractDefinition, ...],
) -> tuple[DuplicateContractFinding, ...]:
    """Return strongly overlapping contract pairs."""
    findings: list[DuplicateContractFinding] = []
    ordered = sorted(
        contracts,
        key=lambda row: (row.layer, row.module_path, row.contract_name),
    )
    for index, left in enumerate(ordered):
        left_fields = set(left.interesting_fields or left.field_names)
        if len(left_fields) < 2:
            left_fields = set(left.field_names)
        for right in ordered[index + 1 :]:
            if left.module_path == right.module_path:
                continue
            right_fields = set(right.interesting_fields or right.field_names)
            if len(right_fields) < 2:
                right_fields = set(right.field_names)
            exact_shared = tuple(sorted(left_fields & right_fields))
            exact_overlap_ratio = len(exact_shared) / max(
                1, min(len(left_fields), len(right_fields))
            )
            if len(exact_shared) >= 2 and exact_overlap_ratio >= 0.8:
                findings.append(
                    DuplicateContractFinding(
                        left_contract_name=left.contract_name,
                        left_layer=left.layer,
                        left_module_name=left.module_name,
                        left_module_path=left.module_path,
                        right_contract_name=right.contract_name,
                        right_layer=right.layer,
                        right_module_name=right.module_name,
                        right_module_path=right.module_path,
                        overlap_ratio=exact_overlap_ratio,
                        shared_fields=exact_shared,
                    )
                )
                continue

            shared_semantics = tuple(
                sorted(set(left.semantic_fields) & set(right.semantic_fields))
            )
            if len(shared_semantics) < 2:
                continue
            semantic_overlap_ratio = len(shared_semantics) / max(
                1,
                min(len(set(left.semantic_fields)), len(set(right.semantic_fields))),
            )
            if not _purpose_guided_semantic_match(
                left,
                right,
                semantic_overlap_ratio=semantic_overlap_ratio,
            ):
                continue
            findings.append(
                DuplicateContractFinding(
                    left_contract_name=left.contract_name,
                    left_layer=left.layer,
                    left_module_name=left.module_name,
                    left_module_path=left.module_path,
                    right_contract_name=right.contract_name,
                    right_layer=right.layer,
                    right_module_name=right.module_name,
                    right_module_path=right.module_path,
                    overlap_ratio=semantic_overlap_ratio,
                    shared_fields=shared_semantics,
                )
            )
    return tuple(findings)


def stranded_consumers(index: SourceIndex) -> tuple[StrandedContractFinding, ...]:
    """Return modules rebuilding typed contract state from raw mapping keys."""
    contracts_by_field: dict[str, set[tuple[str, str]]] = {}
    contract_lookup = {contract.key: contract for contract in index.contracts}
    for contract in index.contracts:
        for field in contract.interesting_fields:
            contracts_by_field.setdefault(field, set()).add(contract.key)

    findings: list[StrandedContractFinding] = []
    for module in sorted(index.parsed_modules, key=lambda row: row.module_path):
        if not module.layer:
            continue
        raw_keys = {
            key for key in module.raw_mapping_keys if key not in GENERIC_FIELDS
        }
        if len(raw_keys) < 2:
            continue
        imported = contract_references(module, contract_lookup)
        candidate_keys: set[tuple[str, str]] = set()
        for key in raw_keys:
            candidate_keys.update(contracts_by_field.get(key, ()))

        best: StrandedContractFinding | None = None
        for candidate_key in candidate_keys:
            if candidate_key in imported:
                continue
            contract = contract_lookup[candidate_key]
            if contract.module_name == module.module_name:
                continue
            shared = tuple(sorted(raw_keys & set(contract.interesting_fields)))
            if len(shared) < 2:
                continue
            overlap_ratio = len(shared) / max(1, len(contract.interesting_fields))
            if overlap_ratio < STRANDED_OVERLAP_THRESHOLD:
                continue
            finding = StrandedContractFinding(
                consumer_module_name=module.module_name,
                consumer_path=module.module_path,
                contract_name=contract.contract_name,
                contract_layer=contract.layer,
                contract_module_name=contract.module_name,
                contract_module_path=contract.module_path,
                overlap_ratio=overlap_ratio,
                shared_raw_keys=shared,
            )
            if best is None or finding.overlap_ratio > best.overlap_ratio:
                best = finding
        if best is not None:
            findings.append(best)
    return tuple(findings)


def layer_counts(
    contracts: tuple[ContractDefinition, ...],
) -> tuple[LayerContractCount, ...]:
    """Return per-layer dataclass inventory counts."""
    counts: dict[str, int] = {layer: 0 for layer in LAYER_ROOTS}
    for contract in contracts:
        if contract.layer:
            counts[contract.layer] += 1
    return tuple(
        LayerContractCount(layer=layer, contract_count=counts[layer])
        for layer in sorted(counts)
    )


def new_findings(items, baseline_items, key_fn):
    """Return findings absent from the baseline inventory."""
    baseline_keys = {key_fn(item) for item in baseline_items}
    return tuple(item for item in items if key_fn(item) not in baseline_keys)


def orphan_key(item: OrphanedContractFinding) -> str:
    return f"{item.module_path}::{item.contract_name}"


def duplicate_key(item: DuplicateContractFinding) -> str:
    left = f"{item.left_module_path}::{item.left_contract_name}"
    right = f"{item.right_module_path}::{item.right_contract_name}"
    return " <-> ".join(sorted((left, right)))


def stranded_key(item: StrandedContractFinding) -> str:
    return f"{item.consumer_path}::{item.contract_module_path}::{item.contract_name}"


def _duplicate_contract_keys(
    findings: tuple[DuplicateContractFinding, ...],
) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for item in findings:
        keys.add((item.left_module_name, item.left_contract_name))
        keys.add((item.right_module_name, item.right_contract_name))
    return keys


def _purpose_guided_semantic_match(
    left: ContractDefinition,
    right: ContractDefinition,
    *,
    semantic_overlap_ratio: float,
) -> bool:
    shared_purpose = set(left.purpose_tokens) & set(right.purpose_tokens)
    if not shared_purpose:
        return False
    if semantic_overlap_ratio >= SEMANTIC_DUPLICATE_THRESHOLD:
        return True
    return (
        semantic_overlap_ratio >= PURPOSE_GUIDED_DUPLICATE_THRESHOLD
        and len(shared_purpose) >= 2
    )


def _same_package(left_path: str, right_path: str) -> bool:
    return PurePosixPath(left_path).parent == PurePosixPath(right_path).parent


__all__ = [
    "duplicate_contracts",
    "duplicate_key",
    "layer_counts",
    "new_findings",
    "orphan_key",
    "orphaned_contracts",
    "stranded_consumers",
    "stranded_key",
]
