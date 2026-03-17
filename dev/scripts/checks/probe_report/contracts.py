"""Backward-compat contract shim for probe-report packet families."""
# shim-owner: tooling/runtime
# shim-reason: keep probe-report contract helpers stable while the canonical
# shim-reason: finding/packet contracts live under `devctl.runtime`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/runtime/finding_contracts.py

from __future__ import annotations

try:
    from dev.scripts.devctl.runtime.finding_contracts import (
    DECISION_PACKET_CONTRACT_ID,
    DECISION_PACKET_SCHEMA_VERSION,
    DecisionPacketPolicy,
    DecisionPacketRecord,
    FINDING_CONTRACT_ID,
    FINDING_SCHEMA_VERSION,
    FindingIdentitySeed,
    FindingRecord,
        PROBE_ALLOWLIST_CONTRACT_ID,
        PROBE_ALLOWLIST_SCHEMA_VERSION,
        PROBE_REPORT_CONTRACT_ID,
        PROBE_REPORT_SCHEMA_VERSION,
        PROBE_RULE_VERSION,
        PROBE_TOPOLOGY_CONTRACT_ID,
        PROBE_TOPOLOGY_SCHEMA_VERSION,
        REVIEW_PACKET_CONTRACT_ID,
        REVIEW_PACKET_SCHEMA_VERSION,
        REVIEW_TARGETS_CONTRACT_ID,
        REVIEW_TARGETS_SCHEMA_VERSION,
        build_finding_id,
        decision_packet_from_finding,
        enrich_probe_hint_contract,
        finding_from_probe_hint,
    )
except ModuleNotFoundError:  # pragma: no cover
    from devctl.runtime.finding_contracts import (
        DECISION_PACKET_CONTRACT_ID,
        DECISION_PACKET_SCHEMA_VERSION,
        DecisionPacketPolicy,
        DecisionPacketRecord,
        FINDING_CONTRACT_ID,
        FINDING_SCHEMA_VERSION,
        FindingIdentitySeed,
        FindingRecord,
        PROBE_ALLOWLIST_CONTRACT_ID,
        PROBE_ALLOWLIST_SCHEMA_VERSION,
        PROBE_REPORT_CONTRACT_ID,
        PROBE_REPORT_SCHEMA_VERSION,
        PROBE_RULE_VERSION,
        PROBE_TOPOLOGY_CONTRACT_ID,
        PROBE_TOPOLOGY_SCHEMA_VERSION,
        REVIEW_PACKET_CONTRACT_ID,
        REVIEW_PACKET_SCHEMA_VERSION,
        REVIEW_TARGETS_CONTRACT_ID,
        REVIEW_TARGETS_SCHEMA_VERSION,
        build_finding_id,
        decision_packet_from_finding,
        enrich_probe_hint_contract,
        finding_from_probe_hint,
    )

PROBE_FINDING_RULE_VERSION = PROBE_RULE_VERSION
build_probe_finding_id = build_finding_id

__all__ = [
    "DECISION_PACKET_CONTRACT_ID",
    "DECISION_PACKET_SCHEMA_VERSION",
    "DecisionPacketPolicy",
    "DecisionPacketRecord",
    "FINDING_CONTRACT_ID",
    "FINDING_SCHEMA_VERSION",
    "FindingIdentitySeed",
    "FindingRecord",
    "PROBE_ALLOWLIST_CONTRACT_ID",
    "PROBE_ALLOWLIST_SCHEMA_VERSION",
    "PROBE_FINDING_RULE_VERSION",
    "PROBE_REPORT_CONTRACT_ID",
    "PROBE_REPORT_SCHEMA_VERSION",
    "PROBE_RULE_VERSION",
    "PROBE_TOPOLOGY_CONTRACT_ID",
    "PROBE_TOPOLOGY_SCHEMA_VERSION",
    "REVIEW_PACKET_CONTRACT_ID",
    "REVIEW_PACKET_SCHEMA_VERSION",
    "REVIEW_TARGETS_CONTRACT_ID",
    "REVIEW_TARGETS_SCHEMA_VERSION",
    "build_finding_id",
    "build_probe_finding_id",
    "decision_packet_from_finding",
    "enrich_probe_hint_contract",
    "finding_from_probe_hint",
]
