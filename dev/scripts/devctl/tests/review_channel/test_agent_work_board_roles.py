from __future__ import annotations

from dev.scripts.devctl.review_channel.agent_work_board_projection import (
    _demote_helper_codex_session,
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


def test_declared_implementer_without_mutation_grant_stays_read_only_implementer_lane() -> None:
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

    assert resolved.role == "implementer"
    assert resolved.declared_role == "implementer"
    assert resolved.role_source == "declared_role_without_mutation_authority"
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


def test_v4552_helper_codex_session_demoted_to_subagent() -> None:
    """v4.55.2 (rev_pkt_4767): when multiple codex session files are recent,
    only session_index=1 (most-recently-active) is the main conductor.
    Older entries are spawn-audit helper sidecars and must be demoted to
    `subagent` so they do not appear as codex:reviewer controller rows
    in `develop next` / `develop launch` dry-run.
    """
    conductor_resolution = RuntimeRoleResolution(
        role="reviewer",
        declared_role="reviewer",
        authority_role="reviewer",
        role_source="actor_authority",
        role_scope="actor",
        mutation_mode="live_tree",
        granted_capabilities=("repo.review",),
    )

    # Most-recently-active codex session: untouched.
    main = _demote_helper_codex_session(
        conductor_resolution, session_index=1, session_count=4
    )
    assert main is conductor_resolution

    # Helper sessions (index >= 2): demoted to subagent.
    for helper_index in (2, 3, 4):
        helper = _demote_helper_codex_session(
            conductor_resolution,
            session_index=helper_index,
            session_count=4,
        )
        assert helper.role == "subagent", helper_index
        assert helper.role_source == "helper_session_demotion"
        assert helper.role_scope == "session"
        assert helper.mutation_mode == "read_only"
        assert helper.granted_capabilities == ()


def test_v4552_single_codex_session_not_demoted() -> None:
    """A solo codex session (session_count == 1) is always the main
    conductor and must retain its resolved authority — no demotion."""
    resolution = RuntimeRoleResolution(
        role="reviewer",
        declared_role="reviewer",
        authority_role="reviewer",
        role_source="actor_authority",
        role_scope="actor",
        mutation_mode="live_tree",
        granted_capabilities=("repo.review",),
    )

    result = _demote_helper_codex_session(
        resolution, session_index=1, session_count=1
    )

    assert result is resolution


def test_v4552_existing_subagent_resolution_preserved() -> None:
    """If a helper-index session has already resolved to `subagent` (e.g.
    via declared_role='subagent'), the demoter is a no-op."""
    resolution = RuntimeRoleResolution(
        role="subagent",
        declared_role="subagent",
        authority_role="",
        role_source="session_declared_role",
        role_scope="session",
        mutation_mode="read_only",
        granted_capabilities=(),
    )

    result = _demote_helper_codex_session(
        resolution, session_index=3, session_count=4
    )

    assert result is resolution


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
