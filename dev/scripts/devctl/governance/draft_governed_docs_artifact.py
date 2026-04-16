"""Persistence helpers for governed markdown plan/doc contracts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

from ..runtime.project_governance import (
    DocPolicy,
    DocRegistry,
    PlanRegistry,
    doc_policy_from_mapping,
    doc_registry_from_mapping,
    plan_registry_from_mapping,
)
from ..runtime.value_coercion import (
    coerce_int,
    coerce_mapping,
    coerce_string,
)
from ..runtime.work_intake_models import PlanTargetRef
from ..time_utils import utc_timestamp

if TYPE_CHECKING:
    from .doc_authority_models import GovernedDocLayout

_ARTIFACT_CONTRACT_ID = "PlanRegistryArtifact"
_ARTIFACT_SCHEMA_VERSION = 1
_ARTIFACT_SUBPATH = Path("governance/plan_registry.json")
_DEFAULT_REPORTS_ROOT = "dev/reports"
_PLAN_DOC_ANCHOR = "section:root"
_PLAN_DOC_TARGET_KIND = "plan_doc"
_SESSION_RESUME_ANCHOR = "session_resume:session-resume"
_SESSION_RESUME_TARGET_KIND = "session_resume"

@dataclass(frozen=True, slots=True)
class GovernedMarkdownContractsArtifact:
    """Typed payload bundle persisted after a governed markdown scan."""

    plan_registry: PlanRegistry
    doc_policy: DocPolicy
    doc_registry: DocRegistry
    plan_targets: Mapping[str, PlanTargetRef]

def resolve_plan_registry_artifact_path(
    repo_root: Path,
    *,
    reports_root: str = "",
) -> Path:
    """Return the repo-owned persisted plan-registry artifact path."""
    resolved_reports_root = str(reports_root or "").strip() or _DEFAULT_REPORTS_ROOT
    return repo_root / resolved_reports_root / _ARTIFACT_SUBPATH


def build_plan_target_ref(
    *,
    relative_path: str,
    title: str,
    scope: str,
    session_resume_hash: str,
    file_text: str,
) -> PlanTargetRef:
    """Build the persisted PlanTargetRef for one plan-registry entry."""
    target_kind = _PLAN_DOC_TARGET_KIND
    anchor_ref = _PLAN_DOC_ANCHOR
    expected_revision = sha256(file_text.encode("utf-8")).hexdigest()[:16]
    if session_resume_hash:
        target_kind = _SESSION_RESUME_TARGET_KIND
        anchor_ref = _SESSION_RESUME_ANCHOR
        expected_revision = session_resume_hash
    target_digest = sha256(
        f"{relative_path}|{target_kind}|{anchor_ref}".encode("utf-8")
    ).hexdigest()[:16]
    return PlanTargetRef(
        target_id=f"plan_target:{target_digest}",
        plan_path=relative_path,
        plan_title=title,
        plan_scope=scope,
        target_kind=target_kind,
        anchor_ref=anchor_ref,
        expected_revision=expected_revision,
    )


def load_governed_markdown_contracts_artifact(
    repo_root: Path,
    *,
    reports_root: str,
    layout: "GovernedDocLayout",
) -> tuple[PlanRegistry, DocPolicy, DocRegistry] | None:
    """Return persisted plan/doc contracts when the artifact is still fresh."""
    payload = _load_artifact_payload(
        resolve_plan_registry_artifact_path(
            repo_root,
            reports_root=reports_root,
        )
    )
    if not _artifact_is_fresh(repo_root, layout=layout, payload=payload):
        return None
    return (
        plan_registry_from_mapping(coerce_mapping(payload.get("plan_registry"))),
        doc_policy_from_mapping(coerce_mapping(payload.get("doc_policy"))),
        doc_registry_from_mapping(coerce_mapping(payload.get("doc_registry"))),
    )


def write_governed_markdown_contracts_artifact(
    repo_root: Path,
    *,
    reports_root: str,
    layout: "GovernedDocLayout",
    artifact: GovernedMarkdownContractsArtifact,
) -> None:
    """Persist the governed markdown scan so later reads can avoid reparsing."""
    artifact_path = resolve_plan_registry_artifact_path(
        repo_root,
        reports_root=reports_root,
    )
    payload = _artifact_payload(
        repo_root,
        layout=layout,
        artifact=artifact,
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_persisted_plan_target_ref(
    repo_root: Path,
    relative_path: str,
    *,
    reports_root: str = "",
) -> PlanTargetRef | None:
    """Return a persisted target ref when the specific source plan is unchanged."""
    payload = _load_artifact_payload(
        resolve_plan_registry_artifact_path(
            repo_root,
            reports_root=reports_root,
        )
    )
    if not payload:
        return None
    target_mapping = coerce_mapping(
        coerce_mapping(payload.get("plan_targets")).get(relative_path)
    )
    if not target_mapping:
        return None
    source_row = _source_row_by_path(payload, relative_path)
    if source_row is None or not _source_row_matches(repo_root, source_row):
        return None
    return _plan_target_ref_from_mapping(target_mapping)

def enumerate_governed_markdown_paths(
    repo_root: Path,
    layout: "GovernedDocLayout",
) -> tuple[str, ...]:
    """Return the governed markdown paths without reading file contents."""
    seen: set[str] = set()
    paths: list[str] = []
    for relative_root in _scan_roots(layout):
        scan_dir = repo_root / relative_root
        if not scan_dir.is_dir():
            continue
        for md_file in sorted(scan_dir.rglob("*.md")):
            rel = md_file.relative_to(repo_root).as_posix()
            if rel in seen:
                continue
            seen.add(rel)
            paths.append(rel)
    for root_file in layout.root_files:
        full_path = repo_root / root_file
        if not full_path.is_file() or root_file in seen:
            continue
        seen.add(root_file)
        paths.append(root_file)
    return tuple(paths)


def _artifact_is_fresh(
    repo_root: Path,
    *,
    layout: "GovernedDocLayout",
    payload: Mapping[str, object],
) -> bool:
    if not payload:
        return False
    if coerce_string(payload.get("contract_id")) != _ARTIFACT_CONTRACT_ID:
        return False
    if coerce_int(payload.get("schema_version")) != _ARTIFACT_SCHEMA_VERSION:
        return False
    source_rows = _source_rows(payload)
    if not source_rows:
        return False
    current_paths = enumerate_governed_markdown_paths(repo_root, layout)
    stored_paths = tuple(row["path"] for row in source_rows)
    if stored_paths != current_paths:
        return False
    return all(_source_row_matches(repo_root, row) for row in source_rows)

def _artifact_payload(
    repo_root: Path,
    *,
    layout: "GovernedDocLayout",
    artifact: GovernedMarkdownContractsArtifact,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    payload["schema_version"] = _ARTIFACT_SCHEMA_VERSION
    payload["contract_id"] = _ARTIFACT_CONTRACT_ID
    payload["generated_at_utc"] = utc_timestamp()
    payload["source_files"] = _source_file_rows(
        repo_root,
        enumerate_governed_markdown_paths(repo_root, layout),
    )
    payload["plan_registry"] = artifact.plan_registry.to_dict()
    payload["doc_policy"] = artifact.doc_policy.to_dict()
    payload["doc_registry"] = artifact.doc_registry.to_dict()
    payload["plan_targets"] = _plan_targets_payload(artifact.plan_targets)
    return payload


def _load_artifact_payload(path: Path) -> Mapping[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, Mapping) else {}

def _plan_target_ref_from_mapping(
    payload: Mapping[str, object],
) -> PlanTargetRef:
    return PlanTargetRef(
        target_id=coerce_string(payload.get("target_id")),
        plan_path=coerce_string(payload.get("plan_path")),
        plan_title=coerce_string(payload.get("plan_title")),
        plan_scope=coerce_string(payload.get("plan_scope")),
        target_kind=coerce_string(payload.get("target_kind")),
        anchor_ref=coerce_string(payload.get("anchor_ref")),
        expected_revision=coerce_string(payload.get("expected_revision")),
    )


def _scan_roots(layout: "GovernedDocLayout") -> tuple[str, ...]:
    roots: list[str] = []
    for candidate in (
        *layout.governed_doc_roots,
        layout.active_docs_root,
        layout.guides_root,
    ):
        normalized = str(candidate or "").strip().rstrip("/")
        if not normalized or normalized in roots:
            continue
        roots.append(normalized)
    return tuple(roots)


def _source_file_rows(
    repo_root: Path,
    relative_paths: tuple[str, ...],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative_path in relative_paths:
        full_path = repo_root / relative_path
        try:
            stat = full_path.stat()
        except OSError:
            continue
        rows.append(
            {
                "path": relative_path,
                "mtime_ns": stat.st_mtime_ns,
                "size": stat.st_size,
            }
        )
    return rows


def _source_rows(payload: Mapping[str, object]) -> tuple[dict[str, int | str], ...]:
    raw_rows = payload.get("source_files")
    if not isinstance(raw_rows, list):
        return ()
    rows: list[dict[str, int | str]] = []
    for row in raw_rows:
        mapping = coerce_mapping(row)
        relative_path = coerce_string(mapping.get("path"))
        if not relative_path:
            continue
        rows.append(
            {
                "path": relative_path,
                "mtime_ns": coerce_int(mapping.get("mtime_ns")),
                "size": coerce_int(mapping.get("size")),
            }
        )
    return tuple(rows)


def _source_row_by_path(
    payload: Mapping[str, object],
    relative_path: str,
) -> dict[str, int | str] | None:
    for row in _source_rows(payload):
        if row["path"] == relative_path:
            return row
    return None


def _source_row_matches(
    repo_root: Path,
    row: Mapping[str, int | str],
) -> bool:
    path_text = str(row.get("path") or "").strip()
    if not path_text:
        return False
    full_path = repo_root / path_text
    try:
        stat = full_path.stat()
    except OSError:
        return False
    return (
        stat.st_mtime_ns == int(row.get("mtime_ns") or 0)
        and stat.st_size == int(row.get("size") or 0)
    )


def _plan_targets_payload(
    plan_targets: Mapping[str, PlanTargetRef],
) -> dict[str, dict[str, object]]:
    payload: dict[str, dict[str, object]] = {}
    for path, target in sorted(plan_targets.items()):
        payload[path] = target.to_dict()
    return payload


__all__ = [
    "build_plan_target_ref",
    "enumerate_governed_markdown_paths",
    "GovernedMarkdownContractsArtifact",
    "load_governed_markdown_contracts_artifact",
    "load_persisted_plan_target_ref",
    "resolve_plan_registry_artifact_path",
    "write_governed_markdown_contracts_artifact",
]
