"""Bootstrap-command inventory for generated AI/operator surfaces."""

from __future__ import annotations

from .system_catalog_models import CatalogBootstrapCommand, CatalogBootstrapLinks


def _entry(
    command_id: str,
    label: str,
    command: str,
    description: str,
    links: CatalogBootstrapLinks | None = None,
) -> CatalogBootstrapCommand:
    """Build one typed bootstrap-command entry."""
    relations = links or CatalogBootstrapLinks()
    return CatalogBootstrapCommand(
        command_id=command_id,
        label=label,
        command=command,
        description=description,
        command_names=relations.command_names,
        guard_ids=relations.guard_ids,
        probe_ids=relations.probe_ids,
        surface_ids=relations.surface_ids,
        contract_ids=relations.contract_ids,
        plan_paths=relations.plan_paths,
    )


def _startup_bootstrap_commands(
    *,
    guard_ids: tuple[str, ...] = (),
    probe_ids: tuple[str, ...] = (),
) -> tuple[CatalogBootstrapCommand, ...]:
    """Return the startup and policy-facing bootstrap entries."""
    from ..runtime.conductor_capability import (
        context_graph_bootstrap_command,
        session_resume_command_for_role,
    )

    return (
        _entry(
            command_id="context_graph_bootstrap",
            label="Slim bootstrap packet",
            command=context_graph_bootstrap_command(),
            description="Repo identity, active plans, hotspots, key commands, and quality signals.",
            links=CatalogBootstrapLinks(
                command_names=("context-graph",),
                contract_ids=("ContextGraphSnapshot", "BootstrapContext"),
                plan_paths=("dev/active/ai_governance_platform.md",),
            ),
        ),
        _entry(
            command_id="startup_context_summary",
            label="Typed startup packet",
            command="python3 dev/scripts/devctl.py startup-context --format summary",
            description="Canonical Step-0 repo receipt before edits or launches.",
            links=CatalogBootstrapLinks(
                command_names=("startup-context",),
                contract_ids=("StartupContext", "WorkIntakePacket"),
                plan_paths=("dev/active/platform_authority_loop.md",),
            ),
        ),
        _entry(
            command_id="session_resume_reviewer",
            label="Reviewer bootstrap packet",
            command=session_resume_command_for_role("reviewer"),
            description="Role-bound reviewer starter packet.",
            links=CatalogBootstrapLinks(
                command_names=("session-resume",),
                contract_ids=("ReviewState", "CoordinationSnapshot"),
                plan_paths=(
                    "dev/active/review_channel.md",
                    "dev/active/remote_control_runtime.md",
                ),
            ),
        ),
        _entry(
            command_id="session_resume_implementer",
            label="Implementer bootstrap packet",
            command=session_resume_command_for_role("implementer"),
            description="Role-bound implementer starter packet.",
            links=CatalogBootstrapLinks(
                command_names=("session-resume",),
                contract_ids=("ReviewState", "CoordinationSnapshot"),
                plan_paths=(
                    "dev/active/review_channel.md",
                    "dev/active/remote_control_runtime.md",
                ),
            ),
        ),
        _entry(
            command_id="governed_push_execute",
            label="Governed push execute",
            command="python3 dev/scripts/devctl.py push --execute",
            description="Canonical publish path after checkpoint and review clearance.",
            links=CatalogBootstrapLinks(
                command_names=("push",),
                contract_ids=("PushDecisionState",),
                plan_paths=("dev/active/remote_commit_pipeline.md",),
            ),
        ),
        _entry(
            command_id="context_graph_diff",
            label="Saved graph diff",
            command="python3 dev/scripts/devctl.py context-graph --mode diff --from previous --to latest --format md",
            description="Typed graph delta over saved baselines.",
            links=CatalogBootstrapLinks(
                command_names=("context-graph",),
                contract_ids=("ContextGraphSnapshot",),
                plan_paths=("dev/active/ai_governance_platform.md",),
            ),
        ),
        _entry(
            command_id="quality_policy",
            label="Quality policy catalog",
            command="python3 dev/scripts/devctl.py quality-policy --format md",
            description="Resolved enabled guard/probe inventory and policy surface.",
            links=CatalogBootstrapLinks(
                command_names=("quality-policy",),
                guard_ids=guard_ids,
                probe_ids=probe_ids,
                contract_ids=("ProjectGovernance", "SystemCatalog"),
                plan_paths=("dev/active/ai_governance_platform.md",),
            ),
        ),
        _entry(
            command_id="check_ci",
            label="Routed CI guard bundle",
            command="python3 dev/scripts/devctl.py check --profile ci",
            description="Repo-owned blocking guard bundle for substantive edits.",
            links=CatalogBootstrapLinks(
                command_names=("check",),
                guard_ids=guard_ids,
                probe_ids=probe_ids,
                contract_ids=("AgentDispatchPacket", "SystemCatalog"),
            ),
        ),
        _entry(
            command_id="probe_report",
            label="Probe hotspot packet",
            command="python3 dev/scripts/devctl.py probe-report --format md",
            description="Non-blocking design-quality guidance and hot files.",
            links=CatalogBootstrapLinks(
                command_names=("probe-report",),
                probe_ids=probe_ids,
            ),
        ),
    )


def _review_bootstrap_commands() -> tuple[CatalogBootstrapCommand, ...]:
    """Return review-channel and governance-review bootstrap entries."""
    return (
        _entry(
            command_id="governance_review_summary",
            label="Governance review summary",
            command="python3 dev/scripts/devctl.py governance-review --format md",
            description="Recent adjudicated findings and cleanup state.",
            links=CatalogBootstrapLinks(
                command_names=("governance-review",),
                plan_paths=("dev/active/review_probes.md",),
            ),
        ),
        _entry(
            command_id="governance_review_record",
            label="Governance review record",
            command="python3 dev/scripts/devctl.py governance-review --record --signal-type probe --check-id probe_exception_quality --verdict fixed --path dev/scripts/devctl/example.py --line 41 --finding-class rule_quality --recurrence-risk recurring --prevention-surface probe --guidance-id probe_exception_quality@dev/scripts/devctl/example.py:41 --guidance-followed true --format md",
            description="Canonical adjudication writeback path for probe/guard/audit outcomes.",
            links=CatalogBootstrapLinks(
                command_names=("governance-review",),
                plan_paths=("dev/active/review_probes.md",),
            ),
        ),
        _entry(
            command_id="review_status",
            label="Review status",
            command="python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
            description="Canonical typed review/runtime status surface.",
            links=CatalogBootstrapLinks(
                command_names=("review-channel",),
                contract_ids=("ReviewState", "CoordinationSnapshot"),
                plan_paths=(
                    "dev/active/review_channel.md",
                    "dev/active/remote_control_runtime.md",
                ),
            ),
        ),
        _entry(
            command_id="review_ensure_follow",
            label="Review ensure follow",
            command="python3 dev/scripts/devctl.py review-channel --action ensure --follow --terminal none --format json",
            description="Repo-owned live follow loop for review status.",
            links=CatalogBootstrapLinks(
                command_names=("review-channel",),
                contract_ids=("ReviewState", "CoordinationSnapshot"),
                plan_paths=(
                    "dev/active/review_channel.md",
                    "dev/active/remote_control_runtime.md",
                ),
            ),
        ),
        _entry(
            command_id="reviewer_checkpoint",
            label="Reviewer checkpoint",
            command="python3 dev/scripts/devctl.py review-channel --action reviewer-checkpoint --reviewer-mode active_dual_agent --reason review-pass --checkpoint-payload-file /tmp/reviewer-checkpoint.json --expected-instruction-revision <live-revision> --expected-implementer-state-hash <live-implementer-state-hash> --terminal none --format md",
            description="Reviewer-owned checkpoint and promotion write path.",
            links=CatalogBootstrapLinks(
                command_names=("review-channel",),
                contract_ids=("ReviewState", "CoordinationSnapshot"),
                plan_paths=("dev/active/review_channel.md",),
            ),
        ),
        _entry(
            command_id="implementer_wait",
            label="Implementer wait",
            command="python3 dev/scripts/devctl.py review-channel --action implementer-wait --reason awaiting-reviewer --terminal none --format json",
            description="Typed bounded wait path for implementer sessions.",
            links=CatalogBootstrapLinks(
                command_names=("review-channel",),
                contract_ids=("ReviewState", "CoordinationSnapshot"),
                plan_paths=("dev/active/review_channel.md",),
            ),
        ),
        _entry(
            command_id="reviewer_wait",
            label="Reviewer wait",
            command="python3 dev/scripts/devctl.py review-channel --action reviewer-wait --reason awaiting-implementer --terminal none --format json",
            description="Typed bounded wait path for reviewer sessions.",
            links=CatalogBootstrapLinks(
                command_names=("review-channel",),
                contract_ids=("ReviewState", "CoordinationSnapshot"),
                plan_paths=("dev/active/review_channel.md",),
            ),
        ),
        _entry(
            command_id="review_packet_watch",
            label="Reviewer packet watch",
            command="python3 dev/scripts/devctl.py review-channel --action watch --target claude --status pending --follow --terminal none --format json",
            description="Packet watch surface for reviewer-side pending work.",
            links=CatalogBootstrapLinks(
                command_names=("review-channel",),
                contract_ids=("ReviewState", "CoordinationSnapshot"),
                plan_paths=("dev/active/review_channel.md",),
            ),
        ),
    )


def _maintenance_bootstrap_commands(
    *,
    surface_ids: tuple[str, ...] = (),
) -> tuple[CatalogBootstrapCommand, ...]:
    """Return maintainer-surface upkeep bootstrap entries."""
    return (
        _entry(
            command_id="docs_check_strict_tooling",
            label="Docs governance",
            command="python3 dev/scripts/devctl.py docs-check --strict-tooling",
            description="Maintainer-doc governance and sync checks.",
            links=CatalogBootstrapLinks(command_names=("docs-check",)),
        ),
        _entry(
            command_id="render_surfaces_write",
            label="Surface refresh",
            command="python3 dev/scripts/devctl.py render-surfaces --write --format md",
            description="Regenerate repo-owned instruction and starter surfaces.",
            links=CatalogBootstrapLinks(
                command_names=("render-surfaces",),
                surface_ids=surface_ids,
                contract_ids=("SystemCatalog",),
            ),
        ),
    )


def collect_bootstrap_commands(
    *,
    guard_ids: tuple[str, ...] = (),
    probe_ids: tuple[str, ...] = (),
    surface_ids: tuple[str, ...] = (),
) -> tuple[CatalogBootstrapCommand, ...]:
    """Build the generated bootstrap command inventory for AI surfaces."""
    return (
        *_startup_bootstrap_commands(
            guard_ids=guard_ids,
            probe_ids=probe_ids,
        ),
        *_review_bootstrap_commands(),
        *_maintenance_bootstrap_commands(surface_ids=surface_ids),
    )
