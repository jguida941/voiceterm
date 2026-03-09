"""Repo-visible operator decision artifact writers."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

from .models import ApprovalRequest, OperatorDecisionArtifact, utc_timestamp

DEFAULT_OPERATOR_DECISION_ROOT = "dev/reports/review_channel/operator_decisions"
OPERATOR_DECISION_TYPED_MODE = "wrapper_artifact_command"
OPERATOR_DECISION_REASON = "operator_decision_recorded"
_DIRECT_DEVCTL_MESSAGE = (
    "Direct devctl review-channel ack|apply|dismiss is not available yet."
)


def record_operator_decision(
    repo_root: Path,
    *,
    approval: ApprovalRequest,
    decision: str,
    note: str = "",
    decision_root_rel: str = DEFAULT_OPERATOR_DECISION_ROOT,
) -> OperatorDecisionArtifact:
    """Write one repo-visible operator decision artifact and refresh latest files."""
    normalized_decision = _normalize_decision(decision)

    timestamp = utc_timestamp()
    safe_packet_id = approval.packet_id.replace("/", "-")
    decision_root = repo_root / decision_root_rel
    decision_root.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": 1,
        "timestamp_utc": timestamp,
        "source": "operator_console",
        "decision": normalized_decision,
        "packet_id": approval.packet_id,
        "from_agent": approval.from_agent,
        "to_agent": approval.to_agent,
        "summary": approval.summary,
        "requested_action": approval.requested_action,
        "policy_hint": approval.policy_hint,
        "note": note.strip(),
        "status": approval.status,
        "evidence_refs": list(approval.evidence_refs),
    }

    stem = f"{timestamp.replace(':', '').replace('-', '')}-{safe_packet_id}-{normalized_decision}"
    json_path = decision_root / f"{stem}.json"
    markdown_path = decision_root / f"{stem}.md"
    latest_json_path = decision_root / "latest.json"
    latest_markdown_path = decision_root / "latest.md"

    json_text = json.dumps(payload, indent=2)
    markdown_text = _render_operator_decision_markdown(payload)
    _atomic_write_text(json_path, json_text)
    _atomic_write_text(markdown_path, markdown_text)
    _atomic_write_text(latest_json_path, json_text)
    _atomic_write_text(latest_markdown_path, markdown_text)

    return OperatorDecisionArtifact(
        json_path=str(json_path.resolve()),
        markdown_path=str(markdown_path.resolve()),
        latest_json_path=str(latest_json_path.resolve()),
        latest_markdown_path=str(latest_markdown_path.resolve()),
    )


def build_operator_decision_report(
    *,
    approval: ApprovalRequest,
    decision: str,
    note: str,
    artifact: OperatorDecisionArtifact,
) -> dict[str, object]:
    """Build the typed command report returned to the desktop shell."""
    normalized_decision = _normalize_decision(decision)
    return {
        "ok": True,
        "reason": OPERATOR_DECISION_REASON,
        "message": (
            f"Recorded operator {normalized_decision} artifact for {approval.packet_id} "
            f"through the typed wrapper command. {_DIRECT_DEVCTL_MESSAGE}"
        ),
        "decision": normalized_decision,
        "packet_id": approval.packet_id,
        "from_agent": approval.from_agent,
        "to_agent": approval.to_agent,
        "requested_action": approval.requested_action,
        "note_present": bool(note.strip()),
        "typed_action_mode": OPERATOR_DECISION_TYPED_MODE,
        "typed_action_available": True,
        "devctl_review_channel_action_available": False,
        "artifact": {
            "json_path": artifact.json_path,
            "markdown_path": artifact.markdown_path,
            "latest_json_path": artifact.latest_json_path,
            "latest_markdown_path": artifact.latest_markdown_path,
        },
    }


def build_operator_decision_error_report(
    *,
    message: str,
    decision: str | None = None,
    packet_id: str | None = None,
) -> dict[str, object]:
    """Build a structured failure payload for invalid CLI input."""
    report: dict[str, object] = {
        "ok": False,
        "reason": "operator_decision_failed",
        "message": message,
        "typed_action_mode": OPERATOR_DECISION_TYPED_MODE,
        "typed_action_available": True,
        "devctl_review_channel_action_available": False,
    }
    if decision is not None:
        report["decision"] = decision
    if packet_id is not None:
        report["packet_id"] = packet_id
    return report


def render_operator_decision_report(
    report: dict[str, object],
    *,
    output_format: str,
) -> str:
    """Render an operator-decision report in JSON or markdown."""
    if output_format == "json":
        return json.dumps(report, indent=2)
    return _render_operator_decision_result_markdown(report)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint used by the desktop shell's typed approval path."""
    parser = argparse.ArgumentParser(
        description=(
            "Record a repo-visible operator approval/deny artifact through a "
            "typed wrapper command."
        )
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--decision", choices=["approve", "deny"], required=True)
    parser.add_argument("--approval-json", required=True)
    parser.add_argument("--note", default="")
    parser.add_argument("--format", choices=["json", "md"], default="md")
    args = parser.parse_args(list(argv) if argv is not None else None)

    packet_id: str | None = None
    try:
        approval_payload = json.loads(args.approval_json)
        approval = approval_request_from_payload(approval_payload)
        packet_id = approval.packet_id
        artifact = record_operator_decision(
            Path(args.repo_root).resolve(),
            approval=approval,
            decision=args.decision,
            note=args.note,
        )
        report = build_operator_decision_report(
            approval=approval,
            decision=args.decision,
            note=args.note,
            artifact=artifact,
        )
        print(render_operator_decision_report(report, output_format=args.format))
        return 0
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        report = build_operator_decision_error_report(
            message=str(exc),
            decision=args.decision,
            packet_id=packet_id,
        )
        print(render_operator_decision_report(report, output_format=args.format))
        return 1


def _atomic_write_text(target: Path, text: str) -> None:
    """Write *text* to *target* atomically via temp-file + rename."""
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(target.parent),
            prefix=f".{target.name}.",
            suffix=".tmp",
        )
        try:
            os.write(fd, text.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp_path, str(target))
    except OSError:
        target.write_text(text, encoding="utf-8")


def _render_operator_decision_markdown(payload: dict[str, object]) -> str:
    lines = ["# Operator Decision", ""]
    for key in (
        "timestamp_utc",
        "source",
        "decision",
        "packet_id",
        "from_agent",
        "to_agent",
        "summary",
        "requested_action",
        "policy_hint",
        "status",
    ):
        lines.append(f"- {key}: {payload[key]}")
    note = str(payload.get("note", "")).strip()
    if note:
        lines.append("")
        lines.append("## Note")
        lines.append(note)
    evidence_refs = payload.get("evidence_refs")
    if isinstance(evidence_refs, list) and evidence_refs:
        lines.append("")
        lines.append("## Evidence Refs")
        for item in evidence_refs:
            lines.append(f"- {item}")
    return "\n".join(lines)


def approval_request_from_payload(payload: object) -> ApprovalRequest:
    """Convert a JSON object into an ApprovalRequest."""
    if not isinstance(payload, dict):
        raise ValueError("approval payload must be a JSON object")

    required_keys = (
        "packet_id",
        "from_agent",
        "to_agent",
        "summary",
        "body",
        "policy_hint",
        "requested_action",
        "status",
    )
    missing = [key for key in required_keys if key not in payload]
    if missing:
        missing_keys = ", ".join(sorted(missing))
        raise ValueError(f"approval payload missing required keys: {missing_keys}")

    evidence_refs_raw = payload.get("evidence_refs", ())
    if isinstance(evidence_refs_raw, list):
        evidence_refs = tuple(str(item) for item in evidence_refs_raw)
    elif isinstance(evidence_refs_raw, tuple):
        evidence_refs = tuple(str(item) for item in evidence_refs_raw)
    else:
        raise ValueError("approval payload field `evidence_refs` must be a list")

    return ApprovalRequest(
        packet_id=str(payload["packet_id"]),
        from_agent=str(payload["from_agent"]),
        to_agent=str(payload["to_agent"]),
        summary=str(payload["summary"]),
        body=str(payload["body"]),
        policy_hint=str(payload["policy_hint"]),
        requested_action=str(payload["requested_action"]),
        status=str(payload["status"]),
        evidence_refs=evidence_refs,
    )


def _normalize_decision(decision: str) -> str:
    normalized_decision = decision.strip().lower()
    if normalized_decision not in {"approve", "deny"}:
        raise ValueError("decision must be `approve` or `deny`")
    return normalized_decision


def _render_operator_decision_result_markdown(report: dict[str, Any]) -> str:
    lines = ["# Operator Decision Result", ""]
    for key in (
        "ok",
        "reason",
        "decision",
        "packet_id",
        "typed_action_mode",
        "typed_action_available",
        "devctl_review_channel_action_available",
    ):
        if key in report:
            lines.append(f"- {key}: {report[key]}")

    message = str(report.get("message", "")).strip()
    if message:
        lines.append("")
        lines.append("## Message")
        lines.append(message)

    artifact = report.get("artifact")
    if isinstance(artifact, dict) and artifact:
        lines.append("")
        lines.append("## Artifact Paths")
        for key in (
            "json_path",
            "markdown_path",
            "latest_json_path",
            "latest_markdown_path",
        ):
            value = artifact.get(key)
            if isinstance(value, str) and value:
                lines.append(f"- {key}: {value}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
