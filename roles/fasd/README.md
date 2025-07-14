# Ansible Role: fasd

Installs `fasd` (fast access to directories and files) from its source repository. It allows you to quickly access files and directories by tracking your most frequently and recently used ones. This role handles the cloning, building, installation, and shell configuration for specified users.

## Requirements

The target system must have `make` and other common build tools installed to compile `fasd` from source. This role will ensure `git` is installed, but not `make`.

## Role Variables

The following variables are available to customize the installation, with default values located in `defaults/main.yml`.

| Variable | Default Value | Description |
|---|---|---|
| `fasd_git_repo_url` | `https://github.com/clvv/fasd.git` | The Git repository URL for `fasd`. |
| `fasd_git_version` | `master` | The branch, tag, or commit to check out for the build. |
| `fasd_clone_dir` | `/tmp/fasd` | The temporary directory where the repository will be cloned. |
| `fasd_install_path`| `/usr/local/bin` | The destination path for the `fasd` binary. |
| `fasd_dependencies` | `[ 'git' ]` | A list of system packages required to run the role. |
| `fasd_users` | `[]` | A list of users to configure `fasd` for. See example below. |
| `fasd_configure_shell` | `true` | If `true`, adds the `fasd` init script to users' `.bashrc`. |
| `fasd_cleanup_build_dir` | `true` | If `true`, removes the temporary clone directory after installation. |

**`fasd_users` structure:**

This variable should be a list of dictionaries, where each dictionary has a `name` key specifying the user.

```yaml
fasd_users:
  - name: "alice"
  - name: "bob"
```

## Dependencies

This role has no dependencies on other Ansible Galaxy roles.

## Example Playbook

Below is an example of how to use this role to install `fasd` and configure it for the user `jdoe`.

```yaml
- name: Install and configure fasd
  hosts: workstations
  become: true
  vars:
    fasd_users:
      - name: "jdoe"
  roles:
    - jonimofo.fasd
```

## License

MIT

## Author Information

This role was created by jonimofo.