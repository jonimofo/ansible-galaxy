# Ansible Role: packages

Installs APT packages and manages system updates via a custom systemd timer on Debian-based systems. Optionally configures automatic security updates via `unattended-upgrades`.

## Features

- Installs a configurable list of packages
- Replaces default `apt-daily` services with a custom systemd timer
- Configurable update schedule
- Automatic cache cleanup and autoremove
- **Security:** Optional automatic security updates via `unattended-upgrades`

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

### Package Management

| Variable | Default | Description |
|----------|---------|-------------|
| `apt_update_packages_to_install` | `[]` | List of packages to install |
| `apt_update_cache_valid_time` | `3600` | Seconds before APT cache is considered stale |

### Custom Update Timer

| Variable | Default | Description |
|----------|---------|-------------|
| `apt_update_timer_on_calendar` | `'*-*-* 03:00:00'` | Systemd OnCalendar schedule for updates |
| `apt_update_timer_persistent` | `true` | Persist timer state across reboots |
| `apt_update_disable_units` | `[apt-daily.timer, ...]` | Default systemd units to disable/mask |
| `apt_update_service_dest` | `/etc/systemd/system/apt_update.service` | Path for custom service unit |
| `apt_update_timer_dest` | `/etc/systemd/system/apt_update.timer` | Path for custom timer unit |
| `apt_update_service_mode` | `'0644'` | File mode for service unit |
| `apt_update_timer_mode` | `'0644'` | File mode for timer unit |
| `apt_update_timer_unit` | `apt_update.timer` | Name of timer unit to enable |

### Security: Unattended Upgrades

| Variable | Default | Description |
|----------|---------|-------------|
| `apt_update_unattended_upgrades` | `false` | Enable automatic security updates |
| `apt_update_unattended_origins` | Debian security | Package origins to auto-upgrade |
| `apt_update_unattended_blacklist` | `[]` | Packages to never auto-upgrade |
| `apt_update_unattended_autofix` | `true` | Attempt to fix interrupted dpkg |
| `apt_update_unattended_remove_unused` | `true` | Auto-remove unused dependencies |
| `apt_update_unattended_reboot` | `false` | Auto-reboot if required (use with caution) |
| `apt_update_unattended_reboot_time` | `"02:00"` | Time to reboot if auto-reboot enabled |
| `apt_update_unattended_mail` | `""` | Email for upgrade notifications (empty = disabled) |
| `apt_update_unattended_mail_on_error` | `true` | Only send mail on errors |

## Dependencies

None.

## Example Playbook

### Basic Usage

```yaml
- name: Configure packages on servers
  hosts: all
  become: true
  vars:
    apt_update_packages_to_install:
      - curl
      - vim
      - git
      - htop
      - tmux
      - zsh
      - jq
    apt_update_timer_on_calendar: '*-*-* 04:00:00'
  roles:
    - role: jonimofo.infrastructure.packages
```

### With Automatic Security Updates (Recommended)

```yaml
- name: Configure packages with security updates
  hosts: all
  become: true
  vars:
    apt_update_packages_to_install:
      - curl
      - vim
      - git
      - ufw
      - fail2ban
    apt_update_unattended_upgrades: true
    apt_update_unattended_remove_unused: true
    apt_update_unattended_blacklist:
      - linux-image
      - linux-headers
  roles:
    - role: jonimofo.infrastructure.packages
```

### With Email Notifications

```yaml
- name: Configure packages with email alerts
  hosts: all
  become: true
  vars:
    apt_update_packages_to_install:
      - curl
      - mailutils
    apt_update_unattended_upgrades: true
    apt_update_unattended_mail: "admin@example.com"
    apt_update_unattended_mail_on_error: true
  roles:
    - role: jonimofo.infrastructure.packages
```

## Tags

- `packages` - All tasks
- `security` - Unattended-upgrades tasks only
- `unattended-upgrades` - Unattended-upgrades tasks only

Run only security tasks:
```bash
ansible-playbook playbook.yml --tags="security"
```

## Platform Notes

### Raspberry Pi OS

Raspberry Pi OS (based on Debian) is fully supported. The role works identically on:
- Raspberry Pi OS (32-bit, armv7l)
- Raspberry Pi OS (64-bit, aarch64)

All packages in Debian repositories are available. Some package names may differ between architectures (e.g., architecture-specific packages).

**Note:** Automatic reboots (`apt_update_unattended_reboot: true`) should be used with caution on headless Pi systems.

### Debian / Ubuntu

Standard Debian and Ubuntu installations are fully supported. The custom systemd timer replaces the default apt-daily services to give you control over update timing.

## Security Considerations

### Why Enable Unattended Upgrades?

- **Security patches are applied automatically** - Reduces window of vulnerability
- **No manual intervention required** - Critical for unattended servers
- **Configurable scope** - Only security updates by default

### Recommendations

1. **Enable unattended-upgrades** on all production systems
2. **Blacklist kernel packages** if you need to control reboot timing
3. **Enable email notifications** for visibility into updates
4. **Disable auto-reboot** unless you have proper monitoring

### What Gets Updated?

By default, only packages from security origins:
- `origin=Debian,codename=${distro_codename}-security`
- `origin=Debian,codename=${distro_codename}`

## What This Role Does

1. Verifies Debian-based system
2. Updates APT cache if stale
3. Installs specified packages
4. Runs `autoremove` and `autoclean`
5. Deploys custom `apt_update.service` and `apt_update.timer`
6. Enables and starts the custom timer
7. Disables and masks default `apt-daily*` units
8. (Optional) Configures `unattended-upgrades` for automatic security updates

## License

GPL-2.0-or-later

## Author Information

jonimofo
