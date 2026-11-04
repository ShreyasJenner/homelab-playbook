# A public Mirror with stand-ins, not a sanitized Playbook

The Playbook stays private and keeps every real value: a runbook is only useful if its addresses, names and paths are the ones on the host. What goes public is the **Mirror**, a copy of the Playbook rewritten commit for commit by `/homelab-mirror`, with every identifying detail swapped for a stand-in from a map committed in the Playbook (and removed from the Mirror). We rejected sanitizing the Playbook itself, because that would cost the detail that makes debugging fast, and starting the Mirror from a single sanitized snapshot, because the point of publishing is the incident-by-incident history.

## Consequences

- **Stand-ins are fixed, never random.** The same Playbook and map always produce the same Mirror, commit hashes included, so each publish only adds commits. A new map entry that matches an old commit rewrites history from there, and that push is a `--force-with-lease`.
- **Media titles become public-domain works rather than the prose being reworded.** Japanese and Chinese songs become traditional folk songs in the same scripts, so the synced-lyrics research still makes sense.
- **The rules for stand-ins are the Public section of the `homelab-blog` skill**, except that the Mirror keeps real ports and full dates, which the runbooks and incident filenames need.
- **A leak check blocks every publish**, and Claude reviews each run's new commits for titles and names the patterns can't catch. The user pushes by hand; the skill never does.
