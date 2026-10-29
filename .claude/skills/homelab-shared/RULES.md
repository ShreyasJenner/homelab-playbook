# Homelab session rules

Shared by the `homelab-*` skills. This is a plain file, not a skill.

## Paste blocks

You can't reach the server; the user runs every command and pastes the output back.

- One block per step, wrapped in `{ … } 2>&1 | tee ~/<task>-<step>.txt`. Keep checks read-only. A change goes in its own block.
- Put `sudo` before every `docker` command.
- Print only the line or variable you need: `grep` for the key, or `grep -o` for the match. `.env` files, `app.ini`, a container's environment, `ntfy token list` and Uptime Kuma's `notification.config` all hold secrets, so they are only ever filtered, never shown whole.
- A change starts with a dated backup (`cp -p <file> <file>.bak-YYYYMMDD`) and ends with an undo line.

## Writing it up

- No secrets in the Playbook (ADR 0001). Write a placeholder such as `<JWT_SECRET>`, and say where the real value lives.
- The host is the source of truth (ADR 0002). Mark what's verified with the date. Anything known only from a chat is marked "Source: chat …, Unverified."
- Use the vocabulary in `GLOSSARY.md`.

## Committing

- Pause so the user can skim before you commit.
- Commit only the files this session changed, never another session's uncommitted files.
- End the commit message with the `Co-Authored-By` line.
- Keep the Progress section of `.scratch/playbook/plan.md` current as you go, so the work can resume if the session ends.
