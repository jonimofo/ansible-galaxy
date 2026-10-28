# Ansible Collection - jonimofo.infrastructure

Roles for the baseline configuration of Debian and Ubuntu servers and workstations: identity, users, SSH, firewall, updates, shell tooling.

Supported: Debian bookworm/trixie, Ubuntu jammy/noble/resolute, x86_64 and aarch64, Ansible 2.15+.

## Roles

| Role | Purpose |
|------|---------|
| `host` | Hostname, `/etc/hosts`, `/tmp` mode, optional DNS via netplan and systemd-resolved |
| `users` | Users, groups, sudo policy, root lock, removal of old accounts |
| `ssh` | sshd hardening drop-in, `authorized_keys`, `AllowUsers`, lockout guard |
| `ufw` | Firewall policies and rules, lockout guard |
| `fail2ban` | Jails (sshd, recidive, custom), incremental bans |
| `timezone` | System timezone |
| `locale` | Locales and `/etc/default/locale` |
| `packages` | APT packages, nightly security updates, `needrestart` |
| `dotfiles` | Dotfiles repo clone and symlinks per user, optional tmux + TPM |
| `fzf` | fzf from source with shell integration |
| `lazydocker` | lazydocker binary |
| `astronvim` | Neovim and AstroNvim per user |

`roles/brave_students_profile` is an internal, unsupported helper and not part of the published API.

Each role has a README with every variable. Breaking changes between major versions are listed in [docs/MIGRATION-2.0.md](docs/MIGRATION-2.0.md) and [CHANGELOG.md](CHANGELOG.md).

## Install

`requirements.yml` in the consuming project:

```yaml
collections:
  - name: jonimofo.infrastructure
    version: "2.0.0"
```

```bash
ansible-galaxy collection install -r requirements.yml
```

## Example playbook

```yaml
- name: Configure Debian server
  hosts: all
  become: true
  pre_tasks:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true
        cache_valid_time: 3600
  roles:
    - { role: jonimofo.infrastructure.host, tags: host }
    - { role: jonimofo.infrastructure.users, tags: users }
    - { role: jonimofo.infrastructure.ssh, tags: ssh }
    - { role: jonimofo.infrastructure.ufw, tags: ufw }
    - { role: jonimofo.infrastructure.fail2ban, tags: fail2ban }
    - { role: jonimofo.infrastructure.timezone, tags: timezone }
    - { role: jonimofo.infrastructure.locale, tags: locale }
    - { role: jonimofo.infrastructure.packages, tags: packages }
    - { role: jonimofo.infrastructure.dotfiles, tags: dotfiles }
    - { role: jonimofo.infrastructure.fzf, tags: fzf }
    - { role: jonimofo.infrastructure.lazydocker, tags: lazydocker }
    - { role: jonimofo.infrastructure.astronvim, tags: astronvim }
```

Variables go in the consumer's `group_vars` and `host_vars`, one file per role. See `playbook.example.yml`.

## Development

```bash
make setup    # venv, dependencies, git hooks
make lint     # yamllint + ansible-lint (production profile)
make audit    # audit/audit.py: structure, security, idempotency checks on every role
```

Branches: `feat/*` or `fix/*` from `develop`, PR to `develop`, `develop` promoted to `main` with a merge commit and a `vX.Y.Z` tag, then `ansible-galaxy collection build` and `publish`. Direct pushes to `main` and `develop` are rejected by the pre-push hook. Commits follow the Angular convention, no em-dashes in added lines.

## License

GPL-2.0-or-later
