"""Governed-exception runtime-state contract rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .runtime_state_contract_rows_governed_exception_core import (
    GOVERNED_EXCEPTION_CORE_CONTRACTS,
)
from .runtime_state_contract_rows_governed_exception_descriptors import (
    GOVERNED_EXCEPTION_DESCRIPTOR_CONTRACTS,
)

if TYPE_CHECKING:
    from ..runtime.governed_exception_lifecycle import GovernedExceptionLifecycle
    from ..runtime.lifetime_bypass_mode import (
        BypassEvaluation,
        BypassExpiry,
        BypassLifecycle,
        BypassReceipt,
        BypassRequest,
    )
    from ..runtime.governed_exception_policy import (
        ExceptionClass,
        ExceptionLifecycleStatus,
        ExceptionPolicy,
    )
    from ..runtime.governed_exception_receipts import (
        AutoRepairReceipt,
        ClosureProof,
        ExceptionReceipt,
        ManualBypassImportReceipt,
        ResolutionReceipt,
    )

    _RUNTIME_MODEL_REFS: tuple[
        type[AutoRepairReceipt],
        type[BypassEvaluation],
        type[BypassExpiry],
        type[BypassLifecycle],
        type[BypassReceipt],
        type[BypassRequest],
        type[ClosureProof],
        type[ExceptionClass],
        type[ExceptionLifecycleStatus],
        type[ExceptionPolicy],
        type[ExceptionReceipt],
        type[GovernedExceptionLifecycle],
        type[ManualBypassImportReceipt],
        type[ResolutionReceipt],
    ]

GOVERNED_EXCEPTION_STATE_CONTRACTS = (
    *GOVERNED_EXCEPTION_CORE_CONTRACTS,
    *GOVERNED_EXCEPTION_DESCRIPTOR_CONTRACTS,
)

__all__ = ["GOVERNED_EXCEPTION_STATE_CONTRACTS"]
