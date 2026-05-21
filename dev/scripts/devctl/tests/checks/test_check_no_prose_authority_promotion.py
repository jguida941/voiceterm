"""Phase 0.6.E v4.44 (rev_pkt_4723) — prose-authority-promotion guard tests.

Tests cover:
- Live repo state passes (post-v4.44 edits)
- Synthetic doc with disallowed phrase fails
- JSON / markdown output shape
- Each disallowed phrase fires its own violation
- Defensive: missing file is silently OK (handled at scan level)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


_GUARD_SCRIPT = (
    Path(__file__).resolve().parents[5]
    / "dev/scripts/checks/check_no_prose_authority_promotion.py"
)


def _run_guard(repo_root: Path, fmt: str = "md") -> subprocess.CompletedProcess[str]:
    """Invoke the guard against an arbitrary repo root."""
    return subprocess.run(
        [
            sys.executable,
            str(_GUARD_SCRIPT),
            "--format",
            fmt,
            "--repo-root",
            str(repo_root),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_v4_44_live_repo_passes_after_doc_edits() -> None:
    """v4.44: the live repo (with v4.44's edits applied to DEVELOPMENT.md,
    INDEX.md, SYSTEM_MAP.md) must pass the guard."""
    live_repo_root = Path(__file__).resolve().parents[5]
    result = _run_guard(live_repo_root)
    assert result.returncode == 0, (
        f"Live repo failed prose-authority guard:\n{result.stdout}\n{result.stderr}"
    )
    assert "ok: True" in result.stdout
    assert "violation_count: 0" in result.stdout


def test_v4_44_synthetic_doc_with_canonical_prose_authority_fails(tmp_path: Path) -> None:
    """v4.44: a doc containing the literal ``Canonical prose authority``
    phrase MUST fail the guard with exit code 1."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "SYSTEM_MAP.md").write_text(
        "# SYSTEM_MAP\n\n"
        "Canonical prose authority binds behavior when typed state is silent.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "Canonical prose authority" in result.stdout
    assert "violation_count: 1" in result.stdout


def test_v4_44_synthetic_doc_with_master_plan_canonical_fails(tmp_path: Path) -> None:
    """v4.44: ``MASTER_PLAN.md is canonical`` phrase MUST fail."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "INDEX.md").write_text(
        "# INDEX\n\n"
        "Note: MASTER_PLAN.md is canonical execution state.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    # Two phrases match in this construction:
    # - "MASTER_PLAN.md is canonical"
    # - "canonical execution state"
    assert "violation_count" in result.stdout


def test_v4_44_synthetic_doc_with_canonical_registry_phrase_fails(tmp_path: Path) -> None:
    """v4.44: ``This file is the canonical registry`` MUST fail — the
    canonical registry is the JSONL store, not the markdown file."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "INDEX.md").write_text(
        "# INDEX\n\n"
        "This file is the canonical registry for `dev/active/*.md`.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "This file is the canonical registry" in result.stdout


def test_v4_44_synthetic_doc_with_agents_workflow_authority_fails(tmp_path: Path) -> None:
    """v4.44: ``AGENTS.md is workflow authority`` MUST fail."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "DEVELOPMENT.md").write_text(
        "# DEVELOPMENT\n\n"
        "AGENTS.md is workflow authority — read it first.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "AGENTS.md is workflow authority" in result.stdout


def test_v4_44_json_output_carries_typed_contract_id(tmp_path: Path) -> None:
    """v4.44: JSON output has ``contract_id: ProseAuthorityPromotionCheck``
    and includes the maintained_doc_paths + disallowed_phrases catalogs."""
    result = _run_guard(tmp_path, fmt="json")
    # tmp_path has no docs at all → ok=True, but JSON shape still present
    payload = json.loads(result.stdout)
    assert payload["contract_id"] == "ProseAuthorityPromotionCheck"
    assert payload["schema_version"] == 1
    assert payload["ok"] is True
    assert payload["violation_count"] == 0
    assert "maintained_doc_paths" in payload
    # v4.44.3 (rev_pkt_4728): scope expanded from 3 to 8 maintained docs to
    # include owner-spec docs (MASTER_PLAN.md, ai_governance_platform.md,
    # platform_authority_loop.md) and platform-guide surfaces
    # (PLATFORM_GUIDE.md, AI_GOVERNANCE_PLATFORM.md).
    assert len(payload["maintained_doc_paths"]) == 8
    assert "disallowed_phrases" in payload
    assert len(payload["disallowed_phrases"]) == 5


def test_v4_44_guard_does_not_match_phrases_with_proper_framing(tmp_path: Path) -> None:
    """v4.44 defensive: a doc that CORRECTLY describes the canonical store
    (e.g. ``the canonical registry is dev/state/plan_index.jsonl``) MUST
    NOT trigger the guard — the disallowed phrase ``This file is the
    canonical registry`` is specific."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "INDEX.md").write_text(
        "# INDEX\n\n"
        "The canonical PlanRow registry is `dev/state/plan_index.jsonl`; "
        "this file is a maintained pointer index over typed state.\n"
    )
    result = _run_guard(tmp_path)
    # Should pass — no disallowed phrase substring matches
    assert result.returncode == 0
    assert "ok: True" in result.stdout


def test_v4_44_guard_scans_only_maintained_doc_paths(tmp_path: Path) -> None:
    """v4.44: the guard only scans the configured maintained-doc paths.
    A disallowed phrase in a NON-listed doc must not trigger."""
    # Create a doc OUTSIDE the maintained-doc list
    other_dir = tmp_path / "dev" / "audits"
    other_dir.mkdir(parents=True)
    (other_dir / "NOTES.md").write_text("Canonical prose authority binds behavior.\n")
    result = _run_guard(tmp_path)
    # Scoped to maintained-doc paths only; this audit file is out of scope
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# v4.44.1 (rev_pkt_4725) — broadened contextual scan regressions
# ---------------------------------------------------------------------------


def test_v4_44_1_agents_md_source_of_truth_caught(tmp_path: Path) -> None:
    """v4.44.1 (rev_pkt_4725 verbatim): codex's false-negative case
    ``\`AGENTS.md\` stays the source of truth for policy/branch workflow.``
    MUST be flagged. Was missed by v4.44 substring-only scan because the
    exact phrase ``AGENTS.md is workflow authority`` wasn't present.
    """
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "DEVELOPMENT.md").write_text(
        "Some content.\n"
        "`AGENTS.md` stays the source of truth for policy/branch workflow.\n"
        "More content.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "AGENTS.md" in result.stdout
    assert "source of truth" in result.stdout


def test_v4_44_1_canonical_bootstrap_order_caught(tmp_path: Path) -> None:
    """v4.44.1: ``The canonical bootstrap order in AGENTS.md:235-242`` MUST
    be flagged (codex's exact reproduction)."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "SYSTEM_MAP.md").write_text(
        "The canonical bootstrap order in `AGENTS.md:235-242` and "
        "`dev/active/INDEX.md:3-4` always comes first.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "canonical bootstrap" in result.stdout


def test_v4_44_1_canonical_tracker_caught(tmp_path: Path) -> None:
    """v4.44.1: ``MASTER_PLAN.md ... canonical tracker`` MUST be flagged
    (codex's exact reproduction)."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "SYSTEM_MAP.md").write_text(
        "| `MASTER_PLAN.md` | MP-377..MP-410 unified | canonical tracker | "
        "in_progress | Apr 19 |\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "canonical tracker" in result.stdout


def test_v4_44_1_index_canonical_registry_caught(tmp_path: Path) -> None:
    """v4.44.1: ``dev/active/INDEX.md ... canonical registry`` MUST be
    flagged (codex's exact reproduction)."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "SYSTEM_MAP.md").write_text(
        "2. `dev/active/INDEX.md` — canonical registry for active docs\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "canonical registry" in result.stdout
    # Doc name surfaced in violation reason
    assert "INDEX.md" in result.stdout


def test_v4_44_1_correctly_framed_projection_not_flagged(tmp_path: Path) -> None:
    """v4.44.1: a line that mentions AGENTS.md AND uses a dangerous term
    BUT also frames it as a projection over typed state MUST NOT be flagged."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "DEVELOPMENT.md").write_text(
        "Some content.\n"
        "`AGENTS.md` is the generated projection of the workflow source of "
        "truth over typed startup-authority; durable rules live in "
        "`dev/config/devctl_repo_policy.json`.\n"
    )
    result = _run_guard(tmp_path)
    # Line has "generated", "projection", "over typed" — multiple qualifiers
    assert result.returncode == 0


def test_v4_44_1_tracker_projection_phrase_not_flagged(tmp_path: Path) -> None:
    """v4.44.1: ``tracker_projection`` (the replacement framing) MUST NOT
    fire the canonical-tracker check."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "SYSTEM_MAP.md").write_text(
        "| `MASTER_PLAN.md` | MP-377..MP-410 unified | "
        "tracker_projection (over `dev/state/plan_index.jsonl`) | "
        "in_progress | Apr 19 |\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 0


def test_v4_44_1_rev_pkt_changelog_line_not_flagged(tmp_path: Path) -> None:
    """v4.44.1: a historical changelog line that mentions ``canonical
    bootstrap`` while documenting a past packet decision MUST NOT be
    flagged (``rev_pkt_`` is a qualifier indicating historical commentary)."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "SYSTEM_MAP.md").write_text(
        "| 2026-04-19 (Codex re-review round 2) | rev_pkt_1353/1356 fixes "
        "applied: purpose statement lines 3-6 rewritten to position "
        "SYSTEM_MAP.md as supplementary navigation (canonical bootstrap "
        "order runs first), section 0 mermaid update. |\n"
    )
    result = _run_guard(tmp_path)
    # ``rev_pkt_`` qualifier exempts this historical changelog
    assert result.returncode == 0


def test_v4_44_1_live_repo_still_passes_after_broadened_scan() -> None:
    """v4.44.1: the live repo (post-v4.44.1 edits) must still pass under
    the broadened contextual scan. This protects against regressions
    where a doc edit silently reintroduces stale prose authority."""
    live_repo_root = Path(__file__).resolve().parents[5]
    result = _run_guard(live_repo_root)
    assert result.returncode == 0, (
        f"Live repo failed broadened prose-authority guard:\n{result.stdout}"
    )


# ---------------------------------------------------------------------------
# v4.44.2 (rev_pkt_4726) — default repo-root regression
# ---------------------------------------------------------------------------


def test_v4_44_2_default_repo_root_matches_explicit_repo_root() -> None:
    """v4.44.2 (rev_pkt_4726): direct CLI invocation WITHOUT ``--repo-root``
    MUST scan the same maintained-doc paths as an explicit
    ``--repo-root <live_repo>`` invocation. Codex caught the v4.44.1
    ``parents[2]`` bug because direct CLI returned ``ok: True, violation_count: 0``
    while focused pytest (which passes ``--repo-root``) showed live violations.
    This test pins the default-mode resolution so a future ``parents[N]`` typo
    cannot silently mask live violations.
    """
    live_repo_root = Path(__file__).resolve().parents[5]
    guard_script = live_repo_root / "dev/scripts/checks/check_no_prose_authority_promotion.py"
    # Run WITHOUT --repo-root (uses script's default resolution)
    default_result = subprocess.run(
        [sys.executable, str(guard_script), "--format", "json"],
        capture_output=True,
        text=True,
        timeout=15,
        cwd=str(live_repo_root),
    )
    # Run WITH --repo-root pointing at the same live repo
    explicit_result = _run_guard(live_repo_root, fmt="json")
    # Both must agree on ok-ness and violation count — proves default resolution
    # is pointing at the real repo root, not <repo>/dev or some other parent.
    default_payload = json.loads(default_result.stdout)
    explicit_payload = json.loads(explicit_result.stdout)
    assert default_payload["ok"] == explicit_payload["ok"], (
        f"default-mode ok={default_payload['ok']} differs from explicit "
        f"--repo-root ok={explicit_payload['ok']}; default resolution likely "
        f"points at the wrong directory. default_stdout={default_result.stdout[:500]}"
    )
    assert default_payload["violation_count"] == explicit_payload["violation_count"], (
        f"default-mode violation_count={default_payload['violation_count']} "
        f"differs from explicit --repo-root "
        f"violation_count={explicit_payload['violation_count']}; default "
        f"resolution likely scanning a different doc set."
    )
    # Maintained doc paths must be identical between both invocations
    assert default_payload["maintained_doc_paths"] == explicit_payload["maintained_doc_paths"]


# ---------------------------------------------------------------------------
# v4.44.3 (rev_pkt_4728) — broadened scope (8 docs) + new dangerous terms
# ---------------------------------------------------------------------------


def test_v4_44_3_scope_includes_master_plan_md(tmp_path: Path) -> None:
    """v4.44.3 (rev_pkt_4728): ``dev/active/MASTER_PLAN.md`` is now in
    the maintained-doc scope so codex's verbatim false-negative
    ``MASTER_PLAN.md says it is the 'single active plan for strategy,
    execution, and release tracking'`` is caught."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "MASTER_PLAN.md").write_text(
        "# Master Plan\n\n"
        "- This file is the single active plan for strategy, execution, "
        "and release tracking.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "single active plan" in result.stdout


def test_v4_44_3_scope_includes_ai_governance_platform_md(tmp_path: Path) -> None:
    """v4.44.3: ``dev/active/ai_governance_platform.md`` is now in scope so
    the verbatim false-negative ``canonical active architecture plan`` is
    caught."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "ai_governance_platform.md").write_text(
        "# AI Governance Platform Plan\n\n"
        "This is the canonical active architecture plan for the standalone "
        "governance product scope.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "canonical active" in result.stdout


def test_v4_44_3_scope_includes_platform_authority_loop_md(tmp_path: Path) -> None:
    """v4.44.3: ``dev/active/platform_authority_loop.md`` is in scope so the
    line ``governed markdown becomes structured authority`` is caught."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "platform_authority_loop.md").write_text(
        "# Platform Authority Loop\n\n"
        "Context budgets so governed markdown becomes structured authority.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "markdown becomes structured authority" in result.stdout


def test_v4_44_3_scope_includes_platform_guide_md(tmp_path: Path) -> None:
    """v4.44.3: ``dev/guides/PLATFORM_GUIDE.md`` is in scope so codex's
    verbatim ``read the active authority docs`` is caught."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "PLATFORM_GUIDE.md").write_text(
        "# Platform Guide\n\n"
        "Then read the active authority docs for your scope.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "active authority docs" in result.stdout


def test_v4_44_3_scope_includes_ai_governance_platform_guide_md(tmp_path: Path) -> None:
    """v4.44.3: ``dev/guides/AI_GOVERNANCE_PLATFORM.md`` is in scope so
    codex's verbatim ``executable source of truth`` is caught."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "AI_GOVERNANCE_PLATFORM.md").write_text(
        "# AI Governance Platform Guide\n\n"
        "That command is the executable source of truth for the shared "
        "layer model.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "executable source of truth" in result.stdout


def test_v4_44_3_tracker_authority_caught(tmp_path: Path) -> None:
    """v4.44.3: ``tracker authority`` is now a dangerous term (codex's
    verbatim ``MASTER_PLAN stays the repo-wide tracker authority``)."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "ai_governance_platform.md").write_text(
        "# Plan\n\n"
        "`MASTER_PLAN` stays the repo-wide tracker authority for "
        "all execution state.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "tracker authority" in result.stdout


def test_v4_44_3_router_authority_caught(tmp_path: Path) -> None:
    """v4.44.3: ``router authority`` is now a dangerous term."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "ai_governance_platform.md").write_text(
        "# Plan\n\n"
        "Retain `dev/active/INDEX.md` as router authority for plan "
        "navigation.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "router authority" in result.stdout


def test_v4_44_3_execution_authority_caught(tmp_path: Path) -> None:
    """v4.44.3: ``execution authority`` is now a dangerous term."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "MASTER_PLAN.md").write_text(
        "# Plan\n\n"
        "- Execution-owner budget: keep repo-wide execution authority "
        "at five or fewer active docs.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "execution authority" in result.stdout


def test_v4_44_3_only_main_active_plan_caught(tmp_path: Path) -> None:
    """v4.44.3: ``only main active plan`` is now a dangerous term."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "ai_governance_platform.md").write_text(
        "# Plan\n\n"
        "Treat this file as the only main active plan for the standalone "
        "governance product scope.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "only main active plan" in result.stdout


def test_v4_44_3_canonical_findings_caught(tmp_path: Path) -> None:
    """v4.44.3: ``canonical findings`` is now a dangerous term."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "DEVELOPMENT.md").write_text(
        "# Development\n\n"
        "- `dev/active/audit.md` -- canonical findings + execution "
        "checklist for pre-release audit work.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "canonical findings" in result.stdout


def test_v4_44_3_typed_planrow_qualifier_exempts(tmp_path: Path) -> None:
    """v4.44.3: a line with ``execution authority`` BUT also with
    ``typed PlanRow`` qualifier MUST NOT be flagged. This protects
    correctly-framed sentences like ``execution authority lives in typed
    PlanRow rows``."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "ai_governance_platform.md").write_text(
        "# Plan\n\n"
        "After ingestion, execution authority lives in typed `PlanRow` "
        "rows and is mirrored as projections only.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 0


def test_v4_44_3_completed_task_line_exempts(tmp_path: Path) -> None:
    """v4.44.3: a completed task line ``- [x] MP-...`` MUST NOT fire even
    if it mentions a dangerous term, because the task is bound to a typed
    PlanRow by ID."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "MASTER_PLAN.md").write_text(
        "# Plan\n\n"
        "- [x] MP-148 Activate the Theme Studio phased track in "
        "`MASTER_PLAN` and lock the canonical tracker IA boundary.\n"
    )
    result = _run_guard(tmp_path)
    # `- [x] ` exempt marker should override `canonical tracker` dangerous term
    assert result.returncode == 0


def test_v4_44_3_negation_exempts(tmp_path: Path) -> None:
    """v4.44.3: lines that NEGATE a dangerous claim (``not a replacement
    execution authority``, ``without treating it as execution authority``)
    MUST NOT be flagged."""
    doc_dir = tmp_path / "dev" / "active"
    doc_dir.mkdir(parents=True)
    (doc_dir / "MASTER_PLAN.md").write_text(
        "# Plan\n\n"
        "Markdown stays a projection, not a replacement execution authority.\n"
        "Writeback sinks without treating it as execution authority.\n"
    )
    result = _run_guard(tmp_path)
    # Both lines have negation qualifiers ("not a replacement", "without treating")
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# v4.45.1 (rev_pkt_4735) — tighten qualifier matching for broad nouns
# ---------------------------------------------------------------------------


def test_v4_45_1_bare_contracts_no_longer_exempts_source_of_truth(tmp_path: Path) -> None:
    """v4.45.1 (rev_pkt_4735 verbatim reproduction): a bare ``contracts``
    appearing in an unrelated clause MUST NOT exempt the line. The previous
    qualifier matcher exempted any line where any qualifier word appeared
    anywhere, including ``contracts may disagree`` which doesn't frame
    contracts as durable authority. The compound-form qualifiers
    (``typed contracts``, ``in contracts``, etc.) now require framing intent.
    """
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "DEVELOPMENT.md").write_text(
        "This markdown file is the source of truth for startup behavior; "
        "contracts may disagree.\n"
    )
    result = _run_guard(tmp_path)
    # Codex's verbatim case — must now fail (was passing pre-v4.45.1)
    assert result.returncode == 1
    assert "source of truth" in result.stdout


def test_v4_45_1_typed_contracts_compound_still_exempts(tmp_path: Path) -> None:
    """v4.45.1 defensive: the compound form ``typed contracts`` demonstrates
    framing intent and MUST still exempt the line."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "DEVELOPMENT.md").write_text(
        "Execution authority lives in typed contracts, receipts, and guards.\n"
    )
    result = _run_guard(tmp_path)
    # Has ``typed contracts`` compound qualifier
    assert result.returncode == 0


def test_v4_45_1_in_contracts_preposition_exempts(tmp_path: Path) -> None:
    """v4.45.1 defensive: ``in contracts`` (preposition form) demonstrates
    framing intent and MUST still exempt the line."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "DEVELOPMENT.md").write_text(
        "The source of truth for startup blockers is encoded in contracts "
        "and surfaced via the typed PlanRow store.\n"
    )
    result = _run_guard(tmp_path)
    # Has ``in contracts`` AND ``typed planrow`` qualifiers
    assert result.returncode == 0


def test_v4_45_1_bare_reducer_no_longer_exempts(tmp_path: Path) -> None:
    """v4.45.1: a bare ``reducer`` appearing in an unrelated clause MUST
    NOT exempt a dangerous claim."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "DEVELOPMENT.md").write_text(
        "AGENTS.md is the source of truth; the reducer is a separate concern.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "source of truth" in result.stdout


def test_v4_45_1_reducer_state_compound_exempts(tmp_path: Path) -> None:
    """v4.45.1 defensive: ``reducer state`` compound MUST still exempt."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "DEVELOPMENT.md").write_text(
        "The execution authority lives in reducer state, not in this prose.\n"
    )
    result = _run_guard(tmp_path)
    # Has ``reducer state`` compound qualifier
    assert result.returncode == 0


def test_v4_45_1_bare_receipts_no_longer_exempts(tmp_path: Path) -> None:
    """v4.45.1: a bare ``receipts`` in unrelated clause MUST NOT exempt."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "DEVELOPMENT.md").write_text(
        "MASTER_PLAN.md is the source of truth; receipts come later.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 1
    assert "source of truth" in result.stdout


def test_v4_45_1_typed_receipts_compound_exempts(tmp_path: Path) -> None:
    """v4.45.1 defensive: ``typed receipts`` compound MUST still exempt."""
    doc_dir = tmp_path / "dev" / "guides"
    doc_dir.mkdir(parents=True)
    (doc_dir / "DEVELOPMENT.md").write_text(
        "The tracker authority for `MP-377` lives in typed receipts and "
        "the typed PlanRow store.\n"
    )
    result = _run_guard(tmp_path)
    assert result.returncode == 0


def test_v4_45_1_live_repo_still_green() -> None:
    """v4.45.1: the live repo must still pass after qualifier tightening.
    Protects against regressions where the precision fix unintentionally
    re-flags correctly-framed live-repo lines."""
    live_repo_root = Path(__file__).resolve().parents[5]
    result = _run_guard(live_repo_root)
    assert result.returncode == 0, (
        f"Live repo failed after v4.45.1 qualifier tightening:\n{result.stdout}"
    )
