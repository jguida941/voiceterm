"""Workflow-profile selection helpers for startup work intake."""

from __future__ import annotations

from dataclasses import dataclass

from .decision_explainability import rejected_rule_trace, rule_match_evidence
from .finding_contracts import RejectedRuleTraceRecord, RuleMatchEvidenceRecord


@dataclass(frozen=True, slots=True)
class WorkflowProfileSelection:
    """Selected workflow profile plus explanation fields."""

    profile: str
    rule_summary: str
    match_evidence: tuple[RuleMatchEvidenceRecord, ...]
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...]


def select_workflow_profile(
    workflow_profiles: tuple[str, ...],
    *,
    advisory_action: str,
    post_push_bundle: str,
) -> WorkflowProfileSelection:
    """Select the best workflow profile for the startup intake packet."""
    if advisory_action == "push_allowed" and post_push_bundle in workflow_profiles:
        return WorkflowProfileSelection(
            profile=post_push_bundle,
            rule_summary=(
                "Startup selected the post-push workflow profile because the "
                "repo is already eligible for the governed push path."
            ),
            match_evidence=(
                rule_match_evidence(
                    "work_intake.select_post_push_bundle",
                    "The repo is push-ready and the configured post-push bundle is available.",
                    f"advisory_action={advisory_action}",
                    f"post_push_bundle={post_push_bundle}",
                ),
            ),
            rejected_rule_traces=tuple(
                rule
                for rule in (
                    (
                        rejected_rule_trace(
                            "work_intake.prefer_bundle_tooling",
                            "Prefer `bundle.tooling` when startup is still in an edit-first state.",
                            "Startup is already push-ready, so the post-push bundle takes priority.",
                        )
                        if "bundle.tooling" in workflow_profiles
                        else None
                    ),
                    rejected_rule_trace(
                        "work_intake.fallback_first_profile",
                        "Fall back to the first advertised workflow profile.",
                        "An explicit post-push bundle matched, so the generic fallback is unnecessary.",
                    ),
                )
                if rule is not None
            ),
        )
    if "bundle.tooling" in workflow_profiles:
        return WorkflowProfileSelection(
            profile="bundle.tooling",
            rule_summary=(
                "Startup selected `bundle.tooling` as the default maintainer "
                "workflow profile because no push-ready post-push handoff applies yet."
            ),
            match_evidence=(
                rule_match_evidence(
                    "work_intake.prefer_bundle_tooling",
                    "The repo advertises `bundle.tooling` and startup is still in an edit-first state.",
                    "bundle.tooling is present in workflow_profiles",
                    f"advisory_action={advisory_action}",
                ),
            ),
            rejected_rule_traces=tuple(
                rule
                for rule in (
                    (
                        rejected_rule_trace(
                            "work_intake.select_post_push_bundle",
                            "Select the configured post-push bundle when startup is push-ready.",
                            "The current startup action is not `push_allowed`.",
                            f"advisory_action={advisory_action}",
                        )
                        if post_push_bundle
                        else None
                    ),
                    rejected_rule_trace(
                        "work_intake.fallback_first_profile",
                        "Fall back to the first advertised workflow profile.",
                        "`bundle.tooling` is available, so the explicit tooling default wins.",
                    ),
                )
                if rule is not None
            ),
        )
    if post_push_bundle and post_push_bundle in workflow_profiles:
        return WorkflowProfileSelection(
            profile=post_push_bundle,
            rule_summary=(
                "Startup fell back to the configured post-push bundle because "
                "`bundle.tooling` is unavailable but repo policy still names a governed workflow."
            ),
            match_evidence=(
                rule_match_evidence(
                    "work_intake.fallback_to_post_push_bundle",
                    "Repo policy still provides a named bundle after `bundle.tooling` drops out.",
                    f"post_push_bundle={post_push_bundle}",
                    "bundle.tooling not present in workflow_profiles",
                ),
            ),
            rejected_rule_traces=(
                rejected_rule_trace(
                    "work_intake.prefer_bundle_tooling",
                    "Prefer `bundle.tooling` when it is available.",
                    "`bundle.tooling` is not present in the advertised workflow profiles.",
                ),
                rejected_rule_trace(
                    "work_intake.fallback_first_profile",
                    "Fall back to the first advertised workflow profile.",
                    "Repo policy already named a more specific bundle.",
                ),
            ),
        )
    fallback = workflow_profiles[0] if workflow_profiles else ""
    return WorkflowProfileSelection(
        profile=fallback,
        rule_summary=(
            "Startup fell back to the first advertised workflow profile because "
            "no explicit tooling default or post-push bundle matched."
            if fallback
            else "No workflow profile could be selected because ProjectGovernance advertised none."
        ),
        match_evidence=(
            rule_match_evidence(
                "work_intake.fallback_first_profile",
                "No specific workflow-profile rule matched, so startup used the first advertised option.",
                f"workflow_profiles={', '.join(workflow_profiles) or '(none)'}",
            ),
        ),
        rejected_rule_traces=(
            rejected_rule_trace(
                "work_intake.prefer_bundle_tooling",
                "Prefer `bundle.tooling` when it is available.",
                "`bundle.tooling` is not present in the advertised workflow profiles.",
            ),
            rejected_rule_trace(
                "work_intake.select_post_push_bundle",
                "Select the configured post-push bundle when startup is push-ready and the bundle is available.",
                "The required bundle was unavailable or the repo is not push-ready.",
                f"advisory_action={advisory_action}",
                f"post_push_bundle={post_push_bundle or '(none)'}",
            ),
        ),
    )


__all__ = ["WorkflowProfileSelection", "select_workflow_profile"]
