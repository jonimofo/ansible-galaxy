# Migrating to jonimofo.infrastructure 2.0.0

2.0.0 merges the QDV role implementations into this collection. It is a breaking release.

## What changed

- Supported platforms: Debian (bookworm, trixie) and Ubuntu (jammy, noble, resolute). Raspberry Pi OS is no longer supported.
- The `fasd` role is removed. The `packages` role installs `zoxide` instead and removes a previously built `/usr/local/bin/fasd`.
- Every role variable is prefixed with the role name (ansible-lint `var-naming[no-role-prefix]`). See the table below.
- `packages`: unattended upgrades are enabled by default (`packages_apt_update_unattended_upgrades: true`).
- `ssh`: `authorized_keys` is managed exclusively for each user in `ssh_allowed_users`, from public key files in `ssh_public_keys_dir`. Check the key files before the first run.

## Variable renames

Rows are added role by role during the port. Consumers rename these keys in `group_vars` and `host_vars`.

| Role | Old variable | New variable | Note |
|---|---|---|---|
| fasd | `fasd_*` | removed | role deleted, use `packages` + zoxide |
| timezone | `timezone_name` default `Asia/Ho_Chi_Minh` | default `Europe/Paris` | variable name unchanged, only the default moved |
| locale | `locale_reboot` | removed | reboot task deleted, reboot manually if needed |
| locale | `locale_env.LC_ALL` | removed from default | setting LC_ALL system-wide overrode per-user LC_*; set it in your own `locale_env` if wanted |
| lazydocker | `lazydocker_download_dir` default `/tmp/ansible-lazydocker` | default `/tmp` | the role no longer creates or chmods the directory |
| lazydocker | `lazydocker_arch_map.armv7l` | removed | 32-bit ARM dropped with Raspberry Pi support |
| astronvim | `neovim_binary_path` | `astronvim_neovim_binary_path` | |
| astronvim | `neovim_download_url` | `astronvim_neovim_download_url` | |
| astronvim | `neovim_version` | `astronvim_neovim_version` | default bumped to v0.12.6 |
| astronvim | | `astronvim_build_packages` | new, default `[git, gcc, unzip]` |
| dotfiles | | `dotfiles_verify_ssh_access` | new, default `true`; set `false` to skip the agent and host checks |
| dotfiles | `dotfiles_user_configs` default `[]` | default dict with `users: []` | the role is a no-op when unconfigured instead of failing |
| dotfiles | clone depth | shallow, single branch | an existing full clone is removed and re-cloned once |
| packages | `apt_update_disable_units` | `packages_apt_update_disable_units` | |
| packages | `apt_update_service_dest` | `packages_apt_update_service_dest` | |
| packages | `apt_update_service_mode` | `packages_apt_update_service_mode` | |
| packages | `apt_update_timer_dest` | `packages_apt_update_timer_dest` | |
| packages | `apt_update_timer_mode` | `packages_apt_update_timer_mode` | |
| packages | `apt_update_timer_on_calendar` | `packages_apt_update_timer_on_calendar` | |
| packages | `apt_update_timer_persistent` | `packages_apt_update_timer_persistent` | |
| packages | `apt_update_timer_unit` | `packages_apt_update_timer_unit` | |
| packages | `apt_update_packages_to_install` | `packages_apt_update_packages_to_install` | |
| packages | `apt_update_unattended_upgrades` | `packages_apt_update_unattended_upgrades` | |
| packages | `apt_update_unattended_origins` | `packages_apt_update_unattended_origins` | |
| packages | `apt_update_unattended_blacklist` | `packages_apt_update_unattended_blacklist` | |
| packages | `apt_update_unattended_autofix` | `packages_apt_update_unattended_autofix` | |
| packages | `apt_update_unattended_remove_unused` | `packages_apt_update_unattended_remove_unused` | |
| packages | `apt_update_unattended_reboot` | `packages_apt_update_unattended_reboot` | |
| packages | `apt_update_unattended_reboot_time` | `packages_apt_update_unattended_reboot_time` | |
| packages | `apt_update_unattended_mail` | `packages_apt_update_unattended_mail` | |
| packages | `apt_update_unattended_mail_on_error` | `packages_apt_update_unattended_mail_on_error` | |
| packages | `apt_update_unattended_upgrades` default `false` | `packages_apt_update_unattended_upgrades` default `true` | nightly service now runs `unattended-upgrade` (security only); set `false` to keep the old nightly `full-upgrade` |
| packages | `apt_update_unattended_origins` Debian list | per-distribution map `packages_apt_update_unattended_origins_map` | override the list directly if needed |
| packages | | `packages_obsolete_paths` | new, removes the old fasd binary and man page |
| packages | | `packages_needrestart_install` | new, default `true` |
| users | | `users_home_mode` | new, default `"0750"`; existing homes are tightened from 0755. Set `""` to skip |
| users | | `users_absent` | new, default `[]` |
| users | user option | `home`, `system` | new optional per-user keys |
| fail2ban | `fail2ban_ignoreip` string (QDV) | list | e.g. `["127.0.0.1/8", "::1", "192.168.100.0/24"]`; default now includes `::1` |
| fail2ban | `fail2ban_ban_action` (QDV) | `fail2ban_banaction` | default `ufw` (QDV hardcoded `iptables-multiport`) |
| fail2ban | `fail2ban_sshd_enabled`, `fail2ban_sshd_port`, `fail2ban_sshd_maxretry`, `fail2ban_sshd_bantime` (QDV) | `fail2ban_jails.sshd.{enabled,port,maxretry,bantime}` | the recidive jail is on by default too |
| fail2ban | `fail2ban_maxretry` default 5 (QDV) | default 3 | bantime/findtime accept seconds or `1h`/`10m` |
