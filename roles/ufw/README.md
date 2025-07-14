# Ansible Role: ufw

This role installs and configures the Uncomplicated Firewall (UFW) on **Debian-based systems**. It handles the installation, default policy configuration, and management of specific firewall rules.

## Requirements

* This role is designed **exclusively for Debian-based distributions** like Debian and Ubuntu due to its use of the `apt` package manager.
* The `community.general` Ansible collection must be installed on your controller: `ansible-galaxy collection install community.general`.

## Role Variables

Default values are located in `defaults/main.yml`.

| Variable | Default Value | Description |
|---|---|---|
| `ufw_pkg_name` | `ufw` | The name of the UFW package to install. |
| `ufw_config_path` | `/etc/default/ufw` | Path to the main UFW configuration file. |
| `ufw_enable_ipv6` | `false` | A boolean to control IPv6 support. |
| `ufw_logging` | `on` | Sets the logging state. Can be `on`, `off`, `low`, `medium`, `high`, `full`. |
| `ufw_state` | `enabled` | The final desired state of the UFW service. Can be `enabled` or `disabled`. |

### Default Policies
The `ufw_default_policies` variable sets the default behavior for traffic.

* `direction`: Can be `incoming`, `outgoing`, or `routed`. (Required)
* `policy`: Can be `allow`, `deny`, or `reject`. (Required)

**Example:**
```yaml
ufw_default_policies:
  - direction: incoming
    policy: deny
  - direction: outgoing
    policy: allow
```

### Firewall Rules
The `ufw_rules` variable is a list of dictionaries defining each firewall rule.
* `rule`: The rule type. Can be `allow`, `deny`, `reject`, `limit`. (Required)
* `name`: The name of an application profile from `/etc/ufw/applications.d`.
* `port`: The port number.
* `proto`: The protocol. Can be `tcp`, `udp`, `ipv6`, `esp`, `ah`.
* `comment`: An optional comment for the rule.

**Example:**
```yaml
ufw_rules:
  - rule: allow
    name: "OpenSSH"
    comment: "Allow SSH access"
  - rule: allow
    port: "80"
    proto: "tcp"
    comment: "Allow HTTP traffic"
  - rule: limit
    port: "22"
    proto: "tcp"
    comment: "Limit SSH connections to mitigate brute-force attacks"
```

## Dependencies

This role has no dependencies on other Ansible Galaxy roles.

## Example Playbook

Here is an example of how to use this role to set up a basic firewall for a web server.

```yaml
- name: Configure firewall for web servers
  hosts: webservers
  become: true
  vars:
    ufw_default_policies:
      - direction: incoming
        policy: deny
      - direction: outgoing
        policy: allow
    ufw_rules:
      - rule: allow
        name: "OpenSSH"
      - rule: allow
        port: "80"
        proto: "tcp"
      - rule: allow
        port: "443"
        proto: "tcp"
  roles:
    - jonimofo.ufw
```

## License

MIT

## Author Information

This role was created by jonimofo.