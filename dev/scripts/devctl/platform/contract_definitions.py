"""Compatibility re-exports for platform contract definitions."""

from .artifact_schema_rows import artifact_schemas
from .runtime_contract_rows import runtime_core_contracts
from .adapter_contract_rows import adapter_contracts
from .lifecycle_contract_rows import runtime_lifecycle_contracts


def shared_contracts():
    """Return the shared backend contracts the extracted platform should expose."""
    return runtime_core_contracts() + runtime_lifecycle_contracts() + adapter_contracts()


__all__ = ["artifact_schemas", "shared_contracts"]
