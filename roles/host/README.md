# Ansible Role: host

This role configures the system's hostname. It sets the transient and permanent hostname and ensures the new hostname is correctly mapped to `127.0.1.1` in `/etc/hosts`, following Debian/Ubuntu conventions.

## Requirements

There are no special requirements for this role. It uses standard `ansible.builtin` modules.

## Role Variables

This role does not have any default variables. It requires the following variable to be set by the user:

* **`desired_hostname`**: The fully qualified domain name (FQDN) to set as the system's hostname. This variable is **required**, and the role will fail if it is not defined.

## Example Playbook

Here is an example of how to use this role to set a server's hostname.

```yaml
- name: Configure system hostname
  hosts: servers
  become: true
  vars:
    desired_hostname: "webserver01.example.com"
  roles:
    - jonimofo.host
```

## License

MIT

## Author Information

This role was created by jonimofo.