#!/usr/bin/env python3
"""The key to the tactile assembly map: which shape each number is.

Written from ``Build_Files/3D_Printing_Files/Tactile_Assembly_Map/tactile_assembly_map_shapes.json``
(the output of scripts/derive_tactile_assembly_map.py) and the plate layout in the
map's OpenSCAD file, to ``Documentation/Step_2_Guide_Option_4_Custom_Braille_Embosser_V2_Tactile_Assembly_Map_Key.md``:
how to read the map, then one row a number with the part and face, what is
raised and what is sunk, the real size, the part it mates with, and the
plate it is on. ``--check`` exits 1 when the page is not what the data
says (the test runs it).

Usage:
    python scripts/tactile_assembly_map_key.py           # write the page
    python scripts/tactile_assembly_map_key.py --check   # compare, exit 1 if stale

Stdlib only. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
SHAPES = ROOT / "Build_Files" / "3D_Printing_Files" / "Tactile_Assembly_Map" / "tactile_assembly_map_shapes.json"
MAP_SCAD = ROOT / "Build_Files" / "3D_Printing_Files" / "Tactile_Assembly_Map" / "Custom_Braille_Embosser_V2_Tactile_Assembly_Map.scad"
PAGE = ROOT / "Documentation" / "Step_2_Guide_Option_4_Custom_Braille_Embosser_V2_Tactile_Assembly_Map_Key.md"
PLATE_NAMES = {1: "Roller A", 2: "Roller B", 3: "Knob and Lid", 4: "Handle", 5: "Base from above", 6: "Base from below"}

HEAD = """# Tactile Assembly Map Key

What each numbered shape on the tactile assembly map is. The map is six flat printed plates, one line of shapes each, that carry the outline of every face where two parts of the Custom Braille Embosser, Version 2, meet, true to size; this page is the words that go with the numbers.

## 1. How to read the map

- Every shape is drawn as seen from above the embosser standing finished, so a peg's outline lies exactly over the hole it enters: find a peg on a gear shape, then the matching hole on the cylinder shape beside it.
- The plate is the table. A shape rises from it in equal steps, 0.75 mm each in the files here (the `level_step_mm` dial sets it, 0.5 to 1 mm). A part's face, its level 1, stands two steps above the plate; the thing standing on that face (a peg, a bump, a stud, a post, a wall) is one step more, and a thing sunk into the face (a keyhole, a dent, a notch, the Lid's hole) is one step less, whatever its real depth. No shape has more than four levels.
- Below each shape, toward the notched edge of the plate, is its number as a raised numeral 10 mm tall. The same number is cut as a row of notches in that edge, one notch a count, so you can count it with a fingernail.
- Above each shape, its number stands in braille on a small sloped block, the braille facing you: the number sign, then the digits. On a plate with two shapes, a raised line runs from the block down to the shape it names; the line is lower than any shape, so it never reads as part of one. The `braille_labels` dial takes the blocks and lines off for a reader who does not read braille; the numerals and notches stay.
- Hold a plate with the notched edge nearest you: the shapes are then the right way round. Numbers run in the order the steps of the Maker Guide use the parts.
- Cylinder A's shapes have a triangle, Cylinder B's a square, on the side that faces the other cylinder when the two are paired.

## 2. The numbers

"""

FOOT = """
## 3. Printing the map

Print `Build_Files/3D_Printing_Files/Tactile_Assembly_Map/Custom_Braille_Embosser_V2_Tactile_Assembly_Map.scad` from OpenSCAD, one plate at a time (set `plate` to 1 to 6 and export), or print the STL of each plate from its `STL/` folder; a sliced Bambu Lab X1C project with the plates is in `Build_Files/3D_Printing_Files/Print_Profiles/X1C/`. The plates are 1.2 mm thick and lie flat on the bed: 0.2 mm layers, any rigid filament, no supports; 0.1 mm layers over the braille blocks (a height-range modifier in the slicer) make the dots smoother. A light colour shows the shapes to a sighted helper too; nothing on the map depends on colour.

Every plate fits a 200 by 200 mm bed. The outlines come from the part files themselves, cut by `scripts/derive_tactile_assembly_map.py`, so a change to a part changes the map.

## 4. What the map is for

The map is a reading aid, not a tool: it does not measure, and nothing fits into it. It reads best with the parts in the other hand, each shape matched to the real face, and does its work before Step 1 of the assembly. The Assembly Guide By Touch says every step for the hands; the map is the picture of the parts it names.
"""


def load_faces() -> List[Dict]:
    """The faces on the map (the gears' hub sides are sketch-only faces for the Visual Assembly Guide)."""
    return [f for f in json.loads(SHAPES.read_text(encoding="utf-8"))["faces"] if f.get("map", True)]


def plates_from_scad() -> Dict[int, int]:
    """Face number -> plate number, read from the ``plates = [...]`` list in the map file."""
    text = MAP_SCAD.read_text(encoding="utf-8")
    m = re.search(r"^plates = \[(.*?)^\];", text, re.S | re.M)
    if not m:
        raise ValueError("no plates list in the map file")
    out: Dict[int, int] = {}
    for p, line in enumerate(l for l in m.group(1).splitlines() if l.strip().startswith("[")):
        for n in re.findall(r"\d+", line.split("//")[0]):
            out[int(n)] = p + 1
    return out


def levels_text(face: Dict) -> str:
    raised = [lv["name"] for lv in face["levels"]]
    return "; ".join(f"{i + 1}: {name}" for i, name in enumerate(raised))


def braille_number(n: int) -> str:
    """The number as braille: the number sign, then a letter a to j a digit (the map's own digit table)."""
    return "⠼" + "".join("⠚⠁⠃⠉⠙⠑⠋⠛⠓⠊"[int(d)] for d in str(n))


def table(faces: Sequence[Dict], plates: Dict[int, int]) -> str:
    rows = ["| Number | Braille | Part and face | Levels, lowest first | Size (mm) | Goes with | Plate |", "|---|---|---|---|---|---|---|"]
    for f in faces:
        w, h = f["size_mm"]
        rows.append(f"| {f['n']} | {braille_number(f['n'])} | {f['name']} | {levels_text(f)} | {w:g} by {h:g} | {f['mates']} | {plates[f['n']]}, {PLATE_NAMES[plates[f['n']]]} |")
    return "\n".join(rows)


def page_text() -> str:
    faces = load_faces()
    plates = plates_from_scad()
    missing = [f["n"] for f in faces if f["n"] not in plates]
    if missing:
        raise ValueError(f"faces on no plate: {missing}")
    return HEAD + table(faces, plates) + "\n" + FOOT


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 when the page is stale")
    args = ap.parse_args(argv)
    text = page_text()
    if args.check:
        current = PAGE.read_text(encoding="utf-8") if PAGE.exists() else ""
        if current != text:
            print(f"{PAGE.relative_to(ROOT).as_posix()} is stale; run python scripts/tactile_assembly_map_key.py")
            return 1
        print(f"{PAGE.relative_to(ROOT).as_posix()} is current")
        return 0
    PAGE.write_text(text, encoding="utf-8", newline="\n")
    print(f"{PAGE.relative_to(ROOT).as_posix()} written, {len(load_faces())} numbers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
