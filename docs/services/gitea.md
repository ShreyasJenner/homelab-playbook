# Gitea

```
Status:     live (since about 2026-10-21)
Host:       homelab
Exposure:   tailnet-only: web through Caddy; SSH through Tailscale Serve TCP (:8313 → localhost:8312).
            8310 and 8312 are published on 0.0.0.0, so also reachable from the home LAN
URL:        https://gitea.example.com
            SSH: git@gitea:<owner>/<repo>.git, through the client's ~/.ssh/config alias `gitea`
Config:     ~/docker/gitea/ (docker-compose.yml; .env: LOCAL_WEBSERVER_PORT=8310, LOCAL_SSH_PORT=8312, UID, GID;
            gitea/ → /data; app.ini at ~/docker/gitea/gitea/gitea/conf/app.ini — never cat it, it holds secrets)
Depends on: Caddy (web); Tailscale Serve (SSH); SQLite (built in)
Per-User:   no; one account (ShreyasJenner, admin, 2FA off)
Verified:   2026-10-28
```

## What it's for

Hosting personal Git repos, including this Playbook.

## How it's set up

- Image **`docker.gitea.com/gitea:28.2.0`, pinned**, so `stacks.sh update` won't change it until the tag is edited. `restart: always`, network `gitea_gitea`.
- `USER_UID`/`USER_GID` 1000. Mounts: `~/docker/gitea/gitea → /data`, plus `/etc/timezone` and `/etc/localtime` read-only.
- Ports: `8310 → 3000` (web) and `8312 → 22` (the image's own SSH server).
- **`app.ini` `[server]`** (2026-10-28): `DOMAIN = gitea`, `ROOT_URL = https://gitea`, `HTTP_PORT = 3000`, `SSH_LISTEN_PORT = 22`, `DISABLE_SSH = false`. `SSH_DOMAIN` and `SSH_PORT` aren't set, so they default to `gitea` and `22`.
- `[service]`: `DISABLE_REGISTRATION = true`, `REQUIRE_SIGNIN_VIEW = true`. `DB_TYPE = sqlite3`.
- **Gitea writes env settings into `app.ini`.** Removing an env var from compose doesn't undo it; edit `app.ini` and restart ([2026-10-24](../incidents/2026-10-24-gitea-down-after-app-ini-edits.md)).
- Health: `https://gitea.example.com/api/healthz` returns `"status": "pass"`. Uptime Kuma doesn't monitor Gitea.

### SSH and clone URLs

SSH reaches the container only through the Serve TCP entry (`tailscale serve --bg --tcp=8313 tcp://localhost:8312`). Caddy can't carry SSH, and a `tailscale serve reset` wipes the entry.

The clone URLs Gitea shows (`git@gitea:…`) only work on a machine with this alias in `~/.ssh/config`:

```
Host gitea
    HostName homelab.tail0000.ts.net
    User git
    Port 8313
    IdentityFile ~/.ssh/id_gitea
```

That's how this laptop is set up (key "Laptop" in Gitea). Add `IdentitiesOnly yes` if the agent offers the wrong key first.

**Push identity:** the SSH key decides which Gitea account a push is credited to. Commit authorship comes from `user.name`/`user.email`. A per-remote identity is set with `[includeIf "hasconfig:remote.*.url:git@gitea:*/**"]` → `~/.gitconfig-gitea` (git 2.36 or newer; the block goes after the default `[user]`). Check with `git config --show-origin user.email`.

## Known issues

- **`ROOT_URL = https://gitea`** is wrong behind Caddy. The HTTPS clone URL and any absolute links Gitea generates point at `https://gitea/`. It should be `https://gitea.example.com/`, with `DOMAIN = gitea.example.com` (follow-up 18).
- **2FA is off** on the only account.
- bob's Homepage links to Gitea, but they have no account, and registration is off. That's deliberate.

## Runbooks

- [Gitea SSH clone or push fails](../runbooks/gitea-ssh-clone-or-push-fails.md)
- [Connection reset after choosing or changing a port](../runbooks/connection-reset-after-port-change.md)
- [A service's address changed](../runbooks/service-address-changed.md)

## Incidents

- [2026-10-22: SSH clone closed the connection](../incidents/2026-10-22-gitea-ssh-clone-connection-closed.md)
- [2026-10-24: Gitea down after `app.ini` edits](../incidents/2026-10-24-gitea-down-after-app-ini-edits.md)
