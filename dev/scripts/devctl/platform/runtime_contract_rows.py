"""Runtime contract row exports for the reusable governance platform blueprint."""

from __future__ import annotations

from .contracts import ContractSpec
from .runtime_guard_violation_contract_rows import GUARD_VIOLATION_CONTRACTS
from .runtime_identity_contract_rows import RUNTIME_IDENTITY_CONTRACTS
from .runtime_state_contract_rows import RUNTIME_STATE_CONTRACTS
from .worktree_orphan_contract_rows import worktree_orphan_contracts


def runtime_core_contracts() -> tuple[ContractSpec, ...]:
    """Return the current shared runtime contract rows."""
    return (
        RUNTIME_IDENTITY_CONTRACTS
        + RUNTIME_STATE_CONTRACTS
        + worktree_orphan_contracts()
        + GUARD_VIOLATION_CONTRACTS
    )
