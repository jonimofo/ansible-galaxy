# Ansible Role: astronvim

Installs Neovim and configures AstroNvim for specified users.

## Features

- Auto-detects CPU architecture (x86_64 vs ARM/aarch64)
- Downloads and installs Neovim from official releases
- Configures AstroNvim template for each user
- Backs up existing Neovim configurations
- Fully idempotent - safe to run multiple times

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
| `astronvim_neovim_binary_path` | `/usr/local/bin/nvim` | Path for nvim binary |
| `astronvim_neovim_download_url` | GitHub releases URL | Base URL for downloads |
| `astronvim_neovim_version` | `v0.12.6` | Neovim version to install. A different installed version is replaced on the next run |
| `astronvim_download_dir` | `/tmp` | Parent of the private download directory (mktemp, root-only) |
| `astronvim_neovim_arch_map` | `{x86_64, aarch64}` | Architecture to release suffix; unsupported architectures fail |
| `astronvim_build_packages` | `[git, gcc, unzip]` | Packages needed to clone the config and build plugins |
| `astronvim_users` | `[]` | List of users to configure |

### User Configuration

Each user in `astronvim_users` should have a `name` key:

```yaml
astronvim_users:
  - name: "alice"
  - name: "bob"
```

## Dependencies

None.

## Example Playbook

### Basic Usage

```yaml
- name: Install AstroNvim
  hosts: all
  become: true
  vars:
    astronvim_users:
      - name: "admin"
  roles:
    - role: jonimofo.infrastructure.astronvim
```

### Multiple Users

```yaml
- name: Install AstroNvim for team
  hosts: workstations
  become: true
  vars:
    astronvim_users:
      - name: "developer"
      - name: "sysadmin"
  roles:
    - role: jonimofo.infrastructure.astronvim
```

### Specific Neovim Version

```yaml
- name: Install specific Neovim version
  hosts: all
  become: true
  vars:
    astronvim_neovim_version: "v0.11.3"
    astronvim_users:
      - name: "admin"
  roles:
    - role: jonimofo.infrastructure.astronvim
```

## What This Role Does

1. Verifies Debian-based system
2. Installs `astronvim_build_packages` (git, gcc, unzip) via apt
3. Detects CPU architecture (x86_64 or aarch64)
4. Downloads the Neovim tarball into a private root-only directory
5. Extracts Neovim to `/usr/local/` owned by root, and repairs ownership left by older runs
6. For each user:
   - Backs up existing nvim configs (`.config/nvim`, `.local/share/nvim`, etc.)
   - Clones AstroNvim template to `~/.config/nvim`
   - Removes `.git` directory for personal customization
   - Installs plugins headlessly (`nvim --headless "+Lazy! sync"`) so the next run is idempotent

## Post-Installation

After installation, users should:

1. Open nvim: `nvim`
2. Wait for lazy.nvim to install plugins
3. Run `:checkhealth` to verify setup

## License

GPL-2.0-or-later

## Author Information

jonimofo
