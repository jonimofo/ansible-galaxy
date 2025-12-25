# Ansible Role: fail2ban

Installs and configures Fail2Ban to protect services from brute-force attacks on Debian-based systems.

## Features

- Secure-by-default configuration (1 hour ban, incremental bans)
- Recidive jail for repeat offenders (1 week ban)
- Per-jail customization (bantime, maxretry, findtime)
- UFW and iptables banaction support
- Incremental ban times (bans get longer each time)
- Easy jail configuration via dictionary

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

### Global Ban Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `fail2ban_bantime` | `3600` | Default ban duration in seconds (1 hour) |
| `fail2ban_findtime` | `600` | Time window to count failures (10 min) |
| `fail2ban_maxretry` | `3` | Failures before ban |
| `fail2ban_bantime_increment` | `true` | Enable incremental ban times |
| `fail2ban_bantime_factor` | `2` | Multiplier for incremental bans |
| `fail2ban_bantime_maxtime` | `604800` | Max ban time (1 week) |

### Network Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `fail2ban_backend` | `systemd` | Log backend (`systemd`, `auto`, `pyinotify`) |
| `fail2ban_allowipv6` | `false` | Enable IPv6 support |
| `fail2ban_ignoreip` | `['127.0.0.1/8']` | IPs/networks to never ban |
| `fail2ban_banaction` | `iptables-multiport` | Ban action (`ufw`, `iptables-multiport`) |

### Package Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `fail2ban_package` | `fail2ban` | APT package name |
| `fail2ban_service_name` | `fail2ban` | Systemd service name |
| `fail2ban_update_cache` | `true` | Update APT cache before install |
| `fail2ban_jail_local_path` | `/etc/fail2ban/jail.local` | Path to config file |

### Jails Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `fail2ban_jails` | sshd + recidive | Dictionary of jails |

#### Jail Options

| Option | Required | Description |
|--------|----------|-------------|
| `enabled` | Yes | Enable/disable jail |
| `port` | No | Port(s) to protect (e.g., `ssh`, `80,443`) |
| `filter` | No | Filter name (defaults to jail name) |
| `logpath` | No | Path to log file to monitor |
| `maxretry` | No | Override global maxretry |
| `bantime` | No | Override global bantime |
| `findtime` | No | Override global findtime |
| `action` | No | Custom action for this jail |
| `backend` | No | Override global backend |

## Dependencies

None.

## Example Playbook

### Basic Usage (defaults are secure)

```yaml
- name: Protect server with fail2ban
  hosts: all
  become: true
  vars:
    fail2ban_ignoreip:
      - 127.0.0.1/8
      - 192.168.1.0/24
  roles:
    - role: jonimofo.infrastructure.fail2ban
```

### With UFW Integration

```yaml
- name: Fail2ban with UFW
  hosts: all
  become: true
  vars:
    fail2ban_banaction: ufw
    fail2ban_ignoreip:
      - 127.0.0.1/8
      - 192.168.1.0/24
  roles:
    - role: jonimofo.infrastructure.fail2ban
```

### Custom SSH Port

```yaml
- name: Fail2ban for custom SSH port
  hosts: all
  become: true
  vars:
    fail2ban_ignoreip:
      - 127.0.0.1/8
    fail2ban_jails:
      sshd:
        enabled: true
        port: 2222
        filter: sshd
      recidive:
        enabled: true
        filter: recidive
        logpath: /var/log/fail2ban.log
        bantime: 604800
        findtime: 86400
        maxretry: 3
  roles:
    - role: jonimofo.infrastructure.fail2ban
```

### Web Server Protection

```yaml
- name: Protect web server
  hosts: webservers
  become: true
  vars:
    fail2ban_ignoreip:
      - 127.0.0.1/8
      - 10.0.0.0/8
    fail2ban_jails:
      sshd:
        enabled: true
        port: ssh
      recidive:
        enabled: true
        filter: recidive
        logpath: /var/log/fail2ban.log
        bantime: 604800
        findtime: 86400
        maxretry: 3
      nginx-http-auth:
        enabled: true
        port: http,https
        filter: nginx-http-auth
      nginx-botsearch:
        enabled: true
        port: http,https
        filter: nginx-botsearch
  roles:
    - role: jonimofo.infrastructure.fail2ban
```

## Platform Notes

### Raspberry Pi OS

Raspberry Pi OS is fully supported. Considerations:

- **Log location:** Uses systemd journal by default (`backend: systemd`)
- **Performance:** Fail2ban has minimal CPU impact on Pi

### Debian / Ubuntu

Standard Debian and Ubuntu installations are fully supported. The role uses the systemd backend by default.

## Security Considerations

### Default Security Posture

This role applies secure defaults:

- **1 hour initial ban** - Long enough to deter attackers
- **Incremental bans** - Repeat offenders get longer bans (up to 1 week)
- **Recidive jail** - Bans IPs that get banned 3 times for 1 week
- **Low retry limit** - Only 3 attempts before ban

### How Incremental Bans Work

With `fail2ban_bantime_increment: true`:

| Ban # | Duration |
|-------|----------|
| 1st | 1 hour |
| 2nd | 2 hours |
| 3rd | 4 hours |
| 4th | 8 hours |
| 5th+ | 1 week (max) |

### Recommendations

1. **Always whitelist your IP** - Add your IP/network to `fail2ban_ignoreip`
2. **Use with UFW** - Set `fail2ban_banaction: ufw` if using UFW
3. **Enable recidive jail** - Catches persistent attackers
4. **Monitor bans** - Check `/var/log/fail2ban.log` regularly

### Lockout Prevention

Before running this role:

1. Add your IP/network to `fail2ban_ignoreip`
2. Have console access as backup
3. Test with short bantime first if unsure

### Check Ban Status

```bash
# Show all jails status
sudo fail2ban-client status

# Show specific jail
sudo fail2ban-client status sshd

# Unban an IP
sudo fail2ban-client set sshd unbanip 1.2.3.4
```

## What This Role Does

1. Verifies Debian-based system
2. Installs fail2ban package
3. Deploys `jail.local` configuration from template
4. Configures global ban settings with incremental bans
5. Configures jails (sshd, recidive, custom)
6. Starts and enables fail2ban service

## License

GPL-2.0-or-later

## Author Information

jonimofo
