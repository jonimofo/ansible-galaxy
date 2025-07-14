# Ansible Role: users

This role manages system users based on a provided list. It also includes a task to configure the `/etc/sudoers` file to grant passwordless `sudo` privileges to any user in the `sudo` group.

## ❗ Security Warning

This role modifies the `/etc/sudoers` file to grant **passwordless sudo access** to members of the `sudo` group. This is a significant security consideration. Ensure you understand the implications before applying this role to production systems.

## Requirements

There are no special requirements for this role. It uses standard `ansible.builtin` modules.

## Role Variables

Default values are located in `defaults/main.yml`.

| Variable | Default Value | Description |
|---|---|---|
| `users_default_shell` | `/bin/bash` | The default login shell for new users if not specified per-user. |
| `users_default_create_home` | `true` | The default setting for creating a home directory if not specified per-user. |

### `users`
This is the main variable for defining the users you want to create. It is a list of dictionaries, where each dictionary represents a user.

* `name`: The username. (Required)
* `groups`: A comma-separated string of groups to add the user to (e.g., `"sudo,www-data"`). (Optional)
* `shell`: The user's login shell. (Optional, defaults to `users_default_shell`)
* `create_home`: A boolean (`true`/`false`) to control home directory creation. (Optional, defaults to `users_default_create_home`)

**Example `users` structure:**
```yaml
users:
  - name: "jdoe"
    groups: "sudo"
  - name: "app_user"
    shell: "/bin/false"
    create_home: false
```

## Dependencies

This role has no dependencies on other Ansible Galaxy roles.

## Example Playbook

Here is an example of how to use this role to create an admin user and a service account.

```yaml
- name: Create system users
  hosts: all
  become: true
  vars:
    users:
      - name: "sysadmin"
        groups: "sudo"
        shell: "/bin/bash"
      - name: "web_runner"
        shell: "/usr/sbin/nologin"
  roles:
    - jonimofo.users
```

## License

MIT

## Author Information

This role was created by jonimofo.