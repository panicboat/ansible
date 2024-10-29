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

install plugin

```sh
ansible-galaxy install -r requirements.yaml
```

deploy playbook

```sh
ansible-playbook playbook.yaml -i inventory.ini
```
