#!/usr/bin/env python3
"""Review probe: suggest concrete module splits for mixed-concern Python files.

This probe composes three bounded signals:
- independent top-level function clusters in the touched file
- local import relationships across the touched Python slice
- latest saved context-graph hotspot ranking

Unlike hard guards, this probe always exits 0 and emits actionable
``risk_hints`` for review tooling.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# Ensure the checks root is on sys.path so sibling modules are importable.
_CHECKS_ROOT = str(Path(__file__).resolve().parent.parent)
if _CHECKS_ROOT not in sys.path:
    sys.path.insert(0, _CHECKS_ROOT)

try:
    from check_bootstrap import (
        REPO_ROOT,
        import_attr,
        import_repo_module,
        resolve_quality_scope_roots,
    )
    from probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
        load_current_text_by_path,
    )
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        import_attr,
        import_repo_module,
        resolve_quality_scope_roots,
    )
    from dev.scripts.checks.probe_support.bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
        load_current_text_by_path,
    )

from code_shape_probes.common import should_scan_python_probe_path

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
is_review_probe_test_path = import_attr(
    "probe_path_filters", "is_review_probe_test_path"
)
build_import_graph = import_attr(
    "python_analysis.cyclic_imports_graph", "build_import_graph"
)
cluster_signals = import_attr("code_shape_support.mixed_concerns", "cluster_signals")
find_function_clusters = import_attr(
    "code_shape_support.mixed_concerns", "find_function_clusters"
)
CLUSTER_THRESHOLD_MEDIUM = import_attr(
    "code_shape_support.mixed_concerns", "CLUSTER_THRESHOLD_MEDIUM"
)
CLUSTER_THRESHOLD_HIGH = import_attr(
    "code_shape_support.mixed_concerns", "CLUSTER_THRESHOLD_HIGH"
)
snapshot_store = import_repo_module(
    "dev.scripts.devctl.context_graph.snapshot_store",
    repo_root=REPO_ROOT,
)

guard = GuardContext(REPO_ROOT)
TARGET_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)
REVIEW_LENS = "design_quality"
_ATTACH_DOCS = [
    "dev/guides/DEVELOPMENT.md#what-checks-protect-us",
    "dev/scripts/README.md#probe-report",
]


@dataclass(frozen=True, slots=True)
class HotspotContext:
    """One bounded context-graph hotspot projection for a source file."""

    temperature: float
    rank: int
    connected_files: tuple[str, ...]


def _load_hotspot_context() -> dict[str, HotspotContext]:
    try:
        snapshot_path = snapshot_store.resolve_context_graph_snapshot_ref(
            "latest",
            repo_root=REPO_ROOT,
        )
        snapshot = snapshot_store.load_context_graph_snapshot(snapshot_path)
    except (OSError, ValueError):
        return {}

    file_by_node_id: dict[str, str] = {}
    temperature_by_file: dict[str, float] = {}
    for node in snapshot.nodes:
        if str(node.get("node_kind") or "") != "source_file":
            continue
        file_path = str(node.get("canonical_pointer_ref") or "").strip()
        node_id = str(node.get("node_id") or "").strip()
        if not file_path or not node_id:
            continue
        file_by_node_id[node_id] = file_path
        temperature_by_file[file_path] = float(node.get("temperature") or 0.0)

    if not file_by_node_id:
        return {}

    neighbors_by_file = {file_path: set() for file_path in temperature_by_file}
    for edge in snapshot.edges:
        source_path = file_by_node_id.get(str(edge.get("source_id") or ""))
        target_path = file_by_node_id.get(str(edge.get("target_id") or ""))
        if not source_path or not target_path or source_path == target_path:
            continue
        neighbors_by_file[source_path].add(target_path)
        neighbors_by_file[target_path].add(source_path)

    ranked_files = sorted(
        temperature_by_file,
        key=lambda file_path: (-temperature_by_file[file_path], file_path),
    )
    hotspot_index: dict[str, HotspotContext] = {}
    for rank, file_path in enumerate(ranked_files, start=1):
        connected_files = tuple(
            sorted(
                neighbors_by_file.get(file_path, ()),
                key=lambda neighbor: (-temperature_by_file.get(neighbor, 0.0), neighbor),
            )[:3]
        )
        hotspot_index[file_path] = HotspotContext(
            temperature=temperature_by_file[file_path],
            rank=rank,
            connected_files=connected_files,
        )
    return hotspot_index


def _reverse_graph(graph: dict[Path, set[Path]]) -> dict[Path, set[Path]]:
    reverse: dict[Path, set[Path]] = {path: set() for path in graph}
    for source_path, targets in graph.items():
        reverse.setdefault(source_path, set())
        for target_path in targets:
            reverse.setdefault(target_path, set()).add(source_path)
    return reverse


def _import_neighbors(
    path: Path,
    *,
    graph: dict[Path, set[Path]],
    reverse_graph: dict[Path, set[Path]],
) -> tuple[str, ...]:
    neighbors = graph.get(path, set()) | reverse_graph.get(path, set())
    return tuple(sorted(neighbor.as_posix() for neighbor in neighbors if neighbor != path)[:3])


def _severity(
    *,
    cluster_count: int,
    import_neighbor_count: int,
    hotspot: HotspotContext | None,
) -> str:
    score = 0
    if cluster_count >= CLUSTER_THRESHOLD_HIGH:
        score += 2
    elif cluster_count >= CLUSTER_THRESHOLD_MEDIUM:
        score += 1
    if import_neighbor_count:
        score += 1
    if hotspot is not None and hotspot.temperature >= 0.75:
        score += 1
    return "high" if score >= 3 else "medium"


def _cluster_plan(path: Path, clusters: list[set[str]]) -> str:
    ordered = sorted(clusters, key=lambda cluster: (-len(cluster), tuple(sorted(cluster))))
    plans: list[str] = []
    for cluster in ordered[:3]:
        seed = sorted(cluster)[0]
        module_name = f"{path.stem}_{seed}.py"
        preview = ", ".join(sorted(cluster)[:3])
        plans.append(f"`{preview}` -> `{module_name}`")
    return "; ".join(plans)


def _ai_instruction(
    *,
    path: Path,
    clusters: list[set[str]],
    import_neighbors: tuple[str, ...],
    hotspot: HotspotContext | None,
) -> str:
    parts = [f"Split `{path.name}` by concern: {_cluster_plan(path, clusters)}."]
    if import_neighbors:
        parts.append(
            "Keep the import-facing seam behind a thin entrypoint for "
            + ", ".join(f"`{neighbor}`" for neighbor in import_neighbors[:2])
            + "."
        )
    if hotspot is not None and hotspot.connected_files:
        parts.append(
            "Start with the hottest cluster first because context-graph rank "
            f"{hotspot.rank} links this file to "
            + ", ".join(f"`{neighbor}`" for neighbor in hotspot.connected_files[:2])
            + "."
        )
    elif hotspot is not None:
        parts.append(
            f"Start with the hottest cluster first because this file is context-graph hotspot #{hotspot.rank}."
        )
    return " ".join(parts)


def _build_risk_hint(
    path: Path,
    *,
    clusters: list[set[str]],
    import_neighbors: tuple[str, ...],
    hotspot: HotspotContext | None,
) -> RiskHint:
    signals = cluster_signals(clusters)
    if import_neighbors:
        signals.append("changed-file import coupling: " + ", ".join(import_neighbors))
    if hotspot is not None:
        signals.append(
            f"context hotspot rank {hotspot.rank} at temperature {hotspot.temperature:.2f}"
        )
        if hotspot.connected_files:
            signals.append(
                "hot graph neighbors: " + ", ".join(hotspot.connected_files[:2])
            )
    return RiskHint(
        file=path.as_posix(),
        symbol=path.stem,
        risk_type="split_advisor",
        severity=_severity(
            cluster_count=len(clusters),
            import_neighbor_count=len(import_neighbors),
            hotspot=hotspot,
        ),
        signals=signals,
        ai_instruction=_ai_instruction(
            path=path,
            clusters=clusters,
            import_neighbors=import_neighbors,
            hotspot=hotspot,
        ),
        review_lens=REVIEW_LENS,
        attach_docs=list(_ATTACH_DOCS),
    )


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_split_advisor")

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, _base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError:
        return emit_probe_report(report, output_format=args.format)

    report.mode = "commit-range" if args.since_ref else "working-tree"
    report.since_ref = args.since_ref
    report.head_ref = args.head_ref
    python_paths = [
        path
        for path in changed_paths
        if should_scan_python_probe_path(
            path,
            target_roots=TARGET_ROOTS,
            is_review_probe_test_path=is_review_probe_test_path,
        )
    ]
    current_text_by_path = load_current_text_by_path(
        changed_paths=python_paths,
        since_ref=args.since_ref,
        head_ref=args.head_ref,
        read_text_from_ref=guard.read_text_from_ref,
        read_text_from_worktree=guard.read_text_from_worktree,
    )
    import_graph = build_import_graph(
        paths=python_paths,
        text_by_path=current_text_by_path,
        target_roots=TARGET_ROOTS,
    )
    reverse_graph = _reverse_graph(import_graph)
    hotspot_index = _load_hotspot_context()
    files_with_hints: set[str] = set()

    for path in python_paths:
        report.files_scanned += 1
        text = current_text_by_path.get(path.as_posix())
        if text is None:
            continue
        clusters = find_function_clusters(text)
        if len(clusters) < CLUSTER_THRESHOLD_MEDIUM:
            continue
        import_neighbors = _import_neighbors(
            path,
            graph=import_graph,
            reverse_graph=reverse_graph,
        )
        hotspot = hotspot_index.get(path.as_posix())
        if not import_neighbors and hotspot is None:
            continue
        files_with_hints.add(path.as_posix())
        report.risk_hints.append(
            _build_risk_hint(
                path,
                clusters=clusters,
                import_neighbors=import_neighbors,
                hotspot=hotspot,
            )
        )

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    sys.exit(main())
