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
| `dotfiles_tmux_enabled` | `false` | Enable tmux setup (install tmux, TPM, symlink configs) |
| `dotfiles_tmux_tpm_repo` | `https://github.com/tmux-plugins/tpm` | TPM repository URL |
| `dotfiles_tmux_tpm_version` | `master` | TPM version/branch to clone |
| `dotfiles_tmux_install_plugins` | `true` | Run TPM install_plugins script after setup |
| `dotfiles_tmux_files` | See below | List of tmux config files to symlink |

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

### Tmux Configuration

When `dotfiles_tmux_enabled: true`, the role will:

1. Install tmux via apt
2. Clone TPM (Tmux Plugin Manager) to `~/.tmux/plugins/tpm`
3. Create symlinks for tmux configuration files
4. Optionally run TPM's `install_plugins` script

Default tmux files to symlink:

```yaml
dotfiles_tmux_files:
  - src: '.tmux.conf'
    dest: '.tmux.conf'
  - src: 'tmux/powerline-config.sh'
    dest: '.config/tmux-powerline/config.sh'
  - src: 'tmux/powerline-theme.sh'
    dest: '.config/tmux-powerline/themes/my-theme.sh'
```

Override `dotfiles_tmux_files` to customize which files are symlinked for your tmux setup.

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

### With Tmux Setup

```yaml
- name: Configure dotfiles with tmux
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
    dotfiles_tmux_enabled: true
    dotfiles_tmux_files:
      - src: '.tmux.conf'
        dest: '.tmux.conf'
      - src: 'tmux/powerline-config.sh'
        dest: '.config/tmux-powerline/config.sh'
      - src: 'tmux/powerline-theme.sh'
        dest: '.config/tmux-powerline/themes/my-theme.sh'
  roles:
    - role: jonimofo.infrastructure.dotfiles
```

## What This Role Does

1. Verifies Debian-based system
2. Installs git via apt
3. Clones dotfiles repository to each user's home
4. Creates parent directories for symlink destinations
5. Creates symlinks from repo files to home directory

When `dotfiles_tmux_enabled: true`:

6. Installs tmux via apt
7. Clones TPM to `~/.tmux/plugins/tpm` for each user
8. Creates parent directories for tmux config files
9. Creates symlinks for tmux configuration files
10. Runs TPM `install_plugins` script (if enabled)

## License

GPL-2.0-or-later

## Author Information

jonimofo
