#!/usr/bin/env python3
"""Render the computer pictures of the parts: the backup for any step a
photo does not yet cover, and the one sure picture of each gear.

Three kinds of picture, all PNG under ``Photos/renders/``:

* ``render-part-<id>``: one printed part alone, from its STL in
  ``Build_Files/3D_Printing_Files/STL/``, centred and filling the frame.
  These are the only pictures whose part identity is certain for the four
  gears, because each comes from a named file.
* ``render-stage-<name>``: a named set of parts in their assembled
  positions, from the assembled example STL split into bodies, seen from
  ONE fixed camera that never moves between stages, so a reader can compare
  stage with stage.
* ``render-exploded``: every part in assembly position but lifted apart
  along the axis the parts go together on, from the same fixed camera.

The assembled example is split into its ten bodies with trimesh and each
body is labelled by its volume against ``Documentation/parts.json`` (within
one per cent), then written to ``build/renders/bodies/<id>.stl``. A short
OpenSCAD file per picture imports the bodies it needs, each in the colour
that part has in the photographs (decorative only: the guide identifies
parts by shape, never by colour), and OpenSCAD renders the preview to PNG.

Usage:
    python scripts/render_parts.py                       # every picture
    python scripts/render_parts.py --only render-exploded --only render-part-base
    python scripts/render_parts.py --list

Local lane: needs trimesh and the OpenSCAD 2026.01.03 nightly (never run with
``python -I``). License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import trimesh

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OPENSCAD = Path(r"C:\Program Files\OpenSCAD (Nightly)\openscad.com")
STL = ROOT / "Build_Files" / "3D_Printing_Files" / "STL"
ASSEMBLED = ROOT / "Build_Files" / "3D_Printing_Files" / "Assembly_Reference" / "Braille_Embosser_V2_Assembled_Example.stl"
PARTS = ROOT / "Documentation" / "parts.json"
MANIFEST = ROOT / "Documentation" / "images.json"
OUT = ROOT / "Photos" / "renders"
BUILD = ROOT / "build" / "renders"
BODIES = BUILD / "bodies"
VOLUME_TOLERANCE = 0.03
IMGSIZE = "1600,1200"
COLORSCHEME = "Tomorrow"  # white background, prints cleanly

# The colours the parts have in the photographs. Decorative only.
PART_COLOURS = {
    "base": "#9e9e9e", "lid": "#2ec4d6", "knob": "#ffc400", "handle": "#ffc400",
    "top-gear-a": "#ff4fa3", "bottom-gear-a": "#ff4fa3", "top-gear-b": "#ff4fa3", "bottom-gear-b": "#ff4fa3",
    "cylinder-a": "#e8e8e8", "cylinder-b": "#e8e8e8", "push-out-plate": "#e8e8e8",
}
# How far up the assembly axis each part lifts in the exploded view, in
# steps of EXPLODE_MM: the Base stays, then the parts in the order they go on.
STACK = {"base": 0, "bottom-gear-a": 1, "bottom-gear-b": 1, "cylinder-a": 2, "cylinder-b": 2,
         "top-gear-a": 3, "top-gear-b": 3, "lid": 4, "knob": 5, "handle": 6}
EXPLODE_MM = 20.0

# One camera for every stage and the exploded view: eye at the centre of the
# two columns, looking down at 60 degrees from the left front. The distance
# is the only number that changes, so the parts keep their size on the page
# between the stages and grow only in the taller exploded view.
STAGE_CAMERA = "-15,0,45,60,0,35,440"
EXPLODED_CAMERA = "-15,0,105,60,0,35,820"
PART_CAMERA = "0,0,0,60,0,35,0"  # with --autocenter --viewall: each part fills its frame

# Single parts seen from a chosen side, for the faces no photograph shows.
# The camera's last-but-one number turns round the part: 0 is the front
# (the window), 90 the right-hand side, 180 the back, 270 the left.
VIEWS: Dict[str, Dict] = {
    "render-base-back": {"ids": ["base"], "camera": "-15,0,45,75,0,180,260",
                         "shows": "the Base from behind: the slit down the back wall and, on its right-hand side, the large arrow pointing up"},
    "render-base-right-side": {"ids": ["base"], "camera": "-15,0,45,75,0,90,260",
                               "shows": "the Base's right-hand side: the long arrow pointing round to the window and the large arrow pointing up beside the slit"},
}

# The pictures-without-words page: one panel per assembly stage, each
# labelled with the step it shows, drawn from the same direction and each
# fitted to its own frame. The page is a supplement to the guide's words,
# never a replacement: the guide's caption under it lists the steps.
PICTOGRAM_PANELS: List[Tuple[str, List[str]]] = [
    ("1", ["cylinder-a"]),
    ("2", ["cylinder-a", "top-gear-a"]),
    ("3", ["cylinder-a", "top-gear-a", "bottom-gear-a"]),
    ("4-6", ["cylinder-b", "top-gear-b", "bottom-gear-b"]),
    ("7", ["cylinder-a", "cylinder-b", "bottom-gear-a", "bottom-gear-b", "top-gear-a", "top-gear-b"]),
    ("8", ["base", "cylinder-a", "cylinder-b", "bottom-gear-a", "bottom-gear-b", "top-gear-a", "top-gear-b"]),
    ("9", ["base", "cylinder-a", "cylinder-b", "bottom-gear-a", "bottom-gear-b", "top-gear-a", "top-gear-b", "knob"]),
    ("10", ["base", "cylinder-a", "cylinder-b", "bottom-gear-a", "bottom-gear-b", "top-gear-a", "top-gear-b", "knob", "lid"]),
    ("11", ["base", "cylinder-a", "cylinder-b", "bottom-gear-a", "bottom-gear-b", "top-gear-a", "top-gear-b", "knob", "lid", "handle"]),
]
PICTOGRAM_NAME = "render-pictogram-page"
PICTOGRAM_COLUMNS = 3
PANEL_W, PANEL_H = 520, 390
PANEL_GAP = 40
PANEL_MARGIN = 40
PICTOGRAM_SHOWS = ("the assembly as nine numbered pictures without words, left to right and top to bottom: "
                   "Cylinder A alone; its top gear on; its bottom gear on; Roller B built; the two rollers paired; "
                   "the pair in the Base; the Knob on; the Lid on; the Handle on")

ROLLERS = ["cylinder-a", "cylinder-b", "bottom-gear-a", "bottom-gear-b", "top-gear-a", "top-gear-b"]
STAGES: Dict[str, List[str]] = {
    "rollers": ROLLERS,
    "rollers-in-base": ["base"] + ROLLERS,
    "knob-on": ["base"] + ROLLERS + ["knob"],
    "lid-on": ["base"] + ROLLERS + ["knob", "lid"],
    "complete": ["base"] + ROLLERS + ["knob", "lid", "handle"],
}


def find_openscad() -> Path:
    if OPENSCAD.exists():
        return OPENSCAD
    raise FileNotFoundError(f"OpenSCAD not found at {OPENSCAD}; install the 2026.01.03 nightly")


def load_parts() -> List[Dict]:
    return json.loads(PARTS.read_text(encoding="utf-8"))


def split_bodies() -> Dict[str, Path]:
    """The assembled example as one STL per part under build/renders/bodies/,
    each named by the part whose volume it matches."""
    parts = load_parts()
    mesh = trimesh.load(ASSEMBLED, force="mesh")
    bodies = mesh.split(only_watertight=False)
    BODIES.mkdir(parents=True, exist_ok=True)
    out: Dict[str, Path] = {}
    for body in bodies:
        # Nearest volume wins, within the tolerance: the example's Lid is the
        # later v9.2 lid, 1.1 % larger than the released Lid.stl, and its
        # cylinders are an older sample, so an exact match is not expected.
        nearest = min(parts, key=lambda p: abs(body.volume - p["volume_mm3"]) / p["volume_mm3"])
        error = abs(body.volume - nearest["volume_mm3"]) / nearest["volume_mm3"]
        if error > VOLUME_TOLERANCE:
            raise ValueError(f"a body of {body.volume:.0f} mm3 is {error:.1%} from the nearest part, {nearest['id']}")
        pid = nearest["id"]
        if pid in out:
            raise ValueError(f"two bodies of the assembled example both match {pid}")
        path = BODIES / f"{pid}.stl"
        if not pid.startswith("cylinder-"):
            # The example's cylinders are an old sample; the real pair is placed below.
            body.export(path)
        out[pid] = path
    # The cylinders the photographs show, from the example pair, turned and
    # seated by scripts/place_cylinders.py (decision D45).
    from scripts.place_cylinders import place
    out.update(place(out_dir=BODIES))
    missing = [p["id"] for p in parts if p["id"] not in out and not p.get("optional")]
    if missing:
        raise ValueError(f"the assembled example has no body for {missing}")
    return out


def _scad_path(path: Path) -> str:
    return path.resolve().as_posix()


def scad_text(bodies: Dict[str, Path], ids: Sequence[str], explode_mm: float = 0.0) -> str:
    lines = []
    for pid in ids:
        lift = explode_mm * STACK[pid] if explode_mm else 0.0
        lines.append(f'translate([0, 0, {lift:g}]) color("{PART_COLOURS[pid]}") import("{_scad_path(bodies[pid])}");')
    return "\n".join(lines) + "\n"


def part_scad_text(pid: str, file: str) -> str:
    return f'color("{PART_COLOURS[pid]}") import("{_scad_path(STL / file)}");\n'


def render(name: str, scad: str, camera: str, fit: bool, out_dir: Path = OUT) -> Path:
    BUILD.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    scad_file = BUILD / f"{name}.scad"
    scad_file.write_text(scad, encoding="utf-8", newline="\n")
    out = out_dir / f"{name}.png"
    cmd = [str(find_openscad()), f"--imgsize={IMGSIZE}", "--projection=o", f"--colorscheme={COLORSCHEME}"]
    if camera:
        cmd.append(f"--camera={camera}")   # otherwise the file's own $vpt, $vpr and $vpd frame it
    if fit:
        cmd += ["--autocenter", "--viewall"]
    cmd += ["-o", str(out), str(scad_file)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0 or not out.exists():
        raise RuntimeError(f"render failed for {name} (rc={result.returncode}):\n{result.stderr[-800:]}")
    return out


def pictogram_page(bodies: Dict[str, Path]) -> Path:
    """Render each panel to build/renders/pictogram/, then lay them out in a
    grid with a numbered badge on each and an arrow between neighbours."""
    from PIL import Image, ImageDraw
    from scripts.photo_contact_sheets import _font

    panel_dir = BUILD / "pictogram"
    rows = (len(PICTOGRAM_PANELS) + PICTOGRAM_COLUMNS - 1) // PICTOGRAM_COLUMNS
    page = Image.new("RGB", (PANEL_MARGIN * 2 + PICTOGRAM_COLUMNS * PANEL_W + (PICTOGRAM_COLUMNS - 1) * PANEL_GAP,
                             PANEL_MARGIN * 2 + rows * PANEL_H + (rows - 1) * PANEL_GAP), "white")
    draw = ImageDraw.Draw(page)
    badge_font = _font(44)
    arrow_font = _font(60)
    for k, (label, ids) in enumerate(PICTOGRAM_PANELS):
        png = render(f"pictogram-{k + 1}", scad_text(bodies, ids), PART_CAMERA, fit=True, out_dir=panel_dir)
        with Image.open(png) as im:
            im = im.convert("RGB")
            im.thumbnail((PANEL_W - 2 * 8, PANEL_H - 2 * 8), Image.LANCZOS)
            col, row = k % PICTOGRAM_COLUMNS, k // PICTOGRAM_COLUMNS
            x0 = PANEL_MARGIN + col * (PANEL_W + PANEL_GAP)
            y0 = PANEL_MARGIN + row * (PANEL_H + PANEL_GAP)
            draw.rectangle([x0, y0, x0 + PANEL_W, y0 + PANEL_H], outline="#444444", width=3)
            page.paste(im, (x0 + (PANEL_W - im.width) // 2, y0 + (PANEL_H - im.height) // 2))
        # The badge: a dark circle with the step number, top left of the panel.
        r = 34
        cx, cy = x0 + 8 + r, y0 + 8 + r
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#111111")
        tw = draw.textlength(label, font=badge_font)
        draw.text((cx - tw / 2, cy - 26), label, fill="white", font=badge_font)
        if col < PICTOGRAM_COLUMNS - 1 and k + 1 < len(PICTOGRAM_PANELS):
            ax = x0 + PANEL_W + PANEL_GAP / 2 - draw.textlength("→", font=arrow_font) / 2
            draw.text((ax, y0 + PANEL_H / 2 - 40), "→", fill="#111111", font=arrow_font)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{PICTOGRAM_NAME}.png"
    page.save(out, "PNG", optimize=True)
    return out


def pictures() -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    names = {p["id"]: p["name"] for p in load_parts()}
    for p in load_parts():
        if p["file"]:
            out[f"render-part-{p['id']}"] = {"kind": "part", "id": p["id"], "file": p["file"], "ids": [p["id"]],
                                             "shows": f"the {p['name']} alone, drawn from its file"}
    for name, ids in STAGES.items():
        out[f"render-stage-{name}"] = {"kind": "stage", "ids": ids,
                                       "shows": "in their assembled positions: " + ", ".join(names[i] for i in ids)}
    out["render-exploded"] = {"kind": "exploded", "ids": list(STACK),
                              "shows": "every part lifted apart along the axis the parts go together on, the Base at the bottom"}
    for name, view in VIEWS.items():
        out[name] = {"kind": "view", "ids": view["ids"], "camera": view["camera"], "shows": view["shows"]}
    out[PICTOGRAM_NAME] = {"kind": "pictogram", "ids": sorted({i for _, ids in PICTOGRAM_PANELS for i in ids}),
                           "shows": PICTOGRAM_SHOWS}
    return out


def register(name: str, out: Path, spec: Dict) -> None:
    """The picture's record in the image registry: made or, when it exists,
    its sha256 brought up to date with the file. The words a reviewer
    wrote in an existing record are kept."""
    records = json.loads(MANIFEST.read_text(encoding="utf-8"))
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    for r in records:
        if r["name"] == out.name:
            r["origin"] = {"kind": "render", "source": name, "sha256": digest, "imported_sha256": digest}
            break
    else:
        angle = {"part": "three-quarter view, the part filling the frame",
                 "view": "three-quarter view from the side the name says",
                 "pictogram": "nine three-quarter views in a grid, each fitted to its frame",
                 "use": "from the user's seat, in front of the embosser and a little above it"}.get(spec["kind"], "fixed three-quarter view from the left front")
        records.append({"name": out.name, "group": out.parent.name,
                        "origin": {"kind": "render", "source": name, "sha256": digest, "imported_sha256": digest},
                        "subject": list(spec["ids"]), "angle": angle, "shows": "Computer rendering of " + spec["shows"],
                        "crop": None, "use": "guide", "alt_status": "none"})
    MANIFEST.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", action="append", default=[], metavar="NAME", help="one picture by name, without .png (repeatable)")
    ap.add_argument("--list", action="store_true", help="print the picture names and stop")
    args = ap.parse_args(argv)
    specs = pictures()
    if args.list:
        print("\n".join(specs))
        return 0
    names = args.only or list(specs)
    unknown = [n for n in names if n not in specs]
    if unknown:
        ap.error(f"unknown picture(s): {unknown}; see --list")
    bodies: Optional[Dict[str, Path]] = None
    for name in names:
        spec = specs[name]
        if spec["kind"] == "part":
            out = render(name, part_scad_text(spec["id"], spec["file"]), PART_CAMERA, fit=True)
        else:
            if bodies is None:
                bodies = split_bodies()
            if spec["kind"] == "stage":
                out = render(name, scad_text(bodies, spec["ids"]), STAGE_CAMERA, fit=False)
            elif spec["kind"] == "view":
                out = render(name, scad_text(bodies, spec["ids"]), spec["camera"], fit=False)
            elif spec["kind"] == "pictogram":
                out = pictogram_page(bodies)
            else:
                out = render(name, scad_text(bodies, spec["ids"], EXPLODE_MM), EXPLODED_CAMERA, fit=False)
        register(name, out, spec)
        print(f"{out.relative_to(ROOT).as_posix()} {out.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
