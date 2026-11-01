---
name: homelab-install
description: Install a new service on homelab through paste blocks the user runs, then record it in the Playbook. Use when the user asks to install, set up or add a service, or another skill concludes one should be installed.
argument-hint: "[exact service, e.g. linkding]"
---

Service: $ARGUMENTS

You can't reach the host: every command is a paste block the user runs (rules in `AGENTS.md`). Page templates, links, secrets and commits also follow `AGENTS.md`. This skill installs on homelab only.

## Steps

1. **Name the service.** The input must be one exact piece of software, such as "linkding". If it's a need or a category instead ("a bookmark manager", "something for recipes"), or a choice between candidates, stop and tell the user to run `/homelab-research <topic>` first. That skill can only be started by the user. Done when one exact service is named.
2. **Load context.** Read `GLOSSARY.md`, `docs/adr/`, `docs/hosts/homelab.md` (stack table, `DEFAULT_STACKS`, backups), `docs/services/caddy.md` (port table), any `docs/research/` note that names the service, and its service page if one exists. A retired page means this is a reinstall: read why it was retired. Done when you can list the ports and subdomains already in use, and say whether a research note or an old page exists.
3. **Grill for the install decisions.** Invoke the `grilling` skill. Put only decisions to the user:
   - Exposure: tailnet-only by default (ADR 0004); public needs a reason and the service's own hardening (2FA, no open sign-ups).
   - the subdomain under `example.com`, and the host port;
   - Users: who gets an account, and whether instances are per-User;
   - data location: `~/docker/<service>/` on the NVMe, or the 4 TB disk for media;
   - the image tag: pinned, or `latest` like most stacks;
   - extras: Homepage tile, Uptime Kuma monitor, ntfy alerts.

   Facts come from the Playbook and upstream docs, never from the user. Done when the frontier is empty and the user confirms.
4. **Draft from upstream.** Read the project's official install docs and example compose file. Draft `docker-compose.yml` and the `.env` keys (values as placeholders such as `<DB_PASSWORD>`). Done when every compose value (image, internal port, volumes, user/uid, health endpoint, dependencies such as a database or Redis) cites its upstream source or is marked as a decision from step 3.
5. **Install.** One paste block per stage, waiting for the output each time. A change starts with a dated backup and ends with a check of the target state and an undo line.
   1. **Pre-check** (read-only): the port is free (`ss -ltn`), the subdomain isn't in the Caddyfile, `~/docker/<service>/` doesn't exist (or, on a reinstall, what's in it), free space on the target disk.
   2. **Stack:** create the folder, compose file and `.env`. Generate secrets on the host (`openssl rand -hex 32`) straight into `.env`, never printed. `sudo docker compose up -d`, then check the container stays up and `curl` its health endpoint on `127.0.0.1:<port>`.
   3. **Caddy:** back up the Caddyfile, add the `@<name> host` matcher and `reverse_proxy localhost:<port>`, run `caddy validate`, then `caddy reload`, then `curl -I https://<name>.example.com`.
   4. **Wiring:** add the stack to `DEFAULT_STACKS` in `~/docker/stacks.sh`. Data outside `~/docker` isn't backed up: say so and ask whether to add a follow-up.
   5. **Browser steps** for the user: create the admin account, turn off open sign-ups, add the Uptime Kuma monitor and Homepage tile chosen in step 3.

   Done when `https://<name>.example.com` answers and every chosen extra is in place. When a check doesn't show the target state, diagnose with the `homelab-debug` skill before going on.
6. **Record.** In this session, before `/clear`:
   - the service page from the `AGENTS.md` template, `Verified: <date>`, with "Why this one" linking the research note; on a reinstall, rewrite the retired page as live;
   - a row in the stack table of `docs/hosts/homelab.md`, linking the page;
   - a row in the port table of `docs/services/caddy.md`;
   - the Homepage and Uptime Kuma pages, if the extras touched them;
   - the research note's service page links, if a note exists;
   - each thing put off (backup coverage, a missing monitor, hardening) as a follow-up in `.claude/skills/homelab-followups/FOLLOWUPS.md`, with drafted commands in its `HOWTO.md`;
   - an incident note for anything that went wrong on the way, plus a runbook if it has happened before.

   Done when `bash .claude/skills/homelab-playbook/check-links.sh` prints nothing.
7. **Pause, then commit** following `AGENTS.md`.

## Pitfalls

- **An app's own port setting is the port inside the container.** It must match the right-hand side of `ports:` ([2026-10-21](../../../docs/incidents/2026-10-21-memos-connection-reset-port-mismatch.md)).
- **Publish on `127.0.0.1:<port>:<internal>`.** Caddy runs in host network mode, so it reaches loopback; `0.0.0.0` also exposes the service to the home LAN (follow-up 4).
- **Validate before every Caddy reload.** A Caddyfile brace error once crash-looped Caddy and took every tailnet service down with it.
- **The nightly backup stops every stack.** A service that mustn't be interrupted mid-job, or keeps a database outside its bind mounts, needs saying on its page.
- **Blocks run in bash on the host and in zsh on the laptop.** Name loop variables `p` or `u`: in zsh, `path` is tied to `PATH`. Quote decorative separators (`echo '---'`): in zsh, a word that starts with `=` is expanded as a command path.
