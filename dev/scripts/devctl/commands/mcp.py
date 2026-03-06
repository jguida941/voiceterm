"""Read-only MCP adapter command for devctl control-plane surfaces.

This command is additive: it does not replace existing CLI workflows.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..common import pipe_output, write_output
from ..config import REPO_ROOT
from ..policy_gate import run_json_policy_gate
from ..reports_retention import PROTECTED_REPORT_PATHS
from ..status_report import build_project_report
from . import check, compat_matrix, failure_cleanup, ship_steps

MCP_ALLOWLIST_PATH = REPO_ROOT / "dev/config/mcp_tools_allowlist.json"
MCP_PROTOCOL_VERSION = "2025-06-18"
MCP_SERVER_NAME = "voiceterm-devctl-mcp"
MCP_SERVER_VERSION = "1.0.0"
SUPPORTED_RESOURCE_URIS = {
    "devctl://mcp/allowlist",
    "devctl://devctl/release-contract",
}

READ_ONLY_ERROR = "tool is not read-only or not allowlisted"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _to_int(value: Any, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            return int(text)
        except ValueError:
            return default
    return default


def _load_allowlist() -> dict:
    try:
        raw = MCP_ALLOWLIST_PATH.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except OSError as exc:
        return {"ok": False, "error": f"unable to read allowlist file: {exc}"}
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"allowlist json parse failed: {exc}"}

    tools = payload.get("tools")
    resources = payload.get("resources")
    if not isinstance(tools, list) or not isinstance(resources, list):
        return {"ok": False, "error": "allowlist must define `tools` and `resources` lists"}

    allowlisted_tools: dict[str, dict] = {}
    duplicate_tools: list[str] = []
    for item in tools:
        if not isinstance(item, dict):
            continue
        tool_id = str(item.get("id", "")).strip()
        if not tool_id:
            continue
        if tool_id in allowlisted_tools:
            duplicate_tools.append(tool_id)
            continue
        allowlisted_tools[tool_id] = item

    allowlisted_resources: dict[str, dict] = {}
    duplicate_resources: list[str] = []
    for item in resources:
        if not isinstance(item, dict):
            continue
        uri = str(item.get("uri", "")).strip()
        if not uri:
            continue
        if uri in allowlisted_resources:
            duplicate_resources.append(uri)
            continue
        allowlisted_resources[uri] = item

    if duplicate_tools:
        duplicates = ", ".join(sorted(set(duplicate_tools)))
        return {"ok": False, "error": f"allowlist contains duplicate tool ids: {duplicates}"}
    if duplicate_resources:
        duplicates = ", ".join(sorted(set(duplicate_resources)))
        return {
            "ok": False,
            "error": f"allowlist contains duplicate resource uris: {duplicates}",
        }

    return {
        "ok": True,
        "path": str(MCP_ALLOWLIST_PATH.relative_to(REPO_ROOT)),
        "version": str(payload.get("version", "unknown")),
        "tools": allowlisted_tools,
        "resources": allowlisted_resources,
    }


TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "status_snapshot": {
        "type": "object",
        "properties": {
            "include_ci": {"type": "boolean"},
            "ci_limit": {"type": "integer", "minimum": 1},
            "include_dev_logs": {"type": "boolean"},
            "dev_root": {"type": "string"},
            "dev_sessions_limit": {"type": "integer", "minimum": 1},
            "parallel": {"type": "boolean"},
        },
        "additionalProperties": False,
    },
    "report_snapshot": {
        "type": "object",
        "properties": {
            "include_ci": {"type": "boolean"},
            "ci_limit": {"type": "integer", "minimum": 1},
            "include_dev_logs": {"type": "boolean"},
            "dev_root": {"type": "string"},
            "dev_sessions_limit": {"type": "integer", "minimum": 1},
            "parallel": {"type": "boolean"},
        },
        "additionalProperties": False,
    },
    "compat_matrix_snapshot": {
        "type": "object",
        "properties": {
            "run_smoke": {"type": "boolean"},
        },
        "additionalProperties": False,
    },
    "release_contract_snapshot": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}


def _tool_status_snapshot(arguments: dict[str, Any]) -> dict[str, Any]:
    include_ci = _to_bool(arguments.get("include_ci"), default=True)
    ci_limit = max(1, _to_int(arguments.get("ci_limit"), 20))
    include_dev_logs = _to_bool(arguments.get("include_dev_logs"), default=False)
    dev_root = arguments.get("dev_root")
    dev_sessions_limit = max(1, _to_int(arguments.get("dev_sessions_limit"), 5))
    parallel = _to_bool(arguments.get("parallel"), default=True)
    payload = build_project_report(
        command="mcp.status_snapshot",
        include_ci=include_ci,
        ci_limit=ci_limit,
        include_dev_logs=include_dev_logs,
        dev_root=dev_root if isinstance(dev_root, str) else None,
        dev_sessions_limit=dev_sessions_limit,
        parallel=parallel,
    )
    return {
        "tool": "status_snapshot",
        "timestamp": _utc_now(),
        "payload": payload,
    }


def _tool_report_snapshot(arguments: dict[str, Any]) -> dict[str, Any]:
    include_ci = _to_bool(arguments.get("include_ci"), default=False)
    ci_limit = max(1, _to_int(arguments.get("ci_limit"), 20))
    include_dev_logs = _to_bool(arguments.get("include_dev_logs"), default=False)
    dev_root = arguments.get("dev_root")
    dev_sessions_limit = max(1, _to_int(arguments.get("dev_sessions_limit"), 5))
    parallel = _to_bool(arguments.get("parallel"), default=True)
    payload = build_project_report(
        command="mcp.report_snapshot",
        include_ci=include_ci,
        ci_limit=ci_limit,
        include_dev_logs=include_dev_logs,
        dev_root=dev_root if isinstance(dev_root, str) else None,
        dev_sessions_limit=dev_sessions_limit,
        parallel=parallel,
    )
    return {
        "tool": "report_snapshot",
        "timestamp": _utc_now(),
        "payload": payload,
    }


def _tool_compat_matrix_snapshot(arguments: dict[str, Any]) -> dict[str, Any]:
    run_smoke = _to_bool(arguments.get("run_smoke"), default=True)
    validation_report = run_json_policy_gate(
        compat_matrix.COMPAT_MATRIX_SCRIPT,
        "compatibility matrix validation gate",
    )
    smoke_report = None
    if run_smoke:
        smoke_report = run_json_policy_gate(
            compat_matrix.COMPAT_MATRIX_SMOKE_SCRIPT,
            "compatibility matrix smoke gate",
        )
    validation_ok = bool(validation_report.get("ok", False))
    smoke_ok = bool(smoke_report.get("ok", False)) if run_smoke else True
    return {
        "tool": "compat_matrix_snapshot",
        "timestamp": _utc_now(),
        "payload": {
            "ok": validation_ok and smoke_ok,
            "run_smoke": run_smoke,
            "validation_ok": validation_ok,
            "smoke_ok": smoke_ok,
            "validation_report": validation_report,
            "smoke_report": smoke_report,
        },
    }


def _tool_release_contract_snapshot(arguments: dict[str, Any]) -> dict[str, Any]:
    _ = arguments
    return {
        "tool": "release_contract_snapshot",
        "timestamp": _utc_now(),
        "payload": {
            "check_profile_release_flags": check.resolve_profile_settings(
                type(
                    "ReleaseArgs",
                    (),
                    {
                        "profile": "release",
                        "skip_build": False,
                        "skip_tests": False,
                        "with_perf": False,
                        "with_mem_loop": False,
                        "with_mutants": False,
                        "with_mutation_score": False,
                        "with_wake_guard": False,
                        "with_ai_guard": False,
                    },
                )()
            )[0],
            "check_release_gate_commands": check.build_release_gate_commands(),
            "ship_verify_checks": [
                {"name": name, "cmd": cmd}
                for name, cmd in ship_steps.build_verify_checks(verify_docs=True)
            ],
            "cleanup_path_contract": {
                "failure_cleanup_root": str(failure_cleanup.FAILURE_ROOT_RELATIVE),
                "failure_cleanup_override_root": str(
                    failure_cleanup.OUTSIDE_OVERRIDE_ROOT_RELATIVE
                ),
                "reports_cleanup_protected_paths": [
                    str(item) for item in PROTECTED_REPORT_PATHS
                ],
            },
        },
    }


TOOL_HANDLERS = {
    "status_snapshot": _tool_status_snapshot,
    "report_snapshot": _tool_report_snapshot,
    "compat_matrix_snapshot": _tool_compat_matrix_snapshot,
    "release_contract_snapshot": _tool_release_contract_snapshot,
}


def _validate_allowlist_contract(allowlist: dict) -> list[str]:
    errors: list[str] = []
    allowlisted_tools = allowlist.get("tools", {})
    allowlisted_resources = allowlist.get("resources", {})

    for tool_id, entry in sorted(allowlisted_tools.items()):
        if tool_id not in TOOL_HANDLERS:
            errors.append(f"allowlist tool has no handler: {tool_id}")
        read_only = False
        if isinstance(entry, dict):
            read_only = _to_bool(entry.get("read_only"), default=False)
        if not read_only:
            errors.append(f"allowlist tool must be read_only=true: {tool_id}")

    for uri in sorted(allowlisted_resources.keys()):
        if uri not in SUPPORTED_RESOURCE_URIS:
            errors.append(f"allowlist resource is not implemented: {uri}")

    return errors


def _build_tool_descriptors(allowlist_tools: dict[str, dict]) -> list[dict]:
    descriptors: list[dict] = []
    for tool_id in sorted(allowlist_tools.keys()):
        item = allowlist_tools[tool_id]
        descriptors.append(
            {
                "name": tool_id,
                "description": str(item.get("description", "")).strip(),
                "inputSchema": TOOL_SCHEMAS.get(
                    tool_id,
                    {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": True,
                    },
                ),
                "annotations": {"readOnlyHint": True},
            }
        )
    return descriptors


def _build_resource_descriptors(allowlist_resources: dict[str, dict]) -> list[dict]:
    resources: list[dict] = []
    for uri in sorted(allowlist_resources.keys()):
        item = allowlist_resources[uri]
        resources.append(
            {
                "uri": uri,
                "name": str(item.get("name", uri)).strip() or uri,
                "description": str(item.get("description", "")).strip(),
                "mimeType": str(item.get("mime_type", "application/json")).strip()
                or "application/json",
            }
        )
    return resources


def _read_resource(uri: str, allowlist: dict) -> dict:
    resources = allowlist["resources"]
    if uri not in resources:
        return {"ok": False, "error": f"resource not allowlisted: {uri}"}
    if uri == "devctl://mcp/allowlist":
        return {"ok": True, "payload": allowlist}
    if uri == "devctl://devctl/release-contract":
        return {"ok": True, "payload": _tool_release_contract_snapshot({})["payload"]}
    return {"ok": False, "error": f"resource not implemented: {uri}"}


def _call_tool(name: str, arguments: dict[str, Any], allowlist: dict) -> dict:
    tool_info = allowlist["tools"].get(name)
    if not tool_info:
        return {"ok": False, "error": f"tool not allowlisted: {name}"}
    if not _to_bool(tool_info.get("read_only"), default=False):
        return {"ok": False, "error": READ_ONLY_ERROR}
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"ok": False, "error": f"tool handler missing: {name}"}
    try:
        payload = handler(arguments)
    except Exception as exc:  # pragma: no cover - defensive error path
        return {"ok": False, "error": f"tool execution failed: {exc}"}
    return {"ok": True, "payload": payload}


def _build_contract(allowlist: dict) -> dict:
    return {
        "command": "mcp",
        "timestamp": _utc_now(),
        "ok": True,
        "protocol_version": MCP_PROTOCOL_VERSION,
        "server_name": MCP_SERVER_NAME,
        "server_version": MCP_SERVER_VERSION,
        "allowlist_path": allowlist["path"],
        "tools": _build_tool_descriptors(allowlist["tools"]),
        "resources": _build_resource_descriptors(allowlist["resources"]),
    }


def _jsonrpc_success(message_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _jsonrpc_error(message_id: Any, code: int, message: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {"code": code, "message": message},
    }


def _write_mcp_message(payload: dict) -> None:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def _read_mcp_message() -> dict | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in {b"\r\n", b"\n"}:
            break
        decoded = line.decode("ascii", errors="ignore").strip()
        if ":" not in decoded:
            continue
        name, value = decoded.split(":", 1)
        headers[name.strip().lower()] = value.strip()
    length_raw = headers.get("content-length", "")
    try:
        content_length = int(length_raw)
    except ValueError:
        return None
    body = sys.stdin.buffer.read(content_length)
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def _serve_stdio(allowlist: dict) -> int:
    while True:
        message = _read_mcp_message()
        if message is None:
            return 0
        if not isinstance(message, dict):
            continue
        method = str(message.get("method", "")).strip()
        message_id = message.get("id")

        if method == "initialize":
            response = _jsonrpc_success(
                message_id,
                {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "serverInfo": {
                        "name": MCP_SERVER_NAME,
                        "version": MCP_SERVER_VERSION,
                    },
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"listChanged": False},
                    },
                },
            )
            _write_mcp_message(response)
            continue

        if method == "notifications/initialized":
            continue

        if method == "tools/list":
            response = _jsonrpc_success(
                message_id,
                {"tools": _build_tool_descriptors(allowlist["tools"])},
            )
            _write_mcp_message(response)
            continue

        if method == "tools/call":
            params = message.get("params", {})
            if not isinstance(params, dict):
                _write_mcp_message(
                    _jsonrpc_error(message_id, -32602, "invalid params: expected object")
                )
                continue
            name = str(params.get("name", "")).strip()
            if not name:
                _write_mcp_message(
                    _jsonrpc_error(message_id, -32602, "invalid params: missing tool name")
                )
                continue
            arguments = params.get("arguments", {})
            if not isinstance(arguments, dict):
                _write_mcp_message(
                    _jsonrpc_error(
                        message_id,
                        -32602,
                        "invalid params: `arguments` must be an object",
                    )
                )
                continue
            result = _call_tool(name, arguments, allowlist)
            if result["ok"]:
                payload = result["payload"]
                response = _jsonrpc_success(
                    message_id,
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(payload, sort_keys=True),
                            }
                        ],
                        "structuredContent": payload,
                        "isError": False,
                    },
                )
            else:
                response = _jsonrpc_success(
                    message_id,
                    {
                        "content": [{"type": "text", "text": result["error"]}],
                        "isError": True,
                    },
                )
            _write_mcp_message(response)
            continue

        if method == "resources/list":
            response = _jsonrpc_success(
                message_id,
                {"resources": _build_resource_descriptors(allowlist["resources"])},
            )
            _write_mcp_message(response)
            continue

        if method == "resources/read":
            params = message.get("params", {})
            if not isinstance(params, dict):
                _write_mcp_message(
                    _jsonrpc_error(message_id, -32602, "invalid params: expected object")
                )
                continue
            uri = str(params.get("uri", "")).strip()
            if not uri:
                _write_mcp_message(
                    _jsonrpc_error(message_id, -32602, "invalid params: missing resource uri")
                )
                continue
            result = _read_resource(uri, allowlist)
            if result["ok"]:
                payload = result["payload"]
                resource_entry = allowlist["resources"].get(uri, {})
                mime_type = "application/json"
                if isinstance(resource_entry, dict):
                    mime_type = (
                        str(resource_entry.get("mime_type", "application/json")).strip()
                        or "application/json"
                    )
                response = _jsonrpc_success(
                    message_id,
                    {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": mime_type,
                                "text": json.dumps(payload, sort_keys=True),
                            }
                        ]
                    },
                )
            else:
                response = _jsonrpc_error(message_id, -32000, result["error"])
            _write_mcp_message(response)
            continue

        if message_id is None:
            continue
        _write_mcp_message(_jsonrpc_error(message_id, -32601, f"method not found: {method}"))


def run(args) -> int:
    """Render MCP contract, invoke read-only tools, or serve stdio MCP transport."""
    allowlist = _load_allowlist()
    if not allowlist.get("ok", False):
        payload = {
            "command": "mcp",
            "timestamp": _utc_now(),
            "ok": False,
            "error": allowlist.get("error", "allowlist unavailable"),
        }
        output = json.dumps(payload, indent=2)
        write_output(output, getattr(args, "output", None))
        return 1
    allowlist_errors = _validate_allowlist_contract(allowlist)
    if allowlist_errors:
        payload = {
            "command": "mcp",
            "timestamp": _utc_now(),
            "ok": False,
            "error": "allowlist validation failed: " + "; ".join(allowlist_errors),
        }
        output = json.dumps(payload, indent=2)
        write_output(output, getattr(args, "output", None))
        return 1

    raw_arguments = getattr(args, "tool_args_json", None)
    if raw_arguments and not getattr(args, "tool", None):
        payload = {
            "command": "mcp",
            "timestamp": _utc_now(),
            "ok": False,
            "error": "--tool-args-json requires --tool",
        }
        output = json.dumps(payload, indent=2)
        write_output(output, getattr(args, "output", None))
        return 2

    if getattr(args, "serve_stdio", False):
        return _serve_stdio(allowlist)

    if getattr(args, "tool", None):
        arguments: dict[str, Any] = {}
        if raw_arguments:
            try:
                parsed = json.loads(raw_arguments)
            except json.JSONDecodeError as exc:
                payload = {
                    "command": "mcp",
                    "timestamp": _utc_now(),
                    "ok": False,
                    "error": f"invalid --tool-args-json payload: {exc}",
                }
                output = json.dumps(payload, indent=2)
                write_output(output, args.output)
                return 2
            if not isinstance(parsed, dict):
                payload = {
                    "command": "mcp",
                    "timestamp": _utc_now(),
                    "ok": False,
                    "error": "--tool-args-json must decode to a JSON object",
                }
                output = json.dumps(payload, indent=2)
                write_output(output, args.output)
                return 2
            arguments = parsed
        result = _call_tool(str(args.tool), arguments, allowlist)
        payload = {
            "command": "mcp",
            "timestamp": _utc_now(),
            "ok": bool(result["ok"]),
            "tool": str(args.tool),
            "result": result.get("payload") if result["ok"] else None,
            "error": None if result["ok"] else result["error"],
        }
        output = (
            json.dumps(payload, indent=2)
            if args.format == "json"
            else "# devctl mcp\n\n```json\n"
            + json.dumps(payload, indent=2)
            + "\n```"
        )
        write_output(output, args.output)
        if args.pipe_command:
            pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
            if pipe_code != 0:
                return pipe_code
        return 0 if result["ok"] else 1

    contract = _build_contract(allowlist)
    if args.format == "json":
        output = json.dumps(contract, indent=2)
    else:
        lines = [
            "# devctl mcp",
            "",
            f"- protocol_version: {contract['protocol_version']}",
            f"- server: {contract['server_name']}@{contract['server_version']}",
            f"- allowlist: {contract['allowlist_path']}",
            "",
            "## Tools (read-only)",
        ]
        for tool in contract["tools"]:
            lines.append(f"- {tool['name']}: {tool['description']}")
        lines.append("")
        lines.append("## Resources")
        for resource in contract["resources"]:
            lines.append(f"- {resource['uri']}: {resource['description']}")
        lines.append("")
        lines.append("Run `python3 dev/scripts/devctl.py mcp --serve-stdio` for MCP stdio transport.")
        output = "\n".join(lines)

    write_output(output, args.output)
    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return 0
