from dev.scripts.checks.command_output_consumed.command import build_report, render_markdown
from dev.scripts.devctl.runtime.command_output_consumption_receipt import (
    build_command_output_consumption_receipt,
)
from dev.scripts.devctl.runtime.command_output_receipt import (
    build_command_output_receipt,
)


def test_authority_output_without_consumption_fails() -> None:
    output = build_command_output_receipt(
        command_name="agent-loop",
        command=("python3", "dev/scripts/devctl.py", "agent-loop"),
        cwd=".",
        exit_code=0,
        stdout='{"may_mutate": false, "next_action": "run_devctl_push"}',
    )

    report = build_report(report_override={"receipt": output.to_dict()})

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "authority_output_unconsumed"


def test_authority_output_with_consumption_passes() -> None:
    output = build_command_output_receipt(
        command_name="agent-loop",
        command=("python3", "dev/scripts/devctl.py", "agent-loop"),
        cwd=".",
        exit_code=0,
        stdout='{"may_mutate": false, "next_action": "run_devctl_push"}',
    )
    consumption = build_command_output_consumption_receipt(
        command_output_receipt_id=output.receipt_id,
        command_name="agent-loop",
        output_sha256=output.stdout_sha256,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_fields=("may_mutate", "next_action"),
        extracted_authority_values={
            "may_mutate": False,
            "next_action": "run_devctl_push",
        },
        extracted_blockers=("may_mutate=false",),
        extracted_next_actions=("do_not_push",),
        contradiction_flags=("push_projected_while_mutation_blocked",),
        resulting_decision="wait",
        decision_rationale="controller denied mutation",
    )

    report = build_report(
        report_override={
            "command_output_receipt": output.to_dict(),
            "consumption": consumption.to_dict(),
        }
    )

    assert report["ok"] is True
    assert report["authority_bearing_receipt_count"] == 1


def test_failed_authority_output_fails_even_when_consumed() -> None:
    output = build_command_output_receipt(
        command_name="check_feature_has_proof_receipt",
        command=("python3", "dev/scripts/checks/check_feature_has_proof_receipt.py"),
        cwd=".",
        exit_code=1,
        stdout="violation_count: 2",
    )
    consumption = build_command_output_consumption_receipt(
        command_output_receipt_id=output.receipt_id,
        command_name="check_feature_has_proof_receipt",
        output_sha256=output.stdout_sha256,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_blockers=("strict_fpr_failed",),
        resulting_decision="repair",
        decision_rationale="strict FPR failed",
    )

    report = build_report(
        report_override={
            "command_output_receipt": output.to_dict(),
            "consumption": consumption.to_dict(),
        }
    )

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "authority_output_assertions_failed"


def test_tail_only_authority_output_without_full_artifact_fails() -> None:
    output = build_command_output_receipt(
        command_name="agent-loop",
        command=("python3", "dev/scripts/devctl.py", "agent-loop"),
        cwd=".",
        exit_code=0,
        stdout='{"may_mutate": true}',
        capture_scope="tail",
    )
    consumption = build_command_output_consumption_receipt(
        command_output_receipt_id=output.receipt_id,
        command_name="agent-loop",
        output_sha256=output.stdout_sha256,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_fields=("may_mutate",),
        extracted_authority_values={"may_mutate": True},
        resulting_decision="continue",
        decision_rationale="controller allowed mutation",
    )

    report = build_report(
        report_override={
            "command_output_receipt": output.to_dict(),
            "consumption": consumption.to_dict(),
        }
    )

    assert report["ok"] is False
    assert any(
        violation["reason"] == "authority_output_tail_without_full_artifact"
        for violation in report["violations"]
    )


def test_tail_only_authority_output_rejects_string_full_artifact_claim() -> None:
    output = build_command_output_receipt(
        command_name="agent-loop",
        command=("python3", "dev/scripts/devctl.py", "agent-loop"),
        cwd=".",
        exit_code=0,
        stdout='{"may_mutate": true}',
        capture_scope="tail",
        artifact_refs=("dev/reports/full-output.txt",),
    )
    consumption = build_command_output_consumption_receipt(
        command_output_receipt_id=output.receipt_id,
        command_name="agent-loop",
        output_sha256=output.stdout_sha256,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_fields=("may_mutate",),
        extracted_authority_values={"may_mutate": True},
        resulting_decision="continue",
        decision_rationale="controller allowed mutation",
    )

    report = build_report(
        report_override={
            "command_output_receipt": output.to_dict(),
            "consumption": consumption.to_dict(),
        }
    )

    assert report["ok"] is False
    assert any(
        violation["reason"] == "authority_output_tail_without_full_artifact"
        for violation in report["violations"]
    )


def test_tail_only_authority_output_accepts_structured_full_artifact() -> None:
    output = build_command_output_receipt(
        command_name="agent-loop",
        command=("python3", "dev/scripts/devctl.py", "agent-loop"),
        cwd=".",
        exit_code=0,
        stdout='{"may_mutate": true}',
        capture_scope="tail",
    )
    full_sha = "a" * 64
    output_payload = output.to_dict()
    output_payload["full_output_artifact_ref"] = {
        "contract_id": "CommandOutputFullArtifact",
        "command_output_receipt_id": output.receipt_id,
        "path": "dev/reports/command_output/full.json",
        "sha256": full_sha,
        "byte_count": 21,
        "capture_scope": "full",
        "created_at_utc": "2026-05-17T18:30:00Z",
    }
    consumption = build_command_output_consumption_receipt(
        command_output_receipt_id=output.receipt_id,
        command_name="agent-loop",
        output_sha256=full_sha,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_fields=("may_mutate",),
        extracted_authority_values={"may_mutate": True},
        resulting_decision="continue",
        decision_rationale="controller allowed mutation",
    )

    report = build_report(
        report_override={
            "command_output_receipt": output_payload,
            "consumption": consumption.to_dict(),
        }
    )

    assert report["ok"] is True


def test_structured_full_artifact_requires_consumption_hash_match() -> None:
    output = build_command_output_receipt(
        command_name="agent-loop",
        command=("python3", "dev/scripts/devctl.py", "agent-loop"),
        cwd=".",
        exit_code=0,
        stdout='{"may_mutate": true}',
        capture_scope="tail",
    )
    output_payload = output.to_dict()
    output_payload["full_output_artifact_ref"] = {
        "contract_id": "CommandOutputFullArtifact",
        "command_output_receipt_id": output.receipt_id,
        "path": "dev/reports/command_output/full.json",
        "sha256": "b" * 64,
        "byte_count": 21,
        "capture_scope": "full",
        "created_at_utc": "2026-05-17T18:30:00Z",
    }
    consumption = build_command_output_consumption_receipt(
        command_output_receipt_id=output.receipt_id,
        command_name="agent-loop",
        output_sha256="a" * 64,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_fields=("may_mutate",),
        extracted_authority_values={"may_mutate": True},
        resulting_decision="continue",
        decision_rationale="controller allowed mutation",
    )

    report = build_report(
        report_override={
            "command_output_receipt": output_payload,
            "consumption": consumption.to_dict(),
        }
    )

    assert report["ok"] is False
    assert any(
        violation["reason"] == "consumption_output_sha_mismatch"
        for violation in report["violations"]
    )


def test_command_output_consumed_markdown_lists_counts() -> None:
    report = build_report(report_override={}, allow_empty=True)

    rendered = render_markdown(report)

    assert "# check_command_output_consumed" in rendered
    assert "command_output_receipt_count" in rendered


def test_command_output_consumed_empty_input_fails() -> None:
    report = build_report(report_override={})

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "no_authority_output_input"


def test_consumption_receipt_missing_may_mutate_field_fails() -> None:
    output = build_command_output_receipt(
        command_name="agent-loop",
        command=("python3", "dev/scripts/devctl.py", "agent-loop"),
        cwd=".",
        exit_code=0,
        stdout='{"may_mutate": false, "next_action": "run_devctl_push"}',
    )
    consumption = build_command_output_consumption_receipt(
        command_output_receipt_id=output.receipt_id,
        command_name="agent-loop",
        output_sha256=output.stdout_sha256,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_fields=("next_action",),
        extracted_authority_values={"next_action": "run_devctl_push"},
        extracted_next_actions=("do_not_push",),
        contradiction_flags=("push_projected_while_mutation_blocked",),
        resulting_decision="wait",
        decision_rationale="controller denied mutation",
    )

    report = build_report(
        report_override={
            "command_output_receipt": output.to_dict(),
            "consumption": consumption.to_dict(),
        }
    )

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "consumption_missing_authority_field"
    assert report["violations"][0]["detail"] == "may_mutate"


def test_consumption_receipt_missing_contradiction_flag_fails() -> None:
    output = build_command_output_receipt(
        command_name="agent-loop",
        command=("python3", "dev/scripts/devctl.py", "agent-loop"),
        cwd=".",
        exit_code=0,
        stdout='{"may_mutate": false, "next_action": "run_devctl_push"}',
    )
    consumption = build_command_output_consumption_receipt(
        command_output_receipt_id=output.receipt_id,
        command_name="agent-loop",
        output_sha256=output.stdout_sha256,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_fields=("may_mutate", "next_action"),
        extracted_authority_values={
            "may_mutate": False,
            "next_action": "run_devctl_push",
        },
        resulting_decision="wait",
        decision_rationale="controller denied mutation",
    )

    report = build_report(
        report_override={
            "command_output_receipt": output.to_dict(),
            "consumption": consumption.to_dict(),
        }
    )

    assert report["ok"] is False
    assert (
        report["violations"][0]["reason"]
        == "consumption_missing_contradiction_flag"
    )


def test_consumption_receipt_mismatched_authority_value_fails() -> None:
    output = build_command_output_receipt(
        command_name="agent-loop",
        command=("python3", "dev/scripts/devctl.py", "agent-loop"),
        cwd=".",
        exit_code=0,
        stdout='{"may_mutate": false, "next_action": "run_devctl_push"}',
    )
    consumption = build_command_output_consumption_receipt(
        command_output_receipt_id=output.receipt_id,
        command_name="agent-loop",
        output_sha256=output.stdout_sha256,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_fields=("may_mutate", "next_action"),
        extracted_authority_values={
            "may_mutate": True,
            "next_action": "run_devctl_push",
        },
        contradiction_flags=("push_projected_while_mutation_blocked",),
        resulting_decision="wait",
        decision_rationale="controller denied mutation",
    )

    report = build_report(
        report_override={
            "command_output_receipt": output.to_dict(),
            "consumption": consumption.to_dict(),
        }
    )

    assert report["ok"] is False
    assert any(
        violation["reason"] == "consumption_authority_value_mismatch"
        and violation["detail"] == "may_mutate"
        for violation in report["violations"]
    )


def test_agent_loop_full_output_requires_packet_attention_fields() -> None:
    output = build_command_output_receipt(
        command_name="agent-loop",
        command=("python3", "dev/scripts/devctl.py", "agent-loop"),
        cwd=".",
        exit_code=0,
        stdout=(
            '{"agent_loop_decision": {'
            '"decision": "wait", '
            '"required_action": "wait_for_scoped_packet", '
            '"reason_code": "no_scoped_active_packet", '
            '"may_mutate": false, '
            '"can_run_next_command": false, '
            '"operator_override": {"requested": true, "active": false, '
            '"state": "target_required"}, '
            '"next_action": "run_devctl_push", '
            '"next_command": "python3 dev/scripts/devctl.py push --execute", '
            '"top_blocker": "none", '
            '"pending_packet_count": 55, '
            '"active_packet_id": "", '
            '"attention_packet_id": "rev_pkt_4383"'
            '}, "packet_attention": {"body_open_required": true}}'
        ),
    )
    fields = (
        "decision",
        "required_action",
        "reason_code",
        "may_mutate",
        "can_run_next_command",
        "operator_override.requested",
        "operator_override.active",
        "operator_override.state",
        "next_action",
        "next_command",
        "top_blocker",
        "pending_packet_count",
        "active_packet_id",
        "attention_packet_id",
    )
    values = {
        "decision": "wait",
        "required_action": "wait_for_scoped_packet",
        "reason_code": "no_scoped_active_packet",
        "may_mutate": False,
        "can_run_next_command": False,
        "operator_override.requested": True,
        "operator_override.active": False,
        "operator_override.state": "target_required",
        "next_action": "run_devctl_push",
        "next_command": "python3 dev/scripts/devctl.py push --execute",
        "top_blocker": "none",
        "pending_packet_count": 55,
        "active_packet_id": "",
        "attention_packet_id": "rev_pkt_4383",
    }
    consumption = build_command_output_consumption_receipt(
        command_output_receipt_id=output.receipt_id,
        command_name="agent-loop",
        output_sha256=output.stdout_sha256,
        consumed_by_actor="codex",
        consumed_by_role="reviewer",
        consumed_at_utc="2026-05-17T18:30:00Z",
        extracted_authority_fields=fields,
        extracted_authority_values=values,
        contradiction_flags=(
            "push_projected_while_mutation_blocked",
            "next_command_projected_while_command_blocked",
            "mutation_projected_while_override_inactive",
            "wait_decision_without_blocker",
            "required_action_without_blocker",
        ),
        resulting_decision="wait",
        decision_rationale="controller denied mutation",
    )

    report = build_report(
        report_override={
            "command_output_receipt": output.to_dict(),
            "consumption": consumption.to_dict(),
        }
    )

    assert report["ok"] is False
    assert any(
        violation["reason"] == "consumption_missing_authority_field"
        and violation["detail"] == "body_open_required"
        for violation in report["violations"]
    )
