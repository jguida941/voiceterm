# CodeRabbit

Canonical home for CodeRabbit triage and Ralph remediation helpers.

- `bridge.py`: canonical workflow entrypoint for triage collect/enforce steps.
- `collect.py`: normalized finding collection logic.
- `support.py`: PR/repo resolution and severity/category helpers.
- `ralph_ai_fix.py`: canonical Ralph remediation entrypoint; still repo-local
  until the remaining guardrail policy extraction lands.
