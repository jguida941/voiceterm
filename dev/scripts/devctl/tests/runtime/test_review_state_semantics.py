from dev.scripts.devctl.runtime.review_state_semantics import (
    classify_implementer_ack_state,
    is_pending_implementer_state,
)


def test_pending_implementer_state_accepts_waiting_for_ack_status() -> None:
    assert is_pending_implementer_state(
        implementer_status="waiting_for_ack",
        implementer_ack="pending",
        implementer_ack_state="",
    )


def test_classify_implementer_ack_state_marks_waiting_for_ack_as_pending() -> None:
    assert (
        classify_implementer_ack_state(
            implementer_status="waiting_for_ack",
            implementer_ack="pending",
            implementer_ack_state="",
            ack_current=False,
            stale_label="stale",
            is_substantive_text=lambda value: bool(str(value or "").strip()),
        )
        == "pending"
    )
