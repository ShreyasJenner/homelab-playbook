---
name: homelab-playbook
description: Continue writing the homelab Playbook (pages in docs/, link passes, AGENTS.md) from where the plan's Progress section left off, one group at a time.
disable-model-invocation: true
argument-hint: "[what to work on; default: the plan's Next]"
---

Work to do: $ARGUMENTS

The plan and its **Progress** section are in `.scratch/playbook/plan.md`. Progress is the single record of what's done, what's next, and what's waiting on whom. Read [`../homelab-shared/RULES.md`](../homelab-shared/RULES.md) first: it covers paste blocks, secrets and commits.

## Steps

1. **Load context.** Read the whole Progress section of the plan, including the Follow-ups list, then `GLOSSARY.md`, `docs/adr/` and the plan's Templates. Read one or two existing pages of each type you'll write (in `docs/hosts/`, `services/`, `runbooks/` and `incidents/`), plus every existing page the work touches, and match their style. Done when you can name the next unit of work and every page it will create or change.
2. **Check dependencies.** If Progress says the work waits on something (another session's commit, the user's review, a check result), confirm it with `git log` and `git status`. If it isn't there yet, tell the user and wait. Done when every dependency is confirmed met.
3. **Write one group.** If no work was named above, do the plan's "Next".
   - Sources rank as the plan says: `.scratch/playbook/research/01-verified-2026-10-28.md` > `00-user-answers.md` > the notes file for the topic. What the user tells you first-hand outranks the notes too.
   - Pages follow the plan's Templates. Every runbook links its incidents and every incident links its runbook. Every service page links its runbooks and incidents. The stack table in `docs/hosts/homelab.md` links every service page.
   - A problem that has happened before gets a runbook. A one-off gets an incident note only.
   - Anything that needs checking on the host goes in a paste block. Wait for the output, and fold it in.
   - Done when every new or changed page follows its template, every chat-only claim is marked Unverified, and `bash .claude/skills/homelab-playbook/check-links.sh` prints nothing.
4. **Record progress.** Update Progress: what was written, what was skipped and why, and what's waiting on whom. Do this after each batch of pages, not just at the end.
5. **Pause, then commit** following the shared rules. One group per commit.
