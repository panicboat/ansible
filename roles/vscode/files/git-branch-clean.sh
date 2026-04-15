#!/usr/bin/env bash
set -eu

working_dir="$(cd "$(dirname "$0")"; pwd)"
list=($(find "$working_dir" -mindepth 1 -maxdepth 1 -type d))

for i in "${!list[@]}"
do
  dir="${list[$i]}"
  echo "$i => $dir"

  if [ ! -d "$dir/.git" ]; then
    echo "Skipping: not a git repository"
    continue
  fi

  lock_file="$dir/.git/index.lock"
  if [ -f "$lock_file" ]; then
    echo "Removing stale lock: $lock_file"
    rm -f "$lock_file"
  fi

  cd "$dir"

  default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | cut -f4 -d'/')
  if [ -z "$default_branch" ]; then
    echo "Skipping: cannot determine default branch"
    continue
  fi

  git checkout -f "$default_branch"
  git clean -fd
  git worktree list --porcelain | grep "^worktree " | awk 'NR>1{print $2}' | while IFS= read -r wt_path; do
    echo "Removing worktree: $wt_path"
    git worktree remove --force "$wt_path" || true
  done
  git worktree prune
  git branch | grep -vE "^\s*[*+]|$default_branch" | xargs git branch -D || true
  git pull origin "$default_branch"
done
