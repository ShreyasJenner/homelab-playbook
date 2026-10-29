# Materialious

```
Status:     retired (→ none; Invidious is used directly)
Host:       homelab
Config:     ~/docker/materialious/ and the named volume materialious_materialious-data (left in place)
```

## Why retired

It was an unnecessary frontend. It was added on 2026-09-23 as a Material-style UI for [Invidious](invidious.md), and needed constant care: ufw blocked its proxy whenever its Docker subnet changed, it needed the companion published on a public URL, every account saw the same "Popular" feed, and fresh sessions got "Auth required" errors.

## Leftovers

Kept on purpose:
- the folder and the named volume
- probably the ufw rule `3407/tcp from 192.0.2.0/20` (port 3407 was Invidious's old Serve port, and the rule was added for Materialious's proxy)
- Invidious's companion `public_url` was added for it
