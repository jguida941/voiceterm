"""Plan-row integration for applied review packets."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from pathlib import Path
import re

from ..governance.draft import scan_repo_governance
from ..runtime.master_plan_contract import (
    IngestionProvenance,
    MasterPlan,
    PlanRow,
    SDLCStage,
    hydrate_plan_row_commit_anchor_ref,
)
from ..runtime.master_plan_store import upsert_plan_row_jsonl
from ..runtime.plan_ref import canonical_plan_ref

PLAN_INTEGRATION_SECTION = "## Generated Review Packet Plan Integrations"
PLAN_INTEGRATION_CONTRACT_ID = "PacketPlanIntegration"


def maybe_append_packet_plan_row(
    *,
    repo_root: Path,
    packet: Mapping[str, object],
    event: Mapping[str, object],
) -> dict[str, object]:
    """Append one idempotent MASTER_PLAN row for a plan-targeted apply event."""
    if _text(event.get("event_type")) != "packet_applied":
        return _result("skipped", "not_packet_applied")
    if _text(packet.get("target_kind")) != "plan":
        return _result("skipped", "target_kind_not_plan")

    packet_id = _text(packet.get("packet_id"))
    target_ref = _canonical_target_ref(packet.get("target_ref"))
    if not packet_id or not target_ref:
        return _result("skipped", "missing_packet_or_target")

    master_plan = _resolve_master_plan(repo_root)
    if master_plan is None:
        return _result(
            "failed",
            "master_plan_authority_unresolved",
            packet_id=packet_id,
            target_ref=target_ref,
        )
    typed_store_path = repo_root / master_plan.typed_store_path
    row = _typed_plan_row(packet=packet, event=event, master_plan=master_plan)
    try:
        store_status, _stored = upsert_plan_row_jsonl(typed_store_path, row)
    except (OSError, ValueError) as exc:
        return _result(
            "failed",
            f"master_plan_store_write_failed:{exc.__class__.__name__}",
            packet_id=packet_id,
            target_ref=target_ref,
            path=str(typed_store_path),
        )
    if store_status == "already_present":
        return _result(
            "already_present",
            "packet_row_exists",
            packet_id=packet_id,
            target_ref=target_ref,
            path=str(typed_store_path),
        )

    master_plan_path = repo_root / (
        master_plan.projection_path or master_plan.source_path
    )
    if not master_plan_path.is_file():
        return _result(
            store_status,
            "typed_row_written_projection_missing",
            packet_id=packet_id,
            target_ref=target_ref,
            path=str(typed_store_path),
            projection_path=str(master_plan_path),
        )

    try:
        existing = master_plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        return _result(
            store_status,
            f"master_plan_read_failed:{exc.__class__.__name__}",
            packet_id=packet_id,
            path=str(typed_store_path),
            projection_path=str(master_plan_path),
        )
    marker = f"source `{packet_id}`"
    if marker in existing:
        return _result(
            store_status,
            "typed_row_written_projection_already_present",
            packet_id=packet_id,
            target_ref=target_ref,
            path=str(typed_store_path),
            projection_path=str(master_plan_path),
        )

    markdown_row = _plan_row(packet=packet, event=event)
    if PLAN_INTEGRATION_SECTION in existing:
        next_text = f"{existing.rstrip()}\n{markdown_row}\n"
    else:
        next_text = (
            f"{existing.rstrip()}\n\n"
            f"{PLAN_INTEGRATION_SECTION}\n\n"
            "This generated ledger projects typed JSONL review-packet plan "
            "integrations for humans. The row authority is "
            f"`{master_plan.typed_store_path}`; keep durable architecture "
            "rules in the owning active plan, not packet history alone.\n\n"
            f"{markdown_row}\n"
        )

    try:
        master_plan_path.write_text(next_text, encoding="utf-8")
    except OSError as exc:
        return _result(
            store_status,
            f"master_plan_write_failed:{exc.__class__.__name__}",
            packet_id=packet_id,
            path=str(typed_store_path),
            projection_path=str(master_plan_path),
        )
    return _result(
        store_status,
        "plan_target_packet_applied",
        packet_id=packet_id,
        target_ref=target_ref,
        path=str(typed_store_path),
        projection_path=str(master_plan_path),
    )


def _resolve_master_plan(repo_root: Path) -> MasterPlan | None:
    try:
        master_plan = scan_repo_governance(repo_root).master_plan
    except (ImportError, OSError, RuntimeError, ValueError):
        return None
    if not _master_plan_authority_available(repo_root, master_plan):
        return None
    return master_plan


def _master_plan_authority_available(
    repo_root: Path,
    master_plan: MasterPlan,
) -> bool:
    typed_store_path = str(master_plan.typed_store_path or "").strip()
    projection_path = str(
        master_plan.projection_path or master_plan.source_path or ""
    ).strip()
    if not typed_store_path or not projection_path:
        return False
    return (repo_root / projection_path).is_file()


def _typed_plan_row(
    *,
    packet: Mapping[str, object],
    event: Mapping[str, object],
    master_plan: MasterPlan,
) -> PlanRow:
    packet_id = _text(packet.get("packet_id"))
    summary = _single_line(_text(packet.get("summary"))) or "Review packet plan row"
    target_ref = _canonical_target_ref(packet.get("target_ref"))
    target_revision = _text(packet.get("target_revision"))
    event_id = _text(event.get("event_id"))
    attestation = _guard_attestation(event)
    evidence_id = _text(attestation.get("attestation_id")) or (
        f"packet_attestation:{event_id}" if event_id else ""
    )
    source_hash = _content_hash(packet)
    return hydrate_plan_row_commit_anchor_ref(
        PlanRow(
            row_id=f"PKT-{_task_slug(packet_id)}",
            title=summary,
            status="open",
            sdlc_stage=SDLCStage.SPEC,
            sourced_from_packets=(packet_id,),
            work_evidence_ids=(evidence_id,) if evidence_id else (),
            plan_revision_at_write=master_plan.plan_revision or target_revision,
            source_doc_path=master_plan.source_path or master_plan.projection_path,
            source_line=0,
            content_hash=source_hash,
            provenance=IngestionProvenance(
                source_file=master_plan.source_path or master_plan.projection_path,
                source_line=0,
                source_kind="PacketPlanIntegration",
                source_hash=source_hash,
                observed_at_utc=_text(event.get("timestamp_utc")),
                section_authority="packet_applied",
            ),
            target_ref=target_ref,
            mutation_op=_text(packet.get("mutation_op"))
            or _text(packet.get("requested_action")),
            anchor_refs=tuple(_string_rows(packet.get("anchor_refs"))),
        )
    )


def _plan_row(
    *,
    packet: Mapping[str, object],
    event: Mapping[str, object],
) -> str:
    packet_id = _text(packet.get("packet_id"))
    summary = _single_line(_text(packet.get("summary"))) or "Review packet plan row"
    target_ref = _canonical_target_ref(packet.get("target_ref"))
    target_revision = _text(packet.get("target_revision"))
    actor = _actor(event) or "system"
    applied_at = _text(event.get("timestamp_utc")) or "unknown"
    task_id = f"PKT-{_task_slug(packet_id)}"
    revision_suffix = f" @ `{target_revision}`" if target_revision else ""
    return (
        f"- [ ] `{task_id}` {summary} "
        f"(source `{packet_id}`; target `{target_ref}`{revision_suffix}; "
        f"applied `{applied_at}` by `{actor}`)."
    )


def _task_slug(packet_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", packet_id).strip("-").upper()
    return slug or "UNKNOWN"


def _actor(event: Mapping[str, object]) -> str:
    metadata = event.get("metadata")
    if not isinstance(metadata, Mapping):
        return ""
    return _text(metadata.get("actor"))


def _guard_attestation(event: Mapping[str, object]) -> dict[str, object]:
    metadata = event.get("metadata")
    if not isinstance(metadata, Mapping):
        return {}
    attestation = metadata.get("guard_attestation")
    if not isinstance(attestation, Mapping):
        return {}
    return dict(attestation)


def _string_rows(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _content_hash(packet: Mapping[str, object]) -> str:
    text = "\n".join(
        [
            _text(packet.get("packet_id")),
            _text(packet.get("summary")),
            _text(packet.get("body")),
            _text(packet.get("target_ref")),
        ]
    )
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _single_line(value: str) -> str:
    return " ".join(value.split())


def _result(
    status: str,
    reason: str,
    **extra: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_id": PLAN_INTEGRATION_CONTRACT_ID,
        "status": status,
        "reason": reason,
    }
    payload.update(extra)
    return payload


def _canonical_target_ref(value: object) -> str:
    return canonical_plan_ref(value) or _text(value)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "PLAN_INTEGRATION_CONTRACT_ID",
    "PLAN_INTEGRATION_SECTION",
    "maybe_append_packet_plan_row",
]
