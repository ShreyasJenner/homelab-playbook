---
name: homelab-research
description: Grill the user into a research brief, research it against primary sources, then grill again on the findings and re-research until the user is done. Notes go in docs/research/.
disable-model-invocation: true
argument-hint: "[topic, e.g. redlib alternatives]"
---

Topic: $ARGUMENTS

The output is one **note** per topic at `docs/research/<topic-slug>.md`, for example `kavita-alternatives.md`. That folder is fixed, so never ask where to save. Page templates, links, secrets and commits follow `AGENTS.md`. You can't reach the hosts, so the Playbook is where you get facts about the homelab.

## Steps

1. **Load context.** Read `GLOSSARY.md`, `docs/adr/`, the service and host pages the topic touches, and any existing note in `docs/research/` on the same topic. If a note exists, this run updates it. Done when you can state the current setup in two lines and say what any existing note already answers.
2. **Grill for the brief.** Invoke the `grilling` skill. The design tree is the **brief**: every question the research has to answer. That includes the need, the must-haves and dealbreakers, the criteria to compare on and their weights, the candidates to include or rule out, the constraints (host, Exposure, ADRs, what's being migrated from), and what result would settle it. Read facts from the Playbook and put only decisions to the user. Done when the frontier is empty and the user confirms the brief is complete.
3. **Research round.** Dispatch one subagent with a fresh context, giving it the brief, the note's path, the [note format](#note-format) and the facts from step 1. It researches against **primary sources** (official docs, repos and their APIs, release pages, registries), cites every claim where the claim appears, dates every number that changes over time, and marks anything it couldn't confirm as "Unverified". It writes the note itself, or rewrites it in place in a later round so the note stays one current answer. Done when the note exists and answers every question in the brief, or says why it couldn't.
4. **Grill on the findings.** Read the note. Summarise the answer in a few lines, then run another `grilling` round on what the findings changed: candidates to drop or add, criteria to reweight, new questions the findings raised, and claims to check more closely. Add the user's answers to the note's Brief section. If anything is left that needs more research, go back to step 3 with the changed brief. Done when the user says the research is finished.
5. **Link and check.** Link the note from each service page it's about, in that page's "Why this one" section. Run `bash .claude/skills/homelab-playbook/check-links.sh`. Done when it prints nothing.
6. **Pause, then commit** following `AGENTS.md`.

## Note format

````
# Research: <topic>

```
Question:   <the question, in one or two lines>
Researched: <YYYY-MM-DD>, from <kinds of sources>. No host access.
Fits:       <service> on <host> (<how it's run and exposed>)
```

<One paragraph on the current setup, linking its service page.>

## Summary
<A ranked answer to the question, a few numbered items.>

## Comparison
<A table of candidates by the brief's criteria, if there are candidates.>

<Sections for anything the brief asked for that a table can't hold.>

## Brief
<The brief's questions and the user's answers, including the ones added in later rounds.>
````

In a later round, add that round's date to `Researched:`.
