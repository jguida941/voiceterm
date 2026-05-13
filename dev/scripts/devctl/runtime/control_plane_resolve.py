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
from .control_plane_quality import resolve_quality
from .control_plane_sources import artifact_paths, load_sources, read_json_artifact
from .post_checkpoint_dirty_support import COMMIT_CHECKPOINT_COMMAND
from .review_packet_inbox import summarize_packet_attention_open_findings
from .startup_blocker_decision import BlockerSnapshot, derive_blocker_decision
from .control_plane_startup_authority import startup_authority_from_receipt
from .value_coercion import coerce_bool, coerce_string


class ControlPlaneGitStateError(RuntimeError):
    """Raised when control-plane git probes cannot produce trustworthy state."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_git_probe(
    repo_root: Path,
    args: list[str],
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(repo_root),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        command = " ".join(args)
        raise ControlPlaneGitStateError(
            f"Failed to probe git state with `{command}` in {repo_root}."
        ) from exc


def load_git_state(repo_root: Path) -> dict[str, Any]:
    """Load branch, HEAD, dirty state, and ahead count from git."""
    result: dict[str, Any] = {
        "branch": "unknown", "head": "unknown", "clean": True, "ahead": 0,
    }
    sb = _run_git_probe(repo_root, ["git", "status", "-sb", "--porcelain"])
    lines = sb.stdout.strip().splitlines()
    if lines:
        header = lines[0].lstrip("# ").strip()
        result["branch"] = header.split("...")[0] if "..." in header else header
        result["clean"] = len(lines) <= 1
        bracket = re.search(r"\[(.+?)\]", header)
        if bracket:
            am = re.search(r"ahead\s+(\d+)", bracket.group(1))
            result["ahead"] = int(am.group(1)) if am else 0

    log = _run_git_probe(repo_root, ["git", "log", "--oneline", "-1"])
    sha_line = log.stdout.strip()
    if sha_line:
        result["head"] = sha_line.split(None, 1)[0]
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
    poll_utc = coerce_string(bridge.get("last_codex_poll_utc"))
    authority: dict[str, Any] = {}
    reviewer_runtime: dict[str, Any] = {}
    if review_state and isinstance(review_state.get("authority_snapshot"), dict):
        authority = review_state["authority_snapshot"]
    if review_state and isinstance(review_state.get("reviewer_runtime"), dict):
        reviewer_runtime = review_state["reviewer_runtime"]
    session_posture = (
        reviewer_runtime.get("session_posture")
        if isinstance(reviewer_runtime.get("session_posture"), dict)
        else {}
    )
    reviewer_mode = (
        coerce_string(session_posture.get("reviewer_mode"))
        or coerce_string(session_posture.get("effective_reviewer_mode"))
        or coerce_string(reviewer_runtime.get("effective_reviewer_mode"))
        or coerce_string(bridge.get("effective_reviewer_mode"))
        or coerce_string(bridge.get("reviewer_mode"))
        or "single_agent"
    )

    # Prefer typed reviewer_freshness from reviewer_runtime over age-derived text
    typed_freshness = ""
    rt_for_freshness = reviewer_runtime
    if rt_for_freshness:
        typed_freshness = coerce_string(rt_for_freshness.get("reviewer_freshness"))
    freshness = (
        typed_freshness
        or coerce_string(authority.get("reviewer_freshness"))
        or (_format_age(_age_seconds(poll_utc)) if poll_utc else "--")
    )

    attention: dict[str, Any] = {}
    if review_state and isinstance(review_state.get("attention"), dict):
        attention = review_state["attention"]
    elif full_json and isinstance(full_json.get("attention"), dict):
        attention = full_json["attention"]
    attention_status = coerce_string(attention.get("status")) or "n/a"
    implementation_permission = coerce_string(
        authority.get("implementation_permission")
    ).lower()
    if (
        freshness in {"fresh", "poll_due"}
        and attention_status == "review_loop_relaunch_required"
    ) or (
        freshness == "fresh"
        and implementation_permission in {"blocked", "suspended"}
    ):
        freshness = "stale"

    accepted = False
    if review_state:
        acceptance = reviewer_runtime.get("review_acceptance", {}) or {}
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
        "attention_status": attention_status,
        "attention_summary": coerce_string(attention.get("summary")) or "n/a",
    }


def resolve_blocker_and_action(
    receipt: dict[str, Any] | None,
    review_state: dict[str, Any] | None,
    quality: dict[str, Any],
    *,
    pending_count: int | None = None,
    startup_authority: dict[str, Any] | None = None,
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
        session = dict(review_state.get("current_session", {}) or {})
        session["open_findings"] = summarize_packet_attention_open_findings(
            review_state,
            fallback=coerce_string(session.get("open_findings")),
            agent="codex",
        )
        rt = review_state.get("reviewer_runtime", {}) or {}
        doctor = rt.get("doctor", {}) if isinstance(rt, dict) else {}

    next_action = coerce_string((receipt or {}).get("push_action")) or "n/a"
    snapshot = derive_blocker_decision(
        quality=quality,
        doctor=doctor,
        session=session,
        push_action=next_action,
        pending_count=pending_count,
        startup_authority=startup_authority
        if startup_authority is not None
        else startup_authority_from_receipt(receipt),
    )
    next_command = _command_for_push_action(snapshot.next_action or next_action)
    return {
        "top_blocker": snapshot.top_blocker,
        "next_action": snapshot.next_action or next_action,
        "next_command": next_command,
        "blocker_snapshot": snapshot,
    }


def resolve_implementation_blocked(
    receipt: dict[str, Any] | None,
    review_state: dict[str, Any] | None,
) -> bool:
    """Prefer live typed authority when the startup receipt is stale."""
    if coerce_bool((receipt or {}).get("implementation_blocked", False)):
        return True
    if not isinstance(review_state, dict):
        return False

    authority = review_state.get("authority_snapshot")
    if isinstance(authority, dict):
        permission = coerce_string(authority.get("implementation_permission")).lower()
        if permission in {"blocked", "suspended"}:
            return True

    reviewer_runtime = review_state.get("reviewer_runtime")
    if not isinstance(reviewer_runtime, dict):
        return False
    if coerce_bool(reviewer_runtime.get("implementation_blocked", False)):
        return True
    doctor = reviewer_runtime.get("doctor")
    return isinstance(doctor, dict) and coerce_bool(
        doctor.get("implementation_blocked", False)
    )


def _command_for_push_action(action: str) -> str:
    """Map a push-decision action token to its governed devctl command."""
    if action.startswith("checkpoint_blocked_by_startup_authority:"):
        kind = action.rsplit(":", 1)[-1]
        if kind == "import_index_atomicity":
            return (
                "stage missing imported file(s), then rerun "
                "python3 dev/scripts/devctl.py startup-context --format summary"
            )
        return COMMIT_CHECKPOINT_COMMAND
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
