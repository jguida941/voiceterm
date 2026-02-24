//! Shared process-group signaling helpers for backend lifecycle teardown.

use std::io;

/// Send a signal to a process group first, then fall back to the direct pid.
///
/// On Unix PTY paths the child typically calls `setsid()`, so signaling `-pid`
/// reaches descendants as well. Callers can choose whether a missing pid (`ESRCH`)
/// should be treated as success (already exited) or as an error.
#[cfg(unix)]
pub(crate) fn signal_process_group_or_pid(
    pid: i32,
    signal: i32,
    missing_is_ok: bool,
) -> io::Result<()> {
    if pid <= 0 {
        return Ok(());
    }

    // SAFETY: `libc::kill` is called with plain integer pid/signal values. We do
    // not dereference pointers, and we only read errno immediately after each
    // syscall to capture its result for this thread.
    unsafe {
        if libc::kill(-pid, signal) == 0 {
            return Ok(());
        }
        let group_err = io::Error::last_os_error();

        if libc::kill(pid, signal) == 0 {
            return Ok(());
        }
        let pid_err = io::Error::last_os_error();

        if missing_target_can_be_ignored(missing_is_ok, &pid_err) {
            return Ok(());
        }

        Err(io::Error::new(
            pid_err.kind(),
            format!(
                "group(-{pid}) signal failed: {group_err}; pid({pid}) signal failed: {pid_err}"
            ),
        ))
    }
}

#[cfg(not(unix))]
pub(crate) fn signal_process_group_or_pid(
    _pid: i32,
    _signal: i32,
    _missing_is_ok: bool,
) -> io::Result<()> {
    Ok(())
}

#[cfg(unix)]
fn is_no_such_process(err: &io::Error) -> bool {
    matches!(err.raw_os_error(), Some(code) if code == libc::ESRCH)
}

#[cfg(unix)]
fn missing_target_can_be_ignored(missing_is_ok: bool, pid_err: &io::Error) -> bool {
    // Treat "missing target" as success only when the direct pid lookup reports ESRCH.
    // A missing process group alone does not guarantee the pid signal path is safe to ignore.
    missing_is_ok && is_no_such_process(pid_err)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[cfg(unix)]
    fn find_missing_pid() -> i32 {
        // Prefer a very high pid to avoid racey "found missing, then reused" windows.
        let high_pid = i32::MAX;
        // SAFETY: Probe-only signal `0` does not deliver a signal; it checks pid
        // existence/permission and is side-effect free for process state.
        let high_res = unsafe { libc::kill(high_pid, 0) };
        let high_err = io::Error::last_os_error();
        if high_res != 0 && is_no_such_process(&high_err) {
            return high_pid;
        }

        // SAFETY: `getpid` has no preconditions and returns the current process id.
        let current_pid = unsafe { libc::getpid() } as i32;
        let mut candidate = current_pid.saturating_add(10_000);
        for _ in 0..1000 {
            // SAFETY: Probe-only signal `0` is used to test pid availability.
            let res = unsafe { libc::kill(candidate, 0) };
            let err = io::Error::last_os_error();
            if res != 0 && is_no_such_process(&err) {
                return candidate;
            }
            candidate = candidate.saturating_add(1);
        }

        panic!("unable to find an unused pid for signal helper tests")
    }

    #[test]
    fn signal_helper_ignores_non_positive_pid() {
        assert!(signal_process_group_or_pid(0, 0, true).is_ok());
        assert!(signal_process_group_or_pid(-1, 0, false).is_ok());
    }

    #[cfg(unix)]
    #[test]
    fn signal_helper_missing_pid_is_optional_error() {
        let missing = find_missing_pid();
        assert!(signal_process_group_or_pid(missing, libc::SIGTERM, true).is_ok());
        assert!(signal_process_group_or_pid(missing, libc::SIGTERM, false).is_err());
    }

    #[cfg(unix)]
    #[test]
    fn signal_helper_optional_missing_requires_pid_esrch() {
        let pid_missing = io::Error::from_raw_os_error(libc::ESRCH);
        let pid_not_missing = io::Error::from_raw_os_error(libc::EPERM);

        assert!(missing_target_can_be_ignored(true, &pid_missing));
        assert!(!missing_target_can_be_ignored(true, &pid_not_missing));
        assert!(!missing_target_can_be_ignored(false, &pid_missing));
    }
}
