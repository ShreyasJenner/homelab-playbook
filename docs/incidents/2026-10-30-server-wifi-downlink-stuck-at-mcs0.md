# Everything slow under heavy traffic: the router sent to the server at 7.3 Mbit/s

- **Date:** 2026-10-30
- **Status:** resolved (the trigger isn't known, so it may come back)
- **Service:** homelab's Wi-Fi link; seen as Kavita, SSH and `git pull` from Gitea all being slow
- **Runbook:** none (first occurrence)

## Symptom

From about 14:15 PDT, under heavy traffic:

- Kavita took seconds to open a manga (it used to be instant). SSH logins took about 10 s (normally 3–5) and typing lagged. A `git pull` of this repo took more than twice as long as usual. The same on the phone and the laptop.
- On the server, `localhost:5000/api/health` answered in 0.001 s, but `https://manga.example.com/api/health` took 0.9–3.4 s, almost all of it DNS (`dns=0.89`). With `--resolve` (no DNS) it took 0.013 s.
- Under that traffic, ping to the router was **avg 72 ms (min 60)**; with it stopped, 2.4 ms. `dig @8.8.8.8` took 876–2448 msec under traffic, 3 msec without.
- Uptime Kuma stayed green: it only checks `localhost`.

## Cause

**The router was sending to the server at the lowest Wi-Fi 6 rate.** `iw dev wlp130s0 link` showed:

```
rx bitrate: 7.3 MBit/s HE-MCS 0 HE-NSS 1      (router → server)
tx bitrate: 1200.9 MBit/s 80MHz HE-MCS 11 HE-NSS 2   (server → router)
```

At 7.3 Mbit/s raw (roughly 500 KiB/s usable), about 345 KiB/s of incoming traffic was enough to fill the router's queue toward the server. Every packet behind it waited about 60–70 ms: DNS replies, SSH keystrokes, every Kavita request. Upload was unaffected.

How long the rate had been stuck is unknown; the Wi-Fi connection had been up for the server's 19 days of uptime.

Why the router picked MCS 0 isn't known. Candidates:
- the signal is very strong (`-31 dBm`; the server is close to the router), which can corrupt high-rate frames (`rx drop misc` was climbing);
- the router's rate control got stuck on a long-lived association;
- the `rtw89_8852be` driver or firmware.

**Ruled out, and how:**

| Hypothesis | Probe | Result |
|---|---|---|
| The 4 TB USB disk saturated | `/proc/diskstats` over 5 s, D-state processes, `/proc/pressure/io` | `sdb busy=1%`, none in D state, `io some avg10=0.00` |
| Failing disk or USB resets | `dmesg` filtered for I/O errors and resets | nothing |
| Memory or swap | `vmstat`, `/proc/pressure/memory` | `si`/`so` 0, `memory some avg10=0.00` |
| CPU | `uptime`, `vmstat` | load 0.21, 94–99% idle |
| Kavita itself | curl to `localhost` | 0.001 s |
| Caddy | curl with `--resolve` to the tailnet IP | 0.013 s under that traffic |
| The ISP uplink | speedtest (hundreds of Mbps both ways); latency to the router, not only past it | 345 KiB/s is a fraction of the line; the delay was on the first hop |
| The server's transmit queue | `tc -s qdisc show dev wlp130s0` | `noqueue`, backlog 0 |
| Wi-Fi power save | `iw dev wlp130s0 set power_save off` at runtime | still min 62 ms; set back to `on` |
| The router or channel, for every device | ping from the laptop on the same Wi-Fi at the same time | laptop → router min 1.9 ms; laptop → server min 72.8 ms |

## Fix (run on homelab, 2026-10-30, about 18:30 PDT)

Reconnected Wi-Fi, which resets the rate negotiation with the router:

```bash
sudo nohup sh -c 'nmcli connection down HomeWiFi; sleep 3; nmcli connection up HomeWiFi' >/dev/null 2>&1 &
```

The SSH session drops for about 30 s. The address came back as `198.51.100.10`, and `/etc/resolv.conf` was untouched. Nothing to undo.

Also done along the way:
- Installed `iw` (`sudo apt-get install -y iw`), to read the link rates.

Not possible: Ethernet (no space to run a cable to the router) and a DHCP reservation (no admin access to the router).

## Verified (2026-10-30)

Under the same traffic:
- `rx bitrate: 1200.9 MBit/s 80MHz HE-MCS 11 HE-NSS 2`, still the same after 20 s of traffic; signal `-34 dBm`.
- Ping to the router avg 2.681 ms (was 72.8). `dig @8.8.8.8` and `@198.51.100.1` 15 msec (was 2448 and 1524).
- `https://manga.example.com/api/health` total 0.028 s (was 1.69). The user confirmed SSH and Kavita feel normal.

## If it comes back

The tell is a low `rx bitrate` while `tx bitrate` is high:

```bash
iw dev wlp130s0 link | grep -E 'signal|rx bitrate|tx bitrate'
ping -c 10 -q 198.51.100.1 | tail -1
```

`rx bitrate` under about 50 Mbit/s (HE-MCS 0–2) together with a router ping in the tens of ms means the same thing. Reconnect Wi-Fi as above. Detecting it automatically is follow-up 35.

## Found on the way

- On the server, `dig @100.100.100.100 manga.example.com` returns `SERVFAIL` instantly, so every public lookup falls back to `8.8.8.8`, the second line in `resolv.conf` (follow-up 36).
- Nextcloud and Euro-Office's dependence on the unreserved LAN address can't be fixed with a reservation (no router access), only by moving them off it (follow-up 37).
