"""Post-audit helpers for `devctl autonomy-swarm`."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .autonomy_report_helpers import DEFAULT_EVENT_LOG as DEFAULT_AUDIT_EVENT_LOG
from .autonomy_report_helpers import DEFAULT_LIBRARY_ROOT as DEFAULT_AUDIT_LIBRARY_ROOT
from .autonomy_report_helpers import DEFAULT_SOURCE_ROOT as DEFAULT_AUDIT_SOURCE_ROOT
from .autonomy_report_helpers import collect_report as collect_post_audit_report
from .autonomy_report_render import render_markdown as render_post_audit_markdown
from .autonomy_swarm_helpers import slug


def build_post_audit_payload(
    *,
    enabled: bool,
    ok: bool | None = None,
    run_label: str | None = None,
    bundle_dir: str | None = None,
    summary_json: str | None = None,
    summary_md: str | None = None,
    metrics: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "enabled": bool(enabled),
        "ok": ok,
        "run_label": run_label,
        "bundle_dir": bundle_dir,
        "summary_json": summary_json,
        "summary_md": summary_md,
        "metrics": metrics or {},
        "warnings": warnings or [],
        "errors": errors or [],
    }


def run_post_audit_digest(args, run_label: str) -> dict[str, Any]:
    """Run autonomy-report collection and return normalized post-audit metadata."""
    audit_label = slug(
        str(args.audit_run_label or f"{run_label}-digest"),
        fallback=f"{run_label}-digest",
    )
    audit_args = SimpleNamespace(
        source_root=str(args.audit_source_root or DEFAULT_AUDIT_SOURCE_ROOT),
        library_root=str(args.audit_library_root or DEFAULT_AUDIT_LIBRARY_ROOT),
        run_label=audit_label,
        event_log=str(args.audit_event_log or DEFAULT_AUDIT_EVENT_LOG),
        refresh_orchestrate=bool(args.audit_refresh_orchestrate),
        copy_sources=bool(args.audit_copy_sources),
        charts=bool(args.audit_charts),
        format="md",
        output=None,
        json_output=None,
        pipe_command=None,
        pipe_args=None,
    )
    audit_report, bundle_dir, _charts_dir = collect_post_audit_report(audit_args)
    summary_json_path = Path(bundle_dir) / "summary.json"
    summary_md_path = Path(bundle_dir) / "summary.md"
    summary_json_path.write_text(json.dumps(audit_report, indent=2), encoding="utf-8")
    summary_md_path.write_text(
        render_post_audit_markdown(audit_report), encoding="utf-8"
    )
    return build_post_audit_payload(
        enabled=True,
        ok=bool(audit_report.get("ok", False)),
        run_label=audit_label,
        bundle_dir=str(bundle_dir),
        summary_json=str(summary_json_path),
        summary_md=str(summary_md_path),
        metrics=audit_report.get("metrics", {}),
        warnings=audit_report.get("warnings", []),
        errors=audit_report.get("errors", []),
    )
