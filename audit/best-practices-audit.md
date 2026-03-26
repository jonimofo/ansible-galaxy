# Best Practices Audit Plan

Audit date: 2026-03-26
Scope: All roles in jonimofo.infrastructure collection

## 1. Role Structure

- [x] Every role has: defaults/, tasks/, meta/, README.md
- [x] handlers/main.yml present where services are managed
- [x] tests/test.yml and tests/inventory present for all roles
- [x] No unnecessary empty files — removed 12 empty vars/main.yml boilerplate files
- [ ] `brave_students_profile` is not a proper role (only has .json and .md, no tasks/)

## 2. Task Quality

- [x] All tasks have descriptive `name:` fields
- [x] FQCN used for all modules (ansible.builtin.*, community.general.*)
- [x] YAML syntax used consistently (key: value format)
- [x] Handlers used for service restarts, not inline restarts
- [x] `changed_when` / `failed_when` used where needed (dotfiles/tmux, locale, users)
- [x] `validate:` parameter used for sshd_config and sudoers
- [x] Loop control with `label:` used where appropriate (ssh, ufw, users)
- [x] Tags applied for selective execution (packages)

## 3. Variable Conventions

- [x] All user-configurable variables in defaults/main.yml
- [x] Variables documented with comments
- [x] Sensible secure defaults provided
- [x] No unused variables defined

### Note: Variable prefixing inconsistent

- Most roles use proper prefixes (`ssh_`, `ufw_`, `fail2ban_`, `users_`, `host_`)
- `packages` role uses `apt_update_` prefix (acceptable, descriptive)
- This is a known issue tracked in `.ansible-lint` skip_list as `var-naming[no-role-prefix]`

## 4. Idempotency

- [x] State checked before downloads (lazydocker: `stat` + `when`, astronvim: checks for existing)
- [x] No unconditional downloads (all check if binary/package exists first)
- [x] No duplicate work on re-runs

## 5. Cross-Platform Compatibility

- [x] Debian-family assertion at role start (all roles check `ansible_os_family == 'Debian'`)
- [x] Architecture detection where needed (lazydocker, astronvim)
- [x] Package names in defaults for override capability

## 6. Documentation

- [x] README.md present for all roles with proper structure
- [x] Variables tables included
- [x] Example playbooks provided
- [x] License and author information present

## 7. Meta Information

- [x] All meta/main.yml have galaxy_info with platforms
- [x] min_ansible_version: '2.12' set consistently
- [x] Supported platforms listed: Debian (bullseye, bookworm, trixie), Ubuntu (focal, jammy, noble)
- [x] All roles use `GPL-2.0-or-later` license, matching `galaxy.yml` (fixed)

## 8. Linting Compliance

- [x] yamllint passes on all project files (zero warnings/errors)
- [x] ansible-lint passes at production profile
- [x] SPDX license headers present on most files
- [x] `.yamllint` ignores `.venv/` and `audit/` (fixed)
- [x] `galaxy.yml` `build_ignore` populated with dev files (fixed)

## 9. Error Handling

- [x] Assertions for required variables (host_hostname)
- [x] Assertions for supported platforms/architectures
- [x] Meaningful fail_msg on assertions
- [x] Graceful handling of missing optional components

## 10. Handlers

- [x] Handlers defined for all service-managing roles (ssh, ufw, fail2ban, packages, locale)
- [x] Handler names are descriptive and unique
- [x] Handlers use appropriate actions (restart sshd, reload ufw, restart fail2ban, reload systemd)
- [x] 7 roles have empty handler files (boilerplate, no services to manage — harmless)
