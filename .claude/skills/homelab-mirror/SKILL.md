---
name: homelab-mirror
description: Rebuild the public Mirror of the Playbook with stand-ins, leak-check it, review the new commits for missed identifying details, and leave it ready for the user to push.
disable-model-invocation: true
---

The **Mirror** is the public copy of the Playbook, rebuilt from its committed `main`, commit for commit, with every identifying detail swapped for a **stand-in** (ADR 0005). Its checkout is `~/dev/projects/github/homelab-playbook`, which pushes to GitHub. The user pushes. This skill stops at the push command.

Files here:
- `map.txt`: real value `==>` stand-in, one rule per line. Its header explains the format and ordering. It never leaves the Playbook.
- `mirror.py`: `build` rebuilds and leak-checks the Mirror; `update` moves the checkout. Run with `python3 -I`.
- `leak_check.py`: run by `build`. Its tests are `test_leak_check.py` (`python3 -m pytest -q .claude/skills/homelab-mirror/`). Run them after any change to the check.
- `notice.md`: the README every Mirror commit carries.

Stand-ins follow the **Public** section of [`homelab-blog`](../homelab-blog/SKILL.md), including its Mirror exceptions. A new stand-in must be the same everywhere it appears, and must keep the shape the text depends on: a title ending in a digit still ends in one, a path stays a path.

## Steps

1. **Build.** Run `python3 -I .claude/skills/homelab-mirror/mirror.py build <scratchpad>/mirror`.
   - `LEAKS`: for each line, add a map rule that replaces the real value with a stand-in (or fix `leak_check.py` test-first if the hit is a false alarm), then build again.
   - `UP TO DATE`: tell the user there's nothing to publish, and stop.

   Done when the build prints `Leak check: clean.`
2. **Review the new commits.** Read every commit listed in `<scratchpad>/mirror/new-commits.txt` with the command the build printed: the full diff and the message. Patterns can't catch these, so you're the reader that does:
   - media titles and their database IDs
   - people's names and handles
   - places finer than the time zone, the ISP
   - device names, account and bucket names

   What ADR 0005 publishes on purpose (the "Not findings" in [`homelab-mirror-audit/READING.md`](../homelab-mirror-audit/READING.md)) needs no stand-in.

   Propose each find as a map line (`real==>stand-in`) and put them to the user together. Add the accepted ones to `map.txt` and go back to step 1.

   Done when every listed commit is read and every proposal is accepted or rejected, with no new map rules from this pass. On a first publish, the list is the whole history. Review it in batches of about ten commits and report after each batch.
3. **Update.** If the build said `REWRITE`, tell the user which published commit changes and that the push will need `--force-with-lease`, and get their agreement. Then run `python3 -I .claude/skills/homelab-mirror/mirror.py update <scratchpad>/mirror`, adding `--rewrite` only after that agreement.

   Done when it prints the push command. Give that command to the user. If the Mirror has never been pushed (no `origin/main` in the checkout) or the build said `REWRITE`, tell them to run `/homelab-mirror-audit` in a new session first, and to push only on its "safe to push". If it isn't safe, put its fixes to the user as in step 2.
4. **Commit the map.** If `map.txt` or the check changed, commit them in the Playbook following AGENTS.md's committing rules. Only committed Playbook work is mirrored, but the map is read from the working tree, so the Mirror already used the new rules.
