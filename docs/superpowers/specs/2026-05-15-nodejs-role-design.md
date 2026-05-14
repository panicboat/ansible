# nodejs role design

## Goal

Ansible で Node.js (nodenv 経由) と npm グローバルパッケージを管理する。初出のパッケージは `@evenrealities/even-terminal`。

## Scope

- Node.js を nodenv でインストールし、global バージョンを設定する
- 指定した npm パッケージを global インストールする

## Role structure

`roles/nodejs/tasks/main.yaml` のみ。設定値（Node.js バージョン・npm パッケージ名）はタスク内にインライン記述する。

Why: 既存ロール（homebrew, scripts など）が設定値をインラインで持つパターンを踏襲し、`vars/main.yaml` は `geerlingguy.dotfiles` ロールが要求する dotfiles 関連変数の置き場に専念させる。

## Node.js version

`22.11.0`（執筆時点の最新 LTS）を単一バージョン固定で採用する。

Why: 現状複数バージョン併用するユースケースは無く、YAGNI に従い単純構成とする。

## Tasks

1. `nodenv install --skip-existing <version>` で Node.js を導入
2. `nodenv global` の現在値を読み取り、対象バージョンと差分があれば `nodenv global <version>` を実行
3. `community.general.npm` で `executable: ~/.nodenv/shims/npm` を指定し global インストール

Why (shim path 指定): `community.general.npm` の `executable` に nodenv shim を渡すことで、shell 初期化に依存せず nodenv 管理下の npm を呼べる。

Why (`--skip-existing` と `nodenv global` の差分チェック): いずれもタスクの冪等性を確保するため。

## Playbook integration

`homebrew` ロール（`nodenv` を Brew でインストールする側）の後に `nodejs` ロールを追加する。

```yaml
roles:
  - dotfiles
  - geerlingguy.dotfiles
  - scripts
  - launchd
  - homebrew
  - homebrew_cask
  - mac_app_store
  - nodejs
```

## npm packages

- `@evenrealities/even-terminal`
