"""Collaboration helpers for operator-console context-pack attachments."""

from __future__ import annotations

from ..state.core.models import ContextPackRef


def parse_context_pack_refs(payload: object) -> tuple[ContextPackRef, ...]:
    """Parse structured context-pack refs from a JSON-like payload."""
    if not isinstance(payload, list):
        return ()
    refs: list[ContextPackRef] = []
    for item in payload:
        parsed = _parse_context_pack_ref(item)
        if parsed is not None and parsed not in refs:
            refs.append(parsed)
    return tuple(refs)


def context_pack_refs_payload(
    context_pack_refs: tuple[ContextPackRef, ...],
) -> list[dict[str, str]]:
    """Render typed context-pack refs back to JSON-safe objects."""
    payload: list[dict[str, str]] = []
    for ref in context_pack_refs:
        row = {
            "pack_kind": ref.pack_kind,
            "pack_ref": ref.pack_ref,
        }
        if ref.adapter_profile:
            row["adapter_profile"] = ref.adapter_profile
        if ref.generated_at_utc:
            row["generated_at_utc"] = ref.generated_at_utc
        payload.append(row)
    return payload


def context_pack_ref_lines(
    context_pack_refs: tuple[ContextPackRef, ...],
) -> tuple[str, ...]:
    """Format typed context-pack refs for compact UI display."""
    return tuple(ref.summary_line() for ref in context_pack_refs)


def _parse_context_pack_ref(payload: object) -> ContextPackRef | None:
    if not isinstance(payload, dict):
        return None
    pack_kind = _normalize_pack_kind(str(payload.get("pack_kind") or "").strip())
    pack_ref = str(payload.get("pack_ref") or "").strip()
    if not pack_kind or not pack_ref:
        return None
    return ContextPackRef(
        pack_kind=pack_kind,
        pack_ref=pack_ref,
        adapter_profile=str(payload.get("adapter_profile") or "").strip(),
        generated_at_utc=str(
            payload.get("generated_at_utc") or payload.get("generated_at") or ""
        ).strip(),
    )


def _normalize_pack_kind(pack_kind: str) -> str:
    if pack_kind == "session_handoff":
        return "handoff_pack"
    return pack_kind
