# Ansible Role: locale

Configures the system locale on Debian-based systems.

## Features

- Installs locale packages
- Generates specified locale
- Sets locale as system default in `/etc/default/locale` and `/etc/environment`

## Requirements

- **Ansible version:** 2.15+
- **Collections:** `community.general` (for `locale_gen` module)
- **Supported OS:** Debian-based systems only
  - Debian (bookworm, trixie)
  - Ubuntu (jammy, noble, resolute)
- **Supported architectures:** x86_64, aarch64
- **Privileges:** Requires `become: true`

## Role Variables

All variables are defined in `defaults/main.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `locale_packages` | `[locales]` | Packages required for locale management |
| `locale_name` | `"en_US.UTF-8"` | Locale to generate and set as default |
| `locale_additional` | `[]` | Additional locales to generate (not set as default) |
| `locale_env` | `{LANG, LANGUAGE}` derived from `locale_name` | Environment variables for `/etc/default/locale` |

### Default locale_env

```yaml
locale_env:
  LANG: "en_US.UTF-8"
  LANGUAGE: "en_US:en"
```

## Dependencies

None.

## Example Playbook

### Basic Usage (US English)

```yaml
- name: Configure locale
  hosts: all
  become: true
  roles:
    - role: jonimofo.infrastructure.locale
```

### German Locale

```yaml
- name: Configure German locale
  hosts: all
  become: true
  vars:
    locale_name: "de_DE.UTF-8"
    locale_env:
      LANG: "de_DE.UTF-8"
      LANGUAGE: "de_DE:de"
  roles:
    - role: jonimofo.infrastructure.locale
```

### With Additional Locales (SSH Forwarding)

When SSH forwards locale settings from your local machine, the remote needs those locales generated. Use `locale_additional` to generate extra locales without changing the system default:

```yaml
- name: Configure locale with additional locales
  hosts: all
  become: true
  vars:
    locale_name: "en_US.UTF-8"
    locale_additional:
      - "fr_FR.UTF-8"
      - "en_GB.UTF-8"
  roles:
    - role: jonimofo.infrastructure.locale
```

## What This Role Does

1. Verifies Debian-based system
2. Installs locale packages
3. Generates specified locale using `locale_gen`
4. Generates additional locales if specified
5. Writes locale environment to `/etc/default/locale`
6. Runs `dpkg-reconfigure locales` if config changed
7. Ensures `LANG` is set in `/etc/environment`

## License

GPL-2.0-or-later

## Author Information

jonimofo
