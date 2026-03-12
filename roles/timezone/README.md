# Ansible Role: timezone

Configures the system timezone on Debian-based systems.

## Features

- Sets the system timezone using `timedatectl` (via `community.general.timezone`)
- Configures `/etc/timezone` and `/etc/localtime` symlink

## Requirements

- **Ansible version:** 2.12+
- **Collections:** `community.general` (for `timezone` module)
- **Supported OS:** Debian-based systems only
  - Debian (bullseye, bookworm, trixie)
  - Ubuntu (focal, jammy, noble)
  - Raspberry Pi OS
- **Supported architectures:** x86_64, aarch64, armv7l
- **Privileges:** Requires `become: true`

## Role Variables

All variables are defined in `defaults/main.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `timezone_name` | `"Asia/Ho_Chi_Minh"` | IANA timezone identifier |

## Dependencies

None.

## Example Playbook

### Basic Usage (Default: Asia/Ho_Chi_Minh)

```yaml
- name: Configure timezone
  hosts: all
  become: true
  roles:
    - role: jonimofo.infrastructure.timezone
```

### Custom Timezone

```yaml
- name: Configure UTC timezone
  hosts: all
  become: true
  vars:
    timezone_name: "UTC"
  roles:
    - role: jonimofo.infrastructure.timezone
```

## License

GPL-2.0-or-later

## Author Information

jonimofo
