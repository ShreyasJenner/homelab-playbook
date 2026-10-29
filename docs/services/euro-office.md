# Euro-Office

```
Status:     live (since 2026-08-24)
Host:       homelab
Exposure:   public (Funnel :8443 → http://localhost:9917); no Caddy route
URL:        https://homelab.tail0000.ts.net:8443/
Config:     ~/docker/euro-office/ (docker-compose.yml; ./data bind; named volumes for config and logs)
            Nextcloud side: the `eurooffice` app's settings ("Nextcloud Office" in Admin settings)
Depends on: Nextcloud (eurooffice connector 11.0.6); Funnel :8443; the host's LAN address;
            a JWT secret shared with Nextcloud
Per-User:   no
Verified:   2026-10-28 (end-to-end check green; internal addresses and JWT match)
```

## What it's for

In-browser editing of the Office documents stored in [Nextcloud](nextcloud.md), including through public share links and the Nextcloud iOS app.

## Why this one

It's the fourth document server tried in 17 days:
1. **[Collabora](collabora.md)** (08-08 → 08-14): its rendering process died on every document open.
2. **The built-in CODE app** (08-08): its connection check always calls Nextcloud's public URL, which times out over Funnel.
3. **[ONLYOFFICE](onlyoffice.md)** (08-14 → 08-24): worked in the browser, but editing in its mobile app is paywalled.
4. **Euro-Office**: a fork of ONLYOFFICE's AGPL code (released 2026-06 by a group including Nextcloud, IONOS and Proton). It has no branded mobile app, so documents are edited through Nextcloud's app or the browser, with no paywall. Because it's the same codebase, every ONLYOFFICE lesson applies. **Mobile editing in the Nextcloud iOS app is confirmed to work.**

## How it's set up

### The address rule

**Server-to-server calls use the LAN address; only the browser uses the Funnel URL.** A container can't reliably reach its own host's Funnel URL (the request times out). So the connector has three addresses:

| Connector field (`occ` key) | Value (2026-10-28) | Direction |
|---|---|---|
| Document server address (`DocumentServerUrl`) | `https://homelab.tail0000.ts.net:8443/` | browser → Euro-Office |
| "Nextcloud Office address for internal requests from the server" (`DocumentServerInternalUrl`) | `http://198.51.100.10:9917/` | Nextcloud → Euro-Office |
| "Server address for internal requests from Nextcloud Office" (`StorageUrl`) | `http://198.51.100.10:8080/` | Euro-Office → Nextcloud |
| Secret key | `<JWT_SECRET>`, the same value as the container's `JWT_SECRET` | both |

Other connector settings (2026-10-28): `verify_peer_off` false, `jwt_header` empty (the default), the demo server off, and documents open in the same tab. Default open formats are docx, xlsx, pptx, pdf, vsdx and the form formats; csv and txt are editable.

**The LAN address appears in both internal fields and in Nextcloud's `trusted_domains`**, and the router doesn't reserve it. If it changes, document editing breaks ([runbook](../runbooks/document-editing-broke-after-lan-ip-change.md)).

How a document open works:
1. The browser opens the file in Nextcloud and loads the editor (`api.js`) from the Funnel URL. If that fails, the connector says "cannot be reached".
2. Nextcloud calls Euro-Office on the LAN address for checks and conversion.
3. Euro-Office fetches the file from Nextcloud and posts save callbacks to the LAN address, signed with the JWT.

**Euro-Office's container log can stay empty during a document open even when everything works.** An empty log proves nothing.

### Container

From the setup chat; the final compose file was never pasted, so details are unverified:

```yaml
services:
  euro-office:
    image: ghcr.io/euro-office/documentserver:latest
    container_name: euro-office
    restart: unless-stopped
    ports:
      - "9917:80"
    environment:
      - JWT_ENABLED=true
      - JWT_SECRET=<JWT_SECRET>
    volumes:
      - ./data:/var/lib/euro-office/documentserver
      - euro-office-logs:/var/log/euro-office/documentserver
      - euro-office-config:/etc/euro-office/documentserver
volumes:
  euro-office-logs:
  euro-office-config:
```

The port `9917:80` is verified. Inside the image run PostgreSQL, RabbitMQ, Redis, nginx and supervisord (`docservice`, `converter`, `adminpanel`, `metrics`, `example`). The health check is `curl http://localhost:9917/healthcheck`, which returns `true`.

### Lessons from the setup (2026-08-24)

- **Don't bind-mount empty host folders over the config or log directories.** They hide the image's own files, and the container crash-loops. Use named volumes, as above.
- **`./data` must be writable by the service**, or conversions fail with `EACCES … App_Data`. Docker creates the folder as root.
- **The demo `example` service has its own JWT.** Its "document security token is not correctly formed" error is a red herring; always test from Nextcloud.
- **Only one office connector should be active.** Several at once gave "Failed to load Nextcloud Office (Collabora)".
- **A leading space in `- JWT_SECRET= value`** becomes part of the secret (an ONLYOFFICE lesson). Compare the two secrets without printing them.
- **A 403 from Nextcloud on the document fetch means a JWT mismatch; a 400 means `trusted_domains`.**
- **An ad blocker** (uBlock Origin) can stop the editor from loading with nothing in any server log.
- Euro-Office may need `ALLOW_PRIVATE_IP_ADDRESS=true` (ONLYOFFICE blocks private IPs by default). Nothing has needed it so far.

## Check it end to end

Run `bash docs/runbooks/euro-office-check.sh` on homelab. It's read-only and prints no secrets:
1. It checks that the editor's `api.js` loads from the container.
2. It checks that `:8443` has Funnel on and the right proxy target.
3. It checks that `api.js` loads from the host.
4. It walks you through opening a document on and off the tailnet.
5. It prints `VERDICT=GREEN` or `VERDICT=RED`.

## Gaps

- Uptime Kuma doesn't monitor Euro-Office. A monitor on `http://localhost:9917/healthcheck` would cover the container, but not Funnel.
- The Nextcloud connector shows "(Collabora)" in some labels. That's leftover branding, not a fault.

## Runbooks

- [A service URL returns 502 or closes the connection](../runbooks/service-url-returns-502.md)
- [Document editing broke after the host's LAN address changed](../runbooks/document-editing-broke-after-lan-ip-change.md)
- Check script: `docs/runbooks/euro-office-check.sh`

## Incidents

- [2026-09-12: document editing broke after the LAN address changed](../incidents/2026-09-12-document-editing-broke-after-lan-ip-change.md)
- [2026-10-28: Euro-Office broken after switching it to Funnel](../incidents/2026-10-28-euro-office-broken-after-funnel-switch.md)
