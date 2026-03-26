# Audit Results

Audit date: 2026-03-26
Auditor: automated review of all roles in jonimofo.infrastructure

## Overall Assessment

The collection is in good shape. Security defaults are solid, Ansible best practices are
followed consistently, and linting passes at production profile. The findings below are
minor improvements, not critical issues.

## Linting Results

- **yamllint**: All project files pass (0 errors, 0 warnings)
- **ansible-lint**: Passed at `production` profile (0 failures, 0 warnings)
- **Note**: `make lint` was failing because `.yamllint` scanned `.venv/` — fixed below

## Findings

### Fixed

1. **`.yamllint` missing `.venv/` ignore** — `make lint` scanned thousands of third-party
   YAML files in `.venv/`, causing false failures. Added `.venv/` and `audit/` to ignore list.

2. **`galaxy.yml` empty `build_ignore`** — `.venv/`, `audit/`, `.githooks/`, `Makefile`,
   `TODO.md`, and other dev files would be included in collection build artifacts.
   Populated `build_ignore` with appropriate patterns.

3. **Inconsistent licenses in meta/main.yml** — `packages`, `ssh`, and `ufw` had
   `license: MIT` while all other roles and `galaxy.yml` use `GPL-2.0-or-later`.
   Updated all three to `GPL-2.0-or-later` for consistency.

4. **Removed `gui_apps` role** — Deleted per user request.

5. **Removed 12 empty `vars/main.yml` files** — Boilerplate from `ansible-galaxy init`
   with no actual content. All variables are properly defined in `defaults/main.yml`.

### Not Fixed (Require Design Decisions)

6. **`brave_students_profile` is not a proper Ansible role** — It contains only
   `student_profile.json` and `brave_steps.md` with no tasks, defaults, or meta. It's
   effectively a documentation/config snippet, not executable.

### All Good (No Issues Found)

- SSH hardening defaults are strong (no root login, no passwords, low MaxAuthTries)
- Firewall defaults deny incoming, logging enabled
- Fail2ban has SSH + recidive jails, incremental bans, ufw integration
- User management locks root, blocks su, validates sudoers
- All config files validated before apply (sshd, sudoers)
- All downloads use HTTPS, archives cleaned up
- No secrets hardcoded, no sensitive data logged
- All tasks named, FQCN used throughout, handlers for service restarts
- Idempotency maintained (state checks before downloads, creates parameters)
- Cross-platform assertions on every role
- Documentation complete with READMEs, variable tables, examples
- Meta files complete with platforms and min_ansible_version
