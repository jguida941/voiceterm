"""Claude Code JSONL normalization for the shared rollout event contract."""

from __future__ import annotations

from typing import Any

from ...runtime.rollout_event import RolloutEvent
from .constants import PROVIDER_CLAUDE
from .message_text import extract_message_text

_SUMMARY_LIMIT = 160


def classify_claude_event(raw: dict[str, Any], *, session_id: str) -> RolloutEvent:
    """Normalize one Claude Code JSONL row into provider-neutral event kinds."""
    event_type = _text(raw.get("type")) or "unknown"
    normalized_event_type, payload, summary, content_error = _normalize_claude_row(
        raw,
        event_type=event_type,
    )
    return RolloutEvent(
        timestamp=_text(raw.get("timestamp")),
        provider=PROVIDER_CLAUDE,
        session_id=session_id,
        event_type=normalized_event_type,
        raw_payload=_raw_with_payload(raw, payload),
        is_escalation_request=False,
        is_error=event_type == "error" or bool(raw.get("isError")) or content_error,
        summary=summary,
    )


def _normalize_claude_row(
    raw: dict[str, Any],
    *,
    event_type: str,
) -> tuple[str, dict[str, Any], str, bool]:
    if event_type == "assistant":
        return _normalize_assistant(raw)
    if event_type == "user":
        return _normalize_user(raw)
    if event_type == "system":
        subtype = _text(raw.get("subtype")) or _text(raw.get("name"))
        summary = f"system[{subtype}]" if subtype else "system"
        return event_type, {}, summary, False
    return event_type, {}, _first_nonempty(raw), False


def _normalize_assistant(raw: dict[str, Any]) -> tuple[str, dict[str, Any], str, bool]:
    message = _message_dict(raw)
    content = _content_items(message)
    tool_use = _first_item(content, "tool_use")
    if tool_use:
        payload = _tool_use_payload(tool_use)
        name = _text(payload.get("name")) or "?"
        command = _tool_command(payload)
        summary = (
            f"tool_call[{name}]: {command[:140]}"
            if command
            else f"tool_call[{name}]"
        )
        return "response_item:function_call", payload, summary, False

    thinking = _first_item(content, "thinking")
    if thinking:
        text = _text(thinking.get("thinking")) or _text(thinking.get("text"))
        payload = {"type": "reasoning"}
        if text:
            payload["summary"] = [{"type": "text", "text": text}]
            payload["content"] = text
            return "response_item:reasoning", payload, _truncate(text), False
        if thinking.get("signature"):
            payload["encrypted_content"] = _text(thinking.get("signature"))
        return "response_item:reasoning", payload, "reasoning (encrypted)", False

    text = _content_text(content) or extract_message_text(message)
    payload = {
        "type": "message",
        "role": "assistant",
        "content": [{"type": "output_text", "text": text}],
    }
    summary = f"assistant: {_truncate(text)}" if text else "assistant"
    return "response_item:message", payload, summary, False


def _normalize_user(raw: dict[str, Any]) -> tuple[str, dict[str, Any], str, bool]:
    message = _message_dict(raw)
    content = _content_items(message)
    tool_result = _first_item(content, "tool_result")
    if tool_result:
        result_text = _text(tool_result.get("content")) or _tool_result_stdout(raw)
        message_text = (
            f"tool_result: {_truncate(result_text)}"
            if result_text
            else "tool_result"
        )
        payload = {"type": "agent_message", "message": message_text}
        return (
            "event_msg:agent_message",
            payload,
            message_text,
            bool(tool_result.get("is_error")) or _tool_result_interrupted(raw),
        )

    text = extract_message_text(message)
    payload = {
        "type": "message",
        "role": "user",
        "content": [{"type": "output_text", "text": text}],
    }
    summary = f"user: {_truncate(text)}" if text else "user"
    return "response_item:message", payload, summary, False


def _tool_use_payload(tool_use: dict[str, Any]) -> dict[str, Any]:
    input_obj = tool_use.get("input")
    arguments = input_obj if isinstance(input_obj, dict) else {}
    return {
        "type": "function_call",
        "name": _text(tool_use.get("name")),
        "arguments": arguments,
        "call_id": _text(tool_use.get("id")),
    }


def _tool_command(payload: dict[str, Any]) -> str:
    arguments = payload.get("arguments")
    if not isinstance(arguments, dict):
        return ""
    return _text(arguments.get("cmd")) or _text(arguments.get("command"))


def _message_dict(raw: dict[str, Any]) -> dict[str, Any]:
    message = raw.get("message")
    return message if isinstance(message, dict) else {}


def _content_items(message: dict[str, Any]) -> list[dict[str, Any]]:
    content = message.get("content")
    if isinstance(content, list):
        return [item for item in content if isinstance(item, dict)]
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return []


def _first_item(items: list[dict[str, Any]], item_type: str) -> dict[str, Any]:
    for item in items:
        if _text(item.get("type")) == item_type:
            return item
    return {}


def _content_text(items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in items:
        if _text(item.get("type")) not in {"text", "output_text"}:
            continue
        text = _text(item.get("text")) or _text(item.get("content"))
        if text:
            parts.append(text)
    return " ".join(parts)


def _tool_result_stdout(raw: dict[str, Any]) -> str:
    result = raw.get("toolUseResult")
    if not isinstance(result, dict):
        return ""
    return _text(result.get("stdout")) or _text(result.get("stderr"))


def _tool_result_interrupted(raw: dict[str, Any]) -> bool:
    result = raw.get("toolUseResult")
    return isinstance(result, dict) and bool(result.get("interrupted"))


def _raw_with_payload(raw: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if not payload:
        return raw
    return {**raw, "payload": payload}


def _first_nonempty(raw: dict[str, Any]) -> str:
    for key in ("summary", "message", "text"):
        value = raw.get(key)
        if isinstance(value, str) and value:
            return value[:_SUMMARY_LIMIT]
    return _text(raw.get("type")) or "unknown"


def _truncate(text: str) -> str:
    squashed = " ".join(text.split())
    if len(squashed) <= _SUMMARY_LIMIT:
        return squashed
    return squashed[: _SUMMARY_LIMIT - 1] + "\u2026"


def _text(value: Any) -> str:
    return str(value or "").strip()


__all__ = ["classify_claude_event"]
