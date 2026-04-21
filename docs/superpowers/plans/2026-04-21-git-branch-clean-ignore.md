# git-branch-clean.sh Ignore Patterns Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `git-branch-clean.sh` に `.git-branch-clean-ignore` ファイルを読み込んで特定の org/repo をスキップする機能を追加する。

**Architecture:** スクリプト起動時に `working_dir/.git-branch-clean-ignore` を読み込んで `ignore_patterns[]` に格納し、`is_ignored()` 関数で `working_dir` からの相対パスを bash glob マッチングする。`process_repos()` の先頭で判定してスキップ。Ansible タスクで空の `.git-branch-clean-ignore` を `force: no` で配置する。

**Tech Stack:** bash, Ansible

---

### Task 1: ignore 機能のテストスクリプトを書く

**Files:**
- Create: `roles/scripts/files/test-ignore.sh`（検証後削除）

- [ ] **Step 1: テストスクリプトを作成する**

```bash
cat > roles/scripts/files/test-ignore.sh << 'EOF'
#!/usr/bin/env bash
set -eu

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

working_dir="$tmpdir"

# Create ignore file
cat > "$tmpdir/.git-branch-clean-ignore" << 'IGNORE'
# this is a comment

org1/repo-skip
*/repo-glob-*
IGNORE

# Load ignore_patterns (same logic as production)
ignore_patterns=()
while IFS= read -r line || [ -n "$line" ]; do
  [[ "$line" =~ ^[[:space:]]*$ ]] && continue
  [[ "$line" =~ ^# ]] && continue
  ignore_patterns+=("$line")
done < "$working_dir/.git-branch-clean-ignore"

is_ignored() {
  local relpath="${1#"$working_dir/"}"
  local pattern
  for pattern in "${ignore_patterns[@]}"; do
    [[ "$relpath" == $pattern ]] && return 0
  done
  return 1
}

echo "=== is_ignored unit tests ==="

# exact match
if is_ignored "$tmpdir/org1/repo-skip"; then
  echo "PASS: org1/repo-skip is ignored (exact match)"
else
  echo "FAIL: org1/repo-skip should be ignored" && exit 1
fi

# glob match
if is_ignored "$tmpdir/org2/repo-glob-abc"; then
  echo "PASS: org2/repo-glob-abc is ignored (glob match)"
else
  echo "FAIL: org2/repo-glob-abc should be ignored" && exit 1
fi

# non-matching path
if is_ignored "$tmpdir/org1/repo-keep"; then
  echo "FAIL: org1/repo-keep should not be ignored" && exit 1
else
  echo "PASS: org1/repo-keep is not ignored"
fi

# comment lines are not patterns
if is_ignored "$tmpdir/# this is a comment"; then
  echo "FAIL: comment lines should not become patterns" && exit 1
else
  echo "PASS: comment lines are not patterns"
fi

echo ""
echo "=== process_repos integration test ==="

# Stub clean_repo
clean_repo() { echo "processed: ${1#"$tmpdir/"}"; }

process_repos() {
  local dir="$1"
  local depth="$2"
  if is_ignored "$dir"; then
    echo "skipped: ${dir#"$tmpdir/"}"
    return
  fi
  if [ -d "$dir/.git" ]; then
    clean_repo "$dir"
    return
  fi
  [ "$depth" -le 0 ] && return
  for subdir in "$dir"/*/; do
    if [ -d "$subdir" ]; then
      process_repos "${subdir%/}" "$((depth - 1))"
    fi
  done
}

mkdir -p "$tmpdir/org1/repo-skip"    && git -C "$tmpdir/org1/repo-skip"    init -q
mkdir -p "$tmpdir/org1/repo-keep"    && git -C "$tmpdir/org1/repo-keep"    init -q
mkdir -p "$tmpdir/org2/repo-glob-x"  && git -C "$tmpdir/org2/repo-glob-x"  init -q

output=$(process_repos "$tmpdir" 2)
echo "$output"

if echo "$output" | grep -q "skipped:.*org1/repo-skip"; then
  echo "PASS: repo-skip was skipped"
else
  echo "FAIL: repo-skip should be skipped" && exit 1
fi

if echo "$output" | grep -q "processed:.*org1/repo-keep"; then
  echo "PASS: repo-keep was processed"
else
  echo "FAIL: repo-keep should be processed" && exit 1
fi

if echo "$output" | grep -q "skipped:.*org2/repo-glob-x"; then
  echo "PASS: repo-glob-x was skipped (glob)"
else
  echo "FAIL: repo-glob-x should be skipped" && exit 1
fi

echo ""
echo "All tests passed."
EOF
chmod +x roles/scripts/files/test-ignore.sh
```

- [ ] **Step 2: テストを実行して通ることを確認する**

```bash
bash roles/scripts/files/test-ignore.sh
```

期待結果:
```
=== is_ignored unit tests ===
PASS: org1/repo-skip is ignored (exact match)
PASS: org2/repo-glob-abc is ignored (glob match)
PASS: org1/repo-keep is not ignored
PASS: comment lines are not patterns

=== process_repos integration test ===
skipped: org1/repo-skip
processed: org1/repo-keep
skipped: org2/repo-glob-x
PASS: repo-skip was skipped
PASS: repo-keep was processed
PASS: repo-glob-x was skipped (glob)

All tests passed.
```

---

### Task 2: git-branch-clean.sh に ignore 機能を実装する

**Files:**
- Modify: `roles/scripts/files/git-branch-clean.sh`

- [ ] **Step 1: スクリプトを書き換える**

`roles/scripts/files/git-branch-clean.sh` の内容を以下で置き換える:

```bash
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
  for pattern in "${ignore_patterns[@]}"; do
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
```

- [ ] **Step 2: テストを実行して通ることを確認する**

```bash
bash roles/scripts/files/test-ignore.sh
```

期待結果: `All tests passed.` が表示されること

- [ ] **Step 3: テストスクリプトを削除する**

```bash
rm roles/scripts/files/test-ignore.sh
```

- [ ] **Step 4: コミットする**

```bash
git add roles/scripts/files/git-branch-clean.sh
git commit -s -m "Add ignore patterns support to git-branch-clean.sh"
```

---

### Task 3: .git-branch-clean-ignore 空ファイルと Ansible タスクを追加する

**Files:**
- Create: `roles/scripts/files/.git-branch-clean-ignore`
- Modify: `roles/scripts/tasks/main.yaml`

- [ ] **Step 1: 空の ignore ファイルを作成する**

```bash
touch roles/scripts/files/.git-branch-clean-ignore
```

- [ ] **Step 2: Ansible タスクを更新する**

`roles/scripts/tasks/main.yaml` の内容を以下で置き換える:

```yaml
- name: Create vscode directory
  ansible.builtin.file:
    path: "{{ workspace_location }}/{{ item }}"
    state: directory
  with_items:
    - .vscode

- name: Copy scripts files
  ansible.builtin.copy:
    src: "{{ item }}"
    dest: "{{ workspace_location }}/{{ item }}"
    force: no
  with_items:
    - git-branch-clean.sh
    - .git-branch-clean-ignore
```

- [ ] **Step 3: コミットする**

```bash
git add roles/scripts/files/.git-branch-clean-ignore roles/scripts/tasks/main.yaml
git commit -s -m "Add .git-branch-clean-ignore deployment via Ansible"
```
