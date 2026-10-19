#!/usr/bin/env python3
"""The assembly guide as a step model, read from its Markdown.

The Markdown is the one source of every sentence; this module reads it
by the conventions the guide is written to and gives the rest of the
tooling (the shot list, the tests, later the template) a structure to
work from:

* ``Guide`` has a title and sections, one per H2;
* a ``Section`` has a title, its blocks, and its steps, one per H3 whose
  text begins ``Step N:``;
* a ``Step`` has its number and title, its action lines (the items of
  its numbered list), its pictures as (alt, path) pairs with the caption
  that follows each, its ``check`` and ``by_touch`` paragraphs (the ones
  beginning ``**Check:**`` and ``**By touch:**``), and its shot requests,
  read from comments of the form
  ``<!-- shot: NAME | angle: ... | show: ... -->``.

Usage:
    python scripts/guide_model.py --report      # one line per step
    python scripts/guide_model.py --json        # build/guide_model.json

Standard library only. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "Documentation" / "Step_2_Guide_Option_2_Custom_Braille_Embosser_V2_Assembly_Guide_By_Touch.md"
OUT_JSON = ROOT / "build" / "guide_model.json"

STEP_HEADING = re.compile(r"^### Step (\d+): (.+?)\s*$")
HEADING = re.compile(r"^(#{1,6}) (.+?)\s*#*$")
IMAGE_LINE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$")
SHOT = re.compile(r"<!--\s*shot:\s*([^|]+?)\s*\|\s*angle:\s*([^|]+?)\s*\|\s*show:\s*(.+?)\s*-->")
NUMBERED = re.compile(r"^\d+\. (.*)$")
BY_TOUCH = "**By touch:**"
CHECK = "**Check:**"
CAREFUL = "**Careful:"


@dataclass
class Shot:
    name: str
    angle: str
    show: str


@dataclass
class Picture:
    alt: str
    path: str
    caption: str = ""


@dataclass
class Step:
    number: int
    title: str
    lines: List[str] = field(default_factory=list)
    pictures: List[Picture] = field(default_factory=list)
    shots: List[Shot] = field(default_factory=list)
    check: str = ""
    by_touch: str = ""
    careful: str = ""
    you_need: str = ""

    @property
    def has_picture(self) -> bool:
        return bool(self.pictures or self.shots)


@dataclass
class Section:
    title: str
    steps: List[Step] = field(default_factory=list)
    pictures: List[Picture] = field(default_factory=list)
    shots: List[Shot] = field(default_factory=list)
    by_touch: List[str] = field(default_factory=list)


@dataclass
class Guide:
    title: str
    sections: List[Section] = field(default_factory=list)

    @property
    def steps(self) -> List[Step]:
        return [s for section in self.sections for s in section.steps]


def _paragraphs(lines: Sequence[str]) -> List[str]:
    """The text blocks of a run of lines: paragraphs, list items and
    picture lines, each as one string, blank lines dropped."""
    out: List[str] = []
    current: List[str] = []
    for line in lines:
        if not line.strip():
            if current:
                out.append(" ".join(current))
                current = []
            continue
        if IMAGE_LINE.match(line.strip()) or NUMBERED.match(line) or HEADING.match(line) or line.lstrip().startswith("<!--"):
            if current:
                out.append(" ".join(current))
                current = []
            out.append(line.rstrip())
            continue
        current.append(line.strip())
    if current:
        out.append(" ".join(current))
    return out


def _fill(target, blocks: Sequence[str]) -> None:
    """Pictures, shots, check and by-touch text from a run of blocks, into
    a Step or a Section."""
    i = 0
    while i < len(blocks):
        b = blocks[i]
        m = IMAGE_LINE.match(b.strip())
        if m:
            caption = ""
            if i + 1 < len(blocks) and not (IMAGE_LINE.match(blocks[i + 1].strip()) or blocks[i + 1].startswith(("**", "<!--", "#")) or NUMBERED.match(blocks[i + 1])):
                caption = blocks[i + 1]
                i += 1
            target.pictures.append(Picture(m.group(1), m.group(2), caption))
        elif b.lstrip().startswith("<!--"):
            for s in SHOT.finditer(b):
                target.shots.append(Shot(s.group(1).strip(), s.group(2).strip(), s.group(3).strip()))
        elif isinstance(target, Step):
            n = NUMBERED.match(b)
            if n:
                target.lines.append(n.group(1).strip())
            elif b.startswith(CHECK):
                target.check = b[len(CHECK):].strip()
            elif b.startswith(BY_TOUCH):
                target.by_touch = b[len(BY_TOUCH):].strip()
            elif b.startswith(CAREFUL):
                target.careful = b
            elif b.startswith("You need"):
                target.you_need = b
        elif b.startswith(BY_TOUCH):
            target.by_touch.append(b[len(BY_TOUCH):].strip())
        i += 1


def parse(text: str) -> Guide:
    lines = text.replace("\r\n", "\n").split("\n")
    title = ""
    sections: List[Section] = []
    section: Optional[Section] = None
    step: Optional[Step] = None
    run: List[str] = []

    def flush() -> None:
        nonlocal run
        if not run:
            return
        blocks = _paragraphs(run)
        if step is not None:
            _fill(step, blocks)
        elif section is not None:
            _fill(section, blocks)
        run = []

    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        h = HEADING.match(line)
        if h:
            level, text_ = len(h.group(1)), h.group(2)
            if level == 1:
                flush()
                title = text_
                continue
            if level == 2:
                flush()
                step = None
                section = Section(text_)
                sections.append(section)
                continue
            if level == 3:
                flush()
                m = STEP_HEADING.match(line.strip())
                if m and section is not None:
                    step = Step(int(m.group(1)), m.group(2))
                    section.steps.append(step)
                else:
                    step = None
                continue
        run.append(line)
    flush()
    if not title:
        raise ValueError("the guide has no H1")
    return Guide(title, sections)


def load(path: Path = GUIDE) -> Guide:
    return parse(path.read_text(encoding="utf-8"))


def report(guide: Guide) -> List[str]:
    out = []
    for section in guide.sections:
        for s in section.steps:
            out.append(f"Step {s.number:>2}: {s.title:40.40} lines={len(s.lines)} pictures={len(s.pictures)} "
                       f"shots={len(s.shots)} check={'yes' if s.check else 'NO'} by-touch={'yes' if s.by_touch else 'NO'}")
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true", help="one line per step")
    ap.add_argument("--json", action="store_true", help=f"write {OUT_JSON.relative_to(ROOT).as_posix()}")
    args = ap.parse_args(argv)
    guide = load()
    if args.json:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(asdict(guide), indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(f"{OUT_JSON.relative_to(ROOT).as_posix()}: {len(guide.steps)} steps in {len(guide.sections)} sections")
    if args.report or not args.json:
        print("\n".join(report(guide)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
