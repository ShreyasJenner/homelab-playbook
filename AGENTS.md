# Homelab Playbook

This repo is the Playbook: the documentation for a self-hosted homelab (one host, homelab). Use the vocabulary in `GLOSSARY.md`. Decisions are in `docs/adr/`. The user-invoked skills for continuing the Playbook and for making homelab changes are listed in `SKILLS.md`.

## Pages

```
docs/
  hosts/      one host page per host
  services/   one service page per service, retired ones included (never-set-up services get none)
  runbooks/
  incidents/  YYYY-MM-DD-slug.md
  adr/
  research/   <topic>.md, one note per question researched
```

**Service page** header block:
```
Status:     live | retired (→ replacement)
Host:       homelab
Exposure:   tailnet-only | public
URL:        https://…
Config:     ~/docker/<service>/
Depends on: …
Verified:   unverified | YYYY-MM-DD
```
Sections: What it's for · Why this one · How it's set up · Runbooks · Incidents. A section with nothing in it is left out. A retired page is short: Status, Why retired, What replaced it. Software choices go in "Why this one", not in an ADR.

**Runbook**: Symptom → Check (commands) → Likely causes → Fix → Related incidents.

**Incident note**: Date · Status (open/resolved) · Service · Symptom · Cause · Fix · Runbook.

Links:
- Every runbook links its incidents, and every incident links its runbook.
- Every service page links its runbooks and incidents.
- The stack table in `docs/hosts/homelab.md` links every service page.
- After editing `docs/`, run `bash .claude/skills/homelab-playbook/check-links.sh`. It prints every broken link, and nothing when all are fine.

**Every debugging session ends with an incident note**, written in that session before `/clear`. A problem that has happened before also gets a runbook; a one-off gets the incident note only.

## Secrets and verification

- No secrets in the Playbook (ADR 0001). Write a placeholder such as `<JWT_SECRET>`, and say where the real value lives.
- The host is the source of truth (ADR 0002). Mark what's verified with the date. Anything known only from a chat is marked "Source: chat …, Unverified."

## Paste blocks

You can't reach the hosts; the user runs every command and pastes the output back.

- One block per step, wrapped in `{ … } 2>&1 | tee ~/<task>-<step>.txt`. Keep checks read-only. A change goes in its own block.
- Put `sudo` before every `docker` command.
- Print only the line or variable you need: `grep` for the key, or `grep -o` for the match. `.env` files, `app.ini`, a container's environment, `ntfy token list` and Uptime Kuma's `notification.config` all hold secrets, so they are only ever filtered, never shown whole.
- A change starts with a dated backup (`cp -p <file> <file>.bak-YYYYMMDD`) and ends with an undo line.

## Committing

- Pause so the user can skim before you commit.
- Commit only the files this session changed, never another session's uncommitted files.
