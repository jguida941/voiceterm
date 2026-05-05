"""Ground-truth-first design preflight for ``devctl develop``."""

from __future__ import annotations

import hashlib
import json
import shlex
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ...collect import collect_git_status
from ...governance.script_catalog_registry import (
    CHECK_SCRIPT_RELATIVE_PATHS,
    PROBE_SCRIPT_RELATIVE_PATHS,
)
from ...platform.connectivity_registry import build_connectivity_registry_snapshot
from ...runtime.ground_truth_probe_receipt import (
    GroundTruthProbeRunInput,
    GroundTruthProbeRunReceipt,
    append_ground_truth_probe_receipt,
    build_ground_truth_probe_receipt,
    detect_ground_truth_trigger_paths,
    trigger_paths_digest,
)
from ...runtime.runtime_truth_snapshot import (
    RuntimeTruthSnapshot,
    RuntimeTruthSource,
    build_runtime_truth_snapshot,
)
from ...runtime.startup_signals import load_startup_quality_signals
from ...time_utils import utc_timestamp
from .models import DevelopmentDesignPreflight, DevelopmentGroundTruthProbe

_REQUIRED_PROBES = (
    "runtime_truth_snapshot",
    "agent_mind",
    "provider_session_state",
    "connectivity_registry",
    "command_registry",
    "startup_quality_signals",
    "existing_contracts",
)


def build_design_preflight(
    *,
    args: Any,
    repo_root: Path,
    review_state: Mapping[str, object],
) -> DevelopmentDesignPreflight | None:
    """Return a design preflight only for the matching `/develop` action."""
    action = str(
        getattr(args, "action_flag", None)
        or getattr(args, "action", None)
        or ""
    ).strip()
    if action != "design-preflight":
        return None
    topic = str(getattr(args, "topic", "") or "").strip()
    connectivity = build_connectivity_registry_snapshot(repo_root=repo_root)
    quality_signals = load_startup_quality_signals(repo_root)
    runtime_truth = build_runtime_truth_snapshot(
        repo_root=repo_root,
        review_state=review_state,
        connectivity_registry=connectivity.to_dict(),
        quality_signals=quality_signals,
    )
    runtime_truth_payload = _runtime_truth_payload(runtime_truth)
    changed_paths = _changed_paths(repo_root=repo_root)
    trigger_paths = detect_ground_truth_trigger_paths(
        repo_root=repo_root,
        changed_paths=changed_paths,
    )
    probes = _probe_rows(
        repo_root=repo_root,
        topic=topic,
        runtime_truth=runtime_truth_payload,
        connectivity=connectivity.to_dict(),
        quality_signals=quality_signals,
    )
    observed_probe_ids = tuple(row.probe_id for row in probes if row.status != "missing")
    routing_decision = _routing_decision(
        topic=topic,
        runtime_truth=runtime_truth_payload,
        connectivity=connectivity.to_dict(),
    )
    receipt: GroundTruthProbeRunReceipt = build_ground_truth_probe_receipt(
        GroundTruthProbeRunInput(
            trigger_paths=trigger_paths,
            design_ids=(topic or "design-preflight", routing_decision),
            required_probe_ids=_REQUIRED_PROBES,
            observed_probe_ids=observed_probe_ids,
            base_ref=str(getattr(args, "since_ref", "") or ""),
            head_ref="HEAD",
            probe_report_path="devctl develop design-preflight",
            probe_report_sha256=_preflight_digest(probes),
            warnings=runtime_truth.warnings,
        )
    )
    receipt_path = ""
    if bool(getattr(args, "record_ground_truth_receipt", False)):
        receipt_path = append_ground_truth_probe_receipt(
            receipt,
            repo_root=repo_root,
        ).relative_to(repo_root).as_posix()
    return DevelopmentDesignPreflight(
        topic=topic or "(unspecified)",
        routing_decision=routing_decision,
        summary=_summary(routing_decision),
        required_probe_ids=_REQUIRED_PROBES,
        observed_probe_ids=observed_probe_ids,
        trigger_paths=trigger_paths,
        trigger_paths_digest=trigger_paths_digest(trigger_paths),
        receipt_verdict=receipt.verdict,
        receipt_path=receipt_path,
        runtime_truth=runtime_truth_payload,
        probes=probes,
        next_commands=_next_commands(topic=topic, receipt_recorded=bool(receipt_path)),
    )


def _changed_paths(*, repo_root: Path) -> tuple[str, ...]:
    payload = collect_git_status(repo_root=repo_root)
    rows = payload.get("changes")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    paths = []
    for row in rows:
        if isinstance(row, Mapping):
            path = str(row.get("path") or "").strip()
            if path:
                paths.append(path)
    return tuple(sorted(dict.fromkeys(paths)))


def _runtime_truth_payload(snapshot: RuntimeTruthSnapshot) -> dict[str, object]:
    # Keep nested source rows visible to the contract-connectivity scanner.
    for source in snapshot.observed_sources:
        if isinstance(source, RuntimeTruthSource):
            break
    return snapshot.to_dict()


def _probe_rows(
    *,
    repo_root: Path,
    topic: str,
    runtime_truth: Mapping[str, object],
    connectivity: Mapping[str, object],
    quality_signals: Mapping[str, object],
) -> tuple[DevelopmentGroundTruthProbe, ...]:
    return (
        _probe(
            "runtime_truth_snapshot",
            "present" if runtime_truth else "missing",
            "Reduced current ReviewState-centered runtime truth.",
            "RuntimeTruthSnapshot",
            ("interaction_mode", "remote_control_active", "live_actor_ids"),
        ),
        _probe(
            "agent_mind",
            "present" if runtime_truth.get("agent_mind_providers") else "missing",
            "Provider-latest reasoning projections checked.",
            ",".join(_strings(runtime_truth.get("agent_mind_providers"))),
            ("session_id", "latest_events"),
        ),
        _provider_session_state_probe(repo_root=repo_root, topic=topic),
        _probe(
            "connectivity_registry",
            "present" if connectivity else "missing",
            "Typed contract writer/reader registry checked.",
            str(connectivity.get("contract_id") or ""),
            ("connected_contracts", "reader_ids"),
        ),
        _probe(
            "command_registry",
            "present",
            "Registered guard/probe command catalogs checked.",
            f"checks={len(CHECK_SCRIPT_RELATIVE_PATHS)} probes={len(PROBE_SCRIPT_RELATIVE_PATHS)}",
            ("CHECK_SCRIPT_RELATIVE_PATHS", "PROBE_SCRIPT_RELATIVE_PATHS"),
        ),
        _probe(
            "startup_quality_signals",
            "present" if quality_signals else "missing",
            "Startup quality-signal summaries checked.",
            ",".join(sorted(quality_signals)),
            tuple(sorted(quality_signals)),
        ),
        _probe(
            "existing_contracts",
            "present" if _contract_ids(connectivity) else "missing",
            "Existing platform contract ids checked before adding a new one.",
            ",".join(_matching_contract_ids(topic, connectivity)[:5]),
            ("contract_id", "runtime_model"),
        ),
    )


def _provider_session_state_probe(
    *,
    repo_root: Path,
    topic: str,
) -> DevelopmentGroundTruthProbe:
    if "remote" not in topic.lower() and "claude" not in topic.lower():
        return _probe(
            "provider_session_state",
            "not_applicable",
            "No provider-native state keyword in the topic.",
            "",
            (),
        )
    try:
        from ..remote_control._session_state_proof import (
            resolve_latest_live_session_state_bridge_proof,
        )
    except ImportError:
        return _probe(
            "provider_session_state",
            "missing",
            "Claude session-state reader is unavailable.",
            "",
            (),
        )
    proof = resolve_latest_live_session_state_bridge_proof(
        now_utc=utc_timestamp(),
        expected_cwd=repo_root,
        max_age_seconds=900,
    )
    if proof is None:
        return _probe(
            "provider_session_state",
            "absent",
            "Claude session-state was checked; no fresh bridgeSessionId proof is active for this repo.",
            "~/.claude/sessions/*.json",
            ("bridgeSessionId", "updatedAt", "pid", "cwd"),
        )
    return _probe(
        "provider_session_state",
        "present",
        "Fresh Claude bridgeSessionId proof found.",
        str(proof.path),
        ("bridgeSessionId", "updatedAt", "pid", "cwd"),
    )


def _routing_decision(
    *,
    topic: str,
    runtime_truth: Mapping[str, object],
    connectivity: Mapping[str, object],
) -> str:
    normalized = topic.lower()
    if "remote" in normalized and (
        runtime_truth.get("remote_control_active")
        or any("RemoteControl" in item for item in _contract_ids(connectivity))
    ):
        return "reuse_existing_surface"
    if _matching_contract_ids(topic, connectivity):
        return "extend_existing_contract"
    if not topic:
        return "blocked_missing_ground_truth"
    return "new_contract_needed"


def _summary(decision: str) -> str:
    return {
        "reuse_existing_surface": (
            "Existing upstream or typed runtime truth was found; route design through it."
        ),
        "extend_existing_contract": (
            "A related typed contract exists; extend it instead of adding a sidecar."
        ),
        "new_contract_needed": (
            "No matching contract was found after probes; a new contract may be justified."
        ),
        "blocked_missing_ground_truth": (
            "Design topic is missing; architecture work is blocked until the state is named."
        ),
    }.get(decision, "Ground-truth preflight completed.")


def _next_commands(*, topic: str, receipt_recorded: bool) -> tuple[str, ...]:
    topic_arg = shlex.quote(topic) if topic else '""'
    commands = []
    if not receipt_recorded:
        commands.append(
            "python3 dev/scripts/devctl.py develop design-preflight "
            f"--topic {topic_arg} --record-ground-truth-receipt --format json"
        )
    commands.append(
        "python3 dev/scripts/checks/check_ground_truth_probe_gate.py --format md"
    )
    return tuple(commands)


def _probe(
    probe_id: str,
    status: str,
    summary: str,
    evidence_ref: str,
    fields: tuple[str, ...],
) -> DevelopmentGroundTruthProbe:
    return DevelopmentGroundTruthProbe(
        probe_id=probe_id,
        status=status,
        summary=summary,
        evidence_ref=evidence_ref,
        observed_fields=fields,
    )


def _contract_ids(connectivity: Mapping[str, object]) -> tuple[str, ...]:
    rows = connectivity.get("connected_contracts")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    ids: list[str] = []
    for row in rows:
        if isinstance(row, Mapping):
            contract_id = str(row.get("contract_id") or "").strip()
            if contract_id:
                ids.append(contract_id)
    return tuple(ids)


def _matching_contract_ids(topic: str, connectivity: Mapping[str, object]) -> tuple[str, ...]:
    terms = [term for term in topic.replace("-", " ").replace("_", " ").split() if term]
    if not terms:
        return ()
    matches = []
    for contract_id in _contract_ids(connectivity):
        lower_id = contract_id.lower()
        if any(term.lower() in lower_id for term in terms):
            matches.append(contract_id)
    return tuple(matches)


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(str(item) for item in value if str(item).strip())


def _preflight_digest(probes: tuple[DevelopmentGroundTruthProbe, ...]) -> str:
    payload = json.dumps([asdict(probe) for probe in probes], sort_keys=True)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = ["build_design_preflight"]
