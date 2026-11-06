---
name: homelab-blog
description: Draft blog posts from the Playbook, one per service (plus an intro and roundups), telling the incidents faced with it, scrubbed of every identifying detail.
disable-model-invocation: true
argument-hint: "[post | paste <post> | published <post> <url>; default: the next planned post]"
---

Work to do: $ARGUMENTS

The series plan is `blog/SERIES.md`: every post, the incidents each one tells, its status, its post URL, the paste mode, and a Playbook gaps list. Drafts go in `blog/drafts/<post>.md`.

This skill writes only under `blog/` and `.scratch/blog/`. The Playbook in `docs/` is its source, read-only. A gap or contradiction found there goes in SERIES.md's Playbook gaps list, for `/homelab-playbook` to fix.

## Pick the branch

- `blog/SERIES.md` doesn't exist → follow [PLAN.md](PLAN.md), then stop.
- `paste <post>` → **Paste** below.
- `published <post> <url>` → set that post's status to published and record the URL in SERIES.md. Done.
- A post name, or nothing (the first post with status planned) → **Draft** below.

## Draft

1. **Load.** Read the post's SERIES.md entry, then everything it points at: the service page(s), each assigned incident note, the runbooks those link, and any retired service page that names this service as its replacement. For the intro post, read `docs/hosts/`, `docs/adr/` and `GLOSSARY.md` instead. Read `.scratch/blog/notes/<post>.md` if an earlier run left one. Done when every assigned incident is read and each is marked **verified** or **unverified** (unverified = its page says Unverified).
2. **Outline, then stop.** Propose:
   - the angle, in one sentence
   - three title options
   - the sections in order
   - which incidents you'll tell, and why each one earns its place. Also say which assigned incidents you'd drop
   - planned `[image: …]` markers
   - up to 3 questions for details the Playbook doesn't hold: what you suspected first, how long it took, what it felt like

   Save the user's answers in `.scratch/blog/notes/<post>.md`. Done when the user approves the outline. Skipped questions are fine.
3. **Write** `blog/drafts/<post>.md` to the post format below. Done when every section of the approved outline is in it.
4. **Scrub.** Rewrite every identifying detail with the stand-ins from **Public** below.
   - Run `bash .claude/skills/homelab-blog/check-public.sh blog/drafts/<post>.md`. Fix every line it prints by rewriting the draft, and run it again.
   - A line naming a software's own public domain or documented default port is fixed by adding that value to `blog/public-domains.txt` or `blog/public-ports.txt`, with its source in the second field.
   - Then do your own pass for what patterns can't catch: names in prose, the ISP, the location, the network move, drive labels, and details that identify you in combination.

   Done when the script prints nothing and your pass finds nothing. Report both results.
5. **Record.** In SERIES.md: set the status to drafted, record the incidents the post actually tells (so no later post tells them again), and add any Playbook gaps.
6. **Stop for review.** The user reads the draft. Commit following `AGENTS.md`, with only `blog/` files in the commit.

## Paste

Builds the copy the user pastes into the blog platform, in `.scratch/blog/out/`.

1. Copy the draft without the Publish notes block and its `---` line.
2. Every `SERIES:<post>` link becomes that post's post URL from SERIES.md. If that post isn't published yet, drop the link and keep its text.
3. Run `check-public.sh` on the copy. Done when it prints nothing.
4. If SERIES.md's paste mode is `html` or `unknown`, also write the HTML copy with `python3 -m markdown -x fenced_code <copy>.md > <copy>.html`, for the user to open in a browser and copy the rendered page.
5. While the paste mode is `unknown`, ask the user whether pasting the Markdown kept its formatting in the blog platform's editor, and record `markdown` or `html` in SERIES.md.

## Post format

```
Publish notes
Title:    …
Subtitle: …
Tags:     a few tags
---
```

Then the post itself, in the order the outline set. A full post usually runs: the setup sketch → why I chose it → how it's set up → the incidents → lessons learned → quick fixes.

- **Reader:** a self-hoster who already knows Docker, reverse proxies and Tailscale. Leave those unexplained.
- **Voice:** first person and casual, honest about wrong turns. 1,200–2,000 words.
- **Setup sketch:** one paragraph (a home server running Docker Compose stacks and Tailscale for private access), linking `[the intro post](SERIES:intro)`. The intro post is the long version of this sketch, so it has none.
- **Incidents:** 2–4 per full post, each told as broke → what I tried → the cause → the fix. A roundup gives each service a short section and one incident.
- **Retired services** appear in their replacement's post, as why I switched (from the retired page's Why retired).
- **Faithful:** every statement about what the user did, saw, thought or felt traces to a Playbook page or a saved answer. Where neither has it, tell the story plainly.
- **Commands and config** go in fenced code blocks, taken from verified pages, with stand-ins and `<PLACEHOLDER>` for secrets. A fix from an unverified incident is told in words, as "what worked for me".
- **Quick fixes:** one item per incident told, with the symptom in bold, then a line for the cause and a line for the fix. The blog platform has no tables.
- **Images:** an `[image: what it shows]` marker where a screenshot or diagram would help. The user takes and redacts it.
- **Links:** other posts as `SERIES:<post>`. The software's official docs and repo are fine to link directly.

## Public

Everything that could identify the user, their network or their hosts gets a stand-in.

- IPs → documentation ranges `192.0.2.x`, `198.51.100.x`, `203.0.113.x`, `2001:db8::`. Well-known public addresses (`127.0.0.1`, `0.0.0.0`, `8.8.8.8`, `1.1.1.1`, `100.100.100.100`) stay.
- Domains → `example.com` names (`cloud.example.com`). The software's own public domains stay.
- Tailnet names → "my tailnet" in prose. The script flags every `ts.net` name.
- Hostnames → "my home server".
- Usernames → `user` or `alice`. Emails → `alice@example.com`.
- Ports → `<PORT>`, except a software's documented default port.
- Paths → `~/docker/<service>/`, `/mnt/media`, `/mnt/backup`.
- Keys, tokens and passwords → `<PLACEHOLDER>`. This includes public keys.
- Removed with no stand-in: MACs, UUIDs, container IDs, drive serials and labels, Git remotes, the ISP, the location, the network move, and personal names.
- Dates → month and year.
- Hardware models, OS and software versions stay.
- **The Mirror** has its own rules ([`homelab-mirror/RULES.md`](../homelab-mirror/RULES.md)); these don't apply to it.
