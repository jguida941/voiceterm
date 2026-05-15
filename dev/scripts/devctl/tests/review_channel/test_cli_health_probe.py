from __future__ import annotations

import pytest

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.review_channel.cli_health_probe import (
    build_cli_health_probe_report,
)
from dev.scripts.devctl.commands.review_channel_command import (
    ReviewChannelAction,
    _validate_args,
)


def _healthy_status_report() -> dict[str, object]:
    return {
        "action": "status",
        "ok": True,
        "errors": [],
        "snapshot_id": "snap-demo",
        "zref": "zref_demo",
        "doctor": {"status": "healthy", "decision_action_id": "continue_scoped_loop"},
        "recovery_assessment": {
            "diagnosis": {"status": "healthy"},
            "decision": {"action_id": "continue_scoped_loop", "command": ""},
        },
        "runtime_readiness": {"status": "ready", "system_ok": True},
        "authority_snapshot": {"required_action": "continue_scoped_loop"},
    }


def test_parser_accepts_status_recovery_probe_modes() -> None:
    args = build_parser().parse_args(
        [
            "review-channel",
            "--action",
            "status",
            "--recovery-probe",
            "--recovery-probe-mode",
            "on_error",
            "--terminal",
            "none",
            "--format",
            "json",
        ]
    )

    assert args.recovery_probe is True
    assert args.recovery_probe_mode == "on_error"


def test_recovery_probe_is_status_only() -> None:
    args = build_parser().parse_args(
        [
            "review-channel",
            "--action",
            "doctor",
            "--recovery-probe",
            "--format",
            "json",
        ]
    )

    with pytest.raises(ValueError, match="--recovery-probe is only valid"):
        _validate_args(args, ReviewChannelAction.DOCTOR)


def test_scheduled_probe_reports_healthy_status() -> None:
    report = build_cli_health_probe_report(
        status_report=_healthy_status_report(),
        exit_code=0,
        mode="scheduled",
    )

    assert report["contract_id"] == "CLIHealthProbeAutomation"
    assert report["toggle_id"] == "CLIHealthProbeAutomation"
    assert report["active"] is True
    assert report["status"] == "healthy"
    assert report["requires_recovery"] is False
    assert report["snapshot_id"] == "snap-demo"


def test_on_error_probe_stays_inactive_for_healthy_status() -> None:
    report = build_cli_health_probe_report(
        status_report=_healthy_status_report(),
        exit_code=0,
        mode="on_error",
    )

    assert report["active"] is False
    assert report["status"] == "not_triggered"
    assert report["requires_recovery"] is False


def test_on_error_probe_surfaces_recovery_condition() -> None:
    status_report = _healthy_status_report()
    status_report.update(
        {
            "doctor": {
                "status": "runtime_missing",
                "recommended_command": (
                    "python3 dev/scripts/devctl.py review-channel --action ensure "
                    "--terminal none --format json"
                ),
            },
            "recommended_command": (
                "python3 dev/scripts/devctl.py review-channel --action ensure "
                "--terminal none --format json"
            ),
            "recommended_command_source": "doctor",
            "recovery_assessment": {
                "diagnosis": {"status": "runtime_missing"},
                "decision": {
                    "action_id": "ensure_runtime",
                    "command": (
                        "python3 dev/scripts/devctl.py review-channel --action ensure "
                        "--terminal none --format json"
                    ),
                },
            },
        }
    )

    report = build_cli_health_probe_report(
        status_report=status_report,
        exit_code=0,
        mode="on_error",
    )

    assert report["active"] is True
    assert report["status"] == "attention"
    assert report["requires_recovery"] is True
    assert report["recommended_command_source"] == "doctor"
    assert report["recovery_action_id"] == "ensure_runtime"
    assert any(
        entry["value"] == "doctor_status:runtime_missing"
        for entry in report["evidence"]
    )


def test_disabled_probe_records_disabled_toggle() -> None:
    report = build_cli_health_probe_report(
        status_report=_healthy_status_report(),
        exit_code=0,
        mode="disabled",
    )

    assert report["active"] is False
    assert report["status"] == "disabled"
    assert report["ok"] is True
