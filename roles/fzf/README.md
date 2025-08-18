# Ansible Role: fzf

Installs `fzf`, a general-purpose command-line fuzzy finder, from its source repository. This role also handles the configuration of shell key-bindings and auto-completion for specified users.

## Requirements

There are no special requirements for this role. It will ensure `git` is installed on the target machine.

## Role Variables

Default values are located in `defaults/main.yml`.

| Variable | Default Value | Description |
|---|---|---|
| `fzf_repo_url` | `https://github.com/junegunn/fzf.git` | The source Git repository for `fzf`. |
| `fzf_install_path` | `/usr/local/bin/fzf` | The destination path where the `fzf` repository will be cloned. The binary will be inside `.../bin/`. |
| `fzf_users` | `[]` | A list of users to configure `fzf` for. See example below. |

**`fzf_users` structure:**

This variable should be a list of dictionaries. Each dictionary represents a user and must contain a `name`. It can also contain `update_bashrc` to control shell modification.

* `name`: The username to configure. (Required)
* `update_bashrc`: A boolean. If `true`, a line will be added to the user's `.bashrc` to source the `fzf` configuration. (Optional)

```yaml
fzf_users:
  - name: "alice"
    update_bashrc: true
  - name: "bob"
    update_bashrc: false
```

## Dependencies

This role has no dependencies on other Ansible Galaxy roles.

## Example Playbook

Here is an example of how to use the role to install `fzf` and configure it for the user `jdoe`.

```yaml
- name: Install and configure fzf
  hosts: workstations
  become: true
  vars:
    fzf_users:
      - name: "jdoe"
        update_bashrc: true
  roles:
    - jonimofo.fzf
```

## License

MIT

## Author Information

This role was created by jonimofo.