# Claude Instructions

This file is generated from the `{{repo_pack_id}}` repo-pack surface policy.
The canonical SDLC + documentation policy lives in `{{process_doc}}`. Read it
and follow it for any non-trivial task. Keep AI notes local-only (this file is
gitignored).

## Bootstrap (read on every session start)

{{bootstrap_steps}}

## Project: {{product_name}} ({{repo_name}})

- **What**: {{project_summary}}
- **Rust source**: `{{rust_source}}`
- **Python tooling**: `{{python_tooling}}`
- **Guard scripts**: `{{guard_scripts}}`
- **MSRV**: {{msrv}}
- **Branches**: {{branch_policy}}

## Source-of-truth quick map

| What | Where |
|---|---|
| Execution state | `{{execution_tracker_doc}}` |
| Active doc registry | `{{active_registry_doc}}` |
| SDLC / process | `{{process_doc}}` |
| Architecture | `{{architecture_doc}}` |
| Build/test/release | `{{development_doc}}` |
| devctl commands | `{{scripts_readme_doc}}` |
| CLI flags | `{{cli_flags_doc}}` |
| CI workflows | `{{ci_workflows_doc}}` |

## Key commands

```bash
{{key_commands_block}}
```

## Mandatory post-edit verification (blocking)

{{post_edit_verification_intro}}

{{post_edit_verification_steps}}

{{post_edit_verification_done_criteria}}

## Guard-enforced limits (CI will block violations)

{{guard_limits_block}}

## User preferences

{{user_preferences_block}}
