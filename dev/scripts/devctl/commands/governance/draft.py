"""devctl governance-draft command implementation."""

from __future__ import annotations

from pathlib import Path

from ...config import REPO_ROOT
from ...governance.draft import render_governance_draft_markdown, scan_repo_governance
from .common import emit_governance_command_output, render_governance_value_error


def run(args) -> int:
    """Scan the repo and emit a ProjectGovernance draft payload."""
    repo_root = getattr(args, "repo_root", None) or REPO_ROOT
    policy_path = getattr(args, "quality_policy", None)

    try:
        gov = scan_repo_governance(Path(repo_root), policy_path=policy_path)
    except ValueError as exc:
        return render_governance_value_error(exc)

    payload = gov.to_dict()
    md = render_governance_draft_markdown(gov)
    return emit_governance_command_output(
        args,
        command="governance-draft",
        json_payload=payload,
        markdown_output=md,
    )
