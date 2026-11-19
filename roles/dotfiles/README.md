# Ansible Role: dotfiles

Puts the listed files of a dotfiles Git repository into user home directories as regular files. Since 3.0.0 no clone and no symlink stay on the host (see `docs/MIGRATION-3.0.md`).

## Features

- The host fetches the listed sources itself, from the repo at a branch, tag or commit: a temporary sparse checkout, one commit deep, deleted in the same run (also on failure)
- Checks SSH agent forwarding and repo access before fetching over SSH
- Fails when a listed source file is missing from the repo, in check mode too
- Creates parent directories as needed
- Copies each file to its destination as a regular file owned by the user, executable bit kept; a symlink at the destination is removed first, its target is not written
- Removes the clone left by a pre-3.0 run once it is clean (see `clone_dir`)
- Supports multiple users with different file mappings
- Optional tmux setup: installs tmux, TPM, and plugins
- Idempotent - safe to run multiple times

## Requirements

- **Ansible version:** 2.15+
- **Supported OS:** Debian-based systems only
  - Debian (bookworm, trixie)
  - Ubuntu (jammy, noble, resolute)
- **Supported architectures:** x86_64, aarch64
- **Privileges:** Requires `become: true`
- **git on the host:** 2.24 or later (installed by the role; Debian bookworm ships 2.39, Ubuntu jammy 2.34)

## Role Variables

All variables are defined in `defaults/main.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `dotfiles_user_configs` | `{repo: '', version: main, clone_dir: .dotfiles, users: []}` | Configuration dict (see below) |
| `dotfiles_verify_ssh_access` | `true` | Check the forwarded SSH agent and repo host before fetching over SSH |
| `dotfiles_tmux_install` | `false` | Install tmux, TPM, and plugins for all users |

### Configuration Structure

```yaml
dotfiles_user_configs:
  repo: 'git@github.com:user/dotfiles.git'  # Git repository URL (required)
  version: 'main'                            # Branch, tag, or commit (fetched one commit deep)
  clone_dir: '.dotfiles'                     # Pre-3.0 clone to clean up, in home
  users:                                     # List of users to configure
    - user: 'username'                       # Username (required)
      home: '/home/username'                 # Home directory (optional)
      files:                                 # Files to copy
        - src: 'bashrc'                      # Source in repo
          dest: '.bashrc'                    # Destination in home
```

### Files, not links

Each destination is a copy, owned by the user. A file edited by hand on the host is overwritten on the next run: change it in the repo instead. A commit SHA as `version` needs a server that allows fetching a commit by id (GitHub and GitLab do).

### `clone_dir`: the pre-3.0 clone

Before 3.0.0 the role kept a clone at `<home>/<clone_dir>` and symlinked into it. After the files are copied, every run checks that path:

- a git clone whose `remote.origin.url` is `repo`, where git reports nothing that would be lost: deleted
- the same clone with uncommitted changes, ignored files, stashes or unpushed commits (on a local branch or a detached HEAD, held by no remote-tracking ref), or a git error while checking: kept, the run prints a warning naming the path; it is deleted on the first run after it is clean

After a deletion, links into the removed clone found at the home top level or next to a listed destination are reported in one warning and left in place: remove them by hand. A user without `files` (or with `files: []`) is skipped: no fetch, no cleanup.

`clone_dir` must be a non-empty relative path below the home (not `.`, no `..`); `src` and `dest` must be relative without `..`, and `home` absolute. The run fails before any fetch otherwise.
- anything else (another repo, a plain folder, nothing): left alone, no message

### Check mode

The temporary checkout, the fetch and its removal run in check mode too: they only touch the temporary directory. `--check --diff` therefore shows the real diff of each file and fails on a missing source; destinations, symlinks and the old clone are not touched.

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

### With Tmux, TPM, and Powerline Theme

```yaml
- name: Configure dotfiles with tmux
  hosts: all
  become: true
  vars:
    dotfiles_tmux_install: true
    dotfiles_user_configs:
      repo: 'git@github.com:jonimofo/dotfiles.git'
      version: 'main'
      clone_dir: 'Repos/dotfiles'
      users:
        - user: bgi
          files:
            - src: '.bashrc'
              dest: '.bashrc'
            - src: '.tmux.conf'
              dest: '.tmux.conf'
            - src: 'tmux/powerline-config.sh'
              dest: '.config/tmux-powerline/config.sh'
            - src: 'tmux/powerline-theme.sh'
              dest: '.config/tmux-powerline/themes/my-theme.sh'
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

1. Verifies Debian-based system and installs git
2. For an scp-like repo URL (`user@host:path`), checks that its host part is a plain `user@host`, then the forwarded agent and the repo host (`dotfiles_verify_ssh_access`). `ssh://` and `https://` URLs are not checked
3. Per user, fetches the listed sources into a private temporary directory (sparse checkout, one commit deep, blob filter)
4. Fails if a listed source is missing from the repo at that version
5. Creates parent directories, removes a symlink at the destination, copies each file as a regular file, then deletes the temporary directory
6. Deletes the pre-3.0 clone at `clone_dir` when it is a clean clone of the repo
7. Optionally installs tmux, clones TPM, and installs tmux plugins

## License

GPL-2.0-or-later

## Author Information

jonimofo
