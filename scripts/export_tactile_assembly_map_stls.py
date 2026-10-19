#!/usr/bin/env python3
"""Export the tactile assembly map's six plates to STL with OpenSCAD, and check each one.

One binary STL a plate, named by its number and what it carries, into
``Build_Files/3D_Printing_Files/Tactile_Assembly_Map/STL/``: the map at its
standard settings, ready to slice. The export runs with ``--hardwarnings``
and the parameter-range check, the way the project's OpenSCAD rule asks, and
refuses if OpenSCAD prints a WARNING or ERROR or writes no file. Each plate
is then read back and refused unless all of this holds:

* every edge is shared by exactly two faces (watertight), and the plate is
  one body;
* it lies flat on z = 0 and its footprint is the size the map file reports;
* its highest point is where the map file reports it (its deepest shape, or
  a braille label's wedge);
* the MakerWorld copy of the map (scripts/tactile_assembly_map_makerworld.py)
  exports the same solid: the same bounds, volume and surface. Neither the
  bytes nor the corners are compared, because OpenSCAD may split a flat face
  into triangles differently from one run to the next, adding points of its
  own inside it.

Usage:
    python scripts/export_tactile_assembly_map_stls.py          # all six
    python scripts/export_tactile_assembly_map_stls.py --plate 2

Local lane: needs trimesh and the OpenSCAD 2026.01.03 nightly. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence

import trimesh

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.render_parts import find_openscad  # noqa: E402
from scripts.tactile_assembly_map_makerworld import COPY, copy_text  # noqa: E402

MAP_DIR = ROOT / "Build_Files" / "3D_Printing_Files" / "Tactile_Assembly_Map"
SCAD = MAP_DIR / "Custom_Braille_Embosser_V2_Tactile_Assembly_Map.scad"
STL_DIR = MAP_DIR / "STL"
CHECK_DIR = ROOT / "build" / "tactile_assembly_map"
PLATES = {1: "Roller_A", 2: "Roller_B", 3: "Knob_Lid", 4: "Handle", 5: "Base_Above", 6: "Base_Below"}
SIZE_TOLERANCE_MM = 0.01
_ECHO_SIZE = re.compile(r": ([\d.]+) x ([\d.]+) x ([\d.]+) mm")
_ECHO_TOP = re.compile(r"; top ([\d.]+) mm")


def openscad_export(scad: Path, plate: int, out: Path) -> str:
    """One plate to a binary STL; the ECHO line with the plate's size."""
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    cmd = [str(find_openscad()), "--hardwarnings", "--check-parameter-ranges=true", "--export-format", "binstl",
           "-D", f"plate={plate}", "-o", str(out), str(scad)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    log = result.stdout + result.stderr
    bad = [line for line in log.splitlines() if line.startswith("WARNING:") or line.startswith("ERROR:")]
    if bad or not out.exists():
        raise RuntimeError(f"plate {plate} of {scad.name} did not export cleanly:\n" + "\n".join(bad or log.splitlines()[-10:]))
    return next((line for line in log.splitlines() if line.startswith("ECHO:")), "")


def problems(stl: Path, echo: str) -> List[str]:
    """What is wrong with an exported plate, as sentences; empty when it is sound."""
    m = _ECHO_SIZE.search(echo)
    top = _ECHO_TOP.search(echo)
    if not m or not top:
        return [f"the map file reported no size or top: {echo!r}"]
    w, h, _thickness = (float(v) for v in m.groups())
    top_mm = float(top.group(1))
    mesh = trimesh.load(stl, force="mesh")
    (x0, y0, z0), (x1, y1, z1) = mesh.bounds
    out = []
    if not mesh.is_watertight:
        out.append("not watertight: an edge is not shared by exactly two faces")
    bodies = len(mesh.split(only_watertight=False))
    if bodies != 1:
        out.append(f"{bodies} bodies, not one")
    if abs(z0) > 1e-6:
        out.append(f"its underside is at z = {z0:g}, not on the bed")
    if abs((x1 - x0) - w) > SIZE_TOLERANCE_MM or abs((y1 - y0) - h) > SIZE_TOLERANCE_MM:
        out.append(f"footprint {x1 - x0:.2f} x {y1 - y0:.2f} mm, where the map file reports {w} x {h} mm")
    if abs(z1 - top_mm) > SIZE_TOLERANCE_MM:
        out.append(f"its top is at z = {z1:.3f} mm, where the map file reports {top_mm} mm")
    return out


def same_solid(a: Path, b: Path) -> bool:
    """The same bounds, volume and surface. Two runs of one plate differ in the
    interior points OpenSCAD adds when it triangulates the flat underside and
    by about 1e-9 in volume; one missing braille dot would move the volume by
    about 2e-5, so 1e-7 tells the two apart."""
    ma, mb = trimesh.load(a, force="mesh"), trimesh.load(b, force="mesh")
    return (bool((abs(ma.bounds - mb.bounds) < SIZE_TOLERANCE_MM).all())
            and math.isclose(ma.volume, mb.volume, rel_tol=1e-7)
            and math.isclose(ma.area, mb.area, rel_tol=1e-7))


def export(plate: int) -> Path:
    out = STL_DIR / f"Tactile_Assembly_Map_Plate_{plate}_{PLATES[plate]}.stl"
    echo = openscad_export(SCAD, plate, out)
    found = problems(out, echo)
    if COPY.read_text(encoding="utf-8") != copy_text():
        found.append(f"{COPY.name} is stale; run python scripts/tactile_assembly_map_makerworld.py")
    else:
        from_copy = CHECK_DIR / f"makerworld_plate_{plate}.stl"
        openscad_export(COPY, plate, from_copy)
        if not same_solid(out, from_copy):
            found.append(f"{COPY.name} exports a different plate {plate}")
    if found:
        raise RuntimeError(f"{out.name} is not fit to ship:\n  " + "\n  ".join(found))
    mesh = trimesh.load(out, force="mesh")
    x, y, z = mesh.extents
    print(f"{out.relative_to(ROOT).as_posix()}  {out.stat().st_size // 1024} KB, {len(mesh.faces)} triangles, "
          f"{x:.2f} x {y:.2f} x {z:.2f} mm: watertight, one body, flat on the bed, same from the MakerWorld copy")
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plate", type=int, choices=sorted(PLATES), help="one plate (default: all six)")
    args = ap.parse_args(argv)
    for plate in ([args.plate] if args.plate else sorted(PLATES)):
        export(plate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
