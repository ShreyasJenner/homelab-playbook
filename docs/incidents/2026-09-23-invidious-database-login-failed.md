# Invidious database login failed

- **Date:** 2026-09-23
- **Status:** resolved
- **Service:** Invidious
- **Runbook:** [A compose or `.env` change didn't take effect](../runbooks/compose-change-didnt-take-effect.md)
- **Source:** chat "Materialious frontend setup" (2026-09-23). Unverified.

## Symptom

Invidious couldn't connect to its database: "password authentication failed", then "role does not exist".

## Cause

Upstream's example compose file hard-codes the database user and password in the Postgres service, while Invidious read them from `.env`. They didn't match. Postgres also only reads `POSTGRES_*` when it first creates its data, so changing the variables later didn't help.

## Fix

Made the Postgres service take its user and password from the same `.env` variables as `INVIDIOUS_CONFIG`, and recreated the database volume.
