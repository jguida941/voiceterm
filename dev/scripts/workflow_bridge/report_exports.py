"""Report export helpers for autonomy workflow bridge commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from .common import append_output, read_json


def export_controller(args: argparse.Namespace) -> int:
    """Export controller summary fields into GitHub action outputs."""
    payload = read_json(Path(args.input_file))
    fields = [
        ("summary_json", str(payload.get("summary_json", ""))),
        ("latest_working_branch", str(payload.get("latest_working_branch", ""))),
        ("branch_base", str(payload.get("branch_base", ""))),
        ("resolved", "true" if payload.get("resolved") else "false"),
        ("controller_run_id", str(payload.get("controller_run_id", ""))),
        ("reason", str(payload.get("reason", ""))),
        ("phone_status_latest_json", str(payload.get("phone_status_latest_json", ""))),
        ("phone_status_latest_md", str(payload.get("phone_status_latest_md", ""))),
    ]
    append_output(Path(args.github_output), fields)
    return 0


def export_swarm(args: argparse.Namespace) -> int:
    """Export swarm-run report summary fields into GitHub outputs."""
    payload = read_json(Path(args.input_file))
    summary = payload.get("swarm", {}).get("summary", {})
    plan_update = payload.get("plan_update", {})
    fields = [
        ("report_ok", "true" if payload.get("ok") else "false"),
        ("run_dir", str(payload.get("run_dir", ""))),
        ("swarm_selected_agents", str(summary.get("selected_agents", ""))),
        ("swarm_worker_agents", str(summary.get("worker_agents", ""))),
        ("reviewer_lane", str(summary.get("reviewer_lane", ""))),
        ("governance_ok", "true" if payload.get("governance", {}).get("ok") else "false"),
        ("plan_update_ok", "true" if plan_update.get("ok") else "false"),
        ("plan_update_updated", "true" if plan_update.get("updated") else "false"),
    ]
    append_output(Path(args.github_output), fields)
    return 0


def assert_swarm_ok(args: argparse.Namespace) -> int:
    """Exit non-zero when swarm report payload is marked not ok."""
    payload = read_json(Path(args.input_file))
    if not payload.get("ok"):
        print("swarm_run report marked not ok")
        return 1
    return 0
