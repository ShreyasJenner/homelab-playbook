# Authentik

```
Status:     retired (tried 2026-10-11)
Host:       homelab
Config:     ~/docker/authentik/ and the named volume authentik_database (left in place)
```

## Why retired

The goal was "a sort of homepage that will store the credentials for all my services". Authentik is a single sign-on server, not that. The need split into a password manager and a dashboard, and Authentik was dropped.

## What replaced it

[Vaultwarden](vaultwarden.md) for credentials (2026-10-15) and [Homepage](homepage.md) as the start page (2026-10-22).
