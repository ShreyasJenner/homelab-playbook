# Gitea SSH clone closed the connection

- **Date:** 2026-10-22
- **Status:** resolved
- **Service:** Gitea
- **Runbook:** [Gitea SSH clone or push fails](../runbooks/gitea-ssh-clone-or-push-fails.md)
- **Source:** chat "Gitea SSH clone connection issue" (2026-10-22). Unverified; end state verified 2026-10-28.

## Symptom

`git clone git@gitea:<repo>` failed with "Connection closed by … port …". The web UI worked.

## Cause

Gitea's SSH port had been mapped with `tailscale serve --https`, which terminates TLS and speaks HTTP, so no SSH banner ever arrived. The clone path was also missing the `owner/` part.

## Fix

Removed the HTTPS mapping and added a TCP one (today: `sudo tailscale serve --bg --tcp=8313 tcp://localhost:8312`), then cloned with `git@gitea:<owner>/<repo>.git`. Verified 2026-10-28: the only Serve entry for Gitea is TCP, and `ssh -T gitea` authenticates.
