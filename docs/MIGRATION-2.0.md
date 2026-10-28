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
