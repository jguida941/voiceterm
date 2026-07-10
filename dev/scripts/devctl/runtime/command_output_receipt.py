"""Typed command-output proof receipts."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from .value_coercion import (
    coerce_int,
    coerce_string,
    coerce_string_items,
)

COMMAND_OUTPUT_RECEIPT_CONTRACT_ID = "CommandOutputReceipt"
COMMAND_OUTPUT_RECEIPT_SCHEMA_VERSION = 1
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
OUTPUT_EXCERPT_MAX_CHARS = 2000


@dataclass(frozen=True, slots=True)
class CommandOutputReceipt:
    """Bounded proof that command output was captured and checked."""

    receipt_id: str
    command_name: str
    argv: tuple[str, ...]
    cwd: str
    exit_code: int
    stdout_sha256: str
    stdout_byte_count: int
    stderr_sha256: str = EMPTY_SHA256
    stderr_byte_count: int = 0
    capture_scope: str = "full"
    output_excerpt: str = ""
    expected_patterns: tuple[str, ...] = ()
    matched_patterns: tuple[str, ...] = ()
    missing_patterns: tuple[str, ...] = ()
    forbidden_patterns: tuple[str, ...] = ()
    matched_forbidden_patterns: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    stream_mode: str = "stderr_to_stdout"
    captured_at_utc: str = ""
    schema_version: int = COMMAND_OUTPUT_RECEIPT_SCHEMA_VERSION
    contract_id: str = COMMAND_OUTPUT_RECEIPT_CONTRACT_ID

    @property
    def output_assertions_satisfied(self) -> bool:
        return (
            self.exit_code == 0
            and not self.missing_patterns
            and not self.matched_forbidden_patterns
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["argv"] = list(self.argv)
        payload["command"] = list(self.argv)
        payload["expected_patterns"] = list(self.expected_patterns)
        payload["matched_patterns"] = list(self.matched_patterns)
        payload["missing_patterns"] = list(self.missing_patterns)
        payload["forbidden_patterns"] = list(self.forbidden_patterns)
        payload["matched_forbidden_patterns"] = list(self.matched_forbidden_patterns)
        payload["artifact_refs"] = list(self.artifact_refs)
        payload["output_assertions_satisfied"] = self.output_assertions_satisfied
        return payload


def build_command_output_receipt(
    *,
    command_name: str,
    command: Sequence[str],
    cwd: str,
    exit_code: int,
    stdout: str,
    stderr: str = "",
    expected_patterns: Sequence[str] = (),
    forbidden_patterns: Sequence[str] = (),
    artifact_refs: Sequence[str] = (),
    captured_at_utc: str = "",
    stream_mode: str = "stderr_to_stdout",
    capture_scope: str = "full",
) -> CommandOutputReceipt:
    """Build a compact receipt over captured command output."""

    stdout_bytes = stdout.encode("utf-8")
    stderr_bytes = stderr.encode("utf-8")
    expected = _unique_strings(expected_patterns)
    forbidden = _unique_strings(forbidden_patterns)
    combined = "\n".join(value for value in (stdout, stderr) if value)
    matched = tuple(pattern for pattern in expected if pattern in combined)
    missing = tuple(pattern for pattern in expected if pattern not in combined)
    matched_forbidden = tuple(pattern for pattern in forbidden if pattern in combined)
    fingerprint_source = "\x00".join(
        (
            command_name,
            " ".join(str(item) for item in command),
            str(exit_code),
            hashlib.sha256(stdout_bytes).hexdigest(),
            hashlib.sha256(stderr_bytes).hexdigest(),
            "\x1f".join(expected),
            "\x1f".join(forbidden),
            coerce_string(capture_scope) or "full",
            stream_mode,
        )
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
    return CommandOutputReceipt(
        receipt_id=f"command_output:{command_name}:{fingerprint}",
        command_name=command_name,
        argv=tuple(str(item) for item in command),
        cwd=cwd,
        exit_code=int(exit_code),
        stdout_sha256=hashlib.sha256(stdout_bytes).hexdigest(),
        stdout_byte_count=len(stdout_bytes),
        stderr_sha256=hashlib.sha256(stderr_bytes).hexdigest(),
        stderr_byte_count=len(stderr_bytes),
        capture_scope=coerce_string(capture_scope) or "full",
        output_excerpt=_excerpt(combined),
        expected_patterns=expected,
        matched_patterns=matched,
        missing_patterns=missing,
        forbidden_patterns=forbidden,
        matched_forbidden_patterns=matched_forbidden,
        artifact_refs=_unique_strings(artifact_refs),
        stream_mode=stream_mode,
        captured_at_utc=captured_at_utc,
    )


def command_output_receipt_from_mapping(
    payload: Mapping[str, object],
) -> CommandOutputReceipt:
    return CommandOutputReceipt(
        receipt_id=coerce_string(payload.get("receipt_id")),
        command_name=coerce_string(payload.get("command_name")),
        argv=coerce_string_items(payload.get("argv") or payload.get("command")),
        cwd=coerce_string(payload.get("cwd")),
        exit_code=coerce_int(payload.get("exit_code")),
        stdout_sha256=coerce_string(payload.get("stdout_sha256")) or EMPTY_SHA256,
        stdout_byte_count=coerce_int(payload.get("stdout_byte_count")),
        stderr_sha256=coerce_string(payload.get("stderr_sha256")) or EMPTY_SHA256,
        stderr_byte_count=coerce_int(payload.get("stderr_byte_count")),
        capture_scope=coerce_string(payload.get("capture_scope")) or "full",
        output_excerpt=coerce_string(payload.get("output_excerpt")),
        expected_patterns=coerce_string_items(payload.get("expected_patterns")),
        matched_patterns=coerce_string_items(payload.get("matched_patterns")),
        missing_patterns=coerce_string_items(payload.get("missing_patterns")),
        forbidden_patterns=coerce_string_items(payload.get("forbidden_patterns")),
        matched_forbidden_patterns=coerce_string_items(
            payload.get("matched_forbidden_patterns")
        ),
        artifact_refs=coerce_string_items(payload.get("artifact_refs")),
        stream_mode=coerce_string(payload.get("stream_mode")) or "stderr_to_stdout",
        captured_at_utc=coerce_string(payload.get("captured_at_utc")),
        schema_version=(
            coerce_int(payload.get("schema_version"))
            or COMMAND_OUTPUT_RECEIPT_SCHEMA_VERSION
        ),
        contract_id=(
            coerce_string(payload.get("contract_id"))
            or COMMAND_OUTPUT_RECEIPT_CONTRACT_ID
        ),
    )


def _unique_strings(values: Sequence[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text.strip() or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)


def _excerpt(value: str) -> str:
    text = value.strip()
    if len(text) <= OUTPUT_EXCERPT_MAX_CHARS:
        return text
    return text[-OUTPUT_EXCERPT_MAX_CHARS:]


__all__ = [
    "COMMAND_OUTPUT_RECEIPT_CONTRACT_ID",
    "COMMAND_OUTPUT_RECEIPT_SCHEMA_VERSION",
    "CommandOutputReceipt",
    "build_command_output_receipt",
    "command_output_receipt_from_mapping",
]
