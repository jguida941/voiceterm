"""Focused tests for the typed startup-context surface."""

from __future__ import annotations

import json
import unittest
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import COMMAND_HANDLERS, build_parser
from dev.scripts.devctl.commands.governance import (
    startup_context as startup_context_command,
)
from dev.scripts.devctl.commands.governance.startup_context import (
    _machine_summary,
    _render_markdown,
    _render_summary,
)
from dev.scripts.devctl.commands.governance.startup_context_defer import (
    auto_defer_publication_for_development,
)
from dev.scripts.devctl.commands.listing import COMMANDS
from dev.scripts.devctl.platform.coordination_snapshot_models import (
    CoordinationActorRecord,
    CoordinationSnapshot,
)
from dev.scripts.devctl.runtime.authority_snapshot import (
    AuthoritySnapshot,
    authority_snapshot_from_mapping,
    build_authority_snapshot,
    summary_next_command,
)
from dev.scripts.devctl.runtime.authority_snapshot_actions import (
    interaction_mode_from_reviewer_mode,
)
from dev.scripts.devctl.runtime.conductor_capability import (
    session_resume_command_for_role,
)
from dev.scripts.devctl.runtime.project_governance import (
    DELIVERY_MODE_LIBRARY_IMPORT_ONLY,
    PROJECT_GOVERNANCE_CONTRACT_ID,
    PROJECT_GOVERNANCE_SCHEMA_VERSION,
    ArtifactRoots,
    BridgeConfig,
    BundleOverrides,
    DocRegistry,
    DocRegistryEntry,
    EnabledChecks,
    MemoryRoots,
    PathRoots,
    PlanRegistryRoots,
    ProjectGovernance,
    PushEnforcement,
    RepoIdentity,
    RepoPackRef,
)
from dev.scripts.devctl.runtime.recovery_authority import (
    RecoveryAuthorityState,
    derive_recovery_authority,
)
from dev.scripts.devctl.runtime.review_state_models import (
    AgentAttentionRecord,
    PacketInboxState,
    ReviewAttentionState,
    ReviewCurrentSessionState,
)
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
    ReviewerRuntimeContract,
    ReviewerSessionOwnerState,
)
from dev.scripts.devctl.runtime.runtime_truth_snapshot import RuntimeTruthSnapshot
from dev.scripts.devctl.runtime.session_posture import SessionPosture
from dev.scripts.devctl.runtime.startup_blocker_decision import BlockerSnapshot
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    BypassAuthorityScope,
    BypassEvaluationInput,
    BypassRequest,
    evaluate_bypass_request,
)
from dev.scripts.devctl.runtime.startup_context import (
    ReviewerGateState,
    StartupContext,
    _derive_advisory_action,
    _derive_push_decision,
    _detect_reviewer_gate,
    _load_startup_review_state,
    blocks_new_implementation,
    build_startup_context,
)
from dev.scripts.devctl.runtime.startup_context_assembly import (
    _collect_active_bypass_lifecycles,
)
from dev.scripts.devctl.runtime.work_intake_models import (
    PlanTargetRef,
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
)


def _minimal_governance(**push_overrides) -> ProjectGovernance:
    """Build a minimal ProjectGovernance for testing advisory logic."""
    pe = PushEnforcement(**push_overrides)
    return ProjectGovernance(
        schema_version=PROJECT_GOVERNANCE_SCHEMA_VERSION,
        contract_id=PROJECT_GOVERNANCE_CONTRACT_ID,
        repo_identity=RepoIdentity(repo_name="test"),
        repo_pack=RepoPackRef(pack_id="test"),
        path_roots=PathRoots(),
        plan_registry=PlanRegistryRoots(),
        artifact_roots=ArtifactRoots(),
        memory_roots=MemoryRoots(),
        bridge_config=BridgeConfig(),
        enabled_checks=EnabledChecks(),
        bundle_overrides=BundleOverrides(overrides={}),
        push_enforcement=pe,
    )


@lru_cache(maxsize=1)
def _live_startup_context() -> StartupContext:
    """Build the live startup snapshot once for read-only smoke assertions."""
    return build_startup_context()


class TestStartupContextBuild(unittest.TestCase):
    """Verify startup-context builds from live repo state."""

    def test_builds_without_error(self) -> None:
        ctx = _live_startup_context()
        self.assertIsNotNone(ctx)

    def test_inline_library_governance_skips_push_decision_derivation(self) -> None:
        with TemporaryDirectory() as tmpdir:
            governance = ProjectGovernance.from_inline(repo_name="embedded")
            ctx = build_startup_context(
                repo_root=Path(tmpdir),
                governance=governance,
                review_state=None,
            )

        self.assertEqual(
            ctx.governance.bridge_config.delivery_mode,
            DELIVERY_MODE_LIBRARY_IMPORT_ONLY,
        )
        self.assertIsNone(ctx.governance.push_enforcement)
        self.assertEqual(ctx.push_decision.action, "no_push_needed")
        self.assertEqual(
            ctx.push_decision.reason,
            f"delivery_mode:{DELIVERY_MODE_LIBRARY_IMPORT_ONLY}",
        )
        self.assertFalse(blocks_new_implementation(ctx))
        self.assertEqual(ctx.contract_id, "StartupContext")

    def test_builds_authority_snapshot(self) -> None:
        ctx = _live_startup_context()

        self.assertIsNotNone(ctx.authority_snapshot)
        assert ctx.authority_snapshot is not None
        self.assertTrue(ctx.authority_snapshot.coordination_state)
        self.assertIn("authority_snapshot", ctx.to_dict())
        self.assertIsNotNone(ctx.current_session)
        assert ctx.current_session is not None
        if ctx.authority_snapshot.current_instruction_revision:
            self.assertEqual(
                ctx.authority_snapshot.current_instruction_revision,
                ctx.current_session.current_instruction_revision,
            )
        else:
            attention_indicators = {ctx.authority_snapshot.attention_status}
            if ctx.authority_snapshot.packet_target is not None:
                attention_indicators.add(
                    ctx.authority_snapshot.packet_target.attention_status
                )
            self.assertTrue(
                attention_indicators
                & {"review_needed", "checkpoint_required", "wake_required"},
                f"expected actionable attention, got {attention_indicators}",
            )
        self.assertEqual(
            ctx.authority_snapshot.implementer_ack_state,
            ctx.current_session.implementer_ack_state,
        )

    def test_collects_active_bypass_lifecycles_for_role(self) -> None:
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            store = repo_root / DEFAULT_BYPASS_LIFECYCLE_STORE_REL
            store.parent.mkdir(parents=True)
            lifecycle = evaluate_bypass_request(
                BypassRequest(
                    request_id="startup-bypass",
                    scope=BypassAuthorityScope.EDIT_ONLY,
                    reason="operator approved startup bypass",
                    actor="operator",
                    requested_at_utc="2026-05-12T16:10:00Z",
                    target_role="implementer",
                    target_surface="startup-context",
                    evidence_refs=("packet:rev_pkt_3847",),
                ),
                BypassEvaluationInput(
                    operator_signature="operator",
                    ai_approval_evidence="packet:rev_pkt_3847",
                    evaluated_at_utc="2026-05-12T16:10:01Z",
                ),
            )
            store.write_text(json.dumps(lifecycle.to_dict()) + "\n", encoding="utf-8")

            collected = _collect_active_bypass_lifecycles(
                repo_root=repo_root,
                role="implementer",
            )

        self.assertIn(lifecycle.lifecycle_id, {row.lifecycle_id for row in collected})

    def test_to_dict_compacts_bypass_lifecycle_projection(self) -> None:
        lifecycle = evaluate_bypass_request(
            BypassRequest(
                request_id="startup-bypass",
                scope=BypassAuthorityScope.EDIT_ONLY,
                reason="operator approved startup bypass with long details",
                actor="operator",
                requested_at_utc="2026-05-12T16:10:00Z",
                target_role="implementer",
                target_surface="startup-context",
                evidence_refs=(
                    "packet:rev_pkt_3847",
                    "packet:rev_pkt_3848",
                    "packet:rev_pkt_3849",
                    "packet:rev_pkt_3850",
                ),
            ),
            BypassEvaluationInput(
                operator_signature="operator",
                ai_approval_evidence="packet:rev_pkt_3847",
                evaluated_at_utc="2026-05-12T16:10:01Z",
            ),
        )

        payload = StartupContext(bypass_lifecycles=(lifecycle,)).to_dict()

        projected = payload["bypass_lifecycles"][0]
        self.assertEqual(projected["lifecycle_id"], lifecycle.lifecycle_id)
        self.assertEqual(projected["state"], lifecycle.state.value)
        self.assertEqual(projected["scope"], "edit_only")
        self.assertEqual(projected["target_role"], "implementer")
        self.assertEqual(projected["approved_scope"], "edit_only")
        self.assertEqual(projected["receipt_id"], lifecycle.receipt.receipt_id)
        self.assertIn("granted_at_utc", projected)
        self.assertNotIn("governed_exception", projected)
        self.assertNotIn("reason", projected)

    def test_startup_mode_fields_match_authority_snapshot(self) -> None:
        ctx = _live_startup_context()

        payload = ctx.to_dict()
        snapshot = payload["authority_snapshot"]
        reviewer_gate = payload["reviewer_gate"]

        self.assertEqual(payload["reviewer_mode"], snapshot["reviewer_mode"])
        self.assertEqual(payload["interaction_mode"], snapshot["interaction_mode"])
        self.assertEqual(
            reviewer_gate["reviewer_mode"],
            snapshot["gate_mode"] or snapshot["reviewer_mode"],
        )
        self.assertEqual(
            reviewer_gate["effective_reviewer_mode"],
            snapshot["effective_reviewer_mode"],
        )
        self.assertEqual(
            reviewer_gate["operator_interaction_mode"],
            snapshot["interaction_mode"],
        )

    def test_authority_snapshot_carries_surface_provenance(self) -> None:
        snapshot = build_authority_snapshot(
            {
                "snapshot_id": "snap-test",
                "zref": "zref_test_head",
                "source_identity": {
                    "generation_id": "gen-test",
                    "head_sha": "head-test",
                    "worktree_hash": "tree-test",
                },
                "source_contract": "ReviewState",
                "source_command": (
                    "python3 dev/scripts/devctl.py review-channel "
                    "--action status --terminal none --format json"
                ),
                "observed_fields": ["head_sha", "worktree_hash", "generation_id"],
                "inferred_fields": ["snapshot_id", "zref"],
                "coordination": {
                    "resync_required": False,
                    "current_slice": "producer provenance closure",
                },
                "reviewer_gate": {
                    "reviewer_mode": "single_agent",
                },
                "implementation_permission": "active",
            }
        )

        payload = snapshot.to_dict()

        self.assertEqual(payload["snapshot_id"], "snap-test")
        self.assertEqual(payload["zref"], "zref_test_head")
        self.assertEqual(payload["source_identity"]["generation_id"], "gen-test")
        self.assertEqual(payload["source_contract"], "ReviewState")
        self.assertEqual(
            payload["observed_fields"],
            ["head_sha", "worktree_hash", "generation_id"],
        )
        restored = authority_snapshot_from_mapping(payload)
        self.assertIsNotNone(restored)
        assert restored is not None
        self.assertEqual(restored.snapshot_id, "snap-test")
        self.assertEqual(restored.source_identity["worktree_hash"], "tree-test")

    def test_has_governance(self) -> None:
        ctx = _live_startup_context()
        self.assertIsNotNone(ctx.governance)
        self.assertTrue(ctx.governance.repo_identity.repo_name)

    def test_to_dict_exposes_key_surfaces(self) -> None:
        governance = replace(
            _minimal_governance(),
            doc_registry=DocRegistry(
                entries=(
                    DocRegistryEntry(
                        path="dev/guides/SYSTEM_MAP.md",
                        doc_class="guide",
                        authority="reference-only",
                        lifecycle="active",
                        scope="connectivity index",
                        artifact_role="connectivity_index",
                        authority_kind="generated_navigation",
                        system_scope="platform_core",
                        consumer_scope="startup_default",
                    ),
                )
            ),
        )
        ctx = StartupContext(
            governance=governance,
            key_surfaces=("dev/guides/SYSTEM_MAP.md",),
        )

        self.assertEqual(ctx.to_dict()["key_surfaces"], ["dev/guides/SYSTEM_MAP.md"])

    def test_to_dict_exposes_connectivity_registry_summary(self) -> None:
        from dev.scripts.devctl.platform.connectivity_registry import (
            build_connectivity_registry_summary,
        )

        summary = build_connectivity_registry_summary().to_dict()
        ctx = StartupContext(connectivity_registry=summary)
        payload = ctx.to_dict()

        self.assertEqual(
            payload["connectivity_registry"]["contract_id"],
            "ConnectivityRegistrySnapshot",
        )
        self.assertEqual(
            payload["connectivity_registry"]["source_contract_count"],
            summary["source_contract_count"],
        )
        self.assertEqual(
            payload["connectivity_registry"]["zero_reader_field_count"],
            0,
        )
        self.assertEqual(
            payload["connectivity_registry"]["aspirational_gap_count"],
            0,
        )
        self.assertIn(
            "startup_context",
            payload["connectivity_registry"]["reader_ids"],
        )

    def test_to_dict_exposes_runtime_spine_and_packet_carry_forward(self) -> None:
        ctx = StartupContext(
            runtime_spine_closure={
                "contract_id": "RuntimeSpineClosureState",
                "ok": False,
                "risky_item_count": 8,
            },
            packet_continuity_index={
                "contract_id": "PacketContinuityIndex",
                "sink_counts": {"live_queue": 1},
            },
            packet_carry_forward_debt=(
                {
                    "contract_id": "PacketCarryForwardDebt",
                    "packet_id": "rev_pkt_2649",
                    "reason": "acked_without_terminal_or_durable_owner",
                },
            ),
            continuity_attention={
                "contract_id": "StartupContinuityAttention",
                "requires_attention": True,
                "packet_debt_count": 1,
            },
        )
        payload = ctx.to_dict()

        self.assertEqual(
            payload["runtime_spine_closure"]["contract_id"],
            "RuntimeSpineClosureState",
        )
        self.assertEqual(
            payload["packet_carry_forward_debt"][0]["packet_id"],
            "rev_pkt_2649",
        )
        self.assertEqual(
            payload["packet_continuity_index"]["contract_id"],
            "PacketContinuityIndex",
        )
        self.assertEqual(
            payload["continuity_attention"]["contract_id"],
            "StartupContinuityAttention",
        )

    def test_startup_connectivity_registry_projects_contract_ids(self) -> None:
        from dev.scripts.devctl.config import REPO_ROOT
        from dev.scripts.devctl.runtime.startup_connectivity_registry import (
            startup_connectivity_registry,
        )

        registry = startup_connectivity_registry(REPO_ROOT)

        self.assertEqual(registry["aspirational_gap_count"], 0)
        self.assertIn("TypedAction", registry["connected_contract_ids"])

    def test_startup_connectivity_registry_skips_ast_reader_verification_by_default(
        self,
    ) -> None:
        from dev.scripts.devctl.config import REPO_ROOT
        from dev.scripts.devctl.runtime import startup_connectivity_registry as module

        with patch.object(
            module,
            "find_missing_connection_findings",
            side_effect=AssertionError("startup must not run AST reader verification"),
        ):
            registry = module.startup_connectivity_registry(REPO_ROOT)

        self.assertEqual(registry["missing_connection_finding_count"], 0)

    def test_authority_snapshot_prefers_recovery_authority_over_startup_routing(
        self,
    ) -> None:
        snapshot = build_authority_snapshot(
            {
                "next_command": (
                    "python3 dev/scripts/devctl.py review-channel "
                    "--action status --terminal none --format json"
                ),
                "control_recovery_action": "coordination_resync",
                "implementation_permission": "active",
                "coordination": {
                    "resync_required": True,
                    "current_slice": "dogfood authority fix",
                    "active_target": {
                        "plan_path": "dev/active/ai_governance_platform.md",
                    },
                },
                "current_session": {
                    "current_instruction_revision": "rev123",
                    "implementer_ack_state": "stale",
                },
                "reviewer_gate": {
                    "reviewer_mode": "single_agent",
                },
                "attention": {
                    "status": "checkpoint_required",
                    "recommended_action": "checkpoint_before_continue",
                    "recommended_command": (
                        'python3 dev/scripts/devctl.py commit -m "checkpoint"'
                    ),
                    "summary": "Checkpoint required before more edits.",
                },
                "recovery_authority": {
                    "decision_action_id": "cut_checkpoint",
                    "command": 'python3 dev/scripts/devctl.py commit -m "checkpoint"',
                },
            }
        )

        self.assertEqual(snapshot.required_action, "cut_checkpoint")
        self.assertEqual(
            snapshot.next_command,
            'python3 dev/scripts/devctl.py commit -m "checkpoint"',
        )

    def test_authority_snapshot_checkpoint_preempts_runtime_relaunch(self) -> None:
        snapshot = build_authority_snapshot(
            {
                "next_command": (
                    'python3 dev/scripts/devctl.py commit -m "<descriptive message>"'
                ),
                "advisory_action": "checkpoint_before_continue",
                "advisory_reason": "staged_index_budget_exceeded",
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": True,
                        "safe_to_continue_editing": False,
                        "checkpoint_reason": "staged_index_budget_exceeded",
                    }
                },
                "push_decision": {"action": "await_checkpoint"},
                "coordination": {"resync_required": True},
                "current_session": {
                    "current_instruction_revision": "rev123",
                    "implementer_ack_state": "missing",
                },
                "reviewer_gate": {"reviewer_mode": "active_dual_agent"},
                "attention": {
                    "status": "reviewer_heartbeat_stale",
                    "summary": "Reviewer heartbeat is stale.",
                },
                "recovery_authority": {
                    "decision_action_id": "relaunch_review_loop",
                    "command": (
                        "python3 dev/scripts/devctl.py review-channel --action launch"
                    ),
                },
            }
        )

        self.assertEqual(snapshot.required_action, "cut_checkpoint")
        self.assertEqual(
            snapshot.next_command,
            'python3 dev/scripts/devctl.py commit -m "<descriptive message>"',
        )

    def test_authority_snapshot_ignores_shared_instruction_without_codex_packet(
        self,
    ) -> None:
        shared_instruction = "Priority action_request: Dogfood split-authority current-slice contradiction"
        snapshot = build_authority_snapshot(
            {
                "coordination": {
                    "resync_required": False,
                    "current_slice": shared_instruction,
                    "active_target": {
                        "plan_path": "dev/active/ai_governance_platform.md",
                    },
                },
                "current_session": {
                    "current_instruction": shared_instruction,
                    "current_instruction_revision": "rev123",
                    "implementer_ack_state": "missing",
                },
                "packet_inbox": {
                    "agents": [
                        {
                            "agent": "codex",
                            "current_instruction_packet_id": "",
                            "pending_actionable_packet_ids": [],
                            "expired_unresolved_packet_ids": ["rev_pkt_0502"],
                            "attention_status": "review_needed",
                            "wake_reason": "expired_unresolved_packet",
                        },
                        {
                            "agent": "claude",
                            "current_instruction_packet_id": "rev_pkt_0523",
                            "pending_actionable_packet_ids": ["rev_pkt_0523"],
                            "expired_unresolved_packet_ids": [],
                            "attention_status": "wake_required",
                            "wake_reason": "action_request_pending",
                        },
                    ],
                },
                "reviewer_gate": {
                    "reviewer_mode": "single_agent",
                },
                "implementation_permission": "active",
                "attention": {
                    "status": "review_needed",
                    "summary": "Expired unresolved review packet remains visible.",
                },
            }
        )

        self.assertEqual(snapshot.current_slice, "")
        self.assertEqual(snapshot.current_instruction_revision, "")
        self.assertEqual(snapshot.implementer_ack_state, "missing")

    def test_authority_snapshot_keeps_packet_derived_instruction(
        self,
    ) -> None:
        shared_instruction = "Priority action_request: Dogfood split-authority current-slice contradiction"
        snapshot = build_authority_snapshot(
            {
                "coordination": {
                    "resync_required": False,
                    "current_slice": shared_instruction,
                    "active_target": {
                        "plan_path": "dev/active/ai_governance_platform.md",
                    },
                },
                "current_session": {
                    "current_instruction": shared_instruction,
                    "current_instruction_revision": "rev123",
                    "implementer_ack_state": "missing",
                },
                "queue": {
                    "derived_next_instruction": shared_instruction,
                    "derived_next_instruction_source": {
                        "packet_id": "rev_pkt_0523",
                        "packet_class": "action_request",
                    },
                },
                "packet_inbox": {
                    "agents": [
                        {
                            "agent": "codex",
                            "current_instruction_packet_id": "",
                            "pending_actionable_packet_ids": [],
                            "expired_unresolved_packet_ids": ["rev_pkt_0502"],
                            "attention_status": "review_needed",
                            "wake_reason": "expired_unresolved_packet",
                        },
                        {
                            "agent": "claude",
                            "current_instruction_packet_id": "rev_pkt_0523",
                            "pending_actionable_packet_ids": ["rev_pkt_0523"],
                            "expired_unresolved_packet_ids": [],
                            "attention_status": "wake_required",
                            "wake_reason": "action_request_pending",
                        },
                    ],
                },
                "reviewer_gate": {
                    "reviewer_mode": "single_agent",
                },
                "implementation_permission": "active",
                "attention": {
                    "status": "review_needed",
                    "summary": "Expired unresolved review packet remains visible.",
                },
            }
        )

        self.assertEqual(snapshot.current_slice, shared_instruction)
        self.assertEqual(snapshot.current_instruction_revision, "rev123")
        self.assertEqual(snapshot.implementer_ack_state, "missing")

    def test_authority_snapshot_uses_typed_reviewer_provider_for_packet_clear(
        self,
    ) -> None:
        shared_instruction = "Cursor reviewer owns the instruction state"
        snapshot = build_authority_snapshot(
            {
                "collaboration": {
                    "review_agent": "cursor",
                    "role_assignments": (),
                },
                "coordination": {
                    "resync_required": False,
                    "current_slice": shared_instruction,
                },
                "current_session": {
                    "current_instruction": shared_instruction,
                    "current_instruction_revision": "rev-cursor",
                    "implementer_ack_state": "current",
                },
                "packet_inbox": {
                    "agents": [
                        {
                            "agent": "cursor",
                            "current_instruction_packet_id": "rev_pkt_cursor_instruction",
                            "pending_actionable_total": 1,
                            "expired_unresolved_total": 0,
                            "attention_status": "wake_required",
                            "wake_reason": "instruction_pending",
                        },
                        {
                            "agent": "codex",
                            "current_instruction_packet_id": "",
                            "pending_actionable_total": 0,
                            "expired_unresolved_total": 0,
                            "attention_status": "none",
                            "wake_reason": "",
                        },
                    ],
                },
                "reviewer_gate": {
                    "reviewer_mode": "single_agent",
                },
                "implementation_permission": "active",
            }
        )

        self.assertEqual(snapshot.current_instruction_revision, "rev-cursor")
        self.assertEqual(snapshot.implementer_ack_state, "current")
        self.assertEqual(snapshot.current_slice, shared_instruction)

    def test_summary_next_command_prefers_cut_checkpoint_recovery_command(self) -> None:
        payload = {
            "startup_authority": {"ok": False},
            "governance": {
                "push_enforcement": {
                    "checkpoint_required": True,
                    "safe_to_continue_editing": False,
                }
            },
            "implementation_permission": "blocked",
            "recovery_authority": {
                "decision_action_id": "cut_checkpoint",
                "command": 'python3 dev/scripts/devctl.py commit -m "checkpoint"',
            },
        }

        self.assertEqual(
            summary_next_command(payload),
            'python3 dev/scripts/devctl.py commit -m "checkpoint"',
        )

    def test_summary_next_command_checkpoint_beats_coordination_resync(self) -> None:
        payload = {
            "startup_authority": {"ok": False},
            "governance": {
                "push_enforcement": {
                    "checkpoint_required": True,
                    "safe_to_continue_editing": False,
                }
            },
            "coordination": {"resync_required": True},
            "push_decision": {"action": "await_checkpoint"},
            "implementation_permission": "active",
            "current_session": {
                "current_instruction_revision": "rev123",
                "implementer_ack_state": "missing",
            },
        }

        self.assertEqual(
            summary_next_command(payload),
            'python3 dev/scripts/devctl.py commit -m "<descriptive message>"',
        )

    def test_summary_next_command_prefers_governed_push_when_push_ready(self) -> None:
        payload = {
            "startup_authority": {"ok": True},
            "governance": {
                "push_enforcement": {
                    "checkpoint_required": False,
                    "safe_to_continue_editing": True,
                }
            },
            "push_decision": {
                "action": "run_devctl_push",
                "next_step_command": "python3 dev/scripts/devctl.py push --execute",
            },
        }

        self.assertEqual(
            summary_next_command(payload),
            "python3 dev/scripts/devctl.py push --execute",
        )

    def test_authority_snapshot_clears_missing_instruction_placeholder_revision(
        self,
    ) -> None:
        snapshot = build_authority_snapshot(
            {
                "coordination": {
                    "resync_required": False,
                },
                "current_session": {
                    "current_instruction": "(missing)",
                    "current_instruction_revision": "rev123",
                    "implementer_ack_state": "stale",
                },
                "reviewer_gate": {
                    "reviewer_mode": "active_dual_agent",
                },
                "implementation_permission": "active",
            }
        )

        self.assertEqual(snapshot.current_instruction_revision, "")
        self.assertEqual(snapshot.current_slice, "")
        self.assertNotEqual(snapshot.coordination_state, "handshake_stale")

    def test_authority_snapshot_carries_actor_role_identity_and_allowed_actions(
        self,
    ) -> None:
        snapshot = build_authority_snapshot(
            {
                "collaboration": {
                    "mutation_owner": "claude",
                    "verification_owner": "codex",
                    "verification_status": "live",
                    "watcher_owner": "claude",
                    "watcher_status": "live",
                    "actor_authorities": [
                        {
                            "actor_id": "codex",
                            "provider": "codex",
                            "role": "reviewer",
                            "live": True,
                            "status": "live",
                            "source": "test",
                            "grants": [
                                {
                                    "capability": "review.checkpoint",
                                    "granted": True,
                                    "source": "test",
                                }
                            ],
                        },
                        {
                            "actor_id": "claude",
                            "provider": "claude",
                            "role": "implementer",
                            "live": True,
                            "status": "live",
                            "source": "test",
                            "grants": [
                                {
                                    "capability": "repo.commit",
                                    "granted": True,
                                    "source": "test",
                                }
                            ],
                        },
                    ],
                },
                "coordination": {
                    "actors": [
                        {
                            "actor_id": "codex",
                            "provider": "codex",
                            "role": "reviewer",
                            "presence": "live",
                        },
                        {
                            "actor_id": "claude",
                            "provider": "claude",
                            "role": "implementer",
                            "presence": "live",
                        },
                    ],
                },
            },
            next_command="python3 dev/scripts/devctl.py review-channel --action status",
            caller_role="reviewer",
        )

        self.assertEqual(snapshot.actor_role, "reviewer")
        self.assertEqual(snapshot.actor_identity, "codex")
        self.assertIn("review-channel.status", snapshot.allowed_actions)
        self.assertIn("review.checkpoint", snapshot.allowed_actions)
        self.assertIn("implementation.edit", snapshot.blocked_actions)
        self.assertEqual(snapshot.mutation_owner, "claude")
        self.assertEqual(snapshot.verification_owner, "codex")
        self.assertEqual(snapshot.verification_status, "live")
        self.assertEqual(snapshot.watcher_owner, "claude")
        self.assertEqual(snapshot.watcher_status, "live")
        self.assertIn("review.checkpoint", snapshot.actor_capabilities)
        self.assertEqual(snapshot.actor_authorities[1].actor_id, "claude")
        self.assertEqual(
            snapshot.to_dict()["actor_authorities"][1]["grants"][0]["capability"],
            "repo.commit",
        )

    def test_has_reviewer_gate(self) -> None:
        ctx = _live_startup_context()
        self.assertIsInstance(ctx.reviewer_gate, ReviewerGateState)

    def test_to_dict_emits_recovery_authority_fields(self) -> None:
        ctx = StartupContext(
            recovery_authority=RecoveryAuthorityState(
                recovery_action="relaunch_allowed",
                recovery_basis="process_dead",
                recovery_scope="entire_lane",
                decision_action_id="relaunch_review_loop",
                diagnosis_status="review_loop_relaunch_required",
            ),
        )

        payload = ctx.to_dict()

        self.assertEqual(payload["recovery_action"], "relaunch_allowed")
        self.assertEqual(payload["recovery_basis"], "process_dead")
        self.assertEqual(payload["recovery_scope"], "entire_lane")
        self.assertEqual(
            payload["recovery_authority"]["decision_action_id"],
            "relaunch_review_loop",
        )

    def test_recovery_authority_allows_relaunch_only_with_dead_process_basis(
        self,
    ) -> None:
        review_state = SimpleNamespace(
            recovery_assessment=SimpleNamespace(
                diagnosis=SimpleNamespace(
                    status="review_loop_relaunch_required",
                    root_cause="review loop process is gone",
                    supporting_causes=("reviewer_conductor_inactive",),
                    evidence=(),
                ),
                decision=SimpleNamespace(
                    action_id="relaunch_review_loop",
                    command="python3 dev/scripts/devctl.py review-channel --action launch",
                    rationale="relaunch reviewer loop",
                ),
            )
        )

        authority = derive_recovery_authority(review_state)

        self.assertEqual(authority.recovery_action, "relaunch_allowed")
        self.assertEqual(authority.recovery_basis, "process_dead")
        self.assertEqual(authority.recovery_scope, "entire_lane")

    def test_recovery_authority_keeps_relaunch_observe_only_without_proof(self) -> None:
        review_state = SimpleNamespace(
            recovery_assessment=SimpleNamespace(
                diagnosis=SimpleNamespace(
                    status="review_loop_relaunch_required",
                    root_cause="output stream quiet",
                    supporting_causes=("output_silence",),
                    evidence=(),
                ),
                decision=SimpleNamespace(
                    action_id="relaunch_review_loop",
                    command="python3 dev/scripts/devctl.py review-channel --action launch",
                    rationale="relaunch reviewer loop",
                ),
            )
        )

        authority = derive_recovery_authority(review_state)

        self.assertEqual(authority.recovery_action, "observe_only")
        self.assertEqual(authority.recovery_basis, "none")
        self.assertEqual(authority.recovery_scope, "entire_lane")

    def test_has_push_decision(self) -> None:
        ctx = _live_startup_context()
        self.assertTrue(ctx.push_decision.action)

    def test_has_advisory_action(self) -> None:
        ctx = _live_startup_context()
        self.assertIn(
            ctx.advisory_action,
            (
                "continue_editing",
                "await_review",
                "checkpoint_before_continue",
                "checkpoint_allowed",
                "repair_reviewer_loop",
                "push_allowed",
                "no_push_needed",
            ),
        )
        self.assertTrue(ctx.advisory_reason)

    def test_has_work_intake(self) -> None:
        ctx = _live_startup_context()
        self.assertIsNotNone(ctx.work_intake)
        self.assertTrue(ctx.work_intake.contract_id)

    def test_projects_implementation_permission_from_control_topology_truth(
        self,
    ) -> None:
        fake_coordination = SimpleNamespace(
            implementation_permission="active",
            to_dict=lambda: {"implementation_permission": "active"},
        )
        fake_work_intake = SimpleNamespace(
            coordination=fake_coordination,
            to_dict=lambda: {"coordination": {"implementation_permission": "active"}},
        )
        with (
            patch(
                "dev.scripts.devctl.runtime.startup_context.build_work_intake_packet",
                return_value=fake_work_intake,
            ),
            patch(
                "dev.scripts.devctl.runtime.startup_context.build_work_intake_ownership_state",
                return_value=SimpleNamespace(concurrent_writer_detected=False),
            ),
            patch(
                "dev.scripts.devctl.runtime.startup_context.build_work_intake_coordination_state",
                return_value=SimpleNamespace(
                    implementation_permission="active",
                    concurrent_writer_conflict_detected=False,
                ),
            ),
            patch(
                "dev.scripts.devctl.runtime.startup_context._load_startup_coordination_snapshot",
                return_value=None,
            ),
            patch(
                "dev.scripts.devctl.runtime.startup_context.load_startup_quality_signals",
                return_value={},
            ),
            patch(
                "dev.scripts.devctl.runtime.startup_context.derive_startup_blocker",
                return_value=BlockerSnapshot(
                    top_blocker="none",
                    next_action="continue editing",
                    blocker_source="none",
                    derivation_evidence=(),
                ),
            ),
            patch(
                "dev.scripts.devctl.runtime.startup_context.build_surface_snapshot_id",
                return_value="snap-test",
            ),
            patch(
                "dev.scripts.devctl.runtime.startup_context.derive_startup_control_truth",
                return_value=("no_live_agents", "blocked"),
            ),
        ):
            ctx = build_startup_context()

        self.assertEqual(ctx.observed_control_topology, "no_live_agents")
        self.assertEqual(ctx.implementation_permission, "blocked")

    def test_has_quality_signals_dict(self) -> None:
        ctx = _live_startup_context()
        self.assertIsInstance(ctx.quality_signals, dict)

    def test_has_contract_ownership_map(self) -> None:
        ctx = _live_startup_context()
        self.assertIn("ReviewState", ctx.contract_ownership_map)
        review_state = ctx.contract_ownership_map["ReviewState"]
        self.assertIn("snapshot_id", review_state["startup_surface_tokens"])
        self.assertEqual(
            review_state["startup_surface_token_count"],
            len(review_state["startup_surface_tokens"]),
        )
        self.assertGreater(review_state["startup_surface_token_count"], 1)

    def test_has_snapshot_id(self) -> None:
        ctx = _live_startup_context()
        self.assertTrue(ctx.snapshot_id)
        self.assertEqual(ctx.push_decision.snapshot_id, ctx.snapshot_id)
        self.assertTrue(ctx.zref)
        self.assertEqual(ctx.push_decision.zref, ctx.zref)

    def test_to_dict_serializes(self) -> None:
        ctx = _live_startup_context()
        d = ctx.to_dict()
        self.assertIn("advisory_action", d)
        self.assertIn("reviewer_gate", d)
        self.assertIn("push_decision", d)
        self.assertIn("governance", d)
        self.assertIn("work_intake", d)
        self.assertIn("quality_signals", d)
        self.assertIn("rule_summary", d)
        self.assertIn("match_evidence", d)
        self.assertIn("rejected_rule_traces", d)
        self.assertIn("contract_ownership_map", d)
        review_state = d["contract_ownership_map"]["ReviewState"]
        self.assertGreaterEqual(
            review_state["startup_surface_token_count"],
            len(review_state["startup_surface_tokens"]),
        )
        self.assertLessEqual(len(review_state["startup_surface_tokens"]), 2)
        self.assertIn("snapshot_id", review_state["startup_surface_tokens"])
        self.assertIn("snapshot_id", d)
        self.assertIn("observed_control_topology", d)
        self.assertIn("implementation_permission", d)

    def test_to_dict_serializes_remote_control_attachment(self) -> None:
        ctx = StartupContext(
            remote_control_attachment=RemoteControlAttachmentState(
                provider="claude",
                role="implementer",
                attachment_id="remote-attach-1",
                session_name="VoiceTerm Bridge Loop",
                remote_session_id="session_abc123",
                session_url="https://claude.ai/code/session_abc123",
                status="attached",
                metadata_path="dev/review_status/sessions/claude-remote-control.json",
            )
        )
        payload = ctx.to_dict()
        self.assertIn("remote_control_attachment", payload)
        self.assertEqual(
            payload["remote_control_attachment"]["remote_session_id"],
            "session_abc123",
        )

    def test_to_dict_serializes_startup_aliases_and_reviewer_runtime(self) -> None:
        ctx = StartupContext(
            advisory_action="checkpoint_before_continue",
            advisory_reason="dirty_path_budget_exceeded",
            reviewer_gate=ReviewerGateState(operator_interaction_mode="remote_control"),
            reviewer_runtime=ReviewerRuntimeContract(
                conductor_visibility="none",
                session_owner=ReviewerSessionOwnerState(
                    provider="codex",
                    session_name="codex-review",
                    session_pid=42,
                    session_visibility="headless",
                ),
            ),
        )

        payload = ctx.to_dict()

        self.assertEqual(payload["action"], "checkpoint_before_continue")
        self.assertEqual(payload["reason"], "dirty_path_budget_exceeded")
        self.assertEqual(payload["interaction_mode"], "remote_control")
        self.assertEqual(payload["reviewer_runtime"]["conductor_visibility"], "none")
        self.assertEqual(
            payload["reviewer_runtime"]["session_owner"]["session_visibility"],
            "headless",
        )
        self.assertEqual(
            payload["reviewer_runtime"]["session_owner"]["session_pid"],
            42,
        )

    def test_to_dict_prefers_runtime_truth_interaction_mode(self) -> None:
        ctx = StartupContext(
            reviewer_gate=ReviewerGateState(operator_interaction_mode="single_agent"),
            session_posture=SessionPosture(interaction_mode="unresolved"),
            runtime_truth=RuntimeTruthSnapshot(
                interaction_mode="remote_control",
                remote_control_active=True,
                remote_control_method="claude_session_state_bridge",
                remote_control_session_id="session_abc123",
            ),
        )

        payload = ctx.to_dict()

        self.assertEqual(payload["interaction_mode"], "remote_control")
        self.assertEqual(
            payload["runtime_truth"]["remote_control_method"],
            "claude_session_state_bridge",
        )

    def test_slim_token_budget(self) -> None:
        ctx = _live_startup_context()
        size = len(json.dumps(ctx.to_dict()))
        tokens = size // 4
        self.assertLess(tokens, 10000, f"startup context too large: {tokens} tokens")

    @patch("dev.scripts.devctl.runtime.startup_review_state.load_current_review_state")
    def test_load_startup_review_state_threads_review_status_dir(
        self,
        load_current_review_state,
    ) -> None:
        sentinel = object()
        load_current_review_state.return_value = sentinel

        repo_root = Path("/tmp/repo")
        review_status_dir = Path("dev/reports/custom-review")
        result = _load_startup_review_state(
            repo_root,
            governance=None,
            review_state=None,
            review_status_dir=review_status_dir,
        )

        load_current_review_state.assert_called_once_with(
            repo_root,
            governance=None,
            review_status_dir=review_status_dir,
            prefer_cached_projection=True,
            allow_live_refresh=False,
        )
        self.assertIs(result, sentinel)

    @patch("dev.scripts.devctl.runtime.startup_review_state.load_current_review_state")
    def test_load_startup_review_state_prefers_frozen_review_state(
        self,
        load_current_review_state,
    ) -> None:
        frozen = object()
        result = _load_startup_review_state(
            Path("/tmp/repo"),
            governance=None,
            review_state=frozen,
            review_status_dir=Path("ignored"),
        )

        load_current_review_state.assert_not_called()
        self.assertIs(result, frozen)


class TestCoordinationParityF1(unittest.TestCase):
    """F1 / MP-384 / MP-387: startup-context, session-resume, and dashboard
    must return identical coordination fields from one governed state.

    Before the ``coordination_loader`` wiring each surface built its own
    coordination snapshot via a distinct helper — ``build_startup_context``
    used the gate-aware ``build_work_intake_coordination_state`` reducer,
    while ``session_resume`` and ``ControlPlaneReadModel`` echoed the
    persisted ``coordination`` mapping on disk. The three surfaces could
    disagree on ``declared_topology``, ``observed_topology``,
    ``recommended_topology``, ``ownership_status``, and ``resync_reasons``
    for the same repo tick. MP-384 fixes that by routing every read
    surface through one shared loader; this test locks the parity in so a
    future refactor cannot silently regress it.
    """

    def test_three_surfaces_report_identical_coordination(self) -> None:
        from dev.scripts.devctl.commands.governance.session_resume_support import (
            build_from_sources,
            current_head,
        )
        from dev.scripts.devctl.config import get_repo_root
        from dev.scripts.devctl.governance.draft import scan_repo_governance
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModelOptions,
            build_control_plane_read_model,
        )
        from dev.scripts.devctl.runtime.review_state_locator import (
            load_current_review_state,
        )

        repo = get_repo_root()
        governance = scan_repo_governance(repo)
        head_sha = current_head(repo)

        # One frozen (governance, review_state) per proof tick: resolve the
        # typed review state ONCE and thread it through all three surfaces so
        # the parity check exercises reducer behaviour under identical inputs
        # instead of racing independent bridge-refreshed reloads of
        # review_state.json that can desync observed_topology and
        # resync_reasons between calls. Before this thread, each surface
        # triggered its own ``load_current_review_state_payload`` and the
        # three could silently diverge whenever ``bridge.md`` was reprojected
        # mid-test.
        review_state = load_current_review_state(repo, governance=governance)

        startup = build_startup_context(
            repo_root=repo,
            governance=governance,
            review_state=review_state,
        )
        dashboard = build_control_plane_read_model(
            repo,
            options=ControlPlaneReadModelOptions(
                governance=governance,
                review_state=review_state,
            ),
        )
        session = build_from_sources(
            repo,
            role="reviewer",
            head_sha=head_sha,
            governance=governance,
            review_state=review_state,
        )

        startup_c = startup.coordination
        dashboard_c = dashboard.coordination
        session_c = session.coordination

        self.assertIsNotNone(
            startup_c,
            "startup-context must carry a coordination snapshot",
        )
        self.assertIsNotNone(
            dashboard_c,
            "dashboard must carry a coordination snapshot",
        )
        self.assertIsNotNone(
            session_c,
            "session-resume must carry a coordination snapshot",
        )
        self.assertIsNotNone(
            startup_c.active_target,
            "startup-context must carry an active target in the coordination snapshot",
        )
        self.assertIsNotNone(
            dashboard_c.active_target,
            "dashboard must carry an active target in the coordination snapshot",
        )
        self.assertIsNotNone(
            session_c.active_target,
            "session-resume must carry an active target in the coordination snapshot",
        )

        parity_fields = (
            "declared_topology",
            "observed_topology",
            "recommended_topology",
            "ownership_status",
            "current_slice",
            "fanout_posture",
            "safe_to_fanout",
            "resync_required",
        )
        for field_name in parity_fields:
            startup_value = getattr(startup_c, field_name)
            dashboard_value = getattr(dashboard_c, field_name)
            session_value = getattr(session_c, field_name)
            self.assertEqual(
                startup_value,
                dashboard_value,
                f"F1 parity: startup-context vs dashboard disagree on {field_name}",
            )
            self.assertEqual(
                startup_value,
                session_value,
                f"F1 parity: startup-context vs session-resume disagree on {field_name}",
            )

        self.assertEqual(
            tuple(startup_c.resync_reasons),
            tuple(dashboard_c.resync_reasons),
            "F1 parity: startup-context vs dashboard disagree on resync_reasons",
        )
        self.assertEqual(
            tuple(startup_c.resync_reasons),
            tuple(session_c.resync_reasons),
            "F1 parity: startup-context vs session-resume disagree on resync_reasons",
        )
        self.assertEqual(
            startup_c.active_target.plan_path,
            dashboard_c.active_target.plan_path,
            "F1 parity: startup-context vs dashboard disagree on active_target.plan_path",
        )
        self.assertEqual(
            startup_c.active_target.plan_path,
            session_c.active_target.plan_path,
            "F1 parity: startup-context vs session-resume disagree on active_target.plan_path",
        )


class TestCLIRegistration(unittest.TestCase):
    """Verify startup-context is wired into the CLI."""

    def test_parser_accepts_startup_context(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["startup-context", "--format", "json"])
        self.assertEqual(args.command, "startup-context")

    def test_parser_accepts_summary_output(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["startup-context", "--format", "summary"])
        self.assertEqual(args.command, "startup-context")
        self.assertEqual(args.format, "summary")

    def test_parser_accepts_defer_publication(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["startup-context", "--defer-publication", "--format", "summary"]
        )
        self.assertEqual(args.command, "startup-context")
        self.assertTrue(args.defer_publication)

    def test_auto_defer_publication_when_implementer_hits_failed_push_loop(
        self,
    ) -> None:
        ctx = SimpleNamespace(
            governance=_minimal_governance(
                checkpoint_required=False,
                safe_to_continue_editing=True,
                worktree_dirty=False,
                dirty_path_count=0,
                untracked_path_count=0,
                staged_path_count=0,
                pending_publication_commits=22,
                latest_push_report_status="blocked",
                latest_push_report_reason="validation_failed",
            ),
            push_decision=SimpleNamespace(
                action="run_devctl_push",
                publication_backlog=SimpleNamespace(
                    pending_publication_commits=22,
                    backlog_urgent=True,
                ),
            ),
        )

        self.assertTrue(
            auto_defer_publication_for_development(
                ctx=ctx,
                caller_role="implementer",
            )
        )

    def test_auto_defer_publication_when_worktree_dirty_blocks_only_publication(
        self,
    ) -> None:
        ctx = SimpleNamespace(
            observed_control_topology="implementer_without_reviewer",
            reviewer_gate=ReviewerGateState(
                reviewer_mode="tools_only",
                effective_reviewer_mode="tools_only",
            ),
            governance=_minimal_governance(
                checkpoint_required=False,
                safe_to_continue_editing=True,
                worktree_dirty=True,
                worktree_clean=False,
                dirty_path_count=7,
                unstaged_path_count=7,
                untracked_path_count=0,
                staged_path_count=0,
                pending_publication_commits=22,
                latest_push_report_status="blocked",
                latest_push_report_reason="validation_failed",
            ),
            push_decision=SimpleNamespace(
                action="await_checkpoint",
                reason="worktree_dirty",
                publication_backlog=SimpleNamespace(
                    pending_publication_commits=22,
                    backlog_urgent=True,
                ),
            ),
        )

        self.assertTrue(
            auto_defer_publication_for_development(
                ctx=ctx,
                caller_role="implementer",
            )
        )

    def test_auto_defer_publication_does_not_apply_to_staged_index(
        self,
    ) -> None:
        ctx = SimpleNamespace(
            observed_control_topology="implementer_without_reviewer",
            reviewer_gate=ReviewerGateState(
                reviewer_mode="tools_only",
                effective_reviewer_mode="tools_only",
            ),
            governance=_minimal_governance(
                checkpoint_required=False,
                safe_to_continue_editing=True,
                worktree_dirty=True,
                worktree_clean=False,
                dirty_path_count=2,
                unstaged_path_count=1,
                staged_path_count=1,
                pending_publication_commits=22,
                latest_push_report_status="blocked",
            ),
            push_decision=SimpleNamespace(
                action="await_checkpoint",
                reason="worktree_dirty",
                publication_backlog=SimpleNamespace(
                    pending_publication_commits=22,
                    backlog_urgent=True,
                ),
            ),
        )

        self.assertFalse(
            auto_defer_publication_for_development(
                ctx=ctx,
                caller_role="implementer",
            )
        )

    def test_auto_defer_publication_does_not_apply_to_checkpoint_pressure(
        self,
    ) -> None:
        ctx = SimpleNamespace(
            governance=_minimal_governance(
                checkpoint_required=True,
                safe_to_continue_editing=False,
                checkpoint_reason="review_loop_relaunch_required",
                pending_publication_commits=22,
                latest_push_report_status="blocked",
            ),
            push_decision=SimpleNamespace(
                action="run_devctl_push",
                publication_backlog=SimpleNamespace(
                    pending_publication_commits=22,
                    backlog_urgent=True,
                ),
            ),
        )

        self.assertFalse(
            auto_defer_publication_for_development(
                ctx=ctx,
                caller_role="implementer",
            )
        )

    def test_handler_registered(self) -> None:
        self.assertIn("startup-context", COMMAND_HANDLERS)

    def test_in_listing(self) -> None:
        self.assertIn("startup-context", COMMANDS)

    def test_markdown_renders_configured_memory_roots(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "clean_worktree",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                    "memory_roots": {
                        "memory_root": ".claude/memory",
                        "context_store_root": "dev/context",
                    },
                },
            }
        )

        self.assertIn("## Continuity Roots", rendered)
        self.assertIn("`.claude/memory`", rendered)
        self.assertIn("`dev/context`", rendered)

    def test_checkpoint_blocker_projects_edit_only_operator_override_hint(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "checkpoint_before_continue",
                "advisory_reason": "staged_index_budget_exceeded",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                },
                "push_decision": {
                    "action": "await_checkpoint",
                    "reason": "staged_index_budget_exceeded",
                },
                "blocker": {
                    "top_blocker": (
                        "startup authority: staged_index_budget_exceeded"
                    ),
                },
            }
        )

        self.assertIn("## Typed Bypass Capabilities", rendered)
        self.assertIn("--operator-override", rendered)
        self.assertIn("--override-scope edit-only", rendered)
        self.assertIn("BypassReceipt", rendered)
        self.assertIn("GovernedExceptionLifecycle", rendered)

    def test_markdown_renders_quality_signals(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "clean_worktree",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                },
                "quality_signals": {
                    "probe_report": {
                        "generated_at": "2026-03-23T00:00:00Z",
                        "risk_hints": 81,
                        "files_with_hints": 14,
                    },
                    "governance_review": {
                        "generated_at_utc": "2026-03-23T00:00:00Z",
                        "total_findings": 95,
                        "open_finding_count": 19,
                        "fixed_count": 62,
                        "cleanup_rate_pct": 65.26,
                    },
                },
            }
        )

        self.assertIn("## Quality Signals", rendered)
        self.assertIn("**probe-report**", rendered)
        self.assertIn("**governance-review**", rendered)

    def test_markdown_renders_continuity_attention(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "clean_worktree",
                "agent_lane": "implementer",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                },
                "continuity_attention": {
                    "contract_id": "StartupContinuityAttention",
                    "message": "After compaction, read typed state before acting.",
                    "requires_attention": True,
                    "runtime_spine_ok": False,
                    "runtime_spine_risky_item_count": 2,
                    "runtime_spine_violation_count": 1,
                    "packet_debt_count": 1,
                    "packet_debt_ids": ["rev_pkt_2649"],
                },
            }
        )

        self.assertIn("### Continuity Attention", rendered)
        self.assertIn("rev_pkt_2649", rendered)
        self.assertIn("session-resume --role implementer --format bootstrap", rendered)

    def test_markdown_renders_work_intake(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "clean_worktree",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                },
                "work_intake": {
                    "confidence": "high",
                    "active_target": {
                        "plan_path": "dev/active/platform_authority_loop.md",
                        "target_kind": "session_resume",
                    },
                    "continuity": {
                        "alignment_status": "aligned",
                        "alignment_reason": "scope_and_instruction_match",
                        "summary": "Land the first startup intake packet.",
                    },
                    "ownership": {
                        "status": "concurrent_writer_activity",
                        "scope_source": "current_session.current_instruction",
                        "summary": (
                            "Dirty paths fall outside the claimed slice while "
                            "typed peer activity is still present."
                        ),
                        "outside_scope_dirty_paths": [
                            "dev/scripts/devctl/review_channel/session_state_hints.py"
                        ],
                        "live_agents": ["codex", "claude"],
                    },
                    "coordination": {
                        "collaboration_topology": "dual_agent",
                        "authority_mode": "reviewer_gated",
                        "work_ownership_mode": "concurrent_writer_conflict",
                        "sync_cadence_mode": "before_scope_change",
                        "summary": (
                            "dual_agent, reviewer_gated, "
                            "concurrent_writer_conflict, before_scope_change, "
                            "not publish-ready"
                        ),
                        "active_roles": ["reviewer", "implementer"],
                        "active_participants": [
                            "codex:reviewer",
                            "claude:implementer",
                        ],
                        "delegated_worktrees": ["../codex-voice-wt-a1"],
                        "duplicate_delegated_worktrees": ["../codex-voice-wt-a1"],
                    },
                    "routing": {
                        "selected_workflow_profile": "bundle.tooling",
                        "preflight_command": "python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute",
                        "rule_summary": "Selected bundle.tooling for edit-first work.",
                        "match_evidence": [
                            {
                                "rule_id": "work_intake.prefer_bundle_tooling",
                                "summary": "bundle.tooling is available.",
                                "evidence": ["advisory_action=continue_editing"],
                            }
                        ],
                        "rejected_rule_traces": [
                            {
                                "rule_id": "work_intake.select_post_push_bundle",
                                "summary": "Use the post-push bundle when startup is push-ready.",
                                "rejected_because": "Startup is not push-ready yet.",
                                "evidence": [],
                            }
                        ],
                    },
                    "session_pacing": {
                        "complexity_band": "high",
                        "source": "saved_context_graph_snapshot",
                        "research_ref_budget": 7,
                        "dependency_edge_count": 5,
                        "implementation_trigger": "patch_after_bounded_refs_or_raise_blocker",
                        "summary": "Review 4 authority refs and 3 implementation refs, then patch or escalate.",
                        "authority_refs": [
                            "dev/active/platform_authority_loop.md",
                            "AGENTS.md",
                        ],
                        "implementation_refs": [
                            "dev/scripts/devctl/runtime/work_intake.py",
                            "dev/scripts/devctl/runtime/startup_context.py",
                        ],
                    },
                    "warm_refs": [
                        "AGENTS.md",
                        "dev/active/INDEX.md",
                        "dev/active/platform_authority_loop.md",
                    ],
                    "writeback_sinks": [
                        "dev/active/platform_authority_loop.md",
                        "dev/active/MASTER_PLAN.md",
                    ],
                },
            }
        )

        self.assertIn("## Work Intake", rendered)
        self.assertIn("dev/active/platform_authority_loop.md", rendered)
        self.assertIn(
            "continuity_summary: Land the first startup intake packet.", rendered
        )
        self.assertIn("ownership: `concurrent_writer_activity`", rendered)
        self.assertIn(
            "outside_scope_dirty_paths: `dev/scripts/devctl/review_channel/session_state_hints.py`",
            rendered,
        )
        self.assertIn("live_agents: `codex`, `claude`", rendered)
        self.assertIn("collaboration_topology: `dual_agent`", rendered)
        self.assertIn("authority_mode: `reviewer_gated`", rendered)
        self.assertIn(
            "work_ownership_mode: `concurrent_writer_conflict`",
            rendered,
        )
        self.assertIn("sync_cadence_mode: `before_scope_change`", rendered)
        self.assertIn("active_roles: `reviewer`, `implementer`", rendered)
        self.assertIn(
            "active_participants: `codex:reviewer`, `claude:implementer`",
            rendered,
        )
        self.assertIn("delegated_worktrees: `../codex-voice-wt-a1`", rendered)
        self.assertIn(
            "duplicate_delegated_worktrees: `../codex-voice-wt-a1`",
            rendered,
        )
        self.assertIn(
            "session_pacing: `high` via `saved_context_graph_snapshot`", rendered
        )
        self.assertIn("research_ref_budget: 7", rendered)
        self.assertIn("dependency_edge_count: 5", rendered)
        self.assertIn(
            "implementation_trigger: `patch_after_bounded_refs_or_raise_blocker`",
            rendered,
        )
        self.assertIn(
            "implementation_refs: `dev/scripts/devctl/runtime/work_intake.py`, `dev/scripts/devctl/runtime/startup_context.py`",
            rendered,
        )
        self.assertIn("selected_workflow_profile: `bundle.tooling`", rendered)
        self.assertIn(
            "workflow_profile_rule_summary: Selected bundle.tooling for edit-first work.",
            rendered,
        )

    def test_markdown_renders_top_level_coordination_snapshot(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "clean_worktree",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                },
                "coordination": {
                    "active_target": {
                        "plan_path": "dev/active/platform_authority_loop.md",
                        "target_kind": "session_resume",
                    },
                    "current_slice": "Wire remote-control bootstrap through CoordinationSnapshot.",
                    "scope_paths": ["dev/scripts/devctl/commands/governance"],
                    "declared_topology": "multi_agent_orchestrated",
                    "observed_topology": "single_agent",
                    "recommended_topology": "single_agent",
                    "fanout_posture": "planned_scaffolding_only",
                    "safe_to_fanout": False,
                    "worktree_strategy": "isolated_worker_worktrees",
                    "resync_required": True,
                    "resync_reasons": ["declared_topology:multi_agent_orchestrated"],
                    "actors": [
                        {
                            "actor_id": "codex",
                            "presence": "live",
                            "provider": "codex",
                            "role": "reviewer",
                            "lane": "Codex review lane",
                            "worktree": "../wt-review",
                            "branch": "feature/review",
                            "mp_scope": "MP-377",
                        }
                    ],
                },
            }
        )

        self.assertIn("## Coordination Snapshot", rendered)
        self.assertIn(
            "current_slice: Wire remote-control bootstrap through CoordinationSnapshot.",
            rendered,
        )
        self.assertIn(
            "topology: `multi_agent_orchestrated` / `single_agent` -> `single_agent`",
            rendered,
        )
        self.assertIn("fanout_posture: `planned_scaffolding_only`", rendered)
        self.assertIn("safe_to_fanout: False", rendered)
        self.assertIn("resync_required: True", rendered)
        self.assertIn(
            "actors: `codex:live|provider=codex|role=reviewer|lane=Codex review lane|worktree=../wt-review|branch=feature/review|scope=MP-377`",
            rendered,
        )

    def test_markdown_renders_latest_push_receipt_fields(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "checkpoint_allowed",
                "advisory_reason": "worktree_dirty_within_budget",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                    "push_enforcement": {
                        "worktree_dirty": True,
                        "worktree_clean": False,
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                        "recommended_action": "commit_before_push",
                        "publication_backlog_state": "none",
                        "latest_push_report_path": "dev/reports/push/latest.json",
                        "latest_push_report_matches_current_branch": False,
                        "latest_push_report_matches_current_head": False,
                        "latest_push_report_matches_current_approved_target": False,
                        "latest_push_report_published_remote": True,
                        "latest_push_report_post_push_green": False,
                        "latest_push_report_status": "published_remote",
                        "latest_push_report_reason": "post_push_bundle_failed",
                    },
                },
                "push_decision": {
                    "action": "await_checkpoint",
                    "reason": "worktree_dirty",
                    "push_eligible_now": False,
                    "has_remote_work_to_push": False,
                    "publication_backlog": {"backlog_state": "none"},
                    "next_step_summary": "checkpoint first",
                    "match_evidence": [],
                    "rejected_rule_traces": [],
                },
            }
        )

        # Effective publication summary appears first
        self.assertIn(
            "- effective_publication_state: "
            "Not yet published (push report is from different branch/commit)",
            rendered,
        )
        self.assertIn("- published_remote: False", rendered)
        self.assertIn("- post_push_green: False", rendered)
        self.assertIn("- latest_push_status: `published_remote`", rendered)
        self.assertIn("- latest_push_reason: `post_push_bundle_failed`", rendered)

        # Raw diagnostics appear under subsection
        self.assertIn("#### Diagnostic: raw push-report booleans", rendered)
        self.assertIn("- latest_push_report: `dev/reports/push/latest.json`", rendered)
        self.assertIn("- latest_push_matches_current_branch: False", rendered)
        self.assertIn("- latest_push_matches_current_head: False", rendered)
        self.assertIn("- latest_push_matches_current_approved_target: False", rendered)
        self.assertIn("- latest_push_report_published_remote: True", rendered)
        self.assertIn("- latest_push_receipt_current: False", rendered)

        # Effective summary must appear before diagnostic subsection
        summary_pos = rendered.index("effective_publication_state")
        diag_pos = rendered.index("Diagnostic: raw push-report booleans")
        self.assertLess(summary_pos, diag_pos)

    def test_markdown_renders_startup_and_push_rule_explanations(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "push_allowed",
                "advisory_reason": "worktree_clean_and_review_accepted",
                "rule_summary": "Startup allows the governed push path.",
                "match_evidence": [
                    {
                        "rule_id": "startup_advisory.push_allowed",
                        "summary": "All startup prerequisites for push are satisfied.",
                        "evidence": ["worktree_clean=True"],
                    }
                ],
                "rejected_rule_traces": [
                    {
                        "rule_id": "startup_advisory.no_push_needed",
                        "summary": "Stop because nothing remains to push.",
                        "rejected_because": "The branch still has remote work to publish.",
                        "evidence": [],
                    }
                ],
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                },
                "push_decision": {
                    "action": "run_devctl_push",
                    "reason": "push_preconditions_satisfied",
                    "push_eligible_now": True,
                    "has_remote_work_to_push": True,
                    "next_step_summary": "Use the governed push path now.",
                    "next_step_command": "python3 dev/scripts/devctl.py push --execute",
                    "rule_summary": "Push uses the governed path now.",
                    "match_evidence": [
                        {
                            "rule_id": "startup_push.run_devctl_push",
                            "summary": "Push prerequisites are green.",
                            "evidence": ["review_gate_allows_push=True"],
                        }
                    ],
                    "rejected_rule_traces": [
                        {
                            "rule_id": "startup_push.no_push_needed",
                            "summary": "Declare that no governed push is needed.",
                            "rejected_because": "The branch still has work to publish upstream.",
                            "evidence": [],
                        }
                    ],
                },
            }
        )

        self.assertIn(
            "startup_rule_summary: Startup allows the governed push path.",
            rendered,
        )
        self.assertIn("push_rule_summary: Push uses the governed path now.", rendered)

    def test_markdown_renders_push_next_step_guidance(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "push_allowed",
                "advisory_reason": "worktree_clean_and_review_accepted",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                },
                "push_decision": {
                    "action": "run_devctl_push",
                    "reason": "push_preconditions_satisfied",
                    "push_eligible_now": True,
                    "has_remote_work_to_push": True,
                    "next_step_summary": "Use the governed push path now.",
                    "next_step_command": (
                        "python3 dev/scripts/devctl.py push --execute"
                    ),
                },
            }
        )

        self.assertIn("next_step_summary: Use the governed push path now.", rendered)
        self.assertIn(
            "next_step_command: `python3 dev/scripts/devctl.py push --execute`",
            rendered,
        )

    def test_markdown_surfaces_publication_backlog_when_commits_are_waiting(
        self,
    ) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "await_review",
                "advisory_reason": "review_pending_before_push",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                    "push_enforcement": {
                        "worktree_dirty": False,
                        "worktree_clean": True,
                        "ahead_of_upstream_commits": 3,
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                        "recommended_action": "use_devctl_push",
                    },
                },
                "push_decision": {
                    "action": "await_review",
                    "reason": "review_pending_before_push",
                    "push_eligible_now": False,
                    "has_remote_work_to_push": True,
                    "next_step_summary": "Wait for review acceptance before push.",
                },
            }
        )

        self.assertIn("ahead_of_upstream_commits: 3", rendered)
        self.assertIn(
            "publication_backlog: 3 local commit(s) waiting for governed push once review is accepted.",
            rendered,
        )

    def test_markdown_blocker_section_omitted_when_state_is_healthy(self) -> None:
        """Healthy startup dicts must render without the shared Blockers table."""
        rendered = _render_markdown(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "no_blockers",
                "reviewer_gate": {},
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                },
            }
        )
        self.assertNotIn("## Blockers", rendered)

    def test_markdown_blocker_section_uses_shared_renderer_contract(self) -> None:
        """Blocking startup states must route through the shared CheckResult renderer.

        Proves the MP-381 contract family has ``startup-context`` as a live
        production caller: ``startup_summary_to_violations`` →
        ``render_check_result_md`` feeds a ``## Blockers`` section carrying
        the ``## Violation Detail`` subtable with typed policy attribution
        (``startup_authority`` / ``push_state_machine``).
        """
        rendered = _render_markdown(
            {
                "advisory_action": "await_review",
                "advisory_reason": "review_pending_before_push",
                "reviewer_gate": {
                    "implementation_blocked": True,
                    "implementation_block_reason": "review pending acceptance",
                    "reviewer_mode": "active_dual_agent",
                },
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                },
                "push_decision": {
                    "action": "await_review",
                    "reason": "review_pending_before_push",
                    "next_step_summary": "Wait for review acceptance before push.",
                    "next_step_command": "python3 dev/scripts/devctl.py push --execute",
                },
            }
        )
        self.assertIn("## Blockers", rendered)
        self.assertIn("## Violation Detail", rendered)
        self.assertIn("| Step | File | Line | Policy | Severity | Fix |", rendered)
        self.assertIn("startup_authority", rendered)
        self.assertIn("reviewer_gate", rendered)
        self.assertIn("push_state_machine", rendered)
        # The hollow step table preamble must not leak into startup output.
        self.assertNotIn("| Step | Status | Duration (s) | Command |", rendered)

    def test_markdown_reviewer_gate_prefers_effective_mode(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "await_review",
                "advisory_reason": "runtime_missing",
                "reviewer_gate": {
                    "bridge_active": True,
                    "reviewer_mode": "active_dual_agent",
                    "effective_reviewer_mode": "tools_only",
                    "review_accepted": False,
                },
                "governance": {
                    "repo_identity": {
                        "repo_name": "test",
                        "current_branch": "feature/x",
                    },
                },
                "push_decision": {"action": "await_review", "next_step_command": ""},
            }
        )

        self.assertIn("- reviewer_mode: tools_only", rendered)
        self.assertNotIn("- reviewer_mode: active_dual_agent", rendered)

    def test_push_decision_recovers_remote_published_post_push_failure_for_current_head(
        self,
    ) -> None:
        approved_target_identity = "tree-receipt-20260403T010000Z:tree-123"
        governance = _minimal_governance(
            current_branch="feature/x",
            current_head_commit="abc123",
            upstream_ref="origin/feature/x",
            ahead_of_upstream_commits=1,
            worktree_clean=True,
            worktree_dirty=False,
            checkpoint_required=False,
            safe_to_continue_editing=True,
            latest_push_report_path="dev/reports/push/latest.json",
            latest_push_report_branch="feature/x",
            latest_push_report_remote="origin",
            latest_push_report_head_commit="abc123",
            latest_push_report_status="published_remote",
            latest_push_report_reason="post_push_bundle_failed",
            latest_push_report_published_remote=True,
            latest_push_report_post_push_green=False,
            current_approved_target_identity=approved_target_identity,
            latest_push_report_approved_target_identity=approved_target_identity,
            latest_push_report_matches_current_approved_target=True,
            latest_push_report_matches_current_branch=True,
            latest_push_report_matches_current_head=True,
        )

        decision = _derive_push_decision(
            governance.push_enforcement,
            review_gate_allows_push=True,
            implementation_blocked=False,
        )

        self.assertEqual(decision.action, "no_push_needed")
        self.assertEqual(decision.reason, "remote_publish_recorded_post_push_pending")
        self.assertIn(
            "Remote publication already succeeded", decision.next_step_summary
        )
        self.assertIn("dev/reports/push/latest.json", decision.next_step_summary)

    def test_push_decision_recovers_blank_target_identity_post_push_failure_for_current_head(
        self,
    ) -> None:
        governance = _minimal_governance(
            current_branch="feature/x",
            current_head_commit="abc123",
            upstream_ref="origin/feature/x",
            ahead_of_upstream_commits=1,
            worktree_clean=True,
            worktree_dirty=False,
            checkpoint_required=False,
            safe_to_continue_editing=True,
            latest_push_report_path="dev/reports/push/latest.json",
            latest_push_report_branch="feature/x",
            latest_push_report_remote="origin",
            latest_push_report_head_commit="abc123",
            latest_push_report_status="published_remote",
            latest_push_report_reason="post_push_bundle_failed",
            latest_push_report_published_remote=True,
            latest_push_report_post_push_green=False,
            current_approved_target_identity="",
            latest_push_report_approved_target_identity="",
            latest_push_report_matches_current_approved_target=True,
            latest_push_report_matches_current_branch=True,
            latest_push_report_matches_current_head=True,
        )

        decision = _derive_push_decision(
            governance.push_enforcement,
            review_gate_allows_push=True,
            implementation_blocked=False,
        )

        self.assertEqual(decision.action, "no_push_needed")
        self.assertEqual(decision.reason, "remote_publish_recorded_post_push_pending")
        self.assertIn(
            "Remote publication already succeeded", decision.next_step_summary
        )
        self.assertIn("dev/reports/push/latest.json", decision.next_step_summary)

    def test_push_decision_waits_for_current_head_governed_push_in_progress(
        self,
    ) -> None:
        approved_target_identity = "tree-receipt-20260403T010000Z:tree-123"
        governance = _minimal_governance(
            current_branch="feature/x",
            current_head_commit="abc123",
            upstream_ref="origin/feature/x",
            ahead_of_upstream_commits=1,
            worktree_clean=True,
            worktree_dirty=False,
            checkpoint_required=False,
            safe_to_continue_editing=True,
            latest_push_report_path="dev/reports/push/latest.json",
            latest_push_report_branch="feature/x",
            latest_push_report_remote="origin",
            latest_push_report_head_commit="abc123",
            latest_push_report_status="validation_ready",
            latest_push_report_reason="push_pending",
            latest_push_report_published_remote=False,
            latest_push_report_post_push_green=False,
            current_approved_target_identity=approved_target_identity,
            latest_push_report_approved_target_identity=approved_target_identity,
            latest_push_report_matches_current_approved_target=True,
            latest_push_report_matches_current_branch=True,
            latest_push_report_matches_current_head=True,
        )

        decision = _derive_push_decision(
            governance.push_enforcement,
            review_gate_allows_push=True,
            implementation_blocked=False,
        )

        self.assertEqual(decision.action, "no_push_needed")
        self.assertEqual(decision.reason, "governed_push_in_progress")
        self.assertIn("already running", decision.next_step_summary)
        self.assertIn("dev/reports/push/latest.json", decision.next_step_summary)

    def test_push_decision_rejects_stale_head_publish_receipt(self) -> None:
        approved_target_identity = "tree-receipt-20260403T010000Z:tree-123"
        governance = _minimal_governance(
            current_branch="feature/x",
            current_head_commit="new-head",
            upstream_ref="origin/feature/x",
            ahead_of_upstream_commits=1,
            worktree_clean=True,
            worktree_dirty=False,
            checkpoint_required=False,
            safe_to_continue_editing=True,
            latest_push_report_path="dev/reports/push/latest.json",
            latest_push_report_branch="feature/x",
            latest_push_report_remote="origin",
            latest_push_report_head_commit="old-head",
            latest_push_report_status="published_remote",
            latest_push_report_reason="post_push_bundle_failed",
            latest_push_report_published_remote=True,
            latest_push_report_post_push_green=False,
            current_approved_target_identity=approved_target_identity,
            latest_push_report_approved_target_identity=approved_target_identity,
            latest_push_report_matches_current_approved_target=True,
            latest_push_report_matches_current_branch=True,
            latest_push_report_matches_current_head=False,
        )

        decision = _derive_push_decision(
            governance.push_enforcement,
            review_gate_allows_push=True,
            implementation_blocked=False,
        )

        self.assertEqual(decision.action, "run_devctl_push")
        self.assertEqual(decision.reason, "push_preconditions_satisfied")
        self.assertTrue(decision.has_remote_work_to_push)

    def test_push_decision_rejects_publish_receipt_for_different_remote(self) -> None:
        approved_target_identity = "tree-receipt-20260403T010000Z:tree-123"
        governance = _minimal_governance(
            current_branch="feature/x",
            current_head_commit="abc123",
            upstream_ref="upstream/feature/x",
            ahead_of_upstream_commits=1,
            worktree_clean=True,
            worktree_dirty=False,
            checkpoint_required=False,
            safe_to_continue_editing=True,
            latest_push_report_path="dev/reports/push/latest.json",
            latest_push_report_branch="feature/x",
            latest_push_report_remote="origin",
            latest_push_report_head_commit="abc123",
            latest_push_report_status="published_remote",
            latest_push_report_reason="post_push_bundle_failed",
            latest_push_report_published_remote=True,
            latest_push_report_post_push_green=False,
            current_approved_target_identity=approved_target_identity,
            latest_push_report_approved_target_identity=approved_target_identity,
            latest_push_report_matches_current_approved_target=True,
            latest_push_report_matches_current_branch=True,
            latest_push_report_matches_current_head=True,
        )

        decision = _derive_push_decision(
            governance.push_enforcement,
            review_gate_allows_push=True,
            implementation_blocked=False,
        )

        self.assertEqual(decision.action, "run_devctl_push")
        self.assertEqual(decision.reason, "push_preconditions_satisfied")
        self.assertTrue(decision.has_remote_work_to_push)

    def test_summary_renders_compact_step_zero_guidance(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "checkpoint_allowed",
                "advisory_reason": "worktree_dirty_within_budget",
                "reviewer_gate": {
                    "implementation_blocked": False,
                    "implementation_block_reason": "",
                },
                "startup_authority": {"ok": True},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                    }
                },
                "push_decision": {
                    "action": "await_review",
                    "next_step_command": "",
                },
            }
        )

        self.assertEqual(
            rendered,
            "\n".join(
                (
                    "action=checkpoint_allowed",
                    "reason=worktree_dirty_within_budget",
                    "interaction_mode=unresolved",
                    "blockers=none",
                    "next=python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md",
                    "typed_bypass_capabilities=AgentLoopOperatorOverride,BypassReceipt,GovernedExceptionLifecycle",
                    "typed_bypass_scope=edit-only blocks vcs.stage,vcs.commit,vcs.push",
                    "continuity_attention=none",
                )
            ),
        )

    def test_summary_names_managed_projection_drift(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "no_push_needed",
                "advisory_reason": "managed_projection_drift_only",
                "reviewer_gate": {
                    "implementation_blocked": False,
                    "implementation_block_reason": "",
                },
                "startup_authority": {"ok": True},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                        "managed_projection_drift": True,
                        "managed_projection_dirty_paths": ["bridge.md"],
                    }
                },
                "push_decision": {
                    "action": "no_push_needed",
                    "next_step_command": "",
                },
            }
        )

        self.assertIn("reason=managed_projection_drift_only", rendered)
        self.assertIn("managed_projection_drift=True", rendered)
        self.assertIn("managed_projection_dirty_paths=bridge.md", rendered)

    def test_summary_surfaces_observed_control_topology(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "repair_reviewer_loop",
                "advisory_reason": "reviewer_absent",
                "observed_control_topology": "implementer_without_reviewer",
                "implementation_permission": "suspended",
                "reviewer_gate": {
                    "implementation_blocked": True,
                    "implementation_block_reason": "reviewer_absent",
                    "review_gate_allows_push": False,
                },
                "startup_authority": {"ok": False},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                    }
                },
                "push_decision": {
                    "action": "await_review",
                    "next_step_command": "",
                },
            }
        )

        self.assertIn(
            "observed_control_topology=implementer_without_reviewer",
            rendered,
        )
        self.assertIn("implementation_permission=suspended", rendered)

    def test_summary_surfaces_development_publication_deferral(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "checkpoint_before_continue",
                "advisory_reason": "dirty_path_budget_exceeded",
                "implementation_permission": "active",
                "publication_deferred_active": True,
                "publication_deferred_reason": "publication_deferred_for_development",
                "deferred_publication_command": (
                    'python3 dev/scripts/devctl.py commit -m "checkpoint"'
                ),
                "deferred_publication_actions": [
                    "vcs.stage",
                    "vcs.commit",
                    "vcs.push",
                ],
                "reviewer_gate": {
                    "implementation_blocked": False,
                    "implementation_block_reason": "",
                },
                "startup_authority": {"ok": False},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": True,
                        "safe_to_continue_editing": False,
                    }
                },
                "push_decision": {
                    "action": "await_checkpoint",
                    "next_step_command": "",
                },
            }
        )

        self.assertIn("publication_deferred_active=True", rendered)
        self.assertIn(
            "publication_deferred_reason=publication_deferred_for_development",
            rendered,
        )
        self.assertIn(
            'deferred_publication_command=python3 dev/scripts/devctl.py commit -m "checkpoint"',
            rendered,
        )
        self.assertIn(
            "deferred_publication_actions=vcs.stage,vcs.commit,vcs.push",
            rendered,
        )

    def test_summary_reports_blockers_and_rerun_when_checkpoint_is_required(
        self,
    ) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "checkpoint_before_continue",
                "advisory_reason": "dirty_path_budget_exceeded",
                "reviewer_gate": {
                    "implementation_blocked": False,
                    "implementation_block_reason": "",
                },
                "startup_authority": {"ok": False},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": True,
                        "safe_to_continue_editing": False,
                    }
                },
                "push_decision": {
                    "action": "await_review",
                    "next_step_command": "",
                },
            }
        )

        self.assertIn("blockers=startup_authority,checkpoint_required", rendered)
        self.assertIn(
            'next=python3 dev/scripts/devctl.py commit -m "<descriptive message>"',
            rendered,
        )

    def test_summary_prefers_reviewer_loop_recovery_command(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "repair_reviewer_loop",
                "advisory_reason": "reviewer_heartbeat_stale",
                "reviewer_gate": {
                    "implementation_blocked": True,
                    "implementation_block_reason": "reviewer_heartbeat_stale",
                    "review_gate_allows_push": False,
                },
                "startup_authority": {"ok": False},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                    }
                },
                "push_decision": {
                    "action": "await_review",
                    "next_step_command": "",
                },
            }
        )

        self.assertIn("action=repair_reviewer_loop", rendered)
        self.assertIn("blockers=startup_authority,reviewer_heartbeat_stale", rendered)
        self.assertIn("review-channel --action launch", rendered)

    def test_summary_surfaces_coordination_and_resync_blocker(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "coordination_visible",
                "reviewer_gate": {
                    "implementation_blocked": False,
                    "implementation_block_reason": "",
                    "operator_interaction_mode": "remote_control",
                },
                "startup_authority": {"ok": True},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                    }
                },
                "push_decision": {
                    "action": "no_push_needed",
                    "next_step_command": "",
                },
                "coordination": {
                    "declared_topology": "multi_agent_orchestrated",
                    "observed_topology": "single_agent",
                    "recommended_topology": "single_agent",
                    "fanout_posture": "planned_scaffolding_only",
                    "safe_to_fanout": False,
                    "worktree_strategy": "isolated_worker_worktrees",
                    "resync_required": True,
                    "current_slice": "Drive startup summary from shared coordination.",
                    "active_target": {
                        "plan_path": "dev/active/remote_control_runtime.md",
                    },
                },
            }
        )

        self.assertIn("blockers=coordination_resync_required", rendered)
        self.assertIn(
            "next=python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
            rendered,
        )
        self.assertIn(
            "coordination=multi_agent_orchestrated/single_agent->single_agent",
            rendered,
        )
        self.assertIn("safe_to_fanout=False", rendered)
        self.assertIn("resync_required=True", rendered)
        self.assertIn("fanout_posture=planned_scaffolding_only", rendered)
        self.assertIn("worktree_strategy=isolated_worker_worktrees", rendered)
        self.assertIn(
            "current_slice=Drive startup summary from shared coordination.",
            rendered,
        )
        self.assertIn("active_target=dev/active/remote_control_runtime.md", rendered)

    def test_summary_surfaces_push_backlog_when_remote_work_is_waiting(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "await_review",
                "advisory_reason": "review_pending_before_push",
                "reviewer_gate": {
                    "implementation_blocked": True,
                    "implementation_block_reason": "claude_ack_stale",
                },
                "startup_authority": {"ok": True},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                        "ahead_of_upstream_commits": 2,
                    }
                },
                "push_decision": {
                    "action": "await_review",
                    "has_remote_work_to_push": True,
                    "push_eligible_now": False,
                    "next_step_command": "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
                },
            }
        )

        self.assertIn("ahead_of_upstream_commits=2", rendered)
        self.assertIn(
            "push_guidance=2 local commit(s) waiting for governed push once review is accepted.",
            rendered,
        )

    def test_command_fails_closed_when_checkpoint_required(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(
                checkpoint_required=True,
                safe_to_continue_editing=False,
                checkpoint_reason="budget",
            ),
            reviewer_gate=ReviewerGateState(),
            advisory_action="checkpoint_before_continue",
            advisory_reason="budget",
        )
        args = build_parser().parse_args(["startup-context", "--format", "json"])

        def _fake_emit(*_args, **kwargs):
            options = kwargs["options"]
            self.assertFalse(options.ok)
            return 1

        with patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ), patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": True,
                "checks_run": 10,
                "checks_passed": 10,
                "errors": [],
                "warnings": [],
            },
        ), patch.object(
            startup_context_command,
            "write_startup_receipt",
            return_value=Path("/tmp/startup-receipt.json"),
        ), patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            side_effect=_fake_emit,
        ):
            rc = startup_context_command.run(args)

        self.assertEqual(rc, 1)

    def test_command_stays_green_within_budget(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(
                checkpoint_required=False,
                safe_to_continue_editing=True,
            ),
            reviewer_gate=ReviewerGateState(),
            advisory_action="continue_editing",
            advisory_reason="clean_worktree",
        )
        args = build_parser().parse_args(["startup-context", "--format", "json"])

        def _fake_emit(*_args, **kwargs):
            options = kwargs["options"]
            self.assertTrue(options.ok)
            return 0

        with patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ), patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": True,
                "checks_run": 10,
                "checks_passed": 10,
                "errors": [],
                "warnings": [],
            },
        ), patch.object(
            startup_context_command,
            "write_startup_receipt",
            return_value=Path("/tmp/startup-receipt.json"),
        ), patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            side_effect=_fake_emit,
        ):
            rc = startup_context_command.run(args)

        self.assertEqual(rc, 0)

    def test_reviewer_role_uses_effective_mode_for_local_edit_gate(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(
                checkpoint_required=False,
                safe_to_continue_editing=True,
            ),
            reviewer_gate=ReviewerGateState(
                bridge_active=True,
                reviewer_mode="active_dual_agent",
                effective_reviewer_mode="tools_only",
                review_accepted=False,
            ),
            advisory_action="continue_editing",
            advisory_reason="clean_worktree",
            implementation_permission="active",
        )
        args = build_parser().parse_args(
            ["startup-context", "--role", "reviewer", "--format", "json"]
        )

        with patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ), patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": True,
                "checks_run": 10,
                "checks_passed": 10,
                "errors": [],
                "warnings": [],
            },
        ), patch.object(
            startup_context_command,
            "write_startup_receipt",
            return_value=Path("/tmp/startup-receipt.json"),
        ), patch.object(
            startup_context_command,
            "reviewer_local_implementation_allowed",
            return_value=True,
        ) as reviewer_local_allowed_mock, patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            return_value=0,
        ), patch.object(
            startup_context_command, "_render_summary", return_value=""
        ):
            rc = startup_context_command.run(args)

        self.assertEqual(rc, 0)
        reviewer_local_allowed_mock.assert_called_once_with(
            reviewer_mode="tools_only",
            reviewer_override=False,
        )

    def test_command_fails_closed_when_startup_authority_is_red(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(
                checkpoint_required=False,
                safe_to_continue_editing=True,
            ),
            reviewer_gate=ReviewerGateState(),
            advisory_action="continue_editing",
            advisory_reason="clean_worktree",
        )
        args = build_parser().parse_args(["startup-context", "--format", "json"])

        def _fake_emit(*_args, **kwargs):
            options = kwargs["options"]
            self.assertFalse(options.ok)
            return 1

        with patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ), patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": False,
                "checks_run": 10,
                "checks_passed": 8,
                "errors": ["over budget"],
                "warnings": [],
            },
        ), patch.object(
            startup_context_command,
            "write_startup_receipt",
            return_value=Path("/tmp/startup-receipt.json"),
        ), patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            side_effect=_fake_emit,
        ):
            rc = startup_context_command.run(args)

        self.assertEqual(rc, 1)

    def test_reviewer_role_uses_bootstrap_intent_and_preloaded_state(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(),
            reviewer_gate=ReviewerGateState(
                reviewer_mode="active_dual_agent",
                effective_reviewer_mode="active_dual_agent",
            ),
            advisory_action="continue_editing",
            advisory_reason="clean_worktree",
        )
        args = build_parser().parse_args(
            ["startup-context", "--role", "reviewer", "--format", "json"]
        )

        with patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ), patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": True,
                "checks_run": 10,
                "checks_passed": 10,
                "errors": [],
                "warnings": [],
            },
        ) as authority_mock, patch.object(
            startup_context_command,
            "write_startup_receipt",
            return_value=Path("/tmp/startup-receipt.json"),
        ), patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            return_value=0,
        ):
            rc = startup_context_command.run(args)

        self.assertEqual(rc, 0)
        authority_mock.assert_called_once_with(
            intent="reviewer_bootstrap",
            governance=ctx.governance,
            reviewer_gate=ctx.reviewer_gate,
        )

    def test_reviewer_override_keeps_implementation_strict_intent(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(),
            reviewer_gate=ReviewerGateState(
                reviewer_mode="active_dual_agent",
                effective_reviewer_mode="active_dual_agent",
            ),
            advisory_action="continue_editing",
            advisory_reason="clean_worktree",
        )
        args = build_parser().parse_args(
            [
                "startup-context",
                "--role",
                "reviewer",
                "--reviewer-override",
                "--format",
                "json",
            ]
        )

        with patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ), patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": True,
                "checks_run": 10,
                "checks_passed": 10,
                "errors": [],
                "warnings": [],
            },
        ) as authority_mock, patch.object(
            startup_context_command,
            "write_startup_receipt",
            return_value=Path("/tmp/startup-receipt.json"),
        ), patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            return_value=0,
        ):
            rc = startup_context_command.run(args)

        self.assertEqual(rc, 0)
        authority_mock.assert_called_once_with(
            intent="implementation_strict",
            governance=ctx.governance,
            reviewer_gate=ctx.reviewer_gate,
        )

    def test_role_bound_checkpoint_receipt_uses_session_resume_command(self) -> None:
        for role, expected_intent in (
            ("reviewer", "reviewer_bootstrap"),
            ("implementer", "implementation_strict"),
        ):
            with self.subTest(role=role):
                ctx = StartupContext(
                    governance=_minimal_governance(
                        checkpoint_required=True,
                        safe_to_continue_editing=False,
                        checkpoint_reason="budget",
                    ),
                    reviewer_gate=ReviewerGateState(),
                    advisory_action="checkpoint_before_continue",
                    advisory_reason="budget",
                    observed_control_topology="single_agent",
                    implementation_permission="active",
                )
                args = build_parser().parse_args(
                    ["startup-context", "--role", role, "--format", "json"]
                )
                captured: dict[str, object] = {}

                def _fake_write(receipt, **_kwargs):
                    captured["receipt"] = receipt
                    return Path("/tmp/startup-receipt.json")

                def _fake_emit(*_args, **kwargs):
                    captured["payload"] = kwargs["json_payload"]
                    captured["human_output"] = kwargs["human_output"]
                    captured["summary"] = kwargs["options"].summary
                    self.assertFalse(kwargs["options"].ok)
                    return 1

                with patch.object(
                    startup_context_command,
                    "build_startup_context",
                    return_value=ctx,
                ), patch.object(
                    startup_context_command,
                    "build_startup_authority_report",
                    return_value={
                        "ok": True,
                        "checks_run": 10,
                        "checks_passed": 10,
                        "errors": [],
                        "warnings": [],
                    },
                ), patch.object(
                    startup_context_command,
                    "write_startup_receipt",
                    side_effect=_fake_write,
                ), patch.object(
                    startup_context_command,
                    "emit_machine_artifact_output",
                    side_effect=_fake_emit,
                ):
                    rc = startup_context_command.run(args)

                self.assertEqual(rc, 1)
                expected_command = session_resume_command_for_role(role)
                payload = captured["payload"]
                self.assertEqual(
                    payload["push_decision"]["next_step_command"],
                    expected_command,
                )
                self.assertIn(
                    f"next={expected_command}",
                    captured["human_output"],
                )
                self.assertEqual(
                    captured["summary"]["push_next_step_command"],
                    expected_command,
                )
                receipt = captured["receipt"]
                self.assertEqual(receipt.push_next_step_command, expected_command)
                self.assertEqual(receipt.receipt_intent_scope, expected_intent)

    def test_command_json_payload_promotes_checkpoint_booleans_and_summary_inbox(
        self,
    ) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(
                checkpoint_required=True,
                safe_to_continue_editing=False,
                checkpoint_reason="budget",
            ),
            reviewer_gate=ReviewerGateState(),
            advisory_action="checkpoint_before_continue",
            advisory_reason="budget",
            attention=ReviewAttentionState(
                status="checkpoint_required",
                owner="operator",
                summary="Checkpoint required before more edits.",
                recommended_action="checkpoint",
                recommended_command=(
                    'python3 dev/scripts/devctl.py commit -m "checkpoint"'
                ),
            ),
            packet_inbox=PacketInboxState(
                attention_revision="attn-rev-1",
                agents=(
                    AgentAttentionRecord(
                        agent="codex",
                        current_instruction_packet_id="rev_pkt_0312",
                        latest_finding_packet_id="rev_pkt_0311",
                        pending_actionable_packet_ids=("rev_pkt_0312",),
                        expired_unresolved_packet_ids=(),
                        attention_status="wake_required",
                        wake_reason="instruction_pending",
                        required_command=(
                            "python3 dev/scripts/devctl.py review-channel "
                            "--action inbox --target codex --status pending --terminal none --format md"
                        ),
                        delivery_state="unseen",
                        attention_revision="attn-agent-rev-1",
                    ),
                ),
            ),
        )
        args = build_parser().parse_args(["startup-context", "--format", "json"])
        captured: dict[str, object] = {}

        def _fake_emit(*_args, **kwargs):
            captured["payload"] = kwargs["json_payload"]
            captured["summary"] = kwargs["options"].summary
            self.assertFalse(kwargs["options"].ok)
            return 1

        with patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ), patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": True,
                "checks_run": 10,
                "checks_passed": 10,
                "errors": [],
                "warnings": [],
            },
        ), patch.object(
            startup_context_command,
            "write_startup_receipt",
            return_value=Path("/tmp/startup-receipt.json"),
        ), patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            side_effect=_fake_emit,
        ):
            rc = startup_context_command.run(args)

        self.assertEqual(rc, 1)
        payload = captured["payload"]
        summary = captured["summary"]
        self.assertTrue(payload["checkpoint_required"])
        self.assertFalse(payload["safe_to_continue_editing"])
        self.assertEqual(summary["packet_inbox"]["attention_revision"], "attn-rev-1")
        self.assertEqual(
            summary["packet_inbox"]["agents"][0]["current_instruction_packet_id"],
            "rev_pkt_0312",
        )

    def test_command_receipt_persists_authority_snapshot(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(),
            reviewer_gate=ReviewerGateState(),
            advisory_action="continue_editing",
            advisory_reason="clean_worktree",
            coordination=CoordinationSnapshot(
                actors=(
                    CoordinationActorRecord(
                        actor_id="codex",
                        provider="codex",
                        role="reviewer",
                        presence="live",
                    ),
                    CoordinationActorRecord(
                        actor_id="claude",
                        provider="claude",
                        role="implementer",
                        presence="live",
                    ),
                )
            ),
            current_session=ReviewCurrentSessionState(
                current_instruction="checkpoint",
                current_instruction_revision="rev123",
                implementer_status="coding",
                implementer_ack="ack",
                implementer_ack_revision="rev123",
                implementer_ack_state="stale",
            ),
            authority_snapshot=AuthoritySnapshot(
                coordination_state="handshake_stale",
                current_instruction_revision="rev123",
                implementer_ack_state="stale",
                next_command='python3 dev/scripts/devctl.py commit -m "checkpoint"',
                safe_to_continue=False,
            ),
        )
        args = build_parser().parse_args(
            ["startup-context", "--role", "reviewer", "--format", "json"]
        )
        captured: dict[str, object] = {}

        def _fake_write(receipt, **_kwargs):
            captured["receipt"] = receipt
            return Path("/tmp/startup-receipt.json")

        with patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ), patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": True,
                "checks_run": 10,
                "checks_passed": 10,
                "errors": [],
                "warnings": [],
            },
        ), patch.object(
            startup_context_command,
            "write_startup_receipt",
            side_effect=_fake_write,
        ), patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            return_value=0,
        ):
            rc = startup_context_command.run(args)

        self.assertEqual(rc, 0)
        receipt = captured["receipt"]
        self.assertIsNotNone(receipt.authority_snapshot)
        assert receipt.authority_snapshot is not None
        self.assertEqual(
            receipt.authority_snapshot.current_instruction_revision,
            "rev123",
        )
        self.assertEqual(receipt.authority_snapshot.implementer_ack_state, "stale")
        self.assertEqual(receipt.authority_snapshot.actor_role, "reviewer")
        self.assertEqual(receipt.authority_snapshot.actor_identity, "codex")
        self.assertIn("review.checkpoint", receipt.authority_snapshot.allowed_actions)
        self.assertIn("implementation.edit", receipt.authority_snapshot.blocked_actions)


class TestReviewerGateSemantics(unittest.TestCase):
    """Verify reviewer gate does NOT conflate ACK with acceptance."""

    def _write_bridge(self, repo_root: Path, verdict: str, findings: str) -> None:
        bridge_text = "\n".join(
            (
                "- Reviewer mode: `active_dual_agent`",
                "",
                "## Current Verdict",
                verdict,
                "",
                "## Open Findings",
                findings,
                "",
                "## Current Instruction For Claude",
                "- Continue the current slice.",
                "",
            )
        )
        (repo_root / "bridge.md").write_text(bridge_text, encoding="utf-8")

    def test_active_bridge_unaccepted_denies_push(self) -> None:
        """In active mode with Needs-review verdict, push is not permitted."""
        gate = ReviewerGateState(
            bridge_active=True,
            reviewer_mode="active_dual_agent",
            review_accepted=False,
        )
        self.assertFalse(gate.review_gate_allows_push)

    def test_active_bridge_accepted_permits_push(self) -> None:
        """In active mode with reviewer-accepted verdict, push is permitted."""
        gate = ReviewerGateState(
            bridge_active=True,
            reviewer_mode="active_dual_agent",
            review_accepted=True,
            review_gate_allows_push=True,
        )
        self.assertTrue(gate.review_gate_allows_push)

    def test_inactive_bridge_permits_push(self) -> None:
        gate = ReviewerGateState(
            bridge_active=False,
            review_gate_allows_push=True,
        )
        self.assertTrue(gate.review_gate_allows_push)

    def test_required_checks_status_defaults_unknown(self) -> None:
        gate = ReviewerGateState()
        self.assertEqual(gate.required_checks_status, "unknown")

    def test_no_bridge_permits_push(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            gate = _detect_reviewer_gate(Path(tmp))
            self.assertTrue(gate.review_gate_allows_push)

    def test_fail_closed_default(self) -> None:
        gate = ReviewerGateState()
        self.assertFalse(gate.review_gate_allows_push)

    def test_live_verdict_based_acceptance(self) -> None:
        """On this repo, current verdict should drive review_accepted."""
        ctx = _live_startup_context()
        if ctx.reviewer_gate.bridge_active:
            # Acceptance must come from verdict, not mode
            self.assertIsInstance(ctx.reviewer_gate.review_accepted, bool)

    def test_detect_reviewer_gate_requires_typed_review_state_for_bridge_sessions(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge(
                repo_root,
                "Reviewer-accepted. Narrow startup-context slice is clean.",
                "- none",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertFalse(gate.review_accepted)
            self.assertFalse(gate.review_gate_allows_push)
            self.assertTrue(gate.implementation_blocked)
            self.assertEqual(
                gate.implementation_block_reason,
                "typed_review_state_required",
            )


class TestAdvisoryAction(unittest.TestCase):
    """Verify the typed startup advisory outcomes."""

    def test_checkpoint_required(self) -> None:
        gov = _minimal_governance(checkpoint_required=True, checkpoint_reason="budget")
        gate = ReviewerGateState()
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "checkpoint_before_continue")

    def test_budget_exceeded(self) -> None:
        gov = _minimal_governance(safe_to_continue_editing=False)
        gate = ReviewerGateState()
        action, _ = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "checkpoint_before_continue")

    def test_review_pending(self) -> None:
        gov = _minimal_governance(worktree_clean=False, worktree_dirty=True)
        gate = ReviewerGateState(bridge_active=True, review_accepted=False)
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "continue_editing")
        self.assertEqual(reason, "review_pending")

    def test_await_review_when_worktree_clean_but_review_pending(self) -> None:
        gov = _minimal_governance(worktree_clean=True, worktree_dirty=False)
        gate = ReviewerGateState(bridge_active=True, review_accepted=False)
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "await_review")
        self.assertEqual(reason, "review_pending_before_push")

    def test_push_decision_requires_checkpoint_when_worktree_dirty(self) -> None:
        gov = _minimal_governance(worktree_clean=False, worktree_dirty=True)
        gate = ReviewerGateState(review_gate_allows_push=False)
        decision = _derive_push_decision(
            gov.push_enforcement,
            review_gate_allows_push=gate.review_gate_allows_push,
            implementation_blocked=gate.implementation_blocked,
            implementation_block_reason=gate.implementation_block_reason,
        )
        self.assertEqual(decision.action, "await_checkpoint")
        self.assertFalse(decision.push_eligible_now)
        self.assertIn("checkpoint", decision.next_step_summary.lower())

    def test_push_decision_names_staged_index_when_index_is_nonempty(self) -> None:
        gov = _minimal_governance(
            worktree_clean=False,
            worktree_dirty=True,
            staged_path_count=4,
            unstaged_path_count=0,
        )
        gate = ReviewerGateState(review_gate_allows_push=False)

        decision = _derive_push_decision(
            gov.push_enforcement,
            review_gate_allows_push=gate.review_gate_allows_push,
            implementation_blocked=gate.implementation_blocked,
            implementation_block_reason=gate.implementation_block_reason,
        )

        self.assertEqual(decision.action, "await_checkpoint")
        self.assertEqual(decision.reason, "staged_index_present")
        self.assertIn("staged work waiting in the index", decision.next_step_summary)

    def test_push_decision_names_mixed_staged_and_unstaged_worktree(self) -> None:
        gov = _minimal_governance(
            worktree_clean=False,
            worktree_dirty=True,
            staged_path_count=2,
            unstaged_path_count=3,
        )
        gate = ReviewerGateState(review_gate_allows_push=False)

        decision = _derive_push_decision(
            gov.push_enforcement,
            review_gate_allows_push=gate.review_gate_allows_push,
            implementation_blocked=gate.implementation_blocked,
            implementation_block_reason=gate.implementation_block_reason,
        )

        self.assertEqual(decision.action, "await_checkpoint")
        self.assertEqual(decision.reason, "staged_and_unstaged_worktree_present")
        self.assertIn(
            "both a staged index and unstaged edits", decision.next_step_summary
        )

    def test_push_decision_waits_for_review_when_clean_but_unaccepted(self) -> None:
        gov = _minimal_governance(worktree_clean=True, worktree_dirty=False)
        gate = ReviewerGateState(review_gate_allows_push=False)
        decision = _derive_push_decision(
            gov.push_enforcement,
            review_gate_allows_push=gate.review_gate_allows_push,
            implementation_blocked=gate.implementation_blocked,
            implementation_block_reason=gate.implementation_block_reason,
        )
        self.assertEqual(decision.action, "await_review")
        self.assertEqual(decision.reason, "review_pending_before_push")
        self.assertEqual(
            decision.next_step_command,
            "python3 dev/scripts/devctl.py review-channel --action status "
            "--terminal none --format json",
        )

    def test_push_decision_runs_devctl_push_when_preconditions_hold(self) -> None:
        gov = _minimal_governance(
            worktree_clean=True,
            worktree_dirty=False,
            ahead_of_upstream_commits=1,
            upstream_ref="origin/feature/test",
        )
        gate = ReviewerGateState(review_gate_allows_push=True)
        decision = _derive_push_decision(
            gov.push_enforcement,
            review_gate_allows_push=gate.review_gate_allows_push,
            implementation_blocked=gate.implementation_blocked,
            implementation_block_reason=gate.implementation_block_reason,
        )
        self.assertEqual(decision.action, "run_devctl_push")
        self.assertTrue(decision.push_eligible_now)
        self.assertEqual(
            decision.next_step_command,
            "python3 dev/scripts/devctl.py push --execute",
        )
        self.assertEqual(decision.publication_backlog.backlog_state, "queued")

    def test_reviewer_loop_blocked(self) -> None:
        gov = _minimal_governance()
        gate = ReviewerGateState(
            bridge_active=True,
            review_accepted=False,
            implementation_blocked=True,
            implementation_block_reason="claude_ack_stale",
        )
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "repair_reviewer_loop")
        self.assertEqual(reason, "claude_ack_stale")

    def test_post_checkpoint_dirty_worktree_outranks_reviewer_loop_relaunch(
        self,
    ) -> None:
        gov = _minimal_governance(
            worktree_clean=False,
            worktree_dirty=True,
            ahead_of_upstream_commits=1,
            recommended_action="commit_before_push",
        )
        gate = ReviewerGateState(
            bridge_active=True,
            review_accepted=False,
            implementation_blocked=True,
            implementation_block_reason="review_loop_relaunch_required",
        )

        action, reason = _derive_advisory_action(gov, gate)

        self.assertEqual(action, "checkpoint_before_continue")
        self.assertEqual(reason, "dirty_after_local_checkpoint")

    def test_summary_next_command_prefers_commit_when_post_checkpoint_dirty(
        self,
    ) -> None:
        payload = {
            "startup_authority": {"ok": False},
            "governance": {
                "push_enforcement": {
                    "checkpoint_required": False,
                    "safe_to_continue_editing": True,
                    "worktree_dirty": True,
                    "ahead_of_upstream_commits": 1,
                    "recommended_action": "commit_before_push",
                }
            },
            "advisory_action": "repair_reviewer_loop",
            "reviewer_gate": {
                "implementation_blocked": True,
                "implementation_block_reason": "review_loop_relaunch_required",
                "review_gate_allows_push": False,
                "recovery_command": (
                    "python3 dev/scripts/devctl.py review-channel --action launch "
                    "--terminal terminal-app --format json"
                ),
            },
            "implementation_permission": "suspended",
        }

        self.assertEqual(
            summary_next_command(payload),
            'python3 dev/scripts/devctl.py commit -m "<descriptive message>"',
        )

    def test_concurrent_writer_activity_blocks_with_distinct_reason(self) -> None:
        gov = _minimal_governance(worktree_clean=False, worktree_dirty=True)
        gate = ReviewerGateState()
        ownership = WorkIntakeOwnershipState(
            status="concurrent_writer_activity",
            outside_scope_dirty_paths=(
                "dev/scripts/devctl/review_channel/session_state_hints.py",
            ),
            live_agents=("codex", "claude"),
            concurrent_writer_detected=True,
        )
        action, reason = _derive_advisory_action(gov, gate, ownership=ownership)
        self.assertEqual(action, "checkpoint_before_continue")
        self.assertEqual(reason, "concurrent_writer_activity")

    def test_duplicate_delegated_worktree_conflict_blocks_with_same_reason(
        self,
    ) -> None:
        gov = _minimal_governance(worktree_clean=False, worktree_dirty=True)
        gate = ReviewerGateState(
            bridge_active=True,
            reviewer_mode="active_dual_agent",
            effective_reviewer_mode="active_dual_agent",
        )
        coordination = WorkIntakeCoordinationState(
            collaboration_topology="multi_agent_orchestrated",
            authority_mode="reviewer_gated",
            work_ownership_mode="concurrent_writer_conflict",
            sync_cadence_mode="before_scope_change",
            delegated_agents=("codex-worker-1", "claude-worker-1"),
            duplicate_delegated_worktrees=("../codex-voice-wt-a1",),
            concurrent_writer_conflict_detected=True,
        )
        action, reason = _derive_advisory_action(
            gov,
            gate,
            coordination=coordination,
        )
        self.assertEqual(action, "checkpoint_before_continue")
        self.assertEqual(reason, "concurrent_writer_activity")

    # -- Detached-publication-only regression tests (F7/F8) --

    def test_detached_manual_approval_surfaces_push(self) -> None:
        """manual_reviewer_approval + clean + accepted → push_allowed, not continue_editing."""
        gov = _minimal_governance(
            worktree_clean=True,
            worktree_dirty=False,
            ahead_of_upstream_commits=1,
        )
        gate = ReviewerGateState(
            implementation_blocked=True,
            implementation_block_reason="manual_reviewer_approval",
            review_accepted=True,
            review_gate_allows_push=False,
        )
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "push_allowed")
        self.assertEqual(reason, "detached_publication_approved")

    def test_detached_hybrid_claude_only_surfaces_push(self) -> None:
        """hybrid_claude_only reason also surfaces push_allowed."""
        gov = _minimal_governance(
            worktree_clean=True,
            worktree_dirty=False,
            ahead_of_upstream_commits=2,
        )
        gate = ReviewerGateState(
            implementation_blocked=True,
            implementation_block_reason="hybrid_claude_only",
            review_accepted=True,
            review_gate_allows_push=False,
        )
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "push_allowed")
        self.assertEqual(reason, "detached_publication_approved")

    def test_non_detached_block_still_repairs_loop(self) -> None:
        """claude_ack_stale is NOT detached — must still repair the loop."""
        gov = _minimal_governance(
            worktree_clean=True,
            worktree_dirty=False,
            ahead_of_upstream_commits=1,
        )
        gate = ReviewerGateState(
            implementation_blocked=True,
            implementation_block_reason="claude_ack_stale",
            review_accepted=True,
            review_gate_allows_push=False,
        )
        action, reason = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "repair_reviewer_loop")
        self.assertEqual(reason, "claude_ack_stale")

    def test_detached_push_decision_aligned_with_advisory(self) -> None:
        """Push and advisory surfaces agree for manual_reviewer_approval."""
        gov = _minimal_governance(
            worktree_clean=True,
            worktree_dirty=False,
            ahead_of_upstream_commits=1,
            upstream_ref="origin/feature/test",
        )
        gate = ReviewerGateState(
            implementation_blocked=True,
            implementation_block_reason="manual_reviewer_approval",
            review_accepted=True,
            review_gate_allows_push=False,
        )
        advisory_action, _ = _derive_advisory_action(gov, gate)
        push_decision = _derive_push_decision(
            gov.push_enforcement,
            review_gate_allows_push=gate.review_gate_allows_push,
            implementation_blocked=gate.implementation_blocked,
            implementation_block_reason=gate.implementation_block_reason,
        )
        self.assertEqual(advisory_action, "push_allowed")
        self.assertEqual(push_decision.action, "run_devctl_push")

    def test_no_push_needed(self) -> None:
        gov = _minimal_governance(worktree_dirty=False, ahead_of_upstream_commits=0)
        gate = ReviewerGateState()
        action, _ = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "no_push_needed")

    def test_managed_projection_drift_only_is_not_source_work(self) -> None:
        gov = _minimal_governance(
            worktree_clean=True,
            worktree_dirty=False,
            ahead_of_upstream_commits=0,
            upstream_ref="origin/feature/test",
            managed_projection_drift=True,
            managed_projection_dirty_paths=("bridge.md",),
            excluded_path_count=1,
        )
        gate = ReviewerGateState()

        action, reason = _derive_advisory_action(gov, gate)
        push_decision = _derive_push_decision(
            gov.push_enforcement,
            review_gate_allows_push=gate.review_gate_allows_push,
            implementation_blocked=gate.implementation_blocked,
        )

        self.assertEqual(action, "no_push_needed")
        self.assertEqual(reason, "managed_projection_drift_only")
        self.assertEqual(push_decision.action, "no_push_needed")
        self.assertEqual(push_decision.reason, "managed_projection_drift_only")

    def test_push_allowed(self) -> None:
        gov = _minimal_governance(
            worktree_clean=True,
            worktree_dirty=False,
            ahead_of_upstream_commits=1,
        )
        gate = ReviewerGateState(review_gate_allows_push=True)
        action, _ = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "push_allowed")

    def test_checkpoint_allowed(self) -> None:
        gov = _minimal_governance(worktree_dirty=True, worktree_clean=False)
        gate = ReviewerGateState(
            checkpoint_permitted=True,
            review_gate_allows_push=False,
        )
        action, _ = _derive_advisory_action(gov, gate)
        self.assertEqual(action, "checkpoint_allowed")

    def test_blocks_new_implementation_when_checkpoint_required(self) -> None:
        ctx = StartupContext(
            governance=_minimal_governance(
                checkpoint_required=True,
                safe_to_continue_editing=False,
            ),
        )
        self.assertTrue(blocks_new_implementation(ctx))

    def test_blocks_new_implementation_allows_clean_context(self) -> None:
        ctx = StartupContext(governance=_minimal_governance())
        self.assertFalse(blocks_new_implementation(ctx))

    def test_blocks_new_implementation_when_reviewer_loop_is_blocked(self) -> None:
        ctx = StartupContext(
            reviewer_gate=ReviewerGateState(
                implementation_blocked=True,
                implementation_block_reason="claude_ack_stale",
            )
        )
        self.assertTrue(blocks_new_implementation(ctx))


class TestTypedReviewStateGatePath(unittest.TestCase):
    """Verify the typed review_state.json path preserves bridge_review_accepted semantics."""

    def _write_bridge_and_typed_state(
        self,
        repo_root: Path,
        verdict: str,
        findings: str,
        reviewer_mode: str = "active_dual_agent",
        effective_reviewer_mode: str | None = None,
        claude_ack_current: bool = True,
        attention_status: str = "healthy",
        typed_review_accepted: bool | None = None,
        typed_publish_clear: bool | None = None,
    ) -> None:
        """Write both bridge.md and review_state.json for typed-path testing."""
        bridge_text = "\n".join(
            (
                f"- Reviewer mode: `{reviewer_mode}`",
                "",
                "## Current Verdict",
                verdict,
                "",
                "## Open Findings",
                findings,
                "",
                "## Current Instruction For Claude",
                "- Continue the current slice.",
                "",
            )
        )
        (repo_root / "bridge.md").write_text(bridge_text, encoding="utf-8")
        (repo_root / "dev" / "reports" / "review_channel" / "latest").mkdir(
            parents=True,
            exist_ok=True,
        )

        # Create the canonical typed state projection directory. The legacy
        # latest root remains session artifact storage, not review-state
        # authority for startup gating.
        state_dir = (
            repo_root
            / "dev"
            / "reports"
            / "review_channel"
            / "projections"
            / "latest"
        )
        state_dir.mkdir(parents=True, exist_ok=True)
        # Compute review_accepted the same way the projection does:
        # verdict must match accepted patterns AND findings must be clear.
        import re

        _ACCEPTED_RE = re.compile(
            r"^(?:reviewer[- ]accepted|accepted|all\s+green|resolved)\b",
            re.IGNORECASE,
        )
        _CLEAR_RE = re.compile(
            r"^(?:\(none\)|none|no\s+blockers|all\s+clear|all\s+green|resolved)\b",
            re.IGNORECASE,
        )
        verdict_ok = bool(
            verdict.strip()
            and _ACCEPTED_RE.match(verdict.strip().splitlines()[0].lstrip("- ").strip())
        )
        finding_lines = [
            ln.lstrip("- ").strip().lower()
            for ln in findings.splitlines()
            if ln.strip()
        ]
        findings_ok = not finding_lines or all(
            _CLEAR_RE.match(ln) is not None for ln in finding_lines
        )
        review_accepted = (
            typed_review_accepted
            if typed_review_accepted is not None
            else verdict_ok and findings_ok
        )
        publish_clear = (
            typed_publish_clear if typed_publish_clear is not None else review_accepted
        )

        state_payload = {
            "review": {
                "surface_mode": "event-backed",
                "bridge_path": "bridge.md",
            },
            "bridge": {
                "reviewer_mode": reviewer_mode,
                "effective_reviewer_mode": (
                    effective_reviewer_mode
                    if effective_reviewer_mode is not None
                    else reviewer_mode
                ),
                "open_findings": findings,
                "review_accepted": review_accepted,
                "claude_ack_current": claude_ack_current,
            },
            "reviewer_runtime": {
                "reviewer_mode": reviewer_mode,
                "effective_reviewer_mode": (
                    effective_reviewer_mode
                    if effective_reviewer_mode is not None
                    else reviewer_mode
                ),
                "reviewer_freshness": "fresh",
                "stale_reason": (
                    "" if attention_status == "healthy" else attention_status
                ),
                "last_poll": {
                    "last_codex_poll_utc": "2026-04-02T00:00:00Z",
                    "last_codex_poll_age_seconds": 15,
                },
                "rollover": {
                    "rollover_id": "",
                    "ack_pending": False,
                    "trigger": "",
                },
                "session_owner": {
                    "provider": "codex",
                    "session_name": "codex-review",
                    "session_pid": 42,
                    "terminal_window_id": 7,
                    "script_path": "/tmp/codex-review.sh",
                },
                "recovery_action_allowed": "",
                "review_acceptance": {
                    "current_verdict": verdict,
                    "open_findings": findings,
                    "review_accepted": review_accepted,
                },
                "publish_clear": publish_clear,
            },
            "attention": {
                "status": attention_status,
            },
            "current_session": {
                "implementer_ack_state": ("current" if claude_ack_current else "stale"),
                "open_findings": findings,
            },
        }
        (state_dir / "review_state.json").write_text(
            json.dumps(state_payload), encoding="utf-8"
        )

    def test_typed_path_uses_bridge_review_accepted_semantics(self) -> None:
        """Typed path must use verdict-based acceptance, not ack_state."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Reviewer-accepted. Clean slice.",
                "- none",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.review_accepted)
            self.assertTrue(gate.review_gate_allows_push)

    def test_typed_path_rejects_when_verdict_not_accepted(self) -> None:
        """Typed path must reject when verdict is not accepted even if ack is current."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Several findings remain.",
                "- Bridge dirtiness coupling",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertFalse(gate.review_accepted)
            self.assertFalse(gate.review_gate_allows_push)

    def test_typed_path_prefers_publish_clear_from_reviewer_runtime(self) -> None:
        """Push gating should read the reviewer-runtime owner, not bridge acceptance alone."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Reviewer-accepted. Clean slice.",
                "- none",
                attention_status="review_loop_relaunch_required",
                typed_review_accepted=True,
                typed_publish_clear=False,
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.review_accepted)
            self.assertFalse(gate.review_gate_allows_push)

    def test_typed_path_blocks_new_implementation_when_ack_is_stale(self) -> None:
        """Active dual-agent stale ack should fail closed for new implementation slices."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Implementer ack is stale.",
                "- none",
                claude_ack_current=False,
                attention_status="claude_ack_stale",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.implementation_blocked)
            self.assertEqual(gate.implementation_block_reason, "claude_ack_stale")

    def test_typed_path_does_not_block_single_agent_lanes(self) -> None:
        """Single-agent reviewer mode should not trip the implementation block."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Single-agent review mode.",
                "- none",
                reviewer_mode="single_agent",
                claude_ack_current=False,
                attention_status="claude_ack_stale",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertFalse(gate.implementation_blocked)

    def test_typed_path_blocks_when_declared_dual_agent_is_not_live(self) -> None:
        """Dead dual-agent state must not count as live implementation authority."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Runtime is missing.",
                "- none",
                reviewer_mode="active_dual_agent",
                effective_reviewer_mode="tools_only",
                claude_ack_current=True,
                attention_status="runtime_missing",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.bridge_active)
            self.assertEqual(gate.reviewer_mode, "active_dual_agent")
            self.assertEqual(gate.effective_reviewer_mode, "tools_only")
            self.assertTrue(gate.implementation_blocked)
            self.assertEqual(gate.implementation_block_reason, "runtime_missing")

    def test_typed_path_promotes_live_remote_control_mode_over_raw_tools_only(
        self,
    ) -> None:
        """Live typed authority must override stale raw bridge reviewer_mode."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Checkpoint required.",
                "- none",
                reviewer_mode="tools_only",
                effective_reviewer_mode="active_dual_agent",
                claude_ack_current=True,
                attention_status="checkpoint_required",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.bridge_active)
            self.assertEqual(gate.reviewer_mode, "active_dual_agent")
            self.assertEqual(gate.effective_reviewer_mode, "active_dual_agent")

    def test_typed_path_uses_review_loop_relaunch_reason_for_detached_dual_agent(
        self,
    ) -> None:
        """Detached dual-agent state should request relaunch, not implementer reset."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Relaunch the reviewer loop before coding.",
                "- none",
                reviewer_mode="active_dual_agent",
                effective_reviewer_mode="tools_only",
                claude_ack_current=True,
                attention_status="review_loop_relaunch_required",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.bridge_active)
            self.assertEqual(gate.reviewer_mode, "active_dual_agent")
            self.assertEqual(gate.effective_reviewer_mode, "tools_only")
            self.assertTrue(gate.implementation_blocked)
            self.assertEqual(
                gate.implementation_block_reason,
                "review_loop_relaunch_required",
            )

    def test_typed_path_uses_review_loop_relaunch_reason_for_automation_only_poll(
        self,
    ) -> None:
        """Automation-only reviewer polling should still surface the relaunch reason."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Relaunch the reviewer loop before coding.",
                "- none",
                reviewer_mode="active_dual_agent",
                effective_reviewer_mode="tools_only",
                claude_ack_current=True,
                attention_status="review_loop_relaunch_required",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.bridge_active)
            self.assertEqual(gate.reviewer_mode, "active_dual_agent")
            self.assertEqual(gate.effective_reviewer_mode, "tools_only")
            self.assertTrue(gate.implementation_blocked)
            self.assertEqual(
                gate.implementation_block_reason,
                "review_loop_relaunch_required",
            )

    def test_typed_path_uses_governance_review_root_candidate(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Reviewer-accepted. Clean slice.",
                "- none",
            )
            portable_state = repo_root / "portable" / "review_state.json"
            portable_state.parent.mkdir(parents=True, exist_ok=True)
            portable_state.write_text(
                (
                    repo_root
                    / "dev"
                    / "reports"
                    / "review_channel"
                    / "projections"
                    / "latest"
                    / "review_state.json"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (
                repo_root
                / "dev"
                / "reports"
                / "review_channel"
                / "projections"
                / "latest"
                / "review_state.json"
            ).unlink()

            governance = replace(
                _minimal_governance(),
                artifact_roots=ArtifactRoots(
                    audit_root="",
                    review_root="portable",
                    governance_log_root="",
                    probe_report_root="",
                ),
            )
            gate = _detect_reviewer_gate(repo_root, governance=governance)

        self.assertTrue(gate.review_accepted)
        self.assertTrue(gate.review_gate_allows_push)

    def test_typed_path_does_not_block_when_implementer_was_freshly_reset_pending(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review. Fresh instruction reset is pending.",
                "- none",
                claude_ack_current=False,
                attention_status="claude_ack_stale",
            )
            state_path = (
                repo_root
                / "dev"
                / "reports"
                / "review_channel"
                / "projections"
                / "latest"
                / "review_state.json"
            )
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            payload["current_session"]["implementer_status"] = "- pending"
            payload["current_session"]["implementer_ack"] = "- pending"
            payload["current_session"]["implementer_ack_state"] = "pending"
            state_path.write_text(json.dumps(payload), encoding="utf-8")

            gate = _detect_reviewer_gate(repo_root)

        self.assertFalse(gate.implementation_blocked)

    def test_typed_path_requires_typed_state_when_bridge_exists(self) -> None:
        """When review_state.json is absent, startup stays fail-closed."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            bridge_text = "\n".join(
                (
                    "- Reviewer mode: `active_dual_agent`",
                    "",
                    "## Current Verdict",
                    "- Reviewer-accepted. Clean slice.",
                    "",
                    "## Open Findings",
                    "- none",
                    "",
                    "## Current Instruction For Claude",
                    "- Continue.",
                    "",
                )
            )
            (repo_root / "bridge.md").write_text(bridge_text, encoding="utf-8")
            gate = _detect_reviewer_gate(repo_root)
            self.assertFalse(gate.review_accepted)
            self.assertFalse(gate.review_gate_allows_push)
            self.assertTrue(gate.implementation_blocked)
            self.assertEqual(
                gate.implementation_block_reason,
                "typed_review_state_required",
            )

    @patch("dev.scripts.devctl.review_channel.state.refresh_status_snapshot")
    def test_typed_path_prefers_refreshed_review_state_projection(
        self,
        refresh_status_snapshot_mock,
    ) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "bridge.md").write_text("# Review Bridge\n", encoding="utf-8")
            review_channel_path = repo_root / "dev" / "active" / "review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
            state_path = (
                repo_root
                / "dev"
                / "reports"
                / "review_channel"
                / "latest"
                / "review_state.json"
            )
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "bridge": {
                            "reviewer_mode": "active_dual_agent",
                            "review_accepted": True,
                            "claude_ack_current": True,
                        },
                        "current_session": {
                            "implementer_ack_state": "current",
                        },
                    }
                ),
                encoding="utf-8",
            )

            def _refresh(*, repo_root, bridge_path, review_channel_path, output_root):
                state_path.write_text(
                    json.dumps(
                        {
                            "bridge": {
                                "reviewer_mode": "active_dual_agent",
                                "review_accepted": False,
                                "claude_ack_current": False,
                            },
                            "attention": {"status": "claude_ack_stale"},
                            "current_session": {
                                "implementer_status": "Working on a stale tranche.",
                                "implementer_ack": "Old ack",
                                "implementer_ack_state": "stale",
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return type(
                    "Snapshot",
                    (),
                    {
                        "projection_paths": type(
                            "ProjectionPaths",
                            (),
                            {"review_state_path": str(state_path)},
                        )()
                    },
                )()

            refresh_status_snapshot_mock.side_effect = _refresh
            governance = replace(
                _minimal_governance(),
                artifact_roots=ArtifactRoots(
                    audit_root="",
                    review_root="dev/reports/review_channel/latest",
                    governance_log_root="",
                    probe_report_root="",
                ),
                bridge_config=BridgeConfig(
                    bridge_path="bridge.md",
                    review_channel_path="dev/active/review_channel.md",
                    bridge_active=True,
                ),
            )

            gate = _detect_reviewer_gate(repo_root, governance=governance)

        self.assertFalse(gate.review_accepted)
        self.assertFalse(gate.review_gate_allows_push)
        self.assertTrue(gate.implementation_blocked)
        self.assertEqual(gate.implementation_block_reason, "claude_ack_stale")

    def test_typed_path_inactive_mode_permits_push(self) -> None:
        """When reviewer mode is inactive, push is permitted regardless."""
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._write_bridge_and_typed_state(
                repo_root,
                "Needs-review.",
                "- findings here",
                reviewer_mode="single_agent",
            )
            gate = _detect_reviewer_gate(repo_root)
            self.assertTrue(gate.review_gate_allows_push)
            self.assertFalse(gate.bridge_active)


class TestPushExclusionPaths(unittest.TestCase):
    """Verify non-authoritative paths are excluded from dirty count."""

    def test_worktree_change_counts_excludes_bridge(self) -> None:
        from dev.scripts.devctl.governance.push_state import _worktree_change_counts

        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            # Simulate a git repo with bridge.md dirty
            import subprocess

            subprocess.run(["git", "init"], cwd=tmp, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmp,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "test"], cwd=tmp, capture_output=True
            )
            (repo_root / "bridge.md").write_text("initial")
            (repo_root / "code.py").write_text("print('hello')")
            subprocess.run(["git", "add", "."], cwd=tmp, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"], cwd=tmp, capture_output=True
            )
            # Modify both files
            (repo_root / "bridge.md").write_text("modified bridge")
            (repo_root / "code.py").write_text("print('modified')")

            # Without exclusion: both files dirty
            dirty, untracked = _worktree_change_counts(repo_root)
            self.assertEqual(dirty, 2)

            # With exclusion: bridge excluded
            dirty, untracked = _worktree_change_counts(
                repo_root, exclude_paths=("bridge.md",)
            )
            self.assertEqual(dirty, 1)

    def test_checkpoint_policy_parses_compat_paths(self) -> None:
        from dev.scripts.devctl.governance.push_policy import PushCheckpointPolicy

        policy = PushCheckpointPolicy(
            compatibility_projection_paths=("bridge.md",),
        )
        self.assertEqual(policy.compatibility_projection_paths, ("bridge.md",))

    def test_worktree_change_counts_excludes_advisory_context(self) -> None:
        from dev.scripts.devctl.governance.push_state import _worktree_change_counts

        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            import subprocess

            subprocess.run(["git", "init"], cwd=tmp, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmp,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "test"],
                cwd=tmp,
                capture_output=True,
            )
            (repo_root / "code.py").write_text("print('hello')")
            subprocess.run(["git", "add", "."], cwd=tmp, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"], cwd=tmp, capture_output=True
            )
            (repo_root / "convo.md").write_text("scratch context")

            dirty, untracked = _worktree_change_counts(repo_root)
            self.assertEqual((dirty, untracked), (1, 1))

            dirty, untracked = _worktree_change_counts(
                repo_root,
                exclude_paths=("convo.md",),
            )
            self.assertEqual((dirty, untracked), (0, 0))

    def test_checkpoint_policy_parses_advisory_context_paths(self) -> None:
        from dev.scripts.devctl.governance.push_policy import PushCheckpointPolicy

        policy = PushCheckpointPolicy(advisory_context_paths=("convo.md",))

        self.assertEqual(policy.advisory_context_paths, ("convo.md",))

    def test_checkpoint_policy_default_empty(self) -> None:
        from dev.scripts.devctl.governance.push_policy import PushCheckpointPolicy

        policy = PushCheckpointPolicy()
        self.assertEqual(policy.compatibility_projection_paths, ())
        self.assertEqual(policy.advisory_context_paths, ())


class TestInteractionModeFromReviewerMode(unittest.TestCase):
    """Verify interaction_mode_from_reviewer_mode maps reviewer modes correctly."""

    def test_active_dual_agent_maps_to_dual_agent(self) -> None:
        self.assertEqual(
            interaction_mode_from_reviewer_mode("active_dual_agent"),
            "dual_agent",
        )

    def test_single_agent_maps_to_single_agent(self) -> None:
        self.assertEqual(
            interaction_mode_from_reviewer_mode("single_agent"),
            "single_agent",
        )

    def test_tools_only_maps_to_unresolved(self) -> None:
        self.assertEqual(
            interaction_mode_from_reviewer_mode("tools_only"),
            "unresolved",
        )

    def test_empty_string_fails_closed_to_unresolved(self) -> None:
        self.assertEqual(
            interaction_mode_from_reviewer_mode(""),
            "unresolved",
        )

    def test_governance_remote_control_without_attachment_falls_closed(self) -> None:
        """Per rev_pkt_3021 #3: governance_mode="remote_control" alone is
        NOT sufficient to promote operator location. Typed attachment
        evidence is required. Without an active attachment, derivation
        falls through to the reviewer_mode fallback, matching the
        fail-closed semantics already in operator_context.py and
        session_posture.py.
        """
        result = interaction_mode_from_reviewer_mode(
            "single_agent",
            governance_mode="remote_control",
        )
        self.assertEqual(result, "single_agent")

    def test_governance_remote_control_with_active_attachment_promotes(self) -> None:
        """Companion to ``..._falls_closed``: governance_mode declares
        intent + active typed attachment proves it -> promote to
        remote_control. This is the only path that promotes operator
        location, regardless of which signal arrives first.
        """
        from datetime import datetime, timezone

        live_now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = interaction_mode_from_reviewer_mode(
            "single_agent",
            governance_mode="remote_control",
            remote_control_attachment=RemoteControlAttachmentState(
                provider="claude",
                session_name="VoiceTerm Bridge Loop",
                remote_session_id="session_abc123",
                status="attached",
                attached_at_utc=live_now_utc,
                last_seen_utc=live_now_utc,
            ),
        )
        self.assertEqual(result, "remote_control")

    def test_governance_local_terminal_is_honored(self) -> None:
        # explicit local_terminal from governance is authoritative
        result = interaction_mode_from_reviewer_mode(
            "active_dual_agent",
            governance_mode="local_terminal",
        )
        self.assertEqual(result, "local_terminal")

    def test_governance_empty_falls_through(self) -> None:
        result = interaction_mode_from_reviewer_mode(
            "single_agent",
            governance_mode="",
        )
        self.assertEqual(result, "single_agent")

    def test_remote_control_attachment_promotes_remote_control_mode(self) -> None:
        # rev_pkt_2986 #4 + rev_pkt_2988 #5: ``remote_attachment_active``
        # is TTL-aware. An ``attached`` status with no heartbeat
        # timestamps is correctly classified as expired/stale, so the
        # fixture must carry a live ``last_seen_utc`` to represent a
        # genuinely active remote-control session.
        from datetime import datetime, timezone

        live_now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = interaction_mode_from_reviewer_mode(
            "single_agent",
            governance_mode="",
            remote_control_attachment=RemoteControlAttachmentState(
                provider="claude",
                session_name="VoiceTerm Bridge Loop",
                remote_session_id="session_abc123",
                status="attached",
                attached_at_utc=live_now_utc,
                last_seen_utc=live_now_utc,
            ),
        )
        self.assertEqual(result, "remote_control")


class TestReviewerGateOperatorInteractionMode(unittest.TestCase):
    """Verify ReviewerGateState carries operator_interaction_mode."""

    def test_default_is_unresolved(self) -> None:
        gate = ReviewerGateState()
        self.assertEqual(gate.operator_interaction_mode, "unresolved")

    def test_explicit_mode(self) -> None:
        gate = ReviewerGateState(operator_interaction_mode="remote_control")
        self.assertEqual(gate.operator_interaction_mode, "remote_control")

    def test_summary_includes_interaction_mode(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "clean_worktree",
                "reviewer_gate": {
                    "implementation_blocked": False,
                    "operator_interaction_mode": "dual_agent",
                },
                "startup_authority": {"ok": True},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                    },
                },
                "push_decision": {"action": "no_push_needed", "next_step_command": ""},
            }
        )
        self.assertIn("interaction_mode=dual_agent", rendered)

    def test_summary_missing_gate_defaults_to_unresolved(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "clean_worktree",
                "startup_authority": {"ok": True},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                    },
                },
                "push_decision": {"action": "no_push_needed", "next_step_command": ""},
            }
        )
        self.assertIn("interaction_mode=unresolved", rendered)

    def test_summary_includes_session_pacing_projection(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "bounded_slice_ready",
                "reviewer_gate": {
                    "implementation_blocked": False,
                    "operator_interaction_mode": "single_agent",
                },
                "startup_authority": {"ok": True},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                    },
                },
                "push_decision": {"action": "no_push_needed", "next_step_command": ""},
                "work_intake": {
                    "session_pacing": {
                        "complexity_band": "high",
                        "research_ref_budget": 7,
                        "focus_file_count": 2,
                        "dependency_edge_count": 5,
                        "live_finding_count": 3,
                        "hot_path_count": 4,
                        "implementation_trigger": "patch_after_bounded_refs_or_raise_blocker",
                    },
                },
            }
        )
        self.assertIn("session_pacing=high/7refs/2files/5deps", rendered)
        self.assertIn("pacing_live_findings=3", rendered)
        self.assertIn("pacing_hot_paths=4", rendered)
        self.assertIn(
            "pacing_trigger=patch_after_bounded_refs_or_raise_blocker",
            rendered,
        )

    def test_summary_includes_plan_routing_projection(self) -> None:
        rendered = _render_summary(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "bounded_slice_ready",
                "reviewer_gate": {
                    "implementation_blocked": False,
                    "operator_interaction_mode": "single_agent",
                },
                "startup_authority": {"ok": True},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                    },
                },
                "push_decision": {"action": "no_push_needed", "next_step_command": ""},
                "work_intake": {
                    "plan_routing": {
                        "phase_id": "MP377-P0",
                        "task_id": "MP377-P0-T01",
                    },
                },
            }
        )

        self.assertIn("plan_routing=MP377-P0/MP377-P0-T01", rendered)

    def test_markdown_includes_plan_routing_projection(self) -> None:
        rendered = _render_markdown(
            {
                "advisory_action": "continue_editing",
                "advisory_reason": "bounded_slice_ready",
                "reviewer_gate": {
                    "implementation_blocked": False,
                    "operator_interaction_mode": "single_agent",
                },
                "startup_authority": {"ok": True},
                "governance": {
                    "push_enforcement": {
                        "checkpoint_required": False,
                        "safe_to_continue_editing": True,
                    },
                },
                "push_decision": {"action": "no_push_needed", "next_step_command": ""},
                "work_intake": {
                    "routing": {},
                    "plan_routing": {
                        "phase_id": "MP377-P0",
                        "phase_title": "Phase P0 - Findings Spine And Plan Authority",
                        "phase_status": "in_progress",
                        "task_id": "MP377-P0-T01",
                        "task_summary": "Implement the canonical backlog reader/writer.",
                        "task_status": "in_progress",
                        "task_owner_doc": "dev/active/platform_authority_loop.md",
                        "dependencies": ["MP377-P0-T00"],
                    },
                    "session_pacing": {},
                },
            }
        )

        self.assertIn(
            "- plan_phase: `MP377-P0` | Phase P0 - Findings Spine And Plan Authority | status=`in_progress`",
            rendered,
        )
        self.assertIn(
            "- plan_task: `MP377-P0-T01` | Implement the canonical backlog reader/writer. | status=`in_progress`",
            rendered,
        )
        self.assertIn(
            "- plan_task_owner_doc: `dev/active/platform_authority_loop.md`", rendered
        )
        self.assertIn("- plan_dependencies: `MP377-P0-T00`", rendered)

    def test_machine_summary_includes_coordination_block(self) -> None:
        coordination = CoordinationSnapshot(
            current_slice="Wire startup summary from shared coordination.",
            declared_topology="multi_agent_orchestrated",
            observed_topology="single_agent",
            recommended_topology="single_agent",
            fanout_posture="planned_scaffolding_only",
            safe_to_fanout=False,
            worktree_strategy="isolated_worker_worktrees",
            resync_required=True,
            active_target=PlanTargetRef(
                target_id="target-1",
                plan_path="dev/active/remote_control_runtime.md",
                plan_title="Remote Control Runtime",
                plan_scope="MP-380..MP-387",
                target_kind="plan_doc",
                anchor_ref="section:execution-checklist",
                expected_revision="rev-1",
            ),
        )
        ctx = SimpleNamespace(
            advisory_action="continue_editing",
            advisory_reason="coordination_visible",
            reviewer_gate=SimpleNamespace(bridge_active=True),
            push_decision=SimpleNamespace(
                push_eligible_now=False,
                action="await_review",
                reason="review_pending",
                next_step_command="python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
                publication_backlog=SimpleNamespace(
                    backlog_state="none",
                    backlog_recommended=False,
                    backlog_urgent=False,
                ),
                publication_guidance="",
            ),
            coordination=coordination,
            work_intake=None,
        )

        summary = _machine_summary(
            ctx=ctx,
            push=None,
            authority_report={"ok": True},
            startup_receipt_path="dev/reports/startup/latest.json",
        )

        self.assertIn("coordination", summary)
        self.assertEqual(
            summary["coordination"]["current_slice"],
            "Wire startup summary from shared coordination.",
        )
        self.assertEqual(
            summary["coordination"]["recommended_topology"],
            "single_agent",
        )
        self.assertTrue(summary["coordination"]["resync_required"])


if __name__ == "__main__":
    unittest.main()
