#!/usr/bin/env python3
"""The tactile assembly map as one file, for MakerWorld's customizer.

MakerWorld's Parametric Model Maker takes a single OpenSCAD file and cannot
read a local ``include``, so the map file and the outlines it includes are
written together into
``Build_Files/3D_Printing_Files/Tactile_Assembly_Map/Custom_Braille_Embosser_V2_Tactile_Assembly_Map_MakerWorld.scad``.
The copy differs from the map file in four places and nowhere else:

* its heading says what it is and that it is written by this script;
* the ``include`` line is gone;
* the outlines stand under the ``[Hidden]`` heading, so the customizer does
  not offer them as dials;
* it opens on Plate 1, because "All plates (preview)" is larger than a print
  bed and a MakerWorld visitor who generates without choosing would get it.

Every dial, range and line of geometry is the map file's own. ``--check``
exits 1 when the copy is not what the two sources give (the test runs it).

Usage:
    python scripts/tactile_assembly_map_makerworld.py           # write the copy
    python scripts/tactile_assembly_map_makerworld.py --check   # compare, exit 1 if stale

Stdlib only. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
MAP_DIR = ROOT / "Build_Files" / "3D_Printing_Files" / "Tactile_Assembly_Map"
MAP_SCAD = MAP_DIR / "Custom_Braille_Embosser_V2_Tactile_Assembly_Map.scad"
SHAPES_SCAD = MAP_DIR / "tactile_assembly_map_shapes.scad"
COPY = MAP_DIR / "Custom_Braille_Embosser_V2_Tactile_Assembly_Map_MakerWorld.scad"

HIDDEN = "/* [Hidden] */\n"
# (the map file's text, the copy's text): each must stand in the map file exactly once.
EDITS = [
    ("// Custom Braille Embosser, Version 2: the tactile assembly map.\n",
     "// Custom Braille Embosser, Version 2: the tactile assembly map,\n"
     "// single-file copy for the MakerWorld customizer.\n"),
    ("// The outlines come from the part files themselves, cut by\n"
     "// scripts/derive_tactile_assembly_map.py into tactile_assembly_map_shapes.scad beside this\n"
     "// file. Never edit that file; rerun the script. The single-file copy for\n"
     "// MakerWorld beside this file is written from the two by\n"
     "// scripts/tactile_assembly_map_makerworld.py: rerun it after any change here.\n",
     "// MakerWorld's Parametric Model Maker takes one file and no local include,\n"
     "// so the outlines, cut from the part files themselves, are written into\n"
     "// this copy under [Hidden], and it opens on Plate 1. Never edit this copy:\n"
     "// scripts/tactile_assembly_map_makerworld.py writes it from\n"
     "// Custom_Braille_Embosser_V2_Tactile_Assembly_Map.scad and\n"
     "// tactile_assembly_map_shapes.scad; change those and rerun it.\n"),
    ("include <tactile_assembly_map_shapes.scad>\n\n", ""),
    ("plate = 0; // [0:All plates (preview),", "plate = 1; // [0:All plates (preview),"),
]


def swap(text: str, old: str, new: str) -> str:
    found = text.count(old)
    if found != 1:
        raise ValueError(f"the map file has {found} of {old.splitlines()[0]!r}; the copy needs exactly one")
    return text.replace(old, new)


def copy_text() -> str:
    text = MAP_SCAD.read_text(encoding="utf-8")
    for old, new in EDITS:
        text = swap(text, old, new)
    return swap(text, HIDDEN, HIDDEN + SHAPES_SCAD.read_text(encoding="utf-8"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 when the copy is stale")
    args = ap.parse_args(argv)
    text = copy_text()
    name = COPY.relative_to(ROOT).as_posix()
    if args.check:
        current = COPY.read_text(encoding="utf-8") if COPY.exists() else ""
        if current != text:
            print(f"{name} is stale; run python scripts/tactile_assembly_map_makerworld.py")
            return 1
        print(f"{name} is current")
        return 0
    COPY.write_text(text, encoding="utf-8", newline="\n")
    print(f"{name} written, {len(text) // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
