# R98 Governed Push Preflight Review-Channel Timeout

Evidence:

- Governed push `python3 dev/scripts/devctl.py push --execute --format md`
  blocked before publication with `validation_failed`.
- The failed router step was `python-tests.devctl-focused` for
  `dev/scripts/devctl/tests/review_channel/test_review_channel.py`.
- Focused reproduction:
  `python3 dev/scripts/devctl.py test-python --suite devctl --path dev/scripts/devctl/tests/review_channel/test_review_channel.py::ReviewChannelCommandTests::test_run_reviewer_checkpoint_can_force_instruction_revision_rotation --timeout-seconds 300 --per-test-timeout-seconds 90 --parallel-workers 1`
  exits with `KeyboardInterrupt` at
  `dev/scripts/devctl/commands/review_channel/_stop.py:256`.
- Full trace shows `review-channel --action reviewer-checkpoint` calls
  `_maybe_stop_detached_review_runtime`, which calls `_run_stop_action`, which
  sends `SIGINT` to the pid from the test heartbeat fixture. The fixture uses
  `os.getpid()`, so the stop helper can signal the current controller process.

Rows to ingest from this plan:

- `MP-NEW-029` Governed push preflight follow-up: prevent review-channel
  detached-runtime stop from self-signaling the current controller process, and
  keep the focused review-channel test inside the governed-push preflight proof
  path.
