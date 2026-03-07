"""MCP JSON-RPC stdio transport layer.

Handles Content-Length message framing and method dispatch for the MCP
stdio server mode.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from . import mcp as mcp_mod
from .mcp_tools import TOOL_SCHEMAS


def jsonrpc_success(message_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def jsonrpc_error(message_id: Any, code: int, message: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {"code": code, "message": message},
    }


def write_mcp_message(payload: dict) -> None:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def read_mcp_message() -> dict | None:
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


def serve_stdio(allowlist: dict) -> int:
    while True:
        message = read_mcp_message()
        if message is None:
            return 0
        if not isinstance(message, dict):
            continue
        method = str(message.get("method", "")).strip()
        message_id = message.get("id")

        if method == "initialize":
            response = jsonrpc_success(
                message_id,
                {
                    "protocolVersion": mcp_mod.MCP_PROTOCOL_VERSION,
                    "serverInfo": {
                        "name": mcp_mod.MCP_SERVER_NAME,
                        "version": mcp_mod.MCP_SERVER_VERSION,
                    },
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"listChanged": False},
                    },
                },
            )
            write_mcp_message(response)
            continue

        if method == "notifications/initialized":
            continue

        if method == "tools/list":
            response = jsonrpc_success(
                message_id,
                {"tools": mcp_mod.build_tool_descriptors(allowlist["tools"])},
            )
            write_mcp_message(response)
            continue

        if method == "tools/call":
            params = message.get("params", {})
            if not isinstance(params, dict):
                write_mcp_message(
                    jsonrpc_error(message_id, -32602, "invalid params: expected object")
                )
                continue
            name = str(params.get("name", "")).strip()
            if not name:
                write_mcp_message(
                    jsonrpc_error(
                        message_id, -32602, "invalid params: missing tool name"
                    )
                )
                continue
            arguments = params.get("arguments", {})
            if not isinstance(arguments, dict):
                write_mcp_message(
                    jsonrpc_error(
                        message_id,
                        -32602,
                        "invalid params: `arguments` must be an object",
                    )
                )
                continue
            result = mcp_mod.call_tool(name, arguments, allowlist)
            if result["ok"]:
                payload = result["payload"]
                response = jsonrpc_success(
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
                response = jsonrpc_success(
                    message_id,
                    {
                        "content": [{"type": "text", "text": result["error"]}],
                        "isError": True,
                    },
                )
            write_mcp_message(response)
            continue

        if method == "resources/list":
            response = jsonrpc_success(
                message_id,
                {
                    "resources": mcp_mod.build_resource_descriptors(
                        allowlist["resources"]
                    )
                },
            )
            write_mcp_message(response)
            continue

        if method == "resources/read":
            params = message.get("params", {})
            if not isinstance(params, dict):
                write_mcp_message(
                    jsonrpc_error(message_id, -32602, "invalid params: expected object")
                )
                continue
            uri = str(params.get("uri", "")).strip()
            if not uri:
                write_mcp_message(
                    jsonrpc_error(
                        message_id, -32602, "invalid params: missing resource uri"
                    )
                )
                continue
            result = mcp_mod.read_resource(uri, allowlist)
            if result["ok"]:
                payload = result["payload"]
                resource_entry = allowlist["resources"].get(uri, {})
                mime_type = "application/json"
                if isinstance(resource_entry, dict):
                    mime_type = (
                        str(resource_entry.get("mime_type", "application/json")).strip()
                        or "application/json"
                    )
                response = jsonrpc_success(
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
                response = jsonrpc_error(message_id, -32000, result["error"])
            write_mcp_message(response)
            continue

        if message_id is None:
            continue
        write_mcp_message(
            jsonrpc_error(message_id, -32601, f"method not found: {method}")
        )
