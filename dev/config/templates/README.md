# Templates

Reusable starter artifacts for governance exports, repo onboarding, and audit
scaffolds.

- `portable_devctl_repo_policy.template.json`: generic starter policy a new
  repo can copy or compare against when adopting the portable guard/probe
  engine.
- `claude_instructions.template.md`: repo-pack template used by
  `render-surfaces` to generate local `CLAUDE.md` instructions.
- `codex_voice_slash.template.md`: repo-pack template for the generated Codex
  `/voice` slash command.
- `claude_voice_skill.template.md`: repo-pack template for the generated
  Claude `/voice` skill.
- `portable_governance_pre_commit_hook.stub.template.sh`: starter hook stub
  rendered into `portable_governance_pre_commit_hook.stub.sh`.
- `portable_governance_tooling_workflow.stub.template.yml`: starter workflow
  stub rendered into `portable_governance_tooling_workflow.stub.yml`.
- `portable_governance_repo_setup.template.md`: AI-friendly onboarding guide
  for exporting the governance stack, running `governance-bootstrap`, and
  getting to the first `adoption-scan`.
  `governance-bootstrap` also turns that into a repo-local
  `dev/guides/PORTABLE_GOVERNANCE_SETUP.md` guide inside the adopted repo.
- `portable_governance_episode.schema.json`: event-level measurement schema for
  guarded coding episodes.
- `portable_governance_eval_record.schema.json`: multi-repo evaluation record
  schema.
- `portable_governance_finding_review.schema.json`: adjudicated finding-review
  schema for the governance ledger.
- `rust_audit_findings_template.md`: remediation scaffold for Rust audit
  findings.

Layout rule:
- Keep machine-consumed JSON templates and human-facing markdown templates in
  the same directory, but name them clearly enough that an export consumer can
  tell "starter file" from "schema" without opening every artifact.
- When a repo-pack template has a checked-in generated counterpart, update the
  template and regenerate the surface with `python3 dev/scripts/devctl.py
  render-surfaces --write`.
