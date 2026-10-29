# Maloja

```
Status:     retired 2026-09-24 (→ Last.fm through Navidrome)
Host:       homelab
Config:     ~/docker/maloja/ (left in place)
```

## Why retired

It was set up on 2026-09-24 as a self-hosted scrobble server for Navidrome. The same evening the user wanted Koito instead, and Koito was never set up. Navidrome now scrobbles to Last.fm.

## Leftovers

Kept on purpose:
- the `~/docker/maloja/` folder
- the `music` Docker network, which only Navidrome is on now
- Navidrome's `ND_LISTENBRAINZ_*` settings, still pointing at `http://maloja:42010/…` (see the [Navidrome page](navidrome.md#known-leftovers))
