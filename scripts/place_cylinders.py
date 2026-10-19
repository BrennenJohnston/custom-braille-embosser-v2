#!/usr/bin/env python3
"""The example cylinders, placed in the assembly frame for the renders.

The assembled example STL carries an old cylinder sample. The real pair the
photographs show is the generated example pair in
``Build_Files/3D_Printing_Files/Embossing_Plates_Examples/``, exported by
the web app with the two cylinders side by side for printing. This script
splits that file, tells Cylinder A from Cylinder B by the arrow column
(raised on A, sunken on B), turns each so its arrow column faces the other
cylinder, and sets each down where it sits in the assembled embosser:
Cylinder A on the left (x = -30), Cylinder B at x = 0, the barrel from
z = -0.2 to 53.8 as the split assembly has it. The bodies are written to
``build/renders/bodies/cylinder-a.stl`` and ``cylinder-b.stl``, where the
render script expects them.

Usage:
    python scripts/place_cylinders.py            # the standard pair
    python scripts/place_cylinders.py --report   # only say which body is which

Local lane: needs trimesh and numpy. License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "Build_Files" / "3D_Printing_Files" / "Embossing_Plates_Examples"
PAIR = EXAMPLES / "Cylinder_Pair_V2_0.4_Washington.stl"
GEARED_PAIR = EXAMPLES / "Cylinder_Pair_Geared_V2_0.4_Washington.stl"
BODIES = ROOT / "build" / "renders" / "bodies"
BARREL_R = 15.4
RAISED_R = 15.65   # a raised dot or arrow stands at least 0.25 above the barrel
SUNK_R = 15.15     # a dimple or sunken arrow sits at least 0.25 below it
COLUMN_HALF_WIDTH_DEG = 12.0
# Where each cylinder sits in the assembly frame, from the split assembled example.
SEAT = {"a": (-30.0, 0.0), "b": (0.0, 0.0)}
BARREL_BOTTOM_Z = -0.2
ARROWS_FACE = {"a": 0.0, "b": 180.0}  # the angle the arrow column faces: toward the other cylinder


def analyse(body: trimesh.Trimesh) -> Dict[str, float]:
    """The facts that tell a cylinder's kind and pose. Two signs agree on
    the kind: the bump on the top face has three corners on Cylinder A
    (a triangle) and four on Cylinder B (a square), and the keyhole's mouth
    in the top face is square on A (14 + the 2 mm countersink each side)
    and 4 mm longer than wide on B (20 x 16 at the mouth)."""
    from scipy.spatial import ConvexHull

    lo, hi = body.bounds
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    v = body.vertices
    r = np.hypot(v[:, 0] - cx, v[:, 1] - cy)
    # The bump: the top-most half millimetre. Its direction is the angle of
    # its centre point (never a median of angles, which breaks at 180).
    top = v[v[:, 2] > hi[2] - 0.5]
    nub_centre = top[:, :2].mean(axis=0)
    nub_angle = float(np.degrees(np.arctan2(nub_centre[1] - cy, nub_centre[0] - cx)))
    nub_corners = int(len(ConvexHull(top[:, :2]).vertices))
    # The keyhole mouth: the top face's vertices inside the barrel, measured
    # along and across the bump's direction.
    face_z = hi[2] - 3.0  # the barrel's top face sits 3 mm under the bump's top
    mouth = v[(np.abs(v[:, 2] - face_z) < 0.15) & (r < 12.0)]
    u = np.array([math.cos(math.radians(nub_angle)), math.sin(math.radians(nub_angle))])
    along = (mouth[:, :2] - [cx, cy]) @ u
    across = (mouth[:, :2] - [cx, cy]) @ np.array([-u[1], u[0]])
    mouth_along = float(along.max() - along.min()) if len(mouth) else 0.0
    mouth_across = float(across.max() - across.min()) if len(mouth) else 0.0
    kind_by_nub = "a" if nub_corners == 3 else "b" if nub_corners == 4 else "?"
    kind_by_mouth = "a" if abs(mouth_along - mouth_across) < 1.5 else "b"
    return {"cx": cx, "cy": cy, "z0": lo[2], "z1": hi[2], "nub_angle": nub_angle, "nub_corners": nub_corners,
            "mouth_along": mouth_along, "mouth_across": mouth_across,
            "kind_by_nub": kind_by_nub, "kind_by_mouth": kind_by_mouth}


def identify(pair: Path = PAIR) -> Dict[str, Tuple[trimesh.Trimesh, Dict[str, float]]]:
    mesh = trimesh.load(pair, force="mesh")
    bodies = mesh.split(only_watertight=False)
    if len(bodies) != 2:
        raise ValueError(f"{pair.name} splits into {len(bodies)} bodies, not 2")
    found: Dict[str, Tuple[trimesh.Trimesh, Dict[str, float]]] = {}
    for body in bodies:
        facts = analyse(body)
        if facts["kind_by_nub"] != facts["kind_by_mouth"]:
            raise ValueError(f"a body of {pair.name} reads two ways: {facts}")
        kind = str(facts["kind_by_nub"])
        if kind in found:
            raise ValueError(f"both bodies of {pair.name} read as Cylinder {kind.upper()}: {facts}")
        found[kind] = (body, facts)
    if set(found) != {"a", "b"}:
        raise ValueError(f"{pair.name} does not hold one A and one B")
    return found


def place(pair: Path = PAIR, out_dir: Path = BODIES) -> Dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, Path] = {}
    for kind, (body, f) in identify(pair).items():
        turn = math.radians(ARROWS_FACE[kind] - f["nub_angle"])
        body.apply_transform(trimesh.transformations.rotation_matrix(turn, [0, 0, 1], [f["cx"], f["cy"], 0]))
        sx, sy = SEAT[kind]
        body.apply_translation([sx - f["cx"], sy - f["cy"], BARREL_BOTTOM_Z - f["z0"]])
        pid = f"cylinder-{kind}"
        out = out_dir / f"{pid}.stl"
        body.export(out)
        written[pid] = out
    return written


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pair", type=Path, default=PAIR, help="the pair STL (default the standard example pair)")
    ap.add_argument("--report", action="store_true", help="say which body is which and stop")
    args = ap.parse_args(argv)
    for kind, (_body, f) in sorted(identify(args.pair).items()):
        print(f"Cylinder {kind.upper()}: centre ({f['cx']:.1f}, {f['cy']:.1f}), z {f['z0']:.1f}..{f['z1']:.1f}, "
              f"bump at {f['nub_angle']:.1f} deg with {f['nub_corners']} corners, "
              f"keyhole mouth {f['mouth_along']:.1f} along x {f['mouth_across']:.1f} across")
    if args.report:
        return 0
    for kind, path in place(args.pair).items():
        m = trimesh.load(path, force="mesh")
        print(f"{path.relative_to(ROOT).as_posix()}: bounds {np.round(m.bounds, 1).tolist()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
