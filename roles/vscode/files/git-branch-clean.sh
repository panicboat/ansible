#!/usr/bin/env bash
# set -eu

working_dir="$(cd $(dirname $0);pwd)"
list=($(find $working_dir -mindepth 1 -maxdepth 1 -type d))

for i in "${!list[@]}"
do
  echo "$i => ${list[$i]}"
  cd ${list[$i]}
  git checkout -f $(git symbolic-ref refs/remotes/origin/HEAD | cut -f4 -d'/')
  git clean -fd
  git branch | grep -v "main\|master\|develop\|*" | xargs git branch -D
  git worktree list --porcelain | awk '/^worktree /{print $2}' | grep -v "^${list[$i]}$" | xargs -I{} git worktree remove --force {}
  git worktree prune
  git pull origin
done
