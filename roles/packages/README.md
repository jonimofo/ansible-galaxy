# Ansible Role: packages

This role performs two main functions on **Debian-based systems** (like Debian and Ubuntu):
1.  Installs a list of specified packages.
2.  Disables the default `apt-daily` services and timers and replaces them with a custom, configurable systemd timer to handle daily `apt-get update` operations.

## Requirements

This role is designed **exclusively for Debian-based distributions** due to its use of `apt` and its focus on managing `apt-daily` systemd units.

## Role Variables

The following variables can be configured, with default values located in `defaults/main.yml`.

| Variable | Default Value | Description |
|---|---|---|
| `apt_update_packages_to_install` | `[]` | **The main variable.** A list of packages to install. |
| `apt_update_cache_valid_time` | `3600` | Time in seconds before the APT cache is considered stale. |
| `apt_update_timer_on_calendar` | `'*-*-* 03:00:00'` | The `OnCalendar` schedule for the custom APT update timer. |
| `apt_update_timer_persistent` | `true` | Makes the last run time of the timer persistent across reboots. |
| `apt_update_disable_units` | `[ apt-daily... ]` | A list of default systemd units to disable and mask. |
| `apt_update_service_dest` | `/etc/systemd/system/apt_update.service` | Destination path for the custom service unit file. |
| `apt_update_timer_dest` | `/etc/systemd/system/apt_update.timer` | Destination path for the custom timer unit file. |

## Dependencies

This role has no dependencies on other Ansible Galaxy roles.

## Example Playbook

Here is an example of how to use this role to install a set of common utilities.

```yaml
- name: Install common packages on servers
  hosts: all
  become: true
  vars:
    apt_update_packages_to_install:
      - curl
      - vim
      - git
      - htop
      - ufw
  roles:
    - jonimofo.packages
```

## License

MIT

## Author Information

This role was created by jonimofo.