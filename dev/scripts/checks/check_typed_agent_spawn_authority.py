#!/usr/bin/env python3
"""Fail closed when peer-agent spawns lack typed AgentSpawnReceipt authority (A23 G44).

Operator amendment 2026-05-22T23:36Z (delete_after_ingest.md A23) requires
that any peer-agent spawn (codex CLI, claude CLI, or other AI agent CLI) be
backed by typed `AgentSpawnReceipt` evidence composed with an active
`BypassLifecycle` receipt covering `agent_spawn_only` (or broader) scope.

This guard inspects rollout-file evidence under `~/.codex/sessions/<YYYY>/<MM>/<DD>/`
plus the typed receipt stores under `dev/state/agent_spawn_receipts.jsonl`
and `dev/state/agent_termination_receipts.jsonl`, and fails closed when:

1. A peer-agent spawn happened (rollout file appeared, codex CLI started)
   but no `AgentSpawnReceipt` was emitted within the spawn-evidence window
   (default 60s).
2. An `AgentSpawnReceipt` claims a `BypassLifecycle` ref that does not
   exist in `dev/state/bypass_lifecycles.jsonl` or has expired.
3. Multiple live sessions exist for the same provider+role+row without a
   typed reason (per A18 G31 cardinality bounds).
4. A peer session was killed (rollout file modified-then-static and no
   matching live process) without a matching `AgentTerminationReceipt`.

NOTE: `AgentSpawnReceipt` and `AgentTerminationReceipt` are not yet
registered in `contract_registry`. Their dataclass shapes below are
proposed; G44 reads stored mappings via duck-typed accessors so that
typed registration can land without churning the guard.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _shared_iter_jsonl,
        parse_utc as _parse_utc,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _shared_iter_jsonl,
        parse_utc as _parse_utc,
        utc_timestamp,
    )


COMMAND = "check_typed_agent_spawn_authority"
CONTRACT_ID = "TypedAgentSpawnAuthorityGuard"

DEFAULT_SPAWN_EVIDENCE_WINDOW_SECONDS = 60

RULE_SPAWN_WITHOUT_RECEIPT = "spawn_evidence_without_agent_spawn_receipt"
RULE_BYPASS_REF_INVALID = "agent_spawn_receipt_bypass_ref_invalid_or_expired"
RULE_DUPLICATE_LIVE_SESSIONS = "duplicate_live_sessions_for_provider_role_row"
RULE_TERMINATION_RECEIPT_MISSING = "peer_session_killed_without_termination_receipt"

DISPLAY_TEXT = (
    "Typed agent-spawn authority violation. Peer-agent spawns must be "
    "backed by typed AgentSpawnReceipt evidence composed with an active "
    "BypassLifecycle receipt; terminations must emit AgentTerminationReceipt."
)


# ---------------------------------------------------------------------------
# Proposed AgentSpawnReceipt / AgentTerminationReceipt dataclasses
# These shapes are guard-local until typed registration in contract_registry.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AgentSpawnReceipt:
    """Proposed typed receipt for a peer-agent spawn event.

    Pending typed registration in `contract_registry`. This guard treats
    stored mappings under `dev/state/agent_spawn_receipts.jsonl` as
    duck-typed `AgentSpawnReceipt` evidence.
    """

    receipt_id: str
    provider: str
    role: str
    row_id: str
    session_id: str
    rollout_path: str
    bypass_receipt_id: str
    spawned_at_utc: str
    spawner_actor_id: str
    schema_version: int = 1
    contract_id: str = "AgentSpawnReceipt"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AgentTerminationReceipt:
    """Proposed typed receipt for a peer-agent termination event.

    Pending typed registration in `contract_registry`. Stored mappings
    under `dev/state/agent_termination_receipts.jsonl` are duck-typed
    `AgentTerminationReceipt` evidence.
    """

    receipt_id: str
    spawn_receipt_id: str
    session_id: str
    terminated_at_utc: str
    terminator_actor_id: str
    reason: str
    schema_version: int = 1
    contract_id: str = "AgentTerminationReceipt"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SpawnAuthorityViolation:
    rule_id: str
    detail: str
    remediation: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "detail": self.detail,
            "remediation": self.remediation,
            "evidence_refs": list(self.evidence_refs),
        }


def build_report(
    *,
    spawn_evidence: Sequence[Mapping[str, object]] | None = None,
    spawn_receipts: Sequence[Mapping[str, object]] | None = None,
    termination_receipts: Sequence[Mapping[str, object]] | None = None,
    bypass_lifecycles: Sequence[Mapping[str, object]] | None = None,
    rollout_dir: Path | None = None,
    spawn_receipt_path: Path | None = None,
    termination_receipt_path: Path | None = None,
    bypass_lifecycle_path: Path | None = None,
    spawn_evidence_window_seconds: int = DEFAULT_SPAWN_EVIDENCE_WINDOW_SECONDS,
    now: datetime | None = None,
) -> dict[str, object]:
    """Build the G44 report from rollout-file evidence + receipt stores.

    Callers may pass explicit sequences for fully-injected unit testing,
    or rely on default repo-path loading.
    """

    warnings: list[str] = []
    checked_surfaces: list[str] = []
    now_utc = now or datetime.now(timezone.utc)

    if spawn_evidence is None:
        rollout_root = rollout_dir or _default_rollout_dir(now_utc)
        checked_surfaces.append(str(rollout_root))
        spawn_evidence = tuple(_iter_rollout_evidence(rollout_root, warnings))
    if spawn_receipts is None:
        receipt_path = spawn_receipt_path or _default_spawn_receipt_path()
        checked_surfaces.append(str(receipt_path))
        spawn_receipts = tuple(_iter_jsonl(receipt_path, warnings=warnings))
    if termination_receipts is None:
        term_path = termination_receipt_path or _default_termination_receipt_path()
        checked_surfaces.append(str(term_path))
        termination_receipts = tuple(_iter_jsonl(term_path, warnings=warnings))
    if bypass_lifecycles is None:
        bypass_path = bypass_lifecycle_path or _default_bypass_lifecycle_path()
        checked_surfaces.append(str(bypass_path))
        bypass_lifecycles = tuple(_iter_jsonl(bypass_path, warnings=warnings))

    violations: list[SpawnAuthorityViolation] = []

    violations.extend(
        _rule_spawn_without_receipt(
            spawn_evidence=spawn_evidence,
            spawn_receipts=spawn_receipts,
            now=now_utc,
            window_seconds=spawn_evidence_window_seconds,
        )
    )
    violations.extend(
        _rule_bypass_ref_invalid(
            spawn_receipts=spawn_receipts,
            bypass_lifecycles=bypass_lifecycles,
            now=now_utc,
        )
    )
    violations.extend(
        _rule_duplicate_live_sessions(
            spawn_receipts=spawn_receipts,
            termination_receipts=termination_receipts,
        )
    )
    violations.extend(
        _rule_termination_receipt_missing(
            spawn_evidence=spawn_evidence,
            spawn_receipts=spawn_receipts,
            termination_receipts=termination_receipts,
            now=now_utc,
        )
    )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "spawn_evidence_count": len(spawn_evidence),
        "spawn_receipt_count": len(spawn_receipts),
        "termination_receipt_count": len(termination_receipts),
        "bypass_lifecycle_count": len(bypass_lifecycles),
        "spawn_evidence_window_seconds": spawn_evidence_window_seconds,
        "checked_surfaces": checked_surfaces,
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Rule helpers
# ---------------------------------------------------------------------------


def _rule_spawn_without_receipt(
    *,
    spawn_evidence: Sequence[Mapping[str, object]],
    spawn_receipts: Sequence[Mapping[str, object]],
    now: datetime,
    window_seconds: int,
) -> tuple[SpawnAuthorityViolation, ...]:
    receipts_by_session = _index_by_session(spawn_receipts)
    receipts_by_rollout = _index_by_rollout(spawn_receipts)
    threshold_ts = now.timestamp() - window_seconds
    violations: list[SpawnAuthorityViolation] = []
    for evidence in spawn_evidence:
        session_id = str(evidence.get("session_id") or "").strip()
        rollout_path = str(evidence.get("rollout_path") or "").strip()
        spawned_at = _parse_utc(str(evidence.get("spawned_at_utc") or ""))
        if spawned_at is None:
            continue
        if spawned_at.timestamp() > threshold_ts:
            # Spawn is fresh; receipt may still be inbound. Treat as
            # within the grace window unless we have a receipt anyway.
            if not _receipt_covers_evidence(
                evidence, receipts_by_session, receipts_by_rollout
            ):
                # Fresh spawn without a receipt: still pending grace window.
                continue
            continue
        if _receipt_covers_evidence(
            evidence, receipts_by_session, receipts_by_rollout
        ):
            continue
        evidence_ref = session_id or rollout_path
        violations.append(
            SpawnAuthorityViolation(
                rule_id=RULE_SPAWN_WITHOUT_RECEIPT,
                detail=(
                    f"rollout evidence for session={session_id!r} "
                    f"rollout_path={rollout_path!r} has no AgentSpawnReceipt "
                    f"within {window_seconds}s of spawned_at_utc"
                ),
                remediation=(
                    "Emit an AgentSpawnReceipt via the typed spawn command "
                    "before peer agent activity continues; raw codex CLI "
                    "launches without a typed receipt are forbidden."
                ),
                evidence_refs=(evidence_ref,) if evidence_ref else (),
            )
        )
    return tuple(violations)


def _rule_bypass_ref_invalid(
    *,
    spawn_receipts: Sequence[Mapping[str, object]],
    bypass_lifecycles: Sequence[Mapping[str, object]],
    now: datetime,
) -> tuple[SpawnAuthorityViolation, ...]:
    bypass_index = _index_bypass_receipts(bypass_lifecycles)
    violations: list[SpawnAuthorityViolation] = []
    for receipt in spawn_receipts:
        receipt_id = str(receipt.get("receipt_id") or "").strip()
        bypass_id = str(receipt.get("bypass_receipt_id") or "").strip()
        if not bypass_id:
            violations.append(
                SpawnAuthorityViolation(
                    rule_id=RULE_BYPASS_REF_INVALID,
                    detail=(
                        f"AgentSpawnReceipt receipt_id={receipt_id!r} "
                        "is missing a bypass_receipt_id reference"
                    ),
                    remediation=(
                        "Spawn receipts must reference an active "
                        "BypassLifecycle receipt via bypass_receipt_id."
                    ),
                    evidence_refs=(receipt_id,) if receipt_id else (),
                )
            )
            continue
        bypass = bypass_index.get(bypass_id)
        if bypass is None:
            violations.append(
                SpawnAuthorityViolation(
                    rule_id=RULE_BYPASS_REF_INVALID,
                    detail=(
                        f"AgentSpawnReceipt receipt_id={receipt_id!r} "
                        f"references bypass_receipt_id={bypass_id!r} which "
                        "does not exist in bypass_lifecycles.jsonl"
                    ),
                    remediation=(
                        "Issue a BypassLifecycle receipt before emitting "
                        "an AgentSpawnReceipt."
                    ),
                    evidence_refs=(receipt_id, bypass_id),
                )
            )
            continue
        if _bypass_expired(bypass, now):
            expires_at = str(bypass.get("expires_at_utc") or "")
            violations.append(
                SpawnAuthorityViolation(
                    rule_id=RULE_BYPASS_REF_INVALID,
                    detail=(
                        f"AgentSpawnReceipt receipt_id={receipt_id!r} "
                        f"references bypass_receipt_id={bypass_id!r} which "
                        f"expired at {expires_at!r}"
                    ),
                    remediation=(
                        "Refresh BypassLifecycle authority before peer-"
                        "agent spawn continues."
                    ),
                    evidence_refs=(receipt_id, bypass_id),
                )
            )
    return tuple(violations)


def _rule_duplicate_live_sessions(
    *,
    spawn_receipts: Sequence[Mapping[str, object]],
    termination_receipts: Sequence[Mapping[str, object]],
) -> tuple[SpawnAuthorityViolation, ...]:
    terminated_spawns = _terminated_spawn_receipt_ids(termination_receipts)
    grouped: dict[tuple[str, str, str], list[Mapping[str, object]]] = {}
    for receipt in spawn_receipts:
        if str(receipt.get("receipt_id") or "") in terminated_spawns:
            continue
        if str(receipt.get("duplicate_reason") or "").strip():
            # Typed reason recorded; A18 G31 cardinality bounds satisfied.
            continue
        provider = str(receipt.get("provider") or "").strip().lower()
        role = str(receipt.get("role") or "").strip().lower()
        row_id = str(receipt.get("row_id") or "").strip()
        if not (provider and role and row_id):
            continue
        key = (provider, role, row_id)
        grouped.setdefault(key, []).append(receipt)

    violations: list[SpawnAuthorityViolation] = []
    for (provider, role, row_id), live_receipts in grouped.items():
        if len(live_receipts) < 2:
            continue
        ids = tuple(
            str(receipt.get("receipt_id") or "") for receipt in live_receipts
        )
        violations.append(
            SpawnAuthorityViolation(
                rule_id=RULE_DUPLICATE_LIVE_SESSIONS,
                detail=(
                    f"{len(live_receipts)} live AgentSpawnReceipts share "
                    f"provider={provider!r} role={role!r} row_id={row_id!r} "
                    "without a typed duplicate_reason (A18 G31)"
                ),
                remediation=(
                    "Terminate the duplicate session via the typed kill "
                    "path or record a duplicate_reason that satisfies the "
                    "A18 G31 cardinality bound."
                ),
                evidence_refs=ids,
            )
        )
    return tuple(violations)


def _rule_termination_receipt_missing(
    *,
    spawn_evidence: Sequence[Mapping[str, object]],
    spawn_receipts: Sequence[Mapping[str, object]],
    termination_receipts: Sequence[Mapping[str, object]],
    now: datetime,
) -> tuple[SpawnAuthorityViolation, ...]:
    terminated_spawns = _terminated_spawn_receipt_ids(termination_receipts)
    killed_sessions = {
        str(evidence.get("session_id") or "").strip(): evidence
        for evidence in spawn_evidence
        if _evidence_is_killed(evidence)
    }
    receipts_by_session = _index_by_session(spawn_receipts)
    violations: list[SpawnAuthorityViolation] = []
    for session_id, evidence in killed_sessions.items():
        if not session_id:
            continue
        receipt = receipts_by_session.get(session_id)
        if receipt is None:
            # Spawn-without-receipt is reported by rule 1; do not double-count.
            continue
        receipt_id = str(receipt.get("receipt_id") or "")
        if receipt_id and receipt_id in terminated_spawns:
            continue
        rollout_path = str(evidence.get("rollout_path") or "")
        violations.append(
            SpawnAuthorityViolation(
                rule_id=RULE_TERMINATION_RECEIPT_MISSING,
                detail=(
                    f"session_id={session_id!r} (rollout {rollout_path!r}) "
                    "killed without matching AgentTerminationReceipt for "
                    f"spawn receipt_id={receipt_id!r}"
                ),
                remediation=(
                    "Emit an AgentTerminationReceipt via the typed kill "
                    "command when a peer session terminates."
                ),
                evidence_refs=(receipt_id, session_id),
            )
        )
    return tuple(violations)


# ---------------------------------------------------------------------------
# Index + classification helpers
# ---------------------------------------------------------------------------


def _index_by_session(
    receipts: Sequence[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    index: dict[str, Mapping[str, object]] = {}
    for receipt in receipts:
        session_id = str(receipt.get("session_id") or "").strip()
        if not session_id:
            continue
        index.setdefault(session_id, receipt)
    return index


def _index_by_rollout(
    receipts: Sequence[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    index: dict[str, Mapping[str, object]] = {}
    for receipt in receipts:
        rollout_path = str(receipt.get("rollout_path") or "").strip()
        if not rollout_path:
            continue
        index.setdefault(rollout_path, receipt)
    return index


def _receipt_covers_evidence(
    evidence: Mapping[str, object],
    receipts_by_session: Mapping[str, Mapping[str, object]],
    receipts_by_rollout: Mapping[str, Mapping[str, object]],
) -> bool:
    session_id = str(evidence.get("session_id") or "").strip()
    if session_id and session_id in receipts_by_session:
        return True
    rollout_path = str(evidence.get("rollout_path") or "").strip()
    if rollout_path and rollout_path in receipts_by_rollout:
        return True
    return False


def _index_bypass_receipts(
    lifecycles: Sequence[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    index: dict[str, Mapping[str, object]] = {}
    for lifecycle in lifecycles:
        receipt = lifecycle.get("receipt")
        if not isinstance(receipt, Mapping):
            continue
        receipt_id = str(receipt.get("receipt_id") or "").strip()
        if not receipt_id:
            continue
        index.setdefault(receipt_id, receipt)
    return index


def _bypass_expired(bypass: Mapping[str, object], now: datetime) -> bool:
    revoked_at = str(bypass.get("revoked_at_utc") or "").strip()
    if revoked_at:
        return True
    expires_at = _parse_utc(str(bypass.get("expires_at_utc") or ""))
    if expires_at is None:
        return False
    return expires_at <= now


def _terminated_spawn_receipt_ids(
    termination_receipts: Sequence[Mapping[str, object]],
) -> set[str]:
    ids: set[str] = set()
    for receipt in termination_receipts:
        spawn_id = str(receipt.get("spawn_receipt_id") or "").strip()
        if spawn_id:
            ids.add(spawn_id)
    return ids


def _evidence_is_killed(evidence: Mapping[str, object]) -> bool:
    killed = evidence.get("killed")
    if isinstance(killed, bool):
        return killed
    state = str(evidence.get("state") or "").strip().lower()
    return state in {"killed", "terminated", "stopped"}


# ---------------------------------------------------------------------------
# Rollout discovery
# ---------------------------------------------------------------------------


def _iter_rollout_evidence(
    rollout_dir: Path,
    warnings: list[str],
) -> Iterable[Mapping[str, object]]:
    if not rollout_dir.exists():
        warnings.append(f"rollout dir missing: {rollout_dir}")
        return ()
    files = sorted(rollout_dir.glob("rollout-*.jsonl"))
    if not files:
        return ()
    records: list[Mapping[str, object]] = []
    for path in files:
        try:
            spawned_at = _parse_rollout_timestamp(path.name)
        except ValueError:
            continue
        session_id = _parse_rollout_session_id(path.name)
        try:
            stat = path.stat()
        except OSError:
            continue
        killed = _rollout_is_stale(stat.st_mtime, datetime.now(timezone.utc))
        records.append(
            {
                "session_id": session_id,
                "rollout_path": str(path),
                "spawned_at_utc": spawned_at,
                "killed": killed,
                "mtime_epoch": stat.st_mtime,
                "provider": "codex",
            }
        )
    return records


def _parse_rollout_timestamp(name: str) -> str:
    # rollout-2026-05-22T18-34-39-019e51d3-...jsonl
    if not name.startswith("rollout-"):
        raise ValueError(name)
    stem = name[len("rollout-"):]
    if len(stem) < 19:
        raise ValueError(name)
    date_part = stem[:10]
    time_part = stem[11:19].replace("-", ":")
    iso = f"{date_part}T{time_part}Z"
    # Validate
    _parse_utc(iso)
    return iso


def _parse_rollout_session_id(name: str) -> str:
    # rollout-2026-05-22T18-34-39-019e51d3-8edb-71e3-a8be-640ddac33546.jsonl
    # After strip: 2026-05-22T18-34-39-019e51d3-8edb-71e3-a8be-640ddac33546
    # Split by '-' yields 10 parts: 5 date/time tokens then 5 UUID tokens.
    if not name.startswith("rollout-") or not name.endswith(".jsonl"):
        return ""
    stem = name[len("rollout-"):-len(".jsonl")]
    parts = stem.split("-")
    if len(parts) < 10:
        return ""
    uuid_parts = parts[5:10]
    return "-".join(uuid_parts)


def _rollout_is_stale(
    mtime_epoch: float,
    now: datetime,
    stale_seconds: int = 600,
) -> bool:
    return (now.timestamp() - mtime_epoch) >= stale_seconds


# ---------------------------------------------------------------------------
# Misc utilities
# ---------------------------------------------------------------------------


def _iter_jsonl(
    path: Path, *, warnings: list[str]
) -> Iterable[Mapping[str, object]]:
    return tuple(
        _shared_iter_jsonl(path, warnings=warnings, missing_label="jsonl missing")
    )


def _default_rollout_dir(now: datetime | None = None) -> Path:
    now_utc = now or datetime.now(timezone.utc)
    home = Path(os.path.expanduser("~"))
    return (
        home
        / ".codex"
        / "sessions"
        / f"{now_utc.year:04d}"
        / f"{now_utc.month:02d}"
        / f"{now_utc.day:02d}"
    )


def _default_spawn_receipt_path() -> Path:
    return REPO_ROOT / "dev/state/agent_spawn_receipts.jsonl"


def _default_termination_receipt_path() -> Path:
    return REPO_ROOT / "dev/state/agent_termination_receipts.jsonl"


def _default_bypass_lifecycle_path() -> Path:
    return REPO_ROOT / "dev/state/bypass_lifecycles.jsonl"


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- spawn_evidence_count: {report.get('spawn_evidence_count')}")
    lines.append(f"- spawn_receipt_count: {report.get('spawn_receipt_count')}")
    lines.append(
        f"- termination_receipt_count: {report.get('termination_receipt_count')}"
    )
    lines.append(f"- bypass_lifecycle_count: {report.get('bypass_lifecycle_count')}")
    lines.append(
        f"- spawn_evidence_window_seconds: "
        f"{report.get('spawn_evidence_window_seconds')}"
    )
    lines.append(f"- violation_count: {report.get('violation_count')}")
    if report.get("display_text"):
        lines.extend(("", str(report["display_text"])))
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('rule_id')}: {violation.get('detail')}"
            )
    warnings = report.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)) and warnings:
        lines.extend(("", "## Warnings", ""))
        for warning in warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rollout-dir",
        type=Path,
        default=None,
        help="Directory of rollout-*.jsonl files. Defaults to today's "
        "~/.codex/sessions/<YYYY>/<MM>/<DD>/.",
    )
    parser.add_argument(
        "--spawn-receipt-path",
        type=Path,
        default=_default_spawn_receipt_path(),
    )
    parser.add_argument(
        "--termination-receipt-path",
        type=Path,
        default=_default_termination_receipt_path(),
    )
    parser.add_argument(
        "--bypass-lifecycle-path",
        type=Path,
        default=_default_bypass_lifecycle_path(),
    )
    parser.add_argument(
        "--spawn-evidence-window-seconds",
        type=int,
        default=DEFAULT_SPAWN_EVIDENCE_WINDOW_SECONDS,
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            rollout_dir=args.rollout_dir,
            spawn_receipt_path=args.spawn_receipt_path,
            termination_receipt_path=args.termination_receipt_path,
            bypass_lifecycle_path=args.bypass_lifecycle_path,
            spawn_evidence_window_seconds=args.spawn_evidence_window_seconds,
        )
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
