"""`devctl integrations-import` command implementation."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from ..common import confirm_or_abort, pipe_output, write_output
from ..config import REPO_ROOT
from ..integration_import_core import (
    append_audit_log,
    collect_mapping_plan,
    is_relative_to,
    list_profiles_payload,
    relative_or_str,
    render_import_md,
    render_profiles_md,
    run_git_capture,
)
from ..integration_federation_policy import (
    federation_allowed_destination_roots,
    federation_audit_log_path,
    federation_max_files,
    federation_sources,
    load_federation_policy,
    source_repo_path,
)


def run(args) -> int:
    """Import allowlisted files from pinned integration sources."""
    errors: list[str] = []
    warnings: list[str] = []
    repo_root = REPO_ROOT.resolve()

    policy_section = load_federation_policy(repo_root)
    sources_cfg = federation_sources(policy_section)
    if not sources_cfg:
        errors.append("No integration_federation.sources configured in policy.")

    audit_log_path = federation_audit_log_path(repo_root, policy_section)
    if args.list_profiles:
        payload = {
            "command": "integrations-import",
            "timestamp": datetime.now().isoformat(),
            "ok": len(errors) == 0,
            "mode": "list-profiles",
            "audit_log": relative_or_str(audit_log_path, repo_root),
            "warnings": warnings,
            "errors": errors,
            **list_profiles_payload(sources_cfg),
        }
        if args.format == "json":
            output = json.dumps(payload, indent=2)
        else:
            output = render_profiles_md(payload)
        write_output(output, args.output)
        if args.pipe_command:
            pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
            if pipe_code != 0:
                return pipe_code
        return 0 if payload["ok"] else 1

    source_name = str(args.source or "").strip()
    profile_name = str(args.profile or "").strip()
    if not source_name:
        errors.append("--source is required unless --list-profiles is used.")
    if not profile_name:
        errors.append("--profile is required unless --list-profiles is used.")

    source_cfg = sources_cfg.get(source_name) if source_name else None
    if source_name and not isinstance(source_cfg, dict):
        errors.append(f"Unknown integration source: {source_name}")
    profiles_cfg = source_cfg.get("profiles") if isinstance(source_cfg, dict) else None
    profile_cfg = profiles_cfg.get(profile_name) if isinstance(profiles_cfg, dict) else None
    if source_name and profile_name and not isinstance(profile_cfg, dict):
        errors.append(f"Unknown profile '{profile_name}' for source '{source_name}'.")

    source_root = source_repo_path(repo_root, source_cfg) if isinstance(source_cfg, dict) else None
    if source_root is None:
        if source_cfg is not None:
            errors.append(f"Source '{source_name}' is missing required `path` in policy.")
    elif not source_root.exists():
        errors.append(f"Source path does not exist: {relative_or_str(source_root, repo_root)}")

    policy_cap = federation_max_files(policy_section)
    if args.max_files is not None and args.max_files <= 0:
        errors.append("--max-files must be > 0 when provided.")
    if args.max_files is not None and args.max_files > policy_cap:
        errors.append(
            f"--max-files={args.max_files} exceeds policy cap ({policy_cap}) for integrations-import."
        )
    effective_cap = args.max_files if isinstance(args.max_files, int) and args.max_files > 0 else policy_cap

    allowed_dest_roots = federation_allowed_destination_roots(repo_root, policy_section)

    plan_pairs: list[tuple[Path, Path]] = []
    mapping_results: list[dict[str, Any]] = []
    if not errors and isinstance(profile_cfg, dict) and source_root is not None:
        mappings = profile_cfg.get("mappings")
        if not isinstance(mappings, list) or not mappings:
            errors.append(f"Profile '{profile_name}' has no valid `mappings` entries.")
        else:
            for index, mapping in enumerate(mappings, start=1):
                if not isinstance(mapping, dict):
                    errors.append(f"Profile mapping #{index} is not an object.")
                    continue
                mapping_from = str(mapping.get("from") or "").strip()
                mapping_to = str(mapping.get("to") or "").strip()
                if not mapping_from or not mapping_to:
                    errors.append(f"Profile mapping #{index} requires `from` and `to`.")
                    continue
                pairs, mapping_errors = collect_mapping_plan(
                    repo_root=repo_root,
                    source_root=source_root.resolve(),
                    mapping_from=mapping_from,
                    mapping_to=mapping_to,
                    allowed_dest_roots=allowed_dest_roots,
                )
                plan_pairs.extend(pairs)
                mapping_results.append(
                    {"from": mapping_from, "to": mapping_to, "files": len(pairs)}
                )
                errors.extend(mapping_errors)

    if len(plan_pairs) > effective_cap:
        errors.append(
            f"Import plan includes {len(plan_pairs)} files which exceeds cap {effective_cap}."
        )

    apply_mode = bool(args.apply and not args.dry_run)
    existing_destinations = [destination for _, destination in plan_pairs if destination.exists()]
    if apply_mode and existing_destinations and not args.overwrite:
        errors.append(
            f"{len(existing_destinations)} destination files already exist; re-run with --overwrite to replace."
        )

    planned_files = len(plan_pairs)
    applied_files = 0
    if apply_mode and not errors:
        confirm_or_abort(
            f"Import {planned_files} files for {source_name}/{profile_name}?",
            args.yes,
        )
        for source_file, destination_file in plan_pairs:
            destination_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination_file)
            applied_files += 1

    source_sha = None
    if source_root is not None and source_root.exists():
        code, sha_out, _ = run_git_capture(["rev-parse", "HEAD"], cwd=source_root)
        if code == 0:
            source_sha = sha_out

    mode = "apply" if apply_mode else "preview"
    report = {
        "command": "integrations-import",
        "timestamp": datetime.now().isoformat(),
        "ok": len(errors) == 0,
        "mode": mode,
        "source": source_name or None,
        "profile": profile_name or None,
        "source_path": (
            relative_or_str(source_root, repo_root)
            if isinstance(source_root, Path) and source_root.exists()
            else None
        ),
        "source_sha": source_sha,
        "planned_files": planned_files,
        "applied_files": applied_files,
        "overwrite": bool(args.overwrite),
        "dry_run": bool(args.dry_run),
        "max_files_effective": effective_cap,
        "mapping_results": mapping_results,
        "warnings": warnings,
        "errors": errors,
        "audit_log": relative_or_str(audit_log_path, repo_root),
        "file_sample": [
            relative_or_str(destination, repo_root)
            for _, destination in plan_pairs[:25]
            if is_relative_to(destination, repo_root)
        ],
    }
    append_audit_log(
        audit_log_path,
        {
            "timestamp": report["timestamp"],
            "command": report["command"],
            "mode": report["mode"],
            "source": report["source"],
            "profile": report["profile"],
            "source_sha": report["source_sha"],
            "planned_files": report["planned_files"],
            "applied_files": report["applied_files"],
            "overwrite": report["overwrite"],
            "dry_run": report["dry_run"],
            "ok": report["ok"],
            "error_count": len(report["errors"]),
            "file_sample": report["file_sample"],
        },
    )

    output = json.dumps(report, indent=2) if args.format == "json" else render_import_md(report)
    write_output(output, args.output)
    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return 0 if report["ok"] else 1
