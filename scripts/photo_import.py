#!/usr/bin/env python3
"""Import the chosen master photos into ``Photos/`` at guide size.

Every record in ``Documentation/images.json`` with ``use`` set to ``guide``
and an origin of kind ``photo`` is read from the master folder (``--masters``
or ``BE_V2_MASTERS``), turned the way its EXIF says (a no-op for this shoot,
which carries none), converted to sRGB when it carries a colour profile,
cropped to its ``crop`` box when it has one, scaled to at most 1600 px on the
long edge, and saved under ``Photos/<group>/<name>`` as a progressive JPEG at
quality 85 with no EXIF and no profile. The sha256 of the saved file is
written back into the record as ``origin.imported_sha256``.

``--propose-crops`` fills in a ``crop`` box for every chosen photo that has
none, found from the mat: the dark mat is thresholded away, the thin light
grid lines are erased with a minimum filter, and the bright parts that remain
give a bounding box, widened by a margin and opened out to a 3:2 frame. The
boxes are proposals; a reviewer looks at the imported pictures and edits any
box in the registry by hand, then imports again.

Usage:
    python scripts/photo_import.py --masters "<Official Version 2 folder>" --propose-crops
    python scripts/photo_import.py --masters "<Official Version 2 folder>"               # import every chosen photo
    python scripts/photo_import.py --masters "<Official Version 2 folder>" --only stage-lid-on.jpg
    python scripts/photo_import.py --masters "<Official Version 2 folder>" --lead finished-standing.jpg

Local lane: needs Pillow (never run with ``python -I``). License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageCms, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "Documentation" / "images.json"
PHOTOS = ROOT / "Photos"
PHOTOS_SUBFOLDER = "Braille Embosser Version 2 Photos"
LEAD = PHOTOS / "Braille_Embosser_V2.jpg"
LONG_EDGE = 1600
LEAD_WIDTH = 1000
QUALITY = 85
MAT_THRESHOLD = 165   # brightness (HSV value) above which a pixel is a part, not the mat
MAT_SATURATION = 70   # saturation above which a pixel is a coloured part; the mat and its lines are grey
MASK_WIDTH = 800      # the mask is found at this width, where a grid line is a pixel or two
GRID_ERASE = 11       # minimum-filter window that swallows the grid lines and small scuffs at that width
MARGIN = 0.06         # of the subject's width and height, each side
FRAME_ASPECT = 3 / 2  # the guide's figure shape: 140 mm wide, 95 mm tall at most
MIN_CROP_WIDTH = LONG_EDGE  # never save a crop smaller than the guide size when the photo has the pixels


def masters_root(arg: Optional[str]) -> Path:
    value = arg or os.environ.get("BE_V2_MASTERS")
    if not value:
        raise SystemExit("name the Official Version 2 folder with --masters or BE_V2_MASTERS")
    root = Path(value)
    if not (root / PHOTOS_SUBFOLDER).is_dir():
        raise SystemExit(f"{root} has no '{PHOTOS_SUBFOLDER}' folder")
    return root


def load_manifest() -> List[Dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save_manifest(records: Sequence[Dict]) -> None:
    MANIFEST.write_text(json.dumps(list(records), indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def chosen(records: Sequence[Dict], only: Sequence[str]) -> List[Dict]:
    out = [r for r in records if r["use"] == "guide" and r["origin"]["kind"] == "photo"]
    if only:
        wanted = set(only)
        out = [r for r in out if r["name"] in wanted]
        missing = wanted - {r["name"] for r in out}
        if missing:
            raise SystemExit(f"not chosen photos: {sorted(missing)}")
    for r in out:
        if not r["name"]:
            raise SystemExit(f"{r['origin']['source']} is chosen for the guide but has no name")
    return out


def open_master(root: Path, record: Dict) -> Image.Image:
    with Image.open(root / PHOTOS_SUBFOLDER / record["origin"]["source"]) as im:
        im = ImageOps.exif_transpose(im)
        profile = im.info.get("icc_profile")
        im = im.convert("RGB")
        if profile:
            src = ImageCms.ImageCmsProfile(io.BytesIO(profile))
            im = ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"), outputMode="RGB")
        return im


def subject_box(im: Image.Image, coloured_only: bool = False) -> Tuple[float, float, float, float]:
    """The bounding box of the parts on the mat, with no margin, as (left,
    top, right, bottom) in the photo's pixels. The mask is found on a copy
    ``MASK_WIDTH`` px wide, where the grid lines are one or two pixels and the
    minimum filter erases them whatever the photo's size. ``coloured_only``
    is for strongly coloured parts on a mat lit brighter than
    ``MAT_THRESHOLD``, where the brightness test would take in the mat."""
    scale = MASK_WIDTH / im.width
    small = im.resize((MASK_WIDTH, max(1, round(im.height * scale))), Image.BILINEAR)
    # The mat is neutral grey at any exposure; a part is either light (white,
    # grey) or strongly coloured (pink, cyan, yellow), so a pixel counts when
    # it is bright OR saturated.
    _h, s, v = small.convert("HSV").split()
    coloured = s.point(lambda x: 255 if x > MAT_SATURATION else 0)
    if coloured_only:
        mask = coloured
    else:
        mask = v.point(lambda x: 255 if x > MAT_THRESHOLD else 0)
        mask.paste(255, mask=coloured)
    mask = mask.filter(ImageFilter.MinFilter(GRID_ERASE))
    box = mask.getbbox()
    if box is None:
        raise ValueError("no subject found above the mat threshold")
    left, top, right, bottom = (v / scale for v in box)
    return left, top, right, bottom


def propose_crop(im: Image.Image) -> Tuple[int, int, int, int]:
    """A crop box round the parts on the mat, as (left, top, right, bottom)."""
    left, top, right, bottom = subject_box(im)
    w, h = right - left, bottom - top
    left, right = left - MARGIN * w, right + MARGIN * w
    top, bottom = top - MARGIN * h, bottom + MARGIN * h
    w, h = right - left, bottom - top
    if w / h < FRAME_ASPECT:
        grow = (h * FRAME_ASPECT - w) / 2
        left, right = left - grow, right + grow
    else:
        grow = (w / FRAME_ASPECT - h) / 2
        top, bottom = top - grow, bottom + grow
    W, H = im.size
    # A small part is framed at least MIN_CROP_WIDTH wide (when the photo has
    # it), so the saved picture keeps the guide's size and the part sits in
    # some mat rather than touching the edges.
    w, h = right - left, bottom - top
    if w < MIN_CROP_WIDTH:
        grow_w = (min(MIN_CROP_WIDTH, W) - w) / 2
        grow_h = grow_w / FRAME_ASPECT
        left, right, top, bottom = left - grow_w, right + grow_w, top - grow_h, bottom + grow_h
    # Slide the frame back inside the picture before clamping, so a subject
    # near an edge keeps its margin on the other side.
    if left < 0:
        right, left = right - left, 0
    if top < 0:
        bottom, top = bottom - top, 0
    if right > W:
        left, right = max(0, left - (right - W)), W
    if bottom > H:
        top, bottom = max(0, top - (bottom - H)), H
    return int(left), int(top), int(right), int(bottom)


def save_jpeg(im: Image.Image, out: Path, long_edge: int) -> str:
    im = im.copy()
    im.thumbnail((long_edge, long_edge), Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "JPEG", quality=QUALITY, progressive=True, optimize=True)
    return hashlib.sha256(out.read_bytes()).hexdigest()


def import_record(root: Path, record: Dict) -> Path:
    im = open_master(root, record)
    if record.get("crop"):
        im = im.crop(tuple(record["crop"]))
    out = PHOTOS / record["group"] / record["name"]
    record["origin"]["imported_sha256"] = save_jpeg(im, out, LONG_EDGE)
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--masters", help="the Official Version 2 folder (or set BE_V2_MASTERS)")
    ap.add_argument("--propose-crops", action="store_true", help="fill in a crop box for every chosen photo without one")
    ap.add_argument("--only", action="append", default=[], metavar="NAME", help="import only this photo (repeatable)")
    ap.add_argument("--lead", metavar="NAME", help="also save this chosen photo as the lead image, 1000 px wide")
    args = ap.parse_args(argv)
    root = masters_root(args.masters)
    records = load_manifest()
    todo = chosen(records, args.only)
    if args.propose_crops:
        proposed = 0
        for r in todo:
            # A box a reviewer set by hand (crop_by "hand") is never recomputed.
            if r.get("crop_by") != "hand":
                r["crop"] = list(propose_crop(open_master(root, r)))
                r["crop_by"] = "mat"
                proposed += 1
                print(f"{r['name']}: crop {r['crop']}")
        save_manifest(records)
        print(f"{proposed} crop boxes proposed")
        return 0
    for r in todo:
        out = import_record(root, r)
        with Image.open(out) as im:
            print(f"{out.relative_to(ROOT).as_posix()}: {im.size[0]}x{im.size[1]}, {out.stat().st_size // 1024} KB")
    if args.lead:
        lead = next((r for r in records if r["name"] == args.lead), None)
        if lead is None or lead["use"] != "guide":
            raise SystemExit(f"{args.lead} is not a chosen photo")
        im = open_master(root, lead)
        if lead.get("crop"):
            im = im.crop(tuple(lead["crop"]))
        save_jpeg(im, LEAD, LEAD_WIDTH)
        print(f"{LEAD.relative_to(ROOT).as_posix()}: lead image from {args.lead}")
    save_manifest(records)
    return 0


if __name__ == "__main__":
    sys.exit(main())
