"""Optional input-source handling for `devctl triage`.

This module owns CIHub probing/ingest plus external issue-file ingestion so
`commands/triage.py` can stay focused on report orchestration.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..common import run_cmd
from ..config import REPO_ROOT
from .bundle import resolve_emit_dir
from .enrich import extract_cihub_issues, extract_issues_from_file
from .support import ingest_cihub_artifacts


def cihub_supports_triage(cihub_bin: str) -> tuple[bool, str]:
    """Detect whether the installed CIHub binary exposes the triage command."""
    try:
        result = subprocess.run(
            [cihub_bin, "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return False, str(exc)

    combined = "\n".join([result.stdout or "", result.stderr or ""])
    match = re.search(r"\{([^}]+)\}", combined)
    if match:
        commands = {part.strip() for part in match.group(1).split(",")}
        return ("triage" in commands), "parsed-help"

    return ("triage" in combined), "fallback-text-search"


def apply_optional_inputs(
    triage_report: dict[str, Any],
    *,
    args: Any,
    owner_map: dict[str, str],
) -> None:
    """Apply optional CIHub and external issue sources to a triage report."""
    emit_dir = resolve_emit_dir(args.cihub_emit_dir)
    explicit_opt_in = bool(getattr(args, "cihub", False))
    cihub_available = shutil.which(args.cihub_bin) is not None
    use_cihub = False
    cihub_warning: str | None = None
    if not args.no_cihub:
        if not cihub_available and not explicit_opt_in:
            cihub_warning = "cihub binary not found; skipping CIHub triage."
        else:
            supports_triage, source = cihub_supports_triage(args.cihub_bin)
            if supports_triage:
                use_cihub = True
            else:
                cihub_warning = "cihub binary does not support `triage`; skipping CIHub triage " f"(probe={source})."

    triage_report["cihub"] = {"enabled": use_cihub, "emit_dir": str(emit_dir)}
    if cihub_warning:
        triage_report["cihub"]["warning"] = cihub_warning
        triage_report["warnings"].append(cihub_warning)
    if use_cihub:
        cihub_env = os.environ.copy()
        cihub_env["CIHUB_EMIT_TRIAGE"] = "1"
        cihub_cmd = [args.cihub_bin, "triage"]
        if args.cihub_run:
            cihub_cmd.extend(["--run", str(args.cihub_run)])
        else:
            cihub_cmd.append("--latest")
        if args.cihub_repo:
            cihub_cmd.extend(["--repo", args.cihub_repo])
        cihub_payload: dict[str, Any] = {
            "step": run_cmd(
                "cihub-triage",
                cihub_cmd,
                cwd=REPO_ROOT,
                env=cihub_env,
                dry_run=args.dry_run,
            )
        }
        cihub_payload.update(ingest_cihub_artifacts(emit_dir))
        triage_report["cihub"].update(cihub_payload)
        step = triage_report["cihub"].get("step", {})
        if isinstance(step, dict) and step.get("returncode") not in (None, 0):
            triage_report["warnings"].append("cihub triage command failed; using local-only signals.")
            triage_report["issues"].append(
                {
                    "category": "infra",
                    "severity": "medium",
                    "owner": owner_map.get("infra", "platform"),
                    "source": "devctl.triage.cihub",
                    "summary": "cihub triage command failed; check cihub version/flags.",
                }
            )
        cihub_issues = extract_cihub_issues(triage_report["cihub"], owner_map)
        triage_report["cihub"]["ingested_issues"] = len(cihub_issues)
        triage_report["issues"].extend(cihub_issues)
    elif not triage_report["cihub"].get("warning"):
        triage_report["cihub"]["warning"] = "cihub triage skipped."

    external_rows: list[dict[str, Any]] = []
    for raw_path in list(getattr(args, "external_issues_file", []) or []):
        source = f"external.{Path(raw_path).name}"
        row: dict[str, Any] = {"path": raw_path, "source": source}
        external_issues, external_error = extract_issues_from_file(
            raw_path,
            source=source,
            owner_map=owner_map,
        )
        if external_error:
            row["error"] = external_error
            triage_report["warnings"].append(f"external issues ingest failed ({raw_path}): {external_error}")
            triage_report["issues"].append(
                {
                    "category": "infra",
                    "severity": "medium",
                    "owner": owner_map.get("infra", "platform"),
                    "source": source,
                    "summary": f"external issues ingest failed for {raw_path}",
                }
            )
        else:
            row["issues"] = len(external_issues)
            triage_report["issues"].extend(external_issues)
        external_rows.append(row)
    triage_report["external_inputs"] = external_rows

    if not args.require_cihub:
        return
    step = triage_report["cihub"].get("step", {})
    step_failed = isinstance(step, dict) and step.get("returncode") not in (None, 0)
    artifacts = triage_report["cihub"].get("artifacts", {})
    missing_artifacts = not isinstance(artifacts, dict) or not artifacts
    if not triage_report["cihub"].get("enabled") or step_failed or missing_artifacts:
        triage_report["cihub"]["warning"] = "cihub triage is required but command/artifacts were not successful."
        triage_report["issues"].append(
            {
                "category": "infra",
                "severity": "high",
                "owner": owner_map.get("infra", "platform"),
                "source": "devctl.triage.cihub",
                "summary": "Required cihub triage command/artifacts unavailable.",
            }
        )
