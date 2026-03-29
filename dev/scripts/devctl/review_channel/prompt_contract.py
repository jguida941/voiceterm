"""Shared governance contract lines injected into conductor prompts."""

from __future__ import annotations

from pathlib import Path

from ..governance.repo_policy import load_repo_governance_section

DEFAULT_POST_EDIT_VERIFICATION_INTRO = (
    "After EVERY file create/edit, you MUST run the repo-required verification "
    "before reporting the task as done."
)
DEFAULT_POST_EDIT_VERIFICATION_STEPS = (
    "Run the task-class bundle from `AGENTS.md` after every file create/edit: "
    "`bundle.runtime`, `bundle.docs`, `bundle.tooling`, or `bundle.release`.",
    "Run any additional path or risk checks required by `AGENTS.md` and "
    "`dev/guides/DEVELOPMENT.md#after-file-edits`.",
    "For complex edits, refactors, new modules, or business-logic changes, run "
    "`python3 dev/scripts/devctl.py check --profile ci`.",
    "If you changed repo-pack templates, repo policy, or generated instruction "
    "surfaces, run `python3 dev/scripts/devctl.py render-surfaces --write --format md` "
    "and `python3 dev/scripts/checks/check_instruction_surface_sync.py`.",
    "`python3 dev/scripts/devctl.py check --profile quick` is only a fast local "
    "iteration step; it does not replace the required bundle or handoff verification.",
)
DEFAULT_POST_EDIT_VERIFICATION_DONE_CRITERIA = (
    "Done means the required guards/tests passed. Do not report completion after "
    "only writing code or running a partial subset of checks. If a required guard "
    "fails, fix it or report the blocker explicitly."
)


def shared_post_edit_verification_lines(*, repo_root: Path) -> list[str]:
    """Return the shared post-edit contract from repo policy or defaults."""
    intro = DEFAULT_POST_EDIT_VERIFICATION_INTRO
    steps = list(DEFAULT_POST_EDIT_VERIFICATION_STEPS)
    done_criteria = DEFAULT_POST_EDIT_VERIFICATION_DONE_CRITERIA
    section, _warnings, _resolved_path = load_repo_governance_section(
        "surface_generation",
        repo_root=repo_root,
    )
    context = section.get("context")
    if isinstance(context, dict):
        intro_value = context.get("post_edit_verification_intro")
        if isinstance(intro_value, str) and intro_value.strip():
            intro = intro_value.strip()
        steps_value = context.get("post_edit_verification_steps")
        parsed_steps = _policy_step_list(steps_value)
        if parsed_steps:
            steps = parsed_steps
        done_value = context.get("post_edit_verification_done_criteria")
        if isinstance(done_value, str) and done_value.strip():
            done_criteria = done_value.strip()
    return [
        "- Shared post-edit verification contract: this live conductor prompt and "
        "the generated `CLAUDE.md` surface must stay aligned.",
        f"- {intro}",
        *[f"- {step}" for step in steps],
        f"- {done_criteria}",
    ]


def _policy_step_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    steps: list[str] = []
    for entry in value:
        text = str(entry).strip()
        if text:
            steps.append(text)
    return steps
