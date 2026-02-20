//! Backend login helpers so auth flows run on the controlling TTY reliably.

/// Result type for login attempts.
pub type AuthResult = std::result::Result<(), String>;

fn validate_login_command(command: &str) -> std::result::Result<&str, String> {
    let trimmed = command.trim();
    if trimmed.is_empty() {
        return Err("login command is empty".to_string());
    }
    Ok(trimmed)
}

fn format_login_exit_error(status: std::process::ExitStatus) -> String {
    let code = status
        .code()
        .map(|value| value.to_string())
        .unwrap_or_else(|| "unknown".to_string());
    format!("login exited with code {code}")
}

fn login_status_result(status: std::process::ExitStatus) -> AuthResult {
    if status.success() {
        Ok(())
    } else {
        Err(format_login_exit_error(status))
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
            .map_err(|err| format!("failed to open /dev/tty: {err}"))?;
        let tty_in = tty
            .try_clone()
            .map_err(|err| format!("failed to clone tty for stdin: {err}"))?;
        let tty_out = tty
            .try_clone()
            .map_err(|err| format!("failed to clone tty for stdout: {err}"))?;
        let tty_err = tty;

        let status = Command::new(trimmed)
            .arg("login")
            .stdin(Stdio::from(tty_in))
            .stdout(Stdio::from(tty_out))
            .stderr(Stdio::from(tty_err))
            .status()
            .map_err(|err| format!("failed to spawn {trimmed} login: {err}"))?;

        login_status_result(status)
    }

    #[cfg(not(unix))]
    {
        let _ = trimmed;
        Err("TTY auth is only supported on Unix platforms".to_string())
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
            Err(err) => assert_eq!(err, "login command is empty"),
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
            Err(err) => assert_eq!(err, "login exited with code 7"),
            Ok(()) => panic!("non-zero exit should fail"),
        }
    }

    #[test]
    fn run_login_command_rejects_blank_input() {
        match run_login_command("   ") {
            Err(err) => assert_eq!(err, "login command is empty"),
            Ok(()) => panic!("blank command should fail"),
        }
    }

    #[cfg(unix)]
    #[test]
    fn run_login_command_with_missing_command_reports_spawn_or_tty_error() {
        match run_login_command("/definitely/not/a/real/voiceterm-login-command") {
            Err(err) => {
                assert!(
                    err.starts_with("failed to open /dev/tty:")
                        || err.starts_with(
                            "failed to spawn /definitely/not/a/real/voiceterm-login-command login:"
                        ),
                    "unexpected error: {err}"
                );
            }
            Ok(()) => panic!("missing command should fail"),
        }
    }

    #[cfg(not(unix))]
    #[test]
    fn run_login_command_non_unix_reports_unsupported_platform() {
        match run_login_command("codex") {
            Err(err) => assert_eq!(err, "TTY auth is only supported on Unix platforms"),
            Ok(()) => panic!("non-unix auth should fail"),
        }
    }
}
