"""Idris-style typechecker gate over campaign mutation_allowed.

These tests pin the new contract that ``campaign_report`` must AND-combine the
``GovernedTransitionTypeChecker`` verdict into ``mutation_allowed``. A
``pending_count`` of zero is no longer enough: every closed lifecycle row must
itself typecheck via ``IdempotentReemit`` semantics, otherwise mutation stays
fail-closed and the failure surfaces in ``publication_proof_summary``.
"""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.commands.development.campaign import campaign_report
from dev.scripts.devctl.commands.development.campaign_idris_gate import (
    TypeCheckerVerdict,
    campaign_typechecker_verdict,
)
from dev.scripts.devctl.commands.development.models import DevelopmentPacketAttention

_REVIEW_STATE_OK = {
    "reviewer_runtime": {"session_posture": {"interaction_mode": "remote_control"}},
    "coordination_state": {
        "coordination_topology": "multi_agent_active",
        "legacy_reviewer_mode": "active_dual_agent",
    },
}


def _write_lifecycles(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def _well_formed_closed_row(lifecycle_id: str) -> dict:
    """A closed_via_commit_anchor row whose composed refs resolve via lifecycle evidence."""
    validation_ref = f"validation_receipt:{lifecycle_id}"
    return {
        "lifecycle_id": lifecycle_id,
        "status": "closed_via_commit_anchor",
        "authority_evidence_refs": [validation_ref],
        "resolution": {
            "resolution_id": f"resolution:{lifecycle_id}",
            "exception_lifecycle_id": lifecycle_id,
            "finding_id": f"finding:{lifecycle_id}",
            "status": "closed",
            "root_cause_class": "ok",
            "root_cause_summary": "ok",
        },
        "closure_proof": {
            "closure_proof_id": f"closure:{lifecycle_id}",
            "exception_lifecycle_id": lifecycle_id,
            "normal_command": "noop",
            "validation_receipt_id": validation_ref,
        },
    }


def test_typechecker_passes_when_closed_rows_carry_well_formed_proof(
    tmp_path: Path,
) -> None:
    store_path = tmp_path / "governed_exception_lifecycles.jsonl"
    _write_lifecycles(store_path, [_well_formed_closed_row("gel:test:ok")])

    verdict = campaign_typechecker_verdict(store_path)

    assert isinstance(verdict, TypeCheckerVerdict)
    assert verdict.allows_mutation is True
    assert verdict.rows_typechecked == 1
    assert verdict.blocking_errors == ()
    assert verdict.summary.startswith("typecheck=ok")


def test_typechecker_blocks_when_closed_row_lacks_closure_proof(
    tmp_path: Path,
) -> None:
    store_path = tmp_path / "governed_exception_lifecycles.jsonl"
    _write_lifecycles(
        store_path,
        [{"lifecycle_id": "gel:test:bad", "status": "closed_via_commit_anchor"}],
    )

    verdict = campaign_typechecker_verdict(store_path)
    assert verdict.allows_mutation is False
    assert verdict.rows_typechecked == 1
    error_codes = {error.code.value for error in verdict.blocking_errors}
    assert "missing_closure_proof" in error_codes

    report = campaign_report(
        _REVIEW_STATE_OK,
        packet_attention=DevelopmentPacketAttention(),
        exception_store_path=store_path,
    )
    assert report.mutation_allowed is False
    assert report.fail_closed is True
    assert "typecheck=blocked" in report.publication_proof_summary


def test_typechecker_surfaces_multiple_errors_in_publication_proof_summary(
    tmp_path: Path,
) -> None:
    """Two malformed closed rows: both errors must appear and the summary tags ``blocked``."""
    store_path = tmp_path / "governed_exception_lifecycles.jsonl"
    _write_lifecycles(
        store_path,
        [
            {"lifecycle_id": "gel:test:a", "status": "closed_via_commit_anchor"},
            {"lifecycle_id": "gel:test:b", "status": "closed"},
        ],
    )

    verdict = campaign_typechecker_verdict(store_path)
    assert verdict.allows_mutation is False
    # Each row should contribute at least one blocking error.
    assert len(verdict.blocking_errors) >= 2
    lifecycle_ids = {error.lifecycle_id for error in verdict.blocking_errors}
    assert "gel:test:a" in lifecycle_ids
    assert "gel:test:b" in lifecycle_ids

    report = campaign_report(
        _REVIEW_STATE_OK,
        packet_attention=DevelopmentPacketAttention(),
        exception_store_path=store_path,
    )
    assert "typecheck=blocked" in report.publication_proof_summary
    # Base publication_proof_summary contents stay intact.
    assert "exceptions=" in report.publication_proof_summary
    assert "push_status=" in report.publication_proof_summary


def test_typechecker_no_op_when_no_closed_rows(tmp_path: Path) -> None:
    """Empty store and pending-only stores must not block mutation by themselves."""
    store_path = tmp_path / "governed_exception_lifecycles.jsonl"
    store_path.write_text("", encoding="utf-8")

    verdict = campaign_typechecker_verdict(store_path)
    assert verdict.allows_mutation is True
    assert verdict.rows_typechecked == 0
    assert verdict.summary.startswith("typecheck=ok")

    # Only-pending rows: typechecker should not inspect them; pending debt is
    # already handled by exception_projection.pending_count.
    _write_lifecycles(
        store_path,
        [{"lifecycle_id": "gel:pending:1", "status": "open"}],
    )
    pending_verdict = campaign_typechecker_verdict(store_path)
    assert pending_verdict.allows_mutation is True
    assert pending_verdict.rows_typechecked == 0


def test_existing_mutation_factors_still_dominate_when_typecheck_passes(
    tmp_path: Path,
) -> None:
    """A well-formed-closed store must not silently grant mutation_allowed.

    ``mutation_allowed`` still requires a codex-implementer with may_mutate, so a
    passing typechecker does not flip an otherwise read-only campaign to True.
    Regression guard: the new gate must compose AND, never OR, with prior logic.
    """
    store_path = tmp_path / "governed_exception_lifecycles.jsonl"
    _write_lifecycles(store_path, [_well_formed_closed_row("gel:test:ok")])

    report = campaign_report(
        _REVIEW_STATE_OK,
        packet_attention=DevelopmentPacketAttention(),
        exception_store_path=store_path,
    )
    # No agent_work_board rows / agent_loop_decisions present in review_state,
    # so no role.may_mutate=True. mutation_allowed must remain False even though
    # the typechecker is happy.
    assert report.mutation_allowed is False
    # Typechecker should announce its pass so reviewers can tell the gate ran.
    assert "typecheck=ok" in report.publication_proof_summary
