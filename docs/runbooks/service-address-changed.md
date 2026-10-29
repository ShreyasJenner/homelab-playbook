# A service's address changed

When a service moves to a new URL (for example from a `ts.net:<port>` Serve address to `<name>.example.com`), any app that stores its own address breaks in quiet ways: passkeys, CORS, generated links, allowed hosts. Uptime Kuma checks `localhost`, so it won't notice.

## Checklist

| Service | What to update |
|---|---|
| Vaultwarden | `DOMAIN` in compose/`.env`; every Bitwarden client's server URL; saved item URIs |
| Mindwtr | `MINDWTR_CLOUD_CORS_ORIGIN` (browser sync only); each device's sync URL |
| Gitea | `ROOT_URL`, `DOMAIN`, `SSH_DOMAIN`/`SSH_PORT` in `app.ini`; each client's `~/.ssh/config` alias |
| Homepage | `HOMEPAGE_ALLOWED_HOSTS`; tile `href`s |
| Memos | the server URL in each client |
| ntfy | `NTFY_BASE_URL`; the server URL in the phone app |
| Nextcloud | `trusted_domains`, `overwrite.cli.url`, `trusted_proxies`; each client's account; Euro-Office's document server address |
| Invidious | `domain` (and the companion `public_url`) |
| Uptime Kuma, Homepage | monitors and tiles that use the old address |
| Caddy | the route itself |

## Where the old addresses still are (2026-10-28)

- Vaultwarden `DOMAIN=https://homelab.tail0000.ts.net:9758` (follow-up 16)
- Mindwtr `MINDWTR_CLOUD_CORS_ORIGIN=https://homelab.tail0000.ts.net:6390` (follow-up 17)
- Gitea `ROOT_URL = https://gitea` (follow-up 18)

## After a change

```bash
cd ~/docker/<stack> && sudo docker compose up -d     # env changes need up -d, not restart
curl -sI https://<name>.example.com | head -1
```

## Related incidents

- [2026-08-19: Mindwtr browser sync blocked by CORS](../incidents/2026-08-19-mindwtr-browser-sync-blocked-by-cors.md)
