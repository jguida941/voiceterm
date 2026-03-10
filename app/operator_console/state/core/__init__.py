"""Core shared dataclasses and value helpers for Operator Console state."""

from .models import (
    AgentLaneData,
    ApprovalRequest,
    ContextPackRef,
    OperatorConsoleSnapshot,
    OperatorDecisionArtifact,
    QualityBacklogSnapshot,
    QualityPrioritySignal,
    utc_timestamp,
)
from .readability import AUDIENCE_MODES, audience_mode_label, resolve_audience_mode
from .value_coercion import safe_int, safe_text
