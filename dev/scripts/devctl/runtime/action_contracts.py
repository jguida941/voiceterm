"""Shared runtime action/run/adapter contract models."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field

from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)


@dataclass(frozen=True, slots=True)
class TypedAction:
    schema_version: int
    contract_id: str
    action_id: str
    repo_pack_id: str
    parameters: dict[str, object]
    requested_by: str = ""
    dry_run: bool = False
    correlation_id: str = ""
    causation_id: str = ""
    run_id: str = ""


RUN_RECORD_CONTRACT_ID = "RunRecord"
RUN_RECORD_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class RunRecord:
    schema_version: int
    contract_id: str
    run_id: str
    action_id: str
    artifact_paths: tuple[str, ...]
    tree_content_hash: str = ""
    status: str = "unknown"
    findings_count: int = 0
    started_at: str = ""
    finished_at: str = ""
    correlation_id: str = ""
    causation_id: str = ""


@dataclass(frozen=True, slots=True)
class ArtifactStore:
    schema_version: int
    contract_id: str
    root: str
    retention_policy: dict[str, object]
    managed_kinds: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProviderAdapter:
    schema_version: int
    contract_id: str
    provider_id: str
    capabilities: tuple[str, ...]
    launch_mode: str
    available: bool = True


@dataclass(frozen=True, slots=True)
class WorkflowAdapter:
    schema_version: int
    contract_id: str
    adapter_id: str
    transport: str
    allowed_actions: tuple[str, ...]
    available: bool = True


ACTION_RESULT_CONTRACT_ID = "ActionResult"
ACTION_RESULT_SCHEMA_VERSION = 1


class ActionOutcome:
    """Explicit outcome states for deterministic guard/startup routing.

    Guards and startup surfaces use these instead of overloading pass/fail
    so they can escalate honestly when the answer is not yet known.
    """

    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    DEFER = "defer"

    ALL = frozenset({PASS, FAIL, UNKNOWN, DEFER})


@dataclass(frozen=True, slots=True)
class ActionResultFields:
    """Inputs for building the canonical ActionResult envelope."""

    action_id: str
    ok: bool
    status: str
    reason: str
    retryable: bool = False
    partial_progress: bool = False
    operator_guidance: str = ""
    warnings: Sequence[str] = field(default_factory=tuple)
    errors: Sequence[dict[str, object]] = field(default_factory=tuple)
    reason_chain: Sequence[str] = field(default_factory=tuple)
    remediation: str = ""
    auto_executable: bool = False
    findings_count: int = 0
    artifact_paths: Sequence[str] = field(default_factory=tuple)
    correlation_id: str = ""
    causation_id: str = ""
    run_id: str = ""


@dataclass(frozen=True, slots=True)
class ActionResult:
    """Canonical result envelope for any command, service call, or agent action.

    Every devctl command, guard, and automation loop should return one of
    these so CLI, UI, AI agents, and automation consumers all parse the
    same outcome shape.

    ``status`` must be one of ``ActionOutcome.ALL``: pass, fail, unknown,
    or defer.  ``unknown`` means the check could not run or the evidence
    is insufficient.  ``defer`` means the check intentionally skipped
    evaluation and a later stage should decide.
    """

    schema_version: int
    contract_id: str
    action_id: str
    ok: bool
    status: str = ActionOutcome.UNKNOWN
    reason: str = ""
    retryable: bool = False
    partial_progress: bool = False
    operator_guidance: str = ""
    warnings: tuple[str, ...] = ()
    errors: tuple[dict[str, object], ...] = ()
    reason_chain: tuple[str, ...] = ()
    remediation: str = ""
    auto_executable: bool = False
    findings_count: int = 0
    artifact_paths: tuple[str, ...] = ()
    correlation_id: str = ""
    causation_id: str = ""
    run_id: str = ""

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        d["warnings"] = list(self.warnings)
        d["errors"] = [dict(item) for item in self.errors]
        d["reason_chain"] = list(self.reason_chain)
        d["artifact_paths"] = list(self.artifact_paths)
        return d


def build_action_result(fields: ActionResultFields) -> ActionResult:
    warnings = tuple(fields.warnings)
    errors = tuple(dict(item) for item in fields.errors)
    reason_chain = tuple(fields.reason_chain)
    artifact_paths = tuple(fields.artifact_paths)
    return ActionResult(
        schema_version=ACTION_RESULT_SCHEMA_VERSION,
        contract_id=ACTION_RESULT_CONTRACT_ID,
        action_id=fields.action_id,
        ok=fields.ok,
        status=fields.status,
        reason=fields.reason,
        retryable=fields.retryable,
        partial_progress=fields.partial_progress,
        operator_guidance=fields.operator_guidance,
        warnings=warnings,
        errors=errors,
        reason_chain=reason_chain,
        remediation=fields.remediation,
        auto_executable=fields.auto_executable,
        findings_count=fields.findings_count,
        artifact_paths=artifact_paths,
        correlation_id=fields.correlation_id,
        causation_id=fields.causation_id,
        run_id=fields.run_id,
    )


def action_result_from_mapping(payload: Mapping[str, object]) -> ActionResult:
    version = coerce_int(payload.get("schema_version")) or ACTION_RESULT_SCHEMA_VERSION
    contract = coerce_string(payload.get("contract_id")) or ACTION_RESULT_CONTRACT_ID
    return ActionResult(
        schema_version=version,
        contract_id=contract,
        action_id=coerce_string(payload.get("action_id")),
        ok=coerce_bool(payload.get("ok")),
        status=coerce_string(payload.get("status")) or "unknown",
        reason=coerce_string(payload.get("reason")),
        retryable=coerce_bool(payload.get("retryable")),
        partial_progress=coerce_bool(payload.get("partial_progress")),
        operator_guidance=coerce_string(payload.get("operator_guidance")),
        warnings=coerce_string_items(payload.get("warnings")),
        errors=_coerce_error_items(payload.get("errors")),
        reason_chain=coerce_string_items(payload.get("reason_chain")),
        remediation=coerce_string(payload.get("remediation")),
        auto_executable=coerce_bool(payload.get("auto_executable")),
        findings_count=coerce_int(payload.get("findings_count")),
        artifact_paths=coerce_string_items(payload.get("artifact_paths")),
        correlation_id=coerce_string(payload.get("correlation_id")),
        causation_id=coerce_string(payload.get("causation_id")),
        run_id=coerce_string(payload.get("run_id")),
    )


def _coerce_error_items(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    errors: list[dict[str, object]] = []
    for item in value:
        mapping = dict(coerce_mapping(item))
        if mapping:
            errors.append(mapping)
    return tuple(errors)


def typed_action_from_mapping(payload: Mapping[str, object]) -> TypedAction:
    parameters = dict(coerce_mapping(payload.get("parameters")))
    return TypedAction(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=coerce_string(payload.get("contract_id")) or "TypedAction",
        action_id=coerce_string(payload.get("action_id")),
        repo_pack_id=coerce_string(payload.get("repo_pack_id")),
        parameters=parameters,
        requested_by=coerce_string(payload.get("requested_by")),
        dry_run=coerce_bool(payload.get("dry_run")),
        correlation_id=coerce_string(payload.get("correlation_id")),
        causation_id=coerce_string(payload.get("causation_id")),
        run_id=coerce_string(payload.get("run_id")),
    )


def run_record_from_mapping(payload: Mapping[str, object]) -> RunRecord:
    return RunRecord(
        schema_version=coerce_int(payload.get("schema_version"))
        or RUN_RECORD_SCHEMA_VERSION,
        contract_id=coerce_string(payload.get("contract_id"))
        or RUN_RECORD_CONTRACT_ID,
        run_id=coerce_string(payload.get("run_id")),
        action_id=coerce_string(payload.get("action_id")),
        artifact_paths=coerce_string_items(payload.get("artifact_paths")),
        tree_content_hash=coerce_string(payload.get("tree_content_hash")),
        status=coerce_string(payload.get("status")) or "unknown",
        findings_count=coerce_int(payload.get("findings_count")),
        started_at=coerce_string(payload.get("started_at")),
        finished_at=coerce_string(payload.get("finished_at")),
        correlation_id=coerce_string(payload.get("correlation_id")),
        causation_id=coerce_string(payload.get("causation_id")),
    )


def provider_adapter_from_mapping(payload: Mapping[str, object]) -> ProviderAdapter:
    return ProviderAdapter(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=coerce_string(payload.get("contract_id")) or "ProviderAdapter",
        provider_id=coerce_string(payload.get("provider_id")),
        capabilities=coerce_string_items(payload.get("capabilities")),
        launch_mode=coerce_string(payload.get("launch_mode")),
        available=coerce_bool(payload.get("available", True)),
    )


def workflow_adapter_from_mapping(payload: Mapping[str, object]) -> WorkflowAdapter:
    return WorkflowAdapter(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=coerce_string(payload.get("contract_id")) or "WorkflowAdapter",
        adapter_id=coerce_string(payload.get("adapter_id")),
        transport=coerce_string(payload.get("transport")),
        allowed_actions=coerce_string_items(payload.get("allowed_actions")),
        available=coerce_bool(payload.get("available", True)),
    )
