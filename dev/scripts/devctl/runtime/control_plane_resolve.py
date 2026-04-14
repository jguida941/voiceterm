"""Gate-resolution helpers for the ControlPlaneReadModel.

Each ``_resolve_*`` function takes pre-loaded source dicts and returns
a derived state dict. No filesystem IO happens here -- all reading is
done by the caller in ``control_plane_read_model.py``.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from typing import Any

from .control_plane_daemons import resolve_daemon_state
from .control_plane_sources import artifact_paths, load_sources, read_json_artifact
from .startup_blocker_decision import BlockerSnapshot, derive_blocker_decision
from .value_coercion import coerce_bool, coerce_string


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_git_state(repo_root: Path) -> dict[str, Any]:
    """Load branch, HEAD, dirty state, and ahead count from git."""
    result: dict[str, Any] = {
        "branch": "unknown", "head": "unknown", "clean": True, "ahead": 0,
    }
    try:
        sb = subprocess.run(
            ["git", "status", "-sb", "--porcelain"],
            capture_output=True, text=True, timeout=5, cwd=str(repo_root),
            check=False,
        )
        lines = sb.stdout.strip().splitlines()
        if lines:
            header = lines[0].lstrip("# ").strip()
            result["branch"] = header.split("...")[0] if "..." in header else header
            result["clean"] = len(lines) <= 1
            bracket = re.search(r"\[(.+?)\]", header)
            if bracket:
                am = re.search(r"ahead\s+(\d+)", bracket.group(1))
                result["ahead"] = int(am.group(1)) if am else 0
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, timeout=5, cwd=str(repo_root),
            check=False,
        )
        sha_line = log.stdout.strip()
        if sha_line:
            result["head"] = sha_line.split(None, 1)[0]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return result


# -------------------------------------------------------
# Gate resolvers
# -------------------------------------------------------

def resolve_reviewer_state(
    review_state: dict[str, Any] | None,
    compact: dict[str, Any] | None,
    full_json: dict[str, Any] | None,
) -> dict[str, Any]:
    """Derive reviewer-related fields from the best available source."""
    def _age_seconds(utc_stamp: str) -> int | None:
        if not utc_stamp or utc_stamp == "n/a":
            return None
        try:
            ts = datetime.fromisoformat(utc_stamp.replace("Z", "+00:00"))
            return max(0, int((datetime.now(timezone.utc) - ts).total_seconds()))
        except (ValueError, TypeError):
            return None

    def _format_age(seconds: int | None) -> str:
        if seconds is None:
            return "--"
        if seconds < 60:
            return f"{seconds}s ago"
        if seconds < 3600:
            return f"{seconds // 60}m ago"
        return f"{seconds // 3600}h ago"

    bridge: dict[str, Any] = {}
    if review_state:
        bridge = review_state.get("bridge", {}) or {}
    reviewer_mode = coerce_string(bridge.get("reviewer_mode")) or "single_agent"
    poll_utc = coerce_string(bridge.get("last_codex_poll_utc"))

    # Prefer typed reviewer_freshness from reviewer_runtime over age-derived text
    typed_freshness = ""
    rt_for_freshness: dict[str, Any] = {}
    if review_state:
        rt_for_freshness = review_state.get("reviewer_runtime", {}) or {}
        typed_freshness = coerce_string(rt_for_freshness.get("reviewer_freshness"))
    freshness = typed_freshness or (_format_age(_age_seconds(poll_utc)) if poll_utc else "--")

    attention: dict[str, Any] = {}
    if review_state and isinstance(review_state.get("attention"), dict):
        attention = review_state["attention"]
    elif full_json and isinstance(full_json.get("attention"), dict):
        attention = full_json["attention"]

    accepted = False
    if review_state:
        rt = review_state.get("reviewer_runtime", {}) or {}
        acceptance = rt.get("review_acceptance", {}) or {}
        # Prefer the typed boolean when present; verdict text is display-only fallback
        raw_bool = acceptance.get("review_accepted")
        if isinstance(raw_bool, bool):
            accepted = raw_bool
        else:
            verdict = coerce_string(acceptance.get("current_verdict"))
            accepted = verdict.lower() in ("accepted", "approved", "pass")

    last_reviewed_sha = coerce_string(bridge.get("head_at_push_time"))
    if not last_reviewed_sha and compact:
        compact_bridge = compact.get("bridge")
        if isinstance(compact_bridge, dict):
            last_reviewed_sha = coerce_string(compact_bridge.get("head_at_push_time"))

    return {
        "reviewer_mode": reviewer_mode,
        "reviewer_freshness": freshness,
        "review_accepted": accepted,
        "last_reviewed_sha": last_reviewed_sha,
        "attention_status": coerce_string(attention.get("status")) or "n/a",
        "attention_summary": coerce_string(attention.get("summary")) or "n/a",
    }


def resolve_quality(push_report: dict[str, Any] | None) -> dict[str, Any]:
    """Derive guard-ok and check details from the push report."""
    if push_report is None:
        return {"last_guard_ok": True, "check_details": ()}
    preflight = push_report.get("preflight_step", {}) or {}
    rc = preflight.get("returncode", -1)
    guard_ok = rc == 0 if isinstance(rc, int) else True
    details: list[dict[str, str]] = []
    if not guard_ok:
        violations = push_report.get("violations")
        if isinstance(violations, list):
            for v in violations[:10]:
                if isinstance(v, dict):
                    details.append({
                        "check": coerce_string(v.get("step_name")) or "unknown",
                        "status": "FAIL",
                        "violation": coerce_string(v.get("summary")),
                    })
    return {"last_guard_ok": guard_ok, "check_details": tuple(details)}


def resolve_blocker_and_action(
    receipt: dict[str, Any] | None,
    review_state: dict[str, Any] | None,
    quality: dict[str, Any],
    *,
    pending_count: int | None = None,
) -> dict[str, Any]:
    """Derive top blocker, next action, and next command.

    Delegates blocker derivation to the canonical
    ``startup_blocker_decision`` reducer so every surface shares one
    producer. ``next_action`` and ``next_command`` still project from
    the governed push receipt because they encode the push state
    machine (``run_devctl_push`` / ``await_checkpoint`` / ``await_
    review``), which is a separate authority from the blocker reason.
    """
    session: dict[str, Any] = {}
    doctor: dict[str, Any] = {}
    if review_state:
        session = review_state.get("current_session", {}) or {}
        rt = review_state.get("reviewer_runtime", {}) or {}
        doctor = rt.get("doctor", {}) if isinstance(rt, dict) else {}

    next_action = coerce_string((receipt or {}).get("push_action")) or "n/a"
    snapshot = derive_blocker_decision(
        quality=quality,
        doctor=doctor,
        session=session,
        push_action=next_action,
        pending_count=pending_count,
    )
    next_command = _command_for_push_action(next_action)
    return {
        "top_blocker": snapshot.top_blocker,
        "next_action": next_action,
        "next_command": next_command,
        "blocker_snapshot": snapshot,
    }


def _command_for_push_action(action: str) -> str:
    """Map a push-decision action token to its governed devctl command."""
    if action == "run_devctl_push":
        return "python3 dev/scripts/devctl.py push --execute"
    if action == "await_checkpoint":
        return "commit current work, then rerun startup-context"
    if action == "await_review":
        return (
            "python3 dev/scripts/devctl.py review-channel "
            "--action status --terminal none --format json"
        )
    return ""


def resolve_pending_packets(review_state: dict[str, Any] | None) -> int:
    """Count live pending action_request packets from review state."""
    if review_state is None:
        return 0
    packets = review_state.get("packets", [])
    if not isinstance(packets, list):
        return 0
    return sum(
        1
        for packet in packets
        if _is_live_pending_action_request(packet, packets)
    )


def _is_live_pending_action_request(
    packet: object,
    packets: list[dict[str, Any]],
) -> bool:
    if not isinstance(packet, dict):
        return False
    if str(packet.get("kind") or "").strip() != "action_request":
        return False
    return _is_live_pending_packet(packet, packets)


def _is_live_pending_packet(
    packet: object,
    packets: list[dict[str, Any]],
) -> bool:
    def _parse_utc_stamp(value: str) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    if not isinstance(packet, dict):
        return False
    status = str(packet.get("status") or "").strip()
    if status != "pending":
        return False
    if _is_resolved_commit_approval_request(packet, packets):
        return False
    expires_at = _parse_utc_stamp(str(packet.get("expires_at_utc") or "").strip())
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        return False
    return True


def _is_resolved_commit_approval_request(
    packet: dict[str, Any],
    packets: list[dict[str, Any]],
) -> bool:
    if str(packet.get("kind") or "").strip() != "commit_approval":
        return False
    if not bool(packet.get("approval_required")):
        return False
    key = _packet_resolution_key(packet)
    if not any(key):
        return False
    for other in packets:
        if not isinstance(other, dict):
            continue
        if str(other.get("status") or "").strip() != "applied":
            continue
        if bool(other.get("approval_required")):
            continue
        if str(other.get("kind") or "").strip() != "commit_approval":
            continue
        if _packet_resolution_key(other) == key:
            return True
    return False


def _packet_resolution_key(packet: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(packet.get("trace_id") or "").strip(),
        str(packet.get("kind") or "").strip(),
        str(packet.get("target_ref") or "").strip(),
        str(packet.get("pipeline_generation") or "").strip(),
    )
