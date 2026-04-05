"""Gate-resolution helpers for the ControlPlaneReadModel.

Each ``_resolve_*`` function takes pre-loaded source dicts and returns
a derived state dict. No filesystem IO happens here -- all reading is
done by the caller in ``control_plane_read_model.py``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .value_coercion import coerce_bool, coerce_string


# -------------------------------------------------------
# Shared IO/time helpers (used by loader and resolvers)
# -------------------------------------------------------

def read_json_artifact(path: Path) -> dict[str, Any] | None:
    """Read a JSON artifact, returning None on any failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def age_seconds(utc_stamp: str) -> int | None:
    if not utc_stamp or utc_stamp == "n/a":
        return None
    try:
        ts = datetime.fromisoformat(utc_stamp.replace("Z", "+00:00"))
        return max(0, int((datetime.now(timezone.utc) - ts).total_seconds()))
    except (ValueError, TypeError):
        return None


def format_age(seconds: int | None) -> str:
    if seconds is None:
        return "--"
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    return f"{seconds // 3600}h ago"


def pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False


# -------------------------------------------------------
# Artifact path resolution
# -------------------------------------------------------

def artifact_paths(repo_root: Path) -> dict[str, Path]:
    """Resolve all artifact paths needed for the read model."""
    try:
        from ..repo_packs import active_path_config
        cfg = active_path_config()
        status_dir = cfg.review_status_dir_rel
        return {
            "receipt": repo_root / "dev/reports/startup/latest/receipt.json",
            "review_state": repo_root / cfg.review_state_json_rel,
            "push_report": repo_root / cfg.push_report_rel,
            "publisher_hb": repo_root / f"{status_dir}/publisher_heartbeat.json",
            "supervisor_hb": repo_root / f"{status_dir}/reviewer_supervisor_heartbeat.json",
            "codex_conductor": repo_root / f"{status_dir}/sessions/codex-conductor.json",
            "claude_conductor": repo_root / f"{status_dir}/sessions/claude-conductor.json",
            "full_json": repo_root / f"{status_dir}/full.json",
            "compact_json": repo_root / f"{status_dir}/compact.json",
        }
    except Exception:
        status_dir = "dev/review_status"
        return {
            "receipt": repo_root / "dev/reports/startup/latest/receipt.json",
            "review_state": repo_root / f"{status_dir}/review_state.json",
            "push_report": repo_root / "dev/reports/push/latest/push_report.json",
            "publisher_hb": repo_root / f"{status_dir}/publisher_heartbeat.json",
            "supervisor_hb": repo_root / f"{status_dir}/reviewer_supervisor_heartbeat.json",
            "codex_conductor": repo_root / f"{status_dir}/sessions/codex-conductor.json",
            "claude_conductor": repo_root / f"{status_dir}/sessions/claude-conductor.json",
            "full_json": repo_root / f"{status_dir}/full.json",
            "compact_json": repo_root / f"{status_dir}/compact.json",
        }


# -------------------------------------------------------
# Source loading
# -------------------------------------------------------

def load_sources(repo_root: Path) -> dict[str, Any]:
    """Load every artifact the read model needs, exactly once."""
    paths = artifact_paths(repo_root)
    return {
        "receipt": read_json_artifact(paths["receipt"]),
        "review_state": read_json_artifact(paths["review_state"]),
        "push_report": read_json_artifact(paths["push_report"]),
        "publisher_hb": read_json_artifact(paths["publisher_hb"]),
        "supervisor_hb": read_json_artifact(paths["supervisor_hb"]),
        "codex_conductor": read_json_artifact(paths["codex_conductor"]),
        "claude_conductor": read_json_artifact(paths["claude_conductor"]),
        "full_json": read_json_artifact(paths["full_json"]),
        "compact_json": read_json_artifact(paths["compact_json"]),
    }


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
    freshness = typed_freshness or (format_age(age_seconds(poll_utc)) if poll_utc else "--")

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


def resolve_daemon_state(sources: dict[str, Any]) -> dict[str, Any]:
    """Derive publisher/supervisor/conductor liveness from heartbeats."""
    pub_running = _is_daemon_running(sources.get("publisher_hb"))
    sup_running = _is_daemon_running(sources.get("supervisor_hb"))
    codex_alive = _is_conductor_alive(sources.get("codex_conductor"))
    claude_alive = _is_conductor_alive(sources.get("claude_conductor"))
    return {
        "publisher_running": pub_running,
        "supervisor_running": sup_running,
        "codex_conductor_alive": codex_alive,
        "claude_conductor_alive": claude_alive,
    }


def _is_daemon_running(data: dict[str, Any] | None) -> bool:
    if data is None:
        return False
    return not bool(data.get("stopped_at_utc", ""))


def _is_conductor_alive(data: dict[str, Any] | None) -> bool:
    if data is None:
        return False
    pid = data.get("session_pid")
    if not isinstance(pid, int) or pid <= 0:
        return False
    return pid_is_alive(pid)


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
) -> dict[str, Any]:
    """Derive top blocker, next action, and next command."""
    session: dict[str, Any] = {}
    doctor: dict[str, Any] = {}
    if review_state:
        session = review_state.get("current_session", {}) or {}
        rt = review_state.get("reviewer_runtime", {}) or {}
        doctor = rt.get("doctor", {}) if isinstance(rt, dict) else {}

    top_blocker = _derive_top_blocker(quality, doctor, session)
    next_action = coerce_string((receipt or {}).get("push_action")) or "n/a"
    next_command = _command_for_action(next_action)
    return {
        "top_blocker": top_blocker,
        "next_action": next_action,
        "next_command": next_command,
    }


def _derive_top_blocker(
    quality: dict[str, Any],
    doctor: dict[str, Any],
    session: dict[str, Any],
) -> str:
    if not quality.get("last_guard_ok", True):
        details = quality.get("check_details", ())
        if details:
            return f"guard fail: {details[0].get('check', 'unknown')}"
        return "code-shape debt"
    blocked = doctor.get("blocked_reason", "")
    if blocked and blocked != "pipeline_unavailable":
        return blocked
    findings = coerce_string(session.get("open_findings"))
    if findings and findings.strip().lower() not in ("none", ""):
        first_line = findings.strip().splitlines()[0].lstrip("- ").strip()
        return first_line[:60] + ("..." if len(first_line) > 60 else "")
    return "none"


def _command_for_action(action: str) -> str:
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
    """Count pending action packets from review state."""
    if review_state is None:
        return 0
    packets = review_state.get("packets", [])
    if not isinstance(packets, list):
        return 0
    return sum(
        1 for p in packets
        if isinstance(p, dict) and p.get("status") == "pending"
    )
