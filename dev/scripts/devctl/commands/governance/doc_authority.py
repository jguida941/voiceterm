"""devctl doc-authority command implementation."""

from __future__ import annotations

from pathlib import Path

from ...governance.doc_authority import build_doc_authority_report, render_doc_authority_md
from .common import emit_governance_command_output


def run(args) -> int:
    """Scan governed docs and emit a doc-authority registry report."""
    repo_root = Path(getattr(args, "repo_path", None) or ".").resolve()
    policy_path = getattr(args, "quality_policy", None)

    report = build_doc_authority_report(repo_root, policy_path=policy_path)
    payload = report.to_dict()
    md = render_doc_authority_md(report)

    return emit_governance_command_output(
        args,
        command="doc-authority",
        json_payload=payload,
        markdown_output=md,
    )
