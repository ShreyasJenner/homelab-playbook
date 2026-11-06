# Custom skills

Skills written for this repo. Type a skill's name in Claude Code to start it. `homelab-debug` also starts on its own when you report something broken, and `homelab-install` when you ask to install a service or another skill decides on one.

| Skill | Type this | Use it to |
|---|---|---|
| [`homelab-playbook`](.claude/skills/homelab-playbook/SKILL.md) | `/homelab-playbook` or `/homelab-playbook <task>` | Continue writing the Playbook from the plan's Progress section, one group at a time, pausing before each commit. With no task, it does the plan's "Next". |
| [`homelab-followups`](.claude/skills/homelab-followups/SKILL.md) | `/homelab-followups 10 28` | Carry out follow-ups (homelab changes listed in its `FOLLOWUPS.md`) one at a time, through paste blocks you run on the host, then record the results in the Playbook. With no numbers, it lists the open ones and asks. |
| [`homelab-debug`](.claude/skills/homelab-debug/SKILL.md) | `/homelab-debug` or `/homelab-debug <service> <symptom>` | Diagnose a broken service through paste blocks: runbook first, ranked hypotheses, read-only probes against a control, then the fix with an undo line. It ends with the incident note, the runbook and service page updates, and follow-ups for anything found on the way. |
| [`homelab-install`](.claude/skills/homelab-install/SKILL.md) | `/homelab-install <service>` | Install one named service on homelab: grills you on Exposure, subdomain, Users and data location, drafts the compose file from upstream docs, then installs it through paste blocks (stack, Caddy, `stacks.sh`) and writes its service page and table rows. If you name a need instead of a service, it sends you to `/homelab-research` first. |
| [`homelab-research`](.claude/skills/homelab-research/SKILL.md) | `/homelab-research <topic>` | Research a question, such as what could replace a service. It grills you for a brief of every question the research has to answer, has a subagent research them against primary sources, then grills you on the findings and researches again until you're done. The note goes in `docs/research/<topic>.md`. |
| [`homelab-blog`](.claude/skills/homelab-blog/SKILL.md) | `/homelab-blog` or `/homelab-blog <post>` | Draft blog posts from the Playbook, one per service plus an intro and roundups, scrubbed of identifying details. On the first run it plans the series in `blog/SERIES.md`. `paste <post>` builds the copy to paste into the blog platform. `published <post> <url>` records the post's link. |
| [`homelab-mirror`](.claude/skills/homelab-mirror/SKILL.md) | `/homelab-mirror` | Rebuild the public Mirror in `~/dev/projects/github/homelab-playbook` from the committed Playbook by its Mirror rules (`RULES.md`): paths and passages left out, every identifying detail swapped for a stand-in. It blocks on any leak or forbidden term, has a subagent review what changed since the last audited build against the Hidden list (a full audit the first time), then prints the push command. You push. Edit `RULES.md` and `hidden.md` to change what goes public. |
| [`homelab-mirror-audit`](.claude/skills/homelab-mirror-audit/SKILL.md) | `/homelab-mirror-audit` | A full audit of the Mirror checkout against the Mirror rules and the Hidden list: the leak check, metadata, the final tree and the whole history read by two independent subagents, and a grep of the history. `/homelab-mirror` runs it before the first push; run it yourself any time. Only blocking findings stop a push: you fix, postpone or accept the rest, and accepted ones go into the Hidden list. |

All of them follow the repo rules in [`AGENTS.md`](AGENTS.md) (page templates, links, paste blocks, secrets, commits), which every session loads through `CLAUDE.md`. Change a rule there, once.

The link checker is `bash .claude/skills/homelab-playbook/check-links.sh`. It prints every broken relative link under `docs/`, and nothing when all are fine.

## Adding one

Put it in `.claude/skills/homelab-<name>/SKILL.md`. The `homelab-` prefix is what gets it committed: `.gitignore` ignores the rest of `.claude/`, where the installed third-party skills (listed in `skills-lock.json`) are symlinks into `.agents/`. Then add a row above.
