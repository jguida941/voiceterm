from dev.scripts.checks.check_commit_body_packet_anchors import (
    evaluate_commit_body_packet_anchors,
)


def _record(commit_sha: str, message: str) -> str:
    return f"{commit_sha}\n{message}\n\x1e\n"


def test_mp_slice_commit_with_packet_anchor_passes() -> None:
    report = evaluate_commit_body_packet_anchors(
        log_text=_record(
            "abc1234",
            "MP-378-LAUNCH-BOOTSTRAP-FIX-S5: build guard\n\nRefs: rev_pkt_4017",
        )
    )

    assert report.ok is True
    assert report.would_fail is False
    assert report.mp_slice_commit_count == 1
    assert report.violation_count == 0


def test_mp_slice_commit_with_task_started_anchor_passes() -> None:
    report = evaluate_commit_body_packet_anchors(
        log_text=_record(
            "abc1234",
            "MP-378-LAUNCH-BOOTSTRAP-FIX-S6: build guard\n\nTask: task_started",
        )
    )

    assert report.mp_slice_commit_count == 1
    assert report.violation_count == 0


def test_mp_slice_commit_without_anchor_reports_violation() -> None:
    report = evaluate_commit_body_packet_anchors(
        log_text=_record(
            "abc1234",
            "MP-378-LAUNCH-BOOTSTRAP-FIX-S7: build guard\n\nNo packet refs.",
        )
    )

    assert report.ok is True
    assert report.report_only is True
    assert report.would_fail is True
    assert report.violation_count == 1
    assert report.violations[0]["commit_sha"] == "abc1234"
    assert report.violations[0]["mp_slice_refs"] == [
        "MP-378-LAUNCH-BOOTSTRAP-FIX-S7"
    ]


def test_non_mp_slice_commit_is_ignored() -> None:
    report = evaluate_commit_body_packet_anchors(
        log_text=_record("abc1234", "Refresh external review snapshot")
    )

    assert report.scanned_commit_count == 1
    assert report.mp_slice_commit_count == 0
    assert report.violation_count == 0
