#!/usr/bin/env python3
"""The image registry and the contact sheets for choosing photos.

The master photos live outside the repository, in the Official Version 2
folder (``--masters``, or the environment variable ``BE_V2_MASTERS``); they
are never written to. This script does two things with them:

``--init-manifest`` writes ``Documentation/images.json``, one record per
master photo: where it came from (``origin``: the folder and file, its
sha256, its pixel size), its group (Style_1 overview, Style_2 finished,
Style_3 parts, Style_4 stages), and the fields the triage fills in by hand
(``name``, ``subject``, ``angle``, ``shows``, ``crop``, ``use``). A record
that already exists is kept as it is, so a reshoot adds photos without
losing the triage of the old ones.

``--sheets`` writes contact sheets into ``build/contact_sheets/``: one group
per sheet series, thirty thumbnails a sheet, each labelled with its record
index, file name and pixel size, so a reviewer can see every photo on a few
pages and fill the registry in while looking at them.

Usage:
    python scripts/photo_contact_sheets.py --masters "<Official Version 2 folder>" --init-manifest --sheets

Local lane: needs Pillow (never run with ``python -I``). License: GPL-3.0-or-later
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "Documentation" / "images.json"
SHEETS = ROOT / "build" / "contact_sheets"
PHOTOS_SUBFOLDER = "Braille Embosser Version 2 Photos"
GROUPS = {"BE_V2_Style_1": "overview", "BE_V2_Style_2": "finished", "BE_V2_Style_3": "parts", "BE_V2_Style_4": "stages"}
THUMB = 320
COLUMNS, ROWS = 6, 5
LABEL_H = 36
GUTTER = 8
FONT_CANDIDATES = (r"C:\Windows\Fonts\arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def masters_root(arg: Optional[str]) -> Path:
    value = arg or os.environ.get("BE_V2_MASTERS")
    if not value:
        raise SystemExit("name the Official Version 2 folder with --masters or BE_V2_MASTERS")
    root = Path(value)
    if not (root / PHOTOS_SUBFOLDER).is_dir():
        raise SystemExit(f"{root} has no '{PHOTOS_SUBFOLDER}' folder")
    return root


def master_photos(root: Path) -> List[Path]:
    photos: List[Path] = []
    for folder, _group in GROUPS.items():
        photos += sorted((root / PHOTOS_SUBFOLDER / folder).glob("*.jpg"))
    return photos


def source_of(root: Path, photo: Path) -> str:
    return photo.relative_to(root / PHOTOS_SUBFOLDER).as_posix()


def new_record(root: Path, photo: Path) -> Dict:
    with Image.open(photo) as im:
        width, height = im.size
    return {
        "name": "",
        "group": GROUPS[photo.parent.name],
        "origin": {"kind": "photo", "source": source_of(root, photo),
                   "sha256": hashlib.sha256(photo.read_bytes()).hexdigest(), "pixels": [width, height]},
        "subject": [],
        "angle": "",
        "shows": "",
        "crop": None,
        "use": "undecided",
        "alt_status": "none",
    }


def load_manifest() -> List[Dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else []


def save_manifest(records: Sequence[Dict]) -> None:
    MANIFEST.write_text(json.dumps(list(records), indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def init_manifest(root: Path) -> int:
    """Add a record for every master photo not yet in the registry; keep the rest."""
    records = load_manifest()
    known = {r["origin"].get("source") for r in records if r["origin"]["kind"] == "photo"}
    added = 0
    for photo in master_photos(root):
        if source_of(root, photo) not in known:
            records.append(new_record(root, photo))
            added += 1
    save_manifest(records)
    print(f"{MANIFEST.relative_to(ROOT).as_posix()}: {len(records)} records ({added} added)")
    return added


def _font(size: int) -> ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _thumbnail(photo: Path) -> Image.Image:
    with Image.open(photo) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((THUMB, THUMB), Image.LANCZOS)
        return im.copy()


def sheet(records: Sequence[Dict], root: Path, title: str, out: Path) -> None:
    font = _font(15)
    cell_w, cell_h = THUMB + GUTTER, THUMB + LABEL_H + GUTTER
    page = Image.new("RGB", (COLUMNS * cell_w + GUTTER, ROWS * cell_h + GUTTER + LABEL_H), "white")
    draw = ImageDraw.Draw(page)
    draw.text((GUTTER, 8), title, fill="black", font=font)
    for k, (index, record) in enumerate(records):
        thumb = _thumbnail(root / PHOTOS_SUBFOLDER / record["origin"]["source"])
        x = GUTTER + (k % COLUMNS) * cell_w
        y = GUTTER + LABEL_H + (k // COLUMNS) * cell_h
        page.paste(thumb, (x + (THUMB - thumb.width) // 2, y + (THUMB - thumb.height) // 2))
        w, h = record["origin"]["pixels"]
        label = f"#{index}  {Path(record['origin']['source']).name}  {w}x{h}"
        draw.text((x, y + THUMB + 4), label, fill="black", font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    page.save(out, "JPEG", quality=88)
    print(f"{out.relative_to(ROOT).as_posix()}: {len(records)} photos")


def write_sheets(root: Path) -> None:
    records = load_manifest()
    if not records:
        raise SystemExit("no registry yet; run --init-manifest first")
    per_page = COLUMNS * ROWS
    for folder, group in GROUPS.items():
        rows = [(i, r) for i, r in enumerate(records) if r["origin"]["kind"] == "photo" and r["group"] == group]
        for page_no, start in enumerate(range(0, len(rows), per_page), 1):
            chunk = rows[start:start + per_page]
            title = f"{folder} ({group}), sheet {page_no}: records #{chunk[0][0]} to #{chunk[-1][0]}"
            sheet(chunk, root, title, SHEETS / f"{group}-sheet-{page_no}.jpg")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--masters", help="the Official Version 2 folder (or set BE_V2_MASTERS)")
    ap.add_argument("--init-manifest", action="store_true", help="add a registry record for every master photo not yet listed")
    ap.add_argument("--sheets", action="store_true", help="write the contact sheets into build/contact_sheets/")
    args = ap.parse_args(argv)
    if not (args.init_manifest or args.sheets):
        ap.error("nothing to do: pass --init-manifest and/or --sheets")
    root = masters_root(args.masters)
    if args.init_manifest:
        init_manifest(root)
    if args.sheets:
        write_sheets(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
