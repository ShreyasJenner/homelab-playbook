# First run: plan the series

Reached from [SKILL.md](SKILL.md) when `blog/SERIES.md` doesn't exist yet. It ends with the plan approved and committed, and no post drafted.

1. **Survey.** Read every page in `docs/services/` and the header and Service line of every note in `docs/incidents/`. Count each service's incidents. Done when every incident note is assigned to exactly one service.
2. **Build the denylist.** Write `.scratch/blog/denylist.txt`, one real value per line: every hostname, tailnet and node name, domain, username, login, custom port number, LAN and tailnet IP, drive label and mount name, and the Git host found in `docs/` (start with `docs/hosts/`). Then ask the user for what the Playbook doesn't hold: their name and handles, ISP, city. The file stays in `.scratch/`, which is never committed. Done when every identifying value in `docs/hosts/` is on the list and the user has answered.
3. **Propose the series**, then stop for approval:
   - `intro` comes first.
   - Services with enough material for a full post, meaning 2 or more incidents or one strong story, each get their own post.
   - The rest go into themed roundups (media, monitoring, productivity, and so on), 3–6 services each.
   - Each retired service goes inside its replacement's post.
   - Assign every incident to one post. A service with no incidents can still appear in a roundup on the strength of its Why this one.

   Done when the user approves the list.
4. **Write `blog/SERIES.md`:**

   ```
   # Blog series

   Paste mode: unknown

   | Post | Services | Incidents | Status | URL |
   |---|---|---|---|---|
   | intro | — | — | planned | |
   | nextcloud | Nextcloud, Collabora (retired), … | [2026-07-19 …](../docs/incidents/…) … | planned | |

   ## Playbook gaps
   ```

   Status is planned, drafted or published. Also create `blog/public-domains.txt` and `blog/public-ports.txt`, each with a header comment: `# value  source`.
5. **Pause, then commit** `blog/` following `AGENTS.md`.
