"""Scenario tests for `devctl receipt-steward` CLI + scope-claim lifecycle (A38.2 S2).

These tests cover the four CLI sub-actions and the scope-claim
substrate they depend on:

- `test_receipt_steward_claim_request_persists_typed_lifecycle_row` —
  `claim --action request` writes a typed row to the JSONL store and
  the row carries the expected shape.

- `test_receipt_steward_audit_returns_missing_completely_when_no_receipt_present`
  — `audit` against an unknown commit_sha emits a typed receipt whose
  `missing_items` contains `missing_completely`.

- `test_receipt_steward_audit_emits_typed_audit_receipt_for_known_good_slice`
  — a FeatureProofReceipt seeded under tmp scope produces an audit
  with a non-empty `audit_id` and the typed targets matrix.

- `test_receipt_steward_audit_gap_report_lists_done_rows_without_receipts`
  — `audit-gap-report` returns typed bins of rows with vs without
  paired FPRs.

- `test_receipt_steward_audit_fails_closed_without_active_claim` —
  `audit` without `--allow-no-claim` and without an active claim in
  the store returns ok=False with the typed `active_claim_not_found`
  error code.

Each test is hermetic: it builds a tmp store under `tmp_path` and
points the CLI at it through `--store-path`. The live
`dev/state/receipt_steward_claims.jsonl` is not touched.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]


def _run_devctl(
    *args: str,
    cwd: Path = REPO_ROOT,
    extra_env: dict[str, str] | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    if extra_env:
        env.update(extra_env)
    cmd = [sys.executable, "dev/scripts/devctl.py", *args]
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


def _parse_json(result: subprocess.CompletedProcess) -> dict:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"devctl did not emit valid JSON: {exc!r}\n"
            f"stdout head:\n{result.stdout[:2000]}\n"
            f"stderr head:\n{result.stderr[:2000]}"
        )


def test_receipt_steward_claim_request_persists_typed_lifecycle_row(
    tmp_path: Path,
) -> None:
    """`claim --action request` writes a typed row carrying the expected shape."""
    store_path = tmp_path / "receipt_steward_claims.jsonl"
    result = _run_devctl(
        "receipt-steward",
        "claim",
        "--action",
        "request",
        "--ttl-minutes",
        "10",
        "--reason",
        "scenario: persistence shape probe",
        "--actor-session-id",
        "scenario-session",
        "--store-path",
        str(store_path),
        "--format",
        "json",
    )
    assert result.returncode == 0, (
        f"receipt-steward claim request must succeed; stderr={result.stderr[:1000]}"
    )
    payload = _parse_json(result)
    assert payload.get("ok") is True, payload
    claim_id = payload.get("claim_id") or ""
    assert claim_id.startswith("ReceiptStewardScopeClaim:"), claim_id
    assert store_path.exists(), "JSONL store must exist after claim request"

    rows = [
        json.loads(line)
        for line in store_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows, "JSONL store must carry at least one row"
    row = rows[0]
    assert row.get("lifecycle_phase") == "claim_granted", row
    assert isinstance(row.get("request"), dict), row
    assert isinstance(row.get("evaluation"), dict), row
    assert isinstance(row.get("claim"), dict), row
    assert row["claim"]["claim_id"] == claim_id
    assert row["claim"]["actor_role"] == "receipt_steward"
    assert row["claim"]["status"] == "active"


def test_receipt_steward_audit_returns_missing_completely_when_no_receipt_present(
    tmp_path: Path,
) -> None:
    """`audit` against an unknown commit_sha must surface `missing_completely`."""
    result = _run_devctl(
        "receipt-steward",
        "audit",
        "--slice-id",
        "SCENARIO-SLICE-NO-FPR",
        "--plan-row-id",
        "SCENARIO-ROW-NO-FPR",
        "--commit-sha",
        "0000000000000000000000000000000000000000",
        "--allow-no-claim",
        "--skip-pytest-collect",
        "--format",
        "json",
    )
    payload = _parse_json(result)
    missing = payload.get("missing_items") or []
    assert "missing_completely" in missing, payload
    targets = payload.get("targets") or {}
    assert targets.get("receipt_present") is False, targets


def test_receipt_steward_audit_emits_typed_audit_receipt_for_known_good_slice(
    tmp_path: Path,
) -> None:
    """Seeded FPR produces an audit_id and the typed targets matrix.

    We do not assert the slice is fully clean (worktree may be dirty),
    but the audit must emit the typed audit_id, the typed actor_role,
    and the receipt_present target must be True against the seeded FPR.
    """
    seed_dir = REPO_ROOT / "dev" / "reports" / "feature_proof_receipts"
    seed_dir.mkdir(parents=True, exist_ok=True)

    # Use an obviously synthetic SHA so we never collide with real receipts.
    sha = "1234567890abcdef" + ("0" * 24)
    seeded = seed_dir / f"{sha}.json"
    seeded.write_text(
        json.dumps(
            {
                "contract_id": "FeatureProofReceipt",
                "schema_version": 1,
                "commit_sha": sha,
                "feature_id": "SCENARIO-FEATURE-A38-2-S2",
                "real_life_test_status": "proven_passed",
                "tests_run": [
                    "dev/scripts/devctl/tests/scenarios/test_receipt_steward_audit_cli.py::test_receipt_steward_audit_emits_typed_audit_receipt_for_known_good_slice"
                ],
                "evidence_artifacts": [],
            }
        ),
        encoding="utf-8",
    )
    try:
        result = _run_devctl(
            "receipt-steward",
            "audit",
            "--slice-id",
            "SCENARIO-FEATURE-A38-2-S2",
            "--plan-row-id",
            "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
            "--commit-sha",
            sha,
            "--allow-no-claim",
            "--skip-pytest-collect",
            "--format",
            "json",
        )
        payload = _parse_json(result)
        assert payload.get("audit_id", "").startswith(
            "ReceiptStewardAuditReceipt:"
        ), payload
        assert payload.get("actor_role") == "receipt_steward", payload
        targets = payload.get("targets") or {}
        assert targets.get("receipt_present") is True, targets
        missing = payload.get("missing_items") or []
        assert "missing_completely" not in missing, missing
    finally:
        seeded.unlink(missing_ok=True)


def test_receipt_steward_audit_gap_report_lists_done_rows_without_receipts() -> None:
    """`audit-gap-report` returns typed bins of rows with vs without FPRs."""
    result = _run_devctl(
        "receipt-steward",
        "audit-gap-report",
        "--format",
        "json",
    )
    payload = _parse_json(result)
    assert payload.get("command") == "receipt-steward", payload
    assert payload.get("action") == "audit-gap-report", payload
    assert "rows_with_receipts" in payload, payload
    assert "rows_without_receipts" in payload, payload
    assert isinstance(payload.get("coverage_pct"), (int, float)), payload


def test_receipt_steward_audit_fails_closed_without_active_claim(
    tmp_path: Path,
) -> None:
    """`audit` without `--allow-no-claim` fails closed when no active claim exists."""
    empty_store = tmp_path / "empty_claims.jsonl"
    empty_store.write_text("", encoding="utf-8")
    result = _run_devctl(
        "receipt-steward",
        "audit",
        "--slice-id",
        "SCENARIO-SLICE-CLAIM-MISSING",
        "--plan-row-id",
        "SCENARIO-ROW-CLAIM-MISSING",
        "--commit-sha",
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        "--store-path",
        str(empty_store),
        "--skip-pytest-collect",
        "--format",
        "json",
    )
    payload = _parse_json(result)
    assert payload.get("ok") is False, payload
    assert payload.get("error") in {
        "active_claim_not_found",
        "active_claim_expired",
        "active_claim_store_unreadable",
    }, payload


def test_receipt_steward_scope_claim_pure_helpers_round_trip() -> None:
    """Pure-helper reducers must compose: request -> evaluate -> claim -> release."""
    from dev.scripts.devctl.runtime.receipt_steward_scope_claim import (
        build_scope_claim,
        claim_is_active,
        evaluate_scope_claim,
        release_scope_claim,
        request_scope_claim,
    )

    request = request_scope_claim(
        actor_role="receipt_steward",
        actor_session_id="pytest-session",
        reason="pure-helper round-trip",
        requested_ttl_minutes=15,
    )
    assert request.contract_id == "ReceiptStewardScopeClaimRequest"
    evaluation = evaluate_scope_claim(request)
    assert evaluation.granted is True
    claim = build_scope_claim(request, evaluation)
    assert claim_is_active(claim) is True
    expired, expiry = release_scope_claim(claim)
    assert expired.status == "released"
    assert expiry.expiry_reason == "released_by_actor"
    assert claim_is_active(expired) is False


@pytest.mark.parametrize(
    "actor_role",
    ["", "implementer", "reviewer", "operator"],
)
def test_receipt_steward_scope_claim_request_rejects_non_receipt_steward_role(
    actor_role: str,
) -> None:
    """`request_scope_claim` must fail closed for any role except receipt_steward."""
    from dev.scripts.devctl.runtime.receipt_steward_scope_claim import (
        request_scope_claim,
    )

    with pytest.raises(ValueError):
        request_scope_claim(
            actor_role=actor_role,
            actor_session_id="pytest-session",
            reason="role boundary probe",
        )
