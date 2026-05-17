from __future__ import annotations

from dev.scripts.devctl.runtime.file_hashes import hash_bytes
from dev.scripts.devctl.runtime.quality_repair_scheduler import (
    CloudFinding,
    FindingAffectedScope,
    reconcile_finding_applicability,
    repair_packet_for_applicable_finding,
    stale_receipt_for_inapplicable_finding,
)


def test_current_cloud_finding_authorizes_repair_packet(tmp_path) -> None:
    target = tmp_path / "app.py"
    target.write_text("print('ok')\n", encoding="utf-8")
    finding = _finding("F-1", "app.py", target.read_bytes())

    applicability = reconcile_finding_applicability(
        repo_root=tmp_path,
        finding=finding,
    )
    packet = repair_packet_for_applicable_finding(
        finding=finding,
        applicability=applicability,
    )

    assert applicability.status == "current"
    assert applicability.repair_authorized is True
    assert applicability.current_paths == ("app.py",)
    assert packet is not None
    assert packet.finding_id == "F-1"
    assert stale_receipt_for_inapplicable_finding(
        finding=finding,
        applicability=applicability,
    ) is None


def test_changed_cloud_finding_becomes_stale(tmp_path) -> None:
    target = tmp_path / "app.py"
    target.write_text("before\n", encoding="utf-8")
    finding = _finding("F-2", "app.py", target.read_bytes())
    target.write_text("after\n", encoding="utf-8")

    applicability = reconcile_finding_applicability(
        repo_root=tmp_path,
        finding=finding,
    )
    receipt = stale_receipt_for_inapplicable_finding(
        finding=finding,
        applicability=applicability,
    )

    assert applicability.status == "stale"
    assert applicability.repair_authorized is False
    assert applicability.stale_paths == ("app.py",)
    assert repair_packet_for_applicable_finding(
        finding=finding,
        applicability=applicability,
    ) is None
    assert receipt is not None
    assert receipt.stale_paths == ("app.py",)
    assert receipt.reason == "affected_file_hash_changed"


def test_missing_cloud_finding_file_blocks_repair(tmp_path) -> None:
    finding = CloudFinding(
        finding_id="F-3",
        source_snapshot_id="cloud-snap",
        affected_scopes=(
            FindingAffectedScope(
                path="missing.py",
                file_sha256=hash_bytes(b"previous"),
            ),
        ),
    )

    applicability = reconcile_finding_applicability(
        repo_root=tmp_path,
        finding=finding,
    )

    assert applicability.status == "missing_file"
    assert applicability.missing_paths == ("missing.py",)
    assert applicability.repair_authorized is False


def test_cloud_finding_without_hash_scope_is_reconciliation_only(tmp_path) -> None:
    finding = CloudFinding(
        finding_id="F-4",
        source_snapshot_id="cloud-snap",
        affected_scopes=(),
    )

    applicability = reconcile_finding_applicability(
        repo_root=tmp_path,
        finding=finding,
    )

    assert applicability.status == "reconciliation_only"
    assert applicability.reason == "no_affected_file_hashes"
    assert applicability.repair_authorized is False


def _finding(finding_id: str, path: str, content: bytes) -> CloudFinding:
    return CloudFinding(
        finding_id=finding_id,
        source_snapshot_id="cloud-snap",
        affected_scopes=(
            FindingAffectedScope(path=path, file_sha256=hash_bytes(content)),
        ),
    )
