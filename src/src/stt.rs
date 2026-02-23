//! Whisper speech-to-text integration so capture results become local transcripts.
//!
//! Wraps `whisper_rs` to provide a simple transcription API. The model is loaded
//! once and reused across captures to avoid repeated initialization overhead.

#[inline]
fn should_insert_boundary_space(prev: char, next: char) -> bool {
    if prev.is_whitespace() || next.is_whitespace() {
        return false;
    }
    if matches!(
        next,
        '.' | ',' | '!' | '?' | ';' | ':' | '%' | ')' | ']' | '}' | '"' | '\''
    ) {
        return false;
    }
    if matches!(prev, '(' | '[' | '{' | '"' | '\'' | '/' | '-') {
        return false;
    }
    true
}

fn append_whisper_segment(transcript: &mut String, segment: &str) {
    let segment = segment.trim();
    if segment.is_empty() {
        return;
    }
    if let (Some(prev), Some(next)) = (transcript.chars().last(), segment.chars().next()) {
        if should_insert_boundary_space(prev, next) {
            transcript.push(' ');
        }
    }
    transcript.push_str(segment);
}

#[cfg(unix)]
mod platform {
    use crate::config::AppConfig;
    use crate::log_debug;
    use anyhow::{anyhow, Context, Result};
    use std::io;
    use std::os::raw::{c_char, c_uint, c_void};
    use std::os::unix::io::AsRawFd;
    use std::sync::Once;
    use whisper_rs::{FullParams, SamplingStrategy, WhisperContext, WhisperContextParameters};

    /// Whisper model context for speech-to-text transcription.
    ///
    /// Holds the loaded GGML model in memory. Create once at startup and reuse
    /// for all transcription requests to avoid repeated model loading.
    pub struct Transcriber {
        ctx: WhisperContext,
    }

    impl Transcriber {
        /// Loads the Whisper model from disk.
        ///
        /// Temporarily redirects stderr to `/dev/null` during loading because
        /// whisper.cpp emits verbose initialization messages.
        ///
        /// Note: this is a process-wide redirect; we keep it brief and expect
        /// model loading to happen during startup before other threads log.
        ///
        /// # Errors
        ///
        /// Returns an error if the model file cannot be loaded or stderr
        /// redirection fails.
        pub fn new(model_path: &str) -> Result<Self> {
            install_whisper_log_silencer();

            let null = std::fs::OpenOptions::new()
                .write(true)
                .open("/dev/null")
                .context("failed to open /dev/null")?;
            let null_fd = null.as_raw_fd();

            // SAFETY: dup(2) duplicates the stderr file descriptor. We restore it
            // after model loading completes. This is safe because we hold the only
            // reference and restore before returning.
            let orig_stderr = unsafe { libc::dup(2) };
            if orig_stderr < 0 {
                return Err(anyhow!(
                    "failed to dup stderr: {}",
                    io::Error::last_os_error()
                ));
            }

            // Redirect stderr to /dev/null temporarily
            // SAFETY: dup2 replaces stderr with /dev/null; both fds are valid.
            let dup_result = unsafe { libc::dup2(null_fd, 2) };
            if dup_result < 0 {
                // SAFETY: orig_stderr is a valid fd from dup(2).
                unsafe {
                    libc::close(orig_stderr);
                }
                return Err(anyhow!(
                    "failed to redirect stderr: {}",
                    io::Error::last_os_error()
                ));
            }

            // Load model (output will be suppressed)
            let ctx_result =
                WhisperContext::new_with_params(model_path, WhisperContextParameters::default());

            // Restore original stderr
            // SAFETY: restore stderr using the saved fd from dup(2).
            let restore_result = unsafe { libc::dup2(orig_stderr, 2) };
            // SAFETY: orig_stderr is a valid fd returned by dup(2).
            unsafe {
                libc::close(orig_stderr);
            }
            if restore_result < 0 {
                return Err(anyhow!(
                    "failed to restore stderr: {}",
                    io::Error::last_os_error()
                ));
            }

            let ctx = ctx_result.context("failed to load whisper model")?;
            Ok(Self { ctx })
        }

        /// Run transcription for the captured PCM samples and return the concatenated text.
        ///
        /// # Errors
        ///
        /// Returns an error if Whisper state allocation fails, decoding fails, or
        /// inference cannot complete for the provided samples.
        pub fn transcribe(&self, samples: &[f32], config: &AppConfig) -> Result<String> {
            let mut state = self
                .ctx
                .create_state()
                .context("failed to create whisper state")?;
            let beam_size = i32::try_from(config.whisper_beam_size).unwrap_or(1);
            let mut params = if config.whisper_beam_size > 1 {
                FullParams::new(SamplingStrategy::BeamSearch {
                    beam_size,
                    patience: -1.0,
                })
            } else {
                FullParams::new(SamplingStrategy::Greedy { best_of: 1 })
            };
            if config.lang.eq_ignore_ascii_case("auto") {
                params.set_language(None);
                params.set_detect_language(true);
            } else {
                params.set_language(Some(&config.lang));
                params.set_detect_language(false);
            }
            params.set_temperature(config.whisper_temperature);
            // Keep one logical core free and clamp worker fanout to reduce contention spikes.
            let n_threads = std::thread::available_parallelism()
                .map(|count| count.get())
                .unwrap_or(1)
                .saturating_sub(1)
                .clamp(1, 4);
            let n_threads = i32::try_from(n_threads).unwrap_or(1);
            params.set_n_threads(n_threads);
            params.set_print_progress(false);
            params.set_print_timestamps(false);
            params.set_print_special(false);
            params.set_print_realtime(false);
            params.set_translate(false);
            params.set_token_timestamps(false);
            state.full(params, samples)?;
            let mut transcript = String::new();
            let num_segments = match state.full_n_segments() {
                Ok(count) => count,
                Err(err) => {
                    log_debug(&format!("Whisper failed to read segment count: {err}"));
                    return Ok(transcript);
                }
            };
            if num_segments < 0 {
                log_debug("Whisper returned a negative segment count");
                return Ok(transcript);
            }
            // Whisper splits output into small segments; stitch them together.
            for i in 0..num_segments {
                match state.full_get_segment_text_lossy(i) {
                    Ok(text) => super::append_whisper_segment(&mut transcript, &text),
                    Err(err) => log_debug(&format!("Failed to read whisper segment {i}: {err}")),
                }
            }
            // Filter out Whisper's [BLANK_AUDIO] token
            let filtered = transcript.replace("[BLANK_AUDIO]", "");
            Ok(filtered)
        }
    }

    fn install_whisper_log_silencer() {
        static INSTALL_LOG_CALLBACK: Once = Once::new();
        INSTALL_LOG_CALLBACK.call_once(|| unsafe {
            // SAFETY: whisper_rs expects a valid callback pointer; we pass a function
            // that ignores its inputs and never dereferences raw pointers.
            whisper_rs::set_log_callback(Some(whisper_log_callback), std::ptr::null_mut());
        });
    }

    #[allow(unused_variables)]
    unsafe extern "C" fn whisper_log_callback(
        _level: c_uint,
        _text: *const c_char,
        _user_data: *mut c_void,
    ) {
        // Silence the default whisper.cpp logger so it does not corrupt the TUI.
        // SAFETY: We do not dereference any incoming pointers.
    }
}

#[cfg(unix)]
pub use platform::Transcriber;

#[cfg(not(unix))]
mod platform {
    use anyhow::{anyhow, Result};

    /// Stub implementation for unsupported targets such as Windows.
    pub struct Transcriber;

    impl Transcriber {
        /// # Errors
        ///
        /// Always returns an error because this target does not support Whisper.
        pub fn new(_: &str) -> Result<Self> {
            Err(anyhow!(
                "Whisper transcription is currently supported only on Unix-like platforms"
            ))
        }

        /// # Errors
        ///
        /// Always returns an error because this target does not support Whisper.
        pub fn transcribe(&self, _: &[f32], _: &AppConfig) -> Result<String> {
            Err(anyhow!(
                "Whisper transcription is currently supported only on Unix-like platforms"
            ))
        }
    }
}

#[cfg(not(unix))]
pub use platform::Transcriber;

#[cfg(test)]
mod tests {
    use super::*;
    #[cfg(unix)]
    use std::io;
    #[cfg(unix)]
    use std::sync::{Mutex, OnceLock};
    #[cfg(unix)]
    use std::thread;
    #[cfg(unix)]
    use std::time::Duration;

    #[test]
    fn append_whisper_segment_inserts_spaces_for_sentence_boundaries() {
        let mut transcript = String::new();
        append_whisper_segment(&mut transcript, "I guess now it does.");
        append_whisper_segment(&mut transcript, "That's kind of weird.");
        append_whisper_segment(&mut transcript, "Nope, there we go.");
        assert_eq!(
            transcript,
            "I guess now it does. That's kind of weird. Nope, there we go."
        );
    }

    #[test]
    fn append_whisper_segment_avoids_extra_space_before_punctuation() {
        let mut transcript = String::new();
        append_whisper_segment(&mut transcript, "hello");
        append_whisper_segment(&mut transcript, "!");
        append_whisper_segment(&mut transcript, "?");
        assert_eq!(transcript, "hello!?");
    }

    #[test]
    fn append_whisper_segment_keeps_contractions_attached() {
        let mut transcript = String::new();
        append_whisper_segment(&mut transcript, "I");
        append_whisper_segment(&mut transcript, "'m");
        append_whisper_segment(&mut transcript, "ready");
        assert_eq!(transcript, "I'm ready");
    }

    #[test]
    fn boundary_spacing_respects_whitespace_and_punctuation_rules() {
        assert!(!should_insert_boundary_space('a', ' '));
        assert!(!should_insert_boundary_space(' ', 'a'));
        assert!(!should_insert_boundary_space('a', '!'));
        assert!(!should_insert_boundary_space('a', '?'));
        assert!(!should_insert_boundary_space('/', 'a'));
        assert!(!should_insert_boundary_space('-', 'a'));
        assert!(!should_insert_boundary_space('(', 'a'));
        assert!(should_insert_boundary_space('a', 'b'));
    }

    #[test]
    fn append_whisper_segment_trims_and_skips_empty_segments() {
        let mut transcript = String::from("hello");
        append_whisper_segment(&mut transcript, "   ");
        append_whisper_segment(&mut transcript, "  world  ");
        append_whisper_segment(&mut transcript, ".");
        assert_eq!(transcript, "hello world.");
    }

    #[cfg(unix)]
    fn stderr_test_lock() -> &'static Mutex<()> {
        static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
        LOCK.get_or_init(|| Mutex::new(()))
    }

    #[cfg(unix)]
    struct StderrPipeGuard {
        saved_stderr_fd: i32,
        read_fd: i32,
    }

    #[cfg(unix)]
    impl StderrPipeGuard {
        fn new() -> Self {
            let mut pipe_fds = [-1i32; 2];
            // SAFETY: pipe_fds is a valid out-pointer for two descriptors.
            let pipe_result = unsafe { libc::pipe(pipe_fds.as_mut_ptr()) };
            assert_eq!(
                pipe_result,
                0,
                "pipe failed: {}",
                io::Error::last_os_error()
            );

            // SAFETY: dup duplicates the current stderr file descriptor.
            let saved_stderr_fd = unsafe { libc::dup(libc::STDERR_FILENO) };
            assert!(
                saved_stderr_fd >= 0,
                "dup(stderr) failed: {}",
                io::Error::last_os_error()
            );

            // SAFETY: dup2 installs pipe_fds[1] as stderr.
            let dup_result = unsafe { libc::dup2(pipe_fds[1], libc::STDERR_FILENO) };
            // SAFETY: close the extra write end; stderr now owns that target.
            unsafe {
                libc::close(pipe_fds[1]);
            }
            assert_eq!(
                dup_result,
                libc::STDERR_FILENO,
                "dup2(stderr<-pipe) failed: {}",
                io::Error::last_os_error()
            );

            // SAFETY: read fd is valid; fcntl reads then updates nonblocking flag.
            let flags = unsafe { libc::fcntl(pipe_fds[0], libc::F_GETFL, 0) };
            assert!(
                flags >= 0,
                "fcntl(F_GETFL) failed: {}",
                io::Error::last_os_error()
            );
            // SAFETY: preserves existing flags and adds O_NONBLOCK.
            let set_result =
                unsafe { libc::fcntl(pipe_fds[0], libc::F_SETFL, flags | libc::O_NONBLOCK) };
            assert_eq!(
                set_result,
                0,
                "fcntl(F_SETFL) failed: {}",
                io::Error::last_os_error()
            );

            Self {
                saved_stderr_fd,
                read_fd: pipe_fds[0],
            }
        }
    }

    #[cfg(unix)]
    impl Drop for StderrPipeGuard {
        fn drop(&mut self) {
            // SAFETY: fds are either valid or already closed; best-effort cleanup.
            unsafe {
                if self.saved_stderr_fd >= 0 {
                    let _ = libc::dup2(self.saved_stderr_fd, libc::STDERR_FILENO);
                    let _ = libc::close(self.saved_stderr_fd);
                    self.saved_stderr_fd = -1;
                }
                if self.read_fd >= 0 {
                    let _ = libc::close(self.read_fd);
                    self.read_fd = -1;
                }
            }
        }
    }

    #[cfg(unix)]
    #[test]
    fn transcriber_rejects_missing_model() {
        let _lock = stderr_test_lock()
            .lock()
            .expect("stderr test lock should not be poisoned");
        let result = Transcriber::new("/no/such/model.bin");
        assert!(result.is_err());
    }

    #[cfg(unix)]
    #[test]
    fn transcriber_restores_stderr_after_failed_model_load() {
        let _lock = stderr_test_lock()
            .lock()
            .expect("stderr test lock should not be poisoned");
        let guard = StderrPipeGuard::new();

        let result = Transcriber::new("/no/such/model.bin");
        assert!(result.is_err());

        let marker = b"stt-stderr-restore-check\n";
        // SAFETY: marker is a valid buffer and STDERR_FILENO is open in-process.
        let write_result = unsafe {
            libc::write(
                libc::STDERR_FILENO,
                marker.as_ptr() as *const libc::c_void,
                marker.len(),
            )
        };
        assert_eq!(
            write_result,
            marker.len() as isize,
            "stderr write failed: {}",
            io::Error::last_os_error()
        );

        let mut buf = [0u8; 256];
        let mut read_len: isize = -1;
        for _ in 0..25 {
            // SAFETY: read_fd is valid for this guard lifetime and buffer is writable.
            let n = unsafe {
                libc::read(
                    guard.read_fd,
                    buf.as_mut_ptr() as *mut libc::c_void,
                    buf.len(),
                )
            };
            if n > 0 {
                read_len = n;
                break;
            }
            if n == 0 {
                break;
            }
            let err = io::Error::last_os_error();
            if err.kind() == io::ErrorKind::WouldBlock {
                thread::sleep(Duration::from_millis(10));
                continue;
            }
            panic!("stderr pipe read failed: {err}");
        }

        assert!(
            read_len > 0,
            "expected stderr marker after restore, read_len={read_len}, err={}",
            io::Error::last_os_error()
        );
        let read_slice = &buf[..read_len as usize];
        assert!(
            read_slice
                .windows(marker.len())
                .any(|window| window == marker),
            "stderr marker missing from restored stream"
        );
    }
}
