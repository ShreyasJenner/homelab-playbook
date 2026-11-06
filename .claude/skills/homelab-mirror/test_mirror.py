"""Tests for mirror.py's rewrite: each builds a throwaway Playbook clone and rewrites it as build does."""
import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("mirror", Path(__file__).with_name("mirror.py"))
mirror = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mirror)


def git(repo, *args):
    env = {**os.environ, "GIT_AUTHOR_NAME": "Real Name", "GIT_AUTHOR_EMAIL": "real@example.org",
           "GIT_COMMITTER_NAME": "Real Name", "GIT_COMMITTER_EMAIL": "real@example.org",
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    return subprocess.run(["git", "-C", str(repo), *args], check=True, env=env,
                          capture_output=True, text=True).stdout


def make_repo(tmp_path, commits):
    repo = tmp_path / "rebuilt"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    for message, files in commits:
        for path, text in files.items():
            f = repo / path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", message)
    return repo


def write(tmp_path, name, text):
    f = tmp_path / name
    f.write_text(text)
    return f


@pytest.fixture
def rewritten(tmp_path):
    repo = make_repo(tmp_path, [
        ("Add pages", {"docs/a.md": "keep harbour\nharbour line about Loadster\n",
                       "docs/loadster.md": "all about it\n", "blog/post.md": "draft\n"}),
        ("Loadster: fix its page", {"docs/loadster.md": "fixed\n"}),
        ("Edit a about Loadster", {"docs/a.md": "keep harbour\nharbour line about Loadster\nmore\n"}),
    ])
    files = {
        "cuts": write(tmp_path, "cuts.txt", "# cut\nregex:harbour line about Loadster\\n==>\n"
                                            "regex: about Loadster==>\n"),
        "map": write(tmp_path, "map.txt", "# map\nharbour==>port\n"),
        "leave_out": write(tmp_path, "leave-out.txt", "# left out\nblog/\nglob:docs/loadster*\n"),
        "notice": write(tmp_path, "notice.md", "# Notice\n"),
    }
    mirror.rewrite(repo, tmp_path / "work", name="Stand Name", email="stand@example.com", **files)
    return repo


def test_cuts_run_on_the_playbook_text_before_the_map(rewritten):
    assert git(rewritten, "show", "main:docs/a.md") == "keep port\nmore\n"


def test_left_out_paths_are_gone_from_every_commit(rewritten):
    names = set(git(rewritten, "log", "--all", "--format=", "--name-only").split())
    assert names == {"docs/a.md", "README.md"}


def test_commit_left_empty_is_dropped_and_messages_are_cut(rewritten):
    assert git(rewritten, "log", "--reverse", "--format=%s", "main").splitlines() == ["Add pages", "Edit a"]


def test_identity_and_offset_are_replaced(rewritten):
    assert set(git(rewritten, "log", "--format=%an %ae %ad", "--date=format:%z", "main").splitlines()) == {
        "Stand Name stand@example.com +0000"}


def test_a_rule_without_a_stand_in_side_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="no ==>"):
        mirror.rules_text(write(tmp_path, "cuts.txt", "regex:oops\n"))
