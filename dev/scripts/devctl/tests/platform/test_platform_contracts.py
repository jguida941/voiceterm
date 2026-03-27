"""Tests for `devctl platform-contracts`."""

from __future__ import annotations

import json
import tempfile
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from dev.scripts.devctl.commands import platform_contracts
from dev.scripts.devctl.platform.blueprint import build_platform_blueprint


def _build_args(*, format: str) -> Namespace:
    return Namespace(
        format=format,
        output=None,
        pipe_command=None,
        pipe_args=None,
    )


def test_platform_blueprint_contract_ids_are_unique() -> None:
    blueprint = build_platform_blueprint()
    contract_ids = [contract.contract_id for contract in blueprint.shared_contracts]
    assert len(contract_ids) == len(set(contract_ids))
    assert len(blueprint.service_lifecycle) >= 1
    assert len(blueprint.caller_authority) >= 1
    assert "RepoPack" in contract_ids
    assert "TypedAction" in contract_ids
    assert "ControlState" in contract_ids
    assert "ReviewState" in contract_ids
    assert "Finding" in contract_ids
    assert "DecisionPacket" in contract_ids
    assert "FailurePacket" in contract_ids
    assert "LocalServiceEndpoint" in contract_ids
    assert "CallerAuthorityPolicy" in contract_ids
    assert len(blueprint.artifact_schemas) >= 1


def test_platform_blueprint_contract_shapes_cover_lifecycle_and_authority() -> None:
    blueprint = build_platform_blueprint()
    contract_map = {
        contract.contract_id: {field.name for field in contract.required_fields}
        for contract in blueprint.shared_contracts
    }
    assert "shutdown_entrypoints" in contract_map["LocalServiceEndpoint"]
    assert "forbidden_actions" in contract_map["CallerAuthorityPolicy"]
    assert "signals" in contract_map["Finding"]
    assert "validation_plan" in contract_map["DecisionPacket"]
    assert "rule_summary" in contract_map["DecisionPacket"]
    assert "match_evidence" in contract_map["DecisionPacket"]
    assert "rejected_rule_traces" in contract_map["DecisionPacket"]


def test_platform_contracts_json_output(capsys) -> None:
    exit_code = platform_contracts.run(_build_args(format="json"))
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "platform-contracts"
    assert payload["schema_version"] == 1
    contract_ids = [row["contract_id"] for row in payload["shared_contracts"]]
    artifact_ids = [row["contract_id"] for row in payload["artifact_schemas"]]
    contract_map = {
        row["contract_id"]: {field["name"] for field in row["required_fields"]}
        for row in payload["shared_contracts"]
    }
    assert "WorkflowAdapter" in contract_ids
    assert "Finding" in contract_ids
    assert "DecisionPacket" in contract_ids
    assert "ProbeReport" in artifact_ids
    assert "ReviewPacket" in artifact_ids
    assert payload["service_lifecycle"][0]["service_id"] == "voiceterm_daemon"
    assert "shutdown_entrypoints" in contract_map["LocalServiceEndpoint"]
    assert "forbidden_actions" in contract_map["CallerAuthorityPolicy"]
    caller_ids = [row["caller_id"] for row in payload["caller_authority"]]
    assert "human_operator" in caller_ids
    layer_ids = [row["layer_id"] for row in payload["layers"]]
    assert "governance_runtime" in layer_ids


def test_platform_contracts_markdown_output(capsys) -> None:
    exit_code = platform_contracts.run(_build_args(format="md"))
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "# devctl platform-contracts" in output
    assert "## Shared Contracts" in output
    assert "## Artifact Schema Matrix" in output
    assert "## Service Lifecycle" in output
    assert "## Caller Authority" in output
    assert "RepoPack" in output
    assert "Current Portability Status" in output


def test_platform_contracts_json_output_path_emits_receipt() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "platform.json"
        args = Namespace(
            format="json",
            output=str(output_path),
            pipe_command=None,
            pipe_args=None,
        )
        stdout = StringIO()
        with redirect_stdout(stdout):
            exit_code = platform_contracts.run(args)
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    receipt = json.loads(stdout.getvalue().strip())
    assert receipt["command"] == "platform-contracts"
    assert receipt["artifact"]["path"] == str(output_path)
    assert payload["command"] == "platform-contracts"
