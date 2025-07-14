# Ansible Role: ssh

This role secures an OpenSSH server on **Debian-based systems**. It applies common security hardening practices such as disabling password and root login, and it configures user access exclusively through a managed list of public keys.

## Requirements

* This role is designed **exclusively for Debian-based distributions** and will fail to run on other OS families.
* The `ansible.posix` collection must be installed: `ansible-galaxy collection install ansible.posix`.

## Role Variables

Default values are located in `defaults/main.yml`.

| Variable | Default Value | Description |
|---|---|---|
| `ssh_exclusive_keys` | `false` | If `true`, removes any unmanaged public keys from a user's `authorized_keys` file. |
| `ssh_strict_host_key_checking` | `ask` | Sets the `StrictHostKeyChecking` option in the client configuration `/etc/ssh/ssh_config`. |
| `ssh_max_auth_tries` | `3` | Sets the maximum number of authentication attempts allowed per connection. |

**`ssh_users`**: This is the primary variable for defining who can access the server. It is a list of dictionaries, where each dictionary represents a user.

* `name`: The username. (Required)
* `pubkey`: The user's full public SSH key. (Required)

**Example `ssh_users` structure:**
```yaml
ssh_users:
  - name: "alice"
    pubkey: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... alice@example.com"
  - name: "bob"
    pubkey: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQ... bob@workstation"
```

## Dependencies

This role has no dependencies on other Ansible Galaxy roles.

## Example Playbook

Here is an example of how to use this role to configure a server for two users.

```yaml
- name: Harden SSH and configure user access
  hosts: all
  become: true
  vars:
    ssh_users:
      - name: "jdoe"
        pubkey: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGoT... jdoe@laptop"
      - name: "service_account"
        pubkey: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIX8T... ansible@controller"
  roles:
    - jonimofo.ssh
```

## License

MIT

## Author Information

This role was created by jonimofo.