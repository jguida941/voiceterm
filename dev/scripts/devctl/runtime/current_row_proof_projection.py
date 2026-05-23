"""Markdown projection and drift checks for current-row proof mode."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from .current_row_proof_config import (
    CHECKBOX_BY_STATUS,
    DEFAULT_PROJECTION_PATH,
    PROJECTION_CONTRACT_ID,
)
from .current_row_proof_requirements import failure
from .current_row_proof_utils import ProofUtils as U


def render_current_row_projection(report: Mapping[str, object]) -> str:
    """Render a user-visible markdown projection from typed proof state."""
    state_hash = str(report.get("typed_state_hash") or typed_state_hash(report))
    lines = [
        "<!-- GENERATED_CURRENT_ROW_EXECUTION_PROJECTION",
        f"contract_id={PROJECTION_CONTRACT_ID}",
        "projection_only=true",
        f"typed_state_hash={state_hash}",
        "-->",
        "",
        "# Current Row Execution Projection",
        "",
        "Generated projection only. This markdown is not durable authority.",
        "",
        f"- row_id: `{report.get('row_id', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- plan_row_status: `{report.get('current_plan_row_status', '')}`",
        f"- source_snapshot_id: `{report.get('source_snapshot_id', '')}`",
        f"- source_hash: `{report.get('source_hash', '')}`",
        f"- ingestion_receipt_id: `{report.get('ingestion_receipt_id', '')}`",
        f"- current_bounded_next_command: `{report.get('current_bounded_next_command', '')}`",
        f"- final_gate_status: `{U.status(report.get('final_gate_status'))}`",
        f"- feature_proof_receipt_status: `{U.status(report.get('feature_proof_receipt_status'))}`",
        f"- last_updated_timestamp: `{report.get('last_updated_timestamp', '')}`",
        "",
        "## Proof Matrix",
        "",
        "| ID | Check | Status | Command | Proof ref |",
        "|---|---:|---|---|---|",
    ]
    for requirement in U.sequence_of_mappings(report.get("proof_requirements")):
        status = str(requirement.get("status") or "missing")
        checkbox = CHECKBOX_BY_STATUS.get(status, "[ ]")
        lines.append(
            "| {id} | {checkbox} | `{status}` | `{command}` | `{proof}` |".format(
                id=U.cell(requirement.get("id")),
                checkbox=checkbox,
                status=U.cell(status),
                command=U.cell(requirement.get("command")),
                proof=U.cell(requirement.get("proof_ref")),
            )
        )
    lines.extend(["", "## Active Packet Refs", ""])
    packet_refs = tuple(U.strings(report.get("active_packet_refs")))
    lines.extend(f"- `{packet_ref}`" for packet_ref in packet_refs) if packet_refs else lines.append("- none")
    lines.extend(["", "## Failures", ""])
    failures = tuple(U.sequence_of_mappings(report.get("failures")))
    if failures:
        for row in failures:
            lines.append(f"- `{U.cell(row.get('reason'))}`: {U.cell(row.get('detail'))}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def validate_projection_sync(
    report: Mapping[str, object],
    *,
    projection_path: Path = DEFAULT_PROJECTION_PATH,
) -> dict[str, object]:
    expected = render_current_row_projection(report)
    try:
        actual = projection_path.read_text(encoding="utf-8")
    except OSError:
        actual = ""
    typed_statuses = {
        str(row.get("id")): str(row.get("status"))
        for row in U.sequence_of_mappings(report.get("proof_requirements"))
    }
    green_without_proof: list[str] = []
    proof_missing_in_projection: list[str] = []
    for line in actual.splitlines():
        if "| [x] |" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and typed_statuses.get(cells[0]) != "passed":
            green_without_proof.append(cells[0])
    for requirement_id, status in typed_statuses.items():
        if status == "passed" and f"| {requirement_id} | [x] |" not in actual:
            proof_missing_in_projection.append(requirement_id)

    projection_claims_authority = bool(actual) and (
        "durable authority" in actual.lower()
        and "not durable authority" not in actual.lower()
    )
    failures: list[dict[str, str]] = []
    if not actual:
        failures.append(
            failure(
                "projection_missing",
                f"Generated projection is missing: {U.repo_relative(projection_path)}",
                "Run render-current-row-projection --write.",
                str(U.repo_relative(projection_path)),
            )
        )
    elif actual != expected:
        failures.append(
            failure(
                "projection_stale_or_manual_edit",
                "Generated projection content does not match typed state rendering.",
                "Regenerate the projection from typed state; do not edit it by hand.",
                str(U.repo_relative(projection_path)),
            )
        )
    if green_without_proof:
        failures.append(
            failure(
                "projection_claims_green_without_typed_proof",
                "Projection has [x] rows without matching typed proof: "
                + ", ".join(sorted(set(green_without_proof))),
                "Regenerate the projection after the typed proof bundle is fixed.",
                str(U.repo_relative(projection_path)),
            )
        )
    if proof_missing_in_projection:
        failures.append(
            failure(
                "projection_missing_existing_typed_proof",
                "Typed proof exists but projection is stale for: "
                + ", ".join(sorted(set(proof_missing_in_projection))),
                "Regenerate the projection from typed state.",
                str(U.repo_relative(projection_path)),
            )
        )
    if projection_claims_authority:
        failures.append(
            failure(
                "projection_claims_authority",
                "Projection text claims durable authority.",
                "Projection output must state it is not authority.",
                str(U.repo_relative(projection_path)),
            )
        )
    return {
        "projection_path": str(U.repo_relative(projection_path)),
        "projection_expected_hash": U.sha256_text(expected),
        "projection_actual_hash": U.sha256_text(actual) if actual else "",
        "projection_in_sync": bool(actual) and actual == expected,
        "projection_green_without_typed_proof_count": len(set(green_without_proof)),
        "projection_typed_proof_missing_count": len(set(proof_missing_in_projection)),
        "projection_claims_authority": projection_claims_authority,
        "failures": failures,
    }


def typed_state_hash(report: Mapping[str, object]) -> str:
    stable = {
        key: value
        for key, value in report.items()
        if key not in {"timestamp", "typed_state_hash"}
    }
    return "sha256:" + hashlib.sha256(
        json.dumps(stable, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()
