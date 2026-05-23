"""Guard and dogfood actions for current-row projection commands."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

from ..config import REPO_ROOT
from ..runtime.current_row_proof_bundle import render_current_row_projection
from .plan_execution_projection_common import (
    ProjectionCommandSupport as Support,
    build_current_row_proof_report as _build_report,
)


def run_current_row_proof_step(args) -> int:
    guard_id = str(args.guard_id)
    row_id = str(args.row_id)
    guard_command = [
        sys.executable or "python3",
        f"dev/scripts/checks/{guard_id}.py",
        "--format",
        "json",
    ]
    completed = subprocess.run(
        guard_command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    guard_payload = Support.json_payload(completed.stdout)
    ok = Support.guard_ok(guard_payload, completed.returncode)
    timestamp = Support.utc_timestamp()
    record = {
        "schema_version": 1,
        "contract_id": "GuardRunResult",
        "row_id": row_id,
        "guard_id": guard_id,
        "ok": ok,
        "status": "passed" if ok else "failed",
        "exit_code": completed.returncode,
        "command": shlex.join(guard_command),
        "receipt_id": Support.receipt_id(row_id, guard_id, timestamp, completed.stdout, completed.stderr),
        "timestamp": timestamp,
        "stdout_json": guard_payload,
        "stderr": completed.stderr.strip(),
    }
    Support.append_jsonl(Path(args.guard_output), record)

    report = _build_report(args, row_id=row_id)
    projection_path = _write_projection(args, report)
    output = {
        "ok": ok,
        "row_id": row_id,
        "guard_id": guard_id,
        "exit_code": completed.returncode,
        "guard_output_path": str(Support.repo_relative(Path(args.guard_output))),
        "projection_path": str(Support.repo_relative(projection_path)),
        "receipt_id": record["receipt_id"],
        "proof_bundle_ok": report.get("ok"),
        "next_bounded_command": report.get("next_bounded_command"),
    }
    if args.format == "json":
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(f"- ok: {ok}")
        print(f"- guard_id: `{guard_id}`")
        print(f"- receipt_id: `{record['receipt_id']}`")
        print(f"- next_bounded_command: `{report.get('next_bounded_command')}`")
    return completed.returncode


def run_current_row_dogfood(args) -> int:
    row_id = str(args.row_id)
    dogfood_command = [
        sys.executable or "python3",
        "dev/scripts/devctl.py",
        "check-router",
        "--execute",
        "--format",
        "json",
        "--command-timeout-seconds",
        str(args.command_timeout_seconds),
        "--route-timeout-seconds",
        str(args.route_timeout_seconds),
    ]
    completed = subprocess.run(
        dogfood_command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload = Support.json_payload(completed.stdout)
    ok = Support.guard_ok(payload, completed.returncode)
    timestamp = Support.utc_timestamp()
    record = {
        "schema_version": 1,
        "contract_id": "DogfoodRunResult",
        "row_id": row_id,
        "ok": ok,
        "status": "passed" if ok else "failed",
        "exit_code": completed.returncode,
        "command": shlex.join(dogfood_command),
        "run_id": Support.receipt_id(row_id, "dogfood", timestamp, completed.stdout, completed.stderr),
        "timestamp": timestamp,
        "stdout_json": payload,
        "stderr": completed.stderr.strip(),
    }
    Support.append_jsonl(Path(args.dogfood_output), record)
    report = _build_report(args, row_id=row_id)
    projection_path = _write_projection(args, report)
    output = {
        "ok": ok,
        "row_id": row_id,
        "exit_code": completed.returncode,
        "dogfood_output_path": str(Support.repo_relative(Path(args.dogfood_output))),
        "projection_path": str(Support.repo_relative(projection_path)),
        "run_id": record["run_id"],
        "proof_bundle_ok": report.get("ok"),
        "next_bounded_command": report.get("next_bounded_command"),
    }
    if args.format == "json":
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(f"- ok: {ok}")
        print(f"- run_id: `{record['run_id']}`")
        print(f"- next_bounded_command: `{report.get('next_bounded_command')}`")
    return completed.returncode


def _write_projection(args, report: dict[str, object]) -> Path:
    projection_path = Path(args.projection_output)
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    projection_path.write_text(render_current_row_projection(report), encoding="utf-8")
    return projection_path
