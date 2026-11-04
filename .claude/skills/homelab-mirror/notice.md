# Homelab Playbook (public mirror)

This is the documentation for my self-hosted homelab: a home server running about 25 services, with the service pages, runbooks, incident notes and decision records I keep while running it. Most of it was written with Claude Code, using the skills in `.claude/skills/` (debugging, installing services, research, follow-ups). `SKILLS.md` lists them.

**It's a sanitized mirror.** The real Playbook is private. This copy is rebuilt from it commit for commit, so the history is real, but every identifying detail is a stand-in:

- Domains are `example.com`, the tailnet is `tail0000.ts.net`, and addresses are in documentation ranges (`192.0.2.x`, `198.51.100.x`, `203.0.113.x`).
- People are `alice` and `bob`. The ISP and location are left out.
- Media titles are public-domain works, so names, years and database IDs in the incident notes don't match what was actually on the disk, and the lyrics research tables are illustrative.

Standard ports and each software's default ports are real; ports chosen for this homelab are stand-ins, the same number everywhere. Dates, software versions and hardware are real. `docs/adr/0005-public-mirror-with-stand-ins.md` explains how the mirror is built.
