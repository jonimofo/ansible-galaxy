# Ansible Role: lazydocker

This role installs **lazydocker**, a free and open-source terminal UI for Docker and Docker-compose that allows you to manage your containers and services with ease. It downloads a specific version of the pre-compiled binary from the official GitHub releases, extracts it, and places it in the specified installation path.

## Requirements

For `lazydocker` to be useful, **Docker** and/or **Docker-compose** must be installed and running on the target machine. This role does not install them.

## Role Variables

The following variables can be configured, with default values located in `defaults/main.yml`.

| Variable | Default Value | Description |
|---|---|---|
| `lazydocker_version` | `"0.24.1"` | The specific version of lazydocker to install. |
| `lazydocker_install_path` | `"/usr/local/bin"` | The directory where the `lazydocker` binary will be placed. |
| `lazydocker_download_dir` | `"/tmp"` | A temporary directory for downloading the release archive. |
| `lazydocker_arch_map` | `{ x86_64: ..., aarch64: ..., armv7l: ... }` | A dictionary mapping the system architecture (`ansible_architecture`) to the string used in the release filename. |

## Dependencies

This role has no dependencies on other Ansible Galaxy roles.

## Example Playbook

Here is a simple example of how to use this role to install the latest version of `lazydocker`.

```yaml
- name: Install lazydocker on servers
  hosts: docker_hosts
  become: true
  vars:
    lazydocker_version: "0.24.1"
  roles:
    - jonimofo.lazydocker
```

## License

MIT

## Author Information

This role was created by jonimofo.
