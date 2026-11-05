# Vaultwarden

```
Status:     live (since 2026-10-15)
Host:       homelab
Exposure:   tailnet-only (binds 127.0.0.1:9734 only; Caddy is the only way in)
URL:        https://vault.example.com (health: /alive)
Config:     ~/docker/vaultwarden/ (docker-compose.yml; .env with ADMIN_TOKEN; data/ → /data:
            db.sqlite3, rsa_key*, attachments)
Depends on: Caddy (Bitwarden clients require HTTPS); Tailscale on every client that syncs
Per-User:   no; one instance, one account per User (ShreyasJenner, bob)
Verified:   2026-10-28; 2026-11-05 (accounts, 2FA)
```

## What it's for

The password manager for every homelab login and beyond, through the official Bitwarden apps and browser extension.

## Why this one

It was on the original wish list for the server. On 2026-06-27 it was compared with official self-hosted Bitwarden (heavier, licensed), Passbolt (team-oriented) and KeePassXC with Syncthing (no server). Vaultwarden is one small container that works with every Bitwarden client, with the premium features free. It was set up after Authentik was dropped (2026-10).

## How it's set up

- Image `vaultwarden/server:latest`, runs as `1000:1000`, port `127.0.0.1:9734 → 80` (`ROCKET_PORT=80`).
- Env (2026-10-28): `SIGNUPS_ALLOWED=false`, `INVITATIONS_ALLOWED=false`, `LOG_LEVEL=warn`, `TZ=Etc/UTC`.
- **`ADMIN_TOKEN` is set in `.env`, so the admin panel (`/admin`) is enabled.** The token is an Argon2 hash; keep it single-quoted in `.env` because of its `$` signs. There's no `data/config.json`. Settings saved in the admin panel would go there and override the env vars.
- **Data** is a bind mount, `~/docker/vaultwarden/data`, so restic backs it up (a cold copy at 02:30).
- **Accounts:** ShreyasJenner and bob, both created on 2026-10-15. Each User has their own vault. Verified 2026-11-05 from the `users` table.
- **2FA (follow-up 22, done 2026-11-05):** both accounts use an authenticator app (TOTP) and have a recovery code. Verified 2026-11-05 with read-only `sqlite3` queries: one enabled `twofactor` row per user, and `totp_recover` set on both. Vaultwarden can't enforce 2FA server-wide, so a new account has to turn it on itself, under Settings → Security → Two-step login. WebAuthn (passkey or security key) waits for follow-up 16, because it's bound to `DOMAIN`.
  - **The recovery codes are in Proton Drive**, not in Vaultwarden or Nextcloud. The Nextcloud backup codes are in Vaultwarden, so keeping these recovery codes in Nextcloud would lock both services if the phone were lost. Keep them somewhere that needs neither service.
- Uptime Kuma checks `http://localhost:9734/alive`, with ntfy alerts.
- **Updates** come through a plain `stacks.sh update`: it's in `DEFAULT_STACKS` since 2026-10-30 (follow-up 12, done). That day's update found nothing newer: the container runs 1.37.4 (image built 2026-10-05), the current `latest`. Verified 2026-10-30.

### Clients

- Log out, choose region "Self-hosted", and enter `https://vault.example.com` with no trailing slash. Tailscale must be on to sync.
- **URI matching:** the default is "Base domain". Every homelab service shares `example.com`, so with Base domain every saved homelab login would be offered on every service. **Each saved homelab login is set to "Host".**

## Known issues

- **`DOMAIN` is still the old `https://homelab.tail0000.ts.net:9758`.** That's the pre-Caddy address, and its port isn't even the real one. Vaultwarden uses `DOMAIN` for WebAuthn/passkeys, attachment links, email links and the admin page. Set it to `https://vault.example.com`, then `sudo docker compose up -d` (follow-up 16). Do this before using a passkey or security key for 2FA. The `DOMAIN` grep on 2026-11-05 found no `DOMAIN=` line in `docker-compose.yml` or `.env`, so it's probably written in YAML form (`DOMAIN: …`). Check with `grep -n 'DOMAIN'`.
- **The restic password must not live only in Vaultwarden.** Restoring Vaultwarden needs the restic password, so that would be circular (follow-up 5).

## Runbooks

- [A service's address changed](../runbooks/service-address-changed.md)
- [Updating containers](../runbooks/updating-containers.md)
