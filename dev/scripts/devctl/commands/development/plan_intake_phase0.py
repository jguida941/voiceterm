"""Phase 0 metadata and authority parsing for plan-intent ingestion."""

from __future__ import annotations

import hashlib
import re
import shlex
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from ...bundles.registry import BUNDLE_REGISTRY
from ...governance.script_catalog_registry import CHECK_SCRIPT_RELATIVE_PATHS
from ...governance.system_catalog import build_system_catalog
from ...runtime.master_plan_contract import PlanRow
from ...runtime.file_hashes import existing_file_hashes
from ...runtime.plan_ingestion_phase0_models import (
    CommandManifestProof,
    GuardMaturityRecord,
    PlanCompositionDispositionEntry,
    ReceiptCoverageInventory,
    RepoStateFingerprint,
)
from ...runtime.plan_intent_ingestion import read_plan_intent_ingestion_receipts
from ...runtime.plan_source_retention import plan_source_snapshot_id
from ...runtime.plan_source_retention_store import read_plan_source_snapshots
from ...runtime.vcs import run_git_capture
from .plan_intake_sources import PlanIntentSource

_HEADING_RE = re.compile(r"^\s*##+\s+(?P<title>.+?)\s*$")
_ROW_BULLET_RE = re.compile(
    r"^\s*-\s*`(?P<row_id>MP[0-9A-Za-z._-]+(?:-[0-9A-Za-z._-]+)*)`\s+"
    r"(?P<title>.+?)\s*$"
)
_BACKTICK_REF_RE = re.compile(r"`([^`]+)`")
_MP_FAMILY_RE = re.compile(r"MP-\d+(?:\.\.\d+)?")
_SHA256_EMPTY = "sha256:" + hashlib.sha256(b"").hexdigest()
SUPPORTED_PLAN_DISPOSITIONS = frozenset(
    {
        "new_closure_row",
        "amends_existing_owner_row",
        "existing_owner_citation_only",
        "adjacent_mp_dependency",
        "portability_blocker",
        "security_blocker",
        "aspirational_until_implemented",
        "deferred_followup",
        "do_not_ingest",
    }
)
SUPPORTED_GUARD_MATURITY_STATES = frozenset(
    {
        "planned",
        "implemented_unregistered",
        "registered_advisory",
        "registered_blocking",
        "retired",
    }
)

_FOUNDATION_REF_SELECTORS: tuple[tuple[str, str], ...] = (
    ("EXC", "EXC"),
    ("CHECKPOINT", "CHECKPOINT"),
    ("DEVELOP", "DEVELOP-NEXT"),
    ("GUARD", "GUARD"),
)
_SECURITY_BLOCKER_ROW_IDS = frozenset(
    {
        "MP377-DAEMON-IPC-SECURITY-HARDENING-S1",
        "MP377-CONTROL-PLANE-THREAT-MODEL-S1",
        "MP377-EVIDENCE-PRIVACY-REDACTION-S1",
        "MP377-GITHUB-WORKFLOW-RECEIPT-BRIDGE-S1",
        "MP377-RELEASE-SUPPLY-CHAIN-SPINE-S1",
        "MP377-GOVERNANCE-ERROR-TAXONOMY-S1",
        "MP377-OPERATOR-INCIDENT-LIFECYCLE-S1",
    }
)
_PORTABILITY_BLOCKER_ROW_IDS = frozenset(
    {
        "MP377-VOICETERM-PRODUCT-NONREGRESSION-S1",
        "MP377-ADOPTER-PILOT-GATE-S1",
        "MP377-VOICETERM-EXTRACTION-S1",
        "MP377-ISLAND-WIRE-OR-RETIRE-S1",
    }
)
_ADJACENT_MP_DEPENDENCY_ROW_IDS = frozenset({"MP377-MP-FAMILY-COMPOSITION-S1"})
_EXISTING_OWNER_CITATION_ONLY_ROW_IDS = frozenset({"MP377-PHASE0-DISPOSITION-MATRIX-S1"})
_ASPIRATIONAL_UNTIL_IMPLEMENTED_ROW_IDS = frozenset()
_AMENDS_EXISTING_OWNER_ROW_IDS = frozenset(
    {
        "MP377-FINAL-AUDIT-MT-COMPOSITION-S1",
        "MP377-RECEIPT-COVERAGE-BACKFILL-S1",
        "MP377-RECEIPT-COVERAGE-INVENTORY-S1",
        "MP377-SUPERSEDED-ROW-DISPOSITION-S1",
    }
)
_DEFERRED_FOLLOWUP_ROW_IDS = frozenset(
    {
        "MP377-VOICETERM-PRODUCT-NONREGRESSION-S1",
        "MP377-ADOPTER-PILOT-GATE-S1",
        "MP377-VOICETERM-EXTRACTION-S1",
        "MP377-ISLAND-WIRE-OR-RETIRE-S1",
        "MP377-DEVSCRIPTS-BADGES-AUDITS-DISPOSITION-S1",
        "MP377-REPO-EXAMPLE-FIXTURE-RETENTION-S1",
    }
)
_KNOWN_SUPERSEDED_ROW_IDS = frozenset(
    {"MP377-P0-T22AB-A", "MP377-P0-T22AB-B", "MP377-P0-T22AB-C"}
)
_GENERATED_PROJECTION_PATHS = ("AGENTS.md", "CLAUDE.md", "bridge.md", "review_only")
_LOCKFILE_NAMES = frozenset(
    {
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "Cargo.lock",
        "poetry.lock",
        "Pipfile.lock",
        "uv.lock",
        "requirements.lock",
    }
)
PLAN_ROW_SCHEMA_LIMIT_WARNING = (
    "Current PlanRow captures identity, provenance, refs, and mutation intent, "
    "but richer dependency, guard, lifecycle, and promotion semantics remain in "
    "PlanCompositionDispositionMatrix/source-snapshot metadata until the schema "
    "migration and dependency-graph rows land."
)


@dataclass(frozen=True, slots=True)
class ParsedPlanAuthorityRow:
    row_id: str
    title: str
    source_line: int


@dataclass(frozen=True, slots=True)
class ParsedPlanAuthoritySections:
    rows_to_ingest: tuple[ParsedPlanAuthorityRow, ...] = ()
    composition_anchor_refs: tuple[str, ...] = ()
    packet_binding_refs: tuple[str, ...] = ()
    adjacent_mp_families: tuple[str, ...] = ()
    existing_today_commands: tuple[str, ...] = ()
    aspirational_commands: tuple[str, ...] = ()
    rows_section_present: bool = False
    unparsed_row_bullets: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PlanIntakePhase0ValidationError(ValueError):
    reason: str

    def __str__(self) -> str:
        return self.reason


@dataclass(frozen=True, slots=True)
class Phase0IntakeMetadata:
    composition_disposition_matrix: tuple[PlanCompositionDispositionEntry, ...]
    command_manifest_proofs: tuple[CommandManifestProof, ...]
    guard_maturity_records: tuple[GuardMaturityRecord, ...]
    repo_state_fingerprint: RepoStateFingerprint
    receipt_coverage_inventory: ReceiptCoverageInventory
    schema_limit_warning: str = PLAN_ROW_SCHEMA_LIMIT_WARNING

    def entry_for_row(self, row_id: str) -> PlanCompositionDispositionEntry | None:
        for entry in self.composition_disposition_matrix:
            if entry.row_id == row_id:
                return entry
        return None


def parse_plan_authority_sections(text: str) -> ParsedPlanAuthoritySections:
    """Parse the bounded authority sections from the consolidated plan markdown."""
    rows: list[ParsedPlanAuthorityRow] = []
    composition_refs: list[str] = []
    packet_refs: list[str] = []
    adjacent_mp_families: list[str] = []
    existing_today_commands: list[str] = []
    aspirational_commands: list[str] = []
    unparsed_row_bullets: list[str] = []
    section = ""
    command_section = ""
    in_code_block = False
    rows_section_present = False
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        heading = _HEADING_RE.match(line)
        if heading is not None:
            section = _normalize_heading(heading.group("title"))
            command_section = ""
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if stripped.endswith(":"):
            normalized = _normalize_heading(stripped)
            if normalized in {
                "required existing-row composition anchors",
                "required packet-binding citations",
                "adjacent mp-family precedence",
                "rows to ingest from this plan",
            }:
                section = normalized
                command_section = ""
                if normalized == "rows to ingest from this plan":
                    rows_section_present = True
                continue
            if normalized == "existing today":
                command_section = "existing_today"
                continue
            if normalized == "aspirational until implemented by the named phases":
                command_section = "aspirational"
                continue
        if in_code_block and command_section and stripped.startswith("python3 "):
            if command_section == "existing_today":
                existing_today_commands.append(stripped)
            else:
                aspirational_commands.append(stripped)
            continue
        if not stripped.startswith("-"):
            continue
        if section == "rows to ingest from this plan":
            match = _ROW_BULLET_RE.match(line)
            if match is not None:
                rows.append(
                    ParsedPlanAuthorityRow(
                        row_id=match.group("row_id").strip(),
                        title=match.group("title").strip(),
                        source_line=index,
                    )
                )
            elif stripped.startswith("- "):
                unparsed_row_bullets.append(f"line {index}: {stripped}")
            continue
        if section == "required existing-row composition anchors":
            composition_refs.extend(_backtick_refs(line))
            continue
        if section == "required packet-binding citations":
            packet_refs.extend(
                ref for ref in _backtick_refs(line) if ref.startswith("PKT-BIND-")
            )
            continue
        if section == "adjacent mp-family precedence":
            adjacent_mp_families.extend(_MP_FAMILY_RE.findall(line))
    return ParsedPlanAuthoritySections(
        rows_to_ingest=tuple(rows),
        composition_anchor_refs=_dedupe(composition_refs),
        packet_binding_refs=_dedupe(packet_refs),
        adjacent_mp_families=_dedupe(adjacent_mp_families),
        existing_today_commands=_dedupe(existing_today_commands),
        aspirational_commands=_dedupe(aspirational_commands),
        rows_section_present=rows_section_present,
        unparsed_row_bullets=_dedupe(unparsed_row_bullets),
    )


def build_phase0_metadata(
    *,
    repo_root: Path,
    source: PlanIntentSource,
    source_hash: str,
    observed_at: str,
    rows: tuple[PlanRow, ...],
    existing_rows: tuple[PlanRow, ...],
    receipt_store_path: Path,
    snapshot_store_path: Path,
    authority_sections: ParsedPlanAuthoritySections | None = None,
) -> Phase0IntakeMetadata:
    """Build additive receipt metadata for phase-0-safe plan ingestion."""
    sections = authority_sections or parse_plan_authority_sections(source.body)
    validate_phase0_authority_sections(sections)
    matrix = tuple(
        _build_disposition_entry(
            row,
            source=source,
            source_hash=source_hash,
            existing_rows=existing_rows,
            sections=sections,
        )
        for row in rows
    )
    command_manifest_proofs = _build_command_manifest_proofs(
        repo_root=repo_root,
        sections=sections,
    )
    guard_maturity_records = _build_guard_maturity_records(command_manifest_proofs)
    repo_state_fingerprint = build_repo_state_fingerprint(
        repo_root=repo_root,
        observed_at_utc=observed_at,
    )
    receipt_coverage_inventory = build_receipt_coverage_inventory(
        existing_rows=existing_rows,
        receipt_store_path=receipt_store_path,
        snapshot_store_path=snapshot_store_path,
    )
    metadata = Phase0IntakeMetadata(
        composition_disposition_matrix=matrix,
        command_manifest_proofs=command_manifest_proofs,
        guard_maturity_records=guard_maturity_records,
        repo_state_fingerprint=repo_state_fingerprint,
        receipt_coverage_inventory=receipt_coverage_inventory,
    )
    validate_phase0_metadata(
        rows=rows,
        metadata=metadata,
        sections=sections,
        existing_rows=existing_rows,
    )
    return metadata


def validate_phase0_authority_sections(sections: ParsedPlanAuthoritySections) -> None:
    """Fail fast when the bounded authority section is malformed."""
    if sections.unparsed_row_bullets:
        raise PlanIntakePhase0ValidationError(
            "rows_to_ingest_contains_unparseable_bullets"
        )
    row_ids = [row.row_id for row in sections.rows_to_ingest]
    duplicates = sorted(
        row_id for row_id, count in Counter(row_ids).items() if count > 1
    )
    if duplicates:
        raise PlanIntakePhase0ValidationError(
            "rows_to_ingest_contains_duplicate_row_ids"
        )


def validate_phase0_metadata(
    *,
    rows: tuple[PlanRow, ...],
    metadata: Phase0IntakeMetadata,
    sections: ParsedPlanAuthoritySections,
    existing_rows: tuple[PlanRow, ...] = (),
) -> None:
    """Validate Phase 0 metadata against the plan's acceptance conditions."""
    row_ids = tuple(row.row_id for row in rows)
    matrix_row_ids = tuple(
        entry.row_id for entry in metadata.composition_disposition_matrix
    )
    if matrix_row_ids != row_ids:
        raise PlanIntakePhase0ValidationError(
            "phase0_composition_matrix_row_mismatch"
        )
    unsupported_dispositions = [
        entry.row_id
        for entry in metadata.composition_disposition_matrix
        if entry.disposition not in SUPPORTED_PLAN_DISPOSITIONS
    ]
    if unsupported_dispositions:
        raise PlanIntakePhase0ValidationError("phase0_unknown_disposition")
    if sections.rows_section_present and len(sections.rows_to_ingest) != len(rows):
        raise PlanIntakePhase0ValidationError("rows_to_ingest_row_count_mismatch")
    existing_row_ids = {row.row_id for row in existing_rows}
    duplicate_owner_claims = [
        entry.row_id
        for entry in metadata.composition_disposition_matrix
        if entry.row_id in existing_row_ids and entry.disposition == "new_closure_row"
    ]
    if duplicate_owner_claims:
        raise PlanIntakePhase0ValidationError(
            "phase0_existing_owner_row_marked_new_closure"
        )
    missing_existing_today_proofs = [
        proof.command
        for proof in metadata.command_manifest_proofs
        if proof.classification == "existing_today"
        and proof.proof_status in {"planned", "missing_manifest_entry"}
    ]
    if missing_existing_today_proofs:
        raise PlanIntakePhase0ValidationError(
            "existing_today_command_missing_manifest_proof"
        )
    unsupported_guard_states = [
        record.guard_id
        for record in metadata.guard_maturity_records
        if record.maturity not in SUPPORTED_GUARD_MATURITY_STATES
    ]
    if unsupported_guard_states:
        raise PlanIntakePhase0ValidationError("unsupported_guard_maturity_state")


def build_repo_state_fingerprint(
    *,
    repo_root: Path,
    observed_at_utc: str,
) -> RepoStateFingerprint:
    """Capture a best-effort repo fingerprint without blocking non-git tests."""
    worktree_identity = str(repo_root.resolve())
    head_sha = _git_stdout(repo_root, "rev-parse", "HEAD")
    branch = _git_stdout(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    upstream = _git_stdout(
        repo_root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
    )
    merge_base_sha = (
        _git_stdout(repo_root, "merge-base", "HEAD", upstream) if upstream else ""
    )
    staged_diff_hash = _git_hash(repo_root, "diff", "--cached", "--binary", "--no-ext-diff")
    unstaged_diff_hash = _git_hash(repo_root, "diff", "--binary", "--no-ext-diff")
    untracked_manifest_hash = _git_hash(
        repo_root,
        "ls-files",
        "--others",
        "--exclude-standard",
    )
    ignored_governed_artifact_hash = _ignored_governed_artifact_hash(repo_root)
    return RepoStateFingerprint(
        head_sha=head_sha,
        branch=branch,
        merge_base_sha=merge_base_sha,
        worktree_identity=worktree_identity,
        staged_diff_hash=staged_diff_hash,
        unstaged_diff_hash=unstaged_diff_hash,
        untracked_manifest_hash=untracked_manifest_hash,
        ignored_governed_artifact_hash=ignored_governed_artifact_hash,
        submodule_or_nested_repo_manifest=_submodule_or_nested_repo_manifest(repo_root),
        generated_projection_hashes=_existing_file_hashes(
            repo_root,
            _GENERATED_PROJECTION_PATHS,
        ),
        dependency_lockfile_hashes=_dependency_lockfile_hashes(repo_root),
        observed_at_utc=observed_at_utc,
        dirty_policy="best_effort_worktree_fingerprint",
    )


def build_receipt_coverage_inventory(
    *,
    existing_rows: tuple[PlanRow, ...],
    receipt_store_path: Path,
    snapshot_store_path: Path,
) -> ReceiptCoverageInventory:
    """Summarize which existing MP-377 rows already have durable proof."""
    rows = tuple(row for row in existing_rows if row.row_id.startswith("MP377"))
    receipts = read_plan_intent_ingestion_receipts(receipt_store_path)
    snapshots = read_plan_source_snapshots(snapshot_store_path)
    receipt_backed_row_ids = {
        row_id
        for receipt in receipts
        if str(receipt.get("status") or "").strip() in {"accepted", "duplicate", "obsolete"}
        for row_id in receipt.get("row_ids") or ()
        if str(row_id).startswith("MP377")
    }
    snapshot_backed_row_ids = {
        snapshot.plan_row_id for snapshot in snapshots if snapshot.plan_row_id.startswith("MP377")
    }
    accepted_receipt_rows: list[str] = []
    packet_binding_only_rows: list[str] = []
    source_snapshot_only_rows: list[str] = []
    superseded_rows: list[str] = []
    deferred_rows: list[str] = []
    missing_proof_rows: list[str] = []
    for row in rows:
        if _row_is_superseded(row):
            superseded_rows.append(row.row_id)
            continue
        if row.status == "deferred":
            deferred_rows.append(row.row_id)
            continue
        if row.row_id in receipt_backed_row_ids:
            accepted_receipt_rows.append(row.row_id)
            continue
        if row.sourced_from_packets and row.row_id not in snapshot_backed_row_ids:
            packet_binding_only_rows.append(row.row_id)
            continue
        if row.row_id in snapshot_backed_row_ids:
            source_snapshot_only_rows.append(row.row_id)
            continue
        missing_proof_rows.append(row.row_id)
    return ReceiptCoverageInventory(
        total_mp377_rows=len(rows),
        accepted_receipt_rows=tuple(sorted(accepted_receipt_rows)),
        packet_binding_only_rows=tuple(sorted(packet_binding_only_rows)),
        source_snapshot_only_rows=tuple(sorted(source_snapshot_only_rows)),
        superseded_rows=tuple(sorted(superseded_rows)),
        deferred_rows=tuple(sorted(deferred_rows)),
        missing_proof_rows=tuple(sorted(missing_proof_rows)),
    )


def _build_command_manifest_proofs(
    *,
    repo_root: Path,
    sections: ParsedPlanAuthoritySections,
) -> tuple[CommandManifestProof, ...]:
    commands = list(sections.existing_today_commands) + list(sections.aspirational_commands)
    if not commands:
        return ()
    catalog = build_system_catalog(repo_root=repo_root)
    command_names = {entry.name for entry in catalog.commands}
    proofs: list[CommandManifestProof] = []
    for command in sections.existing_today_commands:
        proofs.append(
            _command_manifest_proof(
                command,
                classification="existing_today",
                repo_root=repo_root,
                command_names=command_names,
            )
        )
    for command in sections.aspirational_commands:
        proofs.append(
            _command_manifest_proof(
                command,
                classification="aspirational_until_implemented",
                repo_root=repo_root,
                command_names=command_names,
            )
        )
    return tuple(proofs)


def _command_manifest_proof(
    command: str,
    *,
    classification: str,
    repo_root: Path,
    command_names: set[str],
) -> CommandManifestProof:
    tokens = _safe_split(command)
    bundle_refs = _bundle_refs_for_command(command)
    if tokens[:2] == ["python3", "-c"]:
        return CommandManifestProof(
            command=command,
            classification=classification,
            registry_owner="python_inline",
            proof_status="manual_smoke_command",
            resolved_entry="-c",
            bundle_refs=bundle_refs,
        )
    if len(tokens) >= 2 and tokens[0] == "python3" and tokens[1].startswith(
        "dev/scripts/checks/"
    ):
        relative_path = tokens[1]
        script_id = _check_script_id_for_relative_path(relative_path)
        if script_id:
            return CommandManifestProof(
                command=command,
                classification=classification,
                registry_owner="check_script_catalog",
                proof_status=(
                    "registered_blocking"
                    if bundle_refs
                    else "registered_advisory"
                ),
                resolved_entry=script_id,
                bundle_refs=bundle_refs,
            )
        proof_status = (
            "implemented_unregistered"
            if (repo_root / relative_path).exists()
            else _planned_or_missing(classification)
        )
        return CommandManifestProof(
            command=command,
            classification=classification,
            registry_owner="filesystem",
            proof_status=proof_status,
            resolved_entry=relative_path,
            bundle_refs=bundle_refs,
        )
    if tokens[:2] == ["python3", "dev/scripts/devctl.py"] and len(tokens) >= 3:
        subcommand = tokens[2]
        proof_status = (
            "registered_command"
            if subcommand in command_names
            else _planned_or_missing(classification)
        )
        resolved_entry = subcommand
        if subcommand == "demo" and len(tokens) >= 4:
            resolved_entry = f"{subcommand}:{tokens[3]}"
        return CommandManifestProof(
            command=command,
            classification=classification,
            registry_owner="system_catalog.command",
            proof_status=proof_status,
            resolved_entry=resolved_entry,
            bundle_refs=bundle_refs,
        )
    return CommandManifestProof(
        command=command,
        classification=classification,
        registry_owner="unclassified",
        proof_status=_planned_or_missing(classification),
        resolved_entry="",
        bundle_refs=bundle_refs,
    )


def _build_guard_maturity_records(
    command_manifest_proofs: tuple[CommandManifestProof, ...],
) -> tuple[GuardMaturityRecord, ...]:
    records: list[GuardMaturityRecord] = []
    for proof in command_manifest_proofs:
        if not proof.command.startswith("python3 dev/scripts/checks/"):
            continue
        if proof.proof_status == "registered_blocking":
            maturity = "registered_blocking"
        elif proof.proof_status == "registered_advisory":
            maturity = "registered_advisory"
        elif proof.proof_status == "retired":
            maturity = "retired"
        elif proof.proof_status == "implemented_unregistered":
            maturity = "implemented_unregistered"
        else:
            maturity = "planned"
        records.append(
            GuardMaturityRecord(
                guard_id=proof.resolved_entry or _relative_check_path_from_command(proof.command),
                maturity=maturity,
                relative_path=_relative_check_path_from_command(proof.command),
                source_command=proof.command,
                bundle_refs=proof.bundle_refs,
            )
        )
    return tuple(records)


def _build_disposition_entry(
    row: PlanRow,
    *,
    source: PlanIntentSource,
    source_hash: str,
    existing_rows: tuple[PlanRow, ...],
    sections: ParsedPlanAuthoritySections,
) -> PlanCompositionDispositionEntry:
    existing_by_id = {item.row_id: item for item in existing_rows}
    existing_row = existing_by_id.get(row.row_id)
    disposition = _disposition_for_row(
        row.row_id,
        existing_row=existing_row,
        sections=sections,
    )
    if not disposition:
        raise PlanIntakePhase0ValidationError("phase0_disposition_unclassified")
    phase_allowed_to_mutate = _phase_allowed_to_mutate(row.row_id)
    phase_allowed_to_block = _phase_allowed_to_block(
        row.row_id,
        disposition=disposition,
        phase_allowed_to_mutate=phase_allowed_to_mutate,
    )
    return PlanCompositionDispositionEntry(
        row_id=row.row_id,
        disposition=disposition,
        owning_mp_family=_owning_mp_family(
            row.row_id,
            disposition=disposition,
            sections=sections,
        ),
        existing_owner_row_refs=_existing_owner_refs(
            row.row_id,
            title=row.title,
            sections=sections,
            existing_row=existing_row,
        ),
        packet_binding_refs=_packet_binding_refs(source=source, sections=sections),
        source_snapshot_ref=_source_snapshot_ref(
            row_id=row.row_id,
            source=source,
            source_hash=source_hash,
        ),
        why_not_duplicate=_why_not_duplicate(
            row.row_id,
            disposition=disposition,
            existing_row=existing_row,
        ),
        phase_allowed_to_block=phase_allowed_to_block,
        phase_allowed_to_mutate=phase_allowed_to_mutate,
    )


def _disposition_for_row(
    row_id: str,
    *,
    existing_row: PlanRow | None,
    sections: ParsedPlanAuthoritySections,
) -> str:
    if row_id in _KNOWN_SUPERSEDED_ROW_IDS:
        return "do_not_ingest"
    if row_id in _SECURITY_BLOCKER_ROW_IDS:
        return "security_blocker"
    if row_id in _PORTABILITY_BLOCKER_ROW_IDS:
        return "portability_blocker"
    if row_id in _EXISTING_OWNER_CITATION_ONLY_ROW_IDS:
        return "existing_owner_citation_only"
    if row_id in _ADJACENT_MP_DEPENDENCY_ROW_IDS:
        return "adjacent_mp_dependency"
    if row_id in _ASPIRATIONAL_UNTIL_IMPLEMENTED_ROW_IDS:
        return "aspirational_until_implemented"
    if row_id in _DEFERRED_FOLLOWUP_ROW_IDS:
        return "deferred_followup"
    if row_id in _AMENDS_EXISTING_OWNER_ROW_IDS:
        return "amends_existing_owner_row"
    if existing_row is not None:
        return "amends_existing_owner_row"
    if not sections.rows_to_ingest or row_id in {
        item.row_id for item in sections.rows_to_ingest
    }:
        return "new_closure_row"
    return ""


def _owning_mp_family(
    row_id: str,
    *,
    disposition: str,
    sections: ParsedPlanAuthoritySections,
) -> str:
    if disposition == "adjacent_mp_dependency" and sections.adjacent_mp_families:
        return ",".join(sections.adjacent_mp_families)
    if row_id.startswith("MP377"):
        return "MP-377"
    match = _MP_FAMILY_RE.search(row_id)
    return match.group(0) if match is not None else "unknown"


def _existing_owner_refs(
    row_id: str,
    *,
    title: str,
    sections: ParsedPlanAuthoritySections,
    existing_row: PlanRow | None,
) -> tuple[str, ...]:
    if existing_row is not None:
        return (existing_row.row_id,)
    refs = list(_foundation_owner_refs(sections.composition_anchor_refs))
    keyword_pool = f"{row_id} {title}".upper()
    for ref in sections.composition_anchor_refs:
        ref_upper = ref.upper()
        if (
            ("CHECKPOINT" in keyword_pool and "CHECKPOINT" in ref_upper)
            or ("GUARD" in keyword_pool and "GUARD" in ref_upper)
            or ("PACKET" in keyword_pool and "PACKET" in ref_upper)
            or ("DEVELOP" in keyword_pool and "DEVELOP" in ref_upper)
            or ("NEXT" in keyword_pool and "DEVELOP" in ref_upper)
            or ("LIFECYCLE" in keyword_pool and "EXC" in ref_upper)
            or ("EXCEPTION" in keyword_pool and "EXC" in ref_upper)
            or ("OVERRIDE" in keyword_pool and "EXC" in ref_upper)
            or ("EVENT" in keyword_pool and ("T22" in ref_upper or "P1-T0" in ref_upper))
            or ("LIVENESS" in keyword_pool and ("T22" in ref_upper or "P1-T0" in ref_upper))
            or ("BOUNDARY" in keyword_pool and ("T22" in ref_upper or "P1-T0" in ref_upper))
        ):
            refs.append(ref)
    return _dedupe(refs)


def _foundation_owner_refs(composition_anchor_refs: tuple[str, ...]) -> tuple[str, ...]:
    refs: list[str] = []
    upper_refs = {ref.upper(): ref for ref in composition_anchor_refs}
    for _selector, token in _FOUNDATION_REF_SELECTORS:
        for ref_upper, ref in upper_refs.items():
            if token in ref_upper:
                refs.append(ref)
                break
    return _dedupe(refs)


def _packet_binding_refs(
    *,
    source: PlanIntentSource,
    sections: ParsedPlanAuthoritySections,
) -> tuple[str, ...]:
    refs = list(sections.packet_binding_refs)
    packet_id = str(source.packet_payload.get("packet_id") or "").strip()
    if packet_id:
        refs.append(f"packet:{packet_id}")
    return _dedupe(refs)


def _source_snapshot_ref(
    *,
    row_id: str,
    source: PlanIntentSource,
    source_hash: str,
) -> str:
    snapshot_id = plan_source_snapshot_id(
        plan_row_id=row_id,
        source_kind=source.kind,
        source_ref=source.ref,
        source_hash=source_hash,
    )
    return f"plan_source_snapshot:{snapshot_id}"


def _why_not_duplicate(
    row_id: str,
    *,
    disposition: str,
    existing_row: PlanRow | None,
) -> str:
    if row_id == "MP377-PHASE0-DISPOSITION-MATRIX-S1":
        return (
            "Stored as receipt/source-snapshot metadata on ingestion, not as a second "
            "plan-authority store."
        )
    if existing_row is not None or disposition == "amends_existing_owner_row":
        return (
            "Extends existing owner authority through typed receipt and source-snapshot "
            "metadata instead of cloning that authority into a parallel plan."
        )
    if disposition == "existing_owner_citation_only":
        return (
            "Preserves the composition citation in typed receipt metadata while keeping "
            "the owning row as the durable authority surface."
        )
    if disposition == "adjacent_mp_dependency":
        return (
            "Captures upstream/downstream MP-family dependency so MP-377 consumes "
            "adjacent authority instead of forking it."
        )
    if disposition == "aspirational_until_implemented":
        return (
            "Records intended future closure without granting blocking power until the "
            "implementation, registration, and dogfood proof exist."
        )
    if disposition == "security_blocker":
        return (
            "Tracks a security gate as typed plan evidence without elevating adopter "
            "projections or prose into portable authority."
        )
    if disposition == "portability_blocker":
        return (
            "Records extraction and adopter gates in typed state while keeping VoiceTerm "
            "product assumptions outside the portable authority path."
        )
    if disposition == "deferred_followup":
        return (
            "Preserved now for dependency planning, but sequenced for a later phase so it "
            "does not duplicate or prematurely block earlier authority."
        )
    if disposition == "do_not_ingest":
        return (
            "Known superseded or retired authority should stay out of the live ingest "
            "set and remain only as audit evidence."
        )
    return (
        "Introduces missing closure work while citing existing owner families in "
        "receipt/source-snapshot metadata instead of duplicating their durable authority."
    )


def _phase_allowed_to_mutate(row_id: str) -> str:
    if _row_matches(
        row_id,
        (
            "CONSOLIDATION-PLAN-INGEST",
            "FINAL-AUDIT",
            "PHASE0",
            "REPO-BASELINE",
            "STATE-STORE",
            "SCHEMA-MIGRATION",
            "CORRELATION-ID",
            "EVENT-IDEMPOTENCY",
            "RECEIPT-COVERAGE",
            "SUPERSEDED-ROW",
            "REPO-STATE-FINGERPRINT",
        ),
    ):
        return "phase_1"
    if _row_matches(
        row_id,
        (
            "GOVERNANCE-LIFECYCLE",
            "OPERATOR-OVERRIDE",
            "GOVERNED-EXCEPTION",
            "PLAN-INGESTION",
            "PLAN-INDEX-AUTHORITY",
            "RECEIPT-SPINE",
        ),
    ):
        return "phase_2"
    if _row_matches(
        row_id,
        (
            "COMPOSABILITY",
            "UNIQUENESS",
            "SYSTEM-AUDIT-SWARM",
            "GUARD-MATURITY",
            "BRIDGE-PROJECTION-ONLY",
            "STALE-EVIDENCE",
            "CONTEXT-GRAPH",
            "FINDING-LIFECYCLE-CLOSURE",
            "SYNTHESIS-META-LEARNING",
        ),
    ):
        return "phase_3"
    if _row_matches(
        row_id,
        (
            "PLAN-ROW-DEPENDENCY-GRAPH",
            "ROW-SEQUENCING",
            "CROSS-SYSTEM-CONTRACT-GRAPH",
            "CI-CD-DEPENDENCY-PIPELINE",
            "EXCLUSIVE-DOMAIN-AUTHORITY",
            "MP-FAMILY-COMPOSITION",
            "STATE-WRITE-AUTHORITY-CATALOG",
        ),
    ):
        return "phase_4"
    if _row_matches(
        row_id,
        (
            "AGENT-LOOP-BILATERAL",
            "REVIEWER-GROUND-TRUTH",
            "GROUND-TRUTH-PROBE",
            "GATE-CASCADE",
            "AUTOMATION-FLAGGING",
            "SESSION-LIVENESS-WATCHDOG",
        ),
    ):
        return "phase_5"
    if _row_matches(row_id, ("FINAL-BOUNDARY", "SESSION-ITERATION")):
        return "phase_7"
    if _row_matches(
        row_id,
        (
            "EVENT-PRODUCER-CATALOG",
            "AUTOINVAL",
            "PUSH-BASED-EVENTBUS",
            "CHECKPOINT-AUTOMATION-RECEIPT-INVARIANTS",
        ),
    ):
        return "phase_8"
    if _row_matches(
        row_id,
        (
            "THREAT-MODEL",
            "PRIVACY-REDACTION",
            "GITHUB-WORKFLOW",
            "RELEASE-SUPPLY-CHAIN",
            "DAEMON-IPC-SECURITY-HARDENING",
            "VOICETERM-PRODUCT",
            "ADOPTER-PILOT",
            "GOVERNANCE-ERROR-TAXONOMY",
            "OPERATOR-INCIDENT-LIFECYCLE",
        ),
    ):
        return "phase_9"
    if _row_matches(
        row_id,
        (
            "VOICETERM-EXTRACTION",
            "ISLAND-WIRE-OR-RETIRE",
            "DEVSCRIPTS-BADGES-AUDITS-DISPOSITION",
            "REPO-EXAMPLE-FIXTURE-RETENTION",
            "PUBLICATION-SYNC-AUTHORITY",
            "MUTATION-LOOP-ORCHESTRATION",
            "MOBILE-SURFACE-PARITY",
            "CONTROL-PLANE-DAEMON-FACTORY",
            "RALPH-GUARDRAIL-CONTROL-PLANE-DISPOSITION",
            "PROJECTION-RETIREMENT",
        ),
    ):
        return "phase_10"
    return "phase_6"


def _phase_allowed_to_block(
    row_id: str,
    *,
    disposition: str,
    phase_allowed_to_mutate: str,
) -> str:
    if disposition == "do_not_ingest":
        return "never"
    if disposition in {"security_blocker", "portability_blocker"}:
        return phase_allowed_to_mutate
    if "GUARD" in row_id or "CHECK" in row_id or "AUDIT" in row_id:
        return "after_implementation"
    return "after_implementation"


def _row_is_superseded(row: PlanRow) -> bool:
    return bool(row.superseded_by_row) or row.row_id in _KNOWN_SUPERSEDED_ROW_IDS


def _row_matches(row_id: str, tokens: tuple[str, ...]) -> bool:
    upper = row_id.upper()
    return any(token in upper for token in tokens)


def _check_script_id_for_relative_path(relative_path: str) -> str:
    for script_id, rel_path in CHECK_SCRIPT_RELATIVE_PATHS.items():
        if rel_path == relative_path:
            return script_id
    return ""


def _bundle_refs_for_command(command: str) -> tuple[str, ...]:
    refs: list[str] = []
    prefix = _command_bundle_prefix(command)
    for bundle_name, commands in BUNDLE_REGISTRY.items():
        if command in commands:
            refs.append(bundle_name)
            continue
        if prefix and any(item.startswith(prefix) for item in commands):
            refs.append(bundle_name)
    return _dedupe(refs)


def _command_bundle_prefix(command: str) -> str:
    tokens = _safe_split(command)
    if tokens[:2] == ["python3", "dev/scripts/devctl.py"] and len(tokens) >= 3:
        return shlex.join(tokens[:3])
    if len(tokens) >= 2 and tokens[0] == "python3" and tokens[1].startswith(
        "dev/scripts/checks/"
    ):
        return shlex.join(tokens[:2])
    return ""


def _relative_check_path_from_command(command: str) -> str:
    tokens = _safe_split(command)
    if len(tokens) >= 2 and tokens[0] == "python3" and tokens[1].startswith(
        "dev/scripts/checks/"
    ):
        return tokens[1]
    return ""


def _safe_split(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return []


def _planned_or_missing(classification: str) -> str:
    if classification == "existing_today":
        return "missing_manifest_entry"
    return "planned"


def _ignored_governed_artifact_hash(repo_root: Path) -> str:
    code, output, _error = run_git_capture(
        ["status", "--porcelain", "--ignored", "--untracked-files=all"],
        repo_root=repo_root,
    )
    if code != 0:
        return _SHA256_EMPTY
    governed = [
        line[3:].strip()
        for line in output.splitlines()
        if line.startswith("!! ") and line[3:].strip().startswith("dev/")
    ]
    return _hash_text("\n".join(governed))


def _submodule_or_nested_repo_manifest(repo_root: Path) -> tuple[str, ...]:
    entries: list[str] = []
    code, output, _error = run_git_capture(
        ["submodule", "status", "--recursive"],
        repo_root=repo_root,
    )
    if code == 0 and output.strip():
        entries.extend(line.strip() for line in output.splitlines() if line.strip())
    root_git = (repo_root / ".git").resolve()
    for git_path in sorted(repo_root.rglob(".git")):
        try:
            resolved = git_path.resolve()
        except OSError:
            continue
        if resolved == root_git:
            continue
        try:
            rel = git_path.parent.resolve().relative_to(repo_root.resolve())
        except ValueError:
            continue
        entries.append(f"nested:{rel}")
    return _dedupe(entries)


def _existing_file_hashes(
    repo_root: Path,
    relative_paths: tuple[str, ...],
) -> dict[str, str]:
    return existing_file_hashes(repo_root, relative_paths)


def _dependency_lockfile_hashes(repo_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file() or path.name not in _LOCKFILE_NAMES:
            continue
        try:
            relative = str(path.relative_to(repo_root))
        except ValueError:
            continue
        hashes[relative] = _hash_bytes(path.read_bytes())
    return hashes


def _git_stdout(repo_root: Path, *args: str) -> str:
    code, output, _error = run_git_capture(list(args), repo_root=repo_root)
    return output if code == 0 else ""


def _git_hash(repo_root: Path, *args: str) -> str:
    code, output, _error = run_git_capture(list(args), repo_root=repo_root)
    return _hash_text(output if code == 0 else "")


def _backtick_refs(line: str) -> list[str]:
    return [item.strip() for item in _BACKTICK_REF_RE.findall(line) if item.strip()]


def _normalize_heading(value: str) -> str:
    return value.strip().rstrip(":").lower()


def _dedupe(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    ordered: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in ordered:
            ordered.append(text)
    return tuple(ordered)


def _hash_text(value: str) -> str:
    return _hash_bytes(value.encode("utf-8"))


def _hash_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


__all__ = [
    "PLAN_ROW_SCHEMA_LIMIT_WARNING",
    "SUPPORTED_GUARD_MATURITY_STATES",
    "SUPPORTED_PLAN_DISPOSITIONS",
    "ParsedPlanAuthorityRow",
    "ParsedPlanAuthoritySections",
    "Phase0IntakeMetadata",
    "PlanIntakePhase0ValidationError",
    "build_phase0_metadata",
    "build_receipt_coverage_inventory",
    "build_repo_state_fingerprint",
    "parse_plan_authority_sections",
    "validate_phase0_authority_sections",
    "validate_phase0_metadata",
]
