---
name: homelab-mirror-audit
description: Full audit of the Mirror checkout against the Mirror rules and the Hidden list, in five read-only passes ending in a safe-to-push verdict. Run before the first push, or whenever the user wants one.
disable-model-invocation: true
---

A full audit of the **Mirror** checkout (`~/dev/projects/github/homelab-playbook`, branch `main`): conformance to the Mirror rules ([`../homelab-mirror/RULES.md`](../homelab-mirror/RULES.md)) and exposure of anything on the Hidden list ([`../homelab-mirror/hidden.md`](../homelab-mirror/hidden.md)). `/homelab-mirror` runs it before the first push; the user can run it any time. After a full audit, each publish needs only `/homelab-mirror`'s diff review (ADR 0005).

The reading passes run in fresh subagents, so this session may be the one that ran `/homelab-mirror`. [`READING.md`](READING.md) holds the rules every pass follows, the finding format, the severities, the tells and the reading passes. Read it before step 1. [`audit.py`](audit.py) does the mechanical parts without printing a real value: `python3 -I .claude/skills/homelab-mirror-audit/audit.py` lists its commands. After changing it, run its tests (`python3 -m pytest -q .claude/skills/homelab-mirror-audit/`).

Report each pass to the user in a few lines when it finishes.

## Steps

1. **Pass 1: conformance.** Run `audit.py check <scratchpad>/audit`. It rebuilds the Mirror, runs the leak check (the map, the forbidden terms, the private files, the identity) on the checkout itself, and compares the checkout with the build. Every leak line is a blocking finding. A checkout that differs from the build isn't what the current Playbook and rules produce: say so, and audit the checkout anyway, since it's what a push sends.

   Done when you have all three results.
2. **Pass 2: metadata.** Run `audit.py meta` and judge each section against the Mirror rules: a commit name or email that differs from `identity.txt`; refs, tags, notes or stash beyond `main` (`refs/audited/main` is local and never pushed); signatures and extra headers; non-text files and their EXIF tags; symlinks and submodules.

   Done when every section has a finding or a "nothing here".
3. **Passes 3 and 4: the reading.** Run `audit.py prepare <scratchpad>/audit/read`. Then dispatch two `general-purpose` subagents in one message, one per pass. A `fork` would inherit this session's findings, so use fresh ones. Give each only this, with absolute paths:

       Run pass <N> of the Mirror audit. Read <skill dir>/READING.md and follow its rules and its "Pass <N>" section. The Hidden list is <mirror skill dir>/hidden.md. The reading is in <read dir>; the Mirror checkout is <checkout>. Write your findings to <read dir>/pass-<N>.md as you go, and end with them.

   If a pass returns without meeting its completion line in READING.md, dispatch that pass again, alone, and tell it to resume from the `read through:` line of its file.

   Done when both `pass-<N>.md` files meet their completion lines.
4. **Pass 5: history grep.** Merge the findings of passes 1–4 into one list: one finding per leaked thing, under its Hidden list category, noting which passes found it. For each finding a pattern can match, add a line to `<read dir>/categories.tsv`: a generic name, a tab, and a Python regex for the value and its variants (other spellings and cases, regex-escaped forms). Run `audit.py where <read dir>/categories.tsv`.

   Done when every place it lists belongs to a finding, as a known place or a new one.
5. **Decisions.** Give each finding its fix: a cut or a left-out path for category 1, which a stand-in never fixes; a map rule, shown by its stand-in side only; a new stand-in side for an existing rule; or what to change instead (`identity.txt`, `mirror.py`, the host). Put the blocking and fix findings to the user together, each with its fix. For each fix finding, ask whether to fix it now, later, or accept it.

   Record each choice now, in this session. An accepted finding goes into `hidden.md` under its category's "published beside it", in the shape of the entries there, and into ADR 0005 too if it changes what stays hidden. A later fix goes into `.scratch/mirror-audit/open.md` in the finding format. Then commit `hidden.md` and ADR 0005 following AGENTS.md's committing rules. These are the only edits the audit makes.

   Done when every blocking finding has a fix and every fix finding has a choice, recorded.
6. **Verdict.** The verdict is **safe to push** when no blocking finding is left; otherwise it's **not safe**, naming the findings that stand in the way. Fix findings left for later don't block. A pass that didn't finish makes the verdict **not audited**, naming the pass. Write the report to `.scratch/mirror-audit/<YYYY-MM-DD>.md`, adding `-2`, `-3` and so on when that day's report exists: a few lines per pass, a table of finding, category, severity, where, fix (or "accepted", or "later") and the passes that found it, then the verdict.

   Unless the verdict is **not audited**, run `audit.py mark`: this build has been read, so the next reading is only a diff review of what changes after it. On **not safe**, append each blocking finding still standing to `.scratch/mirror-audit/open.md` in the finding format. `/homelab-mirror` then fixes it in its step 1 and checks it at its places, never by reading again.

   Done when the user has the verdict and the report's path.
