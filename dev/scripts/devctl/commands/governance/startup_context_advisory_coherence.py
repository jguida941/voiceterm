"""Keep startup-context advisory_action coherent with the blocker list.

Codex's P1 finding against the governance-quality sweep caught a
contradiction: the startup receipt could advertise
``advisory_action=push_allowed`` alongside
``blockers=coordination_resync_required`` or
``blockers=implementation_permission_blocked`` while the canonical
``next_command`` was simultaneously downgraded to
``review-channel --action status``. Those three fields are meant to
describe the same typed state, so a green action atop a red blocker
list made the summary receipt unreliable for the publish slice it was
supposed to authorize.

This module is the Path A fix: the blocker list is the authoritative
signal. Whenever blockers are present, the coerced advisory_action
must not be ``push_allowed``. Both the pure coercion rule and the
synthetic payload projection live here so the rule is easy to unit
test without standing up a full ``build_startup_context`` fixture
tree, and so the startup-context command module stays focused on
orchestration instead of re-deriving blocker semantics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from dev.scripts.devctl.runtime.startup_context import StartupContext


class BlockerProbePayload(TypedDict):
    """Typed shape the blocker detector needs from StartupContext.

    Mirrors the subset of the rendered startup-context payload that
    ``_summary_blockers`` consults: the advisory pair, startup-authority
    pass/fail, push-enforcement flags, reviewer-gate flags, the
    coordination snapshot, and the rolled-up implementation permission.
    Keeping this shape typed prevents drift between the probe projection
    and the reader function's field expectations.
    """

    advisory_action: str
    advisory_reason: str
    startup_authority: dict[str, object]
    governance: dict[str, object]
    reviewer_gate: dict[str, object]
    coordination: dict[str, object]
    implementation_permission: str


def build_blocker_probe_payload(
    ctx: "StartupContext",
    authority_payload: dict[str, object],
) -> BlockerProbePayload:
    """Project a minimal typed payload for the blocker-detection pass.

    ``_summary_blockers`` reads a dict payload shaped like the public
    startup-context JSON. When we need to detect blockers *before* the
    full payload is serialized — so the advisory_action coercion lands
    before ``build_startup_receipt`` — we build a slim synthetic payload
    that only carries the fields ``_summary_blockers`` actually
    consults. That keeps the blocker contract tied to one reader
    function instead of re-implementing the rules at multiple call
    sites.
    """
    governance = ctx.governance
    push_enforcement_payload = _push_enforcement_projection(governance)
    reviewer_gate_payload = _reviewer_gate_projection(ctx.reviewer_gate)
    coordination_payload = (
        ctx.coordination.to_dict() if ctx.coordination is not None else {}
    )
    return BlockerProbePayload(
        advisory_action=ctx.advisory_action,
        advisory_reason=ctx.advisory_reason,
        startup_authority=authority_payload,
        governance={"push_enforcement": push_enforcement_payload},
        reviewer_gate=reviewer_gate_payload,
        coordination=coordination_payload,
        implementation_permission=ctx.implementation_permission,
    )


def coerce_advisory_for_blockers(
    advisory_action: str,
    advisory_reason: str,
    blockers_csv: str,
) -> tuple[str, str]:
    """Downgrade advisory_action to match the typed blocker list.

    The blocker list is the authoritative signal. Whenever blockers
    are present, ``advisory_action`` cannot stay on ``push_allowed``.
    Downgrade it to ``repair_reviewer_loop`` and stamp the reason with
    the first typed blocker so downstream renderers (``_render_summary``,
    ``_machine_summary``, the markdown projection, and
    ``project_startup_action_routing``) all see the same consistent
    (action, reason) pair rather than a contradiction. ``advisory_action``
    values other than ``push_allowed`` are left untouched because the
    finding only describes the contradiction between the green publish
    action and the red blocker list.
    """
    if blockers_csv == "none":
        return advisory_action, advisory_reason
    if advisory_action != "push_allowed":
        return advisory_action, advisory_reason
    first_blocker = blockers_csv.split(",", 1)[0].strip() or "blocked"
    return "repair_reviewer_loop", f"blockers_present:{first_blocker}"


def _push_enforcement_projection(governance) -> dict[str, object]:
    if governance is None:
        return {"checkpoint_required": False, "safe_to_continue_editing": True}
    push = governance.push_enforcement
    if push is None:
        return {"checkpoint_required": False, "safe_to_continue_editing": True}
    return {
        "checkpoint_required": bool(push.checkpoint_required),
        "safe_to_continue_editing": bool(push.safe_to_continue_editing),
    }


def _reviewer_gate_projection(reviewer_gate) -> dict[str, object]:
    return {
        "implementation_blocked": bool(reviewer_gate.implementation_blocked),
        "review_gate_allows_push": bool(reviewer_gate.review_gate_allows_push),
        "implementation_block_reason": (
            reviewer_gate.implementation_block_reason or ""
        ),
    }


__all__ = [
    "build_blocker_probe_payload",
    "coerce_advisory_for_blockers",
]
