# SSH Role

## Description
This role hardens the OpenSSH server configuration and manages SSH user access by setting secure defaults and deploying user-specific authorized keys.

## Requirements
- Ansible 2.10 or higher
- Target hosts must have OpenSSH installed (`openssh-server`)

## Role Variables
| Variable                       | Default    | Description                                                                                              |
|--------------------------------|------------|----------------------------------------------------------------------------------------------------------|
| `ssh_exclusive_keys`           | `false`    | When `true`, remove all existing `authorized_keys` entries before adding the ones defined in `ssh_users`. |
| `ssh_max_auth_tries`           | `3`        | Maximum number of authentication attempts permitted per connection.                                       |
| `ssh_strict_host_key_checking` | `ask`      | Value for SSH’s `StrictHostKeyChecking` setting (`yes`, `no`, `ask`, or `accept-new`).                   |
| `ssh_users`                    | `[]`       | List of user definitions to configure. Each item is a dict with `name`, `pubkey`, and optional `home`.   |

## Dependencies
None.

## Example Playbook
```yaml
- hosts: all
  become: true

  collections:
    - jonimofo.infrastructure

  vars:
    ssh_strict_host_key_checking: "no"
    ssh_exclusive_keys: true
    ssh_max_auth_tries: 3
    ssh_users:
      - name: alice
        pubkey: "{{ lookup('file', 'files/alice.pub') }}"
      - name: bob
        pubkey: "{{ lookup('file', 'files/bob.pub') }}"
        home: /home/bob

  roles:
    - ssh
````

## License

MIT

## Author Information

* **Name**: Jonimofo
* **GitHub**: [https://github.com/jonimofo](https://github.com/jonimofo)
* **Galaxy**: [https://galaxy.ansible.com/jonimofo/infrastructure](https://galaxy.ansible.com/jonimofo/infrastructure)

