# git-branch-clean.sh Ignore Patterns Design

## Overview

`git-branch-clean.sh` に特定の org・repo をスキップする仕組みを追加する。スキップ対象はスクリプトと同じディレクトリに置く `.git-branch-clean-ignore` ファイルで管理する。

## Ignore File Specification

**配置場所:** スクリプトと同じディレクトリ（`working_dir/.git-branch-clean-ignore`）

**フォーマット:**
- 1行1パターン
- `#` で始まる行はコメント、空行は無視
- パターンは `working_dir` からの相対パスで bash glob マッチング
- ファイルが存在しない場合は何もスキップしない

**例:**
```
# 特定リポジトリをスキップ
CARSENSOR/nova_cloud

# org 配下をすべてスキップ
car-dev-devinpoc/*

# 名前パターンでスキップ
*/carsensor_*
```

## Ansible Deployment

`roles/scripts/files/.git-branch-clean-ignore` に空ファイルを追加し、Ansible タスクで配置する。**既存ファイルは上書きしない（`force: no`）**。

```yaml
- name: Copy scripts files
  ansible.builtin.copy:
    src: "{{ item }}"
    dest: "{{ workspace_location }}/{{ item }}"
    force: no
  with_items:
    - git-branch-clean.sh
    - .git-branch-clean-ignore
```

## Script Changes

### Pattern Loading（起動時）

```bash
ignore_patterns=()
if [ -f "$working_dir/.git-branch-clean-ignore" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" =~ ^# ]] && continue
    ignore_patterns+=("$line")
  done < "$working_dir/.git-branch-clean-ignore"
fi
```

### is_ignored Function

```bash
is_ignored() {
  local relpath="${1#"$working_dir/"}"
  local pattern
  for pattern in "${ignore_patterns[@]}"; do
    [[ "$relpath" == $pattern ]] && return 0
  done
  return 1
}
```

### process_repos（変更箇所のみ）

```bash
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
```

## Changes Summary

| ファイル | 変更内容 |
|---|---|
| `roles/scripts/files/git-branch-clean.sh` | `ignore_patterns` 読み込み・`is_ignored()`・`process_repos` に判定追加 |
| `roles/scripts/files/.git-branch-clean-ignore` | 空ファイルを新規作成 |
| `roles/scripts/tasks/main.yaml` | `.git-branch-clean-ignore` のコピータスク追加（`force: no`）|
