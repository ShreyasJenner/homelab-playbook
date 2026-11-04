# Homelab Playbook

The documentation for a self-hosted homelab: how it is set up, why, and how to fix it when it breaks.

## Environment

**Homelab**:
The whole self-hosted environment: the host, its network, and the services it runs.
_Avoid_: Home server, server (when meaning the whole environment)

**Host**:
One machine you administer that runs services.
_Avoid_: Server, box, node

**Service**:
One self-hosted application, running on a host.
_Avoid_: App, container (a service may be more than one container)

**User**:
A person who uses the homelab's services. Each User has their own accounts and, for some services, their own instance.
_Avoid_: Account (an account is one User's login on one service; admin is an account, not a User), member

**Exposure**:
Who can reach a service: *tailnet-only* (the default: only devices on the tailnet, through the reverse proxy; not the home LAN or the internet) or *public* (open to the internet through Funnel).
_Avoid_: Access (that means logging in), visibility, open

## Media

**Series**:
One manga or light novel, as a reader knows it: every volume and chapter of one title. Each series lives in exactly one folder.
_Avoid_: Title, manga (when meaning one series), book

**Volume**:
One collected book of a series, kept as one file.
_Avoid_: Volume when meaning storage (say Docker volume, disk or partition), tankōbon, book

**Chapter**:
One installment of a series, smaller than a volume. A chapter not yet collected into a volume is kept as its own file.
_Avoid_: Episode, issue

## Documentation

**Playbook**:
The complete body of documentation for the homelab, kept in this repo.
_Avoid_: Docs, documentation, Ansible playbook (spell that out in full if Ansible is ever used)

**Service page**:
The reference for one service: what it is, which host it runs on, how it is configured, what it depends on, and why it is set up that way.
_Avoid_: Service doc, notes

**Host page**:
The reference for one host: its hardware, OS, disks, network, and the services it runs.
_Avoid_: Server page, machine doc

**Runbook**:
A reusable procedure that goes from a symptom, through diagnosis, to a fix.
_Avoid_: Playbook, guide, how-to

**Incident note**:
A short dated record of one thing that went wrong: symptom, cause, fix, and which service it affected. It becomes a runbook when the fix turns out to be reusable.
_Avoid_: Incident report, postmortem, log

**ADR**:
A record of a decision that is hard to reverse, would surprise a future reader, and came out of a real trade-off.
_Avoid_: Decision log, design doc

**Unverified**:
Content taken from a chat that has not yet been checked against the live host.
_Avoid_: Draft, unconfirmed

**Mirror**:
The public copy of the Playbook, with every identifying detail swapped for a stand-in. Its history follows the Playbook's commit for commit.
_Avoid_: Sandbox, public repo, fork

**Stand-in**:
A made-up value that replaces an identifying detail, the same everywhere it appears.
_Avoid_: Fake, placeholder (a placeholder such as `<JWT_SECRET>` marks where a secret was left out)
