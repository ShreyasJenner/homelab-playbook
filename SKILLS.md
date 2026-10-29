# Custom skills

Skills written for this repo. Each is user-invoked: type its name in Claude Code to start it.

| Skill | Type this | Use it to |
|---|---|---|
| [`homelab-playbook`](.claude/skills/homelab-playbook/SKILL.md) | `/homelab-playbook` or `/homelab-playbook <task>` | Continue writing the Playbook from the plan's Progress section, one group at a time, pausing before each commit. With no task, it does the plan's "Next". |
| [`homelab-followups`](.claude/skills/homelab-followups/SKILL.md) | `/homelab-followups 10 28` | Carry out follow-ups (homelab changes listed in the plan's Follow-ups) one at a time, through paste blocks you run on the host, then record the results in the Playbook. With no numbers, it lists the open ones and asks. |
| [`homelab-blog`](.claude/skills/homelab-blog/SKILL.md) | `/homelab-blog` or `/homelab-blog <post>` | Draft blog posts from the Playbook, one per service plus an intro and roundups, scrubbed of identifying details. On the first run it plans the series in `blog/SERIES.md`. `paste <post>` builds the copy to paste into the blog platform. `published <post> <url>` records the post's link. |

Both skills follow the repo rules in [`AGENTS.md`](AGENTS.md) (page templates, links, paste blocks, secrets, commits), which every session loads through `CLAUDE.md`. Change a rule there, once.

The link checker is `bash .claude/skills/homelab-playbook/check-links.sh`. It prints every broken relative link under `docs/`, and nothing when all are fine.

## Adding one

Put it in `.claude/skills/homelab-<name>/SKILL.md`. The `homelab-` prefix is what gets it committed: `.gitignore` ignores the rest of `.claude/`, where the installed third-party skills (listed in `skills-lock.json`) are symlinks into `.agents/`. Then add a row above.
