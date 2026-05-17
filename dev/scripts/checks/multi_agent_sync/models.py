"""Shared constants and lightweight models for the multi-agent sync guard."""

from __future__ import annotations

import re
from dataclasses import dataclass

MASTER_BOARD_HEADING = "## Multi-Agent Coordination Board"
RUNBOOK_BOARD_HEADING = "## 0) Current Execution Mode"
RUNBOOK_INSTRUCTION_HEADING = "## 14) Orchestrator Instruction Log (Append-Only)"
RUNBOOK_LEDGER_HEADING = "## 15) Shared Ledger (Append-Only)"
RUNBOOK_SIGNOFF_HEADING = "## 16) End-of-Cycle Signoff (Required)"

ALLOWED_MASTER_STATUSES = {
    "planned",
    "in-progress",
    "ready-for-review",
    "changes-requested",
    "approved",
    "merged",
    "blocked",
}
ALLOWED_LEDGER_STATUSES = ALLOWED_MASTER_STATUSES | {"ready"}
ALLOWED_INSTRUCTION_STATUSES = {"pending", "acked", "completed", "cancelled"}
UTC_Z_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
SIGNOFF_DATE_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)?$"
)
MP_RANGE_PATTERN = re.compile(r"MP-(\d{3})\.\.MP-(\d{3})")
MP_SINGLE_PATTERN = re.compile(r"MP-(\d{3})")
HANDOFF_TOKEN_PATTERN = re.compile(r"handoff[:=]([A-Za-z0-9_-]+)", re.IGNORECASE)
AGENT_NAME_PATTERN = re.compile(r"AGENT-(\d+)$")


@dataclass(frozen=True, slots=True)
class TableBundle:
    master_rows: list[dict]
    runbook_rows: list[dict]
    instruction_rows: list[dict]
    ledger_rows: list[dict]
    signoff_rows: list[dict]
    errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AgentBundle:
    master_by_agent: dict[str, dict]
    runbook_by_agent: dict[str, dict]
    master_agents: set[str]
    runbook_agents: set[str]
    required_agents: set[str]
    signoff_by_signer: dict[str, dict]
    signoff_signers: set[str]
    expected_signers: set[str]

