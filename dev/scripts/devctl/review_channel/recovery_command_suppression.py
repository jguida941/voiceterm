"""Shared recovery-command suppression for remote-only review producers."""

from __future__ import annotations

from collections.abc import MutableMapping


def suppress_legacy_recovery_command_when_remote_only(
    review_state: MutableMapping[str, object],
) -> None:
    """Mute legacy local recovery commands when typed eligibility says no.

    When ``coordination_state.recovery_eligibility`` is ``remote_only`` or
    ``blocked``, local recovery command strings are projections only. Producers
    suppress them before writing artifacts so disk review state, bridge-poll,
    turn-authority, and dashboard consumers share the same command authority.
    """
    coord = review_state.get("coordination_state")
    if not isinstance(coord, dict):
        return
    eligibility = str(coord.get("recovery_eligibility") or "").strip()
    if eligibility not in {"remote_only", "blocked"}:
        return
    assessment = review_state.get("recovery_assessment")
    if isinstance(assessment, dict):
        decision = assessment.get("decision")
        if isinstance(decision, dict) and decision.get("command"):
            decision["command"] = ""
    attention = review_state.get("attention")
    if isinstance(attention, dict) and attention.get("recommended_command"):
        attention["recommended_command"] = ""
    compat = review_state.get("_compat")
    if isinstance(compat, dict):
        _suppress_doctor_commands(compat.get("doctor"))
    _suppress_doctor_commands(review_state.get("doctor"))


def _suppress_doctor_commands(doctor: object) -> None:
    if not isinstance(doctor, dict):
        return
    if doctor.get("recommended_command"):
        doctor["recommended_command"] = ""
    if doctor.get("decision_command"):
        doctor["decision_command"] = ""


__all__ = ["suppress_legacy_recovery_command_when_remote_only"]
