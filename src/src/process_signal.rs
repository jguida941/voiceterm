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

    unsafe {
        if libc::kill(-pid, signal) == 0 {
            return Ok(());
        }
        let group_err = io::Error::last_os_error();

        if libc::kill(pid, signal) == 0 {
            return Ok(());
        }
        let pid_err = io::Error::last_os_error();

        if missing_is_ok && (is_no_such_process(&group_err) || is_no_such_process(&pid_err)) {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[cfg(unix)]
    fn find_missing_pid() -> i32 {
        let current_pid = unsafe { libc::getpid() } as i32;
        let mut candidate = current_pid + 10_000;
        for _ in 0..1000 {
            let res = unsafe { libc::kill(candidate, 0) };
            let err = io::Error::last_os_error();
            if res != 0 && err.kind() == io::ErrorKind::NotFound {
                return candidate;
            }
            candidate += 1;
        }
        candidate
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
}
