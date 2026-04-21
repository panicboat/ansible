#!/usr/bin/env bash
set -eu

max_depth=2
while [[ $# -gt 0 ]]; do
  case "$1" in
    --max-depth)
      max_depth="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

working_dir="$(cd "$(dirname "$0")"; pwd)"

ignore_patterns=()
if [ -f "$working_dir/.git-branch-clean-ignore" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" =~ ^# ]] && continue
    ignore_patterns+=("$line")
  done < "$working_dir/.git-branch-clean-ignore"
fi

is_ignored() {
  local relpath="${1#"$working_dir/"}"
  local pattern
  for pattern in "${ignore_patterns[@]+"${ignore_patterns[@]}"}"; do
    [[ "$relpath" == $pattern ]] && return 0
  done
  return 1
}

clean_repo() {
  local dir="$1"
  echo "$dir"

  local lock_file="$dir/.git/index.lock"
  if [ -f "$lock_file" ]; then
    echo "Removing stale lock: $lock_file"
    rm -f "$lock_file"
  fi

  cd "$dir"

  local default_branch
  default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | cut -f4 -d'/')
  if [ -z "$default_branch" ]; then
    echo "Skipping: cannot determine default branch"
    return
  fi

  git checkout -f "$default_branch"
  git clean -fd
  git worktree list --porcelain | grep "^worktree " | awk 'NR>1{print $2}' | while IFS= read -r wt_path; do
    echo "Removing worktree: $wt_path"
    git worktree remove --force "$wt_path" || true
  done
  git worktree prune
  git branch | grep -vE "^\s*[*+]|$default_branch" | xargs git branch -D || true
  if ! git pull origin "$default_branch"; then
    echo "Warning: git pull failed for $dir" >&2
  fi
}

process_repos() {
  local dir="$1"
  local depth="$2"

  if is_ignored "$dir"; then
    echo "Skipping: $dir (ignored)"
    return
  fi

  if [ -d "$dir/.git" ]; then
    clean_repo "$dir" || echo "Warning: failed to clean $dir" >&2
    return
  fi

  [ "$depth" -le 0 ] && return

  for subdir in "$dir"/*/; do
    if [ -d "$subdir" ]; then
      process_repos "${subdir%/}" "$((depth - 1))"
    fi
  done
}

process_repos "$working_dir" "$max_depth"
