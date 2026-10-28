# Ansible Role: ssh

Hardens the OpenSSH server through a drop-in in `/etc/ssh/sshd_config.d/`, manages `authorized_keys` and `AllowUsers`, and verifies the server is still reachable afterwards.

## Features

- Hardening written to `/etc/ssh/sshd_config.d/00-ansible.conf`: sorted first, so it wins over the stock `sshd_config` and over cloud-init's `50-cloud-init.conf`, while distro defaults stay in place
- `authorized_keys` per user, exclusive by default, from inline keys, `.pub` files, or a keys directory
- Public keys validated on the control node before anything is written
- `AllowUsers` restricted to the managed users
- Config validated with `sshd -t` before it is written, sshd reloaded (not restarted), then the SSH port is checked from the control node

## Requirements

- **Ansible version:** 2.15+
- **Collections:** `ansible.posix` (for `authorized_key`)
- **Supported OS:** Debian-based systems (the `Include /etc/ssh/sshd_config.d/*.conf` line is added to `sshd_config` if missing)
  - Debian (bookworm, trixie)
  - Ubuntu (jammy, noble, resolute)
- **Supported architectures:** x86_64, aarch64
- **Privileges:** Requires `become: true`

## Role Variables

All variables are defined in `defaults/main.yml`:

### Where the hardening lands

| Variable | Default | Description |
|----------|---------|-------------|
| `ssh_dropin_name` | `00-ansible.conf` | Drop-in file name in `/etc/ssh/sshd_config.d` |
| `ssh_service_name` | `ssh` | Service to reload |
| `ssh_verify_port` | `true` | After the reload, check `ssh_port` answers, then reset the connection and open a new session |
| `ssh_verify_timeout` | `10` | Seconds to wait for `ssh_port` in that check |

### SSH Daemon Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ssh_port` | `22` | SSH daemon listening port |
| `ssh_permit_root_login` | `"no"` | Allow root login (`yes`, `no`, `prohibit-password`, `forced-commands-only`) |
| `ssh_pubkey_authentication` | `true` | Allow public key authentication |
| `ssh_password_authentication` | `false` | Allow password-based authentication |
| `ssh_permit_empty_passwords` | `false` | Allow empty passwords |
| `ssh_max_auth_tries` | `3` | Maximum authentication attempts per connection |
| `ssh_login_grace_time` | `60` | Seconds to authenticate before disconnect |
| `ssh_max_sessions` | `2` | Maximum sessions per network connection |

### Forwarding Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ssh_allow_agent_forwarding` | `false` | Allow SSH agent forwarding (the `dotfiles` role needs it) |
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
| `ssh_users` | `[]` | Users allowed to SSH with their public keys (see below) |
| `ssh_public_keys_dir` | `""` | Directory on the control node with one `<name>.pub` per user without `pubkey`/`pubkey_file` |
| `ssh_exclusive_keys` | `true` | Remove unmanaged keys from `authorized_keys` |

### Additional Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ssh_strict_host_key_checking` | `"ask"` | Client `StrictHostKeyChecking` in `/etc/ssh/ssh_config` (`yes`, `no`, `ask`) |
| `ssh_print_motd` | `false` | Display /etc/motd on login |
| `ssh_print_last_log` | `true` | Display last login info |
| `ssh_use_dns` | `false` | DNS lookup for connecting hosts |
| `ssh_accept_env` | `"LANG LC_*"` | Environment variables to accept |

### ssh_users Structure

Each entry needs `name` and one key source, resolved in this order:

| Key | Description |
|-----|-------------|
| **pubkey** | Inline public key, one or several lines |
| **pubkey_file** | Path on the control node to a `.pub` file |
| (none) | `<ssh_public_keys_dir>/<name>.pub`, when `ssh_public_keys_dir` is set |

Keys are checked before anything is written: non-empty, not the `REPLACE_WITH_REAL_PUBLIC_KEY` placeholder, and starting with a known key type.

## Dependencies

None.

## Example Playbook

### Inline keys

```yaml
- name: Harden SSH
  hosts: all
  become: true
  vars:
    ssh_allow_agent_forwarding: true
    ssh_users:
      - name: "admin"
        pubkey: "ssh-ed25519 AAAA... admin@laptop"
  roles:
    - role: jonimofo.infrastructure.ssh
```

### Keys from a per-inventory directory

```yaml
- name: Harden SSH with project keys
  hosts: all
  become: true
  vars:
    ssh_public_keys_dir: "{{ inventory_dir }}/files/ssh"   # admin.pub, deploy.pub
    ssh_users:
      - name: "admin"
      - name: "deploy"
  roles:
    - role: jonimofo.infrastructure.ssh
```

### Custom port

```yaml
- name: SSH on port 2222
  hosts: all
  become: true
  vars:
    ssh_port: 2222
    ufw_verify_port: 2222   # if you also use the ufw role
    ssh_users:
      - name: "admin"
        pubkey_file: "files/admin.pub"
  roles:
    - role: jonimofo.infrastructure.ssh
```

## Security Considerations

### Lockout Prevention

1. Keys are validated on the control node before `authorized_keys` is touched.
2. The drop-in is validated with `sshd -t` before it is written.
3. Before writing, the role asserts that the user Ansible connects as is in `ssh_users` (and that root login stays allowed when connecting as root).
4. sshd is reloaded immediately (handlers are flushed), `ssh_port` is checked from the control node, then the persistent connection is reset and a new session is opened. A failed login fails the play.
5. With `ssh_exclusive_keys: true`, any key not in `ssh_users` is removed. Make sure the key you connect with is listed.
6. Changing `ssh_port` also needs a firewall rule; with the `ufw` role set `ufw_verify_port` to the same value.

### Why a drop-in

Debian 12+ and Ubuntu 22.04+ ship `sshd_config` with `Include /etc/ssh/sshd_config.d/*.conf` at the top, and sshd keeps the first value it reads. Cloud images add `50-cloud-init.conf` there with `PasswordAuthentication yes`. A `00-` drop-in is read before both, so it wins without rewriting the stock file.

## What This Role Does

1. Verifies Debian-based system
2. Resolves and validates each user's public key on the control node
3. Writes `authorized_keys` (exclusive by default)
4. Ensures `sshd_config` includes `sshd_config.d` (added at the top if a previous tool removed it), asserts the connecting user stays allowed, deploys the validated hardening drop-in
5. Sets `StrictHostKeyChecking` in the client `ssh_config`
6. Reloads sshd now, verifies `ssh_port` from the control node, resets the connection and opens a new session

## License

GPL-2.0-or-later

## Author Information

jonimofo
