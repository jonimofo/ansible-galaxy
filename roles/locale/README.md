# Ansible Role: locale

This role configures the system-wide locale on **Debian-based systems** like Debian and Ubuntu. It installs necessary packages, generates the specified locale, sets it as the default, and can trigger a reboot to apply the changes.

## Requirements

* This role is designed **exclusively for Debian-based distributions** due to its use of `apt` and `dpkg-reconfigure`.
* The `community.general` Ansible collection must be installed (`ansible-galaxy collection install community.general`).
* By default, this role **will reboot the server** if the locale settings are changed. This behavior can be disabled.

## Role Variables

The following variables can be configured, with default values located in `defaults/main.yml`.

| Variable | Default Value | Description |
|---|---|---|
| `locale_packages` | `[ locales ]` | A list of system packages required for locale management. |
| `locale_name` | `"en_US.UTF-8"` | The locale to generate and set as the system default. |
| `locale_env` | `{ LANG: ..., LANGUAGE: ..., LC_ALL: ... }` | A dictionary of environment variables written to `/etc/default/locale`. |
| `locale_reboot` | `true` | If `true`, the machine will be rebooted if the locale is changed. Set to `false` to prevent this. |

## Dependencies

This role has no dependencies on other Ansible Galaxy roles.

## Example Playbook

### Example 1: Set locale to German and allow reboot

```yaml
- name: Configure German locale on servers
  hosts: app_servers
  become: true
  vars:
    locale_name: "de_DE.UTF-8"
    locale_env:
      LANG: "de_DE.UTF-8"
      LANGUAGE: "de_DE:de"
      LC_ALL: "de_DE.UTF-8"
  roles:
    - jonimofo.locale
```

### Example 2: Set locale without rebooting
```yaml
- name: Configure locale on critical server without rebooting
  hosts: database_servers
  become: true
  vars:
    locale_reboot: false
  roles:
    - jonimofo.locale
```

## License

MIT

## Author Information

This role was created by jonimofo.
