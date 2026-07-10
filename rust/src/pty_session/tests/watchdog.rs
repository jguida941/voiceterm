use super::*;

fn pipe_pair_i32() -> [i32; 2] {
    let mut fds = [0; 2];
    let pipe_result = unsafe { libc::pipe(fds.as_mut_ptr()) };
    assert_eq!(
        pipe_result,
        0,
        "pipe() failed with errno {}",
        io::Error::last_os_error()
    );
    fds
}

#[test]
fn lifeline_watch_event_reports_parent_exit_while_lifeline_stays_open() {
    let lifeline = pipe_pair_i32();
    let report_pipe = pipe_pair_i32();

    unsafe {
        let target_pid = libc::fork();
        assert!(target_pid >= 0, "fork failed for lifeline target");

        if target_pid == 0 {
            libc::close(lifeline[1]);
            libc::close(report_pipe[0]);
            let watchdog_pid = spawn_lifeline_watchdog(lifeline[0]);
            assert!(watchdog_pid > 0, "watchdog fork failed in target");
            let bytes = watchdog_pid.to_ne_bytes();
            let wrote = libc::write(
                report_pipe[1],
                bytes.as_ptr() as *const libc::c_void,
                bytes.len(),
            );
            if wrote != bytes.len() as isize {
                libc::_exit(1);
            }
            libc::close(report_pipe[1]);
            libc::_exit(0);
        }

        libc::close(lifeline[0]);
        libc::close(report_pipe[1]);

        let mut bytes = [0u8; mem::size_of::<i32>()];
        let mut read_total = 0usize;
        while read_total < bytes.len() {
            let n = libc::read(
                report_pipe[0],
                bytes[read_total..].as_mut_ptr() as *mut libc::c_void,
                bytes.len() - read_total,
            );
            if n <= 0 {
                break;
            }
            read_total += n as usize;
        }
        libc::close(report_pipe[0]);
        assert_eq!(
            read_total,
            bytes.len(),
            "failed to read watchdog pid from target"
        );
        let watchdog_pid = i32::from_ne_bytes(bytes);

        let mut status = 0;
        let waited = libc::waitpid(target_pid, &mut status, 0);
        assert_eq!(waited, target_pid, "target child should exit cleanly");
        assert!(
            wait_for_process_to_exit(watchdog_pid, Duration::from_secs(2)),
            "watchdog pid {} remained alive after target exit with lifeline open",
            watchdog_pid
        );

        libc::close(lifeline[1]);
    }
}

#[test]
fn lifeline_watch_event_reports_pipe_close_before_parent_exit() {
    let lifeline = pipe_pair_i32();
    let report_pipe = pipe_pair_i32();

    unsafe {
        let target_pid = libc::fork();
        assert!(target_pid >= 0, "fork failed for lifeline target");

        if target_pid == 0 {
            libc::close(lifeline[1]);
            libc::close(report_pipe[0]);
            let watchdog_pid = spawn_lifeline_watchdog(lifeline[0]);
            assert!(watchdog_pid > 0, "watchdog fork failed in target");
            let bytes = watchdog_pid.to_ne_bytes();
            let wrote = libc::write(
                report_pipe[1],
                bytes.as_ptr() as *const libc::c_void,
                bytes.len(),
            );
            if wrote != bytes.len() as isize {
                libc::_exit(1);
            }
            libc::close(report_pipe[1]);
            loop {
                libc::pause();
            }
        }

        libc::close(lifeline[0]);
        libc::close(report_pipe[1]);

        let mut bytes = [0u8; mem::size_of::<i32>()];
        let mut read_total = 0usize;
        while read_total < bytes.len() {
            let n = libc::read(
                report_pipe[0],
                bytes[read_total..].as_mut_ptr() as *mut libc::c_void,
                bytes.len() - read_total,
            );
            if n <= 0 {
                break;
            }
            read_total += n as usize;
        }
        libc::close(report_pipe[0]);
        assert_eq!(
            read_total,
            bytes.len(),
            "failed to read watchdog pid from target"
        );
        let watchdog_pid = i32::from_ne_bytes(bytes);

        libc::close(lifeline[1]);
        assert!(
            wait_for_process_to_exit(watchdog_pid, Duration::from_secs(2)),
            "watchdog pid {} remained alive after lifeline close",
            watchdog_pid
        );

        let _ = libc::kill(target_pid, libc::SIGKILL);
        let mut status = 0;
        let _ = libc::waitpid(target_pid, &mut status, 0);
    }
}
