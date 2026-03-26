# Security Audit Plan

Audit date: 2026-03-26
Scope: All roles in jonimofo.infrastructure collection

## 1. SSH Hardening (roles/ssh)

- [x] Root login disabled or restricted by default (`ssh_permit_root_login: "no"`)
- [x] Password authentication disabled by default (`ssh_password_authentication: false`)
- [x] Empty passwords disallowed (`ssh_permit_empty_passwords: false`)
- [x] MaxAuthTries set to a low value (`ssh_max_auth_tries: 3`)
- [x] Forwarding (agent, TCP, X11) disabled by default
- [x] sshd_config validated before apply (`validate: '/usr/sbin/sshd -t -f %s'`)
- [x] AllowUsers directive used when ssh_users is defined
- [x] authorized_keys managed via ansible.posix.authorized_key
- [x] exclusive_keys enabled by default (removes unmanaged keys)

## 2. Firewall (roles/ufw)

- [x] Default incoming policy is deny
- [x] Default outgoing policy is allow
- [x] UFW enabled by default (`ufw_state: enabled`)
- [x] Logging enabled by default (`ufw_logging: "on"`)
- [x] Reset not enabled by default (`ufw_reset_before_configure: false`)
- [x] Rules support rate limiting (limit rule type documented in examples)

## 3. Intrusion Prevention (roles/fail2ban)

- [x] fail2ban enabled and started by default
- [x] SSH jail enabled by default
- [x] Recidive jail enabled (bans repeat offenders)
- [x] Ban times are reasonable (3600s default, 604800s recidive)
- [x] ignoreip includes localhost only (`127.0.0.1/8`)
- [x] banaction matches firewall in use (`ufw`)
- [x] Incremental ban times enabled

## 4. User Management (roles/users)

- [x] Root account locked by default (`users_lock_root: true`)
- [x] su command disabled for sudo group by default (`users_disable_su: true`)
- [x] passwd root blocked for sudo users
- [x] Warning when disabling passwordless sudo without become_password
- [x] Warning when skipping root lock (connected as root)
- [x] sudoers validated before apply (`visudo -cf %s`)
- [x] Sudoers.d overrides removed (Pi default, cloud-init)
- [x] No sensitive data logged (no passwords handled in tasks)

## 5. Package Management (roles/packages)

- [x] Unattended-upgrades available and configurable
- [x] Security-only origins configured by default
- [x] Auto-reboot disabled by default (safe default)
- [x] Package blacklist supported
- [x] Systemd timer files have correct permissions (0644)

## 6. File Permissions

- [x] /tmp has sticky bit (1777) — set in host role
- [x] Config files have appropriate permissions (0644 for service/timer units)
- [x] Sensitive config files (sudoers, sshd_config) validated before write
- [x] Downloaded binaries set to 0755 (lazydocker)
- [x] No world-writable files created (except /tmp)

## 7. Download Security (roles/lazydocker, astronvim, fzf, fasd)

- [x] Downloads use HTTPS URLs
- [x] Downloaded archives cleaned up after extraction (lazydocker)
- [x] No curl | bash patterns
- [x] No deprecated modules in remaining roles

## 8. Secrets Handling

- [x] No hardcoded passwords, keys, or tokens in defaults
- [x] SSH public keys handled safely (no private keys)
- [x] Vault-compatible variable patterns for secrets

### Note: no `no_log` usage anywhere

- No tasks in the entire collection use `no_log: true`
- Currently acceptable: no tasks handle passwords/tokens directly
- If password-setting tasks are added in future, `no_log` will be needed

## 9. Service Configuration

- [x] Handlers used for service restarts (not inline)
- [x] Services enabled/started explicitly (fail2ban, ufw, unattended-upgrades)
- [x] No services exposed unnecessarily

## 10. Network Security

- [x] IPv6 handled explicitly (ufw: `ufw_enable_ipv6: false`, fail2ban: `fail2ban_allowipv6: false`)
- [x] DNS lookups disabled for SSH by default (`ssh_use_dns: false`)
- [x] APT sources use HTTPS or signed repos
