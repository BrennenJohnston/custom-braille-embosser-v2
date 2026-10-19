#!/usr/bin/env python3
"""The shot list: every photograph the guide still asks for, as one page
for whoever holds the camera.

Read from the guide through ``guide_model``: each ``<!-- shot: ... -->``
comment becomes a row (the section or step it sits in, the shot's name,
the angle to shoot from, and what must be in the frame), and any step with
no picture at all gets a row of its own. The page is a working file for
whoever holds the camera, written to ``build/Shot_List.md``; ``--check``
exits 1 when a page on disk is not what the guide now asks for.

The angle words are the guide's own: standard (front, centred, about 45
degrees above the table, window toward the camera), top, low (about 15
degrees above the table), close (the feature fills the frame; always
paired with a standard shot), hands (the builder's hands in the frame,
coming in from the sides so the join stays visible).

Usage:
    python scripts/shot_list.py            # write the page
    python scripts/shot_list.py --check    # exit 1 when the page is stale

Standard library only. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.guide_model import Guide, load  # noqa: E402

OUT = ROOT / "build" / "Shot_List.md"
TITLE = "Shot list for the assembly guide"
INTRO = ("Every photograph the assembly guide still asks for, in the order the guide uses them. Shoot on the same "
         "mat, with the same light and the same kit as the photographs already in the guide. The angle words: "
         "standard is from the front, centred, about 45 degrees above the table, with the Base's window toward the "
         "camera; top is straight down; low is about 15 degrees above the table; close means the feature fills the "
         "frame and is always paired with a standard shot of the same moment; hands means the builder's hands are in "
         "the frame, coming in from the sides so the join stays visible. Name each file after the shot's name.")
COLUMNS = ("Where", "Shot", "Angle", "What must be in the frame")
NO_PICTURE = "no picture yet"


def rows_for(guide: Guide) -> List[List[str]]:
    rows: List[List[str]] = []
    for section in guide.sections:
        for shot in section.shots:
            rows.append([section.title, shot.name, shot.angle, shot.show])
        for step in section.steps:
            for shot in step.shots:
                rows.append([f"Step {step.number}", shot.name, shot.angle, shot.show])
            if not step.has_picture:
                rows.append([f"Step {step.number}", NO_PICTURE, "standard, hands", f"the action of the step: {step.title}"])
    return rows


def page(guide: Guide) -> str:
    rows = rows_for(guide)
    lines = [f"# {TITLE}", "", INTRO, ""]
    if not rows:
        lines += ["The guide asks for no more photographs.", ""]
        return "\n".join(lines)
    lines += ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    for r in rows:
        lines.append("| " + " | ".join(c.replace("|", "/") for c in r) + " |")
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 when the page on disk is stale")
    args = ap.parse_args(argv)
    text = page(load())
    if args.check:
        on_disk = OUT.read_text(encoding="utf-8").replace("\r\n", "\n") if OUT.exists() else None
        if on_disk != text:
            print(f"{OUT.relative_to(ROOT).as_posix()} is stale; run scripts/shot_list.py")
            return 1
        print(f"{OUT.relative_to(ROOT).as_posix()} is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"{OUT.relative_to(ROOT).as_posix()}: {len(rows_for(load()))} shots")
    return 0


if __name__ == "__main__":
    sys.exit(main())
