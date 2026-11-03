#!/usr/bin/env python3
"""Pack a series' chapter folders into one CBZ per volume, for Kavita.

Usage: make-cbz <source dir> [--dry-run] [--force]

Reads <source dir>/series.toml (writing a blank one if there is none) and
writes the CBZs to ./<folder>/ in the current directory. Chapters in no volume
are packed one CBZ each. It ends by printing the rsync command that copies the
folder to homelab. See docs/services/kavita.md.

Standard library only, so it runs without a venv.
"""

import argparse
import math
import os
import re
import shlex
import shutil
import sys
import tomllib
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

SERVER = "homeserver"
SERVER_MANGA = "/mnt/hdd-4tb/media/manga"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
STATUSES = ("ongoing", "completed")

TEMPLATE = '''\
# series.toml: metadata for make-cbz. Fill it in, then run: make-cbz <this folder>
# Chapters found here: {found}

# The series name, used in every file name and in ComicInfo. If the series is
# already on the server, use exactly the name Kavita shows for it there:
# a different name splits the series.
series = ""

# Optional: the series' folder on the server, when it differs from `series`
# (e.g. "Komi Can't Communicate (Manga)").
# folder = ""

writer = ""
# Optional: only when the artist is not the writer.
# penciller = ""

# The year the series started. A volume can override it (see [volumes]).
year = 0

# "ongoing" or "completed". Kavita shows a completed series as Completed.
status = "ongoing"

# ISO 639-1 code of the language the pages are in, not the original's.
language = "en"

summary = """
"""

genres = []

# Volume number = its chapters, as ranges and lists: "1-7", "1-7, 7.5, 8".
# A range takes in the decimal chapters inside it (1-7 includes 3.5).
# A volume with its own year: 3 = {{ chapters = "15-21", year = 2004 }}
# Chapters in no volume are packed one CBZ per chapter.
[volumes]
# 1 = "1-7"
'''


class Error(Exception):
    pass


@dataclass
class Series:
    name: str
    folder: str
    writer: str
    penciller: str
    year: int
    completed: bool
    language: str
    summary: str
    genres: list
    volumes: dict  # volume number -> (chapter spec, year)


@dataclass
class Pack:
    filename: str
    volume: int | None
    chapter: Decimal | None
    chapters: list
    year: int


def warn(message):
    print(f"make-cbz: warning: {message}", file=sys.stderr)


def natural_key(name):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name.lower())]


def fmt(number, width=0):
    """1 -> "001", 10.5 -> "010.5" for width 3."""
    whole, _, frac = format(number, "f").partition(".")
    return whole.zfill(width) + (f".{frac}" if frac else "")


def chapter_number(name):
    """The chapter number of a folder: the last number in its name."""
    found = re.findall(r"\d+(?:\.\d+)?", name)
    if not found:
        raise Error(f"chapter folder {name!r} has no number in its name")
    number = Decimal(found[-1]).normalize()
    if number.as_tuple().exponent < -1:
        raise Error(f"chapter folder {name!r}: Kavita reads only one decimal digit, "
                    f"so chapter {fmt(number)} would be misnumbered")
    return number


def compress(numbers):
    """[1, 2, 3, 3.5, 5] -> "1-3, 3.5, 5"."""
    parts, run = [], []
    for n in sorted(numbers):
        if run and n == n.to_integral_value() and n == run[-1] + 1:
            run.append(n)
            continue
        if run:
            parts.append(fmt(run[0]) if len(run) == 1 else f"{fmt(run[0])}-{fmt(run[-1])}")
        run = [n] if n == n.to_integral_value() else []
        if not run:
            parts.append(fmt(n))
    if run:
        parts.append(fmt(run[0]) if len(run) == 1 else f"{fmt(run[0])}-{fmt(run[-1])}")
    return ", ".join(parts)


def find_chapters(src, exclude=None):
    chapters = {}
    for folder in sorted(src.iterdir(), key=lambda p: natural_key(p.name)):
        if not folder.is_dir() or folder.name.startswith(".") or folder == exclude:
            continue
        number = chapter_number(folder.name)
        if number in chapters:
            raise Error(f"chapter folders {chapters[number].name!r} and {folder.name!r} "
                        f"are both chapter {fmt(number)}")
        chapters[number] = folder
    if not chapters:
        raise Error(f"no chapter folders in {src}")
    return chapters


def chapter_pages(folder):
    pages = []
    for entry in sorted(folder.iterdir(), key=lambda p: natural_key(p.name)):
        if entry.is_file() and entry.suffix.lower() in IMAGE_EXTS:
            pages.append(entry)
        else:
            warn(f"left out {entry}: not an image")
    if not pages:
        raise Error(f"chapter folder {folder} has no images")
    return pages


def parse_spec(spec, chapters, volume):
    """The chapters a volume's spec ("1-7, 7.5") names."""
    picked = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        lo, sep, hi = part.partition("-")
        try:
            lo = Decimal(lo.strip())
            hi = Decimal(hi.strip()) if sep else lo
        except InvalidOperation:
            raise Error(f"volume {volume}: can't read chapters {part!r}") from None
        if lo > hi:
            raise Error(f"volume {volume}: range {part!r} runs backwards")
        wanted = [lo] if not sep else [Decimal(n) for n in range(math.ceil(lo), math.floor(hi) + 1)]
        missing = [n for n in wanted if n not in chapters]
        if missing:
            raise Error(f"volume {volume}: no folder for chapter {compress(missing)}")
        picked |= {n for n in chapters if lo <= n <= hi}
    if not picked:
        raise Error(f"volume {volume} has no chapters")
    return sorted(picked)


def load_config(path):
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        raise Error(f"{path}: {e}") from None
    name = str(data.get("series", "")).strip()
    if not name:
        raise Error(f"{path}: `series` is empty")
    folder = str(data.get("folder") or name).strip()
    for key, value in (("series", name), ("folder", folder)):
        if "/" in value:
            raise Error(f"{path}: `{key}` can't contain '/'")
    status = data.get("status", "ongoing")
    if status not in STATUSES:
        raise Error(f"{path}: `status` must be one of {', '.join(STATUSES)}, not {status!r}")
    year = int(data.get("year", 0))
    volumes = {}
    for key, value in data.get("volumes", {}).items():
        try:
            volume = int(key)
        except ValueError:
            raise Error(f"{path}: volume {key!r} is not a whole number") from None
        if isinstance(value, str):
            volumes[volume] = (value, year)
        elif isinstance(value, dict) and "chapters" in value:
            volumes[volume] = (str(value["chapters"]), int(value.get("year", year)))
        else:
            raise Error(f"{path}: volume {key} must be \"<chapters>\" or {{ chapters = ..., year = ... }}")
    return Series(
        name=name,
        folder=folder,
        writer=str(data.get("writer", "")).strip(),
        penciller=str(data.get("penciller", "")).strip(),
        year=year,
        completed=status == "completed",
        language=str(data.get("language", "")).strip(),
        summary=str(data.get("summary", "")).strip(),
        genres=[str(g) for g in data.get("genres", [])],
        volumes=volumes,
    )


def plan(series, chapters):
    """The CBZs to write, and the loose-chapter file names the volumes supersede."""
    vwidth = max(2, len(str(max(series.volumes, default=1))))
    cwidth = max(3, len(str(int(max(chapters)))))
    packs, assigned = [], {}
    for volume in sorted(series.volumes):
        spec, year = series.volumes[volume]
        numbers = parse_spec(spec, chapters, volume)
        for n in numbers:
            if n in assigned:
                raise Error(f"chapter {fmt(n)} is in both volume {assigned[n]} and volume {volume}")
            assigned[n] = volume
        packs.append(Pack(f"{series.name} v{volume:0{vwidth}d}.cbz", volume, None, numbers, year))
    for n in sorted(chapters):
        if n not in assigned:
            packs.append(Pack(f"{series.name} c{fmt(n, cwidth)}.cbz", None, n, [n], series.year))
    superseded = [f"{series.name} c{fmt(n, cwidth)}.cbz" for n in sorted(assigned)]
    return packs, superseded, cwidth


def comic_info(series, pack, count):
    root = ET.Element("ComicInfo")

    def add(tag, value):
        if value is not None and value != "":
            ET.SubElement(root, tag).text = str(value)

    add("Series", series.name)
    if pack.chapter is not None:
        add("Number", format(pack.chapter, "f"))
    add("Volume", pack.volume)
    if series.completed:
        add("Count", count)
    add("Summary", series.summary)
    if pack.year > 0:
        add("Year", pack.year)
    add("Writer", series.writer)
    if series.penciller != series.writer:
        add("Penciller", series.penciller)
    add("Genre", ", ".join(series.genres))
    add("LanguageISO", series.language)
    add("Manga", "YesAndRightToLeft")
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def write_cbz(path, info, chapter_pages, cwidth):
    """Write to a temp name, then rename, so a reader never sees half a file
    and an existing file (perhaps a hardlink) is replaced, never rewritten."""
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED) as z:
            z.writestr("ComicInfo.xml", info)
            for number, pages in chapter_pages:
                pwidth = max(3, len(str(len(pages))))
                for i, page in enumerate(pages, 1):
                    z.write(page, f"c{fmt(number, cwidth)}-p{i:0{pwidth}d}{page.suffix.lower()}")
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def run(src, out_root, dry_run=False, force=False):
    config_path = src / "series.toml"
    if not config_path.exists():
        config_path.write_text(TEMPLATE.format(found=compress(find_chapters(src))))
        print(f"Wrote {config_path}. Fill it in and run again.")
        return
    series = load_config(config_path)
    out = out_root / series.folder
    chapters = find_chapters(src, exclude=out)
    packs, superseded, cwidth = plan(series, chapters)
    count = max(series.volumes) if series.volumes else int(max(chapters))
    pages = {n: chapter_pages(folder) for n, folder in chapters.items()}

    if not dry_run:
        out.mkdir(parents=True, exist_ok=True)
    for pack in packs:
        path = out / pack.filename
        if path.exists() and not force:
            action = "skip (exists)"
        else:
            action = "replace" if path.exists() else "write"
        total = sum(len(pages[n]) for n in pack.chapters)
        print(f"{action:14} {pack.filename}  (chapters {compress(pack.chapters)}, {total} pages)")
        if dry_run or action.startswith("skip"):
            continue
        write_cbz(path, comic_info(series, pack, count), [(n, pages[n]) for n in pack.chapters], cwidth)

    removed = []
    for name in superseded:
        if (out / name).exists():
            print(f"{'delete':14} {name}  (now in a volume)")
            removed.append(name)
            if not dry_run:
                (out / name).unlink()

    copy = out / "series.toml"
    if not dry_run and not (copy.exists() and copy.samefile(config_path)):
        shutil.copy2(config_path, copy)

    remote = f"{SERVER_MANGA}/{series.folder}"
    print(f"\n{'Would copy' if dry_run else 'Copy'} to {SERVER} with:")
    print(f"  rsync -rt --chmod=D775,F664 {shlex.quote(str(out) + '/')} "
          f"{shlex.quote(f'{SERVER}:{remote}/')}")
    if removed:
        command = "rm -f -- " + " ".join(shlex.quote(f"{remote}/{name}") for name in removed)
        print("Then delete the superseded chapters on the server:")
        print(f"  ssh {SERVER} {shlex.quote(command)}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="make-cbz", description=__doc__.split("\n")[0])
    parser.add_argument("source", type=Path, help="folder of chapter folders, holding series.toml")
    parser.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    parser.add_argument("--force", action="store_true", help="replace CBZs that already exist")
    args = parser.parse_args(argv)
    try:
        run(args.source, Path.cwd(), args.dry_run, args.force)
    except (Error, OSError) as e:
        sys.exit(f"make-cbz: {e}")


if __name__ == "__main__":
    main()
