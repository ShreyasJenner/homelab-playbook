"""Tests for leak_check.py: each builds a throwaway git repo and runs the check on it, as /homelab-mirror does."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("leak_check.py")
EMAIL = "alice@example.com"


def git(repo, *args, email=EMAIL):
    env = {**os.environ, "GIT_AUTHOR_NAME": "Alice", "GIT_AUTHOR_EMAIL": email,
           "GIT_COMMITTER_NAME": "Alice", "GIT_COMMITTER_EMAIL": email,
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    subprocess.run(["git", "-C", str(repo), *args], check=True, env=env, capture_output=True)


def make_repo(tmp_path, commits, email=EMAIL):
    """commits: list of (message, {path: text or None to delete})."""
    repo = tmp_path / "mirror"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    for message, files in commits:
        for path, text in files.items():
            f = repo / path
            if text is None:
                f.unlink()
            else:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", message, email=email)
    return repo


def make_map(tmp_path, *rules):
    m = tmp_path / "map.txt"
    m.write_text("# a comment\n\n" + "".join(r + "\n" for r in rules))
    return m


def run(repo, map_file, env=None):
    r = subprocess.run([sys.executable, "-I", str(SCRIPT), str(repo), str(map_file), EMAIL],
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout


def test_map_value_only_in_an_old_commit_fails(tmp_path):
    repo = make_repo(tmp_path, [
        ("Add host page", {"docs/host.md": "Login: hastur\n"}),
        ("Scrub host page", {"docs/host.md": "Login: alice\n"}),
    ])
    code, out = run(repo, make_map(tmp_path, "hastur==>alice"))
    assert code == 1
    assert "MAP" in out and "docs/host.md" in out and "hastur" in out


def test_map_value_in_a_commit_message_fails(tmp_path):
    repo = make_repo(tmp_path, [
        ("Follow-up 39: remove Moonlit Harbor duplicates", {"docs/kavita.md": "Wuthering Heights\n"}),
    ])
    code, out = run(repo, make_map(tmp_path, "Moonlit Harbor==>Wuthering Heights"))
    assert code == 1
    assert "message" in out and "Moonlit Harbor" in out


import pytest


# Sample leaks are split across string literals so this file passes the check it tests.
REAL_EMAIL = "someone" "@proton.me"


@pytest.mark.parametrize("kind, leak", [
    ("TAILNET", "https://homelab.tail" "ab12cd.ts.net:8443"),
    ("IP", "DHCP from the router at 192.168" ".4.1"),
    ("IP", "Tailscale IP 100.88" ".1.2"),
    ("IP", "the server at 240.0" ".0.25"),
    ("EMAIL", "alerts go to " + REAL_EMAIL),
])
def test_identifying_pattern_not_in_the_map_fails(tmp_path, kind, leak):
    repo = make_repo(tmp_path, [("Add page", {"docs/page.md": leak + "\n"})])
    code, out = run(repo, make_map(tmp_path))
    assert code == 1
    assert out.startswith(kind) and "docs/page.md" in out


def test_stand_ins_and_well_known_values_pass(tmp_path):
    page = ("https://homelab.tail0000.ts.net:8443, 192.0.2.10, 198.51.100.10, 203.0.113.1,\n"
            "127.0.0.1, 0.0.0.0, 8.8.8.8, 1.1.1.1, 100.100.100.100, 10.10.10.2, 172.20.0.1,\n"
            "alice@example.com, noreply@anthropic.com, busybox 1.36.1, Redlib 0.40.0,\n"
            "Kavita v0.9.1.4, TheTVDB_24.0.0.0, Docker DNS 127.0.0.11, rebind drops 100.64.0.0/10\n")
    repo = make_repo(tmp_path, [("Add page\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
                                 {"docs/page.md": page})])
    code, out = run(repo, make_map(tmp_path))
    assert (code, out) == (0, "")


def test_commit_by_a_real_email_fails(tmp_path):
    repo = make_repo(tmp_path, [("Add page", {"docs/page.md": "hello\n"})], email=REAL_EMAIL)
    code, out = run(repo, make_map(tmp_path))
    assert code == 1
    assert out.startswith("IDENTITY") and REAL_EMAIL in out


@pytest.mark.parametrize("private", ["map.txt", "identity.txt"])
def test_private_file_in_any_commit_fails(tmp_path, private):
    path = f".claude/skills/homelab-mirror/{private}"
    repo = make_repo(tmp_path, [("Add it", {path: "# only a comment\n"}), ("Drop it", {path: None})])
    code, out = run(repo, make_map(tmp_path))
    assert code == 1
    assert out.startswith("PRIVATE") and path in out


def test_secret_found_by_gitleaks_fails(tmp_path):
    token = "ghp_" + "R7kq2Xv9Lm4Tz8Wc1Np6Hd3Jf5Yb0Gs7Ae2Q"  # fake GitHub token shape
    repo = make_repo(tmp_path, [("Add page", {"docs/page.md": f"TOKEN={token}\n"})])
    code, out = run(repo, make_map(tmp_path))
    assert code == 1
    assert out.startswith("GITLEAKS") and "docs/page.md" in out and token not in out


def test_missing_gitleaks_fails_instead_of_passing(tmp_path):
    repo = make_repo(tmp_path, [("Add page", {"docs/page.md": "hello\n"})])
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "git").symlink_to(shutil.which("git"))
    code, out = run(repo, make_map(tmp_path), env={**os.environ, "PATH": str(bin_dir)})
    assert code == 1
    assert out.startswith("GITLEAKS") and "not installed" in out


def test_map_value_matches_any_case_but_only_from_a_word_start(tmp_path):
    repo = make_repo(tmp_path, [("Add page", {"docs/page.md": "[quillbarrowzz.yml](link) and a nozzle\n"})])
    code, out = run(repo, make_map(tmp_path, "Quillbarrow==>Internet Archive", "Ozzle==>Someone"))
    assert code == 1
    assert "quillbarrow" in out.lower() and "ozzle" not in out.lower()
