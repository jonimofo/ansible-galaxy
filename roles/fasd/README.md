# Ansible Role: fasd

Installs fasd (fast directory/file access) from source and configures shell integration for specified users.

## Features

- Installs fasd from official Git repository
- Configures per-user shell integration (.bashrc)
- Provides quick access to frequently used files and directories
- Cleans up build directory after installation

## Requirements

- **Ansible version:** 2.12+
- **Supported OS:** Debian-based systems only
  - Debian (bullseye, bookworm, trixie)
  - Ubuntu (focal, jammy, noble)
  - Raspberry Pi OS
- **Supported architectures:** x86_64, aarch64, armv7l
- **Privileges:** Requires `become: true`

## Role Variables

All variables are defined in `defaults/main.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `fasd_git_repo_url` | `https://github.com/clvv/fasd.git` | Git repository URL |
| `fasd_git_version` | `master` | Branch or tag to checkout |
| `fasd_clone_dir` | `/tmp/fasd` | Temporary directory for cloning |
| `fasd_install_path` | `/usr/local/bin` | Installation path for binary |
| `fasd_dependencies` | `[git, make]` | Packages required to build |
| `fasd_users` | `[]` | List of users to configure |
| `fasd_configure_shell` | `true` | Add fasd init to .bashrc |
| `fasd_cleanup_build_dir` | `true` | Remove temp dir after install |

### User Configuration

Each user in `fasd_users` should have a `name` key:

```yaml
fasd_users:
  - name: "alice"
  - name: "bob"
```

## Dependencies

None.

## Example Playbook

### Basic Usage

```yaml
- name: Install fasd
  hosts: all
  become: true
  vars:
    fasd_users:
      - name: "admin"
  roles:
    - role: jonimofo.infrastructure.fasd
```

### Multiple Users

```yaml
- name: Install fasd for team
  hosts: workstations
  become: true
  vars:
    fasd_users:
      - name: "developer"
      - name: "sysadmin"
  roles:
    - role: jonimofo.infrastructure.fasd
```

### Without Shell Configuration

```yaml
- name: Install fasd only (no bashrc)
  hosts: all
  become: true
  vars:
    fasd_configure_shell: false
  roles:
    - role: jonimofo.infrastructure.fasd
```

## What This Role Does

1. Verifies Debian-based system
2. Installs dependencies (git, make) via apt
3. Clones fasd repository to temp directory
4. Builds and installs fasd to `/usr/local/bin`
5. Adds `eval "$(fasd --init auto)"` to each user's `.bashrc`
6. Cleans up temp build directory

## Usage After Installation

After installation, users get these commands:

| Command | Description |
|---------|-------------|
| `z foo` | Jump to directory matching "foo" |
| `f foo` | Open file matching "foo" |
| `zz foo` | Interactive directory selection |
| `v foo` | Open file in $EDITOR |

## License

GPL-2.0-or-later

## Author Information

jonimofo
