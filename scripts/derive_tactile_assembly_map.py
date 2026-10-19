#!/usr/bin/env python3
"""The tactile assembly map's shapes, taken from the part files themselves.

Every mating face of the embosser (decision D47) is drawn as a top-view
silhouette, true to size, as a set of LEVELS: each level is a region of the
plane that stands that many 0.5 mm steps above the map plate (D48). The
regions are horizontal sections of the real part meshes in the assembly
frame - the split assembled example and the example cylinders that
scripts/render_parts.py and scripts/place_cylinders.py put in
``build/renders/bodies/`` - so a peg's outline is the peg's, a keyhole's is
the keyhole's, and a peg drawn on the map lies exactly over the hole it
enters, because every shape is drawn as seen from above the assembled
embosser.

The output is ``Build_Files/3D_Printing_Files/Tactile_Assembly_Map/tactile_assembly_map_shapes.scad``:
one OpenSCAD list per face, ``[level, polygons]`` pairs where each polygon is
``[points, paths]`` (an outline with its holes), plus the face's size, its
number and its name; and ``tactile_assembly_map_shapes.json`` with the same data and
the SHA-256 of every mesh the shapes were cut from, for the test that pins
them. ``Custom_Braille_Embosser_V2_Tactile_Assembly_Map.scad`` lays the faces out on
plates and adds the numerals and edge notches (D49).

Usage:
    python scripts/derive_tactile_assembly_map.py            # write the shapes
    python scripts/derive_tactile_assembly_map.py --preview  # also a PNG of every face in build/tactile_assembly_map/

Local lane: needs trimesh, shapely and Pillow. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import trimesh
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.render_parts import BODIES, split_bodies  # noqa: E402

MAP_DIR = ROOT / "Build_Files" / "3D_Printing_Files" / "Tactile_Assembly_Map"
SHAPES_SCAD = MAP_DIR / "tactile_assembly_map_shapes.scad"
SHAPES_JSON = MAP_DIR / "tactile_assembly_map_shapes.json"
PREVIEW = ROOT / "build" / "tactile_assembly_map"
STEP_MM = 0.5          # one level, as the shapes file writes it; the map scales levels by its level_step_mm dial (D48, D75)
MAX_LEVELS = 4         # at most four height changes a shape (the owner's rule)
SIMPLIFY_MM = 0.02     # vertices closer than this to the line are dropped
MIN_AREA_MM2 = 0.5     # slivers below this (a seam line, a dot's dome, a hole between two outlines) are dropped

Region = MultiPolygon

# Where each face's shapes are cut. "outer" takes a section's outside
# boundary only; "holes" takes the holes of a section as a region; "polys"
# takes the section's whole polygons; a "near" point keeps only the polygon
# nearest it; a "radius" range keeps the holes whose centre lies at that
# distance from the face's axis. Levels are built from these as unions and
# differences, highest level last.
FACES: List[Dict] = [
    {"n": 1, "id": "cylinder-a-top", "part": "cylinder-a", "name": "Cylinder A, top end", "axis": (-30, 0),
     "step": 1, "mates": "Top Gear A",
     "levels": [
         ("barrel minus the keyhole", [("outer", 53.7), ("minus", ("holes", 50.0, {"radius": (0, 11)}))]),
         ("barrel minus the countersink mouth", [("outer", 53.7), ("minus", ("holes", 53.7, {"radius": (0, 12)}))]),
         ("the triangle bump", [("polys", 55.0)])]},
    {"n": 2, "id": "top-gear-a", "part": "top-gear-a", "name": "Top Gear A, peg side", "axis": (-30, 0),
     "step": 2, "mates": "Cylinder A, top end",
     "levels": [
         # Top Gear A's triangle notch opens into a tooth gap at the rim, so a
         # section shows it as a bite, not a hole; it is the bump's outline
         # grown by the 0.15 mm the gear was cut with.
         ("the toothed body minus its notch", [("outer", 58.0), ("minus", ("polys", 55.0, {"part": "cylinder-a", "buffer": 0.15}))]),
         ("the square peg", [("outer", 45.0)])]},
    {"n": 3, "id": "cylinder-a-bottom", "part": "cylinder-a", "name": "Cylinder A, bottom end", "axis": (-30, 0),
     "step": 3, "mates": "Bottom Gear A",
     "levels": [
         ("barrel minus the keyhole", [("outer", 0.5), ("minus", ("holes", 3.5, {"radius": (0, 11)}))]),
         ("barrel minus the countersink mouth and the dent", [("outer", 0.5), ("minus", ("holes", -0.1))])]},
    {"n": 4, "id": "bottom-gear-a", "part": "bottom-gear-a", "name": "Bottom Gear A, peg side", "axis": (-30, 0),
     "step": 3, "mates": "Cylinder A, bottom end",
     "levels": [
         ("the toothed body", [("outer", -5.0)]),
         ("the peg", [("polys", 10.0, {"near": (-30, 0)})]),
         ("the triangle stud", [("polys", 1.5, {"radius": (8, 15)})])]},
    {"n": 5, "id": "cylinder-b-top", "part": "cylinder-b", "name": "Cylinder B, top end", "axis": (0, 0),
     "step": 4, "mates": "Top Gear B",
     "levels": [
         ("barrel minus the keyhole", [("outer", 53.7), ("minus", ("holes", 50.0, {"radius": (0, 11)}))]),
         ("barrel minus the countersink mouth", [("outer", 53.7), ("minus", ("holes", 53.7, {"radius": (0, 12)}))]),
         ("the square bump", [("polys", 55.0)])]},
    {"n": 6, "id": "top-gear-b", "part": "top-gear-b", "name": "Top Gear B, peg side", "axis": (0, 0),
     "step": 5, "mates": "Cylinder B, top end",
     "levels": [
         ("the toothed body minus its notch", [("outer", 58.0), ("minus", ("holes", 55.0, {"radius": (8, 15)}))]),
         ("the peg", [("outer", 45.0)])]},
    {"n": 7, "id": "cylinder-b-bottom", "part": "cylinder-b", "name": "Cylinder B, bottom end", "axis": (0, 0),
     "step": 6, "mates": "Bottom Gear B",
     "levels": [
         ("barrel minus the keyhole", [("outer", 0.5), ("minus", ("holes", 3.5, {"radius": (0, 11)}))]),
         ("barrel minus the countersink mouth and the dent", [("outer", 0.5), ("minus", ("holes", -0.1))])]},
    {"n": 8, "id": "bottom-gear-b", "part": "bottom-gear-b", "name": "Bottom Gear B, peg side", "axis": (0, 0),
     "step": 6, "mates": "Cylinder B, bottom end",
     "levels": [
         ("the toothed body", [("outer", -5.0)]),
         ("the peg", [("polys", 10.0, {"near": (0, 0)})]),
         ("the square stud", [("polys", 1.5, {"radius": (8, 15)})])]},
    {"n": 9, "id": "knob-top", "part": "knob", "name": "Knob, from above", "axis": (-30, 0),
     "step": 9, "mates": "Top Gear A's pocket (the shaft) and the Handle's cup (the tab)",
     "levels": [
         ("the D-shaped collar", [("outer", 70.0)]),
         ("the head and its tab", [("outer", 79.0)])]},
    {"n": 10, "id": "lid-underside", "part": "lid", "name": "Lid, from above, the post shown through it", "axis": (-15, 0),
     "step": 10, "mates": "the Base's rim; its post into Top Gear B; the Knob through its hole",
     "levels": [
         ("the plate minus the Knob hole", [("outer", 66.0), ("minus", ("holes", 66.0, {"radius": (10, 20), "about": (-15, 0)}))]),
         ("the post", [("polys", 58.0, {"near": (0, 0)})])]},
    {"n": 11, "id": "handle-cup", "part": "handle", "name": "Handle, from above, the cup's keyhole shown through it", "axis": (-30, 0),
     "step": 11, "mates": "the Knob",
     "levels": [
         ("the grip and the cup minus the keyhole", [("outer", 110.0), ("minus", ("holes", 72.0))])]},
    {"n": 12, "id": "base-top", "part": "base", "name": "Base, from above", "axis": (-15, 0),
     "step": 8, "mates": "the roller pair; the Lid",
     "levels": [
         ("the foot", [("outer", -25.0)]),
         # The floor inside the towers (the hollow above it at z -9) with the
         # slot and the two round holes sunk through it, plus the tower walls.
         ("the floor minus its three openings, and the tower walls",
          [("holes", -9.0, {"min_area": 100}), ("minus", ("holes", -11.0, {"min_area": 5})), ("plus", ("polys", 20.0))]),
         ("the tower walls and the two posts", [("polys", 20.0), ("plus", ("polys", -5.0, {"min_area": 30, "radius": (0, 9), "about": (-30, 0)})),
                                                ("plus", ("polys", -5.0, {"min_area": 30, "radius": (0, 9), "about": (0, 0)}))])]},
    {"n": 13, "id": "base-underside", "part": "base", "name": "Base, from below", "axis": (-15, 0),
     "step": 8, "mates": "the Push-out Plate's pegs",
     "levels": [
         # The recessed floor with the slot and two round holes the Push-out Plate's pegs rise through.
         ("the foot minus the three openings", [("outer", -25.0), ("minus", ("holes", -11.0, {"min_area": 5}))]),
         ("the rim the Base stands on", [("polys", -30.0)])]},
    # The gears' hub sides are not on the map (D47 chose the peg sides) but
    # the Visual Assembly Guide draws them: the keyed pocket with its four
    # notches (Top Gear A), the small pocket with its cross of grooves (Top
    # Gear B), the wide and the plain round pockets (the bottom gears), and
    # the small triangle every hub face carries on the arrow side.
    {"n": 14, "id": "top-gear-a-hub", "part": "top-gear-a", "name": "Top Gear A, hub side", "axis": (-30, 0), "map": False,
     "step": 9, "mates": "the Knob's shaft",
     "levels": [("the body minus the keyed pocket, its four notches and the triangle mark", [("outer", 60.0), ("minus", ("holes", 63.5))])]},
    {"n": 15, "id": "top-gear-b-hub", "part": "top-gear-b", "name": "Top Gear B, hub side", "axis": (0, 0), "map": False,
     "step": 10, "mates": "the Lid's post",
     "levels": [("the body minus the small pocket, its cross of grooves and the triangle mark", [("outer", 60.0), ("minus", ("holes", 63.5))])]},
    {"n": 16, "id": "bottom-gear-a-hub", "part": "bottom-gear-a", "name": "Bottom Gear A, hub side", "axis": (-30, 0), "map": False,
     "step": 8, "mates": "the Base's fatter post",
     "levels": [("the body minus the wide pocket and the triangle mark", [("outer", -5.0), ("minus", ("holes", -9.9))])]},
    {"n": 17, "id": "bottom-gear-b-hub", "part": "bottom-gear-b", "name": "Bottom Gear B, hub side", "axis": (0, 0), "map": False,
     "step": 8, "mates": "the Base's thinner post",
     "levels": [("the body minus the small pocket and the triangle mark", [("outer", -5.0), ("minus", ("holes", -9.9))])]},
]

# How the Visual Assembly Guide draws each face as a line sketch: which
# levels are drawn as an outline (a face, with its holes and cuts as inner
# outlines) and which are filled black (what stands up from the face).
SKETCH: Dict[str, Dict[str, List[int]]] = {
    "cylinder-a-top": {"outline": [1], "fill": [3]}, "cylinder-b-top": {"outline": [1], "fill": [3]},
    "cylinder-a-bottom": {"outline": [1], "fill": []}, "cylinder-b-bottom": {"outline": [1], "fill": []},
    "top-gear-a": {"outline": [1], "fill": [2]}, "top-gear-b": {"outline": [1], "fill": [2]},
    "bottom-gear-a": {"outline": [1], "fill": [2, 3]}, "bottom-gear-b": {"outline": [1], "fill": [2, 3]},
    "knob-top": {"outline": [1], "fill": [2]}, "lid-underside": {"outline": [1], "fill": [2]},
    "handle-cup": {"outline": [1], "fill": []},
    "base-top": {"outline": [1, 2], "fill": [3]}, "base-underside": {"outline": [1, 2], "fill": []},
    "top-gear-a-hub": {"outline": [1], "fill": []}, "top-gear-b-hub": {"outline": [1], "fill": []},
    "bottom-gear-a-hub": {"outline": [1], "fill": []}, "bottom-gear-b-hub": {"outline": [1], "fill": []},
}


def _section(mesh: trimesh.Trimesh, z: float) -> List[Polygon]:
    """The mesh's horizontal section at z as polygons in the assembly's own
    x and y (the identity projection keeps them)."""
    s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        raise ValueError(f"no section at z={z}")
    planar, _ = s.to_2D(to_2D=np.eye(4))
    polys = [p for p in planar.polygons_full if p.area >= MIN_AREA_MM2]
    if not polys:
        raise ValueError(f"an empty section at z={z}")
    return polys


def _pick(polys: Sequence[Polygon], opts: Dict, about: Tuple[float, float]) -> List[Polygon]:
    if "min_area" in opts:
        polys = [p for p in polys if p.area >= opts["min_area"]]
    if "near" in opts:
        x, y = opts["near"]
        polys = [min(polys, key=lambda p: math.hypot(p.centroid.x - x, p.centroid.y - y))]
    if "radius" in opts:
        lo, hi = opts["radius"]
        cx, cy = opts.get("about", about)
        polys = [p for p in polys if lo <= math.hypot(p.centroid.x - cx, p.centroid.y - cy) <= hi]
    return list(polys)


_MESHES: Dict[str, trimesh.Trimesh] = {}


def mesh_of(part: str) -> trimesh.Trimesh:
    if part not in _MESHES:
        _MESHES[part] = trimesh.load(BODIES / f"{part}.stl", force="mesh")
    return _MESHES[part]


def _region(mesh: trimesh.Trimesh, spec: Tuple, about: Tuple[float, float]) -> Region:
    kind, z = spec[0], spec[1]
    opts = spec[2] if len(spec) > 2 else {}
    polys = _section(mesh_of(opts["part"]) if "part" in opts else mesh, z)
    if kind == "outer":
        shapes = [Polygon(p.exterior) for p in _pick(polys, opts, about)]
    elif kind == "polys":
        shapes = _pick(polys, opts, about)
    elif kind == "holes":
        holes = [Polygon(h) for p in polys for h in p.interiors if Polygon(h).area >= MIN_AREA_MM2]
        shapes = _pick(holes, opts, about)
    else:
        raise ValueError(kind)
    region = unary_union(shapes)
    if "buffer" in opts:
        region = region.buffer(opts["buffer"], join_style="mitre")
    return _multi(region)


def _multi(g) -> Region:
    if g.is_empty:
        return MultiPolygon()
    if isinstance(g, Polygon):
        return MultiPolygon([g])
    if isinstance(g, MultiPolygon):
        return g
    return MultiPolygon([p for p in g.geoms if isinstance(p, Polygon)])


def _without_sliver_holes(region: Region) -> Region:
    """The region with every hole below MIN_AREA_MM2 filled. Where two
    sections share a boundary (the Base's floor and its tower walls) their
    union leaves holes a thousandth of a millimetre wide that touch corner
    to corner, and a plate extruded from them is not watertight."""
    return MultiPolygon([Polygon(p.exterior, [h for h in p.interiors if Polygon(h).area >= MIN_AREA_MM2])
                         for p in region.geoms])


def level_region(mesh: trimesh.Trimesh, ops: Sequence, about: Tuple[float, float]) -> Region:
    region = _region(mesh, ops[0], about)
    for op in ops[1:]:
        verb, spec = op
        other = _region(mesh, spec, about)
        region = _multi(region.difference(other) if verb == "minus" else region.union(other))
    return region


def face_levels(face: Dict, bodies: Dict[str, Path]) -> List[Tuple[str, Region]]:
    mesh = trimesh.load(bodies[face["part"]], force="mesh")
    out = []
    for name, ops in face["levels"]:
        region = level_region(mesh, ops, face["axis"])
        region = _without_sliver_holes(_multi(region.simplify(SIMPLIFY_MM, preserve_topology=True)))
        if region.is_empty:
            raise ValueError(f"face {face['n']} level '{name}' is empty")
        out.append((name, region))
    if len(out) > MAX_LEVELS:
        raise ValueError(f"face {face['n']} has {len(out)} levels, more than {MAX_LEVELS}")
    return out


def polygon_lists(region: Region) -> List[Tuple[List[List[float]], List[List[int]]]]:
    """Each polygon as (points, paths): the outline, then its holes."""
    out = []
    for poly in region.geoms:
        points: List[List[float]] = []
        paths: List[List[int]] = []
        for ring in [poly.exterior, *poly.interiors]:
            coords = list(ring.coords)[:-1]
            paths.append(list(range(len(points), len(points) + len(coords))))
            points += [[round(x, 3), round(y, 3)] for x, y in coords]
        out.append((points, paths))
    return out


def derive(bodies: Dict[str, Path]) -> List[Dict]:
    faces = []
    for face in FACES:
        levels = face_levels(face, bodies)
        bounds = unary_union([r for _, r in levels]).bounds
        cx, cy = face["axis"]
        faces.append({"n": face["n"], "id": face["id"], "part": face["part"], "name": face["name"], "step": face["step"],
                      "mates": face["mates"], "axis": list(face["axis"]), "map": face.get("map", True), "sketch": SKETCH[face["id"]],
                      "size_mm": [round(bounds[2] - bounds[0], 2), round(bounds[3] - bounds[1], 2)],
                      "offset": [round(-(bounds[0] + bounds[2]) / 2, 3), round(-(bounds[1] + bounds[3]) / 2, 3)],
                      "levels": [{"name": name, "height_mm": (i + 1) * STEP_MM, "polygons": polygon_lists(region)}
                                 for i, (name, region) in enumerate(levels)]})
    return faces


def scad_text(faces: Sequence[Dict]) -> str:
    lines = ["// Generated by scripts/derive_tactile_assembly_map.py from the part files. Do not edit; rerun the script.",
             f"TACTILE_STEP_MM = {STEP_MM};",
             "// faces: [number, name, size [w, h], offset to centre, [[height, [[points, paths], ...]], ...]]",
             "tactile_faces = ["]
    for f in faces:
        if not f["map"]:
            continue
        lvls = []
        for lv in f["levels"]:
            polys = ", ".join(f"[{json.dumps(pts, separators=(',', ':'))}, {json.dumps(paths, separators=(',', ':'))}]" for pts, paths in lv["polygons"])
            lvls.append(f"    [{lv['height_mm']}, [{polys}]]")
        lines.append(f'  [{f["n"]}, "{f["name"]}", {json.dumps(f["size_mm"])}, {json.dumps(f["offset"])}, [\n' + ",\n".join(lvls) + "\n  ]],")
    lines.append("];")
    return "\n".join(lines) + "\n"


def preview(faces: Sequence[Dict]) -> List[Path]:
    from PIL import Image, ImageDraw

    PREVIEW.mkdir(parents=True, exist_ok=True)
    scale = 8  # pixels per mm
    shades = [(200, 200, 200), (150, 150, 150), (100, 100, 100), (40, 40, 40)]
    out = []
    for f in faces:
        w, h = f["size_mm"]
        size = (int(w * scale) + 40, int(h * scale) + 40)
        im = Image.new("RGB", size, (255, 255, 255))
        ox, oy = f["offset"]
        for i, lv in enumerate(f["levels"]):
            # Each level through its own mask, holes cut out, so a deeper
            # hole under a higher level is never painted over.
            mask = Image.new("L", size, 0)
            md = ImageDraw.Draw(mask)
            for pts, paths in lv["polygons"]:
                rings = [[((x + ox + w / 2) * scale + 20, (h / 2 - (y + oy)) * scale + 20) for x, y in (pts[k] for k in path)] for path in paths]
                md.polygon(rings[0], fill=255)
                for hole in rings[1:]:
                    md.polygon(hole, fill=0)
            im.paste(shades[i], mask=mask)
        ImageDraw.Draw(im).text((4, 4), f"{f['n']} {f['name']} {w} x {h} mm", fill=(200, 0, 0))
        p = PREVIEW / f"face-{f['n']:02}.png"
        im.save(p)
        out.append(p)
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--preview", action="store_true", help="also draw every face to build/tactile_assembly_map/")
    args = ap.parse_args(argv)
    bodies = split_bodies()
    faces = derive(bodies)
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    SHAPES_SCAD.write_text(scad_text(faces), encoding="utf-8", newline="\n")
    sources = {pid: hashlib.sha256(path.read_bytes()).hexdigest() for pid, path in sorted(bodies.items())
               if pid in {f["part"] for f in FACES}}
    SHAPES_JSON.write_text(json.dumps({"step_mm": STEP_MM, "sources_sha256": sources, "faces": faces}, indent=1) + "\n",
                           encoding="utf-8", newline="\n")
    for f in faces:
        print(f"{f['n']:2} {f['name']:<58} {f['size_mm'][0]:6.1f} x {f['size_mm'][1]:5.1f} mm, {len(f['levels'])} levels"
              + ("" if f["map"] else " (sketch only)"))
    if args.preview:
        for p in preview(faces):
            print(p.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
