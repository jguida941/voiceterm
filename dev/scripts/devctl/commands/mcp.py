"""Read-only MCP adapter command for devctl control-plane surfaces.

This command is additive: it does not replace existing CLI workflows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..common import pipe_output, write_output
from ..config import REPO_ROOT
from .mcp_tools import TOOL_HANDLERS, TOOL_SCHEMAS, to_bool, utc_now

MCP_ALLOWLIST_PATH = REPO_ROOT / "dev/config/mcp_tools_allowlist.json"
MCP_PROTOCOL_VERSION = "2025-06-18"
MCP_SERVER_NAME = "voiceterm-devctl-mcp"
MCP_SERVER_VERSION = "1.0.0"
SUPPORTED_RESOURCE_URIS = {
    "devctl://mcp/allowlist",
    "devctl://devctl/release-contract",
}

READ_ONLY_ERROR = "tool is not read-only or not allowlisted"


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
        return {
            "ok": False,
            "error": "allowlist must define `tools` and `resources` lists",
        }

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
        return {
            "ok": False,
            "error": f"allowlist contains duplicate tool ids: {duplicates}",
        }
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


def _validate_allowlist_contract(allowlist: dict) -> list[str]:
    errors: list[str] = []
    allowlisted_tools = allowlist.get("tools", {})
    allowlisted_resources = allowlist.get("resources", {})

    for tool_id, entry in sorted(allowlisted_tools.items()):
        if tool_id not in TOOL_HANDLERS:
            errors.append(f"allowlist tool has no handler: {tool_id}")
        read_only = False
        if isinstance(entry, dict):
            read_only = to_bool(entry.get("read_only"), default=False)
        if not read_only:
            errors.append(f"allowlist tool must be read_only=true: {tool_id}")

    for uri in sorted(allowlisted_resources.keys()):
        if uri not in SUPPORTED_RESOURCE_URIS:
            errors.append(f"allowlist resource is not implemented: {uri}")

    return errors


def build_tool_descriptors(allowlist_tools: dict[str, dict]) -> list[dict]:
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


def build_resource_descriptors(allowlist_resources: dict[str, dict]) -> list[dict]:
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


def read_resource(uri: str, allowlist: dict) -> dict:
    resources = allowlist["resources"]
    if uri not in resources:
        return {"ok": False, "error": f"resource not allowlisted: {uri}"}
    if uri == "devctl://mcp/allowlist":
        return {"ok": True, "payload": allowlist}
    if uri == "devctl://devctl/release-contract":
        from .mcp_tools import tool_release_contract_snapshot

        return {"ok": True, "payload": tool_release_contract_snapshot({})["payload"]}
    return {"ok": False, "error": f"resource not implemented: {uri}"}


def call_tool(name: str, arguments: dict[str, Any], allowlist: dict) -> dict:
    tool_info = allowlist["tools"].get(name)
    if not tool_info:
        return {"ok": False, "error": f"tool not allowlisted: {name}"}
    if not to_bool(tool_info.get("read_only"), default=False):
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
        "timestamp": utc_now(),
        "ok": True,
        "protocol_version": MCP_PROTOCOL_VERSION,
        "server_name": MCP_SERVER_NAME,
        "server_version": MCP_SERVER_VERSION,
        "allowlist_path": allowlist["path"],
        "tools": build_tool_descriptors(allowlist["tools"]),
        "resources": build_resource_descriptors(allowlist["resources"]),
    }


def run(args) -> int:
    """Render MCP contract, invoke read-only tools, or serve stdio MCP transport."""
    allowlist = _load_allowlist()
    if not allowlist.get("ok", False):
        payload = {
            "command": "mcp",
            "timestamp": utc_now(),
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
            "timestamp": utc_now(),
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
            "timestamp": utc_now(),
            "ok": False,
            "error": "--tool-args-json requires --tool",
        }
        output = json.dumps(payload, indent=2)
        write_output(output, getattr(args, "output", None))
        return 2

    if getattr(args, "serve_stdio", False):
        from . import mcp_transport

        return mcp_transport.serve_stdio(allowlist)

    if getattr(args, "tool", None):
        arguments: dict[str, Any] = {}
        if raw_arguments:
            try:
                parsed = json.loads(raw_arguments)
            except json.JSONDecodeError as exc:
                payload = {
                    "command": "mcp",
                    "timestamp": utc_now(),
                    "ok": False,
                    "error": f"invalid --tool-args-json payload: {exc}",
                }
                output = json.dumps(payload, indent=2)
                write_output(output, args.output)
                return 2
            if not isinstance(parsed, dict):
                payload = {
                    "command": "mcp",
                    "timestamp": utc_now(),
                    "ok": False,
                    "error": "--tool-args-json must decode to a JSON object",
                }
                output = json.dumps(payload, indent=2)
                write_output(output, args.output)
                return 2
            arguments = parsed
        result = call_tool(str(args.tool), arguments, allowlist)
        payload = {
            "command": "mcp",
            "timestamp": utc_now(),
            "ok": bool(result["ok"]),
            "tool": str(args.tool),
            "result": result.get("payload") if result["ok"] else None,
            "error": None if result["ok"] else result["error"],
        }
        output = (
            json.dumps(payload, indent=2)
            if args.format == "json"
            else "# devctl mcp\n\n```json\n" + json.dumps(payload, indent=2) + "\n```"
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
        lines.append(
            "Run `python3 dev/scripts/devctl.py mcp --serve-stdio` for MCP stdio transport."
        )
        output = "\n".join(lines)

    write_output(output, args.output)
    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return 0
