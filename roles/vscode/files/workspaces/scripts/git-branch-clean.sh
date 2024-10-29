#!/usr/bin/env bash
# set -eu

working_dir="$(cd $(dirname $0);pwd)"
list=($(find $working_dir -mindepth 1 -maxdepth 1 -type d))

for i in "${!list[@]}"
do
  echo "$i => ${list[$i]}"
  cd ${list[$i]}
  git switch $(git symbolic-ref refs/remotes/origin/HEAD | cut -f4 -d'/')
  # git branch | grep -v "main\|master\|develop" | xargs git branch -D
  git pull origin
done
