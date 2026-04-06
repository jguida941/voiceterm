"""Compatibility bundle for review/pipeline runtime-state contract rows."""

from __future__ import annotations

from .runtime_state_contract_rows_pipeline import PIPELINE_STATE_CONTRACTS
from .runtime_state_contract_rows_review import REVIEW_STATE_CONTRACTS


REVIEW_PIPELINE_STATE_CONTRACTS = REVIEW_STATE_CONTRACTS + PIPELINE_STATE_CONTRACTS
