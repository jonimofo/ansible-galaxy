# Ansible Role: users

Creates system users and configures sudo privileges on Debian-based systems.

## Features

- Create users with configurable shell, groups, and home directory
- Configurable passwordless sudo (optional)
- Disable `su` command for sudo group (audit trail)
- Support for service accounts (nologin shell, no home)
- Sudoers validation before applying

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

### User Defaults

| Variable | Default | Description |
|----------|---------|-------------|
| `users_default_shell` | `/bin/bash` | Default shell for new users |
| `users_default_create_home` | `true` | Create home directory by default |

### Sudo Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `users_passwordless_sudo` | `true` | Enable passwordless sudo for sudo group |
| `users_disable_su` | `true` | Disable `su` for sudo group members |
| `users_lock_root` | `true` | Lock root account (no password login) |

### User List

| Variable | Default | Description |
|----------|---------|-------------|
| `users_list` | `[]` | List of users to create |

#### User Options

| Option | Required | Description |
|--------|----------|-------------|
| `name` | Yes | Username |
| `groups` | No | Comma-separated groups (e.g., `"sudo,docker"`) |
| `shell` | No | Login shell (defaults to `users_default_shell`) |
| `create_home` | No | Create home directory (defaults to `users_default_create_home`) |
| `comment` | No | User description/GECOS field |
| `uid` | No | Specific UID |

## Dependencies

None.

## Example Playbook

### Basic Usage

```yaml
- name: Create users
  hosts: all
  become: true
  vars:
    users_list:
      - name: "admin"
        groups: "sudo"
      - name: "developer"
        groups: "sudo,docker"
  roles:
    - role: jonimofo.infrastructure.users
```

### With Password-Required Sudo (More Secure)

```yaml
- name: Create users with password-required sudo
  hosts: production
  become: true
  vars:
    users_passwordless_sudo: false
    users_list:
      - name: "admin"
        groups: "sudo"
  roles:
    - role: jonimofo.infrastructure.users
```

### Service Account

```yaml
- name: Create service account
  hosts: all
  become: true
  vars:
    users_list:
      - name: "app_service"
        shell: "/usr/sbin/nologin"
        create_home: false
        comment: "Application service account"
  roles:
    - role: jonimofo.infrastructure.users
```

### Multiple Users with Different Configs

```yaml
- name: Create multiple users
  hosts: all
  become: true
  vars:
    users_list:
      - name: "sysadmin"
        groups: "sudo,adm"
        shell: "/bin/bash"
        comment: "System Administrator"
      - name: "developer"
        groups: "sudo,docker,www-data"
        shell: "/bin/zsh"
      - name: "backup"
        shell: "/usr/sbin/nologin"
        create_home: false
        uid: 900
  roles:
    - role: jonimofo.infrastructure.users
```

## Platform Notes

### Raspberry Pi OS

Raspberry Pi OS is fully supported. Considerations:

- **Default user:** The `pi` user is not modified by this role
- **Groups:** Common groups: `sudo`, `gpio`, `i2c`, `spi`
- **Cleanup:** Removes override files that bypass sudo configuration:
  - `/etc/sudoers.d/010_pi-nopasswd`
  - `/etc/sudoers.d/90-cloud-init-users`

### Debian / Ubuntu

Standard Debian and Ubuntu installations are fully supported. Common groups:
- `sudo` - Administrative privileges
- `docker` - Docker access
- `www-data` - Web server
- `adm` - Log access

## Security Considerations

### Passwordless Sudo

By default, `users_passwordless_sudo: true` enables passwordless sudo. This is convenient but has security implications:

| Setting | Behavior | Use Case |
|---------|----------|----------|
| `true` | No password for sudo | Development, automation |
| `false` | Password required | Production, shared servers |

### Disable `su`

By default, `users_disable_su: true` prevents sudo group members from using `su`. This:

- Forces use of `sudo` for privilege escalation
- Maintains audit trail in logs
- Prevents direct root shell access

### Lock Root Account

By default, `users_lock_root: true` locks the root account. This:

- Blocks `sudo passwd root` via sudoers (prevents unlocking)
- Locks the root password in `/etc/shadow`
- Blocks direct root login via console or SSH
- Root shell still accessible via `sudo -i` (maintains audit trail)

### Sudoers Result

With defaults (`users_passwordless_sudo: true`, `users_disable_su: true`, `users_lock_root: true`):
```
%sudo ALL=(ALL) NOPASSWD: ALL, !/bin/su, !/usr/bin/su, !/usr/bin/passwd root
```

With `users_passwordless_sudo: false`:
```
%sudo ALL=(ALL) ALL, !/bin/su, !/usr/bin/su, !/usr/bin/passwd root
```

### Recommendations

1. **Production servers:** Set `users_passwordless_sudo: false`
2. **Keep `users_disable_su: true`** - Maintains audit trail
3. **Keep `users_lock_root: true`** - Prevents root password attacks
4. **Use service accounts** for applications (nologin shell)
5. **Limit sudo group** - Only add users who need it

## What This Role Does

1. Verifies Debian-based system
2. Creates users from `users_list`
3. Configures sudo group in `/etc/sudoers`:
   - Passwordless sudo (optional)
   - Disable `su` command (optional)
4. Validates sudoers before applying
5. Removes sudoers.d override files (Pi OS, cloud-init)
6. Locks root account (optional, enabled by default)

## License

GPL-2.0-or-later

## Author Information

jonimofo
