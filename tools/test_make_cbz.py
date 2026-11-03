"""Tests for make-cbz.py. Run with: python -m pytest tools"""

import importlib.util
import xml.etree.ElementTree as ET
import zipfile
from decimal import Decimal
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("make_cbz", Path(__file__).with_name("make-cbz.py"))
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)

D = Decimal


def make_series(root, chapters=("c001", "c002", "c003", "c004"), pages=3):
    src = root / "src"
    for name in chapters:
        (src / name).mkdir(parents=True)
        for i in range(pages, 0, -1):
            (src / name / f"{i}.jpg").write_bytes(f"{name}-{i}".encode())
    return src


def write_toml(src, volumes, **fields):
    fields = {"series": "My Girl", "writer": "Mizuho Sachiko", "year": 2005,
              "status": "ongoing", "language": "en", "summary": "A father & his daughter.",
              "genres": ["Drama"], **fields}
    lines = [f"{k} = {v!r}".replace("'", '"') if not isinstance(v, list)
             else f"{k} = [{', '.join(repr(x).replace(chr(39), chr(34)) for x in v)}]"
             for k, v in fields.items()]
    lines.append("[volumes]")
    lines += [f"{k} = {v}" for k, v in volumes.items()]
    (src / "series.toml").write_text("\n".join(lines) + "\n")


def info(cbz):
    with zipfile.ZipFile(cbz) as z:
        return ET.fromstring(z.read("ComicInfo.xml"))


@pytest.mark.parametrize("name, number", [
    ("c001", D(1)), ("Chapter 10.5", D("10.5")), ("Vol 2 Ch 7", D(7)), ("c100", D(100)), ("c010.50", D("10.5")),
])
def test_chapter_number(name, number):
    assert mc.chapter_number(name) == number


@pytest.mark.parametrize("name", ["extras", "c010.25"])
def test_chapter_number_rejects(name):
    with pytest.raises(mc.Error):
        mc.chapter_number(name)


def test_fmt_and_compress():
    assert mc.fmt(D("10.5"), 3) == "010.5"
    assert mc.fmt(D(100).normalize(), 3) == "100"
    assert mc.compress([D(1), D(2), D(3), D("3.5"), D(5)]) == "1-3, 3.5, 5"


def test_parse_spec():
    chapters = {D(n): None for n in ("1", "2", "3", "3.5", "4", "7.5", "8")}
    assert mc.parse_spec("1-4", chapters, 1) == [D(1), D(2), D(3), D("3.5"), D(4)]
    assert mc.parse_spec("7.5, 8", chapters, 2) == [D("7.5"), D(8)]
    with pytest.raises(mc.Error, match="no folder for chapter 5"):
        mc.parse_spec("4-5", chapters, 3)
    with pytest.raises(mc.Error, match="no folder for chapter 6.5"):
        mc.parse_spec("6.5", chapters, 3)
    with pytest.raises(mc.Error, match="backwards"):
        mc.parse_spec("4-1", chapters, 3)


def test_template_written_when_no_toml(tmp_path):
    src = make_series(tmp_path)
    mc.run(src, tmp_path / "out")
    text = (src / "series.toml").read_text()
    assert "# Chapters found here: 1-4" in text
    assert not (tmp_path / "out").exists()


def test_packs_volumes_and_loose_chapters(tmp_path):
    src = make_series(tmp_path)
    (src / "c002" / "credits.txt").write_text("x")
    write_toml(src, {"1": '"1-2"', "2": '{ chapters = "3", year = 2006 }'})
    mc.run(src, tmp_path)
    out = tmp_path / "My Girl"
    assert sorted(p.name for p in out.iterdir()) == [
        "My Girl c004.cbz", "My Girl v01.cbz", "My Girl v02.cbz", "series.toml"]
    with zipfile.ZipFile(out / "My Girl v01.cbz") as z:
        assert z.namelist() == ["ComicInfo.xml"] + [
            f"c00{c}-p00{p}.jpg" for c in (1, 2) for p in (1, 2, 3)]
        assert all(i.compress_type == zipfile.ZIP_STORED for i in z.infolist())
        assert z.read("c002-p003.jpg") == b"c002-3"

    v1 = info(out / "My Girl v01.cbz")
    assert v1.findtext("Series") == "My Girl"
    assert v1.findtext("Volume") == "1"
    assert v1.find("Number") is None
    assert v1.find("Count") is None
    assert v1.findtext("Year") == "2005"
    assert v1.findtext("Summary") == "A father & his daughter."
    assert v1.find("Penciller") is None
    assert v1.findtext("Manga") == "YesAndRightToLeft"
    assert info(out / "My Girl v02.cbz").findtext("Year") == "2006"
    c4 = info(out / "My Girl c004.cbz")
    assert c4.findtext("Number") == "4"
    assert c4.find("Volume") is None


def test_count_only_when_completed(tmp_path):
    src = make_series(tmp_path)
    write_toml(src, {"1": '"1-2"', "2": '"3-4"'}, status="completed")
    mc.run(src, tmp_path)
    assert info(tmp_path / "My Girl" / "My Girl v01.cbz").findtext("Count") == "2"


def test_overlap_fails(tmp_path):
    src = make_series(tmp_path)
    write_toml(src, {"1": '"1-2"', "2": '"2-3"'})
    with pytest.raises(mc.Error, match="chapter 2 is in both volume 1 and volume 2"):
        mc.run(src, tmp_path)


def test_folder_overrides_output_name(tmp_path):
    src = make_series(tmp_path)
    write_toml(src, {"1": '"1-4"'}, folder="My Girl (Manga)")
    mc.run(src, tmp_path)
    assert (tmp_path / "My Girl (Manga)" / "My Girl v01.cbz").exists()


def test_skip_then_force(tmp_path, capsys):
    src = make_series(tmp_path)
    write_toml(src, {"1": '"1-4"'})
    mc.run(src, tmp_path)
    cbz = tmp_path / "My Girl" / "My Girl v01.cbz"
    cbz.write_bytes(b"old")
    mc.run(src, tmp_path)
    assert cbz.read_bytes() == b"old"
    assert "skip (exists)" in capsys.readouterr().out
    mc.run(src, tmp_path, force=True)
    assert zipfile.is_zipfile(cbz)


def test_volume_supersedes_loose_chapters(tmp_path, capsys):
    src = make_series(tmp_path)
    write_toml(src, {"1": '"1-2"'})
    mc.run(src, tmp_path)
    out = tmp_path / "My Girl"
    assert (out / "My Girl c003.cbz").exists()
    write_toml(src, {"1": '"1-2"', "2": '"3-4"'})
    capsys.readouterr()
    mc.run(src, tmp_path)
    assert not (out / "My Girl c003.cbz").exists()
    assert not (out / "My Girl c004.cbz").exists()
    printed = capsys.readouterr().out
    assert "ssh homeserver" in printed and "My Girl c003.cbz" in printed


def test_dry_run_writes_nothing(tmp_path, capsys):
    src = make_series(tmp_path)
    write_toml(src, {"1": '"1-4"'})
    mc.run(src, tmp_path, dry_run=True)
    assert not (tmp_path / "My Girl").exists()
    assert "write          My Girl v01.cbz  (chapters 1-4, 12 pages)" in capsys.readouterr().out


def test_output_folder_inside_source_is_not_a_chapter(tmp_path):
    src = make_series(tmp_path)
    write_toml(src, {"1": '"1-4"'}, series="Mob Psycho 100")
    mc.run(src, src)
    mc.run(src, src)  # the second run sees ./Mob Psycho 100/ inside the source
