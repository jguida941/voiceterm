"""Tests for governed push report diagnostics."""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.devctl.commands.vcs.push_report import (
    PushReportInputs,
    PushStageTruth,
    build_push_report,
    render_push_report,
)


def _policy() -> SimpleNamespace:
    return SimpleNamespace(
        policy_path="dev/config/push_policy.json",
        development_branch="develop",
        release_branch="master",
        protected_branches=("develop", "master"),
        allowed_branch_prefixes=("feature/",),
        bypass=SimpleNamespace(
            allow_skip_preflight=False,
            allow_skip_post_push=False,
        ),
    )


def _inputs(**overrides: object) -> PushReportInputs:
    values: dict[str, object] = {
        "policy": _policy(),
        "branch": "feature/demo",
        "remote": "origin",
        "head_commit": "abc123",
        "execute": False,
        "skip_preflight": False,
        "skip_post_push": False,
        "dirty_paths": [],
        "fetch_step": None,
        "preflight_step": None,
        "push_step": None,
        "post_push_steps": [],
        "push_stages": PushStageTruth(validation_ready=True),
        "typed_action": {},
        "action_result": {"ok": True, "reason": "execute_flag_required"},
        "warnings": [],
        "errors": [],
    }
    values.update(overrides)
    return PushReportInputs(**values)


def test_push_report_marks_validation_ready_execute_required() -> None:
    report = build_push_report(_inputs())

    assert report["push_diagnostic"] == {
        "summary": "validation_ready_execute_required",
        "validation_state": "passed",
        "publication_state": "awaiting_execute",
        "git_push_state": "not_attempted",
        "post_push_state": "not_started",
    }


def test_push_report_marks_publication_authorization_review_wait() -> None:
    report = build_push_report(
        _inputs(
            execute=True,
            push_stages=PushStageTruth(),
            action_result={"ok": False, "reason": "validation_failed"},
            errors=[
                "Publication authorization blocks `devctl push`: "
                "reason=`operator_approval_pending`."
            ],
        )
    )

    assert report["push_diagnostic"]["summary"] == "publication_awaiting_review"
    assert report["push_diagnostic"]["publication_state"] == "awaiting_review"


def test_push_report_marks_remote_published_post_push_pending() -> None:
    report = build_push_report(
        _inputs(
            execute=True,
            push_stages=PushStageTruth(
                validation_ready=True,
                published_remote=True,
            ),
            action_result={"ok": False, "reason": "post_push_bundle_failed"},
            push_step={
                "name": "git-push",
                "cmd": ["git", "push", "origin", "feature/demo"],
                "returncode": 0,
            },
            post_push_steps=[
                {
                    "name": "push-post-01",
                    "cmd": ["make", "verify"],
                    "returncode": 1,
                }
            ],
        )
    )

    assert report["published_remote"] is True
    assert report["post_push_green"] is False
    assert report["push_diagnostic"]["summary"] == "remote_published_post_push_pending"
    assert report["push_diagnostic"]["git_push_state"] == "landed"
    assert report["push_diagnostic"]["post_push_state"] == "failed"


def test_push_report_names_push_report_artifact_explicitly() -> None:
    report = build_push_report(
        _inputs(artifact_path="dev/reports/push/latest_push_report.json")
    )

    assert report["artifacts"]["push_report_json"] == (
        "dev/reports/push/latest_push_report.json"
    )
    assert report["artifacts"]["latest_json"] == (
        "dev/reports/push/latest_push_report.json"
    )
    rendered = render_push_report(report)
    assert "- push_report_json: dev/reports/push/latest_push_report.json" in rendered
    assert "- latest_json:" not in rendered


def test_push_report_marks_already_pushed_without_git_push_attempt() -> None:
    report = build_push_report(
        _inputs(
            execute=True,
            action_result={"ok": True, "reason": "branch_already_pushed"},
            push_stages=PushStageTruth(
                validation_ready=True,
                published_remote=True,
            ),
            push_step=None,
            post_push_steps=[],
        )
    )

    assert report["published_remote"] is True
    assert report["push_diagnostic"] == {
        "summary": "remote_already_published_post_push_pending",
        "validation_state": "passed",
        "publication_state": "already_published",
        "git_push_state": "not_required",
        "post_push_state": "pending",
    }
