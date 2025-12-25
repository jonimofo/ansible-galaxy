# Ansible Role: host

Sets the system hostname and updates `/etc/hosts` on Debian-based systems.

## Features

- Sets transient and permanent hostname
- Updates `/etc/hosts` with proper Debian convention (127.0.1.1)
- Supports FQDN and short hostname
- Auto-derives short hostname from FQDN

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

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `host_hostname` | `""` | **Yes** | The hostname to set (FQDN or short) |
| `host_short_hostname` | (derived) | No | Short hostname for /etc/hosts |

If `host_short_hostname` is not set, it's automatically derived from `host_hostname` (part before first dot).

## Dependencies

None.

## Example Playbook

### Basic Usage

```yaml
- name: Configure hostname
  hosts: servers
  become: true
  vars:
    host_hostname: "webserver01.example.com"
  roles:
    - role: jonimofo.infrastructure.host
```

### With Explicit Short Hostname

```yaml
- name: Configure hostname with custom short name
  hosts: servers
  become: true
  vars:
    host_hostname: "webserver01.prod.example.com"
    host_short_hostname: "web01"
  roles:
    - role: jonimofo.infrastructure.host
```

### Short Hostname Only

```yaml
- name: Configure simple hostname
  hosts: raspberry_pis
  become: true
  vars:
    host_hostname: "piserver"
  roles:
    - role: jonimofo.infrastructure.host
```

## Platform Notes

### Raspberry Pi OS

Raspberry Pi OS is fully supported. The role follows Debian conventions:

- Sets hostname via `hostnamectl`
- Updates `/etc/hosts` with 127.0.1.1 mapping

**Note:** Raspberry Pi OS uses `raspberrypi` as default hostname. This role will change it.

### Debian / Ubuntu

Standard Debian and Ubuntu installations are fully supported. The role follows the Debian convention of mapping the hostname to `127.0.1.1` (not `127.0.0.1` which is reserved for `localhost`).

## What This Role Does

1. Verifies Debian-based system
2. Validates `host_hostname` is set
3. Derives short hostname if not provided
4. Sets hostname using `hostnamectl`
5. Updates `/etc/hosts`:
   ```
   127.0.1.1 webserver01.example.com webserver01
   ```

## Result

After running with `host_hostname: "server.example.com"`:

**`/etc/hostname`:**
```
server.example.com
```

**`/etc/hosts`:**
```
127.0.0.1 localhost
127.0.1.1 server.example.com server
```

## License

GPL-2.0-or-later

## Author Information

jonimofo
