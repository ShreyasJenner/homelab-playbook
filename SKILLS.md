# Custom skills

Skills written for this repo. Each is user-invoked: type its name in Claude Code to start it.

| Skill | Type this | Use it to |
|---|---|---|
| [`homelab-followups`](.claude/skills/homelab-followups/SKILL.md) | `/homelab-followups 10 28` | Carry out follow-ups (homelab changes listed in the plan's Follow-ups) one at a time, through paste blocks you run on the host, then record the results in the Playbook. With no numbers, it lists the open ones and asks. |

## Adding one

Put it in `.claude/skills/homelab-<name>/SKILL.md`. The `homelab-` prefix is what gets it committed: `.gitignore` ignores the rest of `.claude/`, where the installed third-party skills (listed in `skills-lock.json`) are symlinks into `.agents/`. Then add a row above.
