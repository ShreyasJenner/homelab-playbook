# Homelab Playbook (public mirror)

This is the documentation for my self-hosted homelab: a home server running about 25 services, with the service pages, runbooks, incident notes and decision records I keep while running it. Most of it was written with Claude Code, using the skills in `.claude/skills/` (debugging, installing services, research, follow-ups). `SKILLS.md` lists them.

**It's a sanitized mirror.** The real Playbook is private. This copy is rebuilt from it commit for commit, so the history is real, but some of it is left out and every identifying detail is a stand-in:

- Domains are `example.com`, the tailnet is `tail0000.ts.net`, and addresses are in documentation ranges (`192.0.2.x`, `198.51.100.x`, `203.0.113.x`).
- Usernames and other people are `alice` and `bob`, and devices have generic names. The ISP is left out.
- Some services, and the pages and passages about them, are left out entirely.

Standard ports and each software's default ports are real; ports chosen for this homelab are stand-ins, the same number everywhere. Dates, software versions, hardware and media titles are real, except that the drives go by size and interface alone. `.claude/skills/homelab-mirror/RULES.md` lists the rules the mirror is built by, and `docs/adr/0005-public-mirror-with-stand-ins.md` explains why.
