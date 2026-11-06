"""Tests for audit.py: each builds a throwaway repo and checks that the output names places and shapes, never values."""
import importlib.util
import os
import subprocess
from pathlib import Path

spec = importlib.util.spec_from_file_location("audit", Path(__file__).with_name("audit.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

NAME, EMAIL = "Ada Lighthouse", "ada@example.org"


def git(repo, *args, date=None):
    env = {**os.environ, "GIT_AUTHOR_NAME": NAME, "GIT_AUTHOR_EMAIL": EMAIL,
           "GIT_COMMITTER_NAME": NAME, "GIT_COMMITTER_EMAIL": EMAIL,
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    subprocess.run(["git", "-C", str(repo), *args], check=True, env=env, capture_output=True)


def make_repo(tmp_path, commits):
    """commits: list of (message, {path: text, or None to delete}, date or None)."""
    repo = tmp_path / "mirror"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    for message, files, date in commits:
        for path, text in files.items():
            f = repo / path
            if text is None:
                f.unlink()
            else:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(text)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", message, date=date)
    return repo


def test_redact_keeps_kind_and_place():
    assert audit.redact("MAP 1a2b3c4d docs/host.md: harbourmaster") == "MAP 1a2b3c4d docs/host.md: <value withheld>"
    assert audit.redact("IDENTITY 1a2b3c4d: " + EMAIL) == "IDENTITY 1a2b3c4d: <value withheld>"
    assert audit.redact("TIMEZONE 1a2b3c4d: -0700") == "TIMEZONE 1a2b3c4d: <value withheld>"
    for kept in ("GITLEAKS 1a2b3c4d docs/host.md: generic-api-key", "Leak check: clean.",
                 "UP TO DATE: nothing to publish.", "FIRST PUBLISH: 44 commits; the checkout doesn't exist yet."):
        assert audit.redact(kept) == kept


def test_meta_gives_shapes_and_offsets_not_identities(tmp_path, capsys):
    repo = make_repo(tmp_path, [("First", {"a.md": "one\n"}, "2026-10-30T10:00:00-07:00"),
                                ("Second", {"a.md": "two\n"}, "2026-11-02T10:00:00-08:00")])
    audit.meta(repo, "Someone Else", "someone@example.com")
    out = capsys.readouterr().out
    assert NAME not in out and EMAIL not in out
    assert "2 words, capitalised" in out and "all equal identity.txt's name: False" in out
    assert "2026-11-02: -0700 -> -0800" in out


def test_prepare_keeps_only_what_the_final_tree_lost(tmp_path, capsys):
    repo = make_repo(tmp_path, [
        ("Add pages", {"docs/a.md": "kept line\nold line\n", "docs/b.md": "gone page\n"}, None),
        ("Edit one, delete one", {"docs/a.md": "kept line\nnew line\n", "docs/b.md": None}, None),
    ])
    read = tmp_path / "read"
    audit.prepare(read, repo)
    tree, delta, messages = ((read / name).read_text() for name in ("tree.txt", "delta.txt", "messages.txt"))
    assert "=====FILE docs/a.md\n    1|kept line\n    2|new line\n" in tree
    assert "-old line" in delta and "+gone page" in delta and "docs/b.md] file deleted" in delta
    assert "kept line" not in delta and "new line" not in delta
    assert "Edit one, delete one" in messages and NAME not in messages
    assert "pass 3 reads tree.txt" in capsys.readouterr().out


def test_where_names_places_not_matches(tmp_path, capsys):
    repo = make_repo(tmp_path, [
        ("Add host page", {"docs/host.md": "Login: harbourmaster\n"}, None),
        ("Scrub host page", {"docs/host.md": "Login: alice\nAsk harbourmaster's twin\n"}, None),
    ])
    categories = tmp_path / "categories.tsv"
    categories.write_text("login name\tharbour\\w+\n")
    audit.where(categories, repo)
    out = capsys.readouterr().out
    assert "login name: 3 lines in 2 commits" in out and "final tree: docs/host.md:2" in out
    assert "harbourmaster" not in out


def test_map_marks_stand_ins_and_withholds_real_sides(tmp_path, capsys):
    repo = make_repo(tmp_path, [("Add page", {"docs/page.md": "Ask bob at cloud.example.com\n"}, None)])
    map_file = tmp_path / "map.txt"
    map_file.write_text("# real ==> stand-in\nharbourmaster==>bob\nharbour.example.net==>cloud.example.com\n")
    rules = audit.load_rules(map_file)
    audit.map_at(["docs/page.md:1"], rules, repo)
    audit.map_terms(["bob"], rules)
    out = capsys.readouterr().out
    assert "Ask ⟦bob⟧ at ⟦cloud.example.com⟧" in out and "stand-ins from rules [2, 3]" in out
    assert "'bob': stand-in side of rules [2]; real side of rules none" in out
    assert "harbour" not in out


def test_map_marks_back_reference_and_short_stand_ins(tmp_path, capsys):
    repo = make_repo(tmp_path, [("Add page", {"docs/page.md": "Server 198.51.100.10, grep '198\\.51\\.100\\.7', song 良宵, a b c\n"}, None)])
    map_file = tmp_path / "map.txt"
    map_file.write_text("regex:\\b10\\.1\\.1\\.(\\d{1,3})\\b==>198.51.100.\\1\n"
                        "regex:10\\\\\\.1\\\\\\.1\\\\\\.(\\d{1,3})==>198\\\\.51\\\\.100\\\\.\\1\n"
                        "harbourtune==>良宵\n"
                        "harbourmaster==>b\n")
    audit.map_at(["docs/page.md:1"], audit.load_rules(map_file), repo)
    out = capsys.readouterr().out
    assert "Server ⟦198.51.100.10⟧," in out and "'⟦198\\.51\\.100\\.7⟧'" in out
    assert "song ⟦良宵⟧" in out
    assert "a ⟦b⟧? c" in out  # a short ASCII stand-in only as a whole word, and only as a maybe
    assert "stand-ins from rules [1, 2, 3]" in out and "maybe from rules [4]" in out


def test_diff_gives_what_changed_since_the_audited_build(tmp_path, capsys):
    repo = make_repo(tmp_path, [("Audited", {"docs/a.md": "old line\nsame line\n"}, "2026-10-30T10:00:00+00:00")])
    hidden = tmp_path / "hidden.md"
    hidden.write_text("### 1. The domain\n")
    audit.mark(repo, hidden)
    git(repo, "commit", "-q", "--amend", "-m", "Audited, message reworded", date="2026-10-30T10:00:00+00:00")
    (repo / "docs/a.md").write_text("new line\nsame line\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "Later", date="2026-11-01T10:00:00+00:00")
    read = tmp_path / "read"
    assert audit.diff(read, repo, hidden) == 0
    changes, messages = (read / "diff.txt").read_text(), (read / "messages.txt").read_text()
    assert "+new line" in changes and "-old line" in changes and "+same line" not in changes
    assert "Later" in messages and "Audited, message reworded" in messages
    assert "2 commit messages" in capsys.readouterr().out


def test_diff_without_an_audited_build_asks_for_a_full_audit(tmp_path, capsys):
    repo = make_repo(tmp_path, [("First", {"a.md": "one\n"}, None)])
    assert audit.diff(tmp_path / "read", repo, tmp_path / "hidden.md") == 1
    assert "full audit" in capsys.readouterr().out


def test_diff_names_a_hidden_list_category_added_since_the_audit(tmp_path, capsys):
    repo = make_repo(tmp_path, [("First", {"a.md": "one\n"}, None)])
    hidden = tmp_path / "hidden.md"
    hidden.write_text("# Hidden list\n\n### 1. The domain\n\ntext\n")
    audit.mark(repo, hidden)
    hidden.write_text("# Hidden list\n\n### 1. The domain\n\n### 2. Pets' names\n")
    assert audit.diff(tmp_path / "read", repo, hidden) == 0
    out = capsys.readouterr().out
    assert "NEW CATEGORY: 2. Pets' names" in out and "1. The domain" not in out.split("NEW CATEGORY")[-1]


def test_diff_holds_a_line_that_new_commits_added_then_removed(tmp_path):
    repo = make_repo(tmp_path, [("Audited", {"a.md": "one\n"}, "2026-10-30T10:00:00+00:00")])
    hidden = tmp_path / "hidden.md"
    hidden.write_text("### 1. The domain\n")
    audit.mark(repo, hidden)
    for text, when in (("one\nfleeting line\n", "2026-11-01T10:00:00+00:00"), ("one\n", "2026-11-02T10:00:00+00:00")):
        (repo / "a.md").write_text(text)
        git(repo, "commit", "-q", "-am", "Edit", date=when)
    audit.diff(tmp_path / "read", repo, hidden)
    assert "+fleeting line" in (tmp_path / "read" / "diff.txt").read_text()
