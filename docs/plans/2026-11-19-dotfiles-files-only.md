Status: VALIDATED

# Dotfiles: files only, plus two fixes (3.0.0)

## Goal

The `dotfiles` role delivers only the listed files as real files, with no repo left on the host. The same release fixes the lazydocker check mode and duplicate `127.0.1.1` lines in `/etc/hosts`.

## Decisions

- Source of the files: the server fetches from the git repo itself through the forwarded SSH agent, as before. Nothing is fetched on the control node.
- What is left on the server: only the files. A temporary sparse, shallow checkout of the listed files is copied into the home as real files and deleted in the same run. No clone, no symlink: `~/.bashrc` is the file itself.
- Release: one mode, 3.0.0. Files-only replaces the clone for every consumer; no switch, one code path.
- Old clone: on every run, if `<home>/<clone_dir>` is a git clone whose origin is the configured repo, delete it after the files are copied. Any other folder is left alone. It is kept with a warning when it has uncommitted changes, ignored files, stashes or unpushed commits (on a local branch or a detached HEAD, held by no remote-tracking ref), or a git error while checking.
- The two bug fixes below ship in the same release.

## Behaviour of the dotfiles role

Before any fetch, `clone_dir` must be a non-empty relative path below the home (not `.`, no `..`), every `src` and `dest` relative without `..`, and `home` absolute. A user without `files`, or with `files: []`, is skipped entirely.

Per user in `dotfiles_user_configs.users`, keeping the become pattern that preserves agent forwarding for the connecting user, the per-user `home` key, the no-op when unconfigured, and `verify_ssh.yml` before any fetch:

1. Create a private temporary directory on the host, owned by the user.
2. Fetch `repo` at `version` into it: one commit deep, sparse checkout and blob filter limited to the listed `src` paths, through `ansible.builtin.command` with `argv`. New host keys are accepted as before.
3. Fail if a listed source is missing, with the existing message (credentials stripped from the URL).
4. For each file: ensure the parent of `dest` exists (the home's own mode is left alone), remove a symlink at `dest`, copy the file as a regular file owned by the user, executable bit kept.
5. Always delete the temporary directory, also on failure.
6. After the copies: delete `<home>/<clone_dir>` when its `.git` exists, its `remote.origin.url` is `repo` and `git status --porcelain --ignored` and `git rev-list --max-count=1 HEAD --branches --not --remotes` both succeed and print nothing, and `git rev-parse -q --verify refs/stash` finds no stash; otherwise keep it with a warning, never failing the play; never delete the home itself. After a deletion, report (never delete) links into the removed clone found at the home top level and in the parents of the listed destinations; leave anything else.

Idempotency and check mode: a second run reports `changed=0`. Temp dir, fetch and cleanup run in check mode too and never report a change; only the copy, the symlink removal and the old clone deletion can, and they respect check mode.

## Bugs

1. lazydocker: in check mode, when lazydocker needs installing or updating, `Extract lazydocker binary` failed with "Source ... does not exist" because the download was only simulated. astronvim (Neovim tarball) and fzf are checked for the same pattern.
2. host: `Update /etc/hosts with hostname` used `lineinfile` with `regexp: '^127\.0\.1\.1.*'`. A server whose `/etc/hosts` held three `127.0.1.1` lines (two tab-separated hostname lines and `127.0.1.1 srv1461727.hstgr.cloud srv1461727`) kept three identical lines. Required: exactly one `127.0.1.1` line, the role's own, idempotent, other lines untouched.
