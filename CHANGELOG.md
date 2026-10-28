# Changelog

All notable changes to this collection are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versions follow SemVer.

## [2.0.1] - 2026-10-28

### Fixed

- **ssh**: the `Include /etc/ssh/sshd_config.d/*.conf` line is added to `sshd_config` when missing (hosts provisioned by the former QDV role had a fully templated file), instead of failing.

## [2.0.0] - 2026-10-28

Merges the QDV role implementations into this collection, which becomes the single source of truth for all consumers. Breaking release: see [docs/MIGRATION-2.0.md](docs/MIGRATION-2.0.md) for the variable renames.

### Removed

- `fasd` role. The `packages` role installs `zoxide` and removes a previously built `/usr/local/bin/fasd`.
- Raspberry Pi OS, Debian bullseye, Ubuntu focal and 32-bit ARM support. Platforms are now Debian bookworm/trixie and Ubuntu jammy/noble/resolute, x86_64 and aarch64. `requires_ansible` is 2.15.

### Changed

- **timezone**: default `Europe/Paris`.
- **locale**: follows the `/etc/default/locale` symlink (idempotent), reboot option removed, `LC_ALL` no longer in the default `locale_env`.
- **lazydocker**: 0.25.2, extracts only the binary, root-owned, removes LICENSE/README left by older runs.
- **astronvim**: variables renamed `astronvim_neovim_*`, Neovim v0.12.6, `--no-same-owner` extraction and ownership repair, plugins installed headlessly so the second run is idempotent, new `astronvim_build_packages`.
- **dotfiles**: shallow single-branch clone, listed sources checked before linking, SSH agent and repo host verified before an ssh clone (`dotfiles_verify_ssh_access`), home mode left alone for root-level files, no-op when unconfigured.
- **packages**: all variables renamed `packages_apt_update_*`; unattended upgrades on by default with `Origins-Pattern` and per-distribution security origins; the nightly service runs `unattended-upgrade` (or `apt-get full-upgrade` when unattended upgrades are off) with `apt-get`; the timer is restarted when its unit changes; `needrestart` installed in automatic mode; `packages_obsolete_paths`.
- **users**: supplementary groups created before users, `home` and `system` per-user options, `users_home_mode` (0750), `users_absent`.
- **fail2ban**: `::1` in the default ignore list, README fixed (ban action defaults to `ufw`).
- **ufw**: `ufw_verify_port` lockout guard after enabling.
- **ssh**: hardening written to `/etc/ssh/sshd_config.d/00-ansible.conf` (wins over cloud-init), keys from inline, `pubkey_file` or `ssh_public_keys_dir`, validated before use, sshd reloaded and the port checked from the control node.
- **host**: `host_hostname` defaults to `inventory_hostname`; DNS management via netplan (`host_dns_servers`) and systemd-resolved (backup/fallback servers), each skipped when the tool is absent.

### Added

- `timezone` role.
- `community.general` and `ansible.posix` declared as dependencies.
- Configurable Python audit tool (`make audit`).
- `scripts/em-dashes.py`, pre-commit em-dash check and pre-push protected-branch hook.

### Also since the v1.1.0 tag

- `gui_apps` role removed.
- **dotfiles**: tmux and TPM install (`dotfiles_tmux_install`).
- **users**: root lock and sudo safeguards.
- **packages**: autoremove/autoclean gated behind `packages_run_cleanup`.
- **lazydocker**: download URL fix, no more chmod of `/tmp`.

## [1.1.0] - 2026-04-13

Published on Galaxy from the `v1.1.0` tag.
