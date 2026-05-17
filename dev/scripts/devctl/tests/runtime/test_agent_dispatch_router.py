from __future__ import annotations

from dev.scripts.devctl.runtime.agent_dispatch_router import (
    build_agent_dispatch_router,
)
from dev.scripts.devctl.runtime.review_state_parser import review_state_from_payload


def _decision(
    *,
    actor: str = "claude",
    role: str = "implementer",
    session: str = "s1",
    packet: str = "rev_pkt_1",
    granted_capabilities: tuple[str, ...] | None = None,
) -> dict[str, object]:
    return {
        "actor_id": actor,
        "actor_role": role,
        "session_id": session,
        "active_packet_id": packet,
        "attention_packet_id": packet,
        "source_latest_event_id": "rev_evt_10",
        "granted_capabilities": list(granted_capabilities or ()),
    }


def _work_row(
    *,
    actor: str = "claude",
    provider: str = "",
    role: str = "implementer",
    authority_role: str = "",
    role_scope: str = "",
    role_source: str = "",
    session: str = "s1",
    status: str = "polling",
    idle_seconds: int = 1,
    stale_after_seconds: int = 600,
    worktree: str = "../wt",
    branch: str = "feature/router",
    path_scope: tuple[str, ...] | None = None,
    current_file_or_module: str = "",
    mutation_mode: str = "",
    granted_capabilities: tuple[str, ...] | None = None,
    plan_row_id: str = "",
    work_scope_lease_id: str = "",
) -> dict[str, object]:
    return {
        "actor_id": actor,
        "provider": provider or actor,
        "role": role,
        "authority_role": authority_role,
        "role_scope": role_scope,
        "role_source": role_source,
        "session_id": session,
        "lane_id": f"{actor}_{session}",
        "worktree_identity": worktree,
        "branch": branch,
        "path_scope": list(path_scope or ("dev/scripts/devctl/runtime",)),
        "status": status,
        "idle_seconds": idle_seconds,
        "stale_after_seconds": stale_after_seconds,
        "last_active_utc": "2026-05-01T20:00:00Z",
        "source_event_id": "rev_evt_10",
        "source_surface": f"/sessions/{actor}/{session}.jsonl",
        "confidence_class": "derived_typed_event",
        "current_file_or_module": current_file_or_module,
        "mutation_mode": mutation_mode,
        "granted_capabilities": list(granted_capabilities or ()),
        "plan_row_id": plan_row_id,
        "work_scope_lease_id": work_scope_lease_id,
    }


def _packet(
    *,
    packet_id: str = "rev_pkt_1",
    to_agent: str = "claude",
    plan_id: str = "MP-377",
    target_role: str = "",
    target_session_id: str = "",
    requested_action: str = "implement_agent_dispatch_router",
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "plan_id": plan_id,
        "to_agent": to_agent,
        "kind": "action_request",
        "target_kind": "runtime",
        "target_ref": "agent_dispatch_router",
        "target_revision": "rev-a",
        "target_role": target_role,
        "target_session_id": target_session_id,
        "requested_action": requested_action,
        "latest_event_id": "rev_evt_10",
    }


def test_router_marks_same_packet_two_claude_sessions_ambiguous() -> None:
    review_state = {
        "snapshot_id": "snap-1",
        "source_identity": {"head_sha": "abc"},
        "packets": [_packet()],
        "agent_work_board": {
            "rows": [
                _work_row(session="s1"),
                _work_row(session="s2"),
            ]
        },
        "agent_loop_decisions": [
            _decision(session="s1"),
            _decision(session="s2"),
        ],
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert router["router_state"] == "ambiguous"
    assert router["selected_route_id"] == ""
    assert router["selected_route_ids"] == []
    assert {row["session_id"] for row in router["rejected_routes"]} == {
        "s1",
        "s2",
    }
    assert {
        row["reason"] for row in router["rejected_routes"]
    } == {"multiple_sessions_claim_same_packet"}


def test_router_keeps_valid_route_when_other_work_group_is_ambiguous() -> None:
    review_state = {
        "packets": [
            _packet(packet_id="rev_pkt_1"),
            _packet(packet_id="rev_pkt_2", to_agent="codex"),
        ],
        "agent_work_board": {
            "rows": [
                _work_row(session="s1"),
                _work_row(session="s2"),
                _work_row(actor="codex", role="reviewer", session="c1"),
            ]
        },
        "agent_loop_decisions": [
            _decision(session="s1", packet="rev_pkt_1"),
            _decision(session="s2", packet="rev_pkt_1"),
            _decision(
                actor="codex",
                role="reviewer",
                session="c1",
                packet="rev_pkt_2",
            ),
        ],
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert router["router_state"] == "partial"
    assert router["selected_route_id"] == "route:codex|reviewer|c1|rev_pkt_2"
    assert router["selected_route_ids"] == [
        "route:codex|reviewer|c1|rev_pkt_2"
    ]
    assert {
        row["reason"] for row in router["rejected_routes"]
    } == {"multiple_sessions_claim_same_packet"}


def test_router_rejects_actor_only_queue_route_with_multiple_sessions() -> None:
    review_state = {
        "queue": {
            "derived_next_instruction_source": {
                "packet_id": "rev_pkt_1",
                "to_agent": "claude",
            }
        },
        "packets": [_packet(packet_id="rev_pkt_1")],
        "agent_work_board": {
            "rows": [
                _work_row(session="s1"),
                _work_row(session="s2"),
            ]
        },
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert router["router_state"] == "blocked"
    assert router["selected_route_ids"] == []
    assert router["rejected_routes"] == [
        {
            "route_id": "route:claude|||rev_pkt_1",
            "actor_id": "claude",
            "provider": "claude",
            "actor_role": "",
            "session_id": "",
            "packet_id": "rev_pkt_1",
            "reason": "actor_session_unresolved",
            "evidence_refs": ["s1", "s2"],
        }
    ]


def test_router_keeps_stale_sessions_visible_but_out_of_dispatch() -> None:
    review_state = {
        "packets": [_packet()],
        "agent_work_board": {
            "rows": [
                _work_row(session="s1"),
                _work_row(
                    session="s2",
                    status="idle",
                    idle_seconds=999,
                    stale_after_seconds=600,
                ),
            ]
        },
        "agent_loop_decisions": [
            _decision(session="s1"),
            _decision(session="s2"),
        ],
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert router["router_state"] == "partial"
    assert router["selected_route_ids"] == [
        "route:claude|implementer|s1|rev_pkt_1"
    ]
    assert {
        (node["session_id"], node["freshness_state"])
        for node in router["session_nodes"]
    } == {("s1", "fresh"), ("s2", "stale")}
    assert router["rejected_routes"] == [
        {
            "route_id": "route:claude|implementer|s2|rev_pkt_1",
            "actor_id": "claude",
            "provider": "claude",
            "actor_role": "implementer",
            "session_id": "s2",
            "packet_id": "rev_pkt_1",
            "reason": "session_not_fresh",
            "evidence_refs": [
                "node:claude:implementer:s2",
                "stale",
                "rev_evt_10",
            ],
        }
    ]


def test_router_emits_governance_debt_for_unplanned_live_session() -> None:
    review_state = {
        "agent_work_board": {
            "rows": [_work_row(session="s1")]
        },
        "agent_loop_decisions": [
            _decision(session="s1", packet=""),
        ],
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert router["governance_debt"] == [
        {
            "debt_id": "debt:session_plan_binding:node:claude:implementer:s1",
            "debt_kind": "session_without_plan_binding",
            "severity": "high",
            "route_id": "",
            "session_node_id": "node:claude:implementer:s1",
            "actor_id": "claude",
            "actor_role": "implementer",
            "session_id": "s1",
            "packet_id": "",
            "plan_target_ref": "",
            "reason": "fresh_session_has_no_plan_target_or_packet_plan_binding",
            "required_remediation": (
                "bind session startup to WorkIntakePacket/PlanRow or "
                "scope its active packet to a plan target"
            ),
            "evidence_refs": ["rev_evt_10", "/sessions/claude/s1.jsonl"],
        }
    ]


def test_router_maps_packet_plan_id_into_work_focus_and_routes() -> None:
    review_state = {
        "packets": [_packet(plan_id="MP-412")],
        "agent_work_board": {"rows": [_work_row(session="s1")]},
        "agent_loop_decisions": [_decision(session="s1")],
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert router["routes"][0]["plan_target_ref"] == "MP-412"
    assert router["work_focus"][0]["plan_target_ref"] == "MP-412"
    assert not [
        debt
        for debt in router["governance_debt"]
        if debt["debt_kind"] == "route_without_plan_binding"
    ]


def test_router_exposes_session_graph_for_multiple_codex_and_claude_sessions() -> None:
    review_state = {
        "packets": [
            _packet(
                packet_id="rev_pkt_1",
                target_role="implementer",
                target_session_id="claude-1",
            ),
            _packet(packet_id="rev_pkt_2", to_agent="codex"),
            _packet(packet_id="rev_pkt_3"),
        ],
        "agent_work_board": {
            "rows": [
                _work_row(actor="codex", role="reviewer", session="codex-1"),
                _work_row(actor="codex", role="reviewer", session="codex-2"),
                _work_row(session="claude-1", worktree="../wt-a"),
                _work_row(session="claude-2", worktree="../wt-b"),
                _work_row(session="claude-3", worktree="../wt-c"),
            ]
        },
        "agent_loop_decisions": [
            _decision(session="claude-1", packet="rev_pkt_1"),
            _decision(session="claude-2", packet="rev_pkt_3"),
            _decision(session="claude-3", packet="rev_pkt_3"),
            _decision(
                actor="codex",
                role="reviewer",
                session="codex-1",
                packet="rev_pkt_2",
            ),
            _decision(
                actor="codex",
                role="reviewer",
                session="codex-2",
                packet="rev_pkt_2",
            ),
        ],
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert len(router["session_nodes"]) == 5
    assert {
        (node["actor_id"], node["session_id"], node["freshness_state"])
        for node in router["session_nodes"]
    } == {
        ("codex", "codex-1", "fresh"),
        ("codex", "codex-2", "fresh"),
        ("claude", "claude-1", "fresh"),
        ("claude", "claude-2", "fresh"),
        ("claude", "claude-3", "fresh"),
    }
    selected_route = next(
        route
        for route in router["routes"]
        if route["packet_id"] == "rev_pkt_1"
    )
    assert selected_route["session_node_id"] == "node:claude:implementer:claude-1"
    assert {
        group["group_kind"] for group in router["ambiguous_session_groups"]
    } == {"packet_claim"}
    assert {
        group["actor_id"] for group in router["ambiguous_session_groups"]
    } == {"codex", "claude"}
    assert any(
        link["link_kind"] == "packet_addressed_to"
        and link["to_node_id"] == "node:claude:implementer:claude-1"
        for link in router["peer_links"]
    )
    assert any(
        focus["session_node_id"] == "node:claude:implementer:claude-1"
        and focus["current_packet_id"] == "rev_pkt_1"
        for focus in router["work_focus"]
    )


def test_router_selects_scoped_claude_session_and_preserves_identity() -> None:
    review_state = {
        "packets": [_packet(target_role="coder", target_session_id="s1")],
        "agent_work_board": {"rows": [_work_row(role="implementation", session="s1")]},
        "agent_loop_decisions": [
            _decision(role="coder", session="s1"),
        ],
    }
    guard_dispatch = {
        "recommended_bundle": "bundle.tooling",
        "preflight_command": "python3 dev/scripts/devctl.py check --profile ci",
    }

    router = build_agent_dispatch_router(
        review_state=review_state,
        guard_dispatch=guard_dispatch,
    )
    payload = router.to_dict()

    assert payload["router_state"] == "ready"
    route = payload["routes"][0]
    assert route["actor_id"] == "claude"
    assert route["actor_role"] == "implementer"
    assert route["session_id"] == "s1"
    assert route["route_id"] == payload["selected_route_id"]
    assert payload["selected_route_ids"] == [route["route_id"]]
    assert route["guard_bundle"] == "bundle.tooling"
    assert route["preflight_command"].endswith("--profile ci")


def test_router_selects_scoped_session_when_another_session_claims_packet() -> None:
    review_state = {
        "packets": [_packet(target_role="implementer", target_session_id="s1")],
        "agent_work_board": {
            "rows": [
                _work_row(session="s1"),
                _work_row(session="s2"),
            ]
        },
        "agent_loop_decisions": [
            _decision(session="s1"),
            _decision(session="s2"),
        ],
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert router["router_state"] == "partial"
    assert router["selected_route_id"] == "route:claude|implementer|s1|rev_pkt_1"
    assert router["selected_route_ids"] == [
        "route:claude|implementer|s1|rev_pkt_1"
    ]
    assert [
        (row["session_id"], row["reason"]) for row in router["rejected_routes"]
    ] == [("s2", "packet_route_scope_mismatch")]


def test_router_routes_swapped_provider_roles_from_typed_rows() -> None:
    review_state = {
        "packets": [
            _packet(
                packet_id="rev_pkt_review",
                to_agent="claude",
                target_role="reviewer",
                target_session_id="claude-review",
            ),
            _packet(
                packet_id="rev_pkt_impl",
                to_agent="codex",
                target_role="implementer",
                target_session_id="codex-impl",
            ),
        ],
        "agent_work_board": {
            "rows": [
                _work_row(
                    actor="claude",
                    provider="claude",
                    role="reviewer",
                    session="claude-review",
                    mutation_mode="read_only",
                ),
                _work_row(
                    actor="codex",
                    provider="codex",
                    role="implementer",
                    session="codex-impl",
                    mutation_mode="live_tree",
                    granted_capabilities=("repo.stage", "repo.commit"),
                ),
            ]
        },
        "agent_loop_decisions": [
            _decision(
                actor="claude",
                role="reviewer",
                session="claude-review",
                packet="rev_pkt_review",
            ),
            _decision(
                actor="codex",
                role="implementer",
                session="codex-impl",
                packet="rev_pkt_impl",
                granted_capabilities=("repo.stage",),
            ),
        ],
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert router["router_state"] == "ready"
    routes = {route["packet_id"]: route for route in router["routes"]}
    assert routes["rev_pkt_review"]["provider"] == "claude"
    assert routes["rev_pkt_review"]["actor_role"] == "reviewer"
    assert routes["rev_pkt_review"]["session_node_id"] == (
        "node:claude:reviewer:claude-review"
    )
    assert routes["rev_pkt_impl"]["provider"] == "codex"
    assert routes["rev_pkt_impl"]["actor_role"] == "implementer"
    assert routes["rev_pkt_impl"]["session_node_id"] == (
        "node:codex:implementer:codex-impl"
    )
    assert "route:codex|reviewer" not in " ".join(router["selected_route_ids"])
    assert "route:claude|implementer" not in " ".join(router["selected_route_ids"])


def test_router_rejects_mutation_packet_without_session_capability() -> None:
    review_state = {
        "packets": [
            _packet(
                requested_action="stage_commit_pipeline",
                target_role="implementer",
                target_session_id="s1",
            )
        ],
        "agent_work_board": {
            "rows": [
                _work_row(
                    session="s1",
                    mutation_mode="read_only",
                    granted_capabilities=(),
                )
            ]
        },
        "agent_loop_decisions": [
            _decision(
                session="s1",
                granted_capabilities=("repo.stage",),
            )
        ],
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert router["router_state"] == "blocked"
    assert router["selected_route_ids"] == []
    assert router["rejected_routes"] == [
        {
            "route_id": "route:claude|implementer|s1|rev_pkt_1",
            "actor_id": "claude",
            "provider": "claude",
            "actor_role": "implementer",
            "session_id": "s1",
            "packet_id": "rev_pkt_1",
            "reason": "missing_required_capability",
            "evidence_refs": [
                "node:claude:implementer:s1",
                "repo.stage",
                "",
            ],
        }
    ]


def test_router_rejects_actor_ambiguous_mutation_session_even_with_actor_grants() -> None:
    review_state = {
        "packets": [
            _packet(
                requested_action="stage_commit_pipeline",
                target_role="implementer",
                target_session_id="s1",
            )
        ],
        "agent_work_board": {
            "rows": [
                _work_row(
                    session="s1",
                    mutation_mode="read_only",
                    granted_capabilities=("repo.stage",),
                )
            ]
        },
        "agent_loop_decisions": [
            _decision(
                session="s1",
                granted_capabilities=("repo.stage",),
            )
        ],
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert router["router_state"] == "blocked"
    assert router["selected_route_ids"] == []
    assert router["rejected_routes"] == [
        {
            "route_id": "route:claude|implementer|s1|rev_pkt_1",
            "actor_id": "claude",
            "provider": "claude",
            "actor_role": "implementer",
            "session_id": "s1",
            "packet_id": "rev_pkt_1",
            "reason": "mutation_mode_not_writable",
            "evidence_refs": [
                "node:claude:implementer:s1",
                "read_only",
                "repo.stage",
            ],
        }
    ]


def test_router_blocks_scoped_packet_when_session_does_not_match() -> None:
    review_state = {
        "packets": [_packet(target_role="implementer", target_session_id="s2")],
        "agent_work_board": {"rows": [_work_row(session="s1")]},
        "agent_loop_decisions": [_decision(session="s1")],
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert router["router_state"] == "blocked"
    assert router["selected_route_id"] == ""
    assert router["selected_route_ids"] == []
    assert router["rejected_routes"][0]["reason"] == "packet_route_scope_mismatch"


def test_router_emits_critical_debt_for_overlapping_write_scope() -> None:
    review_state = {
        "agent_work_board": {
            "rows": [
                _work_row(
                    actor="codex",
                    role="reviewer",
                    session="c1",
                    worktree="../wt",
                    path_scope=("dev/scripts/devctl/runtime",),
                    current_file_or_module=(
                        "dev/scripts/devctl/runtime/agent_dispatch_router.py"
                    ),
                    mutation_mode="live_tree",
                ),
                _work_row(
                    actor="codex",
                    role="reviewer",
                    session="c2",
                    worktree="../wt",
                    path_scope=("dev/scripts/devctl/runtime/agent_dispatch_router.py",),
                    current_file_or_module=(
                        "dev/scripts/devctl/runtime/agent_dispatch_router.py"
                    ),
                    mutation_mode="live_tree",
                ),
            ]
        },
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    debts = [
        debt
        for debt in router["governance_debt"]
        if debt["debt_kind"] == "overlapping_write_scope_without_lease_or_plan"
    ]
    assert len(debts) == 1
    assert debts[0]["severity"] == "critical"
    assert debts[0]["reason"] == (
        "fresh_live_sessions_overlap_write_scope_without_"
        "work_scope_lease_or_plan_binding"
    )
    assert "current_file:" in debts[0]["evidence_refs"][2]


def test_router_emits_debt_for_actor_ambiguous_mutation_authority() -> None:
    review_state = {
        "agent_work_board": {
            "rows": [
                _work_row(
                    actor="codex",
                    role="dashboard",
                    authority_role="implementer",
                    role_scope="actor_ambiguous",
                    role_source="actor_authority",
                    session="c1",
                    mutation_mode="read_only",
                    granted_capabilities=("runtime.observe",),
                )
            ]
        },
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    debts = [
        debt
        for debt in router["governance_debt"]
        if debt["debt_kind"] == "session_bound_mutation_authority_required"
    ]
    assert len(debts) == 1
    assert debts[0]["severity"] == "high"
    assert debts[0]["actor_role"] == "dashboard"
    assert debts[0]["reason"] == (
        "actor_scoped_mutation_authority_cannot_select_session"
    )


def test_router_allows_overlapping_write_scope_with_shared_plan() -> None:
    review_state = {
        "agent_work_board": {
            "rows": [
                _work_row(
                    actor="codex",
                    role="reviewer",
                    session="c1",
                    current_file_or_module=(
                        "dev/scripts/devctl/runtime/agent_dispatch_router.py"
                    ),
                    mutation_mode="live_tree",
                    plan_row_id="MP377-P0-T22AF-E",
                ),
                _work_row(
                    actor="codex",
                    role="reviewer",
                    session="c2",
                    current_file_or_module=(
                        "dev/scripts/devctl/runtime/agent_dispatch_router.py"
                    ),
                    mutation_mode="live_tree",
                    plan_row_id="MP377-P0-T22AF-E",
                ),
            ]
        },
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert not [
        debt
        for debt in router["governance_debt"]
        if debt["debt_kind"] == "overlapping_write_scope_without_lease_or_plan"
    ]


def test_router_allows_overlapping_write_scope_with_shared_lease() -> None:
    review_state = {
        "agent_work_board": {
            "rows": [
                _work_row(
                    actor="codex",
                    role="reviewer",
                    session="c1",
                    current_file_or_module=(
                        "dev/scripts/devctl/runtime/agent_dispatch_router.py"
                    ),
                    mutation_mode="live_tree",
                    work_scope_lease_id="lease-router",
                ),
                _work_row(
                    actor="codex",
                    role="reviewer",
                    session="c2",
                    current_file_or_module=(
                        "dev/scripts/devctl/runtime/agent_dispatch_router.py"
                    ),
                    mutation_mode="live_tree",
                    work_scope_lease_id="lease-router",
                ),
            ]
        },
    }

    router = build_agent_dispatch_router(review_state=review_state).to_dict()

    assert not [
        debt
        for debt in router["governance_debt"]
        if debt["debt_kind"] == "overlapping_write_scope_without_lease_or_plan"
    ]


def test_guard_dispatch_packet_alone_is_not_executable_agent_route() -> None:
    router = build_agent_dispatch_router(
        review_state={},
        guard_dispatch={
            "recommended_bundle": "bundle.runtime",
            "preflight_command": "python3 dev/scripts/devctl.py check --profile ci",
        },
    ).to_dict()

    assert router["router_state"] == "no_dispatchable_work"
    assert router["routes"] == []
    assert router["selected_route_id"] == ""
    assert router["selected_route_ids"] == []


def test_review_state_parser_round_trips_agent_dispatch_router() -> None:
    parsed = review_state_from_payload({
        "review_state": {
            "agent_dispatch_router": {
                "contract_id": "AgentDispatchRouter",
                "router_state": "ready",
                "selected_route_id": "route:claude|implementer|s1|rev_pkt_1",
                "selected_route_ids": ["route:claude|implementer|s1|rev_pkt_1"],
            }
        }
    })

    assert parsed.agent_dispatch_router["router_state"] == "ready"
    assert parsed.agent_dispatch_router["selected_route_id"].startswith("route:")
    assert parsed.agent_dispatch_router["selected_route_ids"] == [
        "route:claude|implementer|s1|rev_pkt_1"
    ]
