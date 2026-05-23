"""Shared bootstrap helpers for check scripts."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ENGINE_ROOT = Path(__file__).resolve().parents[3]


def _resolve_repo_root() -> Path:
    """Resolve repo root from DEVCTL_REPO_ROOT env var or file-path fallback."""
    import os
    env_root = os.environ.get("DEVCTL_REPO_ROOT")
    if env_root:
        resolved = Path(env_root).resolve()
        # Keep the engine root on sys.path so engine modules stay importable
        engine_str = str(_ENGINE_ROOT)
        if engine_str not in sys.path:
            sys.path.insert(0, engine_str)
        return resolved
    return _ENGINE_ROOT


REPO_ROOT = _resolve_repo_root()


def _top_level_module_name(module_name: str) -> str:
    return module_name.split(".", 1)[0]


def ensure_repo_root_on_syspath(repo_root: Path) -> None:
    """Add the repo root to `sys.path` once for repo-package imports."""
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def import_local_or_repo_module(
    local_module_name: str,
    repo_module_name: str,
    *,
    repo_root: Path,
) -> Any:
    """Import a helper module in local-script or repo-package execution modes."""
    try:
        return importlib.import_module(local_module_name)
    except ModuleNotFoundError as exc:
        if exc.name != _top_level_module_name(local_module_name):
            raise
    ensure_repo_root_on_syspath(repo_root)
    return importlib.import_module(repo_module_name)


def import_repo_module(module_name: str, *, repo_root: Path) -> Any:
    """Import a repo-owned package module, repairing `sys.path` only when needed."""
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != _top_level_module_name(module_name):
            raise
    ensure_repo_root_on_syspath(repo_root)
    return importlib.import_module(module_name)


def import_attr(module_name: str, attr_name: str) -> Any:
    """Import an attribute from local-script or package execution contexts."""
    module = import_local_or_repo_module(
        module_name,
        f"dev.scripts.checks.{module_name}",
        repo_root=REPO_ROOT,
    )
    return getattr(module, attr_name)


def resolve_quality_scope_roots(
    scope_id: str,
    *,
    repo_root: Path,
) -> tuple[Path, ...]:
    """Resolve repo-configured quality-scope roots for a guard or probe."""
    quality_policy = import_repo_module(
        "dev.scripts.devctl.quality_policy",
        repo_root=repo_root,
    )
    return tuple(
        quality_policy.resolve_quality_scope_roots(
            scope_id,
            repo_root=repo_root,
        )
    )


def resolve_guard_config(
    script_id: str,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Resolve repo-configured per-script settings for a guard or probe."""
    quality_policy = import_repo_module(
        "dev.scripts.devctl.quality_policy",
        repo_root=repo_root,
    )
    config = quality_policy.resolve_guard_config(
        script_id,
        repo_root=repo_root,
    )
    return dict(config) if isinstance(config, dict) else {}


def utc_timestamp() -> str:
    """Return a stable UTC ISO-8601 timestamp for JSON/markdown reports."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_since_ref_format_parser(description: str) -> argparse.ArgumentParser:
    """Build the standard since-ref/head-ref/format parser shared by guards."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument("--head-ref", default="HEAD", help="Head ref used with --since-ref")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def is_under_target_roots(path: Path, *, repo_root: Path, target_roots: tuple[Path, ...]) -> bool:
    """Return whether a repo path falls within one of the configured roots."""
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        relative = path
    return any(relative == root or root in relative.parents for root in target_roots)


def emit_runtime_error(command: str, output_format: str, error: str) -> int:
    """Emit a consistent error report for guard script runtime failures."""
    report = {
        "command": command,
        "timestamp": utc_timestamp(),
        "ok": False,
        "error": error,
    }
    if output_format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"# {command}\n")
        print(f"- ok: False\n- error: {report['error']}")
    return 2


def run_format_check(
    *,
    argv: Sequence[str] | None,
    command: str,
    description: str,
    build_report: "Callable[[], Mapping[str, object]]",
    render_markdown: "Callable[[Mapping[str, object]], str]",
) -> int:
    """Shared ``main()`` body for guard scripts that share the format-only CLI shape.

    Previously each guard re-implemented the same parser plus ``build_report`` ->
    ``render_markdown``/``json.dumps`` dispatch (``check_orphan_files``,
    ``check_feature_completion``, etc). The bodies hashed identically across
    files; routing through this helper removes the AST-level duplication.
    """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report()
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(command, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report.get("ok") else 1


def parse_utc(value: str | None) -> datetime | None:
    """Parse an ISO-8601 UTC timestamp, accepting trailing ``Z`` notation.

    Returns ``None`` for ``None`` or empty/whitespace strings or malformed
    input. Naive datetimes are coerced to UTC; aware datetimes are
    normalised to UTC.
    """
    text = (value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iter_jsonl(
    path: Path,
    *,
    warnings: list[str],
    missing_label: str = "event log missing",
) -> Iterable[Mapping[str, object]]:
    """Iterate JSON-Lines rows from ``path``, recording missing-file warnings.

    Lines that fail JSON parsing are silently skipped; non-Mapping payloads
    are filtered out so callers only see dict rows. ``missing_label`` is the
    prefix used when ``path`` does not exist (e.g. ``"event log missing"``).
    """
    if not path.exists():
        warnings.append(f"{missing_label}: {path}")
        return ()

    def _rows() -> Iterable[Mapping[str, object]]:
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping):
                yield payload

    return _rows()


def packets_from_review_state(
    path: Path,
    warnings: list[str],
) -> tuple[Mapping[str, object], ...]:
    """Load the ``packets`` array from a review-state projection JSON file.

    Missing files, malformed JSON, non-Mapping payloads, and missing/invalid
    ``packets`` arrays all return an empty tuple while recording warnings on
    the supplied list.
    """
    if not path.exists():
        warnings.append(f"review state missing: {path}")
        return ()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"review state load failed: {exc}")
        return ()
    if not isinstance(payload, Mapping):
        return ()
    packets = payload.get("packets")
    if not isinstance(packets, list):
        return ()
    return tuple(p for p in packets if isinstance(p, Mapping))


def normalized_packet_ids(packet_ids: Sequence[str]) -> tuple[str, ...]:
    """Return a de-duplicated, stripped tuple of packet ids in input order."""
    seen: set[str] = set()
    normalized: list[str] = []
    for packet_id in packet_ids:
        value = str(packet_id or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def matches_row(packet: Mapping[str, object], current_row_id: str) -> bool:
    """Return whether ``packet`` belongs to the given plan-row id.

    Empty ``current_row_id`` matches every packet. Otherwise the packet
    matches if its ``target_ref`` substring-contains the row id, or its
    ``plan_id`` is exactly the row id.
    """
    if not current_row_id:
        return True
    target_ref = str(packet.get("target_ref") or "").strip()
    if target_ref and current_row_id in target_ref:
        return True
    plan_id = str(packet.get("plan_id") or "").strip()
    return current_row_id == plan_id


def packet_row_id(packet: Mapping[str, object]) -> str:
    """Extract the plan-row id a packet belongs to.

    Prefers ``plan_id``; falls back to a ``plan:<id>``-prefixed ``target_ref``;
    otherwise returns the raw ``target_ref`` string.
    """
    plan_id = str(packet.get("plan_id") or "").strip()
    if plan_id:
        return plan_id
    target_ref = str(packet.get("target_ref") or "").strip()
    if target_ref.startswith("plan:"):
        return target_ref.split("plan:", 1)[1]
    return target_ref


def coerce_string(value: object) -> str:
    """Return a stripped string view of ``value``.

    ``None`` becomes the empty string. Strings are stripped of whitespace.
    Everything else is round-tripped through ``str()`` and then stripped.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def report_to_dict(report: Any) -> dict[str, object]:
    """Convert a ``@dataclass`` report into a JSON-friendly ``dict``.

    Materialises ``checked_surfaces``, ``violations``, and ``warnings`` as
    ``list`` (instead of the dataclass ``tuple`` defaults) so the payload
    serialises cleanly as JSON arrays.
    """
    from dataclasses import asdict as _asdict

    payload = _asdict(report)
    if hasattr(report, "checked_surfaces"):
        payload["checked_surfaces"] = list(report.checked_surfaces)
    if hasattr(report, "violations"):
        payload["violations"] = list(report.violations)
    if hasattr(report, "warnings"):
        payload["warnings"] = list(report.warnings)
    return payload
