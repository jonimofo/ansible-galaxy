# Ansible Role: docker_compose_app

Deploys Docker Compose applications from private git repositories with systemd service management.

## Features

- **Deployment modes** - Full deploy, update, build, or restart only
- Creates dedicated system user with docker group membership
- Clones private git repositories using SSH agent forwarding
- Manages secret directories with flexible ownership (supports container UIDs)
- Sets ownership and permissions on secret files automatically
- **Frontend build support** - Run build commands after git pull
- Generates systemd service unit for application lifecycle management
- Supports multiple compose files and profiles
- Configurable restart policies and timeouts

## Requirements

- **Ansible version:** 2.12+
- **Supported OS:** Debian-based systems only
  - Debian (bullseye, bookworm, trixie)
  - Ubuntu (focal, jammy, noble)
  - Raspberry Pi OS
- **Supported architectures:** x86_64, aarch64, armv7l
- **Privileges:** Requires `become: true`
- **Dependencies:**
  - Docker and Docker Compose must be installed
  - SSH agent forwarding enabled (for private repo cloning)

## Role Variables

All variables are defined in `defaults/main.yml`:

### Deployment Mode

Control which tasks run using the `docker_compose_app_mode` variable:

| Mode | Git | Dirs | Permissions | Build | Service | Use Case |
|------|-----|------|-------------|-------|---------|----------|
| `deploy` | ✅ | ✅ | ✅ | ✅ | ✅ | Full deployment |
| `update` | ❌ | ✅ | ✅ | ❌ | ✅ | Quick restart, fix permissions |
| `build` | ❌ | ✅ | ✅ | ✅ | ✅ | Rebuild frontend only |
| `restart` | ❌ | ❌ | ❌ | ❌ | ✅ | Just restart service |

| Variable | Default | Description |
|----------|---------|-------------|
| `docker_compose_app_mode` | `deploy` | Deployment mode (see table above) |
| `docker_compose_app_build_command` | `""` | Command to build frontend (e.g., `make front-build`) |

**Usage:**

```bash
# Full deployment (default)
ansible-playbook site.yml

# Quick update - fix permissions and restart (no git pull)
ansible-playbook site.yml -e docker_compose_app_mode=update

# Rebuild frontend and restart (no git pull)
ansible-playbook site.yml -e docker_compose_app_mode=build

# Just restart the service
ansible-playbook site.yml -e docker_compose_app_mode=restart
```

### Application Identity

| Variable | Default | Description |
|----------|---------|-------------|
| `docker_compose_app_name` | `""` | **Required.** Unique name for this application |
| `docker_compose_app_description` | `"Docker Compose Application"` | Description for systemd unit |

### User Management

| Variable | Default | Description |
|----------|---------|-------------|
| `docker_compose_app_user` | `"{{ docker_compose_app_name }}"` | System user to run the stack |
| `docker_compose_app_user_uid` | `""` | Specific UID (optional) |
| `docker_compose_app_user_create` | `true` | Create the user if not exists |
| `docker_compose_app_user_shell` | `/usr/sbin/nologin` | User shell |
| `docker_compose_app_user_groups` | `[]` | Additional groups (docker is always added) |

### Directory Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `docker_compose_app_dir` | `/opt/{{ name }}` | App directory (git clone destination) |
| `docker_compose_app_dir_mode` | `"0755"` | App directory permissions |

### Container Permissions

For apps where the container runs as a different UID than the host user (common with Laravel, Node.js apps):

| Variable | Default | Description |
|----------|---------|-------------|
| `docker_compose_app_container_uid` | `""` | UID the container runs as (e.g., `1000`) |
| `docker_compose_app_container_gid` | `""` | GID the container runs as (defaults to UID) |
| `docker_compose_app_writable_dirs` | `[]` | Directories to chown (relative paths) |
| `docker_compose_app_writable_files` | `[]` | Files to chown (relative paths) |
| `docker_compose_app_remove_hot_file` | `false` | Remove Vite hot file for production |

Example for Laravel:
```yaml
docker_compose_app_container_uid: "1000"
docker_compose_app_writable_dirs:
  - storage
  - bootstrap/cache
docker_compose_app_writable_files:
  - .env
docker_compose_app_remove_hot_file: true
```

### Secrets Directories

| Variable | Default | Description |
|----------|---------|-------------|
| `docker_compose_app_secrets_base_dir` | `/home/{{ ansible_user }}/.secrets` | Base directory for secrets |
| `docker_compose_app_secrets` | `[]` | List of secret directories (see below) |
| `docker_compose_app_secrets_default_mode` | `"0700"` | Default directory mode |
| `docker_compose_app_secrets_file_default_mode` | `"0600"` | Default file mode |

#### Secret Directory Options

| Option | Required | Description |
|--------|----------|-------------|
| `name` | Yes | Directory name |
| `path` | No | Full path (defaults to base_dir/name) |
| `owner` | No | Owner UID/name (defaults to app user) |
| `group` | No | Group GID/name (defaults to owner) |
| `mode` | No | Directory permissions |
| `files` | No | List of expected files with their permissions |

#### Secret File Options

| Option | Required | Description |
|--------|----------|-------------|
| `name` | Yes | File name |
| `owner` | No | Owner UID/name (defaults to directory owner) |
| `group` | No | Group GID/name (defaults to owner) |
| `mode` | No | File permissions (defaults to 0600) |

### Git Repository

| Variable | Default | Description |
|----------|---------|-------------|
| `docker_compose_app_git_repo` | `""` | **Required.** Git repo URL (SSH format) |
| `docker_compose_app_git_version` | `"main"` | Branch, tag, or commit |
| `docker_compose_app_git_force_update` | `true` | Force update (discard local changes) |
| `docker_compose_app_git_accept_hostkey` | `true` | Accept new SSH host keys |
| `docker_compose_app_git_clone_as_ansible_user` | `true` | Use ansible_user's SSH agent |
| `docker_compose_app_git_key_file` | `""` | SSH key path (when not using agent) |

### Docker Compose Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `docker_compose_app_compose_file` | `"docker-compose.yml"` | Compose file(s) |
| `docker_compose_app_compose_profiles` | `[]` | Profiles to activate |
| `docker_compose_app_env_file` | `""` | Environment file path |
| `docker_compose_app_pull_on_start` | `true` | Pull images on start |
| `docker_compose_app_remove_orphans` | `true` | Remove orphan containers |

### Systemd Service

| Variable | Default | Description |
|----------|---------|-------------|
| `docker_compose_app_service_enabled` | `true` | Enable the service |
| `docker_compose_app_service_state` | `"started"` | Desired state |
| `docker_compose_app_service_restart_policy` | `"on-failure"` | Restart policy |
| `docker_compose_app_service_restart_sec` | `10` | Restart delay |
| `docker_compose_app_service_timeout_start_sec` | `300` | Start timeout |
| `docker_compose_app_service_timeout_stop_sec` | `120` | Stop timeout |
| `docker_compose_app_service_environment` | `{}` | Additional env vars |
| `docker_compose_app_docker_compose_cmd` | `"docker compose"` | Compose command (v2) |

## Dependencies

None. However, Docker and Docker Compose must be pre-installed.

## Example Playbook

### Basic Usage

```yaml
- name: Deploy Traefik stack
  hosts: docker_hosts
  become: true
  vars:
    docker_compose_app_name: astrohub
    docker_compose_app_git_repo: "git@github.com:user/astrohub.git"
    docker_compose_app_dir: /opt/astrohub
    docker_compose_app_secrets_base_dir: /home/bgi/.secrets
    docker_compose_app_secrets:
      - name: cloudflare-astrolabvn
        owner: 65532
        group: 65532
        files:
          - name: cf-token
            mode: "0600"
      - name: tinyauth
        owner: 65532
        group: 65532
        files:
          - name: tinyauth_users
            mode: "0600"
  roles:
    - role: geerlingguy.docker
    - role: jonimofo.infrastructure.docker_compose_app
```

### With Custom User UID

```yaml
- name: Deploy app with specific user UID
  hosts: docker_hosts
  become: true
  vars:
    docker_compose_app_name: myapp
    docker_compose_app_user: traefik
    docker_compose_app_user_uid: 65532
    docker_compose_app_git_repo: "git@github.com:user/myapp.git"
  roles:
    - role: jonimofo.infrastructure.docker_compose_app
```

### Multiple Compose Files

```yaml
- name: Deploy with override file
  hosts: docker_hosts
  become: true
  vars:
    docker_compose_app_name: myapp
    docker_compose_app_git_repo: "git@github.com:user/myapp.git"
    docker_compose_app_compose_file:
      - docker-compose.yml
      - docker-compose.prod.yml
    docker_compose_app_compose_profiles:
      - monitoring
  roles:
    - role: jonimofo.infrastructure.docker_compose_app
```

### With Environment File

```yaml
- name: Deploy with environment file
  hosts: docker_hosts
  become: true
  vars:
    docker_compose_app_name: myapp
    docker_compose_app_git_repo: "git@github.com:user/myapp.git"
    docker_compose_app_env_file: /opt/myapp/.env
    docker_compose_app_service_environment:
      COMPOSE_PROJECT_NAME: myapp
      TZ: Asia/Ho_Chi_Minh
  roles:
    - role: jonimofo.infrastructure.docker_compose_app
```

### Laravel App with Frontend Build

```yaml
- name: Deploy Laravel application
  hosts: docker_hosts
  become: true
  vars:
    docker_compose_app_name: myapp
    docker_compose_app_git_repo: "git@github.com:user/myapp.git"
    docker_compose_app_build_command: "make front-build"
    docker_compose_app_container_uid: "1000"
    docker_compose_app_writable_dirs:
      - storage
      - bootstrap/cache
      - resources/js/actions
      - resources/js/routes
      - resources/js/wayfinder
    docker_compose_app_writable_files:
      - .env
    docker_compose_app_remove_hot_file: true
  roles:
    - role: geerlingguy.docker
    - role: jonimofo.infrastructure.docker_compose_app
```

Then use different modes for different operations:

```bash
# Initial deployment or code update
ansible-playbook site.yml

# Rebuild frontend only (after CSS/JS changes)
ansible-playbook site.yml -e docker_compose_app_mode=build

# Quick restart (fix permissions issues)
ansible-playbook site.yml -e docker_compose_app_mode=update

# Just restart containers
ansible-playbook site.yml -e docker_compose_app_mode=restart
```

## Platform Notes

### Raspberry Pi OS

Raspberry Pi OS is fully supported:
- ARM64 Docker images are increasingly available
- Consider memory constraints for large stacks
- Use `docker_compose_app_pull_on_start: false` if bandwidth is limited

### Debian / Ubuntu

Standard Debian and Ubuntu installations are fully supported.

## Security Considerations

### SSH Agent Forwarding

This role uses SSH agent forwarding by default (`docker_compose_app_git_clone_as_ansible_user: true`):
- No SSH keys are stored on the target system
- Requires `ForwardAgent yes` in SSH config
- More secure than deploying keys to targets

### Secret File Management

- Secret directories are created with mode `0700` by default
- Secret files are set to mode `0600` by default
- The role manages ownership/permissions but NOT file contents
- Use container UIDs (e.g., 65532) for file ownership when containers run as non-root
- Missing files trigger helpful debug output showing manual placement commands

### System User

- Created as a system user with `nologin` shell by default
- Added to `docker` group for socket access
- Consider security implications of docker group membership

### Recommendations

1. **Always use SSH agent forwarding** for private repos
2. **Use specific UIDs** matching container user requirements
3. **Never commit secrets** to the git repository
4. **Set restrictive modes** on secret directories and files
5. **Use `docker_compose_app_git_force_update: true`** for immutable deployments

## What This Role Does

Depending on the mode, the role runs these steps:

| Step                                | deploy | update | build | restart |
|-------------------------------------|--------|--------|-------|---------|
| 2. Validate required variables      | ✅     | ✅     | ✅    | ✅      |
| 1. Verify Debian-based system       | ✅     | ✅     | ✅    | ✅      |
| 3. Ensure git is installed          | ✅     | ❌     | ❌    | ❌      |
| 4. Create system user               | ✅     | ❌     | ❌    | ❌      |
| 5. Create app + secrets directories | ✅     | ✅     | ✅    | ❌      |
| 6. Clone/update git repository      | ✅     | ❌     | ❌    | ❌      |
| 7. Set container permissions        | ✅     | ✅     | ✅    | ❌      |
| 8. Run build command                | ✅     | ❌     | ✅    | ❌      |
| 9. Deploy systemd unit              | ✅     | ✅     | ✅    | ✅      |
| 10. Enable and start service        | ✅     | ✅     | ✅    | ✅      |


## Manual Steps Required

After first playbook run, you must place secret files:

```bash
# Place secret files
sudo cp /path/to/cf-token /home/bgi/.secrets/cloudflare-astrolabvn/cf-token
sudo cp /path/to/tinyauth_users /home/bgi/.secrets/tinyauth/tinyauth_users

# Re-run playbook to set correct ownership/permissions
ansible-playbook playbook.yml --tags docker_compose_app
```

On subsequent runs, the role automatically ensures correct ownership/permissions on all defined secret files.

## Service Management

```bash
# Check service status
sudo systemctl status astrohub

# View logs
sudo journalctl -u astrohub -f

# Restart (pulls new images and recreates)
sudo systemctl restart astrohub

# Stop
sudo systemctl stop astrohub

# Reload (same as restart for Type=oneshot)
sudo systemctl reload astrohub
```

## License

GPL-2.0-or-later

## Author Information

jonimofo
