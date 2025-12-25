# Ansible Role: locale

Configures the system locale on Debian-based systems.

## Features

- Installs locale packages
- Generates specified locale
- Sets locale as system default in `/etc/default/locale` and `/etc/environment`
- Optional reboot after locale changes

## Requirements

- **Ansible version:** 2.12+
- **Collections:** `community.general` (for `locale_gen` module)
- **Supported OS:** Debian-based systems only
  - Debian (bullseye, bookworm, trixie)
  - Ubuntu (focal, jammy, noble)
  - Raspberry Pi OS
- **Supported architectures:** x86_64, aarch64, armv7l
- **Privileges:** Requires `become: true`

## Role Variables

All variables are defined in `defaults/main.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `locale_packages` | `[locales]` | Packages required for locale management |
| `locale_name` | `"en_US.UTF-8"` | Locale to generate and set as default |
| `locale_env` | `{LANG, LANGUAGE, LC_ALL}` | Environment variables for `/etc/default/locale` |
| `locale_reboot` | `false` | Reboot after locale change (disabled by default) |

### Default locale_env

```yaml
locale_env:
  LANG: "en_US.UTF-8"
  LANGUAGE: "en_US:en"
  LC_ALL: "en_US.UTF-8"
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
      LC_ALL: "de_DE.UTF-8"
  roles:
    - role: jonimofo.infrastructure.locale
```

### With Reboot Enabled

```yaml
- name: Configure locale with reboot
  hosts: all
  become: true
  vars:
    locale_reboot: true
  roles:
    - role: jonimofo.infrastructure.locale
```

## What This Role Does

1. Verifies Debian-based system
2. Updates apt cache (with retries)
3. Installs locale packages
4. Generates specified locale using `locale_gen`
5. Writes locale environment to `/etc/default/locale`
6. Runs `dpkg-reconfigure locales` if config changed
7. Ensures `LANG` is set in `/etc/environment`
8. Optionally reboots if `locale_reboot: true` and changes were made

## License

GPL-2.0-or-later

## Author Information

jonimofo
