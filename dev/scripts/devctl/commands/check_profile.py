"""Profile rules and conflict detection for `devctl check`.

Use this module when you need to change what a profile enables or disables.
We keep profile logic here so it is not duplicated across commands/tests.
The preset definitions also drive conflict detection, so adding or changing
a profile only requires one update.
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

# ---------------------------------------------------------------------------
# Profile preset definitions (single source of truth).
#
# Each profile entry maps flag names to the values the profile forces.
# Only flags that a profile explicitly overrides are listed; flags not listed
# are left at whatever the user supplied (no conflict possible).
# ---------------------------------------------------------------------------

PROFILE_PRESETS: dict[str, dict[str, object]] = {
    "ci": {
        "skip_build": True,
        "with_perf": False,
        "with_mem_loop": False,
        "with_mutants": False,
        "with_mutation_score": False,
        "with_wake_guard": False,
        "with_ai_guard": False,
        "with_ci_release_gate": False,
    },
    "prepush": {
        "with_perf": True,
        "with_mem_loop": True,
        "with_ai_guard": True,
        "with_ci_release_gate": False,
    },
    "release": {
        "with_mutation_score": True,
        "with_wake_guard": True,
        "with_ai_guard": True,
        "with_ci_release_gate": True,
    },
    "ai-guard": {
        "skip_build": True,
        "with_perf": False,
        "with_mem_loop": False,
        "with_mutants": False,
        "with_mutation_score": False,
        "with_wake_guard": False,
        "with_ai_guard": True,
        "with_ci_release_gate": False,
    },
    "maintainer-lint": {
        "skip_tests": True,
        "skip_build": True,
        "with_perf": False,
        "with_mem_loop": False,
        "with_mutants": False,
        "with_mutation_score": False,
        "with_wake_guard": False,
        "with_ai_guard": False,
        "with_ci_release_gate": False,
    },
    "quick": {
        "skip_build": True,
        "skip_tests": True,
        "with_wake_guard": False,
        "with_ai_guard": False,
        "with_ci_release_gate": False,
    },
}

# Argparse defaults for boolean flags. When a flag's value differs from its
# default, the user explicitly set it on the command line.
BOOLEAN_FLAG_DEFAULTS: dict[str, bool] = {
    "skip_fmt": False,
    "skip_clippy": False,
    "skip_tests": False,
    "skip_build": False,
    "fix": False,
    "with_perf": False,
    "with_mem_loop": False,
    "with_wake_guard": False,
    "with_ai_guard": False,
    "with_mutants": False,
    "with_mutation_score": False,
    "no_parallel": False,
    "keep_going": False,
}


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
        "with_ci_release_gate": False,
    }
    clippy_cmd = ["cargo", "clippy", "--workspace", "--all-features", "--", "-D", "warnings"]

    profile = getattr(args, "profile", None)
    preset = PROFILE_PRESETS.get(profile or "")
    if preset:
        settings.update(preset)
        if profile == "maintainer-lint":
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

    return settings, clippy_cmd


def validate_profile_flag_conflicts(args) -> list[str]:
    """Return warning messages when individual flags conflict with a profile.

    A conflict exists when the user explicitly passes a flag whose value
    differs from, or is redundant with, what the profile forces.  Flags
    at their argparse default are assumed *not* explicitly set and are
    silently ignored.
    """
    profile = getattr(args, "profile", None)
    if not profile:
        return []

    preset = PROFILE_PRESETS.get(profile)
    if preset is None:
        return []

    warnings: list[str] = []

    # --- check flags that the profile overrides ---
    for flag, forced_value in preset.items():
        user_value = getattr(args, flag, BOOLEAN_FLAG_DEFAULTS.get(flag))
        default_value = BOOLEAN_FLAG_DEFAULTS.get(flag)
        # Only warn when the user explicitly changed the flag from its default.
        if user_value == default_value:
            continue
        if user_value == forced_value:
            warnings.append(
                f"--{flag.replace('_', '-')} is redundant with --profile {profile} "
                f"(profile already sets {flag}={forced_value})"
            )
        else:
            warnings.append(
                f"--{flag.replace('_', '-')} conflicts with --profile {profile} "
                f"(profile forces {flag}={forced_value}; your flag will be overridden)"
            )

    # --- check flags that the profile does NOT override but may still conflict ---
    for flag in ("skip_fmt", "skip_clippy"):
        user_value = getattr(args, flag, False)
        if user_value and flag not in preset:
            warnings.append(
                f"--{flag.replace('_', '-')} was passed alongside --profile {profile}; "
                f"the profile does not control this flag, so it will take effect"
            )

    # no_parallel / keep_going: not set by profiles but worth noting.
    if getattr(args, "no_parallel", False) and "no_parallel" not in preset:
        warnings.append(
            f"--no-parallel was passed alongside --profile {profile}; "
            f"the profile does not control parallelism, so sequential mode will take effect"
        )
    if getattr(args, "keep_going", False) and "keep_going" not in preset:
        warnings.append(
            f"--keep-going was passed alongside --profile {profile}; "
            f"the profile does not control keep-going, so it will take effect"
        )

    return warnings
