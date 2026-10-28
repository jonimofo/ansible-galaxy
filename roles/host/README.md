# Ansible Role: host

Sets the hostname, keeps `/etc/hosts` and `/tmp` sane, and optionally manages DNS servers through netplan and systemd-resolved.

## Features

- Sets the system hostname and the `127.0.1.1` line of `/etc/hosts`
- Enforces `1777` on `/tmp` (SSH agent forwarding sockets live there)
- Primary DNS servers per interface via a netplan override, when netplan is installed
- Backup and fallback DNS servers via a systemd-resolved drop-in, when systemd-resolved is installed
- Netplan config validated with `netplan generate` before `netplan apply`

## Requirements

- **Ansible version:** 2.15+
- **Supported OS:** Debian-based systems only
  - Debian (bookworm, trixie)
  - Ubuntu (jammy, noble, resolute)
- **Supported architectures:** x86_64, aarch64
- **Privileges:** Requires `become: true`

## Role Variables

All variables are defined in `defaults/main.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `host_hostname` | `inventory_hostname` | The hostname to set (FQDN or short) |
| `host_short_hostname` | (derived) | Short hostname for `/etc/hosts`, part before the first dot by default |
| `host_dns_file_prefix` | `ansible` | Prefix of the files written: `/etc/netplan/99-<prefix>-dns.yaml`, `/etc/systemd/resolved.conf.d/10-<prefix>-dns.conf` |
| `host_dns_servers` | `[]` | Primary DNS servers set on `host_dns_interface` via netplan. Empty leaves netplan untouched |
| `host_dns_interface` | default-route interface | Interface carrying the primary DNS servers |
| `host_dns_manage_resolved` | `true` | Write the systemd-resolved drop-in (backup and fallback servers) |
| `host_dns_backup_servers` | `[8.8.8.8, 8.8.4.4]` | Servers queried when the primaries are unreachable |
| `host_dns_fallback_servers` | `[1.1.1.1, 1.0.0.1]` | Last-resort servers, used only if nothing else is configured |

## Dependencies

None.

## Example Playbook

### Hostname only

```yaml
- name: Configure host
  hosts: all
  become: true
  vars:
    host_hostname: "server.example.com"
  roles:
    - role: jonimofo.infrastructure.host
```

### With an internal DNS server (Ubuntu, netplan)

```yaml
- name: Configure host with internal DNS
  hosts: all
  become: true
  vars:
    host_dns_file_prefix: "acme"
    host_dns_servers:
      - 10.33.0.26
  roles:
    - role: jonimofo.infrastructure.host
```

## Platform Notes

- **Ubuntu** ships netplan and systemd-resolved: both DNS parts apply.
- **Debian** usually has neither: the resolved part is skipped, and the role fails if `host_dns_servers` is set without netplan. Install `netplan.io` and `systemd-resolved` to opt in.
- Netplan concatenates `nameservers` across files instead of overriding them, so the role removes the `nameservers` block from every other netplan file before writing its own override.
- If you rename `host_dns_file_prefix` on a host that already has an override, delete the old `99-<old>-dns.yaml` and `10-<old>-dns.conf` first.

## What This Role Does

1. Verifies Debian-based system and that `host_hostname` is set
2. Enforces `1777` on `/tmp`
3. Sets the hostname and the `127.0.1.1` line in `/etc/hosts`
4. Detects netplan and systemd-resolved
5. (netplan present, `host_dns_servers` set) strips legacy `nameservers`, writes the override, validates and applies netplan
6. (systemd-resolved present) writes the backup/fallback drop-in and restarts systemd-resolved

## License

GPL-2.0-or-later

## Author Information

jonimofo
