---
name: homelab-followups
description: Carry out homelab follow-ups (host changes on homelab) one at a time, through paste blocks the user runs, and record the results in the Playbook.
disable-model-invocation: true
argument-hint: "[follow-up numbers, e.g. 10 28]"
---

Follow-ups to work on: $ARGUMENTS

Follow-ups are homelab changes, not Playbook writing. Their status lives in [`FOLLOWUPS.md`](FOLLOWUPS.md). The drafted commands for each open one are in [`HOWTO.md`](HOWTO.md), in priority order. Paste blocks, secrets, page templates and commits follow `AGENTS.md`.

## Steps

1. **Load context.** Read `FOLLOWUPS.md`, `GLOSSARY.md`, `docs/adr/`, the `HOWTO.md` sections for the chosen follow-ups, and every page in `docs/` that mentions them (`grep -rn -i 'follow-up <n>' docs/`). Done when you can state, for each chosen follow-up, its current status and the page that records it.
2. **Pick.** If no numbers were given above, list the open follow-ups in `HOWTO.md`'s order and ask which. Done when the user has chosen.
3. **Run one follow-up at a time.** Give one **paste block**: a read-only pre-check of the current state, a backup, the change, then the check from `HOWTO.md`. The HOWTO commands are untested drafts, and the host may have moved on since they were written. Adapt them to the pre-check's output, or split off the pre-check as its own block when the change depends on it. Wait for the user's output. Done when the output shows the check's target state. If it doesn't, diagnose with the `diagnosing-bugs` skill before going on.
4. **Record.**
   - Update every page that mentions the follow-up, so it describes the new state with `Verified: <date>`. Resolve any incident it closes.
   - Mark it done in `FOLLOWUPS.md`, and delete its section from `HOWTO.md`.
   - Write an incident note for anything that went wrong on the way, plus a runbook if the problem has happened before.
   - Done when `grep -rn -i 'follow-up <n>' docs/` shows only pages that describe it as done.
5. **Commit**, following `AGENTS.md`, including `FOLLOWUPS.md` and `HOWTO.md`.
