# Ansible Role: fzf

Installs fzf (fuzzy finder) from source and configures shell integration for specified users.

## Features

- Installs fzf from official Git repository
- Configures per-user shell integration (.fzf.bash)
- Adds key bindings (Ctrl+R, Ctrl+T, Alt+C)
- Enables command-line auto-completion

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
| `fzf_repo_url` | `https://github.com/junegunn/fzf.git` | Git repository URL |
| `fzf_install_path` | `/opt/fzf` | Directory where fzf is cloned |
| `fzf_users` | `[]` | List of users to configure |
| `fzf_update_bashrc` | `true` | Default for adding source line to .bashrc |

### User Configuration

Each user in `fzf_users` can have:

| Option | Required | Description |
|--------|----------|-------------|
| `name` | Yes | Username |
| `update_bashrc` | No | Add source line to .bashrc (default: `fzf_update_bashrc`) |

## Dependencies

None.

## Example Playbook

### Basic Usage

```yaml
- name: Install fzf
  hosts: all
  become: true
  vars:
    fzf_users:
      - name: "admin"
  roles:
    - role: jonimofo.infrastructure.fzf
```

### Multiple Users

```yaml
- name: Install fzf for multiple users
  hosts: workstations
  become: true
  vars:
    fzf_users:
      - name: "alice"
      - name: "bob"
        update_bashrc: false  # don't modify bob's .bashrc
  roles:
    - role: jonimofo.infrastructure.fzf
```

### Custom Install Path

```yaml
- name: Install fzf to custom location
  hosts: all
  become: true
  vars:
    fzf_install_path: "/usr/local/share/fzf"
    fzf_users:
      - name: "developer"
  roles:
    - role: jonimofo.infrastructure.fzf
```

## What This Role Does

1. Verifies Debian-based system
2. Installs git via apt
3. Clones fzf repository to `fzf_install_path`
4. Runs fzf install script (binary only)
5. Creates `.fzf.bash` for each user (sets PATH, sources completions and key bindings)
6. Optionally adds source line to each user's `.bashrc`

## Key Bindings

After installation, users get these key bindings in bash:

| Binding | Action |
|---------|--------|
| `Ctrl+R` | Search command history |
| `Ctrl+T` | Search files in current directory |
| `Alt+C` | Change to subdirectory |

## License

GPL-2.0-or-later

## Author Information

jonimofo
