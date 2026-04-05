"""Support helpers for the session-resume command: data contract, cache, rendering."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...time_utils import utc_timestamp
from .session_resume_paths import (
    get_review_state_mtime,
    governance_interaction_mode,
    resolve_governance,
    resolve_source_paths,
)

if TYPE_CHECKING:
    from ...runtime.project_governance import ProjectGovernance


SESSION_CACHE_RELATIVE_DIR = Path("dev/reports/session_cache/latest")
SESSION_CACHE_FILENAME = "cache.json"

@dataclass(frozen=True, slots=True)
class SessionCachePacket:
    """Compact session state replacing full bootstrap output."""

    schema_version: int = 1
    contract_id: str = "SessionCachePacket"
    generated_at_utc: str = ""
    role: str = "implementer"
    branch: str = ""
    head_sha: str = ""
    advisory_action: str = ""
    advisory_reason: str = ""
    blockers: str = "none"
    interaction_mode: str = "local_terminal"
    current_instruction: str = ""
    instruction_revision: str = ""
    ack_state: str = "missing"
    open_findings: str = ""
    last_guard_ok: bool = True
    review_state_mtime: float = 0.0
    done_summary: str = ""
    next_action: str = ""
    key_rules: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["key_rules"] = list(self.key_rules)
        return payload


def try_cache_hit(
    repo_root: Path,
    *,
    head_sha: str,
    role: str,
    review_state_mtime: float = 0.0,
) -> SessionCachePacket | None:
    """Return the cached packet when it matches current HEAD, role, and review state."""
    cache_path = repo_root / SESSION_CACHE_RELATIVE_DIR / SESSION_CACHE_FILENAME
    if not cache_path.is_file():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    if str(payload.get("head_sha") or "").strip() != head_sha:
        return None
    if str(payload.get("role") or "").strip() != role:
        return None
    cached_mtime = float(payload.get("review_state_mtime") or 0.0)
    if review_state_mtime != cached_mtime:
        return None
    return packet_from_mapping(payload)


def write_cache(repo_root: Path, packet: SessionCachePacket) -> None:
    """Persist the session-cache packet for future cache hits."""
    cache_dir = repo_root / SESSION_CACHE_RELATIVE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / SESSION_CACHE_FILENAME
    cache_path.write_text(
        json.dumps(packet.to_dict(), indent=2),
        encoding="utf-8",
    )


def build_from_sources(
    repo_root: Path,
    *,
    role: str,
    head_sha: str,
    governance: "ProjectGovernance | None" = None,
) -> SessionCachePacket:
    """Build a fresh packet from receipt, compact, and review-state sources."""
    resolved_governance = resolve_governance(repo_root, governance=governance)
    paths = resolve_source_paths(repo_root, governance=resolved_governance)

    receipt = _load_json(repo_root / paths["receipt"])
    compact = _load_json(repo_root / paths["compact"])
    review_state = _load_json(repo_root / paths["review_state"])

    branch = _str_field(receipt, "current_branch")
    advisory_action = _str_field(receipt, "advisory_action")
    advisory_reason = _str_field(receipt, "advisory_reason")
    checkpoint_required = bool(receipt.get("checkpoint_required", False)) if receipt else False
    safe_to_continue = bool(receipt.get("safe_to_continue_editing", True)) if receipt else True
    authority_ok = bool(receipt.get("startup_authority_ok", False)) if receipt else False
    review_gate_push = bool(receipt.get("review_gate_allows_push", False)) if receipt else False
    last_guard_ok = authority_ok

    current_session = _nested_dict(compact, "current_session")
    if not current_session:
        current_session = _nested_dict(review_state, "current_session")

    current_instruction = _str_field(current_session, "current_instruction")
    instruction_revision = _str_field(current_session, "current_instruction_revision")
    ack_state = _str_field(current_session, "implementer_ack_state") or "missing"
    open_findings = _str_field(current_session, "open_findings")

    blockers = compute_blockers(
        checkpoint_required=checkpoint_required,
        safe_to_continue=safe_to_continue,
        authority_ok=authority_ok,
    )
    interaction_mode = derive_interaction_mode(compact, governance=resolved_governance)
    next_action = derive_next_action(receipt, blockers)
    done_summary = _derive_done_summary(receipt)
    rs_mtime = get_review_state_mtime(repo_root, governance=resolved_governance)
    key_rules = distill_key_rules(
        safe_to_continue=safe_to_continue,
        checkpoint_required=checkpoint_required,
        ack_current=(ack_state == "current"),
        review_gate_allows_push=review_gate_push,
        last_guard_ok=last_guard_ok,
    )

    return SessionCachePacket(
        generated_at_utc=utc_timestamp(),
        role=role,
        branch=branch,
        head_sha=head_sha,
        advisory_action=advisory_action,
        advisory_reason=advisory_reason,
        blockers=blockers,
        interaction_mode=interaction_mode,
        current_instruction=current_instruction,
        instruction_revision=instruction_revision,
        ack_state=ack_state,
        open_findings=open_findings,
        last_guard_ok=last_guard_ok,
        review_state_mtime=rs_mtime,
        done_summary=done_summary,
        next_action=next_action,
        key_rules=key_rules,
    )


def compute_blockers(
    *,
    checkpoint_required: bool,
    safe_to_continue: bool,
    authority_ok: bool,
) -> str:
    parts: list[str] = []
    if not authority_ok:
        parts.append("startup_authority")
    if checkpoint_required:
        parts.append("checkpoint_required")
    if not safe_to_continue:
        parts.append("continuation_blocked")
    return ",".join(parts) if parts else "none"


def derive_interaction_mode(
    compact: dict[str, Any] | None,
    *,
    governance: "ProjectGovernance | None" = None,
) -> str:
    """Derive interaction mode, preferring governance BridgeConfig over compact."""
    gov_mode = governance_interaction_mode(governance)
    if gov_mode:
        return gov_mode
    if compact is None:
        return "local_terminal"
    collab = _nested_dict(compact, "collaboration")
    if not collab:
        return "local_terminal"
    reviewer_mode = _str_field(collab, "reviewer_mode")
    if reviewer_mode == "active_dual_agent":
        return "active_dual_agent"
    return "local_terminal"


def derive_next_action(receipt: dict[str, Any] | None, blockers: str) -> str:
    if receipt is None:
        return "run startup-context to generate receipt"
    if blockers != "none":
        cmd = _str_field(receipt, "push_next_step_command")
        if cmd:
            return cmd
        return "resolve blockers, then rerun startup-context"
    push_action = _str_field(receipt, "push_action")
    if push_action == "run_devctl_push":
        return "python3 dev/scripts/devctl.py push --execute"
    return "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"


def distill_key_rules(
    *,
    safe_to_continue: bool,
    checkpoint_required: bool,
    ack_current: bool,
    review_gate_allows_push: bool,
    last_guard_ok: bool,
) -> tuple[str, ...]:
    rules: list[str] = [
        f"safe_to_continue={safe_to_continue}",
        f"checkpoint_required={checkpoint_required}",
        f"ack_current={ack_current}",
        f"review_gate_allows_push={review_gate_allows_push}",
        f"last_guard_ok={last_guard_ok}",
    ]
    return tuple(rules)


def render_markdown(packet: SessionCachePacket) -> str:
    lines = [
        "## Session Resume",
        "",
        f"- **role**: {packet.role}",
        f"- **branch**: {packet.branch}",
        f"- **head**: `{packet.head_sha[:12]}`" if packet.head_sha else "- **head**: (unknown)",
        f"- **advisory**: {packet.advisory_action} / {packet.advisory_reason}",
        f"- **blockers**: {packet.blockers}",
        f"- **mode**: {packet.interaction_mode}",
        f"- **ack**: {packet.ack_state}",
        f"- **guard_ok**: {packet.last_guard_ok}",
        "",
    ]
    if packet.current_instruction:
        lines.append("### Current instruction")
        lines.append(packet.current_instruction)
        lines.append("")
    if packet.open_findings:
        lines.append("### Open findings")
        lines.append(packet.open_findings)
        lines.append("")
    if packet.next_action:
        lines.append(f"**Next**: `{packet.next_action}`")
        lines.append("")
    if packet.key_rules:
        lines.append("### Key rules")
        for rule in packet.key_rules:
            lines.append(f"- {rule}")
        lines.append("")
    return "\n".join(lines)


def render_summary(packet: SessionCachePacket) -> str:
    lines = [
        f"role={packet.role}",
        f"branch={packet.branch}",
        f"head={packet.head_sha[:12]}" if packet.head_sha else "head=unknown",
        f"action={packet.advisory_action}",
        f"reason={packet.advisory_reason}",
        f"blockers={packet.blockers}",
        f"mode={packet.interaction_mode}",
        f"ack={packet.ack_state}",
        f"guard_ok={packet.last_guard_ok}",
        f"next={packet.next_action}",
    ]
    return "\n".join(lines)


def current_head(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def packet_from_mapping(payload: dict[str, Any]) -> SessionCachePacket:
    return SessionCachePacket(
        schema_version=int(payload.get("schema_version") or 1),
        contract_id=str(payload.get("contract_id") or "SessionCachePacket").strip(),
        generated_at_utc=str(payload.get("generated_at_utc") or "").strip(),
        role=str(payload.get("role") or "implementer").strip(),
        branch=str(payload.get("branch") or "").strip(),
        head_sha=str(payload.get("head_sha") or "").strip(),
        advisory_action=str(payload.get("advisory_action") or "").strip(),
        advisory_reason=str(payload.get("advisory_reason") or "").strip(),
        blockers=str(payload.get("blockers") or "none").strip(),
        interaction_mode=str(payload.get("interaction_mode") or "local_terminal").strip(),
        current_instruction=str(payload.get("current_instruction") or "").strip(),
        instruction_revision=str(payload.get("instruction_revision") or "").strip(),
        ack_state=str(payload.get("ack_state") or "missing").strip(),
        open_findings=str(payload.get("open_findings") or "").strip(),
        last_guard_ok=bool(payload.get("last_guard_ok", True)),
        review_state_mtime=float(payload.get("review_state_mtime") or 0.0),
        done_summary=str(payload.get("done_summary") or "").strip(),
        next_action=str(payload.get("next_action") or "").strip(),
        key_rules=tuple(
            str(r).strip() for r in payload.get("key_rules", ()) if str(r).strip()
        ),
    )


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def _nested_dict(data: dict[str, Any] | None, key: str) -> dict[str, Any] | None:
    if data is None:
        return None
    value = data.get(key)
    return dict(value) if isinstance(value, dict) else None


def _str_field(data: dict[str, Any] | None, key: str) -> str:
    if data is None:
        return ""
    return str(data.get(key) or "").strip()


def _derive_done_summary(receipt: dict[str, Any] | None) -> str:
    if receipt is None:
        return ""
    return _str_field(receipt, "push_next_step_summary")
