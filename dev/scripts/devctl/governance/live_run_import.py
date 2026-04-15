"""LIVE_RUN markdown import helpers for governance-import-findings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import get_repo_root
from ..triage.findings_priority import load_accumulated_findings
from .external_findings_log import DEFAULT_CHECK_ID, DEFAULT_SIGNAL_TYPE


def is_live_run_markdown_path(input_path: Path) -> bool:
    """Return True when *input_path* looks like a LIVE_RUN markdown file."""
    return input_path.suffix.lower() in {".md", ".markdown", ".mdown"}


def _override_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_live_run_import_rows(
    *,
    input_path: Path,
    args,
    import_run_id: str,
) -> list[dict[str, Any]]:
    """Convert LIVE_RUN markdown sections into canonical import rows."""
    findings = load_accumulated_findings(input_path)
    if not findings:
        raise ValueError(f"no LIVE_RUN finding sections found in `{input_path}`")

    repo_name = _override_text(getattr(args, "repo_name", None))
    repo_path = _override_text(getattr(args, "repo_path", None))
    if not repo_name and not repo_path:
        repo_root = get_repo_root() or Path.cwd()
        repo_name = repo_root.name
        repo_path = str(repo_root)
    elif not repo_name and repo_path:
        repo_name = Path(repo_path).name or None

    if not repo_name and not repo_path:
        raise ValueError("repo_name or repo_path is required for imported findings")

    check_id = _override_text(getattr(args, "check_id", None)) or DEFAULT_CHECK_ID
    signal_type = _override_text(getattr(args, "signal_type", None)) or DEFAULT_SIGNAL_TYPE
    scan_mode = _override_text(getattr(args, "scan_mode", None)) or "external"
    source_model = _override_text(getattr(args, "source_model", None)) or "live_run_md"
    source_command = _override_text(getattr(args, "source_command", None)) or (
        "governance-import-findings"
    )
    notes = _override_text(getattr(args, "notes", None))

    rows: list[dict[str, Any]] = []
    for index, finding in enumerate(findings, start=1):
        file_path = finding.file_refs[0] if finding.file_refs else ""
        if not file_path:
            raise ValueError(
                f"LIVE_RUN section {finding.qid} in `{input_path}` is missing a file reference"
            )
        rows.append(
            {
                "finding_id": f"{repo_name}:{finding.qid}",
                "repo_name": repo_name,
                "repo_path": repo_path,
                "check_id": check_id,
                "signal_type": signal_type,
                "file_path": file_path,
                "title": finding.heading,
                "summary": finding.summary,
                "evidence": finding.status,
                "severity": finding.severity,
                "source_model": source_model,
                "source_command": source_command,
                "source_artifact": str(input_path),
                "source_row": index,
                "scan_mode": scan_mode,
                "import_run_id": import_run_id,
                "notes": notes or finding.status,
            }
        )
    return rows
