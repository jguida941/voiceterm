"""devctl dashboard command — governance snapshot from existing artifacts."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from ..common import emit_output, write_output
from ..config import REPO_ROOT
from ..runtime.control_plane_read_model import (
    ControlPlaneReadModel,
    build_control_plane_read_model,
)
from ..runtime.control_plane_read_model_support import ControlPlaneReadModelOptions
from ..runtime.control_plane_sources import load_sources
from ..runtime.governance_scan import scan_repo_governance_safely
from ..runtime.startup_blocker_decision import derive_blocker_decision
from ..runtime.review_state_locator import load_current_review_state
from ..runtime.review_state_parser import review_state_from_payload
from ..runtime.dashboard_snapshot_authority import normalize_dashboard_snapshot
from ..time_utils import utc_timestamp
from .dashboard_health import (
    _pid_is_alive,
    _read_conductor_liveness,
    _read_heartbeat,
    build_health_section,
    build_health_section as _build_health_section,
)
from .dashboard_header import project_dashboard_header_fields
from .reporting.dashboard_follow import run_follow
from .reporting.dashboard_views import VIEW_SECTIONS

# Shared utilities extracted to break circular import with dashboard_builders.
from .dashboard_utils import (
    _age_seconds,
    _extract_time_from_iso,
    _format_age,
    _format_duration,
    _parse_bridge,
    _parse_bridge_findings,
    _paths,
    _read_json,
    _tail_lines,
)

# Section-builder functions live in dashboard_builders; imported here so
# _assemble can call them, and re-exported for backward-compatible test access.
from .dashboard_builders import (  # noqa: E402
    CoordinationContext,
    NowSectionContext,
    _build_analytics_section,
    _build_audit_section,
    _build_coordination_section,
    _build_flow_section,
    _build_now_section,
    _build_one_line,
    _build_plan_section,
    _build_probes_section,
    _build_quality_section,
    _build_review_section,
    _build_reviewer_activity_section,
    _build_workers_section,
    _compile_summary,
    _extract_check_details,
    _extract_cleanup_rate,
    _extract_failing_files,
    _extract_push_success_values,
    _extract_push_timers,
    _extract_top_commands,
    _find_agent_by_role,
    _first_meaningful_line,
    _is_reviewer_overdue,
    _publication_effective,
)

from .dashboard_typed_state import (
    _extract_typed_attention,
    _extract_typed_bridge_fields,
    _extract_typed_bridge_findings,
    _extract_typed_coordination,
    _extract_typed_control_packets,
    _extract_typed_doctor,
    _extract_typed_instruction_provenance,
    _extract_typed_packets,
    _extract_typed_priority_decision,
    _extract_typed_runtime_counts,
    _extract_typed_session,
)

def _git_short() -> dict[str, Any]:
    """Return branch, HEAD short sha, dirty state, ahead/behind, dirty count, and recent commits."""
    result: dict[str, Any] = {
        "branch": "unknown",
        "head": "unknown",
        "dirty": "unknown",
        "ahead": 0,
        "behind": 0,
        "dirty_files": 0,
        "recent_commits": [],
    }
    try:
        sb = subprocess.run(
            ["git", "status", "-sb", "--porcelain"],
            capture_output=True, text=True, timeout=5, cwd=str(REPO_ROOT),
            check=False,
        )
        lines = sb.stdout.strip().splitlines()
        if lines:
            header = lines[0].lstrip("# ").strip()
            result["branch"] = header.split("...")[0] if "..." in header else header
            dirty_lines = lines[1:]
            result["dirty"] = "DIRTY" if dirty_lines else "CLEAN"
            result["dirty_files"] = len(dirty_lines)
            ahead, behind = _parse_ahead_behind(header)
            result["ahead"] = ahead
            result["behind"] = behind
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "-3"],
            capture_output=True, text=True, timeout=5, cwd=str(REPO_ROOT),
            check=False,
        )
        commits: list[dict[str, str]] = []
        for line in log.stdout.strip().splitlines():
            parts = line.split(None, 1)
            if parts:
                commits.append({
                    "sha": parts[0],
                    "message": parts[1] if len(parts) > 1 else "",
                })
        if commits:
            result["head"] = commits[0]["sha"]
            result["recent_commits"] = commits
    except (OSError, subprocess.TimeoutExpired):
        pass
    return result


def _parse_ahead_behind(header: str) -> tuple[int, int]:
    """Extract ahead/behind counts from ``[ahead N, behind M]`` in header."""
    ahead, behind = 0, 0
    bracket = re.search(r"\[(.+?)\]", header)
    if bracket:
        content = bracket.group(1)
        am = re.search(r"ahead\s+(\d+)", content)
        bm = re.search(r"behind\s+(\d+)", content)
        ahead = int(am.group(1)) if am else 0
        behind = int(bm.group(1)) if bm else 0
    return ahead, behind


def _session_age(repo_root: Path) -> dict[str, Any]:
    """Read publisher heartbeat and compute session duration from started_at_utc."""
    data = _read_json(repo_root / _paths()["publisher_hb"])
    if data is None:
        return {"session_age_s": None, "session_label": "--", "started_at_utc": "", "started_time": ""}
    started = data.get("started_at_utc", "")
    age_s = _age_seconds(started)
    started_time = _extract_time_from_iso(started) if started else ""
    return {
        "session_age_s": age_s,
        "session_label": _format_duration(age_s),
        "started_at_utc": started,
        "started_time": started_time,
    }


def _repo_name() -> str:
    """Derive repo name from git remote or directory name."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5, cwd=str(REPO_ROOT),
            check=False,
        )
        url = result.stdout.strip()
        if url:
            name = url.rstrip("/").rsplit("/", 1)[-1]
            return name.removesuffix(".git")
    except (OSError, subprocess.TimeoutExpired):
        pass
    return REPO_ROOT.name


def _build_timeline_section(
    repo_root: Path, *, count: int = 10,
) -> list[dict[str, str]]:
    """Build the TIMELINE section from the last *count* devctl event log entries."""
    raw_lines = _tail_lines(repo_root / _paths()["events_jsonl"], count=count)
    events: list[dict[str, str]] = []
    for line in raw_lines:
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        ts_raw = entry.get("timestamp", "")
        time_label = _extract_time_from_iso(ts_raw)
        success = entry.get("success", False)
        dur = entry.get("duration_seconds")
        dur_label = f"{dur:.1f}s" if isinstance(dur, (int, float)) else "n/a"
        events.append({
            "time": time_label,
            "command": entry.get("command", "unknown"),
            "result": "PASS" if success else "FAIL",
            "duration": dur_label,
        })
    return events


def build_snapshot(
    *, repo_root: Path = REPO_ROOT, view: str = "overview", role: str = "dashboard",
) -> dict[str, Any]:
    """Build a DashboardSnapshot dict from existing artifacts and git state.

    Non-overview views only load artifacts their sections need. Typed
    ReviewState (review_state.json) overrides compact.json for session,
    doctor, attention, and packet queue when available.
    """
    git = _git_short()
    needs = VIEW_SECTIONS.get(view, frozenset())
    load_all = not needs  # overview
    p = _paths()
    governance = scan_repo_governance_safely(repo_root)
    typed_review_state = load_current_review_state(
        repo_root,
        governance=governance,
        prefer_cached_projection=False,
    )
    # Pass the typed review-state through ``review_state_override`` so the
    # F1 / MP-384 parity contract holds: ``load_sources`` consumes the exact
    # same frozen snapshot rather than re-running
    # ``load_current_review_state_payload`` and triggering a second
    # bridge-projection refresh that could rewrite ``review_state.json``
    # mid-tick and desync the dashboard from startup-context / session-resume.
    sources = load_sources(
        repo_root,
        governance=governance,
        review_state_override=typed_review_state,
    )

    review_state_payload = sources.get("review_state") if load_all or needs else None
    typed_review_state = typed_review_state or (
        review_state_from_payload(review_state_payload)
        if isinstance(review_state_payload, dict)
        else None
    )
    dashboard_review_state = review_state_payload
    if dashboard_review_state is None and typed_review_state is not None and hasattr(
        typed_review_state,
        "to_dict",
    ):
        dashboard_review_state = typed_review_state.to_dict()

    compact = (
        sources.get("compact_json")
        if load_all or (needs & {"review", "now", "coordination", "health", "workers"})
        else None
    )
    push_data = (
        sources.get("push_report")
        if load_all or (needs & {"publication", "quality", "flow"})
        else None
    )
    receipt = (
        sources.get("receipt")
        if load_all or (needs & {"publication", "flow", "coordination"})
        else None
    )
    agents = _read_json(repo_root / p["agents_json"]) if load_all or (needs & {"review", "workers", "now"}) else None
    pipeline = _read_json(repo_root / p["pipeline_json"]) if load_all or (needs & {"flow"}) else None

    # Prefer typed ReviewState for bridge fields; fall back to markdown parsing
    _need_br = load_all or bool(needs & {"review", "now", "coordination", "reviewer_activity", "findings"})
    _need_fi = load_all or bool(needs & {"findings", "plan"})
    _bridge_path = repo_root / p["bridge_md"]
    bridge = _extract_typed_bridge_fields(dashboard_review_state) if dashboard_review_state and _need_br else (_parse_bridge(_bridge_path) if _need_br else _empty_bridge())
    bridge_findings = _extract_typed_bridge_findings(dashboard_review_state) if dashboard_review_state and _need_fi else (_parse_bridge_findings(_bridge_path) if _need_fi else [])
    gov_data = _read_json(repo_root / p["governance_review_json"]) if load_all or (needs & {"audit"}) else None
    probe_data = _read_json(repo_root / p["probe_summary_json"]) if load_all or (needs & {"quality"}) else None
    ds_data = _read_json(repo_root / p["data_science_json"]) if load_all or (needs & {"analytics"}) else None

    session_info = _session_age(repo_root) if load_all or (needs & {"repo", "coordination"}) else None

    # Build the single resolved control-plane read model so downstream
    # sections can read from it instead of recomputing state independently.
    cp_model = build_control_plane_read_model(
        repo_root,
        sources_override=sources,
        options=ControlPlaneReadModelOptions(
            governance=governance,
            review_state=typed_review_state,
            caller_role=role,
        ),
    )
    startup_context_payload: dict[str, Any] | None = None
    try:
        from ..runtime.startup_context import build_startup_context

        startup_context = build_startup_context(
            repo_root=repo_root,
            governance=governance,
            review_state=typed_review_state,
        )
        startup_context_payload = startup_context.to_dict()
    except Exception:
        startup_context_payload = None

    snapshot = _assemble(
        git, compact, push_data, receipt, agents, pipeline, bridge,
        gov_data=gov_data, probe_data=probe_data, ds_data=ds_data,
        bridge_findings=bridge_findings,
        session_info=session_info,
        repo_root=repo_root,
        view=view,
        review_state=dashboard_review_state,
        control_plane=cp_model,
        startup_context=startup_context_payload,
    )
    return snapshot

def _empty_bridge() -> dict[str, str]:
    """Return the default bridge fields when bridge parsing is skipped."""
    return {
        "last_poll": "n/a", "last_poll_utc": "", "reviewer_mode": "n/a",
        "instruction": "n/a", "verdict": "n/a", "findings_raw": "",
        "reviewed_scope_raw": "", "instruction_full": "n/a",
    }


def _prepare_runtime_sections(
    *,
    compact: dict[str, Any] | None,
    bridge: dict[str, str],
    review_state: dict[str, Any] | None,
    repo_root: Path,
    control_plane: ControlPlaneReadModel | None,
    quality: dict[str, Any],
    session_info: dict[str, Any] | None,
    receipt_push: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    str,
    str,
    dict[str, Any] | None,
    list[dict[str, Any]],
    dict[str, int],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any] | None,
]:
    """Resolve typed runtime sections shared by the dashboard snapshot."""
    if review_state:
        session = _extract_typed_session(review_state)
        doctor = _extract_typed_doctor(review_state)
    else:
        session = (compact or {}).get("current_session", {})
        doctor = (compact or {}).get("doctor", {})
    session_instruction = str(session.get("current_instruction") or "").strip()
    bridge_instruction = str(
        bridge.get("instruction_full") or bridge.get("instruction") or ""
    ).strip()
    instruction_text = (
        bridge_instruction
        if review_state and bridge_instruction and bridge_instruction != "n/a"
        else (session_instruction or bridge_instruction or "n/a")
    )
    top_blocker = (
        control_plane.top_blocker
        if control_plane is not None
        else derive_blocker_decision(
            quality=quality,
            doctor=doctor,
            session=session,
        ).top_blocker
    )
    typed_coordination = (
        control_plane.coordination.to_dict()
        if control_plane and control_plane.coordination is not None
        else _extract_typed_coordination(review_state)
    )
    typed_packets = _extract_typed_packets(review_state)
    typed_runtime_counts = _extract_typed_runtime_counts(review_state)
    typed_attention = _extract_typed_attention(review_state)
    if not typed_coordination or not str(typed_coordination.get("current_slice") or "").strip():
        from ..runtime.startup_context import build_startup_context

        fallback_startup_context = build_startup_context(repo_root=repo_root)
        if fallback_startup_context.coordination is not None:
            typed_coordination = fallback_startup_context.coordination.to_dict()

    health = build_health_section(repo_root, compact, runtime_counts=typed_runtime_counts)
    if control_plane:
        health["publisher"]["running"] = control_plane.publisher_running
        health["supervisor"]["running"] = control_plane.supervisor_running
        health["codex_conductor"]["alive"] = control_plane.codex_conductor_alive
        health["claude_conductor"]["alive"] = control_plane.claude_conductor_alive
        health["active_daemons"] = sum(
            1
            for running in (
                control_plane.publisher_running,
                control_plane.supervisor_running,
            )
            if running
        )
        health["attention_status"] = control_plane.attention_status
        health["attention_summary"] = control_plane.attention_summary

    coordination = _build_coordination_section(
        session,
        bridge,
        doctor,
        CoordinationContext(
            instruction_rev=session.get("current_instruction_revision", "n/a"),
            receipt_push=control_plane.next_action if control_plane else receipt_push,
            session_info=session_info or {},
            typed_packets=typed_packets,
            runtime_counts=typed_runtime_counts,
        ),
    )
    if typed_coordination:
        coordination.update({
            "active_target": typed_coordination.get("active_target"),
            "current_slice": typed_coordination.get("current_slice", ""),
            "scope_paths": typed_coordination.get("scope_paths", []),
            "ownership_status": typed_coordination.get("ownership_status", ""),
            "declared_topology": typed_coordination.get("declared_topology", ""),
            "observed_topology": typed_coordination.get("observed_topology", ""),
            "recommended_topology": typed_coordination.get("recommended_topology", ""),
            "fanout_posture": typed_coordination.get("fanout_posture", ""),
            "safe_to_fanout": typed_coordination.get("safe_to_fanout", False),
            "worktree_strategy": typed_coordination.get("worktree_strategy", ""),
            "resync_required": typed_coordination.get("resync_required", False),
            "resync_reasons": typed_coordination.get("resync_reasons", []),
            "duplicate_worktrees": typed_coordination.get("duplicate_worktrees", []),
            "actors": typed_coordination.get("actors", []),
        })
    return (
        session,
        doctor,
        instruction_text,
        top_blocker,
        typed_coordination,
        typed_packets,
        typed_runtime_counts,
        health,
        coordination,
        typed_attention,
    )


def _assemble(
    git: dict[str, str],
    compact: dict[str, Any] | None,
    push_data: dict[str, Any] | None,
    receipt: dict[str, Any] | None,
    agents: dict[str, Any] | None,
    pipeline: dict[str, Any] | None,
    bridge: dict[str, str],
    *,
    gov_data: dict[str, Any] | None = None,
    probe_data: dict[str, Any] | None = None,
    ds_data: dict[str, Any] | None = None,
    bridge_findings: list[dict[str, str]] | None = None,
    repo_root: Path = REPO_ROOT,
    session_info: dict[str, Any] | None = None,
    view: str = "overview",
    review_state: dict[str, Any] | None = None,
    control_plane: ControlPlaneReadModel | None = None,
    plan: dict[str, Any] | None = None,
    startup_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the typed DashboardSnapshot from raw sources.

    When ``control_plane`` is supplied, the summary/now/health/coordination
    sections read resolved gates from the single read model instead of
    recomputing them independently.
    """
    reviewer_agent = _find_agent_by_role(agents, "reviewer")
    implementer_agent = _find_agent_by_role(agents, "implementer")
    receipt_push = (receipt or {}).get("push_action", "n/a")

    publication_effective = _publication_effective(push_data, receipt, git)
    publication_effective["timers"] = _extract_push_timers(push_data)
    quality = _build_quality_section(push_data)
    quality["probes"] = _build_probes_section(probe_data)
    last_change_age = _age_seconds(bridge.get("last_poll_utc", ""))
    timeline_count = 100 if view == "analytics" else 10
    (
        session,
        doctor,
        instruction_text,
        top_blocker,
        typed_coordination,
        typed_packets,
        typed_runtime_counts,
        health,
        coordination,
        typed_attention,
    ) = _prepare_runtime_sections(
        compact=compact,
        bridge=bridge,
        review_state=review_state,
        repo_root=repo_root,
        control_plane=control_plane,
        quality=quality,
        session_info=session_info,
        receipt_push=receipt_push,
    )

    plan_section = plan if plan is not None else _build_plan_section(
        typed_coordination,
        session,
        bridge_findings or [],
        startup_context=startup_context,
        pending_packets_count=len(typed_packets),
    )
    control_packets = _extract_typed_control_packets(review_state)
    repo_worktree = git["dirty"]
    repo_dirty_files = git.get("dirty_files", 0)
    if (
        control_plane is not None
        and bool(getattr(control_plane, "worktree_clean", False))
        and bool(getattr(control_plane, "managed_projection_drift", False))
    ):
        repo_worktree = "MANAGED_PROJECTION_DRIFT"
        repo_dirty_files = 0

    snapshot: dict[str, Any] = {
        "schema_version": 2,
        "contract_id": "DashboardSnapshot",
        "timestamp": utc_timestamp(),
        "view": view,
        "repo": {
            "name": _repo_name(),
            "branch": git["branch"],
            "head": git["head"],
            "worktree": repo_worktree,
            "session": (session_info or {}).get("session_label", "--"),
            "ahead": git.get("ahead", 0),
            "behind": git.get("behind", 0),
            "dirty_files": repo_dirty_files,
            "recent_commits": git.get("recent_commits", []),
        },
        "now": _build_now_section(NowSectionContext(
            bridge=bridge,
            reviewer=reviewer_agent,
            implementer=implementer_agent,
            session=session,
            instruction_text=instruction_text,
            top_blocker=top_blocker,
            last_change_age=last_change_age,
            coordination=typed_coordination,
            runtime_counts=typed_runtime_counts,
            next_action_override=control_plane.next_action if control_plane else "",
        )),
        "health": health,
        "review": _build_review_section(bridge, reviewer_agent, implementer_agent, session, instruction_text, control_plane.reviewer_mode if control_plane and review_state else ""),
        "workers": _build_workers_section(agents),
        "plan": plan_section,
        "findings": bridge_findings or [],
        "publication": publication_effective,
        "quality": quality,
        "audit": _build_audit_section(gov_data),
        "analytics": _build_analytics_section(ds_data, gov_data, repo_root),
        "coordination": coordination,
        "reviewer_activity": _build_reviewer_activity_section(bridge, reviewer_agent),
        "flow": _build_flow_section(receipt, push_data, session),
        "timeline": _build_timeline_section(repo_root, count=timeline_count),
        "typed_attention": typed_attention,
        "pending_packets": typed_packets,
        "control_packets": control_packets,
        "control_plane": control_plane.to_dict() if control_plane else None,
    }
    if review_state:
        snapshot["now"]["instruction_provenance"] = _extract_typed_instruction_provenance(
            review_state
        )
        snapshot["now"]["priority_decision"] = _extract_typed_priority_decision(
            review_state
        )
    snapshot["summary"] = _compile_summary(snapshot)
    snapshot.update(
        project_dashboard_header_fields(
            summary=snapshot["summary"],
            now=snapshot["now"],
            coordination=snapshot["coordination"],
            control_plane=control_plane,
        )
    )
    return normalize_dashboard_snapshot(
        snapshot,
        repo_root=repo_root,
        review_state=review_state,
    )


def run(args) -> int:
    """Build and render the governance dashboard."""
    if bool(getattr(args, "follow", False)):
        return run_follow(
            args,
            snapshot_builder=lambda: build_snapshot(
                view=getattr(args, "view", "overview"),
                role=getattr(args, "role", "dashboard"),
            ),
            snapshot_renderer=lambda snapshot: _render_dashboard_snapshot(args, snapshot),
        )

    view = getattr(args, "view", "overview")
    role = getattr(args, "role", "dashboard")
    snapshot = build_snapshot(view=view, role=role)

    output = _render_dashboard_snapshot(args, snapshot)

    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return 0


def _render_dashboard_snapshot(args, snapshot: dict[str, Any]) -> str:
    """Render one dashboard snapshot using the requested dashboard format."""
    from .dashboard_render import render_json, render_markdown, render_terminal
    from ..runtime.session_posture_simple_render import render_simple_posture_snapshot

    no_color = getattr(args, "no_color", False)
    fmt = getattr(args, "format", "terminal")
    if fmt == "json":
        return render_json(snapshot)
    if fmt == "md":
        return render_markdown(snapshot)
    if fmt == "simple":
        now = snapshot.get("now", {})
        return render_simple_posture_snapshot(
            title="Dashboard",
            next_action=now.get("next_action") if isinstance(now, dict) else "",
            top_blocker=now.get("top_blocker") if isinstance(now, dict) else "",
            session_posture=snapshot.get("session_posture"),
        )
    return render_terminal(snapshot, no_color=no_color)
