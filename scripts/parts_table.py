#!/usr/bin/env python3
"""The parts table of the assembly guide, from ``Documentation/parts.json``.

``parts.json`` is the one place the facts about each part live: its plain
name, its file in ``Build_Files/3D_Printing_Files/STL/``, the engineering
names it had before the release, its size in mm, and the sentence of what it
does. The guide prints those facts as a pipe table between the markers
``<!-- parts-table -->`` and ``<!-- /parts-table -->``; this script writes
that block and checks that it has not drifted from the facts.

Usage:
    python scripts/parts_table.py            # print the table
    python scripts/parts_table.py --check    # exit 1 when the guide's block differs from the table
    python scripts/parts_table.py --write    # replace the guide's block with the table

Standard library only. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "Documentation" / "parts.json"
GUIDE = ROOT / "Documentation" / "Step_2_Guide_Option_2_Custom_Braille_Embosser_V2_Assembly_Guide_By_Touch.md"
START = "<!-- parts-table -->"
END = "<!-- /parts-table -->"
COLUMNS = ("Part", "File")   # no size: no step uses one (D67)
GENERATED = "generated for your text"


def load_parts(path: Path = PARTS) -> List[Dict[str, Any]]:
    parts = json.loads(path.read_text(encoding="utf-8"))
    ids = [p["id"] for p in parts]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path.name} repeats a part id: {sorted(i for i in ids if ids.count(i) > 1)}")
    return parts


def file_text(part: Dict[str, Any]) -> str:
    return f"`{part['file']}`" if part.get("file") else GENERATED


def table_markdown(parts: Sequence[Dict[str, Any]]) -> str:
    rows = ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    for p in parts:
        name = p["name"] + (" (optional)" if p.get("optional") else "")
        rows.append(f"| {name} | {file_text(p)} |")
    return "\n".join(rows)


def guide_block(text: str) -> Optional[str]:
    """The table between the markers in the guide, or None when the guide has no markers."""
    start = text.find(START)
    end = text.find(END)
    if start < 0 or end < 0 or end < start:
        return None
    return text[start + len(START):end].strip("\n")


def replace_block(text: str, table: str) -> str:
    start = text.find(START)
    end = text.find(END)
    if start < 0 or end < 0 or end < start:
        raise ValueError(f"{GUIDE.name} has no {START} ... {END} block to write into")
    return text[:start + len(START)] + "\n" + table + "\n" + text[end:]


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 when the guide's block differs from the table")
    ap.add_argument("--write", action="store_true", help="replace the guide's block with the table")
    args = ap.parse_args(argv)
    table = table_markdown(load_parts())
    if not (args.check or args.write):
        print(table)
        return 0
    if not GUIDE.exists():
        print(f"{GUIDE.relative_to(ROOT).as_posix()} does not exist")
        return 1
    text = GUIDE.read_text(encoding="utf-8")
    if args.write:
        GUIDE.write_text(replace_block(text, table), encoding="utf-8", newline="\n")
        print(f"{GUIDE.relative_to(ROOT).as_posix()}: parts table written")
        return 0
    block = guide_block(text)
    if block is None:
        print(f"{GUIDE.relative_to(ROOT).as_posix()} has no {START} block")
        return 1
    if block != table:
        print(f"{GUIDE.relative_to(ROOT).as_posix()}: the parts table differs from parts.json; run --write")
        return 1
    print("parts table matches parts.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
