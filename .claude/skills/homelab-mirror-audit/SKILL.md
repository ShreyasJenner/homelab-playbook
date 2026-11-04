---
name: homelab-mirror-audit
description: Audit the Mirror checkout before its first push or a rewrite, in six read-only passes from the leak check to an adversarial read, ending in a safe-to-push verdict.
disable-model-invocation: true
---

An independent audit of the **Mirror** checkout (`~/dev/projects/github/homelab-playbook`, branch `main`) before its first push and before any rewrite (ADR 0005). It needs fresh eyes: if this session has written map rules or run `/homelab-mirror`, ask the user to start a new session, and stop.

Treat the Mirror as untrusted and assume something has leaked: a pass comes back clean only by finishing its whole read. Read [`READING.md`](READING.md) before step 1: its rules bind every pass, and it holds the finding format, the tells and passes 3–5. [`audit.py`](audit.py) does the mechanical parts without printing a real value: `python3 -I .claude/skills/homelab-mirror-audit/audit.py` lists its commands. After changing it, run its tests (`python3 -m pytest -q .claude/skills/homelab-mirror-audit/`).

Report each pass to the user in a few lines when it finishes.

## Steps

1. **Pass 1: leak check.** Run `audit.py check <scratchpad>/audit`. It rebuilds the Mirror with `mirror.py build`, runs the leak check on the checkout itself, and compares the checkout with the build. Every leak line is a blocking finding. A checkout that differs from the build isn't what the current Playbook and map produce: say so, and audit the checkout anyway, since it's what a push sends.

   Done when you have all three results.
2. **Pass 2: metadata.** Run `audit.py meta` and judge each section: a commit name that looks like a person's real name (the push puts it beside the GitHub account); offsets that change on a DST date, which names a region; the hours commits land at; refs, tags, notes or stash beyond `main`; signatures and extra headers; non-text files and their EXIF tags; symlinks and submodules.

   Done when every section has a finding or a "nothing here".
3. **Ask about usage.** Run `audit.py prepare <scratchpad>/audit/read`. It writes the reading for passes 3–5 and prints its size. Ask the user whether there's enough usage left to run those passes as subagents, quoting the sizes it printed:
   - **Subagents** (recommended): passes 3, 4 and 5 each in a fresh subagent, so no pass sees another's findings. About twice the reading.
   - **Inline**: the three passes in order, in this session. Half the reading, but each pass sees the earlier ones' findings, and the verdict says so.
   - **Stop**: end after pass 2, with the verdict "not audited".

   Done when the user has chosen.
4. **Passes 3–5: the reading.**
   - **Subagents:** dispatch three `general-purpose` subagents in one message, one per pass; a `fork` would inherit this session's findings. Give each only this, with absolute paths, so passes 1 and 2 stay out of it:

         Run pass <N> of the Mirror audit. Read <skill dir>/READING.md and follow its rules and its "Pass <N>" section. The reading is in <read dir>; the Mirror checkout is <checkout>. Write your findings to <read dir>/pass-<N>.md as you go, and end with them.

     Report each pass when its subagent returns.
   - **Inline:** do READING.md's passes 3, 4 and 5 yourself, in that order, into the same `pass-<N>.md` files.

   Done when the three `pass-<N>.md` files exist and each pass has met its completion line in READING.md.
5. **Pass 6: history grep.** Merge the findings of passes 1–5 into one list: one finding per leaked thing, noting which passes found it. For each finding a pattern can match, add a line to `<read dir>/categories.tsv`: a generic name, a tab, and a Python regex for the value and its variants (other spellings and cases, regex-escaped forms). Run `audit.py where <read dir>/categories.tsv`.

   Done when every place it lists belongs to a finding, as a known place or a new one.
6. **Verdict.** Give each finding its fix: a new map rule, shown by its stand-in side only; a new stand-in side for an existing rule; or, where no map rule reaches, what to change instead (`identity.txt`, `mirror.py`, the host). Stand-ins follow homelab-mirror's rules: the same everywhere, keeping the shape the text depends on. The verdict is **safe to push** only when no finding is blocking or fix; otherwise it's **not safe**, naming the findings that stand in the way. Write the report (a few lines per pass, a table of finding, severity, where, fix and the passes that found it, then the verdict) to `.scratch/mirror-audit/<YYYY-MM-DD>.md`.

   Done when every finding has a fix and the user has the verdict and the report's path. `/homelab-mirror` applies the fixes, and its next first push or rewrite comes back here.
