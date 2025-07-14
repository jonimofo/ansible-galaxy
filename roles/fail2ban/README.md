# Ansible Role: fail2ban

Installs and configures Fail2Ban, a service that scans log files and bans IPs that show malicious signs such as too many password failures or seeking for exploits.

## Requirements

There are no special requirements for this role.

## Role Variables

All configurable parameters are available in `defaults/main.yml`.

| Variable | Default Value | Description |
|---|---|---|
| `fail2ban_backend` | `systemd` | The default backend for jail monitoring (e.g., `auto`, `systemd`, `pyinotify`). |
| `fail2ban_bantime` | `600` | The ban time in seconds. |
| `fail2ban_findtime` | `600` | The time window (seconds) to check for failures. |
| `fail2ban_maxretry` | `3` | Number of failures before a host is banned. |
| `fail2ban_ignoreip` | `[ '127.0.0.1/8', '192.168.1.0/24' ]` | A list of IPs, CIDR masks, or DNS hosts to ignore. |
| `fail2ban_jail_local_path` | `/etc/fail2ban/jail.local` | The path to the main Fail2Ban configuration file. |
| `fail2ban_package` | `fail2ban` | The name of the Fail2Ban package to install. |
| `fail2ban_service_name` | `fail2ban` | The name of the Fail2Ban service. |
| `fail2ban_update_cache` | `true` | Whether to update the package manager cache before installation. |

The `fail2ban_jails` variable is a dictionary used to define the state of each jail. You can add or override jails by defining this variable.

**Default `fail2ban_jails` structure:**
```yaml
fail2ban_jails:
  sshd:
    enabled: true
    port: ssh
    filter: sshd
```

## Dependencies

This role has no dependencies on other Ansible Galaxy roles.

## Example Playbook

Here is an example of how to use this role. You can override the default variables to customize the installation.

```yaml
- name: Harden servers with Fail2Ban
  hosts: webservers
  become: true
  vars:
    fail2ban_bantime: 1800 # Ban for 30 minutes
    fail2ban_jails:
      sshd:
        enabled: true
        port: 2222
      nginx-http-auth:
        enabled: true
      nginx-botsearch:
        enabled: true
  roles:
    - jonimofo.fail2ban
```

## License

MIT

## Author Information

This role was created by jonimofo.