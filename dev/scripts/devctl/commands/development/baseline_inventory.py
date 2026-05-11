"""Typed baseline authority inventory for MP-377 substrate work."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

from ...bundles.registry import BUNDLE_REGISTRY
from ...common import emit_output, write_output
from ...config import REPO_ROOT
from ...governance.script_catalog_registry import CHECK_SCRIPT_RELATIVE_PATHS
from ...platform.contract_registry_models import CONTRACT_REGISTRY_STORE_REL
from ...platform.connectivity_registry import (
    build_connectivity_registry_snapshot,
    summarize_connectivity_registry,
)
from ...platform.system_catalog import build_system_catalog
from ...review_channel.event_store import (
    DEFAULT_REVIEW_EVENT_LOG_REL,
    DEFAULT_REVIEW_PROJECTIONS_DIR_REL,
    DEFAULT_REVIEW_STATE_JSON_REL,
)
from ...review_channel.packet_contract import VALID_PACKET_KINDS
from ...runtime.baseline_authority_inventory import (
    AuthorityStoreEntry,
    BaselineAuthorityInventoryReceipt,
    DuplicateSystemCluster,
    InventoryCodeSite,
    append_baseline_authority_inventory_receipt,
    baseline_authority_inventory_id,
)
from ...runtime.governed_exception_store import (
    DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL,
)
from ...runtime.ground_truth_probe_receipt import DEFAULT_GROUND_TRUTH_RECEIPT_REL
from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL
from ...runtime.plan_index_authority import PlanIndexAuthorityResult
from ...runtime.plan_intent_ingestion import (
    PLAN_INTENT_INGESTION_RECEIPT_STORE_REL,
)
from ...runtime.plan_source_retention import PLAN_SOURCE_SNAPSHOT_STORE_REL
from ...runtime.relaunch_loop_models import (
    DEFAULT_RELAUNCH_QUEUE_REL,
    DEFAULT_RELAUNCH_RECEIPTS_REL,
    DEFAULT_RELAUNCH_TRACE_REL,
)
from ...runtime.remote_control_invocation_classifiers import (
    DEFAULT_REMOTE_CONTROL_INVOCATION_REL,
)
from ...time_utils import utc_timestamp
from .plan_intake_phase0 import build_repo_state_fingerprint


def _path_text(value: str | Path) -> str:
    return value.as_posix() if isinstance(value, Path) else str(value)


_CODE_SCAN_ROOTS = (
    Path("dev/scripts/devctl"),
    Path("dev/scripts/checks"),
)
_GENERATED_PROJECTION_CANDIDATES = (
    Path("AGENTS.md"),
    Path("CLAUDE.md"),
    Path("bridge.md"),
    Path("review_only"),
)
_DIRECT_WRITE_PATTERNS = (
    ("write_text", re.compile(r"\.write_text\(")),
    ("append_open", re.compile(r"\.open\((?:\"|')a(?:\"|')")),
    ("write_open", re.compile(r"\.open\((?:\"|')w(?:\"|')")),
)
_DIRECT_READ_PATTERNS = (("read_text", re.compile(r"\.read_text\(")),)
_REDUCER_PATTERNS = (
    ("reduce_fn", re.compile(r"^\s*def\s+reduce_[A-Za-z0-9_]+\(")),
    ("build_reduced_fn", re.compile(r"^\s*def\s+build_reduced_[A-Za-z0-9_]+\(")),
)
_EVENT_PRODUCER_PATTERNS = (("append_event", re.compile(r"\bappend_event\(")),)
_EVENT_SUBSCRIBER_PATTERNS = (
    ("load_events", re.compile(r"\bload_events\(")),
    ("refresh_event_bundle", re.compile(r"\brefresh_event_bundle\(")),
    ("build_reduced_review_state", re.compile(r"\bbuild_reduced_review_state\(")),
)
_COMPATIBILITY_PATTERNS = (
    ("compatibility", re.compile(r"\bcompatibility\b", re.IGNORECASE)),
    ("legacy", re.compile(r"\blegacy\b", re.IGNORECASE)),
    ("fallback", re.compile(r"\bfallback\b", re.IGNORECASE)),
    ("shim", re.compile(r"\bshim\b", re.IGNORECASE)),
)
_SEARCH_PATTERNS = (
    "build_system_catalog()",
    "build_connectivity_registry_snapshot()",
    ".write_text(",
    ".read_text(",
    ".open('a')/.open(\"a\")",
    ".open('w')/.open(\"w\")",
    "def reduce_*",
    "def build_reduced_*",
    "append_event(",
    "load_events(",
    "compatibility|legacy|fallback|shim",
)
_PLAN_INDEX_AUTHORITY_RESULT_FIELDS = tuple(PlanIndexAuthorityResult.__dataclass_fields__)
_PLAN_INDEX_AUTHORITY_RESULT_FIELD_TEXT = ",".join(_PLAN_INDEX_AUTHORITY_RESULT_FIELDS)
_STORE_ENTRIES = (
    AuthorityStoreEntry(
        path=str(DEFAULT_MASTER_PLAN_STORE_REL),
        store_kind="governed_jsonl",
        writer_ref=(
            "dev.scripts.devctl.runtime.plan_index_authority:upsert_plan_index_row "
            "(compat via master_plan_store.upsert_plan_row_jsonl; result="
            f"PlanIndexAuthorityResult[{_PLAN_INDEX_AUTHORITY_RESULT_FIELD_TEXT}])"
        ),
        locking_policy="shared_sidecar_lock + atomic_replace",
    ),
    AuthorityStoreEntry(
        path=PLAN_INTENT_INGESTION_RECEIPT_STORE_REL,
        store_kind="append_only_receipt_jsonl",
        writer_ref=(
            "dev.scripts.devctl.runtime.plan_intent_ingestion:"
            "append_plan_intent_ingestion_receipt via "
            "state_store_authority.append_json_mapping"
        ),
        locking_policy="shared_sidecar_lock + append_fsync",
    ),
    AuthorityStoreEntry(
        path=PLAN_SOURCE_SNAPSHOT_STORE_REL,
        store_kind="append_or_replace_snapshot_jsonl",
        writer_ref=(
            "dev.scripts.devctl.runtime.plan_source_retention_store:"
            "append_plan_source_snapshot via shared state_store_authority"
        ),
        locking_policy="shared_sidecar_lock + append_or_atomic_replace",
    ),
    AuthorityStoreEntry(
        path=CONTRACT_REGISTRY_STORE_REL,
        store_kind="repo_owned_contract_registry_jsonl",
        writer_ref=(
            "dev.scripts.devctl.platform.contract_registry:"
            "write_contract_registry_rows"
        ),
        locking_policy="shared_sidecar_lock + atomic_replace",
    ),
    AuthorityStoreEntry(
        path=DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL.as_posix(),
        store_kind="governed_exception_lifecycle_jsonl",
        writer_ref="missing_writer",
        locking_policy="read_only_today",
    ),
    AuthorityStoreEntry(
        path=DEFAULT_GROUND_TRUTH_RECEIPT_REL.as_posix(),
        store_kind="append_only_receipt_jsonl",
        writer_ref=(
            "dev.scripts.devctl.runtime.ground_truth_probe_receipt:"
            "append_ground_truth_probe_receipt via "
            "state_store_authority.append_json_mapping"
        ),
        locking_policy="shared_sidecar_lock + append_fsync",
    ),
    AuthorityStoreEntry(
        path=DEFAULT_REMOTE_CONTROL_INVOCATION_REL,
        store_kind="remote_control_invocation_jsonl",
        writer_ref=(
            "dev.scripts.devctl.runtime.remote_control_invocation_receipt:"
            "record_remote_control_invocation via "
            "relaunch_loop_store.append_jsonl/state_store_authority.append_json_mapping"
        ),
        locking_policy="shared_sidecar_lock + append_fsync",
    ),
    AuthorityStoreEntry(
        path=DEFAULT_RELAUNCH_TRACE_REL.as_posix(),
        store_kind="relaunch_trace_ndjson",
        writer_ref=(
            "dev.scripts.devctl.runtime.relaunch_loop_store:append_jsonl via "
            "state_store_authority.append_json_mapping"
        ),
        locking_policy="shared_sidecar_lock + append_fsync",
    ),
    AuthorityStoreEntry(
        path=DEFAULT_RELAUNCH_QUEUE_REL.as_posix(),
        store_kind="relaunch_queue_jsonl",
        writer_ref=(
            "dev.scripts.devctl.runtime.relaunch_loop_store:append_jsonl via "
            "state_store_authority.append_json_mapping"
        ),
        locking_policy="shared_sidecar_lock + append_fsync",
    ),
    AuthorityStoreEntry(
        path=DEFAULT_RELAUNCH_RECEIPTS_REL.as_posix(),
        store_kind="relaunch_receipt_jsonl",
        writer_ref=(
            "dev.scripts.devctl.runtime.relaunch_loop_store:append_jsonl via "
            "state_store_authority.append_json_mapping"
        ),
        locking_policy="shared_sidecar_lock + append_fsync",
    ),
    AuthorityStoreEntry(
        path=_path_text(DEFAULT_REVIEW_EVENT_LOG_REL),
        store_kind="review_event_log_ndjson",
        writer_ref="dev.scripts.devctl.review_channel.event_store:append_event",
        locking_policy="fcntl_locked_append",
    ),
    AuthorityStoreEntry(
        path=_path_text(DEFAULT_REVIEW_STATE_JSON_REL),
        store_kind="review_state_json",
        writer_ref="dev.scripts.devctl.review_channel.event_reducer:refresh_event_bundle",
        locking_policy="atomic_write_text",
    ),
)
_DUPLICATE_SYSTEM_CLUSTERS = (
    DuplicateSystemCluster(
        cluster_id="plan_row_writers",
        summary=(
            "Multiple product surfaces still request PlanRow mutations, but they now "
            "converge on one locked plan_index_authority writer instead of raw "
            "full-file rewrites."
        ),
        evidence_refs=(
            "dev.scripts.devctl.commands.development.plan_intake:ingest_plan_intent",
            "dev.scripts.devctl.review_channel.packet_plan_integration:maybe_append_packet_plan_row",
            "dev.scripts.devctl.review_channel.packet_creation_binding_plan:bind_packet_to_plan_row",
            "dev.scripts.devctl.runtime.plan_index_authority:upsert_plan_index_row",
        ),
    ),
    DuplicateSystemCluster(
        cluster_id="jsonl_append_helpers",
        summary=(
            "Store-specific append entrypoints still exist, but they now converge on "
            "one locked state_store_authority seam instead of writing raw JSONL "
            "independently."
        ),
        evidence_refs=(
            "dev.scripts.devctl.runtime.state_store_authority:append_json_mapping",
            "dev.scripts.devctl.runtime.plan_intent_ingestion:append_plan_intent_ingestion_receipt",
            "dev.scripts.devctl.runtime.ground_truth_probe_receipt:append_ground_truth_probe_receipt",
            "dev.scripts.devctl.runtime.relaunch_loop_store:append_jsonl",
            "dev.scripts.devctl.governance.ledger_helpers:append_ledger_rows",
            "dev.scripts.devctl.audit_events:emit_devctl_audit_event",
        ),
    ),
    DuplicateSystemCluster(
        cluster_id="review_state_derivations",
        summary=(
            "Review-channel state and projections have multiple derivation/write "
            "paths that must converge on one governed reducer spine."
        ),
        evidence_refs=(
            "dev.scripts.devctl.review_channel.event_store:append_event",
            "dev.scripts.devctl.review_channel.event_reducer:refresh_event_bundle",
            "dev.scripts.devctl.review_channel.projection_bundle:write_projection_bundle_mirrors",
        ),
    ),
)


def run_baseline_inventory(args: Any, *, repo_root: Path = REPO_ROOT) -> int:
    """Build and optionally write the typed baseline authority inventory."""
    receipt = build_baseline_authority_inventory_receipt(
        repo_root=repo_root,
        dry_run=bool(getattr(args, "dry_run", False)),
    )
    path = repo_root / "dev/state/baseline_authority_inventories.jsonl"
    receipt = replace(receipt, receipt_path=str(path.resolve()))
    receipt = replace(receipt, inventory_id=baseline_authority_inventory_id(receipt))
    if not receipt.dry_run:
        append_baseline_authority_inventory_receipt(receipt, repo_root=repo_root)
    output = json.dumps(receipt.to_dict(), indent=2, sort_keys=True)
    return emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )


def build_baseline_authority_inventory_receipt(
    *,
    repo_root: Path,
    dry_run: bool = False,
) -> BaselineAuthorityInventoryReceipt:
    """Collect a typed baseline inventory from current registries and scans."""
    observed_at = utc_timestamp()
    catalog = build_system_catalog(repo_root=repo_root)
    connectivity = build_connectivity_registry_snapshot(repo_root=repo_root)
    connectivity_summary = summarize_connectivity_registry(connectivity)
    state_files = _state_files(repo_root)
    direct_write_sites = _scan_code_sites(
        repo_root,
        patterns=_DIRECT_WRITE_PATTERNS,
        category="direct_write",
    )
    direct_read_sites = _scan_code_sites(
        repo_root,
        patterns=_DIRECT_READ_PATTERNS,
        category="direct_read",
    )
    reducer_sites = _scan_code_sites(
        repo_root,
        patterns=_REDUCER_PATTERNS,
        category="reducer",
    )
    event_producer_sites = _scan_code_sites(
        repo_root,
        patterns=_EVENT_PRODUCER_PATTERNS,
        category="event_producer",
    )
    event_subscriber_sites = _scan_code_sites(
        repo_root,
        patterns=_EVENT_SUBSCRIBER_PATTERNS,
        category="event_subscriber",
    )
    compatibility_shims = _scan_code_sites(
        repo_root,
        patterns=_COMPATIBILITY_PATTERNS,
        category="compatibility",
        max_matches=60,
    )
    receipt = BaselineAuthorityInventoryReceipt(
        inventory_id="",
        recorded_at_utc=observed_at,
        repo_root=str(repo_root.resolve()),
        repo_state_fingerprint=build_repo_state_fingerprint(
            repo_root=repo_root,
            observed_at_utc=observed_at,
        ),
        search_patterns=_SEARCH_PATTERNS,
        file_counts={
            "python_files": len(tuple(_iter_python_files(repo_root))),
            "state_files": len(state_files),
            "workflow_files": len(_workflow_surfaces(repo_root)),
            "generated_projection_paths": len(_generated_projection_paths(repo_root)),
            "direct_write_sites": len(direct_write_sites),
            "direct_read_sites": len(direct_read_sites),
            "reducers": len(reducer_sites),
            "event_producers": len(event_producer_sites),
            "event_subscribers": len(event_subscriber_sites),
            "compatibility_shims": len(compatibility_shims),
        },
        state_store_entries=_STORE_ENTRIES,
        state_files=state_files,
        direct_write_sites=direct_write_sites,
        direct_read_sites=direct_read_sites,
        generated_projection_paths=_generated_projection_paths(repo_root),
        workflow_surfaces=_workflow_surfaces(repo_root),
        check_surfaces=tuple(
            sorted(path for path in CHECK_SCRIPT_RELATIVE_PATHS.values() if path)
        ),
        bundle_surfaces=tuple(sorted(BUNDLE_REGISTRY.keys())),
        packet_kinds=tuple(sorted(VALID_PACKET_KINDS)),
        reducer_sites=reducer_sites,
        event_producer_sites=event_producer_sites,
        event_subscriber_sites=event_subscriber_sites,
        compatibility_shims=compatibility_shims,
        duplicate_system_clusters=_DUPLICATE_SYSTEM_CLUSTERS,
        system_catalog_counts={
            "commands": len(catalog.commands),
            "guards": len(catalog.guards),
            "probes": len(catalog.probes),
            "surfaces": len(catalog.surfaces),
            "contracts": len(catalog.contracts),
        },
        connectivity_registry_counts={
            "source_contract_count": connectivity_summary.source_contract_count,
            "connected_contract_count": connectivity_summary.connected_contract_count,
            "source_field_count": connectivity_summary.source_field_count,
            "zero_reader_field_count": connectivity_summary.zero_reader_field_count,
            "warning_count": connectivity_summary.warning_count,
        },
        status="preview" if dry_run else "accepted",
        dry_run=dry_run,
    )
    return receipt


def _iter_python_files(repo_root: Path):
    for root in _CODE_SCAN_ROOTS:
        abs_root = repo_root / root
        if not abs_root.exists():
            continue
        for path in sorted(abs_root.rglob("*.py")):
            rel = path.relative_to(repo_root).as_posix()
            if "/tests/" in rel or rel.startswith("dev/scripts/devctl/tests/"):
                continue
            yield path


def _scan_code_sites(
    repo_root: Path,
    *,
    patterns: tuple[tuple[str, re.Pattern[str]], ...],
    category: str,
    max_matches: int | None = None,
) -> tuple[InventoryCodeSite, ...]:
    sites: list[InventoryCodeSite] = []
    seen: set[tuple[str, str, int, str, str]] = set()
    for path in _iter_python_files(repo_root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        symbol = ""
        rel_path = path.relative_to(repo_root).as_posix()
        for index, line in enumerate(lines, start=1):
            symbol_match = re.match(r"^\s*(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
            if symbol_match is not None:
                symbol = symbol_match.group(1)
            for pattern_name, regex in patterns:
                if not regex.search(line):
                    continue
                key = (rel_path, symbol, index, pattern_name, category)
                if key in seen:
                    break
                seen.add(key)
                sites.append(
                    InventoryCodeSite(
                        path=rel_path,
                        symbol=symbol,
                        line_number=index,
                        pattern=pattern_name,
                        category=category,
                    )
                )
                break
            if max_matches is not None and len(sites) >= max_matches:
                return tuple(sites)
    return tuple(sites)


def _state_files(repo_root: Path) -> tuple[str, ...]:
    state_root = repo_root / "dev/state"
    paths: list[str] = []
    if state_root.exists():
        for path in sorted(state_root.rglob("*")):
            if path.is_file():
                paths.append(path.relative_to(repo_root).as_posix())
    for relative in (
        _path_text(DEFAULT_REVIEW_EVENT_LOG_REL),
        _path_text(DEFAULT_REVIEW_STATE_JSON_REL),
    ):
        candidate = repo_root / relative
        if candidate.exists():
            paths.append(relative)
    return tuple(sorted(dict.fromkeys(paths)))


def _generated_projection_paths(repo_root: Path) -> tuple[str, ...]:
    paths: list[str] = []
    for relative in _GENERATED_PROJECTION_CANDIDATES:
        candidate = repo_root / relative
        if candidate.exists():
            paths.append(relative.as_posix())
    projections_root = repo_root / _path_text(DEFAULT_REVIEW_PROJECTIONS_DIR_REL)
    if projections_root.exists():
        for path in sorted(projections_root.rglob("*.json")):
            paths.append(path.relative_to(repo_root).as_posix())
    state_json = repo_root / _path_text(DEFAULT_REVIEW_STATE_JSON_REL)
    if state_json.exists():
        paths.append(state_json.relative_to(repo_root).as_posix())
    return tuple(sorted(dict.fromkeys(paths)))


def _workflow_surfaces(repo_root: Path) -> tuple[str, ...]:
    workflows_root = repo_root / ".github/workflows"
    if not workflows_root.exists():
        return ()
    return tuple(
        sorted(path.relative_to(repo_root).as_posix() for path in workflows_root.glob("*"))
    )


__all__ = [
    "build_baseline_authority_inventory_receipt",
    "run_baseline_inventory",
]
