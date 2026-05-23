"""Constants for current-row typed proof assembly."""

from __future__ import annotations

import re

from dev.scripts.checks.check_bootstrap import REPO_ROOT

DEFAULT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
DEFAULT_PLAN_INDEX_PATH = REPO_ROOT / "dev/state/plan_index.jsonl"
DEFAULT_SNAPSHOTS_PATH = REPO_ROOT / "dev/state/plan_source_snapshots.jsonl"
DEFAULT_INGESTION_RECEIPTS_PATH = REPO_ROOT / "dev/state/plan_ingestion_receipts.jsonl"
DEFAULT_CLOSURE_RECEIPTS_PATH = REPO_ROOT / "dev/state/plan_row_closure_receipts.jsonl"
DEFAULT_FEATURE_PROOF_DIR = REPO_ROOT / "dev/reports/feature_proof_receipts"
DEFAULT_GUARD_OUTPUT_PATHS = (
    REPO_ROOT / "dev/reports/plan_execution/guard_runs.jsonl",
    REPO_ROOT / "dev/reports/push/latest_check_router_preflight.json",
)
DEFAULT_DOGFOOD_OUTPUT_PATHS = (REPO_ROOT / "dev/reports/dogfood/runs.jsonl",)
DEFAULT_COLLABORATION_EVIDENCE_PATHS = (
    REPO_ROOT / "dev/reports/review_channel/events/trace.ndjson",
    REPO_ROOT / "dev/reports/review_channel/projections/latest/trace.ndjson",
    REPO_ROOT / "dev/reports/review_channel/projections/latest/review_state.json",
    REPO_ROOT / "dev/reports/review_channel/projections/trace.ndjson",
    REPO_ROOT / "dev/reports/review_channel/projections/review_state.json",
)
DEFAULT_FINAL_GATE_PATHS = (REPO_ROOT / "dev/reports/plan_execution/final_gate_latest.json",)
DEFAULT_PROJECTION_PATH = REPO_ROOT / "dev/reports/plan_execution/current_row.md"

CONTRACT_ID = "CurrentRowProofMode"
PROJECTION_CONTRACT_ID = "CurrentRowExecutionProjection"

REQUIRED_GUARD_IDS = (
    "check_feature_completion",
    "check_plan_row_must_advance",
    "check_no_ingestion_churn_without_advancement",
    "check_pre_commit_guard_coverage",
    "check_slice_finishes_or_reverts",
)
REQUIRED_TEST_COMMANDS = (
    "python3 dev/scripts/devctl.py test-python --suite devctl "
    "--path dev/scripts/devctl/tests/checks/test_check_current_row_proof_bundle.py",
)
REQUIRED_DOGFOOD_COMMANDS = ("python3 dev/scripts/devctl.py check-router --execute",)
REQUIRED_RECEIPT_TYPES = (
    "PlanSourceSnapshot",
    "PlanIntentIngestionReceipt",
    "FeatureProofReceipt",
    "PlanRowClosureReceipt",
)
REQUIRED_ACTOR_ROLE_SESSION_EVIDENCE = (
    "typed_review_channel_packet",
    "bidirectional_packet_exchange",
    "codex_to_claude_packet",
    "claude_to_codex_packet",
    "actor_id",
    "role_id",
    "session_id",
)

CHECKBOX_BY_STATUS = {
    "passed": "[x]",
    "blocked": "[!]",
    "failed": "[!]",
    "progress": "[~]",
    "deferred": "[-]",
}

PACKET_RE = re.compile(r"\brev_pkt_\d+\b")
EVENT_RE = re.compile(r"\brev_evt_\d+\b")
COLLABORATION_DIRECTIONS = ("codex_to_claude", "claude_to_codex")
NON_SEND_PACKET_EVENTS = {
    "packet_body_observed",
    "packet_expired",
    "packet_creation_binding_recorded",
}
