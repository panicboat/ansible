# nodejs role Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ansible で Node.js (nodenv 経由) と npm グローバルパッケージ (`@evenrealities/even-terminal`) を管理する `nodejs` ロールを追加する。

**Architecture:** 新規ロール `roles/nodejs/tasks/main.yaml` を作成し、`playbook.yaml` の `homebrew` 後に組み込む。Node.js 本体は nodenv で 22.11.0 を導入・global 設定し、npm パッケージは `community.general.npm` モジュールで shim 経由インストールする。冪等性は `nodenv install --skip-existing` と `nodenv global` の現値比較で確保する。

**Tech Stack:** Ansible (community.general collection), nodenv (Homebrew 経由で別ロールが導入)

**Spec:** `docs/superpowers/specs/2026-05-15-nodejs-role-design.md`

---

### Task 1: Create nodejs role tasks file

**Files:**
- Create: `roles/nodejs/tasks/main.yaml`

- [ ] **Step 1: Create role directory**

```bash
mkdir -p roles/nodejs/tasks
```

- [ ] **Step 2: Write tasks/main.yaml**

Create `roles/nodejs/tasks/main.yaml` with the following content:

```yaml
- name: Install Node.js via nodenv
  ansible.builtin.command: nodenv install --skip-existing 22.11.0
  register: nodenv_install
  changed_when: "'Installed' in nodenv_install.stdout"

- name: Read current global Node.js version
  ansible.builtin.command: nodenv global
  register: nodenv_global
  changed_when: false

- name: Set global Node.js version
  ansible.builtin.command: nodenv global 22.11.0
  when: nodenv_global.stdout != "22.11.0"

- name: Install npm global packages
  community.general.npm:
    name: "@evenrealities/even-terminal"
    global: true
    executable: "{{ ansible_env.HOME }}/.nodenv/shims/npm"
```

- [ ] **Step 3: Syntax check**

Run: `ansible-playbook playbook.yaml -i inventory.ini --syntax-check`
Expected: `playbook: playbook.yaml` （エラー無し）

注: この時点では `playbook.yaml` に `nodejs` ロールが組み込まれていないため、ロール単体構文は次タスクで検証される。

- [ ] **Step 4: Commit**

```bash
git add roles/nodejs/tasks/main.yaml
git commit -s -m "feat(nodejs): add role to install Node.js via nodenv and npm packages"
```

---

### Task 2: Wire nodejs role into playbook

**Files:**
- Modify: `playbook.yaml`

- [ ] **Step 1: Edit playbook.yaml**

`roles:` リストの末尾に `nodejs` を追加する。`homebrew`（`nodenv` を入れる側）以降に並ぶように配置する。

変更前:
```yaml
  roles:
    - dotfiles
    - geerlingguy.dotfiles
    - scripts
    - launchd
    - homebrew
    - homebrew_cask
    - mac_app_store
```

変更後:
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

- [ ] **Step 2: Syntax check**

Run: `ansible-playbook playbook.yaml -i inventory.ini --syntax-check`
Expected: `playbook: playbook.yaml` （エラー無し、`nodejs` ロールが読み込まれる）

- [ ] **Step 3: Commit**

```bash
git add playbook.yaml
git commit -s -m "feat(playbook): wire nodejs role into playbook"
```

---

### Task 3: Run playbook and verify

**Files:** （変更なし）

- [ ] **Step 1: Execute the playbook**

Run: `ansible-playbook playbook.yaml -i inventory.ini`
Expected:
- `Install Node.js via nodenv`: 既に 22.11.0 が入っていれば `ok`、新規なら `changed`
- `Read current global Node.js version`: 常に `ok`
- `Set global Node.js version`: 既に 22.11.0 が global ならスキップ、そうでなければ `changed`
- `Install npm global packages`: 未インストールなら `changed`、既インストールなら `ok`
- 全体: failed=0

- [ ] **Step 2: Verify Node.js version**

Run: `~/.nodenv/shims/node --version`
Expected: `v22.11.0`

- [ ] **Step 3: Verify npm package**

Run: `~/.nodenv/shims/npm list -g @evenrealities/even-terminal`
Expected: `@evenrealities/even-terminal@<version>` が一覧に表示される

- [ ] **Step 4: Verify idempotency**

Run: `ansible-playbook playbook.yaml -i inventory.ini`
Expected: 2 回目の実行で `nodejs` ロール内の全タスクが `ok`（`changed=0`）になる

- [ ] **Step 5: Run even-terminal smoke check**

Run: `~/.nodenv/shims/even-terminal --help` または該当バイナリ
Expected: ヘルプ出力（実行可能であることの確認）

注: `even-terminal` の正確な CLI 名が異なる場合は `~/.nodenv/versions/22.11.0/bin/` 配下を確認する。

---
