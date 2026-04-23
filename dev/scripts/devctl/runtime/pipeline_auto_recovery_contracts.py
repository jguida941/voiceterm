"""Typed contracts for ``devctl pipeline --action auto-recover``.

The auto-recover lane classifies a wedged ``commit_pipeline.json``
artifact into a typed :class:`PipelineAutoRecoveryClassification`, then
executes the correct recovery sub-action (abandon, recover, or
refresh-authorization) and emits a single
:class:`PipelineAutoRecoveryReceipt` that captures the decision, the
chosen action, and the prior/new pipeline states.

Keeping the classification vocabulary and the receipt schema in one
module means downstream surfaces (dashboard, probe report, future
``finalize-or-publish`` command) can consume the same constants without
re-deriving them from argparse strings or ad hoc dict keys.

Both dataclasses are frozen + slotted so the contracts behave like
value types. ``to_dict`` returns a stable field order so JSON consumers
and snapshot tests do not have to sort keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Contract identifiers ------------------------------------------------

CLASSIFICATION_CONTRACT_ID = "PipelineAutoRecoveryClassification"
RECEIPT_CONTRACT_ID = "PipelineAutoRecoveryReceipt"
SCHEMA_VERSION = 1


# Classification vocabulary ------------------------------------------
#
# These are the only strings the auto-recover command will write into
# ``classification``. Downstream consumers should treat them as closed.

CLASSIFICATION_ALREADY_CLEAN = "already_clean"
CLASSIFICATION_NEEDS_ABANDON = "needs_abandon"
CLASSIFICATION_NEEDS_RECOVER = "needs_recover"
CLASSIFICATION_NEEDS_REFRESH_AUTHORIZATION = "needs_refresh_authorization"
CLASSIFICATION_AMBIGUOUS = "ambiguous"

VALID_CLASSIFICATIONS: tuple[str, ...] = (
    CLASSIFICATION_ALREADY_CLEAN,
    CLASSIFICATION_NEEDS_ABANDON,
    CLASSIFICATION_NEEDS_RECOVER,
    CLASSIFICATION_NEEDS_REFRESH_AUTHORIZATION,
    CLASSIFICATION_AMBIGUOUS,
)


# Chosen-action vocabulary -------------------------------------------
#
# ``chosen_action`` maps 1:1 to the existing ``--action`` choices plus
# ``none`` (when no mutation was needed) and ``bailed`` (when the
# classifier hit ``ambiguous`` and refused to guess).

CHOSEN_ACTION_NONE = "none"
CHOSEN_ACTION_ABANDON = "abandon"
CHOSEN_ACTION_RECOVER = "recover"
CHOSEN_ACTION_REFRESH_AUTHORIZATION = "refresh-authorization"
CHOSEN_ACTION_BAILED = "bailed"

VALID_CHOSEN_ACTIONS: tuple[str, ...] = (
    CHOSEN_ACTION_NONE,
    CHOSEN_ACTION_ABANDON,
    CHOSEN_ACTION_RECOVER,
    CHOSEN_ACTION_REFRESH_AUTHORIZATION,
    CHOSEN_ACTION_BAILED,
)


@dataclass(frozen=True, slots=True)
class PipelineAutoRecoveryClassification:
    """Typed decision output from the auto-recover classifier.

    ``classification`` selects which recovery lane should run.
    ``reason`` is a short machine-readable token (e.g.
    ``head_drifted_on_recoverable_state``) — not a prose sentence — so
    tests can assert against it without string fuzz.
    """

    classification: str
    reason: str
    pipeline_state: str
    head_has_moved: bool
    authorization_expired: bool
    head_movement_classification: str = ""
    managed_receipt_parent_sha: str = ""
    schema_version: int = SCHEMA_VERSION
    contract_id: str = CLASSIFICATION_CONTRACT_ID

    def __post_init__(self) -> None:
        if self.classification not in VALID_CLASSIFICATIONS:
            raise ValueError(
                "PipelineAutoRecoveryClassification.classification must be "
                f"one of {VALID_CLASSIFICATIONS!r}; got {self.classification!r}"
            )
        if not self.reason:
            raise ValueError(
                "PipelineAutoRecoveryClassification.reason is required"
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dict in a stable field order."""
        return dict((
            ("schema_version", self.schema_version),
            ("contract_id", self.contract_id),
            ("classification", self.classification),
            ("reason", self.reason),
            ("pipeline_state", self.pipeline_state),
            ("head_has_moved", self.head_has_moved),
            ("authorization_expired", self.authorization_expired),
            ("head_movement_classification", self.head_movement_classification),
            ("managed_receipt_parent_sha", self.managed_receipt_parent_sha),
        ))


@dataclass(frozen=True, slots=True)
class PipelineAutoRecoveryReceipt:
    """Audit receipt for a single ``--action auto-recover`` run.

    Unlike :class:`~pipeline_recovery_receipt.PipelineRecoveryReceipt`
    (which records one sub-action), this receipt captures the composite
    decision the classifier made. ``sub_receipt_path`` is the absolute
    path of the sub-action's own receipt (abandon/recover/refresh), or
    ``""`` when no mutation was performed.
    """

    classification: str
    chosen_action: str
    reason: str
    pipeline_id: str
    previous_state: str
    new_state: str
    operator_actor: str
    generated_at_utc: str
    sub_receipt_path: str = ""
    artifact_paths: tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = SCHEMA_VERSION
    contract_id: str = RECEIPT_CONTRACT_ID

    def __post_init__(self) -> None:
        if self.classification not in VALID_CLASSIFICATIONS:
            raise ValueError(
                "PipelineAutoRecoveryReceipt.classification must be one of "
                f"{VALID_CLASSIFICATIONS!r}; got {self.classification!r}"
            )
        if self.chosen_action not in VALID_CHOSEN_ACTIONS:
            raise ValueError(
                "PipelineAutoRecoveryReceipt.chosen_action must be one of "
                f"{VALID_CHOSEN_ACTIONS!r}; got {self.chosen_action!r}"
            )
        if not self.reason:
            raise ValueError(
                "PipelineAutoRecoveryReceipt.reason is required"
            )
        if not self.generated_at_utc:
            raise ValueError(
                "PipelineAutoRecoveryReceipt.generated_at_utc is required"
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dict in a stable field order."""
        return dict((
            ("schema_version", self.schema_version),
            ("contract_id", self.contract_id),
            ("classification", self.classification),
            ("chosen_action", self.chosen_action),
            ("reason", self.reason),
            ("pipeline_id", self.pipeline_id),
            ("previous_state", self.previous_state),
            ("new_state", self.new_state),
            ("operator_actor", self.operator_actor),
            ("generated_at_utc", self.generated_at_utc),
            ("sub_receipt_path", self.sub_receipt_path),
            ("artifact_paths", list(self.artifact_paths)),
        ))
