"""Probe artifact readers for remediation guidance."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Mapping

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.repo_packs import active_path_config
from dev.scripts.devctl.runtime.finding_contracts import REVIEW_TARGETS_CONTRACT_ID

DEFAULT_PROBE_REPORT_ROOT = Path(active_path_config().probe_report_output_root_rel)
_SUMMARY_PATH = Path("latest") / "summary.json"


def resolve_probe_report_root(report_root: str | Path | None = None) -> Path:
    if report_root is not None:
        return Path(report_root)
    env_root = os.environ.get("DEVCTL_PROBE_REPORT_ROOT", "").strip()
    if env_root:
        return Path(env_root)
    env_root = os.environ.get("RALPH_PROBE_REPORT_ROOT", "").strip()
    if env_root:
        return Path(env_root)
    return REPO_ROOT / DEFAULT_PROBE_REPORT_ROOT


def _read_probe_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[ralph-ai-fix] failed to read probe artifact {path}: {exc}", file=sys.stderr)
        return None
    return payload if isinstance(payload, dict) else None


def _decision_packet_key(entry: Mapping[str, object]) -> tuple[str, str, str, str]:
    return (
        str(entry.get("finding_id") or "").strip(),
        str(entry.get("file_path") or entry.get("file") or "").strip(),
        str(entry.get("symbol") or "").strip(),
        str(entry.get("check_id") or entry.get("probe") or "").strip(),
    )


def _load_decision_packets(root: Path) -> dict[tuple[str, str, str, str], dict[str, object]]:
    summary = _read_probe_json(root / _SUMMARY_PATH)
    if not isinstance(summary, dict):
        return {}
    rows = summary.get("decision_packets")
    if not isinstance(rows, list):
        return {}
    packets: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        packets[_decision_packet_key(row)] = row
    return packets


def _guidance_entry_from_finding(
    finding: dict,
    *,
    file_path: str = "",
    decision_packets: Mapping[tuple[str, str, str, str], dict[str, object]] | None = None,
) -> dict[str, object] | None:
    ai_instruction = str(finding.get("ai_instruction") or "").strip()
    if not ai_instruction:
        return None
    resolved_path = str(finding.get("file_path") or finding.get("file") or file_path or "").strip()
    entry: dict[str, object] = {
        "finding_id": str(finding.get("finding_id") or "").strip(),
        "file_path": resolved_path,
        "symbol": str(finding.get("symbol") or "").strip(),
        "probe": str(finding.get("check_id") or finding.get("probe") or "").strip(),
        "severity": str(finding.get("severity") or "medium").strip(),
        "ai_instruction": ai_instruction,
        "line": finding.get("line"),
        "end_line": finding.get("end_line"),
    }
    if decision_packets:
        decision_packet = decision_packets.get(_decision_packet_key(entry))
        if isinstance(decision_packet, dict):
            decision_mode = str(decision_packet.get("decision_mode") or "").strip()
            if decision_mode:
                entry["decision_mode"] = decision_mode
            rationale = str(decision_packet.get("rationale") or "").strip()
            if rationale:
                entry["decision_rationale"] = rationale
            precedent = str(decision_packet.get("precedent") or "").strip()
            if precedent:
                entry["precedent"] = precedent
            invariants = decision_packet.get("invariants")
            if isinstance(invariants, list) and invariants:
                entry["invariants"] = [str(item).strip() for item in invariants if str(item).strip()]
            validation_plan = decision_packet.get("validation_plan")
            if isinstance(validation_plan, list) and validation_plan:
                entry["validation_plan"] = [
                    str(item).strip() for item in validation_plan if str(item).strip()
                ]
    return entry


def guidance_ref(entry: Mapping[str, object]) -> str:
    """Build the canonical stable guidance reference used across consumers."""
    file_path = str(entry.get("file_path") or "").strip()
    symbol = str(entry.get("symbol") or "").strip()
    probe = str(entry.get("probe") or "").strip()
    line = entry.get("line")
    location = file_path or symbol or "unknown"
    if isinstance(line, int) and line > 0:
        location = f"{location}:{line}"
    return f"{probe}@{location}" if probe else location


def _entries_from_rows(
    rows: object,
    *,
    file_path: str = "",
    decision_packets: Mapping[tuple[str, str, str, str], dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    if not isinstance(rows, list):
        return []
    entries: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        entry = _guidance_entry_from_finding(
            row,
            file_path=file_path,
            decision_packets=decision_packets,
        )
        if entry is not None:
            entries.append(entry)
    return entries


def _load_review_target_entries(root: Path) -> list[dict[str, object]]:
    review_targets = _read_probe_json(root / "review_targets.json")
    if not isinstance(review_targets, dict):
        return []
    contract_id = str(review_targets.get("contract_id") or "").strip()
    if contract_id and contract_id != REVIEW_TARGETS_CONTRACT_ID:
        print(
            f"[ralph-ai-fix] ignoring non-ReviewTargets artifact at {root / 'review_targets.json'}",
            file=sys.stderr,
        )
        return []
    return _entries_from_rows(
        review_targets.get("findings"),
        decision_packets=_load_decision_packets(root),
    )


def load_probe_entries(report_root: str | Path | None = None) -> list[dict[str, object]]:
    root = resolve_probe_report_root(report_root)
    return _load_review_target_entries(root)
