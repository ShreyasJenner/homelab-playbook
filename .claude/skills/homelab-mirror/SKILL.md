---
name: homelab-mirror
description: Rebuild the public Mirror of the Playbook by its Mirror rules, block on any leak, have an independent reader check what changed against the Hidden list, and leave it ready for the user to push.
disable-model-invocation: true
---

The **Mirror** is the public copy of the Playbook (ADR 0005). Its checkout is `~/dev/projects/github/homelab-playbook`, which pushes to GitHub. The user pushes; this skill stops at the push command. One session runs the whole publish: the reading is done by subagents, which supply the fresh eyes.

Two documents decide what goes public, and the owner edits both:
- [`RULES.md`](RULES.md), the **Mirror rules**: how a build is made. Read it before step 1.
- [`hidden.md`](hidden.md), the **Hidden list**: what must never be recoverable, by category, with what is published on purpose beside each. Private.

The files the rules name are beside this one: `map.txt`, `cuts.txt`, `leave-out.txt`, `forbidden.txt`, `identity.txt`, `notice.md`. `mirror.py` builds (`build`) and moves the checkout (`update`); `leak_check.py` is the check `build` runs. [`../homelab-mirror-audit/audit.py`](../homelab-mirror-audit/audit.py) does the reading's mechanical parts. Run them with `python3 -I`. After changing a script, run the tests: `python3 -m pytest -q .claude/skills/homelab-mirror/ .claude/skills/homelab-mirror-audit/`.

## Steps

1. **Open findings.** If `.scratch/mirror-audit/open.md` exists, show its findings to the user. For each one they choose: fix it now (it becomes a rule in step 2), keep it open, or accept it into the Hidden list's "published beside it". A blocking finding can't stay open. Take the ones fixed now or accepted out of `open.md`.

   Done when each open finding has a choice and no blocking finding stays open.
2. **Build.** Run `mirror.py build <scratchpad>/mirror`.
   - `LEAKS`: every line is a broken rule, and blocks. Draft its fix by kind, and put the drafts to the user grouped by file:
     - `FORBIDDEN`: a cut in `cuts.txt` written against the Playbook's own text, or a path in `leave-out.txt`. A stand-in never fixes it: the Hidden list keeps these absent, under any name. Cut the whole passage, so nothing refers to what's gone.
     - `MAP`, `IP`, `TAILNET`, `EMAIL`: a map rule, in the map section of its Hidden list category, following the Mirror rules for stand-ins.
     - `PRIVATE`, `IDENTITY`, `TIMEZONE`, `GITLEAKS`: `mirror.py`, `identity.txt`, or the Playbook itself.
     - A false alarm: fix `leak_check.py` test-first.

     Add the accepted ones and build again.
   - `UP TO DATE`: tell the user there's nothing to publish, and stop.

   Done when the build prints `Leak check: clean.`
3. **Update the checkout.** If the build said `REWRITE`, tell the user which published commit changes and that the push will need `--force-with-lease`, and get their agreement. Then run `mirror.py update <scratchpad>/mirror`, adding `--rewrite` only after that agreement.

   Done when it prints the push command. Hold it until step 5.
4. **Read.** Each publish is read once. A fix made for a finding is checked at its places, never by reading again: after one, go through steps 2 and 3, then run `audit.py map --at` on each of the finding's places and come back to the findings below. The same goes for each finding fixed in step 1.

   Run `audit.py diff <scratchpad>/read`. What it prints decides the reading:
   - **No audited build**: run a full audit, following [`homelab-mirror-audit`](../homelab-mirror-audit/SKILL.md) in this session. Its decisions step settles its findings, so skip to step 5 once it gives its verdict, or to step 1 if it's not safe.
   - **`NEW CATEGORY`**: a category read for each, then the diff review.
   - Otherwise, the **diff review**.

   Dispatch each reading to a fresh `general-purpose` subagent, with absolute paths:

       Run the <diff review | category read for "<category>"> of the Mirror. Read <audit skill dir>/READING.md and follow its rules and its "<Diff review | Category read>" section. The Hidden list is <skill dir>/hidden.md. The reading is in <read dir>; the Mirror checkout is <checkout>. Write your findings to <read dir>/<diff | category-N>.md as you go, and end with them.

   A category read needs the full reading in a directory of its own: run `audit.py prepare <scratchpad>/read-full`, and give it that as its reading directory.

   Then put the findings to the user, each with its fix (READING.md's fix line):
   - **blocking**: fix it with a rule, through step 2.
   - **fix**: the user chooses now (as blocking), later (append it to `.scratch/mirror-audit/open.md` in the finding format), or accept.
   - **minor**: report it; nothing to decide.

   An accepted finding goes into `hidden.md` at once, under its category's "published beside it", in the shape of the entries there. If it changes what stays hidden, it goes into ADR 0005 too.

   Done when every reading has finished, and every blocking finding is fixed and checked at its places.
5. **Mark and hand over.** Run `audit.py mark`, so the next diff review starts from this build (a full audit has already marked it). Give the user the push command from step 3.

   Done when the user has the push command.
6. **Commit.** If the rule files, `hidden.md`, ADR 0005 or a script changed, commit them in the Playbook following AGENTS.md's committing rules. The build reads the rule files from the working tree, so the Mirror already used them; the build leaves the private ones out.
