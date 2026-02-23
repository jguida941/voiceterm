"""Profile rules for `devctl check`.

Use this module when you need to change what a profile enables or disables.
We keep profile logic here so it is not duplicated across commands/tests.
"""

from __future__ import annotations

# Maintainer lint is strict, but excludes known noisy cast lints for now.
MAINTAINER_LINT_CLIPPY_ARGS = [
    "-W",
    "clippy::redundant_clone",
    "-W",
    "clippy::redundant_closure_for_method_calls",
    "-W",
    "clippy::cast_possible_wrap",
    "-W",
    "dead_code",
]


def resolve_profile_settings(args) -> tuple[dict, list[str]]:
    """Return final check-step flags and clippy command for the selected profile."""
    settings = {
        "skip_build": args.skip_build,
        "skip_tests": args.skip_tests,
        "with_perf": args.with_perf,
        "with_mem_loop": args.with_mem_loop,
        "with_mutants": args.with_mutants,
        "with_mutation_score": args.with_mutation_score,
        "with_wake_guard": args.with_wake_guard,
        "with_ai_guard": args.with_ai_guard,
    }
    clippy_cmd = ["cargo", "clippy", "--workspace", "--all-features", "--", "-D", "warnings"]

    if args.profile == "ci":
        settings.update(
            {
                "skip_build": True,
                "with_perf": False,
                "with_mem_loop": False,
                "with_mutants": False,
                "with_mutation_score": False,
                "with_wake_guard": False,
                "with_ai_guard": False,
            }
        )
    elif args.profile == "prepush":
        settings.update({"with_perf": True, "with_mem_loop": True, "with_ai_guard": True})
    elif args.profile == "release":
        settings.update(
            {"with_mutation_score": True, "with_wake_guard": True, "with_ai_guard": True}
        )
    elif args.profile == "ai-guard":
        settings.update(
            {
                "skip_build": True,
                "with_perf": False,
                "with_mem_loop": False,
                "with_mutants": False,
                "with_mutation_score": False,
                "with_wake_guard": False,
                "with_ai_guard": True,
            }
        )
    elif args.profile == "maintainer-lint":
        settings.update(
            {
                "skip_tests": True,
                "skip_build": True,
                "with_perf": False,
                "with_mem_loop": False,
                "with_mutants": False,
                "with_mutation_score": False,
                "with_wake_guard": False,
                "with_ai_guard": False,
            }
        )
        clippy_cmd = [
            "cargo",
            "clippy",
            "--workspace",
            "--all-features",
            "--",
            "-D",
            "warnings",
            *MAINTAINER_LINT_CLIPPY_ARGS,
        ]
    elif args.profile == "quick":
        settings.update(
            {
                "skip_build": True,
                "skip_tests": True,
                "with_wake_guard": False,
                "with_ai_guard": False,
            }
        )

    return settings, clippy_cmd
