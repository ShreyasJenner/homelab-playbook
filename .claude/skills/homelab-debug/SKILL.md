---
name: homelab-debug
description: Diagnose and fix a broken homelab service through paste blocks the user runs on its host, then record it in the Playbook. Use when a service is down, erroring or misbehaving, or a follow-up's check fails.
argument-hint: "[service and symptom]"
---

Problem: $ARGUMENTS

You can't reach the hosts: every probe is a paste block the user runs (rules in `AGENTS.md`). So each round trip is expensive, and every block has to rule something out. Page templates, links, secrets and commits also follow `AGENTS.md`. The hosts are whatever `docs/hosts/` lists today. The skill names none of them.

## Steps

1. **Get the symptom.** Ask for whatever the user hasn't said: which service, the exact error text, when it started, what changed since it last worked, and whether it fails elsewhere (a public instance, another User's instance, another device). Done when you have all five, or the user has said they don't know.
2. **Read the Playbook.** Read the service page, its runbooks and incidents, and the host page named in its `Host:` field. Run `grep -rln -i '<distinctive error words>' docs/` for runbooks filed under another service. Done when you can name the runbook that matches, or say none does, and list the service's host, Exposure, Depends on and Known issues.
3. **Rank hypotheses.** Write 3–5, starting from the runbook's likely causes, each with its prediction: "if X, then probe Y shows Z". Show them to the user with the first block. Done when each one names the output that would falsify it.
4. **Probe.** One read-only block per round, saying which host it runs on. Each command maps to a hypothesis, and one block covers several hypotheses. The runbook's Check comes first. After each output, say which hypotheses it falsified, quoting the line, and re-rank. When the remaining ones predict the same output, design a **control**: run the same thing with one variable changed. For example, the same version as a working public instance, the same image on another machine on the same network, or the same request from another host. Done when one hypothesis stands and the output has falsified the rest.
5. **Fix.** The change goes in its own block, with a backup, a check of the target state and an undo line. If the cause is outside the homelab (an upstream bug, a third-party block, the ISP), the fix is a workaround or waiting. Say so, and leave the incident open. Done when the check shows the target state, or the user has chosen to wait.
6. **Record.** In this session, before `/clear`:
   - an incident note (`open` or `resolved`), listing what was ruled out and how;
   - the runbook: extend it with the new likely cause and the probe that told it apart, or create one if this has happened before;
   - the service page: Verified date, new state, Known issues, the incident link;
   - the host page, if a fact on it turned out wrong;
   - each problem found on the way that this session didn't fix, as a follow-up in `.claude/skills/homelab-followups/FOLLOWUPS.md`, with drafted commands in its `HOWTO.md`.

   Done when `bash .claude/skills/homelab-playbook/check-links.sh` prints nothing.
7. **Pause, then commit** following `AGENTS.md`.

## Pitfalls

- **Probe the path the service uses.** A plain `curl` to an API the service reaches with its own client and tokens tests a different path. Probe through the service itself (its port, its logs, `docker exec`), or through the same image in a throwaway container.
- **Check Known issues before chasing a symptom.** A container shown as "unhealthy", or a startup error the service page calls noise, may be a known false alarm.
- **Date your facts.** Facts about a host's network (ISP, public IP, CGNAT, LAN address) carry the date they were found. Check the host page and its incidents for a network move or host change since then before reasoning from one.
- **A fix outside the service touches more than the service.** A router restart, a host reboot or a Docker restart can change a LAN address and take down every stack on the host. Check the host page and `FOLLOWUPS.md` for what it would break, and warn before suggesting it.
- **Blocks run in bash on the hosts and in zsh on the laptop.** Name loop variables `p` or `u`: in zsh, `path` is tied to `PATH`. Quote decorative separators (`echo '---'`): in zsh, a word that starts with `=` is expanded as a command path.
- **Throwaway containers get `--rm` and a `docker stop` at the end of the block.** If a block fails partway through, the container is still running, so stop it in the next block.
