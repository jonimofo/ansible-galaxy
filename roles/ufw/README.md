# Ansible Role: ufw

Installs and configures the Uncomplicated Firewall (UFW) on Debian-based systems with secure defaults.

## Features

- Secure-by-default configuration (deny incoming, allow outgoing)
- Flexible rule definitions with source IP and interface support
- Rate limiting support for brute-force protection
- Application profile support (OpenSSH, etc.)
- IPv6 support (optional)
- Configurable logging levels
- **Docker integration** - Manage DOCKER-USER chain to control container access

## Requirements

- **Ansible version:** 2.12+
- **Collections:** `community.general` (install with `ansible-galaxy collection install community.general`)
- **Supported OS:** Debian-based systems only
  - Debian (bullseye, bookworm, trixie)
  - Ubuntu (focal, jammy, noble)
  - Raspberry Pi OS
- **Supported architectures:** x86_64, aarch64, armv7l
- **Privileges:** Requires `become: true`

## Role Variables

All variables are defined in `defaults/main.yml`:

### UFW State

| Variable | Default | Description |
|----------|---------|-------------|
| `ufw_state` | `enabled` | Final UFW state (`enabled`, `disabled`, `reset`) |
| `ufw_reset_before_configure` | `false` | Reset UFW before applying rules (wipes all rules!) |
| `ufw_logging` | `"on"` | Logging level (`on`, `off`, `low`, `medium`, `high`, `full`) |

### Network Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ufw_enable_ipv6` | `false` | Enable IPv6 support |

### Package Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ufw_pkg_name` | `ufw` | APT package name |
| `ufw_update_cache` | `true` | Update APT cache before install |
| `ufw_config_path` | `/etc/default/ufw` | Path to UFW config file |

### Default Policies

| Variable | Default | Description |
|----------|---------|-------------|
| `ufw_default_policies` | deny incoming, allow outgoing | Default traffic policies |

```yaml
ufw_default_policies:
  - direction: incoming
    policy: deny
  - direction: outgoing
    policy: allow
```

### Firewall Rules

| Variable | Default | Description |
|----------|---------|-------------|
| `ufw_rules` | `[]` | List of firewall rules |

#### Rule Options

| Option | Required | Description |
|--------|----------|-------------|
| `rule` | Yes | Rule type: `allow`, `deny`, `reject`, `limit` |
| `port` | No | Port number (e.g., `22`, `80`, `443`) |
| `proto` | No | Protocol: `tcp`, `udp`, `any` |
| `name` | No | Application profile (e.g., `OpenSSH`) |
| `from_ip` | No | Source IP/CIDR (e.g., `192.168.1.0/24`) |
| `to_ip` | No | Destination IP/CIDR |
| `interface` | No | Network interface (e.g., `eth0`) |
| `direction` | No | Direction for interface rules: `in`, `out` |
| `comment` | No | Rule description |

### Docker Integration

Docker bypasses UFW by manipulating iptables directly. This role can manage the `DOCKER-USER` chain to restrict external access to Docker containers while allowing LAN access.

| Variable | Default | Description |
|----------|---------|-------------|
| `ufw_docker_integration` | `false` | Enable Docker integration |
| `ufw_docker_allowed_ports` | `[80/tcp, 443/tcp, 443/udp]` | Ports accessible from internet |
| `ufw_docker_private_networks` | `[172.16.0.0/12, 192.168.0.0/16]` | Networks always allowed |

**Important:** Run this role AFTER Docker is installed for the `DOCKER-USER` chain to exist.

## Dependencies

- `community.general` collection

## Example Playbook

### Basic Web Server

```yaml
- name: Configure firewall for web server
  hosts: webservers
  become: true
  vars:
    ufw_rules:
      - rule: limit
        port: 22
        proto: tcp
        comment: "Rate limit SSH"
      - rule: allow
        port: 80
        proto: tcp
        comment: "Allow HTTP"
      - rule: allow
        port: 443
        proto: tcp
        comment: "Allow HTTPS"
  roles:
    - role: jonimofo.infrastructure.ufw
```

### SSH from Trusted Network Only

```yaml
- name: Restrict SSH to local network
  hosts: servers
  become: true
  vars:
    ufw_rules:
      - rule: allow
        port: 22
        proto: tcp
        from_ip: "192.168.1.0/24"
        comment: "SSH from local network only"
      - rule: deny
        port: 22
        proto: tcp
        comment: "Deny SSH from everywhere else"
  roles:
    - role: jonimofo.infrastructure.ufw
```

### Interface-Specific Rules

```yaml
- name: Configure multi-interface firewall
  hosts: servers
  become: true
  vars:
    ufw_rules:
      - rule: allow
        port: 80
        proto: tcp
        interface: eth0
        direction: in
        comment: "HTTP on public interface"
      - rule: allow
        port: 3306
        proto: tcp
        interface: eth1
        direction: in
        from_ip: "10.0.0.0/8"
        comment: "MySQL on private interface"
  roles:
    - role: jonimofo.infrastructure.ufw
```

### Fresh Setup with Reset

```yaml
- name: Fresh firewall setup
  hosts: new_servers
  become: true
  vars:
    ufw_reset_before_configure: true  # Wipe existing rules
    ufw_rules:
      - rule: allow
        name: "OpenSSH"
        comment: "Allow SSH"
  roles:
    - role: jonimofo.infrastructure.ufw
```

### Docker Server with Traefik

```yaml
- name: Configure Docker server with UFW
  hosts: docker_servers
  become: true
  vars:
    ufw_rules:
      - rule: limit
        port: 22
        proto: tcp
        comment: "Rate limit SSH"
    ufw_docker_integration: true
    ufw_docker_allowed_ports:
      - { port: 80, proto: tcp }
      - { port: 443, proto: tcp }
      - { port: 443, proto: udp }
  roles:
    - role: geerlingguy.docker  # Docker must be installed first
    - role: jonimofo.infrastructure.ufw
```

This configuration:
- Allows SSH with rate limiting (UFW rule)
- Allows ports 80/443 from anywhere (Traefik)
- Allows all Docker ports from LAN (192.168.x, 10.x, 172.16.x)
- Blocks all other Docker ports from internet

## Platform Notes

### Raspberry Pi OS

Raspberry Pi OS is fully supported. Considerations:

- **Headless Pi:** Ensure SSH rule is configured before enabling UFW
- **GPIO/I2C services:** May need rules for local services on specific ports
- **Default interface:** Usually `eth0` (Ethernet) or `wlan0` (WiFi)

### Debian / Ubuntu

Standard Debian and Ubuntu installations are fully supported. UFW is a frontend for iptables and works identically across all Debian-based distributions.

## Security Considerations

### Default Security Posture

This role applies secure defaults:

- **Deny all incoming** - Whitelist-only approach
- **Allow all outgoing** - Permits responses and updates
- **Logging enabled** - Audit denied connections

### Recommendations

1. **Always allow SSH first** - Before enabling UFW remotely
2. **Use `limit` for SSH** - Rate limits brute-force attempts
3. **Restrict by source IP** - When possible, use `from_ip` to limit access
4. **Use interface rules** - On multi-homed systems, bind services to specific interfaces
5. **Enable logging** - Set `ufw_logging: "medium"` or higher for security auditing

### Rate Limiting

The `limit` rule type automatically rate-limits connections:
- Allows 6 connections per 30 seconds from a single IP
- Excess connections are denied
- Perfect for SSH brute-force protection

```yaml
- rule: limit
  port: 22
  proto: tcp
  comment: "Rate limit SSH connections"
```

### Docker and UFW

By default, Docker manipulates iptables directly and bypasses UFW completely. Containers with published ports (e.g., `-p 3306:3306`) are accessible from the internet even if UFW would block them.

When `ufw_docker_integration: true`, this role:

1. Manages the `DOCKER-USER` chain (Docker's hook for custom rules)
2. Allows traffic from private networks (LAN) to all Docker ports
3. Allows only `ufw_docker_allowed_ports` from the internet
4. Drops all other external traffic to Docker containers
5. Creates a systemd service (`ufw-docker`) to persist rules across reboots

| Traffic | Behavior |
|---------|----------|
| Internet → Container (allowed port) | ✅ Allowed |
| Internet → Container (other port) | ❌ Blocked |
| LAN → Container (any port) | ✅ Allowed |
| Container → Container | ✅ Allowed |

**Note:** This only controls network access. For maximum security, also:
- Bind non-public services to `127.0.0.1` in docker-compose (e.g., `127.0.0.1:3306:3306`)
- Use Docker networks for container-to-container communication
- Don't publish ports that only need internal access

### Lockout Prevention

Before running this role remotely:

1. Ensure SSH is in `ufw_rules` with `allow` or `limit`
2. Test with `ufw_state: disabled` first
3. Have console access as backup
4. Keep an SSH session open while testing

### What Gets Blocked

With default policies:

| Traffic | Default | Reason |
|---------|---------|--------|
| Incoming SSH | Blocked | Must add rule |
| Incoming HTTP | Blocked | Must add rule |
| Outgoing apt | Allowed | Updates work |
| Outgoing DNS | Allowed | Resolution works |
| ICMP ping | Blocked | Must add rule if needed |

## What This Role Does

1. Verifies Debian-based system
2. Installs UFW package
3. Configures IPv6 support
4. (Optional) Resets UFW if `ufw_reset_before_configure: true`
5. Sets default policies (deny incoming, allow outgoing)
6. Configures firewall rules from `ufw_rules`
7. Sets logging level
8. Enables UFW
9. (Optional) Configures Docker integration if `ufw_docker_integration: true`

## License

GPL-2.0-or-later

## Author Information

jonimofo
