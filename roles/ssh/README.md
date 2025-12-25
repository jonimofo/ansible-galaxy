# Ansible Role: ssh

Hardens OpenSSH server configuration and manages user access with public key authentication on Debian-based systems.

## Features

- Comprehensive SSH server hardening
- Configurable security settings (all options exposed as variables)
- Public key management with `AllowUsers` whitelist
- Optional exclusive key management (remove unmanaged keys)
- Automatic config validation before applying

## Requirements

- **Ansible version:** 2.12+
- **Collections:** `ansible.posix` (install with `ansible-galaxy collection install ansible.posix`)
- **Supported OS:** Debian-based systems only
  - Debian (bullseye, bookworm, trixie)
  - Ubuntu (focal, jammy, noble)
  - Raspberry Pi OS
- **Supported architectures:** x86_64, aarch64, armv7l
- **Privileges:** Requires `become: true`

## Role Variables

All variables are defined in `defaults/main.yml`:

### SSH Daemon Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ssh_port` | `22` | SSH daemon listening port |
| `ssh_permit_root_login` | `"no"` | Allow root login (`yes`, `no`, `prohibit-password`, `forced-commands-only`) |
| `ssh_password_authentication` | `false` | Allow password-based authentication |
| `ssh_permit_empty_passwords` | `false` | Allow empty passwords |
| `ssh_max_auth_tries` | `3` | Maximum authentication attempts per connection |
| `ssh_login_grace_time` | `60` | Seconds to authenticate before disconnect |
| `ssh_max_sessions` | `2` | Maximum sessions per network connection |

### Forwarding Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ssh_allow_agent_forwarding` | `false` | Allow SSH agent forwarding |
| `ssh_allow_tcp_forwarding` | `false` | Allow TCP port forwarding |
| `ssh_x11_forwarding` | `false` | Allow X11 forwarding |

### Client Keep-Alive

| Variable | Default | Description |
|----------|---------|-------------|
| `ssh_client_alive_interval` | `300` | Seconds before sending keep-alive to client |
| `ssh_client_alive_count_max` | `2` | Keep-alive messages before disconnect |

### User Access

| Variable | Default | Description |
|----------|---------|-------------|
| `ssh_users` | `[]` | List of users with SSH access (see below) |
| `ssh_exclusive_keys` | `true` | Remove unmanaged keys from authorized_keys |

### Additional Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ssh_strict_host_key_checking` | `"ask"` | Client StrictHostKeyChecking (`yes`, `no`, `ask`) |
| `ssh_print_motd` | `false` | Display /etc/motd on login |
| `ssh_print_last_log` | `true` | Display last login info |
| `ssh_use_dns` | `false` | DNS lookup for connecting hosts |
| `ssh_accept_env` | `"LANG LC_*"` | Environment variables to accept |

### ssh_users Structure

```yaml
ssh_users:
  - name: "alice"
    pubkey: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... alice@example.com"
  - name: "bob"
    pubkey: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQ... bob@workstation"
```

## Dependencies

- `ansible.posix` collection

## Example Playbook

### Basic Usage

```yaml
- name: Harden SSH and configure user access
  hosts: all
  become: true
  vars:
    ssh_users:
      - name: "admin"
        pubkey: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... admin@laptop"
  roles:
    - role: jonimofo.infrastructure.ssh
```

### High Security Configuration

```yaml
- name: Maximum SSH hardening
  hosts: production
  become: true
  vars:
    ssh_port: 2222
    ssh_permit_root_login: "no"
    ssh_password_authentication: false
    ssh_max_auth_tries: 2
    ssh_login_grace_time: 30
    ssh_max_sessions: 1
    ssh_allow_agent_forwarding: false
    ssh_allow_tcp_forwarding: false
    ssh_x11_forwarding: false
    ssh_client_alive_interval: 180
    ssh_client_alive_count_max: 2
    ssh_exclusive_keys: true
    ssh_users:
      - name: "deploy"
        pubkey: "ssh-ed25519 AAAAC3..."
  roles:
    - role: jonimofo.infrastructure.ssh
```

### Allow Root with Key Only

```yaml
- name: Allow root access with key only
  hosts: servers
  become: true
  vars:
    ssh_permit_root_login: "prohibit-password"
    ssh_users:
      - name: "root"
        pubkey: "ssh-ed25519 AAAAC3..."
      - name: "admin"
        pubkey: "ssh-ed25519 AAAAC3..."
  roles:
    - role: jonimofo.infrastructure.ssh
```

## Platform Notes

### Raspberry Pi OS

Raspberry Pi OS is fully supported. Considerations:

- **Headless setup:** Ensure you have SSH access configured before running (add `ssh` file to boot partition)
- **Default user:** The default `pi` user should be in `ssh_users` or you may lock yourself out
- **Port change:** If changing `ssh_port`, ensure your firewall allows the new port first

### Debian / Ubuntu

Standard Debian and Ubuntu installations are fully supported. The SSH service is named `ssh` on Debian-based systems (not `sshd`).

## Security Considerations

### Default Security Posture

This role applies secure defaults:

- **Password authentication disabled** - Keys only
- **Root login disabled** - Use sudo instead
- **Empty passwords disabled** - No weak auth
- **All forwarding disabled** - Reduced attack surface
- **Low auth tries** - Brute-force mitigation
- **Keep-alive enabled** - Detect dead connections
- **DNS lookup disabled** - Faster connections, no DNS leak

### Recommendations

1. **Always use Ed25519 keys** - Strongest and fastest
2. **Keep `ssh_exclusive_keys: true`** - Removes unauthorized keys (default)
3. **Change default port** - Reduces automated attacks (not security, obscurity)
4. **Use with fail2ban** - Ban repeated failures
5. **Use with ufw** - Firewall the SSH port

### Lockout Prevention

Before running this role:

1. Ensure your public key is in `ssh_users`
2. Test SSH key authentication manually first
3. Have console/physical access as backup
4. Consider keeping a session open while testing

### What This Role Hardens

| Setting | Value | Security Benefit |
|---------|-------|------------------|
| PasswordAuthentication | no | Prevents password brute-force |
| PermitRootLogin | no | Forces use of sudo, audit trail |
| PermitEmptyPasswords | no | No weak authentication |
| MaxAuthTries | 3 | Limits brute-force attempts |
| X11Forwarding | no | Reduces attack surface |
| AllowTcpForwarding | no | Prevents tunnel abuse |
| AllowAgentForwarding | no | Prevents key theft |
| UseDNS | no | Prevents DNS-based attacks |
| AllowUsers | (list) | Whitelist-only access |

## What This Role Does

1. Verifies Debian-based system
2. Configures `/etc/ssh/ssh_config` client settings
3. Hardens `/etc/ssh/sshd_config` with all security options
4. Validates config before applying (`sshd -t`)
5. Configures `AllowUsers` whitelist from `ssh_users`
6. Deploys public keys to user `authorized_keys`
7. Restarts SSH service to apply changes

## License

GPL-2.0-or-later

## Author Information

jonimofo
