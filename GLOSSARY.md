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

**Exposure**:
Who can reach a service: *tailnet-only* (the default: only devices on the tailnet, through the reverse proxy; not the home LAN or the internet) or *public* (open to the internet through Funnel).
_Avoid_: Access (that means logging in), visibility, open

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
