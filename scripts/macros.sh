#!/bin/bash
#
# VoiceTerm Macro Pack Wizard
# Generates project-local .voiceterm/macros.yaml from starter packs.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK_DIR="$SCRIPT_DIR/macro-packs"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

pack_path_for() {
    case "$1" in
        safe-core) echo "$PACK_DIR/safe-core.yaml" ;;
        power-git) echo "$PACK_DIR/power-git.yaml" ;;
        full-dev) echo "$PACK_DIR/full-dev.yaml" ;;
        *) return 1 ;;
    esac
}

pack_description() {
    case "$1" in
        safe-core) echo "Low-risk daily git/GitHub inspection commands (recommended)" ;;
        power-git) echo "High-impact git/GitHub write actions (insert mode by default)" ;;
        full-dev) echo "Combined safe-core + power-git + codex-voice maintainer workflow" ;;
        *) echo "Unknown" ;;
    esac
}

infer_github_repo() {
    local project_dir="$1"
    local remote_url
    local repo=""

    remote_url="$(git -C "$project_dir" remote get-url origin 2>/dev/null || true)"
    case "$remote_url" in
        git@github.com:*)
            repo="${remote_url#git@github.com:}"
            ;;
        https://github.com/*)
            repo="${remote_url#https://github.com/}"
            ;;
        ssh://git@github.com/*)
            repo="${remote_url#ssh://git@github.com/}"
            ;;
        *)
            repo=""
            ;;
    esac
    repo="${repo%.git}"
    printf "%s" "$repo"
}

infer_github_owner() {
    local repo_slug="$1"
    if [ -z "$repo_slug" ]; then
        printf ""
        return
    fi
    printf "%s" "${repo_slug%%/*}"
}

infer_default_branch() {
    local project_dir="$1"
    local origin_head
    local branch=""

    origin_head="$(git -C "$project_dir" symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null || true)"
    if [ -n "$origin_head" ]; then
        branch="${origin_head#refs/remotes/origin/}"
    fi

    if [ -z "$branch" ] && git -C "$project_dir" show-ref --verify --quiet refs/heads/main; then
        branch="main"
    fi
    if [ -z "$branch" ] && git -C "$project_dir" show-ref --verify --quiet refs/heads/master; then
        branch="master"
    fi
    if [ -z "$branch" ]; then
        branch="$(git -C "$project_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
    fi

    if [ "$branch" = "HEAD" ]; then
        branch=""
    fi

    printf "%s" "$branch"
}

infer_current_branch() {
    local project_dir="$1"
    local branch
    branch="$(git -C "$project_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
    if [ "$branch" = "HEAD" ]; then
        branch=""
    fi
    printf "%s" "$branch"
}

infer_github_user() {
    local fallback="$1"
    local user=""

    if command -v gh >/dev/null 2>&1; then
        user="$(gh api user -q .login 2>/dev/null || true)"
    fi

    if [ -z "$user" ]; then
        user="$fallback"
    fi

    printf "%s" "$user"
}

gh_auth_ready() {
    command -v gh >/dev/null 2>&1 && gh auth status -h github.com >/dev/null 2>&1
}

gh_commands_present() {
    local file_path="$1"
    grep -q 'gh ' "$file_path"
}

validate_gh_context() {
    local file_path="$1"
    local repo_slug="$2"

    if ! gh_commands_present "$file_path"; then
        return 0
    fi

    if ! command -v gh >/dev/null 2>&1; then
        print_warning "GitHub CLI (gh) not found; GitHub macros will fail until installed"
        return 0
    fi

    if ! gh_auth_ready; then
        print_warning "GitHub CLI is not authenticated. Run: gh auth login"
        return 0
    fi

    if [ -n "$repo_slug" ]; then
        if gh repo view "$repo_slug" --json nameWithOwner -q .nameWithOwner >/dev/null 2>&1; then
            print_success "Validated GitHub access via gh for repo: $repo_slug"
        else
            print_warning "GitHub auth is present, but repo validation failed for: $repo_slug"
        fi
    fi
}

sed_escape_replacement() {
    printf "%s" "$1" | sed 's/[&|]/\\&/g'
}

replace_placeholder() {
    local file_path="$1"
    local token="$2"
    local value="$3"

    if ! grep -q "$token" "$file_path"; then
        return 0
    fi

    if [ -z "$value" ]; then
        print_warning "Placeholder $token found but no value was provided"
        return 0
    fi

    local escaped
    escaped="$(sed_escape_replacement "$value")"
    sed "s|$token|$escaped|g" "$file_path" > "${file_path}.rendered"
    mv "${file_path}.rendered" "$file_path"
    return 0
}

render_placeholders() {
    local file_path="$1"
    local repo_slug="$2"
    local owner="$3"
    local default_branch="$4"
    local github_user="$5"
    local current_branch="$6"

    replace_placeholder "$file_path" "__GITHUB_REPO__" "$repo_slug"
    replace_placeholder "$file_path" "__GITHUB_OWNER__" "$owner"
    replace_placeholder "$file_path" "__DEFAULT_BRANCH__" "$default_branch"
    replace_placeholder "$file_path" "__GITHUB_USER__" "$github_user"
    replace_placeholder "$file_path" "__CURRENT_BRANCH__" "$current_branch"
}

validate_macros_file() {
    local file_path="$1"
    local project_dir="$2"
    local ok=1

    if [ ! -f "$file_path" ]; then
        print_error "Macro file not found: $file_path"
        return 1
    fi

    if ! grep -q '^macros:' "$file_path"; then
        print_error "Invalid macro file: missing top-level 'macros:' key"
        ok=0
    fi

    if grep -Eq '__[A-Z0-9_]+__' "$file_path"; then
        print_warning "Unresolved placeholder token found; set values and regenerate"
    fi

    if grep -q 'git ' "$file_path" && ! git -C "$project_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        print_warning "Git macros detected, but project dir is not a git repo: $project_dir"
    fi

    local guessed_repo
    guessed_repo="$(infer_github_repo "$project_dir")"
    validate_gh_context "$file_path" "$guessed_repo"

    if [ "$ok" -eq 1 ]; then
        print_success "Macro file structure check passed"
        return 0
    fi
    return 1
}

install_pack() {
    local pack="$1"
    local project_dir="$2"
    local output_path="$3"
    local repo_slug="$4"
    local owner="$5"
    local default_branch="$6"
    local github_user="$7"
    local current_branch="$8"
    local overwrite="$9"

    local pack_path
    pack_path="$(pack_path_for "$pack")" || {
        print_error "Unknown pack: $pack"
        return 1
    }

    if [ ! -f "$pack_path" ]; then
        print_error "Pack file missing: $pack_path"
        return 1
    fi

    if [ -f "$output_path" ] && [ "$overwrite" != "1" ]; then
        print_error "Macro file already exists: $output_path"
        echo "       Re-run with --overwrite or choose a different --output path"
        return 1
    fi

    mkdir -p "$(dirname "$output_path")"

    local tmp_path="${output_path}.tmp.$$"
    cp "$pack_path" "$tmp_path"

    render_placeholders "$tmp_path" "$repo_slug" "$owner" "$default_branch" "$github_user" "$current_branch"

    mv "$tmp_path" "$output_path"
    print_success "Wrote macro file: $output_path"

    validate_macros_file "$output_path" "$project_dir"
}

prompt_with_default() {
    local prompt="$1"
    local default_value="$2"
    local answer
    if [ -n "$default_value" ]; then
        read -r -p "$prompt [$default_value]: " answer
        if [ -z "$answer" ]; then
            answer="$default_value"
        fi
    else
        read -r -p "$prompt: " answer
    fi
    printf "%s" "$answer"
}

wizard() {
    local preselected_pack="${1:-}"
    echo ""
    echo "VoiceTerm Macro Wizard"
    echo ""

    local project_dir
    project_dir="$(prompt_with_default "Project directory" "$PWD")"
    if [ ! -d "$project_dir" ]; then
        print_error "Directory not found: $project_dir"
        return 1
    fi

    local pack="safe-core"
    if [ -n "$preselected_pack" ]; then
        case "$preselected_pack" in
            safe-core|power-git|full-dev)
                pack="$preselected_pack"
                ;;
            *)
                print_error "Invalid preselected pack: $preselected_pack"
                return 1
                ;;
        esac
        print_step "Using preselected pack '$pack'"
    else
        echo ""
        echo "Choose a macro pack:"
        echo "  1) safe-core (Recommended)"
        echo "  2) power-git"
        echo "  3) full-dev"

        local choice
        choice="$(prompt_with_default "Pack" "1")"
        case "$choice" in
            1|safe-core) pack="safe-core" ;;
            2|power-git) pack="power-git" ;;
            3|full-dev) pack="full-dev" ;;
            *)
                print_error "Invalid pack choice: $choice"
                return 1
                ;;
        esac
    fi

    local default_output="$project_dir/.voiceterm/macros.yaml"
    local output_path
    output_path="$(prompt_with_default "Output file" "$default_output")"

    local pack_path
    pack_path="$(pack_path_for "$pack")"

    local detected_repo detected_owner detected_default_branch detected_github_user detected_current_branch
    detected_repo="$(infer_github_repo "$project_dir")"
    detected_owner="$(infer_github_owner "$detected_repo")"
    detected_default_branch="$(infer_default_branch "$project_dir")"
    detected_github_user="$(infer_github_user "$detected_owner")"
    detected_current_branch="$(infer_current_branch "$project_dir")"

    local repo_slug=""
    local owner=""
    local default_branch=""
    local github_user=""
    local current_branch=""

    if grep -q '__GITHUB_REPO__' "$pack_path"; then
        repo_slug="$(prompt_with_default "GitHub repo slug (owner/name)" "$detected_repo")"
    fi
    if grep -q '__GITHUB_OWNER__' "$pack_path"; then
        owner="$(prompt_with_default "GitHub owner" "$detected_owner")"
    fi
    if grep -q '__DEFAULT_BRANCH__' "$pack_path"; then
        default_branch="$(prompt_with_default "Default branch" "$detected_default_branch")"
    fi
    if grep -q '__GITHUB_USER__' "$pack_path"; then
        github_user="$(prompt_with_default "GitHub user" "$detected_github_user")"
    fi
    if grep -q '__CURRENT_BRANCH__' "$pack_path"; then
        current_branch="$(prompt_with_default "Current branch" "$detected_current_branch")"
    fi

    if [ -z "$owner" ]; then
        owner="$(infer_github_owner "$repo_slug")"
    fi
    if [ -z "$github_user" ]; then
        github_user="$(infer_github_user "$owner")"
    fi

    if gh_commands_present "$pack_path"; then
        if ! command -v gh >/dev/null 2>&1; then
            print_warning "GitHub CLI (gh) not found. Install it to use GitHub macros."
        elif ! gh_auth_ready; then
            if [ -t 0 ] && [ -t 1 ]; then
                local gh_login_answer
                gh_login_answer="$(prompt_with_default "GitHub CLI is not authenticated. Run gh auth login now? (y/N)" "N")"
                case "$gh_login_answer" in
                    y|Y|yes|YES)
                        gh auth login || print_warning "gh auth login did not complete"
                        ;;
                esac
            else
                print_warning "GitHub CLI is not authenticated. Run: gh auth login"
            fi
        fi
    fi

    local overwrite="0"
    if [ -f "$output_path" ]; then
        local overwrite_answer
        overwrite_answer="$(prompt_with_default "File exists. Overwrite? (y/N)" "N")"
        case "$overwrite_answer" in
            y|Y|yes|YES) overwrite="1" ;;
            *)
                print_warning "Canceled (existing file kept)."
                return 0
                ;;
        esac
    fi

    echo ""
    print_step "Installing pack '$pack'"
    install_pack "$pack" "$project_dir" "$output_path" "$repo_slug" "$owner" "$default_branch" "$github_user" "$current_branch" "$overwrite"

    echo ""
    print_success "Wizard complete"
    echo "Next steps:"
    echo "  1) Launch VoiceTerm in this project"
    echo "  2) Open Settings (Ctrl+O) and set Macros = ON"
    echo "  3) Try: 'show git status', 'run ci checks', or 'open pull request fix ci lane'"
}

show_usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  wizard              Interactive setup (default)"
    echo "  install             Non-interactive install"
    echo "  list                List available macro packs"
    echo "  validate            Validate an existing macros file"
    echo ""
    echo "Install options:"
    echo "  --pack <name>         safe-core | power-git | full-dev (default: safe-core)"
    echo "  --project-dir <dir>   Target project directory (default: current directory)"
    echo "  --output <path>       Output macro file path (default: <project>/.voiceterm/macros.yaml)"
    echo "  --repo <owner/name>   Repo slug for __GITHUB_REPO__ (auto-detected if omitted)"
    echo "  --owner <owner>       Owner for __GITHUB_OWNER__ (derived from --repo if omitted)"
    echo "  --default-branch <b>  Branch for __DEFAULT_BRANCH__ (auto-detected if omitted)"
    echo "  --github-user <name>  User for __GITHUB_USER__ (gh api or owner fallback if omitted)"
    echo "  --current-branch <b>  Branch for __CURRENT_BRANCH__ (auto-detected if omitted)"
    echo "  --overwrite           Replace existing output file"
    echo ""
    echo "Examples:"
    echo "  $0"
    echo "  $0 wizard"
    echo "  $0 install --pack safe-core"
    echo "  $0 install --pack full-dev --repo jguida941/codex-voice --overwrite"
    echo "  $0 validate --output ./.voiceterm/macros.yaml"
}

list_packs() {
    echo "Available macro packs:"
    for pack in safe-core power-git full-dev; do
        echo "  - $pack: $(pack_description "$pack")"
    done
}

main() {
    local command="${1:-wizard}"
    if [ $# -gt 0 ]; then
        shift
    fi

    local pack="safe-core"
    local project_dir="$PWD"
    local output_path=""
    local repo_slug=""
    local owner=""
    local default_branch=""
    local github_user=""
    local current_branch=""
    local overwrite="0"

    while [ $# -gt 0 ]; do
        case "$1" in
            --pack)
                pack="${2:-}"
                shift 2
                ;;
            --project-dir)
                project_dir="${2:-}"
                shift 2
                ;;
            --output)
                output_path="${2:-}"
                shift 2
                ;;
            --repo)
                repo_slug="${2:-}"
                shift 2
                ;;
            --owner)
                owner="${2:-}"
                shift 2
                ;;
            --default-branch)
                default_branch="${2:-}"
                shift 2
                ;;
            --github-user)
                github_user="${2:-}"
                shift 2
                ;;
            --current-branch)
                current_branch="${2:-}"
                shift 2
                ;;
            --overwrite)
                overwrite="1"
                shift
                ;;
            -h|--help|help)
                show_usage
                return 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                return 1
                ;;
        esac
    done

    if [ -z "$output_path" ]; then
        output_path="$project_dir/.voiceterm/macros.yaml"
    fi

    if [ -z "$repo_slug" ]; then
        repo_slug="$(infer_github_repo "$project_dir")"
    fi
    if [ -z "$owner" ]; then
        owner="$(infer_github_owner "$repo_slug")"
    fi
    if [ -z "$default_branch" ]; then
        default_branch="$(infer_default_branch "$project_dir")"
    fi
    if [ -z "$github_user" ]; then
        github_user="$(infer_github_user "$owner")"
    fi
    if [ -z "$current_branch" ]; then
        current_branch="$(infer_current_branch "$project_dir")"
    fi

    case "$command" in
        wizard)
            wizard "$pack"
            ;;
        install)
            install_pack "$pack" "$project_dir" "$output_path" "$repo_slug" "$owner" "$default_branch" "$github_user" "$current_branch" "$overwrite"
            ;;
        list)
            list_packs
            ;;
        validate)
            validate_macros_file "$output_path" "$project_dir"
            ;;
        -h|--help|help)
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            return 1
            ;;
    esac
}

main "$@"
