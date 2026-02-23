#!/usr/bin/env python3
"""Validate 3-agent coordination parity between MASTER_PLAN and runbook."""

from __future__ import annotations

import argparse
import json
import re
import sys
from itertools import combinations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MASTER_PLAN_PATH = REPO_ROOT / "dev/active/MASTER_PLAN.md"
RUNBOOK_PATH = REPO_ROOT / "dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md"

MASTER_BOARD_HEADING = "## Multi-Agent Coordination Board (3-Agent Mode)"
RUNBOOK_BOARD_HEADING = "## 0) Current Execution Mode (3 Agents, Default)"
RUNBOOK_INSTRUCTION_HEADING = "## 14) Orchestrator Instruction Log (Append-Only)"
RUNBOOK_LEDGER_HEADING = "## 15) Shared Ledger (Append-Only)"
RUNBOOK_SIGNOFF_HEADING = "## 16) End-of-Cycle Signoff (Required)"

REQUIRED_AGENTS = ("AGENT-1", "AGENT-2", "AGENT-3")
REQUIRED_SIGNERS = REQUIRED_AGENTS + ("ORCHESTRATOR",)
ALLOWED_MASTER_STATUSES = {
    "planned",
    "in-progress",
    "ready-for-review",
    "changes-requested",
    "approved",
    "merged",
    "blocked",
}
ALLOWED_LEDGER_STATUSES = ALLOWED_MASTER_STATUSES | {"ready"}
ALLOWED_INSTRUCTION_STATUSES = {"pending", "acked", "completed", "cancelled"}
UTC_Z_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
SIGNOFF_DATE_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)?$"
)
MP_RANGE_PATTERN = re.compile(r"MP-(\d{3})\.\.MP-(\d{3})")
MP_SINGLE_PATTERN = re.compile(r"MP-(\d{3})")
HANDOFF_TOKEN_PATTERN = re.compile(r"handoff[:=]([A-Za-z0-9_-]+)", re.IGNORECASE)


def _strip_code_ticks(value: str) -> str:
    text = value.strip()
    if text.startswith("`") and text.endswith("`"):
        return text[1:-1]
    return text


def _normalize(value: str) -> str:
    return " ".join(_strip_code_ticks(value).split())


def _split_table_row(line: str) -> list[str]:
    return [_strip_code_ticks(col.strip()) for col in line.strip().split("|")[1:-1]]


def _extract_table_rows(markdown: str, heading: str) -> tuple[list[dict], str | None]:
    lines = markdown.splitlines()
    heading_index = -1
    for idx, line in enumerate(lines):
        if line.strip() == heading:
            heading_index = idx
            break
    if heading_index < 0:
        return [], f"Missing heading: {heading}"

    table_start = -1
    for idx in range(heading_index + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("|"):
            table_start = idx
            break
        if stripped.startswith("## "):
            break
    if table_start < 0:
        return [], f"Missing table under heading: {heading}"

    table_lines: list[str] = []
    for idx in range(table_start, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("|"):
            table_lines.append(stripped)
            continue
        if table_lines:
            break
    if len(table_lines) < 2:
        return [], f"Incomplete table under heading: {heading}"

    headers = _split_table_row(table_lines[0])
    if not headers:
        return [], f"Invalid table header under heading: {heading}"

    rows: list[dict] = []
    for row_line in table_lines[2:]:
        columns = _split_table_row(row_line)
        if len(columns) != len(headers):
            return [], f"Malformed row under heading: {heading}"
        rows.append({headers[i]: columns[i] for i in range(len(headers))})
    return rows, None


def _rows_by_key(rows: list[dict], field: str) -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    for row in rows:
        key = _normalize(str(row.get(field, ""))).upper()
        if key:
            mapping[key] = row
    return mapping


def _ledger_row_matches_agent(row: dict, agent: str, branch: str) -> bool:
    area = _normalize(str(row.get("Area", ""))).upper()
    actor = _normalize(str(row.get("Actor", ""))).upper()
    ledger_branch = _normalize(str(row.get("Branch", "")))
    if area == agent or actor == agent:
        return True
    return bool(branch and ledger_branch == branch)


def _expand_mp_scope_ids(value: str) -> set[str]:
    text = _normalize(value)
    ids = {f"MP-{num}" for num in MP_SINGLE_PATTERN.findall(text)}
    for start_s, end_s in MP_RANGE_PATTERN.findall(text):
        start = int(start_s)
        end = int(end_s)
        if start > end:
            start, end = end, start
        for number in range(start, end + 1):
            ids.add(f"MP-{number:03d}")
    return ids


def _handoff_token(value: str) -> str | None:
    match = HANDOFF_TOKEN_PATTERN.search(value)
    if not match:
        return None
    return match.group(1).strip().lower() or None


def _build_report() -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not MASTER_PLAN_PATH.exists():
        return {
            "command": "check_multi_agent_sync",
            "ok": False,
            "error": f"Missing file: {MASTER_PLAN_PATH.relative_to(REPO_ROOT)}",
        }
    if not RUNBOOK_PATH.exists():
        return {
            "command": "check_multi_agent_sync",
            "ok": False,
            "error": f"Missing file: {RUNBOOK_PATH.relative_to(REPO_ROOT)}",
        }

    master_text = MASTER_PLAN_PATH.read_text(encoding="utf-8")
    runbook_text = RUNBOOK_PATH.read_text(encoding="utf-8")
    master_rows, master_error = _extract_table_rows(master_text, MASTER_BOARD_HEADING)
    runbook_rows, runbook_error = _extract_table_rows(runbook_text, RUNBOOK_BOARD_HEADING)
    instruction_rows, instruction_error = _extract_table_rows(
        runbook_text, RUNBOOK_INSTRUCTION_HEADING
    )
    ledger_rows, ledger_error = _extract_table_rows(runbook_text, RUNBOOK_LEDGER_HEADING)
    signoff_rows, signoff_error = _extract_table_rows(runbook_text, RUNBOOK_SIGNOFF_HEADING)
    for maybe_error in (master_error, runbook_error, instruction_error, ledger_error, signoff_error):
        if maybe_error:
            errors.append(maybe_error)

    master_by_agent = _rows_by_key(master_rows, "Agent")
    runbook_by_agent = _rows_by_key(runbook_rows, "Agent")
    required = set(REQUIRED_AGENTS)
    master_agents = set(master_by_agent)
    runbook_agents = set(runbook_by_agent)

    if required - master_agents:
        errors.append(
            "MASTER_PLAN missing agent rows: " + ", ".join(sorted(required - master_agents))
        )
    if required - runbook_agents:
        errors.append(
            "Runbook missing agent rows: " + ", ".join(sorted(required - runbook_agents))
        )
    if master_agents - required:
        errors.append(
            "MASTER_PLAN has unexpected agent rows: " + ", ".join(sorted(master_agents - required))
        )
    if runbook_agents - required:
        errors.append(
            "Runbook has unexpected agent rows: " + ", ".join(sorted(runbook_agents - required))
        )

    signoff_by_signer = _rows_by_key(signoff_rows, "Signer")
    signoff_signers = set(signoff_by_signer)
    expected_signers = set(REQUIRED_SIGNERS)
    if expected_signers - signoff_signers:
        errors.append(
            "Runbook signoff table missing signers: "
            + ", ".join(sorted(expected_signers - signoff_signers))
        )
    if signoff_signers - expected_signers:
        errors.append(
            "Runbook signoff table has unexpected signers: "
            + ", ".join(sorted(signoff_signers - expected_signers))
        )

    for agent in sorted(required & master_agents & runbook_agents):
        master_row = master_by_agent[agent]
        runbook_row = runbook_by_agent[agent]
        for master_field, runbook_field in (
            ("Lane", "Lane"),
            ("MP scope (authoritative)", "MP scope"),
            ("Worktree", "Worktree"),
            ("Branch", "Branch"),
        ):
            if _normalize(str(master_row.get(master_field, ""))) != _normalize(
                str(runbook_row.get(runbook_field, ""))
            ):
                errors.append(
                    f"{agent} mismatch: MASTER_PLAN {master_field!r} != runbook {runbook_field!r}."
                )

        status = _normalize(str(master_row.get("Status", ""))).lower()
        if status not in ALLOWED_MASTER_STATUSES:
            errors.append(
                f"{agent} has invalid MASTER_PLAN status {status!r}; "
                f"allowed={sorted(ALLOWED_MASTER_STATUSES)}"
            )

        last_update = _normalize(str(master_row.get("Last update (UTC)", "")))
        if not UTC_Z_PATTERN.match(last_update):
            errors.append(
                f"{agent} has invalid Last update (UTC) value {last_update!r}; "
                "expected YYYY-MM-DDTHH:MM:SSZ."
            )

        if status != "planned":
            branch = _normalize(str(master_row.get("Branch", "")))
            matches = [row for row in ledger_rows if _ledger_row_matches_agent(row, agent, branch)]
            if not matches:
                errors.append(
                    f"{agent} status is {status!r} but runbook ledger has no matching entries."
                )

    # Lane lock guard: each agent lane must keep unique branch/worktree in both tables.
    for field in ("Branch", "Worktree"):
        for table_name, mapping in (
            ("MASTER_PLAN", master_by_agent),
            ("runbook", runbook_by_agent),
        ):
            seen: dict[str, list[str]] = {}
            for agent in sorted(required & set(mapping)):
                value = _normalize(str(mapping[agent].get(field, "")))
                if value:
                    seen.setdefault(value, []).append(agent)
            duplicates = {value: owners for value, owners in seen.items() if len(owners) > 1}
            for value, owners in sorted(duplicates.items()):
                errors.append(
                    f"{table_name} lane lock violation: {field} {value!r} shared by {', '.join(owners)}."
                )

    # MP collision guard: overlapping MP scopes require matching handoff token in Notes.
    for left, right in combinations(sorted(required & set(master_by_agent)), 2):
        left_row = master_by_agent[left]
        right_row = master_by_agent[right]
        overlap = sorted(
            _expand_mp_scope_ids(str(left_row.get("MP scope (authoritative)", "")))
            & _expand_mp_scope_ids(str(right_row.get("MP scope (authoritative)", "")))
        )
        if not overlap:
            continue
        left_token = _handoff_token(str(left_row.get("Notes", "")) or "")
        right_token = _handoff_token(str(right_row.get("Notes", "")) or "")
        if not left_token and not right_token:
            errors.append(
                f"MP collision requires handoff token: {left} and {right} overlap on {', '.join(overlap[:5])}."
            )
        elif left_token and right_token and left_token != right_token:
            errors.append(
                f"Handoff token mismatch for MP collision: {left}={left_token}, {right}={right_token}."
            )

    instruction_ids: set[str] = set()
    for row in instruction_rows:
        instruction_id = _normalize(str(row.get("Instruction ID", "")))
        target = _normalize(str(row.get("To", ""))).upper()
        due_utc = _normalize(str(row.get("Due (UTC)", "")))
        ack_token = _normalize(str(row.get("Ack token", "")))
        ack_utc = _normalize(str(row.get("Ack UTC", "")))
        status = _normalize(str(row.get("Status", ""))).lower()

        if not instruction_id:
            errors.append("Instruction row missing Instruction ID.")
        elif instruction_id in instruction_ids:
            errors.append(f"Duplicate Instruction ID: {instruction_id}.")
        else:
            instruction_ids.add(instruction_id)

        if target not in required:
            errors.append(f"Instruction {instruction_id or '<missing>'} has invalid target {target!r}.")
        if due_utc and due_utc.lower() != "pending" and not UTC_Z_PATTERN.match(due_utc):
            errors.append(
                f"Instruction {instruction_id or '<missing>'} has invalid Due (UTC) {due_utc!r}."
            )
        if status not in ALLOWED_INSTRUCTION_STATUSES:
            errors.append(
                f"Instruction {instruction_id or '<missing>'} has invalid status {status!r}; "
                f"allowed={sorted(ALLOWED_INSTRUCTION_STATUSES)}"
            )

        acked = bool(ack_token and ack_token.lower() != "pending")
        if status in {"acked", "completed"} and not acked:
            errors.append(
                f"Instruction {instruction_id or '<missing>'} status {status!r} requires Ack token."
            )
        if acked and not ack_token.upper().startswith("ACK-"):
            warnings.append(
                f"Instruction {instruction_id or '<missing>'} Ack token should start with ACK-."
            )
        if acked and (not ack_utc or ack_utc.lower() == "pending" or not UTC_Z_PATTERN.match(ack_utc)):
            errors.append(
                f"Instruction {instruction_id or '<missing>'} Ack UTC must be populated in UTC timestamp form."
            )

    unknown_ledger_statuses = sorted(
        {
            _normalize(str(row.get("Status", ""))).lower()
            for row in ledger_rows
            if _normalize(str(row.get("Status", ""))).lower() not in ALLOWED_LEDGER_STATUSES
        }
    )
    if unknown_ledger_statuses:
        warnings.append(
            "Runbook ledger includes unknown statuses: " + ", ".join(unknown_ledger_statuses)
        )

    cycle_complete_for_signoff = bool(required & master_agents) and all(
        _normalize(str(master_by_agent[agent].get("Status", ""))).lower() == "merged"
        for agent in sorted(required & master_agents)
    )
    if cycle_complete_for_signoff:
        for signer in REQUIRED_SIGNERS:
            row = signoff_by_signer.get(signer)
            if not row:
                continue
            signoff_date = _normalize(str(row.get("Date (UTC)", "")))
            signoff_result = _normalize(str(row.get("Result", ""))).lower()
            isolation = _normalize(str(row.get("Isolation verified", ""))).lower()
            bundle_ref = _normalize(str(row.get("Bundle reference", "")))
            signature = _normalize(str(row.get("Signature", "")))
            if not signoff_date or signoff_date == "pending" or not SIGNOFF_DATE_PATTERN.match(signoff_date):
                errors.append(
                    f"{signer} signoff Date (UTC) must be populated with YYYY-MM-DD or full UTC timestamp."
                )
            if signoff_result != "pass":
                errors.append(f"{signer} signoff Result must be `pass` after cycle completion.")
            if isolation != "yes":
                errors.append(
                    f"{signer} signoff Isolation verified must be `yes` after cycle completion."
                )
            if not bundle_ref or bundle_ref == "pending":
                errors.append(f"{signer} signoff Bundle reference must be populated.")
            if not signature or signature.lower() == "pending":
                errors.append(f"{signer} signoff Signature must be populated.")

    return {
        "command": "check_multi_agent_sync",
        "ok": not errors,
        "master_plan_path": str(MASTER_PLAN_PATH.relative_to(REPO_ROOT)),
        "runbook_path": str(RUNBOOK_PATH.relative_to(REPO_ROOT)),
        "required_agents": list(REQUIRED_AGENTS),
        "master_agents": sorted(master_agents),
        "runbook_agents": sorted(runbook_agents),
        "instruction_entries": len(instruction_rows),
        "ledger_entries": len(ledger_rows),
        "signoff_signers": sorted(signoff_signers),
        "cycle_complete_for_signoff": cycle_complete_for_signoff,
        "errors": errors,
        "warnings": warnings,
    }


def _render_md(report: dict) -> str:
    lines = ["# check_multi_agent_sync", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    if "error" in report:
        lines.append(f"- error: {report['error']}")
        return "\n".join(lines)
    lines.append(f"- master_plan: {report['master_plan_path']}")
    lines.append(f"- runbook: {report['runbook_path']}")
    lines.append("- required_agents: " + ", ".join(report.get("required_agents", [])))
    lines.append("- master_agents: " + (", ".join(report.get("master_agents", [])) or "none"))
    lines.append("- runbook_agents: " + (", ".join(report.get("runbook_agents", [])) or "none"))
    lines.append(f"- instruction_entries: {report.get('instruction_entries', 0)}")
    lines.append(f"- ledger_entries: {report.get('ledger_entries', 0)}")
    lines.append("- signoff_signers: " + (", ".join(report.get("signoff_signers", [])) or "none"))
    lines.append(f"- cycle_complete_for_signoff: {report.get('cycle_complete_for_signoff', False)}")
    lines.append("- warnings: " + (", ".join(report.get("warnings", [])) if report.get("warnings") else "none"))
    lines.append("- errors: " + (", ".join(report.get("errors", [])) if report.get("errors") else "none"))
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = _build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
