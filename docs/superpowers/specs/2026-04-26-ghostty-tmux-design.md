# Ghostty + tmux Introduction Design

## Overview

iTerm2 を Ghostty に置き換え、tmux を新規導入する。Ansible playbook 実行のみでパッケージ導入と iTerm2 削除が完結し、設定ファイルは別途 dotfiles リポジトリで管理する。

## Rollout Order

設定ファイル不備によるターミナル起動不能リスクを避けるため、ansible 側を先行で完成させ、設定ファイルは後追いで dotfiles に追加する。

1. **ansible リポジトリ更新 → push → `ansible-playbook -i inventory.ini playbook.yaml` 実行**
   - tmux インストール、Ghostty インストール、iTerm2 削除が完了
   - 設定ファイル無しのデフォルト状態で Ghostty/tmux を動作確認可能
2. **dotfiles リポジトリでローカル編集**
   - `.tmux.conf` と `.config/ghostty/config` を新規作成（commit はまだ）
   - `~/.tmux.conf` と `~/.config/ghostty/config` に手動でシンボリックリンクを張って動作確認
3. **動作確認 OK なら dotfiles を commit & push**
   - 次回 `ansible-playbook` 実行時、`geerlingguy.dotfiles` が同パスにリンクするため冪等

## Ansible Changes

### `roles/homebrew/tasks/main.yaml`

`name:` リストに `tmux` を追加（アルファベット順で `tfenv` の後）。

### `roles/homebrew_cask/tasks/main.yaml`

`name:` リストから `iterm2` を削除し、`ghostty` を追加（アルファベット順で `github` の前）。リスト末尾に iTerm2 アンインストールタスクを追加する。

```yaml
- name: uninstall iterm2
  community.general.homebrew_cask:
    name: iterm2
    state: absent
  ignore_errors: true
```

`ignore_errors: true` は既に未インストールの環境（再実行時）でも失敗しないようにするため。

## Dotfiles Changes

### `~/.tmux.conf`（新規）

| 設定 | 値・理由 |
|---|---|
| prefix | `C-b`（デフォルト維持） |
| mouse | on |
| terminal | `tmux-256color` + truecolor (`Tc`) |
| ペイン分割 | `prefix \|` で縦分割、`prefix -` で横分割、現在ディレクトリ引き継ぎ |
| ペイン移動 | `prefix h/j/k/l`（vim 風） |
| status line | 左にセッション名、右に時刻、ミニマル |
| reload | `prefix r` で `~/.tmux.conf` を再読込 |
| tpm | 使わない |

### `.config/ghostty/config`（新規。空ディレクトリは既存）

| 設定 | 値・理由 |
|---|---|
| `theme` | `Dracula`（starship のパレットと統一） |
| `font-family` | `SF Mono`（macOS 標準） |
| `font-size` | `14` |
| `window-padding-x` | `8` |
| `window-padding-y` | `8` |
| `shell-integration` | `zsh` |
| `macos-option-as-alt` | `true`（zsh で word jump を使うため） |

## Validation

### ansible 実行後

- `tmux -V` で tmux がインストールされている
- `which ghostty` で Ghostty がインストールされている
- `/Applications/iTerm.app` が存在しない
- Ghostty を起動してデフォルト設定で動作する

### dotfiles ローカル編集後

- 手動シンボリックリンクで Ghostty が Dracula テーマ + SF Mono で起動する
- tmux 起動時に設定が反映される（mouse、ペイン分割キーバインド等）
- tmux 内で starship プロンプトが正しい色で表示される

### dotfiles push 後

- 別端末等で playbook を再実行し、シンボリックリンクが正しく作成されること

## Changes Summary

| リポジトリ | ファイル | 変更内容 |
|---|---|---|
| ansible | `roles/homebrew/tasks/main.yaml` | `tmux` を追加 |
| ansible | `roles/homebrew_cask/tasks/main.yaml` | `iterm2` 削除、`ghostty` 追加、iTerm2 アンインストールタスク追加 |
| dotfiles | `.tmux.conf` | 新規作成 |
| dotfiles | `.config/ghostty/config` | 新規作成 |
