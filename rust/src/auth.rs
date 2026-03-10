//! Backend login helpers so auth flows run on the controlling TTY reliably.

use std::error::Error;
use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AuthError {
    EmptyCommand,
    OpenTty(String),
    CloneTty {
        stream: &'static str,
        message: String,
    },
    SpawnLogin {
        command: String,
        message: String,
    },
    LoginExited {
        code: Option<i32>,
    },
    UnsupportedPlatform,
    ProviderLogin {
        provider: String,
        source: Box<AuthError>,
    },
    Message(String),
}

impl AuthError {
    #[must_use]
    pub fn with_provider(self, provider: &str) -> Self {
        Self::ProviderLogin {
            provider: provider.to_string(),
            source: Box::new(self),
        }
    }

    #[must_use]
    pub fn message(message: impl Into<String>) -> Self {
        Self::Message(message.into())
    }
}

impl fmt::Display for AuthError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyCommand => write!(f, "login command is empty"),
            Self::OpenTty(message) => write!(f, "failed to open /dev/tty: {message}"),
            Self::CloneTty { stream, message } => {
                write!(f, "failed to clone tty for {stream}: {message}")
            }
            Self::SpawnLogin { command, message } => {
                write!(f, "failed to spawn {command} login: {message}")
            }
            Self::LoginExited { code } => match code {
                Some(code) => write!(f, "login exited with code {code}"),
                None => write!(f, "login exited with code unknown"),
            },
            Self::UnsupportedPlatform => {
                write!(f, "TTY auth is only supported on Unix platforms")
            }
            Self::ProviderLogin { provider, source } => {
                write!(f, "{provider} auth failed: {source}")
            }
            Self::Message(message) => write!(f, "{message}"),
        }
    }
}

impl Error for AuthError {}

/// Result type for login attempts.
pub type AuthResult = std::result::Result<(), AuthError>;

fn validate_login_command(command: &str) -> std::result::Result<&str, AuthError> {
    let trimmed = command.trim();
    if trimmed.is_empty() {
        return Err(AuthError::EmptyCommand);
    }
    Ok(trimmed)
}

fn login_status_result(status: std::process::ExitStatus) -> AuthResult {
    if status.success() {
        Ok(())
    } else {
        Err(AuthError::LoginExited {
            code: status.code(),
        })
    }
}

/// Run `<command> login` using the controlling TTY so the CLI can prompt the user.
///
/// # Errors
///
/// Returns an error when the command is empty, a controlling TTY cannot be
/// opened, process launch fails, or the login command exits unsuccessfully.
pub fn run_login_command(command: &str) -> AuthResult {
    let trimmed = validate_login_command(command)?;

    #[cfg(unix)]
    {
        use std::fs::OpenOptions;
        use std::process::{Command, Stdio};

        let tty = OpenOptions::new()
            .read(true)
            .write(true)
            .open("/dev/tty")
            .map_err(|err| AuthError::OpenTty(err.to_string()))?;
        let tty_in = tty.try_clone().map_err(|err| AuthError::CloneTty {
            stream: "stdin",
            message: err.to_string(),
        })?;
        let tty_out = tty.try_clone().map_err(|err| AuthError::CloneTty {
            stream: "stdout",
            message: err.to_string(),
        })?;
        let tty_err = tty;

        let status = Command::new(trimmed)
            .arg("login")
            .stdin(Stdio::from(tty_in))
            .stdout(Stdio::from(tty_out))
            .stderr(Stdio::from(tty_err))
            .status()
            .map_err(|err| AuthError::SpawnLogin {
                command: trimmed.to_string(),
                message: err.to_string(),
            })?;

        login_status_result(status)
    }

    #[cfg(not(unix))]
    {
        let _ = trimmed;
        Err(AuthError::UnsupportedPlatform)
    }
}

#[cfg(test)]
mod tests {
    use super::{login_status_result, run_login_command, validate_login_command};

    #[cfg(unix)]
    fn success_status() -> std::process::ExitStatus {
        match std::process::Command::new("sh")
            .args(["-c", "exit 0"])
            .status()
        {
            Ok(status) => status,
            Err(err) => panic!("shell should produce a success exit status: {err}"),
        }
    }

    #[cfg(windows)]
    fn success_status() -> std::process::ExitStatus {
        match std::process::Command::new("cmd")
            .args(["/C", "exit", "0"])
            .status()
        {
            Ok(status) => status,
            Err(err) => panic!("cmd should produce a success exit status: {err}"),
        }
    }

    #[cfg(unix)]
    fn failure_status(code: i32) -> std::process::ExitStatus {
        match std::process::Command::new("sh")
            .args(["-c", &format!("exit {code}")])
            .status()
        {
            Ok(status) => status,
            Err(err) => panic!("shell should produce a failure exit status: {err}"),
        }
    }

    #[cfg(windows)]
    fn failure_status(code: i32) -> std::process::ExitStatus {
        match std::process::Command::new("cmd")
            .args(["/C", "exit", &code.to_string()])
            .status()
        {
            Ok(status) => status,
            Err(err) => panic!("cmd should produce a failure exit status: {err}"),
        }
    }

    #[test]
    fn validate_login_command_rejects_blank_input() {
        match validate_login_command("   ") {
            Err(err) => assert_eq!(err.to_string(), "login command is empty"),
            Ok(value) => panic!("blank command should fail, got {value}"),
        }
    }

    #[test]
    fn validate_login_command_trims_whitespace() {
        match validate_login_command("  codex  ") {
            Ok(value) => assert_eq!(value, "codex"),
            Err(err) => panic!("command should trim: {err}"),
        }
    }

    #[cfg(any(unix, windows))]
    #[test]
    fn login_status_result_returns_ok_for_success_status() {
        assert!(login_status_result(success_status()).is_ok());
    }

    #[cfg(any(unix, windows))]
    #[test]
    fn login_status_result_formats_failure_exit_code() {
        match login_status_result(failure_status(7)) {
            Err(err) => assert_eq!(err.to_string(), "login exited with code 7"),
            Ok(()) => panic!("non-zero exit should fail"),
        }
    }

    #[test]
    fn run_login_command_rejects_blank_input() {
        match run_login_command("   ") {
            Err(err) => assert_eq!(err.to_string(), "login command is empty"),
            Ok(()) => panic!("blank command should fail"),
        }
    }

    #[cfg(unix)]
    #[test]
    fn run_login_command_with_missing_command_reports_spawn_or_tty_error() {
        match run_login_command("/definitely/not/a/real/voiceterm-login-command") {
            Err(err) => {
                let message = err.to_string();
                assert!(
                    message.starts_with("failed to open /dev/tty:")
                        || message.starts_with(
                            "failed to spawn /definitely/not/a/real/voiceterm-login-command login:"
                        ),
                    "unexpected error: {message}"
                );
            }
            Ok(()) => panic!("missing command should fail"),
        }
    }

    #[cfg(not(unix))]
    #[test]
    fn run_login_command_non_unix_reports_unsupported_platform() {
        match run_login_command("codex") {
            Err(err) => assert_eq!(
                err.to_string(),
                "TTY auth is only supported on Unix platforms"
            ),
            Ok(()) => panic!("non-unix auth should fail"),
        }
    }
}
