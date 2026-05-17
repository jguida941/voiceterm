from __future__ import annotations

from dev.scripts.devctl.review_channel.agent_work_board_projection import (
    _session_safe_role_resolution,
)
from dev.scripts.devctl.review_channel.agent_work_board_roles import (
    RuntimeRoleResolution,
    build_runtime_role_index,
)


def _grant(capability: str, *, granted: bool = True) -> dict[str, object]:
    return {"capability": capability, "granted": granted}


def test_mutation_authority_overrides_legacy_provider_role() -> None:
    index = build_runtime_role_index(
        {
            "actor_authorities": [
                {
                    "actor_id": "codex",
                    "provider": "codex",
                    "role": "implementer",
                    "live": True,
                    "grants": [_grant("repo.stage"), _grant("repo.commit")],
                }
            ],
            "participants": [
                {
                    "agent_id": "codex",
                    "provider": "codex",
                    "role": "reviewer",
                    "capture_mode": "terminal-script",
                }
            ],
        }
    )

    resolved = index.resolve(
        actor_id="codex",
        provider="codex",
        declared_role="reviewer",
    )

    assert resolved.role == "implementer"
    assert resolved.declared_role == "reviewer"
    assert resolved.authority_role == "implementer"
    assert resolved.role_source == "actor_authority"
    assert resolved.role_scope == "actor"
    assert resolved.mutation_mode == "live_tree"
    assert resolved.granted_capabilities == ("repo.stage", "repo.commit")


def test_declared_implementer_without_mutation_grant_is_dashboard_lane() -> None:
    index = build_runtime_role_index(
        {
            "actor_authorities": [
                {
                    "actor_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "live": True,
                    "grants": [],
                }
            ],
            "participants": [
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "capture_mode": "terminal-script",
                }
            ],
        }
    )

    resolved = index.resolve(
        actor_id="claude",
        provider="claude",
        declared_role="implementer",
    )

    assert resolved.role == "dashboard"
    assert resolved.declared_role == "implementer"
    assert resolved.mutation_mode == "read_only"
    assert resolved.granted_capabilities == ()


def test_subagent_declared_role_remains_session_scoped_read_only() -> None:
    index = build_runtime_role_index(
        {
            "participants": [
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "capture_mode": "terminal-script",
                }
            ]
        }
    )

    resolved = index.resolve(
        actor_id="claude",
        provider="claude",
        declared_role="subagent",
    )

    assert resolved.role == "subagent"
    assert resolved.role_source == "session_declared_role"
    assert resolved.role_scope == "session"
    assert resolved.mutation_mode == "read_only"


def test_actor_scoped_mutation_authority_is_not_cloned_to_multiple_sessions() -> None:
    resolved = _session_safe_role_resolution(
        RuntimeRoleResolution(
            role="implementer",
            declared_role="reviewer",
            authority_role="implementer",
            role_source="actor_authority",
            role_scope="actor",
            mutation_mode="live_tree",
            granted_capabilities=("repo.stage", "repo.commit"),
        ),
        provider_session_count=2,
    )

    assert resolved.role == "dashboard"
    assert resolved.authority_role == "implementer"
    assert resolved.role_scope == "actor_ambiguous"
    assert resolved.mutation_mode == "read_only"
    assert resolved.granted_capabilities == ()
