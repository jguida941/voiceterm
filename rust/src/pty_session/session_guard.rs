//! Tracks PTY child ownership so new sessions can reap stale backend parents from dead runtimes.

use crate::lock_or_recover;
use crate::log_debug;
use crate::process_signal::signal_process_group_or_pid;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io;
use std::os::unix::io::RawFd;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, OnceLock};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

const SESSION_GUARD_DIR_ENV: &str = "VOICETERM_SESSION_GUARD_DIR";
const SESSION_GUARD_ENABLED_ENV: &str = "VOICETERM_SESSION_GUARD";
const ORPHAN_SWEEP_ENABLED_ENV: &str = "VOICETERM_ORPHAN_SWEEP";
const SESSION_GUARD_DIR_NAME: &str = "voiceterm-session-guard";
const SESSION_TERMINATION_GRACE_MS: u64 = 500;
const STALE_CLEANUP_MIN_INTERVAL_MS: u64 = 2_000;
const ORPHAN_SWEEP_MIN_AGE_SECS: u64 = 60;

static SESSION_FILE_SEQUENCE: AtomicU64 = AtomicU64::new(0);
static LAST_STALE_CLEANUP_MS: AtomicU64 = AtomicU64::new(0);
static ACTIVE_SESSION_FILES: OnceLock<Mutex<HashMap<RawFd, PathBuf>>> = OnceLock::new();

#[derive(Debug, Clone)]
struct SessionLeaseEntry {
    owner_pid: i32,
    owner_exec_name: String,
    owner_start_time: Option<String>,
    child_pid: i32,
    exec_name: String,
    child_start_time: Option<String>,
}

impl SessionLeaseEntry {
    fn to_text(&self) -> String {
        let mut text = format!(
            "owner_pid={}\nowner_exec_name={}\nchild_pid={}\nexec_name={}\n",
            self.owner_pid, self.owner_exec_name, self.child_pid, self.exec_name
        );
        if let Some(owner_start_time) = &self.owner_start_time {
            text.push_str(&format!("owner_start_time={owner_start_time}\n"));
        }
        if let Some(child_start_time) = &self.child_start_time {
            text.push_str(&format!("child_start_time={child_start_time}\n"));
        }
        text
    }

    fn parse(text: &str) -> Option<Self> {
        let mut owner_pid = None;
        let mut owner_exec_name = None;
        let mut owner_start_time = None;
        let mut child_pid = None;
        let mut exec_name = None;
        let mut child_start_time = None;
        for line in text.lines() {
            let (key, value) = line.split_once('=')?;
            match key {
                "owner_pid" => owner_pid = value.parse::<i32>().ok(),
                "owner_exec_name" => owner_exec_name = Some(value.to_string()),
                "owner_start_time" => owner_start_time = Some(value.to_string()),
                "child_pid" => child_pid = value.parse::<i32>().ok(),
                "exec_name" => exec_name = Some(value.to_string()),
                "child_start_time" => child_start_time = Some(value.to_string()),
                _ => {}
            }
        }
        let owner_pid = owner_pid?;
        let owner_exec_name = owner_exec_name.unwrap_or_else(|| "voiceterm".to_string());
        let child_pid = child_pid?;
        let exec_name = exec_name?;
        if owner_exec_name.trim().is_empty() || exec_name.trim().is_empty() {
            return None;
        }
        Some(Self {
            owner_pid,
            owner_exec_name,
            owner_start_time,
            child_pid,
            exec_name,
            child_start_time,
        })
    }
}

#[derive(Debug, Clone)]
struct ProcessSnapshot {
    pid: i32,
    ppid: i32,
    tty: String,
    elapsed: Duration,
    command_line: String,
    exec_name: String,
}

fn active_session_files() -> &'static Mutex<HashMap<RawFd, PathBuf>> {
    ACTIVE_SESSION_FILES.get_or_init(|| Mutex::new(HashMap::new()))
}

fn session_guard_enabled() -> bool {
    !matches!(
        std::env::var(SESSION_GUARD_ENABLED_ENV),
        Ok(value)
            if value.eq_ignore_ascii_case("0")
                || value.eq_ignore_ascii_case("false")
                || value.eq_ignore_ascii_case("off")
    )
}

fn orphan_sweep_enabled() -> bool {
    #[cfg(test)]
    if !matches!(
        std::env::var("VOICETERM_ORPHAN_SWEEP_TEST"),
        Ok(value) if value == "1"
    ) {
        return false;
    }

    !matches!(
        std::env::var(ORPHAN_SWEEP_ENABLED_ENV),
        Ok(value)
            if value.eq_ignore_ascii_case("0")
                || value.eq_ignore_ascii_case("false")
                || value.eq_ignore_ascii_case("off")
    )
}

fn session_guard_dir() -> PathBuf {
    if let Ok(path) = std::env::var(SESSION_GUARD_DIR_ENV) {
        let path = path.trim();
        if !path.is_empty() {
            return PathBuf::from(path);
        }
    }
    std::env::temp_dir().join(SESSION_GUARD_DIR_NAME)
}

fn exec_basename(cli_cmd: &str) -> String {
    Path::new(cli_cmd)
        .file_name()
        .and_then(|name| name.to_str())
        .map(ToString::to_string)
        .unwrap_or_else(|| cli_cmd.to_string())
}

fn session_file_path(base_dir: &Path, owner_pid: i32, child_pid: i32) -> PathBuf {
    let now_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_nanos())
        .unwrap_or_default();
    let seq = SESSION_FILE_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    base_dir.join(format!(
        "session-{owner_pid}-{child_pid}-{now_ns}-{seq}.lease"
    ))
}

fn parse_etime_seconds(raw: &str) -> Option<u64> {
    let trimmed = raw.trim();
    if trimmed.is_empty() {
        return None;
    }

    let (days, rest) = if let Some((day_part, time_part)) = trimmed.split_once('-') {
        (day_part.parse::<u64>().ok()?, time_part)
    } else {
        (0, trimmed)
    };

    let mut parts = rest.split(':');
    let first = parts.next()?.parse::<u64>().ok()?;
    let second = parts.next()?.parse::<u64>().ok()?;
    let third = parts.next().and_then(|value| value.parse::<u64>().ok());

    let seconds = match third {
        Some(ss) => first
            .saturating_mul(3600)
            .saturating_add(second.saturating_mul(60))
            .saturating_add(ss),
        None => first.saturating_mul(60).saturating_add(second),
    };
    Some(days.saturating_mul(86_400).saturating_add(seconds))
}

fn parse_ps_snapshot_line(line: &str) -> Option<ProcessSnapshot> {
    let trimmed = line.trim();
    if trimmed.is_empty() {
        return None;
    }

    let mut parts = trimmed.split_whitespace();
    let pid = parts.next()?.parse::<i32>().ok()?;
    let ppid = parts.next()?.parse::<i32>().ok()?;
    let tty = parts.next()?.to_string();
    let elapsed = Duration::from_secs(parse_etime_seconds(parts.next()?)?);
    let command_line = parts.collect::<Vec<_>>().join(" ");
    if command_line.is_empty() {
        return None;
    }
    let exec_name = command_basename(&command_line)?;
    Some(ProcessSnapshot {
        pid,
        ppid,
        tty,
        elapsed,
        command_line,
        exec_name,
    })
}

fn process_snapshots() -> Vec<ProcessSnapshot> {
    let Ok(output) = Command::new("ps")
        .args(["-axo", "pid=,ppid=,tty=,etime=,command="])
        .output()
    else {
        log_debug("session guard: detached orphan sweep skipped (ps snapshot unavailable)");
        return Vec::new();
    };
    String::from_utf8_lossy(&output.stdout)
        .lines()
        .filter_map(parse_ps_snapshot_line)
        .collect()
}

fn collect_leased_child_pids(base_dir: &Path) -> HashSet<i32> {
    let mut leased_pids = HashSet::new();
    let Ok(entries) = fs::read_dir(base_dir) else {
        return leased_pids;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let Ok(contents) = fs::read_to_string(path) else {
            continue;
        };
        let Some(lease) = SessionLeaseEntry::parse(&contents) else {
            continue;
        };
        leased_pids.insert(lease.child_pid);
    }
    leased_pids
}

fn exec_is_shell(exec_name: &str) -> bool {
    matches!(
        exec_name,
        "sh" | "bash" | "zsh" | "fish" | "nu" | "ksh" | "tcsh"
    )
}

fn exec_is_backend(exec_name: &str) -> bool {
    matches!(
        exec_name,
        "codex" | "claude" | "gemini" | "aider" | "opencode"
    )
}

fn orphan_candidates_from_snapshots(
    snapshots: &[ProcessSnapshot],
    leased_child_pids: &HashSet<i32>,
    min_age: Duration,
) -> Vec<ProcessSnapshot> {
    let tty_with_shell: HashSet<&str> = snapshots
        .iter()
        .filter(|snapshot| exec_is_shell(&snapshot.exec_name))
        .map(|snapshot| snapshot.tty.as_str())
        .collect();

    snapshots
        .iter()
        .filter(|snapshot| snapshot.pid > 1)
        .filter(|snapshot| snapshot.ppid == 1)
        .filter(|snapshot| snapshot.tty != "?" && snapshot.tty != "??")
        .filter(|snapshot| exec_is_backend(&snapshot.exec_name))
        .filter(|snapshot| snapshot.elapsed >= min_age)
        .filter(|snapshot| !leased_child_pids.contains(&snapshot.pid))
        .filter(|snapshot| !tty_with_shell.contains(snapshot.tty.as_str()))
        .cloned()
        .collect()
}

fn process_exists(pid: i32) -> bool {
    if pid <= 0 {
        return false;
    }
    // SAFETY: kill(pid, 0) probes process existence without sending a signal.
    unsafe {
        if libc::kill(pid, 0) == 0 {
            return true;
        }
        matches!(
            io::Error::last_os_error().raw_os_error(),
            Some(code) if code == libc::EPERM
        )
    }
}

fn process_command_line(pid: i32) -> Option<String> {
    if pid <= 0 {
        return None;
    }
    let output = Command::new("ps")
        .args(["-p", &pid.to_string(), "-o", "command="])
        .output()
        .ok()?;
    let command = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if command.is_empty() {
        return None;
    }
    Some(command)
}

fn command_basename(command_line: &str) -> Option<String> {
    let token = command_line.split_whitespace().next()?;
    let basename = Path::new(token)
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or(token);
    if basename.trim().is_empty() {
        return None;
    }
    Some(basename.to_string())
}

fn process_parent_pid(pid: i32) -> Option<i32> {
    if pid <= 0 {
        return None;
    }
    let output = Command::new("ps")
        .args(["-p", &pid.to_string(), "-o", "ppid="])
        .output()
        .ok()?;
    let value = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if value.is_empty() {
        return None;
    }
    value.parse::<i32>().ok()
}

fn process_start_time(pid: i32) -> Option<String> {
    if pid <= 0 {
        return None;
    }
    let output = Command::new("ps")
        .args(["-p", &pid.to_string(), "-o", "lstart="])
        .output()
        .ok()?;
    let start_time = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if start_time.is_empty() {
        return None;
    }
    Some(start_time)
}

fn command_matches_exec_name(command_line: &str, exec_name: &str) -> bool {
    command_basename(command_line)
        .map(|basename| basename == exec_name)
        .unwrap_or(false)
}

fn owner_process_is_live(
    owner_pid: i32,
    expected_exec_name: &str,
    expected_start_time: Option<&str>,
) -> bool {
    if !process_exists(owner_pid) {
        return false;
    }
    let Some(command_line) = process_command_line(owner_pid) else {
        // If we cannot inspect the command line, be conservative and assume the owner is alive.
        return true;
    };
    if !command_matches_exec_name(&command_line, expected_exec_name) {
        return false;
    }
    if let Some(expected_start_time) = expected_start_time {
        let Some(actual_start_time) = process_start_time(owner_pid) else {
            // If we cannot inspect process start-time, prefer false-negative over false-positive cleanup.
            return true;
        };
        return actual_start_time == expected_start_time;
    }
    true
}

fn cleanup_clock_millis() -> u64 {
    let now_ms = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis())
        .unwrap_or_default();
    now_ms.min(u128::from(u64::MAX)) as u64
}

fn cleanup_allowed(last_cleanup_ms: u64, now_ms: u64, min_interval_ms: u64) -> bool {
    last_cleanup_ms == 0 || now_ms.saturating_sub(last_cleanup_ms) >= min_interval_ms
}

fn should_run_cleanup(now_ms: u64, min_interval_ms: u64) -> bool {
    let mut prior = LAST_STALE_CLEANUP_MS.load(Ordering::Relaxed);
    loop {
        if !cleanup_allowed(prior, now_ms, min_interval_ms) {
            return false;
        }
        match LAST_STALE_CLEANUP_MS.compare_exchange_weak(
            prior,
            now_ms,
            Ordering::Relaxed,
            Ordering::Relaxed,
        ) {
            Ok(_) => return true,
            Err(observed) => prior = observed,
        }
    }
}

fn terminate_stale_process_tree(child_pid: i32) {
    if child_pid <= 0 {
        return;
    }
    let _ = signal_process_group_or_pid(child_pid, libc::SIGTERM, true);
    let deadline = Instant::now() + Duration::from_millis(SESSION_TERMINATION_GRACE_MS);
    while process_exists(child_pid) && Instant::now() < deadline {
        thread::sleep(Duration::from_millis(20));
    }
    if process_exists(child_pid) {
        let _ = signal_process_group_or_pid(child_pid, libc::SIGKILL, true);
    }
}

fn cleanup_stale_sessions_in_dir(base_dir: &Path) {
    let Ok(entries) = fs::read_dir(base_dir) else {
        return;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let Ok(contents) = fs::read_to_string(&path) else {
            let _ = fs::remove_file(&path);
            continue;
        };
        let Some(lease) = SessionLeaseEntry::parse(&contents) else {
            let _ = fs::remove_file(&path);
            continue;
        };
        if owner_process_is_live(
            lease.owner_pid,
            &lease.owner_exec_name,
            lease.owner_start_time.as_deref(),
        ) {
            continue;
        }
        if process_exists(lease.child_pid) {
            if let Some(parent_pid) = process_parent_pid(lease.child_pid) {
                if parent_pid > 1 && parent_pid != lease.owner_pid {
                    log_debug(&format!(
                        "session guard: stale lease parent mismatch for pid={} owner_pid={} parent_pid={}",
                        lease.child_pid, lease.owner_pid, parent_pid
                    ));
                    let _ = fs::remove_file(&path);
                    continue;
                }
            }
            let Some(command_line) = process_command_line(lease.child_pid) else {
                log_debug(&format!(
                    "session guard: stale lease command lookup failed for pid={}",
                    lease.child_pid
                ));
                let _ = fs::remove_file(&path);
                continue;
            };
            if !command_matches_exec_name(&command_line, &lease.exec_name) {
                log_debug(&format!(
                    "session guard: stale lease command mismatch for pid={} expected={} actual={}",
                    lease.child_pid, lease.exec_name, command_line
                ));
                let _ = fs::remove_file(&path);
                continue;
            }
            if let Some(expected_start_time) = lease.child_start_time.as_deref() {
                let Some(actual_start_time) = process_start_time(lease.child_pid) else {
                    log_debug(&format!(
                        "session guard: stale lease start-time lookup failed for pid={}",
                        lease.child_pid
                    ));
                    let _ = fs::remove_file(&path);
                    continue;
                };
                if actual_start_time != expected_start_time {
                    log_debug(&format!(
                        "session guard: stale lease start-time mismatch for pid={} expected={} actual={}",
                        lease.child_pid, expected_start_time, actual_start_time
                    ));
                    let _ = fs::remove_file(&path);
                    continue;
                }
            }
            log_debug(&format!(
                "session guard: reaping stale backend pid={} exec={}",
                lease.child_pid, lease.exec_name
            ));
            terminate_stale_process_tree(lease.child_pid);
        }
        let _ = fs::remove_file(&path);
    }
}

fn cleanup_detached_backend_orphans(base_dir: &Path) {
    if !orphan_sweep_enabled() {
        return;
    }
    let leased_child_pids = collect_leased_child_pids(base_dir);
    let candidates = orphan_candidates_from_snapshots(
        &process_snapshots(),
        &leased_child_pids,
        Duration::from_secs(ORPHAN_SWEEP_MIN_AGE_SECS),
    );
    for candidate in candidates {
        log_debug(&format!(
            "session guard: reaping detached backend pid={} exec={} tty={} elapsed={:?} cmd={}",
            candidate.pid,
            candidate.exec_name,
            candidate.tty,
            candidate.elapsed,
            candidate.command_line
        ));
        terminate_stale_process_tree(candidate.pid);
    }
}

pub(super) fn cleanup_stale_sessions() {
    if !session_guard_enabled() {
        return;
    }
    if !should_run_cleanup(cleanup_clock_millis(), STALE_CLEANUP_MIN_INTERVAL_MS) {
        return;
    }
    let base_dir = session_guard_dir();
    if let Err(err) = fs::create_dir_all(&base_dir) {
        log_debug(&format!(
            "session guard: failed to create dir {}: {}",
            base_dir.display(),
            err
        ));
        return;
    }
    cleanup_stale_sessions_in_dir(&base_dir);
    cleanup_detached_backend_orphans(&base_dir);
}

pub(super) fn register_session(master_fd: RawFd, child_pid: i32, cli_cmd: &str) {
    if !session_guard_enabled() || child_pid <= 0 {
        return;
    }
    let owner_pid = unsafe { libc::getpid() as i32 };
    let owner_exec_name = process_command_line(owner_pid)
        .and_then(|line| command_basename(&line))
        .unwrap_or_else(|| "voiceterm".to_string());
    let exec_name = exec_basename(cli_cmd);
    let lease = SessionLeaseEntry {
        owner_pid,
        owner_exec_name,
        owner_start_time: process_start_time(owner_pid),
        child_pid,
        exec_name,
        child_start_time: process_start_time(child_pid),
    };
    let base_dir = session_guard_dir();
    if let Err(err) = fs::create_dir_all(&base_dir) {
        log_debug(&format!(
            "session guard: failed to create dir {}: {}",
            base_dir.display(),
            err
        ));
        return;
    }
    let lease_path = session_file_path(&base_dir, owner_pid, child_pid);
    if let Err(err) = fs::write(&lease_path, lease.to_text()) {
        log_debug(&format!(
            "session guard: failed to write lease {}: {}",
            lease_path.display(),
            err
        ));
        return;
    }
    let mut registry = lock_or_recover(
        active_session_files(),
        "pty_session::session_guard::register_session",
    );
    if let Some(previous) = registry.insert(master_fd, lease_path) {
        let _ = fs::remove_file(previous);
    }
}

pub(super) fn unregister_session(master_fd: RawFd) {
    if !session_guard_enabled() {
        return;
    }
    let path = {
        let mut registry = lock_or_recover(
            active_session_files(),
            "pty_session::session_guard::unregister_session",
        );
        registry.remove(&master_fd)
    };
    if let Some(path) = path {
        let _ = fs::remove_file(path);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_dir(label: &str) -> PathBuf {
        let pid = unsafe { libc::getpid() as i32 };
        let seq = SESSION_FILE_SEQUENCE.fetch_add(1, Ordering::Relaxed);
        let path =
            std::env::temp_dir().join(format!("voiceterm-session-guard-test-{label}-{pid}-{seq}"));
        fs::create_dir_all(&path).expect("create test dir");
        path
    }

    fn remove_test_dir(path: &Path) {
        let _ = fs::remove_dir_all(path);
    }

    fn missing_pid() -> i32 {
        let current = unsafe { libc::getpid() as i32 };
        let mut pid = current + 10_000;
        for _ in 0..2000 {
            if !process_exists(pid) {
                return pid;
            }
            pid += 1;
        }
        pid
    }

    #[test]
    fn lease_entry_roundtrip() {
        let entry = SessionLeaseEntry {
            owner_pid: 11,
            owner_exec_name: "voiceterm".to_string(),
            owner_start_time: Some("Mon Jan  1 00:00:00 2024".to_string()),
            child_pid: 22,
            exec_name: "codex".to_string(),
            child_start_time: Some("Mon Jan  1 00:00:01 2024".to_string()),
        };
        let text = entry.to_text();
        let parsed = SessionLeaseEntry::parse(&text).expect("parse lease");
        assert_eq!(parsed.owner_pid, 11);
        assert_eq!(parsed.owner_exec_name, "voiceterm");
        assert_eq!(
            parsed.owner_start_time.as_deref(),
            Some("Mon Jan  1 00:00:00 2024")
        );
        assert_eq!(parsed.child_pid, 22);
        assert_eq!(parsed.exec_name, "codex");
        assert_eq!(
            parsed.child_start_time.as_deref(),
            Some("Mon Jan  1 00:00:01 2024")
        );
    }

    #[test]
    fn lease_entry_parse_accepts_legacy_format_without_start_times() {
        let text = "owner_pid=11\nowner_exec_name=voiceterm\nchild_pid=22\nexec_name=codex\n";
        let parsed = SessionLeaseEntry::parse(text).expect("parse lease");
        assert_eq!(parsed.owner_pid, 11);
        assert_eq!(parsed.owner_exec_name, "voiceterm");
        assert!(parsed.owner_start_time.is_none());
        assert_eq!(parsed.child_pid, 22);
        assert_eq!(parsed.exec_name, "codex");
        assert!(parsed.child_start_time.is_none());
    }

    #[test]
    fn command_match_uses_command_basename() {
        assert!(command_matches_exec_name(
            "/opt/homebrew/bin/codex --version",
            "codex"
        ));
        assert!(!command_matches_exec_name(
            "/usr/bin/python3 app.py",
            "codex"
        ));
    }

    #[test]
    fn owner_process_liveness_rejects_start_time_mismatch() {
        let owner_pid = unsafe { libc::getpid() as i32 };
        let owner_exec_name = process_command_line(owner_pid)
            .and_then(|line| command_basename(&line))
            .unwrap_or_else(|| "voiceterm".to_string());
        if let Some(owner_start_time) = process_start_time(owner_pid) {
            assert!(owner_process_is_live(
                owner_pid,
                &owner_exec_name,
                Some(&owner_start_time)
            ));
            let mismatched_start_time = format!("{owner_start_time}-mismatch");
            let mismatch_live =
                owner_process_is_live(owner_pid, &owner_exec_name, Some(&mismatched_start_time));
            if mismatch_live {
                // Owner-liveness intentionally returns true when a start-time
                // probe is unavailable to avoid false-positive cleanup.
                assert!(process_start_time(owner_pid).is_none());
            } else {
                assert!(!mismatch_live);
            }
        } else {
            assert!(owner_process_is_live(owner_pid, &owner_exec_name, None));
        }
    }

    #[test]
    fn cleanup_allowed_respects_min_interval() {
        assert!(cleanup_allowed(0, 10_000, 500));
        assert!(!cleanup_allowed(10_000, 10_300, 500));
        assert!(cleanup_allowed(10_000, 10_600, 500));
    }

    #[test]
    fn cleanup_removes_entry_for_missing_owner() {
        let dir = create_test_dir("missing-owner");
        let path = dir.join("lease.lease");
        let entry = SessionLeaseEntry {
            owner_pid: missing_pid(),
            owner_exec_name: "voiceterm".to_string(),
            owner_start_time: None,
            child_pid: missing_pid() + 1,
            exec_name: "codex".to_string(),
            child_start_time: None,
        };
        fs::write(&path, entry.to_text()).expect("write lease");
        cleanup_stale_sessions_in_dir(&dir);
        assert!(!path.exists(), "stale lease file should be removed");
        remove_test_dir(&dir);
    }

    #[test]
    fn cleanup_keeps_entry_for_live_owner() {
        let dir = create_test_dir("live-owner");
        let path = dir.join("lease.lease");
        let owner_pid = unsafe { libc::getpid() as i32 };
        let entry = SessionLeaseEntry {
            owner_pid,
            owner_exec_name: process_command_line(owner_pid)
                .and_then(|line| command_basename(&line))
                .unwrap_or_else(|| "voiceterm".to_string()),
            owner_start_time: process_start_time(owner_pid),
            child_pid: missing_pid(),
            exec_name: "codex".to_string(),
            child_start_time: None,
        };
        fs::write(&path, entry.to_text()).expect("write lease");
        cleanup_stale_sessions_in_dir(&dir);
        assert!(path.exists(), "live-owner lease should remain");
        remove_test_dir(&dir);
    }

    #[test]
    fn parse_etime_seconds_handles_common_ps_formats() {
        assert_eq!(parse_etime_seconds("00:05"), Some(5));
        assert_eq!(parse_etime_seconds("03:20"), Some(200));
        assert_eq!(parse_etime_seconds("01:02:03"), Some(3723));
        assert_eq!(
            parse_etime_seconds("2-03:04:05"),
            Some((2 * 86_400) + (3 * 3600) + (4 * 60) + 5)
        );
        assert_eq!(parse_etime_seconds(""), None);
        assert_eq!(parse_etime_seconds("bad"), None);
    }

    #[test]
    fn parse_ps_snapshot_line_extracts_fields() {
        let line = "123 1 ttys080 01:23 codex -C /tmp";
        let parsed = parse_ps_snapshot_line(line).expect("snapshot parse");
        assert_eq!(parsed.pid, 123);
        assert_eq!(parsed.ppid, 1);
        assert_eq!(parsed.tty, "ttys080");
        assert_eq!(parsed.elapsed, Duration::from_secs(83));
        assert_eq!(parsed.exec_name, "codex");
        assert_eq!(parsed.command_line, "codex -C /tmp");
    }

    #[test]
    fn orphan_candidates_require_detached_backend_without_shell() {
        let snapshots = vec![
            ProcessSnapshot {
                pid: 700,
                ppid: 1,
                tty: "ttys080".to_string(),
                elapsed: Duration::from_secs(240),
                command_line: "codex".to_string(),
                exec_name: "codex".to_string(),
            },
            ProcessSnapshot {
                pid: 701,
                ppid: 995,
                tty: "ttys080".to_string(),
                elapsed: Duration::from_secs(240),
                command_line: "/bin/zsh -il".to_string(),
                exec_name: "zsh".to_string(),
            },
            ProcessSnapshot {
                pid: 702,
                ppid: 1,
                tty: "ttys081".to_string(),
                elapsed: Duration::from_secs(240),
                command_line: "claude".to_string(),
                exec_name: "claude".to_string(),
            },
            ProcessSnapshot {
                pid: 703,
                ppid: 1,
                tty: "??".to_string(),
                elapsed: Duration::from_secs(240),
                command_line: "codex".to_string(),
                exec_name: "codex".to_string(),
            },
            ProcessSnapshot {
                pid: 704,
                ppid: 1,
                tty: "ttys082".to_string(),
                elapsed: Duration::from_secs(10),
                command_line: "codex".to_string(),
                exec_name: "codex".to_string(),
            },
        ];

        let leased = HashSet::from([702]);
        let candidates =
            orphan_candidates_from_snapshots(&snapshots, &leased, Duration::from_secs(60));

        assert!(
            candidates.is_empty(),
            "shell-backed, leased, detached-tty, and too-young candidates should all be filtered"
        );
    }

    #[test]
    fn orphan_candidates_include_detached_backend_without_shell_or_lease() {
        let snapshots = vec![ProcessSnapshot {
            pid: 801,
            ppid: 1,
            tty: "ttys090".to_string(),
            elapsed: Duration::from_secs(600),
            command_line: "codex".to_string(),
            exec_name: "codex".to_string(),
        }];
        let leased = HashSet::new();
        let candidates =
            orphan_candidates_from_snapshots(&snapshots, &leased, Duration::from_secs(60));
        assert_eq!(candidates.len(), 1);
        assert_eq!(candidates[0].pid, 801);
    }
}
