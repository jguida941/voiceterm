"""Master-plan row binding for review packets."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from pathlib import Path
import re

from ..governance.draft import scan_repo_governance
from ..runtime.master_plan_contract import IngestionProvenance, PlanRow, SDLCStage
from ..runtime.master_plan_store import upsert_plan_row_jsonl
from ..runtime.plan_ref import canonical_plan_ref
from .event_store import DEFAULT_REVIEW_CHANNEL_PLAN_ID, ReviewChannelArtifactPaths
from .packet_creation_binding_contracts import (
    PACKET_CREATION_BINDING_SECTION,
    binding_result,
)


def bind_packet_to_plan_row(
    *,
    repo_root: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    packet_event: Mapping[str, object],
) -> dict[str, object]:
    """Bind a packet to the configured typed master-plan store."""
    master_plan = _resolve_master_plan(repo_root)
    packet_id = _text(packet_event.get("packet_id"))
    target_ref = _target_ref(packet_event)
    if master_plan is None:
        return binding_result(
            "failed",
            "master_plan_authority_unresolved",
            packet_id=packet_id,
            binding_target_kind="plan_row",
            target_ref=target_ref,
        )

    typed_store_path = repo_root / master_plan.typed_store_path
    row = _typed_plan_row(
        repo_root=repo_root,
        packet_event=packet_event,
        artifact_paths=artifact_paths,
        target_ref=target_ref,
    )
    try:
        store_status, _stored = upsert_plan_row_jsonl(typed_store_path, row)
    except (OSError, ValueError) as exc:
        return binding_result(
            "failed",
            f"master_plan_store_write_failed:{exc.__class__.__name__}",
            packet_id=packet_id,
            binding_target_kind="plan_row",
            binding_target=row.row_id,
            target_ref=target_ref,
            path=str(typed_store_path),
        )

    projection = _append_projection_row(
        repo_root=repo_root,
        master_plan_path=repo_root
        / (master_plan.projection_path or master_plan.source_path),
        typed_store_path=typed_store_path,
        row=row,
        packet_event=packet_event,
        target_ref=target_ref,
    )
    return binding_result(
        store_status,
        "packet_bound_to_plan_row_at_creation",
        packet_id=packet_id,
        binding_target_kind="plan_row",
        binding_target=row.row_id,
        target_ref=target_ref,
        path=str(typed_store_path),
        projection_path=projection,
    )


def _resolve_master_plan(repo_root: Path):
    try:
        master_plan = scan_repo_governance(repo_root).master_plan
    except (ImportError, OSError, RuntimeError, ValueError):
        return None
    projection_path = _text(master_plan.projection_path or master_plan.source_path)
    typed_store_path = _text(master_plan.typed_store_path)
    if not projection_path or not typed_store_path:
        return None
    if not (repo_root / projection_path).is_file():
        return None
    return master_plan


def _typed_plan_row(
    *,
    repo_root: Path,
    packet_event: Mapping[str, object],
    artifact_paths: ReviewChannelArtifactPaths,
    target_ref: str,
) -> PlanRow:
    packet_id = _text(packet_event.get("packet_id"))
    source_hash = _content_hash(packet_event)
    source_doc_path = _repo_relative(
        Path(artifact_paths.event_log_path),
        repo_root=repo_root,
    )
    return PlanRow(
        row_id=f"PKT-BIND-{_task_slug(packet_id)}",
        title=_row_title(packet_event),
        status="queued",
        sdlc_stage=SDLCStage.SPEC,
        sourced_from_packets=(packet_id,),
        work_evidence_ids=(
            f"packet:{packet_id}",
            f"event:{_text(packet_event.get('event_id'))}",
        ),
        source_doc_path=source_doc_path,
        source_line=0,
        content_hash=source_hash,
        provenance=IngestionProvenance(
            source_file=source_doc_path,
            source_line=0,
            source_kind="PacketCreationBinding",
            source_hash=source_hash,
            observed_at_utc=_text(packet_event.get("timestamp_utc")),
            section_authority="packet_posted",
        ),
        anchor_refs=tuple(
            _dedupe([*_rows(packet_event.get("anchor_refs")), f"packet:{packet_id}"])
        ),
        target_ref=target_ref,
        mutation_op=_text(packet_event.get("mutation_op"))
        or _text(packet_event.get("requested_action")),
    )


def _append_projection_row(
    *,
    repo_root: Path,
    master_plan_path: Path,
    typed_store_path: Path,
    row: PlanRow,
    packet_event: Mapping[str, object],
    target_ref: str,
) -> str:
    rel_projection = _repo_relative(master_plan_path, repo_root=repo_root)
    if not master_plan_path.is_file():
        return ""
    try:
        existing = master_plan_path.read_text(encoding="utf-8")
    except OSError:
        return rel_projection
    marker = f"source `{_text(packet_event.get('packet_id'))}`"
    if marker in existing:
        return rel_projection
    next_text = _projection_text(
        existing=existing,
        row=_projection_markdown_row(row=row, packet_event=packet_event, target_ref=target_ref),
        typed_store_path=typed_store_path,
        repo_root=repo_root,
    )
    try:
        master_plan_path.write_text(next_text, encoding="utf-8")
    except OSError:
        return rel_projection
    return rel_projection


def _projection_text(
    *,
    existing: str,
    row: str,
    typed_store_path: Path,
    repo_root: Path,
) -> str:
    if PACKET_CREATION_BINDING_SECTION in existing:
        return f"{existing.rstrip()}\n{row}\n"
    store_ref = _repo_relative(typed_store_path, repo_root=repo_root)
    return (
        f"{existing.rstrip()}\n\n"
        f"{PACKET_CREATION_BINDING_SECTION}\n\n"
        "This generated ledger projects packet creation bindings for humans. "
        f"The typed row authority is `{store_ref}`; packets remain communication "
        f"and provenance after durable ownership lands.\n\n{row}\n"
    )


def _projection_markdown_row(
    *,
    row: PlanRow,
    packet_event: Mapping[str, object],
    target_ref: str,
) -> str:
    packet_id = _text(packet_event.get("packet_id"))
    posted_at = _text(packet_event.get("timestamp_utc")) or "unknown"
    return (
        f"- [ ] `{row.row_id}` {row.title} "
        f"(source `{packet_id}`; target `{target_ref}`; "
        f"posted `{posted_at}`; binding `plan_row`)."
    )


def _target_ref(packet_event: Mapping[str, object]) -> str:
    raw = (
        _text(packet_event.get("target_ref"))
        or _text(packet_event.get("plan_id"))
        or DEFAULT_REVIEW_CHANNEL_PLAN_ID
    )
    return canonical_plan_ref(raw) or raw


def _row_title(packet_event: Mapping[str, object]) -> str:
    kind = _text(packet_event.get("kind")) or "packet"
    summary = _single_line(_text(packet_event.get("summary"))) or "Untitled packet"
    title = f"{_row_title_prefix(kind)}: {summary}"
    return title if len(title) <= 240 else f"{title[:237]}..."


def _row_title_prefix(kind: str) -> str:
    if kind == "finding":
        return "Packet finding"
    if kind == "plan_gap_review":
        return "Packet plan gap"
    if kind == "plan_patch_review":
        return "Packet plan patch"
    if kind == "action_request":
        return "Packet action request"
    if kind == "decision":
        return "Packet decision"
    if kind == "draft":
        return "Packet draft"
    return "Packet work"


def _content_hash(packet_event: Mapping[str, object]) -> str:
    text = "\n".join(
        [
            _text(packet_event.get("packet_id")),
            _text(packet_event.get("kind")),
            _text(packet_event.get("summary")),
            _text(packet_event.get("body")),
            _text(packet_event.get("target_ref")),
            _text(packet_event.get("plan_id")),
        ]
    )
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rows(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dedupe(values: list[str]) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return tuple(seen)


def _task_slug(packet_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", packet_id).strip("-").upper()
    return slug or "UNKNOWN"


def _single_line(value: str) -> str:
    return " ".join(value.split())


def _repo_relative(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["bind_packet_to_plan_row"]
