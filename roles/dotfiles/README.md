# Ansible Role: dotfiles

Clones a dotfiles Git repository and creates symlinks to user home directories.

## Features

- Clones dotfiles repo per-user with configurable branch/version
- Creates parent directories as needed
- Symlinks specified files to home directory
- Supports multiple users with different file mappings
- Idempotent - safe to run multiple times

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
| `dotfiles_user_configs` | `[]` | Configuration dict (see below) |

### Configuration Structure

```yaml
dotfiles_user_configs:
  repo: 'git@github.com:user/dotfiles.git'  # Git repository URL (required)
  version: 'main'                            # Branch, tag, or commit
  clone_dir: '.dotfiles'                     # Clone destination in home
  users:                                     # List of users to configure
    - user: 'username'                       # Username (required)
      home: '/home/username'                 # Home directory (optional)
      files:                                 # Files to symlink
        - src: 'bashrc'                      # Source in repo
          dest: '.bashrc'                    # Destination in home
```

## Dependencies

None.

## Example Playbook

### Basic Usage

```yaml
- name: Configure dotfiles
  hosts: all
  become: true
  vars:
    dotfiles_user_configs:
      repo: 'git@github.com:jonimofo/dotfiles.git'
      version: 'main'
      clone_dir: '.dotfiles'
      users:
        - user: admin
          files:
            - src: 'bashrc'
              dest: '.bashrc'
            - src: 'vimrc'
              dest: '.vimrc'
  roles:
    - role: jonimofo.infrastructure.dotfiles
```

### Multiple Users

```yaml
- name: Configure dotfiles for team
  hosts: workstations
  become: true
  vars:
    dotfiles_user_configs:
      repo: 'https://github.com/company/dotfiles.git'
      version: 'production'
      clone_dir: '.config/dotfiles'
      users:
        - user: developer
          files:
            - src: 'bash/bashrc'
              dest: '.bashrc'
            - src: 'git/gitconfig'
              dest: '.gitconfig'
            - src: 'config/htop/htoprc'
              dest: '.config/htop/htoprc'
        - user: admin
          files:
            - src: 'bash/bashrc'
              dest: '.bashrc'
            - src: 'tmux/tmux.conf'
              dest: '.tmux.conf'
  roles:
    - role: jonimofo.infrastructure.dotfiles
```

### Custom Home Directory

```yaml
- name: Configure dotfiles with custom home
  hosts: all
  become: true
  vars:
    dotfiles_user_configs:
      repo: 'git@github.com:user/dotfiles.git'
      version: 'main'
      clone_dir: '.dotfiles'
      users:
        - user: app
          home: '/opt/app'
          files:
            - src: 'profile'
              dest: '.profile'
  roles:
    - role: jonimofo.infrastructure.dotfiles
```

## What This Role Does

1. Verifies Debian-based system
2. Installs git via apt
3. Clones dotfiles repository to each user's home
4. Creates parent directories for symlink destinations
5. Creates symlinks from repo files to home directory

## License

GPL-2.0-or-later

## Author Information

jonimofo
