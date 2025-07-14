# Ansible Role: dotfiles

An Ansible role that clones a dotfiles Git repository and creates symbolic links to the specified configuration files for one or more users on the system.

## Requirements

The `git` package must be installed on the managed node for the `ansible.builtin.git` module to function correctly.

## Role Variables

The primary variable for this role is `dotfiles_user_configs`. It is a dictionary that defines the repository and the users to configure.

- `dotfiles_user_configs.repo`: The URL of the Git repository containing the dotfiles. (Required)
- `dotfiles_user_configs.version`: The branch, tag, or commit to check out. (Default: `main`)
- `dotfiles_user_configs.clone_dir`: The directory name within the user's home where the repository will be cloned. (Default: `.dotfiles`)
- `dotfiles_user_configs.users`: A list of user objects to configure.
    - `user`: The username. (Required)
    - `home`: The absolute path to the user's home directory. (Optional, defaults to `/home/<username>`)
    - `files`: A list of files to symlink.
        - `src`: The path to the source file within the cloned repository. (Required)
        - `dest`: The destination path for the symlink within the user's home directory. (Required)

Here is an example of the data structure defined in `defaults/main.yml`:

```yaml
dotfiles_user_configs:
  repo: '[https://github.com/example/dotfiles.git](https://github.com/example/dotfiles.git)'
  version: 'main'
  clone_dir: '.dotfiles'
  users:
    - user: alice
      files:
        - src: 'bash/bashrc'
          dest: '.bashrc'
        - src: 'vim/vimrc'
          dest: '.vimrc'
    - user: bob
      home: '/var/lib/bob'
      files:
        - src: 'zsh/zshrc'
          dest: '.zshrc'
```

## Dependencies

This role has no dependencies on other Ansible Galaxy roles.

## Example Playbook

Here is an example of how to use this role in a playbook:

```yaml
- name: Configure user dotfiles
  hosts: servers
  become: true
  vars:
    dotfiles_user_configs:
      repo: '[https://github.com/my-org/dotfiles.git](https://github.com/my-org/dotfiles.git)'
      version: 'production'
      clone_dir: '.config/dotfiles'
      users:
        - user: ansible
          files:
            - src: 'tmux.conf'
              dest: '.tmux.conf'
            - src: 'profile'
              dest: '.profile'
  roles:
    - your_galaxy_username.dotfiles
```

## License

MIT

## Author Information

This role was created by bgi.
