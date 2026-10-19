#!/usr/bin/env python3
"""The MakerWorld listing's pictures, cropped and sized alike.

MakerWorld's upload form keeps real photos of the print apart from computer
renderings, asks for a front, a side and a top view among the photos, and
takes the cover twice: a 4:3 picture for the desktop site and a 3:4 one for
the mobile app. This script writes, under ``MakerWorld_Photos/``:

- ``Cover/``: the desktop cover and the mobile cover;
- ``Real_Photos/``: the photographs, in the order to upload them;
- ``Renders/``: the computer renderings, copied unchanged from
  ``Photos/renders/`` (scripts/render_parts.py and render_use.py make them).

A photograph is read from its full-size master and the parts are found on
the mat (photo_import.subject_box). The frame is drawn round them so they
fill the same share of every picture, unless the master runs out of pixels
first; then the frame is the largest the master holds. Every picture is
saved as sRGB with no EXIF.

Usage:
    python scripts/makerworld_photos.py --masters "<Official Version 2 folder>"

Local lane: needs Pillow (never run with ``python -I``). License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.photo_import import load_manifest, masters_root, open_master, subject_box  # noqa: E402

OUT = ROOT / "MakerWorld_Photos"
RENDERS = ROOT / "Photos" / "renders"
# The sizes MakerWorld's users report the site shows uncropped (the upload
# form's own page cannot be read by a script). The mobile cover stays at
# 768 px wide because the front photo has no more pixels than that to give.
GALLERY = (1600, 1200)
MOBILE = (768, 1024)
FILL = 2 / 3          # the parts' share of the frame's width or height, whichever is tighter
COVER_FILL = 0.75     # a cover is seen small, so its parts fill more of it
QUALITY = 90          # MakerWorld compresses again on upload

STYLE_2 = "BE_V2_Style_2/"
# The tactile map's photos sit in their own folder beside the photos folder.
# They were taken on a brighter-lit mat, so their blue plates are found by
# colour alone.
TACTILE_MAP = "../Braille Embosser Tactile Map/"
# (folder, file, source, size, fill). A source with a slash is a master
# photo by its path; one ending .png is a render in Photos/renders/; any
# other is a name in Documentation/images.json, read from its master.
PICTURES = [
    ("Cover", "1_desktop_4x3.jpg", STYLE_2 + "20261001_175723.jpg", GALLERY, COVER_FILL),
    ("Cover", "2_mobile_3x4.jpg", STYLE_2 + "20261001_175456-2.jpg", MOBILE, COVER_FILL),
    ("Real_Photos", "01_front.jpg", STYLE_2 + "20261001_175456-2.jpg", GALLERY, FILL),
    ("Real_Photos", "02_side.jpg", STYLE_2 + "20261001_175503.jpg", GALLERY, FILL),
    ("Real_Photos", "03_back.jpg", STYLE_2 + "20261001_175507.jpg", GALLERY, FILL),
    ("Real_Photos", "04_underside.jpg", STYLE_2 + "20261001_175522.jpg", GALLERY, FILL),
    ("Real_Photos", "05_embossed_card.jpg", STYLE_2 + "20261001_175723.jpg", GALLERY, FILL),
    ("Real_Photos", "06_all_parts.jpg", "overview-all-parts.jpg", GALLERY, FILL),
    ("Real_Photos", "07_first_cylinder_gears.jpg", "stage-second-gear-beside-cylinder-first.jpg", GALLERY, FILL),
    ("Real_Photos", "08_second_cylinder_gears.jpg", "stage-second-gear-beside-cylinder-second.jpg", GALLERY, FILL),
    ("Real_Photos", "09_rollers_beside_base.jpg", "stage-rollers-beside-base.jpg", GALLERY, FILL),
    ("Real_Photos", "10_knob_on_lid_beside.jpg", "stage-knob-on-lid-beside.jpg", GALLERY, FILL),
    ("Real_Photos", "11_handle_beside.jpg", "stage-handle-beside.jpg", GALLERY, FILL),
    ("Real_Photos", "12_complete_fused_rollers.jpg", "stage-fused-handle-on.jpg", GALLERY, FILL),
    ("Real_Photos", "13_tactile_map_all.jpg", TACTILE_MAP + "TM_All.jpg", GALLERY, FILL),
    ("Real_Photos", "14_tactile_map_1_to_4.jpg", TACTILE_MAP + "TM_P1.jpg", GALLERY, FILL),
    ("Real_Photos", "15_tactile_map_5_to_8.jpg", TACTILE_MAP + "TM_P2.jpg", GALLERY, FILL),
    ("Real_Photos", "16_tactile_map_9_to_11.jpg", TACTILE_MAP + "20261009_084208.jpg", GALLERY, FILL),
    ("Real_Photos", "17_tactile_map_12_and_13.jpg", TACTILE_MAP + "20261009_084220.jpg", GALLERY, FILL),
    ("Renders", "1_exploded.png", "render-exploded.png", GALLERY, None),
    ("Renders", "2_card_into_slit.png", "render-use-03-card-into-slit.png", GALLERY, None),
    ("Renders", "3_half_a_turn.png", "render-use-04-half-a-turn.png", GALLERY, None),
    ("Renders", "4_card_out_dots_up.png", "render-use-05-turned-over-window-up.png", GALLERY, None),
]


def frame(subject: Tuple[float, float, float, float], image_size: Tuple[int, int],
          aspect: float, fill: float) -> Tuple[int, int, int, int]:
    """A box of the given width-to-height ``aspect`` round the subject, which
    fills ``fill`` of the box's width or height, whichever is tighter. When
    the box would be larger than the image it shrinks to the largest that
    fits, and it is slid inside the image, never cutting the subject."""
    left, top, right, bottom = subject
    sw, sh = right - left, bottom - top
    w = max(sw / fill, sh / fill * aspect)
    h = w / aspect
    W, H = image_size
    shrink = min(1.0, W / w, H / h)
    w, h = w * shrink, h * shrink
    if w < sw or h < sh:
        raise ValueError(f"a {aspect:.3g}:1 frame inside {W}x{H} cannot hold a {sw:.0f}x{sh:.0f} subject")
    x0 = min(max((left + right) / 2 - w / 2, 0), W - w)
    y0 = min(max((top + bottom) / 2 - h / 2, 0), H - h)
    return round(x0), round(y0), round(x0 + w), round(y0 + h)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--masters", help="the Official Version 2 folder (or set BE_V2_MASTERS)")
    args = ap.parse_args(argv)
    root = masters_root(args.masters)
    records = {r["name"]: r for r in load_manifest() if r["name"]}
    for folder, name, source, size, fill in PICTURES:
        out = OUT / folder / name
        out.parent.mkdir(parents=True, exist_ok=True)
        if source.endswith(".png"):
            src = RENDERS / source
            with Image.open(src) as im:
                if im.size != size:
                    raise ValueError(f"{source} is {im.size[0]}x{im.size[1]}, not {size[0]}x{size[1]}")
            shutil.copyfile(src, out)
            print(f"{out.relative_to(ROOT).as_posix()}: copied from {source}")
            continue
        record = {"origin": {"source": source}} if "/" in source else records[source]
        im = open_master(root, record)
        box = frame(subject_box(im, coloured_only=source.startswith(TACTILE_MAP)), im.size, size[0] / size[1], fill)
        im.crop(box).resize(size, Image.LANCZOS).save(out, "JPEG", quality=QUALITY, progressive=True, optimize=True)
        scale = size[0] / (box[2] - box[0])
        print(f"{out.relative_to(ROOT).as_posix()}: {size[0]}x{size[1]} from {record['origin']['source']} "
              f"crop {list(box)}, scaled x{scale:.2f}, {out.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
