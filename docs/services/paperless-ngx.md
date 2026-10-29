# Paperless-ngx

```
Status:     retired (set up 2026-10-02)
Host:       homelab
Config:     ~/docker/paperless-ngx/ and the named volumes paperless-ngx_pgdata, paperless-ngx_redisdata (left in place)
```

## Why retired

Two reasons:
- **It deleted Nextcloud's files.** On its first day its consume folder pointed into Nextcloud's data directory, and Paperless deletes everything it consumes ([incident](../incidents/2026-10-02-nextcloud-files-consumed-by-paperless.md)).
- **It needed too much setting up.** Using it properly means a separate consume folder that every new document gets copied into, and that wasn't worth the time.

## What replaced it

Nothing.

## Lesson

Never point a service that deletes what it ingests at another service's data. Give it its own folder.
