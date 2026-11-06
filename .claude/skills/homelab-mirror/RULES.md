# Mirror rules

How `/homelab-mirror` makes the **Mirror** from the Playbook. What must never be recoverable from it is the **Hidden list**, kept privately beside these rules; these rules are how a build gets there. The owner edits both. This file is published; the Hidden list, the map and the other files named below are not.

## History

- Every commit on the Playbook's `main` is mirrored, in order. A commit left empty by the rules below is dropped.
- A build rewrites in two passes. First the left-out paths go and the cuts apply; then the map applies. So a cut is written against the Playbook's own text, and the map never sees what a cut removed.
- Cuts and the map apply to file contents and to commit messages. The map also applies to file names.
- Every commit carries the name and email in `identity.txt`, at its own instant with the offset `+0000`.
- The first commit carries `notice.md` as `README.md`. Each claim the notice makes about what was left out holds.

## Left out

- The private files, wherever they have lived: `map.txt`, `identity.txt`, `hidden.md`, `cuts.txt`, `forbidden.txt`, `leave-out.txt`.
- Every path in `leave-out.txt`, in every commit. A plain line is a file or folder; `glob:` starts a pattern.
- Every passage `cuts.txt` deletes or rewrites. A cut has the map's format; one that ends in `==>` and nothing else deletes its match. A passage that mentions a left-out page is cut whole, so no link points at a page that isn't there.
- Every term in `forbidden.txt`: no file, file name or message holds one. The leak check enforces it, so a match blocks the build until a cut or a left-out path removes it.

## Stand-ins

A stand-in comes from a rule in `map.txt`. It is fixed, never random, the same everywhere it appears, and keeps the shape the text depends on: a path stays a path, an address stays an address, a port stays a number. Each section of the map is headed by the Hidden list category it serves.

- **Addresses**: the documentation ranges `192.0.2.x`, `198.51.100.x`, `203.0.113.x`, `2001:db8::`. Loopback, `0.0.0.0`, the private ranges (`10.x`, `172.16–31.x`) and well-known public resolvers stay.
- **Domains**: `example.com` names. The software's own public domains stay.
- **The tailnet and machine names**: `tail0000.ts.net`, and `homelab` for the server. Devices get a generic name (`laptop-1`, `phone`).
- **Ports**: each port chosen for this homelab gets one stand-in port, the same number everywhere. Standard ports and software defaults stay.
- **Usernames**: `alice` and `bob`. The owner's GitHub handle stays, as a username too.
- **Keys, tokens and passwords** never reach the Playbook (ADR 0001); its placeholders stay as they are.

## Kept as they are

- The owner's name, GitHub handle and email.
- Dates, in full. Hardware models, OS and software versions.
- The media services and the media in them: real titles, songs and artists.
