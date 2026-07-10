"""Support helpers for duplication audit reporting and fallback scanning."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

SHARED_LOGIC_CANDIDATE_EXCLUDES = (
    "**/__pycache__/**",
    "**/tests/**",
    "**/test_*.py",
)
SHARED_HELPER_COMPARE_GLOBS = (
    "dev/scripts/devctl/common.py",
    "dev/scripts/devctl/**/*_support.py",
    "dev/scripts/devctl/**/*_core.py",
    "dev/scripts/devctl/**/*_render.py",
    "dev/scripts/devctl/**/*_parser.py",
    "dev/scripts/devctl/**/*_helpers.py",
    "dev/scripts/checks/**/*_support.py",
    "dev/scripts/checks/**/*_core.py",
    "dev/scripts/checks/**/*_render.py",
    "dev/scripts/checks/**/*_parser.py",
    "dev/scripts/checks/**/*_helpers.py",
    "dev/scripts/checks/rust_guard_common.py",
)
ORCHESTRATION_COMPARE_GLOBS = (
    "dev/scripts/devctl/commands/*.py",
    "dev/scripts/checks/check_*.py",
)
STRING_LITERAL_RE = re.compile(r'(?:"[^"\n]*"|\'[^\'\n]*\')')
NUMBER_LITERAL_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
DECLARATION_NAME_RE = re.compile(
    r"^(?P<prefix>(?:pub\s+)?(?:async\s+)?(?:def|class|fn|struct|enum|trait)\s+)"
    r"[A-Za-z_][A-Za-z0-9_]*"
)
LOCAL_IMPORT_RE = re.compile(
    r"^(?:from\s+(?:\.+|dev\.scripts\.)[A-Za-z0-9_\.]+\s+import\s+.+|"
    r"import\s+dev\.scripts\.[A-Za-z0-9_\.]+)$"
)
ORCHESTRATION_MARKERS = {
    "run-entrypoint": re.compile(r"^def\s+run\s*\(", re.MULTILINE),
    "argparse-parser": re.compile(r"argparse\.ArgumentParser\("),
    "add-argument": re.compile(r"\.add_argument\("),
    "write-output": re.compile(r"\bwrite_output\("),
    "check-script-cmd": re.compile(r"\bcheck_script_cmd\("),
    "run-cmd": re.compile(r"\brun_cmd\("),
    "json-dumps": re.compile(r"\bjson\.dumps\("),
}


def derive_status(
    *,
    errors: list[str],
    warnings: list[str],
    blocked_by_tooling: bool,
    duplication_percent: float | None,
    max_duplication_percent: float,
    report_age_hours: float | None,
    max_age_hours: float,
    report_exists: bool,
) -> str:
    if blocked_by_tooling:
        return "blocked_by_tooling"
    if not report_exists and any("missing report file" in error for error in errors):
        return "missing_report"
    if (
        duplication_percent is not None
        and duplication_percent > max_duplication_percent
        and any("duplication percent exceeds threshold" in error for error in errors)
    ):
        return "duplication_threshold_exceeded"
    if (
        report_age_hours is not None
        and report_age_hours > max_age_hours
        and any("jscpd report is stale" in error for error in errors)
    ):
        return "stale_report"
    if errors:
        return "error"
    if warnings:
        return "ok_with_warnings"
    return "ok"


def render_markdown(report: dict) -> str:
    lines = [
        "# check_duplication_audit",
        "",
        f"- ok: {report['ok']}",
        f"- status: {report['status']}",
        f"- blocked_by_tooling: {report['blocked_by_tooling']}",
        f"- source_root: {report['source_root']}",
        f"- report_path: {report['report_path']}",
        f"- run_jscpd: {report['run_jscpd']}",
        f"- run_python_fallback: {report['run_python_fallback']}",
        f"- allow_missing_tool: {report['allow_missing_tool']}",
        f"- jscpd_status: {report['jscpd_status']}",
        f"- report_exists: {report['report_exists']}",
        (
            "- report_age_hours: null"
            if report["report_age_hours"] is None
            else f"- report_age_hours: {report['report_age_hours']:.2f}"
        ),
        f"- max_age_hours: {report['max_age_hours']:.2f}",
        (
            "- duplication_percent: null"
            if report["duplication_percent"] is None
            else f"- duplication_percent: {report['duplication_percent']:.2f}"
        ),
        f"- max_duplication_percent: {report['max_duplication_percent']:.2f}",
        (
            "- duplicates_count: null"
            if report["duplicates_count"] is None
            else f"- duplicates_count: {report['duplicates_count']}"
        ),
        f"- check_shared_logic: {report.get('check_shared_logic', False)}",
        f"- shared_logic_candidate_count: {report.get('shared_logic_candidate_count', 0)}",
    ]
    if report["errors"]:
        lines.append("- errors:")
        lines.extend(f"  - {entry}" for entry in report["errors"])
    if report["warnings"]:
        lines.append("- warnings:")
        lines.extend(f"  - {entry}" for entry in report["warnings"])
    if not report["errors"]:
        lines.append("- errors: none")
    if not report["warnings"]:
        lines.append("- warnings: none")
    shared_logic_candidates = report.get("shared_logic_candidates", [])
    if shared_logic_candidates:
        lines.append("## Shared logic candidates")
        for item in shared_logic_candidates:
            summary_bits = [
                item["heuristic"],
                f"path={item['path']}",
                f"compared_path={item['compared_path']}",
            ]
            if "shared_significant_lines" in item:
                summary_bits.append(
                    f"shared_significant_lines={item['shared_significant_lines']}"
                )
            if "overlap_ratio" in item:
                summary_bits.append(f"overlap_ratio={item['overlap_ratio']:.2f}")
            if "shared_project_imports" in item:
                summary_bits.append(
                    f"shared_project_imports={item['shared_project_imports']}"
                )
            if "shared_import_ratio" in item:
                summary_bits.append(
                    f"shared_import_ratio={item['shared_import_ratio']:.2f}"
                )
            lines.append(f"- {'; '.join(summary_bits)}")
            lines.append(f"  hint: {item['hint']}")
    return "\n".join(lines)


def find_shared_logic_candidates(
    *,
    repo_root: Path,
    candidate_paths: list[Path],
    path_for_report: Callable[[Path], str],
    min_line_overlap: int,
    min_line_ratio: float,
    min_shared_imports: int,
    min_import_ratio: float,
    min_shared_markers: int,
) -> list[dict]:
    helper_paths = _collect_repo_paths(
        repo_root,
        SHARED_HELPER_COMPARE_GLOBS,
        exclude_globs=SHARED_LOGIC_CANDIDATE_EXCLUDES,
    )
    orchestration_paths = _collect_repo_paths(
        repo_root,
        ORCHESTRATION_COMPARE_GLOBS,
        exclude_globs=SHARED_LOGIC_CANDIDATE_EXCLUDES,
    )
    text_cache: dict[Path, str] = {}
    normalized_line_cache: dict[Path, set[str]] = {}
    import_cache: dict[Path, set[str]] = {}
    marker_cache: dict[Path, set[str]] = {}
    findings: list[dict] = []
    for candidate_path in sorted(set(candidate_paths)):
        if not _is_python_candidate(candidate_path):
            continue
        helper_candidate = _find_helper_overlap(
            repo_root=repo_root,
            candidate_path=candidate_path,
            compare_paths=helper_paths,
            path_for_report=path_for_report,
            text_cache=text_cache,
            normalized_line_cache=normalized_line_cache,
            min_line_overlap=min_line_overlap,
            min_line_ratio=min_line_ratio,
        )
        if helper_candidate is not None:
            findings.append(helper_candidate)
        orchestration_candidate = _find_orchestration_overlap(
            repo_root=repo_root,
            candidate_path=candidate_path,
            compare_paths=orchestration_paths,
            path_for_report=path_for_report,
            text_cache=text_cache,
            import_cache=import_cache,
            marker_cache=marker_cache,
            min_shared_imports=min_shared_imports,
            min_import_ratio=min_import_ratio,
            min_shared_markers=min_shared_markers,
        )
        if orchestration_candidate is not None:
            findings.append(orchestration_candidate)
    return findings


def run_python_fallback(
    *,
    source_root: Path,
    report_path: Path,
    min_lines: int,
    path_for_report: Callable[[Path], str],
) -> tuple[bool, str | None, str]:
    try:
        payload = _build_fallback_payload(source_root=source_root, min_lines=min_lines)
    except (OSError, ValueError) as exc:
        return False, f"python fallback failed: {exc}", "python_fallback_failed"

    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        return (
            False,
            f"python fallback failed to write report at {path_for_report(report_path)}: {exc}",
            "python_fallback_failed",
        )
    return True, None, "python_fallback"


def _collect_repo_paths(
    repo_root: Path,
    patterns: tuple[str, ...],
    *,
    exclude_globs: tuple[str, ...],
) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        paths.update(path for path in repo_root.glob(pattern) if path.is_file())
    return sorted(
        path.relative_to(repo_root)
        for path in paths
        if not _matches_any(path.relative_to(repo_root), exclude_globs)
    )


def _matches_any(path: Path, patterns: tuple[str, ...]) -> bool:
    path_text = path.as_posix()
    return any(path.match(pattern) or path_text == pattern for pattern in patterns)


def _is_python_candidate(path: Path) -> bool:
    return path.suffix == ".py" and not _matches_any(path, SHARED_LOGIC_CANDIDATE_EXCLUDES)


def _read_text(
    repo_root: Path,
    relative_path: Path,
    cache: dict[Path, str],
) -> str:
    cached = cache.get(relative_path)
    if cached is not None:
        return cached
    cache[relative_path] = (repo_root / relative_path).read_text(
        encoding="utf-8",
        errors="ignore",
    )
    return cache[relative_path]


def _normalized_significant_lines(
    repo_root: Path,
    relative_path: Path,
    text_cache: dict[Path, str],
    cache: dict[Path, set[str]],
) -> set[str]:
    cached = cache.get(relative_path)
    if cached is not None:
        return cached
    lines: set[str] = set()
    for raw_line in _read_text(repo_root, relative_path, text_cache).splitlines():
        normalized = _normalize_overlap_line(raw_line)
        if len(normalized) >= 8:
            lines.add(normalized)
    cache[relative_path] = lines
    return lines


def _normalize_overlap_line(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return ""
    if "#" in stripped:
        stripped = stripped.split("#", 1)[0].rstrip()
    stripped = STRING_LITERAL_RE.sub('"STR"', stripped)
    stripped = NUMBER_LITERAL_RE.sub("N", stripped)
    declaration_match = DECLARATION_NAME_RE.match(stripped)
    if declaration_match is not None:
        stripped = f"{declaration_match.group('prefix')}IDENTIFIER"
    return " ".join(stripped.split())


def _local_imports(
    repo_root: Path,
    relative_path: Path,
    text_cache: dict[Path, str],
    cache: dict[Path, set[str]],
) -> set[str]:
    cached = cache.get(relative_path)
    if cached is not None:
        return cached
    imports = {
        line.strip()
        for line in _read_text(repo_root, relative_path, text_cache).splitlines()
        if LOCAL_IMPORT_RE.match(line.strip())
    }
    cache[relative_path] = imports
    return imports


def _orchestration_markers_for_path(
    repo_root: Path,
    relative_path: Path,
    text_cache: dict[Path, str],
    cache: dict[Path, set[str]],
) -> set[str]:
    cached = cache.get(relative_path)
    if cached is not None:
        return cached
    text = _read_text(repo_root, relative_path, text_cache)
    markers = {
        marker_name
        for marker_name, pattern in ORCHESTRATION_MARKERS.items()
        if pattern.search(text)
    }
    cache[relative_path] = markers
    return markers


def _find_helper_overlap(
    *,
    repo_root: Path,
    candidate_path: Path,
    compare_paths: list[Path],
    path_for_report: Callable[[Path], str],
    text_cache: dict[Path, str],
    normalized_line_cache: dict[Path, set[str]],
    min_line_overlap: int,
    min_line_ratio: float,
) -> dict | None:
    candidate_lines = _normalized_significant_lines(
        repo_root, candidate_path, text_cache, normalized_line_cache
    )
    best_match: dict | None = None
    for compare_path in compare_paths:
        if compare_path == candidate_path:
            continue
        compare_lines = _normalized_significant_lines(
            repo_root, compare_path, text_cache, normalized_line_cache
        )
        shared_lines = candidate_lines & compare_lines
        if len(shared_lines) < min_line_overlap:
            continue
        overlap_ratio = len(shared_lines) / max(1, min(len(candidate_lines), len(compare_lines)))
        if overlap_ratio < min_line_ratio:
            continue
        finding = {
            "heuristic": "new-file-vs-shared-helper",
            "path": path_for_report(repo_root / candidate_path),
            "compared_path": path_for_report(repo_root / compare_path),
            "shared_significant_lines": len(shared_lines),
            "overlap_ratio": overlap_ratio,
            "hint": (
                "New file overlaps heavily with an existing shared-helper surface; "
                "prefer extending the helper or extracting the repeated logic into one owner."
            ),
            "summary": (
                f"shared-logic candidate: {path_for_report(repo_root / candidate_path)} "
                f"overlaps {path_for_report(repo_root / compare_path)} via helper reuse "
                f"({len(shared_lines)} shared normalized lines, ratio={overlap_ratio:.2f})"
            ),
        }
        if best_match is None or finding["overlap_ratio"] > best_match["overlap_ratio"]:
            best_match = finding
    return best_match


def _find_orchestration_overlap(
    *,
    repo_root: Path,
    candidate_path: Path,
    compare_paths: list[Path],
    path_for_report: Callable[[Path], str],
    text_cache: dict[Path, str],
    import_cache: dict[Path, set[str]],
    marker_cache: dict[Path, set[str]],
    min_shared_imports: int,
    min_import_ratio: float,
    min_shared_markers: int,
) -> dict | None:
    if not _matches_any(candidate_path, ORCHESTRATION_COMPARE_GLOBS):
        return None
    candidate_imports = _local_imports(repo_root, candidate_path, text_cache, import_cache)
    candidate_markers = _orchestration_markers_for_path(
        repo_root, candidate_path, text_cache, marker_cache
    )
    best_match: dict | None = None
    for compare_path in compare_paths:
        if compare_path == candidate_path:
            continue
        compare_imports = _local_imports(repo_root, compare_path, text_cache, import_cache)
        shared_imports = candidate_imports & compare_imports
        if len(shared_imports) < min_shared_imports:
            continue
        import_ratio = len(shared_imports) / max(
            1, min(len(candidate_imports), len(compare_imports))
        )
        if import_ratio < min_import_ratio:
            continue
        compare_markers = _orchestration_markers_for_path(
            repo_root, compare_path, text_cache, marker_cache
        )
        shared_markers = candidate_markers & compare_markers
        if len(shared_markers) < min_shared_markers:
            continue
        finding = {
            "heuristic": "orchestration-pattern-clone",
            "path": path_for_report(repo_root / candidate_path),
            "compared_path": path_for_report(repo_root / compare_path),
            "shared_project_imports": len(shared_imports),
            "shared_import_ratio": import_ratio,
            "shared_markers": sorted(shared_markers),
            "hint": (
                "New command/check file shares the same project-import scaffold as an existing "
                "runner; extract a shared command-runner helper instead of copying orchestration."
            ),
            "summary": (
                f"shared-logic candidate: {path_for_report(repo_root / candidate_path)} "
                f"matches {path_for_report(repo_root / compare_path)} command scaffolding "
                f"({len(shared_imports)} shared project imports, ratio={import_ratio:.2f})"
            ),
        }
        if best_match is None or finding["shared_import_ratio"] > best_match["shared_import_ratio"]:
            best_match = finding
    return best_match


def _build_fallback_payload(*, source_root: Path, min_lines: int) -> dict:
    if min_lines <= 0:
        raise ValueError("min_lines must be greater than zero")
    if not source_root.exists():
        raise ValueError(f"source root does not exist: {source_root}")

    file_records: list[tuple[Path, list[str]]] = []
    total_lines = 0
    for file_path in sorted(source_root.rglob("*")):
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        file_records.append((file_path, lines))
        total_lines += len(lines)

    window_map: dict[tuple[str, ...], list[tuple[int, int]]] = {}
    for file_idx, (_path, lines) in enumerate(file_records):
        if len(lines) < min_lines:
            continue
        for start in range(0, len(lines) - min_lines + 1):
            window = tuple(lines[start : start + min_lines])
            if not any(fragment.strip() for fragment in window):
                continue
            window_map.setdefault(window, []).append((file_idx, start))

    duplicate_entries: list[dict] = []
    duplicated_line_refs: set[tuple[int, int]] = set()
    for window, hits in window_map.items():
        if len(hits) < 2:
            continue
        anchor_file_idx, anchor_start = hits[0]
        anchor_file_path, _ = file_records[anchor_file_idx]
        for other_file_idx, other_start in hits[1:]:
            other_file_path, _ = file_records[other_file_idx]
            duplicate_entries.append(
                {
                    "format": "python_fallback",
                    "fragment": "\n".join(window),
                    "firstFile": {
                        "name": anchor_file_path.as_posix(),
                        "start": anchor_start + 1,
                    },
                    "secondFile": {
                        "name": other_file_path.as_posix(),
                        "start": other_start + 1,
                    },
                    "lines": min_lines,
                    "tokens": min_lines,
                }
            )
            for offset in range(min_lines):
                duplicated_line_refs.add((anchor_file_idx, anchor_start + offset))
                duplicated_line_refs.add((other_file_idx, other_start + offset))

    duplicated_lines = len(duplicated_line_refs)
    duplication_percent = 0.0
    if total_lines > 0:
        duplication_percent = (duplicated_lines / total_lines) * 100.0

    return {
        "statistics": {
            "total": {
                "lines": total_lines,
                "duplicatedLines": duplicated_lines,
                "percentage": duplication_percent,
            }
        },
        "duplicates": duplicate_entries,
        "meta": {
            "generatedBy": "check_duplication_audit.py python fallback",
            "sourceRoot": source_root.as_posix(),
            "minLines": min_lines,
        },
    }
