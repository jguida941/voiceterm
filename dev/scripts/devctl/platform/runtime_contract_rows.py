"""Runtime contract row exports for the reusable governance platform blueprint."""

from __future__ import annotations

from .contracts import ContractSpec
from .runtime_identity_contract_rows import RUNTIME_IDENTITY_CONTRACTS
from .runtime_state_contract_rows import RUNTIME_STATE_CONTRACTS


def runtime_core_contracts() -> tuple[ContractSpec, ...]:
    """Return the current shared runtime contract rows."""
    return RUNTIME_IDENTITY_CONTRACTS + RUNTIME_STATE_CONTRACTS
