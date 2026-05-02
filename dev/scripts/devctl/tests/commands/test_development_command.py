"""Tests for the read-only ``devctl develop`` command."""

from __future__ import annotations

import json

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands import development


def test_develop_command_is_registered_read_only() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(["develop", "--status", "--format", "json"])

    assert args.command == "develop"
    assert args.action_flag == "status"
    assert "develop" in cli.READ_ONLY_COMMANDS
    assert cli.COMMAND_HANDLERS["develop"] is development.run


def test_develop_status_renders_topology_and_scaling(capsys) -> None:
    args = cli.build_parser().parse_args(["develop", "--status", "--format", "json"])

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "develop"
    assert payload["action"] == "status"
    assert payload["controller_state"] == "read_only"
    assert payload["topology"]["topology_id"] == "develop-default"
    assert "intake_fanout" in payload["topology"]["scaling"]["mode_ids"]
    assert "WorkerPacket" in payload["topology"]["scaling"]["route_outputs"]


def test_develop_launch_is_read_only_preview(capsys) -> None:
    args = cli.build_parser().parse_args(
        ["develop", "launch", "--dry-run", "--max-cycles", "1", "--format", "json"]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "launch"
    assert payload["controller_state"] == "read_only_launch_preview"
    assert payload["inputs"]["dry_run"] is True
    assert any("no worker process is spawned" in item for item in payload["warnings"])


def test_develop_rejects_unknown_fleet() -> None:
    args = cli.build_parser().parse_args(
        ["develop", "--status", "--fleet", "experimental", "--format", "json"]
    )

    report = development.build_report(args)

    assert report.ok is False
    assert report.status == "blocked"
    assert "Only the default DevelopmentModeTopology fleet is implemented." in (
        report.blockers
    )
