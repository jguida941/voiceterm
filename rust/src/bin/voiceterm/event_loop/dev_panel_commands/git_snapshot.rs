//! Git status snapshot capture and parsing for the Control page.

use super::super::*;
use std::path::{Path, PathBuf};

/// Capture git repo state into a snapshot for the Control page renderer.
/// Git commands should follow the live PTY shell cwd so a normal `cd`
/// inside the terminal changes the repo context shown in Control/Handoff.
pub(in super::super) fn refresh_git_snapshot(
    state: &mut EventLoopState,
    session: &voiceterm::pty_session::PtyOverlaySession,
) {
    let snapshot = capture_git_status(
        resolve_session_working_dir(session.child_pid()).as_deref(),
        Path::new(&state.working_dir),
    );
    state.dev_panel_commands.set_git_snapshot(snapshot);
}

/// Run git commands and parse output into a `GitStatusSnapshot`.
fn capture_git_status(
    start_dir: Option<&Path>,
    fallback_dir: &Path,
) -> crate::dev_command::GitStatusSnapshot {
    let repo_root = match find_git_root(start_dir, fallback_dir) {
        Some(root) => root,
        None => {
            return crate::dev_command::GitStatusSnapshot {
                has_error: true,
                error_message: format!("not a git repository: {}", fallback_dir.display()),
                ..Default::default()
            };
        }
    };

    let mut snapshot = crate::dev_command::GitStatusSnapshot::default();

    // `git status --porcelain -b` gives branch + upstream + dirty files in one call.
    match std::process::Command::new("git")
        .args(["status", "--porcelain", "-b"])
        .current_dir(&repo_root)
        .output()
    {
        Ok(output) if output.status.success() => {
            let stdout = String::from_utf8_lossy(&output.stdout);
            parse_git_status_porcelain(&stdout, &mut snapshot);
        }
        Ok(output) => {
            snapshot.has_error = true;
            snapshot.error_message = String::from_utf8_lossy(&output.stderr).trim().to_string();
        }
        Err(err) => {
            snapshot.has_error = true;
            snapshot.error_message = format!("git status failed: {err}");
        }
    }

    // `git log --oneline -5` for last commit + recent commits.
    if !snapshot.has_error {
        match std::process::Command::new("git")
            .args(["log", "--oneline", "-5"])
            .current_dir(&repo_root)
            .output()
        {
            Ok(output) if output.status.success() => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let commits: Vec<String> = stdout
                    .lines()
                    .filter(|l| !l.is_empty())
                    .map(std::string::ToString::to_string)
                    .collect();
                if let Some(first) = commits.first() {
                    snapshot.last_commit = first.clone();
                }
                snapshot.recent_commits = commits;
            }
            _ => {} // Non-critical; leave commits empty.
        }
    }

    // `git diff --stat HEAD` summary for staged + unstaged changes.
    if !snapshot.has_error && snapshot.dirty_count > 0 {
        match std::process::Command::new("git")
            .args(["diff", "--stat", "HEAD"])
            .current_dir(&repo_root)
            .output()
        {
            Ok(output) if output.status.success() => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                // The last line of `git diff --stat` is the summary.
                if let Some(summary) = stdout.lines().last() {
                    let trimmed = summary.trim();
                    if !trimmed.is_empty() {
                        snapshot.diff_stat = trimmed.to_string();
                    }
                }
            }
            _ => {} // Non-critical; leave diff_stat empty.
        }
    }

    snapshot
}

/// Find the git repository root that contains the live PTY cwd or launch path.
fn find_git_root(start_dir: Option<&Path>, fallback_dir: &Path) -> Option<PathBuf> {
    if let Some(root) = start_dir.and_then(find_git_root_from_dir) {
        return Some(root);
    }
    find_git_root_from_dir(fallback_dir)
}

fn find_git_root_from_dir(start_dir: &Path) -> Option<PathBuf> {
    let output = std::process::Command::new("git")
        .args(["rev-parse", "--show-toplevel"])
        .current_dir(start_dir)
        .output()
        .ok()?;
    if !output.status.success() {
        return None;
    }
    let root = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if root.is_empty() {
        None
    } else {
        Some(PathBuf::from(root))
    }
}

pub(in super::super) fn resolve_session_working_dir(child_pid: i32) -> Option<PathBuf> {
    if child_pid <= 0 {
        return None;
    }

    // Prefer procfs when it exists so Linux and procfs-enabled hosts avoid the
    // extra `lsof` subprocess. macOS falls back to `lsof` because it does not
    // expose a stable `/proc/<pid>/cwd` path.
    resolve_procfs_working_dir(child_pid).or_else(|| resolve_lsof_working_dir(child_pid))
}

fn resolve_procfs_working_dir(child_pid: i32) -> Option<PathBuf> {
    std::fs::read_link(format!("/proc/{child_pid}/cwd")).ok()
}

fn resolve_lsof_working_dir(child_pid: i32) -> Option<PathBuf> {
    let output = std::process::Command::new("lsof")
        .args(["-n", "-w", "-F", "pfn0", "-a", "-d", "cwd", "-p"])
        .arg(child_pid.to_string())
        .output()
        .ok()?;
    if !matches!(output.status.code(), Some(0) | Some(1)) {
        return None;
    }

    parse_lsof_cwd_output(&String::from_utf8_lossy(&output.stdout))
}

fn parse_lsof_cwd_output(output: &str) -> Option<PathBuf> {
    let mut current_fd: Option<&str> = None;
    for token in output.split('\0') {
        if token.is_empty() {
            continue;
        }
        let cleaned = token.trim_start_matches('\n');
        if cleaned.is_empty() {
            continue;
        }
        let (tag, value) = cleaned.split_at(1);
        match tag {
            "p" => current_fd = None,
            "f" => current_fd = Some(value),
            "n" if current_fd == Some("cwd") && !value.is_empty() => {
                return Some(PathBuf::from(value));
            }
            _ => {}
        }
    }
    None
}

/// Parse the output of `git status --porcelain -b` into snapshot fields.
/// First line: `## branch...upstream [ahead N, behind M]` (or just `## branch`).
/// Remaining lines: one per dirty/untracked file.
fn parse_git_status_porcelain(output: &str, snapshot: &mut crate::dev_command::GitStatusSnapshot) {
    let mut lines = output.lines();

    // First line is the branch/tracking header.
    if let Some(header) = lines.next() {
        let header = header.strip_prefix("## ").unwrap_or(header);

        // Parse ahead/behind from `[ahead N, behind M]` or `[ahead N]` etc.
        if let Some(bracket_start) = header.find('[') {
            let bracket_content = &header[bracket_start..];
            if let Some(ahead_pos) = bracket_content.find("ahead ") {
                let after = &bracket_content[ahead_pos + 6..];
                snapshot.ahead = after
                    .split(|c: char| !c.is_ascii_digit())
                    .next()
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(0);
            }
            if let Some(behind_pos) = bracket_content.find("behind ") {
                let after = &bracket_content[behind_pos + 7..];
                snapshot.behind = after
                    .split(|c: char| !c.is_ascii_digit())
                    .next()
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(0);
            }
        }

        // Branch name: everything before `...` or `[` or end of string.
        let branch_part = if let Some(dots) = header.find("...") {
            &header[..dots]
        } else if let Some(bracket) = header.find('[') {
            header[..bracket].trim()
        } else {
            header.trim()
        };
        snapshot.branch = branch_part.to_string();
    }

    // Remaining lines: dirty or untracked files.
    // Collect up to 8 changed file entries for display.
    const MAX_CHANGED_FILES: usize = 8;
    for line in lines {
        if line.is_empty() {
            continue;
        }
        if line.starts_with("?? ") {
            snapshot.untracked_count += 1;
        } else {
            snapshot.dirty_count += 1;
        }
        if snapshot.changed_files.len() < MAX_CHANGED_FILES {
            snapshot.changed_files.push(line.to_string());
        }
    }
}

#[cfg(test)]
mod git_status_tests {
    use super::*;
    use std::fs;
    use std::path::PathBuf;

    fn unique_temp_dir(prefix: &str) -> PathBuf {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos();
        std::env::temp_dir().join(format!("voiceterm-{prefix}-{now}"))
    }

    #[test]
    fn parse_porcelain_branch_with_tracking() {
        let output = "## develop...origin/develop [ahead 3, behind 1]\n\
                       M  src/main.rs\n\
                       ?? new_file.txt\n";
        let mut snap = crate::dev_command::GitStatusSnapshot::default();
        parse_git_status_porcelain(output, &mut snap);
        assert_eq!(snap.branch, "develop");
        assert_eq!(snap.ahead, 3);
        assert_eq!(snap.behind, 1);
        assert_eq!(snap.dirty_count, 1);
        assert_eq!(snap.untracked_count, 1);
        assert_eq!(snap.changed_files.len(), 2, "collects changed file entries");
        assert!(
            snap.changed_files[0].contains("main.rs"),
            "first entry is the modified file"
        );
        assert!(
            snap.changed_files[1].starts_with("??"),
            "second entry is untracked"
        );
    }

    #[test]
    fn parse_porcelain_no_upstream() {
        let output = "## feature-branch\n\
                       M  file_a.rs\n\
                       M  file_b.rs\n";
        let mut snap = crate::dev_command::GitStatusSnapshot::default();
        parse_git_status_porcelain(output, &mut snap);
        assert_eq!(snap.branch, "feature-branch");
        assert_eq!(snap.ahead, 0);
        assert_eq!(snap.behind, 0);
        assert_eq!(snap.dirty_count, 2);
        assert_eq!(snap.untracked_count, 0);
    }

    #[test]
    fn parse_porcelain_clean_repo() {
        let output = "## main...origin/main\n";
        let mut snap = crate::dev_command::GitStatusSnapshot::default();
        parse_git_status_porcelain(output, &mut snap);
        assert_eq!(snap.branch, "main");
        assert_eq!(snap.dirty_count, 0);
        assert_eq!(snap.untracked_count, 0);
    }

    #[test]
    fn parse_porcelain_ahead_only() {
        let output = "## develop...origin/develop [ahead 7]\n";
        let mut snap = crate::dev_command::GitStatusSnapshot::default();
        parse_git_status_porcelain(output, &mut snap);
        assert_eq!(snap.ahead, 7);
        assert_eq!(snap.behind, 0);
    }

    #[test]
    fn parse_porcelain_caps_changed_files_at_eight() {
        let mut output = "## main...origin/main\n".to_string();
        for i in 0..12 {
            output.push_str(&format!(" M file_{i}.rs\n"));
        }
        let mut snap = crate::dev_command::GitStatusSnapshot::default();
        parse_git_status_porcelain(&output, &mut snap);
        assert_eq!(snap.dirty_count, 12, "counts all dirty files");
        assert_eq!(snap.changed_files.len(), 8, "caps changed_files at 8");
    }

    #[test]
    fn capture_git_status_runs_in_repo() {
        // This test runs in the actual repo, so it should succeed.
        let snap = capture_git_status(Some(Path::new(".")), Path::new("."));
        assert!(!snap.has_error, "should succeed in a real git repo");
        assert!(!snap.branch.is_empty(), "should have a branch name");
        // In this repo, recent commits should be populated.
        assert!(
            !snap.recent_commits.is_empty(),
            "should have recent commits"
        );
    }

    #[test]
    fn find_git_root_uses_requested_start_dir() {
        let outside = unique_temp_dir("git-root-outside");
        let repo_root = unique_temp_dir("git-root-inside");
        let nested = repo_root.join("nested");
        fs::create_dir_all(&outside).expect("create outside dir");
        fs::create_dir_all(&nested).expect("create nested dir");

        let init = std::process::Command::new("git")
            .args(["init", "-q"])
            .current_dir(&repo_root)
            .output()
            .expect("git init runs");
        assert!(init.status.success(), "git init should succeed");

        let resolved = find_git_root(Some(&nested), &outside).expect("git root should resolve");
        assert_eq!(
            resolved.canonicalize().expect("canonical resolved path"),
            repo_root.canonicalize().expect("canonical repo root"),
        );
        assert_eq!(find_git_root(Some(&outside), &outside), None);

        let _ = fs::remove_dir_all(outside);
        let _ = fs::remove_dir_all(repo_root);
    }

    #[test]
    fn parse_lsof_cwd_output_extracts_cwd_entry() {
        let output = "p330\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice/subdir\0";
        assert_eq!(
            parse_lsof_cwd_output(output),
            Some(PathBuf::from(
                "/Users/jguida941/testing_upgrade/codex-voice/subdir"
            ))
        );
    }

    #[test]
    fn parse_lsof_cwd_output_ignores_non_cwd_entries() {
        let output = "p330\0f3\0n/tmp/other\0";
        assert_eq!(parse_lsof_cwd_output(output), None);
    }
}
