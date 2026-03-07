"""Tests for devctl MCP read-only adapter command."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import check, mcp, mcp_tools, mcp_transport, ship_steps


class McpParserTests(TestCase):
    def test_cli_accepts_mcp_contract_mode_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["mcp", "--format", "json"])
        self.assertEqual(args.command, "mcp")
        self.assertFalse(args.serve_stdio)
        self.assertIsNone(args.tool)
        self.assertEqual(args.format, "json")

    def test_cli_accepts_mcp_tool_invocation_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "mcp",
                "--tool",
                "status_snapshot",
                "--tool-args-json",
                '{"include_ci": true}',
            ]
        )
        self.assertEqual(args.command, "mcp")
        self.assertEqual(args.tool, "status_snapshot")
        self.assertEqual(args.tool_args_json, '{"include_ci": true}')


class McpCommandTests(TestCase):
    def _args(self, **overrides) -> SimpleNamespace:
        payload = {
            "serve_stdio": False,
            "tool": None,
            "tool_args_json": None,
            "format": "json",
            "output": None,
            "pipe_command": None,
            "pipe_args": None,
        }
        payload.update(overrides)
        return SimpleNamespace(**payload)

    @patch("dev.scripts.devctl.commands.mcp.write_output")
    @patch("dev.scripts.devctl.commands.mcp._load_allowlist")
    def test_run_outputs_contract_json(
        self, load_allowlist_mock, write_output_mock
    ) -> None:
        load_allowlist_mock.return_value = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {
                "status_snapshot": {"id": "status_snapshot", "read_only": True},
                "release_contract_snapshot": {
                    "id": "release_contract_snapshot",
                    "read_only": True,
                },
            },
            "resources": {
                "devctl://mcp/allowlist": {"uri": "devctl://mcp/allowlist"},
            },
        }

        rc = mcp.run(self._args())

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "mcp")
        self.assertEqual(
            payload["allowlist_path"], "dev/config/mcp_tools_allowlist.json"
        )
        self.assertGreaterEqual(len(payload["tools"]), 2)

    @patch("dev.scripts.devctl.commands.mcp.write_output")
    @patch("dev.scripts.devctl.commands.mcp._load_allowlist")
    def test_run_fails_when_allowlist_has_unknown_tool(
        self, load_allowlist_mock, write_output_mock
    ) -> None:
        load_allowlist_mock.return_value = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {"unknown_tool": {"id": "unknown_tool", "read_only": True}},
            "resources": {"devctl://mcp/allowlist": {"uri": "devctl://mcp/allowlist"}},
        }

        rc = mcp.run(self._args())

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertIn("allowlist validation failed", payload["error"])
        self.assertIn("unknown_tool", payload["error"])

    @patch("dev.scripts.devctl.commands.mcp.write_output")
    @patch("dev.scripts.devctl.commands.mcp._load_allowlist")
    def test_run_fails_when_allowlist_has_non_read_only_tool(
        self,
        load_allowlist_mock,
        write_output_mock,
    ) -> None:
        load_allowlist_mock.return_value = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {"status_snapshot": {"id": "status_snapshot", "read_only": False}},
            "resources": {"devctl://mcp/allowlist": {"uri": "devctl://mcp/allowlist"}},
        }

        rc = mcp.run(self._args())

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertIn("read_only=true", payload["error"])

    @patch("dev.scripts.devctl.commands.mcp.write_output")
    @patch("dev.scripts.devctl.commands.mcp._load_allowlist")
    def test_run_tool_fails_when_tool_is_unknown(
        self, load_allowlist_mock, write_output_mock
    ) -> None:
        load_allowlist_mock.return_value = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {},
            "resources": {},
        }

        rc = mcp.run(self._args(tool="unknown_tool"))

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["tool"], "unknown_tool")
        self.assertIn("not allowlisted", payload["error"])

    @patch("dev.scripts.devctl.commands.mcp.write_output")
    @patch("dev.scripts.devctl.commands.mcp._load_allowlist")
    def test_run_tool_fails_when_tool_args_json_not_object(
        self,
        load_allowlist_mock,
        write_output_mock,
    ) -> None:
        load_allowlist_mock.return_value = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {"status_snapshot": {"id": "status_snapshot", "read_only": True}},
            "resources": {"devctl://mcp/allowlist": {"uri": "devctl://mcp/allowlist"}},
        }

        rc = mcp.run(self._args(tool="status_snapshot", tool_args_json="[1,2,3]"))

        self.assertEqual(rc, 2)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertIn("JSON object", payload["error"])

    @patch("dev.scripts.devctl.commands.mcp.write_output")
    @patch("dev.scripts.devctl.commands.mcp._load_allowlist")
    def test_run_fails_when_tool_args_json_without_tool(
        self,
        load_allowlist_mock,
        write_output_mock,
    ) -> None:
        load_allowlist_mock.return_value = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {"status_snapshot": {"id": "status_snapshot", "read_only": True}},
            "resources": {"devctl://mcp/allowlist": {"uri": "devctl://mcp/allowlist"}},
        }

        rc = mcp.run(self._args(tool_args_json="{}"))

        self.assertEqual(rc, 2)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertIn("requires --tool", payload["error"])

    def test_validate_allowlist_contract_rejects_unimplemented_resource(self) -> None:
        allowlist = {
            "tools": {"status_snapshot": {"id": "status_snapshot", "read_only": True}},
            "resources": {
                "devctl://unsupported/resource": {
                    "uri": "devctl://unsupported/resource"
                }
            },
        }
        errors = mcp._validate_allowlist_contract(allowlist)
        self.assertTrue(errors)
        self.assertIn("not implemented", errors[0])

    def test_load_allowlist_rejects_duplicate_tool_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            allowlist_path = temp_root / "dev/config/mcp_tools_allowlist.json"
            allowlist_path.parent.mkdir(parents=True, exist_ok=True)
            allowlist_path.write_text(
                json.dumps(
                    {
                        "version": "1",
                        "tools": [
                            {"id": "status_snapshot", "read_only": True},
                            {"id": "status_snapshot", "read_only": True},
                        ],
                        "resources": [],
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(mcp, "REPO_ROOT", temp_root), patch.object(
                mcp, "MCP_ALLOWLIST_PATH", allowlist_path
            ):
                result = mcp._load_allowlist()

        self.assertFalse(result["ok"])
        self.assertIn("duplicate tool ids", result["error"])

    def test_load_allowlist_rejects_duplicate_resource_uris(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            allowlist_path = temp_root / "dev/config/mcp_tools_allowlist.json"
            allowlist_path.parent.mkdir(parents=True, exist_ok=True)
            allowlist_path.write_text(
                json.dumps(
                    {
                        "version": "1",
                        "tools": [],
                        "resources": [
                            {"uri": "devctl://mcp/allowlist"},
                            {"uri": "devctl://mcp/allowlist"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(mcp, "REPO_ROOT", temp_root), patch.object(
                mcp, "MCP_ALLOWLIST_PATH", allowlist_path
            ):
                result = mcp._load_allowlist()

        self.assertFalse(result["ok"])
        self.assertIn("duplicate resource uris", result["error"])

    def test_call_tool_rejects_non_read_only_allowlist_entries(self) -> None:
        allowlist = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {"status_snapshot": {"id": "status_snapshot", "read_only": False}},
            "resources": {},
        }
        result = mcp.call_tool("status_snapshot", {}, allowlist)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], mcp.READ_ONLY_ERROR)

    def test_release_contract_snapshot_contains_required_guardrails(self) -> None:
        payload = mcp_tools.tool_release_contract_snapshot({})["payload"]
        self.assertEqual(
            payload["check_release_gate_commands"],
            check.build_release_gate_commands(),
        )
        verify_checks = payload["ship_verify_checks"]
        self.assertEqual(
            [item["name"] for item in verify_checks[:4]],
            [
                "coderabbit-gate",
                "coderabbit-ralph-gate",
                "check-release",
                "hygiene",
            ],
        )
        self.assertEqual(
            verify_checks,
            [
                {"name": name, "cmd": cmd}
                for name, cmd in ship_steps.build_verify_checks(verify_docs=True)
            ],
        )

    def test_read_resource_supports_contract_payloads(self) -> None:
        allowlist = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {
                "release_contract_snapshot": {
                    "id": "release_contract_snapshot",
                    "read_only": True,
                }
            },
            "resources": {
                "devctl://mcp/allowlist": {"uri": "devctl://mcp/allowlist"},
                "devctl://devctl/release-contract": {
                    "uri": "devctl://devctl/release-contract"
                },
            },
        }
        allowlist_resource = mcp.read_resource("devctl://mcp/allowlist", allowlist)
        self.assertTrue(allowlist_resource["ok"])
        self.assertIn("tools", allowlist_resource["payload"])

        release_resource = mcp.read_resource(
            "devctl://devctl/release-contract", allowlist
        )
        self.assertTrue(release_resource["ok"])
        self.assertIn("check_release_gate_commands", release_resource["payload"])

    @patch("dev.scripts.devctl.commands.mcp_transport.write_mcp_message")
    @patch("dev.scripts.devctl.commands.mcp_transport.read_mcp_message")
    def test_serve_stdio_returns_invalid_params_for_non_object_tool_call(
        self,
        read_message_mock,
        write_message_mock,
    ) -> None:
        allowlist = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {"status_snapshot": {"id": "status_snapshot", "read_only": True}},
            "resources": {"devctl://mcp/allowlist": {"uri": "devctl://mcp/allowlist"}},
        }
        read_message_mock.side_effect = [
            {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": "oops"},
            None,
        ]

        rc = mcp_transport.serve_stdio(allowlist)

        self.assertEqual(rc, 0)
        response = write_message_mock.call_args_list[0].args[0]
        self.assertEqual(response["error"]["code"], -32602)
        self.assertIn("invalid params", response["error"]["message"])

    @patch("dev.scripts.devctl.commands.mcp_transport.write_mcp_message")
    @patch("dev.scripts.devctl.commands.mcp_transport.read_mcp_message")
    def test_serve_stdio_returns_invalid_params_for_missing_tool_name(
        self,
        read_message_mock,
        write_message_mock,
    ) -> None:
        allowlist = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {"status_snapshot": {"id": "status_snapshot", "read_only": True}},
            "resources": {"devctl://mcp/allowlist": {"uri": "devctl://mcp/allowlist"}},
        }
        read_message_mock.side_effect = [
            {"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {}},
            None,
        ]

        rc = mcp_transport.serve_stdio(allowlist)

        self.assertEqual(rc, 0)
        response = write_message_mock.call_args_list[0].args[0]
        self.assertEqual(response["error"]["code"], -32602)
        self.assertIn("missing tool name", response["error"]["message"])

    @patch("dev.scripts.devctl.commands.mcp_transport.write_mcp_message")
    @patch("dev.scripts.devctl.commands.mcp_transport.read_mcp_message")
    def test_serve_stdio_returns_invalid_params_for_non_object_tool_arguments(
        self,
        read_message_mock,
        write_message_mock,
    ) -> None:
        allowlist = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {"status_snapshot": {"id": "status_snapshot", "read_only": True}},
            "resources": {"devctl://mcp/allowlist": {"uri": "devctl://mcp/allowlist"}},
        }
        read_message_mock.side_effect = [
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {"name": "status_snapshot", "arguments": "oops"},
            },
            None,
        ]

        rc = mcp_transport.serve_stdio(allowlist)

        self.assertEqual(rc, 0)
        response = write_message_mock.call_args_list[0].args[0]
        self.assertEqual(response["error"]["code"], -32602)
        self.assertIn("arguments", response["error"]["message"])

    @patch("dev.scripts.devctl.commands.mcp_transport.write_mcp_message")
    @patch("dev.scripts.devctl.commands.mcp_transport.read_mcp_message")
    def test_serve_stdio_returns_invalid_params_for_missing_resource_uri(
        self,
        read_message_mock,
        write_message_mock,
    ) -> None:
        allowlist = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {"status_snapshot": {"id": "status_snapshot", "read_only": True}},
            "resources": {"devctl://mcp/allowlist": {"uri": "devctl://mcp/allowlist"}},
        }
        read_message_mock.side_effect = [
            {"jsonrpc": "2.0", "id": 8, "method": "resources/read", "params": {}},
            None,
        ]

        rc = mcp_transport.serve_stdio(allowlist)

        self.assertEqual(rc, 0)
        response = write_message_mock.call_args_list[0].args[0]
        self.assertEqual(response["error"]["code"], -32602)
        self.assertIn("missing resource uri", response["error"]["message"])

    @patch("dev.scripts.devctl.commands.mcp_transport.write_mcp_message")
    @patch("dev.scripts.devctl.commands.mcp_transport.read_mcp_message")
    def test_serve_stdio_resources_read_uses_allowlist_mime_type(
        self,
        read_message_mock,
        write_message_mock,
    ) -> None:
        allowlist = {
            "ok": True,
            "path": "dev/config/mcp_tools_allowlist.json",
            "version": "1",
            "tools": {"status_snapshot": {"id": "status_snapshot", "read_only": True}},
            "resources": {
                "devctl://mcp/allowlist": {
                    "uri": "devctl://mcp/allowlist",
                    "mime_type": "application/vnd.voiceterm.contract+json",
                }
            },
        }
        read_message_mock.side_effect = [
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "resources/read",
                "params": {"uri": "devctl://mcp/allowlist"},
            },
            None,
        ]

        rc = mcp_transport.serve_stdio(allowlist)

        self.assertEqual(rc, 0)
        response = write_message_mock.call_args_list[0].args[0]
        self.assertEqual(
            response["result"]["contents"][0]["mimeType"],
            "application/vnd.voiceterm.contract+json",
        )
