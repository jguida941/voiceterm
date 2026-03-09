use std::path::{Path, PathBuf};

pub(crate) fn find_devctl_root(working_dir: &Path) -> PathBuf {
    for ancestor in working_dir.ancestors() {
        if devctl_script_path(ancestor).is_file() {
            return ancestor.to_path_buf();
        }
    }
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let repo_root = manifest_dir.parent().unwrap_or(manifest_dir);
    if devctl_script_path(repo_root).is_file() {
        return repo_root.to_path_buf();
    }
    working_dir.to_path_buf()
}

pub(crate) fn devctl_script_path(repo_root: &Path) -> PathBuf {
    repo_root.join("dev").join("scripts").join("devctl.py")
}
