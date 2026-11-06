"""Mechanical parts of the Mirror audit. Prints places, counts and shapes, never a real value.

  python3 -I audit.py check   <work-dir>               pass 1: mirror.py build into <work-dir>, the leak check on the checkout, both compared
  python3 -I audit.py meta    [repo]                   pass 2: identities, dates, refs, headers, non-text files, file modes
  python3 -I audit.py prepare <read-dir> [repo]        passes 3-4: tree.txt, messages.txt and delta.txt, and their size
  python3 -I audit.py where   <categories.tsv> [repo]  pass 5: where each category occurs in the history and the final tree
  python3 -I audit.py diff    <read-dir> [repo]        diff review: diff.txt and messages.txt, what changed since refs/audited/main
  python3 -I audit.py mark    [repo]                   set refs/audited/main to main, and record the Hidden list categories it was read for
  python3 -I audit.py map     <stand-in>...            the map rules with that text on their stand-in or real side (line numbers only)
  python3 -I audit.py map --at <file>:<line>...        a line of the checkout, with the parts that came from a stand-in marked
                                                       (back-references included; a stand-in under 3 ASCII characters
                                                       only as a whole word, marked as a maybe)

repo defaults to the Mirror checkout. categories.tsv holds one "<generic name><TAB><python regex>" per line.
"""
import collections
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MIRROR_SKILL = HERE.parent / "homelab-mirror"
LEAK_LINE = re.compile(r"^(?!GITLEAKS )[A-Z]+ [0-9a-f]{7,40}[ :]")  # "<KIND> <commit> …: <value>" from leak_check.py
SENSITIVE_EXIF = re.compile(r"GPS|Make|Model|Serial|Owner|Artist|Copyright|Software|HostComputer|DateTimeOriginal|CreateDate")


def mirror():
    """homelab-mirror's mirror.py: the checkout (MIRROR), the map (MAP), and identity.txt's NAME and EMAIL."""
    spec = importlib.util.spec_from_file_location("mirror", MIRROR_SKILL / "mirror.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo, *args, binary=False, check=True):
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=check).stdout
    return out if binary else out.decode("utf-8", "replace")


def is_text(data):
    return b"\0" not in data[:8000]  # git's own test


def text_files(repo):
    """(path, lines) for every text file in the final tree of main."""
    for path in git(repo, "ls-tree", "-r", "-z", "--name-only", "main").split("\0"):
        if path:
            data = git(repo, "cat-file", "blob", f"main:{path}", binary=True)
            yield path, data.decode("utf-8", "replace").splitlines() if is_text(data) else None


def diff_lines(log):
    """(commit, path, line) for each added or removed line, and (commit, path, event) for a deleted or non-text file."""
    commit = path = None
    in_header = False
    for line in log.splitlines():
        if line.startswith("\x01"):
            commit = line[1:]
        elif line.startswith("diff --git "):
            path, in_header = line.split(" b/", 1)[-1], True
        elif in_header:
            if line.startswith("@@"):
                in_header = False
            elif line.startswith("deleted file"):
                yield commit, path, "file deleted"
            elif line.startswith("Binary files"):
                yield commit, path, "non-text file changed"
        elif line[:1] in ("+", "-"):
            yield commit, path, line


# ---- pass 1 ------------------------------------------------------------------------------

def redact(line):
    """A leak line keeps its kind and its place, and loses its value."""
    return line.split(": ", 1)[0] + ": <value withheld>" if LEAK_LINE.match(line) and ": " in line else line


def check(work):
    m = mirror()
    print("== mirror.py build")
    built = subprocess.run([sys.executable, "-I", str(MIRROR_SKILL / "mirror.py"), "build", str(work)],
                           capture_output=True, text=True)
    print("\n".join(redact(line) for line in (built.stdout + built.stderr).splitlines()))
    print("== leak check of the checkout itself")
    leaks = subprocess.run([sys.executable, "-I", str(MIRROR_SKILL / "leak_check.py"), str(m.MIRROR), str(m.MAP), m.EMAIL,
                            str(m.FORBIDDEN)],
                           capture_output=True, text=True)
    print("\n".join(redact(line) for line in (leaks.stdout + leaks.stderr).splitlines()) or "clean")
    rebuilt = Path(work) / "rebuilt"
    if not (rebuilt / ".git").exists():
        print("== no build to compare the checkout with")
        return 1
    same = git(rebuilt, "rev-parse", "main") == git(m.MIRROR, "rev-parse", "main")
    print(f"== the checkout's main {'equals' if same else 'differs from'} the build's main")
    return 0 if built.returncode == leaks.returncode == 0 and same else 1


# ---- pass 2 ------------------------------------------------------------------------------

def shape(name):
    words = name.split()
    case = "capitalised" if words and all(w[:1].isupper() for w in words) else "not all capitalised"
    return f"{len(words)} word{'' if len(words) == 1 else 's'}, {case}"


def tool(cmd, data):
    """A tool's output for data on stdin, or None when the tool isn't installed."""
    if not shutil.which(cmd[0]):
        return None
    return subprocess.run(cmd, input=data, capture_output=True).stdout.decode("utf-8", "replace").strip()


def meta(repo, name, email):
    rows = [line.split("\0") for line in
            git(repo, "log", "--all", "--format=%at%x00%an%x00%ae%x00%cn%x00%ce%x00%ai%x00%ci").splitlines()]
    rows.sort(key=lambda row: int(row[0]))
    names = {row[1] for row in rows} | {row[3] for row in rows}
    emails = {row[2].lower() for row in rows} | {row[4].lower() for row in rows}
    print(f"== identities ({len(rows)} commits on every ref)")
    print(f"names: {len(names)} distinct ({'; '.join(sorted(shape(n) for n in names))}); "
          f"all equal identity.txt's name: {names == {name}}")
    print(f"emails: {len(emails)} distinct; all equal identity.txt's email: {emails == {email.lower()}}")

    print("== dates")
    offsets, first, last, changes, previous = collections.Counter(), {}, {}, [], None
    for row in rows:
        day, clock, tz = row[5].split()
        offsets[tz] += 1
        first.setdefault(tz, day)
        last[tz] = day
        if previous and tz != previous:
            changes.append(f"{day}: {previous} -> {tz}")
        previous = tz
    for tz, n in offsets.most_common():
        print(f"author offset {tz}: {n} commits, {first[tz]} to {last[tz]}")
    print("offset changes: " + ("; ".join(changes) or "none"))
    committer = collections.Counter(row[6].split()[2] for row in rows)
    print("committer offsets: " + ", ".join(f"{tz} x{n}" for tz, n in committer.most_common()))
    print(f"committer date differs from author date: {sum(row[5] != row[6] for row in rows)} commits")
    hours = collections.Counter(int(row[5].split()[1][:2]) // 3 for row in rows)
    print("hour of day (author offset): " + "  ".join(f"{h * 3:02d}-{h * 3 + 3:02d}h {hours[h]}" for h in range(8)))

    print("== refs (a push of main sends refs/heads/main only)")
    refs = git(repo, "for-each-ref", "--format=%(refname)").split()
    print("\n".join(r for r in refs if not r.startswith("refs/tags/")) or "none")
    notes = git(repo, "notes", "list", check=False).splitlines()
    stash = git(repo, "stash", "list", check=False).splitlines()
    print(f"tags: {sum(r.startswith('refs/tags/') for r in refs)}; notes: {len(notes)}; stash entries: {len(stash)}")
    for line in sorted(set(git(repo, "remote", "-v").splitlines())):
        print("remote: " + re.sub(r"(@[^:/\s]+:|//[^/\s]+/)[^/\s]+/", r"\1<owner>/", line))

    extra = collections.Counter()
    for commit in git(repo, "rev-list", "--all").split():
        header = git(repo, "cat-file", "commit", commit).split("\n\n", 1)[0]
        extra.update(line.split(" ", 1)[0] for line in header.splitlines()
                     if line and not line.startswith(" ")
                     and line.split(" ", 1)[0] not in ("tree", "parent", "author", "committer"))
    print("== extra commit headers: " + (", ".join(f"{k} x{n}" for k, n in extra.items()) or "none"))

    print("== non-text files, in every commit")
    paths = {}
    for line in git(repo, "rev-list", "--all", "--objects").splitlines():
        sha, _, path = line.partition(" ")
        if path:
            paths.setdefault(sha, path)
    kinds = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch-check=%(objecttype) %(objectname)"],
                           input="\n".join(paths), capture_output=True, text=True, check=True).stdout
    found = 0
    for line in kinds.splitlines():
        kind, sha = line.split()
        data = git(repo, "cat-file", "blob", sha, binary=True) if kind == "blob" else b""
        if kind != "blob" or is_text(data):
            continue
        found += 1
        mime = tool(["file", "-b", "--mime-type", "-"], data) or "binary"
        note = ""
        if mime.startswith("image/"):
            exif = tool(["exiftool", "-s", "-"], data)
            tags = sorted({t.split(":", 1)[0].strip() for t in (exif or "").splitlines()
                           if SENSITIVE_EXIF.search(t.split(":", 1)[0])})
            note = ("; exiftool isn't installed: check its EXIF by hand" if exif is None
                    else f"; identifying EXIF tags: {', '.join(tags) or 'none'}")
        print(f"{paths[sha]}: {mime}, {len(data)} bytes{note}")
    if not found:
        print("none")

    modes = collections.Counter(line.split()[1] for line in
                                git(repo, "log", "--all", "--format=", "--raw", "--no-renames").splitlines()
                                if line.startswith(":"))
    print("== file modes: " + ", ".join(f"{mode} x{n}" for mode, n in sorted(modes.items()))
          + " (120000 = symlink, 160000 = submodule)")


# ---- passes 3-4 --------------------------------------------------------------------------

def prepare(out, repo):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    final = set()
    with open(out / "tree.txt", "w", encoding="utf-8") as tree:
        for path, lines in text_files(repo):
            if lines is None:
                tree.write(f"=====FILE {path}  (not text: pass 2 covers it)\n")
                continue
            tree.write(f"=====FILE {path}\n")
            for n, line in enumerate(lines, 1):
                tree.write(f"{n:>5}|{line}\n")
            final.update(lines)

    log = git(repo, "log", "--reverse", "--format=%x01%h %as%n%B", "main")
    with open(out / "messages.txt", "w", encoding="utf-8") as messages:
        for entry in log.split("\x01")[1:]:
            head, _, body = entry.partition("\n")
            messages.write(f"=====COMMIT {head}\n{body.strip()}\n\n")

    log = git(repo, "log", "--reverse", "-p", "--no-color", "--no-renames", "--format=%x01%h", "main")
    seen, heading = set(), None
    with open(out / "delta.txt", "w", encoding="utf-8") as delta:
        for commit, path, line in diff_lines(log):
            if line[:1] not in ("+", "-"):
                delta.write(f"\n[{commit} {path}] {line}\n")
                heading = None
                continue
            text = line[1:]
            if not text.strip() or text in final or (line[0], text) in seen:
                continue
            seen.add((line[0], text))
            if heading != (commit, path):
                delta.write(f"\n[{commit} {path}]\n")
                heading = (commit, path)
            delta.write(line + "\n")

    total = 0
    for name in ("tree.txt", "messages.txt", "delta.txt"):
        text = (out / name).read_text(encoding="utf-8")
        total += len(text.encode())
        print(f"{name}: {len(text.encode()) // 1024} KB, {text.count(chr(10))} lines")
    print(f"reading: about {total // 1024} KB in all: pass 3 reads tree.txt, pass 4 messages.txt and delta.txt")


# ---- pass 5 ------------------------------------------------------------------------------

def where(categories, repo):
    cats = []
    for n, line in enumerate(Path(categories).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        name, tab, pattern = line.partition("\t")
        if not tab:
            print(f"line {n}: no tab between the name and the regex")
            continue
        try:
            cats.append((name, re.compile(pattern)))
        except re.error as e:
            print(f"line {n} ({name}): bad regex: {e.msg}")

    history = {name: [0, set(), set()] for name, _ in cats}  # lines, commits, files

    def scan(text, commit, place):
        for name, rx in cats:
            if rx.search(text):
                history[name][0] += 1
                history[name][1].add(commit)
                history[name][2].add(place)

    for entry in git(repo, "log", "--all", "--format=%x01%h%x00%B").split("\x01")[1:]:
        commit, _, body = entry.partition("\0")
        for text in body.splitlines():
            scan(text, commit, "(message)")
    for commit, path, line in diff_lines(git(repo, "log", "--all", "-p", "--no-color", "--no-renames", "--format=%x01%h")):
        if line[:1] in ("+", "-"):
            scan(line[1:], commit, path)
    for path in set(git(repo, "log", "--all", "--format=", "--name-only").splitlines()):
        scan(path, "-", f"(file name) {path}")

    places = {name: [] for name, _ in cats}
    for path, lines in text_files(repo):
        for n, text in enumerate(lines or [], 1):
            for name, rx in cats:
                if rx.search(text):
                    places[name].append(f"{path}:{n}")

    for name, _ in cats:
        count, commits, files = history[name]
        commits.discard("-")
        shown, more = places[name][:40], len(places[name]) - 40
        print(f"{name}: {count} lines in {len(commits)} commits ({', '.join(sorted(commits)) or 'none'}); "
              f"files: {', '.join(sorted(files)) or 'none'}")
        print(f"  final tree: {', '.join(shown) or 'none'}{f' (+{more} more)' if more > 0 else ''}")


# ---- diff review ---------------------------------------------------------------------------

AUDITED = "refs/audited/main"  # local to the checkout: a push of main never sends it


def categories(hidden):
    """The Hidden list's category headings."""
    return [line[4:].strip() for line in Path(hidden).read_text(encoding="utf-8").splitlines() if line.startswith("### ")]


def audited_categories(repo):
    return Path(git(repo, "rev-parse", "--absolute-git-dir").strip()) / "audited-categories"  # never pushed


def mark(repo, hidden):
    git(repo, "update-ref", AUDITED, "main")
    audited_categories(repo).write_text("".join(c + "\n" for c in categories(hidden)), encoding="utf-8")
    print(f"{AUDITED} is now {git(repo, 'rev-parse', '--short', 'main').strip()}, read for "
          f"{len(categories(hidden))} Hidden list categories: the next diff review starts here.")


def diff(out, repo, hidden):
    """What a reader of the audited build hasn't seen: the final tree's diff, every new commit's own patch (a line
    one adds and a later one removes is in no tree diff), and every message that is new or reworded.
    A commit is matched across rebuilds by its author time, since a rewrite changes every hash after it."""
    if git(repo, "rev-parse", "-q", "--verify", AUDITED, check=False).strip() == "":
        print(f"No {AUDITED} in {repo}: nothing has been read yet, so this needs a full audit.")
        return 1
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    tree = git(repo, "diff", "--no-color", "--no-renames", "--no-ext-diff", AUDITED, "main")
    seen = set(git(repo, "log", "--format=%at", AUDITED).split())
    fresh = [h for h, when in (line.split() for line in git(repo, "log", "--reverse", "--format=%H %at", "main").splitlines())
             if when not in seen]
    patches = git(repo, "show", "--no-color", "--no-renames", "--no-ext-diff", "--format====COMMIT %h %as", *fresh) \
        if fresh else ""
    changes = f"=====TREE {AUDITED}..main\n{tree}\n=====NEW COMMITS ({len(fresh)})\n{patches}"
    (out / "diff.txt").write_text(changes, encoding="utf-8")

    def messages(ref):
        log = git(repo, "log", "--reverse", "--format=%x01%h %at %as%n%B", ref)
        for entry in log.split("\x01")[1:]:
            head, _, body = entry.partition("\n")
            short, when, day = head.split()
            yield short, when, day, body.strip()

    read = {(when, body) for _, when, _, body in messages(AUDITED)}
    new = [(short, day, body) for short, when, day, body in messages("main") if (when, body) not in read]
    with open(out / "messages.txt", "w", encoding="utf-8") as f:
        for short, day, body in new:
            f.write(f"=====COMMIT {short} {day}\n{body}\n\n")
    files = sum(line.startswith("diff --git ") for line in tree.splitlines())
    print(f"diff.txt: {files} files changed in the tree and {len(fresh)} new commits' patches, "
          f"{changes.count(chr(10))} lines; messages.txt: {len(new)} commit messages new or reworded since {AUDITED}")
    record = audited_categories(repo)
    read_for = set(record.read_text(encoding="utf-8").splitlines()) if record.exists() else set()
    for category in categories(hidden):
        if category not in read_for:
            print(f"NEW CATEGORY: {category} (the audited build wasn't read for it: it needs a category read)")
    return 0


# ---- map ---------------------------------------------------------------------------------

def load_rules(path):
    """(map line number, real side, stand-in side) for each rule. A regex rule keeps its "regex:" prefix."""
    rules = []
    for n, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if raw.strip() and not raw.lstrip().startswith("#"):
            real, sep, stand_in = raw.rpartition("==>")
            rules.append((n, real, stand_in) if sep else (n, raw, "***REMOVED***"))
    return rules


def on_real_side(real, term):
    if real.startswith("regex:"):
        try:
            return bool(re.search(real[6:], term))
        except re.error:
            return False
    return term.lower() in real.lower()


def map_terms(terms, rules):
    for term in terms:
        stand_in = [n for n, _, s in rules if term.lower() in s.lower()]
        real = [n for n, r, _ in rules if on_real_side(r, term)]
        print(f"{term!r}: stand-in side of rules {stand_in or 'none'}; real side of rules {real or 'none'}")


def stand_in_pattern(real, stand_in):
    """(regex finding the stand-in's text in the Mirror, maybe). A regex rule's stand-in is a re.sub template: `\\\\` is
    a backslash and `\\1` or `\\g<name>` a captured value, matched as a run of word characters. A short ASCII
    stand-in ("b") is matched only as a whole word, and only as a maybe: it is also an ordinary word."""
    plain = stand_in if not real.startswith("regex:") or "\\" not in stand_in else None
    if plain is not None:
        if not any(c.isalnum() for c in plain):
            return None, False  # punctuation alone (a rule that deletes words) can't be told from the text
        if len(plain) < 3 and plain.isascii():
            return rf"(?<!\w){re.escape(plain)}(?!\w)", True
        return re.escape(plain), False
    out, i, ends_in_group = [], 0, False
    while i < len(stand_in):
        group = re.match(r"\\(\d+|g<\w+>)", stand_in[i:])
        if group:
            out.append(r"\w+?")
            i += len(group.group(0))
            ends_in_group = i == len(stand_in)
            continue
        if stand_in[i] == "\\" and i + 1 < len(stand_in):
            out.append(re.escape({"n": "\n", "t": "\t"}.get(stand_in[i + 1], stand_in[i + 1])))
            i += 2
        else:
            out.append(re.escape(stand_in[i]))
            i += 1
    return "".join(out) + (r"(?!\w)" if ends_in_group else ""), False


def map_at(places, rules, repo):
    stand_ins = [(n, rx, maybe) for n, r, s in rules if s and s != "***REMOVED***"
                 for rx, maybe in [stand_in_pattern(r, s)] if rx]
    for place in places:
        path, _, number = place.rpartition(":")
        try:
            line = git(repo, "show", f"main:{path}").splitlines()[int(number) - 1]
        except (subprocess.CalledProcessError, ValueError, IndexError):
            print(f"{place}: no such line in the checkout's main")
            continue
        spans = sorted(((m.start(), m.end(), n, maybe) for n, rx, maybe in stand_ins for m in re.finditer(rx, line)
                        if m.end() > m.start()),
                       key=lambda span: (span[3], span[0] - span[1]))  # sure before maybe, then longest first
        chosen = []
        for start, end, n, maybe in spans:
            if all(end <= a or start >= b for a, b, *_ in chosen):
                chosen.append((start, end, n, maybe))
        marked, at = "", 0
        for start, end, n, maybe in sorted(chosen):
            marked += line[at:start] + "⟦" + line[start:end] + "⟧" + ("?" if maybe else "")
            at = end
        print(f"{place}: {marked + line[at:]}")
        sure = sorted({n for _, _, n, maybe in chosen if not maybe})
        maybe = sorted({n for _, _, n, maybe in chosen if maybe})
        parts = ([f"stand-ins from rules {sure}"] if sure else []) + \
                ([f"maybe from rules {maybe} (short stand-ins, marked ⟦…⟧?)"] if maybe else [])
        print(f"  {'; '.join(parts)}" if parts else "  no stand-ins: all of it is the Playbook's own text")


def main(argv):
    command, args = (argv[1], argv[2:]) if len(argv) > 1 else (None, [])
    if command == "check" and len(args) == 1:
        return check(args[0])
    if command == "meta" and len(args) <= 1:
        m = mirror()
        return meta(args[0] if args else m.MIRROR, m.NAME, m.EMAIL)
    if command in ("prepare", "where") and 1 <= len(args) <= 2:
        repo = args[1] if len(args) == 2 else mirror().MIRROR
        return prepare(args[0], repo) if command == "prepare" else where(args[0], repo)
    if command == "diff" and 1 <= len(args) <= 2:
        return diff(args[0], args[1] if len(args) == 2 else mirror().MIRROR, MIRROR_SKILL / "hidden.md")
    if command == "mark" and len(args) <= 1:
        return mark(args[0] if args else mirror().MIRROR, MIRROR_SKILL / "hidden.md")
    if command == "map" and args:
        m = mirror()
        rules = load_rules(m.MAP)
        return map_at(args[1:], rules, m.MIRROR) if args[0] == "--at" else map_terms(args, rules)
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv) or 0)
