# Ghostty + tmux Introduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** iTerm2 を Ghostty に置き換え、tmux を新規導入する。Ansible playbook でパッケージ導入と iTerm2 削除を行い、dotfiles リポジトリで設定ファイルを管理する。

**Architecture:** ansible リポジトリを先行で更新・playbook 実行し、Ghostty/tmux のデフォルト動作を確認してから dotfiles リポジトリで設定ファイルを追加する 2 段ロールアウト。設定ファイルの不備でターミナルが起動不能になるリスクを避ける。

**Tech Stack:** Ansible (community.general.homebrew, community.general.homebrew_cask), Ghostty, tmux, geerlingguy.dotfiles

**Spec:** `docs/superpowers/specs/2026-04-26-ghostty-tmux-design.md`

**Working directories:**
- ansible: `/Users/takanokenichi/GitHub/panicboat/ansible/.claude/worktrees/add-ghostty-tmux`
- dotfiles: `/Users/takanokenichi/GitHub/panicboat/dotfiles`（Phase 2 開始時にブランチ戦略を確認）

---

## Phase 1: Ansible リポジトリ更新

### Task 1: Ansible roles に tmux 追加・iTerm2 を Ghostty に置き換え

**Files:**
- Modify: `roles/homebrew/tasks/main.yaml`
- Modify: `roles/homebrew_cask/tasks/main.yaml`

- [ ] **Step 1: tmux を homebrew formula リストに追加する**

`roles/homebrew/tasks/main.yaml` の `name:` リストで `tfenv` の直後に `tmux` を追加する。具体的には現在の 49 行目 `      - tfenv` の次に新しい行を入れる:

```yaml
      - tfenv
      - tmux
      - trash-cli
```

- [ ] **Step 2: Ghostty を追加し iTerm2 を cask リストから削除する**

`roles/homebrew_cask/tasks/main.yaml` の `name:` リストから `      - iterm2` の行を削除し、アルファベット順で `github` の直前に `      - ghostty` を追加する。結果として該当ブロックは以下になる:

```yaml
- name: install homebrew cask packages
  community.general.homebrew_cask:
    name:
      - 1password
      - cheatsheet
      - claude
      - claude-code
      - clipy
      # - codex
      - ghostty
      - github
      - google-chrome
      - google-cloud-sdk
      # - logi-options+
      - raycast
      - slack
      - visual-studio-code
```

- [ ] **Step 3: iTerm2 アンインストールタスクをファイル末尾に追加する**

`roles/homebrew_cask/tasks/main.yaml` の末尾に以下のタスクを追加する:

```yaml

- name: uninstall iterm2
  community.general.homebrew_cask:
    name: iterm2
    state: absent
  ignore_errors: true
```

- [ ] **Step 4: Ansible 構文チェックを実行する**

worktree 直下で実行する。`hosts: localhost` の playbook なので `-i inventory.ini` は不要:

```bash
cd /Users/takanokenichi/GitHub/panicboat/ansible/.claude/worktrees/add-ghostty-tmux
ansible-playbook playbook.yaml --syntax-check
```

期待結果: `playbook: playbook.yaml` と表示される（inventory 未指定の WARNING は出るが問題なし）。

注: 実際の playbook 実行は Task 3 で本体ディレクトリ (`/Users/takanokenichi/GitHub/panicboat/ansible/`) の既存 `inventory.ini` を使って行う。worktree 内に `inventory.ini` を作る必要は無い。

- [ ] **Step 5: コミットする**

```bash
cd /Users/takanokenichi/GitHub/panicboat/ansible/.claude/worktrees/add-ghostty-tmux
git add roles/homebrew/tasks/main.yaml roles/homebrew_cask/tasks/main.yaml
git commit -s -m "Add tmux and ghostty, remove iterm2"
```

---

### Task 2: worktree で playbook を実行してローカル動作確認する

**Files:**（変更なし。ローカル環境への作用のみ）

- [ ] **Step 1: worktree から playbook を実行する**

`inventory.ini` は本体の既存ファイルを絶対パスで参照する:

```bash
cd /Users/takanokenichi/GitHub/panicboat/ansible/.claude/worktrees/add-ghostty-tmux
ansible-playbook -i /Users/takanokenichi/GitHub/panicboat/ansible/inventory.ini playbook.yaml
```

期待結果: エラーなく完了する。`homebrew` ロールで `tmux` がインストール、`homebrew_cask` ロールで `ghostty` がインストールされ、`iterm2` がアンインストールされる。

- [ ] **Step 2: パッケージ導入を確認する**

```bash
tmux -V
ls -d /Applications/Ghostty.app 2>&1 && echo "Ghostty installed (OK)"
ls /Applications/iTerm.app 2>&1 || echo "iTerm.app removed (OK)"
```

期待結果:
- `tmux 3.x` 系のバージョン表示
- `/Applications/Ghostty.app` のパス表示と `Ghostty installed (OK)`（Ghostty は GUI アプリ cask なので `which ghostty` ではなく `/Applications/Ghostty.app` の存在で確認する）
- `iTerm.app removed (OK)` または `No such file or directory`

- [ ] **Step 3: Ghostty/tmux をデフォルト設定で起動確認する**

Launchpad / Spotlight から Ghostty を起動。デフォルトの色・フォントで zsh + starship が表示されること。Ghostty 内で `tmux` を起動してプロンプトが出ることを確認。

ここまでで Phase 1 のローカル動作は完了。Ghostty/tmux はインストール済み・設定なしの状態。

---

### Task 3: ブランチを push して PR を作成する（またはマージする）

**Files:**（変更なし）

- [ ] **Step 1: ブランチを push する**

```bash
cd /Users/takanokenichi/GitHub/panicboat/ansible/.claude/worktrees/add-ghostty-tmux
git push -u origin HEAD
```

期待結果: `branch 'add-ghostty-tmux' set up to track 'origin/add-ghostty-tmux'.`

- [ ] **Step 2: PR を Draft で作成する**

```bash
gh pr create --draft --title "Add tmux and ghostty, remove iterm2" --body "$(cat <<'EOF'
## Summary

- Homebrew formula に `tmux` を追加
- Homebrew Cask から `iterm2` を削除し `ghostty` を追加
- iTerm2 を `state: absent` でアンインストールするタスクを追加

ローカルで `ansible-playbook` を実行してパッケージ導入を確認済み。設定ファイルは別途 dotfiles リポジトリで追加する（design spec の Rollout Order に従う）。

## Spec

`docs/superpowers/specs/2026-04-26-ghostty-tmux-design.md`

## Test plan

- [x] `ansible-playbook -i inventory.ini playbook.yaml` をローカル実行
- [x] `tmux -V` で tmux が利用可能
- [x] `which ghostty` で Ghostty が利用可能
- [x] `/Applications/iTerm.app` が削除されている
- [x] Ghostty を起動してデフォルト設定で動作する
EOF
)"
```

- [ ] **Step 3: PR URL を確認してユーザーに報告する**

`gh pr create` の出力に表示される PR URL をユーザーに伝える。マージは Phase 2 の作業と並行して任意のタイミングで実行可能。

---

## Phase 2: dotfiles リポジトリで設定ファイルを追加

### Task 4: dotfiles リポジトリのブランチ戦略を確認する

**Files:**（変更なし）

- [ ] **Step 1: ユーザーに 4 択を提示する**

dotfiles リポジトリ (`/Users/takanokenichi/GitHub/panicboat/dotfiles`) で以下のどれで進めるかをユーザーに確認:

1. worktree を使って進める (`.claude/worktrees/<branch>`)
2. worktree を使わず新規ブランチを作成して進める
3. このブランチ（`<現在のブランチ名>` を確認して提示）で進める
4. 任意入力

選択結果に応じて作業ディレクトリを決定する。以降の Task では `<DOTFILES_WORKDIR>` をその作業ディレクトリの絶対パスとして扱う。

参考: `/Users/takanokenichi/.claude/CLAUDE.md` の Workflow セクションのルールに従う。

---

### Task 5: tmux 設定ファイル `.tmux.conf` を作成する

**Files:**
- Create: `<DOTFILES_WORKDIR>/.tmux.conf`

- [ ] **Step 1: `.tmux.conf` を作成する**

`<DOTFILES_WORKDIR>/.tmux.conf` を以下の内容で作成する:

```tmux
# Terminal
set -g default-terminal "tmux-256color"
set -ga terminal-overrides ",*256col*:Tc"

# Mouse
set -g mouse on

# Pane split (current path inherited)
unbind '"'
unbind %
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# Vim-style pane navigation
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Reload config
bind r source-file ~/.tmux.conf \; display-message "tmux.conf reloaded"

# Status line
set -g status-style "bg=default"
set -g status-left "[#S] "
set -g status-right "%Y-%m-%d %H:%M "
set -g status-left-length 30
```

---

### Task 6: Ghostty 設定ファイル `.config/ghostty/config` を作成する

**Files:**
- Create: `<DOTFILES_WORKDIR>/.config/ghostty/config`

- [ ] **Step 1: `.config/ghostty/config` を作成する**

ディレクトリは既に存在する想定（dotfiles リポジトリに `.config/ghostty/` が空ディレクトリで commit 済み）。万一存在しなければ作る:

```bash
mkdir -p <DOTFILES_WORKDIR>/.config/ghostty
```

`<DOTFILES_WORKDIR>/.config/ghostty/config` を以下の内容で作成する:

```ini
theme = Dracula
font-family = SF Mono
font-size = 14
window-padding-x = 8
window-padding-y = 8
shell-integration = zsh
macos-option-as-alt = true
```

---

### Task 7: 手動シンボリックリンクで動作確認する

**Files:**（commit せず、ホームディレクトリに一時的にシンボリックリンク）

- [ ] **Step 1: ホームディレクトリにシンボリックリンクを張る**

```bash
ln -sfn <DOTFILES_WORKDIR>/.tmux.conf ~/.tmux.conf
mkdir -p ~/.config/ghostty
ln -sfn <DOTFILES_WORKDIR>/.config/ghostty/config ~/.config/ghostty/config
```

注: `~/.config/ghostty/` 自体が dotfiles リポジトリのシンボリックリンクとして存在する場合は、内側のファイル個別ではなくディレクトリ全体がリンクされている可能性がある。`ls -la ~/.config/ghostty` で確認:
- `~/.config/ghostty` が dotfiles リポジトリへのシンボリックリンク → `~/.config/ghostty/config` は自動的に新規ファイルが見える状態。`ln` 不要。
- `~/.config/ghostty` が通常ディレクトリ → 上記 `ln -sfn` を使う。

- [ ] **Step 2: Ghostty を起動して設定を確認する**

Ghostty を再起動（既に起動中なら quit してから launchpad で起動）。確認項目:
- 背景色が Dracula の `#282a36` になる
- フォントが SF Mono で表示される
- ウィンドウ周囲に余白がある
- Option キーが Alt として効く（`Option+B` で word jump 等）

- [ ] **Step 3: tmux を起動して設定を確認する**

Ghostty 内で `tmux` を起動。確認項目:
- ステータスバーが下部に表示され、左にセッション名 `[0]` 等、右に日時
- マウスクリックでペイン選択ができる
- `Ctrl+B` の後に `|` でペイン縦分割、`-` で横分割
- 分割後に `Ctrl+B h/j/k/l` でペイン移動
- `Ctrl+B r` で `tmux.conf reloaded` と表示される
- tmux 内で starship プロンプトが Dracula の色で表示される

- [ ] **Step 4: 不具合があれば Task 5/6 に戻って修正する**

設定の不備で起動失敗等があれば、ファイルを編集して Step 2/3 を再確認する。シンボリックリンクは編集と同時に反映される。

---

### Task 8: dotfiles を commit して push する

**Files:**
- Commit: `<DOTFILES_WORKDIR>/.tmux.conf`
- Commit: `<DOTFILES_WORKDIR>/.config/ghostty/config`

- [ ] **Step 1: 変更を確認する**

```bash
cd <DOTFILES_WORKDIR>
git status
```

期待結果: `.tmux.conf` と `.config/ghostty/config` が新規ファイルとして表示される。

- [ ] **Step 2: コミットする**

```bash
cd <DOTFILES_WORKDIR>
git add .tmux.conf .config/ghostty/config
git commit -s -m "Add tmux and ghostty configs"
```

- [ ] **Step 3: push する（ブランチ戦略に応じて）**

Task 4 で選んだブランチ戦略に応じて:

- 新規ブランチ / worktree の場合:
  ```bash
  git push -u origin HEAD
  gh pr create --draft --title "Add tmux and ghostty configs" --body "$(cat <<'EOF'
  ## Summary

  - `.tmux.conf` を新規作成（mouse、ペイン分割、vim 風移動、reload キー）
  - `.config/ghostty/config` を新規作成（Dracula テーマ、SF Mono、shell integration）

  ansible 側の PR (`Add tmux and ghostty, remove iterm2`) のフォローアップ。

  ## Test plan

  - [x] 手動シンボリックリンクで Ghostty が Dracula で起動
  - [x] tmux 設定が反映される（mouse、キーバインド、status line）
  - [ ] PR マージ後、別端末で `ansible-playbook` 再実行して冪等性確認
  EOF
  )"
  ```

- main で進めている場合:
  ```bash
  git push origin main
  ```

---

### Task 9: ansible-playbook 再実行で冪等性を確認する

**Files:**（変更なし。ホームディレクトリの状態確認のみ）

- [ ] **Step 1: dotfiles の PR をマージする（PR 運用の場合）**

PR を Ready for review に変更してマージする。

- [ ] **Step 2: ansible-playbook を再実行する**

```bash
cd /Users/takanokenichi/GitHub/panicboat/ansible
ansible-playbook -i inventory.ini playbook.yaml
```

期待結果: エラーなく完了する。geerlingguy.dotfiles ロールが `~/.tmux.conf` と `~/.config/ghostty/config` のシンボリックリンクを管理下に置く。

- [ ] **Step 3: シンボリックリンクが正しい状態であることを確認する**

```bash
ls -la ~/.tmux.conf
ls -la ~/.config/ghostty/config
```

期待結果: いずれも `/Users/takanokenichi/GitHub/panicboat/dotfiles/...` を指すシンボリックリンクとして表示される。

- [ ] **Step 4: Ghostty/tmux を再起動して最終動作確認する**

Ghostty を quit → 再起動。tmux を起動して、Phase 2 Task 7 の確認項目すべてが満たされていること。

- [ ] **Step 5: ansible 側 worktree のクリーンアップ**

PR マージ済みなら worktree を削除する:

```bash
cd /Users/takanokenichi/GitHub/panicboat/ansible
git worktree remove .claude/worktrees/add-ghostty-tmux
git worktree prune
```

dotfiles 側で worktree を作っていれば同様にクリーンアップする。
