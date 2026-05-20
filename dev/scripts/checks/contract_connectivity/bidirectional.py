"""Bidirectional contract-edge findings."""

from __future__ import annotations

from .findings import _duplicate_contract_keys, _same_package
from .inventory import SourceIndex, contract_references
from .models import BidirectionalReferenceFinding, DuplicateContractFinding


def bidirectional_reference_findings(
    index: SourceIndex,
    *,
    duplicate_findings: tuple[DuplicateContractFinding, ...] = (),
) -> tuple[BidirectionalReferenceFinding, ...]:
    """Return contracts missing inbound or outbound typed-contract edges."""
    duplicate_keys = _duplicate_contract_keys(duplicate_findings)
    contract_lookup = {contract.key: contract for contract in index.contracts}
    modules_by_path = {module.module_path: module for module in index.parsed_modules}
    findings: list[BidirectionalReferenceFinding] = []

    for contract in sorted(index.contracts, key=lambda row: row.module_path):
        if contract.key in duplicate_keys:
            continue
        module = modules_by_path.get(contract.module_path)
        forward_keys = (
            contract_references(module, contract_lookup)
            if module is not None
            else set()
        )
        forward_contracts = tuple(
            sorted(
                (
                    contract_lookup[key]
                    for key in forward_keys
                    if key != contract.key and key in contract_lookup
                ),
                key=lambda row: (row.module_path, row.contract_name),
            ),
        )
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
        missing_directions = tuple(
            direction
            for direction, missing in (
                ("forward", not forward_contracts),
                ("backward", not external_importers),
            )
            if missing
        )
        if not missing_directions:
            continue
        findings.append(
            BidirectionalReferenceFinding(
                contract_name=contract.contract_name,
                layer=contract.layer,
                module_name=contract.module_name,
                module_path=contract.module_path,
                forward_reference_count=len(forward_contracts),
                backward_importer_count=len(external_importers),
                missing_directions=missing_directions,
                forward_contracts=tuple(
                    item.contract_name for item in forward_contracts
                ),
                forward_contract_paths=tuple(
                    item.module_path for item in forward_contracts
                ),
                importer_modules=tuple(
                    importer.module_name for importer in external_importers
                ),
                importer_paths=tuple(
                    importer.module_path for importer in external_importers
                ),
            )
        )
    return tuple(findings)


def bidirectional_reference_key(item: BidirectionalReferenceFinding) -> str:
    missing = ",".join(item.missing_directions)
    return f"{item.module_path}::{item.contract_name}::{missing}"
