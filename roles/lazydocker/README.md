# Ansible Role: lazydocker

Installs lazydocker, a terminal UI for Docker and Docker Compose.

## Features

- Downloads pre-compiled binary from GitHub releases
- Auto-detects CPU architecture (x86_64, aarch64, armv7l)
- Idempotent - skips download if binary exists
- Cleans up downloaded archive after installation

## Requirements

- **Ansible version:** 2.12+
- **Supported OS:** Debian-based systems only
  - Debian (bullseye, bookworm, trixie)
  - Ubuntu (focal, jammy, noble)
  - Raspberry Pi OS
- **Supported architectures:** x86_64, aarch64, armv7l
- **Privileges:** Requires `become: true`
- **Docker:** Must be installed separately (lazydocker requires Docker to be useful)

## Role Variables

All variables are defined in `defaults/main.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `lazydocker_version` | `0.24.1` | Version to install |
| `lazydocker_install_path` | `/usr/local/bin` | Binary installation path |
| `lazydocker_download_dir` | `/tmp` | Temp directory for download |
| `lazydocker_arch_map` | `{x86_64, aarch64, armv7l}` | Architecture mappings |

## Dependencies

None. However, Docker should be installed for lazydocker to be useful.

## Example Playbook

### Basic Usage

```yaml
- name: Install lazydocker
  hosts: all
  become: true
  roles:
    - role: jonimofo.infrastructure.lazydocker
```

### Specific Version

```yaml
- name: Install specific lazydocker version
  hosts: docker_hosts
  become: true
  vars:
    lazydocker_version: "0.23.0"
  roles:
    - role: jonimofo.infrastructure.lazydocker
```

### With Docker Role

```yaml
- name: Install Docker and lazydocker
  hosts: all
  become: true
  roles:
    - role: geerlingguy.docker
    - role: jonimofo.infrastructure.lazydocker
```

## What This Role Does

1. Verifies Debian-based system
2. Verifies supported architecture
3. Constructs download URL based on version and architecture
4. Downloads lazydocker tarball from GitHub releases
5. Extracts binary to installation path
6. Sets executable permissions
7. Cleans up downloaded archive

## Usage

After installation, run:

```bash
lazydocker
```

Key bindings:
- `?` - Show help
- `q` - Quit
- `↑/↓` - Navigate
- `Enter` - Select
- `d` - Remove container
- `s` - Stop container

## License

GPL-2.0-or-later

## Author Information

jonimofo
