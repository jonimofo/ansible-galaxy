# Migrating to jonimofo.infrastructure 2.0.0

2.0.0 merges the QDV role implementations into this collection. It is a breaking release.

## What changed

- Supported platforms: Debian (bookworm, trixie) and Ubuntu (jammy, noble, resolute). Raspberry Pi OS is no longer supported.
- The `fasd` role is removed. The `packages` role installs `zoxide` instead and removes a previously built `/usr/local/bin/fasd`.
- Every role variable is prefixed with the role name (ansible-lint `var-naming[no-role-prefix]`). See the table below.
- `packages`: unattended upgrades are enabled by default (`packages_apt_update_unattended_upgrades: true`).
- `ssh`: hardening moves from line edits in `sshd_config` to the drop-in `/etc/ssh/sshd_config.d/00-ansible.conf`. Keys in `ssh_users` can come inline (`pubkey`), from a file (`pubkey_file`) or from `ssh_public_keys_dir/<name>.pub`. `authorized_keys` stays exclusive by default: list the key you connect with.
- `host`: optional DNS management (netplan + systemd-resolved), off unless `host_dns_servers` is set; the resolved drop-in with public backup servers is written wherever systemd-resolved exists.
- `packages`: `needrestart` is installed in automatic mode; the nightly timer is restarted when its schedule changes.

## Variable renames

Consumers rename these keys in `group_vars` and `host_vars`. Rows marked (QDV) apply to hosts that used the QDV copy of the roles.

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
| packages | `apt_update_cache_valid_time` | `packages_apt_cache_valid_time` | default `3600`, used by the install task since 2.0.2 |
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
| fail2ban | `fail2ban_update_cache` | removed | refresh the apt cache once in `pre_tasks` |
| fail2ban | `fail2ban_ignoreip` string (QDV) | list | e.g. `["127.0.0.1/8", "::1", "192.168.100.0/24"]`; default now includes `::1` |
| fail2ban | `fail2ban_ban_action` (QDV) | `fail2ban_banaction` | default `ufw` (QDV hardcoded `iptables-multiport`) |
| fail2ban | `fail2ban_sshd_enabled`, `fail2ban_sshd_port`, `fail2ban_sshd_maxretry`, `fail2ban_sshd_bantime` (QDV) | `fail2ban_jails.sshd.{enabled,port,maxretry,bantime}` | the recidive jail is on by default too |
| fail2ban | `fail2ban_maxretry` default 5 (QDV) | default 3 | bantime/findtime accept seconds or `1h`/`10m` |
| ufw | `ufw_update_cache` | removed | refresh the apt cache once in `pre_tasks`, see `playbook.example.yml` |
| ufw | `ufw_force_reset` (QDV) | `ufw_reset_before_configure` | |
| ufw | `ufw_default_incoming`, `ufw_default_outgoing` (QDV) | `ufw_default_policies` list of `{direction, policy}` | defaults already deny incoming / allow outgoing |
| ufw | | `ufw_verify_port`, `ufw_verify_timeout` | new; `ufw_verify_port` follows `ssh_port` (else 22), `0` to skip. UFW is not enabled without an allow/limit rule for it |
| ssh | line edits in `/etc/ssh/sshd_config` | drop-in `/etc/ssh/sshd_config.d/00-ansible.conf` | old edited lines stay in the stock file and agree with the drop-in |
| ssh | `ssh_allowed_users` list of names (QDV) | `ssh_users` list of `{name}` | keys read from `ssh_public_keys_dir/<name>.pub` |
| ssh | `ssh_public_keys_dir` default `role_path/files` (QDV) | default `""` | set it per inventory, e.g. `"{{ inventory_dir }}/files/ssh"` |
| ssh | `ssh_password_authentication`, `ssh_pubkey_authentication`, `ssh_x11_forwarding`, `ssh_allow_agent_forwarding` as `"yes"`/`"no"` (QDV) | booleans | |
| ssh | | `ssh_dropin_name`, `ssh_service_name`, `ssh_verify_port`, `ssh_verify_timeout`, `ssh_pubkey_authentication` | new; the role refuses to write AllowUsers without the connecting user |
| ssh | handler `Restart sshd` | `Reload sshd` | |
| host | `host_hostname` default `""` | default `inventory_hostname` | |
| host | | `host_dns_servers`, `host_dns_interface`, `host_dns_backup_servers`, `host_dns_fallback_servers`, `host_dns_manage_resolved` | new, DNS parts skipped when netplan / systemd-resolved are absent |
| host | `host_dns_file_prefix` default `qdv` (QDV) | default `ansible` | **baf and scranton must set it** (`baf` / `qdv`) to keep their existing override files |
