# ntfy `auth-users` type mismatch

- **Date:** 2026-08-30
- **Status:** resolved
- **Service:** ntfy
- **Runbook:** [A new container won't start or crash-loops](../runbooks/new-container-crash-loops.md)
- **Source:** chat "Setting up ntfy in Docker" (2026-08-30). Unverified; the end state was verified on 2026-10-28.

## Symptom

ntfy wouldn't start: `Mismatched type for flag 'auth-users'. Expected '[]interface{}' but actual is 'string'`.

## Cause

In `server.yml`, `auth-users` was written as a single string. It has to be a YAML list.

## Fix

The user moved all of ntfy's config to `.env` instead, where lists are comma-separated: `NTFY_AUTH_USERS=<NTFY_AUTH_USERS>`, with every `$` in the bcrypt hash written as `$$`. Verified 2026-10-28: `alice` (admin) comes from the server config, and there's no `server.yml`.
