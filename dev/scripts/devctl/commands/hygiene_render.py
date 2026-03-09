"""Markdown rendering helpers for `devctl hygiene`."""

from __future__ import annotations

def render_md(report: dict) -> str:
    """Render the markdown hygiene report."""
    archive = report["archive"]
    adr = report["adr"]
    scripts = report["scripts"]
    publications = report["publications"]
    runtime_processes = report["runtime_processes"]
    reports = report["reports"]
    mutation_badge = report["mutation_badge"]
    readme_presence = report["readme_presence"]
    fix_report = report["fix"]
    lines = ["# devctl hygiene", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- strict_warnings: {report['strict_warnings']}")
    lines.append(f"- errors: {report['error_count']}")
    lines.append(f"- warnings: {report['warning_count']}")
    if report["strict_warnings"]:
        lines.append(f"- warning_fail_count: {report['warning_fail_count']}")
    lines.append("")
    lines.append("## Archive")
    lines.append(f"- entries: {archive['total_entries']}")
    lines.extend(f"- error: {message}" for message in archive["errors"])
    lines.extend(f"- warning: {message}" for message in archive["warnings"])
    lines.append("")
    lines.append("## ADRs")
    lines.append(f"- adrs: {adr['total_adrs']}")
    if adr.get("missing_sequence_ids"):
        lines.append("- missing_sequence_ids: " + ", ".join(adr["missing_sequence_ids"]))
    if adr.get("retired_ids"):
        lines.append("- retired_ids: " + ", ".join(adr["retired_ids"]))
    if adr.get("reserved_ids"):
        lines.append("- reserved_ids: " + ", ".join(adr["reserved_ids"]))
    if adr.get("backlog_master_ids"):
        lines.append("- backlog_master_ids: " + ", ".join(adr["backlog_master_ids"]))
    if adr.get("backlog_autonomy_ids"):
        lines.append(
            "- backlog_autonomy_ids: " + ", ".join(adr["backlog_autonomy_ids"])
        )
    if adr.get("next_pointer_value") or adr.get("next_pointer_expected"):
        lines.append(
            "- next_pointer: "
            + (adr.get("next_pointer_value") or "missing")
            + " (expected "
            + (adr.get("next_pointer_expected") or "unknown")
            + ")"
        )
    lines.extend(f"- error: {message}" for message in adr["errors"])
    lines.extend(f"- warning: {message}" for message in adr["warnings"])
    lines.append("")
    lines.append("## Scripts")
    lines.append(f"- top-level scripts: {len(scripts['top_level_scripts'])}")
    lines.append(f"- check scripts: {len(scripts['check_scripts'])}")
    lines.extend(f"- error: {message}" for message in scripts["errors"])
    lines.extend(f"- warning: {message}" for message in scripts["warnings"])
    lines.append("")
    lines.append("## Publications")
    lines.append(f"- tracked publications: {publications['publication_count']}")
    lines.append(f"- stale publications: {publications['stale_publication_count']}")
    lines.extend(f"- error: {message}" for message in publications["errors"])
    lines.extend(f"- warning: {message}" for message in publications["warnings"])
    lines.extend(f"- note: {message}" for message in publications.get("notices", []))
    if (
        not publications["errors"]
        and not publications["warnings"]
        and not publications.get("notices", [])
    ):
        lines.append("- ok")
    lines.append("")
    lines.append("## Runtime Processes")
    lines.append(
        f"- voiceterm test processes detected: {runtime_processes['total_detected']}"
    )
    lines.extend(f"- error: {message}" for message in runtime_processes["errors"])
    lines.extend(f"- warning: {message}" for message in runtime_processes["warnings"])
    lines.append("")
    lines.append("## Reports")
    lines.append(f"- reports root: {reports['reports_root']}")
    lines.append(f"- reports root exists: {reports['reports_root_exists']}")
    lines.append(f"- managed run dirs: {reports['managed_run_dirs']}")
    lines.append(f"- stale cleanup candidates: {reports['candidate_count']}")
    lines.append(f"- reclaim estimate: {reports['candidate_reclaim_human']}")
    lines.extend(f"- error: {message}" for message in reports["errors"])
    lines.extend(f"- warning: {message}" for message in reports["warnings"])
    lines.append("")
    lines.append("## Mutation Badge")
    lines.extend(f"- error: {message}" for message in mutation_badge["errors"])
    lines.extend(f"- warning: {message}" for message in mutation_badge["warnings"])
    if not mutation_badge["errors"] and not mutation_badge["warnings"]:
        lines.append("- ok")
    lines.append("")
    lines.append("## README Presence")
    lines.extend(f"- error: {message}" for message in readme_presence["errors"])
    lines.extend(f"- warning: {message}" for message in readme_presence["warnings"])
    if not readme_presence["errors"] and not readme_presence["warnings"]:
        lines.append("- ok")
    if fix_report["requested"]:
        lines.append("")
        lines.append("## Fix")
        lines.append(f"- removed_pycache_dirs: {len(fix_report['removed'])}")
        lines.extend(f"- removed: {path}" for path in fix_report["removed"])
        lines.extend(f"- skipped: {path}" for path in fix_report["skipped"])
        lines.extend(f"- error: {path}" for path in fix_report["failed"])
    return "\n".join(lines)
