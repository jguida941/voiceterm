"""Shared VCS test push-policy builders."""

from __future__ import annotations

from dev.scripts.devctl.governance.push_policy import (
    PushBypassPolicy,
    PushCheckpointPolicy,
    PushPolicy,
    PushPostPushPolicy,
    PushPreflightPolicy,
    PushPublicationPolicy,
)


def build_test_push_policy() -> PushPolicy:
    return PushPolicy(
        policy_path="dev/config/devctl_repo_policy.json",
        repo_pack_id="test-pack",
        warnings=(),
        default_remote="origin",
        development_branch="develop",
        release_branch="master",
        protected_branches=("develop", "master"),
        allowed_branch_prefixes=("feature/",),
        preflight=PushPreflightPolicy(),
        post_push=PushPostPushPolicy(bundle="bundle.post-push"),
        bypass=PushBypassPolicy(allow_skip_preflight=True),
        checkpoint=PushCheckpointPolicy(
            compatibility_projection_paths=("dev/reports/push/latest.json",)
        ),
        publication=PushPublicationPolicy(),
    )
