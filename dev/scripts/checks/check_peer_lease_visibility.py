#!/usr/bin/env python3
"""Fail when an actor's local state omits active peer write leases before mutation.

This is the A18 G35 pre-mutation visibility guard. It does NOT decide whether
two writers may share scope (that is G32 ``check_write_lease_conflicts``). It
only enforces that, before an actor mutates a PlanRow, the actor's local state
view of peer write leases on the same row is present, current, and within the
configured freshness window.

If the actor cannot see active peer leases, the actor cannot safely choose to
mutate, defer, or coordinate. That is the failure mode this guard forecloses.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        parse_utc as _parse_utc,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        parse_utc as _parse_utc,
        utc_timestamp,
    )


COMMAND = "check_peer_lease_visibility"
CONTRACT_ID = "PeerLeaseVisibilityGuard"

DEFAULT_VIEW_AGE_WINDOW_SECONDS = 300

RULE_MISSING_PEER_LEASES_FROM_LOCAL_STATE = "missing_peer_leases_from_local_state"
RULE_STALE_PEER_LEASE_VIEW = "stale_peer_lease_view"
RULE_PEER_LEASE_VIEW_AGE_EXCEEDS_WINDOW = "peer_lease_view_age_exceeds_window"

DISPLAY_TEXT = (
    "Peer lease visibility violation. Actor cannot mutate without an up-to-date "
    "local view of peer write leases for the same PlanRow."
)


@dataclass(frozen=True, slots=True)
class PeerLeaseVisibilityViolation:
    rule_id: str
    actor_id: str
    row_id: str
    detail: str
    remediation: str
    missing_lease_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "actor_id": self.actor_id,
            "row_id": self.row_id,
            "detail": self.detail,
            "remediation": self.remediation,
            "missing_lease_ids": list(self.missing_lease_ids),
        }


def build_report(
    *,
    actor_view: Mapping[str, object] | None = None,
    peer_leases: Sequence[Mapping[str, object]] | None = None,
    actor_view_path: Path | None = None,
    peer_leases_path: Path | None = None,
    row_id_filter: str = "",
    view_age_window_seconds: int = DEFAULT_VIEW_AGE_WINDOW_SECONDS,
    now: datetime | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    checked_surfaces: list[str] = []
    if actor_view is None:
        view_path = actor_view_path or _default_actor_view_path()
        checked_surfaces.append(str(view_path))
        actor_view = _load_actor_view(view_path, warnings)
    if peer_leases is None:
        leases_path = peer_leases_path or _default_peer_leases_path()
        checked_surfaces.append(str(leases_path))
        peer_leases = _load_peer_leases(leases_path, warnings)
    now_utc = now or datetime.now(timezone.utc)

    actor_id = str(actor_view.get("actor_id") or "").strip()
    row_id = str(actor_view.get("row_id") or "").strip()
    observed_at_raw = str(actor_view.get("peer_write_leases_observed_at") or "").strip()
    local_leases_raw = actor_view.get("peer_write_leases")
    if not isinstance(local_leases_raw, Sequence) or isinstance(
        local_leases_raw, (str, bytes)
    ):
        local_leases: tuple[Mapping[str, object], ...] = ()
    else:
        local_leases = tuple(
            lease for lease in local_leases_raw if isinstance(lease, Mapping)
        )

    failures: list[PeerLeaseVisibilityViolation] = []

    active_peer_leases = tuple(
        _filter_active_peer_leases(
            peer_leases=peer_leases,
            actor_id=actor_id,
            row_id=row_id_filter or row_id,
        )
    )

    if row_id_filter and row_id_filter != row_id:
        # Caller asked about a specific row, and the actor view is not for that
        # row at all. Treat as missing visibility for that row.
        if active_peer_leases:
            failures.append(
                PeerLeaseVisibilityViolation(
                    rule_id=RULE_MISSING_PEER_LEASES_FROM_LOCAL_STATE,
                    actor_id=actor_id,
                    row_id=row_id_filter,
                    detail=(
                        f"actor view row_id={row_id!r} does not match "
                        f"requested row_id={row_id_filter!r}; "
                        f"{len(active_peer_leases)} active peer lease(s) "
                        "not visible to actor"
                    ),
                    remediation=(
                        "Refresh actor's shared round state observation for "
                        "the requested row before mutation."
                    ),
                    missing_lease_ids=_lease_ids(active_peer_leases),
                )
            )

    local_lease_ids = frozenset(
        str(lease.get("lease_id") or "").strip()
        for lease in local_leases
        if str(lease.get("lease_id") or "").strip()
    )
    active_lease_ids = _lease_ids(active_peer_leases)

    # Rule 1: MISSING_PEER_LEASES_FROM_LOCAL_STATE
    # The actor view either omits the peer_write_leases field entirely, or it is
    # an empty sequence while at least one active peer lease exists.
    if active_peer_leases and not local_lease_ids:
        failures.append(
            PeerLeaseVisibilityViolation(
                rule_id=RULE_MISSING_PEER_LEASES_FROM_LOCAL_STATE,
                actor_id=actor_id,
                row_id=row_id,
                detail=(
                    f"{len(active_peer_leases)} active peer write lease(s) "
                    f"exist for row {row_id!r} but actor local state omits "
                    "peer_write_leases"
                ),
                remediation=(
                    "Re-observe shared round state and include peer_write_leases "
                    "for the row before mutation."
                ),
                missing_lease_ids=active_lease_ids,
            )
        )

    # Rule 2: STALE_PEER_LEASE_VIEW
    # The local view has lease entries but is missing at least one active peer
    # lease the world knows about (newer leases granted after the actor's last
    # observation), or contains a lease the world no longer reports active.
    if local_lease_ids:
        missing_from_view = tuple(
            lease_id for lease_id in active_lease_ids if lease_id not in local_lease_ids
        )
        extra_in_view = tuple(
            lease_id
            for lease_id in local_lease_ids
            if lease_id not in frozenset(active_lease_ids)
        )
        if missing_from_view or extra_in_view:
            detail_parts: list[str] = []
            if missing_from_view:
                detail_parts.append(
                    f"active peer leases not in local view: "
                    f"{sorted(missing_from_view)}"
                )
            if extra_in_view:
                detail_parts.append(
                    f"local view references leases no longer active: "
                    f"{sorted(extra_in_view)}"
                )
            failures.append(
                PeerLeaseVisibilityViolation(
                    rule_id=RULE_STALE_PEER_LEASE_VIEW,
                    actor_id=actor_id,
                    row_id=row_id,
                    detail="; ".join(detail_parts),
                    remediation=(
                        "Re-observe shared round state. The local peer-lease "
                        "view diverged from the live lease ledger."
                    ),
                    missing_lease_ids=missing_from_view,
                )
            )

    # Rule 3: PEER_LEASE_VIEW_AGE_EXCEEDS_WINDOW
    # Even if the lease ids match exactly, an observation that is too old does
    # not satisfy the pre-mutation freshness invariant.
    observed_at = _parse_utc(observed_at_raw) if observed_at_raw else None
    if active_peer_leases:
        if observed_at is None:
            failures.append(
                PeerLeaseVisibilityViolation(
                    rule_id=RULE_PEER_LEASE_VIEW_AGE_EXCEEDS_WINDOW,
                    actor_id=actor_id,
                    row_id=row_id,
                    detail=(
                        "peer_write_leases_observed_at missing or invalid; "
                        "cannot prove peer-lease view freshness"
                    ),
                    remediation=(
                        "Stamp peer_write_leases_observed_at in the actor's "
                        "shared round state observation."
                    ),
                )
            )
        else:
            age_seconds = now_utc.timestamp() - observed_at.timestamp()
            if age_seconds > view_age_window_seconds:
                failures.append(
                    PeerLeaseVisibilityViolation(
                        rule_id=RULE_PEER_LEASE_VIEW_AGE_EXCEEDS_WINDOW,
                        actor_id=actor_id,
                        row_id=row_id,
                        detail=(
                            f"peer_write_leases_observed_at age "
                            f"{int(age_seconds)}s exceeds window "
                            f"{view_age_window_seconds}s"
                        ),
                        remediation=(
                            "Refresh shared round state observation before "
                            "starting mutation."
                        ),
                    )
                )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not failures,
        "display_text": DISPLAY_TEXT if failures else "",
        "actor_id": actor_id,
        "row_id": row_id_filter or row_id,
        "view_age_window_seconds": view_age_window_seconds,
        "active_peer_lease_count": len(active_peer_leases),
        "local_peer_lease_count": len(local_leases),
        "peer_write_leases_observed_at": observed_at_raw,
        "checked_surfaces": checked_surfaces,
        "failures": [violation.to_dict() for violation in failures],
        "warnings": warnings,
    }


def _filter_active_peer_leases(
    *,
    peer_leases: Sequence[Mapping[str, object]],
    actor_id: str,
    row_id: str,
) -> Iterable[Mapping[str, object]]:
    for lease in peer_leases:
        lease_row = str(lease.get("row_id") or "").strip()
        if row_id and lease_row and lease_row != row_id:
            continue
        lease_actor = str(lease.get("actor_id") or "").strip()
        if actor_id and lease_actor == actor_id:
            # The actor's own lease is not a "peer" lease for visibility.
            continue
        status = str(lease.get("status") or "").strip().lower()
        if status and status not in {"active", "held", "granted", ""}:
            continue
        yield lease


def _lease_ids(leases: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for lease in leases:
        lease_id = str(lease.get("lease_id") or "").strip()
        if not lease_id or lease_id in seen:
            continue
        seen.add(lease_id)
        result.append(lease_id)
    return tuple(result)


def _load_actor_view(path: Path, warnings: list[str]) -> Mapping[str, object]:
    if not path.exists():
        warnings.append(f"actor view missing: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"actor view load failed: {exc}")
        return {}
    if not isinstance(payload, Mapping):
        return {}
    return payload


def _load_peer_leases(
    path: Path, warnings: list[str]
) -> tuple[Mapping[str, object], ...]:
    if not path.exists():
        warnings.append(f"peer leases missing: {path}")
        return ()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"peer leases load failed: {exc}")
        return ()
    if isinstance(payload, Mapping):
        leases = payload.get("leases")
        if isinstance(leases, list):
            return tuple(lease for lease in leases if isinstance(lease, Mapping))
        return ()
    if isinstance(payload, list):
        return tuple(lease for lease in payload if isinstance(lease, Mapping))
    return ()


def _default_actor_view_path() -> Path:
    return REPO_ROOT / "dev/reports/shared_round_state/actor_view.json"


def _default_peer_leases_path() -> Path:
    return REPO_ROOT / "dev/reports/shared_round_state/peer_write_leases.json"


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- actor_id: `{report.get('actor_id')}`")
    lines.append(f"- row_id: `{report.get('row_id')}`")
    lines.append(f"- view_age_window_seconds: {report.get('view_age_window_seconds')}")
    lines.append(f"- active_peer_lease_count: {report.get('active_peer_lease_count')}")
    lines.append(f"- local_peer_lease_count: {report.get('local_peer_lease_count')}")
    lines.append(
        f"- peer_write_leases_observed_at: `{report.get('peer_write_leases_observed_at')}`"
    )
    if report.get("display_text"):
        lines.extend(("", str(report["display_text"])))
    failures = report.get("failures")
    if isinstance(failures, Sequence) and not isinstance(failures, (str, bytes)) and failures:
        lines.extend(("", "## Failures", ""))
        for violation in failures:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('rule_id')} "
                f"actor={violation.get('actor_id')} "
                f"row={violation.get('row_id')}: {violation.get('detail')}"
            )
    warnings = report.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)) and warnings:
        lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--actor-view-path",
        type=Path,
        default=_default_actor_view_path(),
        help="Local actor view JSON exposing peer_write_leases + observed_at.",
    )
    parser.add_argument(
        "--peer-leases-path",
        type=Path,
        default=_default_peer_leases_path(),
        help="Live peer write lease ledger JSON.",
    )
    parser.add_argument(
        "--row-id",
        default="",
        help="If set, restrict the check to this row id.",
    )
    parser.add_argument(
        "--view-age-window-seconds",
        type=int,
        default=DEFAULT_VIEW_AGE_WINDOW_SECONDS,
        help="Maximum allowed age of peer_write_leases_observed_at, in seconds.",
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            actor_view_path=args.actor_view_path,
            peer_leases_path=args.peer_leases_path,
            row_id_filter=args.row_id,
            view_age_window_seconds=args.view_age_window_seconds,
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
