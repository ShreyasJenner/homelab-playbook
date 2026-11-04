"""Build the Mirror from the Playbook's committed main, check it for leaks, and move the Mirror checkout to it.

  python3 -I mirror.py build  <work-dir>              rebuild into <work-dir>/rebuilt, leak-check, compare, report
  python3 -I mirror.py update <work-dir> [--rewrite]  move the Mirror checkout to the build (--rewrite: accept changed history)

Only committed work on the Playbook's main is mirrored. The script never pushes.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAYBOOK = HERE.parents[2]
MIRROR = Path(os.environ.get("HOMELAB_MIRROR", Path.home() / "dev/projects/github/homelab-playbook"))  # override: tests only
MAP = HERE / "map.txt"
PRIVATE = ("homelab-mirror/map.txt", "homelab-mirror/identity.txt")  # dropped wherever they have lived
# identity.txt: "name: …", "email: …" (the GitHub noreply address), "remote: …" (the GitHub URL)
IDENTITY = dict(line.split(": ", 1) for line in (HERE / "identity.txt").read_text().splitlines() if ": " in line)
NAME, EMAIL, GITHUB = IDENTITY["name"], IDENTITY["email"], IDENTITY["remote"]


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"git {' '.join(args)} failed in {repo}:\n{r.stderr.strip()}")
    return r.stdout.strip()


def commit_keys(repo, ref):
    """Commit hash -> (author date, subject): how a commit is recognised across rebuilds, whatever its hash."""
    out = git(repo, "log", "--format=%H%x00%at%x00%s", ref)  # %at: the instant, whatever the offset
    return {h: (d, s) for h, d, s in (line.split("\x00") for line in out.splitlines())}


def build(work):
    work = Path(work)
    rebuilt = work / "rebuilt"
    shutil.rmtree(rebuilt, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    git(PLAYBOOK, "clone", "-q", "--no-local", "--single-branch", "--branch", "main", str(PLAYBOOK), str(rebuilt))

    rules = work / "rules.txt"  # the map without comments and blank lines, which filter-repo would treat as rules
    rules.write_text("".join(l for l in MAP.read_text(encoding="utf-8").splitlines(keepends=True)
                             if l.strip() and not l.lstrip().startswith("#")), encoding="utf-8")
    notice = git(rebuilt, "hash-object", "-w", str(HERE / "notice.md"))
    private_paths = sorted({p for p in git(rebuilt, "log", "--all", "--format=", "--name-only").splitlines()
                        if p.endswith(PRIVATE)})

    cmd = ["git", "-C", str(rebuilt), "filter-repo", "--force", "--quiet",
           "--replace-text", str(rules), "--replace-message", str(rules),
           "--name-callback", f"return {NAME.encode()!r}",
           "--email-callback", f"return {EMAIL.encode()!r}",
           "--commit-callback",
           # Same instant, offset +0000: a local offset and its DST switch place the author.
           "commit.author_date = commit.author_date.split()[0] + b' +0000'\n"
           "commit.committer_date = commit.committer_date.split()[0] + b' +0000'\n"
           "if not commit.parents:\n"
           f"    commit.file_changes.append(FileChange(b'M', b'README.md', b'{notice}', b'100644'))\n"]
    if private_paths:
        cmd += ["--invert-paths"] + [a for p in private_paths for a in ("--path", p)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"filter-repo failed:\n{r.stderr.strip()}")
    git(rebuilt, "remote", "remove", "origin", check=False)

    leaks = subprocess.run([sys.executable, "-I", str(HERE / "leak_check.py"), str(rebuilt), str(MAP), EMAIL],
                           capture_output=True, text=True)
    if leaks.returncode:
        print(f"LEAKS: the build is blocked.\n{leaks.stdout}{leaks.stderr}", end="")
        return 1

    built = commit_keys(rebuilt, "main")
    if not (MIRROR / ".git").exists():
        new, status = list(built), f"FIRST PUBLISH: {len(built)} commits; {MIRROR} doesn't exist yet."
    else:
        git(rebuilt, "fetch", "-q", str(MIRROR), "+main:refs/published/main")
        published = git(rebuilt, "rev-parse", "refs/published/main")
        seen = set(commit_keys(rebuilt, "refs/published/main").values())
        new = [h for h, key in built.items() if key not in seen]
        if published == git(rebuilt, "rev-parse", "main"):
            status = "UP TO DATE: nothing to publish."
        elif subprocess.run(["git", "-C", str(rebuilt), "merge-base", "--is-ancestor",
                             "refs/published/main", "main"]).returncode == 0:
            status = f"NEW: {len(new)} commits on top of what's published; a normal push."
        else:
            base = git(rebuilt, "merge-base", "refs/published/main", "main", check=False)
            first = git(rebuilt, "log", "--reverse", "--format=%h %s",
                        f"{base}..refs/published/main" if base else "refs/published/main").splitlines()[0]
            status = (f"REWRITE: published history changes from commit {first}. "
                      f"{len(new)} commits are new; the rest only changed stand-ins. "
                      "Update needs --rewrite, and the push needs --force-with-lease.")
    (work / "new-commits.txt").write_text("".join(h + "\n" for h in new))
    print("Leak check: clean.")
    print(status)
    if new:
        print(f"Review the new commits: git -C {rebuilt} show --format=fuller $(cat {work / 'new-commits.txt'})")
    return 0


def update(work, rewrite=False):
    rebuilt = Path(work) / "rebuilt"
    if not (rebuilt / ".git").exists():
        sys.exit(f"No build in {work}: run build first.")
    if not (MIRROR / ".git").exists():
        MIRROR.mkdir(parents=True, exist_ok=True)
        git(MIRROR, "init", "-q", "-b", "main")
        git(MIRROR, "remote", "add", "origin", GITHUB)
    if git(MIRROR, "status", "--porcelain"):
        sys.exit(f"{MIRROR} has local changes. The Mirror is never edited by hand: look at them, then discard them.")
    git(MIRROR, "fetch", "-q", str(rebuilt), "+main:refs/build/main")
    has_main = subprocess.run(["git", "-C", str(MIRROR), "rev-parse", "-q", "--verify", "main"],
                              capture_output=True).returncode == 0
    fast_forward = not has_main or subprocess.run(
        ["git", "-C", str(MIRROR), "merge-base", "--is-ancestor", "main", "refs/build/main"]).returncode == 0
    if not fast_forward and not rewrite:
        sys.exit("The build rewrites published history. Re-run update with --rewrite once the user has agreed.")
    git(MIRROR, "reset", "-q", "--hard", "refs/build/main")
    push = "git push -u origin main" if fast_forward else "git push --force-with-lease origin main"
    print(f"{MIRROR} is at {git(MIRROR, 'log', '-1', '--format=%h %s')}.")
    print(f"To publish: cd {MIRROR} && {push}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "build":
        sys.exit(build(sys.argv[2]))
    if len(sys.argv) >= 3 and sys.argv[1] == "update":
        sys.exit(update(sys.argv[2], rewrite="--rewrite" in sys.argv[3:]))
    sys.exit(__doc__)
