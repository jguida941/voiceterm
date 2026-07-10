from dev.scripts.devctl.runtime.command_output_consumption_receipt import (
    COMMAND_OUTPUT_CONSUMPTION_RECEIPT_CONTRACT_ID,
    build_command_output_consumption_receipt,
    command_output_consumption_receipt_from_mapping,
)


def test_command_output_consumption_receipt_round_trips() -> None:
    receipt = build_command_output_consumption_receipt(
        command_output_receipt_id="command_output:agent-loop:abc123",
        command_name="agent-loop",
        output_sha256="a" * 64,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_fields=("may_mutate", "next_action"),
        extracted_authority_values={
            "may_mutate": False,
            "next_action": "run_devctl_push",
        },
        extracted_blockers=("wait_for_scoped_packet",),
        extracted_permissions=("may_mutate=false",),
        extracted_next_actions=("do_not_push",),
        contradiction_flags=("push_projected_while_mutation_blocked",),
        resulting_decision="wait",
        decision_rationale="controller denied mutation",
        evidence_refs=("rev_pkt_4384",),
    )

    payload = receipt.to_dict()
    parsed = command_output_consumption_receipt_from_mapping(payload)

    assert payload["contract_id"] == COMMAND_OUTPUT_CONSUMPTION_RECEIPT_CONTRACT_ID
    assert parsed.receipt_id == receipt.receipt_id
    assert parsed.extracted_authority_fields == ("may_mutate", "next_action")
    assert parsed.extracted_authority_values == {
        "may_mutate": False,
        "next_action": "run_devctl_push",
    }
    assert parsed.extracted_blockers == ("wait_for_scoped_packet",)
    assert parsed.contradiction_flags == ("push_projected_while_mutation_blocked",)


def test_command_output_consumption_receipt_id_binds_disposition() -> None:
    base = build_command_output_consumption_receipt(
        command_output_receipt_id="command_output:agent-loop:abc123",
        command_name="agent-loop",
        output_sha256="a" * 64,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_values={"may_mutate": False},
        resulting_decision="wait",
        decision_rationale="controller denied mutation",
    )
    changed = build_command_output_consumption_receipt(
        command_output_receipt_id="command_output:agent-loop:abc123",
        command_name="agent-loop",
        output_sha256="a" * 64,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_values={"may_mutate": True},
        resulting_decision="edit",
        decision_rationale="operator override active",
    )

    assert base.receipt_id != changed.receipt_id
