#!/usr/bin/env python3
"""The panels of the Visual Assembly Guide: one picture a step, no words.

Each panel is built from the step still that scripts/animate_assembly.py
renders (the moving part at its start pose, a red dashed arrow from its
leading face to where it enters), in the kit's colours, with a numbered
badge for the order and, at the top right, an identification box in the
manner of brick-set and flat-pack instructions: black line sketches of the
part to find (its two faces, where the faces differ) and, under a red
arrow, the face it goes onto. In a sketch what stands up from a face is
filled black and a hole or a cut is an outline. The sketches are the
faces that scripts/derive_tactile_assembly_map.py cuts from the part files, so
they are the parts' own outlines (decision D54).

A parts panel opens the guide: every part, in the order the steps use
them. Panels go to ``Photos/visual/`` and are registered in images.json.

Usage:
    python scripts/visual_guide.py          # every panel
    python scripts/visual_guide.py --only 8

Local lane: needs Pillow, the rendered stills (``python
scripts/animate_assembly.py --stills``) and the derived shapes (``python
scripts/derive_tactile_assembly_map.py``). License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.animate_assembly import ROLLER_A, ROLLER_B, STEPS, STILLS  # noqa: E402
from scripts.derive_tactile_assembly_map import SHAPES_JSON  # noqa: E402
from scripts.render_parts import BUILD, PART_CAMERA, PART_COLOURS, register, render, split_bodies  # noqa: E402

OUT = ROOT / "Photos" / "visual"
PART_RENDERS = ROOT / "Photos" / "renders"
PANEL = (1400, 1050)
BG = (248, 248, 248)          # the renders' own background (OpenSCAD's Tomorrow scheme)
INK = (40, 40, 40)
RED = (214, 40, 40)
FRAME_W = 6
MARGIN = 36
BADGE_D = 120
BOX_PAD = 22
SKETCH_SCALE = 4.0            # pixels per mm in the identification box
SKETCH_LINE = 3               # the sketch's line, in pixels
SKETCH_GAP = 26               # between two sketches in a row
ARROW_H = 46                  # the red arrow between the rows
SUPERSAMPLE = 3
FONT_PATH = Path("C:/Windows/Fonts/arialbd.ttf")

# The parts the guide inventories, in the order the steps first use them.
PART_ORDER = ["cylinder-a", "top-gear-a", "bottom-gear-a", "cylinder-b", "top-gear-b", "bottom-gear-b",
              "base", "knob", "lid", "handle", "push-out-plate"]

# What each step's identification box shows: the faces to find (left to
# right) and, under the red arrow, the face they go onto. The face ids are
# scripts/derive_tactile_assembly_map.py's.
IDENTIFY: Dict[int, Tuple[List[str], Optional[str]]] = {
    1: (["cylinder-a-top"], None),
    2: (["top-gear-a-hub", "top-gear-a"], "cylinder-a-top"),
    3: (["bottom-gear-a-hub", "bottom-gear-a"], "cylinder-a-bottom"),
    4: (["cylinder-b-top"], None),
    5: (["top-gear-b-hub", "top-gear-b"], "cylinder-b-top"),
    6: (["bottom-gear-b-hub", "bottom-gear-b"], "cylinder-b-bottom"),
    7: (["cylinder-a-top", "cylinder-b-top"], None),
    8: (["bottom-gear-a-hub", "bottom-gear-b-hub"], "base-top"),
    9: (["knob-top"], "top-gear-a-hub"),
    10: (["lid-underside"], "top-gear-b-hub"),
    11: (["handle-cup"], "knob-top"),
}


def font(size: int) -> ImageFont.FreeTypeFont:
    if FONT_PATH.exists():
        return ImageFont.truetype(str(FONT_PATH), size)
    return ImageFont.load_default(size=size)


def content_box(im: Image.Image, margin: int = 0) -> Tuple[int, int, int, int]:
    """The box round everything that is not background."""
    bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
    box = ImageChops.difference(im, bg).getbbox()
    if box is None:
        raise ValueError("an empty picture")
    x0, y0, x1, y1 = box
    return (max(0, x0 - margin), max(0, y0 - margin), min(im.width, x1 + margin), min(im.height, y1 + margin))


def fit(im: Image.Image, size: Tuple[int, int]) -> Image.Image:
    out = im.copy()
    out.thumbnail(size, Image.LANCZOS)
    return out


def part_thumbnails(bodies: Dict[str, Path]) -> Dict[str, Image.Image]:
    """A cropped picture of every part: the per-part renders for the
    printed parts, a render of the placed body for each cylinder."""
    thumbs: Dict[str, Image.Image] = {}
    for pid in PART_ORDER:
        png = PART_RENDERS / f"render-part-{pid}.png"
        if not png.exists():
            # The cylinders are generated, not printed from a file: render the placed body.
            scad = f'color("{PART_COLOURS[pid]}") import("{bodies[pid].resolve().as_posix()}");\n'
            png = render(f"thumb-{pid}", scad, PART_CAMERA, fit=True, out_dir=BUILD)
        im = Image.open(png).convert("RGB")
        thumbs[pid] = im.crop(content_box(im, 10))
    return thumbs


def load_faces() -> Dict[str, Dict]:
    return {f["id"]: f for f in json.loads(SHAPES_JSON.read_text(encoding="utf-8"))["faces"]}


def sketch(face: Dict, scale: float = SKETCH_SCALE) -> Image.Image:
    """The face as a black line drawing: outline levels as outlines with
    their holes, fill levels filled black. Drawn supersampled, then
    reduced, so the lines are smooth."""
    w, h = face["size_mm"]
    ox, oy = face["offset"]
    pad = SKETCH_LINE * 2
    s = scale * SUPERSAMPLE
    size = (int(w * s) + 2 * pad * SUPERSAMPLE, int(h * s) + 2 * pad * SUPERSAMPLE)
    im = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(im)
    line = SKETCH_LINE * SUPERSAMPLE

    def ring_points(pts, path):
        return [((x + ox + w / 2) * s + pad * SUPERSAMPLE, (h / 2 - (y + oy)) * s + pad * SUPERSAMPLE) for x, y in (pts[k] for k in path)]

    levels = {i + 1: lv for i, lv in enumerate(face["levels"])}
    for lvl in face["sketch"]["fill"]:
        mask = Image.new("L", size, 0)
        md = ImageDraw.Draw(mask)
        for pts, paths in levels[lvl]["polygons"]:
            md.polygon(ring_points(pts, paths[0]), fill=255)
            for hole in paths[1:]:
                md.polygon(ring_points(pts, hole), fill=0)
        im.paste((0, 0, 0), mask=mask)
    for lvl in face["sketch"]["outline"]:
        for pts, paths in levels[lvl]["polygons"]:
            for path in paths:
                ring = ring_points(pts, path)
                d.line(ring + ring[:1], fill=(0, 0, 0), width=line, joint="curve")
    return im.resize((size[0] // SUPERSAMPLE, size[1] // SUPERSAMPLE), Image.LANCZOS)


def identification_box(faces: Dict[str, Dict], find: Sequence[str], onto: Optional[str]) -> Image.Image:
    """The box: the faces to find in a row, then a red arrow down to the face they go onto."""
    top = [sketch(faces[f]) for f in find]
    bottom = sketch(faces[onto]) if onto else None
    row_w = sum(im.width for im in top) + SKETCH_GAP * (len(top) - 1)
    row_h = max(im.height for im in top)
    w = max(row_w, bottom.width if bottom else 0) + 2 * BOX_PAD
    h = row_h + 2 * BOX_PAD + ((ARROW_H + bottom.height + BOX_PAD // 2) if bottom else 0)
    box = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(box)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=24, outline=INK, width=4, fill=(255, 255, 255))
    x = (w - row_w) // 2
    for im in top:
        box.paste(im, (x, BOX_PAD + (row_h - im.height) // 2))
        x += im.width + SKETCH_GAP
    if bottom:
        cx = w // 2
        y0 = BOX_PAD + row_h + 8
        y1 = y0 + ARROW_H - 10
        d.line([(cx, y0), (cx, y1 - 14)], fill=RED, width=6)
        d.polygon([(cx - 14, y1 - 18), (cx + 14, y1 - 18), (cx, y1)], fill=RED)
        box.paste(bottom, ((w - bottom.width) // 2, y1 + 6))
    return box


def badge(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str) -> None:
    x, y = xy
    draw.ellipse([x, y, x + BADGE_D, y + BADGE_D], fill=INK)
    f = font(72 if len(text) < 3 else 56)
    w, h = draw.textbbox((0, 0), text, font=f)[2:]
    draw.text((x + (BADGE_D - w) / 2, y + (BADGE_D - h) / 2 - 8), text, font=f, fill=BG)


def step_panel(step: Dict, faces: Dict[str, Dict]) -> Image.Image:
    k = step["n"]
    still = Image.open(STILLS / f"visual-step-{k:02}.png").convert("RGB")
    picture = still.crop(content_box(still, 30))
    panel = Image.new("RGB", PANEL, BG)
    draw = ImageDraw.Draw(panel)
    draw.rectangle([0, 0, panel.width - 1, panel.height - 1], outline=INK, width=FRAME_W)
    box = identification_box(faces, *IDENTIFY[k]) if k in IDENTIFY else None
    box_w = box.width + MARGIN if box else 0
    # The still fills what the badge row and the box leave free.
    top = MARGIN + FRAME_W + BADGE_D + MARGIN // 2
    area = (panel.width - 2 * (MARGIN + FRAME_W) - box_w, panel.height - top - MARGIN - FRAME_W)
    picture = fit(picture, area)
    panel.paste(picture, (MARGIN + FRAME_W + (area[0] - picture.width) // 2, top + (area[1] - picture.height) // 2))
    badge(draw, (MARGIN + FRAME_W, MARGIN + FRAME_W), str(k))
    if box:
        panel.paste(box, (panel.width - MARGIN - FRAME_W - box.width, MARGIN + FRAME_W))
    return panel


def parts_panel(thumbs: Dict[str, Image.Image]) -> Image.Image:
    """Every part, four to a row, in the order of use."""
    panel = Image.new("RGB", PANEL, BG)
    draw = ImageDraw.Draw(panel)
    draw.rectangle([0, 0, panel.width - 1, panel.height - 1], outline=INK, width=FRAME_W)
    cols, rows = 4, 3
    cw = (panel.width - 2 * MARGIN) // cols
    ch = (panel.height - 2 * MARGIN) // rows
    for i, pid in enumerate(PART_ORDER):
        cx = MARGIN + (i % cols) * cw
        cy = MARGIN + (i // cols) * ch
        im = fit(thumbs[pid], (cw - 40, ch - 40))
        panel.paste(im, (cx + (cw - im.width) // 2, cy + (ch - im.height) // 2))
    return panel


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", type=int, action="append", default=[], metavar="N", help="one step's panel (repeatable)")
    args = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    faces = load_faces()
    made: List[Path] = []
    if not args.only:
        thumbs = part_thumbnails(split_bodies())
        out = OUT / "visual-parts.png"
        parts_panel(thumbs).save(out, optimize=True)
        register(out.stem, out, {"kind": "visual", "ids": PART_ORDER,
                                 "shows": "every part, four to a row, in the order the steps use them"})
        made.append(out)
    for s in STEPS:
        if args.only and s["n"] not in args.only:
            continue
        out = OUT / f"visual-step-{s['n']:02}.png"
        step_panel(s, faces).save(out, optimize=True)
        ids = s["move"] or ROLLER_A + ROLLER_B + ["base", "knob", "lid", "handle"]
        register(out.stem, out, {"kind": "visual", "ids": ids,
                                 "shows": f"step {s['n']}, {s['title']}: a numbered panel with the moving part at its start, "
                                          "a red dashed arrow to where it goes, and line sketches of the faces to find and match"})
        made.append(out)
    for p in made:
        print(f"{p.relative_to(ROOT).as_posix()} {p.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
