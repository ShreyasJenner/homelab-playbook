# Tailnet-only by default; Funnel only for document sharing

Services are reached through Caddy on the tailnet, so every URL needs Tailscale. There are three exceptions, which bypass Caddy and use Tailscale directly. **Nextcloud** and **Euro-Office** are public through Funnel, because shared document links have to open and be editable by people outside the tailnet, and the browser of whoever is editing must be able to reach the document server as well as Nextcloud. **Gitea SSH** is served over Tailscale as raw TCP, because Caddy only proxies HTTP and SSH cloning needs TCP. Making everything public behind Caddy was the alternative. We rejected it so that the internet sees only the two services that have to be public.

## Consequences

- Euro-Office is public through Funnel on `:8443` since 2026-10-28, after the first attempt left it tailnet-only and broken. See `docs/incidents/2026-10-28-euro-office-broken-after-funnel-switch.md`. To check it end to end, run `docs/runbooks/euro-office-check.sh`.
