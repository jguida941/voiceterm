//! PTY session lifecycle so backend CLIs behave like true interactive terminals.
//!
//! Spawns backend CLIs in a PTY so they behave as if
//! running in an interactive terminal. Handles I/O forwarding, window resize
//! signals, and graceful process termination.

use crate::log_debug;
use crate::process_signal::signal_process_group_or_pid;
use anyhow::{anyhow, Context, Result};
use crossbeam_channel::{bounded, Receiver, Sender};
use std::ffi::CString;
use std::io::{self};
use std::os::unix::io::RawFd;
use std::os::unix::process::ExitStatusExt;
use std::ptr;
use std::thread;
use std::time::{Duration, Instant};

#[cfg(any(test, feature = "mutants"))]
use super::counters::{
    guard_loop, record_pty_read, record_pty_send, record_wait_for_exit_error,
    record_wait_for_exit_poll, record_wait_for_exit_reap,
};
use super::counters::{read_output_elapsed, read_output_grace_elapsed, wait_for_exit_elapsed};
use super::io::{spawn_passthrough_reader_thread, spawn_reader_thread, try_write, write_all};
use super::session_guard;

/// Uses PTY to run a backend CLI in a proper terminal environment.
pub struct PtyCliSession {
    pub(super) master_fd: RawFd,
    pub(super) lifeline_write_fd: RawFd,
    pub(super) child_pid: i32,
    /// Stream of raw PTY output chunks from the child process.
    pub output_rx: Receiver<Vec<u8>>,
    pub(super) _output_thread: thread::JoinHandle<()>,
}

struct PtySessionInit {
    master_fd: RawFd,
    lifeline_write_fd: RawFd,
    child_pid: i32,
    output_rx: Receiver<Vec<u8>>,
    output_thread: thread::JoinHandle<()>,
}

fn start_pty_session(
    cli_cmd: &str,
    working_dir: &str,
    args: &[String],
    term_value: &str,
    initial_rows: u16,
    initial_cols: u16,
    spawn_reader: fn(RawFd, Sender<Vec<u8>>) -> thread::JoinHandle<()>,
) -> Result<PtySessionInit> {
    session_guard::cleanup_stale_sessions();
    let cwd = CString::new(working_dir)
        .with_context(|| format!("working directory contains NUL byte: {working_dir}"))?;
    let term_value_cstr = term_value_cstring(term_value)?;
    let mut argv: Vec<CString> = Vec::with_capacity(args.len() + 1);
    argv.push(
        CString::new(cli_cmd).with_context(|| format!("cli_cmd contains NUL byte: {cli_cmd}"))?,
    );
    for arg in args {
        argv.push(
            CString::new(arg.as_str())
                .with_context(|| format!("cli arg contains NUL byte: {arg}"))?,
        );
    }

    // SAFETY: argv/cwd/TERM are valid CStrings; spawn_pty_child returns a valid master fd.
    // set_nonblocking only touches the returned master fd.
    unsafe {
        let (master_fd, lifeline_write_fd, child_pid) =
            spawn_pty_child(&argv, &cwd, &term_value_cstr, initial_rows, initial_cols)?;
        set_nonblocking(master_fd)?;
        session_guard::register_session(master_fd, child_pid, cli_cmd);

        let (tx, rx) = bounded(100);
        let output_thread = spawn_reader(master_fd, tx);
        Ok(PtySessionInit {
            master_fd,
            lifeline_write_fd,
            child_pid,
            output_rx: rx,
            output_thread,
        })
    }
}

fn write_text_with_newline(master_fd: RawFd, text: &str) -> Result<()> {
    write_all(master_fd, text.as_bytes())?;
    if !text.ends_with('\n') {
        write_all(master_fd, b"\n")?;
    }
    Ok(())
}

fn child_process_is_alive(child_pid: i32) -> bool {
    if child_pid < 0 {
        return false;
    }
    unsafe {
        // SAFETY: child_pid is owned by this session; waitpid with WNOHANG only inspects state.
        let mut status = 0;
        let ret = libc::waitpid(child_pid, &mut status, libc::WNOHANG);
        ret == 0 // 0 means still running
    }
}

unsafe fn shutdown_pty_child(master_fd: RawFd, child_pid: i32) {
    if child_pid < 0 {
        return;
    }

    // SAFETY: child_pid/master_fd come from spawn_pty_child; cleanup uses best-effort signals.
    if let Err(err) = write_text_with_newline(master_fd, "exit") {
        if !is_benign_shutdown_write_error(&err) {
            log_debug(&format!("failed to send PTY exit command: {err:#}"));
        }
    }
    if !wait_for_exit(child_pid, Duration::from_millis(500)) {
        if let Err(err) = signal_process_group_or_pid(child_pid, libc::SIGTERM, true) {
            log_debug(&format!("SIGTERM to PTY session failed: {}", err));
        }
        if !wait_for_exit(child_pid, Duration::from_millis(500)) {
            if let Err(err) = signal_process_group_or_pid(child_pid, libc::SIGKILL, true) {
                log_debug(&format!("SIGKILL to PTY session failed: {}", err));
            }
            #[cfg(any(test, feature = "mutants"))]
            {
                let mut status = 0;
                let _ = libc::waitpid(child_pid, &mut status, libc::WNOHANG);
            }
            #[cfg(not(any(test, feature = "mutants")))]
            {
                let mut status = 0;
                let ret = libc::waitpid(child_pid, &mut status, 0);
                if waitpid_failed(ret) {
                    log_debug(&format!(
                        "waitpid after SIGKILL failed: {}",
                        io::Error::last_os_error()
                    ));
                }
            }
        }
    }
}

unsafe fn close_pty_session_handles(master_fd: RawFd, lifeline_write_fd: &mut RawFd) {
    session_guard::unregister_session(master_fd);
    close_fd(*lifeline_write_fd);
    *lifeline_write_fd = -1;
    close_fd(master_fd);
}

impl PtyCliSession {
    /// Start a backend CLI under a pseudo-terminal so it behaves like an interactive shell.
    ///
    /// # Errors
    ///
    /// Returns an error if PTY allocation, process spawn, or reader thread setup fails.
    pub fn new(
        cli_cmd: &str,
        working_dir: &str,
        args: &[String],
        term_value: &str,
        initial_rows: u16,
        initial_cols: u16,
    ) -> Result<Self> {
        let init = start_pty_session(
            cli_cmd,
            working_dir,
            args,
            term_value,
            initial_rows,
            initial_cols,
            spawn_reader_thread,
        )?;
        Ok(Self {
            master_fd: init.master_fd,
            lifeline_write_fd: init.lifeline_write_fd,
            child_pid: init.child_pid,
            output_rx: init.output_rx,
            _output_thread: init.output_thread,
        })
    }

    /// Write text to the PTY, automatically ensuring prompts end with a newline.
    ///
    /// # Errors
    ///
    /// Returns an error if writing to the PTY master fails.
    pub fn send(&mut self, text: &str) -> Result<()> {
        #[cfg(any(test, feature = "mutants"))]
        record_pty_send();
        write_text_with_newline(self.master_fd, text)
    }

    /// Drain any waiting output without blocking.
    #[must_use]
    pub fn read_output(&self) -> Vec<Vec<u8>> {
        let mut output = Vec::new();
        while let Ok(line) = self.output_rx.try_recv() {
            output.push(line);
        }
        output
    }

    /// Block for a short window until output arrives or the timeout expires.
    #[must_use]
    pub fn read_output_timeout(&self, timeout: Duration) -> Vec<Vec<u8>> {
        #[cfg(any(test, feature = "mutants"))]
        record_pty_read();
        let mut output = Vec::new();
        let start = Instant::now();
        let mut last_chunk: Option<Instant> = None;

        while read_output_elapsed(start) < timeout {
            match self.output_rx.recv_timeout(Duration::from_millis(100)) {
                Ok(line) => {
                    last_chunk = Some(Instant::now());
                    output.push(line);
                }
                Err(_) => {
                    if output.is_empty() {
                        break;
                    }
                    if let Some(last) = last_chunk {
                        let elapsed = read_output_grace_elapsed(last);
                        if elapsed < Duration::from_millis(300) {
                            continue;
                        }
                    }
                    break;
                }
            }
        }
        output
    }

    /// Check if the PTY session is responsive by verifying the process is alive.
    /// Note: some backends don't output anything until you send a prompt, so we
    /// can't require output for the health check - just verify the process started.
    pub fn is_responsive(&mut self, _timeout: Duration) -> bool {
        // Drain any startup output (banner, prompts, etc.) without blocking
        let _ = self.read_output();

        if !self.is_alive() {
            log_debug("PTY health check: process not alive");
            return false;
        }

        log_debug("PTY health check: process alive, assuming responsive");
        true
    }

    /// Wait up to `timeout` for at least one output chunk, then drain any remaining bytes.
    #[must_use]
    pub fn wait_for_output(&self, timeout: Duration) -> Vec<Vec<u8>> {
        let mut output = Vec::new();
        if let Ok(chunk) = self.output_rx.recv_timeout(timeout) {
            output.push(chunk);
            output.extend(self.read_output());
        }
        output
    }

    /// Peek whether the child is still running (without reaping it).
    #[must_use]
    pub fn is_alive(&self) -> bool {
        child_process_is_alive(self.child_pid)
    }

    /// Non-blocking check for child exit; reaps the child on completion.
    pub fn try_wait(&mut self) -> Option<std::process::ExitStatus> {
        if self.child_pid < 0 {
            return None;
        }
        unsafe {
            let mut status = 0;
            let ret = libc::waitpid(self.child_pid, &mut status, libc::WNOHANG);
            if ret <= 0 {
                None
            } else {
                self.child_pid = -1;
                Some(std::process::ExitStatus::from_raw(status))
            }
        }
    }
}

impl Drop for PtyCliSession {
    fn drop(&mut self) {
        unsafe {
            shutdown_pty_child(self.master_fd, self.child_pid);
            close_pty_session_handles(self.master_fd, &mut self.lifeline_write_fd);
        }
    }
}

/// PTY session that forwards raw output (ANSI intact) while answering terminal queries.
pub struct PtyOverlaySession {
    pub(super) master_fd: RawFd,
    pub(super) lifeline_write_fd: RawFd,
    pub(super) child_pid: i32,
    /// Stream of raw PTY output chunks from the child process.
    pub output_rx: Receiver<Vec<u8>>,
    pub(super) _output_thread: thread::JoinHandle<()>,
}

impl PtyOverlaySession {
    /// Start a backend CLI under a pseudo-terminal but keep output raw for overlay rendering.
    ///
    /// # Errors
    ///
    /// Returns an error if PTY allocation, process spawn, or reader thread setup fails.
    pub fn new(
        cli_cmd: &str,
        working_dir: &str,
        args: &[String],
        term_value: &str,
        initial_rows: u16,
        initial_cols: u16,
    ) -> Result<Self> {
        let init = start_pty_session(
            cli_cmd,
            working_dir,
            args,
            term_value,
            initial_rows,
            initial_cols,
            spawn_passthrough_reader_thread,
        )?;
        Ok(Self {
            master_fd: init.master_fd,
            lifeline_write_fd: init.lifeline_write_fd,
            child_pid: init.child_pid,
            output_rx: init.output_rx,
            _output_thread: init.output_thread,
        })
    }

    /// Write raw bytes to the PTY master.
    ///
    /// # Errors
    ///
    /// Returns an error if writing the provided bytes to the PTY fails.
    pub fn send_bytes(&mut self, bytes: &[u8]) -> Result<()> {
        write_all(self.master_fd, bytes)
    }

    /// Attempt a single non-blocking write to the PTY master.
    ///
    /// # Errors
    ///
    /// Returns any I/O error produced by a non-blocking write attempt.
    pub fn try_send_bytes(&mut self, bytes: &[u8]) -> io::Result<usize> {
        try_write(self.master_fd, bytes)
    }

    /// Write text to the PTY master.
    ///
    /// # Errors
    ///
    /// Returns an error if writing UTF-8 bytes to the PTY fails.
    pub fn send_text(&mut self, text: &str) -> Result<()> {
        write_all(self.master_fd, text.as_bytes())
    }

    /// Write text to the PTY master and ensure it ends with a newline.
    ///
    /// # Errors
    ///
    /// Returns an error if writing to the PTY master fails.
    pub fn send_text_with_newline(&mut self, text: &str) -> Result<()> {
        write_text_with_newline(self.master_fd, text)
    }

    /// Update the PTY window size and notify the child.
    ///
    /// # Errors
    ///
    /// Returns an error if the window-size ioctl fails.
    pub fn set_winsize(&self, rows: u16, cols: u16) -> Result<()> {
        let ws = libc::winsize {
            ws_row: rows.max(1),
            ws_col: cols.max(1),
            ws_xpixel: 0,
            ws_ypixel: 0,
        };
        // SAFETY: ioctl writes to ws and reads master_fd; ws is initialized.
        let result = unsafe { libc::ioctl(self.master_fd, libc::TIOCSWINSZ, &ws) };
        if result != 0 {
            return Err(errno_error("ioctl(TIOCSWINSZ) failed"));
        }
        // Notify the full PTY process tree about resize events.
        let _ = signal_process_group_or_pid(self.child_pid, libc::SIGWINCH, true);
        Ok(())
    }

    /// Peek whether the child is still running (without reaping it).
    #[must_use]
    pub fn is_alive(&self) -> bool {
        child_process_is_alive(self.child_pid)
    }

    /// Query the current PTY window size (rows, cols).
    #[must_use]
    pub fn current_winsize(&self) -> (u16, u16) {
        super::osc::current_terminal_size(self.master_fd)
    }
}

#[cfg(any(test, feature = "mutants"))]
#[cfg_attr(any(test, feature = "mutants"), allow(dead_code))]
pub(crate) fn test_pty_session(
    master_fd: RawFd,
    lifeline_write_fd: RawFd,
    child_pid: i32,
    output_rx: Receiver<Vec<u8>>,
) -> PtyCliSession {
    let handle = thread::spawn(|| {});
    PtyCliSession {
        master_fd,
        lifeline_write_fd,
        child_pid,
        output_rx,
        _output_thread: handle,
    }
}

impl Drop for PtyOverlaySession {
    fn drop(&mut self) {
        unsafe {
            shutdown_pty_child(self.master_fd, self.child_pid);
            close_pty_session_handles(self.master_fd, &mut self.lifeline_write_fd);
        }
    }
}

fn is_benign_shutdown_write_error(err: &anyhow::Error) -> bool {
    for cause in err.chain() {
        if let Some(io_err) = cause.downcast_ref::<io::Error>() {
            if io_err.kind() == io::ErrorKind::BrokenPipe {
                return true;
            }
            if matches!(
                io_err.raw_os_error(),
                Some(code)
                    if code == libc::EIO
                        || code == libc::EPIPE
                        || code == libc::ENXIO
                        || code == libc::EBADF
            ) {
                return true;
            }
        }
    }
    false
}

/// Forks and execs a child process under a new PTY.
///
/// # CRITICAL — HUD overlap fix
///
/// `initial_rows` and `initial_cols` MUST be passed from the caller with the
/// correct terminal size **minus HUD reserved rows**.  DO NOT revert these
/// parameters back to hardcoded 24×80.  When the child (e.g. Claude Code)
/// starts, it reads `process.stdout.rows` exactly once to lay out its TUI.
/// If the PTY is created at full terminal height, the input prompt lands on
/// the same row as the HUD, causing persistent overlap that no later
/// SIGWINCH can reliably fix.  See `main.rs` where `reserved_rows_for_mode`
/// is computed before PTY creation.
///
/// # Safety
///
/// This function performs low-level PTY allocation and process forking.
/// The caller must ensure:
/// - `argv` contains valid null-terminated C strings
/// - `working_dir` is a valid directory path
/// - The returned file descriptor is eventually closed
///
/// The child process calls `_exit(1)` on any setup failure to avoid
/// undefined behavior from returning after `fork()`.
pub(super) unsafe fn spawn_pty_child(
    argv: &[CString],
    working_dir: &CString,
    term_value: &CString,
    initial_rows: u16,
    initial_cols: u16,
) -> Result<(RawFd, RawFd, i32)> {
    let mut master_fd: RawFd = -1;
    let mut slave_fd: RawFd = -1;
    let mut lifeline_fds = [-1; 2];

    // Use the caller-supplied terminal size so the child process starts with the
    // correct geometry.  Falling back to 24x80 when callers pass zero keeps
    // backwards-compatible behaviour for tests and non-overlay sessions.
    let mut winsize = libc::winsize {
        ws_row: if initial_rows > 0 { initial_rows } else { 24 },
        ws_col: if initial_cols > 0 { initial_cols } else { 80 },
        ws_xpixel: 0,
        ws_ypixel: 0,
    };

    #[allow(clippy::unnecessary_mut_passed)]
    // SAFETY: openpty expects valid pointers for master/slave/winsize; we pass stack locals.
    if libc::openpty(
        &mut master_fd,
        &mut slave_fd,
        ptr::null_mut(),
        ptr::null_mut(),
        &mut winsize,
    ) != 0
    {
        return Err(errno_error("openpty failed"));
    }

    if libc::pipe(lifeline_fds.as_mut_ptr()) != 0 {
        close_fd(master_fd);
        close_fd(slave_fd);
        return Err(errno_error("pipe(lifeline) failed"));
    }

    set_cloexec(master_fd)?;
    set_cloexec(slave_fd)?;
    set_cloexec(lifeline_fds[0])?;
    set_cloexec(lifeline_fds[1])?;

    // SAFETY: fork is called before any unsafe Rust invariants are relied on.
    let pid = libc::fork();
    if pid < 0 {
        close_fd(master_fd);
        close_fd(slave_fd);
        close_fd(lifeline_fds[0]);
        close_fd(lifeline_fds[1]);
        return Err(errno_error("fork failed"));
    }

    if pid == 0 {
        close_fd(lifeline_fds[1]);
        child_exec(
            master_fd,
            slave_fd,
            lifeline_fds[0],
            argv,
            working_dir,
            term_value,
        );
    }

    close_fd(slave_fd);
    close_fd(lifeline_fds[0]);
    Ok((master_fd, lifeline_fds[1], pid))
}

/// Child process setup after fork: configures PTY and execs the target binary.
///
/// # Safety
///
/// Must only be called in the child process after `fork()`. This function
/// never returns - it either calls `execvp()` to replace the process image
/// or `_exit(1)` on failure.
///
/// The `-> !` return type indicates this function diverges (never returns).
pub(super) unsafe fn child_exec(
    master_fd: RawFd,
    slave_fd: RawFd,
    lifeline_read_fd: RawFd,
    argv: &[CString],
    working_dir: &CString,
    term_value: &CString,
) -> ! {
    let fail = |context: &str| -> ! {
        let err = io::Error::last_os_error();
        let msg = format!("child_exec {context} failed: {err}\n");
        // SAFETY: write is async-signal-safe and stderr is a valid fd in the child.
        let _ = libc::write(
            libc::STDERR_FILENO,
            msg.as_ptr() as *const libc::c_void,
            msg.len(),
        );
        libc::_exit(1);
    };

    spawn_lifeline_watchdog(lifeline_read_fd);
    close_fd(lifeline_read_fd);
    close_fd(master_fd);

    if libc::setsid() == -1 {
        fail("setsid");
    }
    if libc::ioctl(slave_fd, libc::TIOCSCTTY as libc::c_ulong, 0) == -1 {
        fail("ioctl(TIOCSCTTY)");
    }
    if libc::dup2(slave_fd, libc::STDIN_FILENO) < 0
        || libc::dup2(slave_fd, libc::STDOUT_FILENO) < 0
        || libc::dup2(slave_fd, libc::STDERR_FILENO) < 0
    {
        fail("dup2");
    }
    close_fd(slave_fd);

    if libc::chdir(working_dir.as_ptr()) != 0 {
        fail("chdir");
    }

    let term_key = b"TERM\0";
    if libc::setenv(
        term_key.as_ptr() as *const libc::c_char,
        term_value.as_ptr(),
        1,
    ) != 0
    {
        fail("setenv(TERM)");
    }

    let mut argv_ptrs: Vec<*const libc::c_char> = argv.iter().map(|s| s.as_ptr()).collect();
    argv_ptrs.push(ptr::null());

    libc::execvp(argv_ptrs[0], argv_ptrs.as_ptr());
    fail("execvp");
}

/// Spawn a watchdog process that kills the PTY process group if the parent process disappears.
///
/// The watchdog blocks on a dedicated lifeline pipe. When the parent dies unexpectedly
/// (for example IDE crash / forced terminal kill), the write end closes and the watchdog
/// sends SIGTERM/SIGKILL to the PTY process group rooted at `target_pid`.
unsafe fn spawn_lifeline_watchdog(lifeline_read_fd: RawFd) {
    let target_pid = libc::getpid();
    let watchdog_pid = libc::fork();
    if watchdog_pid < 0 {
        return;
    }
    if watchdog_pid != 0 {
        return;
    }

    close_fds_for_watchdog(lifeline_read_fd);
    wait_for_lifeline_close(lifeline_read_fd);
    close_fd(lifeline_read_fd);
    terminate_process_group_with_escalation(target_pid, Duration::from_millis(500));
    libc::_exit(0);
}

unsafe fn close_fds_for_watchdog(lifeline_read_fd: RawFd) {
    let max_fd = libc::sysconf(libc::_SC_OPEN_MAX);
    let upper = if max_fd > 3 { max_fd as RawFd } else { 1024 };
    for fd in 3..upper {
        if fd == lifeline_read_fd {
            continue;
        }
        let _ = libc::close(fd);
    }
}

unsafe fn wait_for_lifeline_close(lifeline_read_fd: RawFd) {
    let mut byte = [0u8; 1];
    loop {
        let n = libc::read(lifeline_read_fd, byte.as_mut_ptr() as *mut libc::c_void, 1);
        if n == 0 {
            break;
        }
        if n > 0 {
            continue;
        }
        let err = io::Error::last_os_error();
        if matches!(err.raw_os_error(), Some(code) if code == libc::EINTR) {
            continue;
        }
        break;
    }
}

fn term_value_cstring(term_value: &str) -> Result<CString> {
    CString::new(term_value)
        .or_else(|_| CString::new("xterm-256color"))
        .map_err(|_| anyhow!("TERM fallback constant contains an interior NUL byte"))
}

unsafe fn process_exists(pid: i32) -> bool {
    if pid <= 0 {
        return false;
    }
    if libc::kill(pid, 0) == 0 {
        return true;
    }
    matches!(io::Error::last_os_error().raw_os_error(), Some(code) if code == libc::EPERM)
}

unsafe fn terminate_process_group_with_escalation(pid: i32, grace: Duration) {
    let _ = signal_process_group_or_pid(pid, libc::SIGTERM, true);
    let start = Instant::now();
    while start.elapsed() < grace {
        if !process_exists(pid) {
            return;
        }
        thread::sleep(Duration::from_millis(20));
    }
    let _ = signal_process_group_or_pid(pid, libc::SIGKILL, true);
}

/// Configure the PTY master for non-blocking reads.
///
/// # Safety
///
/// `fd` must be a valid, open file descriptor.
pub(super) unsafe fn set_nonblocking(fd: RawFd) -> Result<()> {
    let flags = libc::fcntl(fd, libc::F_GETFL, 0);
    if flags < 0 {
        return Err(errno_error("fcntl(F_GETFL) failed"));
    }
    if libc::fcntl(fd, libc::F_SETFL, flags | libc::O_NONBLOCK) < 0 {
        return Err(errno_error("fcntl(F_SETFL) failed"));
    }
    Ok(())
}

/// Mark a file descriptor close-on-exec so leaked descriptors do not survive exec boundaries.
pub(super) fn set_cloexec(fd: RawFd) -> Result<()> {
    if fd < 0 {
        return Ok(());
    }

    let flags = unsafe { libc::fcntl(fd, libc::F_GETFD) };
    if flags < 0 {
        return Err(errno_error("fcntl(F_GETFD) failed"));
    }
    let result = unsafe { libc::fcntl(fd, libc::F_SETFD, flags | libc::FD_CLOEXEC) };
    if result < 0 {
        return Err(errno_error("fcntl(F_SETFD, FD_CLOEXEC) failed"));
    }
    Ok(())
}

/// Helper that formats OS errors with additional context.
pub(super) fn errno_error(context: &str) -> anyhow::Error {
    anyhow!("{context}: {}", io::Error::last_os_error())
}

/// Close a file descriptor while ignoring errors.
///
/// # Safety
///
/// `fd` must be a valid, open file descriptor (or -1 to ignore).
pub(super) unsafe fn close_fd(fd: RawFd) {
    if fd >= 0 {
        let _ = libc::close(fd);
    }
}

#[cfg_attr(any(test, feature = "mutants"), allow(dead_code))]
pub(super) fn waitpid_failed(ret: i32) -> bool {
    ret < 0
}

/// Wait for the child process to terminate, but bail out after a short timeout.
pub(super) fn wait_for_exit(child_pid: i32, timeout: Duration) -> bool {
    if timeout.is_zero() {
        return false;
    }
    let start = Instant::now();
    let mut status = 0;
    #[cfg(any(test, feature = "mutants"))]
    let mut guard_iters: usize = 0;
    while wait_for_exit_elapsed(start) < timeout {
        #[cfg(any(test, feature = "mutants"))]
        {
            let prev = guard_iters;
            guard_iters += 1;
            assert!(guard_iters > prev);
            guard_loop(start, guard_iters, 10_000, "wait_for_exit");
        }
        #[cfg(any(test, feature = "mutants"))]
        record_wait_for_exit_poll();
        // SAFETY: child_pid is owned by this session; waitpid with WNOHANG only inspects state.
        let result = unsafe { libc::waitpid(child_pid, &mut status, libc::WNOHANG) };
        if result > 0 {
            #[cfg(any(test, feature = "mutants"))]
            record_wait_for_exit_reap();
            return true;
        }
        if result < 0 {
            #[cfg(any(test, feature = "mutants"))]
            record_wait_for_exit_error();
            log_debug(&format!(
                "waitpid({}) failed: {}",
                child_pid,
                io::Error::last_os_error()
            ));
            return true;
        }
        thread::sleep(Duration::from_millis(50));
    }
    false
}
