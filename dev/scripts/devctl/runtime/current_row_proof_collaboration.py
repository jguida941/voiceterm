"""Typed collaboration evidence for current-row proof mode."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from .current_row_proof_config import (
    COLLABORATION_DIRECTIONS,
    EVENT_RE,
    NON_SEND_PACKET_EVENTS,
    PACKET_RE,
)
from .current_row_proof_utils import ProofUtils as U


class CollaborationProof:
    """Build collaboration proof state from packet/event evidence."""

    @staticmethod
    def status(
        paths: Sequence[Path],
        *,
        row_id: str,
        plan_rows: Sequence[Mapping[str, object]],
        not_before_timestamp: str = "",
    ) -> dict[str, object]:
        plan_packet_refs = set(CollaborationProof.plan_packet_refs(plan_rows, row_id))
        active_packet_refs: set[str] = set()
        typed_evidence: list[str] = []
        loose_chat_count = 0
        actor_role_session_state: list[dict[str, str]] = []
        direction_packet_refs: dict[str, list[str]] = {
            direction: [] for direction in COLLABORATION_DIRECTIONS
        }
        direction_actor_state: dict[str, list[dict[str, str]]] = {
            direction: [] for direction in COLLABORATION_DIRECTIONS
        }
        latest_timestamp = ""
        for payload in U.iter_jsonish_many(paths):
            payload_text = json.dumps(payload, sort_keys=True, default=str)
            packet_ids = PACKET_RE.findall(payload_text)
            direct_packet_id = CollaborationProof.packet_id_from_payload(payload, packet_ids)
            plan_packet_matches = plan_packet_refs.intersection(packet_ids)
            if row_id not in payload_text and not plan_packet_matches:
                continue
            timestamp = CollaborationProof.payload_timestamp(payload)
            if not_before_timestamp and timestamp and timestamp < not_before_timestamp:
                continue
            if timestamp and timestamp > latest_timestamp:
                latest_timestamp = timestamp
            event_ids = EVENT_RE.findall(payload_text)
            if direct_packet_id:
                active_packet_refs.add(direct_packet_id)
            else:
                active_packet_refs.update(plan_packet_matches)
            if str(payload.get("source_kind") or "").lower() in {"chat", "loose_chat"}:
                loose_chat_count += 1
                continue
            if packet_ids or event_ids or str(payload.get("contract_id") or "").startswith("Review"):
                proof = packet_ids[0] if packet_ids else event_ids[0] if event_ids else str(payload.get("contract_id"))
                typed_evidence.append(proof)
                state = CollaborationProof.actor_role_session_state(payload)
                if state:
                    actor_role_session_state.append(state)
            direction = CollaborationProof.packet_direction(payload)
            if direction in direction_packet_refs and direct_packet_id and CollaborationProof.is_typed_packet_send(payload):
                CollaborationProof.append_unique(direction_packet_refs[direction], direct_packet_id)
                state = CollaborationProof.actor_role_session_state(payload)
                if state:
                    direction_actor_state[direction].append(state)
        missing_directions = [
            direction for direction in COLLABORATION_DIRECTIONS if not direction_packet_refs[direction]
        ]
        missing_actor_role_session_directions = [
            direction for direction in COLLABORATION_DIRECTIONS if not direction_actor_state[direction]
        ]
        status = CollaborationProof.collaboration_status_name(
            direction_packet_refs,
            missing_directions=missing_directions,
            missing_actor_role_session_directions=missing_actor_role_session_directions,
            loose_chat_count=loose_chat_count,
        )
        return {
            "status": status,
            "proof_ref": CollaborationProof.proof_ref(status, direction_packet_refs, typed_evidence),
            "typed_collaboration_evidence_count": len(typed_evidence),
            "loose_chat_collaboration_count": loose_chat_count,
            "bidirectional_packet_exchange": status == "passed",
            "codex_to_claude_packet_refs": list(direction_packet_refs["codex_to_claude"]),
            "claude_to_codex_packet_refs": list(direction_packet_refs["claude_to_codex"]),
            "missing_packet_directions": missing_directions,
            "missing_actor_role_session_directions": missing_actor_role_session_directions,
            "active_packet_refs": sorted(active_packet_refs),
            "actor_role_session_state": actor_role_session_state,
            "timestamp": latest_timestamp,
        }

    @staticmethod
    def collaboration_status_name(
        direction_packet_refs: Mapping[str, Sequence[str]],
        *,
        missing_directions: Sequence[str],
        missing_actor_role_session_directions: Sequence[str],
        loose_chat_count: int,
    ) -> str:
        if not missing_directions and not missing_actor_role_session_directions:
            return "passed"
        if direction_packet_refs["codex_to_claude"] or direction_packet_refs["claude_to_codex"]:
            return "progress"
        return "failed" if loose_chat_count else "missing"

    @staticmethod
    def proof_ref(
        status: str,
        direction_packet_refs: Mapping[str, Sequence[str]],
        typed_evidence: Sequence[str],
    ) -> str:
        if status == "passed":
            return "+".join(
                f"packet:{direction_packet_refs[direction][0]}" for direction in COLLABORATION_DIRECTIONS
            )
        if direction_packet_refs["codex_to_claude"]:
            return f"packet:{direction_packet_refs['codex_to_claude'][0]}"
        if direction_packet_refs["claude_to_codex"]:
            return f"packet:{direction_packet_refs['claude_to_codex'][0]}"
        return typed_evidence[0] if typed_evidence else ""

    @staticmethod
    def plan_packet_refs(plan_rows: Sequence[Mapping[str, object]], row_id: str) -> Iterable[str]:
        for row in plan_rows:
            row_text = json.dumps(row, sort_keys=True, default=str)
            if row.get("row_id") != row_id and row.get("target_ref") != f"plan:{row_id}" and row_id not in row_text:
                continue
            yield from PACKET_RE.findall(row_text)

    @staticmethod
    def actor_role_session_state(payload: Mapping[str, object]) -> dict[str, str]:
        actor = U.first_text(payload, ("actor", "actor_id", "provider", "target_actor"))
        role = U.first_text(payload, ("role", "role_id", "actor_role", "target_role"))
        session = U.first_text(payload, ("session", "session_id", "target_session_id"))
        if not (actor and role and session):
            nested = tuple(U.nested_mappings(payload))
            actor = actor or U.first_nested_text(nested, ("actor", "actor_id", "provider", "target_actor"))
            role = role or U.first_nested_text(nested, ("role", "role_id", "actor_role", "target_role"))
            session = session or U.first_nested_text(nested, ("session", "session_id", "target_session_id"))
        if actor and role and session:
            return {"actor": actor, "role": role, "session": session}
        return {}

    @staticmethod
    def packet_id_from_payload(payload: Mapping[str, object], packet_ids: Sequence[str]) -> str:
        direct_packet_id = str(payload.get("packet_id") or "").strip()
        return direct_packet_id or (packet_ids[0] if packet_ids else "")

    @staticmethod
    def packet_direction(payload: Mapping[str, object]) -> str:
        from_agent = str(payload.get("from_agent") or "").strip().lower()
        to_agent = str(payload.get("to_agent") or "").strip().lower()
        if from_agent == "codex" and to_agent == "claude":
            return "codex_to_claude"
        if from_agent == "claude" and to_agent == "codex":
            return "claude_to_codex"
        return ""

    @staticmethod
    def is_typed_packet_send(payload: Mapping[str, object]) -> bool:
        if str(payload.get("source_kind") or "").strip().lower() in {"chat", "loose_chat"}:
            return False
        event_type = str(payload.get("event_type") or "").strip()
        if event_type in NON_SEND_PACKET_EVENTS:
            return False
        if event_type and event_type != "packet_posted":
            return False
        return bool(str(payload.get("packet_id") or "").strip())

    @staticmethod
    def payload_timestamp(payload: Mapping[str, object]) -> str:
        for key in ("timestamp_utc", "timestamp", "posted_at", "recorded_at_utc", "captured_at_utc"):
            value = str(payload.get(key) or "").strip()
            if value:
                return value
        return ""

    @staticmethod
    def append_unique(values: list[str], value: str) -> None:
        if value not in values:
            values.append(value)
