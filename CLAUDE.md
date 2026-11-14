# Notes for Claude

## Always push finished work

The owner wants changes pushed to GitHub automatically. When you finish a change,
commit it and push to `main` without asking.

- `git` is not on PATH. Use GitHub Desktop's bundled git: search
  `%LOCALAPPDATA%\GitHubDesktop` for `resources\app\git\cmd\git.exe`
  (the `app-<version>` folder changes when GitHub Desktop updates).
- GitHub login comes from the GitHub CLI (`C:\Program Files\GitHub CLI\gh.exe`),
  wired up as git's credential helper for github.com.
- A GitHub Action commits to `main` every 5 hours, so run `git pull --rebase`
  before pushing.
- Write short, plain commit messages that say what changed.
