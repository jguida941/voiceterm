"""Safe source loaders for ReviewSnapshot orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..config import REPO_ROOT


def safe_startup_context(repo_root: Path = REPO_ROOT) -> Mapping[str, object]:
    try:
        from .startup_context import build_startup_context

        ctx = build_startup_context()
        return ctx.to_dict()
    except Exception:  # broad-except: allow reason=optional startup context must fail closed to an empty default on fresh or partially configured repos. fallback=return {}
        return {}


def safe_project_governance(repo_root: Path) -> object | None:
    """Load ProjectGovernance via repo-pack scan; None on fresh repos."""
    try:
        from .governance_scan import scan_repo_governance_safely

        return scan_repo_governance_safely(repo_root)
    except Exception:  # broad-except: allow reason=optional governance scan must fail closed to no contract object when discovery is unavailable. fallback=return None
        return None


def safe_governance_report(
    repo_root: Path,
    governance: object | None,
) -> Mapping[str, object]:
    """Load the governance-review report using repo-pack-configured paths."""
    try:
        from ..governance_review.log import build_governance_review_report
    except Exception:  # broad-except: allow reason=governance-report import failure should degrade to an empty projection instead of aborting snapshot rendering. fallback=return {}
        return {}
    log_path = resolve_governance_log_path(repo_root, governance)
    if not log_path.is_file():
        return {}
    try:
        return build_governance_review_report(
            log_path=log_path, max_rows=2000, recent_limit=15
        )
    except Exception:  # broad-except: allow reason=report parsing must fail closed to an empty review summary if the JSONL report is malformed or partial. fallback=return {}
        return {}


def resolve_governance_log_path(
    repo_root: Path, governance: object | None
) -> Path:
    """Resolve the JSONL governance-review log via ProjectGovernance."""
    relative = ""
    if governance is not None:
        artifact_roots = getattr(governance, "artifact_roots", None)
        if artifact_roots is not None:
            relative = str(
                getattr(artifact_roots, "governance_log_root", "") or ""
            ).strip()
    if not relative:
        relative = "dev/reports/governance"
    return repo_root / relative / "finding_reviews.jsonl"


def safe_probe_report() -> Mapping[str, object]:
    try:
        from ..review_probe_report import build_probe_report

        return build_probe_report()
    except Exception:  # broad-except: allow reason=probe reporting must fail closed to an empty summary when the probe artifact path is absent or unreadable. fallback=return {}
        return {}


def safe_context_graph_bootstrap() -> Mapping[str, object]:
    try:
        from ..context_graph.builder import build_context_graph
        from ..context_graph.query import build_bootstrap_context

        graph = build_context_graph()
        return build_bootstrap_context(graph)
    except Exception:  # broad-except: allow reason=context graph bootstrap must fail closed to an empty projection when graph generation is unavailable. fallback=return {}
        return {}


__all__ = [
    "resolve_governance_log_path",
    "safe_context_graph_bootstrap",
    "safe_governance_report",
    "safe_probe_report",
    "safe_project_governance",
    "safe_startup_context",
]
