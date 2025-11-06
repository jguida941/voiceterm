use std::os::unix::io::RawFd;
use std::thread;
use std::time::Duration;
use anyhow::{Result, bail};
use crossbeam_channel::{bounded, Receiver};

/// Uses PTY to run Codex in a proper terminal environment
pub struct PtyCodexSession {
    master_fd: RawFd,
    child_pid: i32,
    output_rx: Receiver<String>,
    _output_thread: thread::JoinHandle<()>,
}

impl PtyCodexSession {
    pub fn new(codex_cmd: &str, working_dir: &str) -> Result<Self> {
        unsafe {
            // Create a pseudo-terminal
            let mut master_fd: RawFd = 0;
            let mut slave_fd: RawFd = 0;

            // Create PTY pair
            let ret = libc::openpty(&mut master_fd, &mut slave_fd,
                                   std::ptr::null_mut(),
                                   std::ptr::null_mut(),
                                   std::ptr::null_mut());

            if ret != 0 {
                bail!("Failed to create PTY");
            }

            // Fork process
            let pid = libc::fork();

            if pid < 0 {
                bail!("Fork failed");
            } else if pid == 0 {
                // Child process
                libc::close(master_fd);

                // Make slave the controlling terminal
                libc::setsid();
                libc::ioctl(slave_fd, libc::TIOCSCTTY as libc::c_ulong, 0);

                // Redirect stdin/stdout/stderr to slave
                libc::dup2(slave_fd, 0);
                libc::dup2(slave_fd, 1);
                libc::dup2(slave_fd, 2);
                libc::close(slave_fd);

                // Change to working directory
                let cwd = std::ffi::CString::new(working_dir).unwrap();
                libc::chdir(cwd.as_ptr());

                // Execute Codex
                let cmd = std::ffi::CString::new(codex_cmd).unwrap();
                let args = vec![
                    cmd.clone(),
                ];
                let args_ptrs: Vec<*const libc::c_char> = args.iter()
                    .map(|s| s.as_ptr())
                    .chain(std::iter::once(std::ptr::null()))
                    .collect();

                libc::execvp(cmd.as_ptr(), args_ptrs.as_ptr());

                // If we get here, exec failed
                std::process::exit(1);
            }

            // Parent process
            libc::close(slave_fd);

            // Make master non-blocking
            let flags = libc::fcntl(master_fd, libc::F_GETFL, 0);
            libc::fcntl(master_fd, libc::F_SETFL, flags | libc::O_NONBLOCK);

            // Create channel for output
            let (tx, rx) = bounded(100);

            // Spawn thread to read output
            let master_read = master_fd;
            let output_thread = thread::spawn(move || {
                let mut buffer = [0u8; 4096];
                loop {
                    let n = libc::read(master_read, buffer.as_mut_ptr() as *mut libc::c_void, buffer.len());
                    if n > 0 {
                        let output = String::from_utf8_lossy(&buffer[..n as usize]).to_string();
                        if tx.send(output).is_err() {
                            break;
                        }
                    }
                    thread::sleep(Duration::from_millis(10));
                }
            });

            // Wait a bit for Codex to start
            thread::sleep(Duration::from_millis(500));

            Ok(Self {
                master_fd,
                child_pid: pid,
                output_rx: rx,
                _output_thread: output_thread,
            })
        }
    }

    pub fn send(&mut self, text: &str) -> Result<()> {
        unsafe {
            let bytes = text.as_bytes();
            let ret = libc::write(self.master_fd, bytes.as_ptr() as *const libc::c_void, bytes.len());
            if ret < 0 {
                bail!("Failed to write to PTY");
            }

            // Send newline if not present
            if !text.ends_with('\n') {
                let newline = b"\n";
                libc::write(self.master_fd, newline.as_ptr() as *const libc::c_void, 1);
            }
        }
        Ok(())
    }

    pub fn read_output(&self) -> Vec<String> {
        let mut output = Vec::new();
        while let Ok(line) = self.output_rx.try_recv() {
            output.push(line);
        }
        output
    }

    pub fn read_output_timeout(&self, timeout: Duration) -> Vec<String> {
        let mut output = Vec::new();
        let start = std::time::Instant::now();

        while start.elapsed() < timeout {
            match self.output_rx.recv_timeout(Duration::from_millis(100)) {
                Ok(line) => output.push(line),
                Err(_) => {
                    if !output.is_empty() {
                        break;
                    }
                }
            }
        }
        output
    }

    pub fn is_alive(&self) -> bool {
        unsafe {
            let mut status = 0;
            let ret = libc::waitpid(self.child_pid, &mut status, libc::WNOHANG);
            ret == 0  // 0 means still running
        }
    }
}

impl Drop for PtyCodexSession {
    fn drop(&mut self) {
        unsafe {
            // Send exit command
            let _ = self.send("exit\n");
            thread::sleep(Duration::from_millis(100));

            // Kill process if still running
            libc::kill(self.child_pid, libc::SIGTERM);
            thread::sleep(Duration::from_millis(100));
            libc::kill(self.child_pid, libc::SIGKILL);

            // Close PTY
            libc::close(self.master_fd);
        }
    }
}