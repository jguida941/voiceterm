"""Readable packet projections for operator-facing review-channel history."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
import re

from ..time_utils import parse_utc_timestamp, utc_timestamp
from .pending_packets import partition_live_packet_queue


HISTORY_OPERATIONAL_SUMMARY_SENTINEL = "__review_channel_operational_summary__"

_PIPELINE_ID_RE = re.compile(r"\b(pipeline-[A-Za-z0-9][A-Za-z0-9_.-]*)\b")
_DEFAULT_SAMPLE_LIMIT = 5
_PACKET_FRESHNESS_STALE_AFTER_SECONDS = 3600


def history_operational_summary_requested(args: object) -> bool:
    """Return whether history should render as an OperationalSummaryView."""
    return (
        str(getattr(args, "action", "") or "") == "history"
        and (
            bool(getattr(args, "grouped", False))
            or getattr(args, "summary", None) == HISTORY_OPERATIONAL_SUMMARY_SENTINEL
        )
    )


def build_operational_summary_view(
    review_state: Mapping[str, object],
    *,
    target: str | None = None,
    sample_limit: int | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, object]:
    """Group packet-rich review state into scan-friendly operational buckets."""
    rows = _packet_rows(review_state, target=target)
    live_rows, history_rows, stale_rows = partition_live_packet_queue(rows)
    stale_row_ids = {id(packet) for packet in stale_rows}
    limit = _sample_limit(sample_limit)
    generated_at = (
        _text(generated_at_utc)
        or _text(review_state.get("timestamp"))
        or utc_timestamp()
    )
    generated_dt = parse_utc_timestamp(generated_at)

    route_stage_counts: Counter[tuple[str, str]] = Counter()
    stage_counts: Counter[str] = Counter()
    pipeline_groups: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    active_claims: list[dict[str, object]] = []
    orphan_action_requests: list[dict[str, object]] = []
    stale_awaiting_reaper: list[dict[str, object]] = []

    for packet in rows:
        stage = _lifecycle_stage(packet, stale_row_ids=stale_row_ids)
        route = _route(packet)
        stage_counts[stage] += 1
        route_stage_counts[(route, stage)] += 1
        pipeline_id = _pipeline_id(packet)
        if pipeline_id:
            pipeline_groups[pipeline_id].append(packet)
        if _is_active_claim(packet, stage=stage, pipeline_id=pipeline_id):
            _append_sample(
                active_claims,
                packet,
                stage=stage,
                limit=limit,
                generated_dt=generated_dt,
            )
        if _is_orphan_action_request(packet, stage=stage, pipeline_id=pipeline_id):
            _append_sample(
                orphan_action_requests,
                packet,
                stage=stage,
                limit=limit,
                generated_dt=generated_dt,
            )
        if stage == "expired_without_disposition":
            _append_sample(
                stale_awaiting_reaper,
                packet,
                stage=stage,
                limit=limit,
                generated_dt=generated_dt,
            )

    pipeline_transit = _pipeline_summaries(
        pipeline_groups,
        stale_row_ids=stale_row_ids,
        limit=limit,
        generated_dt=generated_dt,
    )
    return {
        "contract_id": "OperationalSummaryView",
        "schema_version": 1,
        "generated_at_utc": generated_at,
        "source_review_state_timestamp": _text(review_state.get("timestamp")),
        "packet_freshness_stale_after_seconds": _PACKET_FRESHNESS_STALE_AFTER_SECONDS,
        "packet_total": len(rows),
        "live_pending_total": len(live_rows),
        "packet_history_total": len(history_rows),
        "stale_awaiting_reaper_total": len(stale_rows),
        "target_filter": str(target or "").strip(),
        "stage_counts": dict(sorted(stage_counts.items())),
        "pipeline_transit_total": len(pipeline_transit),
        "pipeline_transit_shown_total": min(len(pipeline_transit), limit),
        "pipeline_transit": pipeline_transit[:limit],
        "active_claims": active_claims,
        "orphan_action_requests": orphan_action_requests,
        "stale_awaiting_reaper": stale_awaiting_reaper,
        "routed_packet_buckets": _routed_packet_buckets(route_stage_counts),
    }


def render_operational_summary_view(view: Mapping[str, object]) -> list[str]:
    """Render an OperationalSummaryView as compact markdown sections."""
    lines = ["", "## Operational Summary View"]
    lines.append(f"- packet_total: {view.get('packet_total', 0)}")
    lines.append(f"- live_pending_total: {view.get('live_pending_total', 0)}")
    lines.append(f"- packet_history_total: {view.get('packet_history_total', 0)}")
    lines.append(
        f"- stale_awaiting_reaper_total: {view.get('stale_awaiting_reaper_total', 0)}"
    )
    if view.get("generated_at_utc"):
        lines.append(f"- generated_at_utc: {view.get('generated_at_utc')}")
    if view.get("source_review_state_timestamp"):
        lines.append(
            "- source_review_state_timestamp: "
            f"{view.get('source_review_state_timestamp')}"
        )
    if view.get("packet_freshness_stale_after_seconds") is not None:
        lines.append(
            "- packet_freshness_stale_after_seconds: "
            f"{view.get('packet_freshness_stale_after_seconds')}"
        )
    target_filter = str(view.get("target_filter") or "").strip()
    if target_filter:
        lines.append(f"- target_filter: {target_filter}")
    _append_stage_counts(lines, view.get("stage_counts"))
    _append_pipeline_transit(
        lines,
        view.get("pipeline_transit"),
        total=view.get("pipeline_transit_total"),
        shown=view.get("pipeline_transit_shown_total"),
    )
    _append_samples(lines, "Active Claims", view.get("active_claims"))
    _append_samples(lines, "Orphan Action Requests", view.get("orphan_action_requests"))
    _append_samples(lines, "Stale Awaiting Reaper", view.get("stale_awaiting_reaper"))
    _append_buckets(lines, view.get("routed_packet_buckets"))
    return lines


def _packet_rows(
    review_state: Mapping[str, object],
    *,
    target: str | None,
) -> list[Mapping[str, object]]:
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return []
    requested_target = str(target or "").strip()
    rows = [packet for packet in packets if isinstance(packet, Mapping)]
    if not requested_target:
        return rows
    return [
        packet
        for packet in rows
        if str(packet.get("to_agent") or "").strip() == requested_target
    ]


def _pipeline_summaries(
    pipeline_groups: Mapping[str, list[Mapping[str, object]]],
    *,
    stale_row_ids: set[int],
    limit: int,
    generated_dt,
) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for pipeline_id, packets in pipeline_groups.items():
        stage_counts: Counter[str] = Counter(
            _lifecycle_stage(packet, stale_row_ids=stale_row_ids)
            for packet in packets
        )
        kind_counts: Counter[str] = Counter(
            _text(packet.get("kind")) or "unknown"
            for packet in packets
        )
        action_counts: Counter[str] = Counter(
            _text(packet.get("requested_action")) or "unspecified"
            for packet in packets
        )
        latest = max(packets, key=_sort_key)
        latest_updated_at = _packet_updated_at(latest)
        guard_error_packets = [
            packet for packet in packets if _guard_error_detail(packet)
        ]
        latest_guard_error = _guard_error_detail(latest)
        summaries.append(
            {
                "pipeline_id": pipeline_id,
                "packet_total": len(packets),
                "guard_error_total": len(guard_error_packets),
                "route": _route(latest),
                "latest_packet_id": _text(latest.get("packet_id")),
                "latest_stage": _lifecycle_stage(
                    latest,
                    stale_row_ids=stale_row_ids,
                ),
                "latest_packet_updated_at_utc": latest_updated_at,
                "latest_packet_age_seconds": _age_seconds(
                    latest_updated_at,
                    generated_dt,
                ),
                "stage_counts": dict(sorted(stage_counts.items())),
                "kind_counts": dict(sorted(kind_counts.items())),
                "requested_action_counts": dict(sorted(action_counts.items())),
                "latest_guard_error_reason": _text(
                    latest_guard_error.get("reason")
                ),
                "latest_guard_error_source": _text(
                    latest_guard_error.get("failure_source")
                ),
                "packet_ids": [
                    _text(packet.get("packet_id"))
                    for packet in sorted(packets, key=_sort_key, reverse=True)[:limit]
                    if _text(packet.get("packet_id"))
                ],
                "summary": _truncate(_text(latest.get("summary")), 140),
            }
        )
    return sorted(
        summaries,
        key=_pipeline_summary_sort_key,
    )


def _routed_packet_buckets(
    route_stage_counts: Counter[tuple[str, str]],
) -> list[dict[str, object]]:
    return [
        {
            "route": route,
            "lifecycle_stage": stage,
            "packet_total": count,
        }
        for (route, stage), count in sorted(route_stage_counts.items())
    ]


def _lifecycle_stage(
    packet: Mapping[str, object],
    *,
    stale_row_ids: set[int],
) -> str:
    if id(packet) in stale_row_ids:
        return (
            "expired_with_disposition"
            if _disposition_sink(packet)
            else "expired_without_disposition"
        )
    lifecycle_state = _text(packet.get("lifecycle_current_state"))
    if lifecycle_state:
        return lifecycle_state
    disposition_sink = _disposition_sink(packet)
    if disposition_sink:
        return disposition_sink
    return _text(packet.get("status")) or "unknown"


def _is_active_claim(
    packet: Mapping[str, object],
    *,
    stage: str,
    pipeline_id: str,
) -> bool:
    if stage != "pending" or pipeline_id:
        return False
    kind = _text(packet.get("kind"))
    return kind in {
        "finding",
        "question",
        "instruction",
        "decision",
        "plan_gap_review",
        "plan_patch_review",
        "plan_ready_gate",
        "stop_anchor",
        "continuation_anchor",
        "goal_progress",
    }


def _is_orphan_action_request(
    packet: Mapping[str, object],
    *,
    stage: str,
    pipeline_id: str,
) -> bool:
    return (
        _text(packet.get("kind")) == "action_request"
        and not pipeline_id
        and stage in {"pending", "expired_without_disposition"}
    )


def _append_sample(
    samples: list[dict[str, object]],
    packet: Mapping[str, object],
    *,
    stage: str,
    limit: int,
    generated_dt,
) -> None:
    if len(samples) >= limit:
        return
    samples.append(_packet_sample(packet, stage=stage, generated_dt=generated_dt))


def _packet_sample(
    packet: Mapping[str, object],
    *,
    stage: str,
    generated_dt,
) -> dict[str, object]:
    updated_at = _packet_updated_at(packet)
    guard_error = _guard_error_detail(packet)
    return {
        "packet_id": _text(packet.get("packet_id")),
        "route": _route(packet),
        "kind": _text(packet.get("kind")) or "unknown",
        "lifecycle_stage": stage,
        "packet_updated_at_utc": updated_at,
        "packet_age_seconds": _age_seconds(updated_at, generated_dt),
        "packet_freshness_status": _packet_freshness_status(
            _age_seconds(updated_at, generated_dt)
        ),
        "requested_action": _text(packet.get("requested_action")),
        "target": _target(packet),
        "summary": _truncate(_text(packet.get("summary")), 160),
        "guard_error_reason": _text(guard_error.get("reason")),
        "guard_error_source": _text(guard_error.get("failure_source")),
        "guard_error_evidence": _text(guard_error.get("full_guard_bundle_evidence")),
    }


def _pipeline_id(packet: Mapping[str, object]) -> str:
    for field_name in (
        "target_ref",
        "pipeline_generation",
        "correlation_id",
        "run_id",
    ):
        value = _text(packet.get(field_name))
        match = _PIPELINE_ID_RE.search(value)
        if match:
            return match.group(1)
    return ""


def _route(packet: Mapping[str, object]) -> str:
    from_agent = _text(packet.get("from_agent")) or "unknown"
    to_agent = _text(packet.get("to_agent")) or "unknown"
    return f"{from_agent}->{to_agent}"


def _target(packet: Mapping[str, object]) -> str:
    target_kind = _text(packet.get("target_kind"))
    target_ref = _text(packet.get("target_ref"))
    if target_kind and target_ref:
        return f"{target_kind}:{target_ref}"
    return target_ref or target_kind


def _disposition_sink(packet: Mapping[str, object]) -> str:
    disposition = packet.get("disposition")
    if not isinstance(disposition, Mapping):
        return ""
    return _text(disposition.get("sink"))


def _sort_key(packet: Mapping[str, object]) -> tuple[str, str, str]:
    return (
        _text(packet.get("_sort_timestamp"))
        or _text(packet.get("posted_at"))
        or _text(packet.get("latest_event_id")),
        _text(packet.get("latest_event_id")),
        _text(packet.get("packet_id")),
    )


def _sample_limit(value: int | None) -> int:
    if value is None or value < 0:
        return _DEFAULT_SAMPLE_LIMIT
    return max(1, min(value, 25))


def _append_stage_counts(lines: list[str], counts: object) -> None:
    if not isinstance(counts, Mapping) or not counts:
        return
    rendered = ", ".join(f"{key}={value}" for key, value in counts.items())
    lines.append(f"- lifecycle_stages: {rendered}")


def _pipeline_summary_sort_key(item: Mapping[str, object]) -> tuple[int, str, str]:
    stage_counts = item.get("stage_counts")
    active_rank = 1
    if isinstance(stage_counts, Mapping) and any(
        str(stage) in {"pending", "in_progress", "expired_without_disposition"}
        and int(count or 0) > 0
        for stage, count in stage_counts.items()
    ):
        active_rank = 0
    return (
        active_rank,
        str(item.get("latest_stage") or ""),
        str(item.get("pipeline_id") or ""),
    )


def _append_pipeline_transit(
    lines: list[str],
    groups: object,
    *,
    total: object,
    shown: object,
) -> None:
    if not isinstance(groups, list) or not groups:
        return
    lines.append("")
    lines.append("### Pipeline Transit")
    if _as_int(total) > _as_int(shown):
        lines.append(f"- showing {shown} of {total} pipeline groups")
    for group in groups:
        if not isinstance(group, Mapping):
            continue
        stages = _format_counts(group.get("stage_counts"))
        kinds = _format_counts(group.get("kind_counts"))
        actions = _format_counts(group.get("requested_action_counts"))
        packet_ids = ", ".join(
            str(packet_id)
            for packet_id in group.get("packet_ids", [])
            if str(packet_id)
        )
        line = (
            f"- {group.get('pipeline_id')}: packets={group.get('packet_total', 0)}"
            f" | route={group.get('route')}"
            f" | stages={stages or 'n/a'}"
            f" | kinds={kinds or 'n/a'}"
            f" | actions={actions or 'n/a'}"
        )
        if packet_ids:
            line += f" | recent={packet_ids}"
        latest_age = group.get("latest_packet_age_seconds")
        if latest_age is not None:
            line += f" | latest_age_seconds={latest_age}"
        guard_error_total = _as_int(group.get("guard_error_total"))
        if guard_error_total:
            line += f" | guard_errors={guard_error_total}"
        guard_reason = _text(group.get("latest_guard_error_reason"))
        if guard_reason:
            line += f" | latest_guard_error={guard_reason}"
        summary = _text(group.get("summary"))
        if summary:
            line += f" | {summary}"
        lines.append(line)


def _append_samples(lines: list[str], heading: str, samples: object) -> None:
    if not isinstance(samples, list) or not samples:
        return
    lines.append("")
    lines.append(f"### {heading}")
    for sample in samples:
        if not isinstance(sample, Mapping):
            continue
        line = (
            f"- {sample.get('packet_id')}: {sample.get('lifecycle_stage')}"
            f" | {sample.get('route')}"
            f" | {sample.get('kind')}"
        )
        requested_action = _text(sample.get("requested_action"))
        if requested_action:
            line += f" | action={requested_action}"
        target = _text(sample.get("target"))
        if target:
            line += f" | target={target}"
        updated_at = _text(sample.get("packet_updated_at_utc"))
        if updated_at:
            line += f" | updated={updated_at}"
        if sample.get("packet_age_seconds") is not None:
            line += f" | age_seconds={sample.get('packet_age_seconds')}"
        freshness = _text(sample.get("packet_freshness_status"))
        if freshness:
            line += f" | freshness={freshness}"
        guard_reason = _text(sample.get("guard_error_reason"))
        if guard_reason:
            line += f" | guard_error={guard_reason}"
        guard_evidence = _text(sample.get("guard_error_evidence"))
        if guard_evidence:
            line += f" | guard_evidence={guard_evidence}"
        summary = _text(sample.get("summary"))
        if summary:
            line += f" | {summary}"
        lines.append(line)


def _append_buckets(lines: list[str], buckets: object) -> None:
    if not isinstance(buckets, list) or not buckets:
        return
    lines.append("")
    lines.append("### Routed Packet Buckets")
    for bucket in buckets[:20]:
        if not isinstance(bucket, Mapping):
            continue
        lines.append(
            f"- {bucket.get('route')} | {bucket.get('lifecycle_stage')}: "
            f"{bucket.get('packet_total', 0)}"
        )


def _format_counts(counts: object) -> str:
    if not isinstance(counts, Mapping):
        return ""
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def _as_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _packet_updated_at(packet: Mapping[str, object]) -> str:
    return (
        _text(packet.get("latest_event_at_utc"))
        or _text(packet.get("_sort_timestamp"))
        or _text(packet.get("posted_at"))
        or _text(packet.get("timestamp_utc"))
        or _text(packet.get("created_at_utc"))
    )


def _age_seconds(value: object, generated_dt) -> int | None:
    if generated_dt is None:
        return None
    parsed = parse_utc_timestamp(value)
    if parsed is None:
        return None
    return max(0, int((generated_dt - parsed).total_seconds()))


def _packet_freshness_status(age_seconds: int | None) -> str:
    if age_seconds is None:
        return "unknown"
    if age_seconds > _PACKET_FRESHNESS_STALE_AFTER_SECONDS:
        return "stale"
    return "fresh"


def _guard_error_detail(packet: Mapping[str, object]) -> dict[str, object]:
    disposition = packet.get("disposition")
    if isinstance(disposition, Mapping):
        detail = disposition.get("guard_error_detail")
        if isinstance(detail, Mapping):
            return dict(detail)
    events = packet.get("acted_on_events")
    if isinstance(events, list):
        for event in reversed(events):
            if not isinstance(event, Mapping):
                continue
            detail = event.get("guard_error_detail")
            if isinstance(detail, Mapping):
                return dict(detail)
    return {}


def _text(value: object) -> str:
    return str(value or "").strip()
