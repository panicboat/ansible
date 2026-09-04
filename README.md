# ansible

## Require

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install ansible git
```

## Usage

download git repository

```sh
git clone https://github.com/panicboat/ansible.git
```

edit inventory.ini

```sh
cp inventory.ini.example inventory.ini
```

deploy playbook

```sh
export HOMEBREW_NO_REQUIRE_TAP_TRUST=1
ansible-playbook playbook.yaml -i inventory.ini
```
