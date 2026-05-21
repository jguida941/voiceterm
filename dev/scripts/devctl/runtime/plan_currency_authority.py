"""Plan-currency authority — supersession-aware packet currency selector.

Phase 0.6.A v4.36 (rev_pkt_4708 / plan row
``MP-GUARDIR-V4-PHASE-0-6-A-REVIEW-FEEDBACK-POST-OBEDIENCE-S1``) extends the
v4.33 plan-currency reducer with supersession-aware lineage matching.

Codex's v4.36 finding: exact-SHA equality is too strict during live plan
iteration. A packet posted against v4.33 (SHA c31a8b20) for a row that the
controller later amends to v4.34/v4.35/v4.36 must NOT be mechanically demoted
to stale — the amendments sharpen the row, they do not supersede the work
the packet refers to.

The 3-state currency, highest priority first:

  * ``PLAN_CURRENCY_RANK_CURRENT`` (2) — packet's ``target_revision`` matches
    the latest canonical plan SHA exactly. Render at top of selector.
  * ``PLAN_CURRENCY_RANK_LINEAGE_AMENDED`` (1) — packet's SHA differs from
    current canonical, but appears in the snapshot lineage of the packet's
    ``target_ref`` (plan row). Still outranks truly stale debt, and (when
    selected) should emit a typed ``PlanRevisionRefreshRequired`` blocker.
  * ``PLAN_CURRENCY_RANK_STALE`` (0) — neither current nor in lineage.

The reducer constructs a ``PlanCurrencyContext`` once per agent-attention
build by walking ``dev/state/plan_source_snapshots.jsonl``, extracting the
latest canonical SHA and the row→SHAs lineage map. The context is then
forwarded to ``attention_priority_key`` so every candidate packet is
evaluated against the same snapshot.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .value_coercion import coerce_string

PLAN_SOURCE_SNAPSHOTS_REL = "dev/state/plan_source_snapshots.jsonl"

#: Rank values (3-state, monotonic):
PLAN_CURRENCY_RANK_CURRENT = 2
PLAN_CURRENCY_RANK_LINEAGE_AMENDED = 1
PLAN_CURRENCY_RANK_STALE = 0

PLAN_REVISION_REFRESH_REQUIRED_CONTRACT_ID = "PlanRevisionRefreshRequired"
PLAN_REVISION_REFRESH_REQUIRED_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class PlanCurrencyContext:
    """Plan-snapshot context for the attention selector.

    ``current_plan_sha`` — bare SHA of the latest snapshot row by
    ``captured_at_utc``. Empty when no snapshots exist.

    ``row_snapshot_shas`` — for each ``plan_row_id``, the set of all SHAs
    ever recorded for that row. Used for lineage matching: a packet whose
    ``target_revision`` differs from ``current_plan_sha`` but appears in
    ``row_snapshot_shas[packet.target_ref]`` is in the row's amendment
    lineage (rank LINEAGE_AMENDED), not stale.

    The dataclass is frozen + slots so it can be safely passed across
    reducer call boundaries without defensive copying.
    """

    current_plan_sha: str = ""
    row_snapshot_shas: Mapping[str, frozenset[str]] = field(
        default_factory=lambda: {}
    )

    @property
    def empty(self) -> bool:
        return not self.current_plan_sha and not self.row_snapshot_shas


@dataclass(frozen=True, slots=True)
class PlanRevisionRefreshRequired:
    """Typed blocker emitted when a LINEAGE_AMENDED packet wins selection.

    Codex's v4.36 directive: when an older packet is selected via lineage
    fallback (its SHA is in the row's lineage but the row has newer
    amendments), the system must emit a typed signal so the operator knows
    a refreshed packet is required.

    This contract carries enough fields for the operator/consumer to
    construct the refresh request: old packet id, old SHA, latest canonical
    SHA, target row, and a recommended refreshed packet kind.
    """

    blocker_id: str
    old_packet_id: str
    old_packet_sha: str
    latest_canonical_sha: str
    target_row_id: str
    requested_refresh_kind: str = "task_progress"
    schema_version: int = PLAN_REVISION_REFRESH_REQUIRED_SCHEMA_VERSION
    contract_id: str = PLAN_REVISION_REFRESH_REQUIRED_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return {
            "blocker_id": self.blocker_id,
            "old_packet_id": self.old_packet_id,
            "old_packet_sha": self.old_packet_sha,
            "latest_canonical_sha": self.latest_canonical_sha,
            "target_row_id": self.target_row_id,
            "requested_refresh_kind": self.requested_refresh_kind,
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
        }


def load_plan_currency_context(
    repo_root: Path | str | None = None,
) -> PlanCurrencyContext:
    """Read plan_source_snapshots.jsonl once, return current SHA + lineage.

    The lineage map collects every SHA ever recorded for each
    ``plan_row_id``. The current SHA is the latest by ``captured_at_utc``.
    Empty file or missing path returns an empty ``PlanCurrencyContext``
    (no currency promotion; equivalent to legacy v4.32 behavior).
    """
    root = _coerce_root(repo_root)
    if root is None:
        return PlanCurrencyContext()
    path = root / PLAN_SOURCE_SNAPSHOTS_REL
    if not path.exists():
        return PlanCurrencyContext()

    latest_at_utc = ""
    latest_sha = ""
    row_shas: dict[str, set[str]] = {}
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, Mapping):
                    continue
                captured_at = coerce_string(row.get("captured_at_utc")).strip()
                sha = _extract_sha(row)
                if not sha:
                    continue
                if captured_at >= latest_at_utc:
                    latest_at_utc = captured_at
                    latest_sha = sha
                plan_row_id = coerce_string(row.get("plan_row_id")).strip()
                if plan_row_id:
                    row_shas.setdefault(plan_row_id, set()).add(sha)
    except OSError:
        return PlanCurrencyContext()

    return PlanCurrencyContext(
        current_plan_sha=latest_sha,
        row_snapshot_shas={
            row_id: frozenset(shas) for row_id, shas in row_shas.items()
        },
    )


def current_canonical_plan_sha(repo_root: Path | str | None = None) -> str:
    """Return the latest plan source SHA recorded in plan_source_snapshots.

    Thin wrapper around ``load_plan_currency_context`` for callers that only
    need the canonical SHA. Preserved as a stable public surface for v4.33
    callers; new consumers should use ``load_plan_currency_context`` to also
    get the lineage map.
    """
    return load_plan_currency_context(repo_root).current_plan_sha


def packet_target_sha(packet: Mapping[str, object]) -> str:
    """Extract the plan SHA from a packet's ``target_revision`` field.

    Handles both ``sha256:<hash>`` and bare ``<hash>`` forms. Returns the
    bare hash, or empty string when no target_revision is present.
    """
    if not isinstance(packet, Mapping):
        return ""
    target = coerce_string(packet.get("target_revision")).strip()
    if not target:
        return ""
    if ":" in target:
        _, _, sha = target.partition(":")
        return sha.strip()
    return target


def packet_target_ref(packet: Mapping[str, object]) -> str:
    """Extract the packet's target row id from ``target_ref``."""
    if not isinstance(packet, Mapping):
        return ""
    return coerce_string(packet.get("target_ref")).strip()


def plan_currency_rank(
    packet: Mapping[str, object],
    *,
    current_plan_sha: str = "",
    row_snapshot_shas: Mapping[str, frozenset[str] | set[str]] | None = None,
) -> int:
    """Return the plan-currency rank for ``packet``.

    Returns one of three ranks:

    - ``PLAN_CURRENCY_RANK_CURRENT`` (2) — packet's SHA matches
      ``current_plan_sha`` exactly.
    - ``PLAN_CURRENCY_RANK_LINEAGE_AMENDED`` (1) — packet's SHA differs from
      current canonical but appears in
      ``row_snapshot_shas[packet.target_ref]`` (the row's snapshot lineage).
      Codex's v4.36 supersession-aware fallback: amendments sharpen the row
      but do not supersede the packet's work.
    - ``PLAN_CURRENCY_RANK_STALE`` (0) — neither current nor in lineage,
      OR caller didn't supply context.

    Backwards-compat: when ``current_plan_sha`` is empty AND
    ``row_snapshot_shas`` is None or empty, all packets rank as 0 →
    v4.33+ priority key contributes 0 to the first dimension → existing
    ordering is preserved.
    """
    target_sha = packet_target_sha(packet)
    if not target_sha:
        return PLAN_CURRENCY_RANK_STALE

    current = coerce_string(current_plan_sha).strip()
    if current and target_sha == current:
        return PLAN_CURRENCY_RANK_CURRENT

    if row_snapshot_shas:
        target_ref = packet_target_ref(packet)
        if target_ref:
            lineage = row_snapshot_shas.get(target_ref)
            if lineage and target_sha in lineage:
                return PLAN_CURRENCY_RANK_LINEAGE_AMENDED

    return PLAN_CURRENCY_RANK_STALE


def build_plan_revision_refresh_required(
    *,
    packet: Mapping[str, object],
    latest_canonical_sha: str,
    requested_refresh_kind: str = "task_progress",
) -> PlanRevisionRefreshRequired:
    """Construct a typed refresh-required blocker from a LINEAGE_AMENDED packet.

    The caller (selector consumer) emits this when ``plan_currency_rank``
    returns ``PLAN_CURRENCY_RANK_LINEAGE_AMENDED`` and the packet was
    selected for attention. The blocker carries enough fields for the
    operator to construct a refreshed packet.
    """
    packet_id = coerce_string(packet.get("packet_id")).strip()
    target_row_id = packet_target_ref(packet)
    old_sha = packet_target_sha(packet)
    blocker_id = f"plan_revision_refresh:{packet_id or 'unknown'}:{old_sha[:12] or 'no_sha'}"
    return PlanRevisionRefreshRequired(
        blocker_id=blocker_id,
        old_packet_id=packet_id,
        old_packet_sha=old_sha,
        latest_canonical_sha=coerce_string(latest_canonical_sha).strip(),
        target_row_id=target_row_id,
        requested_refresh_kind=coerce_string(requested_refresh_kind).strip()
        or "task_progress",
    )


def _extract_sha(row: Mapping[str, object]) -> str:
    """Extract a SHA from a PlanSourceSnapshot row's hash fields."""
    for key in ("source_doc_sha256", "body_hash", "source_hash"):
        value = coerce_string(row.get(key)).strip()
        if value:
            if ":" in value:
                _, _, sha = value.partition(":")
                return sha.strip()
            return value
    return ""


def _coerce_root(repo_root: Path | str | None) -> Path | None:
    if repo_root is None:
        try:
            from ..config import REPO_ROOT  # noqa: PLC0415
        except ImportError:
            return None
        return REPO_ROOT
    if isinstance(repo_root, Path):
        return repo_root
    return Path(str(repo_root))


__all__ = [
    "PLAN_CURRENCY_RANK_CURRENT",
    "PLAN_CURRENCY_RANK_LINEAGE_AMENDED",
    "PLAN_CURRENCY_RANK_STALE",
    "PLAN_REVISION_REFRESH_REQUIRED_CONTRACT_ID",
    "PLAN_REVISION_REFRESH_REQUIRED_SCHEMA_VERSION",
    "PLAN_SOURCE_SNAPSHOTS_REL",
    "PlanCurrencyContext",
    "PlanRevisionRefreshRequired",
    "build_plan_revision_refresh_required",
    "current_canonical_plan_sha",
    "load_plan_currency_context",
    "packet_target_ref",
    "packet_target_sha",
    "plan_currency_rank",
]
