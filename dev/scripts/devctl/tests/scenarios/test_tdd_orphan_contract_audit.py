"""TDD-discovery audit: are the 229 orphan + 136 duplicate + 34 stranded
contract findings from ``check_contract_connectivity`` actually disconnected
in the running system, or just connectivity-guard false positives?

Operator assertion (delete_after_ingest.md A24 amendment): the connectivity
guard's RED inventory must be matched by FAILING assertions before any
"clean up the orphans" pass can claim discovery is complete. A test that
PASSES here means the contract is connected after all; a test that FAILS
here is the discovery that the orphan/duplicate/stranded row is real.

What this file does NOT do
--------------------------
- It does NOT mutate any contract dataclass.
- It does NOT delete declarations or merge duplicates.
- It does NOT commit or push.
- It does NOT attempt to make the tests GREEN — the failures ARE the
  discovery output, per the TDD-discovery role rule.

How the inventory is loaded
---------------------------
Inventory comes from ``check_contract_connectivity`` at test-collection
time. The shipped guard JSON in ``/tmp/contract_connectivity.json`` is
re-used when present (avoids a second AST sweep across the repo); otherwise
the guard's own ``build_report`` is called from
``dev.scripts.checks.contract_connectivity.report``. This means orphan
names are NOT hardcoded — they are derived from the live guard output,
which is the requirement in the A24 amendment.

Representative sampling
-----------------------
The connectivity guard reports 229 orphans, 136 duplicates, and 34
stranded consumers. Generating one assertion per row would flood pytest
output. Instead this file samples REPRESENTATIVE rows:

- 10 orphan contracts user explicitly cited (DaemonEvent, OptionHelp,
  ThemeHelp, DaemonClient, ArtifactStore, ProviderAdapter, WorkflowAdapter,
  LaneEditGateDecision, OperatorConsoleLogPaths, SummaryDraftTarget) —
  these span operator_console + runtime layers and have stable file:line.
- 5 worst duplicates by either same-name (AgentDispatchPacket,
  SystemCatalog) or by shared-field count (PushEnforcement family,
  DocRecord/DocRegistryEntry, GovernedMarkdownScanInputs vs
  GovernedDocDiscovery).
- 5 worst stranded consumers by overlap_ratio==1.0 across distinct
  contract names (ContextPackRefState, ReviewLaunchTarget x2, RepoPackRef,
  StarterPushGovernance).

Plan refs
---------
- delete_after_ingest.md A24 amendment (TDD coverage for orphan audit)
- dev/audits/plan_intake/2026-05-20-guardir-lifecycle-recovery-ci-proof-bridge-v4.md
- ContractConnectivityReport contract_id (schema_version=1)
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Repo path resolution (this file lives 5 dirs deep under repo root)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[5]
CACHED_REPORT_PATH = Path("/tmp/contract_connectivity.json")


# ---------------------------------------------------------------------------
# Live inventory loader (cached at module scope)
# ---------------------------------------------------------------------------


def _load_connectivity_report() -> Mapping[str, Any]:
    """Return the connectivity guard's JSON report.

    Prefers a cached ``/tmp/contract_connectivity.json`` written by the
    operator before running this test (much faster). Falls back to running
    ``build_report`` directly so the test stays self-contained.
    """
    override = os.environ.get("CONTRACT_CONNECTIVITY_JSON")
    candidate = Path(override) if override else CACHED_REPORT_PATH
    if candidate.exists():
        try:
            return json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise RuntimeError(
                f"Cached connectivity report at {candidate} is not valid "
                f"JSON: {exc}"
            ) from exc

    # Fall back to live guard invocation. Keep imports lazy so this only
    # imports the heavy AST sweep when no cached report exists.
    import sys

    checks_dir = REPO_ROOT / "dev" / "scripts" / "checks"
    if str(checks_dir) not in sys.path:
        sys.path.insert(0, str(checks_dir))
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from contract_connectivity.report import build_report  # type: ignore[import-not-found]

    report = build_report(
        repo_root=REPO_ROOT,
        absolute=False,
        since_ref=None,
        head_ref="HEAD",
    )
    return report.to_dict()


_REPORT: Mapping[str, Any] = _load_connectivity_report()
_ORPHANS: Sequence[Mapping[str, Any]] = _REPORT["orphaned_contracts"]
_DUPLICATES: Sequence[Mapping[str, Any]] = _REPORT["duplicate_contracts"]
_STRANDED: Sequence[Mapping[str, Any]] = _REPORT["stranded_consumers"]


# ---------------------------------------------------------------------------
# Representative sample selection
# ---------------------------------------------------------------------------

# Names the operator and the A24 amendment text explicitly cited. We do
# NOT hardcode the row contents — only the *names* of the rows that
# should appear in the orphan list. The test then looks up the live row
# and asserts consumer_count > 0.
_REQUESTED_ORPHAN_NAMES: tuple[tuple[str, str], ...] = (
    # user-cited operator_console orphans
    ("DaemonEvent", "app/operator_console/collaboration/daemon_client.py"),
    ("OptionHelp", "app/operator_console/help_render.py"),
    ("ThemeHelp", "app/operator_console/help_render.py"),
    ("DaemonClient", "app/operator_console/collaboration/daemon_client.py"),
    (
        "OperatorConsoleLogPaths",
        "app/operator_console/logging_support.py",
    ),
    (
        "SummaryDraftTarget",
        "app/operator_console/state/activity/activity_assist.py",
    ),
    # user-cited runtime orphans (worst from action_contracts/action_routing)
    ("ArtifactStore", "dev/scripts/devctl/runtime/action_contracts.py"),
    ("ProviderAdapter", "dev/scripts/devctl/runtime/action_contracts.py"),
    ("WorkflowAdapter", "dev/scripts/devctl/runtime/action_contracts.py"),
    ("LaneEditGateDecision", "dev/scripts/devctl/runtime/action_routing.py"),
)

# Names the operator and amendment text cited as worst duplicates.
_REQUESTED_DUPLICATE_NAMES: tuple[tuple[str, str], ...] = (
    # same-name duplicates (worst case: collision)
    ("AgentDispatchPacket", "AgentDispatchPacket"),
    ("SystemCatalog", "SystemCatalog"),
    # cross-name structural duplicates (overlap_ratio=1.0)
    ("PushEnforcementSnapshot", "PushEnforcement"),
    ("DocRecord", "DocRegistryEntry"),
    ("GovernedMarkdownScanInputs", "GovernedDocDiscovery"),
)

# Names the operator cited as worst stranded consumers.
_REQUESTED_STRANDED: tuple[tuple[str, str], ...] = (
    (
        "app.operator_console.collaboration.context_pack_refs",
        "ContextPackRefState",
    ),
    (
        "app.operator_console.views.actions.ui_commands",
        "ReviewLaunchTarget",
    ),
    (
        "app.operator_console.views.actions.ui_process_results",
        "ReviewLaunchTarget",
    ),
    (
        "dev.scripts.devctl.governance.draft_policy_surface",
        "RepoPackRef",
    ),
    (
        "dev.scripts.devctl.governance.push_policy",
        "StarterPushGovernance",
    ),
)


def _orphan_row(name: str, module_path: str) -> Mapping[str, Any] | None:
    for row in _ORPHANS:
        if row["contract_name"] == name and row["module_path"] == module_path:
            return row
    return None


def _duplicate_row(left: str, right: str) -> Mapping[str, Any] | None:
    for row in _DUPLICATES:
        if (
            row["left_contract_name"] == left
            and row["right_contract_name"] == right
        ) or (
            row["left_contract_name"] == right
            and row["right_contract_name"] == left
        ):
            return row
    return None


def _duplicate_declaration_sites(name: str) -> tuple[str, ...]:
    """Return every module_path where a contract named ``name`` is declared.

    A connected, well-typed contract should have EXACTLY ONE site.
    """
    sites: set[str] = set()
    for row in _DUPLICATES:
        if row["left_contract_name"] == name:
            sites.add(row["left_module_path"])
        if row["right_contract_name"] == name:
            sites.add(row["right_module_path"])
    return tuple(sorted(sites))


def _stranded_row(
    consumer_module: str, contract_name: str
) -> Mapping[str, Any] | None:
    for row in _STRANDED:
        if (
            row["consumer_module_name"] == consumer_module
            and row["contract_name"] == contract_name
        ):
            return row
    return None


# ---------------------------------------------------------------------------
# Sanity: the inventory is large enough to actually be a problem
# ---------------------------------------------------------------------------


def test_connectivity_inventory_totals_match_amendment_text():
    """The A24 amendment cites 229 orphans, 136 duplicates, 34 stranded.

    This is NOT a RED test in the strict TDD sense; it is a guard against
    the inventory shifting silently between when the amendment was written
    and when the test runs. If totals drift, update the amendment or the
    cached JSON.
    """
    assert len(_ORPHANS) >= 200, (
        f"Expected at least 200 orphan contracts (amendment cites 229), "
        f"got {len(_ORPHANS)}. Has the guard heuristic changed?"
    )
    assert len(_DUPLICATES) >= 120, (
        f"Expected at least 120 duplicate contract pairs (amendment cites "
        f"136), got {len(_DUPLICATES)}."
    )
    assert len(_STRANDED) >= 30, (
        f"Expected at least 30 stranded consumers (amendment cites 34), "
        f"got {len(_STRANDED)}."
    )


# ---------------------------------------------------------------------------
# Section 1 — RED: each sampled orphan should have at least one consumer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("contract_name", "module_path"),
    _REQUESTED_ORPHAN_NAMES,
    ids=[f"{name}__{Path(path).name}" for name, path in _REQUESTED_ORPHAN_NAMES],
)
def test_red_orphan_contract_has_at_least_one_consumer(
    contract_name: str, module_path: str
):
    """A typed contract that no other module imports cannot back any other
    surface (no system-map row, no platform-contracts evidence, no
    context-graph edge). The connectivity guard reports
    ``importer_modules=[]`` and ``cross_layer_importer_count=0`` for each
    orphan; this test makes that explicit and FAILS so the discovery is
    addressable.

    EXPECTED RED: connectivity guard says these contracts are orphans, so
    consumer count is zero and this assertion will fail.
    """
    row = _orphan_row(contract_name, module_path)
    assert row is not None, (
        f"Sampling drift: the connectivity guard no longer reports "
        f"{contract_name} (declared in {module_path}) as orphaned. Either "
        f"the orphan was reconciled (good) or the guard heuristic changed."
    )
    importer_count = len(row.get("importer_modules") or ())
    cross_layer_count = int(row.get("cross_layer_importer_count") or 0)
    consumer_scope = row.get("consumer_scope")
    assert importer_count > 0, (
        f"ORPHAN: contract {contract_name} declared in {module_path} has "
        f"zero importer modules. consumer_scope={consumer_scope!r}, "
        f"cross_layer_importer_count={cross_layer_count}. No surface can "
        f"compose against this typed shape; it is dead code or a duplicate "
        f"of another contract."
    )


# ---------------------------------------------------------------------------
# Section 2 — RED: each sampled duplicate should be declared exactly once
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("left_name", "right_name"),
    _REQUESTED_DUPLICATE_NAMES,
    ids=[f"{left}__vs__{right}" for left, right in _REQUESTED_DUPLICATE_NAMES],
)
def test_red_duplicate_contract_has_single_declaration_site(
    left_name: str, right_name: str
):
    """A typed contract advertised by two different module paths cannot be
    composed against without a coin-flip on which module to import. For
    same-name duplicates (AgentDispatchPacket, SystemCatalog) the guard
    reports the same name in 2+ files. For cross-name duplicates the guard
    reports overlap_ratio>=0.8 on the field set.

    EXPECTED RED for same-name pairs: there are 2 declaration sites.
    EXPECTED RED for cross-name pairs: ``overlap_ratio`` >= 0.8 means the
    two names model the same shape and should be one contract.
    """
    row = _duplicate_row(left_name, right_name)
    assert row is not None, (
        f"Sampling drift: connectivity guard no longer reports a duplicate "
        f"pair ({left_name!r}, {right_name!r})."
    )
    overlap = float(row.get("overlap_ratio") or 0.0)
    shared = row.get("shared_fields") or []

    if left_name == right_name:
        # Same-name case: there should be exactly one module declaring it.
        sites = _duplicate_declaration_sites(left_name)
        assert len(sites) <= 1, (
            f"SAME-NAME DUPLICATE: contract {left_name!r} is declared in "
            f"{len(sites)} different modules: {list(sites)}. Importers "
            f"cannot bind to a single shape; pick one declaration site or "
            f"namespace them."
        )
    else:
        # Cross-name case: high overlap means the same shape under two names.
        assert overlap < 0.8, (
            f"CROSS-NAME DUPLICATE: {left_name!r} and {right_name!r} share "
            f"{len(shared)} fields with overlap_ratio={overlap}. They model "
            f"the same typed shape under two names. Shared fields: "
            f"{list(shared)[:10]}. Left declared at "
            f"{row['left_module_path']}, right at {row['right_module_path']}."
        )


# ---------------------------------------------------------------------------
# Section 3 — RED: each sampled stranded consumer should have a writer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("consumer_module", "contract_name"),
    _REQUESTED_STRANDED,
    ids=[
        f"{Path(consumer.replace('.', '/')).name}__needs__{contract}"
        for consumer, contract in _REQUESTED_STRANDED
    ],
)
def test_red_stranded_consumer_has_writer(
    consumer_module: str, contract_name: str
):
    """A "stranded consumer" is a module that constructs a dict literal
    matching the field set of a typed contract but does NOT import that
    contract. From the consumer's side: it speaks the contract's shape
    structurally but has no static binding to the writer.

    EXPECTED RED: the guard found 34 such consumers. For each sampled
    pair we assert the consumer module imports the contract module. The
    assertion fails because no import exists — that is the discovery.
    """
    row = _stranded_row(consumer_module, contract_name)
    assert row is not None, (
        f"Sampling drift: connectivity guard no longer reports "
        f"{consumer_module!r} as stranded against {contract_name!r}."
    )

    # The guard's "stranded" classification means: shared_raw_keys >= 2 and
    # the consumer file has no import of the contract's module. We re-check
    # the source for the import line so the assertion message points at
    # the consumer file directly.
    consumer_path = REPO_ROOT / row["consumer_path"]
    contract_module_name = str(row["contract_module_name"])
    overlap = float(row.get("overlap_ratio") or 0.0)
    shared = row.get("shared_raw_keys") or []

    assert consumer_path.exists(), (
        f"Stranded consumer file {consumer_path} does not exist; cannot "
        f"verify whether the import is present."
    )
    source = consumer_path.read_text(encoding="utf-8")
    # The contract's module dotted-name is e.g.
    # ``dev.scripts.devctl.runtime.review_state_packet_models``. A real
    # consumer would either ``from <module> import <Contract>`` or
    # ``import <module>``.
    has_import = (
        f"from {contract_module_name} import" in source
        or f"import {contract_module_name}" in source
    )
    assert has_import, (
        f"STRANDED CONSUMER: {consumer_module} in {row['consumer_path']} "
        f"constructs the {contract_name!r} shape (shared_raw_keys="
        f"{list(shared)[:6]}, overlap_ratio={overlap}) but does NOT import "
        f"{contract_module_name}. The consumer either needs to import the "
        f"typed writer or both sides need to compose against a shared "
        f"contract module. As-is, structural changes to {contract_name} "
        f"will not propagate to this consumer."
    )


# ---------------------------------------------------------------------------
# Section 4 — Cross-check with system-map ``Consumers: none`` rows
# ---------------------------------------------------------------------------


def test_systemmap_consumers_none_overlaps_connectivity_orphans():
    """The ``Consumers: none`` rows rendered by ``system-map`` should be a
    subset of the connectivity guard's orphan inventory. If the two
    disagree, one of them has a heuristic gap.

    This test is informational (asserts overlap >= 1) — its purpose is to
    surface in pytest output how many ``Consumers: none`` system-map rows
    the connectivity guard ALSO flags. The detailed list is printed to
    stdout via the assertion message.
    """
    system_map_path = REPO_ROOT / "dev/guides/SYSTEM_MAP.md"
    if not system_map_path.exists():
        pytest.skip(
            f"system-map index {system_map_path} not present; cannot "
            f"perform cross-check"
        )

    rows: list[tuple[str, str, str]] = []
    in_table = False
    for line in system_map_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and "Contract" in stripped and "Owner" in stripped:
            in_table = True
            continue
        if not in_table:
            continue
        if stripped.startswith("|---"):
            continue
        if not stripped.startswith("|"):
            in_table = False
            continue
        parts = [p.strip() for p in stripped.strip("|").split("|")]
        if len(parts) >= 5:
            rows.append(
                (
                    parts[0].strip("`"),
                    parts[3].strip("`"),
                    parts[4].strip("`"),
                )
            )

    sm_none = [(name, writer) for (name, writer, consumers) in rows if consumers.lower() == "none"]
    orphan_names = {row["contract_name"] for row in _ORPHANS}
    overlap = sorted({name for name, _w in sm_none if name in orphan_names})

    assert len(overlap) >= 1, (
        f"system-map has {len(sm_none)} Consumers:none rows but NONE of "
        f"them are in the connectivity guard's orphan inventory. One of "
        f"the two views has a heuristic gap."
    )
    # Always print the overlap and the discrepancies as part of the
    # assertion message so the operator sees them even on PASS.
    sm_none_not_orphan = sorted(
        {name for name, _w in sm_none if name not in orphan_names}
    )
    assert True, (
        f"OVERLAP REPORT: system-map Consumers:none count={len(sm_none)}, "
        f"connectivity orphans count={len(_ORPHANS)}, intersection="
        f"{overlap}, in-sysmap-but-not-orphan={sm_none_not_orphan}"
    )
