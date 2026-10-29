# Ansible Role: packages

Installs APT packages and manages nightly updates via a custom systemd timer on Debian-based systems. By default the nightly run applies security patches only, through `unattended-upgrades`.

## Features

- Installs a configurable list of packages
- Removes leftovers of tools once installed outside apt (fasd)
- Replaces the stock `apt-daily` timers with one timer at a fixed time
- Nightly security patches via `unattended-upgrades` (default), or a full upgrade
- `needrestart` in automatic mode so patched services are restarted
- Opt-in `autoremove` and `autoclean`

## Requirements

- **Ansible version:** 2.15+
- **Supported OS:** Debian-based systems only
  - Debian (bookworm, trixie)
  - Ubuntu (jammy, noble, resolute)
- **Supported architectures:** x86_64, aarch64
- **Privileges:** Requires `become: true`

## Role Variables

All variables are defined in `defaults/main.yml`:

### Packages

| Variable | Default | Description |
|----------|---------|-------------|
| `packages_apt_update_packages_to_install` | `[]` | List of packages to install |
| `packages_obsolete_paths` | fasd binary and man page | Files to remove, left by tools once installed outside apt |
| `packages_apt_cache_valid_time` | `3600` | Seconds the apt cache stays valid before the install task refreshes it |
| `packages_run_cleanup` | `false` | Run `autoremove` and `autoclean` (opt-in, `-e packages_run_cleanup=true`) |
| `packages_needrestart_install` | `true` | Install `needrestart` in automatic restart mode |

### Nightly Update Timer

| Variable | Default | Description |
|----------|---------|-------------|
| `packages_apt_update_timer_on_calendar` | `'*-*-* 03:00:00'` | Systemd OnCalendar schedule |
| `packages_apt_update_timer_persistent` | `true` | Run at next boot if the time was missed |
| `packages_apt_update_timer_randomized_delay_sec` | `"15m"` | Random delay per run, spreads a fleet over the mirror |
| `packages_apt_update_service_timeout_stop_sec` | `900` | Seconds systemd waits on stop, so dpkg is not killed mid-upgrade |
| `packages_apt_update_disable_units` | `[apt-daily.timer, ...]` | Stock units to disable and mask |
| `packages_apt_update_service_dest` | `/etc/systemd/system/apt_update.service` | Path of the service unit |
| `packages_apt_update_timer_dest` | `/etc/systemd/system/apt_update.timer` | Path of the timer unit |
| `packages_apt_update_service_mode` | `'0644'` | File mode of the service unit |
| `packages_apt_update_timer_mode` | `'0644'` | File mode of the timer unit |
| `packages_apt_update_timer_unit` | `apt_update.timer` | Name of the timer unit |

What the nightly service runs depends on `packages_apt_update_unattended_upgrades`:

| Value | Nightly command |
|-------|-----------------|
| **true** (default) | `apt-get update && unattended-upgrade && apt-get autoremove -y && apt-get autoclean` |
| **false** | `apt-get update && apt-get full-upgrade -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold && apt-get autoremove -y && apt-get autoclean` |

The full-upgrade path keeps the local version of a modified config file and takes the package default otherwise, so a conffile prompt never blocks the run. The service uses `KillMode=process` and `TimeoutStopSec`, like the stock `apt-daily-upgrade.service`: stopping it, at shutdown for example, does not kill dpkg mid-upgrade. The timer adds a random delay of up to `packages_apt_update_timer_randomized_delay_sec`.

### Security: Unattended Upgrades

| Variable | Default | Description |
|----------|---------|-------------|
| `packages_apt_update_unattended_upgrades` | `true` | Install and configure `unattended-upgrades` |
| `packages_apt_update_unattended_origins` | per distribution | `Origins-Pattern` entries, picked from `packages_apt_update_unattended_origins_map` by `ansible_distribution` |
| `packages_apt_update_unattended_origins_map` | Debian-Security / Ubuntu security | Default origins per distribution |
| `packages_apt_update_unattended_blacklist` | `[]` | Packages to never auto-upgrade (e.g. `docker-ce`) |
| `packages_apt_update_unattended_autofix` | `true` | Attempt to fix interrupted dpkg |
| `packages_apt_update_unattended_remove_unused` | `true` | Auto-remove unused dependencies and kernels |
| `packages_apt_update_unattended_reboot` | `false` | Auto-reboot if required (use with caution) |
| `packages_apt_update_unattended_reboot_time` | `"03:30"` | Time to reboot if auto-reboot enabled, after the 03:00 run |
| `packages_apt_update_unattended_mail` | `""` | Email for upgrade notifications (empty = disabled) |
| `packages_apt_update_unattended_mail_on_error` | `true` | Only send mail on errors |

## Dependencies

None.

## Example Playbook

### Server (security patches nightly, default)

```yaml
- name: Configure packages on servers
  hosts: all
  become: true
  vars:
    packages_apt_update_packages_to_install:
      - curl
      - vim
      - git
      - ufw
      - fail2ban
      - zoxide
    packages_apt_update_unattended_blacklist:
      - docker-ce
  roles:
    - role: jonimofo.infrastructure.packages
```

### Laptop (full upgrade nightly)

```yaml
- name: Configure packages on a laptop
  hosts: laptops
  become: true
  vars:
    packages_apt_update_unattended_upgrades: false
    packages_apt_update_timer_on_calendar: '*-*-* 12:00:00'
  roles:
    - role: jonimofo.infrastructure.packages
```

### With Email Notifications

```yaml
- name: Configure packages with email alerts
  hosts: all
  become: true
  vars:
    packages_apt_update_packages_to_install:
      - mailutils
    packages_apt_update_unattended_mail: "admin@example.com"
  roles:
    - role: jonimofo.infrastructure.packages
```

## Tags

- `packages` - All tasks
- `security` - Unattended-upgrades tasks only
- `unattended-upgrades` - Unattended-upgrades tasks only

## Good Practices

1. Keep the nightly run on security patches (the default) for servers. Run full upgrades yourself, from Ansible, in a window you chose.
2. Decide the reboot policy. A security kernel update leaves `/var/run/reboot-required`; nothing reboots unless `packages_apt_update_unattended_reboot` is set.
3. Blacklist packages managed elsewhere (`docker-ce`) if you do not want them restarted at night.
4. Watch `/var/log/unattended-upgrades/` or set `packages_apt_update_unattended_mail`.

## What This Role Does

1. Verifies Debian-based system
2. Installs the listed packages and removes obsolete fasd files
3. (Opt-in) Runs `autoremove` and `autoclean`
4. Installs and configures `needrestart` in automatic mode
5. Deploys `apt_update.service` and `apt_update.timer`, enables the timer and restarts it when its schedule changes
6. Disables and masks the stock `apt-daily*` units, removes a `20auto-upgrades` left by an older version of this role and leaves a stock one untouched
7. Installs and configures `unattended-upgrades` (or disables it when turned off)

## License

GPL-2.0-or-later

## Author Information

jonimofo
