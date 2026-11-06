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
MAP = HERE / "map.txt"              # real value ==> stand-in
CUTS = HERE / "cuts.txt"            # passages to delete or rewrite, run on the Playbook's own text before the map
LEAVE_OUT = HERE / "leave-out.txt"  # paths left out of every commit
FORBIDDEN = HERE / "forbidden.txt"  # terms that must not appear anywhere in the Mirror
NOTICE = HERE / "notice.md"         # the README every Mirror commit carries
sys.path.insert(0, str(HERE))
from leak_check import PRIVATE  # noqa: E402  dropped wherever they have lived
# identity.txt: "name: …", "email: …", "remote: …" (the GitHub URL)
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


def rename_callback(rules_text):
    """filter-repo --filename-callback body: the map applied to file names, as --replace-text applies it to
    contents (every literal in order, then every regex), so a link and the file it points to change alike."""
    literals, regexes = [], []
    for line in rules_text.encode("utf-8").splitlines():
        real, sep, stand_in = line.rpartition(b"==>")
        if not sep:
            real, stand_in = line, b"***REMOVED***"
        if real.startswith(b"regex:"):
            regexes.append((real[6:], stand_in))
        else:
            literals.append((real, stand_in))
    return ("import re\n"
            "if filename is None:\n"  # a deleteall change has no name
            "    return filename\n"
            f"for old, new in {literals!r}:\n"
            "    filename = filename.replace(old, new)\n"
            f"for old, new in {regexes!r}:\n"
            "    filename = re.sub(old, new, filename)\n"
            "return filename\n")


def rules_text(path):
    """The rules without comments and blank lines, which filter-repo would treat as rules. A rule needs a ==>:
    without one, filter-repo would write ***REMOVED*** in its place."""
    lines = [l for l in Path(path).read_text(encoding="utf-8").splitlines(keepends=True)
             if l.strip() and not l.lstrip().startswith("#")]
    bad = [l.strip() for l in lines if "==>" not in l]
    if bad:
        sys.exit(f"{Path(path).name}: a rule with no ==> (end it with ==> to delete the text): {bad[0][:60]}")
    return "".join(lines)


def leave_out_args(repo, leave_out):
    """--path or --path-glob for each left-out path, and for every path a private file has lived at."""
    args = [a for p in sorted({p for p in git(repo, "log", "--all", "--format=", "--name-only").splitlines()
                               if p.endswith(PRIVATE)}) for a in ("--path", p)]
    for line in Path(leave_out).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            args += ["--path-glob", line[5:]] if line.startswith("glob:") else ["--path", line]
    return args


def filter_repo(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), "filter-repo", "--force", "--quiet", *args],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"filter-repo failed:\n{r.stderr.strip()}")


def rewrite(repo, work, cuts, map, leave_out, notice, name, email):
    """Turn a clone of the Playbook into the Mirror, in two passes so the cuts see the Playbook's own text:
    1. left-out paths go, and the cuts apply to contents and messages; commits left empty are dropped;
    2. the map applies to contents, file names and messages, the identity and offset are replaced, and the
       first commit gains the notice as README.md."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    cut_rules, map_rules = work / "cuts.txt", work / "rules.txt"
    cut_rules.write_text(rules_text(cuts), encoding="utf-8")
    map_rules.write_text(rules_text(map), encoding="utf-8")

    first = ["--invert-paths", *leave_out_args(repo, leave_out)]
    if cut_rules.read_text(encoding="utf-8"):
        first += ["--replace-text", str(cut_rules), "--replace-message", str(cut_rules)]
    filter_repo(repo, *first)

    blob = git(repo, "hash-object", "-w", str(notice))
    filter_repo(repo, "--replace-text", str(map_rules), "--replace-message", str(map_rules),
                "--filename-callback", rename_callback(map_rules.read_text(encoding="utf-8")),
                "--name-callback", f"return {name.encode()!r}",
                "--email-callback", f"return {email.encode()!r}",
                "--commit-callback",
                # Same instant, offset +0000: a local offset and its DST switch place the author.
                "commit.author_date = commit.author_date.split()[0] + b' +0000'\n"
                "commit.committer_date = commit.committer_date.split()[0] + b' +0000'\n"
                "if not commit.parents:\n"
                f"    commit.file_changes.append(FileChange(b'M', b'README.md', b'{blob}', b'100644'))\n")


def build(work):
    work = Path(work)
    rebuilt = work / "rebuilt"
    shutil.rmtree(rebuilt, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    git(PLAYBOOK, "clone", "-q", "--no-local", "--single-branch", "--branch", "main", str(PLAYBOOK), str(rebuilt))
    rewrite(rebuilt, work, CUTS, MAP, LEAVE_OUT, NOTICE, NAME, EMAIL)
    git(rebuilt, "remote", "remove", "origin", check=False)

    leaks = subprocess.run([sys.executable, "-I", str(HERE / "leak_check.py"), str(rebuilt), str(MAP), EMAIL, str(FORBIDDEN)],
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
