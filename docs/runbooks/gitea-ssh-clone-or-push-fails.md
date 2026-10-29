# Gitea SSH clone or push fails

## Symptom

- `git clone`/`git push`/`ssh -T gitea` fails with "Connection closed by … port …", a timeout, or "Permission denied (publickey)".
- The web UI at https://gitea.example.com still works.

## Check

On the laptop:

```bash
ssh -G gitea | grep -E '^(hostname|port|user|identityfile|identitiesonly) '   # expect homelab.tail0000.ts.net, 8313, git
ssh -vT gitea 2>&1 | grep -E 'Connecting to|remote software version|Offering|Authenticated|Hi there|closed'
tailscale status | head -3                                                     # is the laptop on the tailnet?
```

On homelab:

```bash
sudo tailscale serve status | grep -A3 8313     # expect tcp://…:8313 → tcp://localhost:8312 (not https://)
sudo docker port gitea                          # 22/tcp -> 0.0.0.0:8312
sudo docker logs gitea --tail 30 2>&1 | grep -i ssh
```

## Likely causes

1. **The Serve entry is missing** (wiped by a `tailscale serve reset`) **or uses `--https`**, which speaks TLS, so no SSH banner ever arrives and the connection closes.
2. **The laptop's `gitea` alias points at the wrong port** (8312 is the host port; over the tailnet it's 8313).
3. **The key isn't in Gitea**, or the agent offers a different key first ("Permission denied").
4. **The clone path is missing the owner:** it's `git@gitea:<owner>/<repo>.git`.
5. The laptop isn't on the tailnet.

## Fix

```bash
sudo tailscale serve --https=8313 off 2>/dev/null     # only if it was added as https
sudo tailscale serve --bg --tcp=8313 tcp://localhost:8312
```

For cause 2, fix the alias as shown on the [Gitea page](../services/gitea.md#ssh-and-clone-urls). For cause 3, add the public key under Gitea → Settings → SSH Keys, and set `IdentitiesOnly yes` in the alias.

## Verify

`ssh -T gitea` prints "Hi there, ShreyasJenner! You've successfully authenticated…", and `git ls-remote origin HEAD` returns a commit.

## Related incidents

- [2026-10-22: SSH clone closed the connection](../incidents/2026-10-22-gitea-ssh-clone-connection-closed.md)
