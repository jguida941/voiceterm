"""Typed pending-packet queue models."""

from __future__ import annotations

from dataclasses import asdict, dataclass


FULL_GUARD_BUNDLE_EVIDENCE_VALUES = {
    "--profile ci",
    "bundle.docs",
    "bundle.release",
    "bundle.runtime",
    "bundle.tooling",
}


@dataclass(frozen=True)
class PendingPacketQueueSnapshot:
    """Expiry-aware pending/expired packet view derived from the event log."""

    pending_packets: tuple[dict[str, object], ...]
    stale_packet_count: int = 0
    control_packets: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True)
class PacketQueueReconciliation:
    """Operator-facing summary of live vs expired/history packet state."""

    packet_total: int
    live_pending_total: int
    history_total: int
    stale_pending_total: int
    queue_pending_total: int
    queue_stale_total: int
    history_shown_total: int
    history_truncated: bool
    stale_pending_hidden_from_inbox_total: int
    pending_total_matches_queue: bool
    stale_total_matches_queue: bool

    def needs_attention(self) -> bool:
        return (
            not self.pending_total_matches_queue
            or not self.stale_total_matches_queue
            or self.stale_pending_hidden_from_inbox_total > 0
            or self.history_truncated
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["needs_attention"] = self.needs_attention()
        return payload


@dataclass(frozen=True, slots=True)
class PacketRuntimeApprovalFields:
    """Typed metadata carried by runtime commit-approval packets."""

    pipeline_generation: str = ""
    staged_snapshot_hash: str = ""
    guard_results_summary: str = ""

    @classmethod
    def from_values(
        cls,
        *,
        pipeline_generation: object = None,
        staged_snapshot_hash: object = None,
        guard_results_summary: object = None,
    ) -> "PacketRuntimeApprovalFields":
        normalized_generation = _clean_optional_text(pipeline_generation) or ""
        normalized_snapshot = _clean_optional_text(staged_snapshot_hash) or ""
        normalized_summary = _clean_optional_text(guard_results_summary) or ""
        return cls(
            pipeline_generation=normalized_generation,
            staged_snapshot_hash=normalized_snapshot,
            guard_results_summary=normalized_summary,
        )

    def to_event_fields(self) -> dict[str, object]:
        fields: dict[str, object] = {}
        fields["pipeline_generation"] = self.pipeline_generation or None
        fields["staged_snapshot_hash"] = self.staged_snapshot_hash or None
        fields["guard_results_summary"] = self.guard_results_summary or None
        return fields

    def has_values(self) -> bool:
        return (
            self.pipeline_generation != ""
            or self.staged_snapshot_hash != ""
            or self.guard_results_summary != ""
        )


@dataclass(frozen=True, slots=True)
class PacketGuardBundleEvidenceFields:
    """Typed guard-bundle evidence metadata carried by action requests."""

    full_guard_bundle_evidence: str = ""

    @classmethod
    def from_values(
        cls,
        *,
        full_guard_bundle_evidence: object = None,
    ) -> "PacketGuardBundleEvidenceFields":
        normalized_evidence = _clean_optional_text(full_guard_bundle_evidence) or ""
        return cls(full_guard_bundle_evidence=normalized_evidence)

    def to_event_fields(self) -> dict[str, object]:
        return {
            "full_guard_bundle_evidence": self.full_guard_bundle_evidence or None,
        }

    def has_values(self) -> bool:
        return self.full_guard_bundle_evidence != ""


def validate_full_guard_bundle_evidence(
    guard_bundle_evidence: PacketGuardBundleEvidenceFields,
    *,
    required: bool = False,
) -> None:
    value = guard_bundle_evidence.full_guard_bundle_evidence
    if not value:
        if required:
            raise ValueError(
                "Stage-commit action_request packets require "
                "--full-guard-bundle-evidence."
            )
        return
    if value not in FULL_GUARD_BUNDLE_EVIDENCE_VALUES:
        raise ValueError(
            "Unsupported --full-guard-bundle-evidence value: "
            f"{value}. Valid values: "
            + ", ".join(sorted(FULL_GUARD_BUNDLE_EVIDENCE_VALUES))
            + "."
        )


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
