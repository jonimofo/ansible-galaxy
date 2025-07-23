# Ansible Role: dotfiles

This role clones a specified dotfiles Git repository and creates symlinks to user home directories based on a defined configuration. It is designed to manage dotfiles for multiple users on a system in an idempotent way.

## Requirements

The `git` package must be installed on the target hosts for the `ansible.builtin.git` module to function correctly. This role does not install `git`.

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
# A list containing the dotfiles configuration.
dotfiles_user_configs:
  # The SSH or HTTPS URL of the git repository.
  repo: 'git@github.com:example/dotfiles.git'

  # The branch, tag, or commit hash to check out.
  version: 'main'

  # The directory name within the user's home where the repo will be cloned.
  clone_dir: '.dotfiles'

  # A list of users to apply the dotfiles to.
  users:
    # A user object.
    - user: 'bobjones'
      # Optional: specify a non-standard home directory.
      # Defaults to '/home/{{ user.user }}' if not set.
      home: '/home/bobjones'
      # A list of files to symlink.
      files:
        # The source file path, relative to the root of the cloned git repo.
        - src: 'bash/bashrc'
          # The destination for the symlink, relative to the user's home directory.
          dest: '.bashrc'
        - src: 'vim/vimrc'
          dest: '.vimrc'
        - src: 'config/htop/htoprc'
          dest: '.config/htop/htoprc'

    - user: 'alice'
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
      repo: 'git@github.com:jonimofo/dotfiles.git'
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
    - jonimofo.infrastructure.dotfiles
```

## License

MIT

## Author Information

This role was created by bgi.
