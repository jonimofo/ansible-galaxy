# Ansible Playbook: Neovim + AstroNvim Setup

## Overview
This Ansible playbook fully automates the installation of Neovim and the configuration of AstroNvim for one or more users on a target system.

The process is broken into two main stages and is fully **idempotent**, meaning you can run it multiple times without changing an already-completed setup.

1.  **Install Neovim**:
    * Automatically detects the target CPU architecture (e.g., `aarch64` for Raspberry Pi or `x86_64` for standard PCs) and downloads the correct Neovim binary.
    * Installs the binary to `/usr/local/bin/`.

2.  **Configure AstroNvim**:
    * For each specified user, it first checks if AstroNvim is already installed by looking for the `lazy.nvim` directory.
    * If not installed, it safely backs up any existing Neovim configurations (`~/.config/nvim`, `~/.local/share/nvim`, etc.) by renaming them with a `.bak` extension.
    * Clones the official AstroNvim template repository.
    * Removes the `.git` directory to allow for personal customization.

## Requirements
* **Ansible**: Must be installed on the machine you are running the playbook from.
* **Git**: Must be installed on the target machine(s).
* **Python**: Must be installed on the target machine(s) (standard Ansible requirement).

## Configuration
You can configure the playbook by editing the `vars` section of your `playbook.yml` file.

| Variable             | Default Value             | Description                                                                 |
| -------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `neovim_version`     | `v0.11.3`                 | The Neovim version tag to download from GitHub releases.                    |
| `neovim_binary_path` | `"/usr/local/bin/nvim"`   | The final path for the Neovim executable. Used for idempotency checks.      |
| `astronvim_users`    | `[]`                      | A list of user objects for whom AstroNvim should be installed. See example below. |


## Usage
1.  Create an inventory file (e.g., `inventory.yml`) to define the hosts you want to target.

    **inventory.yml**
    ```yaml
    all:
      hosts:
        pi:
          ansible_host: 192.168.1.100
          ansible_user: bgi
    ```

2.  Create your main playbook file (`playbook.yml`) and an associated `setup_user.yml` in the same directory. Populate them with the provided code.

3.  Modify the `vars` section in `playbook.yml` to define which users should receive the AstroNvim configuration.

    **playbook.yml (example `vars` section)**
    ```yaml
    vars:
      neovim_version: "v0.10.0"
      neovim_binary_path: "/usr/local/bin/nvim"
      astronvim_users:
        - name: "bgi"
        - name: "another_user"
    ```

4.  Run the playbook from your terminal:

    ```bash
    ansible-playbook playbook.yml -i inventory.yml
    ```
