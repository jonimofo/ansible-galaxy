# Migrating to jonimofo.infrastructure 3.0.0

3.0.0 changes how the `dotfiles` role delivers files. It is a breaking release for hosts that use that role; the other roles are unchanged apart from bug fixes (see `CHANGELOG.md`).

## What changed

- `dotfiles`: the listed files are copied into the home as regular files. No clone and no symlink stay on the host. The host still fetches from the repo itself, through the forwarded SSH agent, into a temporary sparse checkout (one commit deep) that is deleted in the same run.
- `dotfiles`: a symlink at a destination, left by a 2.x run, is replaced by the file. The symlink target, inside the old clone, is not written.
- `dotfiles`: the old clone at `<home>/<clone_dir>` is deleted on every run once the files are copied, if it is a git clone of `dotfiles_user_configs.repo` with no uncommitted change. With uncommitted changes it is kept and the run prints a warning naming the path. Any other folder at that path is left alone.
- `dotfiles`: a file edited by hand on the host is overwritten on the next run. Edits belong in the repo.
- `dotfiles`: `--check --diff` fetches for real into the temporary directory and shows the diff of each file; a source missing from the repo fails in check mode too.
- `dotfiles`: git 2.24 or later on the host (every supported platform ships a newer one).

## Variable changes

| Role | Variable | Before | Now | Note |
|---|---|---|---|---|
| dotfiles | `dotfiles_user_configs.clone_dir` | where the repo was cloned | location of a pre-3.0 clone to clean up | default `.dotfiles` unchanged; keep the value you had so the old clone is found |
| dotfiles | `dotfiles_user_configs.version` | branch, tag or commit, shallow clone | branch, tag or commit, fetched one commit deep | a commit needs a server that allows fetching by id (GitHub, GitLab do) |

## What to do

1. Nothing in `group_vars` or `host_vars`: the variables keep their names and values.
2. Commit or discard any local change in the old clone on the hosts, or the clone is kept with a warning.
3. Run the playbook once with `--check --diff --limit <host>` and read the diff: each dotfile shows as replacing a link with a file.
4. Apply. A second run reports no change for the role.
