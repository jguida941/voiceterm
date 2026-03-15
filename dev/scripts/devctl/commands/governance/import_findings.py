"""devctl governance-import-findings command implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...governance.external_findings_log import (
    DEFAULT_CHECK_ID,
    append_external_finding_rows,
    build_external_finding_report,
    build_external_finding_row,
    resolve_external_finding_log_path,
    resolve_external_finding_summary_root,
)
from ...governance.external_findings_models import ExternalFindingInput
from ...governance.external_findings_render import (
    render_external_finding_markdown,
    write_external_finding_summary,
)
from ...governance_review_log import resolve_governance_review_log_path
from ...jsonl_support import parse_json_line_dict
from ...time_utils import utc_timestamp
from .common import emit_governance_command_output, render_governance_value_error


def run(args) -> int:
    """Import raw external findings into a ledger, then render coverage metrics."""
    try:
        log_path = resolve_external_finding_log_path(getattr(args, "log_path", None))
        summary_root = resolve_external_finding_summary_root(
            getattr(args, "summary_root", None)
        )
        governance_review_log_path = resolve_governance_review_log_path(
            getattr(args, "governance_review_log", None)
        )
        imported_count = 0
        import_run_id = getattr(args, "run_id", None)
        input_path = None
        if getattr(args, "input", None):
            input_path = Path(str(args.input)).expanduser()
            if not input_path.is_absolute():
                input_path = Path.cwd() / input_path
            imported_rows, import_run_id = _load_import_rows(
                input_path=input_path.resolve(),
                input_format=str(getattr(args, "input_format", "auto") or "auto"),
                args=args,
            )
            append_external_finding_rows(imported_rows, log_path=log_path)
            imported_count = len(imported_rows)

        report = build_external_finding_report(
            log_path=log_path,
            governance_review_log_path=governance_review_log_path,
            max_rows=int(getattr(args, "max_rows", 10_000)),
            max_governance_review_rows=int(
                getattr(args, "max_governance_review_rows", 5_000)
            ),
        )
        if input_path is not None:
            report["input_path"] = str(input_path)
            report["imported_count"] = imported_count
        if import_run_id:
            report["import_run_id"] = import_run_id
        report["paths"] = write_external_finding_summary(
            report,
            summary_root=summary_root,
        )
    except ValueError as exc:
        return render_governance_value_error(exc)

    return emit_governance_command_output(
        args,
        command="governance-import-findings",
        json_payload=report,
        markdown_output=render_external_finding_markdown(report),
        summary={
            "imported_count": report.get("imported_count"),
            "total_findings": ((report.get("stats") or {}).get("total_findings")),
            "adjudication_coverage_pct": (
                (report.get("stats") or {}).get("adjudication_coverage_pct")
            ),
        },
    )


def _load_import_rows(
    *,
    input_path: Path,
    input_format: str,
    args,
) -> tuple[list[dict[str, Any]], str]:
    payload_rows = _load_candidate_rows(input_path, input_format=input_format)
    import_run_id = (
        str(getattr(args, "run_id", None) or "").strip()
        or _default_import_run_id(input_path)
    )
    rows = [
        build_external_finding_row(
            finding_input=_build_finding_input(
                item=item,
                source_artifact=input_path,
                source_row=index,
                import_run_id=import_run_id,
                args=args,
            )
        )
        for index, item in enumerate(payload_rows, start=1)
    ]
    return rows, import_run_id


def _load_candidate_rows(input_path: Path, *, input_format: str) -> list[dict[str, Any]]:
    try:
        raw_text = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"unable to read input file `{input_path}`: {exc}") from exc

    mode = input_format.strip().lower()
    if mode not in {"auto", "json", "jsonl"}:
        raise ValueError("input_format must be one of: auto, json, jsonl")
    if mode == "jsonl":
        return _parse_jsonl_rows(raw_text, input_path=input_path)
    if mode == "json":
        return _parse_json_rows(raw_text, input_path=input_path)

    stripped = raw_text.lstrip()
    if input_path.suffix.lower() == ".jsonl" or (
        "\n" in stripped and stripped[:1] not in {"[", "{"}
    ):
        return _parse_jsonl_rows(raw_text, input_path=input_path)
    try:
        return _parse_json_rows(raw_text, input_path=input_path)
    except ValueError:
        return _parse_jsonl_rows(raw_text, input_path=input_path)


def _parse_json_rows(raw_text: str, *, input_path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in `{input_path}`: {exc}") from exc
    if isinstance(payload, list):
        return _ensure_dict_rows(payload, input_path=input_path)
    if isinstance(payload, dict):
        for key in ("findings", "items", "rows"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                return _ensure_dict_rows(candidate, input_path=input_path)
        return _ensure_dict_rows([payload], input_path=input_path)
    raise ValueError(
        f"unsupported JSON payload in `{input_path}`: expected object or list"
    )


def _parse_jsonl_rows(raw_text: str, *, input_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(raw_text.splitlines(), start=1):
        payload = parse_json_line_dict(line)
        if payload is None:
            if line.strip():
                raise ValueError(
                    f"invalid JSONL object at line {index} in `{input_path}`"
                )
            continue
        rows.append(payload)
    if not rows:
        raise ValueError(f"no JSON object rows found in `{input_path}`")
    return rows


def _ensure_dict_rows(items: list[Any], *, input_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"row {index} in `{input_path}` is not a JSON object")
        rows.append(item)
    if not rows:
        raise ValueError(f"no finding rows found in `{input_path}`")
    return rows


def _build_finding_input(
    *,
    item: dict[str, Any],
    source_artifact: Path,
    source_row: int,
    import_run_id: str,
    args,
) -> ExternalFindingInput:
    file_path = _first_text(
        item,
        "file_path",
        "path",
        "file",
    ) or _first_location_text(item, "path", "file")
    if not file_path:
        raise ValueError(f"import row {source_row} is missing file_path/path")

    repo_name = (
        _override_text(getattr(args, "repo_name", None))
        or _first_text(item, "repo_name", "repo")
        or _repo_name_from_path(
            _override_text(getattr(args, "repo_path", None))
            or _first_text(item, "repo_path")
        )
    )
    repo_path = _override_text(getattr(args, "repo_path", None)) or _first_text(
        item,
        "repo_path",
    )

    return ExternalFindingInput(
        finding_id=_first_text(item, "finding_id"),
        repo_name=repo_name,
        repo_path=repo_path,
        check_id=_override_text(getattr(args, "check_id", None))
        or _first_text(
            item,
            "check_id",
            "rule_id",
            "rule",
            "guard_id",
            "probe_id",
            "rule_hint",
        )
        or DEFAULT_CHECK_ID,
        signal_type=_override_text(getattr(args, "signal_type", None))
        or _first_text(item, "signal_type"),
        file_path=file_path,
        title=_first_text(item, "title", "finding", "message", "name"),
        summary=_first_text(item, "summary", "description", "details"),
        evidence=_first_text(item, "evidence", "rationale", "why"),
        severity=_override_text(getattr(args, "severity", None))
        or _first_text(item, "severity"),
        risk_type=_override_text(getattr(args, "risk_type", None))
        or _first_text(item, "risk_type", "category"),
        symbol=_first_text(item, "symbol", "function", "class_name")
        or _first_location_text(item, "symbol"),
        line=_first_int(item, "line", "line_number", "start_line")
        or _first_location_int(item, "line", "start_line"),
        end_line=_first_int(item, "end_line", "end_line_number")
        or _first_location_int(item, "end_line"),
        source_model=_override_text(getattr(args, "source_model", None))
        or _first_text(item, "source_model", "model", "agent"),
        source_command=_override_text(getattr(args, "source_command", None))
        or _first_text(item, "source_command", "command"),
        source_artifact=_first_text(item, "source_artifact") or str(source_artifact),
        source_row=source_row,
        scan_mode=_override_text(getattr(args, "scan_mode", None))
        or _first_text(item, "scan_mode"),
        import_run_id=_first_text(item, "import_run_id", "run_id", "corpus_run_id")
        or import_run_id,
        notes=_override_text(getattr(args, "notes", None))
        or _first_text(item, "notes"),
    )


def _default_import_run_id(input_path: Path) -> str:
    stamp = (
        utc_timestamp()
        .replace(":", "")
        .replace("-", "")
        .replace("T", "-")
        .replace("Z", "z")
    )
    stem = input_path.stem.replace(" ", "-") or "external-findings"
    return f"{stem}-{stamp}"


def _repo_name_from_path(value: str | None) -> str | None:
    text = _override_text(value)
    if not text:
        return None
    name = Path(text).name.strip()
    return name or None


def _override_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_text(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _first_location_text(item: dict[str, Any], *keys: str) -> str | None:
    location = item.get("location")
    if not isinstance(location, dict):
        return None
    return _first_text(location, *keys)


def _first_int(item: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = item.get(key)
        if value is None or value == "":
            continue
        return _parse_int(value, field_name=key)
    return None


def _first_location_int(item: dict[str, Any], *keys: str) -> int | None:
    location = item.get("location")
    if not isinstance(location, dict):
        return None
    return _first_int(location, *keys)


def _parse_int(value: object, *, field_name: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer: {value!r}") from exc
    if result <= 0:
        raise ValueError(f"{field_name} must be positive: {value!r}")
    return result
