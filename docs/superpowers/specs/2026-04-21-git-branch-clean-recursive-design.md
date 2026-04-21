# git-branch-clean.sh Recursive Repository Discovery

## Overview

`git-branch-clean.sh` を改修し、直下のサブディレクトリのみを対象としていた探索を、再帰的な git リポジトリ検出に変更する。

## Interface

```bash
./git-branch-clean.sh [--max-depth N]
```

- `--max-depth N`: 探索の最大深さ（デフォルト: 2）
- 引数なしで実行した場合は `--max-depth 2` と同等

## Architecture

### 関数構成

```
git-branch-clean.sh
├── 引数パース
│   └── --max-depth（デフォルト 2）
├── clean_repo(dir)
│   └── 既存の処理ロジック（stale lock 削除、branch cleanup、pull）
├── process_repos(dir, remaining_depth)
│   ├── $dir/.git が存在する → clean_repo "$dir" して return
│   ├── remaining_depth <= 0 → return
│   └── $dir 直下の各サブディレクトリで process_repos 再帰
└── process_repos "$working_dir" "$max_depth"
```

### 探索ルール

- `$dir/.git` が存在する → そのディレクトリを git リポジトリとして処理し、内部の探索は行わない
- `.git` が存在しない かつ `remaining_depth > 0` → サブディレクトリを探索
- `remaining_depth == 0` に達した場合は探索を打ち切る

## clean_repo Processing Steps

既存ロジックを維持する。

1. `.git/index.lock` が存在すれば削除（stale lock の除去）
2. `origin/HEAD` から default branch を取得（取得できなければスキップ）
3. `git checkout -f <default_branch>` → `git clean -fd`
4. main worktree 以外をすべて `git worktree remove --force` → `git worktree prune`
5. default branch 以外のローカルブランチを `git branch -D` で削除
6. `git pull origin <default_branch>`

## Changes

| 項目 | 変更前 | 変更後 |
|---|---|---|
| 探索範囲 | `find -mindepth 1 -maxdepth 1`（直下のみ）| 再帰関数で任意深さまで探索 |
| 深さ制御 | なし | `--max-depth N`（デフォルト 2）|
| スクリプト配置ディレクトリ自身 | スキップ | `.git` があれば処理対象 |
| ネストした git repo | 非対応 | 発見したら処理して内部は探索しない |
