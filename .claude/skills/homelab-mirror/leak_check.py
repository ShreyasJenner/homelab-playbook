"""Leak check for the Mirror. Prints one line per identifying value left anywhere in its history; nothing when clean.

Usage: python3 -I leak_check.py <mirror-repo> <map.txt> <allowed-email>
Exit 0 = clean, 1 = leaks found. Every commit on every ref is checked, not only the latest.
"""
import ipaddress
import json
import re
import shutil
import subprocess
import sys


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True).stdout.decode("utf-8", "replace")


def real_values(map_file):
    """The left-hand side of every rule in the map: the real values the Mirror must never contain."""
    literals, regexes = [], []
    for line in open(map_file, encoding="utf-8"):
        line = line.rstrip("\r\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        lhs = line.rsplit("==>", 1)[0]
        if lhs.startswith("regex:"):
            regexes.append(re.compile(lhs[6:]))
        elif lhs:
            literals.append(lhs)
    return literals, regexes


PRIVATE = ("homelab-mirror/map.txt", "homelab-mirror/identity.txt")  # never leave the Playbook
TAILNET = re.compile(r"\btail[0-9a-z]+\.ts\.net\b", re.I)
IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")  # not after a letter or _: v0.9.1.4, TheTVDB_24.0.0.0
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
ALLOWED_IPS = {"100.64.0.0", "0.0.0.0", "8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "100.100.100.100"}
STAND_IN_NETS = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]
GENERIC_NETS = [ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8")]  # private ranges, loopback


def pattern_leaks(text, allowed_email):
    """(kind, match) for each value that looks identifying and isn't a stand-in or a well-known public value."""
    for m in TAILNET.finditer(text):
        if m.group(0).lower() != "tail0000.ts.net":
            yield "TAILNET", m.group(0)
    for m in IPV4.finditer(text):
        try:
            ip = ipaddress.ip_address(m.group(0))
        except ValueError:
            continue
        if m.group(0) in ALLOWED_IPS or any(ip in n for n in STAND_IN_NETS + GENERIC_NETS):
            continue
        yield "IP", m.group(0)
    for m in EMAIL.finditer(text):
        e = m.group(0).lower()
        if re.search(r"@(.+\.)?example\.(com|net|org)$", e) or e in ("noreply@anthropic.com", allowed_email.lower()):
            continue
        yield "EMAIL", m.group(0)


def added_lines(repo):
    """(commit, path, text) for every line added by any commit, root commits included."""
    commit = path = None
    for line in git(repo, "log", "--all", "-p", "--no-color", "--no-ext-diff", "--format=commit %H").splitlines():
        if line.startswith("commit "):
            commit = line[7:15]
        elif line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("+") and path:
            yield commit, path, line[1:]


def gitleaks(repo):
    """One line per secret gitleaks finds in any commit (redacted). A missing gitleaks is a failure, never a pass."""
    if not shutil.which("gitleaks"):
        return ["GITLEAKS not installed: install it (sudo pacman -S gitleaks); the check can't pass without it"]
    r = subprocess.run(["gitleaks", "git", repo, "--log-opts=--all", "--no-banner", "--redact",
                        "--log-level=error", "--report-format=json", "--report-path=-", "--exit-code=0"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return [f"GITLEAKS failed to run: {r.stderr.strip()}"]
    return [f"GITLEAKS {f['Commit'][:8]} {f['File']}: {f['RuleID']}" for f in json.loads(r.stdout or "[]")]


def main(repo, map_file, allowed_email):
    literals, regexes = real_values(map_file)
    # Any case ("quillbarrowzz.yml" for Quillbarrow), but only from a word start ("nozzle" isn't Ozzle).
    literal_patterns = [(v, re.compile((r"(?<![A-Za-z0-9])" if v[0].isalnum() else "") + re.escape(v), re.I))
                        for v in literals]
    leaks = []

    def check_map(where, text):
        text = text.replace("\\.", ".")  # a regex-escaped value (grep '192\.168\.…') is still the value
        for value, rx in literal_patterns:
            if rx.search(text):
                leaks.append(f"MAP {where}: {value}")
        for rx in regexes:
            for m in rx.finditer(text):
                leaks.append(f"MAP {where}: {m.group(0)}")
        for kind, match in pattern_leaks(text, allowed_email):
            leaks.append(f"{kind} {where}: {match}")

    for commit, path, text in added_lines(repo):
        check_map(f"{commit} {path}", text)

    for entry in git(repo, "log", "--all", "--format=%H%x00%B%x01").split("\x01"):
        if "\x00" in entry:
            commit, message = entry.strip("\n").split("\x00", 1)
            check_map(f"{commit[:8]} message", message)

    for path in sorted(set(git(repo, "log", "--all", "--format=", "--name-only").split("\n"))):
        if path.endswith(PRIVATE):
            leaks.append(f"PRIVATE {path}")

    for line in git(repo, "log", "--all", "--format=%H %ae %ce").splitlines():
        commit, *emails = line.split()
        for e in sorted(set(emails)):
            if e.lower() != allowed_email.lower():
                leaks.append(f"IDENTITY {commit[:8]}: {e}")

    leaks.extend(gitleaks(repo))

    for line in leaks:
        print(line)
    return 1 if leaks else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
