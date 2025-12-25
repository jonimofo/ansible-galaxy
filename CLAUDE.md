# Project Guidelines for Ansible Galaxy Collection

## Git Commit Conventions

Follow Angular commit message conventions: https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (formatting)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools

### Scope

Use the role name as scope when changes are role-specific:
- `feat(packages): add unattended-upgrades support`
- `fix(ssh): correct sshd config validation`
- `docs(ufw): update README with examples`

### Rules

- **NEVER** include `🤖 Generated with [Claude Code]` or `Co-Authored-By: Claude` in commits
- Keep subject line under 72 characters
- Use imperative mood ("add" not "added")

### Examples

```
feat(packages): add automatic security updates via unattended-upgrades

- Add configurable unattended-upgrades support
- Create templates for apt configuration
- Add security section to README

fix(ssh): disable root login by default

refactor(users): simplify user creation logic

docs: update CLAUDE.md with security guidelines
```

## Overview

This is an Ansible collection (`jonimofo.infrastructure`) for managing Debian-based servers, including Raspberry Pi and standard Debian/Ubuntu machines.

## Ansible Best Practices

Follow the official Ansible best practices: https://docs.ansible.com/ansible/2.9/user_guide/playbooks_best_practices.html

Key principles:
- **Use YAML syntax consistently** - Always use `key: value` format, not `key=value`
- **Name all tasks** - Every task must have a descriptive `name:` field
- **Use FQCN** - Always use fully qualified collection names (e.g., `ansible.builtin.apt` not `apt`)
- **Keep plays and playbooks focused** - Each role should do one thing well
- **Use handlers for service restarts** - Never restart services inline
- **Use `changed_when` and `failed_when`** - Make task status explicit when needed
- **Validate before apply** - Use `validate:` parameter for config files (sshd, sudoers, etc.)

## Cross-Platform Compatibility (Raspberry Pi + Debian)

### Architecture Detection

Always detect and handle different architectures:
```yaml
vars:
  arch_map:
    x86_64: amd64
    aarch64: arm64
    armv7l: armhf

- name: Set architecture
  ansible.builtin.set_fact:
    target_arch: "{{ arch_map[ansible_architecture] | default('amd64') }}"
```

### Distribution Detection

Use Ansible facts for distro-specific logic:
- `ansible_os_family`: "Debian" (covers Debian, Ubuntu, Raspbian)
- `ansible_distribution`: "Debian", "Ubuntu", "Raspbian"
- `ansible_distribution_major_version`: "11", "12", "22", etc.
- `ansible_architecture`: "x86_64", "aarch64", "armv7l"

### Conditional Tasks for Distro Differences

```yaml
- name: Install package (Debian/Raspbian)
  ansible.builtin.apt:
    name: "{{ package_name }}"
  when: ansible_os_family == 'Debian'

- name: Handle Raspberry Pi specific configuration
  ansible.builtin.template:
    src: rpi-config.j2
    dest: /boot/config.txt
  when: ansible_distribution == 'Raspbian' or 'raspberry' in ansible_kernel | lower
```

### Package Handling

- Prefer `ansible.builtin.package` for generic packages
- Use `ansible.builtin.apt` when APT-specific features are needed
- Define package names in `defaults/main.yml` to allow overrides for different distros

## Variable Organization

### Where to Define Variables

All user-configurable variables MUST be defined in `defaults/main.yml`:

```
roles/
└── role_name/
    ├── defaults/
    │   └── main.yml      # ALL user-configurable variables go here
    ├── vars/
    │   └── main.yml      # Internal role variables (rarely used)
    ├── tasks/
    ├── handlers/
    ├── templates/
    ├── files/
    └── meta/
```

### Variable Naming Convention

Prefix all variables with the role name to avoid conflicts:
```yaml
# Good
ssh_port: 22
ssh_permit_root_login: false
ufw_default_policies: {}

# Bad
port: 22
permit_root_login: false
default_policies: {}
```

### Variable Documentation

Document every variable in `defaults/main.yml` with comments:
```yaml
---
# ssh_port: SSH daemon listening port
ssh_port: 22

# ssh_permit_root_login: Allow root login via SSH
# Values: true, false, "prohibit-password", "forced-commands-only"
ssh_permit_root_login: false

# ssh_users: List of users with SSH access
# Each user requires: name, authorized_keys (list)
ssh_users: []
```

## Role Documentation (README.md)

Every role MUST have a complete `README.md` with:

### Required Sections

```markdown
# Role Name

Brief description of what the role does.

## Requirements

- Minimum Ansible version
- Supported platforms (Debian, Ubuntu, Raspbian)
- Supported architectures (x86_64, aarch64, armv7l)
- Any external dependencies

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `role_var1` | `value` | Description |
| `role_var2` | `[]` | Description |

## Dependencies

List any role dependencies or "None".

## Example Playbook

```yaml
- hosts: servers
  roles:
    - role: jonimofo.infrastructure.role_name
      vars:
        role_var1: custom_value
```

## Platform Notes

### Raspberry Pi
- Any Pi-specific considerations

### Debian/Ubuntu
- Any distro-specific considerations

## License

GPL-2.0-or-later

## Author Information

jonimofo
```

## Modular Role Design

### Task Organization

Split complex roles into multiple task files:
```yaml
# tasks/main.yml
---
- name: Include OS-specific variables
  ansible.builtin.include_vars: "{{ item }}"
  with_first_found:
    - "{{ ansible_distribution }}-{{ ansible_distribution_major_version }}.yml"
    - "{{ ansible_distribution }}.yml"
    - "{{ ansible_os_family }}.yml"
    - "default.yml"
  tags: always

- name: Include installation tasks
  ansible.builtin.include_tasks: install.yml
  tags: install

- name: Include configuration tasks
  ansible.builtin.include_tasks: configure.yml
  tags: configure
```

### OS-Specific Variables

Store distro-specific values in `vars/`:
```
vars/
├── Debian.yml
├── Ubuntu.yml
├── Raspbian.yml
└── default.yml
```

### Tagging Strategy

Always tag tasks for selective execution:
- `install` - Installation tasks
- `configure` - Configuration tasks
- `<role_name>` - All tasks in the role

## Idempotency Requirements

All roles MUST be idempotent:
- Use `creates:` parameter for shell/command tasks
- Check state before making changes with `ansible.builtin.stat`
- Use `changed_when: false` for read-only commands
- Register results and use conditions to skip unnecessary actions

## Testing

Each role should have a test playbook in `tests/test.yml` that:
- Can run on both Debian and Raspberry Pi OS
- Uses molecule or a simple localhost test
- Validates the role works correctly

## Security Best Practices

When reviewing or creating roles, always apply security best practices and suggest improvements based on the role's context.

### General Security Principles

- **Never hardcode sensitive values** - Use Ansible Vault or external secret management
- **Use `no_log: true`** - For tasks handling passwords, keys, or tokens
- **Validate before apply** - Use `validate:` parameter for config files (sshd, sudoers, etc.)
- **Principle of least privilege** - Request only necessary permissions
- **Fail securely** - Default to secure states when errors occur

### File and Permission Security

```yaml
# Secure file permissions for sensitive files
- name: Deploy configuration
  ansible.builtin.template:
    src: config.j2
    dest: /etc/app/config.conf
    owner: root
    group: root
    mode: '0600'  # Restrictive by default
```

- Config files with secrets: `0600` (owner read/write only)
- Config files without secrets: `0644`
- Executable scripts: `0755` or `0750`
- Directories with secrets: `0700`

### SSH Hardening (for ssh role)

- Disable root login or use `prohibit-password`
- Disable password authentication, use keys only
- Set `MaxAuthTries` to low value (3-5)
- Use `AllowUsers` or `AllowGroups` to restrict access
- Consider changing default port (security through obscurity, optional)
- Enable `StrictModes`

### Firewall Security (for ufw role)

- Default deny incoming, allow outgoing
- Whitelist only necessary ports
- Consider rate limiting for SSH
- Log denied connections

### User Management (for users role)

- Enforce strong password policies
- Set appropriate `UMASK` (027 or 077)
- Limit sudo access with specific commands when possible
- Set password expiry policies
- Disable unused accounts

### Package Management (for packages role)

- Keep systems updated (unattended-upgrades for security patches)
- Only install necessary packages (minimize attack surface)
- Verify package sources (use official repos)
- Consider automatic security updates

### Service Hardening (for fail2ban and other service roles)

- Enable fail2ban for brute-force protection
- Configure appropriate ban times and thresholds
- Monitor and log authentication failures
- Use systemd security directives when applicable:
  ```ini
  [Service]
  ProtectSystem=strict
  ProtectHome=true
  NoNewPrivileges=true
  PrivateTmp=true
  ```

### Network Security

- Bind services to localhost when external access not needed
- Use TLS/SSL for network services
- Disable unused network protocols
- Consider network segmentation

### Role-Specific Security Review

When working on each role, actively suggest security improvements:

1. **Identify the role's attack surface** - What does it expose?
2. **Review default configurations** - Are defaults secure?
3. **Check for hardening opportunities** - What can be locked down?
4. **Consider defense in depth** - Multiple layers of protection
5. **Document security implications** - Help users understand risks

### Security Checklist for Each Role

Before completing a role review, verify:

- [ ] Sensitive data protected with `no_log: true`
- [ ] File permissions are restrictive
- [ ] Config files validated before apply
- [ ] Services bound to appropriate interfaces
- [ ] Authentication/authorization properly configured
- [ ] Logging enabled for security events
- [ ] Default deny policies where applicable
- [ ] Documentation includes security notes
